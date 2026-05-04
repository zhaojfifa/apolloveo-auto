"""Digital Anchor publish-feedback closure operator API
(Operator Capability Recovery, PR-4).

Surfaces the contract-frozen Phase D.1 write-back primitives so Digital
Anchor operators can complete role / speaker / publish feedback through
the contract-backed path. Mirrors the Matrix Script PR-3 closure router
shape, adapted for the role + segment per-row scope.
"""
from __future__ import annotations

from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from gateway.app.deps import get_task_repository
from gateway.app.services.digital_anchor.closure_binding import (
    ClosureValidationError,
    get_closure_view_for_task,
    get_or_create_for_task,
    write_publish_closure_for_task,
    write_role_feedback_for_task,
    write_segment_feedback_for_task,
)
from gateway.ports.task_repository import ITaskRepository

api_router = APIRouter(
    prefix="/api/digital-anchor/closures",
    tags=["digital-anchor-closure"],
)


_FORBIDDEN_PAYLOAD_KEY_FRAGMENTS = (
    "vendor",
    "model_id",
    "provider",
    "engine",
)


def _scrub_forbidden_keys(payload: Any, *, path: str = "") -> None:
    """Reject vendor/model/provider/engine identifiers in event payloads."""
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


def _ensure_digital_anchor(task: Mapping[str, Any]) -> None:
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "digital_anchor":
            return
    raise HTTPException(
        status_code=400,
        detail="closure_only_available_for_digital_anchor_tasks",
    )


@api_router.get("/{task_id}")
def get_closure_api(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    task = _resolve_task(repo, task_id)
    _ensure_digital_anchor(task)
    try:
        closure = get_or_create_for_task(task)
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(closure)


@api_router.get("/{task_id}/peek")
def peek_closure_api(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    task = _resolve_task(repo, task_id)
    _ensure_digital_anchor(task)
    closure = get_closure_view_for_task(task_id)
    return JSONResponse({"closure": closure})


async def _read_json(request: Request) -> Mapping[str, Any]:
    try:
        body = await request.json()
    except Exception as exc:  # pragma: no cover - parser-specific
        raise HTTPException(status_code=400, detail=f"invalid_json:{exc}")
    if not isinstance(body, Mapping):
        raise HTTPException(status_code=400, detail="event_must_be_object")
    _scrub_forbidden_keys(body)
    return body


@api_router.post("/{task_id}/role-feedback")
async def post_role_feedback_api(
    task_id: str,
    request: Request,
    repo: ITaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    """Append a role-level feedback row + closure record."""
    task = _resolve_task(repo, task_id)
    _ensure_digital_anchor(task)
    body = await _read_json(request)
    try:
        result = write_role_feedback_for_task(
            task,
            role_id=body.get("role_id", ""),
            role_feedback_kind=body.get("role_feedback_kind", ""),
            role_feedback_note=body.get("role_feedback_note"),
            recorded_by=body.get("recorded_by", "operator"),
            recorded_at=body.get("recorded_at"),
        )
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(result, status_code=201)


@api_router.post("/{task_id}/segment-feedback")
async def post_segment_feedback_api(
    task_id: str,
    request: Request,
    repo: ITaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    """Append a segment-level feedback row + closure record."""
    task = _resolve_task(repo, task_id)
    _ensure_digital_anchor(task)
    body = await _read_json(request)
    try:
        result = write_segment_feedback_for_task(
            task,
            segment_id=body.get("segment_id", ""),
            segment_feedback_kind=body.get("segment_feedback_kind", ""),
            audio_feedback_note=body.get("audio_feedback_note"),
            lip_sync_feedback_note=body.get("lip_sync_feedback_note"),
            subtitle_feedback_note=body.get("subtitle_feedback_note"),
            recorded_by=body.get("recorded_by", "operator"),
            recorded_at=body.get("recorded_at"),
        )
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(result, status_code=201)


@api_router.post("/{task_id}/publish-closure")
async def post_publish_closure_api(
    task_id: str,
    request: Request,
    repo: ITaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    """Apply scoped publish closure fields + append one closure record."""
    task = _resolve_task(repo, task_id)
    _ensure_digital_anchor(task)
    body = await _read_json(request)
    try:
        result = write_publish_closure_for_task(
            task,
            publish_status=body.get("publish_status", ""),
            publish_url=body.get("publish_url"),
            channel_metrics=body.get("channel_metrics"),
            operator_publish_notes=body.get("operator_publish_notes"),
            role_ids=body.get("role_ids"),
            segment_ids=body.get("segment_ids"),
            recorded_by=body.get("recorded_by", "operator"),
            record_kind=body.get("record_kind", "publish_callback"),
            recorded_at=body.get("recorded_at"),
        )
    except ClosureValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(result, status_code=201)


__all__ = ["api_router"]
