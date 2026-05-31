"""Matrix Script minimal result loop — first real result-oriented loop (PR-4R).

Produces a REAL, locally-playable ``final.mp4`` from a script / outline:

    outline → shot_plan (PR-2) → scene artifact slots (PR-3)
            → simple FFmpeg color-card scene clips
            → silent audio fallback
            → subtitles.srt
            → FFmpeg assembly → final.mp4
            → manifest.json

The first goal is NOT Akool and NOT high-quality visuals — it is a real,
playable ``final.mp4`` written to a caller-supplied (test temp) directory.

Hard boundary (PR-4R approval):
- NO Akool live API / adapter import; NO webhook / polling / provider async
  job store; ``generation_provider = "none"``.
- NO ``artifact_storage`` / R2 write — output goes only to the caller's
  ``output_dir`` (a test temp dir in CI). This is NOT formal artifact storage.
- NO UI / template / Delivery Center runtime / schema / packet / contract
  change; NO Hot Follow / Digital Anchor change.
- NO provider URL anywhere in the manifest.
- If FFmpeg is unavailable, the loop raises ``FFmpegUnavailableError`` — it
  never fabricates a ``final.mp4``.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from gateway.app.services.matrix_script.scene_artifacts import (
    build_scene_artifact_slots,
)
from gateway.app.services.matrix_script.scene_manifest import (
    build_scene_manifest_skeleton,
)
from gateway.app.services.matrix_script.shot_plan import MatrixScriptShotPlan
from gateway.app.services.matrix_script.shot_plan_builder import build_shot_plan
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    assemble_final_video,
    ffmpeg_available,
    generate_silent_audio,
    probe_duration_seconds,
    render_color_scene_clip,
    scene_color_for_order,
)

# Strategy markers recorded on the manifest (binding per PR-4R §7).
SCENE_STRATEGY = "ffmpeg_color_card"
AUDIO_STRATEGY = "silent_fallback"
GENERATION_PROVIDER = "none"

# Default 9:16 short-video frame (kept small for fast CI rendering).
_DEFAULT_WIDTH = 360
_DEFAULT_HEIGHT = 640
_DEFAULT_TARGET_DURATION_SECONDS = 12.0

# Forbidden tokens that must never appear in the manifest (provider/truth leak).
_FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "akool",
    "provider_url",
    "temporary_url",
    "download_url",
    "provider_task_id",
    "vendor",
    "model_id",
    "credit",
)


@dataclass(frozen=True)
class MinimalResultLoopOutput:
    """Paths + manifest produced by a single loop run (all under output_dir)."""

    output_dir: str
    final_video_path: str
    audio_path: str
    subtitle_path: str
    scene_clip_paths: Tuple[str, ...]
    manifest_path: str
    manifest: Mapping[str, Any]


def _fmt_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(plan: MatrixScriptShotPlan) -> str:
    """Build SRT text from a shot plan's subtitle texts + cumulative durations.

    Pure — no ffmpeg, no I/O. Deterministic for a given plan.
    """
    if not isinstance(plan, MatrixScriptShotPlan):
        raise TypeError("plan must be a MatrixScriptShotPlan")
    lines: List[str] = []
    cursor = 0.0
    for i, shot in enumerate(plan.shots, start=1):
        start = cursor
        end = cursor + float(shot.duration_seconds)
        cursor = end
        text = shot.subtitle_text.strip() or shot.visual_intent.strip()
        lines.append(str(i))
        lines.append(f"{_fmt_srt_timestamp(start)} --> {_fmt_srt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_srt(path: str, plan: MatrixScriptShotPlan) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(build_srt(plan))
    return path


def build_manifest_dict(
    *,
    plan: MatrixScriptShotPlan,
    scene_clip_relpaths: List[str],
    audio_relpath: str,
    subtitle_relpath: str,
    final_video_relpath: str,
) -> Dict[str, Any]:
    """Assemble the manifest dict (pure; no ffmpeg, no I/O).

    Records local relative paths only — never an artifact key, provider URL, or
    download URL. ``generation_provider`` is always ``"none"``.
    """
    manifest_skeleton = build_scene_manifest_skeleton(plan)
    manifest = {
        "manifest_version": "matrix_script_minimal_result_loop_v1",
        "manifest_id": manifest_skeleton.manifest_id,
        "plan_id": plan.plan_id,
        "task_id": plan.task_id,
        "aspect_ratio": plan.aspect_ratio,
        "target_duration_seconds": float(plan.target_duration_seconds),
        "shot_count": len(plan.shots),
        "scene_strategy": SCENE_STRATEGY,
        "audio_strategy": AUDIO_STRATEGY,
        "generation_provider": GENERATION_PROVIDER,
        "final_video_path": final_video_relpath,
        "audio_path": audio_relpath,
        "subtitle_path": subtitle_relpath,
        "scene_clip_paths": list(scene_clip_relpaths),
    }
    _assert_no_forbidden_tokens(manifest)
    return manifest


def _assert_no_forbidden_tokens(manifest: Mapping[str, Any]) -> None:
    blob = json.dumps(manifest, ensure_ascii=False).lower()
    hits = [tok for tok in _FORBIDDEN_TOKENS if tok in blob]
    if hits:
        raise ValueError(f"manifest leaks forbidden tokens: {hits}")


def run_minimal_result_loop(
    outline: Mapping[str, Any],
    output_dir: str,
    *,
    task_id: Optional[str] = None,
    aspect_ratio: str = "9:16",
    target_duration_seconds: float = _DEFAULT_TARGET_DURATION_SECONDS,
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
) -> MinimalResultLoopOutput:
    """Run the full minimal result loop, writing real files under ``output_dir``.

    Raises :class:`FFmpegUnavailableError` if ffmpeg/ffprobe are missing (no
    fake ``final.mp4`` is ever produced).
    """
    if not ffmpeg_available():
        raise FFmpegUnavailableError(
            "ffmpeg/ffprobe not found on PATH; the minimal result loop cannot "
            "produce a real final.mp4 in this environment."
        )

    plan = build_shot_plan(
        outline,
        task_id=task_id,
        aspect_ratio=aspect_ratio,
        target_duration_seconds=target_duration_seconds,
    )
    slots = build_scene_artifact_slots(plan)

    shots_dir = os.path.join(output_dir, "shots")
    audio_dir = os.path.join(output_dir, "audio")
    subs_dir = os.path.join(output_dir, "subtitles")
    final_dir = os.path.join(output_dir, "final")
    work_dir = os.path.join(output_dir, ".work")
    for d in (shots_dir, audio_dir, subs_dir, final_dir, work_dir):
        os.makedirs(d, exist_ok=True)

    # 1. scene clips — one per slot, deterministic filename + color.
    scene_clip_paths: List[str] = []
    for slot, shot in zip(slots, plan.shots):
        clip_path = os.path.join(shots_dir, slot.expected_filename)
        render_color_scene_clip(
            clip_path,
            duration_seconds=float(shot.duration_seconds),
            width=width,
            height=height,
            color=scene_color_for_order(shot.order),
        )
        scene_clip_paths.append(clip_path)

    # 2. silent audio fallback for the whole timeline.
    audio_path = os.path.join(audio_dir, "narration.wav")
    generate_silent_audio(audio_path, duration_seconds=plan.total_duration_seconds)

    # 3. subtitles.
    subtitle_path = os.path.join(subs_dir, "subtitles.srt")
    write_srt(subtitle_path, plan)

    # 4. assemble final.mp4.
    final_video_path = os.path.join(final_dir, "final.mp4")
    assemble_final_video(
        final_video_path,
        scene_clip_paths=scene_clip_paths,
        audio_path=audio_path,
        work_dir=work_dir,
    )

    # 5. manifest.json (relative paths only).
    manifest = build_manifest_dict(
        plan=plan,
        scene_clip_relpaths=[os.path.relpath(p, output_dir) for p in scene_clip_paths],
        audio_relpath=os.path.relpath(audio_path, output_dir),
        subtitle_relpath=os.path.relpath(subtitle_path, output_dir),
        final_video_relpath=os.path.relpath(final_video_path, output_dir),
    )
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    return MinimalResultLoopOutput(
        output_dir=output_dir,
        final_video_path=final_video_path,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        scene_clip_paths=tuple(scene_clip_paths),
        manifest_path=manifest_path,
        manifest=manifest,
    )
