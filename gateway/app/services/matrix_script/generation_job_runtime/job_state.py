"""Matrix Script — Production Job Runtime — closed job-state model + trace vocab.

PR-1 (Durable Job State + Trace Writer) under the signed
``docs/design/MATRIX_SCRIPT_PRODUCTION_JOB_RUNTIME_GATE_SPEC_20260609.md`` and
``docs/contracts/matrix_script/generation_job_runtime_contract_v1.md``.

This module owns ONLY the closed vocabulary + transition rules (no I/O, no DB, no
provider, no ffmpeg, no worker). House style mirrors the existing closed-enum
pattern (string constants + ``frozenset`` + validators; no ``Enum`` classes).
"""
from __future__ import annotations

from typing import Dict, FrozenSet

# --- Closed job-state set (Gate Spec §5) -----------------------------------
JOB_STATE_QUEUED = "queued"
JOB_STATE_PLANNING = "planning"
JOB_STATE_PROVIDER_GENERATING = "provider_generating"
JOB_STATE_PROVIDER_POLLING = "provider_polling"
JOB_STATE_PROVIDER_CLIP_READY = "provider_clip_ready"
JOB_STATE_COMPOSING = "composing"
JOB_STATE_UPLOADING = "uploading"
JOB_STATE_RESULT_READY = "result_ready"
JOB_STATE_FAILED_RETRYABLE = "failed_retryable"
JOB_STATE_FAILED_TERMINAL = "failed_terminal"
JOB_STATE_CANCELLED = "cancelled"

JOB_STATES: FrozenSet[str] = frozenset(
    {
        JOB_STATE_QUEUED,
        JOB_STATE_PLANNING,
        JOB_STATE_PROVIDER_GENERATING,
        JOB_STATE_PROVIDER_POLLING,
        JOB_STATE_PROVIDER_CLIP_READY,
        JOB_STATE_COMPOSING,
        JOB_STATE_UPLOADING,
        JOB_STATE_RESULT_READY,
        JOB_STATE_FAILED_RETRYABLE,
        JOB_STATE_FAILED_TERMINAL,
        JOB_STATE_CANCELLED,
    }
)

# Terminal states never transition out (Gate Spec §5 SM-2).
TERMINAL_STATES: FrozenSet[str] = frozenset(
    {JOB_STATE_RESULT_READY, JOB_STATE_FAILED_TERMINAL, JOB_STATE_CANCELLED}
)

# States where a worker actively holds the job: claim + lease are meaningful ONLY
# here. Transitioning to any other state releases the claim/lease (PR-2 B1 fix:
# prevents a stale claim on failed_retryable from poisoning the reclaim sweep).
ACTIVE_CLAIM_STATES: FrozenSet[str] = frozenset(
    {
        JOB_STATE_PLANNING,
        JOB_STATE_PROVIDER_GENERATING,
        JOB_STATE_PROVIDER_POLLING,
        JOB_STATE_PROVIDER_CLIP_READY,
        JOB_STATE_COMPOSING,
        JOB_STATE_UPLOADING,
    }
)

# Explicit, closed transition graph (Gate Spec §5 table).
ALLOWED_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    JOB_STATE_QUEUED: frozenset({JOB_STATE_PLANNING, JOB_STATE_CANCELLED}),
    JOB_STATE_PLANNING: frozenset(
        {
            JOB_STATE_PROVIDER_GENERATING,
            JOB_STATE_FAILED_RETRYABLE,
            JOB_STATE_FAILED_TERMINAL,
            JOB_STATE_CANCELLED,
        }
    ),
    JOB_STATE_PROVIDER_GENERATING: frozenset(
        {
            JOB_STATE_PROVIDER_POLLING,
            JOB_STATE_PROVIDER_CLIP_READY,
            JOB_STATE_FAILED_RETRYABLE,
            JOB_STATE_CANCELLED,
        }
    ),
    JOB_STATE_PROVIDER_POLLING: frozenset(
        {
            JOB_STATE_PROVIDER_CLIP_READY,
            JOB_STATE_PROVIDER_GENERATING,
            JOB_STATE_FAILED_RETRYABLE,
            JOB_STATE_CANCELLED,
        }
    ),
    JOB_STATE_PROVIDER_CLIP_READY: frozenset(
        {
            JOB_STATE_PROVIDER_GENERATING,
            JOB_STATE_COMPOSING,
            JOB_STATE_FAILED_RETRYABLE,
            JOB_STATE_CANCELLED,
        }
    ),
    JOB_STATE_COMPOSING: frozenset(
        {
            JOB_STATE_UPLOADING,
            JOB_STATE_FAILED_RETRYABLE,
            JOB_STATE_FAILED_TERMINAL,
            JOB_STATE_CANCELLED,
        }
    ),
    JOB_STATE_UPLOADING: frozenset(
        {JOB_STATE_RESULT_READY, JOB_STATE_FAILED_RETRYABLE, JOB_STATE_CANCELLED}
    ),
    JOB_STATE_RESULT_READY: frozenset(),
    JOB_STATE_FAILED_RETRYABLE: frozenset(
        {JOB_STATE_QUEUED, JOB_STATE_FAILED_TERMINAL, JOB_STATE_CANCELLED}
    ),
    JOB_STATE_FAILED_TERMINAL: frozenset(),
    JOB_STATE_CANCELLED: frozenset(),
}

# --- Closed trace vocabulary (Gate Spec §6) --------------------------------
# Persisted ms_phase set (the worker writes one row per phase boundary).
TRACE_PHASES: FrozenSet[str] = frozenset(
    {
        "generation_start",
        "provider_knobs",
        "provider_batch_start",
        "prompt_build",
        "provider_submit",
        "provider_poll",
        "provider_download",
        "provider_normalize",
        "shot_done",
        "provider_trace_presummary",
        "compose_start",
        "compose_done",
        "upload_start",
        "upload_done",
    }
)

TRACE_STATUS_RUNNING = "running"
TRACE_STATUS_SUCCEEDED = "succeeded"
TRACE_STATUS_FALLBACK = "fallback"
TRACE_STATUS_FAILED = "failed"
TRACE_STATUS_SKIPPED = "skipped"
TRACE_STATUS_CANCELLED = "cancelled"
TRACE_STATUSES: FrozenSet[str] = frozenset(
    {
        TRACE_STATUS_RUNNING,
        TRACE_STATUS_SUCCEEDED,
        TRACE_STATUS_FALLBACK,
        TRACE_STATUS_FAILED,
        TRACE_STATUS_SKIPPED,
        TRACE_STATUS_CANCELLED,
    }
)

# Aligned to akool_image_to_video_capability `_KIND_TO_STATUS` taxonomy.
PROVIDER_STATUS_CLASSES: FrozenSet[str] = frozenset(
    {
        "ok",
        "quota",
        "rate_limited",
        "timeout",
        "auth",
        "invalid_input",
        "server_error",
        "unknown",
    }
)

FALLBACK_REASON_CODES: FrozenSet[str] = frozenset(
    {
        "provider_quota",
        "provider_rate_limited",
        "provider_timeout",
        "provider_auth",
        "provider_invalid_input",
        "refiner_unavailable",
        "none",
    }
)

# --- Worker-lifecycle trace events (PR-2; additive to the trace vocabulary) --
# A trace row's ``phase`` field carries a trace EVENT: either a generation
# ms_phase (PR-1) or one of these worker-lifecycle events (PR-2).
WORKER_EVENT_WORKER_STARTED = "worker_started"
WORKER_EVENT_JOB_CLAIMED = "job_claimed"
WORKER_EVENT_HEARTBEAT = "heartbeat"
WORKER_EVENT_DRY_RUN_STARTED = "dry_run_started"
WORKER_EVENT_DRY_RUN_COMPLETED = "dry_run_completed"
WORKER_EVENT_JOB_COMPLETED = "job_completed"
WORKER_EVENT_JOB_FAILED_RETRYABLE = "job_failed_retryable"
WORKER_EVENT_JOB_FAILED_TERMINAL = "job_failed_terminal"

WORKER_EVENTS: FrozenSet[str] = frozenset(
    {
        WORKER_EVENT_WORKER_STARTED,
        WORKER_EVENT_JOB_CLAIMED,
        WORKER_EVENT_HEARTBEAT,
        WORKER_EVENT_DRY_RUN_STARTED,
        WORKER_EVENT_DRY_RUN_COMPLETED,
        WORKER_EVENT_JOB_COMPLETED,
        WORKER_EVENT_JOB_FAILED_RETRYABLE,
        WORKER_EVENT_JOB_FAILED_TERMINAL,
    }
)

# A trace row's ``phase`` may also be a JOB STATE name (PR-3): the worker writes
# a durable per-state row as it enters each state, before that phase's heavy work.
TRACE_EVENTS: FrozenSet[str] = TRACE_PHASES | WORKER_EVENTS | JOB_STATES


class InvalidJobStateError(ValueError):
    """Raised when a state value is outside the closed set."""


class InvalidJobStateTransitionError(ValueError):
    """Raised when a (current -> target) transition is not in the closed graph."""


def is_terminal(state: str) -> bool:
    """True when ``state`` is a terminal job state (no outgoing transitions)."""
    return state in TERMINAL_STATES


def assert_valid_state(state: str) -> str:
    if state not in JOB_STATES:
        raise InvalidJobStateError(f"unknown job state: {state!r}")
    return state


def assert_transition(current: str, target: str) -> str:
    """Validate a state transition against the closed graph; return ``target``."""
    assert_valid_state(current)
    assert_valid_state(target)
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidJobStateTransitionError(
            f"illegal job-state transition: {current!r} -> {target!r}"
        )
    return target


def assert_valid_phase(phase: str) -> str:
    if phase not in TRACE_PHASES:
        raise InvalidJobStateError(f"unknown trace phase: {phase!r}")
    return phase


def assert_valid_trace_event(event: str) -> str:
    """Validate a trace event: a generation ms_phase OR a worker-lifecycle event."""
    if event not in TRACE_EVENTS:
        raise InvalidJobStateError(f"unknown trace event: {event!r}")
    return event


def assert_valid_trace_status(status: str) -> str:
    if status not in TRACE_STATUSES:
        raise InvalidJobStateError(f"unknown trace status: {status!r}")
    return status
