"""R1: generic_refs must resolve to existing factory contracts."""
from __future__ import annotations

from dataclasses import replace

from gateway.app.services.packet.envelope import GenericRef
from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def test_r1_positive_hot_follow_resolves():
    env = hot_follow_reference_envelope()
    report = validate_packet(env)
    rule_hits = [v for v in report.violations if v.rule_id.startswith("R1")]
    assert rule_hits == [], rule_hits


def test_r1_negative_path_not_found():
    env = hot_follow_reference_envelope()
    bad = list(env.generic_refs) + [
        GenericRef(
            ref_id="g_does_not_exist",
            path="docs/contracts/factory_does_not_exist_contract_v1.md",
            version="v1",
        )
    ]
    env2 = replace(env, generic_refs=tuple(bad))
    report = validate_packet(env2)
    assert any(v.rule_id == "R1.path-not-found" for v in report.violations)
    assert not report.ok


def test_r1_negative_path_shape():
    env = hot_follow_reference_envelope()
    bad = list(env.generic_refs) + [
        GenericRef(
            ref_id="g_wrong_shape",
            path="docs/contracts/hot_follow_line_contract.md",  # not factory-generic
            version="v1",
        )
    ]
    env2 = replace(env, generic_refs=tuple(bad))
    report = validate_packet(env2)
    assert any(v.rule_id == "R1.path-shape" for v in report.violations)
