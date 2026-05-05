"""Digital Anchor Workbench E — review zone view (OWC-DA PR-2 / DA-W7).

Pure presentation-layer projection over two already-existing surfaces:

- ``digital_anchor_workbench_role_speaker_surface_v1`` from
  :mod:`gateway.app.services.digital_anchor.workbench_role_speaker_surface`
  (roles / segments — defines the rows review actions target).
- ``digital_anchor_publish_feedback_closure_v1`` from
  :mod:`gateway.app.services.digital_anchor.publish_feedback_closure`
  (closure ``feedback_closure_records[]`` — read-only history of prior
  ``operator_note`` events with optional ``review_zone`` tag).

Authority:

- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W7 (Workbench E 预览与校对面:
  试听 / 视频预览 / 字幕校对 / 表达节奏复核 / 质检 modules; review
  actions write through existing closure D.1 events
  (``role_feedback`` / ``segment_feedback``) with an additive structured
  ``review_zone`` field — closed enum
  ``audition / video_preview / subtitle / cadence / qc`` — mirror of
  OWC-MS MS-W5 pattern; closure shape unchanged; an enum closed-set
  extension on event payload is the only contract touch).
- ``docs/product/digital_anchor_product_flow_v1.md`` §6.1E — 试听 /
  视频预览 / 字幕校对 / 表达与节奏复核 / 质检与诊断.

Hard discipline (binding under OWC-DA gate spec §4):

- No new endpoint; review actions write through the existing
  ``POST /api/digital-anchor/closures/{task_id}/events`` route in
  :mod:`gateway.app.routers.digital_anchor_closure` with
  ``event_kind="operator_note"`` + closed
  ``row_scope="role" | "segment"``.
- No closure-row reshape. The optional ``review_zone`` field flows onto
  the appended ``feedback_closure_records[]`` entry only.
- No second producer; the read-side replay reads the closure verbatim.
- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No operator-driven Phase B authoring affordance (no
  ``roles[]`` / ``segments[]`` enumeration writes).
- No Hot Follow / Matrix Script surface change; non-digital-anchor
  panels return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "digital_anchor"`` branch.
"""
from __future__ import annotations

from typing import Any, Mapping

from .publish_feedback_closure import REVIEW_ZONE_VALUES

# Operator-language labels for the five review zones per
# digital_anchor_product_flow §6.1E. The closed-set order below is
# intentionally fixed for stable rendering across templates and tests.
REVIEW_ZONE_ORDER = ("audition", "video_preview", "subtitle", "cadence", "qc")

REVIEW_ZONE_LABELS_ZH = {
    "audition": "试听（角色 / 配音）",
    "video_preview": "视频预览",
    "subtitle": "字幕校对",
    "cadence": "表达与节奏复核",
    "qc": "质检与诊断",
}

REVIEW_ZONE_GUIDANCE_ZH = {
    "audition": "试听 dub / 角色声音；如需修订请回写 operator_note，role_feedback 行将记录。",
    "video_preview": "预览合成视频 / 段落画面；问题以 operator_note 回写。",
    "subtitle": "审核字幕翻译 / 时间轴 / 可读性，必要时回写校对意见。",
    "cadence": "复核语气 / 速度 / 停顿；意见会写到 segment_feedback 行。",
    "qc": "质检模块（清晰度 / 字幕可读 / 合规风险）；以 operator_note 形式归档。",
}

# OWC-DA PR-2: the contract-shaped event endpoint used by every review
# affordance. The endpoint already exists per Recovery PR-4
# (:mod:`gateway.app.routers.digital_anchor_closure`); DA-W7 does not
# introduce a new route.
REVIEW_EVENT_ENDPOINT_TEMPLATE = "/api/digital-anchor/closures/{task_id}/events"

# Closed row-scope set per the D.1 writeback contract.
REVIEW_ROW_SCOPES = ("role", "segment")
REVIEW_ROW_SCOPE_LABELS_ZH = {
    "role": "角色级（role_feedback）",
    "segment": "段落级（segment_feedback）",
}


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_digital_anchor(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "digital_anchor"


def _zone_history_index(
    closure: Mapping[str, Any] | None,
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    """Index closure feedback_closure_records by (row_scope, row_id, review_zone).

    Reads only the contract-frozen ``operator_note`` records. Records
    without a ``review_zone`` tag are bucketed under
    ``(row_scope, row_id, "_legacy_unzoned")`` so the view can render
    them as historical (untagged) review notes without claiming a zone.
    """
    index: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    if not isinstance(closure, Mapping):
        return index
    for record in _safe_list(closure.get("feedback_closure_records")):
        if not isinstance(record, Mapping):
            continue
        if str(record.get("event_kind") or "") != "operator_note":
            continue
        row_scope = str(record.get("row_scope") or "")
        row_id = str(record.get("row_id") or "")
        if not row_scope or not row_id:
            continue
        zone = record.get("review_zone")
        zone_key = zone if zone in REVIEW_ZONE_VALUES else "_legacy_unzoned"
        bucket = index.setdefault((row_scope, row_id, zone_key), [])
        bucket.append(
            {
                "record_id": str(record.get("record_id") or ""),
                "recorded_at": record.get("recorded_at"),
                "actor_kind": record.get("actor_kind"),
                "review_zone": zone if zone in REVIEW_ZONE_VALUES else None,
            }
        )
    return index


def _zone_payload_template(zone_id: str) -> dict[str, Any]:
    """Return the contract-shaped event body the operator surface posts."""
    return {
        "event_kind": "operator_note",
        "actor_kind": "operator",
        "row_scope": "<role | segment>",
        "row_id": "<role_id | segment_id>",
        "payload": {
            "operator_publish_notes": "<operator note text>",
            "review_zone": zone_id,
        },
    }


def _last_event_for_zone(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not history:
        return None
    return history[-1]


def _row_review_status(
    *,
    row_scope: str,
    row_id: str,
    history_index: dict[tuple[str, str, str], list[dict[str, Any]]],
    endpoint_url: str | None,
) -> dict[str, Any]:
    """Compute per-(row_scope, row_id) per-zone review history + submit form."""
    per_zone: dict[str, Any] = {}
    for zone_id in REVIEW_ZONE_ORDER:
        history = history_index.get((row_scope, row_id, zone_id), [])
        last = _last_event_for_zone(history)
        per_zone[zone_id] = {
            "history_count": len(history),
            "last_record_id": (last or {}).get("record_id"),
            "last_recorded_at": (last or {}).get("recorded_at"),
            "is_reviewed": bool(last),
            "submit_form": (
                {
                    "method": "POST",
                    "action": endpoint_url,
                    "event_kind": "operator_note",
                    "actor_kind": "operator",
                    "row_scope": row_scope,
                    "row_id": row_id,
                    "review_zone": zone_id,
                }
                if endpoint_url
                else None
            ),
        }
    legacy_history = history_index.get((row_scope, row_id, "_legacy_unzoned"), [])
    return {
        "per_zone": per_zone,
        "legacy_unzoned_history_count": len(legacy_history),
    }


def derive_digital_anchor_review_zone_view(
    role_speaker_surface: Mapping[str, Any] | None,
    closure: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
    *,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Project the Digital Anchor Workbench E 预览与校对面 bundle.

    Returns ``{}`` when the panel is not Digital Anchor, so the caller
    can attach the result without further gating.

    When ``task_id`` is provided, the bundle additionally carries a
    per-(row_scope, row_id, zone) ``submit_form`` shape so the template
    can render real operator review submit forms — single endpoint,
    single event_kind, optional ``review_zone`` tag (OWC-DA PR-2 / DA-W7
    real write affordance per gate spec §3 DA-W7).
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_digital_anchor(panel):
        return {}

    surface = _safe_mapping(role_speaker_surface)
    role_surface = _safe_mapping(surface.get("role_surface"))
    speaker_surface = _safe_mapping(surface.get("speaker_surface"))
    roles = _safe_list(role_surface.get("roles"))
    segments = _safe_list(speaker_surface.get("segments"))

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

    role_review_rows: list[dict[str, Any]] = []
    for role in roles:
        if not isinstance(role, Mapping):
            continue
        role_id = str(role.get("role_id") or "")
        if not role_id:
            continue
        status = _row_review_status(
            row_scope="role",
            row_id=role_id,
            history_index=history_index,
            endpoint_url=endpoint_url,
        )
        role_review_rows.append(
            {
                "row_scope": "role",
                "row_id": role_id,
                "row_scope_label_zh": REVIEW_ROW_SCOPE_LABELS_ZH["role"],
                "display_name": role.get("display_name"),
                "framing_kind": role.get("framing_kind"),
                **status,
            }
        )

    segment_review_rows: list[dict[str, Any]] = []
    for segment in segments:
        if not isinstance(segment, Mapping):
            continue
        segment_id = str(segment.get("segment_id") or "")
        if not segment_id:
            continue
        status = _row_review_status(
            row_scope="segment",
            row_id=segment_id,
            history_index=history_index,
            endpoint_url=endpoint_url,
        )
        segment_review_rows.append(
            {
                "row_scope": "segment",
                "row_id": segment_id,
                "row_scope_label_zh": REVIEW_ROW_SCOPE_LABELS_ZH["segment"],
                "binds_role_id": segment.get("binds_role_id"),
                "language_pick": segment.get("language_pick"),
                "dub_kind": segment.get("dub_kind"),
                **status,
            }
        )

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Workbench E · 预览与校对面",
        "panel_subtitle_zh": (
            "试听 / 视频预览 / 字幕校对 / 表达节奏复核 / 质检 五区校对；"
            "通过既有 closure operator_note 事件回写，review_zone 闭枚举为 "
            "OWC-DA PR-2 唯一新增契约位。"
        ),
        "review_zone_enum": sorted(REVIEW_ZONE_VALUES),
        "row_scope_enum": list(REVIEW_ROW_SCOPES),
        "zones_label_zh": "校对分区",
        "zones": zones,
        "role_review_rows_label_zh": "角色级校对历史",
        "role_review_rows": role_review_rows,
        "segment_review_rows_label_zh": "段落级校对历史",
        "segment_review_rows": segment_review_rows,
        "closure_endpoint_label_zh": "回写端点",
        "closure_endpoint_template": REVIEW_EVENT_ENDPOINT_TEMPLATE,
        "closure_endpoint_url": endpoint_url,
        "closure_endpoint_explanation_zh": (
            "通过既有 Recovery PR-4 端点回写：POST /api/digital-anchor/closures/{task_id}/events，"
            "event_kind=operator_note，actor_kind=operator，row_scope ∈ {role, segment}，"
            "payload 包含 operator_publish_notes 与 review_zone。"
        ),
        "phase_b_authoring_forbidden_label_zh": (
            "本面板只回写 operator_note 校对意见；不修改 roles[] / segments[] 枚举，"
            "不动 framing_kind / dub_kind / lip_sync_kind 闭集（OWC-DA gate spec §4.1）。"
        ),
    }


__all__ = [
    "REVIEW_EVENT_ENDPOINT_TEMPLATE",
    "REVIEW_ROW_SCOPES",
    "REVIEW_ROW_SCOPE_LABELS_ZH",
    "REVIEW_ZONE_GUIDANCE_ZH",
    "REVIEW_ZONE_LABELS_ZH",
    "REVIEW_ZONE_ORDER",
    "derive_digital_anchor_review_zone_view",
]
