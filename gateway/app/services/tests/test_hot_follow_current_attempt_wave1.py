from __future__ import annotations

from gateway.app.services.contract_runtime.current_attempt_runtime import (
    HotFollowRouteTruth,
    build_hot_follow_current_attempt,
    build_hot_follow_current_attempt_summary,
    selected_route_from_state,
)


def _compose_ready_artifacts(**extra):
    artifacts = {
        "compose_input": {"mode": "direct", "ready": True},
        "compose_input_ready": True,
        "audio_lane": {
            "source_audio_preserved": False,
            "tts_voiceover_exists": True,
        },
    }
    artifacts.update(extra)
    return artifacts


def test_wave1_url_main_uses_persisted_tts_route_for_current_attempt():
    attempt = build_hot_follow_current_attempt(
        route_truth=HotFollowRouteTruth(
            route="tts_replace_route",
            source="route_event",
            event_id="evt-url",
        ),
        artifact_facts=_compose_ready_artifacts(),
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "actual_burn_subtitle_source": "vi.srt",
        },
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
        },
        dub_status="done",
        compose_status="pending",
        composed_reason="not_done",
    ).to_dict()

    assert attempt["selected_compose_route"] == "tts_replace_route"
    assert attempt["subtitle_required"] is True
    assert attempt["subtitle_process_state"] == "target_subtitle_authoritative_current"
    assert attempt["dub_process_state"] == "dub_ready_current"
    assert attempt["audio_ready"] is True
    assert attempt["dub_current"] is True
    assert attempt["compose_allowed"] is True
    assert attempt["compose_execute_allowed"] is True


def test_wave1_local_preserve_uses_same_l3_contract_and_helper_is_advisory():
    attempt = build_hot_follow_current_attempt(
        route_truth=HotFollowRouteTruth(
            route="preserve_source_route",
            source="route_event",
            event_id="evt-preserve",
        ),
        artifact_facts=_compose_ready_artifacts(
            audio_lane={
                "source_audio_preserved": True,
                "tts_voiceover_exists": False,
            },
            helper_translate_status="failed",
            helper_translate_output_state="helper_output_unavailable",
            helper_translate_provider_health="provider_retryable_failure",
        ),
        subtitle_lane={
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
        },
        voice_state={"audio_ready": False, "audio_ready_reason": "audio_not_ready"},
        dub_status="failed",
        compose_status="pending",
        composed_reason="not_done",
    ).to_dict()

    assert attempt["selected_compose_route"] == "preserve_source_route"
    assert attempt["subtitle_required"] is False
    assert attempt["subtitle_process_state"] == "subtitle_not_required_for_route"
    assert attempt["dub_process_state"] == "dub_not_required_for_route"
    assert attempt["audio_ready"] is True
    assert attempt["dub_current"] is False
    assert attempt["compose_allowed"] is True
    assert attempt["compose_execute_allowed"] is True
    assert attempt["helper_translate_status"] == "failed"


def test_wave1_persisted_preserve_route_is_not_migrated_by_tts_artifacts():
    current_attempt = build_hot_follow_current_attempt_summary(
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
        artifact_facts=_compose_ready_artifacts(
            route_event={
                "event_id": "evt-preserve",
                "command": "enter_preserve_source_route",
                "route": "preserve_source_route",
                "reason": "local_preserve_source_audio",
            },
            audio_lane={
                "source_audio_preserved": True,
                "tts_voiceover_exists": True,
            },
        ),
    )

    assert current_attempt["selected_compose_route"] == "preserve_source_route"
    assert current_attempt["subtitle_required"] is False
    assert current_attempt["no_dub_route_terminal"] is True


def test_wave1_persisted_tts_route_is_not_overridden_by_preserve_artifacts():
    state = {
        "route_event": {
            "event_id": "evt-tts",
            "command": "enter_tts_replace_route",
            "route": "tts_replace_route",
        },
        "artifact_facts": _compose_ready_artifacts(
            audio_lane={
                "source_audio_preserved": True,
                "tts_voiceover_exists": False,
            },
        ),
        "subtitles": {
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
        },
        "audio": {"audio_ready": False, "audio_ready_reason": "audio_not_ready"},
    }

    route = selected_route_from_state({}, state)

    assert route["name"] == "tts_replace_route"
    assert route["compose_allowed"] is False
    assert route["blocked_reason"] in {"preserve_source_route_no_target_subtitle_required", "subtitle_not_ready"}
