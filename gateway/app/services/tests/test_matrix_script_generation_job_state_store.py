"""PR-1 — durable job-state store tests (parametrized: in-memory + SQLAlchemy).

Proves the two impls of the swappable interface behave equivalently. The
SQLAlchemy impl runs against a hermetic tmp SQLite file (so sessions share the
schema); prod uses Render Postgres via the same code path.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.app.services.matrix_script.generation_job_runtime import (
    InMemoryJobStateStore,
    JobNotFoundError,
    SqlAlchemyJobStateStore,
    ensure_generation_job_tables,
    job_state as st,
)


def _sqlalchemy_store(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'jobs.db'}", connect_args={"check_same_thread": False}
    )
    ensure_generation_job_tables(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SqlAlchemyJobStateStore(session_factory=factory)


@pytest.fixture(params=["memory", "sqlalchemy"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryJobStateStore()
    return _sqlalchemy_store(tmp_path)


def test_create_job_starts_queued(store) -> None:
    job_id = store.create_job("task-1", target_shots=1, knobs_summary={"target_shots": 1})
    job = store.get_job(job_id)
    assert job is not None
    assert job["state"] == st.JOB_STATE_QUEUED
    assert job["task_id"] == "task-1"
    assert job["target_shots"] == 1
    assert job["knobs_summary"] == {"target_shots": 1}
    assert job["job_id"].startswith("job-")


def test_create_job_requires_task_id(store) -> None:
    with pytest.raises(ValueError):
        store.create_job("", target_shots=1)


def test_get_jobs_for_task(store) -> None:
    a = store.create_job("task-A", target_shots=1)
    b = store.create_job("task-A", target_shots=2)
    store.create_job("task-B", target_shots=1)
    ids = {j["job_id"] for j in store.get_jobs_for_task("task-A")}
    assert ids == {a, b}


def test_valid_transition_and_invalid_rejected(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    updated = store.transition_state(job_id, st.JOB_STATE_PLANNING)
    assert updated["state"] == st.JOB_STATE_PLANNING
    with pytest.raises(st.InvalidJobStateTransitionError):
        store.transition_state(job_id, st.JOB_STATE_RESULT_READY)  # planning -> result_ready illegal


def test_transition_on_missing_job_raises(store) -> None:
    with pytest.raises(JobNotFoundError):
        store.transition_state("job-missing", st.JOB_STATE_PLANNING)


def test_failure_reason_and_retry_increment(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    store.transition_state(job_id, st.JOB_STATE_PLANNING)
    store.transition_state(job_id, st.JOB_STATE_FAILED_RETRYABLE, failure_reason_code="provider_timeout")
    j = store.transition_state(job_id, st.JOB_STATE_QUEUED, increment_retry=True)
    assert j["failure_reason_code"] == "provider_timeout"
    assert j["retry_count"] == 1


def test_append_and_get_traces_ordered(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    t1 = store.append_trace(job_id, phase="generation_start", status="running", started_at="2026-06-09T00:00:00+00:00")
    t2 = store.append_trace(job_id, phase="prompt_build", status="running", started_at="2026-06-09T00:00:01+00:00", shot_id="shot01")
    traces = store.get_traces(job_id)
    assert [t["trace_id"] for t in traces] == [t1, t2]
    assert [t["seq"] for t in traces] == [1, 2]
    assert traces[1]["shot_id"] == "shot01"


def test_update_trace_sets_end_and_class(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    tid = store.append_trace(job_id, phase="provider_poll", status="running", started_at="2026-06-09T00:00:00+00:00", shot_id="shot01")
    row = store.update_trace(
        tid, status="succeeded", ended_at="2026-06-09T00:00:05+00:00", elapsed_ms=5000,
        provider_status_class="ok", artifact_refs=["r2:clip/shot01"],
    )
    assert row["status"] == "succeeded"
    assert row["ended_at"] == "2026-06-09T00:00:05+00:00"
    assert row["elapsed_ms"] == 5000
    assert row["provider_status_class"] == "ok"
    assert row["artifact_refs"] == ["r2:clip/shot01"]


def test_trace_rejects_unknown_enums(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    with pytest.raises(st.InvalidJobStateError):
        store.append_trace(job_id, phase="not_a_phase", status="running", started_at="x")
    with pytest.raises(st.InvalidJobStateError):
        store.append_trace(job_id, phase="provider_poll", status="bogus", started_at="x")
    with pytest.raises(st.InvalidJobStateError):
        store.append_trace(job_id, phase="provider_poll", status="running", started_at="x", provider_status_class="weird")


def test_trace_rejects_non_opaque_artifact_refs(store) -> None:
    job_id = store.create_job("task-1", target_shots=1)
    with pytest.raises(ValueError):
        store.append_trace(
            job_id, phase="provider_download", status="succeeded", started_at="x",
            artifact_refs=["https://cdn.example.com/clip.mp4?X-Amz-Signature=abc"],
        )


def test_claim_next_queued_job(store) -> None:
    first = store.create_job("task-A", target_shots=1)
    store.create_job("task-B", target_shots=1)
    claimed = store.claim_next_queued_job("worker-1", lease_seconds=600)
    assert claimed is not None
    assert claimed["job_id"] == first  # oldest queued first
    assert claimed["state"] == st.JOB_STATE_PLANNING
    assert claimed["claimed_by"] == "worker-1"
    assert claimed["lease_expires_at"]


def test_claim_returns_none_when_no_queued(store) -> None:
    job_id = store.create_job("task-A", target_shots=1)
    store.transition_state(job_id, st.JOB_STATE_PLANNING)  # no longer queued
    assert store.claim_next_queued_job("worker-1", lease_seconds=600) is None
