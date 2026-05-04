"""PR-U1 — Matrix Script Task Area card summary projection tests.

Authority:
- ``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``
  (the signed UI-alignment gate spec; this PR-U1 implements the
  user-mandated PR slicing for Task Area comprehension).
- ``gateway/app/services/matrix_script/task_card_summary.py`` (helper under test).

These tests are import-light by design: they exercise only the pure
projection ``derive_matrix_script_task_card_summary`` over a hand-built
row dict that mirrors the shape produced by
``gateway/app/services/matrix_script/create_entry.py::build_matrix_script_task_payload``
plus the ``board_bucket`` / ``head_reason`` fields produced by
``gateway/app/services/task_router_presenters.py::build_tasks_page_rows``.

What is proved:

1. Operator-language tri-state badge renders for each ``board_bucket``.
2. Subject / variation count / current blocker fields render as expected.
3. ``publishable_variation_count_value`` is intentionally ``None`` (gated
   to a future Plan E phase that lands the unified publish_readiness
   producer per gate spec §4.7).
4. ``head_reason`` codes from ``derive_board_publishable`` translate to
   operator language for the closed enumerated set; unknown codes fall
   through verbatim.
5. Workbench / delivery action hrefs read from
   ``config.next_surfaces`` when present; fall back to the canonical
   ``/tasks/{task_id}`` and ``/tasks/{task_id}/publish`` shapes.
6. Non-Matrix-Script rows (Hot Follow / Digital Anchor) receive an empty
   summary — guaranteeing the Task Area card rendering for those rows
   stays bytewise unchanged via the template ``{% else %}`` branch.
7. The summary contains no provider / model / vendor / engine identifier
   (validator R3 alignment at the operator boundary).
"""
from __future__ import annotations

from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.task_card_summary import (
    PUBLISHABLE_COUNT_GATED_BY_D1,
    TRI_STATE_BADGE_LABELS,
    derive_matrix_script_task_card_summary,
)


def _matrix_script_row(
    *,
    task_id: str = "ms-001",
    title: str = "测试主题",
    bucket: str = "ready",
    head_reason: str | None = None,
    cells: list[dict[str, Any]] | None = None,
    next_surfaces: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cells = cells if cells is not None else []
    row: dict[str, Any] = {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "title": title,
        "board_bucket": bucket,
        "head_reason": head_reason,
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "delta": {"cells": cells},
            }
        ],
        "config": {
            "next_surfaces": dict(next_surfaces) if next_surfaces else {
                "workbench": f"/tasks/{task_id}",
                "delivery": f"/tasks/{task_id}/publish",
            },
        },
    }
    return row


# -- 1. Tri-state badge ---------------------------------------------------


@pytest.mark.parametrize(
    "bucket,expected_label",
    [
        ("blocked", "阻塞中"),
        ("ready", "就绪"),
        ("publishable", "可发布"),
    ],
)
def test_tri_state_badge_label_per_bucket(bucket: str, expected_label: str) -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket=bucket)
    )
    assert summary["tri_state_bucket"] == bucket
    assert summary["tri_state_badge_label"] == expected_label


def test_unknown_bucket_falls_back_to_ready() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket="unexpected_value")
    )
    assert summary["tri_state_bucket"] == "ready"
    assert summary["tri_state_badge_label"] == TRI_STATE_BADGE_LABELS["ready"]


# -- 2. Field labels + values ---------------------------------------------


def test_subject_field_renders_title() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(title="春节促销脚本")
    )
    assert summary["subject_label"] == "主题"
    assert summary["subject_value"] == "春节促销脚本"


def test_current_variation_count_reads_cells_length() -> None:
    cells = [{"axes": {"tone": "warm"}, "script_slot_ref": f"slot-{i}"} for i in range(7)]
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(cells=cells)
    )
    assert summary["current_variation_count_label"] == "当前变体数"
    assert summary["current_variation_count_value"] == 7


def test_current_variation_count_zero_when_no_cells() -> None:
    summary = derive_matrix_script_task_card_summary(_matrix_script_row(cells=[]))
    assert summary["current_variation_count_value"] == 0


def test_current_variation_count_reads_packet_refs_when_top_level_missing() -> None:
    row = _matrix_script_row(cells=[{"a": 1}, {"a": 2}])
    # Move refs into row["packet"] only — mimic an alternate persistence shape.
    refs = row.pop("line_specific_refs")
    row["packet"] = {"line_specific_refs": refs}
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["current_variation_count_value"] == 2


# -- 3. Publishable count gating -----------------------------------------


def test_publishable_variation_count_intentionally_none_for_d1_gating() -> None:
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    assert summary["publishable_variation_count_label"] == "可发布版本数"
    assert summary["publishable_variation_count_value"] is None
    assert summary["publishable_variation_count_gated_by"] == PUBLISHABLE_COUNT_GATED_BY_D1
    assert "publish_readiness" in summary["publishable_variation_count_tooltip"]


# -- 4. Blocker label translation ----------------------------------------


@pytest.mark.parametrize(
    "head_reason,expected_label",
    [
        ("publish_ready_pending", "等待生成"),
        ("compose_ready_pending", "合成未就绪"),
        ("delivery_required_unresolved", "必交付物缺失"),
        ("scene_pack_blocking_disallowed", "配套素材阻塞被禁止"),
        ("final_fresh", "终片需重新生成"),
        ("subtitles_pending", "字幕未就绪"),
        ("dub_pending", "配音未就绪"),
    ],
)
def test_known_blocker_codes_translate_to_operator_language(
    head_reason: str, expected_label: str
) -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket="blocked", head_reason=head_reason)
    )
    assert summary["current_blocker_label"] == "当前阻塞项"
    assert summary["current_blocker_value"] == expected_label


def test_unknown_blocker_code_falls_through_verbatim() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket="blocked", head_reason="some_future_unknown_code")
    )
    assert summary["current_blocker_value"] == "some_future_unknown_code"


def test_no_blocker_when_head_reason_empty_or_missing() -> None:
    summary_a = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket="ready", head_reason=None)
    )
    summary_b = derive_matrix_script_task_card_summary(
        _matrix_script_row(bucket="ready", head_reason="")
    )
    assert summary_a["current_blocker_value"] is None
    assert summary_b["current_blocker_value"] is None


# -- 5. Action hrefs -----------------------------------------------------


def test_action_hrefs_read_from_next_surfaces_when_present() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(
            task_id="ms-007",
            next_surfaces={
                "workbench": "/tasks/ms-007",
                "delivery": "/tasks/ms-007/publish",
            },
        )
    )
    assert summary["workbench_action_label"] == "进入工作台"
    assert summary["workbench_action_href"] == "/tasks/ms-007"
    assert summary["delivery_action_label"] == "跳交付中心"
    assert summary["delivery_action_href"] == "/tasks/ms-007/publish"


def test_action_hrefs_fall_back_to_canonical_paths_when_surfaces_missing() -> None:
    row = _matrix_script_row(task_id="ms-fallback")
    # Drop next_surfaces entirely.
    row["config"] = {}
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["workbench_action_href"] == "/tasks/ms-fallback"
    assert summary["delivery_action_href"] == "/tasks/ms-fallback/publish"


def test_action_hrefs_empty_when_task_id_missing_and_no_surfaces() -> None:
    row = _matrix_script_row(task_id="")
    row["task_id"] = ""
    row["id"] = ""
    row["config"] = {}
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["workbench_action_href"] == ""
    assert summary["delivery_action_href"] == ""


# -- 6. Non-Matrix-Script rows receive empty summary ---------------------


@pytest.mark.parametrize(
    "kind",
    ["hot_follow", "digital_anchor", "baseline", "apollo_avatar", "", None],
)
def test_non_matrix_script_rows_get_empty_summary(kind: str | None) -> None:
    row = _matrix_script_row()
    row["kind"] = kind
    row["category_key"] = kind
    row["platform"] = kind
    summary = derive_matrix_script_task_card_summary(row)
    assert summary == {}


def test_matrix_script_alias_kind_recognized() -> None:
    row = _matrix_script_row()
    row["kind"] = "matrix-script"  # alias accepted per templates/normalization
    row["category_key"] = "matrix-script"
    summary = derive_matrix_script_task_card_summary(row)
    assert summary.get("is_matrix_script") is True


# -- 7. Validator R3 alignment ------------------------------------------


def test_summary_carries_no_vendor_model_provider_engine_keys() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(
            cells=[{"axes": {"tone": "warm"}, "script_slot_ref": "slot-1"}],
            head_reason="delivery_required_unresolved",
        )
    )
    forbidden = {"vendor_id", "model_id", "provider", "provider_id", "engine_id", "raw_provider_route"}
    assert not (set(summary.keys()) & forbidden)


# -- 8. Stability: helper does not mutate the input row ------------------


def test_helper_does_not_mutate_input_row() -> None:
    row = _matrix_script_row(
        cells=[{"axes": {"tone": "warm"}, "script_slot_ref": "slot-1"}]
    )
    snapshot = repr(row)
    derive_matrix_script_task_card_summary(row)
    assert repr(row) == snapshot
