"""Matrix Script first-preview generation trigger.

This is the New Task -> Workbench production-start link. It reuses the
controlled tomato preview generation path and persists the staged candidate on
the task config so the Workbench can render the first preview without a second
operator click.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from gateway.app.config import get_settings
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

AUTO_PREVIEW_STATUS_KEY = "matrix_script_initial_preview_generation"
STAGED_CANDIDATE_KEY = "matrix_script_staged_candidate"
STATUS_RUNNING = "preview_generation_running"
STATUS_SUCCEEDED = "preview_generation_succeeded"
STATUS_FAILED = "preview_generation_failed"


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


def _task_mapping(task: Any) -> Dict[str, Any]:
    if isinstance(task, Mapping):
        return dict(task)
    attrs = getattr(task, "__dict__", None)
    return dict(attrs) if isinstance(attrs, Mapping) else {}


def build_matrix_script_tomato_preview_payload(task: Mapping[str, Any]) -> Dict[str, Any]:
    """Run the existing tomato result path and return its operator-safe payload."""
    task_id = _task_id(task)
    task_payload = _task_mapping(task)
    result = run_tomato_real_result(
        task_payload,
        _resolve_tomato_output_dir(task_id),
        sink=_build_tomato_sink(task_id),
    )
    payload = tomato_result_to_payload(result)
    payload["preview_url"] = f"/api/matrix-script/{task_id}/tomato-real-result/preview/final.mp4"
    assert_no_delivery_view_forbidden_tokens(payload)
    return payload


def trigger_matrix_script_initial_preview_generation(
    task: Mapping[str, Any],
    repo: Any,
) -> Dict[str, Any]:
    """Synchronously generate and persist the first Matrix Script preview.

    The result is persisted under ``config.matrix_script_staged_candidate``.
    Failures are persisted under ``config.matrix_script_initial_preview_generation``
    so the Workbench can show a retry/error state instead of a dead empty state.
    """
    task_id = _task_id(task)
    _update_config(
        repo,
        task_id,
        task,
        {AUTO_PREVIEW_STATUS_KEY: _status_payload(STATUS_RUNNING, started_at=_utc_now())},
    )
    latest = repo.get(task_id) or task
    try:
        payload = build_matrix_script_tomato_preview_payload(latest)
    except FFmpegUnavailableError:
        failure = _status_payload(
            STATUS_FAILED,
            error="tomato_real_result_generation_unavailable",
        )
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except TomatoRealResultError as exc:
        failure = _status_payload(STATUS_FAILED, error=str(exc))
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure
    except Exception as exc:
        failure = _status_payload(STATUS_FAILED, error=f"{exc.__class__.__name__}: {exc}")
        _update_config(repo, task_id, repo.get(task_id) or latest, {AUTO_PREVIEW_STATUS_KEY: failure})
        return failure

    success = _status_payload(
        STATUS_SUCCEEDED,
        preview_url=payload.get("preview_url"),
        delivery_candidate=payload.get("delivery_candidate"),
    )
    _update_config(
        repo,
        task_id,
        repo.get(task_id) or latest,
        {
            STAGED_CANDIDATE_KEY: payload,
            AUTO_PREVIEW_STATUS_KEY: success,
        },
    )
    return success
