"""Matrix Script Tomato Real Result route (PR-A).

Controlled internal action that runs the fixed tomato case
《海边与圣女果的盛夏约定》 through the controlled real-result path: real local
asset pack → image→motion shots with burned captions → Azure TTS (only if env)
or honest silent fallback → real final.mp4 → artifact staging → a staged
delivery candidate gated by the operator acceptance gate (L3).

Discipline: Matrix-Script-scoped (4xx otherwise); reads the task only (no repo /
publish-state mutation); ``official_publish_ready=false``; no provider URL /
Akool id / model / credit / publish_url / publish_status in the response. ffmpeg
absence → HTTP 503 (no fake final.mp4). The default sink wraps the existing
``artifact_storage`` abstraction — this module does NOT modify it.
"""
from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from gateway.app.config import get_settings
from gateway.app.deps import get_task_repository
from gateway.app.routers.matrix_script_real_trial import ArtifactStorageStagingSink
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    assert_no_delivery_view_forbidden_tokens,
)
from gateway.app.services.matrix_script.simple_scene_renderer import FFmpegUnavailableError
from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
    TomatoRealResultError,
    run_tomato_real_result,
    tomato_result_to_payload,
)
from gateway.ports.task_repository import ITaskRepository

api_router = APIRouter(prefix="/api/matrix-script", tags=["matrix-script-tomato-real-result"])


def resolve_tomato_output_dir(task_id: str) -> str:
    base = get_settings().workspace_root
    return os.path.join(base, "artifacts", "matrix_script_tomato_real_result", task_id)


def build_tomato_sink(task_id: str) -> Any:
    """Build the staging sink (tests monkeypatch this to an in-memory fake)."""
    return ArtifactStorageStagingSink(task_id)


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
    raise HTTPException(status_code=400, detail="tomato_real_result_only_available_for_matrix_script_tasks")


@api_router.post("/{task_id}/tomato-real-result")
def post_tomato_real_result(
    task_id: str,
    active_shot: Optional[str] = None,
    repo: ITaskRepository = Depends(get_task_repository),
) -> JSONResponse:
    """Run the controlled tomato real-result path; return a gated staged candidate.

    ``active_shot`` (thin request parse only) designates the Current Shot Panel active
    shot as the provider-target for the one controlled script-directed generation; the
    service safe-defaults to the designated product shot when absent. No business logic
    here — the value is passed straight through to the service.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    output_dir = resolve_tomato_output_dir(task_id)
    sink = build_tomato_sink(task_id)
    try:
        result = run_tomato_real_result(task, output_dir, sink=sink, active_shot_id=active_shot)
    except TomatoRealResultError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FFmpegUnavailableError:
        raise HTTPException(status_code=503, detail="tomato_real_result_generation_unavailable")
    payload = tomato_result_to_payload(result)
    # Operator-accessible preview link: a dedicated gateway endpoint that streams
    # the staged local final.mp4 — browser-openable regardless of storage backend.
    # Internal staged preview, NOT a publish/provider/download URL.
    payload["preview_url"] = f"/api/matrix-script/{task_id}/tomato-real-result/preview/final.mp4"
    assert_no_delivery_view_forbidden_tokens(payload)
    return JSONResponse(payload)


@api_router.get("/{task_id}/tomato-real-result/preview/final.mp4")
def get_tomato_preview(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
):
    """Stream the staged local tomato final.mp4 for operator preview (not publish)."""
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    local_final = os.path.join(resolve_tomato_output_dir(task_id), "final", "final.mp4")
    if os.path.exists(local_final) and os.path.getsize(local_final) > 0:
        return FileResponse(path=local_final, media_type="video/mp4", filename="final.mp4")
    try:
        from gateway.app.services.artifact_storage import get_download_url

        url = get_download_url(task_id, "matrix_script/%s/final/final.mp4" % task_id)
        if isinstance(url, str) and url:
            return RedirectResponse(url=url, status_code=302)
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="preview_not_available")
