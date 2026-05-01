"""Phase 3B presenter-side wiring tests.

Covers the additive adapter that bridges existing presenter shapes
into the Phase 3A projection module.
"""
from __future__ import annotations

from gateway.app.services.operator_visible_surfaces.wiring import (
    build_board_row_projection,
    build_operator_surfaces_for_publish_hub,
    build_operator_surfaces_for_workbench,
)


# ---------- Board row projection ----------


def test_board_row_projection_marks_publishable_when_gate_open():
    row = {
        "task_id": "t1",
        "ready_gate": {
            "publish_ready": True,
            "compose_ready": True,
            "blocking": [],
        },
    }
    assert build_board_row_projection(row) == {
        "publishable": True,
        "head_reason": None,
    }


def test_board_row_projection_surfaces_first_blocking_as_head_reason():
    row = {
        "ready_gate": {
            "publish_ready": False,
            "compose_ready": True,
            "blocking": ["final_missing", "compose_not_ready"],
        },
    }
    out = build_board_row_projection(row)
    assert out["publishable"] is False
    assert out["head_reason"] == "final_missing"


def test_board_row_projection_handles_missing_ready_gate():
    out = build_board_row_projection({"task_id": "t1"})
    assert out == {"publishable": False, "head_reason": None}


# ---------- Workbench bundle ----------


def test_workbench_bundle_returns_all_four_surface_keys():
    task = {"task_id": "t1", "line_specific_refs": []}
    state = {
        "ready_gate": {
            "publish_ready": True,
            "compose_ready": True,
            "blocking": [],
        },
        "final": {"exists": True},
        "final_stale_reason": None,
    }
    out = build_operator_surfaces_for_workbench(task=task, authoritative_state=state)
    assert set(out.keys()) == {"board", "workbench", "delivery", "hot_follow_panel"}
    assert out["board"]["publishable"] is True
    assert out["delivery"]["publish_gate"] is True
    assert out["workbench"]["line_specific_panel"]["panel_kind"] is None
    assert out["hot_follow_panel"]["mounted"] is False


def test_workbench_bundle_mounts_hot_follow_panel_via_packet_refs():
    task = {
        "task_id": "t1",
        "line_specific_refs": [
            {"ref_id": "hot_follow_subtitle_authority", "binds_to": ["x"]},
        ],
    }
    out = build_operator_surfaces_for_workbench(
        task=task,
        authoritative_state={"ready_gate": {}, "final": {"exists": False}},
    )
    assert out["workbench"]["line_specific_panel"]["panel_kind"] == "hot_follow"
    assert out["hot_follow_panel"]["mounted"] is True
    assert out["hot_follow_panel"]["refs"][0]["ref_id"] == "hot_follow_subtitle_authority"


def test_workbench_bundle_falls_back_to_task_ready_gate_when_state_missing_it():
    task = {
        "ready_gate": {
            "publish_ready": True,
            "compose_ready": True,
            "blocking": [],
        },
    }
    out = build_operator_surfaces_for_workbench(
        task=task,
        authoritative_state={"final": {"exists": True}, "final_stale_reason": None},
    )
    assert out["board"]["publishable"] is True
    assert out["delivery"]["publish_gate"] is True


def test_workbench_bundle_pulls_packet_refs_from_task_packet_envelope():
    task = {
        "packet": {
            "line_specific_refs": [{"ref_id": "matrix_script_variation_matrix"}],
        }
    }
    out = build_operator_surfaces_for_workbench(
        task=task,
        authoritative_state=None,
    )
    assert out["workbench"]["line_specific_panel"]["panel_kind"] == "matrix_script"


# ---------- Publish hub bundle ----------


def test_publish_hub_bundle_blocks_when_final_stale():
    task = {"task_id": "t1"}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "final_stale_reason": "out_of_date_after_dub",
    }
    out = build_operator_surfaces_for_publish_hub(task=task, authoritative_state=state)
    assert out["publish_gate"] is False
    assert out["publish_gate_head_reason"] == "out_of_date_after_dub"
    assert out["publish_status_mirror"]["publish_status"] == "not_published"
    assert out["line_specific_panel"]["panel_kind"] is None


def test_publish_hub_bundle_mirrors_digital_anchor_closure():
    closure = {
        "line_id": "digital_anchor",
        "publish_status": "published",
        "publish_url": "https://example.com/post/1",
        "channel_metrics": {"channel_id": "douyin"},
        "feedback_closure_records": [{"recorded_at": "2026-04-30T10:00:00Z"}],
    }
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "final_stale_reason": None,
    }
    out = build_operator_surfaces_for_publish_hub(
        task={},
        authoritative_state=state,
        publish_feedback_closure=closure,
    )
    assert out["publish_gate"] is True
    assert out["publish_status_mirror"] == {
        "last_published_at": "2026-04-30T10:00:00Z",
        "publish_status": "published",
        "publish_url": "https://example.com/post/1",
        "publish_channel": "douyin",
    }


def test_publish_hub_bundle_optional_items_never_block_gate():
    """Optional deliverables (scene_pack etc.) are excluded by construction."""
    task = {"line_specific_refs": []}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "final_stale_reason": None,
        # Authoritative state may carry optional artifact info that is *not*
        # consumed by the gate. Asserting it doesn't accidentally block.
        "scene_pack": {"exists": False},
        "scene_pack_pending_reason": "not_yet_built",
    }
    out = build_operator_surfaces_for_publish_hub(task=task, authoritative_state=state)
    assert out["publish_gate"] is True
    assert out["publish_gate_head_reason"] is None


def test_publish_hub_bundle_never_carries_vendor_keys():
    """Sanitizer applies to ref payloads forwarded through the resolver."""
    task = {
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "binds_to": ["x"],
                "vendor_id": "leak-attempt",
                "model_id": "leak-attempt",
            },
        ],
    }
    state = {
        "ready_gate": {},
        "final": {"exists": False},
        "final_stale_reason": None,
    }
    out = build_operator_surfaces_for_publish_hub(task=task, authoritative_state=state)
    refs = out["line_specific_panel"]["refs"]
    assert refs and "vendor_id" not in refs[0] and "model_id" not in refs[0]
