"""Matrix Script ffmpeg backbone — Runtime PR-1 (first integration slice).

Gate Spec: ``docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md``.
Implements the offline-proven, secret-free **ffmpeg backbone**:

- ``generate_kenburns_proxy`` — a Ken-Burns (pan/zoom) **proxy** clip from a still
  image. This is a MOTION PROXY, **not generative animation** — the fast-preview /
  fallback tier, never a final-quality or generative claim (Gate Spec §4, §8).
- ``compose_concat`` — ffmpeg concat of per-shot clips into one delivery-spec cut.
- ``qc_report`` / ``qc_probe`` — ffprobe-based quality check with a pass/fail verdict.
- ``generate_with_fallback`` — proxy first; on failure, a static-still clip (the tier
  below the proxy); compose still proceeds (Gate Spec §8 fallback semantics).

Hard boundary (Gate Spec §3, §4, §9):
- Deterministic output only: 1080×1920, 30fps, h264/yuv420p, fixed preset/crf.
- NO credential, NO network, NO provider/vendor/model/engine, NO Akool — local
  ``ffmpeg``/``ffprobe`` only. NO generative ``image_to_video`` provider.
- NO ``artifact_storage`` / R2 write — callers pass an output directory.
- NO schema/contract change; NO UI; NO delivery-truth change. ``official_publish_ready``
  stays ``False`` — backbone output is a *preview candidate* only.
- Operator-safe projections exclude ``local_path`` / raw probe JSON (Gate Spec §7);
  raw fields belong to backend/J-zone, never operator copy.
- If ffmpeg/ffprobe are unavailable, calls raise; a fake clip is NEVER produced.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

# ----- Deterministic fast-preview encode params (Gate Spec §6) -----------------
BACKBONE_WIDTH = 1080
BACKBONE_HEIGHT = 1920
BACKBONE_FPS = 30
BACKBONE_VCODEC_NAME = "h264"        # ffprobe codec_name for the libx264 encoder
BACKBONE_VENCODER = "libx264"
BACKBONE_PIX_FMT = "yuv420p"
BACKBONE_PRESET = "medium"
BACKBONE_CRF = "23"
_RUN_TIMEOUT_SECONDS = 120
_DURATION_TOLERANCE_SECONDS = 0.2

# Honest capability semantics (Gate Spec §4 non-goals).
IS_GENERATIVE = False
TIER_PROXY = "fast_preview_proxy"
TIER_STATIC_STILL = "static_still_fallback"
OPERATOR_LABEL_PROXY = "预览代理（非生成式）"
OPERATOR_LABEL_STATIC = "静态画面（兜底，无运动）"

# The backbone never marks output publish-ready (Gate Spec §5).
OFFICIAL_PUBLISH_READY = False

ZOOM_IN = "in"
ZOOM_OUT = "out"
_ZOOM_INCREMENT = 0.0022
_ZOOM_MAX = 1.2

_CROP_VF = (
    f"scale={BACKBONE_WIDTH}:{BACKBONE_HEIGHT}:force_original_aspect_ratio=increase,"
    f"crop={BACKBONE_WIDTH}:{BACKBONE_HEIGHT}"
)


class FFmpegUnavailableError(RuntimeError):
    """Raised when ffmpeg/ffprobe are not installed. A fake clip is never produced."""


class BackboneRenderError(RuntimeError):
    """Raised when an ffmpeg/ffprobe subprocess fails or input is invalid."""


# A runner is injectable so the fallback path is unit-testable without ffmpeg.
Runner = Callable[[List[str]], None]


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
            "ffmpeg/ffprobe not found on PATH; cannot render a real preview clip. "
            "(A fake clip is never produced.)"
        )


def _run(cmd: List[str]) -> None:
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=_RUN_TIMEOUT_SECONDS, check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or b"").decode("utf-8", "replace")[-400:]
        raise BackboneRenderError(
            f"ffmpeg/ffprobe failed ({proc.returncode}): {' '.join(cmd[:3])}… :: {tail}"
        )


def _frames(duration_seconds: float) -> int:
    return max(1, int(round(float(duration_seconds) * BACKBONE_FPS)))


def _zoom_expr(zoom: str) -> str:
    if zoom == ZOOM_IN:
        return f"min(zoom+{_ZOOM_INCREMENT},{_ZOOM_MAX})"
    if zoom == ZOOM_OUT:
        return f"if(eq(on,1),{_ZOOM_MAX},max(1.0,zoom-{_ZOOM_INCREMENT}))"
    raise BackboneRenderError(f"zoom must be {ZOOM_IN!r} or {ZOOM_OUT!r}, got {zoom!r}")


# ----- Pure command builders (testable without invoking ffmpeg) ----------------

def build_kenburns_command(image_path: str, out_path: str, *, duration_seconds: float, zoom: str) -> List[str]:
    """Build the deterministic Ken-Burns proxy ffmpeg argv. Pure (no side effects)."""
    if duration_seconds <= 0:
        raise BackboneRenderError("duration_seconds must be positive")
    frames = _frames(duration_seconds)
    vf = (
        f"{_CROP_VF},zoompan=z='{_zoom_expr(zoom)}':d={frames}:"
        f"s={BACKBONE_WIDTH}x{BACKBONE_HEIGHT}:fps={BACKBONE_FPS}"
    )
    return [
        ffmpeg_path() or "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-t", str(float(duration_seconds)), "-r", str(BACKBONE_FPS), "-vf", vf,
        "-c:v", BACKBONE_VENCODER, "-preset", BACKBONE_PRESET, "-crf", BACKBONE_CRF,
        "-pix_fmt", BACKBONE_PIX_FMT, "-an", out_path,
    ]


def build_static_still_command(image_path: str, out_path: str, *, duration_seconds: float) -> List[str]:
    """Build the static-still fallback argv (no motion). Pure."""
    if duration_seconds <= 0:
        raise BackboneRenderError("duration_seconds must be positive")
    return [
        ffmpeg_path() or "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-t", str(float(duration_seconds)), "-r", str(BACKBONE_FPS), "-vf", _CROP_VF,
        "-c:v", BACKBONE_VENCODER, "-preset", BACKBONE_PRESET, "-crf", BACKBONE_CRF,
        "-pix_fmt", BACKBONE_PIX_FMT, "-an", out_path,
    ]


def build_compose_command(concat_list_path: str, out_path: str) -> List[str]:
    """Build the ffmpeg concat (stream-copy) compose argv. Pure."""
    return [
        ffmpeg_path() or "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", out_path,
    ]


def build_probe_command(media_path: str) -> List[str]:
    """Build the ffprobe JSON probe argv. Pure."""
    return [
        ffprobe_path() or "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", media_path,
    ]


# ----- Artifact descriptors (internal facts + operator-safe projection) --------

@dataclass(frozen=True)
class ClipArtifact:
    """An L2 artifact fact for a generated backbone clip.

    ``local_path`` is an internal backend fact; ``operator_summary()`` excludes it
    and every raw field (Gate Spec §7 leakage rules).
    """
    kind: str                      # "proxy_clip" | "composed_cut"
    local_path: str                # INTERNAL — never operator copy
    width: int = BACKBONE_WIDTH
    height: int = BACKBONE_HEIGHT
    fps: int = BACKBONE_FPS
    duration_seconds: float = 0.0
    codec: str = BACKBONE_VCODEC_NAME
    tier: str = TIER_PROXY
    is_generative: bool = IS_GENERATIVE
    is_preview_candidate: bool = True
    official_publish_ready: bool = OFFICIAL_PUBLISH_READY
    bytes_resolvable: bool = True

    def operator_summary(self) -> Dict[str, Any]:
        """Operator-safe projection — no local_path / raw manifest / provider field."""
        label = OPERATOR_LABEL_STATIC if self.tier == TIER_STATIC_STILL else OPERATOR_LABEL_PROXY
        return {
            "kind": self.kind,
            "operator_label": label,
            "is_generative": False,
            "tier": self.tier,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps,
            "duration_seconds": round(self.duration_seconds, 3),
            "is_preview_candidate": self.is_preview_candidate,
            "official_publish_ready": False,
        }


# ----- QC (pure verdict + probe runner) ----------------------------------------

def _fps_from_rate(rate: str) -> Optional[float]:
    try:
        if "/" in str(rate):
            num, den = str(rate).split("/", 1)
            den_f = float(den)
            return float(num) / den_f if den_f else None
        return float(rate)
    except (ValueError, ZeroDivisionError):
        return None


def qc_report(probe_data: Dict[str, Any], *, expected_duration_seconds: Optional[float] = None) -> Dict[str, Any]:
    """Compute an operator-safe QC verdict from an ffprobe JSON dict. Pure.

    Verifies resolution / codec / fps / duration-fit and emits a pass/fail per check
    plus an overall verdict. Contains only operator-safe fields (no local_path / raw
    JSON in the returned summary).
    """
    streams = probe_data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    fmt = probe_data.get("format") or {}
    checks: Dict[str, bool] = {}
    if video is None:
        return {"passed": False, "checks": {"has_video_stream": False}, "reason": "no_video_stream",
                "official_publish_ready": False}

    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    codec = str(video.get("codec_name") or "")
    fps = _fps_from_rate(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0")
    duration = None
    for src in (video.get("duration"), fmt.get("duration")):
        try:
            duration = float(src)
            break
        except (TypeError, ValueError):
            continue

    checks["resolution"] = (width == BACKBONE_WIDTH and height == BACKBONE_HEIGHT)
    checks["codec"] = (codec == BACKBONE_VCODEC_NAME)
    checks["fps"] = (fps is not None and abs(fps - BACKBONE_FPS) < 0.01)
    checks["has_duration"] = (duration is not None and duration > 0)
    if expected_duration_seconds is not None and duration is not None:
        checks["duration_fit"] = abs(duration - float(expected_duration_seconds)) <= _DURATION_TOLERANCE_SECONDS

    passed = all(checks.values())
    return {
        "passed": passed,
        "checks": checks,
        "resolution": f"{width}x{height}",
        "codec": codec,
        "fps": fps,
        "duration_seconds": round(duration, 3) if duration is not None else None,
        "official_publish_ready": False,   # QC pass never implies publish-readiness
    }


def probe_media(media_path: str, *, runner_capture: Optional[Callable[[List[str]], bytes]] = None) -> Dict[str, Any]:
    """Run ffprobe and return the parsed JSON dict. ``runner_capture`` is injectable."""
    if runner_capture is None:
        _require_ffmpeg()

        def _capture(cmd: List[str]) -> bytes:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=_RUN_TIMEOUT_SECONDS, check=False)
            if proc.returncode != 0:
                raise BackboneRenderError("ffprobe failed to read media")
            return proc.stdout or b"{}"

        runner_capture = _capture
    raw = runner_capture(build_probe_command(media_path))
    try:
        return json.loads(raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else raw)
    except (ValueError, AttributeError) as exc:
        raise BackboneRenderError(f"ffprobe returned non-JSON output: {exc}") from exc


def qc_probe(media_path: str, *, expected_duration_seconds: Optional[float] = None) -> Dict[str, Any]:
    """Probe a media file and return its operator-safe QC verdict."""
    return qc_report(probe_media(media_path), expected_duration_seconds=expected_duration_seconds)


# ----- Generation (proxy / fallback / compose) ---------------------------------

def generate_kenburns_proxy(
    image_path: str, out_path: str, *, duration_seconds: float = 3.0, zoom: str = ZOOM_IN,
    runner: Optional[Runner] = None,
) -> ClipArtifact:
    """Generate a Ken-Burns **proxy** clip (motion proxy, not generative)."""
    run = runner or _run
    if runner is None:
        _require_ffmpeg()
    if not (isinstance(image_path, str) and image_path):
        raise BackboneRenderError("image_path is required")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    run(build_kenburns_command(image_path, out_path, duration_seconds=duration_seconds, zoom=zoom))
    return ClipArtifact(kind="proxy_clip", local_path=out_path,
                        duration_seconds=float(duration_seconds), tier=TIER_PROXY)


def generate_static_still(
    image_path: str, out_path: str, *, duration_seconds: float = 3.0, runner: Optional[Runner] = None,
) -> ClipArtifact:
    """Generate the static-still fallback clip (no motion) — the tier below the proxy."""
    run = runner or _run
    if runner is None:
        _require_ffmpeg()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    run(build_static_still_command(image_path, out_path, duration_seconds=duration_seconds))
    return ClipArtifact(kind="proxy_clip", local_path=out_path,
                        duration_seconds=float(duration_seconds), tier=TIER_STATIC_STILL)


def generate_with_fallback(
    image_path: str, out_path: str, *, duration_seconds: float = 3.0, zoom: str = ZOOM_IN,
    runner: Optional[Runner] = None,
) -> ClipArtifact:
    """Proxy first; on render failure, fall back to a static still (Gate Spec §8)."""
    try:
        return generate_kenburns_proxy(image_path, out_path, duration_seconds=duration_seconds,
                                       zoom=zoom, runner=runner)
    except BackboneRenderError:
        return generate_static_still(image_path, out_path, duration_seconds=duration_seconds, runner=runner)


def compose_concat(
    clip_paths: Sequence[str], out_path: str, *, work_dir: str, runner: Optional[Runner] = None,
) -> ClipArtifact:
    """Concat per-shot clips into one delivery-spec cut (stream copy)."""
    run = runner or _run
    if runner is None:
        _require_ffmpeg()
    if not clip_paths:
        raise BackboneRenderError("clip_paths must be non-empty")
    os.makedirs(os.path.abspath(work_dir), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    concat_list = os.path.join(work_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as fh:
        for clip in clip_paths:
            fh.write(f"file '{os.path.abspath(clip)}'\n")
    run(build_compose_command(concat_list, out_path))
    return ClipArtifact(kind="composed_cut", local_path=out_path, tier=TIER_PROXY)


# ----- Manifest / evidence projection ------------------------------------------

@dataclass(frozen=True)
class BackboneManifest:
    """Bundled backbone evidence: per-shot clips + composed cut + qc verdict."""
    shot_clips: Sequence[ClipArtifact] = field(default_factory=tuple)
    composed_cut: Optional[ClipArtifact] = None
    qc: Optional[Dict[str, Any]] = None

    def operator_summary(self) -> Dict[str, Any]:
        """Operator-safe manifest projection — no local_path / raw probe JSON."""
        return {
            "shot_clips": [c.operator_summary() for c in self.shot_clips],
            "composed_cut": self.composed_cut.operator_summary() if self.composed_cut else None,
            "qc_passed": bool(self.qc.get("passed")) if self.qc else None,
            "tier": TIER_PROXY,
            "is_generative": False,
            "official_publish_ready": False,
            "note": "预览代理 + 拼接 + 质检，仅供预览；非生成式、非最终成片。",
        }
