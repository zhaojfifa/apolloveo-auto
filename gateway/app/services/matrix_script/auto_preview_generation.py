"""Matrix Script first-preview generation trigger.

This is the New Task -> Workbench production-start link. It reuses the
controlled tomato preview generation path and persists the staged candidate on
the task config so the Workbench can render the first preview without a second
operator click.
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from gateway.app.config import get_settings
from gateway.app.routers.matrix_script_real_trial import ArtifactStorageStagingSink
from gateway.app.services.matrix_script.minimal_result_artifact_staging import StagingError
from gateway.app.services.matrix_script.minimal_result_delivery_view import (
    assert_no_delivery_view_forbidden_tokens,
)
from gateway.app.services.matrix_script.simple_scene_renderer import (
    FFmpegUnavailableError,
    SceneRenderError,
    ffprobe_path,
    probe_duration_seconds,
)
from gateway.app.services.matrix_script.tomato_real_result_orchestrator import (
    TomatoRealResult,
    TomatoRealResultError,
    run_tomato_real_result,
    tomato_result_to_payload,
)

AUTO_PREVIEW_STATUS_KEY = "matrix_script_initial_preview_generation"
STAGED_CANDIDATE_KEY = "matrix_script_staged_candidate"
# Async lifecycle: queued (New Task POST) -> running (background job start) ->
# succeeded / failed (background job terminal). retry_required is a *projection*
# state derived from a stale running/queued attempt; the generator never writes
# it (the projection layer owns the stale guard — see operator_workbench_view).
STATUS_QUEUED = "preview_generation_queued"
STATUS_RUNNING = "preview_generation_running"
STATUS_SUCCEEDED = "preview_generation_succeeded"
STATUS_FAILED = "preview_generation_failed"
STATUS_RETRY_REQUIRED = "preview_generation_retry_required"
MIN_FINAL_VIDEO_BYTES = 1024
OPERATOR_SAFE_GENERATION_FAILURE = "首版预览生成失败：视频文件未完整生成，请重新生成。"


class AutoPreviewValidationError(RuntimeError):
    """Raised when generated preview artifacts are incomplete or unreadable."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _field(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, Mapping):
        return task.get(key, default)
    return getattr(task, key, default)


def _task_id(task: Any) -> str:
    task_id = _field(task, "task_id") or _field(task, "id")
    if not task_id:
        raise ValueError("matrix_script_auto_preview_requires_task_id")
    return str(task_id)


def _config(task: Any) -> Dict[str, Any]:
    cfg = _field(task, "config") or {}
    return dict(cfg) if isinstance(cfg, Mapping) else {}


def _resolve_tomato_output_dir(task_id: str) -> str:
    base = get_settings().workspace_root
    return os.path.join(base, "artifacts", "matrix_script_tomato_real_result", task_id)


def _build_tomato_sink(task_id: str) -> Any:
    return ArtifactStorageStagingSink(task_id)


def _update_config(repo: Any, task_id: str, task: Any, updates: Mapping[str, Any]) -> None:
    cfg = _config(task)
    cfg.update(dict(updates))
    if not hasattr(repo, "update"):
        raise ValueError("task_repository_update_required_for_matrix_script_auto_preview")
    repo.update(task_id, {"config": cfg})


def _status_payload(status: str, **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": status,
        "updated_at": _utc_now(),
        "official_publish_ready": False,
    }
    payload.update(extra)
    return payload


def _failure_payload(*, stage: str, error_summary: str = OPERATOR_SAFE_GENERATION_FAILURE, error: str | None = None) -> Dict[str, Any]:
    payload = _status_payload(
        STATUS_FAILED,
        error_summary=error_summary,
        failed_at=_utc_now(),
        stage=stage,
    )
    if error:
        payload["error"] = error
    return payload


def _task_mapping(task: Any) -> Dict[str, Any]:
    if isinstance(task, Mapping):
        return dict(task)
    attrs = getattr(task, "__dict__", None)
    return dict(attrs) if isinstance(attrs, Mapping) else {}


def _manifest_path_for_result(result: TomatoRealResult) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(result.final_video_path)), "manifest.json")


def _probe_has_video_stream(path: str) -> bool:
    if not ffprobe_path():
        raise FFmpegUnavailableError("ffprobe not found on PATH")
    cmd = [
        ffprobe_path(),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "default=nw=1:nokey=1",
        path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
    if proc.returncode != 0:
        raise SceneRenderError("ffprobe failed to read video stream")
    return "video" in (proc.stdout or b"").decode("utf-8", "replace").splitlines()


def validate_tomato_result_artifacts(result: TomatoRealResult) -> None:
    """Validate final artifacts before exposing them as a staged candidate."""
    final_path = result.final_video_path
    if not final_path or not os.path.exists(final_path):
        raise AutoPreviewValidationError("final_video_missing")
    if os.path.getsize(final_path) <= MIN_FINAL_VIDEO_BYTES:
        raise AutoPreviewValidationError("final_video_too_small")
    duration = probe_duration_seconds(final_path)
    if duration <= 0:
        raise AutoPreviewValidationError("final_video_duration_non_positive")
    if not _probe_has_video_stream(final_path):
        raise AutoPreviewValidationError("final_video_stream_missing")
    manifest_path = _manifest_path_for_result(result)
    if not os.path.exists(manifest_path):
        raise AutoPreviewValidationError("manifest_missing")


def build_matrix_script_tomato_preview_payload(task: Mapping[str, Any]) -> Dict[str, Any]:
    """Run the existing tomato result path and return its operator-safe payload."""
    task_id = _task_id(task)
    task_payload = _task_mapping(task)
    result = run_tomato_real_result(
        task_payload,
        _resolve_tomato_output_dir(task_id),
        sink=_build_tomato_sink(task_id),
    )
    validate_tomato_result_artifacts(result)
    payload = tomato_result_to_payload(result)
    payload["preview_url"] = f"/api/matrix-script/{task_id}/tomato-real-result/preview/final.mp4"
    assert_no_delivery_view_forbidden_tokens(payload)
    return payload


def enqueue_matrix_script_initial_preview_generation(
    task: Mapping[str, Any],
    repo: Any,
) -> Dict[str, Any]:
    """Persist the ``queued`` lifecycle state for the first Matrix Script preview.

    Called synchronously inside the New Task POST so the Workbench has a durable
    in-progress state to poll against, BEFORE the heavy generation runs. The
    actual generation is dispatched to the background and finalized by
    :func:`trigger_matrix_script_initial_preview_generation`.
    """
    task_id = _task_id(task)
    queued = _status_payload(STATUS_QUEUED, queued_at=_utc_now())
    _update_config(repo, task_id, repo.get(task_id) or task, {AUTO_PREVIEW_STATUS_KEY: queued})
    return queued


def trigger_matrix_script_initial_preview_generation(
    task: Mapping[str, Any],
    repo: Any,
) -> Dict[str, Any]:
    """Generate and persist the first Matrix Script preview (background job body).

    Writes ``running`` (with ``started_at``) before the heavy work so the
    Workbench poller observes progress, then finalizes as
    ``preview_generation_succeeded`` (with ``completed_at`` +
    ``config.matrix_script_staged_candidate``) or ``preview_generation_failed``
    (with ``failed_at`` + an operator-safe ``error_summary``). Because the
    request thread no longer blocks on this, a gateway timeout can never leave a
    half-written state; if the worker dies mid-run the projection layer's stale
    guard promotes a lingering ``running`` to ``retry_required``.
    """
    task_id = _task_id(task)
    _update_config(
        repo,
        task_id,
        repo.get(task_id) or task,
        {AUTO_PREVIEW_STATUS_KEY: _status_payload(STATUS_RUNNING, started_at=_utc_now())},
    )
    latest = repo.get(task_id) or task
    try:
        payload = build_matrix_script_tomato_preview_payload(latest)
    except FFmpegUnavailableError:
        failure = _failure_payload(
            stage="generation",
            error_summary="首版预览生成失败：当前环境无法使用 ffmpeg，请重新生成或联系管理员。",
            error="tomato_real_result_generation_unavailable",
        )
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except AutoPreviewValidationError as exc:
        failure = _failure_payload(stage="validation", error=str(exc))
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except StagingError as exc:
        failure = _failure_payload(stage="staging", error=str(exc))
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except TomatoRealResultError as exc:
        failure = _failure_payload(stage="generation", error=str(exc))
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except Exception as exc:
        failure = _failure_payload(stage="generation", error=f"{exc.__class__.__name__}: {exc}")
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure

    success = _status_payload(
        STATUS_SUCCEEDED,
        completed_at=_utc_now(),
        preview_url=payload.get("preview_url"),
        delivery_candidate=payload.get("delivery_candidate"),
    )
    try:
        _update_config(
            repo,
            task_id,
            repo.get(task_id) or latest,
            {
                STAGED_CANDIDATE_KEY: payload,
                AUTO_PREVIEW_STATUS_KEY: success,
            },
        )
    except Exception as exc:
        failure = _failure_payload(stage="persistence", error=f"{exc.__class__.__name__}: {exc}")
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    return success
