from __future__ import annotations

from typing import Any


def run(
    payload: dict[str, Any],
    *,
    defaults: dict[str, Any] | None = None,
    stage_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    _ = payload
    routing = dict((stage_results or {}).get("routing") or {})
    facts = dict((stage_results or {}).get("input") or {})
    decision_key = str(routing.get("decision_key") or "").strip()
    if not decision_key:
        return None

    spec = dict(((defaults or {}).get("advisories") or {}).get(decision_key) or {})
    if not spec:
        return None
    explanation = str(spec.get("explanation") or "")
    if explanation:
        explanation = explanation.format(
            expected_subtitle_source=facts.get("expected_subtitle_source") or "mm.srt",
        )
    return {
        "id": str(spec.get("id") or "").strip() or None,
        "kind": str(spec.get("kind") or "operator_guidance").strip() or "operator_guidance",
        "level": str(spec.get("level") or "info").strip() or "info",
        "recommended_next_action": spec.get("recommended_next_action"),
        "operator_hint": spec.get("operator_hint"),
        "explanation": explanation or None,
        "evidence_fields": list(spec.get("evidence_fields") or []),
    }
