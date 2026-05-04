"""Matrix Script publish-feedback closure binding (Recovery PR-3).

Process-wide binding layer between a Matrix Script ``task_id`` and the
contract-frozen ``matrix_script_publish_feedback_closure_v1`` surface
implemented by :mod:`gateway.app.services.matrix_script.publish_feedback_closure`.

Why this exists
---------------
The Phase D.0 contract froze the closure shape and the Phase D.1 service
landed the in-process store, but no caller instantiated the store. The
publish-hub presenter passes ``publish_feedback_closure=None`` so the
delivery surface's ``publish_status_mirror`` is permanently empty for
every Matrix Script task. The Operator Capability Recovery PR-3 mission
requires the publish feedback closure path to be surfaced through the
contract-backed path so operators can complete the
variation → workbench → delivery → feedback loop.

This module is intentionally narrow:

- One process-wide :class:`InMemoryClosureStore` (``_STORE``).
- One ``task_id → closure_id`` map (``_TASK_TO_CLOSURE``) so a task
  always resolves to the same closure.
- ``get_or_create_for_task(task)`` lazily creates a closure from the
  task's packet on first access.
- ``apply_event_for_task(task_id, event)`` and ``get_closure_view_for_task(task_id)``
  are thin pass-throughs over the store.

Hard discipline
---------------
- No new closure shape; the contract-frozen shape from
  :mod:`publish_feedback_closure` is reused verbatim.
- No packet mutation: the closure is a separate ownership zone (per
  ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
  §"Boundary statement").
- Only Matrix Script tasks may obtain a closure; non-matrix_script tasks
  raise :class:`ClosureValidationError`.
- No durable persistence; the store is in-process per the Recovery red
  lines (PR-3 minimum operator capability, no DB / migration).
- No provider / model / vendor / engine identifier ever flows through
  this module.
"""
from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Mapping, Optional

from .publish_feedback_closure import (
    ClosureValidationError,
    InMemoryClosureStore,
)

MATRIX_SCRIPT_LINE_ID = "matrix_script"

_STORE = InMemoryClosureStore()
_TASK_TO_CLOSURE: Dict[str, str] = {}
_LOCK = Lock()


def _packet_view(task: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the packet view that ``create_closure`` requires.

    The Matrix Script create-entry payload stores the packet under
    ``task["packet"]`` (see
    :mod:`gateway.app.services.matrix_script.create_entry`); some test /
    presenter code paths surface the packet inline. Either is honored.
    """
    if not isinstance(task, Mapping):
        raise ClosureValidationError("task must be a mapping")
    packet = task.get("packet")
    if isinstance(packet, Mapping):
        return packet
    if task.get("line_id") == MATRIX_SCRIPT_LINE_ID and task.get("line_specific_refs"):
        return task
    raise ClosureValidationError(
        "task does not carry a matrix_script packet view (missing packet "
        "envelope and inline line_specific_refs)"
    )


def _task_id(task: Mapping[str, Any]) -> str:
    raw = task.get("task_id") or task.get("id") if isinstance(task, Mapping) else None
    if not isinstance(raw, str) or not raw:
        raise ClosureValidationError("task.task_id is required")
    return raw


def _is_matrix_script(task: Mapping[str, Any]) -> bool:
    if not isinstance(task, Mapping):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == MATRIX_SCRIPT_LINE_ID:
            return True
    return False


def get_or_create_for_task(task: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a contract-shaped closure view for the given Matrix Script task.

    On first access for the task, creates the closure from the packet and
    records the ``task_id → closure_id`` binding; subsequent calls return
    the persisted closure. Non-matrix_script tasks raise
    :class:`ClosureValidationError`.
    """
    if not _is_matrix_script(task):
        raise ClosureValidationError(
            "publish-feedback closure is only available for matrix_script tasks"
        )
    task_id = _task_id(task)
    with _LOCK:
        existing = _TASK_TO_CLOSURE.get(task_id)
        if existing is not None:
            return _STORE.get(existing)
        closure = _STORE.create(_packet_view(task), closure_id=f"closure_{task_id}")
        _TASK_TO_CLOSURE[task_id] = closure["closure_id"]
        return closure


def get_closure_view_for_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Return the persisted closure view, or ``None`` when the task has no
    closure yet (i.e. nothing has triggered :func:`get_or_create_for_task`).

    Read-only — never creates a closure on its own. Useful for presenter
    paths that should display ``not_published`` until an event is fired.
    """
    if not isinstance(task_id, str) or not task_id:
        return None
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE.get(task_id)
        if closure_id is None:
            return None
        return _STORE.get(closure_id)


def apply_event_for_task(
    task_or_task_id: Any, event: Mapping[str, Any]
) -> Dict[str, Any]:
    """Apply a closure event for a Matrix Script task.

    Accepts either the full task mapping (lazy-creating the closure on
    first event) or a bare ``task_id`` string for a closure that already
    exists. Returns ``{"event_id", "closure"}`` per
    :meth:`InMemoryClosureStore.apply`.
    """
    if isinstance(task_or_task_id, Mapping):
        task = task_or_task_id
        get_or_create_for_task(task)
        task_id = _task_id(task)
    elif isinstance(task_or_task_id, str) and task_or_task_id:
        task_id = task_or_task_id
    else:
        raise ClosureValidationError(
            "apply_event_for_task expects a task mapping or a task_id string"
        )
    with _LOCK:
        closure_id = _TASK_TO_CLOSURE.get(task_id)
    if closure_id is None:
        raise ClosureValidationError(
            f"no closure exists for task_id {task_id!r}; create one first"
        )
    return _STORE.apply(closure_id, event)


def reset_for_tests() -> None:
    """Wipe the in-process store. Test-only seam — not exported."""
    with _LOCK:
        _TASK_TO_CLOSURE.clear()
        _STORE._closures.clear()  # type: ignore[attr-defined]


__all__ = [
    "ClosureValidationError",
    "MATRIX_SCRIPT_LINE_ID",
    "apply_event_for_task",
    "get_closure_view_for_task",
    "get_or_create_for_task",
]
