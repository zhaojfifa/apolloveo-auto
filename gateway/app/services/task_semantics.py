from __future__ import annotations

import json
from typing import Any, Dict

from gateway.app.i18n import DEFAULT_LOCALE, t


def _lower(value: Any) -> str:
    return str(value or "").lower()


def _scene_key(task: dict) -> str:
    kind = _lower(
        task.get("kind")
        or task.get("category")
        or task.get("task_kind")
        or task.get("platform")
        or task.get("category_key")
        or ""
    )
    if "apollo_avatar" in kind or "apollo-avatar" in kind or "avatar" in kind:
        return "avatar"
    if "hot" in kind or "follow" in kind:
        return "hot_follow"
    return "baseline"


def _target_lang(task: dict) -> str:
    raw = _lower(
        task.get("target_lang")
        or task.get("content_lang")
        or task.get("language")
        or ""
    )
    return "my" if raw == "mm" else raw


def _is_hot_follow(task: dict) -> bool:
    return _scene_key(task) == "hot_follow"


def _pipeline_config(task: dict) -> dict:
    value = task.get("pipeline_config")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            decoded = json.loads(text)
        except Exception:
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


def _target_subtitle_current_fact(task: dict) -> bool | None:
    if _target_lang(task) != "vi":
        return None
    explicit = task.get("target_subtitle_current")
    if explicit is not None:
        return bool(explicit)
    ready_gate = task.get("ready_gate") if isinstance(task.get("ready_gate"), dict) else {}
    if "subtitle_ready" in ready_gate:
        return bool(ready_gate.get("subtitle_ready"))
    pipeline_config = _pipeline_config(task)
    translation_incomplete = str(pipeline_config.get("translation_incomplete") or "").strip().lower() == "true"
    has_saved_revision = bool(
        str(task.get("subtitles_content_hash") or "").strip()
        or str(task.get("subtitles_override_updated_at") or "").strip()
    )
    if translation_incomplete and not has_saved_revision:
        return False
    return None


def _publishable_main_deliverable(task: dict) -> bool:
    publish_status = _lower(task.get("publish_status") or "")
    if publish_status in _DONE_STATES and (
        task.get("publish_key") or task.get("publish_url")
    ):
        return True
    return False


_DONE_STATES = {"ready", "done", "success", "completed"}
_RUNNING_STATES = {"processing", "running", "queued", "pending"}
_FAILED_STATES = {"failed", "error"}


def project_task_fact_status(task: dict) -> str:
    hot_follow = _is_hot_follow(task)
    ready_gate = task.get("ready_gate") if isinstance(task.get("ready_gate"), dict) else {}
    if bool(ready_gate.get("publish_ready") or ready_gate.get("compose_ready")):
        return "ready"

    if _publishable_main_deliverable(task):
        return "ready"

    final_exists = bool(
        task.get("final_video_key")
        or task.get("final_video_path")
        or task.get("final_url")
        or task.get("final_video_url")
    )
    if final_exists:
        return "ready"

    target_subtitle_current = _target_subtitle_current_fact(task)
    if target_subtitle_current is False:
        statuses = [
            _lower(task.get("status") or ""),
            _lower(task.get("dub_status") or ""),
            _lower(task.get("subtitles_status") or ""),
            _lower(task.get("parse_status") or ""),
            _lower(task.get("publish_status") or ""),
        ]
        if not hot_follow:
            statuses.append(_lower(task.get("pack_status") or ""))
        if any(status in _FAILED_STATES for status in statuses):
            return "failed"
        return "processing"

    compose_status = _lower(task.get("compose_status") or task.get("compose_last_status") or "")
    if compose_status in _DONE_STATES:
        return "ready"

    pack_exists = bool(
        task.get("pack_path")
        or task.get("pack_key")
        or task.get("deliver_pack_key")
        or task.get("pack_url")
    )
    if pack_exists and not hot_follow:
        return "ready"

    main_statuses = [
        compose_status,
        _lower(task.get("dub_status") or ""),
        _lower(task.get("subtitles_status") or ""),
        _lower(task.get("parse_status") or ""),
        _lower(task.get("publish_status") or ""),
    ]
    if any(status in _FAILED_STATES for status in main_statuses):
        return "failed"
    if any(status in _RUNNING_STATES for status in main_statuses):
        return "processing"
    statuses = list(main_statuses)
    if not hot_follow:
        statuses.append(_lower(task.get("pack_status") or ""))
    raw_status = _lower(task.get("status") or "")
    if raw_status in _FAILED_STATES:
        return "failed"
    if raw_status in _RUNNING_STATES and not any(status in _DONE_STATES for status in statuses):
        return "processing"
    if any(status in _DONE_STATES for status in statuses):
        return "ready"
    return "unknown"


def derive_task_semantics(task: dict) -> dict:
    """
    Derive UI semantics for /tasks board without changing backend contract.

    Input: plain dict from DB/ORM.
    Output: dict with UI-friendly fields.
    """

    task_id = str(task.get("task_id") or task.get("id") or "")
    locale = str(task.get("ui_lang") or DEFAULT_LOCALE)

    title = task.get("title") or ""
    title_display = title or t("tasks.untitled", locale=locale)

    cover_url = task.get("cover_url") or None

    raw_status = _lower(task.get("status") or "")
    db_status = project_task_fact_status(task)
    if db_status == "unknown" and raw_status:
        db_status = raw_status

    pack_exists = bool(
        task.get("pack_path")
        or task.get("pack_key")
        or task.get("deliver_pack_key")
        or task.get("pack_url")
    )
    final_exists = bool(
        task.get("final_video_key")
        or task.get("final_video_path")
        or task.get("final_url")
        or task.get("final_video_url")
    )
    raw_exists = bool(
        task.get("raw_url")
        or task.get("video_url")
        or task.get("preview_url")
        or task.get("raw_path")
        or task.get("raw_key")
    )
    if pack_exists:
        download_kind = "pack"
    elif final_exists:
        download_kind = "final_mp4"
    elif raw_exists:
        download_kind = "raw"
    else:
        download_kind = ""
    downloadable_exists = bool(download_kind)
    hot_follow = _is_hot_follow(task)
    if hot_follow:
        pack_ready = pack_exists
        needs_attention = db_status in _FAILED_STATES
        yellow_row = False
        if needs_attention:
            filter_status = "attention"
        elif db_status in _DONE_STATES:
            filter_status = "done"
        elif db_status in {"processing", "queued", "running", "pending"}:
            filter_status = "processing"
        else:
            filter_status = "other"
    else:
        pack_ready = pack_exists or db_status in _DONE_STATES
        needs_attention = (db_status in _FAILED_STATES) and (not pack_exists)
        yellow_row = (db_status in _FAILED_STATES) and pack_exists
        if needs_attention:
            filter_status = "attention"
        elif pack_ready:
            filter_status = "done"
        elif db_status in {"processing", "queued", "running", "pending"}:
            filter_status = "processing"
        else:
            filter_status = "other"

    primary_action_href = f"/tasks/{task_id}" if task_id else ""

    if downloadable_exists and yellow_row:
        download_label_key = "action.force_download"
    elif downloadable_exists:
        download_label_key = "action.download"
    else:
        download_label_key = "action.download_disabled"

    pack_download_href = ""

    scene_key = _scene_key(task)
    scene_label_key = f"tasks.filter.scene.{scene_key}"

    created_label = task.get("created_ago") or task.get("created_at") or task.get("created") or ""

    platform = task.get("platform") or ""
    subtitle_parts = []
    if platform:
        subtitle_parts.append(str(platform))
    if task_id:
        subtitle_parts.append(f"ID: {task_id}")
    subtitle = " · ".join(subtitle_parts)

    video_exists = raw_exists or final_exists

    row_class = "bg-yellow-50/30" if yellow_row else ""
    show_pack_badge = pack_exists or (pack_ready and not hot_follow)
    if pack_ready:
        pack_badge_label_key = "tasks.badge.pack_ready"
        pack_badge_class = "bg-green-50 text-green-700 ring-green-600/20"
    elif pack_exists:
        pack_badge_label_key = "tasks.badge.pack_exists"
        pack_badge_class = "bg-amber-50 text-amber-700 ring-amber-600/20"
    else:
        pack_badge_label_key = ""
        pack_badge_class = ""

    show_video_badge = video_exists
    video_badge_class = "bg-blue-50 text-blue-700 ring-blue-700/10"

    if downloadable_exists:
        if yellow_row:
            download_class = "rounded bg-indigo-50 text-indigo-600 ring-indigo-300 hover:bg-indigo-100 px-2 py-1 text-sm font-semibold ring-1 ring-inset"
        else:
            download_class = "rounded bg-white text-gray-900 ring-gray-300 hover:bg-gray-50 px-2 py-1 text-sm font-semibold ring-1 ring-inset"
        download_disabled_class = ""
    else:
        download_class = ""
        download_disabled_class = "rounded bg-gray-100 px-2 py-1 text-sm font-semibold text-gray-400 cursor-not-allowed"

    return {
        **task,
        "task_id": task_id,
        "title_display": title_display,
        "cover_url": cover_url,
        "db_status": db_status,
        "pack_exists": pack_exists,
        "pack_ready": pack_ready,
        "needs_attention": needs_attention,
        "yellow_row": yellow_row,
        "filter_status": filter_status,
        "primary_action_href": primary_action_href,
        "download_label_key": download_label_key,
        "pack_download_href": pack_download_href,
        "download_kind": download_kind,
        "downloadable_exists": downloadable_exists,
        "scene_key": scene_key,
        "scene_label_key": scene_label_key,
        "created_label": created_label,
        "subtitle": subtitle,
        "video_exists": video_exists,
        "row_class": row_class,
        "show_pack_badge": show_pack_badge,
        "pack_badge_label_key": pack_badge_label_key,
        "pack_badge_class": pack_badge_class,
        "show_video_badge": show_video_badge,
        "video_badge_class": video_badge_class,
        "download_class": download_class,
        "download_disabled_class": download_disabled_class,
    }
