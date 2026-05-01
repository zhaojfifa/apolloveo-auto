from __future__ import annotations

from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_operator_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.task_view_workbench_contract import apply_ready_gate_compose_projection


def _current_attempt(**overrides):
    payload = {
        "contract_version": "hot_follow_current_attempt_contract_v1",
        "selected_compose_route": "preserve_source_route",
        "route_allowed": True,
        "route_allowed_reason": "ready",
        "subtitle_required": False,
        "subtitle_process_state": "subtitle_not_required_for_route",
        "subtitle_ready": False,
        "subtitle_ready_reason": "preserve_source_route",
        "target_subtitle_authoritative_current": False,
        "dub_process_state": "dub_not_required_for_route",
        "audio_ready": True,
        "audio_ready_reason": "ready",
        "dub_current": False,
        "dub_current_reason": "dub_not_required_for_route",
        "compose_input_ready": True,
        "compose_allowed": True,
        "compose_route_allowed": True,
        "compose_execute_allowed": True,
        "compose_reason": "ready",
        "compose_allowed_reason": "ready",
        "no_tts_compose_allowed": True,
        "no_dub_compose_allowed": True,
        "requires_redub": False,
        "requires_recompose": True,
        "final_fresh": False,
        "pending_class": "none",
        "blocking": [],
    }
    payload.update(overrides)
    return payload


def test_wave2_ready_gate_consumes_current_attempt_without_route_reinterpretation():
    state = compute_hot_follow_state(
        {"task_id": "hf-wave2-preserve", "kind": "hot_follow"},
        {
            "task_id": "hf-wave2-preserve",
            "current_attempt": _current_attempt(),
            "artifact_facts": {
                "compose_input": {"mode": "direct", "ready": True},
                "audio_lane": {
                    "source_audio_preserved": True,
                    "tts_voiceover_exists": True,
                },
            },
            "subtitles": {
                "subtitle_ready": True,
                "target_subtitle_current": True,
                "target_subtitle_authoritative_source": True,
            },
            "audio": {
                "audio_ready": True,
                "dub_current": True,
                "no_dub": False,
            },
            "compose_status": "running",
            "pipeline": [{"key": "subtitles", "status": "running", "state": "running"}],
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "preserve_source_route"
    assert state["ready_gate"]["compose_allowed"] is True
    assert state["ready_gate"]["no_tts_compose_allowed"] is True
    assert state["current_attempt"]["selected_compose_route"] == "preserve_source_route"
    assert state["compose_status"] == "running"
    assert state["pipeline"][0]["status"] == "running"


def test_wave2_operator_summary_formats_current_attempt_truth_only():
    current_attempt = _current_attempt(
        selected_compose_route="tts_replace_route",
        subtitle_required=True,
        subtitle_process_state="target_subtitle_materialization_running",
        pending_class="running",
        compose_allowed=False,
        compose_allowed_reason="subtitle_not_ready",
        dub_current=False,
    )

    summary = build_hot_follow_operator_summary(
        artifact_facts={"final_exists": False},
        current_attempt=current_attempt,
        no_dub=False,
        subtitle_ready=False,
    )

    assert summary["selected_compose_route"] == "tts_replace_route"
    assert summary["compose_allowed"] is False
    assert summary["subtitle_required"] is True
    assert summary["dub_current"] is False
    assert summary["pending_class"] == "running"


def test_wave2_compose_projection_alias_does_not_rewrite_ready_gate():
    payload = {
        "ready_gate": {
            "compose_allowed": False,
            "compose_allowed_reason": "subtitle_not_ready",
        },
        "current_attempt": _current_attempt(
            compose_allowed=True,
            compose_allowed_reason="ready",
            compose_reason="ready",
        ),
    }

    apply_ready_gate_compose_projection(payload)

    assert payload["compose_allowed"] is True
    assert payload["compose_allowed_reason"] == "ready"
    assert payload["ready_gate"]["compose_allowed"] is False
    assert payload["ready_gate"]["compose_allowed_reason"] == "subtitle_not_ready"
