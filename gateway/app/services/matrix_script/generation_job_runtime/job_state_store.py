"""Matrix Script — Production Job Runtime — durable job state store (PR-1).

The **swappable interface** (Owner binding condition 2026-06-09): ``IJobStateStore``
plus two implementations — ``InMemoryJobStateStore`` (hermetic tests + the local
harness) and ``SqlAlchemyJobStateStore`` (the durable, Render-Postgres-backed
impl that reuses the app engine). The technology stays isolated behind this
interface so the future Service Topology Split can re-decide persistence.

PR-1 owns durable state + trace truth only: NO worker execution, NO provider
call, NO ffmpeg. ``claim_next_queued_job`` is store capability (exercised by a
unit test); the worker that consumes it is PR-2.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from . import job_state as st
from .models import GenerationJob, GenerationJobTrace

_JSON_FIELDS_JOB = ("knobs_summary",)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _add_seconds(iso: str, seconds: int) -> str:
    return (datetime.fromisoformat(iso) + timedelta(seconds=int(seconds))).isoformat()


def _is_expired(lease_iso: Optional[str], now_iso: str) -> bool:
    if not lease_iso:
        return False
    return datetime.fromisoformat(lease_iso) < datetime.fromisoformat(now_iso)


def _assert_opaque_artifact_refs(artifact_refs: Optional[List[str]]) -> None:
    """Persistence invariant: artifact handles are opaque — never raw URLs/keys."""
    for ref in artifact_refs or []:
        low = str(ref).lower()
        if "http://" in low or "https://" in low:
            raise ValueError("artifact_refs must be opaque handles, not raw URLs")
        if "x-amz" in low or "signature=" in low or "sig=" in low:
            raise ValueError("artifact_refs must not carry signing parameters")


@runtime_checkable
class IJobStateStore(Protocol):
    """Swappable durable job/trace store interface."""

    def create_job(
        self, task_id: str, *, target_shots: int, knobs_summary: Optional[Dict[str, Any]] = None
    ) -> str: ...

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]: ...

    def get_jobs_for_task(self, task_id: str) -> List[Dict[str, Any]]: ...

    def transition_state(
        self, job_id: str, target_state: str, *, failure_reason_code: Optional[str] = None,
        increment_retry: bool = False,
    ) -> Dict[str, Any]: ...

    def append_trace(
        self, job_id: str, *, phase: str, status: str, started_at: str,
        shot_id: Optional[str] = None, ended_at: Optional[str] = None,
        elapsed_ms: Optional[int] = None, provider_status_class: Optional[str] = None,
        fallback_reason_code: Optional[str] = None, artifact_refs: Optional[List[str]] = None,
    ) -> str: ...

    def update_trace(
        self, trace_id: str, *, status: str, ended_at: str,
        elapsed_ms: Optional[int] = None, provider_status_class: Optional[str] = None,
        fallback_reason_code: Optional[str] = None, artifact_refs: Optional[List[str]] = None,
    ) -> Dict[str, Any]: ...

    def get_traces(self, job_id: str) -> List[Dict[str, Any]]: ...

    def claim_next_queued_job(self, worker_id: str, *, lease_seconds: int, now: Optional[str] = None) -> Optional[Dict[str, Any]]: ...

    def heartbeat(self, job_id: str, worker_id: str, *, lease_seconds: int, now: Optional[str] = None) -> Optional[Dict[str, Any]]: ...

    def reclaim_expired_leases(self, *, max_retries: int, now: Optional[str] = None) -> List[str]: ...


class JobNotFoundError(LookupError):
    """Raised when a job_id / trace_id is not present in the store."""


# --------------------------------------------------------------------------
# In-memory implementation (hermetic tests + local harness)
# --------------------------------------------------------------------------
class InMemoryJobStateStore:
    """Volatile store for tests/harness only — never used in production."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._traces: Dict[str, Dict[str, Any]] = {}
        self._seq: Dict[str, int] = {}

    def create_job(self, task_id, *, target_shots, knobs_summary=None) -> str:
        if not task_id:
            raise ValueError("create_job requires task_id")
        job_id = _new_id("job")
        now = _utc_now()
        self._jobs[job_id] = {
            "job_id": job_id, "task_id": str(task_id), "state": st.JOB_STATE_QUEUED,
            "target_shots": int(target_shots), "knobs_summary": dict(knobs_summary or {}),
            "retry_count": 0, "failure_reason_code": None, "claimed_by": None,
            "lease_expires_at": None, "created_at": now, "updated_at": now,
        }
        self._seq[job_id] = 0
        return job_id

    def get_job(self, job_id) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        return dict(job) if job else None

    def get_jobs_for_task(self, task_id) -> List[Dict[str, Any]]:
        rows = [dict(j) for j in self._jobs.values() if j["task_id"] == str(task_id)]
        return sorted(rows, key=lambda j: j["created_at"])  # match SqlAlchemy ordering

    def transition_state(self, job_id, target_state, *, failure_reason_code=None, increment_retry=False):
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        st.assert_transition(job["state"], target_state)
        job["state"] = target_state
        if target_state not in st.ACTIVE_CLAIM_STATES:
            # leaving the active-claim lifecycle releases the claim + lease (B1 fix)
            job["claimed_by"] = None
            job["lease_expires_at"] = None
        if failure_reason_code is not None:
            job["failure_reason_code"] = failure_reason_code
        if increment_retry:
            job["retry_count"] = int(job["retry_count"]) + 1
        job["updated_at"] = _utc_now()
        return dict(job)

    def append_trace(self, job_id, *, phase, status, started_at, shot_id=None, ended_at=None,
                     elapsed_ms=None, provider_status_class=None, fallback_reason_code=None,
                     artifact_refs=None) -> str:
        # validate vocab/opacity first, then existence (matches SqlAlchemy impl)
        st.assert_valid_trace_event(phase)
        st.assert_valid_trace_status(status)
        _validate_optional_classes(provider_status_class, fallback_reason_code)
        _assert_opaque_artifact_refs(artifact_refs)
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        trace_id = _new_id("trc")
        self._seq[job_id] += 1
        self._traces[trace_id] = {
            "trace_id": trace_id, "job_id": job_id, "task_id": self._jobs[job_id]["task_id"],
            "shot_id": shot_id, "phase": phase, "status": status, "started_at": started_at,
            "ended_at": ended_at, "elapsed_ms": elapsed_ms,
            "provider_status_class": provider_status_class,
            "fallback_reason_code": fallback_reason_code,
            "artifact_refs": list(artifact_refs or []), "seq": self._seq[job_id],
        }
        return trace_id

    def update_trace(self, trace_id, *, status, ended_at, elapsed_ms=None,
                     provider_status_class=None, fallback_reason_code=None, artifact_refs=None):
        row = self._traces.get(trace_id)
        if not row:
            raise JobNotFoundError(trace_id)
        st.assert_valid_trace_status(status)
        _validate_optional_classes(provider_status_class, fallback_reason_code)
        _assert_opaque_artifact_refs(artifact_refs)
        row["status"] = status
        row["ended_at"] = ended_at
        if elapsed_ms is not None:
            row["elapsed_ms"] = int(elapsed_ms)
        if provider_status_class is not None:
            row["provider_status_class"] = provider_status_class
        if fallback_reason_code is not None:
            row["fallback_reason_code"] = fallback_reason_code
        if artifact_refs is not None:
            row["artifact_refs"] = list(artifact_refs)
        return dict(row)

    def get_traces(self, job_id) -> List[Dict[str, Any]]:
        rows = [dict(r) for r in self._traces.values() if r["job_id"] == job_id]
        return sorted(rows, key=lambda r: r["seq"])

    def claim_next_queued_job(self, worker_id, *, lease_seconds, now=None) -> Optional[Dict[str, Any]]:
        candidates = sorted(
            (j for j in self._jobs.values() if j["state"] == st.JOB_STATE_QUEUED),
            key=lambda j: j["created_at"],
        )
        if not candidates:
            return None
        now = now or _utc_now()
        job = candidates[0]
        st.assert_transition(job["state"], st.JOB_STATE_PLANNING)
        job["state"] = st.JOB_STATE_PLANNING
        job["claimed_by"] = worker_id
        job["lease_expires_at"] = _add_seconds(now, lease_seconds)
        job["updated_at"] = now
        return dict(job)

    def heartbeat(self, job_id, worker_id, *, lease_seconds, now=None) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        if not job or st.is_terminal(job["state"]) or job.get("claimed_by") != worker_id:
            return None
        now = now or _utc_now()
        job["lease_expires_at"] = _add_seconds(now, lease_seconds)
        job["updated_at"] = now
        return dict(job)

    def reclaim_expired_leases(self, *, max_retries, now=None) -> List[str]:
        now = now or _utc_now()
        reclaimed: List[str] = []
        for job in self._jobs.values():
            if st.is_terminal(job["state"]) or not job.get("claimed_by"):
                continue
            if not _is_expired(job.get("lease_expires_at"), now):
                continue
            st.assert_transition(job["state"], st.JOB_STATE_FAILED_RETRYABLE)
            new_retry = int(job["retry_count"]) + 1
            target = (
                st.JOB_STATE_FAILED_TERMINAL if new_retry >= int(max_retries)
                else st.JOB_STATE_QUEUED
            )
            st.assert_transition(st.JOB_STATE_FAILED_RETRYABLE, target)
            job["state"] = target
            job["retry_count"] = new_retry
            job["failure_reason_code"] = "lease_expired"
            job["claimed_by"] = None
            job["lease_expires_at"] = None
            job["updated_at"] = now
            reclaimed.append(job["job_id"])
        return reclaimed


# --------------------------------------------------------------------------
# SQLAlchemy implementation (durable; Render Postgres in prod, SQLite locally)
# --------------------------------------------------------------------------
class SqlAlchemyJobStateStore:
    """Durable store reusing the app SQLAlchemy engine (Owner 2026-06-09)."""

    def __init__(self, session_factory=None) -> None:
        if session_factory is None:
            from gateway.app.db import SessionLocal  # lazy: avoid import at module load
            session_factory = SessionLocal
        self._session_factory = session_factory

    def _decode_job(self, row: GenerationJob) -> Dict[str, Any]:
        data = row.to_dict()
        if data.get("knobs_summary"):
            try:
                data["knobs_summary"] = json.loads(data["knobs_summary"])
            except (TypeError, ValueError):
                data["knobs_summary"] = {}
        else:
            data["knobs_summary"] = {}
        return data

    def _decode_trace(self, row: GenerationJobTrace) -> Dict[str, Any]:
        data = row.to_dict()
        if data.get("artifact_refs"):
            try:
                data["artifact_refs"] = json.loads(data["artifact_refs"])
            except (TypeError, ValueError):
                data["artifact_refs"] = []
        else:
            data["artifact_refs"] = []
        return data

    def create_job(self, task_id, *, target_shots, knobs_summary=None) -> str:
        if not task_id:
            raise ValueError("create_job requires task_id")
        job_id = _new_id("job")
        now = _utc_now()
        with self._session_factory() as session:
            session.add(
                GenerationJob(
                    job_id=job_id, task_id=str(task_id), state=st.JOB_STATE_QUEUED,
                    target_shots=int(target_shots),
                    knobs_summary=json.dumps(dict(knobs_summary or {}), ensure_ascii=False),
                    retry_count=0, created_at=now, updated_at=now,
                )
            )
            session.commit()
        return job_id

    def get_job(self, job_id) -> Optional[Dict[str, Any]]:
        with self._session_factory() as session:
            row = session.get(GenerationJob, job_id)
            return self._decode_job(row) if row else None

    def get_jobs_for_task(self, task_id) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            rows = (
                session.query(GenerationJob)
                .filter(GenerationJob.task_id == str(task_id))
                .order_by(GenerationJob.created_at)
                .all()
            )
            return [self._decode_job(r) for r in rows]

    def transition_state(self, job_id, target_state, *, failure_reason_code=None, increment_retry=False):
        with self._session_factory() as session:
            row = session.get(GenerationJob, job_id)
            if not row:
                raise JobNotFoundError(job_id)
            st.assert_transition(row.state, target_state)
            row.state = target_state
            if target_state not in st.ACTIVE_CLAIM_STATES:
                # leaving the active-claim lifecycle releases the claim + lease (B1 fix)
                row.claimed_by = None
                row.lease_expires_at = None
            if failure_reason_code is not None:
                row.failure_reason_code = failure_reason_code
            if increment_retry:
                row.retry_count = int(row.retry_count or 0) + 1
            row.updated_at = _utc_now()
            session.commit()
            return self._decode_job(row)

    def append_trace(self, job_id, *, phase, status, started_at, shot_id=None, ended_at=None,
                     elapsed_ms=None, provider_status_class=None, fallback_reason_code=None,
                     artifact_refs=None) -> str:
        st.assert_valid_trace_event(phase)
        st.assert_valid_trace_status(status)
        _validate_optional_classes(provider_status_class, fallback_reason_code)
        _assert_opaque_artifact_refs(artifact_refs)
        trace_id = _new_id("trc")
        with self._session_factory() as session:
            job = session.get(GenerationJob, job_id)
            if not job:
                raise JobNotFoundError(job_id)
            next_seq = (
                session.query(GenerationJobTrace)
                .filter(GenerationJobTrace.job_id == job_id)
                .count()
            ) + 1
            session.add(
                GenerationJobTrace(
                    trace_id=trace_id, job_id=job_id, task_id=job.task_id, shot_id=shot_id,
                    phase=phase, status=status, started_at=started_at, ended_at=ended_at,
                    elapsed_ms=elapsed_ms, provider_status_class=provider_status_class,
                    fallback_reason_code=fallback_reason_code,
                    artifact_refs=json.dumps(list(artifact_refs or []), ensure_ascii=False),
                    seq=next_seq,
                )
            )
            session.commit()
        return trace_id

    def update_trace(self, trace_id, *, status, ended_at, elapsed_ms=None,
                     provider_status_class=None, fallback_reason_code=None, artifact_refs=None):
        st.assert_valid_trace_status(status)
        _validate_optional_classes(provider_status_class, fallback_reason_code)
        _assert_opaque_artifact_refs(artifact_refs)
        with self._session_factory() as session:
            row = session.get(GenerationJobTrace, trace_id)
            if not row:
                raise JobNotFoundError(trace_id)
            row.status = status
            row.ended_at = ended_at
            if elapsed_ms is not None:
                row.elapsed_ms = int(elapsed_ms)
            if provider_status_class is not None:
                row.provider_status_class = provider_status_class
            if fallback_reason_code is not None:
                row.fallback_reason_code = fallback_reason_code
            if artifact_refs is not None:
                row.artifact_refs = json.dumps(list(artifact_refs), ensure_ascii=False)
            session.commit()
            return self._decode_trace(row)

    def get_traces(self, job_id) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            rows = (
                session.query(GenerationJobTrace)
                .filter(GenerationJobTrace.job_id == job_id)
                .order_by(GenerationJobTrace.seq)
                .all()
            )
            return [self._decode_trace(r) for r in rows]

    def claim_next_queued_job(self, worker_id, *, lease_seconds, now=None) -> Optional[Dict[str, Any]]:
        # Simple transactional claim. Concurrency hardening (Postgres
        # SELECT ... FOR UPDATE SKIP LOCKED) is a follow-up before high fan-out.
        now = now or _utc_now()
        with self._session_factory() as session:
            row = (
                session.query(GenerationJob)
                .filter(GenerationJob.state == st.JOB_STATE_QUEUED)
                .order_by(GenerationJob.created_at)
                .first()
            )
            if not row:
                return None
            st.assert_transition(row.state, st.JOB_STATE_PLANNING)
            row.state = st.JOB_STATE_PLANNING
            row.claimed_by = worker_id
            row.lease_expires_at = _add_seconds(now, lease_seconds)
            row.updated_at = now
            session.commit()
            return self._decode_job(row)

    def heartbeat(self, job_id, worker_id, *, lease_seconds, now=None) -> Optional[Dict[str, Any]]:
        now = now or _utc_now()
        with self._session_factory() as session:
            row = session.get(GenerationJob, job_id)
            if not row or st.is_terminal(row.state) or row.claimed_by != worker_id:
                return None
            row.lease_expires_at = _add_seconds(now, lease_seconds)
            row.updated_at = now
            session.commit()
            return self._decode_job(row)

    def reclaim_expired_leases(self, *, max_retries, now=None) -> List[str]:
        now = now or _utc_now()
        reclaimed: List[str] = []
        with self._session_factory() as session:
            rows = (
                session.query(GenerationJob)
                .filter(GenerationJob.claimed_by.isnot(None))
                .all()
            )
            for row in rows:
                if st.is_terminal(row.state) or not _is_expired(row.lease_expires_at, now):
                    continue
                st.assert_transition(row.state, st.JOB_STATE_FAILED_RETRYABLE)
                new_retry = int(row.retry_count or 0) + 1
                target = (
                    st.JOB_STATE_FAILED_TERMINAL if new_retry >= int(max_retries)
                    else st.JOB_STATE_QUEUED
                )
                st.assert_transition(st.JOB_STATE_FAILED_RETRYABLE, target)
                row.state = target
                row.retry_count = new_retry
                row.failure_reason_code = "lease_expired"
                row.claimed_by = None
                row.lease_expires_at = None
                row.updated_at = now
                reclaimed.append(row.job_id)
            session.commit()
        return reclaimed


def _validate_optional_classes(
    provider_status_class: Optional[str], fallback_reason_code: Optional[str]
) -> None:
    if provider_status_class is not None and provider_status_class not in st.PROVIDER_STATUS_CLASSES:
        raise st.InvalidJobStateError(f"unknown provider_status_class: {provider_status_class!r}")
    if fallback_reason_code is not None and fallback_reason_code not in st.FALLBACK_REASON_CODES:
        raise st.InvalidJobStateError(f"unknown fallback_reason_code: {fallback_reason_code!r}")


def get_job_state_store() -> IJobStateStore:
    """Factory: the durable SQLAlchemy store (default). Tests inject impls directly."""
    return SqlAlchemyJobStateStore()
