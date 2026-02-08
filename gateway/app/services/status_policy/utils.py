from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import get_status_policy

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
    del kind
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

    failed = bool(merged.get("error_reason"))
    if not failed:
        for key in FAILED_SUBSTATUSES:
            if str(merged.get(key) or "").lower() == "failed":
                failed = True
                break

    if failed:
        updates["status"] = "failed"
        return updates

    if is_deliverable_ready(task or {}, updates):
        updates["status"] = "ready"
        return updates

    updates["status"] = "running"
    return updates


def policy_upsert(
    repo: Any,
    task_id: str,
    task: Optional[Dict[str, Any]],
    updates: Dict[str, Any],
    *,
    step: str,
    force: bool = False,
) -> Dict[str, Any]:
    cur = (repo.get(task_id) or task or {})
    policy = get_status_policy(cur)

    filtered = policy.reconcile_after_step(
        cur,
        step=step,
        updates=dict(updates or {}),
        force=force,
    ) or {}

    if filtered:
        repo.upsert(task_id, filtered)
        return repo.get(task_id) or cur

    return cur
