from gateway.app.services.contract_runtime import (
    apply_projection_runtime,
    get_blocking_reason_runtime,
    get_contract_runtime_refs,
    get_projection_rules_runtime,
)


def test_contract_runtime_refs_follow_hot_follow_line_binding():
    refs = get_contract_runtime_refs({"kind": "hot_follow"})

    assert refs.line_id == "hot_follow_line"
    assert refs.ready_gate_ref == "docs/contracts/hot_follow_ready_gate.yaml"
    assert refs.projection_rules_ref == "docs/contracts/hot_follow_projection_rules_v1.md"
    assert refs.status_policy_ref == "gateway/app/services/status_policy/hot_follow_state.py"


def test_projection_runtime_final_ready_dominates_publish_truth():
    runtime = get_projection_rules_runtime("docs/contracts/hot_follow_projection_rules_v1.md")
    payload = {
        "final": {"exists": True, "fresh": True, "url": "/v1/tasks/hf/final"},
        "final_fresh": True,
        "current_attempt": {"audio_ready": True},
        "ready_gate": {
            "compose_ready": False,
            "publish_ready": False,
            "blocking": ["compose_not_done", "scenes.running", "audio_not_ready"],
        },
        "compose_status": "pending",
        "composed_ready": False,
        "composed_reason": "compose_not_done",
        "scene_pack": {"exists": False, "status": "running"},
    }

    projected = apply_projection_runtime(
        payload,
        surface="publish",
        projection_runtime=runtime,
    )

    assert projected["composed_ready"] is True
    assert projected["composed_reason"] == "ready"
    assert projected["compose_status"] == "done"
    assert projected["ready_gate"]["compose_ready"] is True
    assert projected["ready_gate"]["publish_ready"] is True
    assert projected["ready_gate"]["blocking"] == []
    assert projected["scene_pack_pending_reason"] == "scenes.running"


def test_projection_runtime_preserves_in_progress_truth_without_final_dominance():
    runtime = get_projection_rules_runtime("docs/contracts/hot_follow_projection_rules_v1.md")
    payload = {
        "final": {"exists": False, "fresh": False, "url": None},
        "final_fresh": False,
        "current_attempt": {"audio_ready": True},
        "ready_gate": {
            "compose_ready": False,
            "publish_ready": False,
            "blocking": ["compose_not_done", "scenes.not_ready"],
        },
        "compose_status": "running",
        "composed_ready": False,
        "composed_reason": "compose_not_done",
        "scene_pack": {"exists": False, "status": "pending"},
    }

    projected = apply_projection_runtime(
        payload,
        surface="publish",
        projection_runtime=runtime,
    )

    assert projected["composed_ready"] is False
    assert projected["compose_status"] == "running"
    assert projected["ready_gate"]["publish_ready"] is False
    assert projected["ready_gate"]["blocking"] == ["compose_not_done", "scenes.not_ready"]
    assert projected["scene_pack_pending_reason"] == "scenes.not_ready"


def test_blocking_reason_runtime_canonicalizes_aliases_and_scene_pack_reason():
    runtime = get_blocking_reason_runtime("docs/contracts/hot_follow_projection_rules_v1.md")

    assert runtime.canonicalize("missing_voiceover") == "voiceover_missing"
    assert runtime.normalize_list(["missing_voiceover", "voiceover_missing"]) == ["voiceover_missing"]
    assert runtime.scene_pack_pending_reason("failed") == "scenes.failed"
