"""Matrix Script minimal result service bridge (PR-5R).

Connects the PR-4R minimal result loop to a Matrix-Script-internal service
entry point. A caller hands in either an explicit Hook/Body/CTA outline OR a
Matrix-Script task-like fixture; the service builds the shot plan (PR-2) +
scene manifest skeleton (PR-3), runs the minimal result loop (PR-4R) to
produce a REAL local ``final.mp4`` result pack, and returns a service-layer
``MatrixScriptMinimalResultSummary`` (local paths only).

This proves Matrix Script now has a callable internal production capability
that creates a real ``final.mp4``.

Hard boundary (PR-5R approval):
- NO Akool / provider / adapter import; NO live API / webhook / polling;
  ``generation_provider`` stays ``"none"``.
- NO ``artifact_storage`` / R2 write — output goes only to the caller-supplied
  ``output_dir`` (a test temp dir in CI). This service does NOT own artifact
  truth; it returns local result-pack paths for service-layer validation only.
- NO route / template / Delivery Center / schema / packet / contract change;
  NO Hot Follow / Digital Anchor change; NO publish logic.
- The outline derived from a task fixture is a deterministic placeholder, NOT
  real script understanding (which is gated behind Capability Expansion W2.3).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from gateway.app.services.matrix_script.minimal_result_loop import (
    GENERATION_PROVIDER,
    run_minimal_result_loop,
)
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    ffmpeg_available,
    probe_duration_seconds,
)


class MinimalResultServiceError(ValueError):
    """Raised when the service request is invalid (not an ffmpeg-absence case)."""


@dataclass(frozen=True)
class MatrixScriptMinimalResultRequest:
    """Service-layer request.

    Provide ``outline`` (Hook/Body/CTA mapping) OR ``task`` (a Matrix Script
    task-like fixture from which a deterministic outline is derived). At least
    one must be supplied. ``output_dir`` is a caller-owned (test temp) path.
    """

    output_dir: str
    task_id: Optional[str] = None
    outline: Optional[Mapping[str, Any]] = None
    task: Optional[Mapping[str, Any]] = None
    aspect_ratio: str = "9:16"
    target_duration_seconds: float = 20.0

    def __post_init__(self) -> None:
        if not isinstance(self.output_dir, str) or not self.output_dir:
            raise MinimalResultServiceError("output_dir must be a non-empty string")
        if self.outline is None and self.task is None:
            raise MinimalResultServiceError("provide either outline or task")
        if self.outline is not None and not isinstance(self.outline, Mapping):
            raise MinimalResultServiceError("outline must be a mapping when set")
        if self.task is not None and not isinstance(self.task, Mapping):
            raise MinimalResultServiceError("task must be a mapping when set")


@dataclass(frozen=True)
class MatrixScriptMinimalResultSummary:
    """Service-layer result summary — local result-pack paths only (not truth)."""

    task_id: Optional[str]
    final_video_path: str
    manifest_path: str
    subtitles_path: str
    audio_path: str
    shot_count: int
    duration_seconds: float
    generation_provider: str
    scene_strategy: str
    audio_strategy: str


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        if key in mapping and mapping.get(key) not in (None, ""):
            return mapping.get(key)
    return None


def _task_field(task: Mapping[str, Any], *keys: str) -> Optional[Any]:
    """Look up a field at top level or under ``config.entry`` (create_entry shape)."""
    top = _first_present(task, *keys)
    if top is not None:
        return top
    config = task.get("config")
    if isinstance(config, Mapping):
        entry = config.get("entry")
        if isinstance(entry, Mapping):
            return _first_present(entry, *keys)
    return None


def derive_outline_from_task(task: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a deterministic Hook/Body/CTA outline from a task-like fixture.

    Deterministic placeholder only — NOT real script understanding. Uses the
    closed Matrix Script entry fields (topic / operator_notes / audience_hint /
    tone_hint / length_hint / target_platform). No vendor/model involvement.
    """
    if not isinstance(task, Mapping):
        raise MinimalResultServiceError("task must be a mapping")

    topic = _task_field(task, "topic")
    hook = str(topic).strip() if topic else "Matrix Script 短视频"

    body: List[str] = []
    notes = _task_field(task, "operator_notes")
    if isinstance(notes, str) and notes.strip():
        for chunk in notes.replace("\r", "\n").split("\n"):
            text = chunk.strip(" .。;；")
            if text:
                body.append(text)
    for hint_key in ("audience_hint", "tone_hint", "length_hint"):
        hint = _task_field(task, hint_key)
        if isinstance(hint, str) and hint.strip():
            body.append(hint.strip())
    if not body:
        body = ["要点一", "要点二", "要点三"]

    platform = _task_field(task, "target_platform")
    cta = f"在 {platform} 关注了解更多" if platform else "关注了解更多"

    return {"hook": hook, "body": body, "cta": cta}


def _resolve_task_id(request: MatrixScriptMinimalResultRequest) -> Optional[str]:
    if request.task_id is not None:
        return request.task_id
    if request.task is not None:
        candidate = _task_field(request.task, "task_id", "id")
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def run_matrix_script_minimal_result(
    request: MatrixScriptMinimalResultRequest,
) -> MatrixScriptMinimalResultSummary:
    """Run the minimal result loop for a task/outline; return a result summary.

    Raises :class:`FFmpegUnavailableError` if ffmpeg/ffprobe are missing — a
    fake ``final.mp4`` is never fabricated.
    """
    if not isinstance(request, MatrixScriptMinimalResultRequest):
        raise MinimalResultServiceError("request must be a MatrixScriptMinimalResultRequest")
    if not ffmpeg_available():
        raise FFmpegUnavailableError(
            "ffmpeg/ffprobe not found on PATH; the Matrix Script minimal result "
            "service cannot produce a real final.mp4 in this environment."
        )

    outline = request.outline if request.outline is not None else derive_outline_from_task(request.task)
    task_id = _resolve_task_id(request)

    output = run_minimal_result_loop(
        outline,
        request.output_dir,
        task_id=task_id,
        aspect_ratio=request.aspect_ratio,
        target_duration_seconds=request.target_duration_seconds,
    )

    # Success precondition: a real final.mp4 must exist before we summarise.
    if not (os.path.exists(output.final_video_path) and os.path.getsize(output.final_video_path) > 0):
        raise MinimalResultServiceError("minimal result loop did not produce a non-empty final.mp4")

    duration_seconds = probe_duration_seconds(output.final_video_path)
    manifest = output.manifest

    return MatrixScriptMinimalResultSummary(
        task_id=task_id,
        final_video_path=output.final_video_path,
        manifest_path=output.manifest_path,
        subtitles_path=output.subtitle_path,
        audio_path=output.audio_path,
        shot_count=int(manifest["shot_count"]),
        duration_seconds=float(duration_seconds),
        generation_provider=str(manifest.get("generation_provider", GENERATION_PROVIDER)),
        scene_strategy=str(manifest["scene_strategy"]),
        audio_strategy=str(manifest["audio_strategy"]),
    )


class MatrixScriptMinimalResultService:
    """Thin class wrapper over :func:`run_matrix_script_minimal_result`."""

    def run(
        self, request: MatrixScriptMinimalResultRequest
    ) -> MatrixScriptMinimalResultSummary:
        return run_matrix_script_minimal_result(request)
