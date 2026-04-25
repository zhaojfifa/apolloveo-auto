from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from gateway.app.lines.base import ProductionLine
from gateway.app.services.contract_runtime.advisory_runtime import maybe_resolve_contract_advisory
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.skills_runtime import load_line_skills_bundle, run_loaded_skills_bundle


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HotFollowSkillsBundle:
    bundle_id: str
    line_id: str
    bundle_ref: str
    hook_kind: str


HOT_FOLLOW_ADVISORY_BUNDLE = HotFollowSkillsBundle(
    bundle_id="hot_follow_skills_v1",
    line_id="hot_follow_line",
    bundle_ref="skills/hot_follow",
    hook_kind="advisory_runtime",
)


def resolve_hot_follow_skills_bundle(line: ProductionLine | None) -> HotFollowSkillsBundle | None:
    if line is None:
        return None
    if line.line_id != HOT_FOLLOW_ADVISORY_BUNDLE.line_id:
        return None
    if str(line.skills_bundle_ref or "").strip() != HOT_FOLLOW_ADVISORY_BUNDLE.bundle_ref:
        return None
    return HOT_FOLLOW_ADVISORY_BUNDLE


def build_hot_follow_advisory_input(
    task: dict[str, Any],
    payload: dict[str, Any],
    *,
    line: ProductionLine | None,
) -> dict[str, Any]:
    line_metadata: dict[str, Any] | None = None
    if line is not None:
        line_metadata = {
            "line_id": line.line_id,
            "line_name": line.line_name,
            "line_version": line.line_version,
            "task_kind": line.task_kind,
            "skills_bundle_ref": line.skills_bundle_ref,
        }
    return {
        "task": dict(task or {}),
        "line": line_metadata,
        "ready_gate": dict(payload.get("ready_gate") or {}),
        "pipeline": payload.get("pipeline") or [],
        "pipeline_legacy": dict(payload.get("pipeline_legacy") or {}),
        "deliverables": payload.get("deliverables") or [],
        "media": dict(payload.get("media") or {}),
        "source_video": dict(payload.get("source_video") or {}),
        "artifact_facts": dict(payload.get("artifact_facts") or {}),
        "current_attempt": dict(payload.get("current_attempt") or {}),
        "operator_summary": dict(payload.get("operator_summary") or {}),
    }


def _build_hot_follow_advisory_v1(advisory_input: dict[str, Any]) -> dict[str, Any] | None:
    line_metadata = dict(advisory_input.get("line") or {})
    line = type(
        "LineBindingStub",
        (),
        {
            "line_id": line_metadata.get("line_id"),
            "skills_bundle_ref": line_metadata.get("skills_bundle_ref"),
        },
    )()
    bundle = load_line_skills_bundle(line)
    if bundle is None:
        return None
    execution = run_loaded_skills_bundle(bundle, advisory_input)
    stage_results = dict(execution.get("stage_results") or {})
    advisory = stage_results.get("recovery") or stage_results.get("quality")
    if not isinstance(advisory, dict):
        return None
    return advisory


def _noop_hot_follow_advisory(_advisory_input: dict[str, Any]) -> dict[str, Any] | None:
    return None


_HOT_FOLLOW_ADVISORY_HOOK: Callable[[dict[str, Any]], dict[str, Any] | None] = _build_hot_follow_advisory_v1


def _normalize_advisory_output(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    advisory = {
        "id": str(value.get("id") or "").strip() or None,
        "kind": str(value.get("kind") or "").strip() or None,
        "level": str(value.get("level") or "").strip() or None,
        "recommended_next_action": value.get("recommended_next_action"),
        "operator_hint": value.get("operator_hint"),
        "explanation": value.get("explanation"),
        "evidence": value.get("evidence"),
    }
    if not any(v is not None and v != "" for v in advisory.values()):
        return None
    return advisory


def _inject_selected_compose_route_evidence(
    advisory: dict[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(advisory, dict):
        return None
    current_attempt = dict(payload.get("current_attempt") or {})
    ready_gate = dict(payload.get("ready_gate") or {})
    artifact_facts = dict(payload.get("artifact_facts") or {})
    artifact_route = artifact_facts.get("selected_compose_route")
    if isinstance(artifact_route, dict):
        artifact_route = artifact_route.get("name")
    selected_route = (
        current_attempt.get("selected_compose_route")
        or ready_gate.get("selected_compose_route")
        or artifact_route
    )
    if not selected_route:
        return advisory
    evidence = dict(advisory.get("evidence") or {})
    evidence["selected_compose_route"] = selected_route
    advisory["evidence"] = evidence
    return advisory


def maybe_build_hot_follow_advisory(
    task: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    binding = get_line_runtime_binding(task or payload)
    line = binding.line
    bundle = resolve_hot_follow_skills_bundle(line)
    if bundle is None:
        return None
    contract_advisory = maybe_resolve_contract_advisory(task, payload)
    if contract_advisory is not None:
        return _inject_selected_compose_route_evidence(
            _normalize_advisory_output(contract_advisory),
            payload,
        )
    advisory_input = build_hot_follow_advisory_input(task, payload, line=line)
    try:
        return _inject_selected_compose_route_evidence(
            _normalize_advisory_output(_HOT_FOLLOW_ADVISORY_HOOK(advisory_input)),
            payload,
        )
    except Exception:
        logger.exception(
            "HF_SKILLS_ADVISORY_SAFE_FALLBACK task=%s bundle=%s",
            (task or {}).get("task_id") or (task or {}).get("id"),
            bundle.bundle_id,
        )
        return None
