from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")
_HELPER_TEMPORARY_REASONS = {
    "helper_translate_pending",
    "helper_translate_provider_exhausted",
    "helper_translate_failed",
}
_HELPER_TERMINAL_REASONS = {
    "helper_translate_terminal_failure",
    "helper_translate_unsupported_language",
    "helper_translate_input_invalid",
}
_HELPER_PENDING_STATES = {"queued", "running", "processing", "pending", "helper_pending"}
_HELPER_RESOLVED_STATES = {"ready", "resolved", "helper_resolved"}
_HELPER_RETRYABLE_FAILURE_STATES = {"failed", "helper_retryable_failure"}
_HELPER_TERMINAL_FAILURE_STATES = {"helper_terminal_failure"}
_HELPER_OUTPUT_PENDING = "helper_output_pending"
_HELPER_OUTPUT_RESOLVED = "helper_output_resolved"
_HELPER_OUTPUT_UNAVAILABLE = "helper_output_unavailable"
_HELPER_PROVIDER_OK = "provider_ok"
_HELPER_PROVIDER_RETRYABLE_FAILURE = "provider_retryable_failure"
_HELPER_PROVIDER_TERMINAL_FAILURE = "provider_terminal_failure"
_HELPER_RESOLVED_WITH_RETRYABLE_PROVIDER_WARNING = "helper_resolved_with_retryable_provider_warning"


def sanitize_helper_translate_error(exc: BaseException | str) -> dict[str, Any]:
    raw = str(exc or "").strip()
    lowered = raw.lower()
    provider = "gemini"
    exhausted = (
        "429" in lowered
        or "resource_exhausted" in lowered
        or "resource exhausted" in lowered
        or "quota" in lowered
        or "rate limit" in lowered
    )
    if exhausted:
        reason = "helper_translate_provider_exhausted"
        message = "翻译服务当前额度不足或请求过多，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。"
    else:
        reason = "helper_translate_failed"
        message = "翻译助手暂时失败，请稍后重试；也可以手动编辑目标字幕并保存后继续配音。"

    compact_raw = _WHITESPACE_RE.sub(" ", _JSON_OBJECT_RE.sub("", raw)).strip()
    debug_hint = compact_raw[:160] if compact_raw else None
    return {
        "reason": reason,
        "message": message,
        "provider": provider,
        "debug_hint": debug_hint,
    }


def helper_translate_failure_updates(
    error: dict[str, Any],
    *,
    input_text: str | None = None,
    target_lang: str | None = None,
) -> dict[str, Any]:
    updates = {
        "subtitle_helper_status": "failed",
        "subtitle_helper_error_reason": error.get("reason") or "helper_translate_failed",
        "subtitle_helper_error_message": error.get("message") or "翻译助手暂时失败，请稍后重试。",
        "subtitle_helper_provider": error.get("provider") or "gemini",
        "subtitle_helper_failed_at": datetime.now(timezone.utc).isoformat(),
    }
    if input_text is not None:
        updates["subtitle_helper_input_text"] = str(input_text or "")
    if target_lang is not None:
        updates["subtitle_helper_target_lang"] = str(target_lang or "")
    return updates


def helper_translate_success_updates(
    *,
    input_text: str | None = None,
    translated_text: str | None = None,
    target_lang: str | None = None,
) -> dict[str, Any]:
    return {
        "subtitle_helper_status": "ready",
        "subtitle_helper_error_reason": None,
        "subtitle_helper_error_message": None,
        "subtitle_helper_provider": "gemini",
        "subtitle_helper_input_text": str(input_text or ""),
        "subtitle_helper_translated_text": str(translated_text or ""),
        "subtitle_helper_target_lang": str(target_lang or ""),
        "subtitle_helper_updated_at": datetime.now(timezone.utc).isoformat(),
    }


def helper_translate_resolved_updates() -> dict[str, Any]:
    return {
        "subtitle_helper_status": "resolved",
        "subtitle_helper_error_reason": None,
        "subtitle_helper_error_message": None,
    }


def helper_translate_lane_state(
    task: dict[str, Any],
    *,
    translation_waiting: bool,
    helper_source_text: str | None = None,
    helper_output_consumed: bool = False,
) -> dict[str, Any]:
    status = str(task.get("subtitle_helper_status") or "").strip().lower()
    reason = str(task.get("subtitle_helper_error_reason") or "").strip() or None
    message = str(task.get("subtitle_helper_error_message") or "").strip() or None
    provider = str(task.get("subtitle_helper_provider") or "").strip() or None
    has_source = bool(str(helper_source_text or "").strip())
    input_text = str(task.get("subtitle_helper_input_text") or "").strip() or None
    translated_text = str(task.get("subtitle_helper_translated_text") or "").strip() or None
    has_execution_evidence = bool(
        provider
        or input_text
        or translated_text
        or str(task.get("subtitle_helper_requested_at") or "").strip()
        or str(task.get("subtitle_helper_updated_at") or "").strip()
        or str(task.get("subtitle_helper_failed_at") or "").strip()
        or str(task.get("translation_execution_ref") or "").strip()
        or str(task.get("helper_requested_at") or "").strip()
        or str(task.get("last_polled_at") or "").strip()
        or str(task.get("helper_responded_at") or "").strip()
    )

    if status in _HELPER_TERMINAL_FAILURE_STATES or (
        status in _HELPER_RETRYABLE_FAILURE_STATES and reason in _HELPER_TERMINAL_REASONS
    ):
        provider_health = _HELPER_PROVIDER_TERMINAL_FAILURE
    elif status in _HELPER_RETRYABLE_FAILURE_STATES or reason in _HELPER_TEMPORARY_REASONS:
        provider_health = _HELPER_PROVIDER_RETRYABLE_FAILURE
    else:
        provider_health = _HELPER_PROVIDER_OK

    if status in _HELPER_RESOLVED_STATES or translated_text or helper_output_consumed:
        output_state = _HELPER_OUTPUT_RESOLVED
    elif provider_health != _HELPER_PROVIDER_OK:
        output_state = _HELPER_OUTPUT_UNAVAILABLE
    elif (status in _HELPER_PENDING_STATES or (translation_waiting and has_source)) and has_execution_evidence:
        output_state = _HELPER_OUTPUT_PENDING
    else:
        output_state = _HELPER_OUTPUT_UNAVAILABLE

    if output_state == _HELPER_OUTPUT_PENDING:
        reason = reason or "helper_translate_pending"
        message = message or "字幕翻译尚未就绪，正在等待翻译结果或可重试处理。"

    composite_state = None
    if output_state == _HELPER_OUTPUT_RESOLVED and provider_health == _HELPER_PROVIDER_RETRYABLE_FAILURE:
        composite_state = _HELPER_RESOLVED_WITH_RETRYABLE_PROVIDER_WARNING

    if composite_state:
        status = composite_state
        visibility = "warning_history_only"
        failed = False
    elif output_state == _HELPER_OUTPUT_RESOLVED:
        status = _HELPER_OUTPUT_RESOLVED
        visibility = "resolved"
        failed = False
    elif output_state == _HELPER_OUTPUT_PENDING:
        status = _HELPER_OUTPUT_PENDING
        visibility = "pending_provider_work"
        failed = False
    else:
        status = _HELPER_OUTPUT_UNAVAILABLE
        visibility = (
            "terminal_provider_failure"
            if provider_health == _HELPER_PROVIDER_TERMINAL_FAILURE
            else ("temporary_provider_issue" if provider_health == _HELPER_PROVIDER_RETRYABLE_FAILURE else "no_helper_used")
        )
        failed = provider_health in {
            _HELPER_PROVIDER_RETRYABLE_FAILURE,
            _HELPER_PROVIDER_TERMINAL_FAILURE,
        }
        if provider_health == _HELPER_PROVIDER_OK:
            reason = None
            message = None

    return {
        "status": status,
        "output_state": output_state,
        "provider_health": provider_health,
        "composite_state": composite_state,
        "failed": failed,
        "reason": reason,
        "message": message,
        "provider": provider,
        "visibility": visibility,
        "retryable": output_state == _HELPER_OUTPUT_PENDING or provider_health == _HELPER_PROVIDER_RETRYABLE_FAILURE,
        "terminal": provider_health == _HELPER_PROVIDER_TERMINAL_FAILURE,
        "warning_only": bool(composite_state),
        "input_text": input_text,
        "translated_text": translated_text,
        "target_lang": str(task.get("subtitle_helper_target_lang") or "").strip() or None,
    }
