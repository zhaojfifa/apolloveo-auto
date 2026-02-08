from __future__ import annotations

from typing import Any

from .registry import get_status_policy
from .utils import coerce_final_status


def policy_upsert(
    repo: Any,
    task_id: str,
    task: dict | None,
    updates: dict,
    *,
    step: str,
    force: bool = False,
) -> dict:
    cur = (repo.get(task_id) or task or {})
    policy = get_status_policy(cur)

    filtered = policy.reconcile_after_step(
        cur,
        step=step,
        updates=dict(updates or {}),
        force=force,
    ) or {}

    filtered = coerce_final_status(
        kind=(cur.get("category_key") or cur.get("platform") or cur.get("kind")),
        task=cur,
        updates=filtered,
    )

    if filtered:
        repo.upsert(task_id, filtered)
        return repo.get(task_id) or cur

    return cur
