from __future__ import annotations

import logging
from typing import Any, Callable

from gateway.app.services.source_audio_policy import source_audio_policy_from_task


logger = logging.getLogger(__name__)


def _first_mapping(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _compose_input_facts(task: dict) -> dict[str, Any]:
    compose = task.get("compose") if isinstance(task.get("compose"), dict) else {}
    policy = task.get("compose_input_policy") if isinstance(task.get("compose_input_policy"), dict) else {}
    profile = _first_mapping(
        policy.get("profile"),
        task.get("compose_input_probe"),
        compose.get("input_probe"),
        task.get("source_video_profile"),
        task.get("video_profile"),
    )
    mode = str(policy.get("mode") or "").strip().lower()
    reason = str(policy.get("reason") or "").strip() or None
    preflight_status = str(compose.get("preflight_status") or task.get("compose_preflight_status") or "").strip().lower()
    preflight_reason = str(compose.get("preflight_reason") or task.get("compose_preflight_reason") or "").strip() or None
    if not mode:
        if preflight_status == "blocked":
            mode = "blocked"
        elif task.get("compose_input_key") or task.get("compose_input_path"):
            mode = "derived"
        elif profile:
            mode = "direct"
        else:
            mode = "unknown"
    if reason is None:
        reason = preflight_reason
    return {
        "mode": mode,
        "blocked": mode == "blocked",
        "reason": reason,
        "profile": dict(profile or {}),
        "source": "compose_input_policy" if policy else ("compose_probe" if profile else "none"),
    }


def _audio_lane_facts(task: dict, persisted_audio: dict[str, Any] | None) -> dict[str, Any]:
    audio = persisted_audio or {}
    source_audio_policy = source_audio_policy_from_task(task)
    tts_voiceover_exists = bool(audio.get("exists") and str(audio.get("voiceover_url") or "").strip())
    source_audio_preserved = source_audio_policy == "preserve"
    config = task.get("config") if isinstance(task.get("config"), dict) else {}
    bgm = config.get("bgm") if isinstance(config.get("bgm"), dict) else {}
    bgm_key = str(bgm.get("bgm_key") or "").strip() or None
    if tts_voiceover_exists and source_audio_preserved:
        mode = "tts_voiceover_plus_source_audio"
    elif tts_voiceover_exists:
        mode = "tts_voiceover_only"
    elif source_audio_preserved:
        mode = "source_audio_preserved_no_tts"
    else:
        mode = "muted_no_tts"
    return {
        "mode": mode,
        "tts_voiceover_exists": tts_voiceover_exists,
        "source_audio_policy": source_audio_policy,
        "source_audio_preserved": source_audio_preserved,
        "bgm_key": bgm_key,
        "bgm_configured": bool(bgm_key),
        "no_tts": not tts_voiceover_exists,
    }


def build_hot_follow_artifact_facts(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
    deliverable_url: Callable[[str, dict, str], str | None],
) -> dict[str, Any]:
    current_final_payload = final_info or {}
    historical_payload = historical_final or {}
    final_payload = current_final_payload if bool(current_final_payload.get("exists")) else historical_payload
    audio_payload = persisted_audio or {}
    subtitle_payload = subtitle_lane or {}
    pack_payload = scene_pack or {}
    subtitle_url = deliverable_url(task_id, task, "mm_srt")
    pack_url = deliverable_url(task_id, task, "pack_zip") or pack_payload.get("download_url")
    compose_input = _compose_input_facts(task)
    audio_lane = _audio_lane_facts(task, audio_payload)
    return {
        "final_exists": bool(current_final_payload.get("exists") or historical_payload.get("exists")),
        "final_url": str(final_payload.get("url") or "").strip() or None,
        "final_updated_at": final_payload.get("updated_at") or task.get("final_updated_at") or task.get("updated_at"),
        "final_asset_version": str(final_payload.get("asset_version") or "").strip() or None,
        "audio_exists": bool(audio_payload.get("exists")),
        "audio_url": str(audio_payload.get("voiceover_url") or "").strip() or None,
        "subtitle_exists": bool(subtitle_payload.get("subtitle_artifact_exists")),
        "subtitle_url": str(subtitle_url or "").strip() or None,
        "pack_exists": bool(pack_url),
        "pack_url": str(pack_url or "").strip() or None,
        "compose_input": compose_input,
        "compose_input_mode": compose_input["mode"],
        "compose_input_blocked": bool(compose_input["blocked"]),
        "compose_input_reason": compose_input["reason"],
        "audio_lane": audio_lane,
        "audio_lane_mode": audio_lane["mode"],
        "tts_voiceover_exists": bool(audio_lane["tts_voiceover_exists"]),
    }


def build_hot_follow_current_attempt_summary(
    *,
    voice_state: dict[str, Any],
    subtitle_lane: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    final_stale_reason: str | None = None,
    artifact_facts: dict[str, Any] | None = None,
    no_dub: bool = False,
    no_dub_compose_allowed: bool = False,
) -> dict[str, Any]:
    artifacts = artifact_facts or {}
    compose_status_norm = str(compose_status or "").strip().lower() or "never"
    compose_reason_norm = str(composed_reason or "").strip().lower() or "unknown"
    dub_status_norm = str(dub_status or "").strip().lower() or "never"
    compose_blocked = bool(artifacts.get("compose_input_blocked"))
    audio_lane = artifacts.get("audio_lane") if isinstance(artifacts.get("audio_lane"), dict) else {}
    no_tts_legal_line = bool(
        audio_lane.get("no_tts")
        and (audio_lane.get("source_audio_preserved") or audio_lane.get("bgm_configured"))
    )
    subtitle_empty = bool(
        not subtitle_lane.get("subtitle_artifact_exists")
        and not str(subtitle_lane.get("edited_text") or subtitle_lane.get("srt_text") or "").strip()
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    no_dub_route_terminal = bool((no_dub or no_dub_compose_allowed or no_tts_legal_line) and subtitle_empty)
    subtitle_empty_terminal = bool(subtitle_empty and not no_dub_route_terminal)
    if compose_blocked:
        compose_status_norm = "blocked"
        compose_reason_norm = str(artifacts.get("compose_input_reason") or "compose_input_blocked").strip()
    if no_dub_route_terminal and dub_status_norm in {"running", "processing", "pending", "never"}:
        dub_status_norm = "skipped"
    audio_ready = bool(voice_state.get("audio_ready"))
    requires_redub = bool(
        subtitle_lane.get("subtitle_ready")
        and not audio_ready
        and str(voice_state.get("audio_ready_reason") or "").strip().lower()
        not in {"dub_running", "dub_not_done", "audio_missing", "unknown"}
    )
    requires_recompose = bool(
        not compose_blocked
        and not no_dub_route_terminal
        and audio_ready
        and (final_stale_reason or compose_reason_norm != "ready")
    )
    return {
        "dub_status": dub_status_norm,
        "audio_ready": audio_ready,
        "audio_ready_reason": str(voice_state.get("audio_ready_reason") or "").strip() or "unknown",
        "dub_current": bool(voice_state.get("dub_current")),
        "dub_current_reason": str(voice_state.get("dub_current_reason") or "").strip() or "unknown",
        "requested_voice": str(voice_state.get("requested_voice") or "").strip() or None,
        "resolved_voice": str(voice_state.get("resolved_voice") or "").strip() or None,
        "actual_provider": str(voice_state.get("actual_provider") or "").strip() or None,
        "compose_status": compose_status_norm,
        "compose_reason": compose_reason_norm,
        "final_stale_reason": final_stale_reason or None,
        "compose_blocked_terminal": compose_blocked,
        "compose_terminal_state": "compose_blocked_terminal" if compose_blocked else None,
        "subtitle_empty_terminal": subtitle_empty_terminal,
        "no_dub_route_terminal": no_dub_route_terminal,
        "subtitle_terminal_state": (
            "no_dub_route_terminal"
            if no_dub_route_terminal
            else ("subtitle_empty_terminal" if subtitle_empty_terminal else None)
        ),
        "requires_redub": requires_redub,
        "requires_recompose": requires_recompose,
        "current_subtitle_source": str(subtitle_lane.get("actual_burn_subtitle_source") or "").strip() or None,
    }


def build_hot_follow_operator_summary(
    *,
    artifact_facts: dict[str, Any],
    current_attempt: dict[str, Any],
    no_dub: bool,
    subtitle_ready: bool = False,
) -> dict[str, Any]:
    last_successful_output_available = bool(artifact_facts.get("final_exists"))
    dub_status = str(current_attempt.get("dub_status") or "").strip().lower()
    compose_status = str(current_attempt.get("compose_status") or "").strip().lower()
    current_attempt_failed = dub_status in {"failed", "error"} or compose_status in {"failed", "error"}
    show_previous_final_as_primary = bool(
        last_successful_output_available
        and not bool(current_attempt.get("audio_ready"))
        and not no_dub
    )
    if no_dub and not subtitle_ready:
        recommended_next_action = "当前素材无可提取字幕，正在等待自动检测完成；也可直接在下方字幕编辑区手工输入缅语文字，保存后即可合成字幕版。"
    elif no_dub:
        recommended_next_action = "当前素材适合字幕驱动路径，可先保存字幕并直接合成字幕版。"
    elif current_attempt.get("requires_redub"):
        recommended_next_action = "当前目标字幕已更新，需重新配音后才能继续合成最新成片。"
    elif current_attempt.get("requires_recompose"):
        recommended_next_action = "当前配音已更新，建议重新合成最终视频以生成最新版本。"
    elif show_previous_final_as_primary and current_attempt_failed:
        recommended_next_action = "当前重配音失败，但上一次成片仍可查看；请先修复当前配音后再重新合成。"
    elif show_previous_final_as_primary:
        recommended_next_action = "当前重配音未完成，上一次成片仍可查看；如需更新版本，请在当前配音完成后重新合成。"
    elif last_successful_output_available:
        recommended_next_action = "当前已有可用成片，可按需继续校对字幕、配音或重新合成。"
    else:
        recommended_next_action = "当前尚无可用成片，请先确保字幕和配音链路完成后再合成。"
    return {
        "last_successful_output_available": last_successful_output_available,
        "current_attempt_failed": current_attempt_failed,
        "show_previous_final_as_primary": show_previous_final_as_primary,
        "recommended_next_action": recommended_next_action,
    }
