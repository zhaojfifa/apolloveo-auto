"""OWC-DA PR-2 — wiring + cross-line isolation tests for the five-panel bundle.

Asserts:
- The wiring layer attaches all five panel keys when ``panel_kind ==
  "digital_anchor"``.
- Hot Follow tasks do NOT receive any of the OWC-DA PR-2 keys.
- Matrix Script tasks do NOT receive any of the OWC-DA PR-2 keys.
- The matrix_script branch's existing five-panel bundle is unchanged
  for matrix_script tasks (regression guard against accidental
  cross-line mutation).
"""
from __future__ import annotations

from typing import Any

from gateway.app.services.operator_visible_surfaces.wiring import (
    build_operator_surfaces_for_workbench,
)


_DA_PR2_KEYS = (
    "digital_anchor_role_binding",
    "digital_anchor_content_structure",
    "digital_anchor_scene_template",
    "digital_anchor_language_output",
    "digital_anchor_review_zone",
)


def _da_task() -> dict[str, Any]:
    return {
        "task_id": "t_da_w_001",
        "kind": "digital_anchor",
        "config": {
            "line_id": "digital_anchor",
            "entry": {
                "topic": "wiring 测试",
                "source_script_ref": "content://da/source/wiring_test",
                "language_scope": {"source_language": "zh-CN", "target_language": ["en-US"]},
                "role_profile_ref": "ref://da/role/host",
                "role_framing_hint": "head",
                "output_intent": "wiring 测试",
                "speaker_segment_count_hint": 2,
            },
        },
        "packet": {
            "line_id": "digital_anchor",
            "packet_version": "v1",
            "binding": {
                "deliverable_profile_ref": "ref://da/dp",
                "asset_sink_profile_ref": "ref://da/sink",
                "capability_plan": [],
            },
            "evidence": {"ready_state": "ready"},
            "metadata": {},
            "generic_refs": [],
            "line_specific_refs": [
                {
                    "ref_id": "digital_anchor_role_pack",
                    "delta": {"roles": [{"role_id": "host", "framing_kind": "head"}]},
                },
                {
                    "ref_id": "digital_anchor_speaker_plan",
                    "delta": {"segments": [{"segment_id": "seg_01", "binds_role_id": "host"}]},
                },
            ],
        },
        "line_specific_refs": [
            {"ref_id": "digital_anchor_role_pack"},
            {"ref_id": "digital_anchor_speaker_plan"},
        ],
        "ready_gate": {"publish_ready": True, "compose_ready": True},
        "final": {"exists": True},
    }


def _hot_follow_task() -> dict[str, Any]:
    return {
        "task_id": "t_hf_001",
        "kind": "hot_follow",
        "config": {"line_id": "hot_follow"},
        "packet": {"line_id": "hot_follow", "line_specific_refs": []},
        "line_specific_refs": [],
        "ready_gate": {"publish_ready": True, "compose_ready": True},
        "final": {"exists": True},
    }


def _matrix_script_task() -> dict[str, Any]:
    return {
        "task_id": "t_ms_001",
        "kind": "matrix_script",
        "config": {"line_id": "matrix_script", "entry": {"topic": "x"}},
        "packet": {
            "line_id": "matrix_script",
            "packet_version": "v1",
            "line_specific_refs": [
                {
                    "ref_id": "matrix_script_variation_matrix",
                    "delta": {"axes": [], "cells": [{"cell_id": "c1"}]},
                },
            ],
        },
        "line_specific_refs": [
            {"ref_id": "matrix_script_variation_matrix"},
        ],
        "ready_gate": {"publish_ready": True, "compose_ready": True},
        "final": {"exists": True},
    }


def test_digital_anchor_task_carries_all_five_pr2_keys() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_da_task(),
        authoritative_state=None,
    )
    workbench = bundle["workbench"]
    for key in _DA_PR2_KEYS:
        assert key in workbench, f"missing key {key!r}"
        assert workbench[key].get("is_digital_anchor") is True


def test_hot_follow_task_does_not_carry_any_pr2_keys() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_hot_follow_task(),
        authoritative_state=None,
    )
    workbench = bundle["workbench"]
    for key in _DA_PR2_KEYS:
        assert key not in workbench, f"hot_follow leaked OWC-DA key {key!r}"


def test_matrix_script_task_does_not_carry_any_pr2_da_keys() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_matrix_script_task(),
        authoritative_state=None,
    )
    workbench = bundle["workbench"]
    for key in _DA_PR2_KEYS:
        assert key not in workbench, f"matrix_script leaked OWC-DA key {key!r}"


def test_matrix_script_existing_five_panel_keys_remain() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_matrix_script_task(),
        authoritative_state=None,
    )
    workbench = bundle["workbench"]
    # Existing OWC-MS PR-2 keys must remain on the matrix_script branch.
    for key in (
        "matrix_script_script_structure",
        "matrix_script_preview_compare",
        "matrix_script_review_zone",
        "matrix_script_qc_diagnostics",
    ):
        assert key in workbench


def test_digital_anchor_role_speaker_surface_still_attached() -> None:
    # Recovery PR-4 substrate: the role-speaker surface must still attach.
    bundle = build_operator_surfaces_for_workbench(
        task=_da_task(),
        authoritative_state=None,
    )
    assert "digital_anchor_role_speaker_surface" in bundle["workbench"]


def test_digital_anchor_review_zone_carries_endpoint_url_with_task_id() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_da_task(),
        authoritative_state=None,
    )
    review = bundle["workbench"]["digital_anchor_review_zone"]
    assert review["closure_endpoint_url"] == "/api/digital-anchor/closures/t_da_w_001/events"


def test_digital_anchor_review_zone_enum_size_is_five() -> None:
    bundle = build_operator_surfaces_for_workbench(
        task=_da_task(),
        authoritative_state=None,
    )
    review = bundle["workbench"]["digital_anchor_review_zone"]
    assert len(review["review_zone_enum"]) == 5
