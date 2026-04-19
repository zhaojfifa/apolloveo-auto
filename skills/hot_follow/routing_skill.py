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
    if not facts:
        return None

    current_subtitle_source = facts.get("current_subtitle_source")
    expected_subtitle_source = facts.get("expected_subtitle_source")
    if current_subtitle_source and current_subtitle_source != expected_subtitle_source:
        return {"decision_key": "subtitle_source_mismatch"}

    if facts.get("compose_blocked"):
        return {"decision_key": "compose_blocked"}

    if facts.get("no_dub_route_terminal"):
        return {"decision_key": "no_dub_route_terminal"}

    if facts.get("requires_recompose"):
        return {"decision_key": "recompose_required"}

    if facts.get("subtitle_ready") and facts.get("audio_ready") and not facts.get("final_exists"):
        return {"decision_key": "compose_missing_final"}

    if facts.get("subtitle_ready") and not facts.get("audio_ready"):
        return {"decision_key": "refresh_dub"}

    if not facts.get("subtitle_ready"):
        return {"decision_key": "review_subtitles"}

    if facts.get("publish_ready") and facts.get("compose_ready") and facts.get("final_exists"):
        return {"decision_key": "final_ready"}

    return None
