from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .blocking_reason_runtime import (
    BlockingReasonRuntime,
    filter_publish_ready_blocking,
    get_blocking_reason_runtime,
    scene_pack_pending_reason,
)
from .runtime_loader import get_contract_runtime_refs, load_markdown_yaml_sections


@dataclass(frozen=True)
class ProjectionRulesRuntime:
    ref: str
    projection_source_contract: dict[str, Any]
    publish_surface_rule_contract: dict[str, Any]
    workbench_surface_rule_contract: dict[str, Any]
    dominance_rules: dict[str, Any]
    final_precedence_rules: dict[str, Any]
    compose_route_reason_rules: dict[str, Any]


@lru_cache(maxsize=16)
def get_projection_rules_runtime(ref: str) -> ProjectionRulesRuntime:
    sections = load_markdown_yaml_sections(ref)
    return ProjectionRulesRuntime(
        ref=ref,
        projection_source_contract=dict(sections.get("projection_source_contract") or {}),
        publish_surface_rule_contract=dict(sections.get("publish_surface_rule_contract") or {}),
        workbench_surface_rule_contract=dict(sections.get("workbench_surface_rule_contract") or {}),
        dominance_rules=dict(sections.get("projection_dominance_contract") or {}),
        final_precedence_rules=dict(sections.get("final_precedence_contract") or {}),
        compose_route_reason_rules=dict(sections.get("compose_route_reason_contract") or {}),
    )


def _current_attempt_ready(state: dict[str, Any]) -> bool:
    ready_gate = state.get("ready_gate") if isinstance(state.get("ready_gate"), dict) else {}
    current_attempt = state.get("current_attempt") if isinstance(state.get("current_attempt"), dict) else {}
    return bool(current_attempt.get("audio_ready")) or bool(ready_gate.get("no_dub_compose_allowed"))


def select_presentation_final(
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    *,
    projection_runtime: ProjectionRulesRuntime | None = None,
) -> dict[str, Any]:
    current = final_info if isinstance(final_info, dict) else {}
    historical = historical_final if isinstance(historical_final, dict) else {}
    rules = (projection_runtime.final_precedence_rules if projection_runtime else {}).get("surface_selection") or {}
    prefer_current = bool(rules.get("prefer_current_final_when_exists", True))
    fallback_historical = bool(rules.get("fallback_to_historical_final_when_current_absent", True))
    if prefer_current and bool(current.get("exists")):
        return dict(current)
    if fallback_historical and bool(historical.get("exists")):
        return dict(historical)
    return dict(current or historical or {})


def derive_compose_allowed_reason(
    ready_gate: dict[str, Any],
    projection_runtime: ProjectionRulesRuntime,
) -> str:
    rules = projection_runtime.compose_route_reason_rules.get("compose_allowed_reason") or {}
    if bool(ready_gate.get("compose_allowed")):
        if bool(ready_gate.get("no_dub_compose_allowed")):
            return str(rules.get("allowed_no_dub") or "no_dub_inputs_ready")
        return str(rules.get("allowed_default") or "voiceover_ready")
    for field in rules.get("blocked_fields") or ():
        value = str(ready_gate.get(field) or "").strip()
        if value:
            return value
    return str(rules.get("blocked_default") or "route_not_allowed")


def scene_pack_pending_reason_for_task(
    task: dict[str, Any] | str | None,
    scene_pack: dict[str, Any] | None,
) -> str | None:
    pack = scene_pack if isinstance(scene_pack, dict) else {}
    if bool(pack.get("exists")):
        return None
    refs = get_contract_runtime_refs(task)
    if refs.projection_rules_ref:
        blocking_runtime = get_blocking_reason_runtime(refs.projection_rules_ref)
        return scene_pack_pending_reason(pack.get("status"), blocking_runtime)
    status = str(pack.get("status") or "").strip().lower()
    if status == "running":
        return "scenes.running"
    if status == "failed":
        return "scenes.failed"
    return "scenes.not_ready"


def apply_projection_runtime(
    state: dict[str, Any],
    *,
    surface: str,
    projection_runtime: ProjectionRulesRuntime,
    blocking_runtime: BlockingReasonRuntime | None = None,
) -> dict[str, Any]:
    payload = dict(state or {})
    ready_gate = dict(payload.get("ready_gate") or {})
    final_info = payload.get("final") if isinstance(payload.get("final"), dict) else {}
    scene_pack = payload.get("scene_pack") if isinstance(payload.get("scene_pack"), dict) else {}
    blocking_runtime = blocking_runtime or get_blocking_reason_runtime(projection_runtime.ref)

    final_ready_dominates = bool(
        projection_runtime.dominance_rules.get("final_exists_plus_current_attempt_ready_dominates_publish_truth", True)
        and bool(final_info.get("exists"))
        and bool(payload.get("final_fresh"))
        and _current_attempt_ready(payload)
    )

    if final_ready_dominates:
        payload["composed_ready"] = True
        payload["composed_reason"] = "ready"
        payload["compose_status"] = "done"
        ready_gate["compose_ready"] = True
        ready_gate["publish_ready"] = True
        ready_gate["blocking"] = filter_publish_ready_blocking(
            ready_gate.get("blocking") or [],
            blocking_runtime,
        )
    else:
        ready_gate["blocking"] = blocking_runtime.sort_by_priority(ready_gate.get("blocking") or [])

    if bool(projection_runtime.dominance_rules.get("scene_pack_pending_non_blocking_when_publish_ready", True)):
        payload["scene_pack_pending_reason"] = (
            scene_pack_pending_reason(scene_pack.get("status"), blocking_runtime)
            if not bool(scene_pack.get("exists"))
            else None
        )
        if bool(ready_gate.get("publish_ready")):
            ready_gate["blocking"] = [
                reason
                for reason in ready_gate.get("blocking") or []
                if not blocking_runtime.is_non_blocking(reason)
            ]

    payload["ready_gate"] = ready_gate
    ready_gate["compose_allowed_reason"] = derive_compose_allowed_reason(
        ready_gate,
        projection_runtime,
    )
    payload["compose_allowed"] = bool(ready_gate.get("compose_allowed"))
    payload["compose_allowed_reason"] = ready_gate["compose_allowed_reason"]
    if surface == "workbench" and bool(projection_runtime.dominance_rules.get("compatibility_fields_cannot_override_authoritative_truth", True)):
        payload["composed_ready"] = bool(ready_gate.get("compose_ready", payload.get("composed_ready")))
        if payload["composed_ready"]:
            payload["composed_reason"] = "ready"
    return payload
