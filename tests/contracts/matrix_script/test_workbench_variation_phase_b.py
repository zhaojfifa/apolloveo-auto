"""Phase B validation: Matrix Script Workbench Variation Surface."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from gateway.app.services.matrix_script.workbench_variation_surface import (
    project_workbench_variation_surface,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md"
)
SAMPLE = (
    REPO_ROOT
    / "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json"
)


def _packet() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _line_ref(packet: dict, ref_id: str) -> dict:
    return next(item for item in packet["line_specific_refs"] if item["ref_id"] == ref_id)


def test_phase_b_contract_exists_and_names_required_surfaces():
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "variation_plan",
        "copy_bundle",
        "slot_detail_surface",
        "attribution_refs",
        "publish_feedback_projection",
        "delivery binding",
        "publish feedback write-back",
    ]
    for token in required:
        assert token in text


def test_projection_matches_variation_matrix_delta_exactly():
    packet = _packet()
    projected = project_workbench_variation_surface(packet)
    delta = _line_ref(packet, "matrix_script_variation_matrix")["delta"]

    assert projected["variation_plan"]["axis_kind_set"] == delta["axis_kind_set"]
    assert projected["variation_plan"]["axes"] == delta["axes"]
    assert projected["variation_plan"]["cells"] == delta["cells"]


def test_projection_matches_slot_pack_delta_exactly():
    packet = _packet()
    projected = project_workbench_variation_surface(packet)
    delta = _line_ref(packet, "matrix_script_slot_pack")["delta"]

    assert projected["copy_bundle"]["slot_kind_set"] == delta["slot_kind_set"]
    assert projected["copy_bundle"]["slots"] == delta["slots"]
    assert projected["slot_detail_surface"]["slots"] == delta["slots"]
    assert (
        projected["slot_detail_surface"]["join_rule"]
        == "variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id"
    )


def test_projection_cell_slot_refs_resolve_for_sample():
    projected = project_workbench_variation_surface(_packet())
    slot_ids = {slot["slot_id"] for slot in projected["copy_bundle"]["slots"]}
    for cell in projected["variation_plan"]["cells"]:
        assert cell["script_slot_ref"] in slot_ids


def test_attribution_refs_are_packet_provenance_only():
    packet = _packet()
    projected = project_workbench_variation_surface(packet)
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


def test_publish_feedback_projection_is_read_only_placeholder():
    packet = _packet()
    projected = project_workbench_variation_surface(packet)
    feedback = projected["publish_feedback_projection"]

    assert feedback == {
        "reference_line": packet["evidence"]["reference_line"],
        "validator_report_path": packet["evidence"]["validator_report_path"],
        "ready_state": packet["evidence"]["ready_state"],
        "feedback_writeback": "not_implemented_phase_b",
    }
    forbidden = {"variation_id", "publish_status", "publish_url", "ctr", "impressions"}
    assert forbidden.isdisjoint(feedback)


def test_phase_b_projection_does_not_mutate_packet():
    packet = _packet()
    before = deepcopy(packet)
    project_workbench_variation_surface(packet)
    assert packet == before


def test_phase_b_projection_has_no_forbidden_scope_or_truth_fields():
    projected = project_workbench_variation_surface(_packet())
    text = json.dumps(projected, sort_keys=True)
    forbidden = [
        "vendor_id",
        "model_id",
        "provider_id",
        "engine_id",
        "digital_anchor",
        "hot_follow_business",
        "delivery_ready",
        "final_ready",
        "publishable",
    ]
    for token in forbidden:
        assert token not in text
    assert projected["result_packet_binding"]["delivery_binding"] == "not_implemented_phase_b"
