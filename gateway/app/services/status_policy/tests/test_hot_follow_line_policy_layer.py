from __future__ import annotations

from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


def test_ready_gate_compose_blocked_overrides_compose_not_done():
    state = compute_hot_follow_state(
        {"task_id": "ffe9083de6ee", "kind": "hot_follow"},
        {
            "task_id": "ffe9083de6ee",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True},
            "audio": {"audio_ready": True, "dub_current": True, "status": "done"},
            "artifact_facts": {
                "compose_input_mode": "blocked",
                "compose_input_blocked": True,
                "compose_input_reason": "bitrate_too_high",
                "compose_input": {
                    "mode": "blocked",
                    "blocked": True,
                    "reason": "bitrate_too_high",
                },
            },
        },
    )

    gate = state["ready_gate"]
    assert gate["compose_ready"] is False
    assert gate["compose_blocked"] is True
    assert gate["compose_blocked_reason"] == "bitrate_too_high"
    assert gate["compose_reason"] == "bitrate_too_high"
    assert gate["blocking"] == ["bitrate_too_high"]
    assert "compose_not_done" not in gate["blocking"]
    assert gate["compose_allowed"] is False
    assert gate["compose_allowed_reason"] == "bitrate_too_high"


def test_ready_gate_models_bgm_only_no_tts_as_legal_no_dub_line_state():
    state = compute_hot_follow_state(
        {"task_id": "c3a11f7852e2", "kind": "hot_follow"},
        {
            "task_id": "c3a11f7852e2",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
            },
            "audio": {
                "status": "pending",
                "audio_ready": False,
                "audio_ready_reason": "dub_not_done",
                "dub_current": False,
                "no_dub": False,
                "no_dub_reason": None,
            },
            "artifact_facts": {
                "audio_lane_mode": "muted_no_tts",
                "tts_voiceover_exists": False,
                "audio_lane": {
                    "mode": "muted_no_tts",
                    "no_tts": True,
                    "source_audio_policy": "mute",
                    "source_audio_preserved": False,
                    "bgm_configured": True,
                },
            },
        },
    )

    gate = state["ready_gate"]
    assert gate["no_dub"] is True
    assert gate["no_dub_compose_allowed"] is True
    assert gate["no_tts_compose_allowed"] is True
    assert gate["selected_compose_route"] == "bgm_only_route"
    assert gate["compose_allowed"] is True
    assert gate["compose_allowed_reason"] == "no_dub_inputs_ready"
    assert gate["no_dub_reason"] == "bgm_only_no_tts"
    assert "subtitle_not_ready" not in gate["blocking"]
    assert "audio_not_done" not in gate["blocking"]


def test_ready_gate_models_preserved_source_audio_no_tts_as_legal_line_state():
    state = compute_hot_follow_state(
        {"task_id": "hf-preserve-no-tts", "kind": "hot_follow"},
        {
            "task_id": "hf-preserve-no-tts",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": False},
            "audio": {"audio_ready": False, "dub_current": False, "no_dub": False},
            "artifact_facts": {
                "audio_lane_mode": "source_audio_preserved_no_tts",
                "tts_voiceover_exists": False,
                "audio_lane": {
                    "mode": "source_audio_preserved_no_tts",
                    "no_tts": True,
                    "source_audio_preserved": True,
                    "source_audio_policy": "preserve",
                    "bgm_configured": False,
                },
            },
        },
    )

    gate = state["ready_gate"]
    assert gate["no_dub"] is True
    assert gate["no_dub_compose_allowed"] is True
    assert gate["no_tts_compose_allowed"] is True
    assert gate["selected_compose_route"] == "preserve_source_route"
    assert gate["compose_allowed"] is True
    assert gate["compose_allowed_reason"] == "no_dub_inputs_ready"
    assert gate["no_dub_reason"] == "source_audio_preserved_no_tts"
