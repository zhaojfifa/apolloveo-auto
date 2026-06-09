"""PR-2 — worker runtime skeleton: concurrency, crash-safety, lease/heartbeat/retry.

Dry-run only (no provider/ffmpeg/upload). Parametrized over both store impls.
Lease timing is deterministic via explicit ``now`` ISO strings (no real sleeps).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gateway.app.services.matrix_script.generation_job_runtime import (
    InMemoryJobStateStore,
    SqlAlchemyJobStateStore,
    WorkerRuntime,
    assert_no_job_trace_leak,
    ensure_generation_job_tables,
    enqueue_generation_job,
    job_state as st,
)

_BASE = datetime(2026, 6, 9, 12, 0, 0, tzinfo=timezone.utc)


def _iso(offset_seconds: int = 0) -> str:
    return (_BASE + timedelta(seconds=offset_seconds)).isoformat()


def _sqlalchemy_store(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'worker.db'}", connect_args={"check_same_thread": False}
    )
    ensure_generation_job_tables(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SqlAlchemyJobStateStore(session_factory=factory)


@pytest.fixture(params=["memory", "sqlalchemy"])
def store(request, tmp_path):
    if request.param == "memory":
        return InMemoryJobStateStore()
    return _sqlalchemy_store(tmp_path)


# --- vocabulary -------------------------------------------------------------
def test_worker_events_closed_and_subset_of_trace_events() -> None:
    assert st.WORKER_EVENTS == {
        "worker_started", "job_claimed", "heartbeat", "dry_run_started",
        "dry_run_completed", "job_completed", "job_failed_retryable", "job_failed_terminal",
    }
    assert st.WORKER_EVENTS <= st.TRACE_EVENTS
    assert st.TRACE_PHASES <= st.TRACE_EVENTS
    assert st.assert_valid_trace_event("worker_started") == "worker_started"
    assert st.assert_valid_trace_event("generation_start") == "generation_start"
    with pytest.raises(st.InvalidJobStateError):
        st.assert_valid_trace_event("nope")


# --- required: concurrency + crash-safety -----------------------------------
def test_one_queued_job_claimed_once(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    w = WorkerRuntime(store, worker_id="w1")
    r1 = w.run_once(now=_iso(0))
    assert r1["claimed"] is True and r1["final_state"] == st.JOB_STATE_RESULT_READY
    r2 = w.run_once(now=_iso(1))
    assert r2["claimed"] is False


def test_two_workers_cannot_claim_same_job(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    a = store.claim_next_queued_job("w1", lease_seconds=600, now=_iso(0))
    b = store.claim_next_queued_job("w2", lease_seconds=600, now=_iso(0))
    assert a is not None and a["claimed_by"] == "w1"
    assert b is None


def test_lease_expiry_allows_reclaim(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    claimed = store.claim_next_queued_job("w1", lease_seconds=10, now=_iso(0))  # lease = T+10
    assert claimed["state"] == st.JOB_STATE_PLANNING
    reclaimed = store.reclaim_expired_leases(max_retries=3, now=_iso(20))  # past T+10
    assert claimed["job_id"] in reclaimed
    job = store.get_job(claimed["job_id"])
    assert job["state"] == st.JOB_STATE_QUEUED
    assert job["retry_count"] == 1 and job["claimed_by"] is None
    again = store.claim_next_queued_job("w2", lease_seconds=10, now=_iso(21))
    assert again["job_id"] == claimed["job_id"] and again["claimed_by"] == "w2"


def test_heartbeat_extends_lease(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    claimed = store.claim_next_queued_job("w1", lease_seconds=10, now=_iso(0))  # lease = T+10
    hb = store.heartbeat(claimed["job_id"], "w1", lease_seconds=100, now=_iso(5))  # lease = T+105
    assert hb is not None
    # at T+20 the original lease (T+10) would be expired, but heartbeat extended it
    reclaimed = store.reclaim_expired_leases(max_retries=3, now=_iso(20))
    assert claimed["job_id"] not in reclaimed
    assert store.get_job(claimed["job_id"])["state"] == st.JOB_STATE_PLANNING
    # a non-claimant cannot heartbeat
    assert store.heartbeat(claimed["job_id"], "intruder", lease_seconds=100, now=_iso(6)) is None


def test_failed_job_records_trace_and_leaves_open_row(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    w = WorkerRuntime(store, worker_id="w1", max_retries=3)
    r = w.run_once(simulate_failure=True)
    assert r["final_state"] == st.JOB_STATE_FAILED_RETRYABLE
    job = store.get_job(r["job_id"])
    assert job["state"] == st.JOB_STATE_FAILED_RETRYABLE and job["retry_count"] == 1
    traces = store.get_traces(r["job_id"])
    assert "job_failed_retryable" in [t["phase"] for t in traces]
    # crash evidence: the OPEN dry_run_started running row persists (TRACE_GAP closure)
    open_running = [t for t in traces if t["status"] == st.TRACE_STATUS_RUNNING]
    assert any(t["phase"] == "dry_run_started" and t["ended_at"] is None for t in open_running)


def test_terminal_job_not_reclaimed(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    w = WorkerRuntime(store, worker_id="w1")
    r = w.run_once(now=_iso(0))
    assert r["final_state"] == st.JOB_STATE_RESULT_READY
    reclaimed = store.reclaim_expired_leases(max_retries=3, now=_iso(99999))  # far future
    assert r["job_id"] not in reclaimed
    assert store.get_job(r["job_id"])["state"] == st.JOB_STATE_RESULT_READY


# --- required: retry budget -> terminal -------------------------------------
def test_retry_budget_failure_reaches_terminal(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    w = WorkerRuntime(store, worker_id="w1", max_retries=1)  # first failure => terminal
    r = w.run_once(simulate_failure=True)
    assert r["final_state"] == st.JOB_STATE_FAILED_TERMINAL
    assert store.get_job(r["job_id"])["state"] == st.JOB_STATE_FAILED_TERMINAL
    assert "job_failed_terminal" in [t["phase"] for t in store.get_traces(r["job_id"])]


def test_reclaim_to_terminal_when_retries_exhausted(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    claimed = store.claim_next_queued_job("w1", lease_seconds=1, now=_iso(0))
    reclaimed = store.reclaim_expired_leases(max_retries=1, now=_iso(10))  # exhausted => terminal
    assert claimed["job_id"] in reclaimed
    assert store.get_job(claimed["job_id"])["state"] == st.JOB_STATE_FAILED_TERMINAL


# --- happy-path lifecycle events + safety -----------------------------------
def test_happy_path_writes_all_lifecycle_events_no_leak(store) -> None:
    enqueue_generation_job({"task_id": "t1"}, store=store)
    w = WorkerRuntime(store, worker_id="w1")
    r = w.run_once(now=_iso(0))
    assert r["final_state"] == st.JOB_STATE_RESULT_READY
    events = [t["phase"] for t in store.get_traces(r["job_id"])]
    for ev in (
        "worker_started", "job_claimed", "heartbeat",
        "dry_run_started", "dry_run_completed", "job_completed",
    ):
        assert ev in events
    for row in store.get_traces(r["job_id"]):
        assert_no_job_trace_leak(row)
    # the job record has no publish-truth field => worker cannot set it true
    assert "official_publish_ready" not in store.get_job(r["job_id"])


def test_claim_released_on_leaving_active_lifecycle(store) -> None:
    # B1 root-cause guard: claim/lease are cleared on entering a non-active state.
    enqueue_generation_job({"task_id": "t1"}, store=store)
    claimed = store.claim_next_queued_job("w1", lease_seconds=600, now=_iso(0))
    assert claimed["claimed_by"] == "w1" and claimed["lease_expires_at"]
    failed = store.transition_state(claimed["job_id"], st.JOB_STATE_FAILED_RETRYABLE)
    assert failed["claimed_by"] is None and failed["lease_expires_at"] is None


def test_reclaim_after_worker_failure_does_not_poison_queue(store) -> None:
    # B1 regression: a worker-induced failed_retryable must NOT crash a later
    # reclaim sweep (it did before: failed_retryable -> failed_retryable illegal).
    enqueue_generation_job({"task_id": "bad"}, store=store)
    w = WorkerRuntime(store, worker_id="w1", lease_seconds=10, max_retries=3)
    bad = w.run_once(simulate_failure=True, now=_iso(0))
    assert bad["final_state"] == st.JOB_STATE_FAILED_RETRYABLE
    assert store.get_job(bad["job_id"])["claimed_by"] is None  # claim released
    # a later run with the lease long past must not raise; a healthy job still runs
    enqueue_generation_job({"task_id": "good"}, store=store)
    r = w.run_once(now=_iso(100000))
    assert r["claimed"] is True and r["final_state"] == st.JOB_STATE_RESULT_READY


def test_run_loop_processes_until_empty(store) -> None:
    for i in range(3):
        enqueue_generation_job({"task_id": f"t{i}"}, store=store)
    results = WorkerRuntime(store, worker_id="w1").run_loop()
    assert len([r for r in results if r.get("claimed")]) == 3
    assert results[-1]["claimed"] is False


# --- CLI (hermetic, injected store) -----------------------------------------
def test_cli_once_processes_a_job() -> None:
    from gateway.app.services.matrix_script.generation_job_runtime import cli

    store = InMemoryJobStateStore()
    enqueue_generation_job({"task_id": "t1"}, store=store)
    rc = cli.main(["--worker-id", "cli-1", "--once"], store=store)
    assert rc == 0
    assert store.get_jobs_for_task("t1")[0]["state"] == st.JOB_STATE_RESULT_READY
