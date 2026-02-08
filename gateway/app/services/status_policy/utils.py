from __future__ import annotations

from typing import Any, Dict, Optional


FAILED_SUBSTATUSES = (
    "subtitles_status",
    "dub_status",
    "scenes_status",
    "pack_status",
    "publish_status",
)


def is_deliverable_ready(task: dict | None, updates: dict | None) -> bool:
    merged: dict[str, Any] = {}
    if task:
        merged.update(task)
    if updates:
        merged.update(updates)

    publish_status = str(merged.get("publish_status") or "").lower()
    publish_key = merged.get("publish_key")
    publish_url = merged.get("publish_url")
    if publish_status == "ready" and (publish_key or publish_url):
        return True

    if merged.get("pack_path"):
        return True
    if merged.get("scenes_path"):
        return True

    return False


def coerce_final_status(kind: str | None, task: dict | None, updates: dict | None) -> Dict[str, Any]:
    updates = dict(updates or {})

    merged: dict[str, Any] = {}
    if task:
        merged.update(task)
    merged.update(updates)

    # Normalize any "done" in status-like fields.
    if str(merged.get("status") or "").lower() == "done":
        updates["status"] = "ready"
        merged["status"] = "ready"

    for key in FAILED_SUBSTATUSES:
        if str(merged.get(key) or "").lower() == "done":
            updates[key] = "ready"
            merged[key] = "ready"

    warnings = list(merged.get("warnings") or [])
    warning_reasons = dict(merged.get("warning_reasons") or {})

    deliverable_ready = is_deliverable_ready(task or {}, updates)
    if deliverable_ready and str(merged.get("dub_status") or "").lower() == "failed":
        if "dub_failed" not in warnings:
            warnings.append("dub_failed")
        warning_reasons.setdefault(
            "dub_failed",
            {"code": "dub_failed", "message": "Dub step failed but deliverable is ready"},
        )

    if str((task or {}).get("status") or "").lower() == "ready" and deliverable_ready:
        updates["status"] = "ready"
        if warnings:
            updates["warnings"] = warnings
        if warning_reasons:
            updates["warning_reasons"] = warning_reasons
        return updates

    if deliverable_ready:
        updates["status"] = "ready"
        if warnings:
            updates["warnings"] = warnings
        if warning_reasons:
            updates["warning_reasons"] = warning_reasons
        return updates

    failed = bool(merged.get("error_reason"))
    if not failed:
        for key in FAILED_SUBSTATUSES:
            if str(merged.get(key) or "").lower() == "failed":
                failed = True
                break

    if failed:
        updates["status"] = "failed"
        if warnings:
            updates["warnings"] = warnings
        if warning_reasons:
            updates["warning_reasons"] = warning_reasons
        return updates

    updates["status"] = "running"
    if warnings:
        updates["warnings"] = warnings
    if warning_reasons:
        updates["warning_reasons"] = warning_reasons
    return updates
