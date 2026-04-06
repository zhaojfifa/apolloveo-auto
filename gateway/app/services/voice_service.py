"""Hot Follow voice / audio presentation helpers.

These helpers are service-layer utilities shared by routers and compatibility
bridges. They do not own repo truth writes.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from gateway.app.config import get_settings
from gateway.app.services.artifact_storage import get_download_url
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang
from gateway.app.services.voice_state import collect_voice_execution_state
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)


def maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    if not enabled:
        return None
    soft_fail = os.getenv("HF_LIPSYNC_SOFT_FAIL", "1").strip().lower() not in ("0", "false", "no")
    message = "Lipsync stub enabled, but no provider is wired in v1.9; continuing basic compose."
    if soft_fail:
        logger.warning("HF_LIPSYNC_STUB_SOFT_FAIL task=%s message=%s", task_id, message)
        return message
    from fastapi import HTTPException

    raise HTTPException(
        status_code=409,
        detail={"reason": "lipsync_stub_blocked", "message": message},
    )


def hf_engine_public(provider: str | None) -> str:
    p = str(provider or "").strip().lower()
    if p in {"edge", "edge-tts", "edge_tts"}:
        return "edge_tts"
    if p in {"azure", "azure-speech", "azure_tts", "azure-tts"}:
        return "azure_speech"
    if p == "lovo":
        return "lovo"
    return "none"


def hf_engine_internal(engine: str | None) -> str | None:
    e = str(engine or "").strip().lower()
    if e in {"edge", "edge-tts", "edge_tts"}:
        return "edge-tts"
    if e in {"azure", "azure-speech", "azure_speech", "azure_tts", "azure-tts"}:
        return "azure-speech"
    if e == "lovo":
        return "lovo"
    if e in {"none", ""}:
        return None
    return None


def hf_source_audio_lane_summary(task: dict, route_state: dict[str, Any] | None = None) -> dict[str, Any]:
    route = route_state or {}
    content_mode = str(route.get("content_mode") or "").strip().lower()
    speech_detected = bool(route.get("speech_detected"))
    title_hint = str(task.get("title") or "").strip().lower()
    has_bgm_hint = any(token in title_hint for token in ("bgm", "音乐", "配乐", "商品", "展示"))

    if content_mode == "silent_candidate":
        return {
            "source_audio_lane": "silent_candidate",
            "source_audio_lane_reason": "未检测到稳定人声，建议优先字幕驱动。",
            "speech_presence": "none",
            "bgm_presence": "possible" if has_bgm_hint else "unknown",
            "audio_mix_mode": "silent_or_fx",
        }
    if content_mode == "subtitle_led":
        return {
            "source_audio_lane": "music_or_text_led",
            "source_audio_lane_reason": "画面文字线索更强，当前素材更像字幕或画面驱动。",
            "speech_presence": "low",
            "bgm_presence": "possible",
            "audio_mix_mode": "text_led",
        }
    if speech_detected and has_bgm_hint:
        return {
            "source_audio_lane": "mixed_audio",
            "source_audio_lane_reason": "检测到人声，同时素材特征显示可能带明显配乐。",
            "speech_presence": "high",
            "bgm_presence": "possible",
            "audio_mix_mode": "speech_plus_bgm",
        }
    if speech_detected:
        return {
            "source_audio_lane": "speech_primary",
            "source_audio_lane_reason": "检测到稳定人声，适合标准配音替换路径。",
            "speech_presence": "high",
            "bgm_presence": "low",
            "audio_mix_mode": "speech_primary",
        }
    return {
        "source_audio_lane": "unknown",
        "source_audio_lane_reason": "当前音频结构信息不足，建议先检查来源字幕和原视频。",
        "speech_presence": "unknown",
        "bgm_presence": "unknown",
        "audio_mix_mode": "unknown",
    }


def hf_screen_text_candidate_summary(
    subtitle_lane: dict[str, Any] | None = None,
    route_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lane = subtitle_lane or {}
    route = route_state or {}
    normalized = str(lane.get("normalized_source_text") or "").strip()
    raw = str(lane.get("raw_source_text") or "").strip()
    content_mode = str(route.get("content_mode") or "").strip().lower()
    onscreen = bool(route.get("onscreen_text_detected"))
    density = str(route.get("onscreen_text_density") or "").strip().lower() or "none"

    candidate_text = normalized or raw
    if not candidate_text or (not onscreen and content_mode != "subtitle_led"):
        return {
            "screen_text_candidate": "",
            "screen_text_candidate_source": None,
            "screen_text_candidate_confidence": "none",
            "screen_text_candidate_mode": "unavailable",
        }
    return {
        "screen_text_candidate": candidate_text,
        "screen_text_candidate_source": "normalized_source" if normalized else "source_text",
        "screen_text_candidate_confidence": density if density in {"high", "low"} else "low",
        "screen_text_candidate_mode": "subtitle_led" if content_mode == "subtitle_led" else "assisted_candidate",
    }


def hf_audio_config(task: dict) -> dict[str, Any]:
    settings = get_settings()
    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    mix = bgm.get("mix_ratio")
    try:
        mix_val = float(mix if mix is not None else 0.3)
    except Exception:
        mix_val = 0.3
    task_id = str(task.get("task_id") or task.get("id") or "")
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    try:
        audio_fit_max_speed = float(pipeline_config.get("audio_fit_max_speed") or 1.25)
    except Exception:
        audio_fit_max_speed = 1.25
    audio_fit_max_speed = max(1.0, min(1.6, audio_fit_max_speed))
    voice_state = collect_voice_execution_state(task, settings)
    provider = normalize_provider(voice_state.get("expected_provider") or task.get("dub_provider") or getattr(settings, "dub_provider", None))
    return {
        "tts_engine": hf_engine_public(provider),
        "tts_voice": voice_state.get("resolved_voice"),
        "requested_voice": voice_state.get("requested_voice"),
        "bgm_key": bgm.get("bgm_key"),
        "bgm_mix": max(0.0, min(1.0, mix_val)),
        "bgm_url": get_download_url(str(bgm.get("bgm_key"))) if bgm.get("bgm_key") else None,
        "voiceover_url": voice_state.get("voiceover_url"),
        "audio_url": voice_state.get("voiceover_url"),
        "audio_fit_max_speed": audio_fit_max_speed,
    }


def hf_audio_display_error(dub_state: str, dub_error: str | None, voice_state: dict[str, Any]) -> str | None:
    state = str(dub_state or "").strip().lower()
    reason = str(voice_state.get("dub_current_reason") or voice_state.get("audio_ready_reason") or "").strip().lower()
    if state in {"running", "processing", "queued"} or reason == "dub_running":
        return None
    if state == "failed":
        return str(dub_error or "").strip() or None
    return None
