from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


TRANSLATION_PENDING_STALE_AFTER_SECONDS = 15 * 60


def _parse_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _age_seconds(value: Any, now: datetime) -> float | None:
    parsed = _parse_dt(value)
    if parsed is None:
        return None
    return max(0.0, (now - parsed).total_seconds())


def hot_follow_translation_waiting_diagnostic(
    task: dict[str, Any] | None,
    *,
    now_fn: Callable[[], datetime] | None = None,
    stale_after_seconds: int = TRANSLATION_PENDING_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    """Read-only diagnostic for translation waiting state.

    This does not write or infer subtitle truth. It only classifies whether a
    pending translation wait appears active or stale for operator escalation.
    """
    task_obj = task if isinstance(task, dict) else {}
    now = (now_fn or (lambda: datetime.now(timezone.utc)))()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    target_reason = str(task_obj.get("target_subtitle_current_reason") or "").strip()
    helper_status = str(task_obj.get("subtitle_helper_status") or "").strip().lower()
    subtitles_status = str(task_obj.get("subtitles_status") or "").strip().lower()
    materialization_status = str(task_obj.get("target_subtitle_materialization_status") or "").strip().lower()
    waiting = bool(
        target_reason in {"target_subtitle_translation_incomplete", "waiting_for_target_subtitle_translation"}
        or helper_status in {"pending", "running", "processing", "helper_output_pending"}
        or materialization_status in {"pending", "running"}
    )
    active_markers = (
        "target_subtitle_materialization_started_at",
        "subtitle_translation_started_at",
        "subtitle_helper_started_at",
        "subtitle_helper_updated_at",
        "updated_at",
    )
    ages = {
        marker: _age_seconds(task_obj.get(marker), now)
        for marker in active_markers
        if _age_seconds(task_obj.get(marker), now) is not None
    }
    recent = any(age <= stale_after_seconds for age in ages.values())
    running = subtitles_status in {"running", "processing"} or materialization_status == "running" or helper_status in {"running", "processing"}
    active = bool(waiting and (running or recent))
    stale = bool(waiting and not active)
    if active:
        classification = "active_translation_running"
    elif stale:
        classification = "stale_pending_without_progress"
    else:
        classification = "not_waiting_for_translation"
    return {
        "kind": "translation_waiting_diagnostic",
        "waiting": waiting,
        "classification": classification,
        "active": active,
        "stale": stale,
        "reason": target_reason or None,
        "subtitles_status": subtitles_status or None,
        "helper_status": helper_status or None,
        "materialization_status": materialization_status or None,
        "stale_after_seconds": int(stale_after_seconds),
        "marker_ages_seconds": {key: int(value) for key, value in ages.items()},
    }
