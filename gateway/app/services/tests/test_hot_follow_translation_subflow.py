from gateway.app.services.hot_follow_translation_subflow import (
    build_target_subtitle_translation_facts,
    reduce_target_subtitle_translation_subflow,
)
from gateway.app.services.hot_follow_process_state import reduce_hot_follow_process_state
from gateway.app.services.hot_follow_workbench_presenter import (
    build_hot_follow_artifact_facts,
    build_hot_follow_operator_summary,
)
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


def _compose_input():
    return {"mode": "direct", "ready": True, "blocked": False}


def _deliverable_url(_task_id: str, _task: dict, _kind: str) -> str | None:
    return None


def test_translation_subflow_fact_layer_keeps_artifacts_as_facts_only():
    facts = build_target_subtitle_translation_facts(
        task={
            "origin_srt_path": "deliver/tasks/t/origin.srt",
            "subtitle_helper_status": "ready",
            "subtitle_helper_translated_text": "Xin chao",
            "subtitle_helper_target_lang": "vi",
        },
        subtitle_lane={
            "parse_source_text": "1\n00:00:00,000 --> 00:00:01,000\nhello\n",
            "subtitle_artifact_exists": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "subtitle_missing",
        },
    )

    assert facts["origin_subtitle_exists"] is True
    assert facts["helper_translation_requested"] is True
    assert facts["helper_raw_output_received"] is True
    assert facts["target_subtitle_materialized"] is False
    assert "waiting" not in facts
    assert "retryable" not in facts


def test_translation_subflow_pending_to_authoritative_current():
    pending = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "helper_translation_requested": True,
            "helper_output_state": "helper_output_pending",
            "helper_provider_health": "provider_ok",
            "target_subtitle_materialized": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
        },
        lane_state="voice_led_tts_route",
    )
    ready = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "helper_translation_requested": True,
            "helper_raw_output_received": True,
            "target_subtitle_materialized": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
        },
        lane_state="voice_led_tts_route",
    )

    assert pending["state"] == "translation_output_pending_retryable"
    assert pending["waiting"] is True
    assert pending["retryable"] is True
    assert ready["state"] == "target_subtitle_authoritative_current"
    assert ready["authoritative_current"] is True
    assert ready["blocking_reason"] is None


def test_translation_subflow_distinguishes_unmaterialized_and_retryable_failure():
    unmaterialized = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "helper_translation_requested": True,
            "helper_raw_output_received": True,
            "target_subtitle_materialized": False,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
        },
        lane_state="voice_led_tts_route",
    )
    failed_retryable = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "helper_translation_requested": True,
            "helper_raw_output_received": True,
            "target_subtitle_materialized": True,
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "target_subtitle_source_mismatch",
        },
        lane_state="voice_led_tts_route",
    )

    assert unmaterialized["state"] == "translation_output_received_unmaterialized"
    assert unmaterialized["blocking_reason"] == "translation_output_unmaterialized"
    assert failed_retryable["state"] == "translation_materialization_failed_retryable"
    assert failed_retryable["blocking_reason"] == "translation_materialization_failed_retryable"


def test_translation_subflow_terminal_manual_override_and_not_required():
    terminal = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "helper_translation_requested": True,
            "helper_provider_health": "provider_terminal_failure",
            "helper_error_reason": "helper_translate_terminal_failure",
        },
        lane_state="voice_led_tts_route",
    )
    manual = reduce_target_subtitle_translation_subflow(
        facts={
            "origin_subtitle_exists": True,
            "target_subtitle_materialized": True,
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "manual_override_present": True,
        },
        lane_state="voice_led_tts_route",
    )
    not_required = reduce_target_subtitle_translation_subflow(
        facts={"origin_subtitle_exists": False},
        lane_state="no_dub_no_tts_route",
    )

    assert terminal["state"] == "translation_materialization_failed_terminal"
    assert terminal["terminal"] is True
    assert manual["state"] == "manual_target_subtitle_override_current"
    assert manual["authoritative_current"] is True
    assert not_required["state"] == "translation_not_required_for_route"


def test_process_reducer_consumes_translation_subflow_for_blocking_reason():
    process = reduce_hot_follow_process_state(
        state={
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {"no_tts": False, "source_audio_preserved": False, "bgm_configured": False},
                "target_subtitle_translation_facts": {
                    "origin_subtitle_exists": True,
                    "helper_translation_requested": True,
                    "helper_raw_output_received": True,
                    "target_subtitle_materialized": False,
                    "target_subtitle_current": False,
                    "target_subtitle_authoritative_source": False,
                },
            },
            "audio": {"audio_ready": False, "audio_ready_reason": "audio_not_ready"},
            "subtitles": {
                "subtitle_ready": False,
                "target_subtitle_current": False,
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice led transcript",
            },
        }
    )

    assert process["target_subtitle_translation_state"] == "translation_output_received_unmaterialized"
    assert process["target_subtitle_translation_blocking_reason"] == "translation_output_unmaterialized"
    assert process["subtitle_translation_waiting_retryable"] is True
    assert process["dub_process_state"] == "dub_waiting_for_target_subtitle"
    assert process["compose_execute_allowed"] is False


def test_ready_gate_and_top_level_process_share_translation_blocking_reason():
    state = compute_hot_follow_state(
        {"task_id": "hf-subflow-gate", "kind": "hot_follow"},
        {
            "task_id": "hf-subflow-gate",
            "final": {"exists": False},
            "artifact_facts": {
                "compose_input": _compose_input(),
                "audio_lane": {"no_tts": False, "source_audio_preserved": False, "bgm_configured": False},
                "target_subtitle_translation_facts": {
                    "origin_subtitle_exists": True,
                    "helper_translation_requested": True,
                    "helper_raw_output_received": True,
                    "target_subtitle_materialized": False,
                    "target_subtitle_current": False,
                    "target_subtitle_authoritative_source": False,
                },
            },
            "audio": {"status": "pending", "audio_ready": False, "audio_ready_reason": "waiting_for_target_subtitle_translation"},
            "subtitles": {
                "subtitle_ready": False,
                "target_subtitle_current": False,
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice led transcript",
            },
        },
    )

    process = state["hot_follow_process_state"]
    assert process["target_subtitle_translation_blocking_reason"] == "translation_output_unmaterialized"
    assert state["ready_gate"]["subtitle_ready_reason"] == "translation_output_unmaterialized"
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"


def test_artifact_facts_and_operator_summary_project_translation_subflow():
    subtitle_lane = {
        "subtitle_artifact_exists": False,
        "subtitle_ready": False,
        "target_subtitle_current": False,
        "target_subtitle_authoritative_source": False,
        "parse_source_text": "voice led transcript",
        "helper_translate_status": "helper_output_pending",
        "helper_translate_output_state": "helper_output_pending",
        "helper_translate_provider_health": "provider_ok",
        "helper_translate_retryable": True,
    }
    facts = build_hot_follow_artifact_facts(
        "hf-subflow-facts",
        {"task_id": "hf-subflow-facts", "compose_input_policy": {"mode": "direct"}},
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane=subtitle_lane,
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    process = reduce_hot_follow_process_state(
        state={
            "artifact_facts": facts,
            "subtitles": subtitle_lane,
            "audio": {"audio_ready": False, "audio_ready_reason": "waiting_for_target_subtitle_translation"},
        }
    )
    summary = build_hot_follow_operator_summary(
        artifact_facts=facts,
        current_attempt={
            "subtitle_translation_waiting_retryable": True,
            "target_subtitle_translation_subflow": process["target_subtitle_translation_subflow"],
            "audio_ready": False,
            "dub_status": "pending",
            "compose_status": "pending",
        },
        no_dub=False,
    )

    assert facts["target_subtitle_translation_facts"]["origin_subtitle_exists"] is True
    assert process["target_subtitle_translation_state"] == "translation_output_pending_retryable"
    assert "目标字幕翻译尚未就绪" in summary["recommended_next_action"]
