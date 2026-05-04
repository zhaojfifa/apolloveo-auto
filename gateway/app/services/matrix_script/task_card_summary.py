"""Matrix Script Task Area card summary projection (PR-U1).

Pure presentation-layer projection over the existing task row dict. Reads
only fields already present on the row (``title``, ``board_bucket``,
``head_reason``, ``line_specific_refs[]``, ``config.next_surfaces``). Emits
operator-language strings for the four Task Area card fields per the
user-mandated PR-U1 narrowing of the signed gate spec at
``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``:

- 主题 (subject)
- 当前变体数 (current variation count)
- 可发布版本数 (publishable variation count)
- 当前阻塞项 (current blocker)

plus the operator-language tri-state badge label
(``blocked`` / ``ready`` / ``publishable`` → ``阻塞中`` / ``就绪`` / ``可发布``)
and the two action hrefs (``进入工作台`` / ``跳交付中心``).

Hard discipline (binding):

- No contract mutation; no projection mutation; no packet write-back.
- ``publishable_variation_count`` is intentionally returned as ``None``
  whenever the cross-line unified publish_readiness producer (Plan D1) is
  not yet emitted — that producer is **forbidden in this Plan E phase**
  per gate spec §4.7. The template renders ``None`` as ``—`` with a
  small operator-language tooltip naming the gating.
- ``current_blocker_label`` translates the existing ``head_reason``
  English engineering shorthand from
  ``gateway/app/services/operator_visible_surfaces/projections.py::derive_board_publishable``
  to operator language for the closed enumerated codes; falls through to
  the raw string for unknown codes (no new code introduced).
- No provider / model / vendor / engine identifier ever appears in the
  return value (validator R3 + sanitization at the operator boundary).

This module is consumed only by ``gateway/app/services/task_router_presenters.py::build_tasks_page_rows``
for rows where ``row["kind"] == "matrix_script"``. Hot Follow rows and
Digital Anchor rows MUST NOT receive the summary; the caller's
gating preserves their bytewise-unchanged Task Area rendering.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

MATRIX_SCRIPT_LINE_ID = "matrix_script"
VARIATION_REF_ID = "matrix_script_variation_matrix"

# Operator-language tri-state badge labels for the Task Area card.
# Keys mirror the existing `board_bucket` enum produced by
# `task_router_presenters.build_tasks_page_rows` so the template can read
# the badge label off the same authoritative tri-state.
TRI_STATE_BADGE_LABELS = {
    "blocked": "阻塞中",
    "ready": "就绪",
    "publishable": "可发布",
}

# Operator-language translation of the closed `head_reason` enum from
# `derive_board_publishable`. Unknown codes fall through to the raw string.
_BLOCKER_LABEL_MAP = {
    "publish_ready_pending": "等待生成",
    "compose_ready_pending": "合成未就绪",
    "delivery_required_unresolved": "必交付物缺失",
    "scene_pack_blocking_disallowed": "配套素材阻塞被禁止",
    "final_fresh": "终片需重新生成",
    "subtitles_pending": "字幕未就绪",
    "dub_pending": "配音未就绪",
}

# Sentinel: the cross-line unified publish_readiness producer (Plan D1) is
# forbidden in this Plan E phase per gate spec §4.7. Until that producer
# lands, "publishable variation count" is unknown by construction.
PUBLISHABLE_COUNT_GATED_BY_D1 = "gated_by_unified_publish_readiness_producer"


def _is_matrix_script_row(row: Mapping[str, Any]) -> bool:
    kind = str(row.get("kind") or row.get("category_key") or row.get("platform") or "").strip().lower()
    return kind in {MATRIX_SCRIPT_LINE_ID, "matrix-script"}


def _variation_cells(row: Mapping[str, Any]) -> list[Any]:
    """Read ``variation_matrix.delta.cells`` from the row's
    ``line_specific_refs[]`` if present. Returns an empty list otherwise.
    """
    refs = row.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        packet = row.get("packet")
        if isinstance(packet, Mapping):
            refs = packet.get("line_specific_refs")
    if not isinstance(refs, (list, tuple)):
        return []
    for item in refs:
        if not isinstance(item, Mapping):
            continue
        if item.get("ref_id") != VARIATION_REF_ID:
            continue
        delta = item.get("delta")
        if not isinstance(delta, Mapping):
            return []
        cells = delta.get("cells")
        return list(cells) if isinstance(cells, (list, tuple)) else []
    return []


def _next_surfaces(row: Mapping[str, Any]) -> Mapping[str, Any]:
    config = row.get("config")
    if not isinstance(config, Mapping):
        return {}
    surfaces = config.get("next_surfaces")
    return surfaces if isinstance(surfaces, Mapping) else {}


def _operator_blocker_label(head_reason: Optional[str]) -> Optional[str]:
    if not head_reason:
        return None
    code = str(head_reason).strip()
    if not code:
        return None
    return _BLOCKER_LABEL_MAP.get(code, code)


def derive_matrix_script_task_card_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project the four Task Area card fields + tri-state badge label +
    action hrefs for a single Matrix Script row.

    Returns an empty dict for non-Matrix-Script rows so the caller can
    safely attach the result without further gating; the template gates
    rendering on ``data-line == "matrix_script"`` regardless.
    """
    if not _is_matrix_script_row(row):
        return {}

    task_id = str(row.get("task_id") or row.get("id") or "").strip()
    subject = row.get("title") or ""
    cells = _variation_cells(row)
    current_variation_count = len(cells)

    bucket = str(row.get("board_bucket") or "ready").strip().lower()
    if bucket not in TRI_STATE_BADGE_LABELS:
        bucket = "ready"
    tri_state_label = TRI_STATE_BADGE_LABELS[bucket]

    head_reason = row.get("head_reason")
    blocker_label = _operator_blocker_label(head_reason if isinstance(head_reason, str) else None)

    surfaces = _next_surfaces(row)
    workbench_href = (
        str(surfaces.get("workbench") or "").strip()
        or (f"/tasks/{task_id}" if task_id else "")
    )
    delivery_href = (
        str(surfaces.get("delivery") or "").strip()
        or (f"/tasks/{task_id}/publish" if task_id else "")
    )

    return {
        "is_matrix_script": True,
        "subject_label": "主题",
        "subject_value": str(subject),
        "current_variation_count_label": "当前变体数",
        "current_variation_count_value": current_variation_count,
        "publishable_variation_count_label": "可发布版本数",
        # None renders as "—" in the template; gating reason exposed for tooltip.
        "publishable_variation_count_value": None,
        "publishable_variation_count_gated_by": PUBLISHABLE_COUNT_GATED_BY_D1,
        "publishable_variation_count_tooltip": "可发布版本数将在统一 publish_readiness 上线后开放",
        "current_blocker_label": "当前阻塞项",
        "current_blocker_value": blocker_label,
        "tri_state_bucket": bucket,
        "tri_state_badge_label": tri_state_label,
        "workbench_action_label": "进入工作台",
        "workbench_action_href": workbench_href,
        "delivery_action_label": "跳交付中心",
        "delivery_action_href": delivery_href,
    }


__all__ = [
    "MATRIX_SCRIPT_LINE_ID",
    "PUBLISHABLE_COUNT_GATED_BY_D1",
    "TRI_STATE_BADGE_LABELS",
    "VARIATION_REF_ID",
    "derive_matrix_script_task_card_summary",
]
