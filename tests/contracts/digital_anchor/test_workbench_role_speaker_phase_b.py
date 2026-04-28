"""Phase B validation: Digital Anchor Workbench Role / Speaker Surface."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from gateway.app.services.digital_anchor.workbench_role_speaker_surface import (
    project_workbench_role_speaker_surface,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md"
)
SAMPLE = (
    REPO_ROOT
    / "schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json"
)
LOG_PATH = REPO_ROOT / "docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md"
EVIDENCE_INDEX_PATH = REPO_ROOT / "docs/execution/apolloveo_2_0_evidence_index_v1.md"


def _packet() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _line_ref(packet: dict, ref_id: str) -> dict:
    return next(item for item in packet["line_specific_refs"] if item["ref_id"] == ref_id)


def test_phase_b_contract_exists_and_names_required_surfaces():
    text = CONTRACT.read_text(encoding="utf-8")
    for token in (
        "role_surface",
        "speaker_surface",
        "role_segment_binding_surface",
        "scene_binding_projection",
        "attribution_refs",
        "phase_c_deferred",
    ):
        assert token in text


def test_projection_matches_role_pack_delta_exactly():
    packet = _packet()
    projected = project_workbench_role_speaker_surface(packet)
    delta = _line_ref(packet, "digital_anchor_role_pack")["delta"]

    assert projected["role_surface"]["framing_kind_set"] == delta["framing_kind_set"]
    assert (
        projected["role_surface"]["appearance_ref_kind_set"]
        == delta["appearance_ref_kind_set"]
    )
    assert projected["role_surface"]["roles"] == delta["roles"]


def test_projection_matches_speaker_plan_delta_exactly():
    packet = _packet()
    projected = project_workbench_role_speaker_surface(packet)
    delta = _line_ref(packet, "digital_anchor_speaker_plan")["delta"]

    assert projected["speaker_surface"]["dub_kind_set"] == delta["dub_kind_set"]
    assert (
        projected["speaker_surface"]["lip_sync_kind_set"]
        == delta["lip_sync_kind_set"]
    )
    assert projected["speaker_surface"]["segments"] == delta["segments"]


def test_role_segment_binding_resolves_against_role_pack():
    projected = project_workbench_role_speaker_surface(_packet())
    roles = {role["role_id"]: role for role in projected["role_surface"]["roles"]}

    for binding in projected["role_segment_binding_surface"]["bindings"]:
        role = roles[binding["binds_role_id"]]
        assert binding["role_resolved"] is True
        assert binding["role_display_name"] == role["display_name"]
        assert binding["role_framing_kind"] == role["framing_kind"]


def test_scene_binding_projection_is_workbench_scope_only():
    projected = project_workbench_role_speaker_surface(_packet())
    scene = projected["scene_binding_projection"]

    assert scene["scene_contract_ref"] is True
    assert scene["scene_binding_writeback"] == "not_implemented_phase_b"
    assert scene["segments"] == [
        {
            "segment_id": segment["segment_id"],
            "script_ref": segment["script_ref"],
        }
        for segment in projected["speaker_surface"]["segments"]
    ]


def test_attribution_refs_are_packet_provenance_only():
    packet = _packet()
    projected = project_workbench_role_speaker_surface(packet)
    refs = projected["attribution_refs"]

    assert refs["generic_refs"] == [
        {"ref_id": item["ref_id"], "path": item["path"], "version": item["version"]}
        for item in packet["generic_refs"]
    ]
    assert refs["line_specific_refs"] == [
        {
            "ref_id": item["ref_id"],
            "path": item["path"],
            "version": item["version"],
            "binds_to": item["binds_to"],
        }
        for item in packet["line_specific_refs"]
    ]
    assert refs["worker_profile_ref"] == packet["binding"]["worker_profile_ref"]
    assert "deliverable_profile_ref" not in refs
    assert "asset_sink_profile_ref" not in refs


def test_phase_b_projection_does_not_mutate_packet():
    packet = _packet()
    before = deepcopy(packet)
    project_workbench_role_speaker_surface(packet)
    assert packet == before


def test_phase_b_projection_has_no_forbidden_scope_or_runtime_truth():
    projected = project_workbench_role_speaker_surface(_packet())
    text = json.dumps(projected, sort_keys=True)
    forbidden = [
        "vendor_id",
        "model_id",
        "provider_id",
        "engine_id",
        "avatar_engine",
        "tts_provider",
        "lip_sync_engine",
        "matrix_script",
        "hot_follow_business",
        "w2.2",
        "w2.3",
        "delivery_ready",
        "final_ready",
        "publishable",
        "current_attempt",
    ]
    for token in forbidden:
        assert token not in text
    assert "delivery_binding" in projected["phase_c_deferred"]


def test_log_and_evidence_index_record_phase_b_rows():
    log_text = LOG_PATH.read_text(encoding="utf-8")
    index_text = EVIDENCE_INDEX_PATH.read_text(encoding="utf-8")
    for needle in (
        "docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md",
        "docs/execution/evidence/digital_anchor_phase_b_workbench_role_speaker_surface_v1.md",
        "tests/contracts/digital_anchor/test_workbench_role_speaker_phase_b.py",
    ):
        assert needle in log_text or needle in index_text
