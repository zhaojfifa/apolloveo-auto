from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol


class WorkerExecutionMode(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class WorkerRequest:
    request_id: str
    line_id: str
    task_id: str
    step_id: str
    worker_capability: str
    execution_mode: WorkerExecutionMode
    worker_profile_ref: str | None = None
    input_refs: dict[str, Any] = field(default_factory=dict)
    strategy_hints: dict[str, Any] = field(default_factory=dict)
    runtime_config: dict[str, Any] = field(default_factory=dict)
    operator_context: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkerResult:
    request_id: str
    task_id: str
    step_id: str
    result: str
    attempt_facts: dict[str, Any]
    artifact_candidates: list[dict[str, Any]] = field(default_factory=list)
    output_facts: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] | None = None
    retry_hint: dict[str, Any] = field(default_factory=dict)
    raw_output: dict[str, Any] = field(default_factory=dict)


class WorkerAdapter(Protocol):
    def execute(self, request: WorkerRequest) -> WorkerResult:
        ...


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_worker_failure_result(
    request: WorkerRequest,
    *,
    reason: str,
    message: str,
    retryable: bool = False,
    after_seconds: int | None = None,
    raw_output: dict[str, Any] | None = None,
    output_facts: dict[str, Any] | None = None,
) -> WorkerResult:
    retry_hint: dict[str, Any] = {"retryable": bool(retryable)}
    if after_seconds is not None:
        retry_hint["after_seconds"] = int(after_seconds)
    return WorkerResult(
        request_id=request.request_id,
        task_id=request.task_id,
        step_id=request.step_id,
        result="timeout" if reason == "timeout" else "failed",
        attempt_facts={
            "started_at": _utcnow_iso(),
            "finished_at": _utcnow_iso(),
            "worker_mode": request.execution_mode.value,
            "provider": request.strategy_hints.get("provider_hint"),
        },
        output_facts=dict(output_facts or {}),
        error={
            "reason": reason,
            "message": message,
        },
        retry_hint=retry_hint,
        raw_output=dict(raw_output or {}),
    )


class WorkerGateway:
    def __init__(self, *, registry: Any) -> None:
        self._registry = registry

    def execute(self, request: WorkerRequest) -> WorkerResult:
        try:
            adapter = self._registry.resolve(request)
        except Exception as exc:
            return build_worker_failure_result(
                request,
                reason="worker_internal_error",
                message=str(exc) or "worker routing failed",
            )
        try:
            return adapter.execute(request)
        except Exception as exc:
            return build_worker_failure_result(
                request,
                reason="worker_internal_error",
                message=str(exc) or "worker execution failed",
            )
