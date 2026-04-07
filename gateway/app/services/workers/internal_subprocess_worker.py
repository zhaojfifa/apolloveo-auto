from __future__ import annotations

from datetime import datetime, timezone
import subprocess
from typing import Any

from gateway.app.services.worker_gateway import WorkerRequest, WorkerResult


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InternalSubprocessWorkerAdapter:
    def execute(self, request: WorkerRequest) -> WorkerResult:
        cmd = list(request.payload.get("cmd") or [])
        if not cmd:
            return WorkerResult(
                request_id=request.request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                result="failed",
                attempt_facts={
                    "started_at": _utcnow_iso(),
                    "finished_at": _utcnow_iso(),
                    "worker_mode": request.execution_mode.value,
                    "provider": request.strategy_hints.get("provider_hint"),
                },
                output_facts={"returncode": 1},
                error={"reason": "validation_error", "message": "worker subprocess cmd missing"},
                retry_hint={"retryable": False},
            )

        timeout_value = request.runtime_config.get("timeout_seconds")
        timeout = int(timeout_value) if timeout_value not in (None, "") else None
        started_at = _utcnow_iso()
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return WorkerResult(
                request_id=request.request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                result="timeout",
                attempt_facts={
                    "started_at": started_at,
                    "finished_at": _utcnow_iso(),
                    "worker_mode": request.execution_mode.value,
                    "provider": request.strategy_hints.get("provider_hint"),
                },
                output_facts={"returncode": None},
                error={
                    "reason": "timeout",
                    "message": f"worker timed out after {timeout}s" if timeout else "worker timed out",
                },
                retry_hint={"retryable": False},
                raw_output={
                    "stdout": str(exc.stdout or ""),
                    "stderr": str(exc.stderr or ""),
                    "cmd_text": " ".join(cmd),
                },
            )
        except Exception as exc:
            return WorkerResult(
                request_id=request.request_id,
                task_id=request.task_id,
                step_id=request.step_id,
                result="failed",
                attempt_facts={
                    "started_at": started_at,
                    "finished_at": _utcnow_iso(),
                    "worker_mode": request.execution_mode.value,
                    "provider": request.strategy_hints.get("provider_hint"),
                },
                output_facts={"returncode": 1},
                error={"reason": "worker_internal_error", "message": str(exc) or "worker subprocess failed"},
                retry_hint={"retryable": False},
                raw_output={"cmd_text": " ".join(cmd)},
            )

        return WorkerResult(
            request_id=request.request_id,
            task_id=request.task_id,
            step_id=request.step_id,
            result="success" if proc.returncode == 0 else "failed",
            attempt_facts={
                "started_at": started_at,
                "finished_at": _utcnow_iso(),
                "worker_mode": request.execution_mode.value,
                "provider": request.strategy_hints.get("provider_hint"),
            },
            output_facts={"returncode": proc.returncode},
            error=(
                None
                if proc.returncode == 0
                else {"reason": "worker_internal_error", "message": "worker subprocess returned non-zero exit code"}
            ),
            retry_hint={"retryable": False},
            raw_output={
                "stdout": str(proc.stdout or ""),
                "stderr": str(proc.stderr or ""),
                "cmd_text": " ".join(cmd),
            },
        )
