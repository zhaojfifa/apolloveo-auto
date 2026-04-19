from __future__ import annotations

from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_artifact_facts
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_current_attempt_summary


def _deliverable_url(_task_id: str, _task: dict, _kind: str) -> str | None:
    return None


def test_artifact_facts_formalize_blocked_compose_input_without_policy_decision():
    facts = build_hot_follow_artifact_facts(
        "ffe9083de6ee",
        {
            "task_id": "ffe9083de6ee",
            "compose_input_policy": {
                "mode": "blocked",
                "reason": "bitrate_too_high",
                "profile": {"width": 720, "height": 1280, "video_bitrate": 9_000_000},
            },
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )

    assert facts["compose_input_mode"] == "blocked"
    assert facts["compose_input_blocked"] is True
    assert facts["compose_input_reason"] == "bitrate_too_high"
    assert facts["compose_input"]["profile"]["video_bitrate"] == 9_000_000


def test_artifact_facts_formalize_muted_no_tts_audio_lane():
    facts = build_hot_follow_artifact_facts(
        "c3a11f7852e2",
        {
            "task_id": "c3a11f7852e2",
            "config": {"source_audio_policy": "mute", "bgm": {"bgm_key": "deliver/tasks/c3/bgm.mp3"}},
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": False},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )

    assert facts["audio_lane_mode"] == "muted_no_tts"
    assert facts["audio_lane"]["no_tts"] is True
    assert facts["audio_lane"]["bgm_configured"] is True
    assert facts["tts_voiceover_exists"] is False


def test_current_attempt_marks_blocked_compose_as_terminal():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
        },
        subtitle_lane={"subtitle_ready": True},
        dub_status="done",
        compose_status="pending",
        composed_reason="final_missing",
        final_stale_reason=None,
        artifact_facts={
            "compose_input_blocked": True,
            "compose_input_reason": "bitrate_too_high",
        },
    )

    assert current_attempt["compose_status"] == "blocked"
    assert current_attempt["compose_reason"] == "bitrate_too_high"
    assert current_attempt["compose_blocked_terminal"] is True
    assert current_attempt["compose_terminal_state"] == "compose_blocked_terminal"
    assert current_attempt["requires_recompose"] is False


def test_current_attempt_marks_legal_no_tts_empty_route_as_terminal_not_running():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_artifact_exists": False,
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
        },
        dub_status="running",
        compose_status="pending",
        composed_reason="final_missing",
        artifact_facts={
            "audio_lane": {
                "no_tts": True,
                "bgm_configured": True,
                "source_audio_preserved": False,
            }
        },
        no_dub_compose_allowed=True,
    )

    assert current_attempt["dub_status"] == "skipped"
    assert current_attempt["no_dub_route_terminal"] is True
    assert current_attempt["subtitle_terminal_state"] == "no_dub_route_terminal"
    assert current_attempt["requires_recompose"] is False
