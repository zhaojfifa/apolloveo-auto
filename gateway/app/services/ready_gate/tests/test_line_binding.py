from gateway.app.lines.base import LineRegistry
from gateway.app.services.ready_gate.hot_follow_rules import HOT_FOLLOW_GATE_SPEC
from gateway.app.services.ready_gate.registry import (
    get_ready_gate_spec_for_line,
    get_ready_gate_spec_for_task,
)


def test_ready_gate_spec_resolves_from_hot_follow_line_contract():
    line = LineRegistry.for_kind("hot_follow")

    assert line is not None
    assert line.line_id == "hot_follow_line"
    assert line.ready_gate_ref == "gateway/app/services/ready_gate/hot_follow_rules.py"
    assert get_ready_gate_spec_for_line(line) is HOT_FOLLOW_GATE_SPEC


def test_ready_gate_spec_resolves_from_task_kind():
    spec = get_ready_gate_spec_for_task({"kind": "hot_follow"})

    assert spec is HOT_FOLLOW_GATE_SPEC
    assert spec.line_id == "hot_follow_line"
