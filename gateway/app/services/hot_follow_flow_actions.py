from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import HTTPException

from gateway.app.services.hot_follow_subtitle_authority import (
    persist_hot_follow_authoritative_target_subtitle,
)
from gateway.app.services.source_audio_policy import normalize_source_audio_policy
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage


MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN = "materialize_target_subtitle_from_origin"
LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW = "local_preserve_to_subtitle_dub_flow"


@dataclass(frozen=True)
class TargetSubtitleMaterializationFailure(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def _now_iso(now_fn: Callable[[], datetime] | None = None) -> str:
    now = (now_fn or (lambda: datetime.now(timezone.utc)))()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.isoformat()


def materialize_target_subtitle_from_origin(
    task_id: str,
    task: dict[str, Any],
    *,
    repo: Any,
    origin_text: str,
    target_lang: str,
    expected_origin_key: str | None = None,
    expected_subtitle_source: str,
    translate_origin_srt_fn: Callable[[str, str], str],
    persist_artifact_fn: Callable[[str], str | None],
    content_hash_fn: Callable[[str | None], str | None],
    write_override_fn: Callable[[str], None] | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Formal target subtitle materialization action.

    The only subtitle-truth write is delegated to Subtitle Stage owner's
    authoritative target subtitle save path.
    """
    current_origin_key = str(task.get("origin_srt_path") or "").strip()
    if expected_origin_key is not None and str(expected_origin_key or "").strip() != current_origin_key:
        raise TargetSubtitleMaterializationFailure(
            "stale_source",
            "origin.srt changed before target subtitle materialization",
        )
    if not str(origin_text or "").strip():
        raise TargetSubtitleMaterializationFailure(
            "no_translated_target_produced",
            "current origin.srt is missing or empty",
        )

    started_at = _now_iso(now_fn)
    policy_upsert(
        repo,
        task_id,
        task,
        {
            "target_subtitle_materialization_action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
            "target_subtitle_materialization_status": "running",
            "target_subtitle_materialization_started_at": started_at,
            "target_subtitle_materialization_error_code": None,
            "target_subtitle_materialization_error_message": None,
        },
        step="subtitles.materialize_target_from_origin.start",
    )
    latest = repo.get(task_id) or task
    try:
        translated_text = translate_origin_srt_fn(str(origin_text), str(target_lang))
    except TargetSubtitleMaterializationFailure:
        raise
    except Exception as exc:
        policy_upsert(
            repo,
            task_id,
            latest,
            {
                "target_subtitle_materialization_status": "failed",
                "target_subtitle_materialization_error_code": "provider_error",
                "target_subtitle_materialization_error_message": str(exc),
            },
            step="subtitles.materialize_target_from_origin.failed",
        )
        raise TargetSubtitleMaterializationFailure("provider_error", str(exc)) from exc

    if not str(translated_text or "").strip():
        policy_upsert(
            repo,
            task_id,
            latest,
            {
                "target_subtitle_materialization_status": "failed",
                "target_subtitle_materialization_error_code": "no_translated_target_produced",
                "target_subtitle_materialization_error_message": "translation produced no target subtitle text",
            },
            step="subtitles.materialize_target_from_origin.failed",
        )
        raise TargetSubtitleMaterializationFailure(
            "no_translated_target_produced",
            "translation produced no target subtitle text",
        )

    try:
        saved = persist_hot_follow_authoritative_target_subtitle(
            task_id,
            latest,
            repo=repo,
            text=str(translated_text),
            text_mode=MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
            target_lang=target_lang,
            source_texts=(origin_text,),
            expected_subtitle_source=expected_subtitle_source,
            persist_artifact_fn=persist_artifact_fn,
            write_override_fn=write_override_fn,
            content_hash_fn=content_hash_fn,
            subtitle_stage_action=MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
            extra_updates={
                "target_subtitle_materialization_action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
                "target_subtitle_materialization_status": "ready",
                "target_subtitle_materialization_completed_at": _now_iso(now_fn),
                "target_subtitle_materialization_error_code": None,
                "target_subtitle_materialization_error_message": None,
            },
            resolve_helper_state=True,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        code = str(detail.get("reason") or "invalid_target")
        message = str(detail.get("message") or exc.detail or "target subtitle is invalid")
        policy_upsert(
            repo,
            task_id,
            latest,
            {
                "target_subtitle_materialization_status": "failed",
                "target_subtitle_materialization_error_code": "invalid_target",
                "target_subtitle_materialization_error_message": message,
            },
            step="subtitles.materialize_target_from_origin.failed",
        )
        raise TargetSubtitleMaterializationFailure("invalid_target", code) from exc
    return saved


def local_preserve_to_subtitle_dub_flow(
    repo: Any,
    task_id: str,
    task: dict[str, Any],
    *,
    reason: str | None = None,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Formal operator action to leave local preserve-source testing path.

    This action does not materialize subtitle truth. It records operator intent
    and queues the formal target-subtitle materialization action.
    """
    task_obj = dict(task or {})
    if str(task_obj.get("kind") or task_obj.get("category_key") or "").strip().lower() != "hot_follow":
        raise ValueError("task is not hot_follow")
    if str(task_obj.get("source_type") or "").strip().lower() != "local" and str(task_obj.get("platform") or "").strip().lower() != "local":
        raise ValueError("task is not local upload")

    config = dict(task_obj.get("config") or {})
    config["source_audio_policy"] = normalize_source_audio_policy("mute")
    pipeline_config = parse_pipeline_config(task_obj.get("pipeline_config"))
    pipeline_config["source_audio_policy"] = "mute"
    pipeline_config["audio_strategy"] = "mute"
    pipeline_config["bgm_strategy"] = "replace"
    timestamp = _now_iso(now_fn)
    updates = {
        "config": config,
        "pipeline_config": pipeline_config_to_storage(pipeline_config),
        "hot_follow_flow_stage_action": LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW,
        "hot_follow_flow_stage_action_at": timestamp,
        "hot_follow_flow_stage_action_reason": str(reason or "operator_selected_subtitle_dub_flow").strip(),
        "target_subtitle_materialization_action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
        "target_subtitle_materialization_status": "pending",
        "target_subtitle_materialization_requested_at": timestamp,
        "compose_status": "pending",
        "compose_error": None,
        "compose_error_reason": None,
        "final_fresh": False,
        "final_stale_reason": "local_preserve_to_subtitle_dub_flow",
    }
    if str(task_obj.get("dub_status") or "").strip().lower() in {"skipped", "done", "ready", "success", "completed"}:
        updates["dub_status"] = "pending"
    return policy_upsert(
        repo,
        task_id,
        task_obj,
        updates,
        step="hot_follow.local_preserve_to_subtitle_dub_flow",
    )
