"""Matrix Script minimal result surface view (PR-8R).

A read-only, operator-facing surface view of the minimal local result. It sits
in front of any Workbench / Delivery presenter as a pre-delivery read model:
"a local minimal final video exists; it is NOT yet in official delivery
storage and NOT publish-ready".

This is NOT a delivery contract, NOT a publish gate, and NOT artifact truth.
``official_publish_ready`` is always ``False``.

Pure conversion (no I/O, no ffmpeg). Consumes the PR-7R operator projection.

Hard boundary (PR-8R approval):
- NO Akool / provider / adapter import; NO provider URL / download URL.
- NO ``artifact_storage`` / R2 write or truth field; local paths only.
- NO official publish gate; NO ``publish_url`` / ``publish_status``.
- NO template change; NO router change; NO Delivery Center runtime change;
  NO schema / packet / contract change; NO Hot Follow / Digital Anchor change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from gateway.app.services.matrix_script.minimal_result_projection import (
    MatrixScriptOperatorResultProjection,
    minimal_result_record_to_operator_projection,
)
from gateway.app.services.matrix_script.minimal_result_record import (
    MatrixScriptMinimalResultRecord,
)

LINE_ID = "matrix_script"
OFFICIAL_PUBLISH_READY_FALSE = False
STORAGE_SCOPE_LOCAL = "local_workspace"

FINAL_VIDEO_LABEL = "本地最小成片"
OPERATOR_NOTE = "已生成本地最小成片，尚未进入正式交付存储"

# Forbidden tokens (provider / artifact-storage / publish leakage). Local
# ``*_path`` keys are allowed.
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


class ResultSurfaceError(ValueError):
    """Raised on an invalid surface-view conversion."""


@dataclass(frozen=True)
class MatrixScriptMinimalResultSurfaceView:
    """Read-only minimal result surface view (pre-delivery, local-scoped)."""

    task_id: Any
    line_id: str
    has_result: bool
    result_status: str
    final_video_label: str
    final_video_path: str
    manifest_path: str
    duration_seconds: float
    shot_count: int
    storage_scope: str
    official_publish_ready: bool
    operator_note: str


def assert_no_result_surface_forbidden_tokens(payload: object) -> None:
    """Raise ``ResultSurfaceError`` if a forbidden token leaks (keys or values)."""
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        key_hits: List[str] = [tok for tok in FORBIDDEN_TOKENS if tok in keys_blob]
        if key_hits:
            raise ResultSurfaceError(f"surface view has forbidden keys: {key_hits}")
    value_hits: List[str] = [tok for tok in FORBIDDEN_TOKENS if tok in str(payload).lower()]
    if value_hits:
        raise ResultSurfaceError(f"surface view leaks forbidden tokens: {value_hits}")


def operator_projection_to_surface_view(
    projection: MatrixScriptOperatorResultProjection,
) -> MatrixScriptMinimalResultSurfaceView:
    """Pure conversion: PR-7R operator projection -> read-only surface view."""
    if not isinstance(projection, MatrixScriptOperatorResultProjection):
        raise ResultSurfaceError("projection must be a MatrixScriptOperatorResultProjection")
    view = MatrixScriptMinimalResultSurfaceView(
        task_id=projection.task_id,
        line_id=LINE_ID,
        has_result=bool(projection.has_final_video),
        result_status=projection.result_status,
        final_video_label=FINAL_VIDEO_LABEL,
        final_video_path=projection.final_video_path,
        manifest_path=projection.manifest_path,
        duration_seconds=float(projection.duration_seconds),
        shot_count=int(projection.shot_count),
        storage_scope=STORAGE_SCOPE_LOCAL,
        official_publish_ready=OFFICIAL_PUBLISH_READY_FALSE,
        operator_note=OPERATOR_NOTE,
    )
    assert_no_result_surface_forbidden_tokens(minimal_result_surface_view_to_dict(view))
    return view


def minimal_result_record_to_surface_view(
    record: MatrixScriptMinimalResultRecord,
) -> MatrixScriptMinimalResultSurfaceView:
    """Convenience: internal record -> operator projection -> surface view."""
    projection = minimal_result_record_to_operator_projection(record)
    return operator_projection_to_surface_view(projection)


def minimal_result_surface_view_to_dict(
    view: MatrixScriptMinimalResultSurfaceView,
) -> Dict[str, object]:
    """Pure serialization (closed key set; local paths only)."""
    return {
        "task_id": view.task_id,
        "line_id": view.line_id,
        "has_result": view.has_result,
        "result_status": view.result_status,
        "final_video_label": view.final_video_label,
        "final_video_path": view.final_video_path,
        "manifest_path": view.manifest_path,
        "duration_seconds": view.duration_seconds,
        "shot_count": view.shot_count,
        "storage_scope": view.storage_scope,
        "official_publish_ready": view.official_publish_ready,
        "operator_note": view.operator_note,
    }
