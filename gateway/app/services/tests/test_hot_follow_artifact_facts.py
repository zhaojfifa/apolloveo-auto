from __future__ import annotations

from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_artifact_facts


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
