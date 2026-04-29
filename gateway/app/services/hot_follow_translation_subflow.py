from __future__ import annotations

from typing import Any


WAITING_TRANSLATION_SUBFLOW_STATES = {
    "translation_requested",
    "translation_inflight",
    "translation_output_pending_retryable",
    "translation_output_received_unmaterialized",
    "translation_materialization_failed_retryable",
    "target_subtitle_stale_after_edit",
}

TERMINAL_TRANSLATION_REASONS = {
    "helper_translate_terminal_failure",
    "helper_translate_unsupported_language",
    "helper_translate_input_invalid",
    "translation_materialization_failed_terminal",
}

MATERIALIZATION_FAILURE_REASONS = {
    "subtitle_missing",
    "target_subtitle_empty",
    "target_subtitle_source_mismatch",
    "target_subtitle_source_copy",
    "target_subtitle_not_authoritative",
}


def _d(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _s(value: Any) -> str:
    return str(value or "").strip()


def _n(value: Any) -> str:
    return _s(value).lower()


def _truthy_text(*values: Any) -> bool:
    return any(bool(_s(value)) for value in values)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _n(value) in {"1", "true", "yes", "y", "on"}


def build_target_subtitle_translation_facts(
    *,
    task: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    subtitle_lane: dict[str, Any] | None = None,
    artifact_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = task or {}
    state = state or {}
    subtitles = subtitle_lane or _d(state.get("subtitles"))
    artifacts = artifact_facts or _d(state.get("artifact_facts"))
    existing = _d(artifacts.get("target_subtitle_translation_facts"))

    origin_key = _s(
        subtitles.get("origin_subtitle_key")
        or subtitles.get("origin_srt_path")
        or task.get("origin_srt_path")
        or task.get("origin_subtitle_key")
    ) or None
    origin_text_present = _truthy_text(
        subtitles.get("parse_source_text"),
        subtitles.get("raw_source_text"),
        subtitles.get("normalized_source_text"),
    )
    helper_status = _s(
        subtitles.get("helper_translate_status")
        or artifacts.get("helper_translate_status")
        or task.get("subtitle_helper_status")
    )
    helper_output_state = _s(
        subtitles.get("helper_translate_output_state")
        or artifacts.get("helper_translate_output_state")
    )
    helper_provider_health = _s(
        subtitles.get("helper_translate_provider_health")
        or artifacts.get("helper_translate_provider_health")
    )
    helper_error_reason = _s(
        subtitles.get("helper_translate_error_reason")
        or artifacts.get("helper_translate_error_reason")
        or task.get("subtitle_helper_error_reason")
    ) or None
    helper_translated_text = _s(
        subtitles.get("helper_translate_translated_text")
        or task.get("subtitle_helper_translated_text")
    ) or None
    if not helper_provider_health and (subtitles.get("helper_translate_failed") or artifacts.get("helper_translate_failed") or helper_error_reason):
        helper_provider_health = (
            "provider_terminal_failure"
            if _n(helper_error_reason) in TERMINAL_TRANSLATION_REASONS
            else "provider_retryable_failure"
        )
    target_materialized = bool(
        _bool(subtitles.get("subtitle_artifact_exists"))
        or _bool(artifacts.get("subtitle_exists"))
        or _bool(artifacts.get("target_subtitle_artifact_exists"))
    )
    subtitle_ready = _bool(subtitles.get("subtitle_ready"))
    target_current = (
        _bool(subtitles.get("target_subtitle_current"))
        if subtitles.get("target_subtitle_current") is not None
        else bool(subtitle_ready)
    )
    target_authoritative = (
        _bool(subtitles.get("target_subtitle_authoritative_source"))
        if subtitles.get("target_subtitle_authoritative_source") is not None
        else bool(subtitle_ready and target_materialized)
    )
    target_reason = _s(
        subtitles.get("target_subtitle_current_reason")
        or subtitles.get("subtitle_ready_reason")
        or task.get("target_subtitle_current_reason")
    ) or None
    manual_override_present = _truthy_text(
        subtitles.get("manual_override_updated_at"),
        subtitles.get("subtitles_override_updated_at"),
        task.get("subtitles_override_updated_at"),
        task.get("subtitles_content_hash"),
    )

    helper_requested = bool(
        helper_status
        or helper_output_state
        or helper_error_reason
        or _s(subtitles.get("helper_translate_input_text") or task.get("subtitle_helper_input_text"))
    )
    helper_raw_output_received = bool(
        helper_output_state == "helper_output_resolved"
        or helper_status in {"ready", "resolved", "helper_output_resolved"}
        or helper_translated_text
    )

    facts = {
        "origin_subtitle_exists": bool(origin_key or origin_text_present),
        "origin_subtitle_key": origin_key,
        "origin_subtitle_text_present": bool(origin_text_present),
        "helper_translation_requested": helper_requested,
        "helper_translation_status": helper_status or None,
        "helper_raw_output_received": helper_raw_output_received,
        "helper_output_state": helper_output_state or None,
        "helper_provider_health": helper_provider_health or None,
        "helper_error_reason": helper_error_reason,
        "helper_error_message": _s(subtitles.get("helper_translate_error_message") or artifacts.get("helper_translate_error_message")) or None,
        "helper_input_text": _s(subtitles.get("helper_translate_input_text") or task.get("subtitle_helper_input_text")) or None,
        "helper_translated_text": helper_translated_text,
        "helper_target_lang": _s(subtitles.get("helper_translate_target_lang") or task.get("subtitle_helper_target_lang")) or None,
        "helper_requested_at": _s(task.get("subtitle_helper_requested_at")) or None,
        "helper_responded_at": _s(task.get("subtitle_helper_updated_at")) or None,
        "helper_failed_at": _s(task.get("subtitle_helper_failed_at")) or None,
        "retry_count": int(task.get("subtitle_helper_retry_count") or task.get("subtitle_retry_count") or 0),
        "target_subtitle_artifact_exists": target_materialized,
        "target_subtitle_materialized": target_materialized,
        "target_subtitle_current": target_current,
        "target_subtitle_authoritative_source": target_authoritative,
        "target_subtitle_current_reason": target_reason,
        "manual_override_present": bool(manual_override_present),
        "manual_override_updated_at": _s(subtitles.get("manual_override_updated_at") or task.get("subtitles_override_updated_at")) or None,
    }
    for key, value in existing.items():
        if value is not None and value != "":
            facts[key] = value
    return facts


def reduce_target_subtitle_translation_subflow(
    *,
    facts: dict[str, Any],
    lane_state: str,
) -> dict[str, Any]:
    lane = _s(lane_state) or "voice_led_tts_route"
    if lane != "voice_led_tts_route":
        state = "translation_not_required_for_route"
        reason = "translation_not_required_for_route"
    elif facts.get("target_subtitle_current") and facts.get("target_subtitle_authoritative_source"):
        state = "manual_target_subtitle_override_current" if facts.get("manual_override_present") else "target_subtitle_authoritative_current"
        reason = "ready"
    elif not facts.get("origin_subtitle_exists"):
        state = "translation_not_started"
        reason = "origin_subtitle_missing"
    else:
        helper_status = _n(facts.get("helper_translation_status"))
        helper_output = _n(facts.get("helper_output_state"))
        provider_health = _n(facts.get("helper_provider_health"))
        error_reason = _n(facts.get("helper_error_reason"))
        target_reason = _n(facts.get("target_subtitle_current_reason"))
        terminal = bool(
            provider_health == "provider_terminal_failure"
            or helper_status in {"helper_terminal_failure", "translation_materialization_failed_terminal"}
            or error_reason in TERMINAL_TRANSLATION_REASONS
            or target_reason in TERMINAL_TRANSLATION_REASONS
        )
        if terminal:
            state = "translation_materialization_failed_terminal"
            reason = error_reason or target_reason or "translation_materialization_failed_terminal"
        elif facts.get("helper_raw_output_received") and not facts.get("target_subtitle_materialized"):
            state = "translation_output_received_unmaterialized"
            reason = "translation_output_unmaterialized"
        elif facts.get("helper_raw_output_received") and not (
            facts.get("target_subtitle_current") and facts.get("target_subtitle_authoritative_source")
        ):
            state = "translation_materialization_failed_retryable"
            reason = target_reason or "translation_materialization_failed_retryable"
        elif target_reason in MATERIALIZATION_FAILURE_REASONS and helper_status in {"failed", "helper_retryable_failure"}:
            state = "translation_materialization_failed_retryable"
            reason = error_reason or target_reason
        elif helper_output == "helper_output_pending":
            state = "translation_output_pending_retryable"
            reason = "helper_output_pending"
        elif helper_status in {"queued", "pending", "helper_pending"}:
            state = "translation_requested"
            reason = "helper_translate_requested"
        elif helper_status in {"running", "processing"}:
            state = "translation_inflight"
            reason = "helper_translate_inflight"
        elif provider_health == "provider_retryable_failure" or helper_status in {"failed", "helper_retryable_failure"}:
            state = "translation_output_pending_retryable"
            reason = error_reason or "helper_translate_retryable_failure"
        elif target_reason in {"target_subtitle_stale_after_edit", "subtitle_stale_after_edit"}:
            state = "target_subtitle_stale_after_edit"
            reason = target_reason
        elif facts.get("helper_translation_requested"):
            state = "translation_requested"
            reason = "helper_translate_requested"
        else:
            state = "translation_not_started"
            reason = "helper_translate_not_started"

    waiting = state in WAITING_TRANSLATION_SUBFLOW_STATES
    retryable = waiting and state != "target_subtitle_stale_after_edit"
    terminal = state == "translation_materialization_failed_terminal"
    authoritative_current = state in {
        "target_subtitle_authoritative_current",
        "manual_target_subtitle_override_current",
    }
    blocking_reason = (
        None
        if authoritative_current or state == "translation_not_required_for_route"
        else (
            "translation_materialization_failed_terminal"
            if terminal
            else (
                "translation_output_unmaterialized"
                if state == "translation_output_received_unmaterialized"
                else (
                    "translation_materialization_failed_retryable"
                    if state == "translation_materialization_failed_retryable"
                    else "waiting_for_target_subtitle_translation"
                )
            )
        )
    )
    operator_action = {
        "translation_requested": "wait_for_provider_or_retry",
        "translation_inflight": "wait_for_provider_or_retry",
        "translation_output_pending_retryable": "wait_for_provider_or_retry",
        "translation_output_received_unmaterialized": "retry_materialization_or_save_manual_target_subtitle",
        "translation_materialization_failed_retryable": "retry_materialization_or_save_manual_target_subtitle",
        "translation_materialization_failed_terminal": "manual_target_subtitle_required",
        "target_subtitle_stale_after_edit": "retry_translation_or_save_manual_target_subtitle",
        "translation_not_started": "request_translation_or_save_manual_target_subtitle",
        "translation_not_required_for_route": "none",
        "target_subtitle_authoritative_current": "none",
        "manual_target_subtitle_override_current": "none",
    }.get(state, "request_translation_or_save_manual_target_subtitle")

    return {
        "version": "hot_follow_target_subtitle_translation_subflow_v1",
        "state": state,
        "reason": reason,
        "facts": facts,
        "waiting": bool(waiting),
        "retryable": bool(retryable),
        "terminal": bool(terminal),
        "authoritative_current": bool(authoritative_current),
        "materialized": bool(facts.get("target_subtitle_materialized")),
        "manual_override_current": state == "manual_target_subtitle_override_current",
        "blocking_reason": blocking_reason,
        "operator_action": operator_action,
    }
