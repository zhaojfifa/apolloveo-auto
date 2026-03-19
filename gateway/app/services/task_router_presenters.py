from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def build_task_workbench_task_json(
    task: dict,
    detail: Any,
    paths: dict[str, Any],
    *,
    workbench_kind: str,
    settings: Any,
    hot_follow_operational_defaults: Callable[[], dict[str, Any]] | None = None,
    hot_follow_ui_collector: Callable[[dict, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    task_json = {
        "task_id": detail.task_id,
        "status": detail.status,
        "platform": detail.platform,
        "category_key": detail.category_key,
        "content_lang": detail.content_lang,
        "ui_lang": detail.ui_lang,
        "source_url": detail.source_url,
        "pipeline_config": detail.pipeline_config,
        "no_dub": detail.no_dub,
        "dub_skip_reason": detail.dub_skip_reason,
        "raw_path": detail.raw_path,
        "origin_srt_path": detail.origin_srt_path,
        "mm_srt_path": detail.mm_srt_path,
        "mm_audio_path": detail.mm_audio_path,
        "mm_txt_path": paths.get("mm_txt_path"),
        "pack_path": detail.pack_path,
        "scenes_path": detail.scenes_path,
        "scenes_status": detail.scenes_status,
        "scenes_key": detail.scenes_key,
        "scenes_error": detail.scenes_error,
        "subtitles_status": detail.subtitles_status,
        "subtitles_key": detail.subtitles_key,
        "subtitles_error": detail.subtitles_error,
        "publish_status": detail.publish_status,
        "publish_provider": detail.publish_provider,
        "publish_key": detail.publish_key,
        "publish_url": detail.publish_url,
        "published_at": detail.published_at,
    }
    if (
        workbench_kind == "hot_follow"
        and hot_follow_operational_defaults is not None
        and hot_follow_ui_collector is not None
    ):
        task_json.update(hot_follow_operational_defaults())
        task_json.update(hot_follow_ui_collector(task, settings))
    return task_json


def build_task_workbench_view(
    task: dict,
    *,
    extract_first_http_url: Callable[[str | None], str | None],
) -> dict[str, Any]:
    return {"source_url_open": extract_first_http_url(task.get("source_url"))}


def build_task_status_payload(
    task_id: str,
    task: dict,
    detail: Any,
    *,
    task_status_shape: Callable[[dict], dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_at = getattr(detail, "updated_at", None)
    updated_ts = None
    if updated_at:
        try:
            updated_ts = (
                updated_at.replace(tzinfo=timezone.utc).timestamp()
                if updated_at.tzinfo is None
                else updated_at.timestamp()
            )
        except Exception:
            updated_ts = None
    now_ts = datetime.now(timezone.utc).timestamp()
    running = any(
        getattr(detail, key, None) == "running"
        for key in ("subtitles_status", "dub_status", "scenes_status", "pack_status")
    )
    stale_for = int(max(0, now_ts - updated_ts)) if updated_ts and running else 0
    stale = bool(running and updated_ts and stale_for > 1800)

    payload = detail.dict()
    for key in (
        "status",
        "last_step",
        "subtitles_status",
        "dub_status",
        "scenes_status",
        "pack_status",
        "subtitles_error",
        "dub_error",
        "scenes_error",
        "scenes_started_at",
        "scenes_finished_at",
        "scenes_elapsed_ms",
        "scenes_attempt",
        "scenes_run_id",
        "scenes_error_message",
        "pack_error",
        "raw_path",
        "origin_srt_path",
        "mm_srt_path",
        "mm_txt_path",
        "mm_audio_path",
        "pack_path",
        "scenes_path",
        "updated_at",
        "warnings",
        "warning_reasons",
    ):
        payload.setdefault(key, None)

    payload["stale"] = stale
    payload["stale_reason"] = "running_but_not_updated" if stale else None
    payload["stale_for_seconds"] = stale_for

    shape = task_status_shape(task)
    log_extra = {
        "task_id": task_id,
        "status": payload.get("status"),
        "last_step": payload.get("last_step"),
        "subtitles_status": payload.get("subtitles_status"),
        "dub_status": payload.get("dub_status"),
        "scenes_status": payload.get("scenes_status"),
        "pack_status": payload.get("pack_status"),
        "stale": payload.get("stale"),
        "step": shape.get("step"),
        "phase": shape.get("phase"),
        "provider": shape.get("provider"),
    }
    return payload, log_extra
