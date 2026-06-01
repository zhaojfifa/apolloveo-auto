"""Matrix Script minimal-result Delivery Center read-only view (PR-14R).

Projects the local minimal result into a Delivery-Center-facing read-only
block. Explicitly NOT official delivery and NOT publishable: the local result
has not entered formal delivery storage and cannot be a published file.

Pure conversion (no I/O). Reads a pre-computed surface dict carried on the task
config (``task['config']['matrix_script_minimal_result']``) — read-only, no
generation, no task mutation. Absent → ``{"has_result": False}``.

Hard boundary (PR-14R): NO Akool / provider URL; NO ``artifact_storage`` / R2;
NO official publish gate / ``publish_url`` / ``publish_status`` /
``download_url`` / ``artifact_key`` / ``r2_key``; NO Delivery publish runtime;
NO schema / packet / contract change.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

LINE_ID = "matrix_script"
OFFICIAL_PUBLISH_READY_FALSE = False
STORAGE_SCOPE_LOCAL = "local_workspace"
FINAL_VIDEO_LABEL = "本地最小成片"
DELIVERY_NOTE = "该结果尚未进入正式交付存储，不能作为正式发布文件。"

FORBIDDEN_TOKENS = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor",
    "model_id", "credit", "provider_task_id", "artifact_key", "final_video_key",
    "r2_key", "publish_url", "publish_status",
)


class DeliveryViewError(ValueError):
    """Raised on an invalid delivery-view conversion."""


def _empty() -> Dict[str, object]:
    return {"has_result": False}


def assert_no_delivery_view_forbidden_tokens(payload: object) -> None:
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        key_hits: List[str] = [t for t in FORBIDDEN_TOKENS if t in keys_blob]
        if key_hits:
            raise DeliveryViewError(f"delivery view has forbidden keys: {key_hits}")
    value_hits: List[str] = [t for t in FORBIDDEN_TOKENS if t in str(payload).lower()]
    if value_hits:
        raise DeliveryViewError(f"delivery view leaks forbidden tokens: {value_hits}")


def _block_from_surface(surface: Mapping[str, Any]) -> Dict[str, object]:
    if not surface.get("has_result"):
        return _empty()
    block: Dict[str, object] = {
        "has_result": True,
        "line_id": LINE_ID,
        "final_video_label": surface.get("final_video_label", FINAL_VIDEO_LABEL),
        "result_status": surface.get("result_status", "generated"),
        "final_video_path": surface.get("final_video_path", ""),
        "duration_seconds": float(surface.get("duration_seconds", 0.0) or 0.0),
        "shot_count": int(surface.get("shot_count", 0) or 0),
        "storage_scope": surface.get("storage_scope", STORAGE_SCOPE_LOCAL),
        # Hard-pinned: a local result is never official-publish-ready here.
        "official_publish_ready": OFFICIAL_PUBLISH_READY_FALSE,
        "delivery_note": DELIVERY_NOTE,
    }
    assert_no_delivery_view_forbidden_tokens(block)
    return block


def minimal_result_surface_view_to_delivery_block(
    view: Any,
) -> Dict[str, object]:
    """Build the delivery block from a PR-8R surface view object."""
    from gateway.app.services.matrix_script.minimal_result_surface import (
        MatrixScriptMinimalResultSurfaceView,
        minimal_result_surface_view_to_dict,
    )

    if not isinstance(view, MatrixScriptMinimalResultSurfaceView):
        raise DeliveryViewError("view must be a MatrixScriptMinimalResultSurfaceView")
    return _block_from_surface(minimal_result_surface_view_to_dict(view))


def derive_matrix_script_minimal_result_delivery_block(task: Any) -> Dict[str, object]:
    """Read-only wiring adapter: surface dict on task config → delivery block.

    No generation, no I/O, no task mutation. Absent/malformed → empty block.
    """
    if not isinstance(task, Mapping):
        return _empty()
    config = task.get("config")
    surface = config.get("matrix_script_minimal_result") if isinstance(config, Mapping) else None
    if not isinstance(surface, Mapping):
        return _empty()
    try:
        return _block_from_surface(surface)
    except DeliveryViewError:
        return _empty()
