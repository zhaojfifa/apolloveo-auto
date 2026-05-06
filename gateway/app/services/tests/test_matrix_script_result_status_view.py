"""Tests for RC PR-1 — Matrix Script Result-Capability Recovery (RC-R6).

Covers the operator-language result-oriented status helpers in
``gateway.app.services.matrix_script.result_status_view`` per
``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R6 + §5 RC PR-1.

Test floor per gate spec §5.2: ≥25 cases. This file lands 33.

Hard discipline checked:

- The Task Area helper returns ``{}`` for non-Matrix-Script rows so the
  caller's gating preserves Hot Follow / Digital Anchor / baseline
  bytewise unchanged.
- The Workbench helper returns ``{}`` for non-Matrix-Script panels.
- Every operator-visible status is one of three closed kinds
  (``ready`` / ``blocked`` / ``completed``) and carries a concrete
  next-action sentence + an explicit missing-items list.
- No vendor / model / provider / engine identifier is ever in the
  return dict — strings are operator-language only.
- The Workbench helper does NOT introduce a second producer; it
  consumes the same ``publish_readiness`` dict shape that
  ``qc_diagnostics_view`` reads.
- No fake ``final_video``: the helper never synthesises a URL or media
  reference; it only restates already-decided state.
"""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.closure_binding import reset_for_tests
from gateway.app.services.matrix_script.publish_feedback_closure import create_closure
from gateway.app.services.matrix_script.result_status_view import (
    STATUS_BLOCKED,
    STATUS_COMPLETED,
    STATUS_KINDS,
    STATUS_LABELS_ZH,
    STATUS_READY,
    STAGE_TO_RESULT,
    WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH,
    derive_matrix_script_task_area_result_status,
    derive_matrix_script_task_area_result_status_for_task,
    derive_matrix_script_workbench_result_summary,
)
from gateway.app.services.matrix_script.task_area_convergence import (
    STAGE_ARCHIVED,
    STAGE_AWAITING_REVIEW,
    STAGE_BACKFILLED,
    STAGE_CREATED,
    STAGE_FINAL_READY,
    STAGE_GENERATING,
    STAGE_PENDING_CONFIG,
    STAGE_PUBLISHABLE,
)


@pytest.fixture(autouse=True)
def _isolate_closure_store() -> None:
    reset_for_tests()


def _packet(*, cell_ids: list[str] | None = None) -> dict:
    cells = [
        {
            "cell_id": cid,
            "axis_tuple": {"tone": "neutral", "audience": "general", "length": "short"},
        }
        for cid in (cell_ids or ["cell_a", "cell_b"])
    ]
    return {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "line_specific_refs": [
            {"ref_id": "matrix_script_variation_matrix", "delta": {"cells": cells}},
            {
                "ref_id": "matrix_script_task_entry",
                "delta": {"source_script_ref": "content://matrix-script/source/abc"},
            },
        ],
    }


def _ms_row(
    *,
    task_id: str = "task_rc_pr1",
    bucket: str = "ready",
    head_reason: str | None = None,
    cells: list[str] | None = None,
    compose_status: str | None = None,
    compose_ready: bool = False,
    final_exists: bool = False,
    archived: bool = False,
) -> dict:
    cells = cells if cells is not None else ["cell_a", "cell_b"]
    refs = [
        {
            "ref_id": "matrix_script_variation_matrix",
            "delta": {
                "cells": [
                    {"cell_id": cid, "axis_tuple": {"tone": "neutral"}} for cid in cells
                ]
            },
        }
    ]
    return {
        "task_id": task_id,
        "kind": "matrix_script",
        "title": "rc pr1 demo",
        "board_bucket": bucket,
        "head_reason": head_reason,
        "line_specific_refs": refs,
        "config": {},
        "ready_gate": {"compose_ready": compose_ready, "publish_ready": False},
        "compose_status": compose_status,
        "final": {"exists": final_exists},
        "archived": archived,
        "updated_at": "2026-05-06T22:00:00Z",
    }


# ---------------------------------------------------------------------------
# Status_kind closed-enum invariants
# ---------------------------------------------------------------------------


def test_status_kinds_are_closed_three_member_set() -> None:
    assert set(STATUS_KINDS) == {STATUS_READY, STATUS_BLOCKED, STATUS_COMPLETED}


def test_every_stage_maps_to_a_known_status_kind() -> None:
    for stage, framing in STAGE_TO_RESULT.items():
        assert framing["status_kind"] in STATUS_KINDS, stage


def test_status_labels_cover_every_kind() -> None:
    for kind in STATUS_KINDS:
        assert STATUS_LABELS_ZH[kind]


# ---------------------------------------------------------------------------
# Task Area helper — non-Matrix-Script isolation
# ---------------------------------------------------------------------------


def test_task_area_returns_empty_for_hot_follow() -> None:
    row = {"task_id": "t1", "kind": "hot_follow", "board_bucket": "ready"}
    assert derive_matrix_script_task_area_result_status(row) == {}


def test_task_area_returns_empty_for_digital_anchor() -> None:
    row = {"task_id": "t2", "kind": "digital_anchor", "board_bucket": "ready"}
    assert derive_matrix_script_task_area_result_status(row) == {}


def test_task_area_returns_empty_for_missing_kind() -> None:
    assert derive_matrix_script_task_area_result_status({"task_id": "t3"}) == {}


def test_task_area_returns_empty_for_non_mapping_row() -> None:
    # Defensive: non-Mapping inputs must not raise.
    assert derive_matrix_script_task_area_result_status(None) == {}  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Task Area helper — per-stage RC-R6 statements
# ---------------------------------------------------------------------------


def test_task_area_publishable_is_ready() -> None:
    row = _ms_row(bucket="publishable")
    out = derive_matrix_script_task_area_result_status(row)
    assert out["is_matrix_script"] is True
    assert out["status_kind"] == STATUS_READY
    assert out["stage"] == STAGE_PUBLISHABLE
    assert out["next_action_zh"]
    assert out["missing_items"] == []


def test_task_area_final_ready_is_ready_with_review_next_action() -> None:
    row = _ms_row(bucket="ready", compose_ready=True, final_exists=True)
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_READY
    assert out["stage"] == STAGE_FINAL_READY
    assert "校对" in out["next_action_zh"]


def test_task_area_awaiting_review_is_blocked_with_final_pending() -> None:
    row = _ms_row(bucket="blocked", head_reason="final_missing", compose_ready=True)
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_BLOCKED
    assert out["stage"] == STAGE_AWAITING_REVIEW
    assert "final_video_pending" in out["missing_items"]


def test_task_area_generating_is_blocked_with_compose_in_progress() -> None:
    row = _ms_row(
        bucket="blocked", head_reason="compose_not_ready", compose_status="running"
    )
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_BLOCKED
    assert out["stage"] == STAGE_GENERATING
    assert "compose_in_progress" in out["missing_items"]


def test_task_area_pending_config_is_blocked_with_empty_cells() -> None:
    row = _ms_row(bucket="ready", cells=[])
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_BLOCKED
    assert out["stage"] == STAGE_PENDING_CONFIG
    assert "variation_cells_empty" in out["missing_items"]


def test_task_area_created_is_blocked_with_two_missing_items() -> None:
    # Cells empty + head_reason explicitly None routes to STAGE_PENDING_CONFIG;
    # to hit STAGE_CREATED we need cells present + nothing else asserted.
    row = _ms_row(
        bucket="ready",
        cells=["cell_a"],
        compose_status=None,
        compose_ready=False,
        final_exists=False,
    )
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_BLOCKED
    assert out["stage"] == STAGE_CREATED
    assert "script_structure_pending" in out["missing_items"]
    assert "variation_cells_empty" in out["missing_items"]


def test_task_area_archived_is_completed() -> None:
    row = _ms_row(bucket="ready", archived=True)
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_kind"] == STATUS_COMPLETED
    assert out["stage"] == STAGE_ARCHIVED
    assert out["missing_items"] == []


def test_task_area_backfilled_is_completed() -> None:
    row = _ms_row(bucket="publishable")
    closure = create_closure(_packet())
    closure["variation_feedback"][0]["publish_status"] = "published"
    out = derive_matrix_script_task_area_result_status(row, closure=closure)
    assert out["status_kind"] == STATUS_COMPLETED
    assert out["stage"] == STAGE_BACKFILLED


def test_task_area_head_reason_is_surfaced_verbatim() -> None:
    row = _ms_row(bucket="blocked", head_reason="ready_gate_blocking")
    out = derive_matrix_script_task_area_result_status(row)
    assert out["head_reason"] == "ready_gate_blocking"
    assert out["head_reason_label_zh"] == "ready gate 阻塞"


def test_task_area_head_reason_label_em_dash_when_none() -> None:
    row = _ms_row(bucket="ready")
    out = derive_matrix_script_task_area_result_status(row)
    assert out["head_reason"] is None
    assert out["head_reason_label_zh"] == "—"


def test_task_area_status_label_matches_kind() -> None:
    row = _ms_row(bucket="publishable")
    out = derive_matrix_script_task_area_result_status(row)
    assert out["status_label_zh"] == STATUS_LABELS_ZH[out["status_kind"]]


def test_task_area_for_task_uses_read_only_closure() -> None:
    # Helper must NOT lazy-create a closure; with no closure created
    # for this task_id, we should still get a populated result.
    row = _ms_row(task_id="task_no_closure", bucket="ready", cells=[])
    out = derive_matrix_script_task_area_result_status_for_task(row)
    assert out["is_matrix_script"] is True
    assert out["stage"] == STAGE_PENDING_CONFIG


# ---------------------------------------------------------------------------
# Task Area helper — no vendor / model / provider / engine leakage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bucket,head_reason,compose_status,final_exists",
    [
        ("publishable", None, None, False),
        ("blocked", "compose_not_ready", "running", False),
        ("ready", None, None, False),
        ("blocked", "ready_gate_blocking", None, False),
    ],
)
def test_task_area_carries_no_vendor_or_model_strings(
    bucket: str,
    head_reason: str | None,
    compose_status: str | None,
    final_exists: bool,
) -> None:
    row = _ms_row(
        bucket=bucket,
        head_reason=head_reason,
        compose_status=compose_status,
        final_exists=final_exists,
    )
    out = derive_matrix_script_task_area_result_status(row)
    blob = repr(out).lower()
    for forbidden in ("vendor", "model_id", "provider", "engine", "swiftcraft"):
        assert forbidden not in blob


# ---------------------------------------------------------------------------
# Workbench helper — non-Matrix-Script isolation
# ---------------------------------------------------------------------------


def test_workbench_returns_empty_when_panel_is_hot_follow() -> None:
    pr = {"publishable": True, "head_reason": None}
    assert (
        derive_matrix_script_workbench_result_summary(pr, {"panel_kind": "hot_follow"})
        == {}
    )


def test_workbench_returns_empty_when_panel_is_digital_anchor() -> None:
    pr = {"publishable": False, "head_reason": "ready_gate_blocking"}
    assert (
        derive_matrix_script_workbench_result_summary(
            pr, {"panel_kind": "digital_anchor"}
        )
        == {}
    )


def test_workbench_returns_empty_when_panel_is_missing() -> None:
    assert derive_matrix_script_workbench_result_summary({"publishable": True}, None) == {}


# ---------------------------------------------------------------------------
# Workbench helper — head_reason mapping + status_kind
# ---------------------------------------------------------------------------


def _ms_panel() -> dict:
    return {"panel_kind": "matrix_script"}


def test_workbench_publishable_is_ready() -> None:
    pr = {
        "publishable": True,
        "head_reason": "publishable_ok",
        "consumed_inputs": {"blocking_count": 0},
        "blocking_advisories": [],
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["is_matrix_script"] is True
    assert out["status_kind"] == STATUS_READY
    assert out["publishable"] is True
    assert out["headline_zh"].startswith("可发布")
    assert out["next_action_zh"]


def test_workbench_blocked_with_head_reason_uses_label_in_headline() -> None:
    pr = {
        "publishable": False,
        "head_reason": "compose_not_ready",
        "consumed_inputs": {"blocking_count": 1},
        "blocking_advisories": [{"id": "a1"}],
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["status_kind"] == STATUS_BLOCKED
    assert "合成前置项未就绪" in out["headline_zh"]
    assert out["blocking_advisory_count"] == 1
    assert out["blocking_count"] == 1


def test_workbench_blocked_with_no_head_reason_falls_back_to_pending_config() -> None:
    pr = {
        "publishable": False,
        "head_reason": None,
        "consumed_inputs": {"blocking_count": 0},
        "blocking_advisories": [],
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["status_kind"] == STATUS_BLOCKED
    assert "variation_cells_empty" in out["missing_items"]


def test_workbench_unknown_head_reason_degrades_gracefully() -> None:
    pr = {
        "publishable": False,
        "head_reason": "future_unknown_reason",
        "consumed_inputs": {"blocking_count": 0},
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    # Unknown enum values fall through verbatim with a generic prompt.
    assert out["status_kind"] == STATUS_BLOCKED
    assert out["head_reason"] == "future_unknown_reason"
    assert out["head_reason_label_zh"] == "future_unknown_reason"
    assert "请联系架构师" in out["next_action_zh"]


@pytest.mark.parametrize("reason", list(WORKBENCH_HEAD_REASON_NEXT_ACTION_ZH.keys()))
def test_workbench_every_known_head_reason_has_an_actionable_sentence(reason: str) -> None:
    publishable = reason == "publishable_ok"
    pr = {
        "publishable": publishable,
        "head_reason": reason,
        "consumed_inputs": {"blocking_count": 0},
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["next_action_zh"]
    assert isinstance(out["next_action_zh"], str)


def test_workbench_blocking_count_defaults_to_zero_when_missing() -> None:
    pr = {"publishable": False, "head_reason": "ready_gate_blocking"}
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["blocking_count"] == 0
    assert out["blocking_advisory_count"] == 0


def test_workbench_no_fake_final_video_when_final_missing() -> None:
    pr = {
        "publishable": False,
        "head_reason": "final_missing",
        "consumed_inputs": {"blocking_count": 0},
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    blob = repr(out).lower()
    # Helper must never synthesise a URL or "preview" media reference.
    for forbidden in ("https://", "http://", "final_video_url", "preview_url", ".mp4"):
        assert forbidden not in blob


def test_workbench_carries_no_vendor_or_model_strings() -> None:
    pr = {
        "publishable": False,
        "head_reason": "publish_not_ready",
        "consumed_inputs": {"blocking_count": 0},
    }
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    blob = repr(out).lower()
    for forbidden in ("vendor", "model_id", "provider", "engine", "swiftcraft"):
        assert forbidden not in blob


def test_workbench_status_label_matches_kind() -> None:
    pr = {"publishable": True, "head_reason": "publishable_ok"}
    out = derive_matrix_script_workbench_result_summary(pr, _ms_panel())
    assert out["status_label_zh"] == STATUS_LABELS_ZH[out["status_kind"]]


def test_workbench_consumes_publish_readiness_verbatim() -> None:
    # Helper does not introduce a second producer — `publishable` and
    # `head_reason` must come from the supplied dict, never recomputed.
    pr_publishable = {"publishable": True, "head_reason": "publishable_ok"}
    pr_blocked = {"publishable": False, "head_reason": "ready_gate_blocking"}
    out_p = derive_matrix_script_workbench_result_summary(pr_publishable, _ms_panel())
    out_b = derive_matrix_script_workbench_result_summary(pr_blocked, _ms_panel())
    assert out_p["publishable"] is True
    assert out_b["publishable"] is False
    assert out_p["head_reason"] == "publishable_ok"
    assert out_b["head_reason"] == "ready_gate_blocking"
