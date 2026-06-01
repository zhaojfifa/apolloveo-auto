"""Matrix Script minimal-result internal trigger route (PR-12R).

A controlled, internal backend action that turns an existing Matrix Script
task into a real LOCAL minimal result (``final.mp4`` + manifest under a local
workspace dir) and returns the read-only surface payload.

This is the "service can run" → "system can trigger" bridge. It is NOT a public
operator button, NOT official delivery, NOT a publish gate.

Discipline (PR-12R approval):
- Matrix-Script-scoped only; non-matrix_script tasks return 4xx.
- Reads the task only — NO task-repository mutation, NO publish-state change.
- NO Akool live API / adapter usage; NO webhook / polling.
- NO ``artifact_storage`` / R2 write — output goes to a local workspace dir.
- Response carries the safe surface dict only: ``official_publish_ready`` is
  always ``false``; NO provider URL / publish URL / artifact key.
- NO UI / template change; NO Hot Follow / Digital Anchor change.
- FFmpeg absence → HTTP 503 (capability unavailable). A fake ``final.mp4`` is
  never fabricated.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from gateway.app.config import get_settings
from gateway.app.deps import get_task_repository
from gateway.app.services.matrix_script.minimal_result_command import (
    MinimalResultCommandError,
    run_minimal_result_command,
)
from gateway.app.services.matrix_script.minimal_result_surface import (
    assert_no_result_surface_forbidden_tokens,
    minimal_result_surface_view_to_dict,
)
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
)
from gateway.ports.task_repository import ITaskRepository

api_router = APIRouter(
    prefix="/api/matrix-script",
    tags=["matrix-script-minimal-result"],
)


def resolve_minimal_result_output_dir(task_id: str) -> str:
    """Local workspace output dir for a task's minimal result.

    Under the existing ``workspace_root`` setting — never R2 / artifact storage.
    Tests monkeypatch this to an isolated temp dir.
    """
    base = get_settings().workspace_root
    return os.path.join(base, "artifacts", "matrix_script_minimal", task_id)


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
        detail="minimal_result_only_available_for_matrix_script_tasks",
    )


@api_router.post("/{task_id}/minimal-result")
def post_minimal_result(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    """Trigger the controlled local minimal-result command for a MS task.

    Returns the read-only surface payload (``has_result`` / local
    ``final_video_path`` / ``storage_scope=local_workspace`` /
    ``official_publish_ready=false`` / operator note). Reads the task only —
    no publish-state or repository mutation.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    output_dir = resolve_minimal_result_output_dir(task_id)
    try:
        view = run_minimal_result_command(task, output_dir, requested_by="internal")
    except MinimalResultCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FFmpegUnavailableError:
        # Capability genuinely unavailable in this environment — never a fake.
        raise HTTPException(
            status_code=503, detail="minimal_result_generation_unavailable"
        )
    payload = minimal_result_surface_view_to_dict(view)
    # Defense-in-depth: never emit a provider/publish/artifact-truth token.
    assert_no_result_surface_forbidden_tokens(payload)
    return JSONResponse(payload)
