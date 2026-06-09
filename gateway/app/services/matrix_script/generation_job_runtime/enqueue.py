"""Matrix Script — Production Job Runtime — thin enqueue seam (PR-1).

Records a durable ``queued`` job for a Matrix Script task. This is the only
runtime touch-point of PR-1: it is **additive** and **thin** — it does NOT run
the worker, call a provider, or run ffmpeg. The existing in-process generation
path (web-dyno BackgroundTasks) is untouched; the worker takes over in PR-3.

``knobs_summary`` is operator-safe (ints/bools only): no secret, no vendor/model
name, no key.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional

from .job_state_store import IJobStateStore, get_job_state_store

_TARGET_SHOTS_ENV = "MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS"
_ATTEMPT_CAP_ENV = "MATRIX_SCRIPT_PROVIDER_ATTEMPT_CAP"
_GEMINI_RETRY_ENV = "MATRIX_SCRIPT_PROVIDER_ENABLE_GEMINI_RETRY"
_AKOOL_REAL_ENV = "MATRIX_SCRIPT_AKOOL_REAL"

_DEFAULT_TARGET_SHOTS = 3  # current default behavior (knob overrides)


def _field(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, Mapping):
        return task.get(key, default)
    return getattr(task, key, default)


def _task_id(task: Any) -> str:
    task_id = _field(task, "task_id") or _field(task, "id")
    if not task_id:
        raise ValueError("matrix_script_generation_job_requires_task_id")
    return str(task_id)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _operator_safe_knobs() -> Dict[str, Any]:
    """Closed, operator-safe knob summary.

    Vendor-neutral keys + ints/bools only — no secret, no vendor/model name
    (``refine_retry`` not ``gemini_*``; ``real_provider`` not ``akool_*``), so the
    summary is safe to persist on the operator-facing job record.
    """
    return {
        "target_shots": _env_int(_TARGET_SHOTS_ENV, _DEFAULT_TARGET_SHOTS),
        "attempt_cap": _env_int(_ATTEMPT_CAP_ENV, 0) or None,
        "refine_retry": _env_bool(_GEMINI_RETRY_ENV, default=True),
        "real_provider": _env_bool(_AKOOL_REAL_ENV, default=False),
    }


def enqueue_generation_job(task: Any, store: Optional[IJobStateStore] = None) -> str:
    """Create a durable ``queued`` generation job for the task; return job_id.

    Thin + additive. The caller wraps this so a failure never blocks task
    creation (mirrors the existing initial-preview enqueue resilience).
    """
    store = store or get_job_state_store()
    task_id = _task_id(task)
    knobs = _operator_safe_knobs()
    target_shots = int(knobs.get("target_shots") or _DEFAULT_TARGET_SHOTS)
    return store.create_job(task_id, target_shots=target_shots, knobs_summary=knobs)
