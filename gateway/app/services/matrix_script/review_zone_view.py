"""Matrix Script Workbench D — review-zone view (OWC-MS PR-2 / MS-W5).

Pure presentation-layer projection over two already-existing surfaces:

- ``matrix_script_workbench_variation_surface_v1`` from
  :mod:`gateway.app.services.matrix_script.workbench_variation_surface`
  (cells / slots — defines the variations review actions target).
- ``matrix_script_publish_feedback_closure_v1`` from
  :mod:`gateway.app.services.matrix_script.publish_feedback_closure`
  (closure ``feedback_closure_records[]`` — read-only history of prior
  ``operator_note`` events with optional ``review_zone`` tag).

Authority:

- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W5 (Workbench D 校对区:
  four review affordances 字幕 / 配音 / 文案 / CTA writing through
  existing closure ``operator_note`` event with an additive structured
  ``review_zone`` field; closed enum ``subtitle / dub / copy / cta``;
  closure shape unchanged; an enum closed-set extension on event payload
  is the only contract touch).
- ``docs/product/matrix_script_product_flow_v1.md`` §6.1D — 字幕校对 /
  配音试听 / 文案 / 标签校对 / CTA 校对.
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
  §"Operator review zone tag (additive, OWC-MS PR-2)" — the closed
  enum + recorded position on the appended ``feedback_closure_records[]``
  entry.

Hard discipline (binding under OWC-MS gate spec §4):

- No new endpoint; review actions write through the existing
  ``POST /api/matrix-script/closures/{task_id}/events`` route in
  :mod:`gateway.app.routers.matrix_script_closure` with
  ``event_kind="operator_note"``.
- No closure-row reshape. The optional ``review_zone`` field flows onto
  the appended ``feedback_closure_records[]`` entry only.
- No second producer; the read-side replay reads the closure verbatim.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No operator-driven Phase B authoring affordance.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "matrix_script"`` branch.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from .publish_feedback_closure import REVIEW_ZONE_VALUES

# Operator-language labels for the four review zones per
# matrix_script_product_flow §6.1D. The closed-set order below is
# intentionally fixed for stable rendering across templates and tests.
REVIEW_ZONE_ORDER = ("subtitle", "dub", "copy", "cta")

REVIEW_ZONE_LABELS_ZH = {
    "subtitle": "字幕校对",
    "dub": "配音校对",
    "copy": "文案校对",
    "cta": "CTA 校对",
}

REVIEW_ZONE_GUIDANCE_ZH = {
    "subtitle": "审核字幕翻译 / 时间轴 / 可读性，必要时回写校对意见。",
    "dub": "试听配音 / 评估韵律与语义保真，必要时回写校对意见。",
    "copy": "审阅文案与 hashtag / 评论关键词，必要时回写校对意见。",
    "cta": "确认 CTA 行动指令清晰可执行，必要时回写校对意见。",
}

# OWC-MS PR-2: the contract-shaped event endpoint used by every review
# affordance. The endpoint already exists per Recovery PR-3
# (:mod:`gateway.app.routers.matrix_script_closure`); MS-W5 does not
# introduce a new route.
REVIEW_EVENT_ENDPOINT_TEMPLATE = "/api/matrix-script/closures/{task_id}/events"


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _zone_history_index(
    closure: Mapping[str, Any] | None,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Index closure feedback_closure_records by (variation_id, review_zone).

    Reads only the contract-frozen ``operator_note`` records. Records
    without a ``review_zone`` tag are bucketed under
    ``(variation_id, "_legacy_unzoned")`` so the view can render them as
    historical (untagged) review notes without claiming a zone.
    """
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not isinstance(closure, Mapping):
        return index
    for record in _safe_list(closure.get("feedback_closure_records")):
        if not isinstance(record, Mapping):
            continue
        if str(record.get("event_kind") or "") != "operator_note":
            continue
        variation_id = str(record.get("variation_id") or "")
        if not variation_id:
            continue
        zone = record.get("review_zone")
        zone_key = zone if zone in REVIEW_ZONE_VALUES else "_legacy_unzoned"
        bucket = index.setdefault((variation_id, zone_key), [])
        bucket.append(
            {
                "event_id": str(record.get("event_id") or ""),
                "recorded_at": record.get("recorded_at"),
                "actor_kind": record.get("actor_kind"),
                "review_zone": zone if zone in REVIEW_ZONE_VALUES else None,
            }
        )
    return index


def _zone_payload_template(zone_id: str) -> dict[str, Any]:
    """Return the contract-shaped event body the operator surface posts.

    The endpoint is the existing
    ``POST /api/matrix-script/closures/{task_id}/events`` per Recovery
    PR-3. ``review_zone`` is the OWC-MS PR-2 additive field validated by
    :mod:`publish_feedback_closure` against ``REVIEW_ZONE_VALUES``.
    """
    return {
        "event_kind": "operator_note",
        "actor_kind": "operator",
        "variation_id": "<cell_id>",
        "payload": {
            "operator_publish_notes": "<operator note text>",
            "review_zone": zone_id,
        },
    }


def _last_event_for_zone(
    history: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not history:
        return None
    # Records are appended in submission order by `apply_event`; the
    # last entry is the most recent. We do not re-sort here because the
    # closure contract pins append-only ordering.
    return history[-1]


def derive_matrix_script_review_zone_view(
    variation_surface: Mapping[str, Any] | None,
    closure: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
    *,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench D 校对区 bundle.

    Returns ``{}`` when the panel is not Matrix Script, so the caller
    can attach the result without further gating.

    When ``task_id`` is provided, the bundle additionally carries a
    per-(variation, zone) ``submit_form`` shape so the template can
    render real operator review submit forms — single endpoint, single
    event_kind, optional ``review_zone`` tag (OWC-MS PR-2 / MS-W5 real
    write affordance per gate spec §3 MS-W5).
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_matrix_script(panel):
        return {}

    surface = _safe_mapping(variation_surface)
    variation_plan = _safe_mapping(surface.get("variation_plan"))
    cells = _safe_list(variation_plan.get("cells"))

    history_index = _zone_history_index(closure)

    resolved_task_id = str(task_id) if task_id else ""
    endpoint_url = (
        REVIEW_EVENT_ENDPOINT_TEMPLATE.format(task_id=resolved_task_id)
        if resolved_task_id
        else None
    )

    zones: list[dict[str, Any]] = []
    for zone_id in REVIEW_ZONE_ORDER:
        zones.append(
            {
                "zone_id": zone_id,
                "zone_label_zh": REVIEW_ZONE_LABELS_ZH[zone_id],
                "zone_guidance_zh": REVIEW_ZONE_GUIDANCE_ZH[zone_id],
                "event_kind": "operator_note",
                "actor_kind": "operator",
                "endpoint_template": REVIEW_EVENT_ENDPOINT_TEMPLATE,
                "endpoint_url": endpoint_url,
                "payload_shape_example": _zone_payload_template(zone_id),
                "input_label_zh": f"输入{REVIEW_ZONE_LABELS_ZH[zone_id]}意见",
                "input_placeholder_zh": "请输入校对意见…（提交后写入 closure operator_note）",
                "submit_label_zh": f"提交 {REVIEW_ZONE_LABELS_ZH[zone_id]} 意见",
            }
        )

    review_status_rows: list[dict[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        variation_id = str(cell.get("cell_id") or "")
        if not variation_id:
            continue
        per_zone: dict[str, Any] = {}
        for zone_id in REVIEW_ZONE_ORDER:
            history = history_index.get((variation_id, zone_id), [])
            last = _last_event_for_zone(history)
            per_zone[zone_id] = {
                "history_count": len(history),
                "last_event_id": (last or {}).get("event_id"),
                "last_recorded_at": (last or {}).get("recorded_at"),
                "is_reviewed": bool(last),
                # Per-(variation, zone) real submit-form shape. Single
                # endpoint, single event_kind, optional review_zone tag.
                # Renders only when task_id was provided so the template
                # can build the form against the resolved closure URL.
                "submit_form": (
                    {
                        "method": "POST",
                        "action": endpoint_url,
                        "event_kind": "operator_note",
                        "actor_kind": "operator",
                        "variation_id": variation_id,
                        "review_zone": zone_id,
                    }
                    if endpoint_url
                    else None
                ),
            }
        legacy_history = history_index.get((variation_id, "_legacy_unzoned"), [])
        review_status_rows.append(
            {
                "variation_id": variation_id,
                "axis_selections": dict(_safe_mapping(cell.get("axis_selections"))),
                "per_zone": per_zone,
                "legacy_unzoned_history_count": len(legacy_history),
            }
        )

    return {
        "is_matrix_script": True,
        "panel_title_zh": "Workbench D · 校对区",
        "panel_subtitle_zh": (
            "字幕 / 配音 / 文案 / CTA 四区校对；通过既有 closure operator_note 事件回写，"
            "review_zone 闭枚举为 OWC-MS PR-2 唯一新增契约位。"
        ),
        "review_zone_enum": sorted(REVIEW_ZONE_VALUES),
        "zones_label_zh": "校对分区",
        "zones": zones,
        "review_status_label_zh": "各变体校对历史",
        "review_status_rows": review_status_rows,
        "closure_endpoint_label_zh": "回写端点",
        "closure_endpoint_template": REVIEW_EVENT_ENDPOINT_TEMPLATE,
        "closure_endpoint_url": endpoint_url,
        "closure_endpoint_explanation_zh": (
            "通过既有 Recovery PR-3 端点回写：POST /api/matrix-script/closures/{task_id}/events，"
            "event_kind=operator_note，actor_kind=operator，payload 包含 operator_publish_notes 与 review_zone。"
        ),
        "phase_b_authoring_forbidden_label_zh": (
            "本面板只回写 operator_note 校对意见；不修改 source_script，不动 axes / cells / slots（OWC-MS gate spec §4.1）。"
        ),
    }


__all__ = [
    "REVIEW_EVENT_ENDPOINT_TEMPLATE",
    "REVIEW_ZONE_GUIDANCE_ZH",
    "REVIEW_ZONE_LABELS_ZH",
    "REVIEW_ZONE_ORDER",
    "derive_matrix_script_review_zone_view",
]
