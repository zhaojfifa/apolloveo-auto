"""Hot Follow state inference using the declarative ready-gate engine.

Business contract:
- ``state["final"]`` is the current final only and must be fresh.
- ``state["historical_final"]`` tracks previously successful physical output.
- Physical file existence does not imply current-ready.
"""

from __future__ import annotations

from typing import Any, Dict

from gateway.app.services.contract_runtime.current_attempt_runtime import (
    HOT_FOLLOW_COMPOSE_ROUTES,
    build_hot_follow_current_attempt_summary,
    selected_route_from_state,
)
from gateway.app.services.contract_runtime.ready_gate_runtime import evaluate_contract_ready_gate


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _pick_current_final(task: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    final = _as_dict(state.get("final")) or _as_dict(task.get("final"))
    if bool(final.get("exists")):
        return dict(final)
    return {"exists": False}


def _pick_historical_final(
    task: Dict[str, Any],
    state: Dict[str, Any],
    current_final: Dict[str, Any],
) -> Dict[str, Any]:
    historical = _as_dict(state.get("historical_final"))
    if historical:
        return dict(historical)
    task_final = _as_dict(task.get("historical_final")) or _as_dict(task.get("final"))
    if bool(current_final.get("exists")) and task_final:
        task_final_key = str(task_final.get("key") or "").strip() or None
        current_key = str(current_final.get("key") or "").strip() or None
        if task_final_key and current_key and task_final_key == current_key:
            return {"exists": False}
    if task_final:
        return dict(task_final)
    return {"exists": False}


def _resolve_current_final_url(
    task_id: str,
    task: Dict[str, Any],
    state: Dict[str, Any],
    current_final: Dict[str, Any],
) -> str | None:
    if not bool(current_final.get("exists")):
        return None
    deliverables = state.get("deliverables")
    if isinstance(deliverables, dict):
        final_item = _as_dict(deliverables.get("final_mp4"))
        if final_item.get("url"):
            return str(final_item.get("url"))
    if isinstance(deliverables, list):
        for row in deliverables:
            if not isinstance(row, dict):
                continue
            if str(row.get("kind") or "").strip().lower() == "final" and row.get("url"):
                return str(row.get("url"))
    media = _as_dict(state.get("media")) or _as_dict(task.get("media"))
    extra = _as_dict(state.get("extra")) or _as_dict(task.get("extra"))
    for candidate in (
        current_final.get("url"),
        media.get("final_url"),
        media.get("final_video_url"),
        extra.get("final_video_url"),
        state.get("final_url"),
        state.get("final_video_url"),
    ):
        if candidate:
            return str(candidate)
    if task_id:
        return f"/v1/tasks/{task_id}/final"
    return None


def _resolve_historical_final_url(
    task_id: str,
    _state: Dict[str, Any],
    historical_final: Dict[str, Any],
) -> str | None:
    if historical_final.get("url"):
        return str(historical_final.get("url"))
    if bool(historical_final.get("exists")) and task_id:
        return f"/v1/tasks/{task_id}/final"
    return None


def _resolve_artifacts(task_id: str, task: Dict[str, Any], state: Dict[str, Any]) -> None:
    current_final = _pick_current_final(task, state)
    historical_final = _pick_historical_final(task, state, current_final)

    current_exists = bool(current_final.get("exists"))
    historical_exists = bool(historical_final.get("exists"))
    current_final_url = _resolve_current_final_url(task_id, task, state, current_final)
    historical_final_url = _resolve_historical_final_url(
        task_id, state, historical_final
    )

    current_out = dict(current_final)
    current_out["exists"] = current_exists
    current_out["url"] = current_final_url if current_exists else None
    if not current_exists:
        current_out["key"] = None

    historical_out = dict(historical_final)
    historical_out["exists"] = historical_exists
    historical_out["url"] = historical_final_url if historical_exists else None

    state["final"] = current_out
    state["historical_final"] = historical_out

    media = dict(_as_dict(state.get("media")))
    media["final_url"] = current_final_url if current_exists else None
    media["final_video_url"] = current_final_url if current_exists else None
    state["media"] = media
    state["final_url"] = current_final_url if current_exists else None
    state["final_video_url"] = current_final_url if current_exists else None

    if isinstance(state.get("deliverables"), dict):
        deliverables = dict(state.get("deliverables") or {})
        final_item = dict(_as_dict(deliverables.get("final_mp4")) or {"label": "final.mp4"})
        final_item["url"] = current_final_url if current_exists else None
        final_item["historical"] = bool(historical_exists and not current_exists)
        final_item["status"] = "done" if current_exists else "pending"
        final_item["state"] = "done" if current_exists else "pending"
        deliverables["final_mp4"] = final_item
        state["deliverables"] = deliverables
    elif isinstance(state.get("deliverables"), list):
        patched = []
        seen_final = False
        for item in state.get("deliverables") or []:
            if not isinstance(item, dict):
                patched.append(item)
                continue
            row = dict(item)
            if str(row.get("kind") or "").strip().lower() == "final":
                row["url"] = current_final_url if current_exists else None
                row["historical"] = bool(historical_exists and not current_exists)
                row["status"] = "done" if current_exists else "pending"
                row["state"] = "done" if current_exists else "pending"
                seen_final = True
            patched.append(row)
        if not seen_final:
            patched.append(
                {
                    "kind": "final",
                    "title": "Final Video",
                    "label": "Final Video",
                    "key": current_out.get("key"),
                    "url": current_final_url if current_exists else None,
                    "status": "done" if current_exists else "pending",
                    "state": "done" if current_exists else "pending",
                    "size": None,
                    "sha256": None,
                    "historical": bool(historical_exists and not current_exists),
                }
            )
        state["deliverables"] = patched


def _apply_gate_side_effects(state: Dict[str, Any], gate_result: Dict[str, Any]) -> None:
    compose_ready = bool(gate_result["compose_ready"])
    compose_blocked = bool(gate_result.get("compose_blocked"))
    compose_input_derive_failed = bool(gate_result.get("compose_input_derive_failed_terminal"))
    compose_exec_failed = bool(gate_result.get("compose_exec_failed_terminal"))
    historical_exists = bool((_as_dict(state.get("historical_final"))).get("exists"))

    compose = dict(_as_dict(state.get("compose")))
    last = dict(_as_dict(compose.get("last")))
    if compose_ready:
        last["status"] = "done"
        last["error"] = None
        state["compose_status"] = "done"
    elif compose_blocked:
        last["status"] = "blocked"
        last["error"] = gate_result.get("compose_blocked_reason") or gate_result.get("compose_reason")
        state["compose_status"] = "blocked"
    elif compose_input_derive_failed or compose_exec_failed:
        last["status"] = "failed"
        last["error"] = gate_result.get("compose_input_reason") or gate_result.get("compose_reason")
        state["compose_status"] = "failed"
    else:
        if last:
            last["status"] = "pending"
        state["compose_status"] = "pending"
    if last:
        compose["last"] = last
    state["compose"] = compose

    pipeline = list(_as_list(state.get("pipeline")))
    for step in pipeline:
        if not isinstance(step, dict):
            continue
        if str(step.get("key") or "").strip().lower() != "compose":
            continue
        step_status = (
            "done"
            if compose_ready
            else ("blocked" if compose_blocked else ("failed" if (compose_input_derive_failed or compose_exec_failed) else "pending"))
        )
        step["status"] = step_status
        step["state"] = step_status
        if compose_ready:
            step["error"] = None
            step["message"] = step.get("message") or "final video merge"
        elif compose_blocked:
            step["error"] = gate_result.get("compose_blocked_reason") or gate_result.get("compose_reason")
        elif compose_input_derive_failed or compose_exec_failed:
            step["error"] = gate_result.get("compose_input_reason") or gate_result.get("compose_reason")
    state["pipeline"] = pipeline

    if isinstance(state.get("deliverables"), list):
        for item in state.get("deliverables") or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("kind") or "").strip().lower() != "final":
                continue
            item_status = (
                "done"
                if compose_ready
                else ("blocked" if compose_blocked else ("failed" if (compose_input_derive_failed or compose_exec_failed) else "pending"))
            )
            item["status"] = item_status
            item["state"] = item_status
            item["historical"] = bool(historical_exists and not compose_ready)
            if not compose_ready:
                item["url"] = None
            break


def _selected_route_payload(route_name: str) -> Dict[str, Any]:
    route = HOT_FOLLOW_COMPOSE_ROUTES.get(route_name) or HOT_FOLLOW_COMPOSE_ROUTES["tts_replace_route"]
    return {
        "name": route.name,
        "required_artifacts": route.required_artifacts,
        "optional_artifacts": route.optional_artifacts,
        "irrelevant_artifacts": route.irrelevant_artifacts,
        "allow_conditions": route.allow_conditions,
        "blocked_conditions": route.blocked_conditions,
    }


def _helper_contract_state(
    *,
    subtitles: Dict[str, Any],
    audio: Dict[str, Any],
    final_exists: bool,
    final_fresh: bool,
) -> Dict[str, Any]:
    helper_translation = dict(_as_dict(subtitles.get("helper_translation")))
    status = str(
        subtitles.get("helper_translate_status")
        or helper_translation.get("status")
        or ""
    ).strip().lower()
    failed = bool(
        subtitles.get("helper_translate_failed")
        or helper_translation.get("failed")
    ) or status == "failed"
    translated_text = str(
        subtitles.get("helper_translate_translated_text")
        or helper_translation.get("translated_text")
        or ""
    ).strip()
    provider_health = str(
        subtitles.get("helper_translate_provider_health")
        or helper_translation.get("provider_health")
        or ""
    ).strip() or "provider_ok"
    output_state = str(
        subtitles.get("helper_translate_output_state")
        or helper_translation.get("output_state")
        or ""
    ).strip() or "helper_output_unavailable"
    if translated_text:
        output_state = "helper_output_resolved"
    elif status in {"pending", "running", "queued"}:
        output_state = "helper_output_pending"
    elif output_state not in {
        "helper_output_unavailable",
        "helper_output_pending",
        "helper_output_resolved",
    }:
        output_state = "helper_output_unavailable"
    if failed and provider_health not in {
        "provider_retryable_failure",
        "provider_terminal_failure",
    }:
        provider_health = "provider_retryable_failure"
    elif not failed and provider_health not in {
        "provider_ok",
        "provider_retryable_failure",
        "provider_terminal_failure",
    }:
        provider_health = "provider_ok"
    mainline_recovered = bool(
        subtitles.get("subtitle_ready")
        or audio.get("audio_ready")
        or final_fresh
        or final_exists
    )
    if failed and mainline_recovered:
        current_state = "helper_resolved_with_retryable_provider_warning"
    elif failed:
        current_state = "helper_retryable_failure_warning_only"
    elif status in {"pending", "running", "queued"}:
        current_state = "helper_sidechannel_waiting"
    else:
        current_state = "irrelevant_to_current_mainline_truth"
    return {
        "current_state": current_state,
        "output_state": output_state,
        "provider_health": provider_health,
        "warning_only": current_state in {
            "helper_retryable_failure_warning_only",
            "helper_resolved_with_retryable_provider_warning",
        },
        "side_channel_only": current_state != "helper_sidechannel_waiting",
    }


def _clear_pipeline_error(pipeline: list[Any], key: str) -> None:
    for row in pipeline:
        if not isinstance(row, dict):
            continue
        if str(row.get("key") or "").strip().lower() != key:
            continue
        row["error"] = None
        break


def _reduce_projection_truth(task: Dict[str, Any], state: Dict[str, Any]) -> None:
    subtitles = dict(_as_dict(state.get("subtitles")))
    audio = dict(_as_dict(state.get("audio")))
    errors = dict(_as_dict(state.get("errors")))
    artifact_facts = dict(_as_dict(state.get("artifact_facts")))
    had_artifact_facts = isinstance(state.get("artifact_facts"), dict) and bool(state.get("artifact_facts"))
    had_current_attempt = isinstance(state.get("current_attempt"), dict) and bool(state.get("current_attempt"))
    ready_gate = dict(_as_dict(state.get("ready_gate")))
    pipeline = list(_as_list(state.get("pipeline")))
    pipeline_legacy = dict(_as_dict(state.get("pipeline_legacy")))
    final_payload = _as_dict(state.get("final"))
    historical_final = _as_dict(state.get("historical_final"))
    final_exists = bool(final_payload.get("exists") or historical_final.get("exists") or artifact_facts.get("final_exists"))
    final_fresh = bool(state.get("final_fresh") or final_payload.get("fresh") or ready_gate.get("publish_ready"))
    subtitles_done = str(subtitles.get("status") or "").strip().lower() in {
        "done",
        "ready",
        "success",
        "completed",
    }
    pack_errors = dict(_as_dict(errors.get("pack")))
    pack_status = str(
        state.get("pack_status")
        or (_as_dict(pipeline_legacy.get("pack"))).get("status")
        or ""
    ).strip().lower()
    if not pack_status:
        for row in pipeline:
            if not isinstance(row, dict):
                continue
            if str(row.get("key") or "").strip().lower() == "pack":
                pack_status = str(row.get("status") or "").strip().lower()
                break

    route_truth = selected_route_from_state(task, state)
    route_name = str(route_truth.get("name") or "tts_replace_route").strip() or "tts_replace_route"
    if had_artifact_facts:
        artifact_facts["selected_compose_route"] = _selected_route_payload(route_name)
        state["artifact_facts"] = artifact_facts

    current_attempt = build_hot_follow_current_attempt_summary(
        voice_state=audio,
        subtitle_lane=subtitles,
        dub_status=str(audio.get("status") or state.get("dub_status") or ""),
        compose_status=str(state.get("compose_status") or ""),
        composed_reason=str(state.get("composed_reason") or ""),
        final_stale_reason=state.get("final_stale_reason"),
        artifact_facts=artifact_facts,
        no_dub=bool(audio.get("no_dub")),
        no_dub_compose_allowed=bool(route_truth.get("no_dub_compose_allowed")),
    )
    route_name = str(current_attempt.get("selected_compose_route") or route_name).strip() or "tts_replace_route"
    if had_artifact_facts:
        artifact_facts["selected_compose_route"] = _selected_route_payload(route_name)

    ready_gate["selected_compose_route"] = route_name
    ready_gate["compose_allowed"] = bool(current_attempt.get("compose_allowed"))
    ready_gate["compose_route_allowed"] = bool(current_attempt.get("compose_route_allowed"))
    ready_gate["compose_input_ready"] = bool(current_attempt.get("compose_input_ready"))
    ready_gate["compose_execute_allowed"] = bool(current_attempt.get("compose_execute_allowed"))
    ready_gate["no_tts_compose_allowed"] = bool(current_attempt.get("no_tts_compose_allowed"))
    ready_gate["no_dub_compose_allowed"] = bool(current_attempt.get("no_dub_compose_allowed"))
    state["ready_gate"] = ready_gate

    authoritative_subtitle_truth = bool(
        subtitles.get("target_subtitle_current")
        and subtitles.get("target_subtitle_authoritative_source")
    )
    if subtitles_done:
        subtitles["error"] = None
        _clear_pipeline_error(pipeline, "subtitles")
    if authoritative_subtitle_truth:
        subtitles["subtitle_ready"] = True
        subtitles["subtitle_ready_reason"] = "ready"
        subtitles["target_subtitle_current_reason"] = "ready"
        subtitles["error"] = None
        subtitles["status"] = "done"
        _clear_pipeline_error(pipeline, "subtitles")
        legacy_subtitles = dict(_as_dict(pipeline_legacy.get("subtitles")))
        legacy_subtitles["status"] = "done"
        pipeline_legacy["subtitles"] = legacy_subtitles
        subtitle_errors = dict(_as_dict(errors.get("subtitles")))
        subtitle_errors["reason"] = None
        subtitle_errors["message"] = None
        errors["subtitles"] = subtitle_errors

    audio_done = str(audio.get("status") or "").strip().lower() in {
        "done",
        "ready",
        "success",
        "completed",
    }
    if audio_done and bool(audio.get("audio_ready")):
        audio["error"] = None
        _clear_pipeline_error(pipeline, "dub")
        legacy_audio = dict(_as_dict(pipeline_legacy.get("audio")))
        legacy_audio["status"] = "done"
        pipeline_legacy["audio"] = legacy_audio
        audio_errors = dict(_as_dict(errors.get("audio")))
        audio_errors["reason"] = None
        audio_errors["message"] = None
        errors["audio"] = audio_errors

    if pack_status not in {"failed", "error"}:
        pack_errors["reason"] = None
        pack_errors["message"] = None
        errors["pack"] = pack_errors

    if route_name == "tts_replace_route":
        audio["no_dub"] = False
        audio["no_dub_reason"] = None
        audio["no_dub_compose_allowed"] = False

    helper_state = _helper_contract_state(
        subtitles=subtitles,
        audio=audio,
        final_exists=final_exists,
        final_fresh=final_fresh,
    )
    helper_translation = dict(_as_dict(subtitles.get("helper_translation")))
    helper_translation["contract_state"] = helper_state["current_state"]
    helper_translation["output_state"] = helper_state["output_state"]
    helper_translation["provider_health"] = helper_state["provider_health"]
    subtitles["helper_translation"] = helper_translation
    subtitles["helper_translate_output_state"] = helper_state["output_state"]
    subtitles["helper_translate_provider_health"] = helper_state["provider_health"]
    state["helper"] = helper_state

    state["pipeline"] = pipeline
    state["pipeline_legacy"] = pipeline_legacy
    state["subtitles"] = subtitles
    state["audio"] = audio
    state["errors"] = errors
    state["artifact_facts"] = artifact_facts
    state["current_attempt"] = current_attempt


def compute_hot_follow_state(task: Dict[str, Any], base_state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state: Dict[str, Any] = dict(base_state or {})
    task_id = str(state.get("task_id") or task.get("task_id") or task.get("id") or "")

    state.setdefault("task_id", task_id)
    state.setdefault("kind", task.get("kind", "hot_follow"))

    _resolve_artifacts(task_id, task, state)

    gate_result = evaluate_contract_ready_gate(task, state)
    _apply_gate_side_effects(state, gate_result)

    composed_ready = bool(gate_result["compose_ready"])
    state["composed_ready"] = composed_ready
    state["composed_reason"] = (
        "ready"
        if composed_ready
        else str(state.get("final_stale_reason") or state.get("composed_reason") or "not_ready")
    )
    state["ready_gate"] = gate_result
    _reduce_projection_truth(task, state)
    return state
