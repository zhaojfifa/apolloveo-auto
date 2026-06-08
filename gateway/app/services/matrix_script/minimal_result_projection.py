"""Matrix Script minimal result projections (PR-7R).

Converts the PR-6R internal ``MatrixScriptMinimalResultRecord`` into
operator-safe and delivery-safe service-layer projections. These projections
are read models only: no I/O, no artifact storage, no publish gate, no runtime
or UI binding.

Hard boundary:
- NO Akool / provider / adapter import; NO live API / webhook / polling.
- NO ``artifact_storage`` / R2 write or artifact truth.
- NO official publish gate; ``official_publish_ready`` is always ``False``.
- NO route / template / Delivery Center runtime / schema / packet / contract
  change; NO Hot Follow / Digital Anchor change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gateway.app.services.matrix_script.minimal_result_record import (
    MatrixScriptMinimalResultRecord,
    ResultRecordError,
    STORAGE_SCOPE_LOCAL,
)

OFFICIAL_PUBLISH_READY_FALSE = False

# Operator-language labels for the (internal) scene_strategy token — the raw token is
# never surfaced to the operator; only this label is (truth-source / operator-safe rule).
_PREVIEW_MODE_LABELS = {
    "ffmpeg_backbone_proxy": "快速预览·镜头代理",
    "ffmpeg_color_card": "快速预览·占位色卡",
}


def _preview_mode_label(scene_strategy: str) -> str:
    return _PREVIEW_MODE_LABELS.get(str(scene_strategy or ""), "快速预览")


def _qc_summary(qc_passed: Optional[bool], qc_resolution: Optional[str]) -> str:
    """Operator-safe QC sentence from the (pass/fail, resolution) facts.

    Surfaces only the verdict + the picture spec (resolution) in operator language —
    never a raw path / codec internals / provider field. Neutral on the legacy path.
    """
    if qc_passed is None:
        return "本次预览未进行质检"
    if qc_passed:
        resolution = str(qc_resolution or "").strip()
        return f"质检通过 · 画面规格 {resolution}".strip() if resolution else "质检通过"
    return "质检未通过 · 可重试"

FORBIDDEN_PROJECTION_TOKENS = (
    "provider_url",
    "temporary_url",
    "download_url",
    "artifact_key",
    "r2_key",
    "publish_url",
    "publish_status",
    "akool",
    "vendor",
    "model_id",
    "credit",
    "provider_task_id",
)


class ResultProjectionError(ValueError):
    """Raised when record -> projection conversion is invalid."""


@dataclass(frozen=True)
class MatrixScriptOperatorResultProjection:
    """Operator-facing minimal result read model.

    Local paths are preserved for current internal validation only. They are
    not artifact truth and not official publish readiness.
    """

    task_id: Any
    line_id: str
    result_status: str
    has_final_video: bool
    final_video_path: str
    has_manifest: bool
    manifest_path: str
    has_subtitles: bool
    subtitles_path: str
    has_audio: bool
    audio_path: str
    duration_seconds: float
    shot_count: int
    publish_ready_candidate: bool
    operator_summary: str
    storage_scope: str
    official_publish_ready: bool = OFFICIAL_PUBLISH_READY_FALSE
    # Operator-safe fast-preview facts surfaced from the manifest (Scope Expansion Batch).
    preview_mode: str = ""             # operator label for scene_strategy (no raw token)
    qc_passed: Optional[bool] = None   # ffmpeg-backbone QC verdict (None on legacy path)
    qc_summary: str = ""               # operator-language QC sentence


@dataclass(frozen=True)
class MatrixScriptDeliveryResultProjection:
    """Delivery-facing minimal result read model.

    This is still not a delivery contract and not a publish gate. It gives a
    future Delivery surface a clean, local-scoped read model without direct
    access to the raw result record.
    """

    task_id: Any
    line_id: str
    result_status: str
    has_final_video: bool
    final_video_path: str
    has_manifest: bool
    manifest_path: str
    has_subtitles: bool
    subtitles_path: str
    has_audio: bool
    audio_path: str
    duration_seconds: float
    shot_count: int
    publish_ready_candidate: bool
    delivery_summary: str
    storage_scope: str
    official_publish_ready: bool = OFFICIAL_PUBLISH_READY_FALSE


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_record(record: MatrixScriptMinimalResultRecord) -> None:
    if not isinstance(record, MatrixScriptMinimalResultRecord):
        raise ResultProjectionError("record must be a MatrixScriptMinimalResultRecord")
    if record.storage_scope != STORAGE_SCOPE_LOCAL:
        raise ResultProjectionError("record.storage_scope must be local_workspace")


def _summary(record: MatrixScriptMinimalResultRecord, *, audience: str) -> str:
    return (
        f"{audience}: {record.shot_count} shots, "
        f"{record.duration_seconds:.2f}s, status={record.result_status}"
    )


def minimal_result_record_to_operator_projection(
    record: MatrixScriptMinimalResultRecord,
) -> MatrixScriptOperatorResultProjection:
    """Pure conversion: internal record -> operator-safe projection."""
    _validate_record(record)
    projection = MatrixScriptOperatorResultProjection(
        task_id=record.task_id,
        line_id=record.line_id,
        result_status=record.result_status,
        has_final_video=_nonempty(record.final_video_path),
        final_video_path=record.final_video_path,
        has_manifest=_nonempty(record.manifest_path),
        manifest_path=record.manifest_path,
        has_subtitles=_nonempty(record.subtitles_path),
        subtitles_path=record.subtitles_path,
        has_audio=_nonempty(record.audio_path),
        audio_path=record.audio_path,
        duration_seconds=float(record.duration_seconds),
        shot_count=int(record.shot_count),
        publish_ready_candidate=bool(record.publish_ready_candidate),
        operator_summary=_summary(record, audience="operator"),
        storage_scope=STORAGE_SCOPE_LOCAL,
        official_publish_ready=OFFICIAL_PUBLISH_READY_FALSE,
        preview_mode=_preview_mode_label(record.scene_strategy),
        qc_passed=record.qc_passed,
        qc_summary=_qc_summary(record.qc_passed, record.qc_resolution),
    )
    assert_no_result_projection_forbidden_tokens(operator_projection_to_dict(projection))
    return projection


def minimal_result_record_to_delivery_projection(
    record: MatrixScriptMinimalResultRecord,
) -> MatrixScriptDeliveryResultProjection:
    """Pure conversion: internal record -> delivery-safe projection."""
    _validate_record(record)
    projection = MatrixScriptDeliveryResultProjection(
        task_id=record.task_id,
        line_id=record.line_id,
        result_status=record.result_status,
        has_final_video=_nonempty(record.final_video_path),
        final_video_path=record.final_video_path,
        has_manifest=_nonempty(record.manifest_path),
        manifest_path=record.manifest_path,
        has_subtitles=_nonempty(record.subtitles_path),
        subtitles_path=record.subtitles_path,
        has_audio=_nonempty(record.audio_path),
        audio_path=record.audio_path,
        duration_seconds=float(record.duration_seconds),
        shot_count=int(record.shot_count),
        publish_ready_candidate=bool(record.publish_ready_candidate),
        delivery_summary=_summary(record, audience="delivery"),
        storage_scope=STORAGE_SCOPE_LOCAL,
        official_publish_ready=OFFICIAL_PUBLISH_READY_FALSE,
    )
    assert_no_result_projection_forbidden_tokens(delivery_projection_to_dict(projection))
    return projection


def operator_projection_to_dict(
    projection: MatrixScriptOperatorResultProjection,
) -> Dict[str, object]:
    """Serialize the operator projection with a closed, UI-safe key set."""
    if not isinstance(projection, MatrixScriptOperatorResultProjection):
        raise ResultProjectionError(
            "projection must be a MatrixScriptOperatorResultProjection"
        )
    payload: Dict[str, object] = {
        "task_id": projection.task_id,
        "line_id": projection.line_id,
        "result_status": projection.result_status,
        "has_final_video": projection.has_final_video,
        "final_video_path": projection.final_video_path,
        "has_manifest": projection.has_manifest,
        "manifest_path": projection.manifest_path,
        "has_subtitles": projection.has_subtitles,
        "subtitles_path": projection.subtitles_path,
        "has_audio": projection.has_audio,
        "audio_path": projection.audio_path,
        "duration_seconds": projection.duration_seconds,
        "shot_count": projection.shot_count,
        "publish_ready_candidate": projection.publish_ready_candidate,
        "operator_summary": projection.operator_summary,
        "storage_scope": projection.storage_scope,
        "official_publish_ready": projection.official_publish_ready,
        "preview_mode": projection.preview_mode,
        "qc_passed": projection.qc_passed,
        "qc_summary": projection.qc_summary,
    }
    assert_no_result_projection_forbidden_tokens(payload)
    return payload


def delivery_projection_to_dict(
    projection: MatrixScriptDeliveryResultProjection,
) -> Dict[str, object]:
    """Serialize the delivery projection with a closed, delivery-safe key set."""
    if not isinstance(projection, MatrixScriptDeliveryResultProjection):
        raise ResultProjectionError(
            "projection must be a MatrixScriptDeliveryResultProjection"
        )
    payload: Dict[str, object] = {
        "task_id": projection.task_id,
        "line_id": projection.line_id,
        "result_status": projection.result_status,
        "has_final_video": projection.has_final_video,
        "final_video_path": projection.final_video_path,
        "has_manifest": projection.has_manifest,
        "manifest_path": projection.manifest_path,
        "has_subtitles": projection.has_subtitles,
        "subtitles_path": projection.subtitles_path,
        "has_audio": projection.has_audio,
        "audio_path": projection.audio_path,
        "duration_seconds": projection.duration_seconds,
        "shot_count": projection.shot_count,
        "publish_ready_candidate": projection.publish_ready_candidate,
        "delivery_summary": projection.delivery_summary,
        "storage_scope": projection.storage_scope,
        "official_publish_ready": projection.official_publish_ready,
    }
    assert_no_result_projection_forbidden_tokens(payload)
    return payload


def assert_no_result_projection_forbidden_tokens(payload: object) -> None:
    """Reject provider/artifact/publish leakage in keys or string values."""
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        hits: List[str] = [tok for tok in FORBIDDEN_PROJECTION_TOKENS if tok in keys_blob]
        if hits:
            raise ResultProjectionError(f"result projection has forbidden keys: {hits}")
    blob = str(payload).lower()
    value_hits: List[str] = [tok for tok in FORBIDDEN_PROJECTION_TOKENS if tok in blob]
    if value_hits:
        raise ResultProjectionError(
            f"result projection leaks forbidden tokens: {value_hits}"
        )


def projection_error_from_record_error(exc: ResultRecordError) -> ResultProjectionError:
    """Translate a record validation error without importing UI/runtime layers."""
    return ResultProjectionError(str(exc))
