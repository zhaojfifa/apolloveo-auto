from __future__ import annotations

import subprocess

from gateway.app.services.worker_gateway import WorkerExecutionMode, WorkerGateway, WorkerRequest, WorkerResult
from gateway.app.services.worker_gateway_registry import WorkerGatewayRegistry
from gateway.app.services.workers.internal_subprocess_worker import InternalSubprocessWorkerAdapter


class _StaticAdapter:
    def __init__(self, mode: str) -> None:
        self._mode = mode

    def execute(self, request: WorkerRequest) -> WorkerResult:
        return WorkerResult(
            request_id=request.request_id,
            task_id=request.task_id,
            step_id=request.step_id,
            result="success",
            attempt_facts={
                "started_at": "2026-04-07T00:00:00+00:00",
                "finished_at": "2026-04-07T00:00:01+00:00",
                "worker_mode": self._mode,
                "provider": request.strategy_hints.get("provider_hint"),
            },
            output_facts={"returncode": 0},
            retry_hint={"retryable": False},
        )


def test_worker_gateway_registry_dispatches_by_execution_mode():
    registry = WorkerGatewayRegistry()
    registry.register(
        line_id="hot_follow_line",
        step_id="dub",
        worker_capability="tts",
        execution_mode=WorkerExecutionMode.EXTERNAL,
        adapter=_StaticAdapter("external"),
    )
    registry.register(
        line_id="hot_follow_line",
        step_id="compose",
        worker_capability="ffmpeg",
        execution_mode=WorkerExecutionMode.HYBRID,
        adapter=_StaticAdapter("hybrid"),
    )
    gateway = WorkerGateway(registry=registry)

    external_result = gateway.execute(
        WorkerRequest(
            request_id="r1",
            line_id="hot_follow_line",
            task_id="t1",
            step_id="dub",
            worker_capability="tts",
            execution_mode=WorkerExecutionMode.EXTERNAL,
        )
    )
    hybrid_result = gateway.execute(
        WorkerRequest(
            request_id="r2",
            line_id="hot_follow_line",
            task_id="t2",
            step_id="compose",
            worker_capability="ffmpeg",
            execution_mode=WorkerExecutionMode.HYBRID,
        )
    )

    assert external_result.attempt_facts["worker_mode"] == "external"
    assert hybrid_result.attempt_facts["worker_mode"] == "hybrid"


def test_internal_subprocess_worker_adapter_returns_timeout_result(monkeypatch):
    adapter = InternalSubprocessWorkerAdapter()

    def _boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["ffmpeg", "-i", "in.mp4", "out.mp4"], timeout=5, stderr="timeout stderr")

    monkeypatch.setattr(subprocess, "run", _boom)

    result = adapter.execute(
        WorkerRequest(
            request_id="r1",
            line_id="hot_follow_line",
            task_id="t1",
            step_id="compose",
            worker_capability="ffmpeg",
            execution_mode=WorkerExecutionMode.INTERNAL,
            runtime_config={"timeout_seconds": 5},
            payload={"cmd": ["ffmpeg", "-i", "in.mp4", "out.mp4"]},
        )
    )

    assert result.result == "timeout"
    assert result.error == {
        "reason": "timeout",
        "message": "worker timed out after 5s",
    }
    assert result.raw_output["stderr"] == "timeout stderr"
