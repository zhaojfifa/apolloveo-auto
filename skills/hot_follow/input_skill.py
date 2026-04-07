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
    ready_gate = dict(payload.get("ready_gate") or {})
    artifact_facts = dict(payload.get("artifact_facts") or {})
    current_attempt = dict(payload.get("current_attempt") or {})
    operator_summary = dict(payload.get("operator_summary") or {})
    task = dict(payload.get("task") or {})

    target_lang = task.get("target_lang") or task.get("content_lang") or "mm"
    expected_subtitle_source = hot_follow_subtitle_filename(target_lang)

    subtitle_ready = bool(ready_gate.get("subtitle_ready"))
    audio_ready = bool(current_attempt.get("audio_ready") or ready_gate.get("audio_ready"))
    compose_ready = bool(ready_gate.get("compose_ready"))
    publish_ready = bool(ready_gate.get("publish_ready"))
    blocking = list(ready_gate.get("blocking") or [])
    return {
        "task_id": str(task.get("task_id") or task.get("id") or "").strip() or None,
        "target_lang": str(target_lang).strip().lower() or "mm",
        "expected_subtitle_source": expected_subtitle_source,
        "subtitle_ready": subtitle_ready,
        "subtitle_ready_reason": str(ready_gate.get("subtitle_ready_reason") or "").strip() or None,
        "audio_ready": audio_ready,
        "audio_ready_reason": str(
            current_attempt.get("audio_ready_reason") or ready_gate.get("audio_ready_reason") or ""
        ).strip()
        or None,
        "compose_ready": compose_ready,
        "publish_ready": publish_ready,
        "blocking": blocking,
        "final_exists": bool(artifact_facts.get("final_exists")),
        "subtitle_exists": bool(artifact_facts.get("subtitle_exists")),
        "audio_exists": bool(artifact_facts.get("audio_exists")),
        "requires_recompose": bool(current_attempt.get("requires_recompose")),
        "compose_status": str(current_attempt.get("compose_status") or "").strip().lower() or None,
        "final_stale_reason": str(current_attempt.get("final_stale_reason") or "").strip() or None,
        "current_subtitle_source": str(current_attempt.get("current_subtitle_source") or "").strip() or None,
        "last_successful_output_available": operator_summary.get("last_successful_output_available"),
    }
