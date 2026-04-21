from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")


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
