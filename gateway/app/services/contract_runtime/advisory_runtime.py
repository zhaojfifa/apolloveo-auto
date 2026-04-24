from __future__ import annotations

from typing import Any

from .projection_rules_runtime import get_projection_rules_runtime
from .runtime_loader import get_contract_runtime_refs


def _compact_evidence(fields: list[str], facts: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for field in fields:
        if field in facts:
            evidence[field] = facts.get(field)
    return evidence


def _advisory_from_rule(rule_key: str, facts: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any] | None:
    advisories = rules.get("advisories") if isinstance(rules.get("advisories"), dict) else {}
    rule = advisories.get(rule_key)
    if not isinstance(rule, dict):
        return None
    evidence_fields = rule.get("evidence_fields") if isinstance(rule.get("evidence_fields"), list) else []
    return {
        "id": str(rule.get("id") or "").strip() or None,
        "kind": str(rule.get("kind") or "operator_guidance").strip() or None,
        "level": str(rule.get("level") or "info").strip() or None,
        "recommended_next_action": rule.get("recommended_next_action"),
        "operator_hint": rule.get("operator_hint"),
        "explanation": rule.get("explanation"),
        "evidence": _compact_evidence([str(field) for field in evidence_fields], facts),
    }


def _advisory_facts(payload: dict[str, Any]) -> dict[str, Any]:
    ready_gate = dict(payload.get("ready_gate") or {})
    artifact_facts = dict(payload.get("artifact_facts") or {})
    current_attempt = dict(payload.get("current_attempt") or {})
    operator_summary = dict(payload.get("operator_summary") or {})
    return {
        "publish_ready": bool(ready_gate.get("publish_ready")),
        "compose_ready": bool(ready_gate.get("compose_ready")),
        "subtitle_ready": bool(ready_gate.get("subtitle_ready")),
        "subtitle_ready_reason": str(ready_gate.get("subtitle_ready_reason") or "").strip() or None,
        "audio_ready": bool(current_attempt.get("audio_ready") or ready_gate.get("audio_ready")),
        "audio_ready_reason": str(
            current_attempt.get("audio_ready_reason") or ready_gate.get("audio_ready_reason") or ""
        ).strip()
        or None,
        "final_exists": bool(artifact_facts.get("final_exists")),
        "audio_exists": bool(artifact_facts.get("audio_exists")),
        "selected_compose_route": str(
            current_attempt.get("selected_compose_route") or ready_gate.get("selected_compose_route") or ""
        ).strip()
        or None,
        "no_tts_compose_allowed": bool(
            current_attempt.get("no_tts_compose_allowed") or ready_gate.get("no_tts_compose_allowed")
        ),
        "no_dub_compose_allowed": bool(
            current_attempt.get("no_dub_compose_allowed") or ready_gate.get("no_dub_compose_allowed")
        ),
        "no_dub_reason": str(ready_gate.get("no_dub_reason") or "").strip() or None,
        "no_dub_route_terminal": bool(current_attempt.get("no_dub_route_terminal")),
        "retriable_dub_failure": bool(current_attempt.get("retriable_dub_failure")),
        "current_attempt_failure_class": current_attempt.get("current_attempt_failure_class"),
        "tts_lane_expected": bool(current_attempt.get("tts_lane_expected")),
        "requires_redub": bool(current_attempt.get("requires_redub")),
        "requires_recompose": bool(current_attempt.get("requires_recompose")),
        "compose_status": str(current_attempt.get("compose_status") or "").strip().lower() or None,
        "last_successful_output_available": operator_summary.get("last_successful_output_available"),
    }


def _select_advisory_key(facts: dict[str, Any], rules: dict[str, Any]) -> str | None:
    selection = rules.get("selection") if isinstance(rules.get("selection"), dict) else {}
    routes = set(selection.get("terminal_no_tts_routes") or ["preserve_source_route", "bgm_only_route", "no_tts_compose_route"])
    if facts["publish_ready"] and facts["compose_ready"] and facts["final_exists"]:
        return str(selection.get("final_ready") or "final_ready")
    if facts["subtitle_ready_reason"] == "waiting_for_target_subtitle_translation":
        return "subtitle_translation_waiting_retryable"
    if facts["retriable_dub_failure"]:
        return str(selection.get("retriable_dub_failure") or "retriable_dub_failure")
    if (
        facts["no_dub_route_terminal"]
        and facts["no_tts_compose_allowed"]
        and facts["selected_compose_route"] in routes
        and facts["no_dub_reason"]
    ):
        return str(selection.get("terminal_no_tts") or "no_dub_route_terminal")
    return None


def maybe_resolve_contract_advisory(
    task: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    refs = get_contract_runtime_refs(task or payload)
    if not refs.projection_rules_ref:
        return None
    runtime = get_projection_rules_runtime(refs.projection_rules_ref)
    rules = runtime.advisory_resolution_rules
    if not rules:
        rules = {}
    facts = _advisory_facts(payload)
    if facts.get("subtitle_ready_reason") == "waiting_for_target_subtitle_translation":
        return {
            "id": "hf_advisory_translation_waiting_retryable",
            "kind": "operator_guidance",
            "level": "info",
            "recommended_next_action": "wait_or_retry_translation",
            "operator_hint": "subtitle translation still pending",
            "explanation": "当前目标字幕翻译尚未就绪，线路处于等待/可重试状态；请等待翻译返回或重试字幕步骤，再继续配音和合成。",
            "evidence": {
                "subtitle_ready": facts.get("subtitle_ready"),
                "subtitle_ready_reason": facts.get("subtitle_ready_reason"),
                "audio_ready": facts.get("audio_ready"),
                "audio_ready_reason": facts.get("audio_ready_reason"),
            },
        }
    rule_key = _select_advisory_key(facts, rules)
    if not rule_key:
        return None
    return _advisory_from_rule(rule_key, facts, rules)
