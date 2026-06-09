"""Matrix Script — Production Job Runtime — worker 1-shot generation (PR-3).

Executes EXACTLY ONE script-directed shot by REUSING the existing PR-254 stack
(`run_tomato_real_result`) — no rewrite of Akool / Gemini / Azure / ffmpeg. Runs
off the FastAPI request lifecycle (driven by ``WorkerRuntime``).

Durability: ``StateWalker`` opens a per-state ``running`` trace row BEFORE each
phase's heavy work (driven by the orchestrator's additive ``on_phase`` hook) and
closes it on advance — so a crash/exception leaves the in-flight state's OPEN row
as durable evidence. One of three outcomes:
  1) ``result_ready`` + final.mp4 (provider clip consumed), or
  2) ``result_ready`` + fallback final.mp4 (provider failed, ffmpeg fallback), or
  3) ``failed_retryable`` / ``failed_terminal`` + durable trace (hard failure / crash).
``official_publish_ready`` stays ``false`` throughout.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from . import job_state as st
from .trace_writer import JobTraceWriter

logger = logging.getLogger(__name__)

# Orchestrator ms_phase boundary -> worker job state (the durable state walk).
_PHASE_TO_STATE = {
    "generation_start": st.JOB_STATE_PLANNING,
    "provider_batch_start": st.JOB_STATE_PROVIDER_GENERATING,
    "compose_start": st.JOB_STATE_COMPOSING,
    "upload_start": st.JOB_STATE_UPLOADING,
}

# Closed happy-path order for monotonic advance (intermediate states traced en route).
_HAPPY_ORDER = (
    st.JOB_STATE_QUEUED,
    st.JOB_STATE_PLANNING,
    st.JOB_STATE_PROVIDER_GENERATING,
    st.JOB_STATE_PROVIDER_POLLING,
    st.JOB_STATE_PROVIDER_CLIP_READY,
    st.JOB_STATE_COMPOSING,
    st.JOB_STATE_UPLOADING,
    st.JOB_STATE_RESULT_READY,
)

# Bound provider load to exactly one shot, one attempt (PR-3 scope).
_ONE_SHOT_OVERRIDES = {
    "MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS": "1",
    "MATRIX_SCRIPT_PROVIDER_ATTEMPT_CAP": "1",
}


class WorkerGenerationError(RuntimeError):
    """Raised when the worker cannot run the generation (e.g. task not found)."""


class StateWalker:
    """Monotonic durable state walk with an OPEN per-state trace row.

    Each entered state opens a ``running`` row (write-before-heavy-work); the row
    closes (``succeeded``) when the next state is entered. The CURRENT state's row
    stays OPEN until ``finalize`` — so a crash leaves it open as in-flight evidence.
    """

    def __init__(self, store: Any, writer: JobTraceWriter, job_id: str) -> None:
        self._store = store
        self._writer = writer
        self._job_id = job_id
        self._open_tid: Optional[str] = None

    def _current(self) -> Optional[str]:
        job = self._store.get_job(self._job_id) or {}
        return job.get("state")

    def _close(self, status: str = st.TRACE_STATUS_SUCCEEDED) -> None:
        if self._open_tid is not None:
            self._writer.end_phase(self._open_tid, status=status)
            self._open_tid = None

    def open_current(self) -> None:
        cur = self._current()
        if cur in _HAPPY_ORDER:
            self._open_tid = self._writer.begin_phase(cur)  # OPEN row for the current state

    def advance_to(self, target: str) -> None:
        if target not in _HAPPY_ORDER:
            return
        cur = self._current()
        if cur not in _HAPPY_ORDER:
            return
        ci, ti = _HAPPY_ORDER.index(cur), _HAPPY_ORDER.index(target)
        for i in range(ci + 1, ti + 1):
            nxt = _HAPPY_ORDER[i]
            self._close(st.TRACE_STATUS_SUCCEEDED)  # close the prior state's row
            self._store.transition_state(self._job_id, nxt)
            self._open_tid = self._writer.begin_phase(nxt)  # OPEN row before this phase's heavy work

    def on_phase(self, name: str) -> None:
        """Subscribe to the orchestrator's ms_phase boundaries (fires before heavy work)."""
        target = _PHASE_TO_STATE.get(name)
        if target:
            self.advance_to(target)

    def finalize(self) -> None:
        self._close(st.TRACE_STATUS_SUCCEEDED)


def one_shot_env(base: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Full env (gate + creds + knobs resolve together) with the 1-shot overrides."""
    env = dict(base if base is not None else os.environ)
    env.update(_ONE_SHOT_OVERRIDES)
    return env


def execute_one_shot_generation(
    job: Dict[str, Any],
    store: Any,
    writer: JobTraceWriter,
    walker: StateWalker,
    *,
    task: Optional[Any] = None,
    task_repo: Optional[Any] = None,
    use_gemini: bool = False,
    sink: Optional[Any] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Real off-dyno 1-shot generation via the reused tomato stack.

    Loads the task (File/S3 task repo), runs ``run_tomato_real_result`` bounded to
    one shot with the durable ``on_phase`` walk, persists the staged result into
    ``task.config`` (best-effort, so the existing Workbench poller lights up), and
    returns a summary. State advances to UPLOADING via the walker; the caller
    (``WorkerRuntime``) finalizes UPLOADING -> RESULT_READY.
    """
    # Lazy import: keep this package importable without the heavy generation stack.
    from gateway.app.services.matrix_script import auto_preview_generation as ap

    task_id = str(job["task_id"])
    if task is None:
        if task_repo is None:
            from gateway.app.deps import get_task_repository

            task_repo = get_task_repository()
        task = task_repo.get(task_id)
    if task is None:
        raise WorkerGenerationError(f"task_not_found:{task_id}")

    env = one_shot_env()
    out_dir = output_dir or ap._resolve_tomato_output_dir(task_id)
    the_sink = sink if sink is not None else ap._build_tomato_sink(task_id)

    result = ap.run_tomato_real_result(
        ap._task_mapping(task),
        out_dir,
        sink=the_sink,
        env=env,
        use_gemini=use_gemini,
        on_phase=walker.on_phase,
    )
    ap.validate_tomato_result_artifacts(result)
    payload = ap.tomato_result_to_payload(result)
    payload["preview_url"] = f"/api/matrix-script/{task_id}/tomato-real-result/preview/final.mp4"
    ap.assert_no_delivery_view_forbidden_tokens(payload)

    # Best-effort: mirror the staged result into task.config so the existing
    # Workbench poller observes success unchanged. The durable job state + trace
    # is the source of truth; this sync never blocks the job's terminal state.
    if task_repo is not None:
        try:
            success = ap._status_payload(
                ap.STATUS_SUCCEEDED,
                completed_at=ap._utc_now(),
                preview_url=payload.get("preview_url"),
                delivery_candidate=payload.get("delivery_candidate"),
            )
            ap._update_config(
                task_repo,
                task_id,
                task_repo.get(task_id) or task,
                {ap.STAGED_CANDIDATE_KEY: payload, ap.AUTO_PREVIEW_STATUS_KEY: success},
            )
        except Exception:  # noqa: BLE001 — poller sync is best-effort, not the truth source
            logger.warning("worker task.config persist failed task=%s", task_id, exc_info=True)

    return {
        "final_video": True,
        "generation_provider": payload.get("generation_provider"),
        "official_publish_ready": bool(payload.get("official_publish_ready", False)),
    }


def make_one_shot_generation_fn(
    *, task_repo: Optional[Any] = None, use_gemini: bool = False,
    sink: Optional[Any] = None, output_dir: Optional[str] = None,
):
    """Build a ``WorkerRuntime`` generation_fn that runs the real 1-shot generation."""

    def _fn(job, store, writer, walker):
        return execute_one_shot_generation(
            job, store, writer, walker,
            task_repo=task_repo, use_gemini=use_gemini, sink=sink, output_dir=output_dir,
        )

    return _fn
