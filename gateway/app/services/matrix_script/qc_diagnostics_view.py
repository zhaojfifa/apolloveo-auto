"""Matrix Script Workbench E — QC + diagnostics view (OWC-MS PR-2 / MS-W6).

Pure presentation-layer projection over four already-existing surfaces:

- ``publish_readiness`` from
  :mod:`gateway.app.services.operator_visible_surfaces.publish_readiness`
  (single L4 producer per
  ``docs/contracts/publish_readiness_contract_v1.md``;
  ``head_reason`` ∈ closed enum;
  ``blocking_advisories`` from L4 advisory emitter).
- ``matrix_script_delivery_binding_v1`` from
  :mod:`gateway.app.services.matrix_script.delivery_binding`
  (per-row ``required`` / ``blocking_publish`` / ``artifact_lookup``).
- ``matrix_script_delivery_comprehension`` from
  :mod:`gateway.app.services.matrix_script.delivery_comprehension`
  (operator-language lanes + per-row artifact_status + publish-blocking
  explanation; reused for cross-surface consistency).
- ``matrix_script_workbench_variation_surface_v1`` from
  :mod:`gateway.app.services.matrix_script.workbench_variation_surface`
  (slot-level ``length_hint`` for the 时长 quality item).

Authority:

- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W6 (Workbench E
  质检与诊断区: render PR-1 L4 ``advisory_emitter`` output in the
  Matrix Script branch; 风险提示 / 合规提示 / 时长 / 清晰度 /
  字幕可读性 / 产物状态 / ready gate 解释 mapped from existing
  advisory taxonomy; pure presentation; no advisory rule change).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1E.

Hard discipline (binding under OWC-MS gate spec §4):

- No new advisory id / rule / evidence_field; ``blocking_advisories[]``
  is read verbatim from the unified producer.
- No second producer for publishability / final_provenance / advisories.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No template-invented quality state; quality items not yet observable
  on existing truth render the ``"unobservable_pending_upstream"``
  sentinel with operator-language explanation naming the gate.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "matrix_script"`` branch.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

# Operator-language translations for the closed publish_readiness
# `head_reason` enum (from
# `docs/contracts/publish_readiness_contract_v1.md`). Strings are
# operator-readable; the closed enum membership is enforced by
# `compute_publish_readiness`. Unknown values fall through verbatim so
# any future enum additions degrade gracefully.
HEAD_REASON_LABELS_ZH = {
    "publishable_ok": "可发布 · 无阻塞",
    "ready_gate_blocking": "ready gate 阻塞",
    "publish_not_ready": "发布前置项未就绪",
    "compose_not_ready": "合成前置项未就绪",
    "final_missing": "成片缺失",
    "final_stale": "成片过期",
    "final_provenance_historical": "当前 provenance 仍为历史尝试，未推进到当前 attempt",
    "required_deliverable_missing": "必交付物缺失",
    "required_deliverable_blocking": "必交付物阻塞发布",
    "unresolved": "未解析",
}

# Quality-item metadata. The "duration / clarity / subtitle readability"
# triplet is enumerated by the gate spec §3 MS-W6; the items below are
# emitted unconditionally so reviewers walking ENGINEERING_RULES §13
# product-flow module presence can see all three. Items not yet
# observable on existing truth render the
# ``"unobservable_pending_upstream"`` sentinel.
QUALITY_ITEM_DURATION = "duration"
QUALITY_ITEM_CLARITY = "clarity"
QUALITY_ITEM_SUBTITLE_READABILITY = "subtitle_readability"

QUALITY_ITEM_LABELS_ZH = {
    QUALITY_ITEM_DURATION: "时长",
    QUALITY_ITEM_CLARITY: "清晰度",
    QUALITY_ITEM_SUBTITLE_READABILITY: "字幕可读性",
}

QUALITY_STATUS_OBSERVED = "observed"
QUALITY_STATUS_UNOBSERVABLE = "unobservable_pending_upstream"

UNOBSERVABLE_LABEL_ZH = "—（待上游 provenance / 字幕校对落地后可观察）"


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _ready_gate_explanation(
    publish_readiness: Mapping[str, Any],
) -> dict[str, Any]:
    head_reason = publish_readiness.get("head_reason")
    inputs = _safe_mapping(publish_readiness.get("consumed_inputs"))
    raw = inputs.get("first_blocking_reason")
    label = (
        HEAD_REASON_LABELS_ZH.get(str(head_reason)) if head_reason is not None else None
    )
    return {
        "publishable": bool(publish_readiness.get("publishable")),
        "head_reason": head_reason,
        "head_reason_label_zh": label or (str(head_reason) if head_reason else "—"),
        "first_blocking_reason_raw": raw,
        "publish_ready": bool(inputs.get("ready_gate_publish_ready")),
        "compose_ready": bool(inputs.get("ready_gate_compose_ready")),
        "final_fresh": bool(inputs.get("final_fresh")),
        "final_provenance": inputs.get("final_provenance"),
        "blocking_count": int(inputs.get("blocking_count") or 0),
    }


def _risk_items_from_advisories(
    blocking_advisories: Iterable[Any],
) -> list[dict[str, Any]]:
    """Render each L4 advisory verbatim — no new ids / hints / evidence."""
    items: list[dict[str, Any]] = []
    for advisory in blocking_advisories:
        if not isinstance(advisory, Mapping):
            continue
        items.append(
            {
                "advisory_id": advisory.get("id"),
                "level": advisory.get("level"),
                "kind": advisory.get("kind"),
                "operator_hint": advisory.get("operator_hint"),
                "explanation_zh": advisory.get("explanation"),
                "recommended_next_action": advisory.get("recommended_next_action"),
            }
        )
    return items


def _compliance_items() -> list[dict[str, Any]]:
    """Render the closed compliance reminders the operator surface owns.

    These are documentation-only operator reminders; they do NOT carry
    new compliance truth. The reminders re-state the operator-visible
    surface red lines from
    ``docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`` §2.5 +
    §5.3 (Workbench red lines): no provider / model / vendor controls
    on this surface; helper layer is explanation-only.
    """
    return [
        {
            "compliance_id": "no_provider_controls",
            "label_zh": "前台不出现 vendor / model / provider / engine 控件",
            "explanation_zh": (
                "供应商差异在后端 capability_plan / worker / tool registry 装配；本面板仅展示业务结果。"
            ),
        },
        {
            "compliance_id": "no_phase_b_authoring",
            "label_zh": "本面板不授权 Phase B 创作",
            "explanation_zh": (
                "axes / cells / slots 由 §8.C 确定性生成；运营在工作台层不修改 source_script（OWC-MS gate spec §4.1）。"
            ),
        },
    ]


def _quality_item(
    quality_id: str, *, value: Any, value_label_zh: str | None
) -> dict[str, Any]:
    if value is None:
        return {
            "quality_id": quality_id,
            "label_zh": QUALITY_ITEM_LABELS_ZH[quality_id],
            "status_code": QUALITY_STATUS_UNOBSERVABLE,
            "value": None,
            "value_label_zh": UNOBSERVABLE_LABEL_ZH,
        }
    return {
        "quality_id": quality_id,
        "label_zh": QUALITY_ITEM_LABELS_ZH[quality_id],
        "status_code": QUALITY_STATUS_OBSERVED,
        "value": value,
        "value_label_zh": value_label_zh
        if value_label_zh is not None
        else (str(value) if value is not None else UNOBSERVABLE_LABEL_ZH),
    }


def _duration_summary(
    variation_surface: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Summarize 时长 from slot.length_hint values across slots.

    The Phase B authoring helper assigns ``slot.length_hint`` per slot
    from the closed ``LENGTH_PICKS`` set (30/45/60/75/90/105/120). The
    summary returns ``{min, max, average_seconds}`` so reviewers see the
    duration spread across variations without inventing a per-cell
    runtime number.
    """
    surface = _safe_mapping(variation_surface)
    copy_bundle = _safe_mapping(surface.get("copy_bundle"))
    slots = _safe_list(copy_bundle.get("slots"))
    lengths: list[int] = []
    for slot in slots:
        if not isinstance(slot, Mapping):
            continue
        raw = slot.get("length_hint")
        try:
            value = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            value = None
        if value is not None:
            lengths.append(value)
    if not lengths:
        return None
    average_seconds = sum(lengths) / len(lengths)
    return {
        "min_seconds": min(lengths),
        "max_seconds": max(lengths),
        "average_seconds": round(average_seconds, 2),
        "sample_count": len(lengths),
    }


def _artifact_status_items(
    delivery_comprehension: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Render per-deliverable artifact-status rows from delivery comprehension.

    Reads the existing ``lanes`` projection (per
    :mod:`delivery_comprehension`) and emits a flat operator-language
    list. Reuses the comprehension layer's ``artifact_status_label_zh``
    so 产物状态 explanations stay consistent across Workbench E and
    Delivery Center.
    """
    items: list[dict[str, Any]] = []
    lanes = _safe_mapping(delivery_comprehension.get("lanes"))
    for lane_id in ("required_blocking", "required_non_blocking", "optional_non_blocking"):
        lane = _safe_mapping(lanes.get(lane_id))
        for row in _safe_list(lane.get("rows")):
            if not isinstance(row, Mapping):
                continue
            items.append(
                {
                    "deliverable_id": row.get("deliverable_id"),
                    "kind": row.get("kind"),
                    "kind_label_zh": row.get("kind_label_zh"),
                    "lane_id": lane_id,
                    "lane_label_zh": lane.get("lane_label_zh"),
                    "artifact_status_code": row.get("artifact_status_code"),
                    "artifact_status_label_zh": row.get("artifact_status_label_zh"),
                    "artifact_status_explanation_zh": row.get(
                        "artifact_status_explanation_zh"
                    ),
                    "required": bool(row.get("required")),
                    "blocking_publish": bool(row.get("blocking_publish")),
                }
            )
    return items


def derive_matrix_script_qc_diagnostics_view(
    publish_readiness: Mapping[str, Any] | None,
    delivery_comprehension: Mapping[str, Any] | None,
    variation_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench E 质检与诊断区 bundle.

    Returns ``{}`` when the panel is not Matrix Script, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script(panel):
        return {}

    pr = _safe_mapping(publish_readiness)
    comprehension = _safe_mapping(delivery_comprehension)

    duration = _duration_summary(_safe_mapping(variation_surface))
    duration_label = (
        f"min={duration['min_seconds']}s · max={duration['max_seconds']}s · avg={duration['average_seconds']}s · n={duration['sample_count']}"
        if duration
        else None
    )

    quality_items = [
        _quality_item(
            QUALITY_ITEM_DURATION,
            value=duration,
            value_label_zh=duration_label,
        ),
        _quality_item(QUALITY_ITEM_CLARITY, value=None, value_label_zh=None),
        _quality_item(
            QUALITY_ITEM_SUBTITLE_READABILITY, value=None, value_label_zh=None
        ),
    ]

    blocking_advisories = _safe_list(pr.get("blocking_advisories"))
    publish_blocking = _safe_mapping(comprehension.get("publish_blocking_explanation"))

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Workbench E · 质检与诊断区",
        "panel_subtitle_zh": (
            "只读视图；blocking_advisories 由统一 L4 advisory_emitter 提供，"
            "head_reason 来自统一 publish_readiness 上游。"
        ),
        "ready_gate_label_zh": "Ready gate 解释",
        "ready_gate_explanation": _ready_gate_explanation(pr),
        "risk_items_label_zh": "风险提示（来自 publish_readiness.blocking_advisories）",
        "risk_items": _risk_items_from_advisories(blocking_advisories),
        "compliance_items_label_zh": "合规提示",
        "compliance_items": _compliance_items(),
        "quality_items_label_zh": "时长 / 清晰度 / 字幕可读性",
        "quality_items": quality_items,
        "artifact_status_label_zh": "产物状态（按 Delivery Center 投射）",
        "artifact_status_items": _artifact_status_items(comprehension),
        "publish_blocking_explanation_label_zh": "发布阻塞解释（共享 Delivery Center 解释）",
        "publish_blocking_explanation": publish_blocking,
    }


__all__ = [
    "HEAD_REASON_LABELS_ZH",
    "QUALITY_ITEM_CLARITY",
    "QUALITY_ITEM_DURATION",
    "QUALITY_ITEM_LABELS_ZH",
    "QUALITY_ITEM_SUBTITLE_READABILITY",
    "QUALITY_STATUS_OBSERVED",
    "QUALITY_STATUS_UNOBSERVABLE",
    "UNOBSERVABLE_LABEL_ZH",
    "derive_matrix_script_qc_diagnostics_view",
]
