"""Matrix Script — Production Job Runtime — Worker Runtime Skeleton (PR-2).

A generation worker that runs **off the FastAPI request lifecycle**: it claims a
durable job via ``IJobStateStore``, walks the closed state machine, and writes
durable trace at every step. PR-2 is **dry-run only** — NO Akool/Gemini/Azure
call, NO ffmpeg, NO R2 upload, NO final.mp4. The real generation lands in PR-3.

Crash-safety: the dry-run opens a ``running`` trace row BEFORE the (stubbed)
heavy work; a crash/exception leaves that row + a durable ``job_failed_*`` state,
so failure always leaves evidence (the TRACE_GAP closure carried into the worker).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from . import job_state as st
from .generation import StateWalker
from .job_state_store import IJobStateStore, get_job_state_store
from .trace_writer import JobTraceWriter

logger = logging.getLogger(__name__)

WORKER_DEFAULT_LEASE_SECONDS = 600
WORKER_DEFAULT_MAX_RETRIES = 3

# The closed legal state path a dry-run walks after the claim leaves the job at
# ``planning`` (claim => planning). No real work happens at any step in PR-2.
_DRY_RUN_GENERATION_STATES = (
    st.JOB_STATE_PROVIDER_GENERATING,
    st.JOB_STATE_PROVIDER_POLLING,
    st.JOB_STATE_PROVIDER_CLIP_READY,
    st.JOB_STATE_COMPOSING,
    st.JOB_STATE_UPLOADING,
)


class WorkerDryRunError(RuntimeError):
    """Raised inside the dry-run to exercise the crash/failure path (tests)."""


class WorkerRuntime:
    """Off-dyno generation worker (dry-run skeleton)."""

    def __init__(
        self,
        store: Optional[IJobStateStore] = None,
        *,
        worker_id: str,
        lease_seconds: int = WORKER_DEFAULT_LEASE_SECONDS,
        max_retries: int = WORKER_DEFAULT_MAX_RETRIES,
        generation_fn: Optional[Any] = None,
    ) -> None:
        self._store = store or get_job_state_store()
        self._worker_id = worker_id
        self._lease_seconds = int(lease_seconds)
        self._max_retries = int(max_retries)
        # PR-3: real 1-shot generation_fn(job, store, writer, walker). When None,
        # the PR-2 dry-run path runs (skeleton / hermetic test mode). Injected by
        # the CLI (real default) or by tests (fakes).
        self._generation_fn = generation_fn

    def run_once(
        self, *, simulate_failure: bool = False, now: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reclaim stale leases, claim one job, dry-run it, leave durable trace."""
        self._store.reclaim_expired_leases(max_retries=self._max_retries, now=now)
        job = self._store.claim_next_queued_job(
            self._worker_id, lease_seconds=self._lease_seconds, now=now
        )
        if job is None:
            logger.info("worker=%s event=no_queued_job", self._worker_id)
            return {"claimed": False, "worker_id": self._worker_id}

        job_id = job["job_id"]
        writer = JobTraceWriter(self._store, job_id)
        writer.record_event(st.WORKER_EVENT_WORKER_STARTED)
        writer.record_event(st.WORKER_EVENT_JOB_CLAIMED)
        summary: Dict[str, Any] = {}
        try:
            if self._store.heartbeat(
                job_id, self._worker_id, lease_seconds=self._lease_seconds, now=now
            ) is None:
                # claim/lease lost before processing (reclaimed / taken) — fail
                # cleanly so durable evidence is left rather than an illegal move
                raise WorkerDryRunError("lease lost before processing")
            writer.record_event(st.WORKER_EVENT_HEARTBEAT)
            if self._generation_fn is not None:
                # PR-3 real path: open a per-state running row, run the bounded
                # 1-shot generation (which advances state via walker.on_phase),
                # then finalize to result_ready. A crash leaves the in-flight
                # state's OPEN running row as durable evidence.
                walker = StateWalker(self._store, writer, job_id)
                walker.open_current()  # OPEN planning row (before heavy work)
                summary = self._generation_fn(job, self._store, writer, walker) or {}
                walker.advance_to(st.JOB_STATE_RESULT_READY)
                walker.finalize()
            else:
                # PR-2 dry-run path (skeleton / test mode) — unchanged.
                self._dry_run(job_id, writer, simulate_failure=simulate_failure)
                self._store.transition_state(job_id, st.JOB_STATE_RESULT_READY)
            writer.record_event(st.WORKER_EVENT_JOB_COMPLETED)
            logger.info("worker=%s job=%s event=job_completed", self._worker_id, job_id)
            return {"claimed": True, "job_id": job_id, "final_state": st.JOB_STATE_RESULT_READY, **summary}
        except Exception as exc:  # noqa: BLE001 — failure must leave durable evidence, not crash silently
            return self._handle_failure(job_id, writer, exc)

    def _dry_run(self, job_id: str, writer: JobTraceWriter, *, simulate_failure: bool) -> None:
        """Walk the legal state path with NO real work; open trace before, close after."""
        dry_tid = writer.begin_phase(st.WORKER_EVENT_DRY_RUN_STARTED)  # OPEN running row (before)
        for nxt in _DRY_RUN_GENERATION_STATES:
            if simulate_failure and nxt == st.JOB_STATE_PROVIDER_POLLING:
                raise WorkerDryRunError("simulated dry-run failure")
            self._store.transition_state(job_id, nxt)  # dry-run: state walk only, no provider/ffmpeg
        writer.end_phase(dry_tid, status=st.TRACE_STATUS_SUCCEEDED)  # close (after)
        writer.record_event(st.WORKER_EVENT_DRY_RUN_COMPLETED)

    def _handle_failure(self, job_id: str, writer: JobTraceWriter, exc: Exception) -> Dict[str, Any]:
        job = self._store.get_job(job_id) or {}
        will_terminal = (int(job.get("retry_count", 0)) + 1) >= self._max_retries
        self._store.transition_state(
            job_id, st.JOB_STATE_FAILED_RETRYABLE,
            failure_reason_code="worker_error", increment_retry=True,
        )
        if will_terminal:
            self._store.transition_state(
                job_id, st.JOB_STATE_FAILED_TERMINAL, failure_reason_code="worker_error"
            )
            writer.record_event(st.WORKER_EVENT_JOB_FAILED_TERMINAL, status=st.TRACE_STATUS_FAILED)
            final = st.JOB_STATE_FAILED_TERMINAL
        else:
            writer.record_event(st.WORKER_EVENT_JOB_FAILED_RETRYABLE, status=st.TRACE_STATUS_FAILED)
            final = st.JOB_STATE_FAILED_RETRYABLE
        # NOTE: the OPEN dry_run_started running row is intentionally left open —
        # it is the durable evidence of the phase that was in flight at failure.
        logger.warning(
            "worker=%s job=%s event=%s error=%s", self._worker_id, job_id, final, exc.__class__.__name__
        )
        return {"claimed": True, "job_id": job_id, "final_state": final, "error": exc.__class__.__name__}

    def run_loop(self, *, max_iterations: Optional[int] = None) -> List[Dict[str, Any]]:
        """Claim + dry-run jobs until none remain (or ``max_iterations`` reached)."""
        results: List[Dict[str, Any]] = []
        i = 0
        while max_iterations is None or i < max_iterations:
            result = self.run_once()
            results.append(result)
            if not result.get("claimed"):
                break
            i += 1
        return results
