from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List


def _lower(v: Any) -> str:
    return str(v or "").lower()


def _scene_key(task: Dict[str, Any]) -> str:
    kind = _lower(
        task.get("kind")
        or task.get("category")
        or task.get("task_kind")
        or task.get("platform")
        or ""
    )
    if "apollo_avatar" in kind or "apollo-avatar" in kind or "avatar" in kind:
        return "avatar"
    if "hot" in kind or "follow" in kind:
        return "hot"
    return "baseline"


def _db_status(task: Dict[str, Any]) -> str:
    s = _lower(task.get("status") or task.get("db_status") or task.get("state") or "")
    if not s:
        return "unknown"
    if s in {"done", "ready", "success"}:
        return "ready"
    if s in {"running", "processing", "in_progress"}:
        return "processing"
    if s in {"queued", "pending"}:
        return "queued"
    if s in {"failed", "error"}:
        return "failed"
    return s


def _pack_exists(task: Dict[str, Any]) -> bool:
    deliverables = task.get("deliverables") or {}
    return bool(
        task.get("pack_key")
        or task.get("pack_path")
        or task.get("deliver_pack_key")
        or task.get("deliverables_pack_key")
        or task.get("pack_url")
        or task.get("pack_download_url")
        or deliverables.get("pack")
        or deliverables.get("pack_zip")
        or deliverables.get("capcut_pack")
    )


def _video_exists(task: Dict[str, Any]) -> bool:
    deliverables = task.get("deliverables") or {}
    return bool(
        task.get("raw_url")
        or task.get("video_url")
        or task.get("preview_url")
        or task.get("raw_path")
        or task.get("raw_key")
        or deliverables.get("raw")
        or deliverables.get("video")
    )


def _pack_download_url(task: Dict[str, Any], task_id: str) -> str | None:
    return task.get("pack_download_url") or task.get("pack_url") or (
        f"/v1/tasks/{task_id}/pack" if task_id else None
    )


def _detail_url(task_id: str) -> str | None:
    return f"/tasks/{task_id}" if task_id else None


def _created_label(task: Dict[str, Any]) -> str:
    return (
        task.get("created_ago")
        or task.get("created_at")
        or task.get("created")
        or ""
    )


def _title(task: Dict[str, Any]) -> str:
    return task.get("title") or task.get("name") or task.get("summary") or ""


def _subtitle(task: Dict[str, Any]) -> str:
    platform = task.get("platform") or task.get("source_platform") or ""
    task_id = task.get("task_id") or task.get("id") or ""
    account = task.get("account") or task.get("author") or task.get("owner") or ""
    parts: List[str] = []
    if platform:
        parts.append(str(platform))
    if task_id:
        parts.append(f"ID: {task_id}")
    if account:
        parts.append(f"@{account}")
    return " · ".join(parts)


def derive_task_semantics(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    derived: List[Dict[str, Any]] = []
    for t in tasks:
        task_id = str(t.get("task_id") or t.get("id") or "")
        scene = _scene_key(t)
        db_status = _db_status(t)
        pack_exists = _pack_exists(t)
        video_exists = _video_exists(t)
        done = pack_exists or db_status == "ready"
        processing = (not done) and db_status in {"processing", "queued"}
        needs_attention = db_status == "failed" and not pack_exists
        yellow = db_status == "failed" and pack_exists

        row = dict(t)
        row.update(
            {
                "scene_key": scene,
                "scene_label_key": f"tasks.scene.{scene}",
                "db_status": db_status,
                "pack_exists": pack_exists,
                "video_exists": video_exists,
                "done": done,
                "processing": processing,
                "needs_attention": needs_attention,
                "yellow": yellow,
                "pack_download_url": _pack_download_url(t, task_id),
                "primary_action_url": _detail_url(task_id),
                "detail_url": _detail_url(task_id),
                "created_label": _created_label(t),
                "title_text": _title(t),
                "subtitle_text": _subtitle(t),
            }
        )
        derived.append(row)
    return derived
