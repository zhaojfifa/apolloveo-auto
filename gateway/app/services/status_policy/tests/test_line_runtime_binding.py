from gateway.app.services.ready_gate.hot_follow_rules import HOT_FOLLOW_GATE_SPEC
from gateway.app.services.status_policy.registry import get_status_runtime_binding


def test_status_runtime_binding_exposes_line_and_gate_spec_for_hot_follow():
    binding = get_status_runtime_binding({"kind": "hot_follow"})

    assert binding.kind == "hot_follow"
    assert binding.line is not None
    assert binding.line.line_id == "hot_follow_line"
    assert binding.line.status_policy_ref == "gateway/app/services/status_policy/hot_follow_state.py"
    assert binding.ready_gate_spec is HOT_FOLLOW_GATE_SPEC
