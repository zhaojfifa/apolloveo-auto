"""Tests for OWC-MS PR-1 — Matrix Script Task Area Workflow Convergence.

Covers MS-W1 (three-tier projection) + MS-W2 (eight-stage state +
8-field card) per ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 and the
binding line-specific authority at
``docs/product/matrix_script_product_flow_v1.md`` §§5.1–5.3.

Test floor per gate spec §5.2: ≥25 cases.
"""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.closure_binding import reset_for_tests
from gateway.app.services.matrix_script.publish_feedback_closure import create_closure
from gateway.app.services.matrix_script.task_area_convergence import (
    BEST_VERSION_TOOLTIP,
    EIGHT_STAGES,
    EIGHT_STAGE_LABELS,
    LANE_LABELS,
    LANE_PUBLISH,
    LANE_SCRIPT,
    LANE_VARIATION,
    STAGE_ARCHIVED,
    STAGE_AWAITING_REVIEW,
    STAGE_BACKFILLED,
    STAGE_CREATED,
    STAGE_FINAL_READY,
    STAGE_GENERATING,
    STAGE_PENDING_CONFIG,
    STAGE_PUBLISHABLE,
    derive_matrix_script_eight_stage_state,
    derive_matrix_script_full_card_summary,
    derive_matrix_script_three_tier_lanes,
)


@pytest.fixture(autouse=True)
def _isolate_closure_store() -> None:
    """Each test starts with a clean closure store."""
    reset_for_tests()


def _packet(*, cell_ids: list[str] | None = None) -> dict:
    """Minimal Matrix Script packet sufficient for closure creation."""
    cells = [
        {"cell_id": cid, "axis_tuple": {"tone": "neutral", "audience": "general", "length": "short"}}
        for cid in (cell_ids or ["cell_a", "cell_b"])
    ]
    return {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "delta": {"cells": cells},
            },
            {
                "ref_id": "matrix_script_task_entry",
                "delta": {"source_script_ref": "content://matrix-script/source/abc123"},
            },
        ],
    }


def _matrix_script_row(
    *,
    task_id: str = "task_owc_ms_001",
    title: str = "Spring matrix script demo",
    bucket: str = "ready",
    head_reason: str | None = None,
    cells: list[str] | None = None,
    source_script_ref: str | None = "content://matrix-script/source/abc123",
    compose_status: str | None = None,
    final_exists: bool = False,
    compose_ready: bool = False,
    archived: bool = False,
    updated_at: str | None = "2026-05-04T15:00:00Z",
) -> dict:
    cells = cells if cells is not None else ["cell_a", "cell_b"]
    refs: list[dict] = [
        {
            "ref_id": "matrix_script_variation_matrix",
            "delta": {
                "cells": [
                    {"cell_id": cid, "axis_tuple": {"tone": "neutral"}} for cid in cells
                ]
            },
        }
    ]
    if source_script_ref is not None:
        refs.append(
            {
                "ref_id": "matrix_script_task_entry",
                "delta": {"source_script_ref": source_script_ref},
            }
        )
    row: dict = {
        "task_id": task_id,
        "kind": "matrix_script",
        "title": title,
        "board_bucket": bucket,
        "head_reason": head_reason,
        "line_specific_refs": refs,
        "config": {"next_surfaces": {"workbench": f"/tasks/{task_id}", "delivery": f"/tasks/{task_id}/publish"}},
        "ready_gate": {"compose_ready": compose_ready, "publish_ready": False},
        "compose_status": compose_status,
        "final": {"exists": final_exists},
        "archived": archived,
        "updated_at": updated_at,
    }
    return row


# ---------------------------------------------------------------------------
# Eight-stage state projection (MS-W2)
# ---------------------------------------------------------------------------


def test_eight_stages_constant_matches_product_flow_authority() -> None:
    assert EIGHT_STAGES == (
        STAGE_CREATED,
        STAGE_PENDING_CONFIG,
        STAGE_GENERATING,
        STAGE_AWAITING_REVIEW,
        STAGE_FINAL_READY,
        STAGE_PUBLISHABLE,
        STAGE_BACKFILLED,
        STAGE_ARCHIVED,
    )
    assert EIGHT_STAGE_LABELS[STAGE_CREATED] == "已创建"
    assert EIGHT_STAGE_LABELS[STAGE_PENDING_CONFIG] == "待配置"
    assert EIGHT_STAGE_LABELS[STAGE_GENERATING] == "生成中"
    assert EIGHT_STAGE_LABELS[STAGE_AWAITING_REVIEW] == "待校对"
    assert EIGHT_STAGE_LABELS[STAGE_FINAL_READY] == "成片完成"
    assert EIGHT_STAGE_LABELS[STAGE_PUBLISHABLE] == "可发布"
    assert EIGHT_STAGE_LABELS[STAGE_BACKFILLED] == "已回填"
    assert EIGHT_STAGE_LABELS[STAGE_ARCHIVED] == "已归档"


def test_stage_pending_config_when_no_variation_cells() -> None:
    row = _matrix_script_row(cells=[])
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_PENDING_CONFIG
    assert state["stage_label"] == "待配置"


def test_stage_created_when_cells_exist_but_nothing_else_progressed() -> None:
    row = _matrix_script_row()
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_CREATED
    assert state["stage_label"] == "已创建"


def test_stage_generating_when_compose_status_running() -> None:
    row = _matrix_script_row(compose_status="running")
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_GENERATING
    assert state["stage_label"] == "生成中"


def test_stage_awaiting_review_when_compose_ready_but_no_final() -> None:
    row = _matrix_script_row(compose_ready=True, final_exists=False)
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_AWAITING_REVIEW


def test_stage_final_ready_when_final_exists_but_not_publishable() -> None:
    row = _matrix_script_row(final_exists=True, bucket="ready")
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_FINAL_READY


def test_stage_publishable_when_board_bucket_publishable() -> None:
    row = _matrix_script_row(final_exists=True, bucket="publishable")
    state = derive_matrix_script_eight_stage_state(row)
    assert state["stage"] == STAGE_PUBLISHABLE


def test_stage_backfilled_when_closure_has_published_variation() -> None:
    row = _matrix_script_row()
    closure = create_closure(_packet())
    closure["variation_feedback"][0]["publish_status"] = "published"
    state = derive_matrix_script_eight_stage_state(row, closure=closure)
    assert state["stage"] == STAGE_BACKFILLED
    assert state["stage_label"] == "已回填"


def test_stage_archived_takes_precedence_over_other_signals() -> None:
    row = _matrix_script_row(final_exists=True, bucket="publishable", archived=True)
    closure = create_closure(_packet())
    closure["variation_feedback"][0]["publish_status"] = "published"
    state = derive_matrix_script_eight_stage_state(row, closure=closure)
    assert state["stage"] == STAGE_ARCHIVED


def test_stage_index_is_position_in_eight_stages_tuple() -> None:
    state = derive_matrix_script_eight_stage_state(_matrix_script_row(cells=[]))
    assert state["stage_index"] == EIGHT_STAGES.index(STAGE_PENDING_CONFIG)


def test_eight_stage_returns_empty_for_non_matrix_script() -> None:
    row = {"task_id": "x", "kind": "hot_follow"}
    assert derive_matrix_script_eight_stage_state(row) == {}


# ---------------------------------------------------------------------------
# Three-tier lanes projection (MS-W1)
# ---------------------------------------------------------------------------


def test_three_tier_lanes_returns_all_three_lanes_in_order() -> None:
    row = _matrix_script_row()
    out = derive_matrix_script_three_tier_lanes(row)
    keys = [lane["key"] for lane in out["lanes"]]
    assert keys == [LANE_SCRIPT, LANE_VARIATION, LANE_PUBLISH]
    labels = [lane["label"] for lane in out["lanes"]]
    assert labels == [LANE_LABELS[LANE_SCRIPT], LANE_LABELS[LANE_VARIATION], LANE_LABELS[LANE_PUBLISH]]


def test_script_lane_carries_subject_and_source_script_ref() -> None:
    row = _matrix_script_row(title="Demo subject")
    out = derive_matrix_script_three_tier_lanes(row)
    script_lane = out["lanes"][0]
    assert script_lane["rows"][0]["subject"] == "Demo subject"
    assert script_lane["rows"][0]["source_script_ref"] == "content://matrix-script/source/abc123"
    assert script_lane["rows"][0]["task_id"] == "task_owc_ms_001"


def test_variation_lane_renders_one_row_per_cell_with_pending_default() -> None:
    row = _matrix_script_row(cells=["cell_a", "cell_b", "cell_c"])
    out = derive_matrix_script_three_tier_lanes(row)
    variation_lane = out["lanes"][1]
    assert [r["variation_id"] for r in variation_lane["rows"]] == ["cell_a", "cell_b", "cell_c"]
    assert all(r["publish_status"] == "pending" for r in variation_lane["rows"])


def test_variation_lane_joins_closure_publish_status_when_present() -> None:
    row = _matrix_script_row(cells=["cell_a", "cell_b"])
    closure = create_closure(_packet(cell_ids=["cell_a", "cell_b"]))
    closure["variation_feedback"][0]["publish_status"] = "published"
    closure["variation_feedback"][1]["publish_status"] = "failed"
    out = derive_matrix_script_three_tier_lanes(row, closure=closure)
    statuses = [r["publish_status"] for r in out["lanes"][1]["rows"]]
    assert statuses == ["published", "failed"]


def test_publish_lane_is_empty_without_channel_metrics() -> None:
    row = _matrix_script_row()
    out = derive_matrix_script_three_tier_lanes(row)
    assert out["lanes"][2]["rows"] == []


def test_publish_lane_flattens_channel_metrics_per_variation_per_channel() -> None:
    row = _matrix_script_row(cells=["cell_a", "cell_b"])
    closure = create_closure(_packet(cell_ids=["cell_a", "cell_b"]))
    closure["variation_feedback"][0]["publish_status"] = "published"
    closure["variation_feedback"][0]["publish_url"] = "https://example.com/a"
    closure["variation_feedback"][0]["channel_metrics"] = [
        {"platform": "tiktok", "account_id": "ig_a", "published_at": "2026-05-04T10:00:00Z"},
        {"platform": "youtube", "account_id": "yt_a", "published_at": "2026-05-04T10:05:00Z"},
    ]
    closure["variation_feedback"][1]["publish_status"] = "published"
    closure["variation_feedback"][1]["channel_metrics"] = [
        {"platform": "tiktok", "account_id": "ig_b", "published_at": "2026-05-04T11:00:00Z"},
    ]
    out = derive_matrix_script_three_tier_lanes(row, closure=closure)
    publish_lane = out["lanes"][2]
    assert len(publish_lane["rows"]) == 3
    platforms = sorted(r["platform"] for r in publish_lane["rows"])
    assert platforms == ["tiktok", "tiktok", "youtube"]


def test_three_tier_lanes_returns_empty_for_non_matrix_script() -> None:
    row = {"task_id": "x", "kind": "digital_anchor"}
    assert derive_matrix_script_three_tier_lanes(row) == {}


# ---------------------------------------------------------------------------
# Full card summary (MS-W1 + MS-W2 superset of PR-U1)
# ---------------------------------------------------------------------------


def test_full_summary_preserves_pr_u1_keys() -> None:
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row)
    for key in (
        "is_matrix_script",
        "subject_label",
        "subject_value",
        "current_variation_count_label",
        "current_variation_count_value",
        "publishable_variation_count_label",
        "publishable_variation_count_value",
        "current_blocker_label",
        "current_blocker_value",
        "tri_state_bucket",
        "tri_state_badge_label",
        "workbench_action_label",
        "workbench_action_href",
        "delivery_action_label",
        "delivery_action_href",
    ):
        assert key in summary, f"missing PR-U1 key: {key}"


def test_full_summary_rebinds_publishable_variation_count_to_closure_published_count() -> None:
    row = _matrix_script_row()
    closure = create_closure(_packet())
    # zero published rows
    out_zero = derive_matrix_script_full_card_summary(row, closure=closure)
    assert out_zero["publishable_variation_count_value"] == 0
    assert out_zero["publishable_variation_count_gated_by"] is None
    # one published row
    closure["variation_feedback"][0]["publish_status"] = "published"
    out_one = derive_matrix_script_full_card_summary(row, closure=closure)
    assert out_one["publishable_variation_count_value"] == 1


def test_full_summary_publishable_count_zero_when_no_closure() -> None:
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row, closure=None)
    assert summary["publishable_variation_count_value"] == 0


def test_full_summary_core_script_name_reads_source_script_ref() -> None:
    row = _matrix_script_row(source_script_ref="content://matrix-script/source/xyz789")
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["core_script_name_label"] == "核心脚本名称"
    assert summary["core_script_name_value"] == "content://matrix-script/source/xyz789"


def test_full_summary_core_script_name_none_when_ref_missing() -> None:
    row = _matrix_script_row(source_script_ref=None)
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["core_script_name_value"] is None


def test_full_summary_published_channel_count_dedupes_across_variations() -> None:
    row = _matrix_script_row(cells=["cell_a", "cell_b"])
    closure = create_closure(_packet(cell_ids=["cell_a", "cell_b"]))
    closure["variation_feedback"][0]["channel_metrics"] = [
        {"platform": "tiktok", "account_id": "x"},
        {"platform": "youtube", "account_id": "y"},
    ]
    closure["variation_feedback"][1]["channel_metrics"] = [
        {"platform": "tiktok", "account_id": "z"},  # tiktok again - dedup
        {"platform": "weibo", "account_id": "w"},
    ]
    summary = derive_matrix_script_full_card_summary(row, closure=closure)
    assert summary["published_channel_count_label"] == "已发布账号数"
    assert summary["published_channel_count_value"] == 3  # tiktok, youtube, weibo


def test_full_summary_best_version_intentionally_none_for_pr1() -> None:
    """OWC-MS PR-1 does not expose a best-version selector — that is
    OWC-MS PR-2 workbench D 校对区. Field stays None / "—" with the
    explicit operator-language tooltip naming the gating."""
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["best_version_label"] == "当前最佳版本"
    assert summary["best_version_value"] is None
    assert summary["best_version_tooltip"] == BEST_VERSION_TOOLTIP


def test_full_summary_last_generated_at_prefers_updated_at() -> None:
    row = _matrix_script_row(updated_at="2026-05-04T20:00:00Z")
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["last_generated_at_label"] == "最近一次生成时间"
    assert summary["last_generated_at_value"] == "2026-05-04T20:00:00Z"


def test_full_summary_last_generated_at_falls_back_to_created_at() -> None:
    row = _matrix_script_row(updated_at=None)
    row["created_at"] = "2026-05-03T08:00:00Z"
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["last_generated_at_value"] == "2026-05-03T08:00:00Z"


def test_full_summary_attaches_eight_stage_projection() -> None:
    row = _matrix_script_row(compose_status="running")
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["eight_stage"]["stage"] == STAGE_GENERATING
    assert summary["eight_stage"]["stage_label"] == "生成中"


def test_full_summary_attaches_three_tier_lanes_view() -> None:
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row)
    assert summary["lanes_view"]["is_matrix_script"] is True
    assert {lane["key"] for lane in summary["lanes_view"]["lanes"]} == {
        LANE_SCRIPT,
        LANE_VARIATION,
        LANE_PUBLISH,
    }


def test_full_summary_returns_empty_for_hot_follow_row() -> None:
    row = {"task_id": "x", "kind": "hot_follow", "title": "y"}
    assert derive_matrix_script_full_card_summary(row) == {}


def test_full_summary_returns_empty_for_digital_anchor_row() -> None:
    row = {"task_id": "x", "kind": "digital_anchor", "title": "y"}
    assert derive_matrix_script_full_card_summary(row) == {}


# ---------------------------------------------------------------------------
# Discipline / boundary tests
# ---------------------------------------------------------------------------


def test_full_summary_does_not_mutate_closure() -> None:
    row = _matrix_script_row()
    closure = create_closure(_packet())
    snapshot_before = {
        "variation_feedback": [dict(r) for r in closure["variation_feedback"]],
        "feedback_closure_records": list(closure["feedback_closure_records"]),
    }
    derive_matrix_script_full_card_summary(row, closure=closure)
    assert closure["variation_feedback"] == snapshot_before["variation_feedback"]
    assert closure["feedback_closure_records"] == snapshot_before["feedback_closure_records"]


def test_full_summary_does_not_mutate_input_row() -> None:
    row = _matrix_script_row()
    snapshot = dict(row)
    derive_matrix_script_full_card_summary(row)
    # Input row keys preserved bytewise (no helper-side mutation).
    for key, value in snapshot.items():
        assert row[key] == value


def test_full_summary_carries_no_provider_or_vendor_identifier() -> None:
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row)
    flat = repr(summary).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in flat, f"forbidden identifier {forbidden!r} leaked into summary"


def test_full_summary_lane_count_matches_underlying_lanes_view() -> None:
    row = _matrix_script_row()
    summary = derive_matrix_script_full_card_summary(row)
    lanes = summary["lanes_view"]["lanes"]
    # script lane always one row; variation lane = number of cells; publish lane = 0 with no closure.
    assert len(lanes[0]["rows"]) == 1
    assert len(lanes[1]["rows"]) == 2
    assert len(lanes[2]["rows"]) == 0


def test_full_summary_no_card_collapses_into_baseline_when_kind_missing() -> None:
    row = {"task_id": "x", "title": "no kind"}
    assert derive_matrix_script_full_card_summary(row) == {}


def test_eight_stage_state_resolves_publishable_under_published_closure() -> None:
    """Backfilled stage > publishable: a task that has at least one
    published variation is in 已回填 even if board_bucket is publishable.
    """
    row = _matrix_script_row(final_exists=True, bucket="publishable")
    closure = create_closure(_packet())
    closure["variation_feedback"][0]["publish_status"] = "published"
    state = derive_matrix_script_eight_stage_state(row, closure=closure)
    assert state["stage"] == STAGE_BACKFILLED
