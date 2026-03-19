from gateway.app.services.ready_gate.engine import ReadyGateSpec
from gateway.app.services.status_policy import hot_follow_state


def test_compute_hot_follow_state_consumes_runtime_bound_gate_spec(monkeypatch):
    sentinel_spec = ReadyGateSpec(line_id="hot_follow_line", signals=(), gates=(), blocking=())
    seen = {}

    def _fake_get_status_runtime_binding(task):
        seen["task"] = dict(task)
        return type(
            "Binding",
            (),
            {
                "kind": "hot_follow",
                "line": type("Line", (), {"line_id": "hot_follow_line"})(),
                "ready_gate_spec": sentinel_spec,
            },
        )()

    def _fake_evaluate_ready_gate(spec, task, state):
        seen["spec"] = spec
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

    monkeypatch.setattr(hot_follow_state, "get_status_runtime_binding", _fake_get_status_runtime_binding)
    monkeypatch.setattr(hot_follow_state, "evaluate_ready_gate", _fake_evaluate_ready_gate)

    state = hot_follow_state.compute_hot_follow_state({"task_id": "t1", "kind": "hot_follow"}, {"task_id": "t1"})

    assert seen["task"]["kind"] == "hot_follow"
    assert seen["spec"] is sentinel_spec
    assert state["ready_gate"]["blocking"] == ["compose_not_done"]
