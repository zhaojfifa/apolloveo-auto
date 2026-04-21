from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Callable

from gateway.app.services.hot_follow_runtime_bridge import (
    compat_collect_hot_follow_workbench_ui,
    compat_hot_follow_operational_defaults,
    compat_hot_follow_task_status_shape,
)
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state

logger = logging.getLogger(__name__)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _hot_follow_board_base_state(task: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    final_url = task.get("final_url") or task.get("final_video_url")
    final_key = task.get("final_video_key") or task.get("final_video_path")
    compose_status = task.get("compose_status")
    compose_last_status = task.get("compose_last_status")

    final_payload = dict(_as_dict(task.get("final")))
    if final_key:
        final_payload.setdefault("key", final_key)
    if final_url:
        final_payload.setdefault("url", final_url)
    if final_payload.get("exists") is None:
        final_payload["exists"] = bool(final_key or final_url)

    historical_final = dict(_as_dict(task.get("historical_final")))
    media = dict(_as_dict(task.get("media")))
    if final_url:
        media.setdefault("final_url", final_url)
        media.setdefault("final_video_url", final_url)

    deliverables_raw = task.get("deliverables")
    if isinstance(deliverables_raw, dict):
        deliverables: dict[str, Any] | list[Any] = dict(deliverables_raw)
    elif isinstance(deliverables_raw, list):
        deliverables = [
            dict(item) if isinstance(item, dict) else item
            for item in deliverables_raw
        ]
    else:
        deliverables = {}

    if isinstance(deliverables, dict) and bool(final_payload.get("exists")):
        final_item = dict(_as_dict(deliverables.get("final_mp4")) or {"label": "final.mp4"})
        if final_key:
            final_item.setdefault("key", final_key)
        if final_url:
            final_item.setdefault("url", final_url)
        final_item.setdefault("status", "done" if final_payload.get("exists") else "pending")
        final_item.setdefault("state", "done" if final_payload.get("exists") else "pending")
        deliverables["final_mp4"] = final_item

    return {
        "task_id": task_id,
        "kind": "hot_follow",
        "ready_gate": dict(_as_dict(task.get("ready_gate"))),
        "final": final_payload,
        "historical_final": historical_final,
        "final_url": final_url,
        "final_video_url": final_url,
        "media": media,
        "deliverables": deliverables,
        "audio": dict(_as_dict(task.get("audio"))),
        "subtitles": dict(_as_dict(task.get("subtitles"))),
        "compose_status": compose_status,
        "compose_last_status": compose_last_status,
    }


def _bind_hot_follow_projection(task: dict[str, Any]) -> dict[str, Any]:
    try:
        return compute_hot_follow_state(task, _hot_follow_board_base_state(task))
    except Exception as exc:
        logger.warning(
            "HOT_FOLLOW_BOARD_STATE_FALLBACK task_id=%s error=%s",
            str(task.get("task_id") or task.get("id") or ""),
            str(exc),
        )
        return {}


def _project_hot_follow_compose_status(record: dict[str, Any], payload: dict[str, Any]) -> None:
    compose_status = str(payload.get("compose_status") or "").strip().lower()
    if not compose_status and bool(payload.get("composed_ready")):
        compose_status = "done"
    if compose_status:
        record["compose_status"] = compose_status
    compose_last = _as_dict(_as_dict(payload.get("compose")).get("last"))
    compose_last_status = str(compose_last.get("status") or compose_status or "").strip().lower()
    if compose_last_status:
        record["compose_last_status"] = compose_last_status


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
        row = {
            "task_id": t.get("task_id") or t.get("id"),
            "platform": t.get("platform"),
            "source_url": t.get("source_url"),
            "title": t.get("title") or "",
            "category_key": t.get("category_key") or "",
            "content_lang": t.get("content_lang") or "",
            "target_lang": t.get("target_lang") or t.get("content_lang") or "",
            "status": t.get("status") or "pending",
            "parse_status": t.get("parse_status"),
            "dub_status": t.get("dub_status"),
            "compose_status": t.get("compose_status"),
            "compose_last_status": t.get("compose_last_status"),
            "final_video_key": t.get("final_video_key"),
            "final_video_path": t.get("final_video_path"),
            "final_url": t.get("final_url"),
            "final_video_url": t.get("final_video_url"),
            "publish_status": t.get("publish_status"),
            "publish_key": t.get("publish_key"),
            "publish_url": t.get("publish_url"),
            "ready_gate": t.get("ready_gate"),
            "target_subtitle_current": t.get("target_subtitle_current"),
            "target_subtitle_current_reason": t.get("target_subtitle_current_reason"),
            "subtitles_content_hash": t.get("subtitles_content_hash"),
            "subtitles_override_updated_at": t.get("subtitles_override_updated_at"),
            "pipeline_config": t.get("pipeline_config"),
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
        kind_value = str(t.get("kind") or t.get("category_key") or t.get("platform") or "").strip().lower()
        if kind_value == "hot_follow":
            payload = _bind_hot_follow_projection(t)
            final_payload = payload.get("final") if isinstance(payload.get("final"), dict) else {}
            row["ready_gate"] = payload.get("ready_gate") if isinstance(payload.get("ready_gate"), dict) else row["ready_gate"]
            row["final_url"] = payload.get("final_url") or row["final_url"] or final_payload.get("url")
            row["final_video_url"] = payload.get("final_video_url") or row["final_video_url"] or final_payload.get("url")
            row["final_video_key"] = row["final_video_key"] or final_payload.get("key")
            _project_hot_follow_compose_status(row, payload)
        rows.append(row)
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
        hot_follow_operational_defaults=hot_follow_operational_defaults or compat_hot_follow_operational_defaults,
        hot_follow_ui_collector=hot_follow_ui_collector or compat_collect_hot_follow_workbench_ui,
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
        bound_task = t
        kind_value = str(t.get("kind") or t.get("category_key") or t.get("platform") or "").strip().lower()
        if kind_value == "hot_follow":
            payload = _bind_hot_follow_projection(t)
            final_payload = payload.get("final") if isinstance(payload.get("final"), dict) else {}
            bound_task = dict(t)
            if isinstance(payload.get("ready_gate"), dict):
                bound_task["ready_gate"] = payload.get("ready_gate")
            bound_task["final_url"] = payload.get("final_url") or bound_task.get("final_url") or final_payload.get("url")
            bound_task["final_video_url"] = payload.get("final_video_url") or bound_task.get("final_video_url") or final_payload.get("url")
            bound_task["final_video_key"] = bound_task.get("final_video_key") or final_payload.get("key")
            _project_hot_follow_compose_status(bound_task, payload)
        download_paths = resolve_download_urls(bound_task)
        pack_path = download_paths.get("pack_path")
        scenes_path = download_paths.get("scenes_path")
        status = derive_status(bound_task)
        summaries.append(
            task_summary_cls(
                task_id=str(bound_task.get("task_id") or bound_task.get("id")),
                title=bound_task.get("title"),
                kind=bound_task.get("kind"),
                source_url=str(bound_task.get("source_url")) if bound_task.get("source_url") else None,
                source_link_url=extract_first_http_url(bound_task.get("source_url")),
                platform=bound_task.get("platform"),
                account_id=bound_task.get("account_id"),
                account_name=bound_task.get("account_name"),
                video_type=bound_task.get("video_type"),
                template=bound_task.get("template"),
                category_key=bound_task.get("category_key") or "beauty",
                content_lang=bound_task.get("content_lang") or "my",
                ui_lang=bound_task.get("ui_lang") or "en",
                style_preset=bound_task.get("style_preset"),
                face_swap_enabled=bool(bound_task.get("face_swap_enabled")),
                status=status,
                last_step=bound_task.get("last_step"),
                duration_sec=bound_task.get("duration_sec"),
                thumb_url=bound_task.get("thumb_url"),
                cover_url=bound_task.get("cover_url"),
                pack_path=pack_path,
                scenes_path=scenes_path,
                scenes_status=bound_task.get("scenes_status"),
                scenes_key=bound_task.get("scenes_key"),
                scenes_error=bound_task.get("scenes_error"),
                subtitles_status=bound_task.get("subtitles_status"),
                subtitles_key=bound_task.get("subtitles_key"),
                subtitles_error=bound_task.get("subtitles_error"),
                created_at=(
                    coerce_datetime(bound_task.get("created_at") or bound_task.get("created") or bound_task.get("createdAt"))
                    or datetime(1970, 1, 1, tzinfo=timezone.utc)
                ),
                updated_at=coerce_datetime(bound_task.get("updated_at") or bound_task.get("updatedAt")),
                error_message=bound_task.get("error_message"),
                error_reason=bound_task.get("error_reason"),
                parse_provider=bound_task.get("parse_provider"),
                subtitles_provider=bound_task.get("subtitles_provider"),
                dub_provider=bound_task.get("dub_provider"),
                pack_provider=bound_task.get("pack_provider"),
                face_swap_provider=bound_task.get("face_swap_provider"),
                publish_status=bound_task.get("publish_status"),
                publish_provider=bound_task.get("publish_provider"),
                publish_key=bound_task.get("publish_key"),
                publish_url=bound_task.get("publish_url"),
                published_at=bound_task.get("published_at"),
                priority=bound_task.get("priority"),
                assignee=bound_task.get("assignee"),
                ops_notes=bound_task.get("ops_notes"),
                selected_tool_ids=normalize_selected_tool_ids(bound_task.get("selected_tool_ids")),
                pipeline_config=parse_pipeline_config(bound_task.get("pipeline_config")),
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
        "raw_download_url": paths.get("raw_download_url"),
        "origin_srt_path": detail.origin_srt_path,
        "origin_srt_download_url": paths.get("origin_srt_download_url"),
        "mm_srt_path": detail.mm_srt_path,
        "mm_srt_download_url": paths.get("mm_srt_download_url"),
        "mm_audio_path": detail.mm_audio_path,
        "mm_audio_download_url": paths.get("mm_audio_download_url"),
        "mm_txt_path": paths.get("mm_txt_path"),
        "mm_txt_download_url": paths.get("mm_txt_download_url"),
        "pack_path": detail.pack_path,
        "pack_download_url": paths.get("pack_download_url"),
        "scenes_path": detail.scenes_path,
        "scenes_download_url": paths.get("scenes_download_url"),
        "final_download_url": paths.get("final_download_url"),
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
    task_status_shape: Callable[[dict], dict[str, str]] | None = None,
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

    shape = (task_status_shape or compat_hot_follow_task_status_shape)(task)
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
