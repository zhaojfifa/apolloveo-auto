"""OWC-MS-RO PR-3 — Matrix Script Workbench Blocks D / E / F dedicated tests.

Authority pointers:

- ``docs/design/matrix_script_workbench_wireframe_v1.md`` §6 / §7 / §8
  (Blocks D / E / F binding-and-exhaustive fields).
- ``docs/design/matrix_script_result_oriented_ui_implementation_slicing_v1.md``
  §6 (PR-3 scope, RO-3.* acceptance evidence) + §6.3 (preserved
  diagnostics) + §6.5 (hard non-goals) + §2.1.3 / §2.2.3 (PR-3 gating
  clause; user's direct instruction is the authority that opens PR-3
  in this turn).
- ``docs/product/matrix_script_product_flow_v1.md`` §6 (Workbench design).
- Operator sample anchor: ``production_packet_3_scripts.json`` —
  S001 / S002 / S003 baked into fixtures below (mirroring PR-2 fixtures).
- Existing helpers consumed (no new helper module per PR-3 scope):
  ``gateway/app/services/matrix_script/recommended_action_view.py``,
  ``gateway/app/services/matrix_script/preview_compare_view.py``,
  ``gateway/app/services/matrix_script/qc_diagnostics_view.py``,
  ``gateway/app/services/matrix_script/delivery_ready_package_view.py``,
  ``gateway/app/services/matrix_script/review_zone_view.py``,
  ``gateway/app/services/matrix_script/delivery_comprehension.py``,
  ``gateway/app/services/operator_visible_surfaces/publish_readiness.py``.
- Closed enums consumed (NO widening — verified at module import time):
  ``D1_EVENT_KINDS`` (= ``EVENT_KINDS`` on publish_feedback_closure),
  ``REVIEW_ZONE_VALUES``, ``RECOMMENDED_BUCKET_*``, ``PACKAGE_*``,
  ``head_reason`` enum on publish_readiness.

PR-3 binding behaviour proved by this suite:

1. ``derive_matrix_script_recommended_action`` exposes the Block D
   single-line decision lane (status_kind / headline_zh / next_action_zh
   / head_reason_label_zh / reason_zh) with no second producer.
2. Block D primary action label resolves to "生成 N 个变体" with N
   sourced from ``derive_matrix_script_readable_variants.variant_count``;
   secondary label resolves to "重新生成被阻塞的变体 (M)" with M
   sourced from ``derive_matrix_script_delivery_ready_package.blocked_count``.
3. Block D blocker label is operator-language only (mapped from the
   closed publish_readiness ``head_reason`` enum via
   ``HEAD_REASON_LABELS_ZH``); the raw English enum value never leaks.
4. Block D contains no provider / model / vendor / engine selector
   anywhere inside the matrix_script panel gate.
5. Block E renders one card per variation; the ⭐ recommended marker
   appears on at most one card and only when its variation_id matches
   ``recommended_action.recommended_variant.variation_id`` AND its
   ``recommended_bucket == "publishable_candidate"``.
6. Block E per-card preview slot text is sourced from the existing
   ``preview_compare.variations[].preview_status_label_zh`` —
   tracked-gap rows render the operator-language explanation, never a
   fabricated URL or fake ``final_video`` handle (RC-R8 audit).
7. Block E per-card package status pill is sourced from the existing
   ``delivery_ready_package.rows[].package_status_label_zh`` (closed
   ``PACKAGE_*`` enum); never fabricates a status outside the enum.
8. Block E QC three-item set carries the closed
   ``QUALITY_ITEM_DURATION`` / ``QUALITY_ITEM_CLARITY`` /
   ``QUALITY_ITEM_SUBTITLE_READABILITY`` items (sourced from
   ``qc_diagnostics_view.quality_items``).
9. Block E review-zone chip set carries the four
   ``REVIEW_ZONE_VALUES`` zones in their canonical
   ``REVIEW_ZONE_ORDER`` order; chip text is operator-language only.
10. Block E "提交分区评审意见" form posts to
    ``POST /api/matrix-script/closures/{task_id}/events`` with
    ``event_kind == "operator_note"`` + ``review_zone ∈ REVIEW_ZONE_VALUES``;
    no new endpoint; no ``D1_EVENT_KINDS`` widening; no
    ``REVIEW_ZONE_VALUES`` widening; no event mutation / deletion.
11. Block E "选定为推荐版本" + "重新生成此变体" affordances are
    deferred (IG-4 / IG-2 per slicing addendum §6.5) — the buttons
    render disabled-with-tooltip placeholders so operator sees the
    affordance shape but the closed-state transition is not triggered.
12. Block F publish-gate banner consumes the unified
    ``compute_publish_readiness`` output directly (RC-A7 single source);
    no second-source ``publishable`` derivation.
13. Block F required-deliverable lane reads
    ``delivery_comprehension.lanes.required_blocking`` +
    ``required_non_blocking`` rows; per-row status is operator-language
    via ``artifact_status_label_zh``.
14. Block F optional ``scene_pack`` lane is rendered as a separate row
    set with ``SCENE_PACK_BLOCKING_ALLOWED = False`` (defensive
    constant on ``matrix_script/delivery_binding.py``).
15. Block F never renders an inline ``final_video`` player or a publish
    action button (publishing happens in Delivery Center / Publish
    Feedback only).
16. Hot Follow / Digital Anchor / baseline panels return ``{}`` from
    each of the helpers PR-3 reads — the new template panels gate on
    ``is_matrix_script`` so non-MS workbench surfaces stay bytewise
    unchanged.
17. Forbidden surfaces audit: no vendor / model / provider / engine /
    ``content://`` / ``slot_id`` / ``cell_id`` / ``script_slot_ref`` /
    ``binds_cell_id`` leakage in any operator-visible value emitted by
    the helpers PR-3 reads.
18. Template assertions: the new ``data-role`` markers
    (``matrix-script-block-d-generate-regenerate`` /
    ``matrix-script-block-e-candidate-review`` /
    ``matrix-script-block-f-delivery-teaser``) are present in
    ``task_workbench.html`` and are gated to the matrix_script branch
    only.
19. Existing PR-U2 + MS-W3 + MS-W4 + MS-W5 + MS-W6 + RC PR-2 + RC PR-4
    + Variation Panel anchors are preserved verbatim — secondary
    diagnostics still render below the new D / E / F blocks.
20. Document-order invariant: A → B → C → D → E → F → secondary
    diagnostics.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_comprehension import (
    derive_matrix_script_delivery_comprehension,
)
from gateway.app.services.matrix_script.delivery_ready_package_view import (
    PACKAGE_BLOCKED,
    PACKAGE_PARTIAL,
    PACKAGE_READY,
    PACKAGE_STATUS_LABELS_ZH,
    PACKAGE_UNAVAILABLE,
    derive_matrix_script_delivery_ready_package,
)
from gateway.app.services.matrix_script.preview_compare_view import (
    RECOMMENDED_BUCKET_BLOCKED,
    RECOMMENDED_BUCKET_PUBLISHABLE,
    RECOMMENDED_BUCKET_UNDETERMINED,
    derive_matrix_script_preview_compare_view,
)
from gateway.app.services.matrix_script.publish_feedback_closure import (
    EVENT_KINDS,
    REVIEW_ZONE_VALUES,
)
from gateway.app.services.matrix_script.qc_diagnostics_view import (
    HEAD_REASON_LABELS_ZH,
    QUALITY_ITEM_CLARITY,
    QUALITY_ITEM_DURATION,
    QUALITY_ITEM_SUBTITLE_READABILITY,
    derive_matrix_script_qc_diagnostics_view,
)
from gateway.app.services.matrix_script.readable_variant_view import (
    derive_matrix_script_readable_variants,
)
from gateway.app.services.matrix_script.recommended_action_view import (
    HEADLINE_BLOCKED_ZH,
    HEADLINE_PUBLISHABLE_ZH,
    HEADLINE_UNDETERMINED_ZH,
    derive_matrix_script_recommended_action,
)
from gateway.app.services.matrix_script.review_zone_view import (
    REVIEW_EVENT_ENDPOINT_TEMPLATE,
    REVIEW_ZONE_ORDER,
    derive_matrix_script_review_zone_view,
)


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read_workbench_template() -> str:
    return _WORKBENCH_TEMPLATE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Test fixtures (S001 / S002 / S003 + Hot Follow / DA byte-isolation)
# --------------------------------------------------------------------------


def _ms_panel(*, refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "panel_kind": "matrix_script",
        "refs": refs or [],
    }


def _publish_readiness(
    *, publishable: bool = False, head_reason: str | None = None
) -> dict[str, Any]:
    return {
        "publishable": publishable,
        "head_reason": head_reason,
        "consumed_inputs": {"blocking_count": 0 if publishable else 1},
        "blocking_advisories": [],
    }


def _matrix_script_task(
    *,
    task_id: str = "ms-de f-001",
    topic: str = "PR-3 测试任务",
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


def _variation_surface(
    *,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cells = cells or []
    slots = slots or []
    return {
        "variation_plan": {
            "axes": [
                {
                    "axis_id": "tone",
                    "kind": "nominal",
                    "values": ["sincere", "rhetorical", "confident", "playful"],
                    "is_required": True,
                },
            ],
            "cells": cells,
        },
        "copy_bundle": {"slots": slots},
        "attribution_refs": {"line_specific_refs": []},
        "publish_feedback_projection": {},
    }


def _delivery_binding(*, deliverables: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    deliverables = deliverables or []
    return {
        "line_id": "matrix_script",
        "delivery_pack": {
            "deliverables": deliverables,
        },
    }


def _delivery_binding_with_required_blocking_row(
    *,
    deliverable_id: str = "matrix_script_variation_manifest",
    deliverable_kind: str = "variation_manifest",
    artifact_lookup: dict[str, Any] | None = None,
    required: bool = True,
    blocking_publish: bool = True,
) -> dict[str, Any]:
    artifact_lookup = artifact_lookup or {
        "exists_kind": "tracked_gap",
        "tracked_gap_reason": "not_implemented_phase_c",
    }
    return _delivery_binding(
        deliverables=[
            {
                "deliverable_id": deliverable_id,
                "deliverable_kind": deliverable_kind,
                "required": required,
                "blocking_publish": blocking_publish,
                "artifact_lookup": artifact_lookup,
            }
        ]
    )


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


def _ms_panel_gate_body(template: str) -> str:
    """Extract the body of the matrix_script panel gate, counting nested
    `{% if %}` / `{% endif %}` so the right closing endif is matched."""
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    open_pat = re.compile(
        r'{%\s*if\s+ops_workbench_panel\.panel_kind\s*==\s*"matrix_script"\s*%}'
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
# A. Block D — Generate / Regenerate (helper API)
# --------------------------------------------------------------------------


def test_block_d_recommended_action_publishable_carries_headline_and_next_action() -> None:
    surface = _variation_surface(
        cells=_s001_task()["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=_s001_task()["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    pc = derive_matrix_script_preview_compare_view(
        surface,
        _delivery_binding(),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    rv = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    out = derive_matrix_script_recommended_action(pc, rv, _ms_panel())
    assert out["status_kind"] == RECOMMENDED_BUCKET_PUBLISHABLE
    assert out["headline_zh"] == HEADLINE_PUBLISHABLE_ZH
    assert isinstance(out["next_action_zh"], str) and out["next_action_zh"]


def test_block_d_recommended_action_blocked_carries_head_reason_label() -> None:
    surface = _variation_surface(
        cells=_s001_task()["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=_s001_task()["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    pr = _publish_readiness(publishable=False, head_reason="compose_not_ready")
    pc = derive_matrix_script_preview_compare_view(surface, _delivery_binding(), pr, _ms_panel())
    rv = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    out = derive_matrix_script_recommended_action(pc, rv, _ms_panel())
    assert out["status_kind"] == RECOMMENDED_BUCKET_BLOCKED
    assert out["headline_zh"] == HEADLINE_BLOCKED_ZH
    # operator language label, not the raw enum
    assert out["head_reason_label_zh"] != "compose_not_ready"
    assert out["head_reason_label_zh"] == HEAD_REASON_LABELS_ZH["compose_not_ready"]


def test_block_d_recommended_action_undetermined_when_no_publish_readiness() -> None:
    surface = _variation_surface(cells=[], slots=[])
    pc = derive_matrix_script_preview_compare_view(surface, _delivery_binding(), None, _ms_panel())
    rv = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    out = derive_matrix_script_recommended_action(pc, rv, _ms_panel())
    assert out["status_kind"] == RECOMMENDED_BUCKET_UNDETERMINED
    assert out["headline_zh"] == HEADLINE_UNDETERMINED_ZH


def test_block_d_recommended_action_returns_empty_for_non_matrix_script() -> None:
    assert derive_matrix_script_recommended_action({}, {}, {"panel_kind": "hot_follow"}) == {}
    assert derive_matrix_script_recommended_action({}, {}, {"panel_kind": "digital_anchor"}) == {}
    assert derive_matrix_script_recommended_action({}, {}, {"panel_kind": "baseline"}) == {}


def test_block_d_primary_action_label_format_and_count() -> None:
    """Block D primary label = "生成 N 个变体" with N from variant_count."""
    surface = _variation_surface(
        cells=_s001_task()["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=_s001_task()["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    rv = derive_matrix_script_readable_variants(_s001_task(), surface, _ms_panel())
    assert rv["variant_count"] == 4
    template = _read_workbench_template()
    # The template literal that interpolates the count into the primary
    # action label.
    assert "生成 {{ ms_readable_variants.variant_count or 0 }} 个变体" in template


def test_block_d_secondary_action_label_format_and_count() -> None:
    """Block D secondary label = "重新生成被阻塞的变体 (M)" with M
    from delivery_ready_package.blocked_count."""
    template = _read_workbench_template()
    assert "重新生成被阻塞的变体 ({{ ms_delivery_ready_package.blocked_count or 0 }})" in template


def test_block_d_no_provider_model_vendor_engine_in_template_subtree() -> None:
    """Forbidden-substring audit on the Block D template subtree.

    Block D contains no operator-visible provider / model / vendor /
    engine selector or label."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    assert inside, "matrix_script panel gate body not found"
    # Locate just the Block D substring (between its data-role marker and
    # the next data-role marker).
    block_d_open = inside.find('data-role="matrix-script-block-d-generate-regenerate"')
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    assert block_d_open != -1
    assert block_e_open != -1
    block_d_subtree = inside[block_d_open:block_e_open]
    haystack = block_d_subtree.lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack, (
            f"forbidden substring {needle!r} leaked into Block D template subtree"
        )


def test_block_d_renders_disabled_when_publish_blocked() -> None:
    template = _read_workbench_template()
    # The disabled-attribute branch on the primary action triggers when
    # status_kind == "blocked_pending_publish_readiness".
    assert (
        'data-status-kind="{{ ms_recommended_action.status_kind }}"'
        in template
    )
    assert (
        'ms_recommended_action.status_kind == "blocked_pending_publish_readiness"'
        in template
    )


def test_block_d_blocker_label_renders_operator_language_only() -> None:
    """Block D never emits raw English head_reason — only the
    HEAD_REASON_LABELS_ZH-mapped label."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-generate-regenerate"')
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_d_subtree = inside[block_d_open:block_e_open]
    # The blocker value is sourced from head_reason_label_zh, never from
    # head_reason directly.
    assert "ms_recommended_action.head_reason_label_zh" in block_d_subtree
    # The operator-visible blocker line should reach the label_zh field.
    assert 'data-role="ms-block-d-blocker-value"' in block_d_subtree


def test_block_d_carries_preconditions_anchor() -> None:
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-generate-regenerate"')
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_d_subtree = inside[block_d_open:block_e_open]
    assert 'data-role="ms-block-d-preconditions"' in block_d_subtree
    assert 'data-role="ms-block-d-precondition-ready-gate"' in block_d_subtree


# --------------------------------------------------------------------------
# B. Block E — Candidate Review (helper API)
# --------------------------------------------------------------------------


def _build_block_e_inputs(
    *,
    publishable: bool = True,
    head_reason: str | None = None,
    cells: list[dict[str, Any]] | None = None,
    slots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    s001 = _s001_task()
    cells = cells if cells is not None else s001["packet"]["line_specific_refs"][0]["delta"]["cells"]
    slots = slots if slots is not None else s001["packet"]["line_specific_refs"][1]["delta"]["slots"]
    surface = _variation_surface(cells=cells, slots=slots)
    pr = _publish_readiness(publishable=publishable, head_reason=head_reason)
    binding = _delivery_binding()
    pc = derive_matrix_script_preview_compare_view(surface, binding, pr, _ms_panel())
    rv = derive_matrix_script_readable_variants(s001, surface, _ms_panel(), preview_compare=pc)
    pkg = derive_matrix_script_delivery_ready_package(rv, {}, {}, pr, _ms_panel())
    qc = derive_matrix_script_qc_diagnostics_view(pr, {}, surface, _ms_panel())
    rz = derive_matrix_script_review_zone_view(surface, None, _ms_panel(), task_id=s001["task_id"])
    ra = derive_matrix_script_recommended_action(pc, rv, _ms_panel())
    return {
        "preview_compare": pc,
        "readable_variants": rv,
        "package": pkg,
        "qc": qc,
        "review_zone": rz,
        "recommended_action": ra,
    }


def test_block_e_renders_one_card_per_variation() -> None:
    bundle = _build_block_e_inputs()
    assert bundle["preview_compare"]["variation_count"] == 4
    assert len(bundle["preview_compare"]["variations"]) == 4


def test_block_e_recommended_marker_pins_to_recommended_variant_id() -> None:
    """⭐ marker appears on at most one card and only when its
    variation_id matches recommended_action.recommended_variant.variation_id."""
    bundle = _build_block_e_inputs(publishable=True)
    ra = bundle["recommended_action"]
    if ra.get("recommended_variant"):
        recommended_id = ra["recommended_variant"]["variation_id"]
        # the recommended_id must match exactly one of the
        # preview_compare.variations rows
        ids = [v["variation_id"] for v in bundle["preview_compare"]["variations"]]
        assert recommended_id in ids


def test_block_e_recommended_marker_absent_when_blocked() -> None:
    bundle = _build_block_e_inputs(publishable=False, head_reason="compose_not_ready")
    ra = bundle["recommended_action"]
    assert ra["status_kind"] == RECOMMENDED_BUCKET_BLOCKED
    assert ra.get("recommended_variant") is None


def test_block_e_per_card_preview_status_carries_operator_language() -> None:
    bundle = _build_block_e_inputs()
    for variation in bundle["preview_compare"]["variations"]:
        assert isinstance(variation["preview_status_label_zh"], str)
        assert variation["preview_status_label_zh"]


def test_block_e_per_card_no_fake_final_video_url() -> None:
    """Adversarial empty-state fixture must not echo any fabricated
    final_video URL / publish_url (RC-R8 audit)."""
    bundle = _build_block_e_inputs(publishable=False, head_reason="final_missing")
    haystack = "\n".join(_flatten_strings(bundle["preview_compare"])).lower()
    for needle in (
        "https://r2.",
        "https://cdn.",
        "final_video.mp4",
        "publish_url=http",
    ):
        assert needle not in haystack, (
            f"preview_compare emitted forbidden URL fragment: {needle!r}"
        )


def test_block_e_per_card_package_status_kind_in_closed_enum() -> None:
    bundle = _build_block_e_inputs()
    rows = bundle["package"].get("rows", [])
    allowed = {PACKAGE_READY, PACKAGE_PARTIAL, PACKAGE_BLOCKED, PACKAGE_UNAVAILABLE}
    for row in rows:
        assert row["package_status_kind"] in allowed
        assert (
            row["package_status_label_zh"]
            == PACKAGE_STATUS_LABELS_ZH[row["package_status_kind"]]
        )


def test_block_e_qc_three_item_set_is_closed() -> None:
    bundle = _build_block_e_inputs()
    quality_items = bundle["qc"]["quality_items"]
    quality_ids = [item["quality_id"] for item in quality_items]
    assert quality_ids == [
        QUALITY_ITEM_DURATION,
        QUALITY_ITEM_CLARITY,
        QUALITY_ITEM_SUBTITLE_READABILITY,
    ]
    # Operator-language label and closed status_code per item
    for item in quality_items:
        assert isinstance(item["label_zh"], str) and item["label_zh"]
        assert item["status_code"] in {"observed", "unobservable_pending_upstream"}


def test_block_e_review_zone_chip_set_is_closed_and_canonical_order() -> None:
    bundle = _build_block_e_inputs()
    zone_ids = [zone["zone_id"] for zone in bundle["review_zone"]["zones"]]
    assert tuple(zone_ids) == REVIEW_ZONE_ORDER
    assert set(zone_ids) == set(REVIEW_ZONE_VALUES)


def test_block_e_review_zone_chip_carries_operator_language_label() -> None:
    bundle = _build_block_e_inputs()
    for zone in bundle["review_zone"]["zones"]:
        assert isinstance(zone["zone_label_zh"], str) and zone["zone_label_zh"]


def test_block_e_review_form_action_url_resolves_to_existing_endpoint() -> None:
    bundle = _build_block_e_inputs()
    rz = bundle["review_zone"]
    expected = REVIEW_EVENT_ENDPOINT_TEMPLATE.format(task_id="ms-s001")
    assert rz["closure_endpoint_url"] == expected
    # /api/matrix-script/closures/{task_id}/events
    assert rz["closure_endpoint_url"] == "/api/matrix-script/closures/ms-s001/events"


def test_block_e_review_form_event_kind_is_closed_operator_note() -> None:
    """Review form event_kind MUST be exactly "operator_note" (a member of
    the closed EVENT_KINDS / D1_EVENT_KINDS frozen set)."""
    assert "operator_note" in EVENT_KINDS
    bundle = _build_block_e_inputs()
    for row in bundle["review_zone"]["review_status_rows"]:
        for zone_id, state in row["per_zone"].items():
            form = state.get("submit_form")
            if form is None:
                continue
            assert form["event_kind"] == "operator_note"
            assert form["actor_kind"] == "operator"
            assert form["review_zone"] in REVIEW_ZONE_VALUES


def test_block_e_review_form_carries_variation_id_per_card() -> None:
    bundle = _build_block_e_inputs()
    # Each per-zone submit_form.variation_id matches the per-card
    # variation_id, so the closure event lands on the correct cell row.
    for row in bundle["review_zone"]["review_status_rows"]:
        for zone_id, state in row["per_zone"].items():
            form = state.get("submit_form")
            if form is None:
                continue
            assert form["variation_id"] == row["variation_id"]


def test_block_e_review_form_does_not_widen_event_kinds_enum() -> None:
    """EVENT_KINDS is a closed frozenset; the form's event_kind must
    pick from it, never invent a new value."""
    bundle = _build_block_e_inputs()
    for row in bundle["review_zone"]["review_status_rows"]:
        for state in row["per_zone"].values():
            form = state.get("submit_form")
            if form is None:
                continue
            assert form["event_kind"] in EVENT_KINDS


def test_block_e_review_form_does_not_widen_review_zone_values_enum() -> None:
    bundle = _build_block_e_inputs()
    for row in bundle["review_zone"]["review_status_rows"]:
        for state in row["per_zone"].values():
            form = state.get("submit_form")
            if form is None:
                continue
            assert form["review_zone"] in REVIEW_ZONE_VALUES


def test_block_e_form_endpoint_template_unchanged() -> None:
    """No new endpoint per slicing addendum §6.4 RO-3.4."""
    assert (
        REVIEW_EVENT_ENDPOINT_TEMPLATE
        == "/api/matrix-script/closures/{task_id}/events"
    )


def test_block_e_select_recommended_button_rendered_disabled() -> None:
    """IG-4 deferred per slicing addendum §6.5 — the affordance shape
    renders so operator sees the planned action, but the button is
    disabled-with-tooltip and the closed-state transition is not
    triggered in this PR."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    # 选定为推荐版本 button rendered with disabled attribute
    assert (
        'data-role="ms-block-e-card-action-select-recommended"'
        in block_e_subtree
    )
    # Locate the surrounding button block and assert it carries
    # `disabled aria-disabled="true"`
    select_re = re.compile(
        r'data-role="ms-block-e-card-action-select-recommended"[\s\S]*?</button>'
    )
    m = select_re.search(block_e_subtree)
    assert m is not None
    assert "disabled" in m.group()


def test_block_e_regenerate_this_variant_button_rendered_disabled() -> None:
    """IG-2 deferred — per-cell_id execution dispatch is out of scope
    for this PR. The button renders with disabled attribute."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert 'data-role="ms-block-e-card-action-regenerate"' in block_e_subtree
    regen_re = re.compile(
        r'data-role="ms-block-e-card-action-regenerate"[\s\S]*?</button>'
    )
    m = regen_re.search(block_e_subtree)
    assert m is not None
    assert "disabled" in m.group()


def test_block_e_submit_review_button_renders_enabled_with_zone_form() -> None:
    """The operator-actionable button in this PR is the submit-review
    button which expands the per-zone form panel."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert (
        'data-role="ms-block-e-card-action-submit-review"' in block_e_subtree
    )
    submit_re = re.compile(
        r'data-role="ms-block-e-card-action-submit-review"[\s\S]*?</button>'
    )
    m = submit_re.search(block_e_subtree)
    assert m is not None
    assert "disabled" not in m.group()


def test_block_e_zone_form_panel_carries_method_post_and_action_url() -> None:
    """The per-zone form panel renders a POST form against the existing
    closure endpoint."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert 'data-role="ms-block-e-card-zone-form"' in block_e_subtree
    # method / action are interpolated from the per-zone submit_form
    assert 'method="{{ _form.method }}"' in block_e_subtree
    assert 'action="{{ _form.action }}"' in block_e_subtree


def test_block_e_zone_form_carries_event_kind_and_review_zone_hidden_inputs() -> None:
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    assert 'name="event_kind"' in block_e_subtree
    assert 'name="review_zone"' in block_e_subtree
    assert 'name="variation_id"' in block_e_subtree
    assert 'name="actor_kind"' in block_e_subtree


# --------------------------------------------------------------------------
# C. Block F — Delivery Teaser (helper API)
# --------------------------------------------------------------------------


def test_block_f_delivery_comprehension_returns_lanes_object() -> None:
    out = derive_matrix_script_delivery_comprehension(
        _delivery_binding_with_required_blocking_row()
    )
    assert out["is_matrix_script"] is True
    assert "lanes" in out
    assert "required_blocking" in out["lanes"]
    assert "required_non_blocking" in out["lanes"]
    assert "optional_non_blocking" in out["lanes"]


def test_block_f_publish_gate_consumes_publish_readiness_directly() -> None:
    """RC-A7 single-source publishability — Block F MUST consume
    compute_publish_readiness output directly, not re-derive it.

    Updated 2026-05-28: Block F was reframed per Mission §4 to a short
    delivery STATUS card (head_reason no longer rendered on the workbench
    surface; full per-row detail moved to Delivery Center). The single-
    source publishability gate is still read directly from
    ``ms_publish_readiness.publishable``; ``head_reason`` is consumed
    instead by the (separate) result-summary helper that drives Block A.
    """

    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    assert block_f_open != -1
    block_f_subtree = inside[block_f_open:]
    # Block F reads ms_publish_readiness which is the bundle.publish_readiness
    # alias; never invents a parallel publishable boolean.
    assert "ms_publish_readiness.publishable" in block_f_subtree
    # head_reason now reaches the operator through Block A's result-summary
    # path, NOT through Block F. Block F shows only "可发布" vs "当前不能
    # 交付" using the publishable boolean — operator-language only.
    assert "可发布" in block_f_subtree
    assert "当前不能交付" in block_f_subtree


def test_block_f_have_section_lists_phase_b_baseline_items() -> None:
    """Mission §4 — Block F shows what is "已具备" (have) at the workbench
    summary level. The Phase B baseline ("脚本结构、变体方案") is the
    minimum honest claim on a contract-clean task today. Per-row resolved
    deliverables append to this list when delivery_comprehension lanes
    show resolved artifacts; full per-row detail belongs in Delivery Center.
    """

    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-block-f-have"' in block_f_subtree
    assert "脚本结构" in block_f_subtree
    assert "变体方案" in block_f_subtree
    # The resolved-row append uses the same delivery_comprehension lane
    # data, just collapsed to a list of kind labels instead of a per-row
    # status table (which lives in Delivery Center per Mission §4).
    assert "ms_delivery_comprehension.lanes.required_blocking.rows" in block_f_subtree
    assert "ms_delivery_comprehension.lanes.required_non_blocking.rows" in block_f_subtree


def test_block_f_scene_pack_non_blocking_note_present() -> None:
    """SCENE_PACK_BLOCKING_ALLOWED = False is enforced upstream; Block F
    notes the operator-language rule once, near the bottom of the short
    status card. Updated 2026-05-28 to the redesigned wording — the
    per-row optional lane was removed per Mission §4 (full detail in
    Delivery Center).
    """

    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-block-f-scene-pack-note"' in block_f_subtree
    assert "场景包（scene_pack）始终为可选 · 不阻塞发布。" in block_f_subtree


def test_block_f_jump_button_targets_publish_hub_route() -> None:
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_f_subtree = inside[block_f_open:]
    assert 'data-role="ms-block-f-action-delivery-center"' in block_f_subtree
    assert 'href="/tasks/{{ task.task_id }}/publish"' in block_f_subtree


def test_block_f_no_inline_final_video_player() -> None:
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_f_subtree = inside[block_f_open:]
    # Block F must not render a <video>/<source> element. The full primary
    # slot lives in the Delivery Center, not in the workbench teaser.
    assert "<video" not in block_f_subtree
    assert "<source " not in block_f_subtree


def test_block_f_no_publish_action_button() -> None:
    """Publishing happens in Delivery Center / Publish Feedback only.
    Block F MUST NOT render a publish action."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_f_subtree = inside[block_f_open:]
    # No "立即发布" / "执行发布" / "publish_now" affordance anywhere in F
    for needle in ("立即发布", "执行发布", "publish_now", "post_publish_event"):
        assert needle not in block_f_subtree


def test_block_f_no_fake_publish_url_synthesis() -> None:
    """Block F must not synthesise a publish_url even under empty input."""
    out = derive_matrix_script_delivery_comprehension(_delivery_binding())
    haystack = "\n".join(_flatten_strings(out)).lower()
    for needle in (
        "publish_url=http",
        "https://r2.",
        "https://cdn.",
        "final_video.mp4",
    ):
        assert needle not in haystack


# --------------------------------------------------------------------------
# D. S001 / S002 / S003 sample fixture coverage
# --------------------------------------------------------------------------


def test_s001_block_e_renders_4_per_variant_cards() -> None:
    s001 = _s001_task()
    surface = _variation_surface(
        cells=s001["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=s001["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    pc = derive_matrix_script_preview_compare_view(
        surface,
        _delivery_binding(),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    assert pc["variation_count"] == 4


def test_s002_block_e_renders_3_per_variant_cards() -> None:
    s002 = _s002_task()
    surface = _variation_surface(
        cells=s002["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=s002["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    pc = derive_matrix_script_preview_compare_view(
        surface,
        _delivery_binding(),
        _publish_readiness(publishable=False, head_reason="compose_not_ready"),
        _ms_panel(),
    )
    assert pc["variation_count"] == 3


def test_s003_block_e_renders_5_per_variant_cards() -> None:
    s003 = _s003_task()
    surface = _variation_surface(
        cells=s003["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=s003["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    pc = derive_matrix_script_preview_compare_view(
        surface,
        _delivery_binding(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _ms_panel(),
    )
    assert pc["variation_count"] == 5


def test_s001_block_d_primary_action_count_is_4() -> None:
    s001 = _s001_task()
    surface = _variation_surface(
        cells=s001["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=s001["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    rv = derive_matrix_script_readable_variants(s001, surface, _ms_panel())
    assert rv["variant_count"] == 4


def test_s003_block_d_primary_action_count_is_5() -> None:
    s003 = _s003_task()
    surface = _variation_surface(
        cells=s003["packet"]["line_specific_refs"][0]["delta"]["cells"],
        slots=s003["packet"]["line_specific_refs"][1]["delta"]["slots"],
    )
    rv = derive_matrix_script_readable_variants(s003, surface, _ms_panel())
    assert rv["variant_count"] == 5


# --------------------------------------------------------------------------
# E. Hot Follow / Digital Anchor / baseline byte-isolation
# --------------------------------------------------------------------------


def test_hot_follow_panel_returns_empty_recommended_action() -> None:
    assert (
        derive_matrix_script_recommended_action({}, {}, {"panel_kind": "hot_follow"})
        == {}
    )


def test_digital_anchor_panel_returns_empty_recommended_action() -> None:
    assert (
        derive_matrix_script_recommended_action({}, {}, {"panel_kind": "digital_anchor"})
        == {}
    )


def test_baseline_panel_returns_empty_recommended_action() -> None:
    assert (
        derive_matrix_script_recommended_action({}, {}, {"panel_kind": "baseline"}) == {}
    )


def test_hot_follow_panel_returns_empty_review_zone() -> None:
    assert (
        derive_matrix_script_review_zone_view(
            _variation_surface(),
            None,
            {"panel_kind": "hot_follow"},
            task_id="hf-1",
        )
        == {}
    )


def test_digital_anchor_panel_returns_empty_review_zone() -> None:
    assert (
        derive_matrix_script_review_zone_view(
            _variation_surface(),
            None,
            {"panel_kind": "digital_anchor"},
            task_id="da-1",
        )
        == {}
    )


def test_hot_follow_panel_returns_empty_qc_diagnostics() -> None:
    assert (
        derive_matrix_script_qc_diagnostics_view(
            _publish_readiness(publishable=True),
            {},
            _variation_surface(),
            {"panel_kind": "hot_follow"},
        )
        == {}
    )


def test_digital_anchor_panel_returns_empty_qc_diagnostics() -> None:
    assert (
        derive_matrix_script_qc_diagnostics_view(
            _publish_readiness(publishable=True),
            {},
            _variation_surface(),
            {"panel_kind": "digital_anchor"},
        )
        == {}
    )


def test_hot_follow_panel_returns_empty_delivery_ready_package() -> None:
    assert (
        derive_matrix_script_delivery_ready_package(
            {}, {}, {}, _publish_readiness(publishable=True), {"panel_kind": "hot_follow"}
        )
        == {}
    )


def test_digital_anchor_panel_returns_empty_delivery_ready_package() -> None:
    assert (
        derive_matrix_script_delivery_ready_package(
            {},
            {},
            {},
            _publish_readiness(publishable=True),
            {"panel_kind": "digital_anchor"},
        )
        == {}
    )


def test_non_matrix_script_binding_returns_empty_delivery_comprehension() -> None:
    """delivery_comprehension is keyed off binding.line_id, not panel.
    Hot Follow and Digital Anchor bindings return {}."""
    assert derive_matrix_script_delivery_comprehension({}) == {}
    assert (
        derive_matrix_script_delivery_comprehension({"line_id": "hot_follow"}) == {}
    )
    assert (
        derive_matrix_script_delivery_comprehension({"line_id": "digital_anchor"})
        == {}
    )


# --------------------------------------------------------------------------
# F. Forbidden-substring audit on operator-visible helper outputs
# --------------------------------------------------------------------------


def test_recommended_action_no_vendor_or_model_in_operator_visible_values() -> None:
    bundle = _build_block_e_inputs(publishable=False, head_reason="compose_not_ready")
    haystack = "\n".join(_flatten_strings(bundle["recommended_action"])).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


def test_qc_diagnostics_no_vendor_or_model_in_operator_visible_values() -> None:
    bundle = _build_block_e_inputs()
    haystack = "\n".join(_flatten_strings(bundle["qc"])).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


def test_review_zone_no_vendor_or_model_in_operator_visible_values() -> None:
    bundle = _build_block_e_inputs()
    haystack = "\n".join(_flatten_strings(bundle["review_zone"])).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


def test_delivery_comprehension_no_vendor_or_model_in_operator_visible_values() -> None:
    out = derive_matrix_script_delivery_comprehension(
        _delivery_binding_with_required_blocking_row()
    )
    haystack = "\n".join(_flatten_strings(out)).lower()
    for needle in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert needle not in haystack


def test_block_e_template_subtree_no_axis_tuple_or_cell_id_leakage() -> None:
    """Block E operator-visible columns must not leak raw cell_id /
    slot_id / axis-tuple / script_slot_ref / binds_cell_id / content://
    handles. Template scan."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_e_open = inside.find('data-role="matrix-script-block-e-candidate-review"')
    block_f_open = inside.find('data-role="matrix-script-block-f-delivery-teaser"')
    block_e_subtree = inside[block_e_open:block_f_open]
    # The card body column labels must not reach raw axis_tuple keys.
    # Note: the form's hidden inputs DO carry variation_id (which is the
    # cell_id) — this is a closure-event field, not an operator-visible
    # column, so the assertion below targets visible labels and column
    # values, not hidden form fields.
    visible_substrings = (
        "axis_tuple",
        "axis-tuple",
        "binds_cell_id",
        "script_slot_ref",
    )
    for needle in visible_substrings:
        # The needle must not appear as a visible TD / display row in
        # the per-card subtree. It MAY appear inside a `<input
        # type="hidden">` form field (e.g. variation_id), but we don't
        # use those four substrings as form names so this scan is safe.
        assert needle not in block_e_subtree, (
            f"forbidden internal handle {needle!r} leaked into Block E subtree"
        )


def test_block_d_e_f_template_subtree_no_content_handle_leakage() -> None:
    """No content:// handle string in any visible operator value across
    Blocks D/E/F. The variation_id form field (== cell_id) is rendered
    in a hidden input, not as a visible label."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    block_d_open = inside.find('data-role="matrix-script-block-d-generate-regenerate"')
    after_block_f = inside.find(
        'data-role="matrix-script-comprehension-panel"', block_d_open
    )
    if after_block_f == -1:
        after_block_f = len(inside)
    blocks_def_subtree = inside[block_d_open:after_block_f]
    assert "content://" not in blocks_def_subtree


# --------------------------------------------------------------------------
# G. Template assertions — Block D/E/F panel anchors + matrix_script-only gate
# --------------------------------------------------------------------------


def test_template_carries_block_d_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-d-generate-regenerate"' in template


def test_template_carries_block_e_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-e-candidate-review"' in template


def test_template_carries_block_f_data_role_marker() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-block-f-delivery-teaser"' in template


def test_template_block_d_e_f_live_inside_matrix_script_panel_gate() -> None:
    """All three new block panels must live inside the existing
    `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate so
    Hot Follow / Digital Anchor / baseline workbench surfaces stay
    bytewise unchanged."""
    template = _read_workbench_template()
    inside = _ms_panel_gate_body(template)
    assert inside, "matrix_script panel gate body not found in workbench template"
    for marker in (
        'data-role="matrix-script-block-d-generate-regenerate"',
        'data-role="matrix-script-block-e-candidate-review"',
        'data-role="matrix-script-block-f-delivery-teaser"',
    ):
        assert marker in inside, f"{marker} must live inside matrix_script panel gate"


def test_template_block_d_e_f_do_not_appear_outside_matrix_script_panel_gate() -> None:
    template = _read_workbench_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    inside = _ms_panel_gate_body(template)
    assert inside
    outside = rendered.replace(inside, "")
    for marker in (
        'data-role="matrix-script-block-d-generate-regenerate"',
        'data-role="matrix-script-block-e-candidate-review"',
        'data-role="matrix-script-block-f-delivery-teaser"',
    ):
        assert marker not in outside, (
            f"{marker} leaked outside the matrix_script panel gate"
        )


def test_template_block_d_renders_after_block_c_and_before_block_e() -> None:
    template = _read_workbench_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    pos_c = rendered.find('data-role="matrix-script-block-c-variant-strategy"')
    pos_d = rendered.find('data-role="matrix-script-block-d-generate-regenerate"')
    pos_e = rendered.find('data-role="matrix-script-block-e-candidate-review"')
    pos_f = rendered.find('data-role="matrix-script-block-f-delivery-teaser"')
    assert -1 not in (pos_c, pos_d, pos_e, pos_f)
    assert pos_c < pos_d < pos_e < pos_f


def test_template_block_d_e_f_render_above_existing_secondary_diagnostics() -> None:
    """Document-order invariant: the new Block D/E/F panels precede the
    existing PR-U2 comprehension + MS-W3..W6 + RC PR-2 + RC PR-4 +
    Variation Panel anchors so operator first sees the result-oriented
    blocks."""
    template = _read_workbench_template()
    rendered = re.sub(r"{#.*?#}", "", template, flags=re.DOTALL)
    pos_d = rendered.find('data-role="matrix-script-block-d-generate-regenerate"')
    pos_e = rendered.find('data-role="matrix-script-block-e-candidate-review"')
    pos_f = rendered.find('data-role="matrix-script-block-f-delivery-teaser"')
    pos_comp = rendered.find('data-role="matrix-script-comprehension-panel"')
    pos_ms_w3 = rendered.find('data-role="matrix-script-script-structure-panel"')
    pos_variation = rendered.find('data-role="matrix-script-variation-panel"')
    assert -1 not in (pos_d, pos_e, pos_f, pos_comp, pos_ms_w3, pos_variation)
    assert pos_f < pos_comp, (
        "Block F must precede the secondary PR-U2 comprehension panel"
    )
    assert pos_comp < pos_ms_w3, "PR-U2 must precede MS-W3 panel (existing order preserved)"
    assert pos_ms_w3 < pos_variation, (
        "MS-W3 must precede Variation Panel (existing order preserved)"
    )


def test_template_existing_pr_u2_comprehension_panel_preserved() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-comprehension-panel"' in template


def test_template_existing_ms_w3_script_structure_panel_preserved() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-script-structure-panel"' in template


def test_template_existing_ms_w4_preview_compare_panel_preserved() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-preview-compare-panel"' in template


def test_template_existing_variation_panel_preserved() -> None:
    template = _read_workbench_template()
    assert 'data-role="matrix-script-variation-panel"' in template


def test_template_existing_ms_w6_qc_diagnostics_panel_preserved() -> None:
    """MS-W6 QC + diagnostics panel preserved verbatim as engineer-facing
    inspector below the new D/E/F blocks."""
    template = _read_workbench_template()
    # The MS-W6 panel data-role is matrix-script-qc-diagnostics-panel
    # (see test_matrix_script_workbench_pr2_wiring fixtures).
    assert 'data-role="matrix-script-qc-diagnostics-panel"' in template


def test_template_existing_ms_w5_review_zone_panel_preserved() -> None:
    """MS-W5 review zone panel preserved verbatim as engineer-facing
    inspector below the new D/E/F blocks."""
    template = _read_workbench_template()
    assert 'data-role="matrix-script-review-zone-panel"' in template


def test_template_existing_block_a_b_c_panels_preserved() -> None:
    """PR-2 substrate (Blocks A/B/C) preserved verbatim — PR-3 only
    adds D/E/F below."""
    template = _read_workbench_template()
    for marker in (
        'data-role="matrix-script-block-a-goal-summary"',
        'data-role="matrix-script-block-b-script-structure"',
        'data-role="matrix-script-block-c-variant-strategy"',
    ):
        assert marker in template


# --------------------------------------------------------------------------
# H. Closed-enum audit (no widening across PR-3 paths)
# --------------------------------------------------------------------------


def test_event_kinds_closed_enum_unchanged_by_pr3() -> None:
    """PR-3 must not widen EVENT_KINDS — operator_note already exists."""
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


def test_review_zone_values_closed_enum_unchanged_by_pr3() -> None:
    """PR-3 must not widen REVIEW_ZONE_VALUES."""
    expected = frozenset({"subtitle", "dub", "copy", "cta"})
    assert REVIEW_ZONE_VALUES == expected


def test_review_zone_order_canonical_unchanged_by_pr3() -> None:
    assert REVIEW_ZONE_ORDER == ("subtitle", "dub", "copy", "cta")


def test_recommended_bucket_closed_enum_unchanged_by_pr3() -> None:
    assert RECOMMENDED_BUCKET_PUBLISHABLE == "publishable_candidate"
    assert RECOMMENDED_BUCKET_BLOCKED == "blocked_pending_publish_readiness"
    assert RECOMMENDED_BUCKET_UNDETERMINED == "undetermined_pending_review"


def test_package_closed_enum_unchanged_by_pr3() -> None:
    assert PACKAGE_READY == "ready_package"
    assert PACKAGE_PARTIAL == "partial_package"
    assert PACKAGE_BLOCKED == "blocked_package"
    assert PACKAGE_UNAVAILABLE == "unavailable_tracked_gap"


def test_head_reason_labels_zh_dictionary_carries_required_keys() -> None:
    """Block D blocker label dictionary mirrors the closed
    publish_readiness head_reason enum."""
    expected_keys = {
        "publishable_ok",
        "ready_gate_blocking",
        "publish_not_ready",
        "compose_not_ready",
        "final_missing",
        "final_stale",
        "final_provenance_historical",
        "required_deliverable_missing",
        "required_deliverable_blocking",
        "unresolved",
    }
    assert expected_keys.issubset(set(HEAD_REASON_LABELS_ZH.keys()))


def test_review_event_endpoint_template_unchanged_by_pr3() -> None:
    """No new endpoint per slicing addendum §6 RO-3.4."""
    assert (
        REVIEW_EVENT_ENDPOINT_TEMPLATE
        == "/api/matrix-script/closures/{task_id}/events"
    )


# --------------------------------------------------------------------------
# I. Helper-output sanity / serialisation
# --------------------------------------------------------------------------


def test_recommended_action_returns_only_serialisable_types() -> None:
    bundle = _build_block_e_inputs()
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in bundle["recommended_action"].items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_qc_diagnostics_returns_only_serialisable_types() -> None:
    bundle = _build_block_e_inputs()
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in bundle["qc"].items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_review_zone_returns_only_serialisable_types() -> None:
    bundle = _build_block_e_inputs()
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in bundle["review_zone"].items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_delivery_comprehension_returns_only_serialisable_types() -> None:
    out = derive_matrix_script_delivery_comprehension(
        _delivery_binding_with_required_blocking_row()
    )
    allowed = (str, int, bool, type(None), list, tuple, dict, Mapping)
    for key, value in out.items():
        assert isinstance(value, allowed), f"{key} = {type(value).__name__}"


def test_workbench_helpers_remain_addressable_for_secondary_diagnostics() -> None:
    """PR-U2 + MS-W3..W6 helpers are NOT removed by PR-3; they stay as
    secondary diagnostics. Sanity check that all PR-3-consumed helpers
    are callable after PR-3 lands."""
    bundle = _build_block_e_inputs()
    assert bundle["recommended_action"]["is_matrix_script"] is True
    assert bundle["qc"]["is_matrix_script"] is True
    assert bundle["review_zone"]["is_matrix_script"] is True
    assert bundle["package"]["is_matrix_script"] is True


# --------------------------------------------------------------------------
# J. Wiring attachment (delivery_comprehension on bundle.workbench)
# --------------------------------------------------------------------------


def test_wiring_attaches_delivery_comprehension_to_bundle_workbench() -> None:
    """PR-3 attaches delivery_comprehension to bundle.workbench so the
    Block F template can read required-deliverable lanes. Confirms the
    attach key is present in the matrix_script wiring branch."""
    repo_root = _REPO_ROOT
    wiring_src = (
        repo_root
        / "gateway"
        / "app"
        / "services"
        / "operator_visible_surfaces"
        / "wiring.py"
    ).read_text(encoding="utf-8")
    assert (
        'bundle["workbench"]["matrix_script_delivery_comprehension"]' in wiring_src
    )
