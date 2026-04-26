"""Hot Follow reference baseline regression.

Pins the green validator + onboarding-gate outcome that backs
``docs/execution/evidence/hot_follow_reference_packet_validation_v1.md``.
If this fails, the reference green baseline has drifted — fix the cause,
do not relax the test.
"""
from __future__ import annotations

import json
from pathlib import Path

from gateway.app.services.packet.entry import (
    envelope_from_dict,
    validate_packet_path,
)
from gateway.app.services.packet.onboarding_gate import (
    GATE_PASSED,
    evaluate_onboarding,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE = REPO_ROOT / "schemas/packets/hot_follow/sample/reference_packet_v1.json"


def test_hot_follow_reference_validator_is_green():
    report = validate_packet_path(SAMPLE)
    assert report.ok is True
    assert report.violations == []
    assert report.missing == []
    assert report.rule_versions == {
        "content_rules": "v1",
        "envelope_rules": "v1",
    }


def test_hot_follow_reference_onboarding_gate_passes():
    payload = json.loads(SAMPLE.read_text())
    envelope = envelope_from_dict(payload)
    report = validate_packet_path(SAMPLE)
    gate = evaluate_onboarding(envelope, report)
    assert gate.gate_status == GATE_PASSED
    assert gate.blocked_reasons == []
    assert gate.rule_versions["onboarding_gate"] == "v1"
    assert any("reference_evidence:" in link for link in gate.evidence_links)
