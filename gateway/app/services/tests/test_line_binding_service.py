from gateway.app.services.line_binding_service import get_line_runtime_binding


def test_hot_follow_line_binding_exposes_runtime_contract_metadata():
    binding = get_line_runtime_binding({"kind": "hot_follow"})
    payload = binding.to_payload()

    assert binding.kind == "hot_follow"
    assert binding.line is not None
    assert payload["bound"] is True
    assert payload["line_id"] == "hot_follow_line"
    assert payload["skills_bundle_ref"] == "skills/hot_follow"
    assert payload["sop_profile_ref"] == "docs/runbooks/hot_follow_sop.md"
    assert payload["input_contract_ref"] == "docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md"
    assert payload["worker_profile_ref"] == "docs/contracts/worker_gateway_contract.md"
    assert payload["ready_gate_ref"] == "docs/contracts/hot_follow_ready_gate.yaml"
    assert payload["status_policy_ref"] == "gateway/app/services/status_policy/hot_follow_state.py"
    assert payload["confirmation_policy"] == {
        "before_execute": False,
        "before_result_accept": False,
        "before_publish": True,
        "before_retry": False,
    }
