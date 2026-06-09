"""Matrix Script — Production Job Runtime (PR-1: Durable Job State + Trace Writer).

Signed Gate Spec: ``docs/design/MATRIX_SCRIPT_PRODUCTION_JOB_RUNTIME_GATE_SPEC_20260609.md``.
Contract: ``docs/contracts/matrix_script/generation_job_runtime_contract_v1.md``.

PR-1 scope ONLY: closed job-state model, durable trace truth source behind a
swappable store interface, and a thin enqueue seam. NO worker execution, NO
provider call, NO ffmpeg, NO UI, NO auth change. ``official_publish_ready``
unaffected (remains False).
"""
from __future__ import annotations

from .enqueue import enqueue_generation_job
from .job_state import (
    ALLOWED_TRANSITIONS,
    FALLBACK_REASON_CODES,
    JOB_STATES,
    PROVIDER_STATUS_CLASSES,
    TERMINAL_STATES,
    TRACE_PHASES,
    TRACE_STATUSES,
    InvalidJobStateError,
    InvalidJobStateTransitionError,
    assert_transition,
    assert_valid_phase,
    assert_valid_state,
    assert_valid_trace_status,
    is_terminal,
)
from .job_state_store import (
    IJobStateStore,
    InMemoryJobStateStore,
    JobNotFoundError,
    SqlAlchemyJobStateStore,
    get_job_state_store,
)
from .models import (
    GenerationJob,
    GenerationJobTrace,
    ensure_generation_job_tables,
)
from .trace_writer import (
    JobTraceWriter,
    assert_no_job_trace_leak,
    run_local_trace_harness,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "FALLBACK_REASON_CODES",
    "JOB_STATES",
    "PROVIDER_STATUS_CLASSES",
    "TERMINAL_STATES",
    "TRACE_PHASES",
    "TRACE_STATUSES",
    "InvalidJobStateError",
    "InvalidJobStateTransitionError",
    "assert_transition",
    "assert_valid_phase",
    "assert_valid_state",
    "assert_valid_trace_status",
    "is_terminal",
    "IJobStateStore",
    "InMemoryJobStateStore",
    "JobNotFoundError",
    "SqlAlchemyJobStateStore",
    "get_job_state_store",
    "GenerationJob",
    "GenerationJobTrace",
    "ensure_generation_job_tables",
    "JobTraceWriter",
    "assert_no_job_trace_leak",
    "run_local_trace_harness",
    "enqueue_generation_job",
]
