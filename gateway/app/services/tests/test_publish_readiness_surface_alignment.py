"""Surface-alignment integration tests
(Operator Capability Recovery, PR-1 reviewer-fix).

The reviewer-fail finding: Workbench rendered `ops.delivery.publish_gate`
+ `ops.board.publishable` from two paths fed different inputs (Board
without L2, Delivery with L2), so the same task could produce different
publishability strings on Board vs Delivery vs Workbench. PR-1 collapses
all three onto the unified `compute_publish_readiness` producer with the
same inputs; these tests prove the surfaces agree.

Authority:
- ``docs/contracts/publish_readiness_contract_v1.md`` §"Single-producer rule"
- ``docs/contracts/factory_delivery_contract_v1.md``
  §"Per-Deliverable Required / Blocking Fields (Plan D Amendment)"
  §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)"
- ``docs/contracts/hot_follow_current_attempt_contract_v1.md``
  §"`final_provenance` Field (Plan D Amendment)"

Discipline: import-light. Builds the surface bundles directly via
`build_board_row_projection` and `build_operator_surfaces_for_workbench`
without instantiating the FastAPI app or the publish-hub HTTP path.
"""
from __future__ import annotations

from typing import Any

import pytest

from gateway.app.services.operator_visible_surfaces import (
    CLOSED_HEAD_REASON_ENUM,
    build_board_row_projection,
    build_operator_surfaces_for_publish_hub,
    build_operator_surfaces_for_workbench,
    compute_publish_readiness,
)


def _build_surfaces(task: dict, state: dict) -> tuple[dict, dict, dict]:
    """Assemble Board, Workbench, Delivery views for the same task state."""
    board = build_board_row_projection({**task, "ready_gate": state.get("ready_gate") or {}, "final": state.get("final"), "final_stale_reason": state.get("final_stale_reason"), "current_attempt": state.get("current_attempt")})
    workbench = build_operator_surfaces_for_workbench(
        task=task,
        authoritative_state=state,
    )
    delivery = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state=state,
    )
    return board, workbench, delivery


# ---------- Same task state → same publishability across surfaces --------


def test_alignment_publishable_state_agrees_on_all_three_surfaces() -> None:
    task = {"task_id": "t1", "kind": "hot_follow", "ready_gate": {"publish_ready": True, "compose_ready": True}}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "final_stale_reason": None,
        "current_attempt": {"final_provenance": "current"},
    }
    board, workbench, delivery = _build_surfaces(task, state)

    assert board["publishable"] is True
    assert workbench["publish_readiness"]["publishable"] is True
    assert delivery["publish_readiness"]["publishable"] is True
    # Workbench's overlaid `board` and `delivery` views also agree
    assert workbench["board"]["publishable"] is True
    assert workbench["delivery"]["publish_gate"] is True
    # And the legacy two-field shape on Delivery's bundle agrees
    assert delivery["publish_gate"] is True


def test_alignment_blocked_state_agrees_on_all_three_surfaces() -> None:
    task = {"task_id": "t2", "kind": "hot_follow"}
    state = {
        "ready_gate": {"publish_ready": False, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
    }
    board, workbench, delivery = _build_surfaces(task, state)

    # All three surfaces report blocked with the SAME head_reason from the
    # SAME closed enum.
    assert board["publishable"] is False
    assert workbench["publish_readiness"]["publishable"] is False
    assert delivery["publish_readiness"]["publishable"] is False

    head = workbench["publish_readiness"]["head_reason"]
    assert head in CLOSED_HEAD_REASON_ENUM
    assert board["head_reason"] == head
    assert delivery["publish_gate_head_reason"] == head
    assert workbench["board"]["head_reason"] == head
    assert workbench["delivery"]["publish_gate_head_reason"] == head


def test_alignment_with_ready_gate_blocking_strings() -> None:
    """Even when ready_gate emits a known blocking string, the normalized
    head_reason is identical across surfaces and remains in the closed enum.
    """
    task = {"task_id": "t3", "kind": "hot_follow"}
    state = {
        "ready_gate": {
            "publish_ready": False,
            "compose_ready": False,
            "blocking": ["voiceover_missing"],
        },
        "final": {"exists": True},
    }
    board, workbench, delivery = _build_surfaces(task, state)

    head = workbench["publish_readiness"]["head_reason"]
    assert head in CLOSED_HEAD_REASON_ENUM
    assert head == "publish_not_ready"
    assert board["head_reason"] == head
    assert delivery["publish_gate_head_reason"] == head
    assert workbench["delivery"]["publish_gate_head_reason"] == head
    assert workbench["board"]["head_reason"] == head


# ---------- final_provenance="historical" --------------------------------


def test_alignment_final_provenance_historical() -> None:
    """When L3 declares the final historical, all three surfaces refuse to
    publish with the same closed-enum head_reason.
    """
    task = {"task_id": "t4", "kind": "hot_follow"}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "current_attempt": {"final_provenance": "historical"},
    }
    board, workbench, delivery = _build_surfaces(task, state)

    head = workbench["publish_readiness"]["head_reason"]
    assert head == "final_provenance_historical"
    assert head in CLOSED_HEAD_REASON_ENUM
    # Board sees the same provenance via `current_attempt` plumbed in
    assert board["publishable"] is False
    assert board["head_reason"] == "final_provenance_historical"
    assert delivery["publish_readiness"]["publishable"] is False
    assert delivery["publish_gate_head_reason"] == "final_provenance_historical"


def test_alignment_final_provenance_current_does_not_block() -> None:
    task = {"task_id": "t5", "kind": "hot_follow"}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "current_attempt": {"final_provenance": "current"},
    }
    board, workbench, delivery = _build_surfaces(task, state)
    assert board["publishable"] is True
    assert workbench["publish_readiness"]["publishable"] is True
    assert delivery["publish_gate"] is True


# ---------- Matrix Script blocking rows ----------------------------------


def _matrix_script_task_with_unresolved_required_row() -> tuple[dict, dict]:
    """Build a Matrix Script task whose `project_delivery_binding` will
    surface an unresolved required row (today's Plan E B4 default emits
    `artifact_lookup_unresolved` because the L3 final_provenance emitter
    isn't wired into Matrix Script presenter yet — exactly the case PR-1
    must gate cleanly).
    """
    packet = {
        "line_id": "matrix_script",
        "binding": {},
        "evidence": {},
    }
    task = {
        "task_id": "ms-1",
        "kind": "matrix_script",
        "packet": packet,
    }
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
    }
    return task, state


def test_alignment_matrix_script_blocking_required_row() -> None:
    """PR-1 reviewer-fix #2 closure test: unconditional. A Matrix Script
    packet with no resolved artifact handles MUST produce a blocked
    publish_readiness through the unified producer path on BOTH the
    Workbench and Delivery surfaces. Failure here means either:
      (a) `_matrix_script_delivery_rows` is reading from the wrong key
          on the delivery binding output (real bug fixed in this PR), or
      (b) the producer's row-status reader does not understand the
          contract `artifact_lookup` shape (also fixed in this PR).
    """
    task, state = _matrix_script_task_with_unresolved_required_row()
    workbench = build_operator_surfaces_for_workbench(task=task, authoritative_state=state)
    delivery = build_operator_surfaces_for_publish_hub(task=task, authoritative_state=state)

    workbench_pr = workbench["publish_readiness"]
    delivery_pr = delivery["publish_readiness"]

    # Cross-surface agreement first.
    assert workbench_pr["publishable"] == delivery_pr["publishable"]
    assert workbench_pr["head_reason"] == delivery_pr["head_reason"]
    assert workbench_pr["head_reason"] in CLOSED_HEAD_REASON_ENUM

    # Unconditional blocked-result assertion — this is the reviewer's
    # explicit requirement: unresolved required rows MUST produce blocked.
    assert workbench_pr["publishable"] is False, (
        "Matrix Script unresolved required rows did not block publish via the "
        "unified producer; check `_matrix_script_delivery_rows` read path."
    )
    assert delivery_pr["publishable"] is False
    assert workbench_pr["head_reason"] in {
        "required_deliverable_missing",
        "required_deliverable_blocking",
    }, (
        f"Expected required-deliverable head_reason; got {workbench_pr['head_reason']!r}."
    )

    # Legacy two-field shape on Delivery agrees too.
    assert delivery["publish_gate"] is False
    assert delivery["publish_gate_head_reason"] == workbench_pr["head_reason"]
    # Workbench's overlaid bundle.delivery agrees.
    assert workbench["delivery"]["publish_gate"] is False
    assert workbench["delivery"]["publish_gate_head_reason"] == workbench_pr["head_reason"]
    assert workbench["board"]["publishable"] is False


def test_matrix_script_delivery_rows_reaches_producer_via_authoritative_path() -> None:
    """Direct read-path assertion: `_matrix_script_delivery_rows` returns
    the same rows the delivery binding's `delivery_pack.deliverables`
    list contains. Guards against future refactors that move the rows.
    """
    from gateway.app.services.matrix_script.delivery_binding import (
        project_delivery_binding,
    )
    from gateway.app.services.operator_visible_surfaces.wiring import (
        _matrix_script_delivery_rows,
    )

    task, _state = _matrix_script_task_with_unresolved_required_row()
    packet = task["packet"]
    binding = project_delivery_binding(packet)
    expected_rows = binding["delivery_pack"]["deliverables"]
    actual_rows = _matrix_script_delivery_rows(packet)

    assert actual_rows is not None, (
        "_matrix_script_delivery_rows returned None — read path is broken."
    )
    assert len(actual_rows) == len(expected_rows) > 0
    # Every expected required row appears in what reaches the producer.
    expected_required_kinds = sorted(
        r["kind"] for r in expected_rows if r.get("required")
    )
    actual_required_kinds = sorted(
        r["kind"] for r in actual_rows if r.get("required")
    )
    assert actual_required_kinds == expected_required_kinds
    assert "variation_manifest" in actual_required_kinds
    assert "script_slot_bundle" in actual_required_kinds


def test_alignment_matrix_script_resolved_rows_publish() -> None:
    """When Matrix Script delivery rows are not blocking (passed directly
    via the producer for a synthesis test), the surfaces all agree.
    """
    rows = [
        {
            "kind": "variation_manifest",
            "required": True,
            "blocking_publish": True,
            "artifact_lookup": {"status": "resolved"},
        },
        {
            "kind": "scene_pack",
            "required": False,
            "blocking_publish": False,
            "artifact_lookup": {"status": "unresolved"},
        },
    ]
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        l3_current_attempt={"final_provenance": "current"},
        delivery_rows=rows,
    )
    assert result["publishable"] is True


# ---------- scene_pack remains non-blocking ------------------------------


def test_alignment_scene_pack_never_blocks_publish() -> None:
    """`factory_delivery_contract_v1.md` §"Scene-Pack Non-Blocking Rule" —
    scene_pack rows MUST NOT block publish, even if a malformed row asserts
    `required=true, blocking_publish=true`. The producer clamps
    defensively; surfaces agree.
    """
    malformed = [
        {
            "kind": "scene_pack",
            "required": True,
            "blocking_publish": True,
            "artifact_lookup": {"status": "unresolved"},
        }
    ]
    result = compute_publish_readiness(
        ready_gate={"publish_ready": True, "compose_ready": True},
        l2_facts={"final": {"exists": True}},
        l3_current_attempt={"final_provenance": "current"},
        delivery_rows=malformed,
    )
    assert result["publishable"] is True
    assert result["head_reason"] == "publishable_ok"


def test_alignment_scene_pack_unresolved_does_not_change_workbench_or_delivery() -> None:
    """For a Hot Follow task with an unresolved scene_pack pending and
    everything else green, all three surfaces still report publishable.
    """
    task = {"task_id": "t-sp", "kind": "hot_follow"}
    state = {
        "ready_gate": {"publish_ready": True, "compose_ready": True, "blocking": []},
        "final": {"exists": True},
        "current_attempt": {"final_provenance": "current"},
    }
    board, workbench, delivery = _build_surfaces(task, state)
    # Hot Follow does not surface delivery rows today (Hot Follow has no
    # contract-frozen per-row zoning yet); the unified producer accepts
    # delivery_rows=None and remains publishable.
    assert board["publishable"] is True
    assert workbench["publish_readiness"]["publishable"] is True
    assert delivery["publish_gate"] is True


# ---------- Cross-surface invariant under randomized states --------------


@pytest.mark.parametrize(
    "ready_gate,final_exists,final_stale_reason,provenance",
    [
        ({"publish_ready": True, "compose_ready": True}, True, None, "current"),
        ({"publish_ready": False, "compose_ready": True}, True, None, "current"),
        ({"publish_ready": True, "compose_ready": False}, True, None, "current"),
        ({"publish_ready": True, "compose_ready": True}, False, None, "current"),
        ({"publish_ready": True, "compose_ready": True}, True, "subtitle_changed", "current"),
        ({"publish_ready": True, "compose_ready": True}, True, None, "historical"),
        ({"publish_ready": True, "compose_ready": True, "blocking": ["voiceover_missing"]}, True, None, "current"),
        ({"publish_ready": True, "compose_ready": True, "blocking": ["unknown_future_reason"]}, True, None, "current"),
    ],
)
def test_alignment_invariant_board_workbench_delivery_agree(
    ready_gate: dict[str, Any],
    final_exists: bool,
    final_stale_reason: str | None,
    provenance: str,
) -> None:
    """Cross-surface invariant: for any reachable input combination, Board,
    Workbench, and Delivery report the same publishable boolean and the
    same closed-enum head_reason.
    """
    task = {"task_id": "t-inv", "kind": "hot_follow"}
    state = {
        "ready_gate": dict(ready_gate),
        "final": {"exists": final_exists},
        "final_stale_reason": final_stale_reason,
        "current_attempt": {"final_provenance": provenance},
    }
    board, workbench, delivery = _build_surfaces(task, state)

    assert board["publishable"] == workbench["publish_readiness"]["publishable"]
    assert board["publishable"] == delivery["publish_readiness"]["publishable"]
    assert board["head_reason"] == workbench["publish_readiness"]["head_reason"]
    assert board["head_reason"] == delivery["publish_gate_head_reason"]
    if board["head_reason"] is not None:
        assert board["head_reason"] in CLOSED_HEAD_REASON_ENUM
