"""Matrix Script minimal result — Workbench read-only block (PR-9R).

The architecture-to-operator-result bridge: turns the PR-8R
``MatrixScriptMinimalResultSurfaceView`` into a closed, read-only block payload
the Workbench template renders as a small "本地最小成片" panel. It also exposes a
wiring adapter that reads an optional, pre-computed surface dict carried on the
task config (read-only) — so no generation runs on the workbench path.

This is NOT official delivery, NOT a publish gate, NOT artifact truth.
``official_publish_ready`` is always ``False``; when there is no local result
the block is ``{"has_result": False}`` and the template renders nothing.

Hard boundary (PR-9R approval):
- NO Akool / provider / adapter import; NO provider URL / download URL.
- NO ``artifact_storage`` / R2 write or truth field; local paths only.
- NO official publish gate; NO ``publish_url`` / ``publish_status``.
- NO Delivery Center runtime change; NO Hot Follow / Digital Anchor change;
  NO schema / packet / contract change. Workbench gets a small read-only block
  only — no layout redesign.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from gateway.app.services.matrix_script.minimal_result_surface import (
    FINAL_VIDEO_LABEL,
    LINE_ID,
    OFFICIAL_PUBLISH_READY_FALSE,
    OPERATOR_NOTE,
    STORAGE_SCOPE_LOCAL,
    MatrixScriptMinimalResultSurfaceView,
    minimal_result_surface_view_to_dict,
)

# Reuse the surface-layer forbidden-token discipline.
from gateway.app.services.matrix_script.minimal_result_surface import (
    FORBIDDEN_TOKENS as _SURFACE_FORBIDDEN_TOKENS,
)

WORKBENCH_BLOCK_FORBIDDEN_TOKENS = _SURFACE_FORBIDDEN_TOKENS

# Closed key set of the workbench block (read-only).
_BLOCK_KEYS = (
    "has_result",
    "line_id",
    "result_status",
    "final_video_label",
    "final_video_path",
    "manifest_path",
    "duration_seconds",
    "shot_count",
    "storage_scope",
    "official_publish_ready",
    "operator_note",
)


class WorkbenchResultBlockError(ValueError):
    """Raised on an invalid workbench-block conversion."""


def _empty_block() -> Dict[str, object]:
    return {"has_result": False}


def assert_no_workbench_block_forbidden_tokens(payload: object) -> None:
    """Raise if a forbidden provider/storage/publish token leaks (keys or values)."""
    if isinstance(payload, dict):
        keys_blob = " ".join(str(k).lower() for k in payload.keys())
        key_hits: List[str] = [t for t in WORKBENCH_BLOCK_FORBIDDEN_TOKENS if t in keys_blob]
        if key_hits:
            raise WorkbenchResultBlockError(f"workbench block has forbidden keys: {key_hits}")
    value_hits: List[str] = [
        t for t in WORKBENCH_BLOCK_FORBIDDEN_TOKENS if t in str(payload).lower()
    ]
    if value_hits:
        raise WorkbenchResultBlockError(f"workbench block leaks forbidden tokens: {value_hits}")


def _block_from_surface_dict(surface: Mapping[str, Any]) -> Dict[str, object]:
    """Build the read-only block from a surface-view dict. Pure."""
    if not surface.get("has_result"):
        return _empty_block()
    block: Dict[str, object] = {
        "has_result": True,
        "line_id": LINE_ID,
        "result_status": surface.get("result_status", "generated"),
        "final_video_label": surface.get("final_video_label", FINAL_VIDEO_LABEL),
        "final_video_path": surface.get("final_video_path", ""),
        "manifest_path": surface.get("manifest_path", ""),
        "duration_seconds": float(surface.get("duration_seconds", 0.0) or 0.0),
        "shot_count": int(surface.get("shot_count", 0) or 0),
        "storage_scope": surface.get("storage_scope", STORAGE_SCOPE_LOCAL),
        # Hard-pin: the workbench block can never assert official publish readiness.
        "official_publish_ready": OFFICIAL_PUBLISH_READY_FALSE,
        "operator_note": surface.get("operator_note", OPERATOR_NOTE),
    }
    assert_no_workbench_block_forbidden_tokens(block)
    return block


def minimal_result_surface_view_to_workbench_block(
    view: MatrixScriptMinimalResultSurfaceView,
) -> Dict[str, object]:
    """Acceptance #1: a Workbench/service-view can receive a surface view.

    Returns a closed read-only block payload for template consumption.
    """
    if not isinstance(view, MatrixScriptMinimalResultSurfaceView):
        raise WorkbenchResultBlockError(
            "view must be a MatrixScriptMinimalResultSurfaceView"
        )
    return _block_from_surface_dict(minimal_result_surface_view_to_dict(view))


def derive_matrix_script_minimal_result_workbench_block(
    task: Any,
) -> Dict[str, object]:
    """Wiring adapter: read an optional pre-computed surface dict off the task.

    Read-only — NO generation, NO ffmpeg, NO storage. The surface dict (as
    produced by ``minimal_result_surface_view_to_dict``) may be carried at
    ``task['config']['matrix_script_minimal_result']``. Absent / malformed →
    ``{"has_result": False}`` so the template renders nothing and existing
    behavior is unchanged.
    """
    if not isinstance(task, Mapping):
        return _empty_block()
    config = task.get("config")
    surface = config.get("matrix_script_minimal_result") if isinstance(config, Mapping) else None
    if not isinstance(surface, Mapping):
        return _empty_block()
    try:
        return _block_from_surface_dict(surface)
    except WorkbenchResultBlockError:
        # Never break the workbench on a malformed/forbidden surface payload.
        return _empty_block()
