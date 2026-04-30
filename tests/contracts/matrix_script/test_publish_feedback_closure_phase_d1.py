"""Phase D.1 validation: Matrix Script publish feedback closure write-back."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from gateway.app.services.matrix_script.delivery_binding import project_delivery_binding
from gateway.app.services.matrix_script.publish_feedback_closure import (
    ClosureValidationError,
    EVENT_KINDS,
    InMemoryClosureStore,
    SURFACE_ID,
    apply_event,
    create_closure,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md"
SAMPLE = (
    REPO_ROOT
    / "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json"
)


def _packet() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _cell_ids(packet: dict) -> list[str]:
    for ref in packet["line_specific_refs"]:
        if ref["ref_id"] == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    return []


def test_create_closure_seeds_one_row_per_variation_cell_and_copies_identity():
    packet = _packet()
    closure = create_closure(packet)

    assert closure["surface"] == SURFACE_ID
    assert closure["line_id"] == "matrix_script"
    assert closure["packet_version"] == packet["packet_version"]
    assert closure["closure_id"]
    cell_ids = _cell_ids(packet)
    assert [row["variation_id"] for row in closure["variation_feedback"]] == cell_ids
    for row in closure["variation_feedback"]:
        assert row["publish_url"] is None
        assert row["publish_status"] == "pending"
        assert row["channel_metrics"] == []
        assert row["operator_publish_notes"] is None
        assert row["last_event_id"] is None
    assert closure["feedback_closure_records"] == []


def test_create_closure_does_not_mutate_packet():
    packet = _packet()
    before = deepcopy(packet)
    create_closure(packet)
    assert packet == before


def test_apply_event_operator_publish_writes_url_and_pending_status_and_appends_record():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]

    event_id = apply_event(
        closure,
        {
            "event_kind": "operator_publish",
            "actor_kind": "operator",
            "variation_id": cell_id,
            "recorded_at": "2026-04-28T10:00:00Z",
            "payload": {"publish_url": "https://example.com/clip/1"},
        },
    )

    row = closure["variation_feedback"][0]
    assert row["publish_url"] == "https://example.com/clip/1"
    assert row["publish_status"] == "pending"
    assert row["last_event_id"] == event_id
    assert len(closure["feedback_closure_records"]) == 1
    record = closure["feedback_closure_records"][0]
    assert record == {
        "event_id": event_id,
        "variation_id": cell_id,
        "event_kind": "operator_publish",
        "recorded_at": "2026-04-28T10:00:00Z",
        "actor_kind": "operator",
        "payload_ref": None,
    }


def test_platform_callback_flips_status_and_can_canonicalize_url():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    apply_event(
        closure,
        {
            "event_kind": "operator_publish",
            "variation_id": cell_id,
            "payload": {"publish_url": "https://stage.example.com/x"},
        },
    )
    apply_event(
        closure,
        {
            "event_kind": "platform_callback",
            "variation_id": cell_id,
            "payload": {
                "publish_status": "published",
                "publish_url": "https://cdn.example.com/x",
            },
        },
    )

    row = closure["variation_feedback"][0]
    assert row["publish_status"] == "published"
    assert row["publish_url"] == "https://cdn.example.com/x"


def test_metrics_snapshot_appends_to_channel_metrics_and_validates_keys():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    apply_event(
        closure,
        {
            "event_kind": "metrics_snapshot",
            "variation_id": cell_id,
            "payload": {
                "channel_id": "youtube",
                "captured_at": "2026-04-28T11:00:00Z",
                "impressions": 100,
                "views": 80,
                "engagement_rate": 0.4,
                "completion_rate": 0.7,
            },
        },
    )
    row = closure["variation_feedback"][0]
    assert len(row["channel_metrics"]) == 1
    assert row["channel_metrics"][0]["channel_id"] == "youtube"

    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "metrics_snapshot",
                "variation_id": cell_id,
                "payload": {
                    "channel_id": "x",
                    "captured_at": "2026-04-28T12:00:00Z",
                    "ctr": 0.1,
                },
            },
        )

    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "metrics_snapshot",
                "variation_id": cell_id,
                "payload": {
                    "channel_id": "x",
                    "captured_at": "2026-04-28T12:00:00Z",
                    "engagement_rate": 1.5,
                },
            },
        )


def test_operator_retract_and_note_apply_minimum_field_rules():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    apply_event(
        closure,
        {"event_kind": "operator_retract", "variation_id": cell_id, "payload": {}},
    )
    apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": cell_id,
            "payload": {"operator_publish_notes": "needs rework"},
        },
    )
    row = closure["variation_feedback"][0]
    assert row["publish_status"] == "retracted"
    assert row["operator_publish_notes"] == "needs rework"


def test_unknown_variation_id_is_rejected():
    closure = create_closure(_packet())
    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "operator_publish",
                "variation_id": "cell_does_not_exist",
                "payload": {},
            },
        )


def test_status_origin_rules_are_enforced():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "operator_publish",
                "variation_id": cell_id,
                "payload": {"publish_status": "published"},
            },
        )
    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "platform_callback",
                "variation_id": cell_id,
                "payload": {"publish_status": "pending"},
            },
        )


def test_actor_kind_must_match_event_kind_origin():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "operator_publish",
                "actor_kind": "platform",
                "variation_id": cell_id,
                "payload": {},
            },
        )


def test_records_are_append_only_and_each_event_appends_one_row():
    packet = _packet()
    closure = create_closure(packet)
    cell_id = _cell_ids(packet)[0]
    e1 = apply_event(
        closure,
        {"event_kind": "operator_publish", "variation_id": cell_id, "payload": {}},
    )
    e2 = apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": cell_id,
            "payload": {"operator_publish_notes": "v1"},
        },
    )
    e3 = apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": cell_id,
            "payload": {"operator_publish_notes": "v2"},
        },
    )
    ids = [r["event_id"] for r in closure["feedback_closure_records"]]
    assert ids == [e1, e2, e3]
    assert closure["variation_feedback"][0]["operator_publish_notes"] == "v2"
    assert closure["variation_feedback"][0]["last_event_id"] == e3


def test_in_memory_store_round_trip_and_isolation():
    store = InMemoryClosureStore()
    packet = _packet()
    created = store.create(packet)
    closure_id = created["closure_id"]
    cell_id = _cell_ids(packet)[0]

    store.apply(
        closure_id,
        {"event_kind": "operator_publish", "variation_id": cell_id, "payload": {}},
    )
    fetched = store.get(closure_id)
    assert fetched["variation_feedback"][0]["publish_status"] == "pending"
    assert len(fetched["feedback_closure_records"]) == 1

    fetched["variation_feedback"][0]["publish_status"] = "MUTATED"
    refetched = store.get(closure_id)
    assert refetched["variation_feedback"][0]["publish_status"] == "pending"


def test_phase_c_delivery_projection_remains_read_only_after_phase_d_writes():
    """The Phase C projection must continue to defer Phase D, not own it."""
    packet = _packet()
    before = project_delivery_binding(packet)

    store = InMemoryClosureStore()
    closure = store.create(packet)
    cell_id = _cell_ids(packet)[0]
    store.apply(
        closure["closure_id"],
        {
            "event_kind": "operator_publish",
            "variation_id": cell_id,
            "payload": {"publish_url": "https://example.com/x"},
        },
    )

    after = project_delivery_binding(packet)
    assert after == before
    assert after["phase_d_deferred"] == [
        "variation_id_feedback",
        "publish_url",
        "publish_status",
        "channel_metrics",
        "operator_publish_notes",
        "feedback_closure_records",
    ]


def test_phase_d1_does_not_introduce_forbidden_scope_tokens():
    closure = create_closure(_packet())
    text = json.dumps(closure, sort_keys=True)
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


def test_phase_d1_contract_freeze_tokens_present_in_contract():
    text = CONTRACT.read_text(encoding="utf-8")
    for token in (
        SURFACE_ID,
        "variation_feedback",
        "feedback_closure_records",
        "channel_metrics",
        "publish_status",
    ):
        assert token in text
    for kind in EVENT_KINDS:
        assert kind in text
