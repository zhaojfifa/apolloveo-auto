from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

_TTS_FAILURE_REASONS = {
    "empty_or_invalid_audio",
    "tts_failed",
    "tts_failed:empty_or_invalid_audio",
    "tts_failed_timeout",
    "tts_failed_cancelled",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_tts_failure_reason(value: Any) -> bool:
    reason = _norm(value)
    return bool(
        reason in _TTS_FAILURE_REASONS
        or reason.startswith("tts_failed")
        or reason.startswith("tts_")
        or "empty_or_invalid_audio" in reason
    )


def select_compose_route_name(
    *,
    audio_lane: dict[str, Any],
    no_dub: bool,
    no_dub_compose_allowed: bool,
    subtitle_ready: bool = False,
    helper_translate_failed_voice_led: bool = False,
) -> str:
    if helper_translate_failed_voice_led and not bool(audio_lane.get("tts_voiceover_exists")):
        return "tts_replace_route"
    if bool(audio_lane.get("tts_voiceover_exists")):
        return "tts_replace_route"
    if bool(audio_lane.get("source_audio_preserved")):
        return "preserve_source_route"
    if bool(audio_lane.get("bgm_configured")):
        return "bgm_only_route"
    if bool(subtitle_ready) and not no_dub and not no_dub_compose_allowed:
        return "tts_replace_route"
    if no_dub or no_dub_compose_allowed or bool(audio_lane.get("no_tts")):
        return "no_tts_compose_route"
    return "tts_replace_route"


def route_allowance(
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


def terminal_dub_lane_state(
    *,
    route: str,
    route_allowed: bool,
    dub_status: str,
    no_dub: bool,
    no_dub_reason: str | None,
) -> str:
    status = _norm(dub_status) or "absent"
    if route == "tts_replace_route":
        return status
    if not route_allowed:
        return status
    reason = _norm(no_dub_reason)
    if reason in {"target_subtitle_empty", "dub_input_empty"}:
        return "empty"
    if no_dub or status == "skipped":
        return "skipped"
    if status in {"running", "processing", "pending", "queued", "never", "unknown", "absent"}:
        return "absent"
    return status


def _route_should_stay_tts(
    *,
    route_name: str,
    subtitles: dict[str, Any],
    audio: dict[str, Any],
    no_dub: bool,
    no_dub_compose_allowed: bool,
) -> bool:
    return bool(
        route_name == "no_tts_compose_route"
        and subtitles.get("subtitle_ready")
        and not audio.get("audio_ready")
        and not no_dub
        and not no_dub_compose_allowed
    )


def selected_route_from_state(task: dict, state: dict) -> dict[str, Any]:
    _ = task
    artifact_facts = state.get("artifact_facts") if isinstance(state.get("artifact_facts"), dict) else {}
    compose_input = artifact_facts.get("compose_input") if isinstance(artifact_facts.get("compose_input"), dict) else {}
    audio_lane = artifact_facts.get("audio_lane") if isinstance(artifact_facts.get("audio_lane"), dict) else {}
    selected = artifact_facts.get("selected_compose_route")
    route_name = str((selected or {}).get("name") if isinstance(selected, dict) else selected or "").strip()
    audio = state.get("audio") if isinstance(state.get("audio"), dict) else {}
    subtitles = state.get("subtitles") if isinstance(state.get("subtitles"), dict) else {}
    no_dub = bool(audio.get("no_dub"))
    no_dub_reason = _norm(audio.get("no_dub_reason"))
    no_dub_compose_allowed = bool(audio.get("no_dub_compose_allowed")) or (
        no_dub and no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}
    )
    subtitle_ready = bool(subtitles.get("subtitle_ready"))
    if bool(audio.get("audio_ready")) or bool(audio.get("voiceover_url") or audio.get("tts_voiceover_url") or audio.get("dub_preview_url")):
        route_name = "tts_replace_route"
    if (
        no_dub
        and not bool(audio.get("audio_ready"))
        and not bool(audio_lane.get("tts_voiceover_exists"))
        and not bool(audio_lane.get("source_audio_preserved"))
        and not bool(audio_lane.get("bgm_configured"))
    ):
        route_name = "no_tts_compose_route"
    if not route_name:
        route_name = select_compose_route_name(
            audio_lane=audio_lane,
            no_dub=no_dub,
            no_dub_compose_allowed=no_dub_compose_allowed,
            subtitle_ready=subtitle_ready,
            helper_translate_failed_voice_led=bool(artifact_facts.get("helper_translate_failed_voice_led")),
        )
    if _route_should_stay_tts(
        route_name=route_name,
        subtitles=subtitles,
        audio=audio,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    ):
        route_name = "tts_replace_route"
    audio_ready = bool(audio.get("audio_ready"))
    helper_translate_failed_voice_led = bool(
        not subtitle_ready
        and (
            artifact_facts.get("helper_translate_failed_voice_led")
            or (
                artifact_facts.get("helper_translate_failed")
                and (
                    str(subtitles.get("parse_source_text") or "").strip()
                    or str(subtitles.get("raw_source_text") or "").strip()
                    or str(subtitles.get("normalized_source_text") or "").strip()
                )
            )
        )
    )
    helper_failure_with_authoritative_subtitle = bool(
        subtitle_ready
        and artifact_facts.get("helper_translate_failed")
        and not audio_ready
    )
    if helper_failure_with_authoritative_subtitle:
        route_name = "tts_replace_route"
    elif helper_translate_failed_voice_led and not audio_ready:
        route_name = "tts_replace_route"
    allowed, reason = route_allowance(
        route=route_name,
        compose_input=compose_input,
        audio_lane=audio_lane,
        subtitle_lane=subtitles,
        voice_state=audio,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
    compose_input_mode = _norm(compose_input.get("mode"))
    compose_input_ready = bool(compose_input.get("ready") or compose_input_mode in {"direct", "derived_ready"})
    compose_input_terminal_reason = str(
        compose_input.get("failure_code") or compose_input.get("reason") or compose_input_mode or "compose_input_not_ready"
    ).strip()
    compose_execute_allowed = bool(allowed and compose_input_ready)
    no_tts_allowed = route_name in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"} and allowed
    return {
        "name": route_name,
        "compose_allowed": allowed,
        "compose_route_allowed": allowed,
        "compose_input_ready": compose_input_ready,
        "compose_input_mode": compose_input_mode,
        "compose_input_reason": compose_input_terminal_reason,
        "compose_execute_allowed": compose_execute_allowed,
        "blocked_reason": "" if allowed else reason,
        "no_tts_compose_allowed": no_tts_allowed,
        "no_dub_compose_allowed": no_tts_allowed,
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
    compose_status_norm = _norm(compose_status) or "never"
    compose_reason_norm = _norm(composed_reason) or "unknown"
    audio_lane = artifacts.get("audio_lane") if isinstance(artifacts.get("audio_lane"), dict) else {}
    selected = artifacts.get("selected_compose_route") if isinstance(artifacts.get("selected_compose_route"), dict) else {}
    selected_route = str(selected.get("name") or "").strip()
    subtitle_ready = bool(subtitle_lane.get("subtitle_ready"))
    audio_ready = bool(voice_state.get("audio_ready"))
    helper_translate_failed = bool(artifacts.get("helper_translate_failed") and not subtitle_ready)
    helper_translate_failed_voice_led = bool(artifacts.get("helper_translate_failed_voice_led") and helper_translate_failed)
    if bool(voice_state.get("audio_ready")) or bool(audio_lane.get("tts_voiceover_exists")):
        selected_route = "tts_replace_route"
    if (
        no_dub
        and not audio_ready
        and not bool(audio_lane.get("tts_voiceover_exists"))
        and not bool(audio_lane.get("source_audio_preserved"))
        and not bool(audio_lane.get("bgm_configured"))
    ):
        selected_route = "no_tts_compose_route"
    if not selected_route:
        selected_route = select_compose_route_name(
            audio_lane=audio_lane,
            no_dub=no_dub,
            no_dub_compose_allowed=no_dub_compose_allowed,
            subtitle_ready=subtitle_ready,
            helper_translate_failed_voice_led=helper_translate_failed_voice_led,
        )
    if _route_should_stay_tts(
        route_name=selected_route,
        subtitles=subtitle_lane,
        audio=voice_state,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    ):
        selected_route = "tts_replace_route"
    if bool(artifacts.get("helper_translate_failed") and subtitle_ready and not audio_ready):
        selected_route = "tts_replace_route"
    elif helper_translate_failed_voice_led and not audio_ready:
        selected_route = "tts_replace_route"
    route_allowed, route_reason = route_allowance(
        route=selected_route,
        compose_input=artifacts.get("compose_input") if isinstance(artifacts.get("compose_input"), dict) else {},
        audio_lane=audio_lane,
        subtitle_lane=subtitle_lane,
        voice_state=voice_state,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
    compose_blocked = bool(artifacts.get("compose_input_blocked"))
    compose_input = artifacts.get("compose_input") if isinstance(artifacts.get("compose_input"), dict) else {}
    compose_input_mode = _norm(compose_input.get("mode") or artifacts.get("compose_input_mode"))
    compose_input_ready = bool(
        compose_input.get("ready")
        or artifacts.get("compose_input_ready")
        or compose_input_mode in {"direct", "derived_ready"}
    )
    compose_input_derive_failed = bool(
        compose_input.get("derive_failed")
        or artifacts.get("compose_input_derive_failed")
        or compose_input_mode == "derive_failed"
    )
    compose_input_reason = str(
        compose_input.get("failure_code")
        or artifacts.get("compose_input_failure_code")
        or compose_input.get("reason")
        or artifacts.get("compose_input_reason")
        or compose_input_mode
        or "compose_input_not_ready"
    ).strip()
    if compose_blocked:
        compose_status_norm = "blocked"
        compose_reason_norm = str(artifacts.get("compose_input_reason") or "compose_input_blocked").strip()
    elif compose_input_derive_failed:
        compose_status_norm = "failed"
        compose_reason_norm = compose_input_reason or "compose_input_derive_failed"
    no_tts_route = selected_route in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"}
    subtitle_empty = bool(
        not subtitle_lane.get("subtitle_artifact_exists")
        and not str(subtitle_lane.get("edited_text") or subtitle_lane.get("srt_text") or "").strip()
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    no_dub_route_terminal = bool(no_tts_route and route_allowed)
    subtitle_empty_terminal = bool(subtitle_empty and not no_dub_route_terminal)
    no_dub_reason = str(voice_state.get("no_dub_reason") or "").strip() or None
    dub_status_norm = terminal_dub_lane_state(
        route=selected_route,
        route_allowed=route_allowed,
        dub_status=dub_status,
        no_dub=no_dub,
        no_dub_reason=no_dub_reason,
    )
    tts_lane_expected = bool(selected_route == "tts_replace_route" and subtitle_ready and not no_dub)
    retriable_dub_failure = bool(
        tts_lane_expected
        and not audio_ready
        and (
            _norm(dub_status) in {"failed", "error"}
            or _is_tts_failure_reason(voice_state.get("audio_ready_reason"))
            or _is_tts_failure_reason(voice_state.get("dub_error"))
            or _is_tts_failure_reason(voice_state.get("error_reason"))
        )
    )
    requires_redub = bool(
        selected_route == "tts_replace_route"
        and subtitle_lane.get("subtitle_ready")
        and not audio_ready
        and (
            retriable_dub_failure
            or _norm(voice_state.get("audio_ready_reason")) not in {"dub_running", "dub_not_done", "audio_missing", "unknown"}
        )
    )
    requires_recompose = bool(
        not compose_blocked
        and not compose_input_derive_failed
        and route_allowed
        and not no_dub_route_terminal
        and (audio_ready or no_tts_route)
        and (final_stale_reason or compose_reason_norm != "ready")
    )
    compose_execute_allowed = bool(route_allowed and compose_input_ready)
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
        "compose_route_allowed": route_allowed,
        "compose_input_ready": compose_input_ready,
        "compose_execute_allowed": compose_execute_allowed,
        "no_tts_compose_allowed": bool(no_tts_route and route_allowed),
        "no_dub_compose_allowed": bool(no_tts_route and route_allowed),
        "compose_blocked_terminal": compose_blocked,
        "compose_input_derive_failed_terminal": compose_input_derive_failed,
        "compose_input_blocked_terminal": compose_blocked,
        "compose_exec_failed_terminal": bool(
            not compose_input_derive_failed
            and not compose_blocked
            and compose_status_norm in {"failed", "error"}
        ),
        "compose_terminal_state": (
            "compose_blocked_terminal"
            if compose_blocked
            else (
                "compose_input_derive_failed_terminal"
                if compose_input_derive_failed
                else ("compose_exec_failed_terminal" if compose_status_norm in {"failed", "error"} else None)
            )
        ),
        "compose_allowed_reason": "ready" if route_allowed else route_reason,
        "subtitle_empty_terminal": subtitle_empty_terminal,
        "no_dub_route_terminal": no_dub_route_terminal,
        "tts_lane_expected": tts_lane_expected,
        "retriable_dub_failure": retriable_dub_failure,
        "current_attempt_failure_class": "retriable_dub_failure" if retriable_dub_failure else None,
        "helper_translate_failed": helper_translate_failed,
        "helper_translate_failed_voice_led": helper_translate_failed_voice_led,
        "helper_translate_error_reason": artifacts.get("helper_translate_error_reason"),
        "helper_translate_error_message": artifacts.get("helper_translate_error_message"),
        "subtitle_terminal_state": (
            "helper_translate_failed_terminal"
            if helper_translate_failed
            else (
                "no_dub_route_terminal"
                if no_dub_route_terminal
                else ("subtitle_empty_terminal" if subtitle_empty_terminal else None)
            )
        ),
        "requires_redub": requires_redub,
        "requires_recompose": requires_recompose,
        "current_subtitle_source": str(subtitle_lane.get("actual_burn_subtitle_source") or "").strip() or None,
    }
