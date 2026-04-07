from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gateway.app.services.worker_gateway import WorkerAdapter, WorkerExecutionMode, WorkerGateway, WorkerRequest
from gateway.app.services.workers.internal_subprocess_worker import InternalSubprocessWorkerAdapter


@dataclass(frozen=True)
class _WorkerRegistryKey:
    line_id: str
    step_id: str
    worker_capability: str
    execution_mode: str


class WorkerGatewayRegistry:
    def __init__(self) -> None:
        self._adapters: dict[_WorkerRegistryKey, WorkerAdapter] = {}

    def register(
        self,
        *,
        line_id: str,
        step_id: str,
        worker_capability: str,
        execution_mode: WorkerExecutionMode,
        adapter: WorkerAdapter,
    ) -> WorkerAdapter:
        key = _WorkerRegistryKey(
            line_id=str(line_id or "").strip(),
            step_id=str(step_id or "").strip(),
            worker_capability=str(worker_capability or "").strip(),
            execution_mode=execution_mode.value,
        )
        self._adapters[key] = adapter
        return adapter

    def resolve(self, request: WorkerRequest) -> WorkerAdapter:
        candidates = (
            _WorkerRegistryKey(request.line_id, request.step_id, request.worker_capability, request.execution_mode.value),
            _WorkerRegistryKey(request.line_id, request.step_id, "*", request.execution_mode.value),
            _WorkerRegistryKey(request.line_id, request.step_id, request.worker_capability, "*"),
            _WorkerRegistryKey(request.line_id, request.step_id, "*", "*"),
        )
        for key in candidates:
            adapter = self._adapters.get(key)
            if adapter is not None:
                return adapter
        raise RuntimeError(
            "no worker adapter registered for "
            f"line={request.line_id} step={request.step_id} capability={request.worker_capability} "
            f"mode={request.execution_mode.value}"
        )


_DEFAULT_REGISTRY = WorkerGatewayRegistry()
_DEFAULT_GATEWAY = WorkerGateway(registry=_DEFAULT_REGISTRY)


def get_worker_gateway_registry() -> WorkerGatewayRegistry:
    return _DEFAULT_REGISTRY


def get_worker_gateway() -> WorkerGateway:
    return _DEFAULT_GATEWAY


def _register_defaults() -> None:
    _DEFAULT_REGISTRY.register(
        line_id="hot_follow_line",
        step_id="compose",
        worker_capability="ffmpeg",
        execution_mode=WorkerExecutionMode.INTERNAL,
        adapter=InternalSubprocessWorkerAdapter(),
    )


_register_defaults()
