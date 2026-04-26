"""E1..E5: envelope structural rules from factory_packet_envelope_contract_v1."""
from __future__ import annotations

from dataclasses import replace

from gateway.app.services.packet.envelope import (
    Binding,
    CapabilityPlanItem,
    Evidence,
    LineSpecificRef,
)
from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def test_e1_negative_empty_line_id():
    env = hot_follow_reference_envelope()
    env2 = replace(env, line_id="")
    report = validate_packet(env2)
    assert any(v.rule_id == "E1" for v in report.violations)


def test_e3_negative_dangling_binds_to():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        line_specific_refs=(
            LineSpecificRef(
                ref_id="hot_follow_scene_plan",
                path="docs/contracts/hot_follow_line_contract.md",
                version="v1",
                binds_to=("does_not_exist",),
            ),
        ),
    )
    report = validate_packet(env2)
    assert any(v.rule_id == "E3" for v in report.violations)


def test_e4_negative_invalid_ready_state():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        evidence=replace(env.evidence, ready_state="totally_made_up"),
    )
    report = validate_packet(env2)
    assert any(v.rule_id == "E4" for v in report.violations)


def test_e4_positive_permitted_states():
    env = hot_follow_reference_envelope()
    for st in ("draft", "validating", "ready", "gated", "frozen"):
        env2 = replace(env, evidence=replace(env.evidence, ready_state=st))
        report = validate_packet(env2)
        assert not any(v.rule_id == "E4" for v in report.violations), st


def test_e5_negative_capability_kind_outside_closure():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        binding=Binding(
            worker_profile_ref=env.binding.worker_profile_ref,
            deliverable_profile_ref=env.binding.deliverable_profile_ref,
            asset_sink_profile_ref=env.binding.asset_sink_profile_ref,
            capability_plan=(CapabilityPlanItem(kind="rocket_science"),),
        ),
    )
    report = validate_packet(env2)
    assert any(v.rule_id == "E5" for v in report.violations)
