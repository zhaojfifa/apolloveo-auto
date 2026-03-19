"""Declarative Ready Gate Engine — public API.

Usage::

    from gateway.app.services.ready_gate import evaluate_ready_gate
    from gateway.app.services.ready_gate.hot_follow_rules import HOT_FOLLOW_GATE_SPEC

    result = evaluate_ready_gate(HOT_FOLLOW_GATE_SPEC, task, state)
"""

from .engine import (
    BlockingRule,
    GateRule,
    OverrideRule,
    ReadyGateSpec,
    Signal,
    evaluate_ready_gate,
)
from .registry import (
    get_ready_gate_spec,
    get_ready_gate_spec_for_line,
    get_ready_gate_spec_for_task,
)

__all__ = [
    "BlockingRule",
    "GateRule",
    "OverrideRule",
    "ReadyGateSpec",
    "Signal",
    "evaluate_ready_gate",
    "get_ready_gate_spec",
    "get_ready_gate_spec_for_line",
    "get_ready_gate_spec_for_task",
]
