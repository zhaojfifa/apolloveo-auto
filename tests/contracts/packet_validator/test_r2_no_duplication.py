"""R2: no generic-shape duplication in line-specific objects."""
from __future__ import annotations

from dataclasses import replace

from gateway.app.services.packet.envelope import LineSpecificRef
from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def test_r2_positive_bound_extension():
    env = hot_follow_reference_envelope()
    report = validate_packet(env)
    rule_hits = [v for v in report.violations if v.rule_id.startswith("R2")]
    assert rule_hits == [], rule_hits


def test_r2_negative_unbound_generic_shape():
    env = hot_follow_reference_envelope()
    # Add a line-specific object whose name uses a generic-shape suffix but
    # does not bind to any generic_ref.
    env2 = replace(
        env,
        line_specific_refs=tuple(env.line_specific_refs)
        + (
            LineSpecificRef(
                ref_id="rogue_delivery",
                path="docs/contracts/some_line_delivery_v1.md",
                version="v1",
                binds_to=(),
            ),
        ),
        line_specific_objects={
            **env.line_specific_objects,
            "rogue_delivery": {"final_video_path": "x"},
        },
    )
    report = validate_packet(env2)
    assert any(v.rule_id.startswith("R2") for v in report.violations)
    assert not report.ok
