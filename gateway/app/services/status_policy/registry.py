from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import gateway.app.lines.hot_follow as _line_reg_hot_follow  # noqa: F401
from gateway.app.lines.base import LineRegistry, ProductionLine
from gateway.app.services.ready_gate import ReadyGateSpec, get_ready_gate_spec_for_line
from .base import StatusPolicy
from .apollo_avatar import ApolloAvatarStatusPolicy


_DEFAULT = StatusPolicy()


_POLICIES: Dict[str, StatusPolicy] = {
    "apollo_avatar": ApolloAvatarStatusPolicy(),
}


@dataclass(frozen=True)
class StatusRuntimeBinding:
    line: ProductionLine | None
    policy: StatusPolicy
    kind: str
    ready_gate_spec: ReadyGateSpec | None = None


def get_policy(kind: str | None) -> Tuple[StatusPolicy, str]:
    """Return (policy, normalized_kind) without mutating the singleton."""
    k = (kind or "").strip().lower()
    if k == "apollo-avatar":
        k = "apollo_avatar"
    policy = _POLICIES.get(k, _DEFAULT)
    return policy, k


def _resolve_task_kind(task: dict | None) -> str:
    if not task:
        return ""
    return (
        (task.get("kind") if isinstance(task, dict) else None)
        or (task.get("task_kind") if isinstance(task, dict) else None)
        or (task.get("category") if isinstance(task, dict) else None)
        or (task.get("category_key") if isinstance(task, dict) else None)
        or (task.get("platform") if isinstance(task, dict) else None)
    )


def get_status_runtime_binding(task: dict | None) -> StatusRuntimeBinding:
    kind = _resolve_task_kind(task)
    policy, normalized_kind = get_policy(kind)
    line = LineRegistry.for_kind(normalized_kind)
    return StatusRuntimeBinding(
        line=line,
        policy=policy,
        kind=normalized_kind,
        ready_gate_spec=get_ready_gate_spec_for_line(line),
    )


def get_status_policy(task: dict | None) -> Tuple[StatusPolicy, str]:
    """Return (policy, kind) for a task dict."""
    binding = get_status_runtime_binding(task)
    return binding.policy, binding.kind
