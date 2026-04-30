"""R5: no truth-shape state fields in packet (with envelope.evidence.ready_state exception)."""
from __future__ import annotations

from dataclasses import replace

from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope


def test_r5_positive_clean_packet():
    env = hot_follow_reference_envelope()
    report = validate_packet(env)
    rule_hits = [v for v in report.violations if v.rule_id.startswith("R5")]
    assert rule_hits == [], rule_hits


def test_r5_negative_status_in_metadata():
    env = hot_follow_reference_envelope()
    env2 = replace(env, metadata={**env.metadata, "status": "running"})
    report = validate_packet(env2)
    assert any(v.rule_id == "R5.forbidden-field-name" for v in report.violations)


def test_r5_negative_done_in_line_specific_object():
    env = hot_follow_reference_envelope()
    env2 = replace(
        env,
        line_specific_objects={
            **env.line_specific_objects,
            "hot_follow_scene_plan": {"camera_lock": True, "done": True},
        },
    )
    report = validate_packet(env2)
    assert any(v.rule_id == "R5.forbidden-field-name" for v in report.violations)
