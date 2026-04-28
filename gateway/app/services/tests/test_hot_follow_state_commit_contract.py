from gateway.app.services.contract_runtime.current_attempt_runtime import (
    build_hot_follow_current_attempt_summary,
    selected_route_from_state,
)
from gateway.app.services import task_view_presenters
from gateway.app.services.task_view_helpers import hot_follow_terminal_no_dub_projection
from gateway.app.services.task_view_projection import hf_pipeline_state
from gateway.app.services.task_view_workbench_contract import _subtitles_section


VI_TARGET_SRT = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"


def _compose_input():
    return {
        "mode": "direct",
        "ready": True,
        "blocked": False,
        "reason": None,
    }


def test_visible_target_text_before_authority_commit_does_not_project_no_tts_route():
    route = selected_route_from_state(
        {"kind": "hot_follow"},
        {
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {
                    "tts_voiceover_exists": False,
                    "source_audio_preserved": False,
                    "bgm_configured": False,
                    "no_tts": True,
                },
            },
            "audio": {
                "audio_ready": False,
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            "subtitles": {
                "subtitle_ready": False,
                "target_subtitle_current": False,
                "target_subtitle_authoritative_source": False,
                "target_subtitle_current_reason": "subtitle_missing",
                "edited_text": VI_TARGET_SRT,
                "srt_text": VI_TARGET_SRT,
                "primary_editable_text": VI_TARGET_SRT,
            },
            "final": {"exists": False},
        },
    )

    assert route["name"] == "tts_replace_route"
    assert route["no_tts_compose_allowed"] is False
    assert route["compose_execute_allowed"] is False


def test_url_lane_authority_false_helper_pending_keeps_downstream_deferred():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "target_subtitle_not_authoritative",
            "dub_current": False,
            "dub_current_reason": "target_subtitle_not_authoritative",
            "dub_matches_current_subtitle": False,
            "dub_subtitle_reason": "target_subtitle_not_authoritative",
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_ready_reason": "helper_output_pending",
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "target_subtitle_not_authoritative",
            "dub_input_text": "",
            "dub_input_source": None,
            "actual_burn_subtitle_source": None,
            "helper_translate_status": "helper_output_pending",
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="audio_not_ready",
        artifact_facts={
            "compose_input": _compose_input(),
            "audio_lane": {
                "tts_voiceover_exists": False,
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": False,
            },
            "helper_translate_status": "helper_output_pending",
        },
        no_dub=False,
        no_dub_compose_allowed=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["audio_ready"] is False
    assert current_attempt["compose_allowed"] is False
    assert current_attempt["compose_execute_allowed"] is False
    assert current_attempt["tts_lane_expected"] is False
    assert current_attempt["current_subtitle_source"] is None
    assert current_attempt["no_dub_route_terminal"] is False


def test_voice_led_helper_pending_is_retryable_translation_waiting_state():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "waiting_for_target_subtitle_translation",
            "dub_current": False,
            "dub_current_reason": "waiting_for_target_subtitle_translation",
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_ready_reason": "waiting_for_target_subtitle_translation",
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "parse_source_text": "1\n00:00:00,000 --> 00:00:02,000\n你好\n",
            "dub_input_text": "",
            "helper_translate_status": "helper_output_pending",
            "helper_translate_output_state": "helper_output_pending",
            "helper_translate_provider_health": "provider_ok",
            "helper_translate_retryable": True,
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="audio_not_ready",
        artifact_facts={
            "compose_input": _compose_input(),
            "audio_lane": {
                "tts_voiceover_exists": False,
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": False,
            },
            "selected_compose_route": {"name": "tts_replace_route"},
            "helper_translate_status": "helper_output_pending",
            "helper_translate_output_state": "helper_output_pending",
            "helper_translate_provider_health": "provider_ok",
            "helper_translate_retryable": True,
        },
        no_dub=False,
        no_dub_compose_allowed=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["subtitle_translation_waiting_retryable"] is True
    assert current_attempt["subtitle_terminal_state"] == "subtitle_translation_waiting_retryable"
    assert current_attempt["compose_execute_allowed"] is False
    assert current_attempt["helper_translate_retryable"] is True


def test_retry_subtitles_pipeline_done_is_demoted_without_target_authority():
    status, summary = hf_pipeline_state(
        {
            "kind": "hot_follow",
            "status": "processing",
            "last_step": "subtitles",
            "subtitles_status": "done",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "target_subtitle_authoritative_source": False,
        },
        "subtitles",
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_ready_reason": "subtitle_missing",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "target_subtitle_authoritative_source": False,
        },
    )

    assert status != "done"
    assert status == "running"
    assert summary == "subtitle_missing"


def test_url_lane_authority_true_success_transitions_coherently_to_tts_ready():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "voiceover_url": "/v1/tasks/6de25b30e6e1/audio_mm",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_ready_reason": "ready",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "dub_input_text": VI_TARGET_SRT,
            "dub_input_source": "target_subtitle",
            "actual_burn_subtitle_source": "vi.srt",
            "edited_text": VI_TARGET_SRT,
        },
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        final_stale_reason=None,
        artifact_facts={
            "compose_input": _compose_input(),
            "audio_lane": {
                "tts_voiceover_exists": True,
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": False,
            },
            "final_exists": True,
        },
        no_dub=False,
        no_dub_compose_allowed=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["audio_ready"] is True
    assert current_attempt["compose_allowed"] is True
    assert current_attempt["compose_execute_allowed"] is True
    assert current_attempt["current_subtitle_source"] == "vi.srt"
    assert current_attempt["no_dub_route_terminal"] is False


def test_recovered_authoritative_subtitle_truth_clears_subtitles_error_surface():
    section = _subtitles_section(
        task={"subtitles_error": "权威目标字幕缺失，不能记录为字幕成功。"},
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "subtitle_ready_reason": "ready",
            "primary_editable_text": VI_TARGET_SRT,
            "edited_text": VI_TARGET_SRT,
            "srt_text": VI_TARGET_SRT,
            "helper_translate_failed": True,
            "helper_translate_error_reason": "helper_translate_provider_exhausted",
            "helper_translate_error_message": "翻译服务当前额度不足或请求过多，请稍后重试。",
            "helper_translate_terminal": True,
        },
        subtitles_state="done",
        origin_text="",
        subtitles_text=VI_TARGET_SRT,
        normalized_source_text="",
    )

    assert section["error"] is None
    assert section["helper_translation"]["failed"] is False
    assert section["helper_translation"]["reason"] is None
    assert section["helper_translation"]["message"] is None
    assert section["helper_translation"]["terminal"] is False


def test_recovered_authoritative_route_ignores_stale_no_dub_residue():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "edited_text": VI_TARGET_SRT,
            "srt_text": VI_TARGET_SRT,
        },
        dub_status="skipped",
        compose_status="pending",
        composed_reason="audio_not_ready",
        artifact_facts={
            "compose_input": _compose_input(),
            "audio_lane": {
                "tts_voiceover_exists": False,
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": True,
            },
        },
        no_dub=True,
        no_dub_compose_allowed=True,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["no_tts_compose_allowed"] is False


def test_stable_local_upload_helper_success_still_uses_tts_route():
    route = selected_route_from_state(
        {"kind": "hot_follow"},
        {
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {
                    "tts_voiceover_exists": False,
                    "source_audio_preserved": False,
                    "bgm_configured": False,
                    "no_tts": True,
                },
            },
            "audio": {"audio_ready": False, "no_dub": False, "no_dub_reason": None},
            "subtitles": {
                "subtitle_ready": True,
                "target_subtitle_current": True,
                "target_subtitle_authoritative_source": True,
                "target_subtitle_current_reason": "ready",
                "edited_text": VI_TARGET_SRT,
            },
        },
    )

    assert route["name"] == "tts_replace_route"


def test_stable_preserve_bgm_source_audio_route_is_unchanged():
    route = selected_route_from_state(
        {"kind": "hot_follow"},
        {
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {
                    "tts_voiceover_exists": False,
                    "source_audio_preserved": True,
                    "bgm_configured": True,
                    "no_tts": True,
                },
            },
            "audio": {"audio_ready": False, "no_dub": False, "no_dub_reason": None},
            "subtitles": {
                "subtitle_ready": False,
                "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            },
        },
    )

    assert route["name"] == "preserve_source_route"
    assert route["compose_allowed"] is True


def test_preserve_source_no_tts_lane_does_not_select_tts_replace_or_stale_block():
    state = {
        "artifact_facts": {
            "compose_input": _compose_input(),
            "audio_lane": {
                "tts_voiceover_exists": False,
                "source_audio_preserved": True,
                "bgm_configured": False,
                "no_tts": True,
            },
        },
        "audio": {
            "audio_ready": False,
            "audio_ready_reason": "dub_stale_after_subtitles",
            "dub_current": False,
            "dub_current_reason": "dub_stale_after_subtitles",
            "no_dub": False,
            "no_dub_reason": None,
        },
        "subtitles": {
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            "dub_input_text": "",
        },
        "final": {"exists": False},
    }

    route = selected_route_from_state({"kind": "hot_follow"}, state)
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state=state["audio"],
        subtitle_lane=state["subtitles"],
        dub_status="pending",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=state["artifact_facts"],
        no_dub=False,
    )

    assert route["name"] == "preserve_source_route"
    assert route["name"] != "tts_replace_route"
    assert route["compose_allowed"] is True
    assert current_attempt["selected_compose_route"] == "preserve_source_route"
    assert current_attempt["no_dub_route_terminal"] is True
    assert current_attempt["tts_lane_expected"] is False
    assert current_attempt["compose_allowed_reason"] == "ready"


def test_preserve_source_no_target_projection_sets_legal_no_dub_owner():
    no_dub, no_dub_reason, no_dub_message = hot_follow_terminal_no_dub_projection(
        pipeline_config={"source_audio_policy": "preserve"},
        task={"kind": "hot_follow", "config": {"source_audio_policy": "preserve"}},
        route_state={"content_mode": "voice_led"},
        subtitle_lane={
            "subtitle_ready": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            "dub_input_text": "",
        },
        voice_state={"audio_ready": False, "deliverable_audio_done": False, "voiceover_url": None},
    )

    assert no_dub is True
    assert no_dub_reason == "source_audio_preserved_no_tts"
    assert no_dub_message


def test_local_preserve_source_plus_tts_success_keeps_tts_route_and_no_dub_false():
    no_dub, no_dub_reason, no_dub_message = hot_follow_terminal_no_dub_projection(
        pipeline_config={"source_audio_policy": "preserve"},
        task={"kind": "hot_follow", "config": {"source_audio_policy": "preserve"}},
        route_state={"content_mode": "voice_led"},
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "dub_input_text": VI_TARGET_SRT,
            "dub_input_source": "target_subtitle",
        },
        voice_state={"audio_ready": True, "deliverable_audio_done": True, "voiceover_url": "/v1/tasks/a1c142fbf911/audio_mm"},
    )
    route = selected_route_from_state(
        {"kind": "hot_follow"},
        {
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {
                    "tts_voiceover_exists": True,
                    "source_audio_preserved": True,
                    "bgm_configured": False,
                    "no_tts": False,
                },
            },
            "audio": {"audio_ready": True, "no_dub": no_dub, "no_dub_reason": no_dub_reason},
            "subtitles": {
                "subtitle_ready": True,
                "target_subtitle_current": True,
                "target_subtitle_authoritative_source": True,
                "target_subtitle_current_reason": "ready",
                "edited_text": VI_TARGET_SRT,
            },
        },
    )

    assert no_dub is False
    assert no_dub_reason is None
    assert no_dub_message is None
    assert route["name"] == "tts_replace_route"
    assert route["compose_allowed"] is True


def test_presentation_current_attempt_dub_status_uses_l3_summary_not_l1_pipeline():
    presentation = task_view_presenters.hf_rerun_presentation_state(
        {"task_id": "hf-present-dub-status", "kind": "hot_follow"},
        {"audio_ready": False, "audio_ready_reason": "dub_stale_after_subtitles"},
        {"exists": False},
        {"exists": False},
        "done",
        current_attempt={"dub_status": "pending"},
    )

    assert presentation["current_attempt"]["dub_status"] == "pending"


def test_stable_successful_url_closure_route_and_no_dub_projection_are_unchanged():
    no_dub, no_dub_reason, no_dub_message = hot_follow_terminal_no_dub_projection(
        pipeline_config={"no_dub": "true", "dub_skip_reason": "target_subtitle_empty"},
        task={"dub_skip_reason": "target_subtitle_empty"},
        route_state={"content_mode": "voice_led"},
        subtitle_lane={
            "subtitle_ready": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
            "edited_text": VI_TARGET_SRT,
        },
        voice_state={"audio_ready": True, "voiceover_url": "/v1/tasks/hf/audio_mm"},
    )
    route = selected_route_from_state(
        {"kind": "hot_follow"},
        {
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {
                    "tts_voiceover_exists": True,
                    "source_audio_preserved": False,
                    "bgm_configured": False,
                    "no_tts": False,
                },
                "final_exists": True,
            },
            "audio": {"audio_ready": True, "no_dub": False, "no_dub_reason": None},
            "subtitles": {
                "subtitle_ready": True,
                "target_subtitle_current": True,
                "target_subtitle_authoritative_source": True,
                "target_subtitle_current_reason": "ready",
                "edited_text": VI_TARGET_SRT,
            },
            "final": {"exists": True, "fresh": True},
        },
    )

    assert no_dub is False
    assert no_dub_reason is None
    assert no_dub_message is None
    assert route["name"] == "tts_replace_route"
    assert route["compose_allowed"] is True
