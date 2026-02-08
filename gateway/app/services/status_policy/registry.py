from __future__ import annotations

from typing import Any, Dict

from .base import StatusPolicy
from .apollo_avatar import ApolloAvatarStatusPolicy
from .utils import coerce_final_status


_DEFAULT = StatusPolicy()


_POLICIES: Dict[str, StatusPolicy] = {
    "apollo_avatar": ApolloAvatarStatusPolicy(),
}


def get_policy(kind: str | None) -> StatusPolicy:
    k = (kind or "").strip().lower()
    if k == "apollo-avatar":
        k = "apollo_avatar"
    policy = _POLICIES.get(k, _DEFAULT)
    setattr(policy, "kind", k)
    return policy


def get_status_policy(task: dict | None) -> StatusPolicy:
    if not task:
        return _DEFAULT
    kind = (
        (task.get("kind") if isinstance(task, dict) else None)
        or (task.get("task_kind") if isinstance(task, dict) else None)
        or (task.get("category") if isinstance(task, dict) else None)
        or (task.get("category_key") if isinstance(task, dict) else None)
        or (task.get("platform") if isinstance(task, dict) else None)
    )
    return get_policy(kind)


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
        kind=(cur.get("kind") or cur.get("category_key") or cur.get("platform")),
        task=cur,
        updates=filtered,
    )

    if filtered:
        repo.upsert(task_id, filtered)
        return repo.get(task_id) or cur

    return cur
