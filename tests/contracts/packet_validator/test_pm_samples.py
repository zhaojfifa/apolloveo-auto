"""Gate-level pytest: validate PM-supplied Matrix Script + Digital Anchor packets.

Loads the JSON Sample shipped under `schemas/packets/<line>/sample/` and runs
`gateway.app.services.packet.validator.validate_packet` against the matching
schema. Both samples MUST pass with zero violations / zero missing fields.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from gateway.app.services.packet.entry import validate_packet_dict, validate_packet_path  # noqa: E402
from gateway.app.services.packet.validator import CAPABILITY_KINDS, RULE_SET_VERSION  # noqa: E402


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.mark.parametrize(
    "line_id, sample_name",
    [
        ("matrix_script", "matrix_script_packet_v1.sample.json"),
        ("digital_anchor", "digital_anchor_packet_v1.sample.json"),
    ],
)
def test_pm_sample_passes_validator(repo_root: Path, line_id: str, sample_name: str) -> None:
    sample_path = repo_root / "schemas" / "packets" / line_id / "sample" / sample_name
    schema_path = repo_root / "schemas" / "packets" / line_id / "packet.schema.json"

    assert sample_path.exists(), f"PM sample missing: {sample_path}"
    assert schema_path.exists(), f"schema missing: {schema_path}"

    report = validate_packet_path(sample_path, repo_root=repo_root, schema_path=schema_path)

    assert report.missing == [], f"missing fields: {report.missing}"
    assert report.violations == [], f"violations: {[v.__dict__ for v in report.violations]}"
    assert report.ok is True
    assert report.rule_versions["content_rules"] == RULE_SET_VERSION


def test_new_lines_registered() -> None:
    assert (REPO_ROOT / "schemas/packets/matrix_script/packet.schema.json").exists()
    assert (REPO_ROOT / "schemas/packets/digital_anchor/packet.schema.json").exists()


def test_capability_kinds_cover_new_lines() -> None:
    assert {"variation", "speaker", "avatar", "lip_sync"}.issubset(CAPABILITY_KINDS)


def test_validator_rejects_vendor_pin() -> None:
    bad = {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "generic_refs": [
            {"ref_id": "g_input", "path": "docs/contracts/factory_input_contract_v1.md", "version": "v1"},
            {"ref_id": "g_struct", "path": "docs/contracts/factory_content_structure_contract_v1.md", "version": "v1"},
            {"ref_id": "g_scene", "path": "docs/contracts/factory_scene_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_audio", "path": "docs/contracts/factory_audio_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_lang", "path": "docs/contracts/factory_language_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_deliv", "path": "docs/contracts/factory_delivery_contract_v1.md", "version": "v1"},
        ],
        "line_specific_refs": [],
        "binding": {
            "worker_profile_ref": "wp",
            "deliverable_profile_ref": "dp",
            "asset_sink_profile_ref": "asp",
            "capability_plan": [
                {"kind": "subtitles", "vendor_id": "akool", "mode": "author"}
            ],
        },
        "evidence": {
            "reference_line": "hot_follow",
            "reference_evidence_path": "docs/contracts/hot_follow_line_contract.md",
            "validator_report_path": "x.json",
            "ready_state": "draft",
        },
    }
    report = validate_packet_dict(bad, repo_root=REPO_ROOT)
    rule_ids = {v.rule_id for v in report.violations}
    assert "R3.provider-pin" in rule_ids
    assert "R3.vendor-leak" in rule_ids
    assert report.ok is False


def test_validator_rejects_truth_state_field() -> None:
    bad = {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "generic_refs": [
            {"ref_id": "g_input", "path": "docs/contracts/factory_input_contract_v1.md", "version": "v1"},
            {"ref_id": "g_struct", "path": "docs/contracts/factory_content_structure_contract_v1.md", "version": "v1"},
            {"ref_id": "g_scene", "path": "docs/contracts/factory_scene_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_audio", "path": "docs/contracts/factory_audio_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_lang", "path": "docs/contracts/factory_language_plan_contract_v1.md", "version": "v1"},
            {"ref_id": "g_deliv", "path": "docs/contracts/factory_delivery_contract_v1.md", "version": "v1"},
        ],
        "line_specific_refs": [],
        "binding": {
            "worker_profile_ref": "wp",
            "deliverable_profile_ref": "dp",
            "asset_sink_profile_ref": "asp",
            "capability_plan": [{"kind": "subtitles", "mode": "author"}],
        },
        "line_specific_objects": {"variation_matrix": {"status": "ready"}},
        "evidence": {
            "reference_line": "hot_follow",
            "reference_evidence_path": "docs/contracts/hot_follow_line_contract.md",
            "validator_report_path": "x.json",
            "ready_state": "draft",
        },
    }
    report = validate_packet_dict(bad, repo_root=REPO_ROOT)
    assert any(v.rule_id == "R5.forbidden-field-name" for v in report.violations)
