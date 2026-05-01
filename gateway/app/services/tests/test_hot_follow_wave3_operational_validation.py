from __future__ import annotations

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services.contract_runtime.current_attempt_runtime import (
    build_hot_follow_current_attempt_summary,
)
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_operator_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.voice_service import (
    hf_screen_text_candidate_summary,
    hf_source_audio_lane_summary,
)


def _compose_input():
    return {"mode": "direct", "ready": True, "blocked": False}


def _state_for_attempt(task_id: str, current_attempt: dict, artifact_facts: dict) -> dict:
    state = {
        "task_id": task_id,
        "kind": "hot_follow",
        "current_attempt": current_attempt,
        "artifact_facts": artifact_facts,
        "final": {
            "exists": bool(current_attempt.get("final_fresh")),
            "fresh": bool(current_attempt.get("final_fresh")),
            "url": f"/v1/tasks/{task_id}/final" if current_attempt.get("final_fresh") else None,
        },
        "historical_final": {"exists": False},
        "subtitles": {
            "subtitle_ready": bool(current_attempt.get("subtitle_ready")),
            "target_subtitle_current": bool(current_attempt.get("target_subtitle_authoritative_current")),
            "target_subtitle_authoritative_source": bool(current_attempt.get("target_subtitle_authoritative_current")),
            "subtitle_ready_reason": current_attempt.get("subtitle_ready_reason"),
        },
        "audio": {
            "status": "done" if current_attempt.get("audio_ready") else "pending",
            "audio_ready": bool(current_attempt.get("audio_ready")),
            "audio_ready_reason": current_attempt.get("audio_ready_reason"),
            "dub_current": bool(current_attempt.get("dub_current")),
            "dub_current_reason": current_attempt.get("dub_current_reason"),
        },
        "composed_reason": "ready" if current_attempt.get("final_fresh") else "not_done",
    }
    return compute_hot_follow_state({"task_id": task_id, "kind": "hot_follow"}, state)


def test_wave3_url_main_flow_reaches_subtitle_dub_then_compose_ready():
    artifact_facts = {
        "route_event": {
            "event_id": "evt-url-main",
            "command": "enter_tts_replace_route",
            "route": "tts_replace_route",
        },
        "compose_input": _compose_input(),
        "audio_lane": {
            "source_audio_preserved": False,
            "tts_voiceover_exists": True,
        },
        "final_exists": True,
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "status": "done",
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "actual_burn_subtitle_source": "vi.srt",
            "parse_source_text": "origin text",
        },
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        artifact_facts=artifact_facts,
    )
    state = _state_for_attempt("hf-wave3-url", current_attempt, artifact_facts)
    operator_summary = build_hot_follow_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
        subtitle_ready=True,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["subtitle_process_state"] == "target_subtitle_authoritative_current"
    assert current_attempt["dub_process_state"] == "dub_ready_current"
    assert current_attempt["compose_execute_allowed"] is True
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["compose_ready"] is True
    assert operator_summary["selected_compose_route"] == "tts_replace_route"


def test_wave3_running_and_stale_pending_are_operator_visible():
    running = build_hot_follow_current_attempt_summary(
        voice_state={"audio_ready": False, "audio_ready_reason": "audio_not_ready"},
        subtitle_lane={
            "status": "running",
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "parse_source_text": "origin text",
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="not_done",
        artifact_facts={
            "route_event": {"command": "enter_tts_replace_route", "route": "tts_replace_route"},
            "compose_input": _compose_input(),
            "audio_lane": {"source_audio_preserved": False, "tts_voiceover_exists": False},
        },
    )
    stale = build_hot_follow_current_attempt_summary(
        voice_state={"audio_ready": False, "audio_ready_reason": "waiting_for_target_subtitle_translation"},
        subtitle_lane={
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "parse_source_text": "origin text",
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="not_done",
        artifact_facts={
            "route_event": {"command": "enter_tts_replace_route", "route": "tts_replace_route"},
            "compose_input": _compose_input(),
            "audio_lane": {"source_audio_preserved": False, "tts_voiceover_exists": False},
        },
    )

    assert running["pending_class"] == "running"
    assert stale["pending_class"] == "stale_waiting_without_progress"
    assert build_hot_follow_operator_summary(
        artifact_facts={},
        current_attempt=running,
        no_dub=False,
    )["pending_class"] == "running"
    assert build_hot_follow_operator_summary(
        artifact_facts={},
        current_attempt=stale,
        no_dub=False,
    )["pending_class"] == "stale_waiting_without_progress"


def test_wave3_local_preserve_flow_helper_failure_does_not_block_compose():
    artifact_facts = {
        "route_event": {
            "event_id": "evt-local-preserve",
            "command": "enter_preserve_source_route",
            "route": "preserve_source_route",
        },
        "compose_input": _compose_input(),
        "audio_lane": {
            "source_audio_preserved": True,
            "tts_voiceover_exists": False,
        },
        "helper_translate_status": "failed",
        "helper_translate_provider_health": "provider_retryable_failure",
        "final_exists": True,
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={"audio_ready": False, "audio_ready_reason": "audio_not_ready"},
        subtitle_lane={
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
        },
        dub_status="failed",
        compose_status="done",
        composed_reason="ready",
        artifact_facts=artifact_facts,
    )
    state = _state_for_attempt("hf-wave3-preserve", current_attempt, artifact_facts)

    assert current_attempt["selected_compose_route"] == "preserve_source_route"
    assert current_attempt["subtitle_required"] is False
    assert current_attempt["compose_allowed"] is True
    assert current_attempt["compose_execute_allowed"] is True
    assert current_attempt["helper_translate_status"] == "failed"
    assert state["ready_gate"]["selected_compose_route"] == "preserve_source_route"
    assert state["ready_gate"]["compose_ready"] is True


def test_wave3_local_preserve_reentry_requires_explicit_tts_route_event():
    preserve_artifacts = {
        "route_event": {
            "event_id": "evt-preserve",
            "command": "enter_preserve_source_route",
            "route": "preserve_source_route",
        },
        "compose_input": _compose_input(),
        "audio_lane": {
            "source_audio_preserved": True,
            "tts_voiceover_exists": True,
        },
    }
    preserve_attempt = build_hot_follow_current_attempt_summary(
        voice_state={"audio_ready": True, "audio_ready_reason": "ready", "dub_current": True},
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
        },
        dub_status="done",
        compose_status="pending",
        composed_reason="not_done",
        artifact_facts=preserve_artifacts,
    )
    reentry_artifacts = {
        **preserve_artifacts,
        "route_event": {
            "event_id": "evt-reentry",
            "command": "enter_tts_replace_route",
            "route": "tts_replace_route",
            "previous_route": "preserve_source_route",
            "reason": "operator_reentry",
        },
    }
    reentry_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "actual_burn_subtitle_source": "vi.srt",
        },
        dub_status="done",
        compose_status="pending",
        composed_reason="not_done",
        artifact_facts=reentry_artifacts,
    )

    assert preserve_attempt["selected_compose_route"] == "preserve_source_route"
    assert reentry_attempt["selected_compose_route"] == "tts_replace_route"
    assert reentry_attempt["route_event_id"] == "evt-reentry"
    assert reentry_attempt["compose_execute_allowed"] is True


def test_wave3_router_summary_helpers_delegate_to_service_layer(monkeypatch):
    source_calls = []
    screen_calls = []
    monkeypatch.setattr(
        hf_router,
        "_svc_hf_source_audio_lane_summary",
        lambda task, route_state=None: source_calls.append((task, route_state)) or {"source_audio_lane": "delegated"},
    )
    monkeypatch.setattr(
        hf_router,
        "_svc_hf_screen_text_candidate_summary",
        lambda subtitle_lane=None, route_state=None: screen_calls.append((subtitle_lane, route_state)) or {"screen_text_candidate": "delegated"},
    )

    assert hf_router._hf_source_audio_lane_summary({"task_id": "r"}, {"content_mode": "voice_led"}) == {
        "source_audio_lane": "delegated"
    }
    assert hf_router._hf_screen_text_candidate_summary({"raw_source_text": "x"}, {"content_mode": "subtitle_led"}) == {
        "screen_text_candidate": "delegated"
    }
    assert source_calls
    assert screen_calls
    assert hf_source_audio_lane_summary({"task_id": "svc"}, {})["source_audio_lane"] == "unknown"
    assert hf_screen_text_candidate_summary({}, {})["screen_text_candidate_mode"] == "unavailable"
