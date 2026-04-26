"""R3: capability_plan elements are capability kinds, not vendors."""
from __future__ import annotations

from dataclasses import replace

from gateway.app.services.packet.envelope import Binding, CapabilityPlanItem
from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def test_r3_positive_kinds_only():
    env = hot_follow_reference_envelope()
    report = validate_packet(env)
    rule_hits = [v for v in report.violations if v.rule_id.startswith("R3")]
    assert rule_hits == [], rule_hits


def test_r3_negative_unknown_kind():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        binding=replace(
            env.binding,
            capability_plan=(CapabilityPlanItem(kind="not_a_capability"),),
        ),
    )
    report = validate_packet(env2)
    assert any(v.rule_id == "R3.unknown-kind" for v in report.violations)


def test_r3_negative_vendor_pin_in_extras():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        binding=replace(
            env.binding,
            capability_plan=(
                CapabilityPlanItem(kind="dub", extras={"vendor_id": "azure"}),
            ),
        ),
    )
    report = validate_packet(env2)
    rule_hits = {v.rule_id for v in report.violations}
    assert "R3.provider-pin" in rule_hits or "R3.vendor-leak" in rule_hits
