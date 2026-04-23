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
from .runtime_loader import load_markdown_yaml_sections


@dataclass(frozen=True)
class ProjectionRulesRuntime:
    ref: str
    projection_source_contract: dict[str, Any]
    publish_surface_rule_contract: dict[str, Any]
    workbench_surface_rule_contract: dict[str, Any]
    dominance_rules: dict[str, Any]


@lru_cache(maxsize=16)
def get_projection_rules_runtime(ref: str) -> ProjectionRulesRuntime:
    sections = load_markdown_yaml_sections(ref)
    return ProjectionRulesRuntime(
        ref=ref,
        projection_source_contract=dict(sections.get("projection_source_contract") or {}),
        publish_surface_rule_contract=dict(sections.get("publish_surface_rule_contract") or {}),
        workbench_surface_rule_contract=dict(sections.get("workbench_surface_rule_contract") or {}),
        dominance_rules=dict(sections.get("projection_dominance_contract") or {}),
    )


def _current_attempt_ready(state: dict[str, Any]) -> bool:
    ready_gate = state.get("ready_gate") if isinstance(state.get("ready_gate"), dict) else {}
    current_attempt = state.get("current_attempt") if isinstance(state.get("current_attempt"), dict) else {}
    return bool(current_attempt.get("audio_ready")) or bool(ready_gate.get("no_dub_compose_allowed"))


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
        ready_gate["blocking"] = blocking_runtime.normalize_list(ready_gate.get("blocking") or [])

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
    if surface == "workbench" and bool(projection_runtime.dominance_rules.get("compatibility_fields_cannot_override_authoritative_truth", True)):
        payload["composed_ready"] = bool(ready_gate.get("compose_ready", payload.get("composed_ready")))
        if payload["composed_ready"]:
            payload["composed_reason"] = "ready"
    return payload
