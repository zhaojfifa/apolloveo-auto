"""Minimal FFmpeg scene renderer for the Matrix Script result loop (PR-4R).

First-version, deliberately minimal rendering primitives used by
``minimal_result_loop.py`` to produce a REAL, playable local ``final.mp4``:

- a scene clip is an FFmpeg ``lavfi`` color card of a fixed duration
  (``scene_strategy = ffmpeg_color_card``);
- audio is a silent track (``audio_strategy = silent_fallback``);
- the final video is the concatenated scene clips muxed with the silent audio.

Hard boundary (PR-4R approval):
- NO Akool / provider / adapter import; NO provider URL; ``generation_provider``
  is always ``"none"``.
- NO ``artifact_storage`` / R2 write — callers write only to a caller-supplied
  (test temp) directory.
- NO UI / template / route / runtime / schema / packet / contract change.
- If FFmpeg is unavailable, every render call raises
  :class:`FFmpegUnavailableError`. A fake ``final.mp4`` is NEVER produced.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import List, Optional, Sequence

# Deterministic color palette for scene cards (cycled by shot order). Names are
# FFmpeg lavfi color names — no randomness.
_SCENE_COLORS: Sequence[str] = (
    "navy",
    "teal",
    "maroon",
    "darkgreen",
    "purple",
    "gray",
    "black",
    "darkblue",
)

_DEFAULT_FPS = 25
_DEFAULT_AUDIO_RATE = 44100
_RUN_TIMEOUT_SECONDS = 120


class FFmpegUnavailableError(RuntimeError):
    """Raised when ffmpeg/ffprobe are not installed.

    Callers MUST surface this (or skip) rather than fabricate a ``final.mp4``.
    """


class SceneRenderError(RuntimeError):
    """Raised when an ffmpeg/ffprobe subprocess fails."""


def ffmpeg_path() -> Optional[str]:
    return shutil.which("ffmpeg")


def ffprobe_path() -> Optional[str]:
    return shutil.which("ffprobe")


def ffmpeg_available() -> bool:
    """True only if BOTH ffmpeg and ffprobe are on PATH."""
    return ffmpeg_path() is not None and ffprobe_path() is not None


def _require_ffmpeg() -> None:
    if not ffmpeg_available():
        raise FFmpegUnavailableError(
            "ffmpeg/ffprobe not found on PATH; cannot render a real final.mp4. "
            "Install ffmpeg to run the Matrix Script minimal result loop. "
            "(A fake final.mp4 is never produced.)"
        )


def _run(cmd: List[str]) -> None:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=_RUN_TIMEOUT_SECONDS,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or b"").decode("utf-8", "replace")[-400:]
        raise SceneRenderError(f"ffmpeg command failed ({proc.returncode}): {' '.join(cmd[:3])}… :: {tail}")


def scene_color_for_order(order: int) -> str:
    """Deterministic color-card color for a 1-based shot order."""
    if order < 1:
        raise SceneRenderError("order must be >= 1")
    return _SCENE_COLORS[(order - 1) % len(_SCENE_COLORS)]


def render_color_scene_clip(
    out_path: str,
    *,
    duration_seconds: float,
    width: int,
    height: int,
    color: str,
    fps: int = _DEFAULT_FPS,
) -> str:
    """Render a single solid-color scene clip to ``out_path``. Returns the path."""
    _require_ffmpeg()
    if duration_seconds <= 0:
        raise SceneRenderError("duration_seconds must be positive")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        ffmpeg_path(),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s={int(width)}x{int(height)}:d={float(duration_seconds)}:r={int(fps)}",
        "-t",
        str(float(duration_seconds)),
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        out_path,
    ]
    _run(cmd)
    return out_path


def generate_silent_audio(
    out_path: str,
    *,
    duration_seconds: float,
    sample_rate: int = _DEFAULT_AUDIO_RATE,
) -> str:
    """Generate a silent mono WAV of the given duration (silent fallback)."""
    _require_ffmpeg()
    if duration_seconds <= 0:
        raise SceneRenderError("duration_seconds must be positive")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        ffmpeg_path(),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={int(sample_rate)}:cl=mono",
        "-t",
        str(float(duration_seconds)),
        out_path,
    ]
    _run(cmd)
    return out_path


def assemble_final_video(
    out_path: str,
    *,
    scene_clip_paths: Sequence[str],
    audio_path: str,
    work_dir: str,
) -> str:
    """Concatenate scene clips + mux silent audio into ``out_path``."""
    _require_ffmpeg()
    if not scene_clip_paths:
        raise SceneRenderError("scene_clip_paths must be non-empty")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    os.makedirs(work_dir, exist_ok=True)
    concat_list = os.path.join(work_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as fh:
        for clip in scene_clip_paths:
            # concat demuxer requires absolute or work-relative paths, quoted.
            fh.write(f"file '{os.path.abspath(clip)}'\n")
    cmd = [
        ffmpeg_path(),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list,
        "-i",
        audio_path,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        out_path,
    ]
    _run(cmd)
    return out_path


def probe_duration_seconds(path: str) -> float:
    """Return the container duration of a media file via ffprobe (seconds)."""
    _require_ffmpeg()
    cmd = [
        ffprobe_path(),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nokey=1",
        path,
    ]
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=_RUN_TIMEOUT_SECONDS, check=False
    )
    if proc.returncode != 0:
        raise SceneRenderError("ffprobe failed to read media duration")
    raw = (proc.stdout or b"").decode("utf-8", "replace").strip()
    try:
        return float(raw)
    except ValueError as exc:
        raise SceneRenderError(f"ffprobe returned non-numeric duration: {raw!r}") from exc
