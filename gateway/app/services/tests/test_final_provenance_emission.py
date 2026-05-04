"""Regression tests for the L3 `final_provenance` emitter on
`HotFollowCurrentAttempt` (Operator Capability Recovery, PR-1).

Authority:
- ``docs/contracts/hot_follow_current_attempt_contract_v1.md``
  §"`final_provenance` Field (Plan D Amendment)"
- ``docs/contracts/publish_readiness_contract_v1.md``
  (final_provenance is consumed verbatim; UI MUST NOT compute it from
   timestamps)

Discipline: the L3 producer emits the closed enum {current, historical}.
The unified publish_readiness producer consumes it; tests in
`test_publish_readiness_unified_producer.py` cover the consumer side.
"""
from __future__ import annotations

from gateway.app.services.contract_runtime.current_attempt_runtime import (
    HotFollowRouteTruth,
    build_hot_follow_current_attempt,
)


def _route(name: str = "tts_replace_route") -> HotFollowRouteTruth:
    return HotFollowRouteTruth(route=name, source="explicit", reason="ready", event_id=None)


def _build(**overrides):
    defaults = dict(
        route_truth=_route(),
        artifact_facts={"final_exists": False},
        subtitle_lane={"subtitle_ready": False},
        voice_state={},
        dub_status="absent",
        compose_status="absent",
        composed_reason="not_ready",
        final_stale_reason=None,
    )
    defaults.update(overrides)
    return build_hot_follow_current_attempt(**defaults)


def test_final_provenance_current_when_no_final_exists() -> None:
    attempt = _build()
    assert attempt.final_provenance == "current"
    assert attempt.to_dict()["final_provenance"] == "current"


def test_final_provenance_current_when_final_fresh_and_no_redo() -> None:
    attempt = _build(
        artifact_facts={
            "final_exists": True,
            "compose_input": {"mode": "ready", "ready": True},
            "audio_lane": {"source_audio_preserved": False},
        },
        subtitle_lane={"subtitle_ready": True, "subtitle_ready_reason": "ready"},
        voice_state={"audio_ready": True, "dub_current": True, "audio_ready_reason": "ready"},
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        final_stale_reason=None,
    )
    assert attempt.final_fresh is True
    assert attempt.final_provenance == "current"


def test_final_provenance_historical_when_final_stale() -> None:
    attempt = _build(
        artifact_facts={"final_exists": True},
        subtitle_lane={"subtitle_ready": True, "subtitle_ready_reason": "ready"},
        voice_state={"audio_ready": True, "dub_current": True},
        dub_status="done",
        compose_status="done",
        composed_reason="not_ready",
        final_stale_reason="subtitle_changed",
    )
    assert attempt.final_fresh is False
    assert attempt.final_provenance == "historical"


def test_final_provenance_historical_when_requires_recompose() -> None:
    """final_exists=True with compose pending re-emission flips provenance.

    Constructed via stale_reason because the producer's `requires_recompose`
    derivation path is internal; provenance fans out from the same stale
    final-exists case the contract names.
    """
    attempt = _build(
        artifact_facts={"final_exists": True},
        subtitle_lane={"subtitle_ready": True, "subtitle_ready_reason": "ready"},
        voice_state={"audio_ready": True, "dub_current": True},
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
        final_stale_reason="dub_changed",
    )
    assert attempt.final_fresh is False
    assert attempt.final_provenance == "historical"


def test_final_provenance_in_to_dict_output() -> None:
    attempt = _build()
    payload = attempt.to_dict()
    assert "final_provenance" in payload
    assert payload["final_provenance"] in {"current", "historical"}
