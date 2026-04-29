from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from fastapi import HTTPException

from gateway.app.providers.gemini_subtitles import GeminiSubtitlesError, translate_segments_with_gemini
from gateway.app.services.hot_follow_helper_translation import (
    helper_translate_failure_updates,
    helper_translate_success_updates,
    sanitize_helper_translate_error,
)
from gateway.app.services.hot_follow_language_profiles import hot_follow_internal_lang
from gateway.app.services.hot_follow_subtitle_authority import persist_hot_follow_authoritative_target_subtitle
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.subtitle_helpers import (
    hf_expected_subtitle_filename,
    hf_load_normalized_source_text,
    hf_load_origin_subtitles_text,
    hf_subtitle_content_hash,
    hf_subtitles_override_path,
    hf_sync_saved_target_subtitle_artifact,
)
from gateway.app.steps.subtitles import _parse_srt_to_segments, segments_to_srt
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage


@dataclass(frozen=True)
class TargetSubtitleTranslationExecutionResult:
    translated_text: str
    saved_task: dict[str, Any]
    execution_ref: str
    retry_count: int
    materialized: bool


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _retry_count(task: dict[str, Any], *, retry: bool) -> int:
    current = int(task.get("subtitle_translation_retry_count") or task.get("subtitle_helper_retry_count") or 0)
    return current + 1 if retry or task.get("subtitle_translation_requested_at") else current


def _source_subtitle_text(task_id: str, task: dict[str, Any]) -> str:
    normalized_source_text = hf_load_normalized_source_text(task_id, task).strip()
    origin_source_text = hf_load_origin_subtitles_text(task).strip()
    return normalized_source_text if "-->" in normalized_source_text else origin_source_text


def _dispatch_updates(
    *,
    task: dict[str, Any],
    source_text: str,
    target_lang: str,
    retry: bool,
    now_fn: Callable[[], str],
) -> tuple[str, int, dict[str, Any]]:
    execution_ref = str(uuid4())
    requested_at = now_fn()
    retry_count = _retry_count(task, retry=retry)
    return execution_ref, retry_count, {
        "subtitle_translation_execution_ref": execution_ref,
        "subtitle_translation_requested_at": requested_at,
        "subtitle_translation_last_polled_at": requested_at,
        "subtitle_translation_output_received_at": None,
        "subtitle_translation_materialized_at": None,
        "subtitle_translation_failed_at": None,
        "subtitle_translation_retry_count": retry_count,
        "subtitle_helper_status": "running",
        "subtitle_helper_error_reason": None,
        "subtitle_helper_error_message": None,
        "subtitle_helper_provider": "gemini",
        "subtitle_helper_input_text": source_text,
        "subtitle_helper_target_lang": target_lang,
        "subtitles_status": "running",
        "subtitles_error": None,
        "subtitles_error_reason": None,
        "target_subtitle_current": False,
        "target_subtitle_current_reason": "helper_translate_inflight",
    }


def _failure_updates(
    *,
    detail: dict[str, Any],
    source_text: str,
    target_lang: str,
    retry_count: int,
    now_fn: Callable[[], str],
) -> dict[str, Any]:
    failed_at = now_fn()
    updates = helper_translate_failure_updates(detail, input_text=source_text, target_lang=target_lang)
    updates.update(
        {
            "subtitle_translation_last_polled_at": failed_at,
            "subtitle_translation_failed_at": failed_at,
            "subtitle_translation_retry_count": retry_count,
            "subtitles_status": "failed",
            "subtitles_error": detail.get("message") or detail.get("reason") or "helper_translate_failed",
            "subtitles_error_reason": detail.get("reason") or "helper_translate_failed",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": detail.get("reason") or "helper_translate_failed",
            "compose_ready": False,
            "publish_ready": False,
            "error_message": detail.get("message") or detail.get("reason") or "helper_translate_failed",
            "error_reason": detail.get("reason") or "helper_translate_failed",
        }
    )
    return updates


def _current_target_recovery_updates(task: dict[str, Any]) -> dict[str, Any]:
    if not bool(task.get("target_subtitle_current")):
        return {}
    updates: dict[str, Any] = {
        "subtitles_status": "ready",
        "subtitles_error": None,
        "subtitles_error_reason": None,
        "target_subtitle_current": True,
        "target_subtitle_current_reason": str(task.get("target_subtitle_current_reason") or "ready"),
        "error_message": None,
        "error_reason": None,
    }
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    reason = str(pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or "").strip().lower()
    if reason in {"target_subtitle_empty", "dub_input_empty"}:
        pipeline_config.pop("no_dub", None)
        pipeline_config.pop("dub_skip_reason", None)
        updates["pipeline_config"] = pipeline_config_to_storage(pipeline_config)
        updates["dub_skip_reason"] = None
        if str(task.get("dub_status") or "").strip().lower() == "skipped":
            updates["dub_status"] = "pending"
    if task.get("publish_ready") is not None:
        updates["publish_ready"] = bool(task.get("publish_ready"))
    return updates


def _materialize_authoritative_target_subtitle(
    task_id: str,
    task: dict[str, Any],
    *,
    repo: Any,
    translated_text: str,
    target_lang: str,
    execution_ref: str,
    retry_count: int,
    now_fn: Callable[[], str],
) -> dict[str, Any]:
    materialized_at = now_fn()
    return persist_hot_follow_authoritative_target_subtitle(
        task_id,
        task,
        repo=repo,
        text=translated_text,
        text_mode="source_subtitle_lane_translation",
        target_lang=target_lang,
        source_texts=(
            hf_load_normalized_source_text(task_id, task),
            hf_load_origin_subtitles_text(task),
        ),
        expected_subtitle_source=hf_expected_subtitle_filename(target_lang),
        persist_artifact_fn=lambda saved_text: hf_sync_saved_target_subtitle_artifact(task_id, task, saved_text),
        write_override_fn=lambda saved_text: hf_subtitles_override_path(task_id).parent.mkdir(parents=True, exist_ok=True)
        or hf_subtitles_override_path(task_id).write_text(saved_text, encoding="utf-8"),
        content_hash_fn=hf_subtitle_content_hash,
        extra_updates={
            "subtitle_translation_execution_ref": execution_ref,
            "subtitle_translation_materialized_at": materialized_at,
            "subtitle_translation_retry_count": retry_count,
        },
        resolve_helper_state=True,
        now_fn=now_fn,
    )


def execute_target_subtitle_translation(
    task_id: str,
    task: dict[str, Any],
    *,
    repo: Any,
    target_lang: str,
    retry: bool = False,
    translate_segments_fn: Callable[..., dict[int, str]] = translate_segments_with_gemini,
    now_fn: Callable[[], str] = _now,
) -> TargetSubtitleTranslationExecutionResult:
    target_lang = hot_follow_internal_lang(target_lang)
    source_text = _source_subtitle_text(task_id, task)
    if not source_text:
        raise HTTPException(
            status_code=400,
            detail={"reason": "source_subtitle_lane_empty", "message": "来源字幕为空，无法执行完整字幕翻译。"},
        )
    if "-->" not in source_text:
        raise HTTPException(
            status_code=400,
            detail={"reason": "source_subtitle_lane_not_srt", "message": "来源字幕不是 SRT，无法保留时间轴执行完整字幕翻译。"},
        )
    segments = _parse_srt_to_segments(source_text)
    if not segments:
        raise HTTPException(
            status_code=400,
            detail={"reason": "source_subtitle_lane_invalid_srt", "message": "来源字幕 SRT 无法解析，未写入目标字幕。"},
        )

    execution_ref, retry_count, dispatch = _dispatch_updates(
        task=task,
        source_text=source_text,
        target_lang=target_lang,
        retry=retry,
        now_fn=now_fn,
    )
    running_task = policy_upsert(repo, task_id, task, dispatch, step="target_subtitle_translation")
    try:
        translations = translate_segments_fn(segments=segments, target_lang=target_lang)
    except GeminiSubtitlesError as exc:
        detail = sanitize_helper_translate_error(exc)
        policy_upsert(
            repo,
            task_id,
            running_task,
            {
                **_failure_updates(
                    detail=detail,
                    source_text=source_text,
                    target_lang=target_lang,
                    retry_count=retry_count,
                    now_fn=now_fn,
                ),
                **_current_target_recovery_updates(task),
            },
            step="target_subtitle_translation",
        )
        raise HTTPException(status_code=409, detail=detail) from exc

    output_received_at = now_fn()
    for seg in segments:
        idx = int(seg.get("index") or 0)
        seg[target_lang] = str(translations.get(idx) or seg.get("origin") or "").strip()
    translated_text = segments_to_srt(segments, target_lang)
    output_task = policy_upsert(
        repo,
        task_id,
        running_task,
        {
            **helper_translate_success_updates(
                input_text=source_text,
                translated_text=translated_text,
                target_lang=target_lang,
            ),
            "subtitle_translation_last_polled_at": output_received_at,
            "subtitle_translation_output_received_at": output_received_at,
            "subtitle_translation_retry_count": retry_count,
        },
        step="target_subtitle_translation",
    )
    saved_task = _materialize_authoritative_target_subtitle(
        task_id,
        output_task,
        repo=repo,
        translated_text=translated_text,
        target_lang=target_lang,
        execution_ref=execution_ref,
        retry_count=retry_count,
        now_fn=now_fn,
    )
    return TargetSubtitleTranslationExecutionResult(
        translated_text=translated_text,
        saved_task=saved_task,
        execution_ref=execution_ref,
        retry_count=retry_count,
        materialized=True,
    )
