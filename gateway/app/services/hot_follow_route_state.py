from __future__ import annotations

from typing import Any, Callable

from gateway.app.services.contract_runtime.current_attempt_runtime import (
    HOT_FOLLOW_COMPOSE_ROUTES,
    build_hot_follow_current_attempt_summary as _contract_current_attempt_summary,
    selected_route_from_state,
)
from gateway.app.services.source_audio_policy import source_audio_policy_from_task


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
    failure_code = str(policy.get("failure_code") or "").strip() or None
    safe_key = str(policy.get("safe_key") or task.get("compose_input_key") or task.get("compose_input_path") or "").strip() or None
    preflight_status = str(compose.get("preflight_status") or task.get("compose_preflight_status") or "").strip().lower()
    preflight_reason = str(compose.get("preflight_reason") or task.get("compose_preflight_reason") or "").strip() or None
    if not mode:
        if preflight_status == "blocked":
            mode = "blocked"
        elif task.get("compose_input_key") or task.get("compose_input_path"):
            mode = "derived_ready"
        elif profile:
            mode = "direct"
        else:
            mode = "unknown"
    if mode == "derived":
        mode = "derived_ready"
    if reason is None:
        reason = preflight_reason
    blocked = mode == "blocked"
    derive_failed = mode == "derive_failed"
    ready = mode in {"direct", "derived_ready"}
    return {
        "mode": mode,
        "blocked": blocked,
        "ready": ready,
        "derive_failed": derive_failed,
        "reason": reason,
        "failure_code": failure_code,
        "profile": dict(profile or {}),
        "safe_key": safe_key,
        "source": str(policy.get("source") or "").strip()
        or ("raw" if policy or profile else "none"),
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
    subtitle_exists = bool(subtitle_payload.get("subtitle_artifact_exists"))
    subtitle_url = deliverable_url(task_id, task, "mm_srt") if subtitle_exists else None
    pack_url = deliverable_url(task_id, task, "pack_zip") or pack_payload.get("download_url")
    compose_input = _compose_input_facts(task)
    audio_lane = _audio_lane_facts(task, audio_payload)
    helper_translate_failed = bool(subtitle_payload.get("helper_translate_failed"))
    helper_translate_failed_voice_led = bool(
        helper_translate_failed
        and (
            str(subtitle_payload.get("parse_source_text") or "").strip()
            or str(subtitle_payload.get("raw_source_text") or "").strip()
            or str(subtitle_payload.get("normalized_source_text") or "").strip()
        )
    )
    selected_route = selected_route_from_state(
        task,
        {
            "artifact_facts": {
                "compose_input": compose_input,
                "audio_lane": audio_lane,
                "helper_translate_failed": helper_translate_failed,
                "helper_translate_failed_voice_led": helper_translate_failed_voice_led,
                "final_exists": bool(current_final_payload.get("exists") or historical_payload.get("exists")),
            },
            "audio": {
                "audio_ready": bool(audio_lane.get("tts_voiceover_exists")),
                "voiceover_url": str(audio_payload.get("voiceover_url") or "").strip() or None,
                "no_dub": False,
                "no_dub_reason": None,
            },
            "subtitles": {
                "subtitle_ready": bool(subtitle_payload.get("subtitle_ready")),
                "subtitle_ready_reason": subtitle_payload.get("subtitle_ready_reason"),
                "target_subtitle_current_reason": subtitle_payload.get("target_subtitle_current_reason"),
                "target_subtitle_authoritative_source": bool(subtitle_payload.get("target_subtitle_authoritative_source")),
                "parse_source_text": subtitle_payload.get("parse_source_text"),
                "raw_source_text": subtitle_payload.get("raw_source_text"),
                "normalized_source_text": subtitle_payload.get("normalized_source_text"),
            },
            "final": {"exists": bool(current_final_payload.get("exists"))},
            "historical_final": {"exists": bool(historical_payload.get("exists"))},
        },
    )["name"]
    route = HOT_FOLLOW_COMPOSE_ROUTES[selected_route]
    return {
        "final_exists": bool(current_final_payload.get("exists") or historical_payload.get("exists")),
        "final_url": str(final_payload.get("url") or "").strip() or None,
        "final_updated_at": final_payload.get("updated_at") or task.get("final_updated_at") or task.get("updated_at"),
        "final_asset_version": str(final_payload.get("asset_version") or "").strip() or None,
        "audio_exists": bool(audio_payload.get("exists")),
        "audio_url": str(audio_payload.get("voiceover_url") or "").strip() or None,
        "subtitle_exists": subtitle_exists,
        "subtitle_url": str(subtitle_url or "").strip() or None,
        "helper_translate_failed": helper_translate_failed,
        "helper_translate_failed_voice_led": helper_translate_failed_voice_led,
        "helper_translate_status": subtitle_payload.get("helper_translate_status"),
        "helper_translate_error_reason": subtitle_payload.get("helper_translate_error_reason"),
        "helper_translate_error_message": subtitle_payload.get("helper_translate_error_message"),
        "helper_translate_retryable": bool(subtitle_payload.get("helper_translate_retryable")),
        "helper_translate_terminal": bool(subtitle_payload.get("helper_translate_terminal")),
        "pack_exists": bool(pack_url),
        "pack_url": str(pack_url or "").strip() or None,
        "compose_input": compose_input,
        "compose_input_mode": compose_input["mode"],
        "compose_input_blocked": bool(compose_input["blocked"]),
        "compose_input_ready": bool(compose_input["ready"]),
        "compose_input_derive_failed": bool(compose_input["derive_failed"]),
        "compose_input_reason": compose_input["reason"],
        "compose_input_failure_code": compose_input["failure_code"],
        "compose_input_safe_key": compose_input["safe_key"],
        "audio_lane": audio_lane,
        "audio_lane_mode": audio_lane["mode"],
        "tts_voiceover_exists": bool(audio_lane["tts_voiceover_exists"]),
        "selected_compose_route": {
            "name": selected_route,
            "required_artifacts": route.required_artifacts,
            "optional_artifacts": route.optional_artifacts,
            "irrelevant_artifacts": route.irrelevant_artifacts,
            "allow_conditions": route.allow_conditions,
            "blocked_conditions": route.blocked_conditions,
        },
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
    return _contract_current_attempt_summary(
        voice_state=voice_state,
        subtitle_lane=subtitle_lane,
        dub_status=dub_status,
        compose_status=compose_status,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
        artifact_facts=artifact_facts,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
