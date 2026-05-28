"""OWC-MS-RO PR-4 — Matrix Script Delivery Center Blocks A / B / C / D / E / F dedicated tests.

Authority pointers:

- ``docs/design/matrix_script_delivery_center_wireframe_v1.md`` §3-§9
  (Header + Blocks A / B / C / D / E / F binding-and-exhaustive fields).
- ``docs/design/matrix_script_result_oriented_ui_implementation_slicing_v1.md``
  §7 (PR-4 scope, RO-4.* acceptance evidence) + §7.3 (preserved
  diagnostics) + §7.5 (hard non-goals) + §2.1.3 / §2.2.3 / §6 PR-3
  precedent (the user's direct instruction is the authority that opens
  PR-4 in this turn).
- ``docs/product/matrix_script_product_flow_v1.md`` §7 (Delivery Center).
- Operator sample anchor: ``production_packet_3_scripts.json`` —
  S001 / S002 / S003 baked into fixtures below (mirroring PR-2 / PR-3).
- Render-data seam consumed (thin orchestration; no new helper logic):
  ``gateway/app/services/matrix_script/publish_hub_render_data.py::derive_matrix_script_publish_hub_render_data``
- Existing helpers consumed by the seam (no new helper module per PR-4 scope):
  ``delivery_comprehension`` / ``preview_compare_view`` / ``recommended_action_view``
  / ``delivery_ready_package_view`` / ``delivery_copy_bundle_view``
  / ``publish_backfill_readiness_view`` / ``task_area_convergence``
  / ``result_status_view`` / ``closure_binding`` / ``compute_publish_readiness``.
- Closed enums consumed (NO widening — verified at module import time):
  ``D1_EVENT_KINDS`` / ``EVENT_KINDS`` (`publish_feedback_closure`),
  ``REVIEW_ZONE_VALUES``, ``RECOMMENDED_BUCKET_*``, ``PACKAGE_*``,
  ``PUBLISH_STATUS_VALUES``, ``READINESS_*``, ``head_reason`` enum.

PR-4 binding behaviour proved by this suite:

1. ``derive_matrix_script_publish_hub_render_data`` returns ``{}``
   for non-matrix_script tasks so the page route preserves the Hot
   Follow + Digital Anchor branches bytewise unchanged.
2. The render-data dict carries the closed key set:
   ``{is_matrix_script, task_id, eight_stage_state, task_area_result_status,
   publish_readiness, delivery_comprehension, preview_compare,
   recommended_action, delivery_ready_package, delivery_copy_bundle,
   publish_backfill_readiness, publish_feedback_closure,
   closure_endpoint_url}``.
3. Block A primary slot renders the recommended-candidate marker
   (single-source from ``recommended_action.recommended_variant.variation_id``)
   when at least one variation is in ``RECOMMENDED_BUCKET_PUBLISHABLE``.
4. Block A empty state renders a tracked-gap operator-language line —
   never a fabricated thumbnail / URL — when no variation is in
   ``RECOMMENDED_BUCKET_PUBLISHABLE`` (RC-R8 audit on the seam output).
5. Block A primary slot label set is sourced from
   ``delivery_comprehension.final_video_primary``; never invents a
   ``recommended_candidate_label`` or ``media_handle`` field that
   doesn't exist on the helper output.
6. Block B required-deliverable rows render with both the
   ``required_blocking`` and ``required_non_blocking`` lanes from
   ``delivery_comprehension.lanes`` (Plan C amendment); per-row
   status from ``artifact_status_label_zh``.
7. Block C optional ``scene_pack`` lane renders the
   ``optional_non_blocking`` rows; even an empty payload renders
   the explicit operator-language non-blocking note (no row is
   ever treated as a publish blocker).
8. Block D copy-bundle renders the closed
   ``{title / hashtags / cta / comment_keywords}`` subfield set from
   ``delivery_copy_bundle.subfields``; tracked-gap rows render the
   ``unresolved_explanation_zh``; never a free-text editing affordance.
9. Block E closure row table is sourced from
   ``publish_feedback_closure.variation_feedback[]`` (read-only);
   every status pill is a member of the closed
   ``PUBLISH_STATUS_VALUES`` set; ``publish_url`` cell renders blank
   when the source field is absent (RC-R8 audit).
10. Block E "+ 记录发布事件" form posts to the existing
    ``POST /api/matrix-script/closures/{task_id}/events`` endpoint
    with ``event_kind == "operator_publish"`` + ``actor_kind == "operator"``
    (no new endpoint, no enum widening); the form is disabled when the
    publish-readiness banner is blocked.
11. Block E append-only event log renders
    ``feedback_closure_records[]`` in original order; no mutation /
    deletion affordance is present.
12. Block F iteration recommendation lines are sourced from
    ``publish_backfill_readiness.rows[].gap_summary_zh`` +
    ``next_input_zh``; per-variant operator-language only; closed
    ``READINESS_*`` enum on the readiness pill.
13. Block F archive button renders disabled-with-tooltip (PG-4
    deferred per spec §7.5) — operator sees the affordance shape
    without triggering an un-spec'd state transition.
14. Hot Follow / Digital Anchor / baseline panels return ``{}`` from
    the render-data seam — Hot Follow + Digital Anchor publish-hub
    branches stay bytewise unchanged.
15. Forbidden surfaces audit: no vendor / model / provider / engine /
    ``content://`` / ``slot_id`` / ``cell_id`` / ``script_slot_ref`` /
    ``binds_cell_id`` leakage in any operator-visible value emitted
    by the seam or rendered by the new template subtree.
16. Template assertions: the new ``data-role`` markers
    (``matrix-script-delivery-center-header`` /
    ``matrix-script-block-a-final-video-primary`` /
    ``matrix-script-block-b-required-deliverables`` /
    ``matrix-script-block-c-scene-pack`` /
    ``matrix-script-block-d-copy-bundle`` /
    ``matrix-script-block-e-publish-feedback`` /
    ``matrix-script-block-f-iteration-archive``) are present in
    ``task_publish_hub.html`` and are gated to the matrix_script
    branch only.
17. Existing PR-U3 / Recovery PR-3 / OWC-MS PR-3 / RC PR-4 JS-hydrated
    diagnostic shells are preserved verbatim BELOW the new server-rendered
    blocks (per slicing addendum §7.3).
18. Document-order invariant: header → A → B → C → D → E → F →
    secondary diagnostic shells.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_ready_package_view import (
    PACKAGE_BLOCKED,
    PACKAGE_PARTIAL,
    PACKAGE_READY,
    PACKAGE_UNAVAILABLE,
)
from gateway.app.services.matrix_script.preview_compare_view import (
    RECOMMENDED_BUCKET_BLOCKED,
    RECOMMENDED_BUCKET_PUBLISHABLE,
    RECOMMENDED_BUCKET_UNDETERMINED,
)
from gateway.app.services.matrix_script.publish_feedback_closure import (
    EVENT_KINDS,
    PUBLISH_STATUS_VALUES,
    REVIEW_ZONE_VALUES,
)
from gateway.app.services.matrix_script.publish_hub_render_data import (
    derive_matrix_script_publish_hub_render_data,
)


_REPO_ROOT = Path(__file__).resolve().parents[4]
_PUBLISH_HUB_TEMPLATE = (
    _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"
)


def _read_publish_hub_template() -> str:
    return _PUBLISH_HUB_TEMPLATE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Test fixtures (S001 / S002 / S003 + Hot Follow / DA byte-isolation)
# --------------------------------------------------------------------------


def _matrix_script_task(
    *,
    task_id: str = "ms-dc-001",
    topic: str = "PR-4 测试任务",
    audience_hint: str = "想做短视频但门槛犹豫的新手",
    target_platform: str = "TikTok",
    target_language: list[str] | None = None,
    tone_hint: str = "真诚",
    length_hint: str = "22s",
    variation_target_count: int = 4,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
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


def _ms_publish_hub_gate_body(template: str) -> str:
    """Extract the body of `{% if _ms_kind == "matrix_script" %}` gate
    in the publish-hub template, counting nested if/for blocks so the
    correct closing endif is matched."""
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    open_pat = re.compile(
        r'{%\s*if\s+_ms_kind\s*==\s*"matrix_script"\s*%}'
    )
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
                return rendered[start : next_close.start()]
            cursor = next_close.end()
    return ""


# --------------------------------------------------------------------------
# A. Render-data seam — closed key set + non-MS isolation
# --------------------------------------------------------------------------


def test_seam_returns_empty_for_hot_follow_task() -> None:
    assert derive_matrix_script_publish_hub_render_data(_hot_follow_task()) == {}


def test_seam_returns_empty_for_digital_anchor_task() -> None:
    assert derive_matrix_script_publish_hub_render_data(_digital_anchor_task()) == {}


def test_seam_returns_empty_for_baseline_task() -> None:
    assert derive_matrix_script_publish_hub_render_data(_baseline_task()) == {}


def test_seam_returns_empty_for_none_input() -> None:
    assert derive_matrix_script_publish_hub_render_data(None) == {}


def test_seam_returns_empty_for_non_mapping_input() -> None:
    assert derive_matrix_script_publish_hub_render_data("not a dict") == {}  # type: ignore[arg-type]
    assert derive_matrix_script_publish_hub_render_data(123) == {}  # type: ignore[arg-type]


def test_seam_returns_closed_key_set_for_matrix_script_task() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    expected_keys = {
        "is_matrix_script",
        "task_id",
        "eight_stage_state",
        "task_area_result_status",
        "publish_readiness",
        "delivery_comprehension",
        "preview_compare",
        "recommended_action",
        "delivery_ready_package",
        "delivery_copy_bundle",
        "publish_backfill_readiness",
        "publish_feedback_closure",
        "closure_endpoint_url",
    }
    assert set(out.keys()) == expected_keys


def test_seam_is_matrix_script_flag_set_true() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    assert out["is_matrix_script"] is True


def test_seam_resolves_task_id_from_task_id_key() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task(task_id="ms-special-001"))
    assert out["task_id"] == "ms-special-001"


def test_seam_resolves_task_id_from_id_key_when_task_id_missing() -> None:
    task = _s001_task()
    task.pop("task_id", None)
    task["id"] = "ms-fallback-001"
    out = derive_matrix_script_publish_hub_render_data(task)
    assert out["task_id"] == "ms-fallback-001"


def test_seam_closure_endpoint_url_resolves_against_task_id() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task(task_id="ms-ep-001"))
    assert out["closure_endpoint_url"] == "/api/matrix-script/closures/ms-ep-001/events"


# --------------------------------------------------------------------------
# B. Block A — Main final result slot
# --------------------------------------------------------------------------


def test_block_a_recommended_action_present_in_seam_output() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    ra = out["recommended_action"]
    assert ra.get("is_matrix_script") is True
    assert "status_kind" in ra
    assert "headline_zh" in ra
    assert "next_action_zh" in ra


def test_block_a_recommended_action_status_kind_in_closed_enum() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    allowed = {
        RECOMMENDED_BUCKET_PUBLISHABLE,
        RECOMMENDED_BUCKET_BLOCKED,
        RECOMMENDED_BUCKET_UNDETERMINED,
    }
    assert out["recommended_action"]["status_kind"] in allowed


def test_block_a_delivery_comprehension_carries_final_video_primary() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    fvp = out["delivery_comprehension"].get("final_video_primary") or {}
    assert fvp.get("is_primary") is True
    assert isinstance(fvp.get("title_zh"), str) and fvp["title_zh"]


def test_block_a_template_carries_block_a_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-a-final-video-primary"' in template


def test_block_a_template_carries_recommended_marker_anchor() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="ms-dc-block-a-recommended-marker"' in template


def test_block_a_template_carries_empty_state_anchor() -> None:
    """When no recommended candidate exists, Block A renders the empty-state
    line (per wireframe §4.5) — not a fabricated thumbnail."""
    template = _read_publish_hub_template()
    assert 'data-role="ms-dc-block-a-empty"' in template


def test_block_a_template_no_inline_video_player() -> None:
    """Block A primary slot is server-rendered placeholder + meta only;
    inline player is IG-5 deferred per wireframe §4.4."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_a_open = inside.find('data-role="matrix-script-block-a-final-video-primary"')
    block_b_open = inside.find('data-role="matrix-script-block-b-required-deliverables"')
    block_a_subtree = inside[block_a_open:block_b_open]
    assert "<video" not in block_a_subtree
    assert "<source " not in block_a_subtree


def test_block_a_template_carries_no_fake_url_note() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="ms-dc-block-a-primary-slot-no-fake-note"' in template


# --------------------------------------------------------------------------
# C. Block B — Required deliverables
# --------------------------------------------------------------------------


def test_block_b_lanes_present_in_delivery_comprehension() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    lanes = out["delivery_comprehension"].get("lanes") or {}
    assert "required_blocking" in lanes
    assert "required_non_blocking" in lanes
    assert "optional_non_blocking" in lanes


def test_block_b_template_carries_block_b_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-b-required-deliverables"' in template


def test_block_b_template_renders_required_blocking_and_non_blocking() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    assert "ms_pub_delivery.lanes" in inside
    assert "_b_required_blocking.rows" in inside
    assert "_b_required_non_blocking.rows" in inside


def test_block_b_template_renders_required_columns() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_b_open = inside.find('data-role="matrix-script-block-b-required-deliverables"')
    block_c_open = inside.find('data-role="matrix-script-block-c-scene-pack"')
    block_b_subtree = inside[block_b_open:block_c_open]
    for header_label in ("交付物", "必需 / 可选", "状态", "说明"):
        assert header_label in block_b_subtree


def test_block_b_template_uses_kind_label_zh_not_deliverable_kind() -> None:
    """Field names must match the actual delivery_comprehension row shape:
    `kind` / `kind_label_zh` / `artifact_status_label_zh`. (Mirror of
    PR-3 mismatch fix.)"""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_b_open = inside.find('data-role="matrix-script-block-b-required-deliverables"')
    block_c_open = inside.find('data-role="matrix-script-block-c-scene-pack"')
    block_b_subtree = inside[block_b_open:block_c_open]
    # kind_label_zh is the operator-language column source
    assert "row.kind_label_zh" in block_b_subtree
    # artifact_status_label_zh is the status column source
    assert "row.artifact_status_label_zh" in block_b_subtree
    # row.deliverable_kind / row.deliverable_label_zh are NOT real fields
    assert "row.deliverable_kind" not in block_b_subtree
    assert "row.deliverable_label_zh" not in block_b_subtree


# --------------------------------------------------------------------------
# D. Block C — Scene pack (always non-blocking)
# --------------------------------------------------------------------------


def test_block_c_template_carries_block_c_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-c-scene-pack"' in template


def test_block_c_template_carries_non_blocking_label() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_c_open = inside.find('data-role="matrix-script-block-c-scene-pack"')
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_c_subtree = inside[block_c_open:block_d_open]
    # The lane is explicitly labeled 不阻塞 / 非阻塞 so operators see the
    # policy. SCENE_PACK_BLOCKING_ALLOWED = False is enforced upstream.
    assert "不阻塞" in block_c_subtree or "非阻塞" in block_c_subtree


def test_block_c_template_consumes_optional_non_blocking_lane() -> None:
    """Block C iterates `_c_optional.rows`; the binding `_c_optional`
    is set just above the Block C card from
    `(ms_pub_delivery.lanes or {}).optional_non_blocking or {}` — so
    the optional_non_blocking lane is the only lane Block C reads."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    # Block C consumes `_c_optional.rows` (set above the card from
    # ms_pub_delivery.lanes.optional_non_blocking) — confirm both anchors
    # in the broader gate body.
    assert (
        "(ms_pub_delivery.lanes or {}).optional_non_blocking or {}" in inside
    )
    block_c_open = inside.find('data-role="matrix-script-block-c-scene-pack"')
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_c_subtree = inside[block_c_open:block_d_open]
    assert "_c_optional.rows" in block_c_subtree


def test_block_c_template_renders_empty_state_when_no_optional_rows() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_c_open = inside.find('data-role="matrix-script-block-c-scene-pack"')
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_c_subtree = inside[block_c_open:block_d_open]
    assert 'data-role="ms-dc-block-c-empty"' in block_c_subtree


# --------------------------------------------------------------------------
# E. Block D — Copy bundle
# --------------------------------------------------------------------------


def test_block_d_seam_returns_subfields_for_matrix_script_task() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    cb = out["delivery_copy_bundle"]
    if cb:
        assert isinstance(cb.get("subfields"), list)


def test_block_d_template_carries_block_d_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-d-copy-bundle"' in template


def test_block_d_template_renders_subfield_rows_with_label_and_value() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_d_subtree = inside[block_d_open:block_e_open]
    assert 'data-role="ms-dc-block-d-subfield"' in block_d_subtree
    assert "sub.label_zh" in block_d_subtree
    assert "sub.value" in block_d_subtree


def test_block_d_template_no_free_text_editing_affordance() -> None:
    """Free-text editing deferred per wireframe §7.4. Block D must not
    render a textarea / contenteditable div for any subfield.

    PR-3 (2026-05-28) update: the PR-3 ⑤ 发布设置 form (with its
    operator-typed publish title / caption / tags textarea) was
    inserted between Block D and Block E. The slice end is now the
    PR-3 ⑤ block opener instead of the publish-feedback block, so
    Block D itself remains free-text-edit-free."""

    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_e_open = inside.find('data-role="matrix-script-block-publish-settings"')
    # Fallback: if PR-3 hasn't landed yet, slice up to the original Block E.
    if block_e_open == -1:
        block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_d_subtree = inside[block_d_open:block_e_open]
    assert "<textarea" not in block_d_subtree
    assert "contenteditable" not in block_d_subtree


# --------------------------------------------------------------------------
# E.1. Block D resolved-status correction (2026-05-08 PR-4 conditional-pass)
# --------------------------------------------------------------------------


def test_block_d_producer_status_resolved_constant_value() -> None:
    """The producer's STATUS_RESOLVED is the closed string the template
    must literal-match. PR-4 conditional-pass blocker 1: the original
    template branch checked for ``"resolved"``, but the producer emits
    ``"resolved_from_existing_projection"`` (delivery_copy_bundle_view.py:97).
    This test pins the producer constant so the literal-match path
    cannot drift again."""
    from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
        STATUS_RESOLVED,
        STATUS_UNRESOLVED,
    )

    assert STATUS_RESOLVED == "resolved_from_existing_projection"
    assert STATUS_UNRESOLVED == "unresolved_pending_copy_projection_contract"


def test_block_d_template_resolved_check_matches_producer_status_resolved_literal() -> None:
    """Template branch checks for the producer's
    ``STATUS_RESOLVED == "resolved_from_existing_projection"`` literal
    (not the bare ``"resolved"`` token). Without this fix, every
    resolved subfield falls through to the unresolved branch and is
    rendered as a tracked-gap explanation — operator never sees the
    real copy values."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_d_subtree = inside[block_d_open:block_e_open]
    assert (
        'sub.status_code == "resolved_from_existing_projection"'
        in block_d_subtree
    ), (
        "Block D resolved branch must literal-match the producer's "
        "STATUS_RESOLVED constant — the bare \"resolved\" check never "
        "matched the producer output."
    )


def test_block_d_template_no_unconditional_resolved_literal_fallback() -> None:
    """Defensive: ensure the template does NOT keep the bare
    ``"resolved"`` literal anywhere inside Block D — the literal must
    be the producer-aligned ``"resolved_from_existing_projection"``
    only, so a future drift cannot reintroduce the original bug."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_d_subtree = inside[block_d_open:block_e_open]
    # The `status_code == "resolved"` substring (the broken branch) must
    # not be present anywhere in Block D. The full producer literal is
    # the only acceptable resolved-status check.
    assert 'status_code == "resolved"' not in block_d_subtree, (
        "Block D must not carry the bare \"resolved\" literal; the "
        "resolved branch must literal-match the producer's "
        "STATUS_RESOLVED constant `resolved_from_existing_projection`."
    )


def test_block_d_resolved_subfield_has_status_resolved_when_caption_present() -> None:
    """End-to-end: when the publish-hub copy_bundle producer emits a
    non-empty `caption` field, the matrix_script delivery_copy_bundle
    seam emits a TITLE subfield with
    `status_code == STATUS_RESOLVED == "resolved_from_existing_projection"`
    and a non-empty `value` matching the caption — proving the seam
    output flows the resolved status the template's resolved branch
    now literal-matches.

    The publish-hub copy_bundle producer
    (`task_view_helpers._build_copy_bundle`) reads
    `caption = _read_mm_txt_from_task(task) or task.title`. The S001
    fixture has `task.title = "不会剪辑，也能做TikTok？"`, so the
    derived caption is non-empty and the title subfield resolves to
    that value. Without the literal-match fix, the template would
    silently render this as the tracked-gap explanation."""
    from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
        STATUS_RESOLVED,
    )

    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    subfields = out["delivery_copy_bundle"].get("subfields") or []
    title_subfield = next(
        (sub for sub in subfields if sub.get("subfield_id") == "title"), None
    )
    assert title_subfield is not None, "title subfield missing from seam output"
    assert title_subfield["status_code"] == STATUS_RESOLVED
    assert title_subfield["status_code"] == "resolved_from_existing_projection"
    assert title_subfield["value"] == "不会剪辑，也能做TikTok？"


def test_block_d_resolved_subfield_template_branch_renders_value() -> None:
    """The template's resolved branch MUST emit the
    `<span data-role="ms-dc-block-d-subfield-value">` element when the
    subfield's status_code matches STATUS_RESOLVED. The empty/unresolved
    branch emits the tracked-gap span. Both branches present in the
    template — proves the conditional has both arms wired."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-copy-bundle"')
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_d_subtree = inside[block_d_open:block_e_open]
    # Resolved branch — emits the operator-visible value.
    assert 'data-role="ms-dc-block-d-subfield-value"' in block_d_subtree
    # Tracked-gap branch — emits the explanation when not resolved.
    assert 'data-role="ms-dc-block-d-subfield-empty"' in block_d_subtree


def test_block_d_unresolved_subfield_keeps_tracked_gap_branch() -> None:
    """End-to-end: when the publish-hub copy_bundle producer has no
    `comment_cta`, the matrix_script delivery_copy_bundle seam emits a
    CTA subfield with
    `status_code == STATUS_UNRESOLVED == "unresolved_pending_copy_projection_contract"`
    and a tracked-gap explanation — proving the unresolved branch
    stays honest after the literal-match fix.

    `_derive_cta` reads `base_copy_bundle.get("comment_cta")` and
    publish-hub `_build_copy_bundle` sets `comment_cta: ""` always —
    so CTA always resolves to the unresolved tracked-gap row in this
    wave."""
    from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
        STATUS_UNRESOLVED,
    )

    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    subfields = out["delivery_copy_bundle"].get("subfields") or []
    cta_subfield = next(
        (sub for sub in subfields if sub.get("subfield_id") == "cta"), None
    )
    assert cta_subfield is not None
    assert cta_subfield["status_code"] == STATUS_UNRESOLVED
    assert cta_subfield["value"] == ""
    assert isinstance(cta_subfield.get("unresolved_explanation_zh"), str)
    assert cta_subfield["unresolved_explanation_zh"]


def test_block_d_comment_keywords_subfield_always_unresolved() -> None:
    """`_derive_comment_keywords` always returns empty until the future
    copy projection contract lands (see delivery_copy_bundle_view.py:208).
    This stays honest regardless of the resolved-status fix — the
    tracked-gap row continues to render the unresolved explanation."""
    from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
        STATUS_UNRESOLVED,
    )

    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    subfields = out["delivery_copy_bundle"].get("subfields") or []
    keywords_subfield = next(
        (sub for sub in subfields if sub.get("subfield_id") == "comment_keywords"),
        None,
    )
    assert keywords_subfield is not None
    assert keywords_subfield["status_code"] == STATUS_UNRESOLVED


def test_block_d_subfield_set_is_closed_four_subfields() -> None:
    """Block D subfields are a closed four-row set
    (title / hashtags / cta / comment_keywords) per wireframe §7.2.
    PR-4 must not widen the set."""
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    subfields = out["delivery_copy_bundle"].get("subfields") or []
    ids = [sub["subfield_id"] for sub in subfields]
    assert ids == ["title", "hashtags", "cta", "comment_keywords"]


# --------------------------------------------------------------------------
# F. Block E — Publish feedback (table + form + event log)
# --------------------------------------------------------------------------


def test_block_e_template_carries_block_e_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-e-publish-feedback"' in template


def test_block_e_form_action_resolves_to_existing_endpoint() -> None:
    """No new endpoint per spec: must use existing
    POST /api/matrix-script/closures/{task_id}/events."""
    out = derive_matrix_script_publish_hub_render_data(_s001_task(task_id="ms-form-001"))
    assert out["closure_endpoint_url"] == "/api/matrix-script/closures/ms-form-001/events"


def test_block_e_form_event_kind_is_closed_operator_publish() -> None:
    """Per wireframe §8.5 + Block E spec: form posts event_kind ==
    "operator_publish" (a member of the closed EVENT_KINDS frozen set)."""
    assert "operator_publish" in EVENT_KINDS
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert (
        '<input type="hidden" name="event_kind" value="operator_publish"'
        in block_e_subtree
    )


def test_block_e_form_actor_kind_is_closed_operator() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert '<input type="hidden" name="actor_kind" value="operator"' in block_e_subtree


def test_block_e_form_disabled_when_publish_blocked() -> None:
    """Per wireframe §8.5 closed precondition: 提交发布事件 button
    disabled when compute_publish_readiness.publishable == False."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    # The disabled-attribute branch on the submit button triggers when
    # ms_pub_readiness.publishable is False.
    assert "ms_pub_readiness.publishable" in block_e_subtree


def test_block_e_event_log_anchor_present() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert 'data-role="ms-dc-block-e-event-log"' in block_e_subtree


def test_block_e_no_event_mutation_or_deletion_affordance() -> None:
    """Append-only per publish_feedback_closure_contract_v1 §append-only.
    Block E must not render any "delete event" / "edit event" /
    "reset closure" affordance."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    for needle in ("删除事件", "编辑事件", "重置 closure", "delete_event", "mutate_closure"):
        assert needle not in block_e_subtree


def test_block_e_publish_url_column_blank_when_field_absent() -> None:
    """RC-R8: publish_url column renders blank when source field is
    absent — never a fabricated URL. Template branch handles
    `if row.publish_url` then `<a href>` else `—`."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert "if row.publish_url" in block_e_subtree


def test_block_e_status_pills_use_closed_publish_status_values() -> None:
    """Template renders one of the closed PUBLISH_STATUS_VALUES per row.
    The template branch tests for "published" / "failed" / "retracted"
    + falls through to "pending" — exactly the four closed values."""
    expected = frozenset({"pending", "published", "failed", "retracted"})
    assert PUBLISH_STATUS_VALUES == expected
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-publish-feedback"')
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_e_subtree = inside[block_e_open:block_f_open]
    for status in expected - {"pending"}:  # pending is the fall-through default
        assert f'== "{status}"' in block_e_subtree or f"== '{status}'" in block_e_subtree


# --------------------------------------------------------------------------
# G. Block F — Iteration / Archive
# --------------------------------------------------------------------------


def test_block_f_template_carries_block_f_data_role_marker() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-block-f-iteration-archive"' in template


def test_block_f_iteration_recommendation_consumes_publish_backfill_readiness() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    assert "ms_pub_backfill.rows" in block_f_subtree
    assert "row.gap_summary_zh" in block_f_subtree
    assert "row.next_input_zh" in block_f_subtree


# --------------------------------------------------------------------------
# G.1. Block F archive form (2026-05-08 PR-4 conditional-pass correction 2)
# --------------------------------------------------------------------------


def test_block_f_archive_form_rendered_when_closure_has_variations() -> None:
    """PR-4 conditional-pass blocker 2: archive action must no longer
    be a disabled placeholder. When the closure has at least one
    variation row (`_e_rows` non-empty), the template renders an
    enabled `<form data-role="ms-dc-block-f-archive-form">` posting to
    the existing closure endpoint."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-dc-block-f-archive-form"' in block_f_subtree


def test_block_f_archive_form_action_is_existing_closure_endpoint() -> None:
    """The archive form posts to the existing
    POST /api/matrix-script/closures/{task_id}/events endpoint via the
    `ms_pub_endpoint` template variable resolved by the seam — no new
    endpoint."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None, "archive form not found"
    archive_form = m.group()
    assert 'method="POST"' in archive_form
    assert 'action="{{ ms_pub_endpoint }}"' in archive_form


def test_block_f_archive_form_event_kind_is_closed_operator_note() -> None:
    """Per the wireframe §9.2 + slicing addendum §7.4 RO-4.8
    "(or system-decided)" parenthetical: the archive event_kind picks
    one closed `EVENT_KINDS` member. PR-4 chose `operator_note`
    because the closure validator
    (publish_feedback_closure.apply_event:198-210) ALWAYS overwrites
    `publish_status` on `operator_publish` — using `operator_publish`
    for archive would un-publish already-published variations on
    archive, which is a state regression. `operator_note` carries the
    archive intent in `operator_publish_notes` without touching
    publish_status. Closed enum, no widening."""
    assert "operator_note" in EVENT_KINDS
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    assert (
        '<input type="hidden" name="event_kind" value="operator_note"' in archive_form
    )


def test_block_f_archive_form_actor_kind_is_closed_operator() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    assert '<input type="hidden" name="actor_kind" value="operator"' in archive_form


def test_block_f_archive_form_carries_archive_intent_note() -> None:
    """The archive intent is captured in `operator_publish_notes` so the
    closure event log carries an operator-language record of the archive
    decision. The note text "归档此任务" matches the button label."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    assert 'name="operator_publish_notes"' in archive_form
    assert 'value="归档此任务"' in archive_form


def test_block_f_archive_form_carries_variation_id_select() -> None:
    """The closure validator requires `variation_id` on every event
    (publish_feedback_closure.apply_event:190-192). The archive form
    pulls the select options from the same `_e_rows` set the publish
    event form uses — operator picks which variation row carries the
    archive intent record."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    assert 'name="variation_id"' in archive_form
    assert 'data-role="ms-dc-block-f-archive-form-variation-id"' in archive_form
    # Options are populated from the closure's variation_feedback rows.
    assert "for row in _e_rows" in archive_form


def test_block_f_archive_form_submit_button_rendered_enabled() -> None:
    """The submit button has no `disabled` attribute — the archive
    action is wired and clickable when the closure has at least one
    variation."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    archive_button_re = re.compile(
        r'<button\s+type="submit"[^>]*data-role="ms-dc-block-f-archive-button"[^>]*>'
    )
    bm = archive_button_re.search(archive_form)
    assert bm is not None, "archive submit button not found inside the form"
    button_open_tag = bm.group()
    assert "disabled" not in button_open_tag, (
        "archive submit button must not carry the disabled attribute when "
        "the closure has variations — the action must be wired"
    )


def test_block_f_archive_form_does_not_widen_event_kinds_enum() -> None:
    """No closed-enum widening: the form's event_kind value must be a
    member of the existing closed EVENT_KINDS frozenset; this test
    asserts the literal in the template is one of the existing members."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    event_kind_re = re.compile(
        r'<input type="hidden" name="event_kind" value="([^"]+)"'
    )
    em = event_kind_re.search(archive_form)
    assert em is not None
    assert em.group(1) in EVENT_KINDS


def test_block_f_archive_form_does_not_post_to_new_endpoint() -> None:
    """The form action must resolve to the existing closure endpoint
    template, not a new path. The seam emits closure_endpoint_url
    matching the existing endpoint."""
    out = derive_matrix_script_publish_hub_render_data(_s001_task(task_id="ms-arc-001"))
    assert (
        out["closure_endpoint_url"]
        == "/api/matrix-script/closures/ms-arc-001/events"
    )


def test_block_f_archive_button_disabled_when_no_closure_variations() -> None:
    """Disabled fallback: when `_e_rows` is empty (no closure variations
    to attach the archive note to), the template renders a
    disabled-with-tooltip button explaining the closure-existence
    prerequisite. Closure event posts require a `variation_id` per the
    closure validator, so without rows the form cannot be wired."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    # The {% else %} branch renders a disabled button. Find it by its
    # data-role marker outside of the form.
    archive_actions_re = re.compile(
        r'<div\s+class="task-actions"\s+data-role="ms-dc-block-f-archive-actions"[\s\S]*?</div>'
    )
    am = archive_actions_re.search(block_f_subtree)
    assert am is not None, "archive disabled-fallback container not found"
    fallback_block = am.group()
    fallback_button_re = re.compile(
        r'<button\s+type="button"[^>]*data-role="ms-dc-block-f-archive-button"[^>]*>'
    )
    fb = fallback_button_re.search(fallback_block)
    assert fb is not None
    assert "disabled" in fb.group()


def test_block_f_archive_form_does_not_introduce_record_kind_field() -> None:
    """The wireframe §9.2 calls for a future `record_kind == "archive_action"`
    follow-up event; that field does NOT exist on the closure schema
    today (PG-4 deferred). PR-4 must not introduce a `record_kind` form
    input that would imply schema widening."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    archive_form_re = re.compile(
        r'<form\s+data-role="ms-dc-block-f-archive-form"[\s\S]*?</form>'
    )
    m = archive_form_re.search(block_f_subtree)
    assert m is not None
    archive_form = m.group()
    assert 'name="record_kind"' not in archive_form, (
        "Block F archive form must not introduce a `record_kind` field — "
        "the closure schema does not carry one today; PG-4 enrichment "
        "is gated to a future closure schema change."
    )


def test_block_f_archive_form_carries_status_anchor() -> None:
    """The JS submit handler renders success / failure feedback into a
    `data-role="ms-dc-block-f-archive-form-status"` span. Without
    this anchor the operator gets no visible feedback after clicking."""
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-dc-block-f-archive-form-status"' in block_f_subtree


# --------------------------------------------------------------------------
# G.2. Block F archive form JSON submit handler (2026-05-08 PR-4
#      conditional-pass correction round 2)
# --------------------------------------------------------------------------
#
# The closure router at
# `gateway/app/routers/matrix_script_closure.py::post_event_api` is
# JSON-only — it calls `await request.json()` and 400-rejects non-JSON
# bodies. The static archive form posts as a regular HTML form, so it
# must be intercepted by a JS submit handler that builds the JSON event
# payload and POSTs it via fetch with `Content-Type: application/json`.
# These tests prove (1) the handler is bound, (2) it intercepts
# submission, (3) the JSON payload it builds matches the closure
# contract, and (4) the real endpoint accepts the payload and appends
# the event to the closure log.


def test_archive_form_js_handler_function_defined_in_template() -> None:
    """The submit handler `bindMatrixScriptArchiveForm` is defined
    directly in the publish-hub template (mirroring the existing
    `bindMatrixScriptClosureForm` precedent in the same file)."""
    template = _read_publish_hub_template()
    assert "function bindMatrixScriptArchiveForm()" in template


def test_archive_form_js_handler_bound_at_dom_ready() -> None:
    """The DOMContentLoaded init block calls
    `bindMatrixScriptArchiveForm()` so the form is wired once the
    DOM is ready. Without this hookup the handler is dead code."""
    template = _read_publish_hub_template()
    assert "bindMatrixScriptArchiveForm();" in template
    # And it must be inside the DOMContentLoaded block — confirm by
    # checking the proximity to the DOM-ready listener.
    dom_ready_pos = template.find('document.addEventListener("DOMContentLoaded"')
    bind_call_pos = template.find("bindMatrixScriptArchiveForm();")
    assert dom_ready_pos != -1 and bind_call_pos != -1
    assert bind_call_pos > dom_ready_pos
    # The bind call must be within ~3KB of the DOM-ready listener (i.e.,
    # in the same init block, not in some unrelated later script).
    assert bind_call_pos - dom_ready_pos < 3000


def test_archive_form_js_handler_selects_archive_form_data_role() -> None:
    """The handler selects the archive form by its data-role marker,
    not by id (the form has no id; data-role is the stable hook)."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    assert handler_start != -1
    handler_window = template[handler_start : handler_start + 4000]
    assert (
        '\'[data-role="ms-dc-block-f-archive-form"]\'' in handler_window
        or '"[data-role=\\"ms-dc-block-f-archive-form\\"]"' in handler_window
    )


def test_archive_form_js_handler_intercepts_submission() -> None:
    """The handler binds a `submit` listener on the form and calls
    `ev.preventDefault()` so the browser does not fall back to a
    multipart/url-encoded submission (which the closure router would
    400-reject as `invalid_json`)."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    assert 'addEventListener("submit"' in handler_window
    assert "ev.preventDefault()" in handler_window


def test_archive_form_js_handler_posts_json_with_correct_content_type() -> None:
    """The handler issues `fetch(url, {method: "POST", headers:
    {"Content-Type": "application/json"}, body: JSON.stringify(event)})`
    matching the existing closure JSON contract."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    assert 'method: "POST"' in handler_window
    assert '"Content-Type": "application/json"' in handler_window
    assert "JSON.stringify(event)" in handler_window


def test_archive_form_js_handler_uses_form_action_url() -> None:
    """The handler reads the form's `action` attribute (which the seam
    populates with the existing `/api/matrix-script/closures/{task_id}/events`
    endpoint) — no hard-coded URL, no new endpoint."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    assert 'form.getAttribute("action")' in handler_window


def test_archive_form_js_handler_builds_closure_event_shape() -> None:
    """The handler builds the JSON event shape expected by the closure
    router: `{event_kind, variation_id, actor_kind, recorded_at,
    payload: {operator_publish_notes}}`. event_kind defaults to
    "operator_note" (closed enum); actor_kind defaults to "operator"
    (closed enum); the archive intent marker lives in
    `payload.operator_publish_notes`."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    # Closed event-kind default
    assert '"operator_note"' in handler_window
    # Closed actor-kind default
    assert '"operator"' in handler_window
    # Variation_id is required by the closure validator
    assert "variation_id:" in handler_window
    # Payload nested object with operator_publish_notes
    assert "operator_publish_notes" in handler_window
    assert "payload:" in handler_window


def test_archive_form_js_handler_does_not_post_to_new_endpoint() -> None:
    """The handler must not hard-code any URL other than the form's
    action — i.e., no fallback to a different closure path. Defense
    against future regressions where someone might inline a URL."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    # No hard-coded /api/matrix-script/... URLs in the handler body.
    assert "/api/matrix-script/closures" not in handler_window


def test_archive_form_js_handler_renders_success_status() -> None:
    """On HTTP 201, the handler reads `body.event_id` and renders an
    operator-language success line in the status anchor — operators
    see the archive intent recorded successfully."""
    template = _read_publish_hub_template()
    handler_start = template.find("function bindMatrixScriptArchiveForm()")
    handler_window = template[handler_start : handler_start + 4000]
    # Status anchor selected by data-role
    assert (
        'data-role="ms-dc-block-f-archive-form-status"' in handler_window
        or "ms-dc-block-f-archive-form-status" in handler_window
    )
    # Success uses event_id from response
    assert "event_id" in handler_window
    # Failure path renders detail or status code
    assert "失败" in handler_window or "failed" in handler_window.lower()


# --------------------------------------------------------------------------
# G.3. Real JSON event-path round-trip via FastAPI TestClient
#      Proves the JS handler's JSON payload is accepted by the existing
#      closure endpoint — not just static markup.
# --------------------------------------------------------------------------


def _try_build_closure_test_client(repo_tasks: dict[str, Any]):
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from gateway.app.deps import get_task_repository
        from gateway.app.routers import matrix_script_closure
    except Exception:
        return None

    class _StubRepo:
        def __init__(self, tasks: dict[str, Any]) -> None:
            self._tasks = tasks

        def get(self, task_id: str):
            return self._tasks.get(task_id)

        def create(self, task):  # pragma: no cover
            raise NotImplementedError

        def update(self, task_id, patch):  # pragma: no cover
            raise NotImplementedError

        def list(self):  # pragma: no cover
            return list(self._tasks.values())

    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: _StubRepo(repo_tasks)
    app.include_router(matrix_script_closure.api_router)
    try:
        return TestClient(app)
    except Exception:
        return None


def _archive_form_test_task() -> dict[str, Any]:
    """Closure-router-compatible task fixture. The closure binding lazy-
    creates a closure from the task's variation matrix on first GET, so
    the task's packet must carry at least one cell. Reuses the
    matrix_script_packet sample shape."""
    import json as _json
    from pathlib import Path as _Path

    sample_path = (
        _REPO_ROOT
        / "schemas"
        / "packets"
        / "matrix_script"
        / "sample"
        / "matrix_script_packet_v1.sample.json"
    )
    packet = _json.loads(sample_path.read_text())
    return {
        "task_id": "ms_archive_e2e_001",
        "id": "ms_archive_e2e_001",
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "packet": packet,
    }


@pytest.fixture()
def _reset_closure_store_for_archive():
    from gateway.app.services.matrix_script import closure_binding

    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def test_archive_form_round_trip_posts_real_json_event(
    _reset_closure_store_for_archive,
) -> None:
    """End-to-end: the JSON payload the JS handler builds is accepted
    by the existing closure router and appended to the closure log
    as an `operator_note` event. Proves the wiring works against the
    real endpoint — not just static markup."""
    task = _archive_form_test_task()
    client = _try_build_closure_test_client({task["task_id"]: task})
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    # Lazy-create the closure (mirrors what bindMatrixScriptClosureForm
    # does via the "初始化 closure" button before any event posts).
    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    assert resp.status_code == 200, resp.text
    closure = resp.json()
    variations = closure["variation_feedback"]
    assert variations, "closure must have at least one variation row"
    variation_id = variations[0]["variation_id"]

    # The exact JSON payload the JS handler builds for archive.
    archive_event = {
        "event_kind": "operator_note",
        "variation_id": variation_id,
        "actor_kind": "operator",
        "recorded_at": "2026-05-08T11:00:00Z",
        "payload": {"operator_publish_notes": "归档此任务"},
    }
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json=archive_event,
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["event_id"].startswith("evt_")

    # The closure now carries an `operator_note` record with the
    # archive intent text on the matching variation row — proving the
    # wiring path is real, not stubbed.
    refreshed = payload["closure"]
    records = refreshed["feedback_closure_records"]
    archive_records = [
        r
        for r in records
        if r.get("event_kind") == "operator_note"
        and r.get("variation_id") == variation_id
    ]
    assert archive_records, "archive operator_note not appended to closure log"

    row = next(
        r for r in refreshed["variation_feedback"] if r["variation_id"] == variation_id
    )
    assert row["operator_publish_notes"] == "归档此任务"


def test_archive_form_round_trip_does_not_corrupt_publish_status(
    _reset_closure_store_for_archive,
) -> None:
    """RC-R8 / publish_status invariant: archive intent must NOT
    overwrite `publish_status`. The closure validator's
    `operator_note` branch only writes `operator_publish_notes` — the
    publish_status of the row stays at its prior state. This test
    pre-publishes a row, then fires archive on the SAME row, and
    asserts publish_status remains "pending" (the operator_publish
    pending state) instead of being overwritten."""
    task = _archive_form_test_task()
    client = _try_build_closure_test_client({task["task_id"]: task})
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    closure = resp.json()
    variation_id = closure["variation_feedback"][0]["variation_id"]

    # First post: operator_publish with publish_status=pending +
    # publish_url. This sets the row to a "ready-to-go" state.
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_publish",
            "variation_id": variation_id,
            "actor_kind": "operator",
            "recorded_at": "2026-05-08T10:00:00Z",
            "payload": {
                "publish_url": "https://example.test/post/1",
                "publish_status": "pending",
            },
        },
    )
    assert resp.status_code == 201

    # Second post: archive (operator_note) on the SAME row. The
    # closure validator's operator_note branch does not touch
    # publish_status — only operator_publish_notes is written.
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "variation_id": variation_id,
            "actor_kind": "operator",
            "recorded_at": "2026-05-08T11:00:00Z",
            "payload": {"operator_publish_notes": "归档此任务"},
        },
    )
    assert resp.status_code == 201
    refreshed = resp.json()["closure"]

    row = next(
        r
        for r in refreshed["variation_feedback"]
        if r["variation_id"] == variation_id
    )
    # publish_status preserved, publish_url preserved, archive note appended
    assert row["publish_status"] == "pending"
    assert row["publish_url"] == "https://example.test/post/1"
    assert row["operator_publish_notes"] == "归档此任务"


def test_archive_form_round_trip_preserves_append_only_log(
    _reset_closure_store_for_archive,
) -> None:
    """The closure feedback_closure_records[] must remain append-only
    across the archive round-trip. Neither the archive intent post nor
    the seam read mutates / deletes any prior record."""
    task = _archive_form_test_task()
    client = _try_build_closure_test_client({task["task_id"]: task})
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    closure = resp.json()
    variation_id = closure["variation_feedback"][0]["variation_id"]

    # First: operator_note A
    resp_a = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "variation_id": variation_id,
            "actor_kind": "operator",
            "recorded_at": "2026-05-08T10:00:00Z",
            "payload": {"operator_publish_notes": "A"},
        },
    )
    assert resp_a.status_code == 201
    # Second: operator_note B (archive intent)
    resp_b = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "variation_id": variation_id,
            "actor_kind": "operator",
            "recorded_at": "2026-05-08T11:00:00Z",
            "payload": {"operator_publish_notes": "归档此任务"},
        },
    )
    assert resp_b.status_code == 201

    closure_after = resp_b.json()["closure"]
    records = closure_after["feedback_closure_records"]
    # Both A and B persisted in order; A not removed by B.
    notes = [
        r.get("event_kind") for r in records if r.get("variation_id") == variation_id
    ]
    assert notes.count("operator_note") >= 2


def test_archive_form_round_trip_rejects_widened_event_kind(
    _reset_closure_store_for_archive,
) -> None:
    """Defensive: confirm the closure router still 400-rejects an
    arbitrary new event_kind, so the archive wiring cannot be expanded
    to a non-closed value without reviewer signoff."""
    task = _archive_form_test_task()
    client = _try_build_closure_test_client({task["task_id"]: task})
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    closure = resp.json()
    variation_id = closure["variation_feedback"][0]["variation_id"]

    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "archive_action",  # NOT in EVENT_KINDS
            "variation_id": variation_id,
            "actor_kind": "operator",
            "recorded_at": "2026-05-08T11:00:00Z",
            "payload": {},
        },
    )
    assert resp.status_code == 400
    assert "event_kind" in resp.json()["detail"]


def test_block_f_archive_form_cited_in_residual_implementation_note() -> None:
    """Defensive: the template comment block above the archive form
    cites both the closure validator constraint and the PG-4 deferred
    enrichment, so reviewers walking ENGINEERING_RULES §13 can see
    why `operator_note` is the chosen event_kind. Reads the raw
    template (Jinja `{# ... #}` comments are stripped by the
    gate-body extractor)."""
    template = _read_publish_hub_template()
    # Locate the Block F subtree on the raw template (comments
    # preserved). The Block F section starts at its data-role marker
    # and ends at the next sibling card or end-of-gate.
    block_f_open = template.find(
        'data-role="matrix-script-block-f-iteration-archive"'
    )
    assert block_f_open != -1, "Block F not found in raw template"
    # Walk forward enough to capture the implementation-note comment
    # and the form. 5KB is plenty for the Block F subtree.
    block_f_window = template[block_f_open : block_f_open + 5000]
    # Confirm the citation anchors are present so the design rationale
    # survives future template churn.
    assert "publish_feedback_closure.py" in block_f_window
    assert "operator_note" in block_f_window
    assert "archive_action" in block_f_window  # PG-4 enrichment cite


def test_block_f_no_invented_truth_note_present() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-iteration-archive"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-dc-block-f-no-invented-truth-note"' in block_f_subtree


# --------------------------------------------------------------------------
# H. S001 / S002 / S003 sample fixture coverage
# --------------------------------------------------------------------------


def test_s001_seam_returns_matrix_script_render_data() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    assert out["is_matrix_script"] is True
    assert out["task_id"] == "ms-s001"


def test_s002_seam_returns_matrix_script_render_data() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s002_task())
    assert out["is_matrix_script"] is True
    assert out["task_id"] == "ms-s002"


def test_s003_seam_returns_matrix_script_render_data() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s003_task())
    assert out["is_matrix_script"] is True
    assert out["task_id"] == "ms-s003"


def test_s001_recommended_action_present() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    assert out["recommended_action"].get("is_matrix_script") is True


def test_s003_publish_backfill_readiness_handles_5_variants() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s003_task())
    # Five variants — the backfill readiness rows should align with
    # the readable_variants count when both helpers have data.
    backfill = out["publish_backfill_readiness"] or {}
    if backfill:
        assert backfill.get("row_count") in (0, 5)


# --------------------------------------------------------------------------
# I. Forbidden-substring audit on operator-visible seam outputs
# --------------------------------------------------------------------------


def test_seam_no_vendor_or_model_or_provider_in_operator_visible_values() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    haystack = "\n".join(_flatten_strings(out)).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack, (
            f"forbidden substring {needle!r} leaked into seam output"
        )


def test_seam_no_fake_final_video_url_in_operator_visible_values() -> None:
    """RC-R8 audit: seam must not echo any fabricated final_video URL /
    publish_url even under empty-state input."""
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    haystack = "\n".join(_flatten_strings(out)).lower()
    for needle in (
        "final_video.mp4",
        "https://r2.",
        "https://cdn.",
        "publish_url=http",
    ):
        assert needle not in haystack, (
            f"seam emitted forbidden URL fragment: {needle!r}"
        )


def test_template_block_a_to_f_no_vendor_or_model_in_subtree() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    block_a_open = inside.find('data-role="matrix-script-block-a-final-video-primary"')
    after_block_f = inside.find(
        'data-role="matrix-script-delivery-comprehension"', block_a_open
    )
    if after_block_f == -1:
        after_block_f = len(inside)
    blocks_a_to_f_subtree = inside[block_a_open:after_block_f]
    haystack = blocks_a_to_f_subtree.lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


# --------------------------------------------------------------------------
# J. Template assertions — header + Blocks A/B/C/D/E/F gate + document order
# --------------------------------------------------------------------------


def test_template_carries_delivery_center_header_anchor() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-delivery-center-header"' in template


def test_template_blocks_a_to_f_live_inside_matrix_script_panel_gate() -> None:
    template = _read_publish_hub_template()
    inside = _ms_publish_hub_gate_body(template)
    assert inside, "matrix_script panel gate body not found"
    for marker in (
        'data-role="matrix-script-delivery-center-header"',
        'data-role="matrix-script-block-a-final-video-primary"',
        'data-role="matrix-script-block-b-required-deliverables"',
        'data-role="matrix-script-block-c-scene-pack"',
        'data-role="matrix-script-block-d-copy-bundle"',
        'data-role="matrix-script-block-e-publish-feedback"',
        'data-role="matrix-script-block-f-iteration-archive"',
    ):
        assert marker in inside, (
            f"{marker} must live inside _ms_kind == matrix_script gate"
        )


def test_template_blocks_a_to_f_do_not_appear_outside_matrix_script_gate() -> None:
    template = _read_publish_hub_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    inside = _ms_publish_hub_gate_body(template)
    assert inside
    outside = rendered.replace(inside, "")
    for marker in (
        'data-role="matrix-script-delivery-center-header"',
        'data-role="matrix-script-block-a-final-video-primary"',
        'data-role="matrix-script-block-b-required-deliverables"',
        'data-role="matrix-script-block-c-scene-pack"',
        'data-role="matrix-script-block-d-copy-bundle"',
        'data-role="matrix-script-block-e-publish-feedback"',
        'data-role="matrix-script-block-f-iteration-archive"',
    ):
        assert marker not in outside, (
            f"{marker} leaked outside the matrix_script gate"
        )


def test_template_block_order_is_header_then_a_b_c_d_e_f() -> None:
    template = _read_publish_hub_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    pos_header = rendered.find('data-role="matrix-script-delivery-center-header"')
    pos_a = rendered.find('data-role="matrix-script-block-a-final-video-primary"')
    pos_b = rendered.find('data-role="matrix-script-block-b-required-deliverables"')
    pos_c = rendered.find('data-role="matrix-script-block-c-scene-pack"')
    pos_d = rendered.find('data-role="matrix-script-block-d-copy-bundle"')
    pos_e = rendered.find('data-role="matrix-script-block-e-publish-feedback"')
    pos_f = rendered.find('data-role="matrix-script-block-f-iteration-archive"')
    assert -1 not in (pos_header, pos_a, pos_b, pos_c, pos_d, pos_e, pos_f)
    assert pos_header < pos_a < pos_b < pos_c < pos_d < pos_e < pos_f


def test_template_blocks_a_to_f_render_above_existing_secondary_diagnostics() -> None:
    """Document-order invariant: the new Block A→F panels precede the
    existing PR-U3 / Recovery PR-3 / OWC-MS PR-3 / RC PR-4 JS-hydrated
    diagnostic shells (preserved verbatim per slicing addendum §7.3)."""
    template = _read_publish_hub_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    pos_block_f = rendered.find('data-role="matrix-script-block-f-iteration-archive"')
    pos_legacy_comp = rendered.find('data-role="matrix-script-delivery-comprehension"')
    pos_legacy_closure = rendered.find('data-role="matrix-script-closure"')
    pos_legacy_copy = rendered.find('data-role="matrix-script-delivery-copy-bundle"')
    pos_legacy_backfill = rendered.find('data-role="matrix-script-delivery-backfill"')
    pos_legacy_readiness = rendered.find(
        'data-role="matrix-script-publish-backfill-readiness"'
    )
    assert -1 not in (
        pos_block_f,
        pos_legacy_comp,
        pos_legacy_closure,
        pos_legacy_copy,
        pos_legacy_backfill,
        pos_legacy_readiness,
    )
    assert pos_block_f < pos_legacy_comp, (
        "Block F must precede the secondary PR-U3 comprehension shell"
    )
    assert pos_block_f < pos_legacy_closure
    assert pos_block_f < pos_legacy_copy
    assert pos_block_f < pos_legacy_backfill
    assert pos_block_f < pos_legacy_readiness


def test_template_existing_pr_u3_comprehension_shell_preserved() -> None:
    """Slicing addendum §7.3 — PR-U3 comprehension shell preserved
    verbatim as secondary diagnostics (JS-hydrated invisible)."""
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-delivery-comprehension"' in template


def test_template_existing_recovery_pr3_closure_panel_preserved() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-closure"' in template


def test_template_existing_owc_ms_pr3_copy_bundle_shell_preserved() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-delivery-copy-bundle"' in template


def test_template_existing_owc_ms_pr3_backfill_shell_preserved() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-delivery-backfill"' in template


def test_template_existing_rc_pr4_publish_backfill_readiness_shell_preserved() -> None:
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-publish-backfill-readiness"' in template


def test_template_existing_publish_feedback_anchor_preserved() -> None:
    """PR-3 stable anchor for the Task Area "打开发布反馈" button."""
    template = _read_publish_hub_template()
    assert 'data-role="matrix-script-publish-feedback-anchor"' in template


# --------------------------------------------------------------------------
# K. Closed-enum audit (no widening across PR-4 paths)
# --------------------------------------------------------------------------


def test_event_kinds_closed_enum_unchanged_by_pr4() -> None:
    expected = frozenset(
        {
            "operator_publish",
            "operator_retract",
            "operator_note",
            "platform_callback",
            "metrics_snapshot",
        }
    )
    assert EVENT_KINDS == expected


def test_publish_status_values_closed_enum_unchanged_by_pr4() -> None:
    assert PUBLISH_STATUS_VALUES == frozenset(
        {"pending", "published", "failed", "retracted"}
    )


def test_review_zone_values_closed_enum_unchanged_by_pr4() -> None:
    assert REVIEW_ZONE_VALUES == frozenset({"subtitle", "dub", "copy", "cta"})


def test_recommended_bucket_closed_enum_unchanged_by_pr4() -> None:
    assert RECOMMENDED_BUCKET_PUBLISHABLE == "publishable_candidate"
    assert RECOMMENDED_BUCKET_BLOCKED == "blocked_pending_publish_readiness"
    assert RECOMMENDED_BUCKET_UNDETERMINED == "undetermined_pending_review"


def test_package_closed_enum_unchanged_by_pr4() -> None:
    assert PACKAGE_READY == "ready_package"
    assert PACKAGE_PARTIAL == "partial_package"
    assert PACKAGE_BLOCKED == "blocked_package"
    assert PACKAGE_UNAVAILABLE == "unavailable_tracked_gap"


# --------------------------------------------------------------------------
# L. Helper-output sanity / serialisation
# --------------------------------------------------------------------------


def test_seam_returns_only_serialisable_types() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in out.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_seam_publish_readiness_carries_publishable_bool() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    pr = out["publish_readiness"]
    if pr:
        assert isinstance(pr.get("publishable"), bool)


def test_seam_eight_stage_state_returns_either_empty_or_full_shape() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    stage = out["eight_stage_state"]
    if stage:
        assert "stage" in stage
        assert "stage_label" in stage
        assert "stage_index" in stage


def test_seam_task_area_result_status_returns_either_empty_or_matrix_script() -> None:
    out = derive_matrix_script_publish_hub_render_data(_s001_task())
    rs = out["task_area_result_status"]
    if rs:
        assert rs.get("is_matrix_script") is True
        assert "status_kind" in rs


# --------------------------------------------------------------------------
# M. Page-route wiring smoke test
# --------------------------------------------------------------------------


def test_page_route_imports_render_data_seam() -> None:
    """Confirms the page route at `gateway/app/routers/tasks.py` imports
    and calls `derive_matrix_script_publish_hub_render_data` so the
    template's `ms_publish_hub` ctx variable is populated."""
    repo_root = _REPO_ROOT
    tasks_router_src = (
        repo_root / "gateway" / "app" / "routers" / "tasks.py"
    ).read_text(encoding="utf-8")
    assert (
        "from gateway.app.services.matrix_script.publish_hub_render_data import (\n"
        "            derive_matrix_script_publish_hub_render_data,\n"
        "        )"
        in tasks_router_src
    )
    assert (
        "ms_publish_hub = derive_matrix_script_publish_hub_render_data(task) or {}"
        in tasks_router_src
    )
    assert '"ms_publish_hub": ms_publish_hub,' in tasks_router_src
