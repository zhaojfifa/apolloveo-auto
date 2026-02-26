from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


FAILED_SUBSTATUSES = (
    "subtitles_status",
    "dub_status",
    "scenes_status",
    "pack_status",
    "publish_status",
)


STEP_RULES: dict[str, dict[str, Any]] = {
    "subtitles": {
        "status": "subtitles_status",
        "keys": ("origin_srt_path", "mm_srt_path"),
        "errors": ("subtitles_error",),
        "started": "subtitles_started_at",
        "finished": "subtitles_finished_at",
        "elapsed": "subtitles_elapsed_ms",
    },
    "dub": {
        "status": "dub_status",
        "keys": ("mm_audio_key", "mm_audio_path"),
        "errors": ("dub_error",),
        "started": "dub_started_at",
        "finished": "dub_finished_at",
        "elapsed": "dub_elapsed_ms",
    },
    "scenes": {
        "status": "scenes_status",
        "keys": ("scenes_key", "scenes_pack_key", "scenes_path"),
        "errors": ("scenes_error", "scenes_error_message"),
        "started": "scenes_started_at",
        "finished": "scenes_finished_at",
        "elapsed": "scenes_elapsed_ms",
    },
    "pack": {
        "status": "pack_status",
        "keys": ("pack_key", "pack_path"),
        "errors": ("pack_error",),
        "started": "pack_started_at",
        "finished": "pack_finished_at",
        "elapsed": "pack_elapsed_ms",
    },
    "compose": {
        "status": "compose_status",
        "keys": ("compose_key", "final_video_key", "final_video_path"),
        "errors": ("compose_error", "compose_error_message"),
        "started": "compose_started_at",
        "finished": "compose_finished_at",
        "elapsed": "compose_elapsed_ms",
    },
}

STATUS_RANK = {"idle": 0, "queued": 1, "running": 2, "done": 3}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_step_status(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in {"done", "ready", "success", "completed"}:
        return "done"
    if v in {"failed", "error"}:
        return "failed"
    if v in {"running", "processing"}:
        return "running"
    if v in {"queued"}:
        return "queued"
    if v in {"idle", "pending", "none", "null", ""}:
        return "idle"
    return "idle"


def _any_truthy(merged: dict[str, Any], names: tuple[str, ...]) -> bool:
    for name in names:
        if merged.get(name):
            return True
    return False


def _status_can_downgrade(cur: str, nxt: str) -> bool:
    if cur == "done" and nxt != "done":
        return True
    if cur == "failed" and nxt != "failed":
        return True
    if cur in STATUS_RANK and nxt in STATUS_RANK and STATUS_RANK[nxt] < STATUS_RANK[cur]:
        return True
    return False


def apply_monotonic_step_policy(task: dict | None, updates: dict | None, *, force: bool = False) -> Dict[str, Any]:
    updates = dict(updates or {})
    cur = dict(task or {})
    merged = dict(cur)
    merged.update(updates)

    for rule in STEP_RULES.values():
        status_key = rule["status"]
        started_key = rule["started"]
        finished_key = rule["finished"]
        elapsed_key = rule["elapsed"]
        key_exists = _any_truthy(merged, rule["keys"])
        error_exists = _any_truthy(merged, rule["errors"])

        cur_status = _normalize_step_status(cur.get(status_key))
        next_status = _normalize_step_status(merged.get(status_key))
        if not force and _status_can_downgrade(cur_status, next_status):
            next_status = cur_status

        # Hard constraints: key wins done, error wins failed.
        if key_exists:
            next_status = "done"
        if error_exists:
            next_status = "failed"

        updates[status_key] = next_status

        if next_status == "running":
            if not merged.get(started_key):
                updates[started_key] = _now_iso()
        elif next_status in {"done", "failed"}:
            if not merged.get(finished_key):
                updates[finished_key] = _now_iso()
            started = merged.get(started_key) or updates.get(started_key)
            finished = merged.get(finished_key) or updates.get(finished_key)
            if started and finished and not merged.get(elapsed_key):
                try:
                    st = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
                    ed = datetime.fromisoformat(str(finished).replace("Z", "+00:00"))
                    updates[elapsed_key] = max(0, int((ed - st).total_seconds() * 1000))
                except Exception:
                    pass

        merged[status_key] = updates.get(status_key, merged.get(status_key))
        if started_key in updates:
            merged[started_key] = updates[started_key]
        if finished_key in updates:
            merged[finished_key] = updates[finished_key]
        if elapsed_key in updates:
            merged[elapsed_key] = updates[elapsed_key]

    return updates


def normalize_task_steps_for_read(task: dict | None) -> Dict[str, Any]:
    merged = dict(task or {})
    out: dict[str, Any] = {}

    for rule in STEP_RULES.values():
        status_key = rule["status"]
        key_exists = _any_truthy(merged, rule["keys"])
        error_exists = _any_truthy(merged, rule["errors"])
        status = _normalize_step_status(merged.get(status_key))
        if key_exists:
            status = "done"
        if error_exists:
            status = "failed"
        if status == "idle":
            if merged.get(rule["finished"]):
                status = "done"
            elif merged.get(rule["started"]):
                status = "running"
        out[status_key] = status
        if status in {"done", "failed"} and not merged.get(rule["finished"]):
            out[rule["finished"]] = _now_iso()

    return out


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

    # Normalize top-level status wording only.
    if str(merged.get("status") or "").lower() == "done":
        updates["status"] = "ready"
        merged["status"] = "ready"

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
