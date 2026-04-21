from __future__ import annotations

from typing import Any

from gateway.app.services.hot_follow_language_profiles import hot_follow_subtitle_filename


def run(
    payload: dict[str, Any],
    *,
    defaults: dict[str, Any] | None = None,
    stage_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    _ = defaults, stage_results
    current_attempt = dict(payload.get("current_attempt") or {})
    operator_summary = dict(payload.get("operator_summary") or {})
    task = dict(payload.get("task") or {})

    target_lang = task.get("target_lang") or task.get("content_lang") or "mm"
    expected_subtitle_source = hot_follow_subtitle_filename(target_lang)

    subtitle_ready = current_attempt.get("subtitle_ready") if "subtitle_ready" in current_attempt else None
    audio_ready = bool(current_attempt.get("audio_ready"))
    compose_status = str(current_attempt.get("compose_status") or "").strip().lower()
    compose_ready = compose_status == "done"
    final_exists = bool(operator_summary.get("last_successful_output_available"))
    publish_ready = bool(operator_summary.get("publish_ready"))
    blocking = list(current_attempt.get("blocking") or [])
    return {
        "task_id": str(task.get("task_id") or task.get("id") or "").strip() or None,
        "target_lang": str(target_lang).strip().lower() or "mm",
        "expected_subtitle_source": expected_subtitle_source,
        "subtitle_ready": subtitle_ready,
        "subtitle_ready_reason": str(current_attempt.get("subtitle_ready_reason") or "").strip() or None,
        "audio_ready": audio_ready,
        "audio_ready_reason": str(current_attempt.get("audio_ready_reason") or "").strip() or None,
        "compose_ready": compose_ready,
        "compose_allowed": bool(current_attempt.get("compose_allowed")),
        "compose_route_allowed": bool(current_attempt.get("compose_route_allowed")),
        "compose_input_ready": bool(current_attempt.get("compose_input_ready")),
        "compose_execute_allowed": bool(current_attempt.get("compose_execute_allowed")),
        "compose_input_mode": str(current_attempt.get("compose_input_mode") or "").strip() or None,
        "compose_input_reason": str(current_attempt.get("compose_input_reason") or "").strip() or None,
        "publish_ready": publish_ready,
        "blocking": blocking,
        "compose_blocked": bool(current_attempt.get("compose_blocked_terminal")),
        "compose_blocked_reason": str(current_attempt.get("compose_reason") or "").strip() or None,
        "compose_input_derive_failed_terminal": bool(current_attempt.get("compose_input_derive_failed_terminal")),
        "compose_input_blocked_terminal": bool(current_attempt.get("compose_input_blocked_terminal")),
        "compose_exec_failed_terminal": bool(current_attempt.get("compose_exec_failed_terminal")),
        "no_dub_compose_allowed": bool(current_attempt.get("no_dub_compose_allowed")),
        "no_tts_compose_allowed": bool(current_attempt.get("no_tts_compose_allowed")),
        "no_dub_reason": str(current_attempt.get("no_dub_reason") or "").strip() or None,
        "no_dub_route_terminal": bool(current_attempt.get("no_dub_route_terminal")),
        "helper_translate_failed": bool(current_attempt.get("helper_translate_failed")),
        "helper_translate_failed_voice_led": bool(current_attempt.get("helper_translate_failed_voice_led")),
        "helper_translate_error_reason": str(current_attempt.get("helper_translate_error_reason") or "").strip() or None,
        "helper_translate_error_message": str(current_attempt.get("helper_translate_error_message") or "").strip() or None,
        "selected_compose_route": str(current_attempt.get("selected_compose_route") or "").strip() or None,
        "subtitle_terminal_state": str(current_attempt.get("subtitle_terminal_state") or "").strip() or None,
        "final_exists": final_exists,
        "subtitle_exists": bool(current_attempt.get("subtitle_exists")),
        "audio_exists": bool(current_attempt.get("audio_exists")),
        "requires_recompose": bool(current_attempt.get("requires_recompose")),
        "requires_redub": bool(current_attempt.get("requires_redub")),
        "compose_status": compose_status or None,
        "final_stale_reason": str(current_attempt.get("final_stale_reason") or "").strip() or None,
        "current_subtitle_source": str(current_attempt.get("current_subtitle_source") or "").strip() or None,
        "last_successful_output_available": operator_summary.get("last_successful_output_available"),
    }
