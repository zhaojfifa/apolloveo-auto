"""OWC-DA PR-2 / DA-W7 — additive REVIEW_ZONE_VALUES closed enum tests.

The only contract touch authorised by OWC-DA gate spec §3 DA-W7 is an
additive closed-set extension on the ``operator_note`` event payload of
the Digital Anchor publish-feedback closure (mirrors OWC-MS MS-W5).

These tests assert:
- The enum membership exactly matches the gate spec wording
  ``audition / video_preview / subtitle / cadence / qc``.
- A valid ``review_zone`` flows onto the appended record only.
- An invalid ``review_zone`` raises ``ClosureValidationError``.
- ``operator_note`` without ``review_zone`` remains valid (legacy path).
- The closure shape envelope, ``D1_EVENT_KINDS``,
  ``D1_PUBLISH_STATUS_VALUES``, ``D1_ROW_SCOPES`` are byte-stable.
- The Matrix Script closure remains unaffected.
"""
from __future__ import annotations

from gateway.app.services.digital_anchor.publish_feedback_closure import (
    ClosureValidationError,
    D1_EVENT_KINDS,
    D1_PUBLISH_STATUS_VALUES,
    D1_ROW_SCOPES,
    REVIEW_ZONE_VALUES,
    apply_writeback_event,
    create_closure,
)
from gateway.app.services.digital_anchor.delivery_binding import (
    project_delivery_binding,
)


def _packet() -> dict:
    return {
        "line_id": "digital_anchor",
        "packet_version": "v1",
        "binding": {
            "deliverable_profile_ref": "ref://da/delivery_profile",
            "asset_sink_profile_ref": "ref://da/sink",
            "capability_plan": [],
        },
        "evidence": {"ready_state": "ready"},
        "metadata": {"notes": "test"},
        "generic_refs": [],
        "line_specific_refs": [
            {
                "ref_id": "digital_anchor_role_pack",
                "delta": {
                    "roles": [
                        {"role_id": "host_lead", "display_name": "主播", "framing_kind": "head"},
                    ],
                },
            },
            {
                "ref_id": "digital_anchor_speaker_plan",
                "delta": {
                    "segments": [
                        {
                            "segment_id": "seg_01",
                            "binds_role_id": "host_lead",
                            "script_ref": "content://da/seg/seg_01",
                            "language_pick": "en-US",
                        },
                    ],
                },
            },
        ],
    }


def _closure() -> dict:
    pkt = _packet()
    return create_closure(pkt, project_delivery_binding(pkt), closure_id="closure_test_001")


def test_review_zone_values_membership_matches_gate_spec() -> None:
    assert REVIEW_ZONE_VALUES == frozenset(
        {"audition", "video_preview", "subtitle", "cadence", "qc"}
    )


def test_review_zone_values_is_immutable_frozenset() -> None:
    assert isinstance(REVIEW_ZONE_VALUES, frozenset)


def test_d1_event_kinds_byte_stable() -> None:
    assert D1_EVENT_KINDS == frozenset(
        {
            "publish_attempted",
            "publish_accepted",
            "publish_rejected",
            "publish_retracted",
            "metrics_snapshot",
            "operator_note",
        }
    )


def test_d1_publish_status_values_byte_stable() -> None:
    assert D1_PUBLISH_STATUS_VALUES == frozenset(
        {"pending", "published", "failed", "retracted"}
    )


def test_d1_row_scopes_byte_stable() -> None:
    assert D1_ROW_SCOPES == frozenset({"role", "segment"})


def test_operator_note_with_valid_review_zone_appends_to_record() -> None:
    closure = _closure()
    pkt = _packet()
    apply_writeback_event(
        closure,
        pkt,
        event_kind="operator_note",
        row_scope="role",
        row_id="host_lead",
        actor_kind="operator",
        payload={"operator_publish_notes": "试听通过", "review_zone": "audition"},
    )
    last_record = closure["feedback_closure_records"][-1]
    assert last_record["event_kind"] == "operator_note"
    assert last_record["review_zone"] == "audition"


def test_operator_note_without_review_zone_omits_field_on_record() -> None:
    closure = _closure()
    pkt = _packet()
    apply_writeback_event(
        closure,
        pkt,
        event_kind="operator_note",
        row_scope="segment",
        row_id="seg_01",
        actor_kind="operator",
        payload={"operator_publish_notes": "legacy 留言"},
    )
    last_record = closure["feedback_closure_records"][-1]
    assert "review_zone" not in last_record


def test_operator_note_with_unknown_review_zone_raises() -> None:
    closure = _closure()
    pkt = _packet()
    try:
        apply_writeback_event(
            closure,
            pkt,
            event_kind="operator_note",
            row_scope="role",
            row_id="host_lead",
            actor_kind="operator",
            payload={"operator_publish_notes": "x", "review_zone": "lighting"},
        )
    except ClosureValidationError as exc:
        assert "review_zone" in str(exc)
    else:  # pragma: no cover - the call should always raise
        raise AssertionError("expected ClosureValidationError")


def test_operator_note_review_zone_does_not_change_row_shape() -> None:
    closure = _closure()
    pkt = _packet()
    apply_writeback_event(
        closure,
        pkt,
        event_kind="operator_note",
        row_scope="role",
        row_id="host_lead",
        actor_kind="operator",
        payload={"operator_publish_notes": "已校对", "review_zone": "subtitle"},
    )
    role_row = closure["role_feedback"][-1]
    # the row gets the note as before; no review_zone column on the row
    assert role_row["role_feedback_note"] == "已校对"
    assert "review_zone" not in role_row


def test_review_zone_does_not_leak_onto_non_operator_note_event() -> None:
    closure = _closure()
    pkt = _packet()
    apply_writeback_event(
        closure,
        pkt,
        event_kind="publish_attempted",
        row_scope="role",
        row_id="host_lead",
        actor_kind="operator",
        payload={"review_zone": "qc"},
    )
    record = closure["feedback_closure_records"][-1]
    assert record["event_kind"] == "publish_attempted"
    assert "review_zone" not in record


def test_matrix_script_closure_review_zone_values_unchanged_by_da_addition() -> None:
    # Matrix Script closure-side enum is preserved byte-stable per gate
    # spec §4.2 cross-line preservation. Importing it here confirms the
    # OWC-DA additive landing did not touch the Matrix Script module.
    from gateway.app.services.matrix_script.publish_feedback_closure import (
        REVIEW_ZONE_VALUES as MS_REVIEW_ZONE_VALUES,
    )

    assert MS_REVIEW_ZONE_VALUES == frozenset({"subtitle", "dub", "copy", "cta"})
