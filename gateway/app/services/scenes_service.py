import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from gateway.app.services.scene_split import generate_scenes_package
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.task_events import append_task_event

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_value(task: dict[str, Any], field: str) -> Any:
    value = task.get(field)
    if value is None and isinstance(task.get("deliverables"), dict):
        value = task.get("deliverables", {}).get(field)
    return value


def _derive_scenes_status(task: dict[str, Any]) -> str:
    if _task_value(task, "scenes_key"):
        return "done"
    if _task_value(task, "scenes_error"):
        return "failed"
    started = task.get("scenes_started_at")
    finished = task.get("scenes_finished_at")
    if started and not finished:
        return "running"
    return "pending"


def _with_event(task: dict[str, Any], *, code: str, message: str, extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    patch = {"events": list(task.get("events") or [])}
    append_task_event(
        patch,
        channel="scenes",
        code=code,
        message=message,
        extra=extra or {},
    )
    return patch["events"]


def _upsert(repo: Any, task_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    current = repo.get(task_id) or {}
    patch = dict(updates or {})
    if isinstance(patch.get("deliverables"), dict):
        existing = current.get("deliverables") if isinstance(current.get("deliverables"), dict) else {}
        merged = dict(existing)
        merged.update(patch.get("deliverables") or {})
        patch["deliverables"] = merged
    if "scenes_status" not in patch:
        shadow = dict(current)
        shadow.update(patch)
        patch["scenes_status"] = _derive_scenes_status(shadow)
    return policy_upsert(repo, task_id, current, patch, step="scenes_service", force=False) or (repo.get(task_id) or {})


def _run_scenes_job(task_id: str, repo: Any, run_id: str) -> None:
    start = time.perf_counter()
    logger.info("SCENES_RUN_START", extra={"task_id": task_id, "run_id": run_id})
    current = repo.get(task_id) or {}
    _upsert(
        repo,
        task_id,
        {
            "events": _with_event(
                current,
                code="SCENES_RUN_START",
                message="Scenes build started",
                extra={"task_id": task_id, "run_id": run_id},
            )
        },
    )
    try:
        result = generate_scenes_package(task_id)
        scenes_key = result.get("scenes_key")
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        latest = repo.get(task_id) or {}
        _upsert(
            repo,
            task_id,
            {
                "scenes_key": scenes_key,
                "scene_pack_key": scenes_key,
                "scenes_error": None,
                "scenes_error_message": None,
                "scenes_finished_at": _now_iso(),
                "scenes_elapsed_ms": elapsed_ms,
                "deliverables": {
                    "scenes_key": scenes_key,
                    "scene_pack_key": scenes_key,
                },
                "events": _with_event(
                    latest,
                    code="SCENES_RUN_DONE",
                    message="Scenes build completed",
                    extra={"task_id": task_id, "run_id": run_id, "scenes_key": scenes_key},
                ),
            },
        )
        logger.info("SCENES_RUN_DONE", extra={"task_id": task_id, "run_id": run_id, "scenes_key": scenes_key})
    except Exception as exc:  # pragma: no cover
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        latest = repo.get(task_id) or {}
        err = {"type": type(exc).__name__, "message": str(exc)}
        _upsert(
            repo,
            task_id,
            {
                "scenes_error": err,
                "scenes_error_message": str(exc),
                "scenes_finished_at": _now_iso(),
                "scenes_elapsed_ms": elapsed_ms,
                "events": _with_event(
                    latest,
                    code="SCENES_RUN_FAIL",
                    message="Scenes build failed",
                    extra={"task_id": task_id, "run_id": run_id, "error": err},
                ),
            },
        )
        logger.exception("SCENES_RUN_FAIL", extra={"task_id": task_id, "run_id": run_id})


class ScenesService:
    @staticmethod
    def enqueue_scenes_build(task_id: str, *, repo: Any, background_tasks: Any) -> dict[str, Any]:
        task = repo.get(task_id)
        if not task:
            return {
                "task_id": task_id,
                "status": "not_found",
                "scenes_key": None,
                "message": "Task not found",
                "error": "task_not_found",
            }

        scenes_key = _task_value(task, "scenes_key")
        if scenes_key:
            logger.info("SCENES_ENQUEUE", extra={"task_id": task_id, "status": "already_ready", "scenes_key": scenes_key})
            return {
                "task_id": task_id,
                "status": "already_ready",
                "scenes_key": str(scenes_key),
                "message": "Scenes already ready",
                "error": None,
            }

        status = _derive_scenes_status(task)
        if status == "running":
            logger.info("SCENES_ENQUEUE", extra={"task_id": task_id, "status": "already_running"})
            return {
                "task_id": task_id,
                "status": "already_running",
                "scenes_key": None,
                "message": "Scenes build already running",
                "error": None,
            }

        now = _now_iso()
        run_id = uuid4().hex[:12]
        attempt_raw = task.get("scenes_attempt")
        try:
            attempt = int(attempt_raw or 0) + 1
        except Exception:
            attempt = 1
        updated = _upsert(
            repo,
            task_id,
            {
                "scenes_started_at": now,
                "scenes_finished_at": None,
                "scenes_elapsed_ms": None,
                "scenes_attempt": attempt,
                "scenes_run_id": run_id,
                "scenes_error": None,
                "scenes_error_message": None,
                "events": _with_event(
                    task,
                    code="SCENES_ENQUEUE",
                    message="Scenes build enqueued",
                    extra={"task_id": task_id, "run_id": run_id, "attempt": attempt},
                ),
            },
        )
        background_tasks.add_task(_run_scenes_job, task_id, repo, run_id)
        logger.info("SCENES_ENQUEUE", extra={"task_id": task_id, "status": "queued", "run_id": run_id})
        return {
            "task_id": task_id,
            "status": "queued",
            "scenes_key": _task_value(updated, "scenes_key"),
            "message": "Scenes build queued",
            "error": None,
            "run_id": run_id,
        }
