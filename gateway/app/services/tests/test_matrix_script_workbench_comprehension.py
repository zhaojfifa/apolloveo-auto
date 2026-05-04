"""PR-U2 — Matrix Script Workbench operator-comprehension projection tests.

Authority:
- ``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``
  (signed UI-alignment gate spec; PR-U2 implements the user-mandated
  Workbench comprehension narrowing).
- ``gateway/app/services/matrix_script/workbench_comprehension.py`` (helper under test).
- ``gateway/app/services/matrix_script/workbench_variation_surface.py`` (input projection shape).

These tests are import-light: they exercise the pure helper
``derive_matrix_script_workbench_comprehension`` over hand-built inputs
that mirror the shapes produced by ``project_workbench_variation_surface``
+ ``derive_workbench_panel_dispatch``.

What is proved:

1. Returns ``{}`` when the panel is not Matrix Script (Hot Follow /
   Digital Anchor / Baseline workbench surfaces never receive the
   bundle).
2. Four-zone alignment header binds ``content_structure`` /
   ``scene_plan`` / ``audio_plan`` / ``language_plan`` against
   ``line_specific_refs[].binds_to``; unbound zones render the
   ``empty_label_zh`` sentinel without inventing a binding.
3. Task identity summary counts (axes / cells / slots) match the
   variation surface input.
4. ``ready_state`` operator-language label translates known codes;
   unknown codes fall through verbatim; missing/empty becomes ``"—"``.
5. ``next_step_zone`` is always ``"system"`` and ``next_step_label_zh``
   names "无需操作" — operator-driven Phase B authoring is forbidden in
   this Plan E phase per gate spec §4.3, so the Workbench Variation
   Panel stays read-only at the projection level.
6. Variation summary text ``共 N 组变体 · ...`` matches the cells / axes
   / slots counts.
7. Axis-tuple grouping kicks in only above the threshold; sample cell
   ids cap at 3; ordering is stable (descending count then group_key).
8. Validator R3 alignment — no vendor / model / provider / engine
   identifier in the return value.
9. Helper does not mutate the input.
"""
from __future__ import annotations

from typing import Any

import pytest

from gateway.app.services.matrix_script.workbench_comprehension import (
    DEFAULT_CELL_GROUPING_THRESHOLD,
    derive_matrix_script_workbench_comprehension,
)


def _matrix_script_panel(refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "panel_kind": "matrix_script",
        "refs": refs if refs is not None else [
            {
                "ref_id": "matrix_script_variation_matrix",
                "binds_to": ["factory_input_contract_v1"],
                "version": "v1",
            },
            {
                "ref_id": "matrix_script_slot_pack",
                "binds_to": ["factory_language_plan_contract_v1"],
                "version": "v1",
            },
        ],
    }


def _variation_surface(
    *,
    axes: list[dict[str, Any]] | None = None,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
    ready_state: str | None = "ready",
    attribution_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if attribution_refs is None:
        attribution_refs = [
            {
                "ref_id": "matrix_script_variation_matrix",
                "version": "v1",
                "binds_to": ["factory_input_contract_v1"],
            },
            {
                "ref_id": "matrix_script_slot_pack",
                "version": "v1",
                "binds_to": ["factory_language_plan_contract_v1"],
            },
        ]
    return {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "readyState": ready_state,
        "variation_plan": {
            "axes": axes or [],
            "cells": cells or [],
        },
        "copy_bundle": {
            "slots": slots or [],
        },
        "slot_detail_surface": {
            "join_rule": "variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id",
            "slots": slots or [],
        },
        "attribution_refs": {
            "generic_refs": [],
            "line_specific_refs": attribution_refs,
            "capability_plan": [],
            "worker_profile_ref": None,
        },
        "publish_feedback_projection": {
            "ready_state": ready_state,
            "feedback_writeback": "not_implemented_phase_b",
        },
    }


# -- 1. Non-Matrix-Script panel kinds get empty bundle ------------------


@pytest.mark.parametrize(
    "panel_kind", ["hot_follow", "digital_anchor", "baseline", "", None]
)
def test_non_matrix_script_panel_returns_empty(panel_kind: str | None) -> None:
    panel = {"panel_kind": panel_kind, "refs": []}
    assert derive_matrix_script_workbench_comprehension(_variation_surface(), panel) == {}


def test_missing_inputs_return_empty_safely() -> None:
    assert derive_matrix_script_workbench_comprehension(None, None) == {}
    assert derive_matrix_script_workbench_comprehension({}, {}) == {}


# -- 2. Four-zone alignment ----------------------------------------------


def test_four_zone_alignment_emits_all_four_zones_in_order() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    zones = bundle["four_zone_alignment"]
    assert [z["zone_id"] for z in zones] == [
        "content_structure",
        "scene_plan",
        "audio_plan",
        "language_plan",
    ]
    assert [z["zone_label_zh"] for z in zones] == ["内容结构", "场景规划", "音频规划", "语言规划"]


def test_content_structure_zone_binds_variation_matrix() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    cs = next(z for z in bundle["four_zone_alignment"] if z["zone_id"] == "content_structure")
    assert cs["is_bound"] is True
    assert any(r["ref_id"] == "matrix_script_variation_matrix" for r in cs["bound_refs"])


def test_language_plan_zone_binds_slot_pack() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    lp = next(z for z in bundle["four_zone_alignment"] if z["zone_id"] == "language_plan")
    assert lp["is_bound"] is True
    assert any(r["ref_id"] == "matrix_script_slot_pack" for r in lp["bound_refs"])


def test_unbound_zones_render_empty_label_without_inventing_binding() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    for zone_id in ("scene_plan", "audio_plan"):
        zone = next(z for z in bundle["four_zone_alignment"] if z["zone_id"] == zone_id)
        assert zone["is_bound"] is False
        assert zone["bound_refs"] == []
        assert zone["empty_label_zh"] == "—（此线未绑定）"


def test_zone_lookup_falls_back_to_panel_refs_when_attribution_empty() -> None:
    surface = _variation_surface(attribution_refs=[])
    bundle = derive_matrix_script_workbench_comprehension(surface, _matrix_script_panel())
    cs = next(z for z in bundle["four_zone_alignment"] if z["zone_id"] == "content_structure")
    assert cs["is_bound"] is True


# -- 3. Task identity summary --------------------------------------------


def test_task_identity_summary_counts_match_inputs() -> None:
    axes = [{"axis_id": f"a{i}"} for i in range(3)]
    cells = [{"cell_id": f"c{i}", "axis_selections": {}} for i in range(5)]
    slots = [{"slot_id": f"s{i}"} for i in range(5)]
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(axes=axes, cells=cells, slots=slots),
        _matrix_script_panel(),
    )
    summary = bundle["task_identity_summary"]
    assert summary["axes_count"] == 3
    assert summary["cells_count"] == 5
    assert summary["slots_count"] == 5


# -- 4. ready_state translation ------------------------------------------


@pytest.mark.parametrize(
    "code,expected",
    [
        ("ready", "已就绪"),
        ("pending", "等待生成"),
        ("in_progress", "进行中"),
        ("blocked", "已阻塞"),
        ("error", "错误"),
        ("draft", "草稿"),
    ],
)
def test_ready_state_known_codes_translate(code: str, expected: str) -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(ready_state=code), _matrix_script_panel()
    )
    assert bundle["task_identity_summary"]["ready_state_label_zh"] == expected


def test_ready_state_unknown_falls_through_verbatim() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(ready_state="some_future_code"), _matrix_script_panel()
    )
    assert bundle["task_identity_summary"]["ready_state_label_zh"] == "some_future_code"


def test_ready_state_missing_renders_dash() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(ready_state=None), _matrix_script_panel()
    )
    assert bundle["task_identity_summary"]["ready_state_label_zh"] == "—"


# -- 5. Next step is always "system" / no operator action ---------------


def test_next_step_zone_is_system_and_label_says_no_action_required() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    assert bundle["next_step_zone"] == "system"
    assert "无需操作" in bundle["next_step_label_zh"]
    assert "Phase B" in bundle["next_step_label_zh"]
    # Explanation must name the §4.3 forbidden scope so reviewers can
    # trace the read-only invariant back to the gate spec.
    assert "§4.3" in bundle["next_step_explanation_zh"]


# -- 6. Variation summary text ------------------------------------------


def test_variation_summary_text_matches_counts() -> None:
    axes = [{"axis_id": "a1"}, {"axis_id": "a2"}]
    cells = [{"cell_id": f"c{i}", "axis_selections": {}} for i in range(4)]
    slots = [{"slot_id": f"s{i}"} for i in range(4)]
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(axes=axes, cells=cells, slots=slots),
        _matrix_script_panel(),
    )
    text = bundle["variation_summary"]["summary_text_zh"]
    assert "共 4 组变体" in text
    assert "2 条 axis" in text
    assert "4 个 slot" in text


# -- 7. Axis-tuple grouping (readability hint) ---------------------------


def test_axis_tuple_grouping_disabled_below_threshold() -> None:
    cells = [
        {"cell_id": f"c{i}", "axis_selections": {"tone": "warm"}}
        for i in range(DEFAULT_CELL_GROUPING_THRESHOLD)
    ]
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(cells=cells), _matrix_script_panel()
    )
    assert bundle["should_group_cells"] is False
    assert bundle["axis_tuple_groupings"] == []


def test_axis_tuple_grouping_enabled_above_threshold() -> None:
    cells = (
        [{"cell_id": f"warm-{i}", "axis_selections": {"tone": "warm"}} for i in range(5)]
        + [{"cell_id": f"cool-{i}", "axis_selections": {"tone": "cool"}} for i in range(3)]
    )
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(cells=cells), _matrix_script_panel()
    )
    assert bundle["should_group_cells"] is True
    groupings = bundle["axis_tuple_groupings"]
    assert len(groupings) == 2
    # Sorted by descending count then group_key — `warm` (5) precedes `cool` (3).
    assert groupings[0]["group_key"] == "tone=warm"
    assert groupings[0]["count"] == 5
    assert groupings[1]["group_key"] == "tone=cool"
    assert groupings[1]["count"] == 3
    # Sample cell ids capped at 3.
    assert len(groupings[0]["sample_cell_ids"]) == 3
    assert len(groupings[1]["sample_cell_ids"]) == 3


def test_axis_tuple_grouping_handles_empty_axis_selections() -> None:
    cells = [{"cell_id": f"c{i}", "axis_selections": {}} for i in range(8)]
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(cells=cells), _matrix_script_panel()
    )
    groupings = bundle["axis_tuple_groupings"]
    assert len(groupings) == 1
    assert groupings[0]["group_key"] == "—"
    assert groupings[0]["count"] == 8


def test_axis_tuple_grouping_threshold_override() -> None:
    cells = [{"cell_id": f"c{i}", "axis_selections": {"tone": "warm"}} for i in range(3)]
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(cells=cells),
        _matrix_script_panel(),
        cell_grouping_threshold=2,
    )
    assert bundle["should_group_cells"] is True
    assert bundle["cell_grouping_threshold"] == 2


# -- 8. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_workbench_comprehension(
        _variation_surface(), _matrix_script_panel()
    )
    forbidden = {"vendor_id", "model_id", "provider", "provider_id", "engine_id", "raw_provider_route"}

    def _walk_forbidden(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value.keys()) & forbidden)
            for v in value.values():
                _walk_forbidden(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _walk_forbidden(v)

    _walk_forbidden(bundle)


# -- 9. Helper does not mutate inputs ----------------------------------


def test_helper_does_not_mutate_inputs() -> None:
    surface = _variation_surface(
        axes=[{"axis_id": "tone"}],
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "warm"}}],
        slots=[{"slot_id": "s1"}],
    )
    panel = _matrix_script_panel()
    snapshot_surface = repr(surface)
    snapshot_panel = repr(panel)
    derive_matrix_script_workbench_comprehension(surface, panel)
    assert repr(surface) == snapshot_surface
    assert repr(panel) == snapshot_panel
