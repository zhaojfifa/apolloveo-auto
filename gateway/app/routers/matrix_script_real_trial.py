"""Matrix Script real operator trial route (PR-17R).

Controlled internal action that runs the real operator trial for a Matrix
Script task: optional Akool one-shot under the explicit gate, fallback scenes,
real final.mp4, artifact staging, and a Delivery staged-candidate payload.

Discipline: Matrix-Script-scoped (4xx otherwise); reads the task only (no repo
or publish-state mutation); `official_publish_ready=false`; no provider URL /
Akool task id / model / credit / publish_url / publish_status in the response.
FFmpeg absence → HTTP 503 (no fake final.mp4). Real generation stays gated:
with `MATRIX_SCRIPT_AKOOL_REAL` unset/false the trial uses fallback scenes only.
The default sink wraps the existing `artifact_storage` abstraction — this
module does NOT modify it.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from gateway.app.config import get_settings
from gateway.app.deps import get_task_repository
from gateway.app.services.matrix_script.akool_real_gate import assert_no_gate_forbidden_tokens
from gateway.app.services.matrix_script.real_trial_orchestrator import (
    RealTrialError,
    real_trial_result_to_payload,
    run_matrix_script_real_trial,
)
from gateway.app.services.matrix_script.simple_scene_renderer import FFmpegUnavailableError
from gateway.ports.task_repository import ITaskRepository

api_router = APIRouter(prefix="/api/matrix-script", tags=["matrix-script-real-trial"])


class ArtifactStorageStagingSink:
    """Production sink: stages a local file via the existing artifact_storage
    abstraction and returns an opaque artifact ref. No provider URL involved.
    """

    def __init__(self, task_id: str) -> None:
        self._task_id = task_id

    def put(self, local_path: str, artifact_name: str) -> str:
        from gateway.app.services.artifact_storage import upload_artifact

        upload_artifact(self._task_id, local_path, artifact_name)
        return f"artifact://{artifact_name}"


def resolve_real_trial_output_dir(task_id: str) -> str:
    base = get_settings().workspace_root
    return os.path.join(base, "artifacts", "matrix_script_real_trial", task_id)


def build_real_trial_sink(task_id: str) -> Any:
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
    raise HTTPException(status_code=400, detail="real_trial_only_available_for_matrix_script_tasks")


@api_router.post("/{task_id}/real-trial")
def post_real_trial(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
) -> JSONResponse:
    """Run the real operator trial; return a Delivery staged-candidate payload."""
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    output_dir = resolve_real_trial_output_dir(task_id)
    sink = build_real_trial_sink(task_id)
    try:
        result = run_matrix_script_real_trial(task, output_dir, sink=sink)
    except RealTrialError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FFmpegUnavailableError:
        raise HTTPException(status_code=503, detail="real_trial_generation_unavailable")
    payload = real_trial_result_to_payload(result)
    # Defense-in-depth: never emit a provider/publish token in operator payload.
    assert_no_gate_forbidden_tokens(payload)
    return JSONResponse(payload)
