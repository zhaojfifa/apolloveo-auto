from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def filter_tasks_for_kind(items: list[dict[str, Any]], kind_norm: str) -> list[dict[str, Any]]:
    kind_value = str(kind_norm or "").strip().lower()
    if not kind_value:
        return list(items or [])
    if kind_value == "apollo_avatar":
        return [
            t
            for t in (items or [])
            if (str(t.get("platform") or "").lower() == "apollo_avatar")
            or (str(t.get("category_key") or "").lower() == "apollo_avatar")
        ]
    return [
        t
        for t in (items or [])
        if str(t.get("category_key") or "").lower() == kind_value
        or str(t.get("platform") or "").lower() == kind_value
    ]


def build_tasks_page_rows(
    db_tasks: list[dict[str, Any]],
    *,
    kind_norm: str,
    pack_path_for_list: Callable[[dict[str, Any]], str | None],
    normalize_selected_tool_ids: Callable[[Any], list[str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for t in filter_tasks_for_kind(db_tasks, kind_norm):
        rows.append(
            {
                "task_id": t.get("task_id") or t.get("id"),
                "platform": t.get("platform"),
                "source_url": t.get("source_url"),
                "title": t.get("title") or "",
                "category_key": t.get("category_key") or "",
                "content_lang": t.get("content_lang") or "",
                "status": t.get("status") or "pending",
                "created_at": t.get("created_at") or "",
                "pack_path": pack_path_for_list(t),
                "pack_key": t.get("pack_key"),
                "pack_url": t.get("pack_url"),
                "deliver_pack_key": t.get("deliver_pack_key"),
                "cover_url": t.get("cover_url"),
                "thumb_url": t.get("thumb_url"),
                "raw_path": t.get("raw_path"),
                "raw_key": t.get("raw_key"),
                "raw_url": t.get("raw_url"),
                "video_url": t.get("video_url"),
                "preview_url": t.get("preview_url"),
                "ui_lang": t.get("ui_lang") or "",
                "selected_tool_ids": normalize_selected_tool_ids(t.get("selected_tool_ids")),
            }
        )
    return rows


def build_task_workbench_page_context(
    task: dict[str, Any],
    *,
    spec: Any,
    settings: Any,
    task_to_detail: Callable[[dict[str, Any]], Any],
    resolve_download_urls: Callable[[dict[str, Any]], dict[str, Any]],
    build_task_workbench_task_json: Callable[..., dict[str, Any]],
    build_task_workbench_view: Callable[..., dict[str, Any]],
    extract_first_http_url: Callable[[str | None], str | None],
    hot_follow_operational_defaults: Callable[[], dict[str, Any]] | None = None,
    hot_follow_ui_collector: Callable[[dict, Any], dict[str, Any]] | None = None,
    features: dict[str, Any] | None = None,
) -> dict[str, Any]:
    env_summary = {
        "workspace_root": settings.workspace_root,
        "douyin_api_base": getattr(settings, "douyin_api_base", ""),
        "whisper_model": getattr(settings, "whisper_model", ""),
        "gpt_model": getattr(settings, "gpt_model", ""),
        "asr_backend": getattr(settings, "asr_backend", None) or "whisper",
        "subtitles_backend": getattr(settings, "subtitles_backend", "gemini"),
        "gemini_model": getattr(settings, "gemini_model", ""),
    }
    try:
        from gateway.app.providers.registry import resolve_tool_providers

        env_summary["defaults"] = resolve_tool_providers().get("tools", {})
    except Exception:
        env_summary["defaults"] = {}

    paths = resolve_download_urls(task)
    detail = task_to_detail(task)
    task_json = build_task_workbench_task_json(
        task,
        detail,
        paths,
        workbench_kind=spec.kind,
        settings=settings,
        hot_follow_operational_defaults=hot_follow_operational_defaults,
        hot_follow_ui_collector=hot_follow_ui_collector,
    )
    task_view = build_task_workbench_view(
        task,
        extract_first_http_url=extract_first_http_url,
    )
    return {
        "task": detail,
        "task_json": task_json,
        "task_view": task_view,
        "env_summary": env_summary,
        "features": features or {},
        "workbench_kind": spec.kind,
        "workbench_js": spec.js,
    }


def build_task_summaries_page(
    items: list[dict[str, Any]],
    *,
    kind_norm: str,
    page: int,
    page_size: int,
    resolve_download_urls: Callable[[dict[str, Any]], dict[str, Any]],
    derive_status: Callable[[dict[str, Any]], str],
    extract_first_http_url: Callable[[str | None], str | None],
    coerce_datetime: Callable[[Any], datetime | None],
    parse_pipeline_config: Callable[[Any], dict[str, Any]],
    normalize_selected_tool_ids: Callable[[Any], list[str]],
    task_summary_cls: Callable[..., Any],
) -> tuple[list[Any], int]:
    filtered = filter_tasks_for_kind(items, kind_norm)
    total = len(filtered)
    page_items = filtered[(page - 1) * page_size : (page - 1) * page_size + page_size]

    summaries: list[Any] = []
    for t in page_items:
        download_paths = resolve_download_urls(t)
        pack_path = download_paths.get("pack_path")
        scenes_path = download_paths.get("scenes_path")
        status = derive_status(t)
        summaries.append(
            task_summary_cls(
                task_id=str(t.get("task_id") or t.get("id")),
                title=t.get("title"),
                kind=t.get("kind"),
                source_url=str(t.get("source_url")) if t.get("source_url") else None,
                source_link_url=extract_first_http_url(t.get("source_url")),
                platform=t.get("platform"),
                account_id=t.get("account_id"),
                account_name=t.get("account_name"),
                video_type=t.get("video_type"),
                template=t.get("template"),
                category_key=t.get("category_key") or "beauty",
                content_lang=t.get("content_lang") or "my",
                ui_lang=t.get("ui_lang") or "en",
                style_preset=t.get("style_preset"),
                face_swap_enabled=bool(t.get("face_swap_enabled")),
                status=status,
                last_step=t.get("last_step"),
                duration_sec=t.get("duration_sec"),
                thumb_url=t.get("thumb_url"),
                cover_url=t.get("cover_url"),
                pack_path=pack_path,
                scenes_path=scenes_path,
                scenes_status=t.get("scenes_status"),
                scenes_key=t.get("scenes_key"),
                scenes_error=t.get("scenes_error"),
                subtitles_status=t.get("subtitles_status"),
                subtitles_key=t.get("subtitles_key"),
                subtitles_error=t.get("subtitles_error"),
                created_at=(
                    coerce_datetime(t.get("created_at") or t.get("created") or t.get("createdAt"))
                    or datetime(1970, 1, 1, tzinfo=timezone.utc)
                ),
                updated_at=coerce_datetime(t.get("updated_at") or t.get("updatedAt")),
                error_message=t.get("error_message"),
                error_reason=t.get("error_reason"),
                parse_provider=t.get("parse_provider"),
                subtitles_provider=t.get("subtitles_provider"),
                dub_provider=t.get("dub_provider"),
                pack_provider=t.get("pack_provider"),
                face_swap_provider=t.get("face_swap_provider"),
                publish_status=t.get("publish_status"),
                publish_provider=t.get("publish_provider"),
                publish_key=t.get("publish_key"),
                publish_url=t.get("publish_url"),
                published_at=t.get("published_at"),
                priority=t.get("priority"),
                assignee=t.get("assignee"),
                ops_notes=t.get("ops_notes"),
                selected_tool_ids=normalize_selected_tool_ids(t.get("selected_tool_ids")),
                pipeline_config=parse_pipeline_config(t.get("pipeline_config")),
            )
        )
    return summaries, total


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
