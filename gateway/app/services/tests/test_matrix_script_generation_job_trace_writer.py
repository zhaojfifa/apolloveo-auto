"""PR-1 — durable trace writer tests (incl. the TRACE_GAP closure + leak guard)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.app.services.matrix_script.generation_job_runtime import (
    InMemoryJobStateStore,
    JobTraceWriter,
    SqlAlchemyJobStateStore,
    assert_no_job_trace_leak,
    ensure_generation_job_tables,
    run_local_trace_harness,
    job_state as st,
)


def _job(store):
    job_id = store.create_job("t1", target_shots=1)
    store.transition_state(job_id, st.JOB_STATE_PLANNING)
    return job_id


def test_begin_phase_persists_running_row_before_end() -> None:
    store = InMemoryJobStateStore()
    job_id = _job(store)
    writer = JobTraceWriter(store, job_id)
    tid = writer.begin_phase("provider_poll", shot_id="shot01")
    rows = store.get_traces(job_id)
    assert len(rows) == 1
    assert rows[0]["trace_id"] == tid
    assert rows[0]["status"] == st.TRACE_STATUS_RUNNING
    assert rows[0]["phase"] == "provider_poll"
    assert rows[0]["shot_id"] == "shot01"
    assert rows[0]["ended_at"] is None


def test_trace_gap_closure_worker_kill_leaves_running_row() -> None:
    # Simulate a worker kill mid-phase: begin_phase, then NEVER end_phase.
    # The failing phase must remain identifiable from durable state alone
    # (the whole point of PR-1 — no dependency on ephemeral Render logs).
    store = InMemoryJobStateStore()
    job_id = _job(store)
    store.transition_state(job_id, st.JOB_STATE_PROVIDER_GENERATING)
    writer = JobTraceWriter(store, job_id)
    writer.begin_phase("provider_submit", shot_id="shot01")
    # <-- worker dies here; no end_phase call -->
    running = [r for r in store.get_traces(job_id) if r["status"] == st.TRACE_STATUS_RUNNING]
    assert len(running) == 1
    assert running[0]["phase"] == "provider_submit"
    assert running[0]["ended_at"] is None


def test_end_phase_sets_status_end_and_elapsed() -> None:
    store = InMemoryJobStateStore()
    job_id = _job(store)
    writer = JobTraceWriter(store, job_id)
    tid = writer.begin_phase("compose_start")
    row = writer.end_phase(tid, status=st.TRACE_STATUS_SUCCEEDED)
    assert row["status"] == st.TRACE_STATUS_SUCCEEDED
    assert row["ended_at"] is not None
    assert row["elapsed_ms"] is not None and row["elapsed_ms"] >= 0


def test_end_phase_rejects_running_status() -> None:
    store = InMemoryJobStateStore()
    job_id = _job(store)
    writer = JobTraceWriter(store, job_id)
    tid = writer.begin_phase("compose_start")
    with pytest.raises(ValueError):
        writer.end_phase(tid, status=st.TRACE_STATUS_RUNNING)


def test_assert_no_job_trace_leak_passes_clean_row() -> None:
    assert_no_job_trace_leak(
        {"phase": "provider_poll", "status": "succeeded", "artifact_refs": ["r2:clip/shot01"]}
    )


@pytest.mark.parametrize(
    "bad",
    [
        {"api_key": "sk-123"},
        {"download_url": "https://cdn.example.com/clip.mp4"},
        {"note": "akool task created"},
        {"path": "/Users/foo/clip.mp4"},
        {"authorization": "Bearer xyz"},
    ],
)
def test_assert_no_job_trace_leak_rejects_secrets(bad) -> None:
    with pytest.raises(ValueError):
        assert_no_job_trace_leak(bad)


def test_local_harness_reaches_result_ready_no_leak() -> None:
    out = run_local_trace_harness()
    assert out["job"]["state"] == st.JOB_STATE_RESULT_READY
    phases = [t["phase"] for t in out["traces"]]
    assert phases[0] == "generation_start"
    assert "upload_start" in phases
    assert all(t["status"] != st.TRACE_STATUS_RUNNING for t in out["traces"])
    for row in out["traces"]:
        assert_no_job_trace_leak(row)


def test_local_harness_runs_on_sqlalchemy_store(tmp_path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'harness.db'}", connect_args={"check_same_thread": False}
    )
    ensure_generation_job_tables(engine)
    store = SqlAlchemyJobStateStore(
        session_factory=sessionmaker(bind=engine, autoflush=False, autocommit=False)
    )
    out = run_local_trace_harness(store)
    assert out["job"]["state"] == st.JOB_STATE_RESULT_READY
    assert len(out["traces"]) >= 6
