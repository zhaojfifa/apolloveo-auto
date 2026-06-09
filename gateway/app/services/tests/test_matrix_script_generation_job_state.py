"""PR-1 — closed job-state model + trace vocabulary tests."""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.generation_job_runtime import job_state as st


def test_closed_state_set_is_exactly_eleven() -> None:
    assert st.JOB_STATES == {
        "queued", "planning", "provider_generating", "provider_polling",
        "provider_clip_ready", "composing", "uploading", "result_ready",
        "failed_retryable", "failed_terminal", "cancelled",
    }


def test_terminal_states() -> None:
    assert st.TERMINAL_STATES == {"result_ready", "failed_terminal", "cancelled"}
    for term in st.TERMINAL_STATES:
        assert st.is_terminal(term)
        assert st.ALLOWED_TRANSITIONS[term] == frozenset()


def test_every_state_has_a_transition_entry() -> None:
    assert set(st.ALLOWED_TRANSITIONS) == set(st.JOB_STATES)


def test_transition_targets_are_all_valid_states() -> None:
    for targets in st.ALLOWED_TRANSITIONS.values():
        for target in targets:
            assert target in st.JOB_STATES


def test_happy_path_transitions_are_allowed() -> None:
    chain = [
        ("queued", "planning"), ("planning", "provider_generating"),
        ("provider_generating", "provider_polling"),
        ("provider_polling", "provider_clip_ready"),
        ("provider_clip_ready", "composing"), ("composing", "uploading"),
        ("uploading", "result_ready"),
    ]
    for cur, nxt in chain:
        assert st.assert_transition(cur, nxt) == nxt


def test_retry_loop_and_terminal_paths() -> None:
    assert st.assert_transition("failed_retryable", "queued") == "queued"
    assert st.assert_transition("failed_retryable", "failed_terminal") == "failed_terminal"
    assert st.assert_transition("provider_clip_ready", "provider_generating") == "provider_generating"


def test_illegal_transition_raises() -> None:
    with pytest.raises(st.InvalidJobStateTransitionError):
        st.assert_transition("queued", "result_ready")
    with pytest.raises(st.InvalidJobStateTransitionError):
        st.assert_transition("result_ready", "queued")  # terminal has no exit
    with pytest.raises(st.InvalidJobStateTransitionError):
        st.assert_transition("uploading", "composing")  # no backward jump


def test_unknown_state_raises() -> None:
    with pytest.raises(st.InvalidJobStateError):
        st.assert_valid_state("nope")
    with pytest.raises(st.InvalidJobStateError):
        st.assert_transition("nope", "queued")


def test_trace_vocabulary_closed_sets() -> None:
    assert "generation_start" in st.TRACE_PHASES
    assert "upload_done" in st.TRACE_PHASES
    assert st.TRACE_STATUSES == {
        "running", "succeeded", "fallback", "failed", "skipped", "cancelled"
    }
    assert "ok" in st.PROVIDER_STATUS_CLASSES
    assert "none" in st.FALLBACK_REASON_CODES


def test_trace_validators_reject_unknown() -> None:
    assert st.assert_valid_phase("provider_poll") == "provider_poll"
    assert st.assert_valid_trace_status("running") == "running"
    with pytest.raises(st.InvalidJobStateError):
        st.assert_valid_phase("not_a_phase")
    with pytest.raises(st.InvalidJobStateError):
        st.assert_valid_trace_status("not_a_status")
