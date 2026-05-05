"""OWC-MS PR-2 — additive `review_zone` enum on `operator_note` events.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W5 (additive structured
  ``review_zone`` field; closed enum subtitle / dub / copy / cta;
  closure shape unchanged).
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
  §"Operator review zone tag (additive, OWC-MS PR-2)".
- ``gateway/app/services/matrix_script/publish_feedback_closure.py``
  (the additive validation + recording lives in ``apply_event``).

Import-light: drives the ``apply_event`` validator + the
``InMemoryClosureStore`` flow directly; no FastAPI / HTTP cases.

What is proved:

1. ``REVIEW_ZONE_VALUES`` enumerates exactly the four operator-language
   zones {subtitle, dub, copy, cta}.
2. Legacy ``operator_note`` events without ``review_zone`` are still
   accepted (no migration; back-compat preserved).
3. ``operator_note`` with a valid ``review_zone`` is accepted; the
   appended ``feedback_closure_records[]`` entry carries the field;
   the ``variation_feedback[]`` row shape is unchanged (no new key).
4. ``operator_note`` with an unknown ``review_zone`` raises
   ``ClosureValidationError`` and does NOT append an event.
5. ``review_zone`` on event kinds other than ``operator_note`` is
   silently ignored (the validator does not accept the field on
   non-operator_note events; no record is tagged).
6. The closure-wide envelope (``surface``, ``closure_id``, ``line_id``,
   ``packet_version``, ``variation_feedback``, ``feedback_closure_records``)
   shape is unchanged.
7. Closure-shape envelope keys do not gain ``review_zone``.
"""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.publish_feedback_closure import (
    ACTOR_KINDS,
    CHANNEL_METRICS_KEYS,
    EVENT_KINDS,
    InMemoryClosureStore,
    REVIEW_ZONE_VALUES,
    SURFACE_ID,
    apply_event,
    create_closure,
    ClosureValidationError,
)


def _packet_with_two_cells() -> dict:
    return {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "delta": {
                    "cells": [
                        {"cell_id": "cell_001"},
                        {"cell_id": "cell_002"},
                    ]
                },
            }
        ],
    }


# -- 1. Closed enum membership ------------------------------------------


def test_review_zone_values_is_exactly_four_zones() -> None:
    assert REVIEW_ZONE_VALUES == frozenset({"subtitle", "dub", "copy", "cta"})


def test_review_zone_values_does_not_widen_event_kinds_or_actor_kinds() -> None:
    # The additive enum lives ONLY on the operator_note payload — the
    # event_kind set and actor_kind set must not have grown.
    assert EVENT_KINDS == frozenset(
        {
            "operator_publish",
            "operator_retract",
            "operator_note",
            "platform_callback",
            "metrics_snapshot",
        }
    )
    assert ACTOR_KINDS == frozenset({"operator", "platform", "system"})


def test_review_zone_values_does_not_widen_channel_metrics_keys() -> None:
    assert "review_zone" not in CHANNEL_METRICS_KEYS


# -- 2. Legacy untagged operator_note still accepted --------------------


def test_legacy_operator_note_without_review_zone_accepted() -> None:
    closure = create_closure(_packet_with_two_cells())
    apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": "cell_001",
            "payload": {"operator_publish_notes": "untagged review note"},
        },
    )
    assert len(closure["feedback_closure_records"]) == 1
    record = closure["feedback_closure_records"][-1]
    assert record["event_kind"] == "operator_note"
    assert "review_zone" not in record


# -- 3. Tagged operator_note accepted; recorded position correct -------


@pytest.mark.parametrize("zone", sorted(REVIEW_ZONE_VALUES))
def test_operator_note_with_valid_review_zone_records_tag(zone: str) -> None:
    closure = create_closure(_packet_with_two_cells())
    apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": "cell_001",
            "payload": {
                "operator_publish_notes": "字幕翻译需要复核",
                "review_zone": zone,
            },
        },
    )
    record = closure["feedback_closure_records"][-1]
    assert record["review_zone"] == zone


def test_operator_note_with_review_zone_does_not_widen_variation_feedback_row() -> None:
    closure = create_closure(_packet_with_two_cells())
    apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": "cell_001",
            "payload": {
                "operator_publish_notes": "字幕翻译需要复核",
                "review_zone": "subtitle",
            },
        },
    )
    row = next(
        r for r in closure["variation_feedback"] if r["variation_id"] == "cell_001"
    )
    # Variation row shape is bytewise unchanged — `review_zone` lives
    # on the appended record only.
    assert "review_zone" not in row
    expected_row_keys = {
        "variation_id",
        "publish_url",
        "publish_status",
        "channel_metrics",
        "operator_publish_notes",
        "last_event_id",
    }
    assert set(row.keys()) == expected_row_keys


# -- 4. Unknown review_zone raises and does NOT append ------------------


def test_operator_note_with_unknown_review_zone_raises_and_does_not_append() -> None:
    closure = create_closure(_packet_with_two_cells())
    initial = len(closure["feedback_closure_records"])
    with pytest.raises(ClosureValidationError) as exc:
        apply_event(
            closure,
            {
                "event_kind": "operator_note",
                "variation_id": "cell_001",
                "payload": {
                    "operator_publish_notes": "字幕翻译需要复核",
                    "review_zone": "audio",
                },
            },
        )
    assert "review_zone" in str(exc.value)
    assert len(closure["feedback_closure_records"]) == initial


# -- 5. review_zone on non-operator_note event kinds is ignored ---------


def test_review_zone_on_operator_publish_is_silently_ignored() -> None:
    closure = create_closure(_packet_with_two_cells())
    apply_event(
        closure,
        {
            "event_kind": "operator_publish",
            "variation_id": "cell_001",
            "payload": {
                "publish_url": "https://x",
                "publish_status": "pending",
                # Should not be recorded — the validator only tags operator_note.
                "review_zone": "subtitle",
            },
        },
    )
    record = closure["feedback_closure_records"][-1]
    assert "review_zone" not in record


def test_review_zone_on_metrics_snapshot_is_rejected_by_existing_payload_guard() -> None:
    """`metrics_snapshot` payload is constrained to CHANNEL_METRICS_KEYS by
    the existing pre-PR-2 validator; PR-2 does not relax that constraint.
    A `review_zone` key on a metrics_snapshot payload is rejected by the
    existing channel_metrics forbidden-keys guard — this is a property
    of the additive-only design (the new field is gated to operator_note
    payloads only).
    """
    closure = create_closure(_packet_with_two_cells())
    initial = len(closure["feedback_closure_records"])
    with pytest.raises(ClosureValidationError):
        apply_event(
            closure,
            {
                "event_kind": "metrics_snapshot",
                "variation_id": "cell_001",
                "payload": {
                    "channel_id": "tiktok-account-1",
                    "captured_at": "2026-05-05T10:00:00Z",
                    "review_zone": "subtitle",
                },
            },
        )
    assert len(closure["feedback_closure_records"]) == initial


# -- 6. Closure-wide envelope shape is unchanged ------------------------


def test_closure_envelope_keys_unchanged_under_review_zone_writes() -> None:
    closure = create_closure(_packet_with_two_cells())
    apply_event(
        closure,
        {
            "event_kind": "operator_note",
            "variation_id": "cell_001",
            "payload": {"operator_publish_notes": "x", "review_zone": "subtitle"},
        },
    )
    expected = {
        "surface",
        "closure_id",
        "line_id",
        "packet_version",
        "variation_feedback",
        "feedback_closure_records",
    }
    assert set(closure.keys()) == expected
    assert closure["surface"] == SURFACE_ID


# -- 7. The store path also records the tag (no extra contract surface) -


def test_in_memory_store_apply_records_review_zone_tag_on_record() -> None:
    store = InMemoryClosureStore()
    store.create(_packet_with_two_cells(), closure_id="closure_test_w5")
    result = store.apply(
        "closure_test_w5",
        {
            "event_kind": "operator_note",
            "variation_id": "cell_002",
            "payload": {
                "operator_publish_notes": "CTA 文案需要打磨",
                "review_zone": "cta",
            },
        },
    )
    closure = result["closure"]
    record = closure["feedback_closure_records"][-1]
    assert record["review_zone"] == "cta"
