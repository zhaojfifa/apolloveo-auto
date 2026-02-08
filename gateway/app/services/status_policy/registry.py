from __future__ import annotations

from typing import Dict

from .base import StatusPolicy
from .apollo_avatar import ApolloAvatarStatusPolicy


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

