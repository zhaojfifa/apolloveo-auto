from __future__ import annotations

from typing import Any


NO_TTS_ROUTES = {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"}
STALE_NO_DUB_REASONS = {"target_subtitle_empty", "dub_input_empty"}
WAITING_SUBTITLE_REASONS = {
    "target_subtitle_translation_incomplete",
    "waiting_for_target_subtitle_translation",
    "helper_output_pending",
    "helper_translate_pending",
}
TTS_FAILURE_REASONS = {
    "empty_or_invalid_audio",
    "tts_failed",
    "tts_failed:empty_or_invalid_audio",
    "tts_failed_timeout",
    "tts_failed_cancelled",
}


def _d(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _s(value: Any) -> str:
    return str(value or "").strip()


def _n(value: Any) -> str:
    return _s(value).lower()


def _truthy_text(*values: Any) -> bool:
    return any(bool(_s(value)) for value in values)


def _is_tts_failure(value: Any) -> bool:
    reason = _n(value)
    return bool(
        reason in TTS_FAILURE_REASONS
        or reason.startswith("tts_failed")
        or reason.startswith("tts_")
        or "empty_or_invalid_audio" in reason
    )


def _compose_input_state(artifact_facts: dict[str, Any]) -> tuple[dict[str, Any], bool, bool, bool, str]:
    compose_input = _d(artifact_facts.get("compose_input"))
    mode = _n(compose_input.get("mode") or artifact_facts.get("compose_input_mode"))
    ready = bool(
        compose_input.get("ready")
        or artifact_facts.get("compose_input_ready")
        or mode in {"direct", "derived_ready"}
    )
    blocked = bool(compose_input.get("blocked") or artifact_facts.get("compose_input_blocked") or mode == "blocked")
    derive_failed = bool(
        compose_input.get("derive_failed")
        or artifact_facts.get("compose_input_derive_failed")
        or mode == "derive_failed"
    )
    reason = _s(
        compose_input.get("failure_code")
        or artifact_facts.get("compose_input_failure_code")
        or compose_input.get("reason")
        or artifact_facts.get("compose_input_reason")
        or mode
        or "compose_input_not_ready"
    )
    return compose_input, ready, blocked, derive_failed, reason


def reduce_hot_follow_process_state(
    *,
    task: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    voice_state: dict[str, Any] | None = None,
    subtitle_lane: dict[str, Any] | None = None,
    artifact_facts: dict[str, Any] | None = None,
    dub_status: str | None = None,
    compose_status: str | None = None,
    composed_reason: str | None = None,
    final_stale_reason: str | None = None,
    no_dub: bool | None = None,
    no_dub_compose_allowed: bool | None = None,
) -> dict[str, Any]:
    task = task or {}
    state = state or {}
    artifacts = artifact_facts or _d(state.get("artifact_facts"))
    audio_lane = _d(artifacts.get("audio_lane"))
    subtitles = subtitle_lane or _d(state.get("subtitles"))
    audio = voice_state or _d(state.get("audio"))
    final = _d(state.get("final"))
    historical_final = _d(state.get("historical_final"))
    selected = _d(artifacts.get("selected_compose_route"))

    subtitle_ready = bool(subtitles.get("subtitle_ready"))
    target_current_hint = subtitles.get("target_subtitle_current")
    target_authoritative_hint = subtitles.get("target_subtitle_authoritative_source")
    target_current = bool(subtitle_ready if target_current_hint is None else target_current_hint)
    target_authoritative = bool(
        (subtitle_ready and subtitles.get("subtitle_artifact_exists"))
        if target_authoritative_hint is None
        else target_authoritative_hint
    )
    target_ready = bool(subtitle_ready and target_current and target_authoritative)
    source_available = _truthy_text(
        subtitles.get("parse_source_text"),
        subtitles.get("raw_source_text"),
        subtitles.get("normalized_source_text"),
    )
    visible_target_pending = bool(
        not target_ready
        and _truthy_text(
            subtitles.get("primary_editable_text"),
            subtitles.get("edited_text"),
            subtitles.get("srt_text"),
        )
    )
    target_reason = _s(
        subtitles.get("target_subtitle_current_reason")
        or subtitles.get("subtitle_ready_reason")
    )
    helper_output = _s(subtitles.get("helper_translate_output_state") or artifacts.get("helper_translate_output_state"))
    helper_status = _s(subtitles.get("helper_translate_status") or artifacts.get("helper_translate_status"))
    helper_pending = helper_output == "helper_output_pending" or helper_status == "helper_output_pending"
    translation_waiting = bool(
        not target_ready
        and (
            target_reason in WAITING_SUBTITLE_REASONS
            or helper_pending
        )
        and source_available
    )

    audio_ready = bool(audio.get("audio_ready"))
    voiceover_exists = bool(
        audio.get("voiceover_url")
        or audio.get("tts_voiceover_url")
        or audio.get("dub_preview_url")
        or audio_lane.get("tts_voiceover_exists")
    )
    source_audio_preserved = bool(audio_lane.get("source_audio_preserved"))
    bgm_configured = bool(audio_lane.get("bgm_configured"))
    no_tts_audio_lane = bool(audio_lane.get("no_tts"))
    no_dub_reason = _n(audio.get("no_dub_reason") or task.get("dub_skip_reason"))
    explicit_no_dub = bool(audio.get("no_dub")) if no_dub is None else bool(no_dub)
    explicit_no_dub_allowed = (
        bool(audio.get("no_dub_compose_allowed"))
        if no_dub_compose_allowed is None
        else bool(no_dub_compose_allowed)
    )
    if no_dub_reason in STALE_NO_DUB_REASONS and (target_ready or visible_target_pending or translation_waiting):
        explicit_no_dub = False
        explicit_no_dub_allowed = False
        no_dub_reason = ""

    route = _s(selected.get("name"))
    lane = "voice_led_tts_route"
    if audio_ready or voiceover_exists or translation_waiting or visible_target_pending:
        route = "tts_replace_route"
        lane = "voice_led_tts_route"
    elif explicit_no_dub_allowed and _s(selected.get("name")) in NO_TTS_ROUTES:
        route = _s(selected.get("name"))
        lane = "voice_led_plus_preserved_source_audio_route" if route == "preserve_source_route" else "no_dub_no_tts_route"
    elif source_audio_preserved and target_reason == "preserve_source_route_no_target_subtitle_required":
        route = "preserve_source_route"
        lane = "voice_led_plus_preserved_source_audio_route"
    elif source_audio_preserved and not voiceover_exists:
        route = "preserve_source_route"
        lane = "voice_led_plus_preserved_source_audio_route"
    elif bgm_configured and no_tts_audio_lane and not voiceover_exists:
        route = "bgm_only_route"
        lane = "no_dub_no_tts_route"
    elif target_ready or subtitle_ready:
        route = "tts_replace_route"
        lane = "voice_led_tts_route"
    elif explicit_no_dub or explicit_no_dub_allowed:
        if source_audio_preserved:
            route = "preserve_source_route"
            lane = "voice_led_plus_preserved_source_audio_route"
        elif bgm_configured:
            route = "bgm_only_route"
            lane = "no_dub_no_tts_route"
        else:
            route = "no_tts_compose_route"
            lane = "no_dub_no_tts_route"
    elif no_tts_audio_lane and not source_available and not target_ready:
        route = "no_tts_compose_route"
        lane = "no_dub_no_tts_route"
    elif not route:
        route = "tts_replace_route"

    subtitle_required = lane == "voice_led_tts_route"
    no_dub_route_terminal = bool(lane in {"no_dub_no_tts_route", "voice_led_plus_preserved_source_audio_route"})
    if subtitle_required:
        if target_ready:
            subtitle_state = "target_subtitle_authoritative_current"
        elif translation_waiting:
            subtitle_state = "target_subtitle_translation_waiting_retryable"
        elif source_available:
            subtitle_state = "subtitle_source_available"
        else:
            subtitle_state = "subtitle_source_missing"
    else:
        subtitle_state = "subtitle_skipped_terminal" if no_dub_route_terminal else "subtitle_not_required_for_route"

    route_allowed = False
    route_reason = "route_not_allowed"
    if route == "tts_replace_route":
        route_allowed = bool(audio_ready)
        route_reason = "ready" if route_allowed else _s(audio.get("audio_ready_reason") or "audio_not_ready")
    elif route == "preserve_source_route":
        route_allowed = source_audio_preserved
        route_reason = "ready" if route_allowed else "source_audio_not_preserved"
    elif route == "bgm_only_route":
        route_allowed = bgm_configured
        route_reason = "ready" if route_allowed else "bgm_missing"
    elif route == "no_tts_compose_route":
        route_allowed = bool(explicit_no_dub or explicit_no_dub_allowed or no_tts_audio_lane)
        route_reason = "ready" if route_allowed else "no_tts_not_selected"

    dub_status_norm = _n(dub_status if dub_status is not None else audio.get("status") or task.get("dub_status")) or "absent"
    if no_dub_route_terminal:
        dub_state = "dub_not_required_for_route"
        dub_step_status = "skipped"
    elif not target_ready:
        dub_state = "dub_waiting_for_target_subtitle"
        dub_step_status = "pending"
    elif audio_ready and bool(audio.get("dub_current", audio_ready)):
        dub_state = "dub_ready_current"
        dub_step_status = "done"
    elif _n(audio.get("dub_current_reason") or audio.get("audio_ready_reason")) in {
        "dub_stale_after_subtitles",
        "dub_stale_after_speed_change",
    }:
        dub_state = "dub_stale_after_subtitle_change"
        dub_step_status = "pending"
    elif dub_status_norm in {"failed", "error"} or _is_tts_failure(audio.get("audio_ready_reason")):
        dub_state = "dub_retryable_failure"
        dub_step_status = "failed"
    else:
        dub_state = "dub_waiting_for_target_subtitle" if not target_ready else "dub_retryable_failure"
        dub_step_status = "pending"

    compose_input, compose_input_ready, compose_blocked, compose_derive_failed, compose_input_reason = _compose_input_state(artifacts)
    compose_status_norm = _n(compose_status if compose_status is not None else task.get("compose_status")) or "never"
    compose_reason_norm = _n(composed_reason) or "unknown"
    final_exists = bool(artifacts.get("final_exists") or final.get("exists") or historical_final.get("exists"))
    final_fresh = bool(final_stale_reason is None and final_exists and compose_reason_norm == "ready")
    if compose_blocked:
        compose_state = "compose_failed_terminal"
        compose_step_status = "blocked"
        compose_reason = compose_input_reason or "compose_input_blocked"
    elif compose_derive_failed:
        compose_state = "compose_failed_terminal"
        compose_step_status = "failed"
        compose_reason = compose_input_reason or "compose_input_derive_failed"
    elif compose_status_norm in {"running", "processing"}:
        compose_state = "compose_running"
        compose_step_status = "running"
        compose_reason = "compose_running"
    elif subtitle_required and subtitle_state != "target_subtitle_authoritative_current":
        compose_state = "compose_not_allowed_waiting_subtitle"
        compose_step_status = "pending"
        compose_reason = "waiting_for_target_subtitle_translation" if translation_waiting else "subtitle_not_ready"
    elif route == "tts_replace_route" and not audio_ready:
        compose_state = "compose_not_allowed_waiting_audio"
        compose_step_status = "pending"
        compose_reason = _s(audio.get("audio_ready_reason") or "audio_not_ready")
    elif final_fresh:
        compose_state = "compose_done"
        compose_step_status = "done"
        compose_reason = "ready"
    elif route_allowed and compose_input_ready:
        compose_state = "compose_allowed_ready"
        compose_step_status = "pending"
        compose_reason = "ready"
    elif compose_status_norm in {"failed", "error"}:
        compose_state = "compose_failed_retryable"
        compose_step_status = "failed"
        compose_reason = _s(composed_reason or "compose_exec_failed")
    else:
        compose_state = "compose_not_allowed_waiting_audio" if route == "tts_replace_route" else "compose_allowed_ready"
        compose_step_status = "pending"
        compose_reason = route_reason

    compose_execute_allowed = bool(route_allowed and compose_input_ready)
    no_tts_allowed = bool(route in NO_TTS_ROUTES and route_allowed)
    tts_lane_expected = bool(route == "tts_replace_route" and target_ready and not explicit_no_dub)
    retriable_dub_failure = bool(dub_state == "dub_retryable_failure" and tts_lane_expected)
    subtitle_terminal_state = (
        "subtitle_translation_waiting_retryable"
        if subtitle_state == "target_subtitle_translation_waiting_retryable"
        else ("no_dub_route_terminal" if no_dub_route_terminal else None)
    )

    return {
        "version": "hot_follow_process_state_v1",
        "lane_state": lane,
        "selected_compose_route": route,
        "route_allowed": route_allowed,
        "route_allowed_reason": "ready" if route_allowed else route_reason,
        "no_dub": bool(no_dub_route_terminal),
        "no_dub_reason": (
            "source_audio_preserved_no_tts"
            if route == "preserve_source_route"
            else ("bgm_only_no_tts" if route == "bgm_only_route" else ("compose_no_tts" if route == "no_tts_compose_route" else None))
        ),
        "no_tts_compose_allowed": no_tts_allowed,
        "no_dub_compose_allowed": no_tts_allowed,
        "subtitle_required": subtitle_required,
        "subtitle_process_state": subtitle_state,
        "subtitle_step_status": (
            "done"
            if subtitle_state == "target_subtitle_authoritative_current"
            else ("skipped" if subtitle_state == "subtitle_skipped_terminal" else "pending")
        ),
        "subtitle_terminal_state": subtitle_terminal_state,
        "subtitle_translation_waiting_retryable": subtitle_state == "target_subtitle_translation_waiting_retryable",
        "target_subtitle_authoritative_current": target_ready,
        "dub_process_state": dub_state,
        "dub_step_status": dub_step_status,
        "audio_ready": audio_ready,
        "audio_ready_reason": _s(audio.get("audio_ready_reason") or ("ready" if audio_ready else "audio_not_ready")),
        "dub_current": bool(audio.get("dub_current")) if not no_dub_route_terminal else False,
        "dub_current_reason": _s(audio.get("dub_current_reason") or ("ready" if audio_ready else "audio_not_ready")),
        "tts_lane_expected": tts_lane_expected,
        "retriable_dub_failure": retriable_dub_failure,
        "current_attempt_failure_class": "retriable_dub_failure" if retriable_dub_failure else None,
        "compose_process_state": compose_state,
        "compose_step_status": compose_step_status,
        "compose_allowed": route_allowed,
        "compose_input_ready": compose_input_ready,
        "compose_execute_allowed": compose_execute_allowed,
        "compose_allowed_reason": "ready" if route_allowed else route_reason,
        "compose_reason": compose_reason,
        "compose_input": compose_input,
        "compose_input_mode": _n(compose_input.get("mode")),
        "compose_blocked_terminal": compose_blocked,
        "compose_input_derive_failed_terminal": compose_derive_failed,
        "compose_input_blocked_terminal": compose_blocked,
        "compose_exec_failed_terminal": compose_state == "compose_failed_retryable",
        "compose_terminal_state": (
            "compose_blocked_terminal"
            if compose_blocked
            else ("compose_input_derive_failed_terminal" if compose_derive_failed else ("compose_exec_failed_terminal" if compose_state == "compose_failed_retryable" else None))
        ),
        "requires_redub": bool(tts_lane_expected and not audio_ready),
        "requires_recompose": bool(compose_state == "compose_allowed_ready" and not no_dub_route_terminal),
    }
