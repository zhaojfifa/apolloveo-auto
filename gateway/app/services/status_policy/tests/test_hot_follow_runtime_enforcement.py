from __future__ import annotations

from gateway.app.services.hot_follow_skills_advisory import maybe_build_hot_follow_advisory
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


def _artifact_facts(
    *,
    route_name: str = "tts_replace_route",
    helper_translate_failed: bool = False,
    helper_translate_failed_voice_led: bool = False,
    final_exists: bool = False,
    audio_lane: dict | None = None,
    compose_input: dict | None = None,
) -> dict:
    return {
        "final_exists": final_exists,
        "helper_translate_failed": helper_translate_failed,
        "helper_translate_failed_voice_led": helper_translate_failed_voice_led,
        "helper_translate_error_reason": "helper_translate_provider_exhausted" if helper_translate_failed else None,
        "helper_translate_error_message": "temporary provider issue" if helper_translate_failed else None,
        "compose_input": compose_input
        or {
            "mode": "direct",
            "ready": True,
            "blocked": False,
            "derive_failed": False,
            "reason": None,
            "failure_code": None,
        },
        "compose_input_mode": "direct",
        "compose_input_ready": True,
        "compose_input_blocked": False,
        "compose_input_derive_failed": False,
        "compose_input_reason": None,
        "audio_lane": audio_lane
        or {
            "mode": "tts_voiceover_only",
            "tts_voiceover_exists": False,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_key": None,
            "bgm_configured": False,
            "no_tts": False,
        },
        "selected_compose_route": {"name": route_name},
    }


def _base_state(
    *,
    subtitles: dict | None = None,
    audio: dict | None = None,
    artifact_facts: dict | None = None,
    final: dict | None = None,
    historical_final: dict | None = None,
    compose_status: str = "pending",
    composed_reason: str = "final_missing",
    final_stale_reason=None,
    errors: dict | None = None,
    pipeline: list | None = None,
    pipeline_legacy: dict | None = None,
) -> dict:
    return {
        "task_id": "hf-runtime-enforcement",
        "kind": "hot_follow",
        "subtitles": subtitles
        or {
            "status": "pending",
            "error": None,
            "subtitle_ready": False,
            "subtitle_ready_reason": "subtitle_missing",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "target_subtitle_authoritative_source": False,
            "helper_translate_status": None,
            "helper_translate_failed": False,
        },
        "audio": audio
        or {
            "status": "pending",
            "error": None,
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
            "dub_current_reason": "dub_not_done",
            "no_dub": False,
            "no_dub_reason": None,
        },
        "artifact_facts": artifact_facts or _artifact_facts(),
        "final": final or {"exists": False},
        "historical_final": historical_final or {"exists": False},
        "compose_status": compose_status,
        "composed_reason": composed_reason,
        "final_stale_reason": final_stale_reason,
        "errors": errors
        or {
            "subtitles": {"reason": None, "message": None},
            "audio": {"reason": None, "message": None},
        },
        "pipeline": pipeline
        or [
            {"key": "subtitles", "status": "pending", "error": None},
            {"key": "dub", "status": "pending", "error": None},
        ],
        "pipeline_legacy": pipeline_legacy
        or {
            "subtitles": {"status": "pending"},
            "audio": {"status": "pending"},
        },
    }


def test_subtitle_waiting_does_not_project_terminal_no_tts_route():
    state = compute_hot_follow_state(
        {"task_id": "hf-route-waiting", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "pending",
                "error": "translation incomplete",
                "subtitle_ready": False,
                "subtitle_ready_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice-led source",
                "helper_translate_status": "failed",
                "helper_translate_failed": True,
            },
            audio={
                "status": "skipped",
                "error": None,
                "audio_ready": False,
                "audio_ready_reason": "dub_not_done",
                "dub_current": False,
                "dub_current_reason": "dub_not_done",
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            artifact_facts=_artifact_facts(
                route_name="no_tts_compose_route",
                helper_translate_failed=True,
                helper_translate_failed_voice_led=True,
                audio_lane={
                    "mode": "muted_no_tts",
                    "tts_voiceover_exists": False,
                    "source_audio_policy": "mute",
                    "source_audio_preserved": False,
                    "bgm_key": None,
                    "bgm_configured": False,
                    "no_tts": True,
                },
            ),
        ),
    )

    assert state["artifact_facts"]["selected_compose_route"]["name"] == "tts_replace_route"
    assert state["current_attempt"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["no_tts_compose_allowed"] is False
    assert state["current_attempt"]["no_dub_route_terminal"] is False


def test_selected_compose_route_is_single_sourced_across_surfaces():
    state = compute_hot_follow_state(
        {"task_id": "hf-route-single-source", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": None,
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": None,
                "helper_translate_failed": False,
            },
            audio={
                "status": "done",
                "error": None,
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": False,
                "no_dub_reason": None,
            },
            artifact_facts=_artifact_facts(final_exists=True),
            final={"exists": True, "fresh": True},
            compose_status="done",
            composed_reason="ready",
        ),
    )

    route = state["ready_gate"]["selected_compose_route"]
    assert route == "tts_replace_route"
    assert state["artifact_facts"]["selected_compose_route"]["name"] == route
    assert state["current_attempt"]["selected_compose_route"] == route
    advisory = maybe_build_hot_follow_advisory(
        {"task_id": "hf-route-single-source", "kind": "hot_follow"},
        {
            "ready_gate": state["ready_gate"],
            "artifact_facts": state["artifact_facts"],
            "current_attempt": state["current_attempt"],
            "operator_summary": {"last_successful_output_available": True},
            "pipeline": [],
            "pipeline_legacy": {},
            "deliverables": [],
            "media": {},
            "source_video": {},
        },
    )
    assert ((advisory or {}).get("evidence") or {}).get("selected_compose_route") == route


def test_subtitles_done_clears_stale_subtitle_error():
    state = compute_hot_follow_state(
        {"task_id": "hf-subtitles-clear", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": "missing_authoritative_subtitle",
                "subtitle_ready": False,
                "subtitle_ready_reason": "missing_authoritative_subtitle",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "missing_authoritative_subtitle",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": None,
                "helper_translate_failed": False,
            },
            errors={
                "subtitles": {
                    "reason": "missing_authoritative_subtitle",
                    "message": "missing_authoritative_subtitle",
                },
                "audio": {"reason": None, "message": None},
            },
            pipeline=[
                {"key": "subtitles", "status": "done", "error": "missing_authoritative_subtitle"},
            ],
            pipeline_legacy={"subtitles": {"status": "pending"}},
        ),
    )

    assert state["subtitles"]["subtitle_ready"] is True
    assert state["subtitles"]["subtitle_ready_reason"] == "ready"
    assert state["subtitles"]["error"] is None
    assert state["errors"]["subtitles"] == {"reason": None, "message": None}
    assert state["pipeline"][0]["error"] is None
    assert state["pipeline_legacy"]["subtitles"]["status"] == "done"


def test_audio_done_and_audio_ready_clear_top_level_audio_error():
    state = compute_hot_follow_state(
        {"task_id": "hf-audio-clear", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": None,
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": None,
                "helper_translate_failed": False,
            },
            audio={
                "status": "done",
                "error": "stale audio error",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": False,
                "no_dub_reason": None,
            },
            errors={
                "subtitles": {"reason": None, "message": None},
                "audio": {"reason": "tts_failed", "message": "stale audio error"},
            },
            pipeline=[{"key": "dub", "status": "done", "error": "stale audio error"}],
            pipeline_legacy={"audio": {"status": "pending"}},
        ),
    )

    assert state["audio"]["error"] is None
    assert state["errors"]["audio"] == {"reason": None, "message": None}
    assert state["pipeline"][0]["error"] is None
    assert state["pipeline_legacy"]["audio"]["status"] == "done"


def test_pack_pending_clears_stale_pipeline_failed_pack_error():
    state = compute_hot_follow_state(
        {"task_id": "hf-pack-clear", "kind": "hot_follow"},
        _base_state(
            errors={
                "subtitles": {"reason": None, "message": None},
                "audio": {"reason": None, "message": None},
                "pack": {"reason": "pipeline_failed", "message": "pipeline_failed"},
            },
            pipeline=[{"key": "pack", "status": "pending", "error": None}],
            pipeline_legacy={"pack": {"status": "pending"}},
        ),
    )

    assert state["errors"]["pack"] == {"reason": None, "message": None}


def test_helper_retryable_warning_does_not_override_mainline_success():
    state = compute_hot_follow_state(
        {"task_id": "hf-helper-warning", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": None,
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": "failed",
                "helper_translate_failed": True,
                "helper_translate_error_reason": "helper_translate_provider_exhausted",
                "helper_translate_error_message": "temporary provider issue",
            },
            audio={
                "status": "done",
                "error": None,
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": False,
                "no_dub_reason": None,
            },
            artifact_facts=_artifact_facts(
                helper_translate_failed=True,
                helper_translate_failed_voice_led=True,
                final_exists=True,
            ),
            final={"exists": True, "fresh": True},
            compose_status="done",
            composed_reason="ready",
        ),
    )

    assert state["helper"]["current_state"] == "helper_resolved_with_retryable_provider_warning"
    assert state["helper"]["output_state"] == "helper_output_unavailable"
    assert state["helper"]["provider_health"] == "provider_retryable_failure"
    assert state["current_attempt"]["helper_translate_failed"] is False
    assert state["current_attempt"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"


def test_helper_state_is_always_explicit_not_null():
    state = compute_hot_follow_state(
        {"task_id": "hf-helper-explicit", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "pending",
                "error": None,
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "subtitle_missing",
                "target_subtitle_authoritative_source": False,
                "helper_translate_status": "pending",
                "helper_translate_failed": False,
            },
        ),
    )

    assert state["helper"]["current_state"] == "helper_sidechannel_waiting"
    assert state["helper"]["output_state"] == "helper_output_pending"
    assert state["helper"]["provider_health"] == "provider_ok"
    assert state["subtitles"]["helper_translate_output_state"] == "helper_output_pending"
    assert state["subtitles"]["helper_translate_provider_health"] == "provider_ok"


def test_history_residue_does_not_drive_current_truth():
    state = compute_hot_follow_state(
        {
            "task_id": "hf-history-residue",
            "kind": "hot_follow",
            "events": [
                {"channel": "dub", "code": "target_subtitle_empty"},
                {"channel": "dub", "code": "dub_input_empty"},
            ],
        },
        _base_state(
            subtitles={
                "status": "done",
                "error": None,
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": None,
                "helper_translate_failed": False,
            },
            audio={
                "status": "done",
                "error": None,
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            artifact_facts=_artifact_facts(
                route_name="no_tts_compose_route",
                final_exists=True,
            ),
            final={"exists": True, "fresh": True},
            compose_status="done",
            composed_reason="ready",
        ),
    )

    assert state["artifact_facts"]["selected_compose_route"]["name"] == "tts_replace_route"
    assert state["current_attempt"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["audio"]["no_dub"] is False
    assert state["audio"]["no_dub_reason"] is None


def test_23b8cbd4439b_class_sequence_closes_cleanly():
    early = compute_hot_follow_state(
        {"task_id": "23b8cbd4439b-early", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "pending",
                "error": "translation incomplete",
                "subtitle_ready": False,
                "subtitle_ready_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice-led source",
                "helper_translate_status": "failed",
                "helper_translate_failed": True,
            },
            audio={
                "status": "pending",
                "error": None,
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "dub_current": False,
                "dub_current_reason": "dub_not_done",
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            artifact_facts=_artifact_facts(
                route_name="no_tts_compose_route",
                helper_translate_failed=True,
                helper_translate_failed_voice_led=True,
                audio_lane={
                    "mode": "muted_no_tts",
                    "tts_voiceover_exists": False,
                    "source_audio_policy": "mute",
                    "source_audio_preserved": False,
                    "bgm_key": None,
                    "bgm_configured": False,
                    "no_tts": True,
                },
            ),
        ),
    )
    middle = compute_hot_follow_state(
        {"task_id": "23b8cbd4439b-middle", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": "missing_authoritative_subtitle",
                "subtitle_ready": False,
                "subtitle_ready_reason": "missing_authoritative_subtitle",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": "failed",
                "helper_translate_failed": True,
            },
            audio={
                "status": "done",
                "error": "stale audio error",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            errors={
                "subtitles": {"reason": "missing_authority", "message": "missing_authority"},
                "audio": {"reason": "tts_failed", "message": "stale audio error"},
                "pack": {"reason": "pipeline_failed", "message": "pipeline_failed"},
            },
            pipeline=[
                {"key": "subtitles", "status": "done", "error": "missing_authority"},
                {"key": "dub", "status": "done", "error": "stale audio error"},
                {"key": "pack", "status": "pending", "error": None},
            ],
            pipeline_legacy={
                "subtitles": {"status": "pending"},
                "audio": {"status": "pending"},
                "pack": {"status": "pending"},
            },
            artifact_facts=_artifact_facts(
                route_name="no_tts_compose_route",
                helper_translate_failed=True,
                helper_translate_failed_voice_led=True,
                final_exists=True,
            ),
            final={"exists": True, "fresh": True},
            compose_status="pending",
            composed_reason="final_missing",
        ),
    )
    clean = compute_hot_follow_state(
        {"task_id": "23b8cbd4439b-clean", "kind": "hot_follow"},
        _base_state(
            subtitles={
                "status": "done",
                "error": None,
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
                "target_subtitle_authoritative_source": True,
                "helper_translate_status": "failed",
                "helper_translate_failed": True,
            },
            audio={
                "status": "done",
                "error": None,
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "dub_current": True,
                "dub_current_reason": "ready",
                "no_dub": False,
                "no_dub_reason": None,
            },
            artifact_facts=_artifact_facts(final_exists=True),
            final={"exists": True, "fresh": True},
            compose_status="done",
            composed_reason="ready",
        ),
    )

    assert early["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert early["current_attempt"]["no_dub_route_terminal"] is False
    assert middle["errors"]["subtitles"] == {"reason": None, "message": None}
    assert middle["errors"]["audio"] == {"reason": None, "message": None}
    assert middle["errors"]["pack"] == {"reason": None, "message": None}
    assert clean["current_attempt"]["selected_compose_route"] == "tts_replace_route"
    assert clean["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert clean["current_attempt"]["audio_ready"] is True
    assert clean["composed_reason"] == "ready"
