from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from fastapi import HTTPException

from gateway.app.services.hot_follow_helper_translation import helper_translate_resolved_updates
from gateway.app.services.hot_follow_subtitle_currentness import (
    compute_hot_follow_target_subtitle_currentness,
    has_semantic_target_subtitle_text,
)
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage


@dataclass(frozen=True)
class SubtitleAuthorityDecision:
    accepted: bool
    reason: str
    message: str
    target_currentness: dict[str, object]


def _reason_message(reason: str) -> str:
    messages = {
        "subtitle_missing": "权威目标字幕缺失，不能记录为字幕成功。",
        "target_subtitle_empty": "目标字幕内容为空或只有时间轴，不能记录为字幕成功。",
        "target_subtitle_not_authoritative": "当前字幕结果不是权威目标字幕，不能记录为字幕成功。",
        "target_subtitle_translation_incomplete": "目标字幕翻译未完成，不能记录为字幕成功。",
        "target_subtitle_source_copy": "目标字幕与来源字幕相同，不能记录为字幕成功。",
        "target_subtitle_source_mismatch": "目标字幕产物不是期望的权威目标字幕文件，不能记录为字幕成功。",
    }
    return messages.get(reason, "目标字幕尚未成为可用的权威当前字幕，不能记录为字幕成功。")


def evaluate_hot_follow_subtitle_authority(
    *,
    target_lang: str | None,
    target_text: str | None,
    source_texts: Iterable[str | None],
    subtitle_artifact_exists: bool,
    expected_subtitle_source: str | None,
    actual_subtitle_source: str | None,
    translation_incomplete: bool = False,
    has_saved_revision: bool = False,
    target_subtitle_authoritative: bool = True,
) -> SubtitleAuthorityDecision:
    semantic_target = has_semantic_target_subtitle_text(target_text)
    raw_target = str(target_text or "")
    target_currentness = compute_hot_follow_target_subtitle_currentness(
        target_lang=target_lang,
        target_text=target_text,
        source_texts=source_texts,
        subtitle_artifact_exists=subtitle_artifact_exists,
        expected_subtitle_source=expected_subtitle_source,
        actual_subtitle_source=actual_subtitle_source,
        translation_incomplete=translation_incomplete,
        has_saved_revision=has_saved_revision,
    )
    reason = str(target_currentness.get("target_subtitle_current_reason") or "subtitle_missing")
    accepted = bool(target_currentness.get("target_subtitle_current"))
    if not target_subtitle_authoritative:
        reason = "target_subtitle_not_authoritative"
        accepted = False
    elif translation_incomplete:
        reason = "target_subtitle_translation_incomplete"
        accepted = False
    elif not semantic_target and raw_target.strip():
        reason = "target_subtitle_empty"
        accepted = False

    resolved_currentness = {
        **target_currentness,
        "target_subtitle_current": bool(accepted),
        "target_subtitle_current_reason": reason,
    }
    return SubtitleAuthorityDecision(
        accepted=bool(accepted),
        reason=reason,
        message=_reason_message(reason),
        target_currentness=resolved_currentness,
    )


def _recovered_subtitle_commit_scrub_updates(task: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {
        "subtitles_error_reason": None,
        "target_subtitle_authoritative_source": True,
    }
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    stale_no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip().lower()
    if stale_no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}:
        pipeline_config.pop("no_dub", None)
        pipeline_config.pop("dub_skip_reason", None)
        updates["pipeline_config"] = pipeline_config_to_storage(pipeline_config)
        updates["dub_skip_reason"] = None
        if str(task.get("dub_status") or "").strip().lower() == "skipped":
            updates["dub_status"] = "pending"
    if str(task.get("subtitle_helper_status") or "").strip().lower() == "failed":
        updates.update(helper_translate_resolved_updates())
    return updates


def persist_hot_follow_authoritative_target_subtitle(
    task_id: str,
    task: dict[str, Any],
    *,
    repo: Any,
    text: str,
    text_mode: str,
    target_lang: str,
    source_texts: Iterable[str | None],
    expected_subtitle_source: str,
    persist_artifact_fn: Callable[[str], str | None],
    write_override_fn: Callable[[str], None] | None = None,
    content_hash_fn: Callable[[str | None], str | None],
    extra_updates: dict[str, Any] | None = None,
    resolve_helper_state: bool = False,
    now_fn: Callable[[], str] | None = None,
) -> dict[str, Any]:
    decision = evaluate_hot_follow_subtitle_authority(
        target_lang=target_lang,
        target_text=text,
        source_texts=source_texts,
        subtitle_artifact_exists=True,
        expected_subtitle_source=expected_subtitle_source,
        actual_subtitle_source=expected_subtitle_source,
        translation_incomplete=False,
        has_saved_revision=bool(str(text or "").strip()),
        target_subtitle_authoritative=True,
    )
    if not decision.accepted:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": decision.reason,
                "message": decision.message,
            },
        )

    if write_override_fn is not None:
        write_override_fn(text)
    synced_key = persist_artifact_fn(text)
    actual_source = Path(str(synced_key)).name if synced_key else None
    persisted = evaluate_hot_follow_subtitle_authority(
        target_lang=target_lang,
        target_text=text,
        source_texts=source_texts,
        subtitle_artifact_exists=bool(synced_key),
        expected_subtitle_source=expected_subtitle_source,
        actual_subtitle_source=actual_source,
        translation_incomplete=False,
        has_saved_revision=bool(str(text or "").strip()),
        target_subtitle_authoritative=True,
    )
    if not persisted.accepted:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": persisted.reason,
                "message": persisted.message,
            },
        )

    updates: dict[str, Any] = {
        "subtitles_status": "ready",
        "subtitles_error": None,
        "subtitles_error_reason": None,
        "last_step": "subtitles",
        "mm_srt_path": synced_key or task.get("mm_srt_path"),
        "subtitles_override_updated_at": (now_fn or (lambda: datetime.now(timezone.utc).isoformat()))(),
        "subtitles_override_mode": text_mode,
        "subtitles_content_hash": content_hash_fn(text),
        "compose_status": "pending",
        "compose_error": None,
        "compose_error_reason": None,
        "error_message": None,
        "error_reason": None,
        "target_subtitle_current": True,
        "target_subtitle_current_reason": persisted.reason,
        "target_subtitle_authoritative_source": True,
    }
    updates.update(_recovered_subtitle_commit_scrub_updates(task))
    if resolve_helper_state:
        updates.update(helper_translate_resolved_updates())
    if extra_updates:
        updates.update(extra_updates)
    return policy_upsert(repo, task_id, task, updates, step="subtitles")


def finalize_hot_follow_subtitles_step(
    task_id: str,
    task: dict[str, Any],
    *,
    repo: Any,
    target_text: str,
    target_lang: str,
    source_texts: Iterable[str | None],
    target_subtitle_key: str | None,
    subtitles_key: str | None,
    origin_key: str | None,
    expected_subtitle_source: str,
    translation_incomplete: bool,
    target_subtitle_authoritative: bool,
    target_subtitle_required: bool = True,
) -> dict[str, Any]:
    actual_source = Path(str(target_subtitle_key)).name if target_subtitle_key else None
    decision = evaluate_hot_follow_subtitle_authority(
        target_lang=target_lang,
        target_text=target_text,
        source_texts=source_texts,
        subtitle_artifact_exists=bool(target_subtitle_key),
        expected_subtitle_source=expected_subtitle_source,
        actual_subtitle_source=actual_source,
        translation_incomplete=translation_incomplete,
        has_saved_revision=False,
        target_subtitle_authoritative=target_subtitle_authoritative,
    )
    translation_waiting_retryable = bool(
        translation_incomplete
        and target_subtitle_required
        and any(has_semantic_target_subtitle_text(text) for text in source_texts)
    )
    updates: dict[str, Any] = {
        "origin_srt_path": origin_key,
        "mm_srt_path": target_subtitle_key if target_subtitle_authoritative else None,
        "last_step": "subtitles",
        "subtitles_key": subtitles_key,
        "subtitle_structure_path": subtitles_key,
        "target_subtitle_current": bool(decision.target_currentness.get("target_subtitle_current")),
        "target_subtitle_current_reason": decision.reason,
    }
    if decision.accepted:
        updates.update(
            {
                "subtitles_status": "ready",
                "subtitles_error": None,
                "subtitles_error_reason": None,
                "target_subtitle_authoritative_source": True,
                "error_message": None,
                "error_reason": None,
            }
        )
        updates.update(_recovered_subtitle_commit_scrub_updates(task))
    elif translation_waiting_retryable:
        updates.update(
            {
                "subtitles_status": "pending",
                "subtitles_error": "subtitle translation not ready yet; waiting for retryable translation resolution",
            }
        )
    elif not target_subtitle_required:
        updates.update(
            {
                "subtitles_status": "ready",
                "subtitles_error": None,
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "preserve_source_route_no_target_subtitle_required",
            }
        )
    else:
        updates.update(
            {
                "subtitles_status": "failed",
                "subtitles_error": decision.message,
            }
        )
    return policy_upsert(repo, task_id, task, updates, step="subtitles")
