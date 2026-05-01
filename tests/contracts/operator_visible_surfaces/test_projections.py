"""Phase 3A: minimal wiring for operator-visible surfaces.

Covers:
- Gap A1 — Board per-packet `publishable` boolean
- Gap A2 — Single derived Delivery publish gate
- Gap A3 — Delivery last-publish-status mirror (read-only)
- Workbench `line_specific_refs[]` mount resolver
- Operator-payload hygiene (no vendor/model/provider/engine leak)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gateway.app.services.operator_visible_surfaces import (
    PANEL_REF_DISPATCH,
    derive_board_publishable,
    derive_delivery_publish_gate,
    derive_delivery_publish_status_mirror,
    resolve_line_specific_panel,
    sanitize_operator_payload,
)
from gateway.app.services.operator_visible_surfaces.projections import (
    FORBIDDEN_OPERATOR_KEYS,
    project_operator_surfaces,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------- Gap A1: Board publishable ----------


def test_board_publishable_true_when_ready_gate_clean():
    out = derive_board_publishable(
        {"publish_ready": True, "compose_ready": True, "blocking": []}
    )
    assert out == {"publishable": True, "head_reason": None}


def test_board_publishable_false_with_blocker_head_reason():
    out = derive_board_publishable(
        {
            "publish_ready": False,
            "compose_ready": True,
            "blocking": ["compose_input_blocked", "subtitle_missing"],
            "compose_reason": "compose_input_blocked",
        }
    )
    assert out["publishable"] is False
    assert out["head_reason"] == "compose_input_blocked"


def test_board_publishable_falls_back_to_compose_reason_when_no_blocking():
    out = derive_board_publishable(
        {
            "publish_ready": False,
            "compose_ready": False,
            "blocking": [],
            "compose_reason": "route_not_allowed",
        }
    )
    assert out == {"publishable": False, "head_reason": "route_not_allowed"}


def test_board_publishable_handles_missing_ready_gate():
    out = derive_board_publishable({})
    assert out == {"publishable": False, "head_reason": None}


# ---------- Gap A2: Delivery publish gate ----------


def test_delivery_publish_gate_open_when_all_inputs_ready():
    out = derive_delivery_publish_gate(
        {"publish_ready": True, "compose_ready": True, "blocking": []},
        {"final": {"exists": True}},
    )
    assert out == {"publish_gate": True, "publish_gate_head_reason": None}


def test_delivery_publish_gate_closed_when_final_missing():
    out = derive_delivery_publish_gate(
        {"publish_ready": True, "compose_ready": True, "blocking": []},
        {"final": {"exists": False}},
    )
    assert out["publish_gate"] is False
    assert out["publish_gate_head_reason"] == "final_missing"


def test_delivery_publish_gate_closed_when_final_stale():
    out = derive_delivery_publish_gate(
        {"publish_ready": True, "compose_ready": True, "blocking": []},
        {"final": {"exists": True}, "final_stale_reason": "final_stale_after_subtitle_change"},
    )
    assert out["publish_gate"] is False
    assert out["publish_gate_head_reason"] == "final_stale_after_subtitle_change"


def test_delivery_publish_gate_uses_first_blocker_head_reason():
    out = derive_delivery_publish_gate(
        {
            "publish_ready": False,
            "compose_ready": False,
            "blocking": ["compose_exec_failed"],
        },
        {"final": {"exists": True}},
    )
    assert out == {
        "publish_gate": False,
        "publish_gate_head_reason": "compose_exec_failed",
    }


def test_optional_items_never_block_publish_gate():
    """scene_pack / pack_zip / edit_bundle_zip are not inputs to the gate."""
    # An optional pack failing must not appear in the gate inputs.
    ready_gate = {"publish_ready": True, "compose_ready": True, "blocking": []}
    l2 = {"final": {"exists": True}, "scene_pack": {"exists": False}}
    out = derive_delivery_publish_gate(ready_gate, l2)
    assert out["publish_gate"] is True


# ---------- Gap A3: Delivery publish-status mirror ----------


def test_publish_status_mirror_empty_when_no_closure():
    out = derive_delivery_publish_status_mirror(None)
    assert out == {
        "last_published_at": None,
        "publish_status": "not_published",
        "publish_url": None,
        "publish_channel": None,
    }


def test_publish_status_mirror_reads_digital_anchor_closure():
    closure = {
        "line_id": "digital_anchor",
        "publish_status": "published",
        "publish_url": "https://example/v",
        "channel_metrics": {"channel_id": "yt"},
        "feedback_closure_records": [
            {"recorded_at": "2026-04-30T12:00:00Z"},
            {"recorded_at": "2026-05-01T08:30:00Z"},
        ],
    }
    out = derive_delivery_publish_status_mirror(closure)
    assert out == {
        "last_published_at": "2026-05-01T08:30:00Z",
        "publish_status": "published",
        "publish_url": "https://example/v",
        "publish_channel": "yt",
    }


def test_publish_status_mirror_aggregates_matrix_script_rows():
    closure = {
        "line_id": "matrix_script",
        "variation_feedback": [
            {"variation_id": "c1", "publish_status": "published", "publish_url": "u1",
             "channel_metrics": [{"channel_id": "yt"}]},
            {"variation_id": "c2", "publish_status": "published", "publish_url": None,
             "channel_metrics": [{"channel_id": "yt"}]},
        ],
        "feedback_closure_records": [
            {"recorded_at": "2026-05-01T01:00:00Z"},
        ],
    }
    out = derive_delivery_publish_status_mirror(closure)
    assert out["publish_status"] == "published"
    assert out["publish_url"] == "u1"
    assert out["publish_channel"] == "yt"
    assert out["last_published_at"] == "2026-05-01T01:00:00Z"


def test_publish_status_mirror_matrix_script_pending_when_mixed():
    closure = {
        "line_id": "matrix_script",
        "variation_feedback": [
            {"variation_id": "c1", "publish_status": "published"},
            {"variation_id": "c2", "publish_status": "pending"},
        ],
    }
    out = derive_delivery_publish_status_mirror(closure)
    assert out["publish_status"] == "pending"


def test_publish_status_mirror_reports_failed_for_matrix_script():
    closure = {
        "line_id": "matrix_script",
        "variation_feedback": [
            {"variation_id": "c1", "publish_status": "published"},
            {"variation_id": "c2", "publish_status": "failed"},
        ],
    }
    out = derive_delivery_publish_status_mirror(closure)
    assert out["publish_status"] == "failed"


# ---------- Workbench line_specific_refs[] mount resolver ----------


@pytest.mark.parametrize(
    "ref_id,expected_panel",
    [
        ("matrix_script_variation_matrix", "matrix_script"),
        ("matrix_script_slot_pack", "matrix_script"),
        ("digital_anchor_role_pack", "digital_anchor"),
        ("digital_anchor_speaker_plan", "digital_anchor"),
        ("hot_follow_subtitle_authority", "hot_follow"),
        ("hot_follow_dub_compose_legality", "hot_follow"),
    ],
)
def test_resolver_dispatches_each_frozen_ref_id(ref_id, expected_panel):
    assert PANEL_REF_DISPATCH[ref_id] == expected_panel
    out = resolve_line_specific_panel({"line_specific_refs": [{"ref_id": ref_id}]})
    assert out["panel_kind"] == expected_panel
    assert [r["ref_id"] for r in out["refs"]] == [ref_id]


def test_resolver_returns_none_when_no_known_ref_id():
    out = resolve_line_specific_panel({"line_specific_refs": [{"ref_id": "unknown_ref"}]})
    assert out == {"panel_kind": None, "refs": []}


def test_resolver_handles_missing_line_specific_refs():
    assert resolve_line_specific_panel({}) == {"panel_kind": None, "refs": []}


def test_resolver_works_against_matrix_script_sample_packet():
    sample = REPO_ROOT / "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json"
    packet = json.loads(sample.read_text(encoding="utf-8"))
    out = resolve_line_specific_panel(packet)
    assert out["panel_kind"] == "matrix_script"
    ref_ids = {r["ref_id"] for r in out["refs"]}
    assert "matrix_script_variation_matrix" in ref_ids


def test_resolver_works_against_digital_anchor_sample_packet():
    sample = REPO_ROOT / "schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json"
    packet = json.loads(sample.read_text(encoding="utf-8"))
    out = resolve_line_specific_panel(packet)
    assert out["panel_kind"] == "digital_anchor"
    ref_ids = {r["ref_id"] for r in out["refs"]}
    assert "digital_anchor_role_pack" in ref_ids


# ---------- Operator-payload hygiene ----------


def test_sanitize_strips_all_forbidden_vendor_keys():
    raw = {
        "ref_id": "x",
        "vendor_id": "v",
        "model_id": "m",
        "provider": "p",
        "provider_id": "pid",
        "engine_id": "e",
        "raw_provider_route": "rpr",
        "safe_field": "kept",
    }
    cleaned = sanitize_operator_payload(raw)
    assert "safe_field" in cleaned
    assert cleaned["ref_id"] == "x"
    for forbidden in FORBIDDEN_OPERATOR_KEYS:
        assert forbidden not in cleaned


def test_resolver_payload_is_sanitized():
    ref = {
        "ref_id": "matrix_script_variation_matrix",
        "delta": {"cells": []},
        "vendor_id": "leaked-vendor",
        "model_id": "leaked-model",
    }
    out = resolve_line_specific_panel({"line_specific_refs": [ref]})
    payload = out["refs"][0]["ref_payload"]
    assert "vendor_id" not in payload
    assert "model_id" not in payload
    assert payload["ref_id"] == "matrix_script_variation_matrix"
    assert payload["delta"] == {"cells": []}


# ---------- Combined surface projection ----------


def test_project_operator_surfaces_assembles_all_four_payloads():
    packet = {
        "line_id": "digital_anchor",
        "line_specific_refs": [
            {"ref_id": "digital_anchor_role_pack"},
            {"ref_id": "digital_anchor_speaker_plan"},
        ],
    }
    out = project_operator_surfaces(
        ready_gate={
            "publish_ready": True,
            "compose_ready": True,
            "blocking": [],
        },
        l2_facts={"final": {"exists": True}},
        packet=packet,
        publish_feedback_closure={
            "line_id": "digital_anchor",
            "publish_status": "pending",
            "feedback_closure_records": [],
        },
    )
    assert out["board"] == {"publishable": True, "head_reason": None}
    assert out["delivery"]["publish_gate"] is True
    assert out["delivery"]["publish_status_mirror"]["publish_status"] == "pending"
    assert out["workbench"]["line_specific_panel"]["panel_kind"] == "digital_anchor"
    assert out["hot_follow_panel"]["mounted"] is False


def test_project_operator_surfaces_for_hot_follow_panel_mount():
    packet = {
        "line_id": "hot_follow",
        "line_specific_refs": [
            {"ref_id": "hot_follow_subtitle_authority"},
            {"ref_id": "hot_follow_dub_compose_legality"},
        ],
    }
    out = project_operator_surfaces(
        ready_gate={"publish_ready": False, "compose_ready": False, "blocking": ["compose_input_blocked"]},
        l2_facts={"final": {"exists": False}},
        packet=packet,
    )
    assert out["board"]["publishable"] is False
    assert out["board"]["head_reason"] == "compose_input_blocked"
    assert out["delivery"]["publish_gate"] is False
    assert out["hot_follow_panel"]["mounted"] is True
    assert {r["ref_id"] for r in out["hot_follow_panel"]["refs"]} == {
        "hot_follow_subtitle_authority",
        "hot_follow_dub_compose_legality",
    }
