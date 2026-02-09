from __future__ import annotations

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

    db_status = _lower(task.get("status") or "")
    if not db_status:
        db_status = "unknown"

    pack_exists = bool(
        task.get("pack_path")
        or task.get("pack_key")
        or task.get("deliver_pack_key")
        or task.get("pack_url")
    )
    pack_ready = pack_exists or db_status in {"ready", "done"}
    needs_attention = (db_status in {"failed", "error"}) and (not pack_exists)
    yellow_row = (db_status in {"failed", "error"}) and pack_exists
    if needs_attention:
        filter_status = "attention"
    elif pack_ready:
        filter_status = "done"
    elif db_status in {"processing", "queued"}:
        filter_status = "processing"
    else:
        filter_status = "other"

    primary_action_href = f"/tasks/{task_id}" if task_id else ""

    if pack_exists and yellow_row:
        download_label_key = "action.force_download"
    elif pack_exists:
        download_label_key = "action.download"
    else:
        download_label_key = "action.download_disabled"

    pack_download_href = f"/v1/tasks/{task_id}/pack" if task_id else ""

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

    video_exists = bool(
        task.get("raw_url")
        or task.get("video_url")
        or task.get("preview_url")
        or task.get("raw_path")
        or task.get("raw_key")
    )

    row_class = "bg-yellow-50/30" if yellow_row else ""
    show_pack_badge = pack_exists or pack_ready
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

    if pack_exists:
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
