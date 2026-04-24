"""Hot Follow state inference using the declarative ready-gate engine.

Business contract:
- ``state["final"]`` is the current final only and must be fresh.
- ``state["historical_final"]`` tracks previously successful physical output.
- Physical file existence does not imply current-ready.
"""

from __future__ import annotations

from typing import Any, Dict

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
    current_attempt = _as_dict(state.get("current_attempt"))
    waiting_retryable = bool(
        current_attempt.get("subtitle_translation_waiting_retryable")
        or (
            not bool(gate_result.get("subtitle_ready"))
            and not bool(gate_result.get("audio_ready"))
            and str(gate_result.get("subtitle_ready_reason") or "").strip() == "waiting_for_target_subtitle_translation"
            and str(gate_result.get("audio_ready_reason") or "").strip() == "waiting_for_target_subtitle_translation"
            and str(gate_result.get("selected_compose_route") or "").strip() == "tts_replace_route"
            and not bool(gate_result.get("no_dub"))
        )
    )

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
            kind = str(item.get("kind") or "").strip().lower()
            if waiting_retryable and kind in {"subtitle", "audio"}:
                item["status"] = "pending"
                item["state"] = "pending"
                continue
            if kind != "final":
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
    return state
