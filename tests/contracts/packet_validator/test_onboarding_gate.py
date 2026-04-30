"""Onboarding gate skeleton tests.

Covers the matrix declared in
``gateway/app/services/packet/onboarding_gate.py``.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from gateway.app.services.packet.envelope import (
    Evidence,
    FieldRef,
    PacketValidationReport,
    Violation,
)
from gateway.app.services.packet.onboarding_gate import (
    GATE_BLOCKED,
    GATE_PASSED,
    GATE_PENDING,
    evaluate_onboarding,
)
from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def _green_report() -> PacketValidationReport:
    return validate_packet(hot_follow_reference_envelope())


def test_ready_plus_green_validator_passes():
    envelope = hot_follow_reference_envelope()
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_PASSED
    assert gate.blocked_reasons == []
    assert gate.rule_versions["onboarding_gate"] == "v1"


def test_draft_returns_pending():
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=replace(envelope.evidence, ready_state="draft"),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_PENDING


def test_validating_returns_pending():
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=replace(envelope.evidence, ready_state="validating"),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_PENDING


def test_gated_blocks_with_reasons():
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=replace(envelope.evidence, ready_state="gated"),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_BLOCKED
    assert gate.blocked_reasons  # non-empty


def test_ready_plus_validator_violations_blocks():
    envelope = hot_follow_reference_envelope()
    bad_report = PacketValidationReport(
        ok=False,
        missing=[],
        violations=[
            Violation(
                rule_id="R3.unknown-kind",
                field=FieldRef(path="binding.capability_plan[0].kind"),
                reason="unknown",
            )
        ],
        advisories=[],
        rule_versions={"content_rules": "v1", "envelope_rules": "v1"},
    )
    gate = evaluate_onboarding(envelope, bad_report)
    assert gate.gate_status == GATE_BLOCKED
    assert any("R3.unknown-kind" in r for r in gate.blocked_reasons)


def test_missing_reference_evidence_blocks(tmp_path: Path):
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=Evidence(
            reference_line="hot_follow",
            reference_evidence_path="docs/contracts/_does_not_exist.md",
            validator_report_path=None,
            ready_state="ready",
        ),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_BLOCKED
    assert any("reference_evidence_path" in r for r in gate.blocked_reasons)


def test_invalid_ready_state_blocks():
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=replace(envelope.evidence, ready_state="bogus"),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_BLOCKED
    assert any("outside permitted set" in r for r in gate.blocked_reasons)


def test_frozen_plus_green_passes():
    envelope = hot_follow_reference_envelope()
    envelope = replace(
        envelope,
        evidence=replace(envelope.evidence, ready_state="frozen"),
    )
    gate = evaluate_onboarding(envelope, _green_report())
    assert gate.gate_status == GATE_PASSED
