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
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from gateway.app.config import get_settings
from gateway.app.deps import get_task_repository
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    assert_no_delivery_view_forbidden_tokens,
)
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
    abstraction and returns an opaque artifact ref + a browser preview URL.

    Uses only the existing abstraction (``upload_artifact`` / ``get_download_url``)
    — artifact_storage.py is NOT modified. The preview URL is ``/files/<key>``
    for the local backend (served by the app's ``/files`` route) or a presigned
    ``https://`` URL for R2 — an internal staged preview, never a provider URL.
    """

    def __init__(self, task_id: str) -> None:
        self._task_id = task_id

    def put(self, local_path: str, artifact_name: str) -> str:
        from gateway.app.services.artifact_storage import upload_artifact

        upload_artifact(self._task_id, local_path, artifact_name)
        return f"artifact://{artifact_name}"

    def preview_url_for(self, artifact_name: str) -> "str | None":
        from gateway.app.services.artifact_storage import get_download_url

        try:
            return get_download_url(self._task_id, artifact_name)
        except Exception:
            return None


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
    # Operator-accessible preview link: a dedicated gateway endpoint that
    # streams the staged local final.mp4 — browser-openable regardless of the
    # storage backend / static-file config. Internal staged preview, NOT a
    # publish/provider/download URL.
    payload["preview_url"] = f"/api/matrix-script/{task_id}/real-trial/preview/final.mp4"
    # Defense-in-depth: never emit a provider/publish/download token. Uses the
    # delivery-view guard (bans provider_url / temporary_url / publish_url /
    # download_url / akool / model_id / credit; permits the preview link).
    assert_no_delivery_view_forbidden_tokens(payload)
    return JSONResponse(payload)


@api_router.get("/{task_id}/real-trial/preview/final.mp4")
def get_real_trial_preview(
    task_id: str, repo: ITaskRepository = Depends(get_task_repository)
):
    """Stream the staged local final.mp4 for operator preview (not publish).

    Serves the local staged file when present; otherwise redirects to the
    storage abstraction's URL (e.g. R2 presigned). 404 when neither exists.
    Matrix-Script-scoped; reads the task only.
    """
    task = _resolve_task(repo, task_id)
    _ensure_matrix_script(task)
    local_final = os.path.join(resolve_real_trial_output_dir(task_id), "final", "final.mp4")
    if os.path.exists(local_final) and os.path.getsize(local_final) > 0:
        return FileResponse(path=local_final, media_type="video/mp4", filename="final.mp4")
    # Fallback: storage-backed URL (e.g. R2 presigned) via the existing abstraction.
    try:
        from gateway.app.services.artifact_storage import get_download_url

        url = get_download_url(task_id, "matrix_script/%s/final/final.mp4" % task_id)
        if isinstance(url, str) and url:
            return RedirectResponse(url=url, status_code=302)
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="preview_not_available")
