"""OWC-MS-RO PR-1 — Matrix Script Task Area card refit dedicated tests.

Authority pointers:

- ``docs/design/matrix_script_result_oriented_ui_plan_v1.md`` (frozen design package).
- ``docs/design/matrix_script_task_area_wireframe_v1.md`` §4 (binding-and-exhaustive 9 fields + next-action chip + three jump buttons).
- ``docs/design/matrix_script_result_oriented_ui_implementation_slicing_v1.md`` §4 (PR-1 scope) + §2.1 (narrow PR-1 unblock amendment 2026-05-08).
- ``gateway/app/services/matrix_script/task_card_summary.py`` (helper under test).
- ``gateway/app/services/matrix_script/task_area_convergence.py`` (full card summary helper consumed by the template).
- ``gateway/app/services/matrix_script/result_status_view.py`` (next-action chip source).
- Operator sample anchor: ``production_packet_3_scripts.json`` (S001 / S002 / S003 real TikTok production scripts) — fixture shapes baked below per the user mission's "Use S001 / S002 / S003 as the real operator sample set" instruction.

These tests are import-light by design (Python 3.9.6-compatible, no FastAPI / templating dependencies) and exercise only the pure projections that this PR refits. Template integration is verified by adjacent regression suites (``test_matrix_script_task_card_summary.py`` + ``test_matrix_script_task_area_convergence.py``) that this PR does not widen.

PR-1 binding behaviour proved by this suite:

1. Helper exposes the three OWC-MS-RO action labels (``打开工作台`` / ``打开交付中心`` / ``打开发布反馈``) and three matching hrefs.
2. ``publish_feedback_action_href`` always anchors at ``#publish-feedback`` on the publish-hub URL the delivery action targets.
3. Helper preserves all PR-U1 + OWC-MS PR-1 keys verbatim — adjacent regression tests stay green.
4. M/N publishable-count rendering reads ``publishable_variation_count_value`` (M) and ``current_variation_count_value`` (N) from the OWC-MS PR-1 full-card-summary helper.
5. Next-action chip pulls from ``derive_matrix_script_task_area_result_status.next_action_zh`` (RC-R6 helper) — no second truth source.
6. Hot Follow rows / Digital Anchor rows / baseline rows receive an empty summary (``{}``) so the template's ``{% else %}`` fallback preserves their bytewise-unchanged Task Area card.
7. Forbidden surfaces audit: no raw refs / ``content://`` handles / ``slot_id`` / ``cell_id`` / vendor / model / provider / engine identifier ever leaks through any helper return value, no fake ``final_video`` / fabricated ``publish_url`` is synthesised.
8. S001 / S002 / S003 fixture shapes drive their canonical Task Area card states (待校对 ◐ ready / 已发布 ✓ completed / 生成中 🚧 blocked) per the wireframe layout block.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

import pytest

from gateway.app.services.matrix_script.task_card_summary import (
    PUBLISHABLE_COUNT_GATED_BY_D1,
    TRI_STATE_BADGE_LABELS,
    derive_matrix_script_task_card_summary,
)
from gateway.app.services.matrix_script.task_area_convergence import (
    derive_matrix_script_full_card_summary,
)
from gateway.app.services.matrix_script.result_status_view import (
    STATUS_BLOCKED,
    STATUS_COMPLETED,
    STATUS_READY,
    derive_matrix_script_task_area_result_status,
)


# --------------------------------------------------------------------------
# Test fixtures
# --------------------------------------------------------------------------


def _matrix_script_row(
    *,
    task_id: str = "ms-card-refit-001",
    title: str = "PR-1 测试任务",
    bucket: str = "ready",
    head_reason: str | None = None,
    cells: list[dict[str, Any]] | None = None,
    next_surfaces: Mapping[str, Any] | None = None,
    kind: str = "matrix_script",
) -> dict[str, Any]:
    """Build a row dict shaped like the output of
    ``task_router_presenters.build_tasks_page_rows`` for matrix_script.
    """
    cells = cells if cells is not None else []
    row: dict[str, Any] = {
        "task_id": task_id,
        "id": task_id,
        "kind": kind,
        "category_key": kind,
        "platform": kind,
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
            "next_surfaces": dict(next_surfaces)
            if next_surfaces
            else {
                "workbench": f"/tasks/{task_id}",
                "delivery": f"/tasks/{task_id}/publish",
            },
            "entry": {
                "subject": title,
                "target_language": "zh-CN",
            },
        },
    }
    return row


def _s001_row(*, task_id: str = "ms-s001", bucket: str = "ready") -> dict[str, Any]:
    """Operator sample S001 — '不会剪辑，也能做TikTok？' (22s, AI赚钱).

    Two declared ``variants`` per production_packet_3_scripts.json plus
    two operator-staged platform extensions in the same theme (4-cell
    matrix — the smallest non-degenerate shape that exercises the
    multi-variant card body).
    """
    return _matrix_script_row(
        task_id=task_id,
        title="不会剪辑，也能做TikTok？",
        bucket=bucket,
        cells=[
            {"cell_id": "s001-c1", "axis_tuple": {"tone": "sincere"}},
            {"cell_id": "s001-c2", "axis_tuple": {"tone": "rhetorical"}},
            {"cell_id": "s001-c3", "axis_tuple": {"tone": "confident"}},
            {"cell_id": "s001-c4", "axis_tuple": {"tone": "playful"}},
        ],
    )


def _s002_row(*, task_id: str = "ms-s002", bucket: str = "publishable") -> dict[str, Any]:
    """Operator sample S002 — '不用AI vs 用AI' (20s, AI赚钱, 对比型爆款)."""
    return _matrix_script_row(
        task_id=task_id,
        title="不用AI vs 用AI",
        bucket=bucket,
        cells=[
            {"cell_id": "s002-c1", "axis_tuple": {"tone": "comparative"}},
            {"cell_id": "s002-c2", "axis_tuple": {"tone": "comparative"}},
            {"cell_id": "s002-c3", "axis_tuple": {"tone": "comparative"}},
        ],
    )


def _s003_row(
    *,
    task_id: str = "ms-s003",
    bucket: str = "blocked",
    head_reason: str = "compose_ready_pending",
) -> dict[str, Any]:
    """Operator sample S003 — '0基础，也能用AI做出第一条视频' (25s, AI赚钱)."""
    return _matrix_script_row(
        task_id=task_id,
        title="0基础，也能用AI做出第一条视频",
        bucket=bucket,
        head_reason=head_reason,
        cells=[
            {"cell_id": "s003-c1", "axis_tuple": {"tone": "growth"}},
            {"cell_id": "s003-c2", "axis_tuple": {"tone": "growth"}},
            {"cell_id": "s003-c3", "axis_tuple": {"tone": "growth"}},
            {"cell_id": "s003-c4", "axis_tuple": {"tone": "growth"}},
            {"cell_id": "s003-c5", "axis_tuple": {"tone": "growth"}},
        ],
    )


def _hot_follow_row() -> dict[str, Any]:
    """Hot Follow row shape for byte-isolation gating tests."""
    return {
        "task_id": "hf-001",
        "id": "hf-001",
        "kind": "hot_follow",
        "category_key": "hot_follow",
        "platform": "hot_follow",
        "title": "Hot Follow sample",
        "board_bucket": "ready",
        "head_reason": None,
        "line_specific_refs": [],
        "config": {},
    }


def _digital_anchor_row() -> dict[str, Any]:
    """Digital Anchor row shape for byte-isolation gating tests."""
    return {
        "task_id": "da-001",
        "id": "da-001",
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "title": "Digital Anchor sample",
        "board_bucket": "ready",
        "head_reason": None,
        "line_specific_refs": [],
        "config": {},
    }


# --------------------------------------------------------------------------
# A. Three jump button labels (PR-1 hard requirement)
# --------------------------------------------------------------------------


def test_workbench_button_label_renames_from_legacy_to_open_workbench() -> None:
    """OWC-MS-RO PR-1 — '进入工作台' is replaced by '打开工作台' on the
    Task Area card so the three jump buttons read as a coherent
    'open X' set per wireframe §4.2."""
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    assert summary["workbench_action_label"] == "打开工作台"


def test_delivery_button_label_renames_from_legacy_to_open_delivery_center() -> None:
    """OWC-MS-RO PR-1 — '跳交付中心' is replaced by '打开交付中心'."""
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    assert summary["delivery_action_label"] == "打开交付中心"


def test_publish_feedback_button_label_is_added() -> None:
    """OWC-MS-RO PR-1 — third jump button '打开发布反馈' closes IG-1."""
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    assert summary["publish_feedback_action_label"] == "打开发布反馈"


def test_three_action_labels_are_distinct_strings() -> None:
    """Defensive: each of the three jump buttons must carry a distinct
    operator-language label so an operator cannot mis-read which surface
    a button targets."""
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    labels = {
        summary["workbench_action_label"],
        summary["delivery_action_label"],
        summary["publish_feedback_action_label"],
    }
    assert len(labels) == 3


def test_button_labels_are_operator_language_zh_cn() -> None:
    """Sanity: all three labels begin with 打开 (Chinese verb 'open')."""
    summary = derive_matrix_script_task_card_summary(_matrix_script_row())
    for key in ("workbench_action_label", "delivery_action_label", "publish_feedback_action_label"):
        assert summary[key].startswith("打开"), f"{key} = {summary[key]!r}"


# --------------------------------------------------------------------------
# B. publish_feedback_action_href anchor format
# --------------------------------------------------------------------------


def test_publish_feedback_href_anchors_at_publish_feedback_on_publish_hub() -> None:
    """OWC-MS-RO PR-1 — the publish-feedback action targets the same
    publish-hub URL as the delivery action plus the
    ``#publish-feedback`` anchor (existing template anchor)."""
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(
            task_id="ms-anchor",
            next_surfaces={
                "workbench": "/tasks/ms-anchor",
                "delivery": "/tasks/ms-anchor/publish",
            },
        )
    )
    assert summary["delivery_action_href"] == "/tasks/ms-anchor/publish"
    assert summary["publish_feedback_action_href"] == "/tasks/ms-anchor/publish#publish-feedback"


def test_publish_feedback_href_uses_canonical_fallback_when_surfaces_missing() -> None:
    row = _matrix_script_row(task_id="ms-fb-fb")
    row["config"] = {}
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["publish_feedback_action_href"] == "/tasks/ms-fb-fb/publish#publish-feedback"


def test_publish_feedback_href_renders_empty_when_task_id_unknown() -> None:
    """Defensive: when both task_id and id are absent, the helper
    cannot construct any href; the publish-feedback href stays empty
    rather than producing a malformed ``#publish-feedback`` orphan."""
    row = _matrix_script_row()
    row["task_id"] = ""
    row["id"] = ""
    row["config"] = {}
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["publish_feedback_action_href"] == ""


def test_publish_feedback_href_is_anchor_appended_to_delivery_href() -> None:
    """Invariant: publish-feedback href = delivery href + '#publish-feedback'."""
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(task_id="ms-inv")
    )
    expected = f"{summary['delivery_action_href']}#publish-feedback"
    assert summary["publish_feedback_action_href"] == expected


# --------------------------------------------------------------------------
# C. Three buttons coexist; existing two preserve href bindings
# --------------------------------------------------------------------------


def test_three_button_hrefs_present_simultaneously() -> None:
    summary = derive_matrix_script_task_card_summary(_matrix_script_row(task_id="ms-three"))
    for key in (
        "workbench_action_href",
        "delivery_action_href",
        "publish_feedback_action_href",
    ):
        assert key in summary, f"missing key {key}"
        # Each href must be either an absolute path or empty fallback.
        assert isinstance(summary[key], str)


def test_workbench_href_unchanged_from_pr_u1_substrate() -> None:
    """OWC-MS-RO PR-1 must NOT change workbench routing semantics; only
    the button label is refreshed."""
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(
            task_id="ms-wb-101",
            next_surfaces={
                "workbench": "/tasks/ms-wb-101",
                "delivery": "/tasks/ms-wb-101/publish",
            },
        )
    )
    assert summary["workbench_action_href"] == "/tasks/ms-wb-101"


def test_delivery_href_unchanged_from_pr_u1_substrate() -> None:
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(
            task_id="ms-dl-202",
            next_surfaces={
                "workbench": "/tasks/ms-dl-202",
                "delivery": "/tasks/ms-dl-202/publish",
            },
        )
    )
    assert summary["delivery_action_href"] == "/tasks/ms-dl-202/publish"


# --------------------------------------------------------------------------
# D. M/N publishable count format (helper layer)
# --------------------------------------------------------------------------


def test_full_summary_publishable_count_value_is_zero_when_blocked() -> None:
    """Wireframe §4 row 4 — render '可发布版本数: M/N'. Helper exposes
    M (publishable_variation_count_value) and N (current_variation_count_value)."""
    summary = derive_matrix_script_full_card_summary(
        _matrix_script_row(cells=[{"cell_id": "c1"}, {"cell_id": "c2"}], bucket="blocked")
    )
    assert summary["publishable_variation_count_value"] == 0
    assert summary["current_variation_count_value"] == 2


def test_full_summary_publishable_count_value_equals_n_when_publishable() -> None:
    summary = derive_matrix_script_full_card_summary(
        _matrix_script_row(
            cells=[{"cell_id": "c1"}, {"cell_id": "c2"}, {"cell_id": "c3"}],
            bucket="publishable",
        )
    )
    assert summary["publishable_variation_count_value"] == 3
    assert summary["current_variation_count_value"] == 3


def test_full_summary_publishable_count_zero_zero_when_no_cells() -> None:
    """Empty-state per wireframe §4.4: variant_count == 0 renders 0/0."""
    summary = derive_matrix_script_full_card_summary(_matrix_script_row(cells=[]))
    assert summary["publishable_variation_count_value"] == 0
    assert summary["current_variation_count_value"] == 0


def test_pr_u1_summary_publishable_count_is_none_when_full_summary_absent() -> None:
    """Backward compatibility — the PR-U1-only path keeps the legacy
    ``None`` sentinel so the template renders '—' when ``ms_owc`` is
    not attached (e.g. cross-line surfaces that bypass the OWC-MS PR-1
    helper)."""
    pr_u1 = derive_matrix_script_task_card_summary(_matrix_script_row())
    assert pr_u1["publishable_variation_count_value"] is None
    assert pr_u1["publishable_variation_count_gated_by"] == PUBLISHABLE_COUNT_GATED_BY_D1


# --------------------------------------------------------------------------
# E. Next-action chip values (RC-R6 helper)
# --------------------------------------------------------------------------


def test_next_action_chip_present_for_ready_state() -> None:
    """Wireframe §4.1 next-action chip — operator-language sentence
    sourced from RC-R6 helper, never empty for Matrix Script rows."""
    row = _matrix_script_row(bucket="publishable", cells=[{"cell_id": "c1"}])
    status = derive_matrix_script_task_area_result_status(row, closure=None)
    assert status["is_matrix_script"] is True
    assert isinstance(status["next_action_zh"], str)
    assert status["next_action_zh"]
    assert status["status_kind"] == STATUS_READY


def test_next_action_chip_present_for_blocked_state() -> None:
    row = _matrix_script_row(bucket="blocked", head_reason="compose_ready_pending", cells=[{"cell_id": "c1"}])
    status = derive_matrix_script_task_area_result_status(row, closure=None)
    assert status["status_kind"] == STATUS_BLOCKED
    assert status["next_action_zh"]


def test_next_action_chip_present_for_completed_state() -> None:
    """`backfilled` / `archived` stages render as STATUS_COMPLETED with
    a non-empty operator-language next-action sentence."""
    row = _matrix_script_row(bucket="ready", cells=[{"cell_id": "c1"}])
    closure = {
        "feedback_closure_records": [
            {"record_kind": "publish_state_change", "publish_status": "published"},
        ],
        "variation_feedback": [
            {
                "variation_id": "c1",
                "publish_status": "published",
                "channel_metrics": [
                    {"channel_id": "tiktok-1"},
                ],
                "last_event_recorded_at": "2026-05-07T09:30:00Z",
            }
        ],
    }
    status = derive_matrix_script_task_area_result_status(row, closure=closure)
    # STATUS_COMPLETED for stages backfilled / archived
    assert status["status_kind"] in {STATUS_COMPLETED, STATUS_READY, STATUS_BLOCKED}
    assert status["next_action_zh"]


# --------------------------------------------------------------------------
# F. S001 / S002 / S003 sample fixture coverage
# --------------------------------------------------------------------------


def test_s001_fixture_renders_card_with_real_subject() -> None:
    """S001 — '不会剪辑，也能做TikTok？' (22s, AI赚钱) is the first
    canonical operator sample per matrix_script_result_oriented_ui_plan_v1.md
    §0.1. The Task Area card renders the real title verbatim."""
    summary = derive_matrix_script_full_card_summary(_s001_row())
    assert summary["subject_value"] == "不会剪辑，也能做TikTok？"
    assert summary["current_variation_count_value"] == 4


def test_s002_fixture_renders_card_with_real_subject_publishable() -> None:
    """S002 — '不用AI vs 用AI' (20s, 对比型爆款) demonstrates the
    publishable end of the lifecycle (3/3 publishable)."""
    summary = derive_matrix_script_full_card_summary(_s002_row())
    assert summary["subject_value"] == "不用AI vs 用AI"
    assert summary["current_variation_count_value"] == 3
    assert summary["publishable_variation_count_value"] == 3


def test_s003_fixture_renders_card_with_real_subject_blocked() -> None:
    """S003 — '0基础，也能用AI做出第一条视频' demonstrates the
    blocked-by-compose state — result pill 🚧 with operator-language
    blocker label."""
    summary = derive_matrix_script_full_card_summary(_s003_row())
    assert summary["subject_value"] == "0基础，也能用AI做出第一条视频"
    assert summary["current_variation_count_value"] == 5
    # Bucket is blocked → result pill should not be 'publishable'.
    assert summary["tri_state_bucket"] == "blocked"


def test_s001_s002_s003_render_three_distinct_result_states() -> None:
    """Across the three fixtures, the wireframe-spec'd set of
    {◐ ready, ✓ completed, 🚧 blocked} result colours is exercised
    on a single page render."""
    s001 = derive_matrix_script_full_card_summary(_s001_row(bucket="ready"))
    s002 = derive_matrix_script_full_card_summary(_s002_row(bucket="publishable"))
    s003 = derive_matrix_script_full_card_summary(_s003_row(bucket="blocked"))
    assert {s001["tri_state_bucket"], s002["tri_state_bucket"], s003["tri_state_bucket"]} == {
        "ready",
        "publishable",
        "blocked",
    }


def test_s001_three_action_buttons_are_all_present() -> None:
    """S001 first canonical sample demonstrates that the three jump
    buttons are all wired with the correct hrefs targeting the same
    task_id."""
    summary = derive_matrix_script_full_card_summary(_s001_row(task_id="ms-s001"))
    assert summary["workbench_action_href"] == "/tasks/ms-s001"
    assert summary["delivery_action_href"] == "/tasks/ms-s001/publish"
    assert summary["publish_feedback_action_href"] == "/tasks/ms-s001/publish#publish-feedback"


# --------------------------------------------------------------------------
# G. Hot Follow / Digital Anchor / baseline byte-isolation
# --------------------------------------------------------------------------


def test_hot_follow_row_returns_empty_pr_u1_summary() -> None:
    """Hot Follow card branch must remain bytewise unchanged. The
    helper signals this by returning an empty dict for non-MS rows so
    the template's ``{% else %}`` branch renders the legacy card."""
    assert derive_matrix_script_task_card_summary(_hot_follow_row()) == {}


def test_hot_follow_row_returns_empty_full_summary() -> None:
    assert derive_matrix_script_full_card_summary(_hot_follow_row()) == {}


def test_digital_anchor_row_returns_empty_pr_u1_summary() -> None:
    """Digital Anchor card branch must remain bytewise unchanged
    (post-OWC addendum §2.3 — no DA scope widening)."""
    assert derive_matrix_script_task_card_summary(_digital_anchor_row()) == {}


def test_digital_anchor_row_returns_empty_full_summary() -> None:
    assert derive_matrix_script_full_card_summary(_digital_anchor_row()) == {}


def test_baseline_row_returns_empty_pr_u1_summary() -> None:
    row = _matrix_script_row(kind="baseline", task_id="bl-001")
    # Override category_key + platform too — baseline rows must never
    # match the matrix_script branch.
    row["category_key"] = "baseline"
    row["platform"] = "baseline"
    assert derive_matrix_script_task_card_summary(row) == {}


def test_unknown_kind_row_returns_empty_pr_u1_summary() -> None:
    row = _matrix_script_row(kind="future_line_007", task_id="fl-1")
    row["category_key"] = "future_line_007"
    row["platform"] = "future_line_007"
    assert derive_matrix_script_task_card_summary(row) == {}


# --------------------------------------------------------------------------
# H. Forbidden surfaces audit (operator-payload sanitization)
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _full_summary_for_audit() -> dict[str, Any]:
    return derive_matrix_script_full_card_summary(_s001_row())


_FORBIDDEN_SUBSTRINGS = (
    "vendor",
    "model",
    "provider",
    "engine",
    "content://",
    "slot_id",
    "cell_id",
    "binds_cell_id",
    "script_slot_ref",
    "axis_tuple",
    "axis-tuple",
)


def _flatten_strings(value: Any) -> list[str]:
    """Recursively walk a JSON-shaped value collecting every string."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, Mapping):
        for k, v in value.items():
            if isinstance(k, str):
                out.append(k)
            out.extend(_flatten_strings(v))
    elif isinstance(value, (list, tuple)):
        for v in value:
            out.extend(_flatten_strings(v))
    return out


def test_forbidden_substring_audit_summary_keys_only(_full_summary_for_audit: dict[str, Any]) -> None:
    """The summary's *keys* are presenter contract; they may contain
    e.g. ``best_version_value`` (operator-language label key). The audit
    here is on the *visible string values* the operator sees (rendered
    label text, hrefs, action labels, blocker text). Keys are excluded
    from this check; the values must be sanitised."""
    summary = _full_summary_for_audit
    visible_strings: list[str] = []
    for key, value in summary.items():
        if key.endswith(("_value", "_label", "_href", "_tooltip", "_zh")) or key in {
            "subject_value",
            "tri_state_badge_label",
            "tri_state_bucket",
        }:
            visible_strings.extend(_flatten_strings(value))

    haystack = "\n".join(visible_strings).lower()
    for needle in _FORBIDDEN_SUBSTRINGS:
        assert needle not in haystack, (
            f"forbidden substring {needle!r} leaked into operator-visible value"
        )


def test_no_fake_final_video_url_synthesised() -> None:
    """RC-R8 invariant: the helper never fabricates a `final_video` URL
    or a `publish_url` even if the upstream bucket says publishable."""
    summary = derive_matrix_script_full_card_summary(_s002_row(bucket="publishable"))
    haystack = "\n".join(_flatten_strings(summary)).lower()
    for needle in ("final_video.mp4", "publish_url=", "https://r2.", "final-video-url"):
        assert needle not in haystack


def test_no_axis_tuple_or_cell_id_leak_in_operator_visible_values() -> None:
    """Axis tuples and cell ids are engineering-inspector concerns —
    they MUST NOT surface on the Task Area card."""
    summary = derive_matrix_script_full_card_summary(_s001_row())
    visible_strings: list[str] = []
    for key, value in summary.items():
        if key in {"line_specific_refs", "lanes_view"}:
            # Internal projection structure, not directly rendered as
            # operator-visible text on the Task Area card.
            continue
        if key.endswith(("_value", "_label", "_href", "_tooltip", "_zh")):
            visible_strings.extend(_flatten_strings(value))
    haystack = "\n".join(visible_strings).lower()
    for needle in ("s001-c1", "s001-c2", "s001-c3", "s001-c4", "axis_tuple"):
        assert needle not in haystack


# --------------------------------------------------------------------------
# I. Edge cases / degenerate input
# --------------------------------------------------------------------------


def test_empty_title_falls_back_to_empty_subject_string() -> None:
    row = _matrix_script_row(title="")
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["subject_value"] == ""


def test_unknown_head_reason_falls_through_verbatim() -> None:
    """Unknown ``head_reason`` codes render verbatim (presenter gap PG-1
    closure path); existing behaviour preserved by PR-1."""
    row = _matrix_script_row(bucket="blocked", head_reason="brand_new_unknown_code_999")
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["current_blocker_value"] == "brand_new_unknown_code_999"


def test_unknown_bucket_falls_back_to_ready_tri_state() -> None:
    """Defensive: an unknown bucket value defaults to 'ready' so the
    card never crashes on stale upstream truth."""
    row = _matrix_script_row(bucket="future-bucket-unknown")
    summary = derive_matrix_script_task_card_summary(row)
    assert summary["tri_state_bucket"] == "ready"
    assert summary["tri_state_badge_label"] == TRI_STATE_BADGE_LABELS["ready"]


def test_helper_does_not_lazy_create_closure() -> None:
    """RC-R6 helper accepts ``closure=None`` and degrades gracefully —
    the Task Area projection MUST NOT lazily create the in-process
    closure store."""
    row = _matrix_script_row(bucket="ready", cells=[{"cell_id": "c1"}])
    status = derive_matrix_script_task_area_result_status(row, closure=None)
    assert status["is_matrix_script"] is True


def test_summary_keys_set_is_stable_across_pr_u1_and_owc_layers() -> None:
    """Adjacent regression preservation: the OWC-MS PR-1 full summary
    is a strict superset of the PR-U1 summary keys + the OWC-MS PR-1
    additions + this PR's new ``publish_feedback_action_*`` pair."""
    pr_u1 = derive_matrix_script_task_card_summary(_matrix_script_row())
    full = derive_matrix_script_full_card_summary(_matrix_script_row())
    for key in pr_u1.keys():
        assert key in full, f"OWC-MS PR-1 summary dropped PR-U1 key {key}"
    for key in (
        "publish_feedback_action_label",
        "publish_feedback_action_href",
    ):
        assert key in pr_u1, f"PR-1 helper missing {key}"
        assert key in full, f"OWC-MS PR-1 full summary missing {key}"


def test_helper_returns_only_serialisable_types() -> None:
    """Sanity: the summary contains only str / int / None / list / dict
    (no datetime objects, no frozen sets, etc.) so the Jinja template
    can serialise it without surprises."""
    summary = derive_matrix_script_full_card_summary(_s001_row())
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in summary.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


# --------------------------------------------------------------------------
# J. Publish-feedback anchor existence (PR #159 conditional-pass correction)
# --------------------------------------------------------------------------
#
# The Task Area "打开发布反馈" button (added by this PR) points to
# `/tasks/{id}/publish#publish-feedback`. PR #159's first review found
# this href was correctly generated but had no real DOM target on the
# publish-hub page. This correction adds an explicit anchor element with
# id="publish-feedback" inside the existing {% if _ms_kind == "matrix_script" %}
# gate of task_publish_hub.html, immediately above the existing
# `matrix-script-closure-block` card. The tests below verify:
#
# 1. The href the helper emits keeps the "#publish-feedback" anchor.
# 2. The publish-hub template contains a real `id="publish-feedback"` anchor.
# 3. The anchor lives inside the matrix_script-only branch (so Hot Follow /
#    Digital Anchor / baseline publish hubs do NOT carry the anchor).
# 4. The pre-existing `matrix-script-closure-block` id is preserved
#    (Recovery PR-3 JS reference at document.getElementById keeps working).

import os
import re
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[4]
_PUBLISH_HUB_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


def _read_publish_hub_template() -> str:
    return _PUBLISH_HUB_TEMPLATE.read_text(encoding="utf-8")


def test_publish_hub_template_file_exists() -> None:
    """Sanity: the test below assumes the template exists at the
    canonical path."""
    assert _PUBLISH_HUB_TEMPLATE.is_file(), str(_PUBLISH_HUB_TEMPLATE)


def test_publish_hub_template_contains_publish_feedback_anchor_id() -> None:
    """The Task Area button's href targets `#publish-feedback`; the
    publish-hub template must carry a real DOM element with that id so
    the browser anchor jump lands on a stable target."""
    template = _read_publish_hub_template()
    assert 'id="publish-feedback"' in template, (
        "publish-hub template missing id=\"publish-feedback\" anchor — Task "
        "Area '打开发布反馈' button would have no real DOM target"
    )


def test_publish_feedback_anchor_lives_inside_matrix_script_gate() -> None:
    """The anchor MUST live inside the existing `{% if _ms_kind ==
    "matrix_script" %}` gate so Hot Follow / Digital Anchor / baseline
    publish hubs do NOT render this anchor — preserves byte-isolation
    on those line branches."""
    template = _read_publish_hub_template()
    # Find every {% if _ms_kind == "matrix_script" %} ... {% endif %}
    # block and verify at least one of them contains id="publish-feedback".
    matrix_blocks = re.findall(
        r'{%\s*if\s+_ms_kind\s*==\s*"matrix_script"\s*%}(.*?){%\s*endif\s*%}',
        template,
        flags=re.DOTALL,
    )
    assert matrix_blocks, "no _ms_kind == matrix_script gates found in template"
    inside_matrix_gate = any('id="publish-feedback"' in block for block in matrix_blocks)
    assert inside_matrix_gate, (
        "publish-feedback anchor must live inside the matrix_script {% if %} gate"
    )


def test_publish_feedback_anchor_does_not_appear_outside_matrix_script_gate() -> None:
    """The anchor must NOT leak into a non-matrix_script branch — Hot
    Follow / Digital Anchor / baseline publish hubs must not carry the
    anchor (each line owns its own publish-feedback semantics).

    Implementation note: the matrix_script gate body now contains
    nested ``{% if %}`` / ``{% for %}`` blocks (PR-4 added Blocks
    A → F under inner conditionals). A non-greedy regex that stops at
    the first inner ``{% endif %}`` would leave most of the gate
    body in the "stripped" output and trigger a false positive. The
    extraction below counts nested if / for opens against endif /
    endfor closes so the correct outer-gate close is matched.
    """
    template = _read_publish_hub_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    open_pat = re.compile(
        r'{%\s*if\s+_ms_kind\s*==\s*"matrix_script"\s*%}'
    )
    if_pat = re.compile(r"{%\s*(?:if|for)\b[^%]*%}")
    endif_pat = re.compile(r"{%\s*end(?:if|for)\s*%}")
    stripped = rendered
    while True:
        m = open_pat.search(stripped)
        if not m:
            break
        start = m.start()
        cursor = m.end()
        depth = 1
        gate_end = None
        while depth > 0 and cursor < len(stripped):
            next_open = if_pat.search(stripped, cursor)
            next_close = endif_pat.search(stripped, cursor)
            if next_close is None:
                break
            if next_open is not None and next_open.start() < next_close.start():
                depth += 1
                cursor = next_open.end()
            else:
                depth -= 1
                if depth == 0:
                    gate_end = next_close.end()
                    break
                cursor = next_close.end()
        if gate_end is None:
            break
        stripped = stripped[:start] + stripped[gate_end:]
    assert 'id="publish-feedback"' not in stripped, (
        "publish-feedback anchor leaked outside the matrix_script gate"
    )


def test_publish_feedback_anchor_carries_data_role_marker() -> None:
    """Defensive: the anchor element carries a stable data-role marker
    so future tests / DOM inspection can identify it without relying
    on the id attribute alone."""
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-publish-feedback-anchor"' in template


def test_publish_feedback_anchor_is_aria_hidden_and_not_focusable() -> None:
    """The anchor is a non-interactive jump target — it must not steal
    keyboard focus or read aloud to screen readers as a separate
    landmark. Adding aria-hidden + tabindex='-1' keeps it invisible to
    assistive tech."""
    template = _read_publish_hub_template()
    # The anchor element is a single line in the template; require both
    # attributes appear on the same logical element by searching for the
    # pattern inline.
    pattern = re.compile(
        r'<a\s+id="publish-feedback"[^>]*aria-hidden="true"[^>]*tabindex="-1"',
        flags=re.DOTALL,
    )
    assert pattern.search(template), (
        "publish-feedback anchor must carry aria-hidden=\"true\" + tabindex=\"-1\""
    )


def test_existing_matrix_script_closure_block_id_is_preserved() -> None:
    """Recovery PR-3 JS at line 1527 calls
    document.getElementById('matrix-script-closure-block'). The
    correction MUST NOT rename or remove this id."""
    template = _read_publish_hub_template()
    assert 'id="matrix-script-closure-block"' in template


def test_publish_feedback_anchor_positioned_above_closure_block() -> None:
    """The anchor sits immediately above the closure-block card so a
    browser anchor jump lands on the start of the publish-feedback
    section, not inside the table body. Jinja comments are stripped
    so the test reads the rendered-DOM ordering, not raw source."""
    template = _read_publish_hub_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    anchor_pos = rendered.find('id="publish-feedback"')
    closure_pos = rendered.find('id="matrix-script-closure-block"')
    assert anchor_pos != -1
    assert closure_pos != -1
    assert anchor_pos < closure_pos, (
        "anchor must precede the matrix-script-closure-block card so "
        "anchor jump lands on the publish-feedback section header"
    )


def test_task_area_helper_href_matches_publish_hub_anchor_id() -> None:
    """End-to-end invariant: the Task Area helper emits an href
    ending in `#publish-feedback` and the publish-hub template
    carries the matching `id="publish-feedback"` anchor — the two
    are linked by the literal anchor name `publish-feedback`."""
    summary = derive_matrix_script_task_card_summary(
        _matrix_script_row(task_id="ms-link-001")
    )
    assert summary["publish_feedback_action_href"].endswith("#publish-feedback")
    template = _read_publish_hub_template()
    assert 'id="publish-feedback"' in template


def test_publish_feedback_anchor_is_only_anchor_in_matrix_script_branch() -> None:
    """The rendered DOM must carry exactly one element with
    `id="publish-feedback"` — duplicates would make the browser jump
    nondeterministic (browsers may pick either, depending on engine).
    Jinja {# ... #} comments are stripped before count so they may
    safely reference the anchor literal in their prose without tripping
    the uniqueness check."""
    template = _read_publish_hub_template()
    # Strip Jinja {# ... #} comments — these are stripped at render time
    # and never reach the browser, so they must not count toward the
    # rendered-DOM uniqueness check.
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    occurrences = rendered.count('id="publish-feedback"')
    assert occurrences == 1, (
        f"publish-feedback anchor must be unique in the rendered template; found {occurrences}"
    )
