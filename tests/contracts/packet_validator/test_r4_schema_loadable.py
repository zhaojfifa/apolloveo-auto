"""R4: packet schema must be loadable as JSON Schema Draft 2020-12."""
from __future__ import annotations

import json
from pathlib import Path

from gateway.app.services.packet.validator import validate_packet

from ._fixtures import hot_follow_reference_envelope

DRAFT = "https://json-schema.org/draft/2020-12/schema"


def _write(tmp_path: Path, name: str, payload: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload))
    return p


def test_r4_positive_valid_schema(tmp_path):
    schema_path = _write(
        tmp_path,
        "packet.schema.json",
        {
            "$schema": DRAFT,
            "$id": "apolloveo://packets/hot_follow/v1",
            "type": "object",
        },
    )
    report = validate_packet(hot_follow_reference_envelope(), schema_path=schema_path)
    rule_hits = [v for v in report.violations if v.rule_id.startswith("R4")]
    assert rule_hits == [], rule_hits


def test_r4_negative_draft_mismatch(tmp_path):
    schema_path = _write(
        tmp_path,
        "packet.schema.json",
        {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "$id": "apolloveo://packets/hot_follow/v1",
            "type": "object",
        },
    )
    report = validate_packet(hot_follow_reference_envelope(), schema_path=schema_path)
    assert any(v.rule_id == "R4.draft-mismatch" for v in report.violations)


def test_r4_negative_missing_id(tmp_path):
    schema_path = _write(
        tmp_path,
        "packet.schema.json",
        {"$schema": DRAFT, "type": "object"},
    )
    report = validate_packet(hot_follow_reference_envelope(), schema_path=schema_path)
    assert any(v.rule_id == "R4.missing-id" for v in report.violations)


def test_r4_negative_parse_error(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{this is not json")
    report = validate_packet(hot_follow_reference_envelope(), schema_path=p)
    assert any(v.rule_id == "R4.parse-error" for v in report.violations)
