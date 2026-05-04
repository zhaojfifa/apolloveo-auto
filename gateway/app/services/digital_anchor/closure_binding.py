"""Digital Anchor publish-feedback closure binding (Recovery PR-4).

Process-wide binding layer between a Digital Anchor ``task_id`` and the
contract-frozen ``digital_anchor_publish_feedback_closure_v1`` surface
implemented by
:mod:`gateway.app.services.digital_anchor.publish_feedback_closure`.

Mirrors the Matrix Script PR-3 closure binding pattern. The closure
shape and write-back primitives are unchanged from the Phase D.0 / D.1
contracts; this module only owns lazy creation + per-task lookup so the
publish-hub presenter can surface the closure to operators.

Discipline:
- Digital-Anchor-only at the type boundary; non-digital_anchor tasks
  raise ``ClosureValidationError``.
- Closure is a separate ownership zone — the binding NEVER mutates
  packet truth, role/speaker workbench projection, or delivery binding.
- No durable persistence; in-process per Recovery red lines.
- No vendor / model / provider / engine identifiers in any payload.
"""
from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Mapping, Optional

from .delivery_binding import project_delivery_binding
from .publish_feedback_closure import (
    ClosureValidationError,
    InMemoryClosureStore,
)


DIGITAL_ANCHOR_LINE_ID = "digital_anchor"

_STORE = InMemoryClosureStore()
_TASK_TO_CLOSURE: Dict[str, str] = {}
_LOCK = Lock()


def _packet_view(task: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(task, Mapping):
        raise ClosureValidationError("task must be a mapping")
    packet = task.get("packet")
    if isinstance(packet, Mapping):
        return packet
    if task.get("line_id") == DIGITAL_ANCHOR_LINE_ID and task.get("line_specific_refs"):
        return task
    raise ClosureValidationError(
        "task does not carry a digital_anchor packet view (missing packet "
        "envelope and inline line_specific_refs)"
    )


def _task_id(task: Mapping[str, Any]) -> str:
    raw = task.get("task_id") or task.get("id") if isinstance(task, Mapping) else None
    if not isinstance(raw, str) or not raw:
        raise ClosureValidationError("task.task_id is required")
    return raw


def _is_digital_anchor(task: Mapping[str, Any]) -> bool:
    if not isinstance(task, Mapping):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == DIGITAL_ANCHOR_LINE_ID:
            return True
    return False


def get_or_create_for_task(task: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a contract-shaped closure view for the given Digital Anchor task.

    On first access for the task, projects the delivery binding from the
    packet, creates the closure, and records the ``task_id → closure_id``
    binding; subsequent calls return the persisted closure.
    """
    if not _is_digital_anchor(task):
        raise ClosureValidationError(
            "publish-feedback closure is only available for digital_anchor tasks"
        )
    task_id = _task_id(task)
    with _LOCK:
        existing = _TASK_TO_CLOSURE.get(task_id)
        if existing is not None:
            return _STORE.get(existing)
        packet = _packet_view(task)
        delivery_projection = project_delivery_binding(packet)
        closure = _STORE.create(
            packet,
            delivery_projection,
            closure_id=f"closure_{task_id}",
        )
        _TASK_TO_CLOSURE[task_id] = closure["closure_id"]
        return closure


def get_closure_view_for_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return the persisted closure view, or ``None`` if no closure exists yet."""
    if not isinstance(task_id, str) or not task_id:
        return None
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE.get(task_id)
        if closure_id is None:
            return None
        return _STORE.get(closure_id)


def _packet_for_task_id(task_id: str, task_loader) -> Mapping[str, Any]:
    """Resolve a packet for a previously-bound task_id.

    Used by event-apply paths that take a bare task_id; callers must
    pass a ``task_loader`` callable that returns the task mapping.
    """
    task = task_loader(task_id)
    if not isinstance(task, Mapping):
        raise ClosureValidationError(f"unknown task_id: {task_id!r}")
    return _packet_view(task)


def write_role_feedback_for_task(
    task: Mapping[str, Any],
    *,
    role_id: str,
    role_feedback_kind: str,
    role_feedback_note: Optional[str] = None,
    recorded_by: str = "operator",
    recorded_at: Optional[str] = None,
) -> Dict[str, Any]:
    get_or_create_for_task(task)
    task_id = _task_id(task)
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE[task_id]
    return _STORE.write_role_feedback(
        closure_id,
        _packet_view(task),
        role_id=role_id,
        role_feedback_kind=role_feedback_kind,
        role_feedback_note=role_feedback_note,
        recorded_by=recorded_by,
        recorded_at=recorded_at,
    )


def write_segment_feedback_for_task(
    task: Mapping[str, Any],
    *,
    segment_id: str,
    segment_feedback_kind: str,
    audio_feedback_note: Optional[str] = None,
    lip_sync_feedback_note: Optional[str] = None,
    subtitle_feedback_note: Optional[str] = None,
    recorded_by: str = "operator",
    recorded_at: Optional[str] = None,
) -> Dict[str, Any]:
    get_or_create_for_task(task)
    task_id = _task_id(task)
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE[task_id]
    return _STORE.write_segment_feedback(
        closure_id,
        _packet_view(task),
        segment_id=segment_id,
        segment_feedback_kind=segment_feedback_kind,
        audio_feedback_note=audio_feedback_note,
        lip_sync_feedback_note=lip_sync_feedback_note,
        subtitle_feedback_note=subtitle_feedback_note,
        recorded_by=recorded_by,
        recorded_at=recorded_at,
    )


def write_publish_closure_for_task(
    task: Mapping[str, Any],
    *,
    publish_status: str,
    publish_url: Optional[str] = None,
    channel_metrics: Optional[Mapping[str, Any]] = None,
    operator_publish_notes: Optional[str] = None,
    role_ids: Optional[list[str]] = None,
    segment_ids: Optional[list[str]] = None,
    recorded_by: str = "operator",
    record_kind: str = "publish_callback",
    recorded_at: Optional[str] = None,
) -> Dict[str, Any]:
    get_or_create_for_task(task)
    task_id = _task_id(task)
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE[task_id]
    return _STORE.write_publish_closure(
        closure_id,
        _packet_view(task),
        publish_status=publish_status,
        publish_url=publish_url,
        channel_metrics=channel_metrics,
        operator_publish_notes=operator_publish_notes,
        role_ids=role_ids,
        segment_ids=segment_ids,
        recorded_by=recorded_by,
        record_kind=record_kind,
        recorded_at=recorded_at,
    )


def reset_for_tests() -> None:
    """Wipe the in-process store. Test-only seam — not exported in __all__."""
    with _LOCK:
        _TASK_TO_CLOSURE.clear()
        _STORE._closures.clear()  # type: ignore[attr-defined]


__all__ = [
    "ClosureValidationError",
    "DIGITAL_ANCHOR_LINE_ID",
    "get_closure_view_for_task",
    "get_or_create_for_task",
    "write_publish_closure_for_task",
    "write_role_feedback_for_task",
    "write_segment_feedback_for_task",
]
