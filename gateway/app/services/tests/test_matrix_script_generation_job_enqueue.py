"""PR-1 — thin enqueue seam tests (additive; no provider/ffmpeg/worker)."""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.generation_job_runtime import (
    InMemoryJobStateStore,
    assert_no_job_trace_leak,
    enqueue_generation_job,
    job_state as st,
)

_KNOBS = (
    "MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS",
    "MATRIX_SCRIPT_PROVIDER_ATTEMPT_CAP",
    "MATRIX_SCRIPT_PROVIDER_ENABLE_GEMINI_RETRY",
    "MATRIX_SCRIPT_AKOOL_REAL",
)


def _clear_knobs(monkeypatch):
    for name in _KNOBS:
        monkeypatch.delenv(name, raising=False)


def test_enqueue_creates_queued_job_default_shots(monkeypatch) -> None:
    _clear_knobs(monkeypatch)
    store = InMemoryJobStateStore()
    job_id = enqueue_generation_job({"task_id": "task-1", "kind": "matrix_script"}, store=store)
    job = store.get_job(job_id)
    assert job is not None
    assert job["state"] == st.JOB_STATE_QUEUED
    assert job["task_id"] == "task-1"
    assert job["target_shots"] == 3  # current default behavior
    assert job["knobs_summary"]["target_shots"] == 3


def test_enqueue_respects_target_shots_knob(monkeypatch) -> None:
    _clear_knobs(monkeypatch)
    monkeypatch.setenv("MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS", "1")
    store = InMemoryJobStateStore()
    job_id = enqueue_generation_job({"task_id": "task-2"}, store=store)
    job = store.get_job(job_id)
    assert job["target_shots"] == 1
    assert job["knobs_summary"]["target_shots"] == 1


def test_enqueue_requires_task_id() -> None:
    store = InMemoryJobStateStore()
    with pytest.raises(ValueError):
        enqueue_generation_job({"kind": "matrix_script"}, store=store)


def test_enqueue_knobs_summary_is_operator_safe(monkeypatch) -> None:
    _clear_knobs(monkeypatch)
    store = InMemoryJobStateStore()
    job_id = enqueue_generation_job({"task_id": "task-3"}, store=store)
    job = store.get_job(job_id)
    # vendor-neutral keys only — no vendor/model/secret token in the stored summary
    assert set(job["knobs_summary"]) == {"target_shots", "attempt_cap", "refine_retry", "real_provider"}
    assert_no_job_trace_leak(job["knobs_summary"])


def test_enqueue_accepts_attribute_style_task() -> None:
    class _Task:
        task_id = "task-obj"

    store = InMemoryJobStateStore()
    job_id = enqueue_generation_job(_Task(), store=store)
    assert store.get_job(job_id)["task_id"] == "task-obj"
