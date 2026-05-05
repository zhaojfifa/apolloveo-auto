"""Matrix Script Workbench C — preview-compare view (OWC-MS PR-2 / MS-W4).

Pure presentation-layer projection over three already-existing surfaces:

- ``matrix_script_workbench_variation_surface_v1`` from
  :mod:`gateway.app.services.matrix_script.workbench_variation_surface`
  (axes / cells / slot bundle).
- ``matrix_script_delivery_binding_v1`` from
  :mod:`gateway.app.services.matrix_script.delivery_binding`
  (per-row ``artifact_lookup`` — closed contract per
  ``docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md``).
- The unified ``publish_readiness`` projection from
  :mod:`gateway.app.services.operator_visible_surfaces.publish_readiness`
  (single-producer rule per
  ``docs/contracts/publish_readiness_contract_v1.md``).

Authority:

- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W4 (Workbench C 预览对比区:
  side-by-side multi-variation preview using B4 ``artifact_lookup`` rows
  now backed by PR-1 ``final_provenance``; 差异项提示 derived from existing
  axis-tuple comparator; 推荐版本标识 derived from PR-1 unified
  ``publish_readiness`` producer + closure 操作历史).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1C — 版本 A / B / C
  并排预览 / 差异项提示 / 推荐版本标识.

Hard discipline (binding under OWC-MS gate spec §4):

- No second producer for publishability; the recommended-version label
  derives strictly from ``publish_readiness.publishable`` +
  ``head_reason`` + ``consumed_inputs.first_blocking_reason``.
- No advisory derivation; advisories are read verbatim from
  ``publish_readiness.blocking_advisories`` when needed (consumed by
  MS-W6 — not duplicated here).
- No new ``deliverable_id`` / ``ref_id`` / contract field.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No template-invented preview state; non-Matrix-Script panels return
  ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "matrix_script"`` branch.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .delivery_comprehension import _artifact_status_label_zh
from .publish_feedback_closure import VARIATION_REF_ID

# Operator-language label set for recommended-version marker derivation.
RECOMMENDED_BUCKET_PUBLISHABLE = "publishable_candidate"
RECOMMENDED_BUCKET_BLOCKED = "blocked_pending_publish_readiness"
RECOMMENDED_BUCKET_UNDETERMINED = "undetermined_pending_review"

_RECOMMENDED_LABELS_ZH = {
    RECOMMENDED_BUCKET_PUBLISHABLE: "推荐 · 可发布候选",
    RECOMMENDED_BUCKET_BLOCKED: "暂不推荐 · 发布门禁阻塞",
    RECOMMENDED_BUCKET_UNDETERMINED: "—（待校对完成 + publish_readiness 上线后收敛）",
}


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _slots_by_id(slots: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for slot in slots:
        if not isinstance(slot, Mapping):
            continue
        slot_id = slot.get("slot_id")
        if isinstance(slot_id, str) and slot_id:
            index[slot_id] = slot
    return index


def _variation_manifest_artifact_lookup(deliverables: Iterable[Mapping[str, Any]]) -> Any:
    """Return the artifact_lookup payload from the variation_manifest row.

    The Matrix Script delivery binding emits the variation manifest as a
    single row keyed by ``deliverable_id="matrix_script_variation_manifest"``
    (see :mod:`gateway.app.services.matrix_script.delivery_binding`). It
    carries the resolved ``artifact_lookup`` for the variation matrix as
    a whole — per-cell artifact handles do not yet exist on the contract
    surface (gated by future Plan E variation-level provenance). The
    preview compare view applies the manifest-level artifact_lookup to
    every variation row and explains the per-cell granularity gap in
    operator language.
    """
    for row in deliverables:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("deliverable_id") or "") == "matrix_script_variation_manifest":
            return row.get("artifact_lookup")
    return None


def _diff_hints_from_axes(
    axes: Iterable[Mapping[str, Any]],
    cells: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Derive per-axis diff hints by walking distinct values across cells.

    Returns one entry per axis_id present on the axes list, listing the
    distinct ``axis_selections[axis_id]`` values observed across the
    cells. An axis with a single distinct value across all cells is
    marked ``is_differing=False`` (no diff hint emitted as actionable).
    Stable ordering by axis_id position in the axes list.
    """
    hints: list[dict[str, Any]] = []
    cell_list = [c for c in cells if isinstance(c, Mapping)]
    for axis in axes:
        if not isinstance(axis, Mapping):
            continue
        axis_id = axis.get("axis_id")
        if not isinstance(axis_id, str) or not axis_id:
            continue
        values: list[Any] = []
        seen: set[str] = set()
        for cell in cell_list:
            selections = _safe_mapping(cell.get("axis_selections"))
            value = selections.get(axis_id)
            key = repr(value)
            if key not in seen:
                seen.add(key)
                values.append(value)
        hints.append(
            {
                "axis_id": axis_id,
                "distinct_value_count": len(values),
                "distinct_values": values,
                "is_differing": len(values) > 1,
            }
        )
    return hints


def _published_status_for_variation(
    closure: Mapping[str, Any] | None, variation_id: str
) -> dict[str, Any]:
    """Read closure publish_status / publish_url for a variation, if any.

    Reads the contract-frozen ``variation_feedback[]`` row (per
    :mod:`publish_feedback_closure`); never mutates the closure; returns
    ``{publish_status: "pending", publish_url: None}`` when the closure
    is absent or carries no row for the variation.
    """
    if not isinstance(closure, Mapping):
        return {"publish_status": "pending", "publish_url": None}
    rows = _safe_list(closure.get("variation_feedback"))
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("variation_id") or "") == variation_id:
            return {
                "publish_status": str(row.get("publish_status") or "pending"),
                "publish_url": row.get("publish_url"),
            }
    return {"publish_status": "pending", "publish_url": None}


def _recommended_marker(
    *,
    publish_readiness: Mapping[str, Any],
    published_status: str,
) -> dict[str, Any]:
    """Compute the recommended-version marker per gate spec MS-W4.

    Recommended marker derives from PR-1 ``publish_readiness`` only:

    - ``publishable_candidate`` when ``publish_readiness.publishable`` is
      True AND the closure has not already published the variation (a
      published variation is no longer a candidate for "推荐发布").
    - ``blocked_pending_publish_readiness`` when ``publishable`` is False;
      the operator-language reason mirrors the closed
      ``head_reason`` enum.
    - ``undetermined_pending_review`` when no ``publish_readiness`` is
      provided (caller did not have the bundle key).
    """
    if not isinstance(publish_readiness, Mapping):
        return {
            "bucket": RECOMMENDED_BUCKET_UNDETERMINED,
            "label_zh": _RECOMMENDED_LABELS_ZH[RECOMMENDED_BUCKET_UNDETERMINED],
            "explanation_zh": (
                "未提供 publish_readiness 投射；推荐标识需要统一 publish_readiness 上线。"
            ),
            "head_reason": None,
        }
    publishable = bool(publish_readiness.get("publishable"))
    head_reason = publish_readiness.get("head_reason")
    if publishable and published_status != "published":
        return {
            "bucket": RECOMMENDED_BUCKET_PUBLISHABLE,
            "label_zh": _RECOMMENDED_LABELS_ZH[RECOMMENDED_BUCKET_PUBLISHABLE],
            "explanation_zh": (
                "publish_readiness=publishable 且未在 closure 中标记为已发布 → 列入推荐候选。"
            ),
            "head_reason": head_reason,
        }
    if not publishable:
        return {
            "bucket": RECOMMENDED_BUCKET_BLOCKED,
            "label_zh": _RECOMMENDED_LABELS_ZH[RECOMMENDED_BUCKET_BLOCKED],
            "explanation_zh": (
                "publish_readiness 阻塞中；以 publish_readiness.head_reason 为准展示阻塞原因。"
            ),
            "head_reason": head_reason,
        }
    return {
        "bucket": RECOMMENDED_BUCKET_UNDETERMINED,
        "label_zh": _RECOMMENDED_LABELS_ZH[RECOMMENDED_BUCKET_UNDETERMINED],
        "explanation_zh": (
            "publish_readiness=publishable，但 closure 已记录该变体已发布；不再列为新推荐。"
        ),
        "head_reason": head_reason,
    }


def derive_matrix_script_preview_compare_view(
    variation_surface: Mapping[str, Any] | None,
    delivery_binding: Mapping[str, Any] | None,
    publish_readiness: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
    *,
    closure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench C 预览对比区 bundle.

    Returns ``{}`` when the panel is not Matrix Script, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script(panel):
        return {}

    surface = _safe_mapping(variation_surface)
    variation_plan = _safe_mapping(surface.get("variation_plan"))
    copy_bundle = _safe_mapping(surface.get("copy_bundle"))
    axes = _safe_list(variation_plan.get("axes"))
    cells = _safe_list(variation_plan.get("cells"))
    slots = _safe_list(copy_bundle.get("slots"))
    slot_index = _slots_by_id(slots)

    binding = _safe_mapping(delivery_binding)
    delivery_pack = _safe_mapping(binding.get("delivery_pack"))
    deliverables = _safe_list(delivery_pack.get("deliverables"))
    manifest_artifact_lookup = _variation_manifest_artifact_lookup(deliverables)
    artifact_status = _artifact_status_label_zh(manifest_artifact_lookup)

    # Distinguish "no publish_readiness provided" (None) from "producer
    # output present but blocked" — the recommended marker buckets the
    # two cases differently.
    pr = (
        _safe_mapping(publish_readiness)
        if isinstance(publish_readiness, Mapping)
        else None
    )

    variations: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        cell_id = str(cell.get("cell_id") or "")
        slot_ref = str(cell.get("script_slot_ref") or "")
        slot = slot_index.get(slot_ref) or {}
        language_scope = _safe_mapping(slot.get("language_scope"))
        target_language = language_scope.get("target_language") or []
        if isinstance(target_language, str):
            target_language = [target_language]
        published = _published_status_for_variation(closure, cell_id)
        recommended = _recommended_marker(
            publish_readiness=pr,
            published_status=published["publish_status"],
        )
        variations.append(
            {
                "variation_id": cell_id,
                "axis_selections": dict(_safe_mapping(cell.get("axis_selections"))),
                "script_slot_ref": slot_ref,
                "slot_body_ref": slot.get("body_ref"),
                "slot_length_hint": slot.get("length_hint"),
                "language_scope": {
                    "source_language": language_scope.get("source_language"),
                    "target_language": list(target_language)
                    if isinstance(target_language, (list, tuple))
                    else [],
                },
                "preview_status_code": artifact_status["status_code"],
                "preview_status_label_zh": artifact_status["status_label_zh"],
                "preview_status_explanation_zh": artifact_status["status_explanation_zh"],
                "publish_status": published["publish_status"],
                "publish_url": published["publish_url"],
                "recommended_bucket": recommended["bucket"],
                "recommended_label_zh": recommended["label_zh"],
                "recommended_explanation_zh": recommended["explanation_zh"],
                "recommended_head_reason": recommended["head_reason"],
            }
        )

    diff_hints = _diff_hints_from_axes(axes, cells)
    differing_axes = [hint["axis_id"] for hint in diff_hints if hint["is_differing"]]
    invariant_axes = [hint["axis_id"] for hint in diff_hints if not hint["is_differing"]]

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Workbench C · 预览对比区",
        "panel_subtitle_zh": (
            "并排呈现多变体预览；artifact_lookup / publish_readiness 由统一上游推断，本面板仅做投射。"
        ),
        "source_ref_id": VARIATION_REF_ID,
        "variation_count": len(variations),
        "variations_label_zh": "变体并排预览（A / B / C …）",
        "variations": variations,
        "diff_hints_label_zh": "差异项提示（按 axis 列出 distinct 值集合）",
        "diff_hints": diff_hints,
        "differing_axes": differing_axes,
        "invariant_axes": invariant_axes,
        "recommended_label_zh": "推荐版本标识",
        "recommended_explanation_zh": (
            "推荐标识由统一 publish_readiness 决定；本视图仅展示其结论，不发明评分。"
        ),
        "per_cell_artifact_granularity_note_zh": (
            "当前 variation_manifest 行只有一个共享 artifact_lookup；待 per-variation provenance 上线后细化为每变体单独解析。"
        ),
    }


__all__ = [
    "RECOMMENDED_BUCKET_BLOCKED",
    "RECOMMENDED_BUCKET_PUBLISHABLE",
    "RECOMMENDED_BUCKET_UNDETERMINED",
    "derive_matrix_script_preview_compare_view",
]
