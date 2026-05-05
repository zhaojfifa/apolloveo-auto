"""OWC-MS PR-2 — Matrix Script Workbench D 校对区 view tests (MS-W5).

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W5.
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
  §"Operator review zone tag (additive, OWC-MS PR-2)".
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1D.

Import-light: exercises the pure helper
``derive_matrix_script_review_zone_view`` over hand-built variation
surfaces + closure shapes.

What is proved:

1. Returns ``{}`` for non-Matrix-Script panels.
2. Four review zones render in stable order (subtitle / dub / copy /
   cta) with operator-language labels + per-zone guidance.
3. Each zone's payload-shape example carries ``event_kind="operator_note"``,
   ``actor_kind="operator"``, ``payload.review_zone`` matching the zone id,
   and the existing ``/api/matrix-script/closures/{task_id}/events`` endpoint
   template (no new endpoint).
4. Per-variation review status reads closure ``feedback_closure_records[]``
   and indexes by ``(variation_id, review_zone)``; events without
   ``review_zone`` flow into a ``legacy_unzoned_history_count`` counter
   and never inflate per-zone history.
5. ``last_recorded_at`` and ``is_reviewed`` reflect the most recent
   record per zone.
6. Validator R3 alignment.
7. Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from gateway.app.services.matrix_script.review_zone_view import (
    REVIEW_EVENT_ENDPOINT_TEMPLATE,
    REVIEW_ZONE_ORDER,
    derive_matrix_script_review_zone_view,
)


def _matrix_script_panel() -> dict[str, Any]:
    return {"panel_kind": "matrix_script"}


def _variation_surface(*, cells: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "variation_plan": {
            "cells": cells
            or [
                {"cell_id": "cell_001", "axis_selections": {"tone": "formal"}},
                {"cell_id": "cell_002", "axis_selections": {"tone": "casual"}},
            ]
        }
    }


# -- 1. Non-Matrix-Script panel returns empty ---------------------------


@pytest.mark.parametrize("panel_kind", ["hot_follow", "digital_anchor", "baseline", "", None])
def test_non_matrix_script_panel_returns_empty(panel_kind: Any) -> None:
    panel = {"panel_kind": panel_kind}
    assert derive_matrix_script_review_zone_view(_variation_surface(), None, panel) == {}


# -- 2. Four zones render in stable order -------------------------------


def test_zones_emit_four_in_stable_order() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    assert [z["zone_id"] for z in bundle["zones"]] == list(REVIEW_ZONE_ORDER)
    labels = {z["zone_id"]: z["zone_label_zh"] for z in bundle["zones"]}
    assert labels["subtitle"] == "字幕校对"
    assert labels["dub"] == "配音校对"
    assert labels["copy"] == "文案校对"
    assert labels["cta"] == "CTA 校对"


def test_review_zone_enum_exposed_sorted() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    assert bundle["review_zone_enum"] == sorted(["subtitle", "dub", "copy", "cta"])


# -- 3. Zone payload-shape uses existing endpoint -----------------------


def test_zone_payload_shape_example_uses_existing_endpoint_and_event_kind() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    for zone in bundle["zones"]:
        example = zone["payload_shape_example"]
        assert example["event_kind"] == "operator_note"
        assert example["actor_kind"] == "operator"
        assert example["payload"]["review_zone"] == zone["zone_id"]
        assert zone["endpoint_template"] == REVIEW_EVENT_ENDPOINT_TEMPLATE
        assert zone["endpoint_template"] == "/api/matrix-script/closures/{task_id}/events"


# -- 3b. MS-W5 real submit affordance: per-(variation, zone) form ------


def test_submit_form_resolves_endpoint_url_when_task_id_provided() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel(), task_id="ms_w5_task_42"
    )
    assert (
        bundle["closure_endpoint_url"]
        == "/api/matrix-script/closures/ms_w5_task_42/events"
    )
    for zone in bundle["zones"]:
        assert (
            zone["endpoint_url"]
            == "/api/matrix-script/closures/ms_w5_task_42/events"
        )
        assert zone["input_label_zh"]
        assert zone["submit_label_zh"]


def test_submit_form_per_variation_per_zone_carries_real_action_and_payload_keys() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel(), task_id="ms_w5_task_42"
    )
    rows = bundle["review_status_rows"]
    assert rows  # exactly two cells in the fixture
    for row in rows:
        for zone_id in ("subtitle", "dub", "copy", "cta"):
            form = row["per_zone"][zone_id]["submit_form"]
            assert form is not None
            assert form["method"] == "POST"
            assert (
                form["action"]
                == "/api/matrix-script/closures/ms_w5_task_42/events"
            )
            assert form["event_kind"] == "operator_note"
            assert form["actor_kind"] == "operator"
            assert form["variation_id"] == row["variation_id"]
            assert form["review_zone"] == zone_id


def test_submit_form_absent_when_no_task_id_provided() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    assert bundle["closure_endpoint_url"] is None
    for row in bundle["review_status_rows"]:
        for zone_id in ("subtitle", "dub", "copy", "cta"):
            assert row["per_zone"][zone_id]["submit_form"] is None
        for zone in bundle["zones"]:
            assert zone["endpoint_url"] is None


def test_closure_endpoint_explanation_names_recovery_pr3_endpoint() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    explanation = bundle["closure_endpoint_explanation_zh"]
    assert "Recovery PR-3" in explanation
    assert "POST /api/matrix-script/closures/{task_id}/events" in explanation
    assert "operator_note" in explanation


# -- 4. Per-variation review status reads closure history ---------------


def test_review_status_one_row_per_cell_with_per_zone_keys() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    rows = bundle["review_status_rows"]
    assert [r["variation_id"] for r in rows] == ["cell_001", "cell_002"]
    for row in rows:
        assert set(row["per_zone"].keys()) == set(REVIEW_ZONE_ORDER)
        for state in row["per_zone"].values():
            assert state["is_reviewed"] is False
            assert state["history_count"] == 0


def test_per_zone_history_indexes_by_variation_and_zone() -> None:
    closure = {
        "feedback_closure_records": [
            {
                "event_id": "evt_a",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T10:00:00Z",
            },
            {
                "event_id": "evt_b",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T11:00:00Z",
            },
            {
                "event_id": "evt_c",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "dub",
                "recorded_at": "2026-05-05T12:00:00Z",
            },
            # Non-operator_note events MUST be ignored.
            {
                "event_id": "evt_d",
                "variation_id": "cell_001",
                "event_kind": "operator_publish",
                "recorded_at": "2026-05-05T13:00:00Z",
            },
        ]
    }
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), closure, _matrix_script_panel()
    )
    cell001 = next(r for r in bundle["review_status_rows"] if r["variation_id"] == "cell_001")
    assert cell001["per_zone"]["subtitle"]["history_count"] == 2
    assert cell001["per_zone"]["dub"]["history_count"] == 1
    assert cell001["per_zone"]["copy"]["history_count"] == 0
    assert cell001["per_zone"]["cta"]["history_count"] == 0


def test_legacy_unzoned_history_does_not_inflate_per_zone() -> None:
    closure = {
        "feedback_closure_records": [
            {
                "event_id": "evt_legacy",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "recorded_at": "2026-05-05T08:00:00Z",
                # No `review_zone` — legacy untagged note.
            },
            {
                "event_id": "evt_subtitle",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T09:00:00Z",
            },
        ]
    }
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), closure, _matrix_script_panel()
    )
    cell001 = next(r for r in bundle["review_status_rows"] if r["variation_id"] == "cell_001")
    assert cell001["per_zone"]["subtitle"]["history_count"] == 1
    assert cell001["legacy_unzoned_history_count"] == 1
    # And no other per-zone bucket gets inflated by the legacy event.
    for zone_id in ("dub", "copy", "cta"):
        assert cell001["per_zone"][zone_id]["history_count"] == 0


# -- 5. last_recorded_at + is_reviewed for most recent event ------------


def test_last_recorded_at_reflects_most_recent_per_zone() -> None:
    closure = {
        "feedback_closure_records": [
            {
                "event_id": "evt_subtitle_first",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T10:00:00Z",
            },
            {
                "event_id": "evt_subtitle_latest",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T13:00:00Z",
            },
        ]
    }
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), closure, _matrix_script_panel()
    )
    cell001 = next(r for r in bundle["review_status_rows"] if r["variation_id"] == "cell_001")
    state = cell001["per_zone"]["subtitle"]
    assert state["is_reviewed"] is True
    assert state["last_event_id"] == "evt_subtitle_latest"
    assert state["last_recorded_at"] == "2026-05-05T13:00:00Z"


def test_invalid_review_zone_in_record_falls_into_legacy_bucket() -> None:
    closure = {
        "feedback_closure_records": [
            {
                "event_id": "evt_bogus",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "audio",  # Not in the closed enum.
                "recorded_at": "2026-05-05T14:00:00Z",
            }
        ]
    }
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), closure, _matrix_script_panel()
    )
    cell001 = next(r for r in bundle["review_status_rows"] if r["variation_id"] == "cell_001")
    for zone_id in REVIEW_ZONE_ORDER:
        assert cell001["per_zone"][zone_id]["history_count"] == 0
    assert cell001["legacy_unzoned_history_count"] == 1


# -- 6. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_review_zone_view(
        _variation_surface(), None, _matrix_script_panel()
    )
    forbidden = {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
    }

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value.keys()) & forbidden)
            for v in value.values():
                _walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _walk(v)

    _walk(bundle)


# -- 7. Helper does not mutate inputs -----------------------------------


def test_helper_does_not_mutate_inputs() -> None:
    surface = _variation_surface()
    closure = {
        "feedback_closure_records": [
            {
                "event_id": "evt_a",
                "variation_id": "cell_001",
                "event_kind": "operator_note",
                "review_zone": "subtitle",
                "recorded_at": "2026-05-05T10:00:00Z",
            }
        ]
    }
    snap_surface = deepcopy(surface)
    snap_closure = deepcopy(closure)
    derive_matrix_script_review_zone_view(surface, closure, _matrix_script_panel())
    assert surface == snap_surface
    assert closure == snap_closure
