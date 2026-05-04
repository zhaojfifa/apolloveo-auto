"""Matrix Script publish-feedback closure operator API
(Operator Capability Recovery, PR-3).

Surfaces the contract-frozen
``matrix_script_publish_feedback_closure_v1`` shape implemented by
:mod:`gateway.app.services.matrix_script.publish_feedback_closure`
through a narrow JSON capability so Matrix Script operators can
complete the variation → workbench → delivery → feedback loop.

Discipline:

- Matrix-Script-scoped only; non-matrix_script tasks return 4xx.
- No packet mutation; closure is a separate ownership zone per
  ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
  §"Boundary statement".
- No provider / model / vendor / engine identifiers in input or
  output; the contract's closed enums are the only acceptable values.
- No durable persistence; in-process per Recovery red lines.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from gateway.app.deps import get_task_repository
from gateway.app.services.matrix_script.closure_binding import (
    ClosureValidationError,
    apply_event_for_task,
    get_closure_view_for_task,
    get_or_create_for_task,
)
from gateway.ports.task_repository import ITaskRepository

api_router = APIRouter(
    prefix="/api/matrix-script/closures",
    tags=["matrix-script-closure"],
)


_FORBIDDEN_PAYLOAD_KEY_FRAGMENTS = (
    "vendor",
    "model_id",
    "provider",
    "engine",
)


def _scrub_forbidden_keys(payload: Any, *, path: str = "") -> None:
    """Reject vendor/model/provider/engine identifiers in event payloads.

    Operator-visible payloads must not carry donor / runtime identifiers
    per the operator-visible surface red line. Walks the payload depth-
    first and raises ``HTTPException(400)`` on the first hit.
    """
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            normalized = str(key).lower()
            for fragment in _FORBIDDEN_PAYLOAD_KEY_FRAGMENTS:
                if fragment in normalized:
                    raise HTTPException(
                        status_code=400,
                        detail=f"forbidden_payload_key:{path or ''}{key}",
                    )
            _scrub_forbidden_keys(value, path=f"{path}{key}.")
    elif isinstance(payload, (list, tuple)):
        for index, item in enumerate(payload):
            _scrub_forbidden_keys(item, path=f"{path}[{index}].")


def _resolve_task(repo: ITaskRepository, task_id: str) -> Mapping[str, Any]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    return task


def _ensure_matrix_script(task: Mapping[str, Any]) -> None:
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return
    raise HTTPException(
        status_code=400,
        detail="closure_only_available_for_matrix_script_tasks",
    )


@api_router.get("/{task_id}")
def get_closure_api(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    """Return the closure view for a Matrix Script task.

    Lazily creates the closure on first call so the operator surface can
    render variation_feedback rows without a separate bootstrap call.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    try:
        closure = get_or_create_for_task(task)
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(closure)


@api_router.post("/{task_id}/events")
async def post_event_api(
    task_id: str,
    request: Request,
    repo: ITaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    """Apply one closure event for a Matrix Script task.

    Body shape (contract-aligned, JSON only)::

        {
          "event_kind": "operator_publish" | "operator_retract" |
                        "operator_note" | "platform_callback" |
                        "metrics_snapshot",
          "variation_id": "<cell_id>",
          "actor_kind": "operator" | "platform" | "system",  # optional
          "recorded_at": "<ISO-8601>",                       # optional
          "payload_ref": "<opaque>",                          # optional
          "payload": { ... }
        }

    Returns ``{"event_id", "closure"}`` on success per the closure
    contract. Contract violations (unknown enum, wrong actor for kind,
    forbidden payload keys, etc.) return ``HTTP 400`` with an
    error-code-shaped detail.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    try:
        body = await request.json()
    except Exception as exc:  # pragma: no cover - parser-specific
        raise HTTPException(status_code=400, detail=f"invalid_json:{exc}")
    if not isinstance(body, Mapping):
        raise HTTPException(status_code=400, detail="event_must_be_object")
    _scrub_forbidden_keys(body.get("payload"))
    try:
        result = apply_event_for_task(task, body)
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(result, status_code=201)


@api_router.get("/{task_id}/peek")
def peek_closure_api(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    """Read-only peek that does not auto-create a closure.

    Returns ``{"closure": null}`` until the first event or first
    :func:`get_closure_api` call has materialized the closure. Useful
    for surfaces that want to render ``not_published`` placeholder UX.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    closure = get_closure_view_for_task(task_id)
    return JSONResponse({"closure": closure})


__all__ = ["api_router"]
