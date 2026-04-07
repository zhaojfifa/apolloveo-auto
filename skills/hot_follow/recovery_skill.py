from __future__ import annotations

from typing import Any


def run(
    payload: dict[str, Any],
    *,
    defaults: dict[str, Any] | None = None,
    stage_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    _ = payload, defaults
    facts = dict((stage_results or {}).get("input") or {})
    advisory = dict((stage_results or {}).get("quality") or {})
    if not advisory:
        return None

    evidence_fields = list(advisory.pop("evidence_fields", []) or [])
    evidence: dict[str, Any] = {}
    for field in evidence_fields:
        value = facts.get(field)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        evidence[field] = value
    advisory["evidence"] = evidence
    return advisory
