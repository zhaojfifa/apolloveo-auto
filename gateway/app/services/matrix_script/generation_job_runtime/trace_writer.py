"""Matrix Script — Production Job Runtime — durable trace writer (PR-1).

The TRACE_GAP closure mechanism (Gate Spec §6 / SM-5): ``begin_phase`` persists a
``running`` row BEFORE the heavy work; ``end_phase`` updates it. A worker kill
between the two always leaves the ``running`` row, naming the failing phase —
without depending on ephemeral Render logs.

Also the no-secret guard (``assert_no_job_trace_leak``) and a hermetic local
harness (Gate Spec §10 PR-1: "exercised by tests + a local harness"). NO worker
execution, NO provider call, NO ffmpeg here.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import job_state as st
from .job_state_store import IJobStateStore, InMemoryJobStateStore

# Operator-safe red line: a durable trace row must never carry a secret, a raw
# provider/vendor name, a raw signed URL, a key/token, or a local path.
_FORBIDDEN_TRACE_TOKENS = (
    "api_key", "apikey", "x-op-key", "authorization", "bearer", "secret", "token=",
    "akool", "gemini", "azure", "openai", "vendor", "provider_url", "download_url",
    "temporary_url", "presigned", "x-amz", "signature=", "/users/", "/var/", "/tmp/",
    "file://",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_no_job_trace_leak(row: Any) -> None:
    """Raise if a trace row (or any payload) leaks a forbidden token."""
    blob = str(row).lower()
    hits = [t for t in _FORBIDDEN_TRACE_TOKENS if t in blob]
    if hits:
        raise ValueError(f"job trace leaks forbidden tokens: {hits}")


class JobTraceWriter:
    """Per-job durable trace writer with the write-before-heavy-work discipline."""

    def __init__(self, store: IJobStateStore, job_id: str) -> None:
        self._store = store
        self._job_id = job_id
        self._starts: Dict[str, float] = {}  # trace_id -> monotonic start

    def begin_phase(self, phase: str, *, shot_id: Optional[str] = None) -> str:
        """Persist a ``running`` row BEFORE the heavy work; return its trace_id."""
        st.assert_valid_phase(phase)
        trace_id = self._store.append_trace(
            self._job_id, phase=phase, status=st.TRACE_STATUS_RUNNING,
            started_at=_utc_now(), shot_id=shot_id,
        )
        self._starts[trace_id] = time.monotonic()
        return trace_id

    def end_phase(
        self, trace_id: str, *, status: str,
        provider_status_class: Optional[str] = None,
        fallback_reason_code: Optional[str] = None,
        artifact_refs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update the row at phase end with elapsed_ms + terminal phase status."""
        if status == st.TRACE_STATUS_RUNNING:
            raise ValueError("end_phase status must not be 'running'")
        started = self._starts.pop(trace_id, None)
        elapsed_ms = int((time.monotonic() - started) * 1000) if started is not None else None
        return self._store.update_trace(
            trace_id, status=status, ended_at=_utc_now(), elapsed_ms=elapsed_ms,
            provider_status_class=provider_status_class,
            fallback_reason_code=fallback_reason_code, artifact_refs=artifact_refs,
        )


def run_local_trace_harness(store: Optional[IJobStateStore] = None) -> Dict[str, Any]:
    """Hermetic local harness: walk one job queued -> result_ready writing trace.

    No provider/ffmpeg/network — deterministic phase walk only. Returns the final
    job + ordered traces for inspection (used by the PR-1 test).
    """
    store = store or InMemoryJobStateStore()
    job_id = store.create_job("ms-harness-task", target_shots=1, knobs_summary={"target_shots": 1})
    writer = JobTraceWriter(store, job_id)

    store.transition_state(job_id, st.JOB_STATE_PLANNING)
    t = writer.begin_phase("generation_start")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED)

    store.transition_state(job_id, st.JOB_STATE_PROVIDER_GENERATING)
    t = writer.begin_phase("prompt_build", shot_id="shot01")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED)
    store.transition_state(job_id, st.JOB_STATE_PROVIDER_POLLING)
    t = writer.begin_phase("provider_poll", shot_id="shot01")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED, provider_status_class="ok")
    store.transition_state(job_id, st.JOB_STATE_PROVIDER_CLIP_READY)
    t = writer.begin_phase("provider_download", shot_id="shot01")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED, artifact_refs=["r2:clip/shot01"])

    store.transition_state(job_id, st.JOB_STATE_COMPOSING)
    t = writer.begin_phase("compose_start")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED)
    store.transition_state(job_id, st.JOB_STATE_UPLOADING)
    t = writer.begin_phase("upload_start")
    writer.end_phase(t, status=st.TRACE_STATUS_SUCCEEDED, artifact_refs=["r2:final/final.mp4"])
    store.transition_state(job_id, st.JOB_STATE_RESULT_READY)

    return {"job": store.get_job(job_id), "traces": store.get_traces(job_id)}
