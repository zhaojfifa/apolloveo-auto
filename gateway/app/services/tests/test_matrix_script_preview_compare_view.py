"""OWC-MS PR-2 — Matrix Script Workbench C 预览对比区 view tests (MS-W4).

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W4 (multi-variation preview;
  axis-tuple comparator for diff hints; recommended marker from PR-1 unified
  publish_readiness; consumes existing artifact_lookup; no second producer).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1C.

Import-light: exercises the pure helper
``derive_matrix_script_preview_compare_view`` over hand-built inputs that
mirror the shapes produced by ``project_workbench_variation_surface``,
``project_delivery_binding`` (artifact_lookup), and the unified
``compute_publish_readiness`` producer.

What is proved:

1. Returns ``{}`` for non-Matrix-Script panels.
2. Variation rows enumerate one per cell with axis_selections /
   script_slot_ref / slot_body_ref / slot_length_hint /
   language_scope passthrough.
3. ``preview_status`` is read from the ``variation_manifest`` row's
   ``artifact_lookup`` (operator-language label set reused from
   ``delivery_comprehension._artifact_status_label_zh``).
4. ``publish_status`` reads from the closure ``variation_feedback[]``
   row when present; defaults to ``pending`` when no closure exists.
5. ``recommended_marker`` derives from ``publish_readiness.publishable``
   ONLY (not from a second derivation):
   - ``publishable_candidate`` when publishable AND not already
     ``published`` in closure.
   - ``blocked_pending_publish_readiness`` when not publishable; carries
     ``head_reason`` from the producer.
   - ``undetermined_pending_review`` when publishable but already
     published OR no publish_readiness provided.
6. ``diff_hints`` lists per-axis distinct values across cells; axes
   with a single distinct value are marked ``is_differing=False``.
7. ``differing_axes`` and ``invariant_axes`` partition correctly.
8. Validator R3 alignment.
9. Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from gateway.app.services.matrix_script.preview_compare_view import (
    RECOMMENDED_BUCKET_BLOCKED,
    RECOMMENDED_BUCKET_PUBLISHABLE,
    RECOMMENDED_BUCKET_UNDETERMINED,
    derive_matrix_script_preview_compare_view,
)


def _matrix_script_panel() -> dict[str, Any]:
    return {
        "panel_kind": "matrix_script",
        "refs": [
            {"ref_id": "matrix_script_variation_matrix"},
            {"ref_id": "matrix_script_slot_pack"},
        ],
    }


def _variation_surface(
    *,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
    axes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "variation_plan": {
            "axes": axes
            or [
                {"axis_id": "tone", "kind": "categorical", "values": ["formal", "casual"]},
                {"axis_id": "audience", "kind": "enum", "values": ["b2b", "b2c"]},
                {"axis_id": "length", "kind": "range", "values": {"min": 30, "max": 60, "step": 30}},
            ],
            "cells": cells
            or [
                {
                    "cell_id": "cell_001",
                    "axis_selections": {"tone": "formal", "audience": "b2b", "length": 60},
                    "script_slot_ref": "slot_001",
                },
                {
                    "cell_id": "cell_002",
                    "axis_selections": {"tone": "casual", "audience": "b2c", "length": 30},
                    "script_slot_ref": "slot_002",
                },
            ],
        },
        "copy_bundle": {
            "slots": slots
            or [
                {
                    "slot_id": "slot_001",
                    "binds_cell_id": "cell_001",
                    "body_ref": "content://matrix-script/t/slot/slot_001",
                    "length_hint": 60,
                    "language_scope": {"source_language": "zh", "target_language": ["mm"]},
                },
                {
                    "slot_id": "slot_002",
                    "binds_cell_id": "cell_002",
                    "body_ref": "content://matrix-script/t/slot/slot_002",
                    "length_hint": 30,
                    "language_scope": {"source_language": "zh", "target_language": ["mm"]},
                },
            ],
        },
    }


def _delivery_binding(*, artifact_lookup: Any = "artifact_lookup_unresolved") -> dict[str, Any]:
    return {
        "surface": "matrix_script_delivery_binding_v1",
        "line_id": "matrix_script",
        "delivery_pack": {
            "deliverables": [
                {
                    "deliverable_id": "matrix_script_variation_manifest",
                    "kind": "variation_manifest",
                    "required": True,
                    "blocking_publish": True,
                    "artifact_lookup": artifact_lookup,
                },
                {
                    "deliverable_id": "matrix_script_slot_bundle",
                    "kind": "script_slot_bundle",
                    "required": True,
                    "blocking_publish": True,
                    "artifact_lookup": "artifact_lookup_unresolved",
                },
            ]
        },
    }


# -- 1. Non-Matrix-Script panel returns empty ---------------------------


@pytest.mark.parametrize("panel_kind", ["hot_follow", "digital_anchor", "baseline", "", None])
def test_non_matrix_script_panel_returns_empty(panel_kind: Any) -> None:
    panel = {"panel_kind": panel_kind}
    assert (
        derive_matrix_script_preview_compare_view(_variation_surface(), _delivery_binding(), {}, panel)
        == {}
    )


def test_empty_inputs_return_empty_for_non_matrix_panel() -> None:
    assert derive_matrix_script_preview_compare_view(None, None, None, None) == {}


# -- 2. Variation rows enumerate per cell -------------------------------


def test_variation_rows_one_per_cell_with_axis_selections() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel()
    )
    assert bundle["variation_count"] == 2
    assert [v["variation_id"] for v in bundle["variations"]] == ["cell_001", "cell_002"]
    assert bundle["variations"][0]["axis_selections"] == {
        "tone": "formal",
        "audience": "b2b",
        "length": 60,
    }


def test_variation_row_passes_through_slot_metadata() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel()
    )
    row = bundle["variations"][0]
    assert row["script_slot_ref"] == "slot_001"
    assert row["slot_body_ref"] == "content://matrix-script/t/slot/slot_001"
    assert row["slot_length_hint"] == 60
    assert row["language_scope"]["source_language"] == "zh"
    assert row["language_scope"]["target_language"] == ["mm"]


def test_variation_row_with_unresolved_slot_handles_missing_slot_metadata() -> None:
    surface = _variation_surface(
        cells=[
            {
                "cell_id": "cell_001",
                "axis_selections": {"tone": "formal"},
                "script_slot_ref": "slot_missing",
            }
        ],
        slots=[],
    )
    bundle = derive_matrix_script_preview_compare_view(
        surface, _delivery_binding(), {}, _matrix_script_panel()
    )
    row = bundle["variations"][0]
    assert row["script_slot_ref"] == "slot_missing"
    assert row["slot_body_ref"] is None
    assert row["slot_length_hint"] is None


# -- 3. Preview status reads from variation_manifest artifact_lookup ----


def test_preview_status_unresolved_from_sentinel() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(),
        _delivery_binding(artifact_lookup="artifact_lookup_unresolved"),
        {},
        _matrix_script_panel(),
    )
    for v in bundle["variations"]:
        assert v["preview_status_code"] == "unresolved"
        assert v["preview_status_label_zh"] == "尚未解析"


def test_preview_status_current_fresh_from_handle() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(),
        _delivery_binding(
            artifact_lookup={
                "artifact_ref": "slot_001",
                "freshness": "fresh",
                "provenance": "current",
            }
        ),
        {},
        _matrix_script_panel(),
    )
    for v in bundle["variations"]:
        assert v["preview_status_code"] == "current_fresh"
        assert "当前" in v["preview_status_label_zh"]


def test_preview_status_historical_from_handle() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(),
        _delivery_binding(
            artifact_lookup={
                "artifact_ref": "slot_001",
                "freshness": "historical",
                "provenance": "historical",
            }
        ),
        {},
        _matrix_script_panel(),
    )
    for v in bundle["variations"]:
        assert v["preview_status_code"] == "historical"
        assert "历史" in v["preview_status_label_zh"]


# -- 4. Publish status reads from closure variation_feedback ------------


def test_publish_status_defaults_to_pending_when_no_closure() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel(), closure=None
    )
    for v in bundle["variations"]:
        assert v["publish_status"] == "pending"
        assert v["publish_url"] is None


def test_publish_status_reads_closure_variation_feedback_row() -> None:
    closure = {
        "variation_feedback": [
            {"variation_id": "cell_001", "publish_status": "published", "publish_url": "https://x"},
            {"variation_id": "cell_002", "publish_status": "pending", "publish_url": None},
        ]
    }
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel(), closure=closure
    )
    rows = {v["variation_id"]: v for v in bundle["variations"]}
    assert rows["cell_001"]["publish_status"] == "published"
    assert rows["cell_001"]["publish_url"] == "https://x"
    assert rows["cell_002"]["publish_status"] == "pending"


# -- 5. Recommended marker derives from publish_readiness ONLY ----------


def test_recommended_publishable_candidate_when_publishable_and_unpublished() -> None:
    pr = {"publishable": True, "head_reason": "publishable_ok"}
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), pr, _matrix_script_panel()
    )
    for v in bundle["variations"]:
        assert v["recommended_bucket"] == RECOMMENDED_BUCKET_PUBLISHABLE


def test_recommended_blocked_when_publish_readiness_blocked() -> None:
    pr = {"publishable": False, "head_reason": "required_deliverable_missing"}
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), pr, _matrix_script_panel()
    )
    for v in bundle["variations"]:
        assert v["recommended_bucket"] == RECOMMENDED_BUCKET_BLOCKED
        assert v["recommended_head_reason"] == "required_deliverable_missing"


def test_recommended_undetermined_when_already_published() -> None:
    pr = {"publishable": True, "head_reason": "publishable_ok"}
    closure = {
        "variation_feedback": [
            {"variation_id": "cell_001", "publish_status": "published", "publish_url": None},
            {"variation_id": "cell_002", "publish_status": "pending", "publish_url": None},
        ]
    }
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(),
        _delivery_binding(),
        pr,
        _matrix_script_panel(),
        closure=closure,
    )
    rows = {v["variation_id"]: v for v in bundle["variations"]}
    assert rows["cell_001"]["recommended_bucket"] == RECOMMENDED_BUCKET_UNDETERMINED
    assert rows["cell_002"]["recommended_bucket"] == RECOMMENDED_BUCKET_PUBLISHABLE


def test_recommended_undetermined_when_no_publish_readiness_provided() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), None, _matrix_script_panel()
    )
    for v in bundle["variations"]:
        assert v["recommended_bucket"] == RECOMMENDED_BUCKET_UNDETERMINED


# -- 6. Diff hints + 7. partition --------------------------------------


def test_diff_hints_list_one_per_axis_with_distinct_values() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel()
    )
    hints = {h["axis_id"]: h for h in bundle["diff_hints"]}
    assert hints["tone"]["distinct_value_count"] == 2
    assert hints["audience"]["distinct_value_count"] == 2
    assert hints["length"]["distinct_value_count"] == 2
    for hint in hints.values():
        assert hint["is_differing"] is True


def test_diff_hints_invariant_axis_marked_non_differing() -> None:
    cells = [
        {
            "cell_id": "cell_a",
            "axis_selections": {"tone": "formal", "audience": "b2b", "length": 60},
            "script_slot_ref": "slot_a",
        },
        {
            "cell_id": "cell_b",
            "axis_selections": {"tone": "casual", "audience": "b2b", "length": 30},
            "script_slot_ref": "slot_b",
        },
    ]
    surface = _variation_surface(cells=cells, slots=[])
    bundle = derive_matrix_script_preview_compare_view(
        surface, _delivery_binding(), {}, _matrix_script_panel()
    )
    hints = {h["axis_id"]: h for h in bundle["diff_hints"]}
    assert hints["audience"]["is_differing"] is False
    assert hints["audience"]["distinct_value_count"] == 1
    assert "audience" in bundle["invariant_axes"]
    assert "tone" in bundle["differing_axes"]


# -- 8. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_preview_compare_view(
        _variation_surface(), _delivery_binding(), {}, _matrix_script_panel()
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


# -- 9. Helper does not mutate inputs -----------------------------------


def test_helper_does_not_mutate_inputs() -> None:
    surface = _variation_surface()
    binding = _delivery_binding()
    pr = {"publishable": True, "head_reason": "publishable_ok"}
    closure = {"variation_feedback": [{"variation_id": "cell_001", "publish_status": "pending"}]}
    snap_surface = deepcopy(surface)
    snap_binding = deepcopy(binding)
    snap_pr = deepcopy(pr)
    snap_closure = deepcopy(closure)
    derive_matrix_script_preview_compare_view(
        surface, binding, pr, _matrix_script_panel(), closure=closure
    )
    assert surface == snap_surface
    assert binding == snap_binding
    assert pr == snap_pr
    assert closure == snap_closure
