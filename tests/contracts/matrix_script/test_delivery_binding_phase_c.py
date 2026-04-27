"""Phase C validation: Matrix Script Delivery Binding."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from gateway.app.services.matrix_script.delivery_binding import project_delivery_binding

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/matrix_script/delivery_binding_contract_v1.md"
SAMPLE = (
    REPO_ROOT
    / "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json"
)


def _packet() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _line_ref(packet: dict, ref_id: str) -> dict:
    return next(item for item in packet["line_specific_refs"] if item["ref_id"] == ref_id)


def test_phase_c_contract_exists_and_names_required_surfaces():
    text = CONTRACT.read_text(encoding="utf-8")
    for token in (
        "delivery_pack",
        "result_packet_binding",
        "manifest",
        "metadata_projection",
        "phase_d_deferred",
        "publish feedback write-back",
    ):
        assert token in text


def test_delivery_pack_projects_visible_deliverables_from_packet_truth():
    packet = _packet()
    projected = project_delivery_binding(packet)
    pack = projected["delivery_pack"]

    assert pack["deliverable_profile_ref"] == packet["binding"]["deliverable_profile_ref"]
    assert pack["asset_sink_profile_ref"] == packet["binding"]["asset_sink_profile_ref"]

    deliverables = {item["deliverable_id"]: item for item in pack["deliverables"]}
    assert set(deliverables) == {
        "matrix_script_variation_manifest",
        "matrix_script_slot_bundle",
        "matrix_script_subtitle_bundle",
        "matrix_script_audio_preview",
        "matrix_script_scene_pack",
    }
    assert deliverables["matrix_script_variation_manifest"]["source_ref_id"] == (
        "matrix_script_variation_matrix"
    )
    assert deliverables["matrix_script_slot_bundle"]["source_ref_id"] == (
        "matrix_script_slot_pack"
    )
    assert deliverables["matrix_script_audio_preview"]["required"] is False
    assert deliverables["matrix_script_scene_pack"]["required"] is False


def test_result_packet_binding_projects_refs_profiles_and_cell_slot_join():
    packet = _packet()
    projected = project_delivery_binding(packet)
    result = projected["result_packet_binding"]

    assert result["generic_refs"] == [item["ref_id"] for item in packet["generic_refs"]]
    assert result["line_specific_refs"] == [
        item["ref_id"] for item in packet["line_specific_refs"]
    ]
    assert result["binding_profile_refs"] == {
        "worker_profile_ref": packet["binding"]["worker_profile_ref"],
        "deliverable_profile_ref": packet["binding"]["deliverable_profile_ref"],
        "asset_sink_profile_ref": packet["binding"]["asset_sink_profile_ref"],
    }
    assert result["capability_plan"] == [
        {
            "kind": item["kind"],
            "mode": item["mode"],
            "required": item["required"],
        }
        for item in packet["binding"]["capability_plan"]
    ]

    cells = _line_ref(packet, "matrix_script_variation_matrix")["delta"]["cells"]
    slots = {
        item["slot_id"]: item
        for item in _line_ref(packet, "matrix_script_slot_pack")["delta"]["slots"]
    }
    for binding in result["cell_slot_bindings"]:
        cell = next(item for item in cells if item["cell_id"] == binding["cell_id"])
        slot = slots[cell["script_slot_ref"]]
        assert binding["script_slot_ref"] == cell["script_slot_ref"]
        assert binding["slot_id"] == slot["slot_id"]
        assert binding["body_ref"] == slot["body_ref"]


def test_manifest_and_metadata_are_read_only_packet_projection():
    packet = _packet()
    projected = project_delivery_binding(packet)
    manifest = projected["manifest"]

    assert manifest["manifest_id"] == "matrix_script_delivery_manifest_v1"
    assert manifest["line_id"] == packet["line_id"]
    assert manifest["packet_version"] == packet["packet_version"]
    assert manifest["metadata"] == packet["metadata"]
    assert manifest["validator_report_path"] == packet["evidence"]["validator_report_path"]
    assert manifest["packet_ready_state"] == packet["evidence"]["ready_state"]
    assert manifest["write_policy"] == "read_only_phase_c"
    assert projected["metadata_projection"]["display_only"] is True


def test_phase_d_feedback_writeback_is_deferred_not_implemented():
    projected = project_delivery_binding(_packet())
    assert projected["phase_d_deferred"] == [
        "variation_id_feedback",
        "publish_url",
        "publish_status",
        "channel_metrics",
        "operator_publish_notes",
        "feedback_closure_records",
    ]
    text = json.dumps(projected, sort_keys=True)
    assert "feedback_writeback" not in text
    assert "publish_feedback" not in text


def test_phase_c_projection_does_not_mutate_packet():
    packet = _packet()
    before = deepcopy(packet)
    project_delivery_binding(packet)
    assert packet == before


def test_phase_c_projection_has_no_forbidden_scope_or_runtime_truth():
    projected = project_delivery_binding(_packet())
    text = json.dumps(projected, sort_keys=True)
    forbidden = [
        "vendor_id",
        "model_id",
        "provider_id",
        "engine_id",
        "digital_anchor",
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
