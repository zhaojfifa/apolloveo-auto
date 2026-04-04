"""Voice / TTS execution state chain for Hot Follow.

Extracted from tasks.py as part of Phase 1.3 Port Merge.
All eight functions form a cohesive dependency closure:
  _collect_voice_execution_state
  └── _build_hot_follow_voice_options
  └── _voice_state_config
  └── _resolve_hot_follow_requested_voice
  └── _hot_follow_expected_provider
  └── _resolve_hot_follow_provider_voice
  └── _hf_persisted_audio_state
  └── _hf_audio_matches_expected
"""
from __future__ import annotations

from typing import Any, Optional

from gateway.app.config import get_settings
from gateway.app.services.hot_follow_language_profiles import get_hot_follow_language_profile
from gateway.app.services.tts_policy import (
    normalize_provider,
    normalize_target_lang,
    resolve_tts_voice,
)
from gateway.app.services.artifact_storage import object_exists, object_head
from gateway.app.services.media_validation import MIN_AUDIO_BYTES, media_meta_from_head
from gateway.app.utils.pipeline_config import parse_pipeline_config


# ── Helpers (alphabetical by call-chain depth) ───────────────────────────────

def hf_dub_matches_current_subtitle(task: dict) -> tuple[bool, str]:
    current_hash = str(task.get("subtitles_content_hash") or "").strip() or None
    dub_hash = str(task.get("dub_source_subtitles_content_hash") or "").strip() or None
    current_updated_at = str(task.get("subtitles_override_updated_at") or "").strip() or None
    dub_updated_at = str(task.get("dub_source_subtitle_updated_at") or "").strip() or None
    if current_hash and dub_hash and current_hash != dub_hash:
        return False, "dub_stale_after_subtitles"
    if current_updated_at and dub_updated_at and current_updated_at != dub_updated_at:
        return False, "dub_stale_after_subtitles"
    return True, "ready"


def hf_current_audio_fit_max_speed(task: dict) -> str:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    try:
        speed = float(pipeline_config.get("audio_fit_max_speed") or 1.25)
    except Exception:
        speed = 1.25
    speed = max(1.0, min(1.6, speed))
    return f"{speed:.2f}"


def hf_dub_matches_current_audio_config(task: dict) -> tuple[bool, str]:
    current_speed = hf_current_audio_fit_max_speed(task)
    dub_speed = str(task.get("dub_source_audio_fit_max_speed") or "").strip() or None
    if dub_speed and dub_speed != current_speed:
        return False, "dub_stale_after_speed_change"
    return True, "ready"

def build_hot_follow_voice_options(
    settings, target_lang: str | None
) -> dict[str, list[dict[str, str]]]:
    options: dict[str, list[dict[str, str]]] = {"azure_speech": [], "edge_tts": []}
    profile = get_hot_follow_language_profile(target_lang)
    labels = {
        "female": "女声",
        "male": "男声",
    }
    azure_map = getattr(settings, "azure_tts_voice_map", {}) or {}
    edge_map = getattr(settings, "edge_tts_voice_map", {}) or {}
    for voice_id in profile.allowed_voice_options:
        label = labels["female"] if "female" in voice_id else labels["male"]
        if azure_map.get(voice_id):
            options["azure_speech"].append({"value": voice_id, "label": label})
        if edge_map.get(voice_id):
            options["edge_tts"].append({"value": voice_id, "label": label})
    return options


def resolve_hot_follow_requested_voice(
    settings,
    task: dict,
    provider: str | None,
) -> str | None:
    config = dict(task.get("config") or {})
    requested = str(
        config.get("tts_requested_voice")
        or config.get("hot_follow_tts_requested_voice")
        or ""
    ).strip() or None
    if requested:
        return requested

    provider_norm = normalize_provider(provider)
    reverse_edge = {
        str(v).strip(): str(k).strip()
        for k, v in ((getattr(settings, "edge_tts_voice_map", {}) or {}).items())
        if str(k).strip() and str(v).strip()
    }
    reverse_azure = {
        str(v).strip(): str(k).strip()
        for k, v in ((getattr(settings, "azure_tts_voice_map", {}) or {}).items())
        if str(k).strip() and str(v).strip()
    }
    reverse_lovo = {}
    if getattr(settings, "lovo_speaker_mm_female_1", None):
        reverse_lovo[str(getattr(settings, "lovo_speaker_mm_female_1")).strip()] = "mm_female_1"
    if getattr(settings, "lovo_speaker_mm_male_1", None):
        reverse_lovo[str(getattr(settings, "lovo_speaker_mm_male_1")).strip()] = "mm_male_1"

    profile = get_hot_follow_language_profile(task.get("target_lang") or task.get("content_lang") or "mm")
    for candidate in (task.get("voice_id"), task.get("mm_audio_voice_id")):
        voice = str(candidate or "").strip() or None
        if not voice:
            continue
        if voice in profile.allowed_voice_options:
            return voice
        if provider_norm == "edge-tts" and voice in reverse_edge:
            return reverse_edge[voice]
        if provider_norm == "azure-speech" and voice in reverse_azure:
            return reverse_azure[voice]
        if provider_norm == "lovo" and voice in reverse_lovo:
            return reverse_lovo[voice]
    return None


def hot_follow_expected_provider(
    task: dict, requested_voice: str | None, default_provider: str | None
) -> str:
    provider = normalize_provider(default_provider)
    target_lang = normalize_target_lang(
        task.get("target_lang") or task.get("content_lang") or "mm"
    )
    if (
        str(task.get("kind") or "").strip().lower() == "hot_follow"
        and target_lang in {"my", "vi"}
    ):
        requested = str(requested_voice or "").strip()
        profile = get_hot_follow_language_profile(target_lang)
        if not requested or requested in profile.allowed_voice_options:
            return "azure-speech"
    return provider


def voice_state_config(task: dict) -> dict[str, Any]:
    config = dict(task.get("config") or {})
    return {
        "requested_voice": str(
            config.get("tts_requested_voice")
            or config.get("hot_follow_tts_requested_voice")
            or ""
        ).strip()
        or None,
        "resolved_voice": str(config.get("tts_resolved_voice") or "").strip() or None,
        "provider": normalize_provider(
            config.get("tts_provider")
            or task.get("dub_provider")
            or get_settings().dub_provider
        ),
        "request_token": str(config.get("tts_request_token") or "").strip() or None,
        "completed_token": str(config.get("tts_completed_token") or "").strip()
        or None,
    }


def resolve_hot_follow_provider_voice(
    settings,
    provider: str | None,
    requested_voice: str | None,
    *,
    task: dict | None = None,
) -> str | None:
    if isinstance(task, dict):
        actual_voice = str(task.get("mm_audio_voice_id") or "").strip() or None
        if actual_voice:
            return actual_voice
    requested = str(requested_voice or "").strip() or None
    if not requested:
        return None
    provider_norm = normalize_provider(provider)
    if provider_norm == "edge-tts":
        return (getattr(settings, "edge_tts_voice_map", {}) or {}).get(
            requested, requested
        )
    if provider_norm == "azure-speech":
        return (getattr(settings, "azure_tts_voice_map", {}) or {}).get(
            requested, requested
        )
    if provider_norm == "lovo":
        if requested == "mm_female_1":
            return getattr(settings, "lovo_speaker_mm_female_1", None) or requested
        if requested == "mm_male_1":
            return getattr(settings, "lovo_speaker_mm_male_1", None) or requested
    return requested


def hf_persisted_audio_state(task_id: str, task: dict) -> dict[str, Any]:
    from gateway.app.services.task_view_helpers import task_key

    audio_key = task_key(task, "mm_audio_key") or task_key(task, "mm_audio_path")
    exists = False
    size_bytes = 0
    if audio_key and object_exists(str(audio_key)):
        meta = object_head(str(audio_key))
        size_bytes, _ = media_meta_from_head(meta)
        exists = int(size_bytes or 0) >= MIN_AUDIO_BYTES
    return {
        "audio_key": str(audio_key) if audio_key else None,
        "exists": bool(exists),
        "size_bytes": int(size_bytes or 0),
        "voiceover_url": f"/v1/tasks/{task_id}/audio_mm"
        if task_id and exists
        else None,
        "deliverable_audio_done": bool(exists),
    }


def hf_audio_matches_expected(
    *,
    actual_provider: str | None,
    expected_provider: str | None,
    resolved_voice: str | None,
    expected_resolved_voice: str | None,
) -> tuple[bool, str]:
    if not expected_resolved_voice:
        return False, "voice_unresolved"
    if not resolved_voice:
        return False, "resolved_voice_missing"
    if normalize_provider(actual_provider) != normalize_provider(expected_provider):
        return False, "provider_mismatch"
    if str(resolved_voice).strip() != str(expected_resolved_voice).strip():
        return False, "voice_mismatch"
    return True, "ready"


# ── Aggregate function ───────────────────────────────────────────────────────

def collect_voice_execution_state(task: dict, settings) -> dict[str, Any]:
    """Build a complete voice execution state snapshot for *task*."""
    target_lang = normalize_target_lang(
        task.get("target_lang") or task.get("content_lang") or "mm"
    )
    task_id = str(task.get("task_id") or task.get("id") or "")
    voice_options_by_provider = build_hot_follow_voice_options(settings, target_lang)
    config_state = voice_state_config(task)
    requested_voice = config_state.get(
        "requested_voice"
    ) or resolve_hot_follow_requested_voice(
        settings, task, config_state.get("provider")
    )
    expected_provider = hot_follow_expected_provider(
        task,
        requested_voice,
        config_state.get("provider")
        or task.get("dub_provider")
        or getattr(settings, "dub_provider", None),
    )
    actual_provider = normalize_provider(
        task.get("mm_audio_provider") or expected_provider
    )
    expected_resolved_voice, _ = resolve_tts_voice(
        settings=settings,
        provider=expected_provider,
        target_lang=target_lang,
        requested_voice=requested_voice,
    )
    resolved_voice = (
        str(task.get("mm_audio_voice_id") or "").strip()
        or str(config_state.get("resolved_voice") or "").strip()
        or resolve_hot_follow_provider_voice(
            settings,
            actual_provider,
            requested_voice,
            task=task,
        )
    )
    persisted_audio = hf_persisted_audio_state(task_id, task)
    audio_exists = bool(persisted_audio.get("exists"))
    dub_status = str(task.get("dub_status") or "").strip().lower()
    dub_running = dub_status in {"queued", "running", "processing"}
    dub_done = dub_status in {"ready", "done", "success", "completed"}
    matches_expected, match_reason = hf_audio_matches_expected(
        actual_provider=actual_provider,
        expected_provider=expected_provider,
        resolved_voice=resolved_voice,
        expected_resolved_voice=expected_resolved_voice,
    )
    audio_ready_reason = "ready"
    if dub_running and not audio_exists:
        audio_ready_reason = "dub_running"
    elif not audio_exists:
        audio_ready_reason = "audio_missing"
    elif not dub_done:
        audio_ready_reason = "dub_not_done"
    elif not matches_expected:
        audio_ready_reason = match_reason
    elif (
        config_state.get("request_token")
        and config_state.get("completed_token")
        and config_state.get("completed_token") != config_state.get("request_token")
        and not audio_exists
    ):
        audio_ready_reason = "dub_not_current"
    subtitle_current = task.get("target_subtitle_current")
    subtitle_current_reason = str(task.get("target_subtitle_current_reason") or "").strip() or "subtitle_not_current"
    dub_matches_current_subtitle, dub_subtitle_reason = hf_dub_matches_current_subtitle(task)
    dub_matches_current_audio_config, dub_config_reason = hf_dub_matches_current_audio_config(task)
    if subtitle_current is False:
        audio_ready_reason = subtitle_current_reason
    elif not dub_matches_current_subtitle:
        audio_ready_reason = dub_subtitle_reason
    elif not dub_matches_current_audio_config:
        audio_ready_reason = dub_config_reason
    audio_ready = audio_ready_reason == "ready"
    dub_current = audio_ready and audio_exists and matches_expected
    return {
        "target_lang": target_lang,
        "voice_options_by_provider": voice_options_by_provider,
        "requested_voice": requested_voice,
        "actual_provider": actual_provider,
        "resolved_voice": resolved_voice,
        "expected_provider": expected_provider,
        "expected_resolved_voice": expected_resolved_voice,
        "audio_ready": audio_ready,
        "audio_ready_reason": audio_ready_reason,
        "voiceover_url": persisted_audio.get("voiceover_url")
        if dub_current
        else None,
        "deliverable_audio_done": bool(
            persisted_audio.get("deliverable_audio_done")
        ),
        "dub_current": bool(dub_current),
        "dub_current_reason": audio_ready_reason if not dub_current else "ready",
        "dub_matches_current_subtitle": bool(dub_matches_current_subtitle),
        "dub_subtitle_reason": dub_subtitle_reason,
        "current_audio_fit_max_speed": hf_current_audio_fit_max_speed(task),
        "dub_source_audio_fit_max_speed": str(task.get("dub_source_audio_fit_max_speed") or "").strip() or None,
        "dub_matches_current_audio_config": bool(dub_matches_current_audio_config),
        "dub_config_reason": dub_config_reason,
    }
