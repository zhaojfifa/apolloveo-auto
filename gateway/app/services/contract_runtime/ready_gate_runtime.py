from __future__ import annotations

from typing import Any

from gateway.app.services.hot_follow_route_state import selected_route_from_state
from gateway.app.services.ready_gate import evaluate_ready_gate
from gateway.app.services.ready_gate.registry import get_ready_gate_spec

from .blocking_reason_runtime import get_blocking_reason_runtime
from .runtime_loader import get_contract_runtime_refs


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _apply_route_truth(
    task: dict[str, Any],
    state: dict[str, Any],
    gate_result: dict[str, Any],
    *,
    blocking_ref: str | None,
) -> None:
    blocking_runtime = get_blocking_reason_runtime(blocking_ref) if blocking_ref else None
    route = selected_route_from_state(task, state)
    route_name = str(route.get("name") or "").strip()
    compose_allowed = bool(route.get("compose_allowed"))
    compose_route_allowed = bool(route.get("compose_route_allowed", compose_allowed))
    compose_input_ready = bool(route.get("compose_input_ready"))
    compose_execute_allowed = bool(route.get("compose_execute_allowed"))
    compose_input_mode = str(route.get("compose_input_mode") or "").strip().lower()
    compose_input_reason = str(route.get("compose_input_reason") or "").strip()
    compose_status = str(state.get("compose_status") or task.get("compose_status") or "").strip().lower()
    compose_error_reason = str(
        state.get("compose_error_reason")
        or task.get("compose_error_reason")
        or (_as_dict(state.get("compose_error"))).get("reason")
        or (_as_dict(task.get("compose_error"))).get("reason")
        or ""
    ).strip()
    blocked_reason = str(route.get("blocked_reason") or "").strip()

    def _reason(value: str | None) -> str:
        if blocking_runtime is None:
            return str(value or "").strip()
        return blocking_runtime.canonicalize(value)

    gate_result["selected_compose_route"] = route_name
    gate_result["compose_allowed"] = compose_allowed
    gate_result["compose_route_allowed"] = compose_route_allowed
    gate_result["compose_input_ready"] = compose_input_ready
    gate_result["compose_execute_allowed"] = compose_execute_allowed
    gate_result["compose_input_mode"] = compose_input_mode
    gate_result["compose_input_reason"] = _reason(compose_input_reason) or None
    gate_result["no_tts_compose_allowed"] = bool(route.get("no_tts_compose_allowed"))
    gate_result["no_dub_compose_allowed"] = bool(route.get("no_dub_compose_allowed"))
    if gate_result["no_tts_compose_allowed"]:
        gate_result["no_dub"] = True

    if compose_input_mode == "derive_failed":
        reason = _reason(compose_input_reason) or "compose_input_derive_failed"
        gate_result["compose_input_derive_failed_terminal"] = True
        gate_result["compose_input_blocked_terminal"] = False
        gate_result["compose_exec_failed_terminal"] = False
        gate_result["compose_execute_allowed"] = False
        gate_result["compose_reason"] = "compose_input_derive_failed"
        gate_result["compose_input_reason"] = reason
        gate_result["blocking"] = ["compose_input_derive_failed"]
    elif compose_input_mode == "blocked" or blocked_reason == "compose_input_blocked" or bool(gate_result.get("compose_blocked")):
        reason = _reason(gate_result.get("compose_blocked_reason") or blocked_reason or "compose_input_blocked")
        gate_result["compose_blocked"] = True
        gate_result["compose_blocked_reason"] = reason
        gate_result["compose_execute_allowed"] = False
        gate_result["compose_reason"] = reason
        gate_result["blocking"] = [reason]
        gate_result["compose_input_blocked_terminal"] = True
        gate_result["compose_input_derive_failed_terminal"] = False
        gate_result["compose_exec_failed_terminal"] = False
    elif compose_status in {"failed", "error"}:
        reason = _reason(compose_error_reason) or "compose_exec_failed"
        gate_result["compose_exec_failed_terminal"] = True
        gate_result["compose_execute_allowed"] = False
        gate_result["compose_reason"] = reason
        gate_result["blocking"] = ["compose_exec_failed"]
    elif compose_route_allowed and not compose_input_ready and compose_input_mode not in {"", "unknown"}:
        reason = _reason(compose_input_reason) or "compose_input_not_ready"
        gate_result["compose_execute_allowed"] = False
        gate_result["compose_reason"] = reason
        gate_result["blocking"] = [reason]
    elif not compose_allowed and blocked_reason and not str(gate_result.get("no_dub_reason") or "").strip():
        gate_result["compose_reason"] = _reason(blocked_reason)
    elif compose_allowed and gate_result.get("compose_reason") == "route_not_allowed":
        gate_result["compose_reason"] = "compose_not_done"
    elif gate_result["no_tts_compose_allowed"] and not str(gate_result.get("no_dub_reason") or "").strip():
        if route_name == "preserve_source_route":
            gate_result["no_dub_reason"] = "source_audio_preserved_no_tts"
        elif route_name == "bgm_only_route":
            gate_result["no_dub_reason"] = "bgm_only_no_tts"
        elif route_name == "no_tts_compose_route":
            gate_result["no_dub_reason"] = "compose_no_tts"

    if blocking_runtime is not None:
        gate_result["blocking"] = blocking_runtime.normalize_list(gate_result.get("blocking") or [])


def evaluate_contract_ready_gate(
    task: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    refs = get_contract_runtime_refs(task)
    if not refs.ready_gate_ref:
        raise RuntimeError("ready gate ref is not configured for task")
    spec = get_ready_gate_spec(refs.ready_gate_ref)
    gate_result = evaluate_ready_gate(spec, task, state)
    _apply_route_truth(
        task,
        state,
        gate_result,
        blocking_ref=refs.projection_rules_ref,
    )
    return gate_result
