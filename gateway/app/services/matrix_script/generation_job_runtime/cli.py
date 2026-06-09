"""Matrix Script — Production Job Runtime — local worker CLI (PR-2).

Run a dry-run generation worker locally, off the FastAPI request lifecycle:

    python -m gateway.app.services.matrix_script.generation_job_runtime.cli \
        --worker-id local-1 --once

    python -m gateway.app.services.matrix_script.generation_job_runtime.cli \
        --worker-id local-1 --max-iterations 5

Uses the configured ``DATABASE_URL`` (default local SQLite); ensures the job
tables exist first. Dry-run only — NO provider/ffmpeg/upload (PR-2 boundary).
"""
from __future__ import annotations

import argparse
import logging
from typing import List, Optional

from .generation import make_one_shot_generation_fn
from .job_state_store import IJobStateStore, get_job_state_store
from .worker import WORKER_DEFAULT_LEASE_SECONDS, WORKER_DEFAULT_MAX_RETRIES, WorkerRuntime

logger = logging.getLogger("ms_job_worker")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ms-job-worker",
        description="Matrix Script generation job worker — dry-run skeleton (PR-2). "
        "No Akool/Gemini/Azure/ffmpeg/R2.",
    )
    p.add_argument("--worker-id", required=True, help="identifier for this worker run")
    p.add_argument("--lease-seconds", type=int, default=WORKER_DEFAULT_LEASE_SECONDS)
    p.add_argument("--max-retries", type=int, default=WORKER_DEFAULT_MAX_RETRIES)
    p.add_argument("--once", action="store_true", help="claim + dry-run one job, then exit")
    p.add_argument(
        "--max-iterations", type=int, default=None,
        help="loop mode: stop after N claimed jobs (default: until none queued)",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="skeleton dry-run (no provider/ffmpeg); default runs the real 1-shot generation",
    )
    return p


def main(argv: Optional[List[str]] = None, *, store: Optional[IJobStateStore] = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    if store is None:
        # local-first: ensure the durable tables exist on the configured DB.
        from gateway.app.db import engine
        from .models import ensure_generation_job_tables

        ensure_generation_job_tables(engine)
        store = get_job_state_store()

    # default: real off-dyno 1-shot generation; --dry-run uses the PR-2 skeleton.
    generation_fn = None if args.dry_run else make_one_shot_generation_fn()
    worker = WorkerRuntime(
        store, worker_id=args.worker_id,
        lease_seconds=args.lease_seconds, max_retries=args.max_retries,
        generation_fn=generation_fn,
    )
    if args.once:
        logger.info("worker=%s once result=%s", args.worker_id, worker.run_once())
    else:
        results = worker.run_loop(max_iterations=args.max_iterations)
        logger.info("worker=%s loop processed=%d", args.worker_id, len(results))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
