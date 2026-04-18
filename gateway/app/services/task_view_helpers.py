"""Task view helpers: data accessors, deliverable URLs, publish-hub payload,
task-to-detail conversion, and supporting utilities.

Extracted from tasks.py as part of Phase 1.3 Port Merge.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException

from gateway.app.config import get_settings
from gateway.app.schemas import TaskDetail
from gateway.app.services.task_semantics import project_task_fact_status
from gateway.app.services.artifact_storage import (
    get_download_url,
    get_object_bytes,
    object_exists,
    object_head,
)
from gateway.app.services.media_validation import (
    MIN_AUDIO_BYTES,
    MIN_VIDEO_BYTES,
    deliver_key,
    media_meta_from_head,
)
from gateway.app.services.hot_follow_language_profiles import (
    get_hot_follow_language_profile,
)
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Core task-field accessors
# ═══════════════════════════════════════════════════════════════════════════════

def task_value(task: dict, field: str) -> Optional[str]:
    """Safe accessor: look up *field* in *task* dict (or its ``deliverables`` sub-dict)."""
    if isinstance(task, dict):
        value = task.get(field)
        if value is None:
            deliverables = task.get("deliverables")
            if isinstance(deliverables, dict):
                value = deliverables.get(field)
        return value
    return getattr(task, field, None)


def task_key(task: dict, field: str) -> Optional[str]:
    """Return ``str(value)`` for a storage-key field, or ``None``."""
    value = task_value(task, field)
    return str(value) if value else None


def task_endpoint(task_id: str, kind: str) -> Optional[str]:
    """Return the open/preview URL path for the given deliverable *kind*."""
    safe_id = str(task_id)
    if kind == "raw":
        return f"/v1/tasks/{safe_id}/raw"
    if kind == "origin":
        return f"/v1/tasks/{safe_id}/subs_origin"
    if kind == "mm":
        return f"/v1/tasks/{safe_id}/subs_mm"
    if kind == "mm_txt":
        return f"/v1/tasks/{safe_id}/mm_txt"
    if kind == "audio":
        return f"/v1/tasks/{safe_id}/audio_mm"
    if kind == "pack":
        return f"/v1/tasks/{safe_id}/pack"
    if kind == "scenes":
        return f"/v1/tasks/{safe_id}/scenes"
    if kind == "final":
        return f"/v1/tasks/{safe_id}/final"
    if kind == "publish_bundle":
        return f"/v1/tasks/{safe_id}/publish_bundle"
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Auth / signed-URL helpers (needed by _deliverable_url & _publish_hub_payload)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_op_access_key() -> Optional[str]:
    key = (os.getenv("OP_ACCESS_KEY") or "").strip()
    return key or None


def op_gate_enabled() -> bool:
    return bool(_get_op_access_key())


def _op_sign(task_id: str, kind: str, exp: int) -> str:
    secret = _get_op_access_key()
    if not secret:
        return ""
    msg = f"{task_id}:{kind}:{exp}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def signed_op_url(task_id: str, kind: str) -> str:
    exp = int(time.time()) + 86400
    sig = _op_sign(task_id, kind, exp)
    base = f"/op/dl/{task_id}?kind={kind}&exp={exp}"
    return f"{base}&sig={sig}" if sig else base


def download_code(task_id: str) -> str:
    return str(task_id).upper()[:6]


# ═══════════════════════════════════════════════════════════════════════════════
# Text / URL utilities
# ═══════════════════════════════════════════════════════════════════════════════

def extract_first_http_url(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"https?://\S+", text)
    return match.group(0) if match else None


def coerce_datetime(value) -> datetime:
    """Best-effort convert *value* to a timezone-aware ``datetime``."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return datetime.now(timezone.utc)
        if s.isdigit():
            return datetime.fromtimestamp(int(s), tz=timezone.utc)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except Exception:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


def model_allowed_fields(model_cls) -> set[str]:
    if hasattr(model_cls, "model_fields"):
        return set(model_cls.model_fields.keys())
    if hasattr(model_cls, "__fields__"):
        return set(model_cls.__fields__.keys())
    return set()


def normalize_selected_tool_ids(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            decoded = json.loads(text)
        except Exception:
            decoded = None
        if isinstance(decoded, list):
            return [str(v) for v in decoded if str(v).strip()]
        return [v.strip() for v in text.split(",") if v.strip()]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# SRT / translation QA
# ═══════════════════════════════════════════════════════════════════════════════

def count_srt_cues(srt_text: str | None) -> int:
    text = str(srt_text or "")
    if not text.strip():
        return 0
    return len(
        re.findall(
            r"(?m)^\s*\d+\s*\r?\n\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}",
            text,
        )
    )


def build_translation_qa_summary(
    origin_srt_text: str | None, translated_srt_text: str | None
) -> dict:
    source_count = count_srt_cues(origin_srt_text)
    translated_count = count_srt_cues(translated_srt_text)
    return {
        "source_count": source_count,
        "translated_count": translated_count,
        "has_mismatch": source_count != translated_count,
    }


def build_workbench_debug_payload(
    show_debug: bool, scene_outputs: list[dict] | None, compose_last: dict | None
) -> dict:
    if not show_debug:
        return {}
    compose = compose_last or {}
    return {
        "scene_outputs": list(scene_outputs or []),
        "compose_last_ffmpeg_cmd": compose.get("ffmpeg_cmd"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Status helpers
# ═══════════════════════════════════════════════════════════════════════════════

def scenes_status_from_ssot(task: dict) -> str:
    if task_key(task, "scenes_key"):
        return "done"
    if task_value(task, "scenes_error"):
        return "failed"
    started_at = task_value(task, "scenes_started_at")
    finished_at = task_value(task, "scenes_finished_at")
    if started_at and not finished_at:
        return "running"
    events = task.get("events") if isinstance(task, dict) else None
    if isinstance(events, list):
        for ev in reversed(events):
            if not isinstance(ev, dict):
                continue
            if str(ev.get("channel") or "").lower() != "scenes":
                continue
            code = str(ev.get("code") or "").upper()
            if code in {"SCENES_RUN_DONE"}:
                return "done"
            if code in {"SCENES_RUN_FAIL", "SCENES_RUN_FAILED"}:
                return "failed"
            if code in {"SCENES_ENQUEUE", "SCENES_RUN_START"}:
                return "running"
            break
    return "pending"


def derive_status(task: dict) -> str:
    projected = project_task_fact_status(task)
    if projected != "unknown":
        return projected
    raw_status = str(task.get("status") or "").strip().lower()
    return raw_status or "unknown"


def _compose_done_like(status: Any) -> bool:
    return str(status or "").strip().lower() in {
        "done",
        "ready",
        "success",
        "completed",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Compose error
# ═══════════════════════════════════════════════════════════════════════════════

def compose_error_parts(task: dict) -> tuple[str | None, str | None]:
    reason_field = task.get("compose_error_reason")
    raw = task.get("compose_error")
    if not reason_field and not raw:
        return (None, None)
    if isinstance(raw, dict):
        reason = raw.get("reason")
        message = raw.get("message")
        resolved_reason = (
            str(reason) if reason else (str(reason_field) if reason_field else None)
        )
        resolved_message = str(message) if message else None
        return (resolved_reason, resolved_message)
    text = str(raw).strip() if raw is not None else ""
    if not text:
        return (None, None)
    return (str(reason_field) if reason_field else "compose_failed", text)


# ═══════════════════════════════════════════════════════════════════════════════
# Deliverable URLs
# ═══════════════════════════════════════════════════════════════════════════════

def deliverable_url(task_id: str, task: dict, kind: str) -> Optional[str]:
    if kind == "raw_video":
        key = task_key(task, "raw_path")
        return signed_op_url(task_id, "raw") if key and object_exists(str(key)) else None
    if kind == "final_mp4":
        key = task_key(task, "final_video_key") or task_key(task, "final_video_path")
        return signed_op_url(task_id, "final_mp4") if key and object_exists(str(key)) else None
    if kind == "pack_zip":
        pack_type = task_value(task, "pack_type")
        pack_key = task_value(task, "pack_key") or task_value(task, "pack_path")
        if pack_type == "capcut_v18" and pack_key and object_exists(str(pack_key)):
            return signed_op_url(task_id, "pack")
        if pack_key and object_exists(str(pack_key)):
            return signed_op_url(task_id, "pack")
        return None
    if kind == "scenes_zip":
        scenes_key = task_value(task, "scenes_pack_key") or task_value(task, "scenes_key")
        scenes_path = task_value(task, "scenes_path")
        scenes_status = str(
            task_value(task, "scenes_pack_status")
            or task_value(task, "scenes_status")
            or ""
        ).lower()
        if scenes_key and object_exists(str(scenes_key)):
            return signed_op_url(task_id, "scenes")
        if scenes_path and scenes_status == "ready":
            return signed_op_url(task_id, "scenes")
        return None
    if kind == "origin_srt":
        key = task_key(task, "origin_srt_path")
        return signed_op_url(task_id, "origin_srt") if key and object_exists(key) else None
    if kind == "mm_srt":
        key = task_key(task, "mm_srt_path")
        return signed_op_url(task_id, "mm_srt") if key and object_exists(key) else None
    if kind == "mm_txt":
        mm_key = task_key(task, "mm_srt_path")
        if not mm_key:
            return None
        txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
        return signed_op_url(task_id, "mm_txt") if object_exists(txt_key) else None
    if kind == "mm_audio":
        if str(task.get("kind") or "").strip().lower() == "hot_follow":
            from gateway.app.services.voice_state import hf_current_voiceover_asset

            asset = hf_current_voiceover_asset(task_id, task, get_settings())
            key = asset.get("key")
        else:
            key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
        return signed_op_url(task_id, "mm_audio") if key and object_exists(str(key)) else None
    if kind == "edit_bundle_zip":
        return signed_op_url(task_id, "publish_bundle")
    return None


def deliverable_open_url(task_id: str, task: dict, kind: str) -> Optional[str]:
    profile = get_hot_follow_language_profile(
        task.get("target_lang") or task.get("content_lang") or "mm"
    )
    if kind == "final_mp4":
        key = task_key(task, "final_video_key") or task_key(task, "final_video_path")
        return task_endpoint(task_id, "final") if key and object_exists(str(key)) else None
    if kind == "pack_zip":
        pack_key = task_value(task, "pack_key") or task_value(task, "pack_path")
        return task_endpoint(task_id, "pack") if pack_key and object_exists(str(pack_key)) else None
    if kind == "scenes_zip":
        scenes_key = task_value(task, "scenes_pack_key") or task_value(task, "scenes_key")
        return task_endpoint(task_id, "scenes") if scenes_key and object_exists(str(scenes_key)) else None
    if kind == "origin_srt":
        key = task_key(task, "origin_srt_path")
        return task_endpoint(task_id, "origin") if key and object_exists(key) else None
    if kind == "mm_srt":
        key = task_key(task, "mm_srt_path")
        return task_endpoint(task_id, "mm") if key and object_exists(key) else None
    if kind == "mm_txt":
        mm_key = task_key(task, "mm_srt_path")
        if not mm_key:
            return None
        txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
        return task_endpoint(task_id, "mm_txt") if object_exists(txt_key) else None
    if kind == "mm_audio":
        if str(task.get("kind") or "").strip().lower() == "hot_follow":
            from gateway.app.services.voice_state import hf_current_voiceover_asset

            asset = hf_current_voiceover_asset(task_id, task, get_settings())
            key = asset.get("key")
        else:
            key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
        return task_endpoint(task_id, "audio") if key and object_exists(str(key)) else None
    if kind == "raw_video":
        key = task_key(task, "raw_path")
        return task_endpoint(task_id, "raw") if key and object_exists(str(key)) else None
    if kind == "publish_bundle":
        pack_key = task_value(task, "pack_key") or task_value(task, "pack_path")
        return task_endpoint(task_id, "publish_bundle") if pack_key and object_exists(str(pack_key)) else None
    if profile and kind == "subtitle_txt":
        key = task_key(task, "mm_srt_path")
        if not key:
            return None
        txt_key = key[:-4] + ".txt" if key.endswith(".srt") else f"{key}.txt"
        return task_endpoint(task_id, "mm_txt") if object_exists(txt_key) else None
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Composed-state aggregation
# ═══════════════════════════════════════════════════════════════════════════════

def _coerce_dt(value: Any) -> datetime | None:
    """Parse an ISO timestamp string or datetime into a UTC-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def compute_final_staleness(task: dict, final_exists: bool, compose_done: bool) -> str | None:
    """Return a stale-reason string if the final video predates current inputs, else None.

    Staleness is detected via snapshot fields written by compose (preferred) and
    falls back to timestamp comparison when snapshots are absent (legacy tasks).

    Returns one of: ``None``, ``"final_stale_after_dub"``,
    ``"final_stale_after_subtitles"``.
    """
    if not final_exists or not compose_done:
        return None

    # ── audio staleness ────────────────────────────────────────────────────
    audio_stale = False
    current_audio_sha = str(task.get("audio_sha256") or "").strip() or None
    composed_audio_sha = str(task.get("final_source_audio_sha256") or "").strip() or None
    current_dub_at = str(task.get("dub_generated_at") or "").strip() or None
    composed_dub_at = str(task.get("final_source_dub_generated_at") or "").strip() or None
    current_source_audio_policy = source_audio_policy_from_task(task)
    composed_source_audio_policy = str(task.get("final_source_audio_policy") or "").strip().lower() or None
    compose_finished_at = str(task.get("compose_last_finished_at") or task.get("final_updated_at") or "").strip() or None

    if composed_source_audio_policy and composed_source_audio_policy != current_source_audio_policy:
        audio_stale = True
    if not audio_stale and not composed_source_audio_policy and current_source_audio_policy != "mute":
        audio_stale = True
    if composed_audio_sha and current_audio_sha and composed_audio_sha != current_audio_sha:
        audio_stale = True
    if not audio_stale and composed_dub_at and current_dub_at and composed_dub_at != current_dub_at:
        audio_stale = True
    if not audio_stale and current_dub_at and compose_finished_at:
        _dub_dt = _coerce_dt(current_dub_at)
        _compose_dt = _coerce_dt(compose_finished_at)
        if _dub_dt is not None and _compose_dt is not None:
            audio_stale = _dub_dt > _compose_dt

    # ── subtitle staleness ─────────────────────────────────────────────────
    subtitle_stale = False
    current_sub_hash = str(task.get("subtitles_content_hash") or "").strip() or None
    composed_sub_hash = str(task.get("final_source_subtitles_content_hash") or "").strip() or None
    current_sub_at = str(task.get("subtitles_override_updated_at") or "").strip() or None
    composed_sub_at = str(task.get("final_source_subtitle_updated_at") or "").strip() or None

    if composed_sub_hash and current_sub_hash and composed_sub_hash != current_sub_hash:
        subtitle_stale = True
    if not subtitle_stale and composed_sub_at and current_sub_at and composed_sub_at != current_sub_at:
        subtitle_stale = True
    if not subtitle_stale and current_sub_at and compose_finished_at:
        _sub_dt = _coerce_dt(current_sub_at)
        _compose_dt = _coerce_dt(compose_finished_at)
        if _sub_dt is not None and _compose_dt is not None:
            subtitle_stale = _sub_dt > _compose_dt

    if audio_stale:
        return "final_stale_after_dub"
    if subtitle_stale:
        return "final_stale_after_subtitles"
    return None


def compute_composed_state(task: dict, task_id: str) -> dict[str, Any]:
    from gateway.app.services.voice_state import collect_voice_execution_state

    final_key = (
        task_key(task, "final_video_key")
        or task_key(task, "final_video_path")
        or deliver_key(task_id, "final.mp4")
    )
    final_meta = (
        object_head(str(final_key))
        if final_key and object_exists(str(final_key))
        else None
    )
    final_size, final_ctype = media_meta_from_head(final_meta)
    final_asset_version = (
        task.get("final_asset_version")
        or (final_meta.get("etag") if isinstance(final_meta, dict) else None)
        or task.get("final_video_sha256")
        or None
    )
    final_exists = bool(
        final_key and object_exists(str(final_key)) and int(final_size or 0) > 0
    )
    raw_key = task_key(task, "raw_path")
    raw_exists = bool(raw_key and object_exists(str(raw_key)))
    voice_state = collect_voice_execution_state(task, get_settings())
    if str(task.get("kind") or "").strip().lower() == "hot_follow":
        voice_exists = bool(voice_state.get("dub_current") and voice_state.get("voiceover_url"))
    else:
        voice_key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
        voice_exists = bool(voice_key and object_exists(str(voice_key)))
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    no_dub = pipeline_config.get("no_dub") == "true"
    no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip().lower()
    no_dub_compose_allowed = no_dub and no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}
    compose_status = str(task.get("compose_status") or "").lower()
    compose_last_status = str(
        task.get("compose_last_status") or compose_status
    ).lower()
    compose_done = compose_last_status in {"done", "ready", "success", "completed"}
    compose_error_reason, compose_error_message = compose_error_parts(task)

    final_stale_reason = compute_final_staleness(task, final_exists, compose_done)
    final_fresh = final_exists and compose_done and final_stale_reason is None

    composed_ready = bool(
        final_fresh
        and compose_error_reason is None
        and (bool(voice_state.get("audio_ready")) or no_dub_compose_allowed)
    )
    if composed_ready:
        composed_reason = "ready"
    elif final_stale_reason:
        composed_reason = final_stale_reason
    elif not raw_exists:
        composed_reason = "missing_raw"
    elif not voice_exists and not no_dub_compose_allowed:
        composed_reason = "missing_voiceover"
    elif not voice_state.get("audio_ready") and not no_dub_compose_allowed:
        composed_reason = str(
            voice_state.get("audio_ready_reason") or "audio_not_ready"
        )
    elif compose_status in {"running", "processing", "queued"}:
        composed_reason = "compose_in_progress"
    elif compose_error_reason in {"subtitles_missing", "font_missing"}:
        composed_reason = compose_error_reason
    elif compose_error_reason or compose_status in {"failed", "error"}:
        composed_reason = "compose_failed"
    else:
        composed_reason = "final_missing"

    # historical_final is only exposed when it is acting as fallback/reference.
    # If current final is fresh and valid, do not mirror the same object into
    # historical_final by default.
    historical_exposed = bool(final_exists and not final_fresh)
    historical_final_info = {
        "exists": historical_exposed,
        "key": str(final_key) if (historical_exposed and final_key) else None,
        "size_bytes": int(final_size) if final_size is not None else None,
        "duration_ms": int(task.get("final_duration_ms"))
        if task.get("final_duration_ms") is not None
        else None,
        "asset_version": str(final_asset_version) if (historical_exposed and final_asset_version) else None,
        "updated_at": task.get("final_updated_at") if historical_exposed else None,
        "content_type": task.get("final_mime") or final_ctype or "video/mp4",
        "url": task_endpoint(task_id, "final")
        if historical_exposed and int(final_size or 0) >= MIN_VIDEO_BYTES
        else None,
    }
    final_info = {
        "exists": final_fresh,
        "fresh": final_fresh,
        "stale_reason": final_stale_reason,
        "key": str(final_key) if (final_fresh and final_key) else None,
        "size_bytes": int(final_size) if final_size is not None else None,
        "duration_ms": int(task.get("final_duration_ms"))
        if task.get("final_duration_ms") is not None
        else None,
        "asset_version": str(final_asset_version) if (final_fresh and final_asset_version) else None,
        "updated_at": task.get("final_updated_at") if final_fresh else None,
        "content_type": task.get("final_mime") or final_ctype or "video/mp4",
        "url": task_endpoint(task_id, "final")
        if final_fresh and int(final_size or 0) >= MIN_VIDEO_BYTES
        else None,
    }
    return {
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final": final_info,
        "historical_final": historical_final_info,
        "final_stale_reason": final_stale_reason,
        "final_fresh": final_fresh,
        "compose_error_reason": compose_error_reason,
        "compose_error_message": compose_error_message,
        "raw_exists": raw_exists,
        "voice_exists": voice_exists,
        "audio_ready": bool(voice_state.get("audio_ready")),
        "audio_ready_reason": voice_state.get("audio_ready_reason"),
    }


def scene_pack_info(task: dict, task_id: str) -> dict[str, Any]:
    key = (
        task_key(task, "scenes_key")
        or task_key(task, "scenes_pack_key")
        or f"deliver/scenes/{task_id}/scenes.zip"
    )
    scenes_key_ready = bool(task_key(task, "scenes_key"))
    exists = bool(key and object_exists(str(key)))
    if scenes_key_ready:
        exists = True
    meta = object_head(str(key)) if exists else None
    size_bytes, _ = media_meta_from_head(meta)
    status_raw = str(
        task.get("scenes_pack_last_status")
        or task.get("scenes_pack_status")
        or task.get("scenes_status")
        or ""
    ).lower()
    if status_raw in {"ready", "done", "success", "completed"}:
        status = "done"
    elif status_raw in {"running", "processing", "queued"}:
        status = "running"
    elif status_raw in {"failed", "error"}:
        status = "failed"
    else:
        status = "pending"
    if scenes_key_ready:
        status = "done"
    elif exists and status != "running":
        status = "done"
    return {
        "exists": exists,
        "key": str(key) if key else None,
        "url": task_endpoint(task_id, "scenes") if exists else None,
        "size_bytes": int(size_bytes) if size_bytes is not None else None,
        "asset_version": (
            meta.get("etag") if isinstance(meta, dict) else None
        )
        or task.get("scenes_pack_asset_version"),
        "status": status,
        "started_at": task.get("scenes_pack_last_started_at"),
        "finished_at": task.get("scenes_pack_last_finished_at"),
        "error": task.get("scenes_pack_error") or task.get("scenes_error"),
        "error_reason": task.get("scenes_pack_error_reason"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Resolve hub final URL
# ═══════════════════════════════════════════════════════════════════════════════

def _deliverables_final_url(deliverables: Any) -> str | None:
    if isinstance(deliverables, dict):
        final_item = deliverables.get("final_mp4")
        if isinstance(final_item, dict):
            url = final_item.get("open_url") or final_item.get("url")
            if url:
                return str(url)
    if isinstance(deliverables, list):
        for item in deliverables:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip().lower()
            key = str(item.get("key") or "").strip().lower()
            label = str(
                item.get("label") or item.get("title") or ""
            ).strip().lower()
            if (
                kind == "final"
                or key.endswith("final.mp4")
                or "final video" in label
                or label == "final.mp4"
            ):
                url = item.get("open_url") or item.get("url")
                if url:
                    return str(url)
    return None


def resolve_hub_final_url(
    task_id: str, hub: dict[str, Any] | None = None
) -> str | None:
    payload = hub or {}
    media = (
        payload.get("media") if isinstance(payload.get("media"), dict) else {}
    )
    extra = (
        payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    )
    url = (
        _deliverables_final_url(payload.get("deliverables"))
        or media.get("final_url")
        or media.get("final_video_url")
        or payload.get("final_url")
        or payload.get("final_video_url")
        or extra.get("final_video_url")
        or None
    )
    if url:
        return str(url)
    final_info = (
        payload.get("final") if isinstance(payload.get("final"), dict) else {}
    )
    if bool(final_info.get("exists")):
        return task_endpoint(task_id, "final")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Compose-done backfill
# ═══════════════════════════════════════════════════════════════════════════════

def backfill_compose_done_if_final_ready(
    repo, task_id: str, task: dict, composed_ready: bool
) -> bool:
    if not composed_ready:
        return False
    compose_status = str(task.get("compose_status") or "").strip().lower()
    compose_last_status = str(
        task.get("compose_last_status") or ""
    ).strip().lower()
    pipeline_compose_status = ""
    pipeline = task.get("pipeline")
    if isinstance(pipeline, dict):
        compose_node = pipeline.get("compose")
        if isinstance(compose_node, dict):
            pipeline_compose_status = str(
                compose_node.get("status") or ""
            ).strip().lower()
    if (
        _compose_done_like(compose_status)
        and _compose_done_like(compose_last_status or compose_status)
        and (
            not pipeline_compose_status
            or _compose_done_like(pipeline_compose_status)
        )
    ):
        return False
    now = datetime.now(timezone.utc).isoformat()
    updates: dict[str, Any] = {
        "compose_status": "done",
        "compose_last_status": "done",
        "compose_error": None,
        "compose_error_reason": None,
        "compose_last_error": None,
        "compose_last_finished_at": now,
        "updated_at": now,
    }
    if not task.get("compose_last_started_at"):
        updates["compose_last_started_at"] = now
    task_status = str(task.get("status") or "").strip().lower()
    if task_status in {
        "",
        "pending",
        "processing",
        "running",
        "queued",
        "failed",
        "error",
    }:
        updates["status"] = "ready"
    if isinstance(pipeline, dict):
        patched_pipeline = dict(pipeline)
        compose_node = patched_pipeline.get("compose")
        compose_dict = (
            dict(compose_node) if isinstance(compose_node, dict) else {}
        )
        compose_dict["status"] = "done"
        compose_dict["state"] = "done"
        compose_dict["updated_at"] = now
        patched_pipeline["compose"] = compose_dict
        updates["pipeline"] = patched_pipeline
    policy_upsert(
        repo, task_id, None, updates, step="task_view_helpers.backfill"
    )
    logger.info(
        "hot_follow_compose_backfill_done", extra={"task_id": task_id}
    )
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Publish-hub payload
# ═══════════════════════════════════════════════════════════════════════════════

def _read_mm_txt_from_task(task: dict) -> str:
    mm_key = task_key(task, "mm_srt_path")
    if not mm_key:
        return ""
    txt_key = (
        mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
    )
    if not object_exists(txt_key):
        return ""
    data = get_object_bytes(txt_key)
    if not data:
        return ""
    try:
        return data.decode("utf-8").strip()
    except UnicodeDecodeError:
        return data.decode(errors="ignore").strip()


def _publish_sop_markdown() -> str:
    return (
        "# Publish SOP\n"
        "1) Download the edit bundle (pack.zip).\n"
        "2) Import into CapCut and finish edits.\n"
        "3) Copy caption and hashtags from Copy Bundle.\n"
        "4) Publish manually (publish bundle in v2.0).\n"
    )


def _build_copy_bundle(task: dict) -> dict[str, str]:
    caption = _read_mm_txt_from_task(task) or (task.get("title") or "")
    return {
        "caption": caption.strip(),
        "hashtags": "",
        "comment_cta": "",
        "link_text": task.get("publish_url") or "",
        "publish_time_suggestion": "",
    }


def publish_hub_payload(task: dict) -> dict[str, object]:
    """Build the full publish-hub response dict for *task*."""
    task_id = str(task_value(task, "task_id") or task_value(task, "id") or "")
    composed = compute_composed_state(task, task_id)
    scene_pack = scene_pack_info(task, task_id)

    deliverables = {}
    for key, label in (
        ("pack_zip", "pack.zip"),
        ("scenes_zip", "scenes.zip"),
        ("origin_srt", "origin.srt"),
        ("mm_srt", "mm.srt"),
        ("mm_txt", "mm.txt"),
        ("mm_audio", "mm_audio"),
        ("edit_bundle_zip", "scenes_bundle.zip"),
    ):
        download_url = deliverable_url(task_id, task, key)
        open_url = deliverable_open_url(task_id, task, key)
        if download_url or open_url:
            item = {"label": label, "url": download_url or open_url}
            item["download_url"] = download_url
            item["open_url"] = open_url
            if key == "edit_bundle_zip":
                item["artifact"] = "scenes_bundle"
                item["description"] = (
                    "Scenes package for re-editing / advanced workflow"
                )
            deliverables[key] = item
    scene_pack_pending_reason = None
    if not bool(scene_pack.get("exists")):
        if scene_pack.get("status") == "running":
            scene_pack_pending_reason = "scenes.running"
        elif scene_pack.get("status") == "failed":
            scene_pack_pending_reason = "scenes.failed"
        else:
            scene_pack_pending_reason = "scenes.not_ready"
    short_code = download_code(task_id)
    short_url = f"/d/{short_code}"
    final_payload_probe = {
        "deliverables": deliverables,
        "media": {
            "final_video_url": (composed.get("final") or {}).get("url"),
            "final_url": (composed.get("final") or {}).get("url"),
        },
        "final": composed.get("final") or {"exists": False},
        "compose_status": task.get("compose_status"),
        "compose_last_status": task.get("compose_last_status"),
    }
    final_preview_url = resolve_hub_final_url(task_id, final_payload_probe)
    composed_ready = bool(composed.get("composed_ready"))
    composed_reason = str(composed.get("composed_reason") or ("ready" if composed_ready else "not_ready"))
    if final_preview_url:
        final_item = dict(
            deliverables.get("final_mp4") or {"label": "final.mp4"}
        )
        final_item["download_url"] = deliverable_url(task_id, task, "final_mp4")
        final_item["open_url"] = final_preview_url
        final_item["url"] = final_preview_url
        deliverables["final_mp4"] = final_item

    return {
        "task_id": task_id,
        "gate_enabled": op_gate_enabled(),
        "media": {
            "final_video_url": final_preview_url,
            "final_url": final_preview_url,
        },
        "final_url": final_preview_url,
        "final_video_url": final_preview_url,
        "deliverables": deliverables,
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final": composed.get("final") or {"exists": False},
        "historical_final": composed.get("historical_final") or {"exists": False},
        "final_fresh": bool(composed.get("final_fresh")),
        "final_stale_reason": composed.get("final_stale_reason"),
        "scene_pack": scene_pack,
        "scene_pack_pending_reason": scene_pack_pending_reason,
        "scene_pack_action_url": f"/tasks/{task_id}",
        "copy_bundle": _build_copy_bundle(task),
        "download_code": short_code,
        "mobile": {
            "qr_target": short_url,
            "short_link": short_url,
            "short_url": short_url,
            "qr_url": short_url,
        },
        "sop_markdown": _publish_sop_markdown(),
        "archive": {
            "publish_provider": task.get("publish_provider") or "-",
            "publish_key": task.get("publish_key") or "-",
            "publish_status": task.get("publish_status") or "-",
            "publish_url": task.get("publish_url") or "-",
            "published_at": task.get("published_at") or "-",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Download-URL resolution (for _task_to_detail)
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_download_urls(task: dict) -> dict[str, Optional[str]]:
    task_id = str(task.get("task_id") or task.get("id"))
    raw_url = task_endpoint(task_id, "raw") if task.get("raw_path") else None
    origin_url = (
        task_endpoint(task_id, "origin") if task.get("origin_srt_path") else None
    )
    mm_url = task_endpoint(task_id, "mm") if task.get("mm_srt_path") else None
    audio_url = deliverable_open_url(task_id, task, "mm_audio")
    mm_txt_url = task_endpoint(task_id, "mm_txt") if mm_url else None
    pack_key = task.get("pack_key")
    pack_type = task.get("pack_type")
    pack_url = None
    if pack_type == "capcut_v18" and pack_key:
        pack_url = task_endpoint(task_id, "pack")
    elif task.get("pack_path"):
        pack_url = task_endpoint(task_id, "pack")
    scenes_url = (
        task_endpoint(task_id, "scenes")
        if task_value(task, "scenes_key")
        else None
    )
    raw_download_url = deliverable_url(task_id, task, "raw_video")
    origin_download_url = deliverable_url(task_id, task, "origin_srt")
    mm_download_url = deliverable_url(task_id, task, "mm_srt")
    mm_txt_download_url = deliverable_url(task_id, task, "mm_txt")
    audio_download_url = deliverable_url(task_id, task, "mm_audio")
    pack_download_url = deliverable_url(task_id, task, "pack_zip")
    scenes_download_url = deliverable_url(task_id, task, "scenes_zip")
    final_download_url = deliverable_url(task_id, task, "final_mp4")

    return {
        "raw_path": raw_url,
        "raw_download_url": raw_download_url,
        "origin_srt_path": origin_url,
        "origin_srt_download_url": origin_download_url,
        "mm_srt_path": mm_url,
        "mm_srt_download_url": mm_download_url,
        "mm_audio_path": audio_url,
        "mm_audio_download_url": audio_download_url,
        "mm_txt_path": mm_txt_url,
        "mm_txt_download_url": mm_txt_download_url,
        "pack_path": pack_url,
        "pack_download_url": pack_download_url,
        "scenes_path": scenes_url,
        "scenes_download_url": scenes_download_url,
        "final_download_url": final_download_url,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# task_to_detail — TaskDetail serializer
# ═══════════════════════════════════════════════════════════════════════════════

def task_to_detail(task: dict) -> TaskDetail:
    """Convert an internal task dict to a ``TaskDetail`` response model."""
    paths = resolve_download_urls(task)
    status = derive_status(task)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))

    payload = {
        "task_id": str(task.get("task_id") or task.get("id")),
        "title": task.get("title"),
        "kind": task.get("kind"),
        "source_url": str(task.get("source_url"))
        if task.get("source_url")
        else None,
        "source_link_url": extract_first_http_url(task.get("source_url")),
        "platform": task.get("platform"),
        "account_id": task.get("account_id"),
        "account_name": task.get("account_name"),
        "video_type": task.get("video_type"),
        "template": task.get("template"),
        "category_key": task.get("category_key") or "beauty",
        "content_lang": task.get("content_lang") or "my",
        "ui_lang": task.get("ui_lang") or "en",
        "style_preset": task.get("style_preset"),
        "face_swap_enabled": bool(task.get("face_swap_enabled")),
        "status": status,
        "last_step": task.get("last_step"),
        "duration_sec": task.get("duration_sec"),
        "thumb_url": task.get("thumb_url"),
        "raw_path": paths.get("raw_path"),
        "origin_srt_path": paths.get("origin_srt_path"),
        "mm_srt_path": paths.get("mm_srt_path"),
        "mm_audio_path": paths.get("mm_audio_path"),
        "mm_audio_key": task.get("mm_audio_key") if paths.get("mm_audio_path") else None,
        "pack_path": paths.get("pack_path"),
        "scenes_path": paths.get("scenes_path"),
        "scenes_status": scenes_status_from_ssot(task),
        "scenes_key": task.get("scenes_key"),
        "scenes_error": task.get("scenes_error"),
        "scenes_started_at": task.get("scenes_started_at"),
        "scenes_finished_at": task.get("scenes_finished_at"),
        "scenes_elapsed_ms": task.get("scenes_elapsed_ms"),
        "scenes_attempt": task.get("scenes_attempt"),
        "scenes_run_id": task.get("scenes_run_id"),
        "scenes_error_message": task.get("scenes_error_message"),
        "subtitles_status": task.get("subtitles_status"),
        "subtitles_key": task.get("subtitles_key"),
        "subtitles_error": task.get("subtitles_error"),
        "created_at": coerce_datetime(
            task.get("created_at") or task.get("created") or task.get("createdAt")
        ),
        "updated_at": coerce_datetime(
            task.get("updated_at") or task.get("updatedAt")
        ),
        "error_message": task.get("error_message"),
        "error_reason": task.get("error_reason"),
        "parse_provider": task.get("parse_provider"),
        "subtitles_provider": task.get("subtitles_provider"),
        "dub_provider": task.get("dub_provider"),
        "pack_provider": task.get("pack_provider"),
        "face_swap_provider": task.get("face_swap_provider"),
        "publish_status": task.get("publish_status"),
        "publish_provider": task.get("publish_provider"),
        "publish_key": task.get("publish_key"),
        "publish_url": task.get("publish_url"),
        "published_at": task.get("published_at"),
        "priority": task.get("priority"),
        "assignee": task.get("assignee"),
        "ops_notes": task.get("ops_notes"),
        "selected_tool_ids": normalize_selected_tool_ids(
            task.get("selected_tool_ids")
        ),
        "pipeline_config": pipeline_config,
        "no_dub": pipeline_config.get("no_dub") == "true",
        "dub_skip_reason": pipeline_config.get("dub_skip_reason"),
        "subtitle_track_kind": pipeline_config.get("subtitle_track_kind"),
    }

    allowed = model_allowed_fields(TaskDetail)
    payload = {k: v for k, v in payload.items() if k in allowed}
    return TaskDetail(**payload)
