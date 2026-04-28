"""Phase C validation: Digital Anchor Delivery Binding."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from gateway.app.services.digital_anchor.delivery_binding import project_delivery_binding

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/digital_anchor/delivery_binding_contract_v1.md"
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
        "digital_anchor_role_manifest",
        "digital_anchor_speaker_segment_bundle",
        "digital_anchor_subtitle_bundle",
        "digital_anchor_audio_bundle",
        "digital_anchor_lip_sync_bundle",
        "digital_anchor_scene_pack",
    }
    assert deliverables["digital_anchor_role_manifest"]["source_ref_id"] == (
        "digital_anchor_role_pack"
    )
    assert deliverables["digital_anchor_speaker_segment_bundle"]["source_ref_id"] == (
        "digital_anchor_speaker_plan"
    )
    assert deliverables["digital_anchor_subtitle_bundle"]["required"] is True
    assert deliverables["digital_anchor_audio_bundle"]["required"] is True
    assert deliverables["digital_anchor_lip_sync_bundle"]["required"] is False
    assert deliverables["digital_anchor_scene_pack"]["required"] is False


def test_result_packet_binding_projects_refs_profiles_and_role_segment_join():
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

    roles = {
        item["role_id"]: item
        for item in _line_ref(packet, "digital_anchor_role_pack")["delta"]["roles"]
    }
    segments = _line_ref(packet, "digital_anchor_speaker_plan")["delta"]["segments"]
    for binding in result["role_segment_bindings"]:
        segment = next(
            item for item in segments if item["segment_id"] == binding["segment_id"]
        )
        role = roles[segment["binds_role_id"]]
        assert binding["binds_role_id"] == segment["binds_role_id"]
        assert binding["role_id"] == role["role_id"]
        assert binding["role_display_name"] == role["display_name"]
        assert binding["appearance_ref"] == role["appearance_ref"]
        assert binding["script_ref"] == segment["script_ref"]


def test_manifest_and_metadata_are_read_only_packet_projection():
    packet = _packet()
    projected = project_delivery_binding(packet)
    manifest = projected["manifest"]

    assert manifest["manifest_id"] == "digital_anchor_delivery_manifest_v1"
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
        "role_feedback",
        "segment_feedback",
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


def test_log_and_evidence_index_record_phase_c_rows():
    log_text = LOG_PATH.read_text(encoding="utf-8")
    index_text = EVIDENCE_INDEX_PATH.read_text(encoding="utf-8")
    for needle in (
        "docs/contracts/digital_anchor/delivery_binding_contract_v1.md",
        "docs/execution/evidence/digital_anchor_phase_c_delivery_binding_v1.md",
        "tests/contracts/digital_anchor/test_delivery_binding_phase_c.py",
    ):
        assert needle in log_text or needle in index_text
