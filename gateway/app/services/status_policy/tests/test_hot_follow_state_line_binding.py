from gateway.app.services.status_policy import hot_follow_state


def test_compute_hot_follow_state_consumes_runtime_bound_gate_spec(monkeypatch):
    seen = {}

    def _fake_evaluate_contract_ready_gate(task, state):
        seen["task"] = dict(task)
        seen["state"] = dict(state)
        return {
            "final_exists": False,
            "subtitle_ready": True,
            "subtitle_ready_reason": "ready",
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "compose_ready": False,
            "publish_ready": False,
            "compose_reason": "compose_not_done",
            "blocking": ["compose_not_done"],
        }

    monkeypatch.setattr(
        hot_follow_state,
        "evaluate_contract_ready_gate",
        _fake_evaluate_contract_ready_gate,
    )

    state = hot_follow_state.compute_hot_follow_state({"task_id": "t1", "kind": "hot_follow"}, {"task_id": "t1"})

    assert seen["task"]["kind"] == "hot_follow"
    assert seen["state"]["task_id"] == "t1"
    assert state["ready_gate"]["blocking"] == ["compose_not_done"]
