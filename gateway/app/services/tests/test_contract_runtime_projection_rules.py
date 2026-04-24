from gateway.app.services.contract_runtime import (
    apply_projection_runtime,
    get_blocking_reason_runtime,
    get_contract_runtime_refs,
    get_projection_rules_runtime,
    scene_pack_pending_reason_for_task,
    select_presentation_final,
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


def test_projection_runtime_derives_no_tts_compose_allowed_reason_from_contract():
    runtime = get_projection_rules_runtime("docs/contracts/hot_follow_projection_rules_v1.md")
    payload = {
        "final": {"exists": False},
        "final_fresh": False,
        "current_attempt": {"audio_ready": False},
        "ready_gate": {
            "compose_allowed": True,
            "no_dub_compose_allowed": True,
            "compose_ready": False,
            "publish_ready": False,
            "blocking": ["compose_not_done"],
        },
        "compose_status": "pending",
        "composed_ready": False,
        "scene_pack": {"exists": True, "status": "done"},
    }

    projected = apply_projection_runtime(
        payload,
        surface="workbench",
        projection_runtime=runtime,
    )

    assert projected["compose_allowed"] is True
    assert projected["compose_allowed_reason"] == "no_dub_inputs_ready"
    assert projected["ready_gate"]["compose_allowed_reason"] == "no_dub_inputs_ready"


def test_projection_runtime_selects_current_before_historical_final():
    runtime = get_projection_rules_runtime("docs/contracts/hot_follow_projection_rules_v1.md")

    selected = select_presentation_final(
        {"exists": True, "url": "/current"},
        {"exists": True, "url": "/historical"},
        projection_runtime=runtime,
    )
    fallback = select_presentation_final(
        {"exists": False, "url": None},
        {"exists": True, "url": "/historical"},
        projection_runtime=runtime,
    )

    assert selected["url"] == "/current"
    assert fallback["url"] == "/historical"


def test_blocking_reason_runtime_canonicalizes_aliases_and_scene_pack_reason():
    runtime = get_blocking_reason_runtime("docs/contracts/hot_follow_projection_rules_v1.md")

    assert runtime.canonicalize("missing_voiceover") == "voiceover_missing"
    assert runtime.normalize_list(["missing_voiceover", "voiceover_missing"]) == ["voiceover_missing"]
    assert runtime.sort_by_priority(["subtitle_not_ready", "compose_input_blocked"]) == [
        "compose_input_blocked",
        "subtitle_not_ready",
    ]
    assert runtime.scene_pack_pending_reason("failed") == "scenes.failed"


def test_scene_pack_pending_reason_for_task_uses_bound_projection_contract():
    assert (
        scene_pack_pending_reason_for_task(
            {"kind": "hot_follow"},
            {"exists": False, "status": "running"},
        )
        == "scenes.running"
    )


def test_projection_runtime_loads_boundary_rule_freeze_contract():
    runtime = get_projection_rules_runtime("docs/contracts/hot_follow_projection_rules_v1.md")

    assert "url_voice_led_standard_dubbing" in runtime.runtime_boundary_rule_freeze_rules
    assert "preserve_source_route_resolution" in runtime.runtime_boundary_rule_freeze_rules
    assert "helper_side_channel_coexistence" in runtime.runtime_boundary_rule_freeze_rules
    assert "historical_event_isolation" in runtime.runtime_boundary_rule_freeze_rules
