"""Phase D.1 validation: Digital Anchor publish feedback closure write-back."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from gateway.app.services.digital_anchor.delivery_binding import project_delivery_binding
from gateway.app.services.digital_anchor.publish_feedback_closure import (
    ClosureValidationError,
    InMemoryClosureStore,
    SURFACE_ID,
    append_feedback_closure_record,
    create_closure,
    project_closure_view,
    write_publish_closure,
    write_role_feedback,
    write_segment_feedback,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE = (
    REPO_ROOT
    / "schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json"
)
CONTRACT = (
    REPO_ROOT
    / "docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md"
)
DELIVERY_BINDING = (
    REPO_ROOT / "gateway/app/services/digital_anchor/delivery_binding.py"
)
EVIDENCE = (
    REPO_ROOT
    / "docs/execution/evidence/digital_anchor_phase_d1_publish_feedback_closure_writeback_v1.md"
)
LOG_PATH = REPO_ROOT / "docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md"
INDEX_PATH = REPO_ROOT / "docs/execution/apolloveo_2_0_evidence_index_v1.md"


def _packet() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _delivery(packet: dict) -> dict:
    return project_delivery_binding(packet)


def test_create_closure_copies_identity_from_packet_and_delivery_manifest():
    packet = _packet()
    delivery = _delivery(packet)

    closure = create_closure(packet, delivery)

    assert closure["surface"] == SURFACE_ID
    assert closure["line_id"] == "digital_anchor"
    assert closure["packet_version"] == packet["packet_version"]
    assert closure["delivery_manifest_id"] == delivery["manifest"]["manifest_id"]
    assert closure["deliverable_profile_ref"] == delivery["manifest"][
        "deliverable_profile_ref"
    ]
    assert closure["asset_sink_profile_ref"] == delivery["manifest"][
        "asset_sink_profile_ref"
    ]
    assert closure["role_feedback"] == []
    assert closure["segment_feedback"] == []
    assert closure["publish_url"] is None
    assert closure["publish_status"] == "not_published"
    assert closure["channel_metrics"] == {}
    assert closure["operator_publish_notes"] is None
    assert closure["feedback_closure_records"] == []


def test_role_feedback_joins_to_role_pack_and_appends_record():
    packet = _packet()
    closure = create_closure(packet, _delivery(packet))

    record_id = write_role_feedback(
        closure,
        packet,
        role_id="role_anchor_a",
        role_feedback_kind="accepted",
        role_feedback_note="role accepted",
        record_id="rec_role_1",
        recorded_at="2026-04-28T10:00:00Z",
    )

    assert record_id == "rec_role_1"
    assert closure["role_feedback"] == [
        {
            "role_id": "role_anchor_a",
            "role_display_name": "Anchor A",
            "role_feedback_kind": "accepted",
            "role_feedback_note": "role accepted",
            "linked_segments": ["seg_001", "seg_002"],
        }
    ]
    assert closure["feedback_closure_records"][0] == {
        "record_id": "rec_role_1",
        "recorded_at": "2026-04-28T10:00:00Z",
        "recorded_by": "operator",
        "record_kind": "operator_review",
        "role_ids": ["role_anchor_a"],
        "segment_ids": [],
        "note": "role accepted",
    }


def test_segment_feedback_joins_to_speaker_plan_and_appends_record():
    packet = _packet()
    closure = create_closure(packet, _delivery(packet))

    write_segment_feedback(
        closure,
        packet,
        segment_id="seg_003",
        segment_feedback_kind="needs_revision",
        audio_feedback_note="audio needs review",
        record_id="rec_segment_1",
    )

    assert closure["segment_feedback"] == [
        {
            "segment_id": "seg_003",
            "binds_role_id": "role_anchor_b",
            "script_ref": "content://digital_anchor/v1/seg_003",
            "segment_feedback_kind": "needs_revision",
            "audio_feedback_note": "audio needs review",
            "lip_sync_feedback_note": None,
            "subtitle_feedback_note": None,
        }
    ]
    assert closure["feedback_closure_records"][0]["record_id"] == "rec_segment_1"
    assert closure["feedback_closure_records"][0]["role_ids"] == ["role_anchor_b"]
    assert closure["feedback_closure_records"][0]["segment_ids"] == ["seg_003"]


def test_publish_closure_status_is_scoped_to_closure_object_only():
    packet = _packet()
    delivery = _delivery(packet)
    packet_before = deepcopy(packet)
    delivery_before = deepcopy(delivery)
    closure = create_closure(packet, delivery)

    write_publish_closure(
        closure,
        packet,
        publish_status="published",
        publish_url="https://example.com/digital-anchor/1",
        channel_metrics={
            "views": 100,
            "likes": 10,
            "shares": 3,
            "comments": 2,
            "watch_seconds": 500,
            "captured_at": "2026-04-28T11:00:00Z",
        },
        operator_publish_notes="published and checked",
        role_ids=["role_anchor_a"],
        segment_ids=["seg_001"],
        record_id="rec_publish_1",
    )

    assert closure["publish_status"] == "published"
    assert closure["publish_url"] == "https://example.com/digital-anchor/1"
    assert closure["channel_metrics"]["views"] == 100
    assert closure["operator_publish_notes"] == "published and checked"
    assert closure["feedback_closure_records"][0]["record_kind"] == "publish_callback"
    assert packet == packet_before
    assert delivery == delivery_before
    assert "publish_status" not in json.dumps(packet)
    for section in (
        "delivery_pack",
        "result_packet_binding",
        "manifest",
        "metadata_projection",
    ):
        assert "publish_status" not in json.dumps(delivery[section])


def test_records_are_append_only_and_rows_are_last_write_wins():
    packet = _packet()
    closure = create_closure(packet, _delivery(packet))

    r1 = write_role_feedback(
        closure,
        packet,
        role_id="role_anchor_a",
        role_feedback_kind="needs_revision",
        role_feedback_note="v1",
        record_id="rec_1",
    )
    r2 = write_role_feedback(
        closure,
        packet,
        role_id="role_anchor_a",
        role_feedback_kind="accepted",
        role_feedback_note="v2",
        record_id="rec_2",
    )
    r3 = append_feedback_closure_record(
        closure,
        packet,
        record_kind="correction_note",
        recorded_by="reviewer",
        role_ids=["role_anchor_a"],
        note="kept prior records",
        record_id="rec_3",
    )

    assert [r["record_id"] for r in closure["feedback_closure_records"]] == [
        r1,
        r2,
        r3,
    ]
    assert closure["role_feedback"] == [
        {
            "role_id": "role_anchor_a",
            "role_display_name": "Anchor A",
            "role_feedback_kind": "accepted",
            "role_feedback_note": "v2",
            "linked_segments": ["seg_001", "seg_002"],
        }
    ]


def test_invalid_role_segment_status_and_metrics_are_rejected():
    packet = _packet()
    closure = create_closure(packet, _delivery(packet))

    with pytest.raises(ClosureValidationError):
        write_role_feedback(
            closure,
            packet,
            role_id="missing_role",
            role_feedback_kind="accepted",
        )
    with pytest.raises(ClosureValidationError):
        write_segment_feedback(
            closure,
            packet,
            segment_id="missing_segment",
            segment_feedback_kind="accepted",
        )
    with pytest.raises(ClosureValidationError):
        write_publish_closure(closure, packet, publish_status="ready")
    with pytest.raises(ClosureValidationError):
        write_publish_closure(
            closure,
            packet,
            publish_status="published",
            channel_metrics={"views": -1},
        )
    with pytest.raises(ClosureValidationError):
        write_publish_closure(
            closure,
            packet,
            publish_status="published",
            role_ids=["role_anchor_b"],
            segment_ids=["seg_001"],
        )


def test_in_memory_store_persists_separate_closure_and_returns_isolated_views():
    packet = _packet()
    store = InMemoryClosureStore()
    created = store.create(packet, _delivery(packet), closure_id="closure_a")

    result = store.write_role_feedback(
        created["closure_id"],
        packet,
        role_id="role_anchor_b",
        role_feedback_kind="not_used",
        record_id="rec_store_1",
    )
    fetched = store.get(created["closure_id"])

    assert result["record_id"] == "rec_store_1"
    assert fetched["role_feedback"][0]["role_id"] == "role_anchor_b"
    fetched["role_feedback"][0]["role_feedback_kind"] = "MUTATED"
    assert store.get(created["closure_id"])["role_feedback"][0][
        "role_feedback_kind"
    ] == "not_used"


def test_project_closure_view_is_deepcopy():
    packet = _packet()
    closure = create_closure(packet, _delivery(packet))
    write_role_feedback(
        closure,
        packet,
        role_id="role_anchor_a",
        role_feedback_kind="accepted",
    )

    view = project_closure_view(closure)
    view["role_feedback"][0]["role_feedback_kind"] = "MUTATED"

    assert closure["role_feedback"][0]["role_feedback_kind"] == "accepted"


def test_phase_c_delivery_binding_file_remains_free_of_phase_d_ownership():
    text = DELIVERY_BINDING.read_text(encoding="utf-8")
    assert "digital_anchor_publish_feedback_closure_v1" not in text
    assert "write_publish_closure" not in text
    assert '"publish_status"' in text
    assert '"phase_d_deferred"' in text


def test_phase_d1_evidence_log_and_index_rows_are_present():
    assert EVIDENCE.exists(), f"missing evidence: {EVIDENCE}"
    log_text = LOG_PATH.read_text(encoding="utf-8")
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    for needle in (
        "docs/execution/evidence/digital_anchor_phase_d1_publish_feedback_closure_writeback_v1.md",
        "gateway/app/services/digital_anchor/publish_feedback_closure.py",
        "tests/contracts/digital_anchor/test_publish_feedback_closure_phase_d1.py",
    ):
        assert needle in log_text or needle in index_text


def test_contract_tokens_still_match_phase_d1_writeback_surface():
    text = CONTRACT.read_text(encoding="utf-8")
    for token in (
        SURFACE_ID,
        "role_feedback[]",
        "segment_feedback[]",
        "publish_status",
        "feedback_closure_records[]",
        "append-only",
    ):
        assert token in text
