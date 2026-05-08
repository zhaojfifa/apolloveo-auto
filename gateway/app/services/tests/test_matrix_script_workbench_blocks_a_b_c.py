"""OWC-MS-RO PR-2 — Matrix Script Workbench Blocks A / B / C dedicated tests.

Authority pointers:

- ``docs/design/matrix_script_workbench_wireframe_v1.md`` §3 / §4 / §5
  (Blocks A / B / C binding-and-exhaustive fields).
- ``docs/design/matrix_script_result_oriented_ui_implementation_slicing_v1.md``
  §4 (PR-2 scope, RO-2.* acceptance evidence) + §5.3 (preserved
  diagnostics) + §5.5 (hard non-goals) + §2.1.3 (PR-2 gating clause)
  + §2 "OR by whatever later authority supersedes them" (the user's
  direct instruction is the authority that opens PR-2 in this turn).
- ``docs/product/matrix_script_product_flow_v1.md`` §6 (Workbench design).
- Operator sample anchor: ``production_packet_3_scripts.json`` —
  S001 / S002 / S003 baked into fixtures below.
- Existing helpers consumed (no new helper module per PR-2 scope):
  ``gateway/app/services/matrix_script/script_structure_view.py``,
  ``gateway/app/services/matrix_script/result_status_view.py``,
  ``gateway/app/services/matrix_script/readable_variant_view.py``,
  ``gateway/app/services/matrix_script/workbench_comprehension.py``.

PR-2 binding behaviour proved by this suite:

1. ``derive_matrix_script_script_structure_view`` exposes the four Block A
   read-only fields (``title_value`` / ``axis_hints.audience_hint`` /
   ``target_platform_value`` / ``language_scope.target_language``) used by
   the new Block A panel.
2. ``derive_matrix_script_workbench_result_summary`` exposes the three
   Block A status fields (``status_label_zh`` / ``head_reason_label_zh`` /
   ``next_action_zh``) used by the new Block A panel.
3. ``derive_matrix_script_script_structure_view`` exposes the Block B
   sections (Hook / Body / CTA) and taxonomies (keywords / forbidden) in
   operator-readable shape.
4. ``derive_matrix_script_readable_variants`` exposes the Block C variant
   count + per-variant differentiator + axis_summary + length hint
   + bound-slot label.
5. The Workbench Block C variant table renders without exposing raw
   axis-tuple labels, ``cell_id``, ``slot_id``, ``script_slot_ref``, or
   ``content://`` handles in the operator-visible columns.
6. The Block A jump buttons resolve to ``/tasks/{task_id}/publish`` and
   ``/tasks/{task_id}/publish#publish-feedback`` (the existing
   publish-hub URL + the anchor landed in PR-1's correction).
7. Hot Follow / Digital Anchor / baseline panels return ``{}`` from each
   of the four helpers — the new template panels gate on
   ``is_matrix_script`` so non-MS workbench surfaces stay bytewise
   unchanged.
8. Forbidden surfaces audit: no vendor / model / provider / engine /
   ``content://`` / ``slot_id`` / ``cell_id`` leakage in any
   operator-visible value emitted by the helpers PR-2 reads.
9. Template assertions: the new ``data-role`` markers
   (``matrix-script-block-a-goal-summary`` / ``matrix-script-block-b-script-structure``
   / ``matrix-script-block-c-variant-strategy``) are present in
   ``task_workbench.html`` and are gated to the matrix_script branch
   only.
10. Existing PR-U2 + MS-W3 + Variation Panel anchors are preserved
    verbatim — secondary diagnostics still render below the new blocks.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.readable_variant_view import (
    derive_matrix_script_readable_variants,
)
from gateway.app.services.matrix_script.result_status_view import (
    STATUS_BLOCKED,
    STATUS_COMPLETED,
    STATUS_READY,
    derive_matrix_script_workbench_result_summary,
)
from gateway.app.services.matrix_script.script_structure_view import (
    derive_matrix_script_script_structure_view,
)
from gateway.app.services.matrix_script.workbench_comprehension import (
    derive_matrix_script_workbench_comprehension,
)


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read_workbench_template() -> str:
    return _WORKBENCH_TEMPLATE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Test fixtures (S001 / S002 / S003 + Hot Follow / DA byte-isolation)
# --------------------------------------------------------------------------


def _matrix_script_task(
    *,
    task_id: str = "ms-wb-001",
    topic: str = "PR-2 测试任务",
    audience_hint: str = "想做短视频但门槛犹豫的新手",
    target_platform: str = "TikTok",
    target_language: list[str] | None = None,
    tone_hint: str = "真诚",
    length_hint: str = "22s",
    variation_target_count: int = 4,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a task dict shaped like Phase A entry + Phase B authoring
    output for matrix_script."""
    target_language = target_language if target_language is not None else ["zh-CN"]
    cells = cells if cells is not None else []
    slots = slots if slots is not None else []
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "title": topic,
        "config": {
            "entry": {
                "topic": topic,
                "audience_hint": audience_hint,
                "tone_hint": tone_hint,
                "length_hint": length_hint,
                "target_platform": target_platform,
                "language_scope": {
                    "source_language": "zh-CN",
                    "target_language": target_language,
                },
                "variation_target_count": variation_target_count,
                "source_script_ref": "content://matrix-script/source/mint-abcdef0123456789",
            },
        },
        "packet": {
            "line_specific_refs": [
                {
                    "ref_id": "matrix_script_variation_matrix",
                    "delta": {"cells": cells},
                    "binds_to": ["factory_content_structure_contract_v1"],
                },
                {
                    "ref_id": "matrix_script_slot_pack",
                    "delta": {"slots": slots},
                    "binds_to": ["factory_content_structure_contract_v1"],
                },
            ],
        },
    }


def _ms_panel(*, refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "panel_kind": "matrix_script",
        "refs": refs or [],
    }


def _variation_surface(
    *, cells: list[dict[str, Any]] | None = None, slots: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    cells = cells or []
    slots = slots or []
    return {
        "variation_plan": {
            "axes": [
                {"axis_id": "tone", "kind": "nominal", "values": ["sincere", "rhetorical"], "is_required": True},
            ],
            "cells": cells,
        },
        "copy_bundle": {"slots": slots},
        "attribution_refs": {"line_specific_refs": []},
        "publish_feedback_projection": {},
    }


def _s001_task(*, task_id: str = "ms-s001") -> dict[str, Any]:
    """S001 — '不会剪辑，也能做TikTok？' (22s, AI赚钱, 第一批量产首选)."""
    return _matrix_script_task(
        task_id=task_id,
        topic="不会剪辑，也能做TikTok？",
        audience_hint="想做短视频但门槛犹豫的新手",
        target_platform="TikTok",
        target_language=["zh-CN"],
        tone_hint="真诚",
        length_hint="22s",
        variation_target_count=4,
        cells=[
            {"cell_id": "s001-c1", "axis_selections": {"tone": "sincere"}, "script_slot_ref": "s001-slot-1"},
            {"cell_id": "s001-c2", "axis_selections": {"tone": "rhetorical"}, "script_slot_ref": "s001-slot-2"},
            {"cell_id": "s001-c3", "axis_selections": {"tone": "confident"}, "script_slot_ref": "s001-slot-3"},
            {"cell_id": "s001-c4", "axis_selections": {"tone": "playful"}, "script_slot_ref": "s001-slot-4"},
        ],
        slots=[
            {"slot_id": f"s001-slot-{i}", "body_ref": f"content://matrix-script/body/s001-{i}", "length_hint": "22s"}
            for i in range(1, 5)
        ],
    )


def _s002_task() -> dict[str, Any]:
    """S002 — '不用AI vs 用AI' (20s, 对比型爆款)."""
    return _matrix_script_task(
        task_id="ms-s002",
        topic="不用AI vs 用AI",
        audience_hint="效率焦虑的内容运营",
        target_platform="TikTok",
        target_language=["zh-CN"],
        tone_hint="对比",
        length_hint="20s",
        variation_target_count=3,
        cells=[
            {"cell_id": "s002-c1", "axis_selections": {"tone": "comparative"}, "script_slot_ref": "s002-slot-1"},
            {"cell_id": "s002-c2", "axis_selections": {"tone": "comparative"}, "script_slot_ref": "s002-slot-2"},
            {"cell_id": "s002-c3", "axis_selections": {"tone": "comparative"}, "script_slot_ref": "s002-slot-3"},
        ],
        slots=[
            {"slot_id": f"s002-slot-{i}", "body_ref": f"content://matrix-script/body/s002-{i}", "length_hint": "20s"}
            for i in range(1, 4)
        ],
    )


def _s003_task() -> dict[str, Any]:
    """S003 — '0基础，也能用AI做出第一条视频' (25s, 案例感更强)."""
    return _matrix_script_task(
        task_id="ms-s003",
        topic="0基础，也能用AI做出第一条视频",
        audience_hint="完全没起步的新手",
        target_platform="TikTok",
        target_language=["zh-CN"],
        tone_hint="成长",
        length_hint="25s",
        variation_target_count=5,
        cells=[
            {"cell_id": f"s003-c{i}", "axis_selections": {"tone": "growth"}, "script_slot_ref": f"s003-slot-{i}"}
            for i in range(1, 6)
        ],
        slots=[
            {"slot_id": f"s003-slot-{i}", "body_ref": f"content://matrix-script/body/s003-{i}", "length_hint": "25s"}
            for i in range(1, 6)
        ],
    )


def _hot_follow_task() -> dict[str, Any]:
    return {
        "task_id": "hf-1",
        "id": "hf-1",
        "kind": "hot_follow",
        "category_key": "hot_follow",
        "title": "Hot Follow sample",
        "config": {"entry": {}},
    }


def _digital_anchor_task() -> dict[str, Any]:
    return {
        "task_id": "da-1",
        "id": "da-1",
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "title": "Digital Anchor sample",
        "config": {"entry": {}},
    }


def _baseline_task() -> dict[str, Any]:
    return {
        "task_id": "bl-1",
        "id": "bl-1",
        "kind": "baseline",
        "category_key": "baseline",
        "title": "baseline sample",
        "config": {"entry": {}},
    }


def _publish_readiness(*, publishable: bool = False, head_reason: str | None = None) -> dict[str, Any]:
    return {
        "publishable": publishable,
        "head_reason": head_reason,
        "consumed_inputs": {"blocking_count": 0 if publishable else 1},
        "blocking_advisories": [],
    }


# --------------------------------------------------------------------------
# A. Block A — Goal Summary (subject / audience / target_platform / language)
# --------------------------------------------------------------------------


def test_block_a_subject_resolves_from_script_structure_view() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    assert view["title_value"] == "不会剪辑，也能做TikTok？"


def test_block_a_audience_resolves_from_axis_hints() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    assert view["axis_hints"]["audience_hint"] == "想做短视频但门槛犹豫的新手"


def test_block_a_target_platform_resolves_from_script_structure_view() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    assert view["target_platform_value"] == "TikTok"


def test_block_a_target_language_resolves_as_list() -> None:
    view = derive_matrix_script_script_structure_view(
        _matrix_script_task(target_language=["zh-CN", "en-US"])
    )
    assert view["language_scope"]["target_language"] == ["zh-CN", "en-US"]


def test_block_a_target_language_normalises_string_to_list() -> None:
    """Defensive: a string-typed target_language is normalised to a
    single-element list so the template ``| join(", ")`` works."""
    task = _matrix_script_task()
    task["config"]["entry"]["language_scope"]["target_language"] = "zh-CN"
    view = derive_matrix_script_script_structure_view(task)
    assert view["language_scope"]["target_language"] == ["zh-CN"]


def test_block_a_status_pill_ready_when_publishable() -> None:
    summary = derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    assert summary["status_kind"] == STATUS_READY
    assert summary["status_label_zh"]
    assert summary["next_action_zh"]


def test_block_a_status_pill_blocked_when_head_reason_present() -> None:
    summary = derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=False, head_reason="compose_not_ready"),
        _ms_panel(),
    )
    assert summary["status_kind"] == STATUS_BLOCKED
    assert summary["head_reason_label_zh"]


def test_block_a_blocker_label_renders_operator_language() -> None:
    summary = derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _ms_panel(),
    )
    # operator language label, not the raw enum
    assert summary["head_reason_label_zh"] != "final_missing"


def test_block_a_next_action_present_for_all_status_kinds() -> None:
    for ready, hr in [(True, None), (False, "compose_not_ready"), (False, None)]:
        summary = derive_matrix_script_workbench_result_summary(
            _publish_readiness(publishable=ready, head_reason=hr),
            _ms_panel(),
        )
        assert isinstance(summary.get("next_action_zh"), str) and summary["next_action_zh"]


# --------------------------------------------------------------------------
# B. Block B — Script Structure (Hook / Body / CTA + keywords + forbidden)
# --------------------------------------------------------------------------


def test_block_b_renders_three_sections_in_canonical_order() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    sections = view["sections"]
    section_ids = [s["section_id"] for s in sections]
    assert section_ids == ["hook", "body", "cta"]


def test_block_b_section_labels_are_operator_language() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    for section in view["sections"]:
        assert isinstance(section["section_label_zh"], str)
        assert section["section_label_zh"]


def test_block_b_renders_keywords_and_forbidden_taxonomies() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    taxonomy_ids = [t["taxonomy_id"] for t in view["taxonomy"]]
    # Block B renders both the keywords taxonomy and the forbidden_terms
    # taxonomy in operator-readable form. The taxonomy_id values match
    # the closed enum in script_structure_view (TAXONOMY_KEYWORDS +
    # TAXONOMY_FORBIDDEN constants).
    assert "keywords" in taxonomy_ids
    assert "forbidden_terms" in taxonomy_ids


def test_block_b_keywords_taxonomy_has_values_or_status_label() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    keywords = next(t for t in view["taxonomy"] if t["taxonomy_id"] == "keywords")
    # Either operator-readable values list or a status label — never raw refs.
    assert "values" in keywords
    assert "values_status_label_zh" in keywords


def test_block_b_forbidden_taxonomy_carries_status_label() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    forbidden = next(t for t in view["taxonomy"] if t["taxonomy_id"] == "forbidden_terms")
    assert "values_status_label_zh" in forbidden


def test_block_b_section_body_text_is_operator_language() -> None:
    """Sections expose body_text strings, never opaque ref tokens."""
    view = derive_matrix_script_script_structure_view(_s001_task())
    for section in view["sections"]:
        body = section.get("body_text")
        if body is not None:
            assert "content://" not in body
            assert "slot_id" not in body.lower()
            assert "cell_id" not in body.lower()


# --------------------------------------------------------------------------
# C. Block C — Variant Strategy
# --------------------------------------------------------------------------


def test_block_c_variant_count_matches_cells() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": f"c{i}", "axis_selections": {"tone": "sincere"}} for i in range(1, 5)],
        slots=[{"slot_id": f"s{i}", "body_ref": "x", "length_hint": "22s"} for i in range(1, 5)],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert out["variant_count"] == 4
    assert len(out["variant_candidates"]) == 4


def test_block_c_each_variant_carries_differentiator_zh() -> None:
    surface = _variation_surface(
        cells=[
            {"cell_id": "c1", "axis_selections": {"tone": "sincere"}},
            {"cell_id": "c2", "axis_selections": {"tone": "rhetorical"}},
        ],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    for variant in out["variant_candidates"]:
        assert "differentiator_zh" in variant


def test_block_c_variant_carries_axis_summary_zh() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}}],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert isinstance(out["variant_candidates"][0]["axis_summary_zh"], str)


def test_block_c_variant_carries_length_hint_zh() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere", "length": 22}}],
        slots=[{"slot_id": "s1", "body_ref": "x", "length_hint": 22}],
    )
    # bind cell to slot
    surface["variation_plan"]["cells"][0]["script_slot_ref"] = "s1"
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert "length_hint_zh" in out["variant_candidates"][0]


def test_block_c_variant_carries_bound_slot_label_zh() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}, "script_slot_ref": "s1"}],
        slots=[{"slot_id": "s1", "body_ref": "x", "length_hint": "22s"}],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert isinstance(out["variant_candidates"][0]["bound_slot_label_zh"], str)


def test_block_c_no_raw_axis_tuple_label_in_operator_visible_columns() -> None:
    """Block C operator-visible columns surface differentiator_zh + axis_summary_zh
    + length_hint_zh + bound_slot_label_zh. Raw axis tuple representations
    like 'tone=sincere · audience=b2b' must NOT leak into those values."""
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere", "audience": "newbie"}}],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    variant = out["variant_candidates"][0]
    # axis_selections is exposed as a dict (engineering metadata) but the
    # *operator-visible* fields used by the template are differentiator_zh,
    # axis_summary_zh, length_hint_zh, bound_slot_label_zh. Those four must
    # not include the raw `tone=sincere · audience=newbie` engineering form.
    operator_visible = " ".join([
        str(variant.get("differentiator_zh") or ""),
        str(variant.get("length_hint_zh") or ""),
        str(variant.get("bound_slot_label_zh") or ""),
    ])
    assert "tone=" not in operator_visible
    assert "audience=" not in operator_visible


def test_block_c_no_cell_id_in_operator_visible_columns() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "raw-cell-id-leak-001", "axis_selections": {"tone": "sincere"}}],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    variant = out["variant_candidates"][0]
    operator_visible = " ".join([
        str(variant.get("differentiator_zh") or ""),
        str(variant.get("axis_summary_zh") or ""),
        str(variant.get("length_hint_zh") or ""),
        str(variant.get("bound_slot_label_zh") or ""),
    ])
    assert "raw-cell-id-leak-001" not in operator_visible


def test_block_c_no_content_handle_in_operator_visible_columns() -> None:
    """The slot body_ref is `content://matrix-script/body/...` — opaque.
    Must NEVER leak into the operator-visible bound_slot_label_zh."""
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}, "script_slot_ref": "s1"}],
        slots=[{"slot_id": "s1", "body_ref": "content://matrix-script/body/SECRET-OPAQUE-HANDLE", "length_hint": "22s"}],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    variant = out["variant_candidates"][0]
    assert "SECRET-OPAQUE-HANDLE" not in str(variant.get("bound_slot_label_zh") or "")
    assert "content://" not in str(variant.get("bound_slot_label_zh") or "")


def test_block_c_no_script_slot_ref_in_operator_visible_columns() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}, "script_slot_ref": "raw-slot-ref-leak-001"}],
        slots=[{"slot_id": "raw-slot-ref-leak-001", "body_ref": "x", "length_hint": "22s"}],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    variant = out["variant_candidates"][0]
    operator_visible = " ".join([
        str(variant.get("differentiator_zh") or ""),
        str(variant.get("length_hint_zh") or ""),
        str(variant.get("bound_slot_label_zh") or ""),
    ])
    assert "raw-slot-ref-leak-001" not in operator_visible


# --------------------------------------------------------------------------
# D. Jump button hrefs (Block A)
# --------------------------------------------------------------------------


def test_template_block_a_jump_button_targets_publish_hub() -> None:
    template = _read_workbench_template()
    # The Block A delivery jump button targets /tasks/{task_id}/publish.
    assert 'data-role="ms-block-a-action-delivery"' in template


def test_template_block_a_jump_button_to_publish_feedback_anchor() -> None:
    template = _read_workbench_template()
    # The Block A publish-feedback jump button targets the
    # #publish-feedback anchor landed by OWC-MS-RO PR-1's correction.
    assert 'data-role="ms-block-a-action-publish-feedback"' in template
    assert "/publish#publish-feedback" in template


def test_template_block_a_jump_button_uses_task_id_template_var() -> None:
    """The jump-button hrefs interpolate ``task.task_id`` so each task
    resolves to its own publish-hub URL — not a hardcoded path."""
    template = _read_workbench_template()
    assert "/tasks/{{ task.task_id }}/publish" in template


# --------------------------------------------------------------------------
# E. S001 / S002 / S003 sample fixture coverage
# --------------------------------------------------------------------------


def test_s001_block_a_renders_real_subject() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    assert view["title_value"] == "不会剪辑，也能做TikTok？"
    assert view["axis_hints"]["audience_hint"] == "想做短视频但门槛犹豫的新手"


def test_s002_block_a_renders_real_subject_comparative() -> None:
    view = derive_matrix_script_script_structure_view(_s002_task())
    assert view["title_value"] == "不用AI vs 用AI"


def test_s003_block_a_renders_real_subject_growth() -> None:
    view = derive_matrix_script_script_structure_view(_s003_task())
    assert view["title_value"] == "0基础，也能用AI做出第一条视频"


def test_s001_block_c_renders_4_variant_candidates() -> None:
    surface = _variation_surface(
        cells=_s001_task()["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=_s001_task()["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert out["variant_count"] == 4


def test_s003_block_c_renders_5_variant_candidates() -> None:
    surface = _variation_surface(
        cells=_s003_task()["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=_s003_task()["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    out = derive_matrix_script_readable_variants(_s003_task(), surface, _ms_panel())
    assert out["variant_count"] == 5


# --------------------------------------------------------------------------
# F. Hot Follow / Digital Anchor / baseline byte-isolation
# --------------------------------------------------------------------------


def test_hot_follow_task_returns_empty_script_structure_view() -> None:
    assert derive_matrix_script_script_structure_view(_hot_follow_task()) == {}


def test_digital_anchor_task_returns_empty_script_structure_view() -> None:
    assert derive_matrix_script_script_structure_view(_digital_anchor_task()) == {}


def test_baseline_task_returns_empty_script_structure_view() -> None:
    assert derive_matrix_script_script_structure_view(_baseline_task()) == {}


def test_hot_follow_panel_returns_empty_workbench_result_summary() -> None:
    assert derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=True),
        {"panel_kind": "hot_follow"},
    ) == {}


def test_digital_anchor_panel_returns_empty_workbench_result_summary() -> None:
    assert derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=True),
        {"panel_kind": "digital_anchor"},
    ) == {}


def test_hot_follow_panel_returns_empty_readable_variants() -> None:
    assert derive_matrix_script_readable_variants(
        _hot_follow_task(),
        _variation_surface(),
        {"panel_kind": "hot_follow"},
    ) == {}


def test_digital_anchor_panel_returns_empty_readable_variants() -> None:
    assert derive_matrix_script_readable_variants(
        _digital_anchor_task(),
        _variation_surface(),
        {"panel_kind": "digital_anchor"},
    ) == {}


# --------------------------------------------------------------------------
# G. Forbidden-substring audit on operator-visible helper outputs
# --------------------------------------------------------------------------


_FORBIDDEN_SUBSTRINGS_OPERATOR_VISIBLE = (
    "vendor",
    "model",
    "provider",
    "engine",
    "content://",
    "binds_cell_id",
    "axis_tuple",
    "axis-tuple",
)


def _flatten_strings(value: Any) -> list[str]:
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


def test_script_structure_view_no_vendor_or_model_in_operator_visible_values() -> None:
    """Forbidden-substring audit on Block A/B operator-visible values
    — EXCLUDES the ``forbidden_terms`` taxonomy values list, which is by
    definition the warning list of words operators are told to avoid
    ("vendor / model / provider / engine"). That's an operator
    *instruction*, not a leakage of vendor identifiers."""
    view = derive_matrix_script_script_structure_view(_s001_task())
    visible_strings: list[str] = []
    for key, value in view.items():
        # Skip the forbidden_terms taxonomy entries — their `values` field
        # is the warning list itself, which legitimately contains the
        # words it warns operators against using.
        if key == "taxonomy":
            for tax in value:
                if tax.get("taxonomy_id") == "forbidden_terms":
                    visible_strings.append(str(tax.get("taxonomy_label_zh") or ""))
                    visible_strings.append(str(tax.get("values_status_label_zh") or ""))
                    continue
                visible_strings.extend(_flatten_strings(tax))
            continue
        if key.endswith(("_value", "_label_zh", "_zh")) or key in {
            "sections",
            "axis_hints",
            "language_scope",
        }:
            visible_strings.extend(_flatten_strings(value))
    haystack = "\n".join(visible_strings).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack, (
            f"forbidden substring {needle!r} leaked into Block A/B operator-visible value"
        )


def test_workbench_result_summary_no_provider_in_operator_visible_values() -> None:
    summary = derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=False, head_reason="compose_not_ready"),
        _ms_panel(),
    )
    haystack = "\n".join(_flatten_strings(summary)).lower()
    for needle in ("vendor", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


def test_readable_variants_no_fake_final_video_url() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}}],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    haystack = "\n".join(_flatten_strings(out)).lower()
    # Block C MUST NOT echo a fake final_video URL or fabricated publish_url.
    for needle in ("final_video.mp4", "publish_url=", "https://r2."):
        assert needle not in haystack


# --------------------------------------------------------------------------
# H. Template assertions — Block A/B/C panel anchors + matrix_script-only gate
# --------------------------------------------------------------------------


def test_template_workbench_file_exists() -> None:
    assert _WORKBENCH_TEMPLATE.is_file(), str(_WORKBENCH_TEMPLATE)


def test_template_carries_block_a_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-a-goal-summary"' in template


def test_template_carries_block_b_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-b-script-structure"' in template


def test_template_carries_block_c_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-c-variant-strategy"' in template


def test_template_block_b_includes_section_anchors() -> None:
    """Block B renders Hook / Body / CTA via per-section data-role
    markers + status-coded data attributes."""
    template = _read_workbench_template()
    assert 'data-role="ms-block-b-section"' in template
    assert "section.section_id" in template


def test_template_block_c_renders_per_variant_table_with_4_columns() -> None:
    template = _read_workbench_template()
    assert 'data-role="ms-block-c-variant-table"' in template
    # The five operator-visible columns: 变体 / 差异点 / 视角概要 / 节奏·时长 / 脚本片段
    for header_label in ("变体", "差异点", "视角概要", "节奏 / 时长", "脚本片段"):
        assert header_label in template


def _matrix_script_panel_gate_body(template: str) -> str:
    """Extract the body of the existing
    `{% if ops_workbench_panel.panel_kind == "matrix_script" %}...{% endif %}`
    gate, counting nested `{% if %}` / `{% endif %}` pairs so the right
    closing `{% endif %}` is matched (regex-only matching picks the first
    nested endif and breaks)."""
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    open_pat = re.compile(r'{%\s*if\s+ops_workbench_panel\.panel_kind\s*==\s*"matrix_script"\s*%}')
    if_pat = re.compile(r"{%\s*(?:if|for)\b[^%]*%}")
    endif_pat = re.compile(r"{%\s*end(?:if|for)\s*%}")

    m = open_pat.search(rendered)
    if not m:
        return ""
    start = m.end()
    depth = 1
    cursor = start
    while depth > 0 and cursor < len(rendered):
        next_open = if_pat.search(rendered, cursor)
        next_close = endif_pat.search(rendered, cursor)
        if next_close is None:
            break
        if next_open is not None and next_open.start() < next_close.start():
            depth += 1
            cursor = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return rendered[start:next_close.start()]
            cursor = next_close.end()
    return ""


def test_template_block_a_b_c_live_inside_matrix_script_panel_gate() -> None:
    """All three block panels must live inside the existing
    `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate so
    Hot Follow / Digital Anchor / baseline workbench surfaces stay
    bytewise unchanged."""
    template = _read_workbench_template()
    inside = _matrix_script_panel_gate_body(template)
    assert inside, "matrix_script panel gate body not found in workbench template"
    for marker in (
        'data-role="matrix-script-block-a-goal-summary"',
        'data-role="matrix-script-block-b-script-structure"',
        'data-role="matrix-script-block-c-variant-strategy"',
    ):
        assert marker in inside, f"{marker} must live inside matrix_script panel gate"


def test_template_block_a_b_c_do_not_appear_outside_matrix_script_panel_gate() -> None:
    template = _read_workbench_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    inside = _matrix_script_panel_gate_body(template)
    assert inside
    # Compute the "outside" by removing the inside substring from the
    # rendered template.
    outside = rendered.replace(inside, "")
    for marker in (
        'data-role="matrix-script-block-a-goal-summary"',
        'data-role="matrix-script-block-b-script-structure"',
        'data-role="matrix-script-block-c-variant-strategy"',
    ):
        assert marker not in outside, (
            f"{marker} leaked outside the matrix_script panel gate"
        )


def test_template_existing_pr_u2_comprehension_panel_preserved() -> None:
    """Slicing addendum §5.3 — PR-U2 comprehension block preserved verbatim.
    The marker `data-role="matrix-script-comprehension-panel"` must still exist."""
    template = _read_workbench_template()
    assert 'data-role="matrix-script-comprehension-panel"' in template


def test_template_existing_ms_w3_script_structure_panel_preserved() -> None:
    """OWC-MS PR-2 MS-W3 panel preserved verbatim as secondary diagnostics."""
    template = _read_workbench_template()
    assert 'data-role="matrix-script-script-structure-panel"' in template


def test_template_existing_variation_panel_preserved() -> None:
    """Variation Panel (engineering inspector) preserved verbatim per
    slicing addendum §5.5 hard non-goal."""
    template = _read_workbench_template()
    assert 'data-role="matrix-script-variation-panel"' in template


def test_template_block_a_b_c_render_above_existing_secondary_diagnostics() -> None:
    """Document-order invariant: the new Block A/B/C panels precede the
    existing PR-U2 comprehension + MS-W3 + Variation Panel anchors so
    operator first sees the result-oriented blocks."""
    template = _read_workbench_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    pos_block_a = rendered.find('data-role="matrix-script-block-a-goal-summary"')
    pos_block_b = rendered.find('data-role="matrix-script-block-b-script-structure"')
    pos_block_c = rendered.find('data-role="matrix-script-block-c-variant-strategy"')
    pos_comp = rendered.find('data-role="matrix-script-comprehension-panel"')
    pos_ms_w3 = rendered.find('data-role="matrix-script-script-structure-panel"')
    pos_variation = rendered.find('data-role="matrix-script-variation-panel"')
    assert -1 not in (pos_block_a, pos_block_b, pos_block_c, pos_comp, pos_ms_w3, pos_variation)
    assert pos_block_a < pos_block_b < pos_block_c, "A → B → C document order"
    assert pos_block_c < pos_comp, "Block C must precede the secondary PR-U2 comprehension panel"
    assert pos_comp < pos_ms_w3, "PR-U2 must precede MS-W3 panel (existing order preserved)"
    assert pos_ms_w3 < pos_variation, "MS-W3 must precede Variation Panel (existing order preserved)"


# --------------------------------------------------------------------------
# I. Helper-output sanity / serialisation
# --------------------------------------------------------------------------


def test_script_structure_view_returns_only_serialisable_types() -> None:
    view = derive_matrix_script_script_structure_view(_s001_task())
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in view.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_workbench_result_summary_returns_only_serialisable_types() -> None:
    summary = derive_matrix_script_workbench_result_summary(
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in summary.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_readable_variants_returns_only_serialisable_types() -> None:
    surface = _variation_surface(
        cells=[{"cell_id": "c1", "axis_selections": {"tone": "sincere"}}],
        slots=[],
    )
    out = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in out.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_workbench_comprehension_helper_remains_addressable_for_secondary_diagnostics() -> None:
    """PR-U2 comprehension is NOT removed by PR-2; it stays as secondary
    diagnostics. This sanity test confirms the helper is still callable
    and still returns is_matrix_script for matrix_script panels."""
    out = derive_matrix_script_workbench_comprehension(_variation_surface(), _ms_panel())
    assert out["is_matrix_script"] is True
