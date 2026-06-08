"""Matrix Script minimal result record (PR-6R).

Converts the PR-5R :class:`MatrixScriptMinimalResultSummary` into an internal,
projection-ready **result record** that a future Workbench / Delivery
projection can consume. This is a pure conversion layer — no I/O, no ffmpeg.

The record is NOT a formal delivery contract and NOT artifact truth. It is an
internal Matrix Script service-layer record scoped to the local workspace.
``publish_ready_candidate`` is an internal candidate hint only — it is NOT the
official publish gate.

Hard boundary (PR-6R approval):
- NO Akool / provider / adapter import; NO live API / webhook / polling;
  ``generation_provider`` stays ``"none"``.
- NO ``artifact_storage`` / R2 write or truth field; paths are local-workspace
  paths only (``*_path``), never ``*_key`` / ``download_url`` / ``r2_key``.
- NO publish logic / ``publish_url`` / ``publish_status``.
- NO route / template / Delivery Center runtime / schema / packet / contract
  change; NO Hot Follow / Digital Anchor change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gateway.app.services.matrix_script.minimal_result_service import (
    MatrixScriptMinimalResultSummary,
)

LINE_ID = "matrix_script"
RESULT_STATUS_GENERATED = "generated"
STORAGE_SCOPE_LOCAL = "local_workspace"
GENERATION_PROVIDER_NONE = "none"

# Tokens that must never appear in a result record (provider / artifact-storage
# truth / publish leakage). Note: ``*_path`` keys are allowed local paths.
FORBIDDEN_TOKENS = (
    "provider_url",
    "temporary_url",
    "download_url",
    "akool",
    "vendor",
    "model_id",
    "credit",
    "provider_task_id",
    "artifact_key",
    "final_video_key",
    "r2_key",
    "publish_url",
    "publish_status",
)


class ResultRecordError(ValueError):
    """Raised on an invalid summary → record conversion."""


@dataclass(frozen=True)
class MatrixScriptMinimalResultRecord:
    """Internal, projection-ready Matrix Script result record (local-scoped)."""

    task_id: Any  # Optional[str] — None allowed for fixture-driven runs
    line_id: str
    final_video_path: str
    manifest_path: str
    subtitles_path: str
    audio_path: str
    shot_count: int
    duration_seconds: float
    result_status: str
    publish_ready_candidate: bool
    storage_scope: str
    generation_provider: str
    scene_strategy: str
    audio_strategy: str
    # Operator-safe ffmpeg-backbone QC facts (hashable scalars; None on the legacy path).
    qc_passed: Optional[bool] = None
    qc_resolution: Optional[str] = None


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def compute_publish_ready_candidate(summary: MatrixScriptMinimalResultSummary) -> bool:
    """Internal candidate hint (NOT the official publish gate).

    True only when the local result pack is complete and provider/scope are the
    expected local, provider-free values.
    """
    return bool(
        _is_nonempty_str(summary.final_video_path)
        and _is_nonempty_str(summary.manifest_path)
        and _is_nonempty_str(summary.subtitles_path)
        and _is_nonempty_str(summary.audio_path)
        and isinstance(summary.duration_seconds, (int, float))
        and not isinstance(summary.duration_seconds, bool)
        and summary.duration_seconds > 0
        and isinstance(summary.shot_count, int)
        and not isinstance(summary.shot_count, bool)
        and summary.shot_count > 0
        and summary.generation_provider == GENERATION_PROVIDER_NONE
    )


def minimal_result_summary_to_record(
    summary: MatrixScriptMinimalResultSummary,
) -> MatrixScriptMinimalResultRecord:
    """Pure conversion: summary → internal result record. No I/O."""
    if not isinstance(summary, MatrixScriptMinimalResultSummary):
        raise ResultRecordError("summary must be a MatrixScriptMinimalResultSummary")
    return MatrixScriptMinimalResultRecord(
        task_id=summary.task_id,
        line_id=LINE_ID,
        final_video_path=summary.final_video_path,
        manifest_path=summary.manifest_path,
        subtitles_path=summary.subtitles_path,
        audio_path=summary.audio_path,
        shot_count=int(summary.shot_count),
        duration_seconds=float(summary.duration_seconds),
        result_status=RESULT_STATUS_GENERATED,
        publish_ready_candidate=compute_publish_ready_candidate(summary),
        storage_scope=STORAGE_SCOPE_LOCAL,
        generation_provider=summary.generation_provider or GENERATION_PROVIDER_NONE,
        scene_strategy=summary.scene_strategy,
        audio_strategy=summary.audio_strategy,
        qc_passed=summary.qc_passed,
        qc_resolution=summary.qc_resolution,
    )


def minimal_result_record_to_dict(
    record: MatrixScriptMinimalResultRecord,
) -> Dict[str, object]:
    """Pure serialization (closed key set; local paths only, no truth/provider field)."""
    payload: Dict[str, object] = {
        "task_id": record.task_id,
        "line_id": record.line_id,
        "final_video_path": record.final_video_path,
        "manifest_path": record.manifest_path,
        "subtitles_path": record.subtitles_path,
        "audio_path": record.audio_path,
        "shot_count": record.shot_count,
        "duration_seconds": record.duration_seconds,
        "result_status": record.result_status,
        "publish_ready_candidate": record.publish_ready_candidate,
        "storage_scope": record.storage_scope,
        "generation_provider": record.generation_provider,
        "scene_strategy": record.scene_strategy,
        "audio_strategy": record.audio_strategy,
    }
    assert_no_result_record_forbidden_tokens(payload)
    return payload


def assert_no_result_record_forbidden_tokens(payload: object) -> None:
    """Raise ``ResultRecordError`` if any forbidden token leaks.

    Checks both serialized values AND, for mappings, the key names — so a
    forbidden truth/publish *field* (e.g. ``publish_url``) can never slip in.
    """
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        hits: List[str] = [tok for tok in FORBIDDEN_TOKENS if tok in keys_blob]
        if hits:
            raise ResultRecordError(f"result record has forbidden keys: {hits}")
    blob = str(payload).lower()
    value_hits: List[str] = [tok for tok in FORBIDDEN_TOKENS if tok in blob]
    if value_hits:
        raise ResultRecordError(f"result record leaks forbidden tokens: {value_hits}")
