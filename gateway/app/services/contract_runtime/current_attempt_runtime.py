from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gateway.app.services.hot_follow_process_state import reduce_hot_follow_process_state


@dataclass(frozen=True)
class HotFollowComposeRoute:
    name: str
    required_artifacts: tuple[str, ...]
    optional_artifacts: tuple[str, ...]
    irrelevant_artifacts: tuple[str, ...]
    allow_conditions: tuple[str, ...]
    blocked_conditions: tuple[str, ...]


FORMAL_HOT_FOLLOW_ROUTES = {"tts_replace_route", "preserve_source_route"}


@dataclass(frozen=True)
class HotFollowRouteTruth:
    route: str
    source: str
    reason: str | None = None
    event_id: str | None = None


@dataclass(frozen=True)
class HotFollowCurrentAttempt:
    contract_version: str
    selected_compose_route: str
    route_allowed: bool
    route_allowed_reason: str
    subtitle_required: bool
    subtitle_process_state: str
    subtitle_ready: bool
    subtitle_ready_reason: str
    target_subtitle_authoritative_current: bool
    target_subtitle_source: str | None
    dub_process_state: str
    audio_ready: bool
    audio_ready_reason: str
    dub_current: bool
    dub_current_reason: str
    compose_input_ready: bool
    compose_allowed: bool
    compose_route_allowed: bool
    compose_execute_allowed: bool
    compose_reason: str
    compose_allowed_reason: str
    requires_redub: bool
    requires_recompose: bool
    final_fresh: bool
    final_stale_reason: str | None
    route_truth_source: str
    route_truth_reason: str | None
    route_event_id: str | None
    pending_class: str
    blocking: tuple[str, ...]
    helper_translate_status: str | None = None
    helper_translate_output_state: str | None = None
    helper_translate_provider_health: str | None = None
    helper_translate_warning_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "selected_compose_route": self.selected_compose_route,
            "route_allowed": self.route_allowed,
            "route_allowed_reason": self.route_allowed_reason,
            "subtitle_required": self.subtitle_required,
            "subtitle_process_state": self.subtitle_process_state,
            "subtitle_ready": self.subtitle_ready,
            "subtitle_ready_reason": self.subtitle_ready_reason,
            "target_subtitle_authoritative_current": self.target_subtitle_authoritative_current,
            "target_subtitle_source": self.target_subtitle_source,
            "dub_process_state": self.dub_process_state,
            "audio_ready": self.audio_ready,
            "audio_ready_reason": self.audio_ready_reason,
            "dub_current": self.dub_current,
            "dub_current_reason": self.dub_current_reason,
            "compose_input_ready": self.compose_input_ready,
            "compose_allowed": self.compose_allowed,
            "compose_route_allowed": self.compose_route_allowed,
            "compose_execute_allowed": self.compose_execute_allowed,
            "compose_reason": self.compose_reason,
            "compose_allowed_reason": self.compose_allowed_reason,
            "requires_redub": self.requires_redub,
            "requires_recompose": self.requires_recompose,
            "final_fresh": self.final_fresh,
            "final_stale_reason": self.final_stale_reason,
            "route_truth_source": self.route_truth_source,
            "route_truth_reason": self.route_truth_reason,
            "route_event_id": self.route_event_id,
            "pending_class": self.pending_class,
            "blocking": list(self.blocking),
            "helper_translate_status": self.helper_translate_status,
            "helper_translate_output_state": self.helper_translate_output_state,
            "helper_translate_provider_health": self.helper_translate_provider_health,
            "helper_translate_warning_only": self.helper_translate_warning_only,
        }


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

_DEFAULT_RUNTIME_BOUNDARY_RULES: dict[str, Any] = {
    "url_voice_led_standard_dubbing": {
        "keep_tts_replace_when": ["subtitle_ready", "target_subtitle_authoritative_source"],
        "keep_tts_replace_current_reasons": [
            "target_subtitle_translation_incomplete",
            "helper_translate_provider_exhausted",
            "helper_translate_failed",
        ],
        "helper_failure_history_diagnostic_only_after_target_ready": True,
    },
    "preserve_source_route_resolution": {
        "explicit_no_target_required_reasons": [
            "preserve_source_route_no_target_subtitle_required",
        ],
        "preserve_policy_alone_does_not_force_no_tts_terminal": True,
        "preserve_policy_still_uses_tts_route_when": [
            "subtitle_ready",
            "helper_translate_failed_voice_led",
            "target_subtitle_translation_incomplete",
        ],
    },
    "helper_side_channel_coexistence": {
        "helper_failure_is_side_channel_only_when_any": [
            "subtitle_ready",
            "audio_ready",
            "final_exists",
            "final_fresh",
        ],
    },
    "historical_event_isolation": {
        "current_truth_dominates_when_any": [
            "subtitle_ready",
            "audio_ready",
            "final_exists",
            "final_fresh",
        ],
        "stale_no_dub_reasons_ignored_when_current_truth": [
            "target_subtitle_empty",
            "dub_input_empty",
        ],
    },
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _route_from_command(command: str) -> str:
    if command == "enter_tts_replace_route":
        return "tts_replace_route"
    if command == "enter_preserve_source_route":
        return "preserve_source_route"
    return ""


def _route_truth_from_mapping(value: Any, *, source: str) -> HotFollowRouteTruth | None:
    data = _dict(value)
    if not data:
        return None
    route = _clean(data.get("route") or data.get("target_route") or data.get("selected_compose_route"))
    if not route:
        route = _route_from_command(_clean(data.get("command")))
    if route not in FORMAL_HOT_FOLLOW_ROUTES:
        return None
    return HotFollowRouteTruth(
        route=route,
        source=source,
        reason=_clean(data.get("reason") or data.get("route_reason")) or None,
        event_id=_clean(data.get("event_id") or data.get("id")) or None,
    )


def read_hot_follow_route_truth(
    *,
    task: dict[str, Any] | None = None,
    state: dict[str, Any] | None = None,
    artifact_facts: dict[str, Any] | None = None,
) -> HotFollowRouteTruth | None:
    task_obj = _dict(task)
    state_obj = _dict(state)
    artifacts = _dict(artifact_facts)
    candidates: tuple[tuple[str, Any], ...] = (
        ("state.route_truth", state_obj.get("route_truth")),
        ("state.route_event", state_obj.get("route_event")),
        ("state.latest_route_event", state_obj.get("latest_route_event")),
        ("state.current_route_event", state_obj.get("current_route_event")),
        ("task.route_truth", task_obj.get("route_truth")),
        ("task.route_event", task_obj.get("route_event")),
        ("task.latest_route_event", task_obj.get("latest_route_event")),
        ("task.current_route_event", task_obj.get("current_route_event")),
        ("artifact_facts.route_truth", artifacts.get("route_truth")),
        ("artifact_facts.route_event", artifacts.get("route_event")),
        ("artifact_facts.latest_route_event", artifacts.get("latest_route_event")),
    )
    for source, candidate in candidates:
        truth = _route_truth_from_mapping(candidate, source=source)
        if truth is not None:
            return truth
    selected = _dict(artifacts.get("selected_compose_route"))
    if selected and _clean(selected.get("route_truth_source") or selected.get("contract_version")):
        return _route_truth_from_mapping(selected, source="artifact_facts.selected_compose_route")
    return None


def _is_tts_failure_reason(value: Any) -> bool:
    reason = _norm(value)
    return bool(
        reason in _TTS_FAILURE_REASONS
        or reason.startswith("tts_failed")
        or reason.startswith("tts_")
        or "empty_or_invalid_audio" in reason
    )


def _runtime_boundary_rules(task: dict | None) -> dict[str, Any]:
    try:
        from .runtime_loader import get_contract_runtime_refs
        from .projection_rules_runtime import get_projection_rules_runtime

        refs = get_contract_runtime_refs(task or {})
        if refs.projection_rules_ref:
            runtime = get_projection_rules_runtime(refs.projection_rules_ref)
            loaded = runtime.runtime_boundary_rule_freeze_rules
            if isinstance(loaded, dict) and loaded:
                return loaded
    except Exception:
        pass
    return _DEFAULT_RUNTIME_BOUNDARY_RULES


def _current_truth_dominates(
    *,
    rules: dict[str, Any],
    subtitle_ready: bool,
    audio_ready: bool,
    final_exists: bool,
    final_fresh: bool,
) -> bool:
    names = set(
        str(v).strip()
        for v in (((rules.get("historical_event_isolation") or {}).get("current_truth_dominates_when_any")) or [])
        if str(v).strip()
    )
    checks = {
        "subtitle_ready": bool(subtitle_ready),
        "audio_ready": bool(audio_ready),
        "final_exists": bool(final_exists),
        "final_fresh": bool(final_fresh),
    }
    return any(checks.get(name, False) for name in names)


def _should_keep_tts_route(
    *,
    rules: dict[str, Any],
    subtitle_ready: bool,
    target_subtitle_authoritative_source: bool,
    target_subtitle_current_reason: str,
    helper_translate_failed_voice_led: bool,
    explicit_preserve_without_target: bool,
) -> bool:
    if explicit_preserve_without_target:
        return False
    url_rules = rules.get("url_voice_led_standard_dubbing") or {}
    preserve_rules = rules.get("preserve_source_route_resolution") or {}
    keep_when = set(str(v).strip() for v in (url_rules.get("keep_tts_replace_when") or []) if str(v).strip())
    keep_reasons = set(str(v).strip() for v in (url_rules.get("keep_tts_replace_current_reasons") or []) if str(v).strip())
    preserve_keep = set(
        str(v).strip() for v in (preserve_rules.get("preserve_policy_still_uses_tts_route_when") or []) if str(v).strip()
    )
    if "subtitle_ready" in keep_when and subtitle_ready:
        if "target_subtitle_authoritative_source" not in keep_when or target_subtitle_authoritative_source:
            return True
    if target_subtitle_current_reason and target_subtitle_current_reason in keep_reasons:
        return True
    if helper_translate_failed_voice_led and "helper_translate_failed_voice_led" in preserve_keep:
        return True
    if target_subtitle_current_reason == "target_subtitle_translation_incomplete" and "target_subtitle_translation_incomplete" in preserve_keep:
        return True
    return False


def _explicit_preserve_source_without_target(
    *,
    rules: dict[str, Any],
    source_audio_preserved: bool,
    subtitle_ready: bool,
    target_subtitle_current_reason: str,
) -> bool:
    preserve_rules = rules.get("preserve_source_route_resolution") or {}
    explicit_reasons = {
        str(v).strip()
        for v in (preserve_rules.get("explicit_no_target_required_reasons") or [])
        if str(v).strip()
    }
    return bool(
        source_audio_preserved
        and not subtitle_ready
        and target_subtitle_current_reason in explicit_reasons
    )


def _helper_failure_is_side_channel_only(
    *,
    rules: dict[str, Any],
    subtitle_ready: bool,
    audio_ready: bool,
    final_exists: bool,
    final_fresh: bool,
) -> bool:
    coexistence = rules.get("helper_side_channel_coexistence") or {}
    names = {
        str(v).strip()
        for v in (coexistence.get("helper_failure_is_side_channel_only_when_any") or [])
        if str(v).strip()
    }
    checks = {
        "subtitle_ready": bool(subtitle_ready),
        "audio_ready": bool(audio_ready),
        "final_exists": bool(final_exists),
        "final_fresh": bool(final_fresh),
    }
    return any(checks.get(name, False) for name in names)


def _visible_target_text_pending_authority(subtitles: dict[str, Any], *, subtitle_ready: bool) -> bool:
    return bool(
        not subtitle_ready
        and str(
            subtitles.get("primary_editable_text")
            or subtitles.get("edited_text")
            or subtitles.get("srt_text")
            or ""
        ).strip()
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


def _compose_input_from_artifacts(artifacts: dict[str, Any]) -> tuple[bool, bool, bool, str, str]:
    compose_input = _dict(artifacts.get("compose_input"))
    mode = _norm(compose_input.get("mode") or artifacts.get("compose_input_mode"))
    ready = bool(
        compose_input.get("ready")
        or artifacts.get("compose_input_ready")
        or mode in {"direct", "derived_ready"}
    )
    blocked = bool(compose_input.get("blocked") or artifacts.get("compose_input_blocked") or mode == "blocked")
    derive_failed = bool(
        compose_input.get("derive_failed")
        or artifacts.get("compose_input_derive_failed")
        or mode == "derive_failed"
    )
    reason = _clean(
        compose_input.get("failure_code")
        or artifacts.get("compose_input_failure_code")
        or compose_input.get("reason")
        or artifacts.get("compose_input_reason")
        or mode
        or "compose_input_not_ready"
    )
    return ready, blocked, derive_failed, reason, mode


def _subtitle_source_available(subtitle_lane: dict[str, Any]) -> bool:
    return bool(
        _clean(subtitle_lane.get("parse_source_text"))
        or _clean(subtitle_lane.get("raw_source_text"))
        or _clean(subtitle_lane.get("normalized_source_text"))
        or subtitle_lane.get("origin_subtitle_exists")
        or subtitle_lane.get("source_subtitle_exists")
    )


def _target_subtitle_ready(subtitle_lane: dict[str, Any]) -> bool:
    return bool(
        subtitle_lane.get("subtitle_ready")
        and subtitle_lane.get("target_subtitle_current")
        and subtitle_lane.get("target_subtitle_authoritative_source")
    )


def _subtitle_process_state(route: str, subtitle_lane: dict[str, Any]) -> tuple[bool, bool, str, str]:
    if route == "preserve_source_route":
        return False, False, "subtitle_not_required_for_route", "preserve_source_route"
    target_ready = _target_subtitle_ready(subtitle_lane)
    if target_ready:
        return True, True, "target_subtitle_authoritative_current", "ready"
    status = _norm(subtitle_lane.get("status") or subtitle_lane.get("subtitles_status"))
    reason = _clean(
        subtitle_lane.get("target_subtitle_current_reason")
        or subtitle_lane.get("subtitle_ready_reason")
        or subtitle_lane.get("reason")
    )
    if status in {"running", "processing"}:
        return True, False, "target_subtitle_materialization_running", reason or "running"
    if reason in {
        "target_subtitle_translation_incomplete",
        "waiting_for_target_subtitle_translation",
        "helper_output_pending",
        "helper_translate_pending",
    }:
        return True, False, "target_subtitle_materialization_stale_pending", reason
    if _subtitle_source_available(subtitle_lane):
        return True, False, "subtitle_source_available", reason or "target_subtitle_missing"
    if status in {"failed", "error"}:
        return True, False, "subtitle_terminal_failure", reason or "subtitle_failed"
    return True, False, "subtitle_source_missing", reason or "subtitle_missing"


def build_hot_follow_current_attempt(
    *,
    route_truth: HotFollowRouteTruth,
    artifact_facts: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    voice_state: dict[str, Any] | None,
    dub_status: str | None,
    compose_status: str | None,
    composed_reason: str | None,
    final_stale_reason: str | None = None,
) -> HotFollowCurrentAttempt:
    artifacts = _dict(artifact_facts)
    subtitles = _dict(subtitle_lane)
    voice = _dict(voice_state)
    audio_lane = _dict(artifacts.get("audio_lane"))
    route = route_truth.route if route_truth.route in FORMAL_HOT_FOLLOW_ROUTES else "tts_replace_route"

    subtitle_required, subtitle_ready, subtitle_state, subtitle_reason = _subtitle_process_state(route, subtitles)
    compose_input_ready, compose_blocked, compose_derive_failed, compose_input_reason, _compose_input_mode = _compose_input_from_artifacts(artifacts)

    source_audio_preserved = bool(audio_lane.get("source_audio_preserved"))
    tts_audio_ready = bool(voice.get("audio_ready"))
    tts_dub_current = bool(voice.get("dub_current", tts_audio_ready)) and tts_audio_ready
    audio_ready = tts_audio_ready if route == "tts_replace_route" else source_audio_preserved
    audio_ready_reason = (
        _clean(voice.get("audio_ready_reason") or ("ready" if tts_audio_ready else "audio_not_ready"))
        if route == "tts_replace_route"
        else ("ready" if source_audio_preserved else "source_audio_not_preserved")
    )

    route_allowed = route in FORMAL_HOT_FOLLOW_ROUTES
    route_reason = "ready" if route_allowed else "unknown_route"
    if route == "preserve_source_route" and not source_audio_preserved:
        route_allowed = False
        route_reason = "source_audio_not_preserved"

    dub_status_norm = _norm(dub_status or voice.get("status")) or "absent"
    if route == "preserve_source_route":
        dub_state = "dub_not_required_for_route"
        dub_current = False
        dub_current_reason = "dub_not_required_for_route"
    elif not subtitle_ready:
        dub_state = "dub_waiting_for_target_subtitle"
        dub_current = False
        dub_current_reason = "waiting_for_target_subtitle"
    elif tts_dub_current:
        dub_state = "dub_ready_current"
        dub_current = True
        dub_current_reason = _clean(voice.get("dub_current_reason") or "ready")
    elif dub_status_norm in {"running", "processing"}:
        dub_state = "dub_running"
        dub_current = False
        dub_current_reason = "dub_running"
    elif dub_status_norm in {"failed", "error"} or _is_tts_failure_reason(voice.get("audio_ready_reason")):
        dub_state = "dub_retryable_failure"
        dub_current = False
        dub_current_reason = _clean(voice.get("dub_current_reason") or voice.get("audio_ready_reason") or "dub_retryable_failure")
    else:
        dub_state = "dub_waiting_for_target_subtitle" if not subtitle_ready else "dub_missing"
        dub_current = False
        dub_current_reason = _clean(voice.get("dub_current_reason") or voice.get("audio_ready_reason") or "audio_not_ready")

    if compose_blocked:
        compose_allowed = False
        compose_reason = compose_input_reason or "compose_input_blocked"
    elif compose_derive_failed:
        compose_allowed = False
        compose_reason = compose_input_reason or "compose_input_derive_failed"
    elif not route_allowed:
        compose_allowed = False
        compose_reason = route_reason
    elif route == "tts_replace_route" and not subtitle_ready:
        compose_allowed = False
        compose_reason = subtitle_reason or "subtitle_not_ready"
    elif route == "tts_replace_route" and not dub_current:
        compose_allowed = False
        compose_reason = dub_current_reason or "dub_not_current"
    else:
        compose_allowed = True
        compose_reason = "ready"

    compose_execute_allowed = bool(compose_allowed and compose_input_ready)
    final_fresh = bool(final_stale_reason is None and artifacts.get("final_exists") and _norm(composed_reason) == "ready")
    requires_redub = bool(route == "tts_replace_route" and subtitle_ready and not dub_current)
    requires_recompose = bool(compose_allowed and compose_input_ready and not final_fresh and _norm(compose_status) != "running")
    blocking: list[str] = []
    if not compose_allowed:
        blocking.append(compose_reason)
    elif not compose_input_ready:
        blocking.append(compose_input_reason or "compose_input_not_ready")
    pending_class = "none"
    if subtitle_state.endswith("_running") or dub_state == "dub_running" or _norm(compose_status) in {"running", "processing"}:
        pending_class = "running"
    elif subtitle_state.endswith("_stale_pending"):
        pending_class = "stale_waiting_without_progress"
    elif blocking:
        pending_class = "blocked_action_required"

    return HotFollowCurrentAttempt(
        contract_version="hot_follow_current_attempt_contract_v1",
        selected_compose_route=route,
        route_allowed=route_allowed,
        route_allowed_reason=route_reason,
        subtitle_required=subtitle_required,
        subtitle_process_state=subtitle_state,
        subtitle_ready=subtitle_ready,
        subtitle_ready_reason=subtitle_reason,
        target_subtitle_authoritative_current=subtitle_ready,
        target_subtitle_source=_clean(subtitles.get("actual_burn_subtitle_source")) or None,
        dub_process_state=dub_state,
        audio_ready=audio_ready,
        audio_ready_reason=audio_ready_reason,
        dub_current=dub_current,
        dub_current_reason=dub_current_reason,
        compose_input_ready=compose_input_ready,
        compose_allowed=compose_allowed,
        compose_route_allowed=compose_allowed,
        compose_execute_allowed=compose_execute_allowed,
        compose_reason=compose_reason if compose_execute_allowed or not compose_input_ready else compose_reason,
        compose_allowed_reason="ready" if compose_allowed else compose_reason,
        requires_redub=requires_redub,
        requires_recompose=requires_recompose,
        final_fresh=final_fresh,
        final_stale_reason=final_stale_reason,
        route_truth_source=route_truth.source,
        route_truth_reason=route_truth.reason,
        route_event_id=route_truth.event_id,
        pending_class=pending_class,
        blocking=tuple(blocking),
        helper_translate_status=artifacts.get("helper_translate_status"),
        helper_translate_output_state=artifacts.get("helper_translate_output_state"),
        helper_translate_provider_health=artifacts.get("helper_translate_provider_health"),
        helper_translate_warning_only=bool(artifacts.get("helper_translate_warning_only")),
    )


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
    current_attempt = state.get("current_attempt")
    if (
        isinstance(current_attempt, dict)
        and current_attempt.get("selected_compose_route")
        and "compose_allowed" in current_attempt
    ):
        route_name = str(current_attempt.get("selected_compose_route") or "tts_replace_route").strip()
        return {
            "name": route_name,
            "compose_allowed": bool(current_attempt.get("compose_allowed")),
            "compose_route_allowed": bool(current_attempt.get("compose_route_allowed", current_attempt.get("compose_allowed"))),
            "compose_input_ready": bool(current_attempt.get("compose_input_ready")),
            "compose_input_mode": str(current_attempt.get("compose_input_mode") or "").strip(),
            "compose_input_reason": str(current_attempt.get("compose_reason") or "").strip(),
            "compose_execute_allowed": bool(current_attempt.get("compose_execute_allowed")),
            "blocked_reason": "" if current_attempt.get("compose_allowed") else str(current_attempt.get("compose_allowed_reason") or "route_not_allowed").strip(),
            "no_tts_compose_allowed": bool(current_attempt.get("no_tts_compose_allowed")),
            "no_dub_compose_allowed": bool(current_attempt.get("no_dub_compose_allowed")),
        }
    route_truth = read_hot_follow_route_truth(task=task, state=state, artifact_facts=_dict(state.get("artifact_facts")))
    if route_truth is not None:
        attempt = build_hot_follow_current_attempt(
            route_truth=route_truth,
            artifact_facts=_dict(state.get("artifact_facts")),
            subtitle_lane=_dict(state.get("subtitles")),
            voice_state=_dict(state.get("audio")),
            dub_status=str(_dict(state.get("audio")).get("status") or task.get("dub_status") or ""),
            compose_status=str(state.get("compose_status") or task.get("compose_status") or ""),
            composed_reason=str(state.get("composed_reason") or task.get("composed_reason") or ""),
            final_stale_reason=state.get("final_stale_reason") or task.get("final_stale_reason"),
        ).to_dict()
        return {
            "name": attempt["selected_compose_route"],
            "compose_allowed": bool(attempt["compose_allowed"]),
            "compose_route_allowed": bool(attempt["compose_route_allowed"]),
            "compose_input_ready": bool(attempt["compose_input_ready"]),
            "compose_input_mode": str(attempt.get("compose_input_mode") or "").strip(),
            "compose_input_reason": str(attempt.get("compose_reason") or "").strip(),
            "compose_execute_allowed": bool(attempt["compose_execute_allowed"]),
            "blocked_reason": "" if attempt["compose_allowed"] else str(attempt.get("compose_allowed_reason") or "route_not_allowed").strip(),
            "no_tts_compose_allowed": bool(attempt.get("no_tts_compose_allowed")),
            "no_dub_compose_allowed": bool(attempt.get("no_dub_compose_allowed")),
        }
    existing_process = state.get("hot_follow_process_state") or state.get("process_state")
    if isinstance(existing_process, dict) and existing_process.get("selected_compose_route"):
        route_name = str(existing_process.get("selected_compose_route") or "tts_replace_route").strip()
        compose_input = existing_process.get("compose_input") if isinstance(existing_process.get("compose_input"), dict) else {}
        return {
            "name": route_name,
            "compose_allowed": bool(existing_process.get("compose_allowed")),
            "compose_route_allowed": bool(existing_process.get("compose_allowed")),
            "compose_input_ready": bool(existing_process.get("compose_input_ready")),
            "compose_input_mode": str(existing_process.get("compose_input_mode") or "").strip(),
            "compose_input_reason": str(existing_process.get("compose_reason") or "").strip(),
            "compose_execute_allowed": bool(existing_process.get("compose_execute_allowed")),
            "blocked_reason": "" if existing_process.get("compose_allowed") else str(existing_process.get("compose_allowed_reason") or "route_not_allowed").strip(),
            "no_tts_compose_allowed": bool(existing_process.get("no_tts_compose_allowed")),
            "no_dub_compose_allowed": bool(existing_process.get("no_dub_compose_allowed")),
        }
    process_state = reduce_hot_follow_process_state(task=task, state=state)
    route_name = str(process_state.get("selected_compose_route") or "tts_replace_route").strip()
    return {
        "name": route_name,
        "compose_allowed": bool(process_state.get("compose_allowed")),
        "compose_route_allowed": bool(process_state.get("compose_allowed")),
        "compose_input_ready": bool(process_state.get("compose_input_ready")),
        "compose_input_mode": str(process_state.get("compose_input_mode") or "").strip(),
        "compose_input_reason": str(process_state.get("compose_reason") or "").strip(),
        "compose_execute_allowed": bool(process_state.get("compose_execute_allowed")),
        "blocked_reason": "" if process_state.get("compose_allowed") else str(process_state.get("compose_allowed_reason") or "route_not_allowed").strip(),
        "no_tts_compose_allowed": bool(process_state.get("no_tts_compose_allowed")),
        "no_dub_compose_allowed": bool(process_state.get("no_dub_compose_allowed")),
    }

def _legacy_selected_route_from_state(task: dict, state: dict) -> dict[str, Any]:
    rules = _runtime_boundary_rules(task)
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
    visible_target_text_pending_authority = _visible_target_text_pending_authority(
        subtitles,
        subtitle_ready=subtitle_ready,
    )
    target_reason = str(subtitles.get("target_subtitle_current_reason") or subtitles.get("subtitle_ready_reason") or "").strip()
    target_authoritative = bool(subtitles.get("target_subtitle_authoritative_source"))
    final_payload = state.get("final") if isinstance(state.get("final"), dict) else {}
    historical_final = state.get("historical_final") if isinstance(state.get("historical_final"), dict) else {}
    final_exists = bool(final_payload.get("exists") or historical_final.get("exists") or artifact_facts.get("final_exists"))
    final_fresh = bool(state.get("final_fresh") or final_payload.get("fresh"))
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
    explicit_preserve_without_target = _explicit_preserve_source_without_target(
        rules=rules,
        source_audio_preserved=bool(audio_lane.get("source_audio_preserved")),
        subtitle_ready=subtitle_ready,
        target_subtitle_current_reason=target_reason,
    )
    if bool(audio.get("audio_ready")) or bool(audio.get("voiceover_url") or audio.get("tts_voiceover_url") or audio.get("dub_preview_url")):
        route_name = "tts_replace_route"
    current_truth_dominates = _current_truth_dominates(
        rules=rules,
        subtitle_ready=subtitle_ready,
        audio_ready=bool(audio.get("audio_ready")),
        final_exists=final_exists,
        final_fresh=final_fresh,
    )
    if explicit_preserve_without_target:
        route_name = "preserve_source_route"
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
            helper_translate_failed_voice_led=helper_translate_failed_voice_led,
        )
    keep_tts_route = _should_keep_tts_route(
        rules=rules,
        subtitle_ready=subtitle_ready,
        target_subtitle_authoritative_source=target_authoritative,
        target_subtitle_current_reason=target_reason,
        helper_translate_failed_voice_led=helper_translate_failed_voice_led,
        explicit_preserve_without_target=explicit_preserve_without_target,
    )
    stale_no_dub_reasons = {
        str(v).strip()
        for v in (((rules.get("historical_event_isolation") or {}).get("stale_no_dub_reasons_ignored_when_current_truth")) or [])
        if str(v).strip()
    }
    if current_truth_dominates and keep_tts_route and no_dub_reason in stale_no_dub_reasons:
        no_dub = False
        no_dub_reason = ""
        no_dub_compose_allowed = False
    if visible_target_text_pending_authority and no_dub_reason in stale_no_dub_reasons:
        no_dub = False
        no_dub_reason = ""
        no_dub_compose_allowed = False
    if keep_tts_route:
        route_name = "tts_replace_route"
    if visible_target_text_pending_authority and route_name == "no_tts_compose_route":
        route_name = "tts_replace_route"
    if _route_should_stay_tts(
        route_name=route_name,
        subtitles=subtitles,
        audio=audio,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    ):
        route_name = "tts_replace_route"
    audio_ready = bool(audio.get("audio_ready"))
    helper_failure_with_authoritative_subtitle = bool(
        subtitle_ready
        and artifact_facts.get("helper_translate_failed")
        and not audio_ready
    )
    helper_failure_side_channel_only = _helper_failure_is_side_channel_only(
        rules=rules,
        subtitle_ready=subtitle_ready,
        audio_ready=audio_ready,
        final_exists=final_exists,
        final_fresh=final_fresh,
    )
    if helper_failure_with_authoritative_subtitle:
        route_name = "tts_replace_route"
    elif helper_translate_failed_voice_led and not audio_ready:
        route_name = "tts_replace_route"
    if artifact_facts.get("helper_translate_failed") and helper_failure_side_channel_only and route_name != "preserve_source_route":
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
    route_truth = read_hot_follow_route_truth(artifact_facts=artifacts)
    if route_truth is not None:
        attempt = build_hot_follow_current_attempt(
            route_truth=route_truth,
            artifact_facts=artifacts,
            subtitle_lane=subtitle_lane,
            voice_state=voice_state,
            dub_status=dub_status,
            compose_status=compose_status,
            composed_reason=composed_reason,
            final_stale_reason=final_stale_reason,
        )
        payload = attempt.to_dict()
        route = payload["selected_compose_route"]
        no_tts_route = route == "preserve_source_route"
        dub_status_out = (
            "skipped"
            if payload["dub_process_state"] == "dub_not_required_for_route"
            else (
                "done"
                if payload["dub_process_state"] == "dub_ready_current"
                else (
                    "running"
                    if payload["dub_process_state"] == "dub_running"
                    else ("failed" if payload["dub_process_state"] == "dub_retryable_failure" else "pending")
                )
            )
        )
        compose_status_norm = _norm(compose_status) or "never"
        if payload["compose_execute_allowed"] and compose_status_norm not in {"running", "processing"}:
            compose_status_norm = "pending"
        if payload["final_fresh"]:
            compose_status_norm = "done"
        process_state = {
            "version": "hot_follow_current_attempt_contract_v1",
            "selected_compose_route": route,
            "route_allowed": payload["route_allowed"],
            "route_allowed_reason": payload["route_allowed_reason"],
            "subtitle_required": payload["subtitle_required"],
            "subtitle_process_state": payload["subtitle_process_state"],
            "subtitle_step_status": "done" if payload["subtitle_ready"] else ("skipped" if no_tts_route else "pending"),
            "subtitle_terminal_state": "no_dub_route_terminal" if no_tts_route else None,
            "subtitle_translation_waiting_retryable": payload["pending_class"] == "stale_waiting_without_progress",
            "target_subtitle_authoritative_current": payload["target_subtitle_authoritative_current"],
            "dub_process_state": payload["dub_process_state"],
            "dub_step_status": dub_status_out,
            "audio_ready": payload["audio_ready"],
            "audio_ready_reason": payload["audio_ready_reason"],
            "dub_current": payload["dub_current"],
            "dub_current_reason": payload["dub_current_reason"],
            "compose_process_state": "compose_allowed_ready" if payload["compose_allowed"] else "compose_not_allowed",
            "compose_step_status": compose_status_norm,
            "compose_allowed": payload["compose_allowed"],
            "compose_input_ready": payload["compose_input_ready"],
            "compose_execute_allowed": payload["compose_execute_allowed"],
            "compose_allowed_reason": payload["compose_allowed_reason"],
            "compose_reason": payload["compose_reason"],
            "no_tts_compose_allowed": no_tts_route and payload["compose_allowed"],
            "no_dub_compose_allowed": no_tts_route and payload["compose_allowed"],
            "no_dub": no_tts_route,
            "no_dub_reason": "source_audio_preserved_no_tts" if no_tts_route else None,
            "requires_redub": payload["requires_redub"],
            "requires_recompose": payload["requires_recompose"],
            "current_subtitle_source": payload["target_subtitle_source"],
        }
        payload.update(
            {
                "dub_status": dub_status_out,
                "requested_voice": str(voice_state.get("requested_voice") or "").strip() or None,
                "resolved_voice": str(voice_state.get("resolved_voice") or "").strip() or None,
                "actual_provider": str(voice_state.get("actual_provider") or "").strip() or None,
                "compose_status": compose_status_norm,
                "final_stale_reason": final_stale_reason or None,
                "no_tts_compose_allowed": no_tts_route and payload["compose_allowed"],
                "no_dub_compose_allowed": no_tts_route and payload["compose_allowed"],
                "compose_blocked_terminal": bool(_compose_input_from_artifacts(artifacts)[1]),
                "compose_input_derive_failed_terminal": bool(_compose_input_from_artifacts(artifacts)[2]),
                "compose_input_blocked_terminal": bool(_compose_input_from_artifacts(artifacts)[1]),
                "compose_exec_failed_terminal": _norm(compose_status) in {"failed", "error"},
                "compose_terminal_state": None,
                "subtitle_empty_terminal": False,
                "no_dub_route_terminal": no_tts_route,
                "tts_lane_expected": route == "tts_replace_route" and payload["subtitle_ready"],
                "retriable_dub_failure": payload["dub_process_state"] == "dub_retryable_failure",
                "current_attempt_failure_class": "retriable_dub_failure" if payload["dub_process_state"] == "dub_retryable_failure" else None,
                "subtitle_translation_waiting_retryable": payload["pending_class"] == "stale_waiting_without_progress",
                "helper_translate_composite_state": artifacts.get("helper_translate_composite_state"),
                "helper_translate_failed": False,
                "helper_translate_failed_voice_led": False,
                "helper_translate_error_reason": artifacts.get("helper_translate_error_reason"),
                "helper_translate_error_message": artifacts.get("helper_translate_error_message"),
                "helper_translate_retryable": bool(artifacts.get("helper_translate_retryable")),
                "helper_translate_terminal": bool(artifacts.get("helper_translate_terminal")),
                "subtitle_terminal_state": process_state["subtitle_terminal_state"],
                "process_state": process_state,
                "hot_follow_process_state": process_state,
                "current_subtitle_source": payload["target_subtitle_source"],
            }
        )
        return payload

    rules = _runtime_boundary_rules({})
    artifacts = artifact_facts or {}
    compose_status_norm = _norm(compose_status) or "never"
    compose_reason_norm = _norm(composed_reason) or "unknown"
    audio_lane = artifacts.get("audio_lane") if isinstance(artifacts.get("audio_lane"), dict) else {}
    selected = artifacts.get("selected_compose_route") if isinstance(artifacts.get("selected_compose_route"), dict) else {}
    selected_route = str(selected.get("name") or "").strip()
    subtitle_ready = bool(subtitle_lane.get("subtitle_ready"))
    visible_target_text_pending_authority = _visible_target_text_pending_authority(
        subtitle_lane,
        subtitle_ready=subtitle_ready,
    )
    audio_ready = bool(voice_state.get("audio_ready"))
    target_reason = str(
        subtitle_lane.get("target_subtitle_current_reason")
        or subtitle_lane.get("subtitle_ready_reason")
        or ""
    ).strip()
    translation_waiting_retryable = bool(
        not subtitle_ready
        and target_reason
        in {
            "target_subtitle_translation_incomplete",
            "waiting_for_target_subtitle_translation",
        }
        and selected_route == "tts_replace_route"
    )
    target_authoritative = bool(subtitle_lane.get("target_subtitle_authoritative_source"))
    final_exists = bool(artifacts.get("final_exists"))
    final_fresh = bool(final_stale_reason is None and artifacts.get("final_exists") and compose_reason_norm == "ready")
    helper_translate_failed = bool(artifacts.get("helper_translate_failed") and not subtitle_ready)
    helper_translate_failed_voice_led = bool(artifacts.get("helper_translate_failed_voice_led") and helper_translate_failed)
    explicit_preserve_without_target = _explicit_preserve_source_without_target(
        rules=rules,
        source_audio_preserved=bool(audio_lane.get("source_audio_preserved")),
        subtitle_ready=subtitle_ready,
        target_subtitle_current_reason=target_reason,
    )
    if bool(voice_state.get("audio_ready")) or bool(audio_lane.get("tts_voiceover_exists")):
        selected_route = "tts_replace_route"
    current_truth_dominates = _current_truth_dominates(
        rules=rules,
        subtitle_ready=subtitle_ready,
        audio_ready=audio_ready,
        final_exists=final_exists,
        final_fresh=final_fresh,
    )
    no_dub_reason = str(voice_state.get("no_dub_reason") or "").strip() or None
    if explicit_preserve_without_target:
        selected_route = "preserve_source_route"
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
    keep_tts_route = _should_keep_tts_route(
        rules=rules,
        subtitle_ready=subtitle_ready,
        target_subtitle_authoritative_source=target_authoritative,
        target_subtitle_current_reason=target_reason,
        helper_translate_failed_voice_led=helper_translate_failed_voice_led,
        explicit_preserve_without_target=explicit_preserve_without_target,
    )
    stale_no_dub_reasons = {
        str(v).strip()
        for v in (((rules.get("historical_event_isolation") or {}).get("stale_no_dub_reasons_ignored_when_current_truth")) or [])
        if str(v).strip()
    }
    if current_truth_dominates and keep_tts_route and str(no_dub_reason or "").strip() in stale_no_dub_reasons:
        no_dub = False
        no_dub_reason = None
        no_dub_compose_allowed = False
    if visible_target_text_pending_authority and str(no_dub_reason or "").strip() in stale_no_dub_reasons:
        no_dub = False
        no_dub_reason = None
        no_dub_compose_allowed = False
    if keep_tts_route:
        selected_route = "tts_replace_route"
    if visible_target_text_pending_authority and selected_route == "no_tts_compose_route":
        selected_route = "tts_replace_route"
    if _route_should_stay_tts(
        route_name=selected_route,
        subtitles=subtitle_lane,
        audio=voice_state,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    ):
        selected_route = "tts_replace_route"
    helper_failure_side_channel_only = _helper_failure_is_side_channel_only(
        rules=rules,
        subtitle_ready=subtitle_ready,
        audio_ready=audio_ready,
        final_exists=final_exists,
        final_fresh=final_fresh,
    )
    if bool(artifacts.get("helper_translate_failed") and subtitle_ready and not audio_ready):
        selected_route = "tts_replace_route"
    elif helper_translate_failed_voice_led and not audio_ready:
        selected_route = "tts_replace_route"
    if artifacts.get("helper_translate_failed") and helper_failure_side_channel_only:
        helper_translate_failed = False
        helper_translate_failed_voice_led = False
        if selected_route != "preserve_source_route":
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
    dub_status_norm = terminal_dub_lane_state(
        route=selected_route,
        route_allowed=route_allowed,
        dub_status=dub_status,
        no_dub=no_dub,
        no_dub_reason=no_dub_reason,
    )
    if translation_waiting_retryable and dub_status_norm in {"failed", "error", "absent"}:
        dub_status_norm = "pending"
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
    process_state = reduce_hot_follow_process_state(
        task={},
        voice_state=voice_state,
        subtitle_lane=subtitle_lane,
        artifact_facts=artifacts,
        dub_status=dub_status,
        compose_status=compose_status_norm,
        composed_reason=compose_reason_norm,
        final_stale_reason=final_stale_reason,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )
    selected_route = str(process_state.get("selected_compose_route") or selected_route or "tts_replace_route")
    route_allowed = bool(process_state.get("compose_allowed"))
    compose_input_ready = bool(process_state.get("compose_input_ready"))
    compose_execute_allowed = bool(process_state.get("compose_execute_allowed"))
    no_tts_route = selected_route in {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"}
    no_dub_route_terminal = bool(process_state.get("subtitle_terminal_state") == "no_dub_route_terminal")
    if str(process_state.get("selected_compose_route") or "") == "tts_replace_route":
        dub_status_norm = str(process_state.get("dub_step_status") or dub_status_norm).strip()
    translation_waiting_retryable = bool(process_state.get("subtitle_translation_waiting_retryable"))
    retriable_dub_failure = bool(process_state.get("retriable_dub_failure"))
    tts_lane_expected = bool(process_state.get("tts_lane_expected"))
    requires_redub = bool(process_state.get("requires_redub"))
    requires_recompose = bool(process_state.get("requires_recompose"))
    compose_reason_norm = str(process_state.get("compose_reason") or compose_reason_norm)
    compose_status_norm = str(process_state.get("compose_step_status") or compose_status_norm)

    return {
        "dub_status": dub_status_norm,
        "audio_ready": bool(process_state.get("audio_ready")),
        "audio_ready_reason": str(process_state.get("audio_ready_reason") or voice_state.get("audio_ready_reason") or "").strip() or "unknown",
        "dub_current": bool(process_state.get("dub_current")),
        "dub_current_reason": str(process_state.get("dub_current_reason") or voice_state.get("dub_current_reason") or "").strip() or "unknown",
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
        "compose_allowed_reason": str(process_state.get("compose_allowed_reason") or ("ready" if route_allowed else route_reason)),
        "subtitle_empty_terminal": subtitle_empty_terminal,
        "no_dub_route_terminal": no_dub_route_terminal,
        "tts_lane_expected": tts_lane_expected,
        "retriable_dub_failure": retriable_dub_failure,
        "current_attempt_failure_class": "retriable_dub_failure" if retriable_dub_failure else None,
        "subtitle_translation_waiting_retryable": translation_waiting_retryable,
        "helper_translate_status": artifacts.get("helper_translate_status"),
        "helper_translate_output_state": artifacts.get("helper_translate_output_state"),
        "helper_translate_provider_health": artifacts.get("helper_translate_provider_health"),
        "helper_translate_composite_state": artifacts.get("helper_translate_composite_state"),
        "helper_translate_failed": helper_translate_failed,
        "helper_translate_failed_voice_led": helper_translate_failed_voice_led,
        "helper_translate_error_reason": artifacts.get("helper_translate_error_reason"),
        "helper_translate_error_message": artifacts.get("helper_translate_error_message"),
        "helper_translate_retryable": bool(artifacts.get("helper_translate_retryable")),
        "helper_translate_terminal": bool(artifacts.get("helper_translate_terminal")),
        "helper_translate_warning_only": bool(artifacts.get("helper_translate_warning_only")),
        "subtitle_terminal_state": (
            process_state.get("subtitle_terminal_state")
            or (
                "helper_translate_failed_terminal"
                if helper_translate_failed
                else ("subtitle_empty_terminal" if subtitle_empty_terminal else None)
            )
        ),
        "process_state": process_state,
        "hot_follow_process_state": process_state,
        "requires_redub": requires_redub,
        "requires_recompose": requires_recompose,
        "current_subtitle_source": str(
            process_state.get("current_subtitle_source")
            or subtitle_lane.get("actual_burn_subtitle_source")
            or ""
        ).strip() or None,
    }
