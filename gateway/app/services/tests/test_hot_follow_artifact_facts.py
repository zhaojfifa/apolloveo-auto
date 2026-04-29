from __future__ import annotations

from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_artifact_facts
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_current_attempt_summary
from gateway.app.services.hot_follow_workbench_presenter import build_hot_follow_operator_summary
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.task_view_projection import hf_deliverables


def _deliverable_url(_task_id: str, _task: dict, _kind: str) -> str | None:
    return None


def test_origin_subtitle_deliverable_uses_subtitle_fact_truth_when_step_failed():
    deliverables = hf_deliverables(
        "hf-origin-truth",
        {
            "task_id": "hf-origin-truth",
            "kind": "hot_follow",
            "target_lang": "vi",
            "origin_srt_path": "deliver/tasks/hf-origin-truth/origin.srt",
            "subtitles_status": "failed",
        },
        subtitle_lane_loader=lambda *_args, **_kwargs: {
            "raw_source_text": "1\n00:00:00,000 --> 00:00:02,000\n你好\n",
            "parse_source_text": "1\n00:00:00,000 --> 00:00:02,000\n你好\n",
            "subtitle_artifact_exists": False,
        },
        current_voiceover_asset_loader=lambda *_args, **_kwargs: {"exists": False, "key": None},
        object_exists_fn=lambda _key: False,
        task_endpoint_loader=lambda task_id, kind: f"/v1/tasks/{task_id}/{kind}",
        signed_op_url_loader=lambda task_id, kind: f"/op/dl/{task_id}?kind={kind}",
        download_url_loader=lambda _key: None,
    )

    origin = next(row for row in deliverables if row["kind"] == "origin_subtitle")
    target = next(row for row in deliverables if row["kind"] == "subtitle")
    assert origin["state"] == "done"
    assert origin["status"] == "done"
    assert origin["open_url"] == "/v1/tasks/hf-origin-truth/origin"
    assert target["state"] == "failed"


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


def test_translation_incomplete_voice_led_shape_stays_on_tts_replace_route():
    artifact_facts = build_hot_follow_artifact_facts(
        "hf-url-translation-incomplete",
        {
            "task_id": "hf-url-translation-incomplete",
            "compose_input_policy": {"mode": "direct"},
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={
            "subtitle_artifact_exists": False,
            "subtitle_ready": False,
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "parse_source_text": "voice led transcript",
        },
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "hf-url-translation-incomplete", "kind": "hot_follow"},
        {
            "task_id": "hf-url-translation-incomplete",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice led transcript",
            },
            "audio": {"status": "pending", "audio_ready": False, "audio_ready_reason": "audio_missing"},
            "artifact_facts": artifact_facts,
        },
    )

    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["no_tts_compose_allowed"] is False


def test_translation_incomplete_voice_led_route_stays_single_source_across_fact_and_gate():
    artifact_facts = build_hot_follow_artifact_facts(
        "hf-url-translation-incomplete-single-source",
        {
            "task_id": "hf-url-translation-incomplete-single-source",
            "compose_input_policy": {"mode": "direct"},
        },
        final_info={"exists": False},
        historical_final=None,
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={
            "subtitle_artifact_exists": False,
            "subtitle_ready": False,
            "subtitle_ready_reason": "target_subtitle_translation_incomplete",
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "parse_source_text": "voice led transcript",
        },
        scene_pack=None,
        deliverable_url=_deliverable_url,
    )
    state = compute_hot_follow_state(
        {"task_id": "hf-url-translation-incomplete-single-source", "kind": "hot_follow"},
        {
            "task_id": "hf-url-translation-incomplete-single-source",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "target_subtitle_authoritative_source": False,
                "parse_source_text": "voice led transcript",
            },
            "audio": {
                "status": "pending",
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
            "artifact_facts": artifact_facts,
        },
    )
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_ready_reason": "target_subtitle_translation_incomplete",
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "target_subtitle_authoritative_source": False,
            "parse_source_text": "voice led transcript",
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts=artifact_facts,
        no_dub=True,
    )

    assert artifact_facts["selected_compose_route"]["name"] == "tts_replace_route"
    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert state["ready_gate"]["selected_compose_route"] == "tts_replace_route"


def test_preserve_policy_translation_incomplete_still_requires_tts_route_without_explicit_preserve_exception():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_artifact_exists": False,
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "target_subtitle_authoritative_source": False,
            "parse_source_text": "voice led transcript",
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
        },
        dub_status="failed",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts={
            "audio_lane": {
                "mode": "source_audio_preserved_no_tts",
                "tts_voiceover_exists": False,
                "source_audio_policy": "preserve",
                "source_audio_preserved": True,
                "bgm_configured": False,
                "no_tts": True,
            },
            "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        },
        no_dub=False,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["tts_lane_expected"] is False or current_attempt["selected_compose_route"] == "tts_replace_route"


def test_preserve_policy_explicit_no_target_exception_stays_preserve_source_route():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
        },
        subtitle_lane={
            "subtitle_ready": False,
            "subtitle_artifact_exists": False,
            "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            "target_subtitle_authoritative_source": False,
            "parse_source_text": "helper transcript",
            "edited_text": "",
            "srt_text": "",
            "dub_input_text": "",
        },
        dub_status="pending",
        compose_status="pending",
        composed_reason="compose_not_done",
        artifact_facts={
            "audio_lane": {
                "mode": "source_audio_preserved_no_tts",
                "tts_voiceover_exists": False,
                "source_audio_policy": "preserve",
                "source_audio_preserved": True,
                "bgm_configured": False,
                "no_tts": True,
            },
            "compose_input": {"mode": "direct", "ready": True, "blocked": False},
        },
        no_dub=False,
    )

    assert current_attempt["selected_compose_route"] == "preserve_source_route"
    assert current_attempt["no_dub_route_terminal"] is True


def test_current_truth_ignores_stale_empty_no_dub_reason_when_audio_is_ready():
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "no_dub_reason": "target_subtitle_empty",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_artifact_exists": True,
            "target_subtitle_authoritative_source": True,
            "edited_text": "ok",
            "srt_text": "ok",
            "dub_input_text": "ok",
        },
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        artifact_facts={
            "final_exists": True,
            "audio_lane": {
                "mode": "tts_voiceover_only",
                "tts_voiceover_exists": True,
                "source_audio_policy": "mute",
                "source_audio_preserved": False,
                "bgm_configured": False,
                "no_tts": False,
            },
            "compose_input": {"mode": "direct", "ready": True, "blocked": False},
            "helper_translate_status": "helper_output_unavailable",
            "helper_translate_output_state": "helper_output_unavailable",
            "helper_translate_provider_health": "provider_retryable_failure",
            "helper_translate_failed": True,
            "helper_translate_failed_voice_led": True,
            "helper_translate_retryable": True,
            "helper_translate_terminal": False,
        },
        no_dub=True,
    )

    assert current_attempt["selected_compose_route"] == "tts_replace_route"
    assert current_attempt["no_dub_route_terminal"] is False
    assert current_attempt["tts_lane_expected"] is True
    assert current_attempt["helper_translate_status"] == "helper_output_unavailable"
    assert current_attempt["helper_translate_output_state"] == "helper_output_unavailable"
    assert current_attempt["helper_translate_provider_health"] == "provider_retryable_failure"
    assert current_attempt["helper_translate_failed"] is False
    assert current_attempt["helper_translate_failed_voice_led"] is False


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


def test_no_dub_no_tts_compose_marks_subtitle_lane_terminal_not_running():
    artifact_facts = {
        "compose_input": {"mode": "direct", "ready": True, "blocked": False, "reason": None},
        "compose_input_ready": True,
        "audio_lane": {
            "tts_voiceover_exists": False,
            "source_audio_preserved": False,
            "bgm_configured": False,
            "no_tts": True,
        },
        "selected_compose_route": {"name": "no_tts_compose_route"},
    }
    state = compute_hot_follow_state(
        {"task_id": "hf-no-dub-terminal", "kind": "hot_follow"},
        {
            "task_id": "hf-no-dub-terminal",
            "final": {"exists": False},
            "subtitles": {
                "status": "running",
                "state": "running",
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
                "target_subtitle_current": False,
                "target_subtitle_authoritative_source": False,
            },
            "audio": {
                "status": "skipped",
                "audio_ready": False,
                "audio_ready_reason": "audio_missing",
                "no_dub": True,
                "no_dub_reason": "compose_no_tts",
            },
            "artifact_facts": artifact_facts,
            "current_attempt": {
                "selected_compose_route": "no_tts_compose_route",
                "no_dub_route_terminal": True,
            },
            "pipeline": [
                {"key": "subtitles", "status": "running", "state": "running", "error": "subtitle_missing"},
                {"key": "compose", "status": "pending", "state": "pending"},
            ],
        },
    )

    subtitles = state["subtitles"]
    subtitle_step = next(row for row in state["pipeline"] if row["key"] == "subtitles")
    assert state["ready_gate"]["selected_compose_route"] == "no_tts_compose_route"
    assert state["ready_gate"]["compose_allowed"] is True
    assert state["ready_gate"]["subtitle_ready_reason"] == "no_dub_route_terminal"
    assert subtitles["status"] == "skipped"
    assert subtitles["subtitle_ready_reason"] == "no_dub_route_terminal"
    assert subtitle_step["status"] == "skipped"
    assert subtitle_step["message"] == "no_dub_route_terminal"


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
    for dub_status, no_dub_reason, expected, compose_allowed, no_tts_allowed in (
        ("running", None, "absent", True, True),
        ("pending", "dub_input_empty", "pending", False, False),
        ("skipped", None, "skipped", True, True),
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
        assert current_attempt["compose_allowed"] is compose_allowed
        assert current_attempt["no_tts_compose_allowed"] is no_tts_allowed


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


def test_helper_failure_does_not_override_mainline_success():
    artifact_facts = {
        "final_exists": True,
        "audio_exists": True,
        "helper_translate_status": "helper_resolved_with_retryable_provider_warning",
        "helper_translate_output_state": "helper_output_resolved",
        "helper_translate_provider_health": "provider_retryable_failure",
        "helper_translate_composite_state": "helper_resolved_with_retryable_provider_warning",
        "helper_translate_failed": False,
        "helper_translate_failed_voice_led": False,
        "helper_translate_error_reason": "helper_translate_provider_exhausted",
        "helper_translate_error_message": "翻译服务当前额度不足或请求过多，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。",
        "helper_translate_retryable": True,
        "helper_translate_terminal": False,
        "helper_translate_warning_only": True,
        "audio_lane": {
            "mode": "tts_voiceover_only",
            "tts_voiceover_exists": True,
            "source_audio_policy": "mute",
            "source_audio_preserved": False,
            "bgm_configured": False,
            "no_tts": False,
        },
        "compose_input": {"mode": "direct", "ready": True, "blocked": False},
    }
    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "subtitle_artifact_exists": True,
            "target_subtitle_authoritative_source": True,
            "edited_text": "1\n00:00:00,000 --> 00:00:01,000\nđây là cô gái\n",
            "srt_text": "1\n00:00:00,000 --> 00:00:01,000\nđây là cô gái\n",
            "dub_input_text": "đây là cô gái",
        },
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        artifact_facts=artifact_facts,
        no_dub=False,
    )

    operator_summary = build_hot_follow_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
        subtitle_ready=True,
    )

    assert current_attempt["helper_translate_status"] == "helper_resolved_with_retryable_provider_warning"
    assert current_attempt["helper_translate_output_state"] == "helper_output_resolved"
    assert current_attempt["helper_translate_provider_health"] == "provider_retryable_failure"
    assert current_attempt["helper_translate_composite_state"] == "helper_resolved_with_retryable_provider_warning"
    assert current_attempt["helper_translate_warning_only"] is True
    assert current_attempt["helper_translate_failed"] is False
    assert current_attempt["helper_translate_failed_voice_led"] is False
    assert operator_summary["current_attempt_failed"] is False
    assert "翻译助手" not in operator_summary["recommended_next_action"]
