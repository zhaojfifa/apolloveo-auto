from __future__ import annotations

from typing import Any

import gateway.app.lines.hot_follow as _line_reg_hot_follow  # noqa: F401
from gateway.app.lines.base import LineRegistry, ProductionLine

from .engine import ReadyGateSpec
from .hot_follow_rules import (
    HOT_FOLLOW_GATE_SPEC,
    HOT_FOLLOW_READY_GATE_CONTRACT_REF,
    HOT_FOLLOW_READY_GATE_RUNTIME_REF,
)


_READY_GATE_SPECS_BY_REF: dict[str, ReadyGateSpec] = {
    HOT_FOLLOW_READY_GATE_CONTRACT_REF: HOT_FOLLOW_GATE_SPEC,
    HOT_FOLLOW_READY_GATE_RUNTIME_REF: HOT_FOLLOW_GATE_SPEC,
}

_READY_GATE_SPECS_BY_LINE_ID: dict[str, ReadyGateSpec] = {
    HOT_FOLLOW_GATE_SPEC.line_id: HOT_FOLLOW_GATE_SPEC,
}


def _resolve_task_kind(task: dict[str, Any] | None) -> str:
    if not isinstance(task, dict):
        return ""
    kind = (
        task.get("kind")
        or task.get("task_kind")
        or task.get("category")
        or task.get("category_key")
        or task.get("platform")
    )
    return str(kind or "").strip().lower()


def get_ready_gate_spec(ref: str | None) -> ReadyGateSpec | None:
    key = str(ref or "").strip()
    if not key:
        return None
    return _READY_GATE_SPECS_BY_REF.get(key)


def get_ready_gate_spec_for_line(line: ProductionLine | None) -> ReadyGateSpec | None:
    if line is None:
        return None
    spec = get_ready_gate_spec(line.ready_gate_ref)
    if spec is not None:
        return spec
    return _READY_GATE_SPECS_BY_LINE_ID.get(line.line_id)


def get_ready_gate_spec_for_task(task: dict[str, Any] | None) -> ReadyGateSpec | None:
    line = LineRegistry.for_kind(_resolve_task_kind(task))
    return get_ready_gate_spec_for_line(line)
