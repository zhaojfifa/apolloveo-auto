"""Matrix Script Workbench comprehension projection (PR-U2).

Pure presentation-layer projection over the existing
``matrix_script_workbench_variation_surface_v1`` projection plus the
existing ``ops_workbench_panel`` resolver shape. Reads only fields that
are already projected by:

- ``gateway/app/services/matrix_script/workbench_variation_surface.py``
- ``gateway/app/services/operator_visible_surfaces/projections.py``
  (``derive_workbench_panel_dispatch``)

and emits operator-language strings + small derived counts that drive the
Matrix Script Workbench comprehension block per the user-mandated PR-U2
narrowing of the signed gate spec at
``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``:

- Four-zone alignment header (``content_structure`` / ``scene_plan`` /
  ``audio_plan`` / ``language_plan``) with each zone showing the bound
  ``line_specific_refs[]`` ref ids per ``binds_to``.
- Task identity / next-step clarity block ("此阶段无需操作 ·
  Phase B 已自动生成" because the §8.C deterministic Phase B authoring is
  the only authoring path in this Plan E phase per gate spec §4.3 — no
  operator-driven Phase B authoring affordance).
- Variation summary (total cells / total axes / total slots) + a
  readability-grouping hint (axis-tuple grouping over a configurable
  threshold).
- Operator-language ``ready_state`` mirror.

Hard discipline (binding under gate spec §4):

- No projection mutation; no packet write-back; no contract mutation.
- No new ``panel_kind`` enum value; no new ``ref_id`` enumerated.
- No provider / model / vendor / engine identifier in the return value
  (validator R3).
- No D1 unified ``publish_readiness`` producer; no D2 / D3 / D4; no
  Asset Library; no promote service.
- No Hot Follow surface change; no Digital Anchor surface change.
- The ``next_step_zone`` returned is always ``"system"`` in this phase
  because operator-driven Phase B authoring is forbidden per gate spec
  §4.3; the Workbench Variation Panel stays read-only at the projection
  level. Future Plan E phases may introduce ``"operator"`` next-step
  zones; they require their own gate-spec authoring step.

This module is consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
when the panel resolver dispatches to ``panel_kind="matrix_script"``.
Hot Follow / Digital Anchor / Baseline workbench surfaces never receive
the comprehension bundle.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# Operator-language labels for the four generic plan zones from the
# factory architecture (`docs/architecture/factory_four_layer_architecture_baseline_v1.md`).
# These zone ids mirror existing factory contract names; they are NOT
# new contract truth — they re-use the `binds_to` values that
# Matrix Script `line_specific_refs[]` already carry.
FOUR_ZONE_LABELS = (
    ("content_structure", "内容结构", ("factory_input_contract_v1", "factory_content_structure_contract_v1")),
    ("scene_plan", "场景规划", ("factory_scene_plan_contract_v1",)),
    ("audio_plan", "音频规划", ("factory_audio_plan_contract_v1",)),
    ("language_plan", "语言规划", ("factory_language_plan_contract_v1",)),
)

# Operator-language ready_state labels. Falls through verbatim for
# unknown values so future ready_state codes degrade gracefully.
_READY_STATE_LABELS = {
    "ready": "已就绪",
    "pending": "等待生成",
    "in_progress": "进行中",
    "blocked": "已阻塞",
    "error": "错误",
    "draft": "草稿",
}

# Default cell-count threshold above which the template SHOULD switch to
# axis-tuple grouping for readability. Presentation-only hint; no
# contract field consulted.
DEFAULT_CELL_GROUPING_THRESHOLD = 6


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _bound_refs_for_zone(
    line_specific_refs: Iterable[Mapping[str, Any]],
    zone_binds: tuple[str, ...],
) -> list[dict[str, str]]:
    """Return the subset of ``line_specific_refs[]`` whose ``binds_to``
    intersects ``zone_binds``. Each entry exposes ``ref_id`` + ``version``
    only — no path, no delta, no nested truth.
    """
    bound: list[dict[str, str]] = []
    for ref in line_specific_refs:
        if not isinstance(ref, Mapping):
            continue
        binds_to = _safe_list(ref.get("binds_to"))
        if not any(b in zone_binds for b in binds_to):
            continue
        bound.append(
            {
                "ref_id": str(ref.get("ref_id") or ""),
                "version": str(ref.get("version") or ""),
            }
        )
    return bound


def _operator_ready_state_label(ready_state: Any) -> str:
    if not ready_state:
        return "—"
    code = str(ready_state).strip()
    if not code:
        return "—"
    return _READY_STATE_LABELS.get(code, code)


def _axis_tuple_groupings(cells: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Group cells by their axis_selections tuple for operator readability.

    Returns a list of `{group_key, count, sample_cell_ids}` dicts ordered
    by descending count then by `group_key` for stability. Only emits the
    `cell_id` for the first three cells of each group as a sample (kept
    short to avoid runaway template size on large variation matrices).
    """
    groups: dict[str, dict[str, Any]] = {}
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        axis_selections = _safe_mapping(cell.get("axis_selections"))
        # Stable canonical group key — sorted axis_id=value pairs.
        group_key = " · ".join(
            f"{axis_id}={value}" for axis_id, value in sorted(axis_selections.items())
        ) or "—"
        bucket = groups.setdefault(
            group_key,
            {"group_key": group_key, "count": 0, "sample_cell_ids": []},
        )
        bucket["count"] += 1
        if len(bucket["sample_cell_ids"]) < 3:
            bucket["sample_cell_ids"].append(str(cell.get("cell_id") or ""))
    return sorted(groups.values(), key=lambda g: (-g["count"], g["group_key"]))


def derive_matrix_script_workbench_comprehension(
    variation_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
    *,
    cell_grouping_threshold: int = DEFAULT_CELL_GROUPING_THRESHOLD,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench comprehension bundle.

    Inputs:
    - ``variation_surface`` — the
      ``matrix_script_workbench_variation_surface_v1`` projection from
      ``project_workbench_variation_surface``.
    - ``line_specific_panel`` — the workbench panel resolver output from
      ``derive_workbench_panel_dispatch`` (carries ``panel_kind`` +
      ``refs[]`` with ``ref_id`` / ``binds_to``).

    Returns an empty dict when the panel is not Matrix Script, so the
    caller can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if str(panel.get("panel_kind") or "").strip().lower() != "matrix_script":
        return {}

    surface = _safe_mapping(variation_surface)
    variation_plan = _safe_mapping(surface.get("variation_plan"))
    copy_bundle = _safe_mapping(surface.get("copy_bundle"))
    attribution = _safe_mapping(surface.get("attribution_refs"))
    publish_feedback = _safe_mapping(surface.get("publish_feedback_projection"))

    axes = _safe_list(variation_plan.get("axes"))
    cells = _safe_list(variation_plan.get("cells"))
    slots = _safe_list(copy_bundle.get("slots"))
    attribution_refs = _safe_list(attribution.get("line_specific_refs"))
    panel_refs = _safe_list(panel.get("refs"))

    # Prefer the attribution_refs list (carries `binds_to` + `version`)
    # for the zone lookup; fall back to the panel resolver refs if the
    # attribution list is absent on this projection version.
    zone_source = attribution_refs if attribution_refs else panel_refs

    four_zone_alignment = []
    for zone_id, zone_label_zh, zone_binds in FOUR_ZONE_LABELS:
        bound = _bound_refs_for_zone(zone_source, zone_binds)
        four_zone_alignment.append(
            {
                "zone_id": zone_id,
                "zone_label_zh": zone_label_zh,
                "bound_refs": bound,
                "is_bound": bool(bound),
                "empty_label_zh": "—（此线未绑定）",
            }
        )

    cell_count = len(cells)
    axes_count = len(axes)
    slots_count = len(slots)

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Matrix Script · 工作台理解",
        "panel_subtitle_zh": "对齐 content_structure / scene_plan / audio_plan / language_plan 四区；只读投射 · 不发明事实",
        "four_zone_alignment_label_zh": "四区对齐",
        "four_zone_alignment": four_zone_alignment,
        "task_identity_label_zh": "任务身份",
        "task_identity_summary": {
            "axes_count": axes_count,
            "cells_count": cell_count,
            "slots_count": slots_count,
            "ready_state": surface.get("readyState") or publish_feedback.get("ready_state"),
            "ready_state_label_zh": _operator_ready_state_label(
                surface.get("readyState") or publish_feedback.get("ready_state")
            ),
        },
        "next_step_label_zh": "此阶段无需操作 · Phase B 已自动生成",
        "next_step_zone": "system",
        "next_step_explanation_zh": (
            "Phase B 由 §8.C 确定性生成；本阶段网关禁止运营手动改动 axes / cells / slots（见 gate spec §4.3）。"
        ),
        "variation_summary_label_zh": "变体概要",
        "variation_summary": {
            "total_cells": cell_count,
            "total_axes": axes_count,
            "total_slots": slots_count,
            "summary_text_zh": (
                f"共 {cell_count} 组变体 · {axes_count} 条 axis · {slots_count} 个 slot"
            ),
        },
        "cell_grouping_threshold": int(cell_grouping_threshold),
        "should_group_cells": cell_count > int(cell_grouping_threshold),
        "axis_tuple_groupings": _axis_tuple_groupings(cells) if cell_count > int(cell_grouping_threshold) else [],
    }


__all__ = [
    "DEFAULT_CELL_GROUPING_THRESHOLD",
    "FOUR_ZONE_LABELS",
    "derive_matrix_script_workbench_comprehension",
]
