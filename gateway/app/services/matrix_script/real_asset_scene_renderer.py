"""Matrix Script Tomato Real Result — real-asset scene renderer (PR-A).

Turns a real local still image into a REAL motion video clip with a burned-in
operator-language caption. This is the difference between a color-card and an
operator-usable shot: the pixels are a real photograph, gently animated.

Pipeline per shot (two minimal ffmpeg passes, easy to debug):
  1. image → 9:16 motion clip via ``zoompan`` (Ken-Burns), framed by a focus
     point + zoom range (so a reused photo re-frames into a distinct shot).
  2. (optional) composite a transparent caption PNG via ``overlay``.

The caption PNG is rendered with Pillow + a system CJK font. This build of
ffmpeg has NO ``drawtext`` / ``subtitles`` filter (no libfreetype / libass), so
text is composited as an image. If Pillow is unavailable the clip is produced
WITHOUT a burned caption (the run still emits the .srt sidecar) — committed code
has no hard Pillow dependency.

Hard boundary: NO provider import / URL; NO ``artifact_storage`` write (caller
owns the output dir); NO schema / packet / contract change. ffmpeg absence
raises (never a fake clip).
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    SceneRenderError,
    ffmpeg_available,
    ffmpeg_path,
)

_DEFAULT_FPS = 25
_RUN_TIMEOUT_SECONDS = 180

# System CJK font candidates (this build has no libfreetype; Pillow draws text).
_FONT_CANDIDATES: Tuple[str, ...] = (
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)


@dataclass(frozen=True)
class ShotRenderResult:
    shot_id: str
    clip_path: str
    rendered: bool
    caption_burned: bool


def _run(cmd: List[str]) -> None:
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=_RUN_TIMEOUT_SECONDS, check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or b"").decode("utf-8", "replace")[-500:]
        raise SceneRenderError(f"ffmpeg failed ({proc.returncode}): {' '.join(cmd[:4])}… :: {tail}")


def _require_ffmpeg() -> None:
    if not ffmpeg_available():
        raise FFmpegUnavailableError(
            "ffmpeg/ffprobe not found on PATH; cannot render a real asset clip. "
            "(A fake clip is never produced.)"
        )


def available_font() -> Optional[str]:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def render_image_motion_clip(
    image_path: str,
    out_path: str,
    *,
    duration_seconds: float,
    width: int,
    height: int,
    focus: Tuple[float, float] = (0.5, 0.5),
    zoom: Tuple[float, float] = (1.0, 1.10),
    fps: int = _DEFAULT_FPS,
) -> str:
    """Render a real still image into a 9:16 Ken-Burns motion clip."""
    _require_ffmpeg()
    if not os.path.exists(image_path):
        raise SceneRenderError(f"image does not exist: {image_path}")
    if duration_seconds <= 0:
        raise SceneRenderError("duration_seconds must be positive")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    frames = max(int(round(duration_seconds * fps)), 1)
    z0, z1 = float(zoom[0]), float(zoom[1])
    fx, fy = float(focus[0]), float(focus[1])
    step = (z1 - z0) / max(frames - 1, 1)
    # Cover the target frame, crop to it, then zoompan in toward the focus point.
    z_expr = f"if(eq(on,0),{z0:.5f},min(zoom+{step:.6f},{z1:.5f}))"
    x_expr = f"iw*{fx:.4f}-(iw/zoom/2)"
    y_expr = f"ih*{fy:.4f}-(ih/zoom/2)"
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"format=yuv420p"
    )
    cmd = [
        ffmpeg_path(), "-y",
        "-loop", "1", "-i", image_path,
        "-t", f"{float(duration_seconds):.3f}",
        "-vf", vf,
        "-r", str(int(fps)),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    _run(cmd)
    return out_path


def render_caption_png(
    text: str,
    out_png: str,
    *,
    width: int,
    height: int,
    font_path: Optional[str] = None,
) -> Optional[str]:
    """Render a transparent full-frame caption PNG (Pillow). None if unavailable."""
    if not text or not text.strip():
        return None
    font_path = font_path or available_font()
    if not font_path:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_size = max(int(height * 0.045), 28)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        return None

    # Word-wrap CJK by character width budget.
    max_text_w = int(width * 0.88)

    def _text_w(s: str) -> int:
        box = draw.textbbox((0, 0), s, font=font)
        return box[2] - box[0]

    lines: List[str] = []
    cur = ""
    for ch in text.strip():
        if _text_w(cur + ch) <= max_text_w:
            cur += ch
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)

    line_h = int(font_size * 1.32)
    block_h = line_h * len(lines)
    pad = int(font_size * 0.5)
    band_top = height - block_h - pad * 2 - int(height * 0.06)
    band_bottom = band_top + block_h + pad * 2
    # Semi-transparent dark band for legibility over any photo.
    draw.rectangle([(0, band_top), (width, band_bottom)], fill=(0, 0, 0, 140))

    y = band_top + pad
    for ln in lines:
        w = _text_w(ln)
        x = (width - w) // 2
        # simple outline for contrast
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, y + dy), ln, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255))
        y += line_h

    img.save(out_png)
    return out_png


def overlay_caption(clip_in: str, caption_png: str, out_path: str) -> str:
    """Composite a full-frame caption PNG over a clip via ``overlay``."""
    _require_ffmpeg()
    if not os.path.exists(clip_in):
        raise SceneRenderError(f"clip does not exist: {clip_in}")
    if not os.path.exists(caption_png):
        raise SceneRenderError(f"caption png does not exist: {caption_png}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        ffmpeg_path(), "-y",
        "-i", clip_in,
        "-i", caption_png,
        "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        out_path,
    ]
    _run(cmd)
    return out_path


def render_shot_clip(
    image_path: str,
    work_dir: str,
    out_path: str,
    *,
    shot_id: str,
    duration_seconds: float,
    width: int,
    height: int,
    caption_text: str = "",
    focus: Tuple[float, float] = (0.5, 0.5),
    zoom: Tuple[float, float] = (1.0, 1.10),
    fps: int = _DEFAULT_FPS,
) -> ShotRenderResult:
    """Render one shot: real image → motion clip → (optional) burned caption."""
    os.makedirs(work_dir, exist_ok=True)
    motion_path = os.path.join(work_dir, f"{shot_id}_motion.mp4")
    render_image_motion_clip(
        image_path, motion_path,
        duration_seconds=duration_seconds, width=width, height=height,
        focus=focus, zoom=zoom, fps=fps,
    )
    caption_burned = False
    final_clip = motion_path
    if caption_text and caption_text.strip():
        caption_png = os.path.join(work_dir, f"{shot_id}_caption.png")
        png = render_caption_png(caption_text, caption_png, width=width, height=height)
        if png:
            overlay_caption(motion_path, png, out_path)
            final_clip = out_path
            caption_burned = True
    if final_clip != out_path:
        # No caption burned: promote the motion clip to the out_path.
        os.replace(motion_path, out_path)
        final_clip = out_path
    return ShotRenderResult(
        shot_id=shot_id, clip_path=out_path, rendered=True, caption_burned=caption_burned
    )
