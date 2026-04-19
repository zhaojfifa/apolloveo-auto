from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from gateway.app.services.source_audio_policy import source_audio_policy_from_task


@dataclass(frozen=True)
class HotFollowComposeRoute:
    name: str
    required_artifacts: tuple[str, ...]
    optional_artifacts: tuple[str, ...]
    irrelevant_artifacts: tuple[str, ...]
    allow_conditions: tuple[str, ...]
    blocked_conditions: tuple[str, ...]


HOT_FOLLOW_COMPOSE_ROUTES: dict[str, HotFollowComposeRoute] = {
    "tts_replace_route": HotFollowComposeRoute(
        name="tts_replace_route",
        required_artifacts=("compose_input", "tts_voiceover"),
        optional_artifacts=("target_subtitle", "bgm", "scene_pack"),
        irrelevant_artifacts=("source_audio_preserved",),
        allow_conditions=("compose_input_ready", "audio_ready"),
        blocked_conditions=("compose_input_blocked", "audio_missing"),
    ),
    "preserve_source_route": HotFollowComposeRoute(
        name="preserve_source_route",
        required_artifacts=("compose_input", "source_audio"),
        optional_artifacts=("target_subtitle", "bgm", "scene_pack"),
        irrelevant_artifacts=("tts_voiceover",),
        allow_conditions=("compose_input_ready", "source_audio_preserved"),
        blocked_conditions=("compose_input_blocked", "source_audio_not_preserved"),
    ),
    "bgm_only_route": HotFollowComposeRoute(
        name="bgm_only_route",
        required_artifacts=("compose_input", "bgm"),
        optional_artifacts=("target_subtitle", "scene_pack"),
        irrelevant_artifacts=("tts_voiceover", "source_audio_preserved"),
        allow_conditions=("compose_input_ready", "bgm_configured"),
        blocked_conditions=("compose_input_blocked", "bgm_missing"),
    ),
    "no_tts_compose_route": HotFollowComposeRoute(
        name="no_tts_compose_route",
        required_artifacts=("compose_input",),
        optional_artifacts=("target_subtitle", "scene_pack"),
        irrelevant_artifacts=("tts_voiceover", "bgm", "source_audio_preserved"),
        allow_conditions=("compose_input_ready", "no_tts_compose_selected"),
        blocked_conditions=("compose_input_blocked", "no_tts_not_selected"),
    ),
}


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


def _selected_compose_route(
    *,
    audio_lane: dict[str, Any],
    no_dub: bool,
    no_dub_compose_allowed: bool,
) -> str:
    if bool(audio_lane.get("tts_voiceover_exists")):
        return "tts_replace_route"
    if bool(audio_lane.get("source_audio_preserved")):
        return "preserve_source_route"
    if bool(audio_lane.get("bgm_configured")):
        return "bgm_only_route"
    if no_dub or no_dub_compose_allowed or bool(audio_lane.get("no_tts")):
        return "no_tts_compose_route"
    return "tts_replace_route"


def _route_allowance(
    *,
    route: str,
    compose_input: dict[str, Any],
    audio_lane: dict[str, Any],
    subtitle_lane: dict[str, Any],
    voice_state: dict[str, Any] | None = None,
    no_dub_compose_allowed: bool = False,
) -> tuple[bool, str]:
    if bool(compose_input.get("blocked")):
        return False, str(compose_input.get("reason") or "compose_input_blocked")
    voice = voice_state or {}
    subtitle_ready = bool(subtitle_lane.get("subtitle_ready"))
    audio_ready = bool(voice.get("audio_ready"))
    if route == "tts_replace_route":
        if not audio_ready:
            return False, str(voice.get("audio_ready_reason") or "audio_not_ready")
        return True, "ready"
    if route == "preserve_source_route":
        return (True, "ready") if audio_lane.get("source_audio_preserved") else (False, "source_audio_not_preserved")
    if route == "bgm_only_route":
        return (True, "ready") if audio_lane.get("bgm_configured") else (False, "bgm_missing")
    if route == "no_tts_compose_route":
        return (True, "ready") if no_dub_compose_allowed or audio_lane.get("no_tts") else (False, "no_tts_not_selected")
    return False, "unknown_route"


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
    selected_route = _selected_compose_route(
        audio_lane=audio_lane,
        no_dub=False,
        no_dub_compose_allowed=False,
    )
    route = HOT_FOLLOW_COMPOSE_ROUTES[selected_route]
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
        "selected_compose_route": {
            "name": selected_route,
            "required_artifacts": route.required_artifacts,
            "optional_artifacts": route.optional_artifacts,
            "irrelevant_artifacts": route.irrelevant_artifacts,
            "allow_conditions": route.allow_conditions,
            "blocked_conditions": route.blocked_conditions,
        },
    }


def selected_route_from_state(task: dict, state: dict) -> dict[str, Any]:
    artifact_facts = state.get("artifact_facts") if isinstance(state.get("artifact_facts"), dict) else {}
    compose_input = artifact_facts.get("compose_input") if isinstance(artifact_facts.get("compose_input"), dict) else {}
    audio_lane = artifact_facts.get("audio_lane") if isinstance(artifact_facts.get("audio_lane"), dict) else {}
    selected = artifact_facts.get("selected_compose_route")
    route_name = str((selected or {}).get("name") if isinstance(selected, dict) else selected or "").strip()
    audio = state.get("audio") if isinstance(state.get("audio"), dict) else {}
    no_dub = bool(audio.get("no_dub"))
    no_dub_reason = str(audio.get("no_dub_reason") or "").strip().lower()
    no_dub_compose_allowed = no_dub and no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}
    if bool(audio.get("audio_ready")) or bool(audio.get("voiceover_url") or audio.get("tts_voiceover_url") or audio.get("dub_preview_url")):
        route_name = "tts_replace_route"
    if not route_name:
        route_name = _selected_compose_route(
            audio_lane=audio_lane,
            no_dub=no_dub,
            no_dub_compose_allowed=no_dub_compose_allowed,
        )
    subtitles = state.get("subtitles") if isinstance(state.get("subtitles"), dict) else {}
    allowed, reason = _route_allowance(
        route=route_name,
        compose_input=compose_input,
        audio_lane=audio_lane,
        subtitle_lane=subtitles,
        voice_state=audio,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
    return {
        "name": route_name,
        "compose_allowed": allowed,
        "blocked_reason": "" if allowed else reason,
        "no_tts_compose_allowed": route_name in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"} and allowed,
        "no_dub_compose_allowed": route_name in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"} and allowed,
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
    audio_lane = artifacts.get("audio_lane") if isinstance(artifacts.get("audio_lane"), dict) else {}
    selected = artifacts.get("selected_compose_route") if isinstance(artifacts.get("selected_compose_route"), dict) else {}
    selected_route = str(selected.get("name") or "").strip()
    if bool(voice_state.get("audio_ready")) or bool(audio_lane.get("tts_voiceover_exists")):
        selected_route = "tts_replace_route"
    if not selected_route:
        selected_route = _selected_compose_route(
            audio_lane=audio_lane,
            no_dub=no_dub,
            no_dub_compose_allowed=no_dub_compose_allowed,
        )
    route_allowed, route_reason = _route_allowance(
        route=selected_route,
        compose_input=artifacts.get("compose_input") if isinstance(artifacts.get("compose_input"), dict) else {},
        audio_lane=audio_lane,
        subtitle_lane=subtitle_lane,
        voice_state=voice_state,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
    compose_blocked = bool(artifacts.get("compose_input_blocked"))
    if compose_blocked:
        compose_status_norm = "blocked"
        compose_reason_norm = str(artifacts.get("compose_input_reason") or "compose_input_blocked").strip()
    audio_ready = bool(voice_state.get("audio_ready"))
    no_tts_route = selected_route in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"}
    subtitle_empty = bool(
        not subtitle_lane.get("subtitle_artifact_exists")
        and not str(subtitle_lane.get("edited_text") or subtitle_lane.get("srt_text") or "").strip()
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    no_dub_route_terminal = bool(no_tts_route and route_allowed and subtitle_empty)
    subtitle_empty_terminal = bool(subtitle_empty and not no_dub_route_terminal)
    dub_status_norm = str(dub_status or "").strip().lower() or "never"
    if no_tts_route and route_allowed and dub_status_norm in {"running", "processing", "pending", "never"}:
        dub_status_norm = "skipped"
    requires_redub = bool(
        selected_route == "tts_replace_route"
        and subtitle_lane.get("subtitle_ready")
        and not audio_ready
        and str(voice_state.get("audio_ready_reason") or "").strip().lower()
        not in {"dub_running", "dub_not_done", "audio_missing", "unknown"}
    )
    requires_recompose = bool(
        not compose_blocked
        and route_allowed
        and not no_dub_route_terminal
        and (audio_ready or no_tts_route)
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
        "selected_compose_route": selected_route,
        "compose_allowed": route_allowed,
        "compose_blocked_terminal": compose_blocked,
        "compose_terminal_state": "compose_blocked_terminal" if compose_blocked else None,
        "compose_allowed_reason": "ready" if route_allowed else route_reason,
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
