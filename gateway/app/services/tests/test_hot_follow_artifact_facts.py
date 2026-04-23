from __future__ import annotations

from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_artifact_facts
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_current_attempt_summary
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_operator_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


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
    assert facts["compose_input_ready"] is False
    assert facts["compose_input_reason"] == "bitrate_too_high"
    assert facts["compose_input"]["profile"]["video_bitrate"] == 9_000_000


def test_artifact_facts_formalize_derive_failed_compose_input():
    facts = build_hot_follow_artifact_facts(
        "hf-derive-failed",
        {
            "task_id": "hf-derive-failed",
            "compose_input_policy": {
                "mode": "derive_failed",
                "source": "derived_safe",
                "profile": {"width": 1081, "height": 1921, "pix_fmt": "yuv422p"},
                "safe_key": "video_input_safe.mp4",
                "reason": "derived compose input is not encoder-safe",
                "failure_code": "derive_not_encoder_safe",
            },
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )

    assert facts["compose_input_mode"] == "derive_failed"
    assert facts["compose_input_ready"] is False
    assert facts["compose_input_derive_failed"] is True
    assert facts["compose_input_failure_code"] == "derive_not_encoder_safe"
    assert facts["compose_input"]["safe_key"] == "video_input_safe.mp4"
    assert facts["compose_input"]["source"] == "derived_safe"


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
    assert facts["selected_compose_route"]["name"] == "bgm_only_route"
    assert "tts_voiceover" in facts["selected_compose_route"]["irrelevant_artifacts"]


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


def test_current_attempt_marks_derive_failed_compose_input_as_terminal():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
        },
        subtitle_lane={"subtitle_ready": True},
        dub_status="pending",
        compose_status="failed",
        composed_reason="compose_input_derive_failed",
        artifact_facts={
            "compose_input": {
                "mode": "derive_failed",
                "ready": False,
                "derive_failed": True,
                "reason": "derived compose input is not encoder-safe",
                "failure_code": "derive_not_encoder_safe",
                "profile": {},
                "source": "derived_safe",
            },
            "audio_lane": {"no_tts": True, "bgm_configured": False, "source_audio_preserved": False},
            "selected_compose_route": {"name": "no_tts_compose_route"},
        },
        no_dub_compose_allowed=True,
    )

    assert current_attempt["compose_status"] == "failed"
    assert current_attempt["compose_route_allowed"] is True
    assert current_attempt["compose_input_ready"] is False
    assert current_attempt["compose_execute_allowed"] is False
    assert current_attempt["compose_input_derive_failed_terminal"] is True
    assert current_attempt["compose_terminal_state"] == "compose_input_derive_failed_terminal"
    assert current_attempt["requires_recompose"] is False


def test_current_attempt_marks_legal_no_tts_route_as_terminal_not_running():
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

    assert current_attempt["dub_status"] == "absent"
    assert current_attempt["no_dub_route_terminal"] is True
    assert current_attempt["subtitle_terminal_state"] == "no_dub_route_terminal"
    assert current_attempt["requires_recompose"] is False


def test_route_local_tts_expected_when_subtitle_ready_without_voiceover():
    artifact_facts = build_hot_follow_artifact_facts(
        "c3a11f7852e2",
        {"task_id": "c3a11f7852e2", "compose_input_policy": {"mode": "direct"}},
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True, "subtitle_ready": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "c3a11f7852e2", "kind": "hot_follow"},
        {
            "task_id": "c3a11f7852e2",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True, "subtitle_artifact_exists": True},
            "audio": {"status": "absent", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["compose_allowed"] is False
    assert state["ready_gate"]["no_tts_compose_allowed"] is False
    assert state["ready_gate"]["audio_ready"] is False
    assert "voiceover_missing" in state["ready_gate"]["blocking"]


def test_ready_gate_distinguishes_route_allowed_from_compose_execute_allowed():
    artifact_facts = build_hot_follow_artifact_facts(
        "hf-derive-failed-gate",
        {
            "task_id": "hf-derive-failed-gate",
            "compose_input_policy": {
                "mode": "derive_failed",
                "source": "derived_safe",
                "reason": "derived compose input is not encoder-safe",
                "failure_code": "derive_not_encoder_safe",
            },
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True, "subtitle_ready": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "hf-derive-failed-gate", "kind": "hot_follow"},
        {
            "task_id": "hf-derive-failed-gate",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True, "subtitle_artifact_exists": True},
            "audio": {"status": "absent", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    gate = state["ready_gate"]
    assert gate["selected_compose_route"] == "tts_replace_route"
    assert gate["compose_route_allowed"] is False
    assert gate["compose_input_ready"] is False
    assert gate["compose_execute_allowed"] is False
    assert gate["compose_reason"] == "compose_input_derive_failed"
    assert gate["blocking"] == ["compose_input_derive_failed"]


def test_preserve_source_route_allowed_without_tts_voiceover():
    artifact_facts = build_hot_follow_artifact_facts(
        "hf-preserve-route",
        {
            "task_id": "hf-preserve-route",
            "compose_input_policy": {"mode": "direct"},
            "config": {"source_audio_policy": "preserve"},
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True, "subtitle_ready": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "hf-preserve-route", "kind": "hot_follow"},
        {
            "task_id": "hf-preserve-route",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True, "subtitle_artifact_exists": True},
            "audio": {"status": "absent", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "preserve_source_route"
    assert state["ready_gate"]["compose_allowed"] is True
    assert state["ready_gate"]["no_tts_compose_allowed"] is True


def test_bgm_only_route_allowed_without_tts_voiceover():
    artifact_facts = build_hot_follow_artifact_facts(
        "hf-bgm-route",
        {
            "task_id": "hf-bgm-route",
            "compose_input_policy": {"mode": "direct"},
            "config": {"source_audio_policy": "mute", "bgm": {"bgm_key": "deliver/tasks/hf-bgm-route/bgm.mp3"}},
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True, "subtitle_ready": True},
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "hf-bgm-route", "kind": "hot_follow"},
        {
            "task_id": "hf-bgm-route",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True, "subtitle_artifact_exists": True},
            "audio": {"status": "absent", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "bgm_only_route"
    assert state["ready_gate"]["compose_allowed"] is True
    assert state["ready_gate"]["no_tts_compose_allowed"] is True


def test_tts_replace_route_missing_voiceover_blocks_only_tts_route():
    artifact_facts = {
        "compose_input": {"mode": "direct", "blocked": False, "reason": None, "profile": {}, "source": "test"},
        "compose_input_blocked": False,
        "audio_lane": {"tts_voiceover_exists": True, "source_audio_preserved": False, "bgm_configured": False, "no_tts": False},
        "selected_compose_route": {"name": "tts_replace_route"},
    }
    state = compute_hot_follow_state(
        {"task_id": "hf-tts-route", "kind": "hot_follow"},
        {
            "task_id": "hf-tts-route",
            "final": {"exists": False},
            "subtitles": {"subtitle_ready": True, "subtitle_artifact_exists": True},
            "audio": {"status": "pending", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["compose_allowed"] is False
    assert state["ready_gate"]["compose_reason"] == "audio_missing"


def test_non_tts_route_dub_terminal_states_do_not_stay_pending_or_running():
    for dub_status, no_dub_reason, expected in (
        ("running", None, "absent"),
        ("pending", "dub_input_empty", "empty"),
        ("skipped", None, "skipped"),
    ):
        current_attempt = build_hot_follow_current_attempt_summary(
            voice_state={
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "no_dub_reason": no_dub_reason,
            },
            subtitle_lane={"subtitle_ready": True, "subtitle_artifact_exists": True, "edited_text": "ok"},
            dub_status=dub_status,
            compose_status="pending",
            composed_reason="final_missing",
            artifact_facts={
                "compose_input": {"mode": "direct", "blocked": False, "reason": None, "profile": {}, "source": "test"},
                "audio_lane": {"no_tts": True, "bgm_configured": False, "source_audio_preserved": False},
                "selected_compose_route": {"name": "no_tts_compose_route"},
            },
            no_dub=bool(no_dub_reason or dub_status == "skipped"),
            no_dub_compose_allowed=True,
        )

        assert current_attempt["dub_status"] == expected
        assert current_attempt["compose_allowed"] is True
        assert current_attempt["no_tts_compose_allowed"] is True


def test_operator_summary_projects_terminal_blocked_and_no_dub_attempts():
    blocked = build_hot_follow_operator_summary(
        artifact_facts={"final_exists": False},
        current_attempt={
            "compose_status": "blocked",
            "compose_blocked_terminal": True,
            "compose_reason": "bitrate_too_high",
        },
        no_dub=False,
        subtitle_ready=True,
    )
    no_dub = build_hot_follow_operator_summary(
        artifact_facts={"final_exists": False},
        current_attempt={
            "dub_status": "skipped",
            "no_dub_route_terminal": True,
        },
        no_dub=True,
        subtitle_ready=False,
    )

    assert "bitrate_too_high" in blocked["recommended_next_action"]
    assert "无 TTS 合成路径" in no_dub["recommended_next_action"]
