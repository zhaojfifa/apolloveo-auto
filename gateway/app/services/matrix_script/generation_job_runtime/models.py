"""Matrix Script — Production Job Runtime — durable ORM models (PR-1).

Two additive tables on the EXISTING app SQLAlchemy ``Base`` / engine (Owner
decision 2026-06-09: reuse the app DB; one Render Postgres for tasks + jobs +
trace). No change to the ``tasks`` table or any existing model. Timestamps are
ISO-8601 UTC strings (matching the codebase ``_utc_now()`` convention); JSON-ish
fields are stored as TEXT for SQLite/Postgres portability.

Tables created idempotently by ``ensure_generation_job_tables`` (mirrors the
``ensure_provider_config_table`` precedent) and also by the global
``Base.metadata.create_all`` at startup.
"""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import Column, Integer, String, Text

from gateway.app.db import Base


class GenerationJob(Base):
    """One generation job for a Matrix Script task (a task may have many jobs)."""

    __tablename__ = "generation_jobs"

    job_id = Column(String(64), primary_key=True)
    task_id = Column(String(64), index=True, nullable=False)
    state = Column(String(40), nullable=False)
    target_shots = Column(Integer, nullable=False, default=1)
    knobs_summary = Column(Text, nullable=True)  # JSON dict (operator-safe knob ints/bools)
    retry_count = Column(Integer, nullable=False, default=0)
    failure_reason_code = Column(String(64), nullable=True)
    claimed_by = Column(String(120), nullable=True)
    lease_expires_at = Column(String(40), nullable=True)  # ISO-8601 UTC
    created_at = Column(String(40), nullable=False)  # ISO-8601 UTC
    updated_at = Column(String(40), nullable=False)  # ISO-8601 UTC

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "task_id": self.task_id,
            "state": self.state,
            "target_shots": self.target_shots,
            "knobs_summary": self.knobs_summary,
            "retry_count": self.retry_count,
            "failure_reason_code": self.failure_reason_code,
            "claimed_by": self.claimed_by,
            "lease_expires_at": self.lease_expires_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class GenerationJobTrace(Base):
    """One durable trace row per phase boundary (Gate Spec §6).

    Written at phase START (``status=running``, ``started_at`` set) BEFORE the
    heavy work, updated at phase END — so a worker kill always leaves the failing
    phase identifiable (the TRACE_GAP closure).
    """

    __tablename__ = "generation_job_trace"

    trace_id = Column(String(64), primary_key=True)
    job_id = Column(String(64), index=True, nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    shot_id = Column(String(64), nullable=True)
    phase = Column(String(48), nullable=False)
    status = Column(String(24), nullable=False)
    started_at = Column(String(40), nullable=False)  # ISO-8601 UTC
    ended_at = Column(String(40), nullable=True)  # ISO-8601 UTC
    elapsed_ms = Column(Integer, nullable=True)
    provider_status_class = Column(String(24), nullable=True)
    fallback_reason_code = Column(String(40), nullable=True)
    artifact_refs = Column(Text, nullable=True)  # JSON list of OPAQUE handles only
    seq = Column(Integer, nullable=False, default=0)  # monotonic per job for ordering

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "job_id": self.job_id,
            "task_id": self.task_id,
            "shot_id": self.shot_id,
            "phase": self.phase,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "elapsed_ms": self.elapsed_ms,
            "provider_status_class": self.provider_status_class,
            "fallback_reason_code": self.fallback_reason_code,
            "artifact_refs": self.artifact_refs,
            "seq": self.seq,
        }


def ensure_generation_job_tables(engine) -> None:
    """Idempotently create the job + trace tables (SQLite/Postgres portable)."""
    Base.metadata.create_all(
        bind=engine,
        tables=[GenerationJob.__table__, GenerationJobTrace.__table__],
        checkfirst=True,
    )
