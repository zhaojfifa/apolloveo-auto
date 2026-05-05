"""Digital Anchor Workbench C — scene template view (OWC-DA PR-2 / DA-W5).

Pure presentation-layer projection over two already-existing surfaces:

- ``task["config"]["entry"]`` — the closed eleven-field entry contract,
  in particular ``scene_binding_hint`` (the operator-supplied opaque
  reference to a scene template) per
  :mod:`gateway.app.services.digital_anchor.create_entry`.
- ``digital_anchor_workbench_role_speaker_surface_v1`` from
  :mod:`gateway.app.services.digital_anchor.workbench_role_speaker_surface`
  (the ``scene_binding_projection`` already exposes the generic
  ``g_scene`` reference and per-segment script_ref join).

Authority:

- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W5 (Workbench C 场景模板面:
  Scene Plan / 布局模式 / 背景 / 信息区 / 标题区 / 辅助区 read-view +
  scene template select bound to existing ``scene_template_ref``
  indirection; operator action: select an existing ``scene_template``
  from PR-2 Asset Supply).
- ``docs/product/digital_anchor_product_flow_v1.md`` §6.1C — Scene Plan /
  布局模式 / 背景模板 / 信息区 / 标题区 / 辅助区.

Hard discipline (binding under OWC-DA gate spec §4):

- No Digital Anchor packet truth mutation.
- No scene authoring platform; the operator selection affordance is a
  read-only browse pointer back to PR-2 Asset Supply.
- No scene template ``scene_template_ref`` widening; the value rendered
  is whatever the entry contract carried.
- No vendor / model / provider / engine / video-gen-engine identifier
  in the return value (validator R3).
- No new ``panel_kind`` / ``ref_id`` / contract field.
- No Hot Follow / Matrix Script surface change; non-digital-anchor
  panels return ``{}``.

Consumed only by
``gateway/app/services/operator_visible_surfaces/wiring.py::build_operator_surfaces_for_workbench``
inside the existing ``panel_kind == "digital_anchor"`` branch.
"""
from __future__ import annotations

from typing import Any, Mapping


# Operator-language scene-zone labels per digital_anchor_product_flow §6.1C.
SCENE_ZONE_LAYOUT = "layout_mode"
SCENE_ZONE_BACKGROUND = "background"
SCENE_ZONE_INFO = "info_zone"
SCENE_ZONE_TITLE = "title_zone"
SCENE_ZONE_AUX = "auxiliary_zone"

SCENE_ZONE_ORDER = (
    SCENE_ZONE_LAYOUT,
    SCENE_ZONE_BACKGROUND,
    SCENE_ZONE_INFO,
    SCENE_ZONE_TITLE,
    SCENE_ZONE_AUX,
)

SCENE_ZONE_LABELS_ZH = {
    SCENE_ZONE_LAYOUT: "布局模式",
    SCENE_ZONE_BACKGROUND: "背景",
    SCENE_ZONE_INFO: "信息区",
    SCENE_ZONE_TITLE: "标题区",
    SCENE_ZONE_AUX: "辅助区",
}

SCENE_ZONE_GUIDANCE_ZH = {
    SCENE_ZONE_LAYOUT: "由所选 scene_template 的 layout_mode 决定；本面板不创作布局。",
    SCENE_ZONE_BACKGROUND: "由所选 scene_template 的 background_policy 决定；切换需通过 Asset Supply 选择新模板。",
    SCENE_ZONE_INFO: "由 scene_template 的 info_zone_policy 决定；运营不在工作台层定义信息区。",
    SCENE_ZONE_TITLE: "由 scene_template 的 title_zone_policy 决定；运营不在工作台层编辑标题样式。",
    SCENE_ZONE_AUX: "由 scene_template 的 reference_style_policy 决定；运营不在工作台层添加辅助元素。",
}

# Closed status codes for scene resolution.
STATUS_TEMPLATE_BOUND = "scene_template_bound"
STATUS_TEMPLATE_BOUND_LABEL_ZH = "已绑定 scene_template_ref；具体策略由模板提供。"

STATUS_TEMPLATE_PENDING = "scene_template_pending_selection"
STATUS_TEMPLATE_PENDING_LABEL_ZH = (
    "尚未通过 Asset Supply 选择 scene_template；本面板暂以 entry.scene_binding_hint 占位。"
)

STATUS_GENERIC_REF_ONLY = "generic_scene_ref_only"
STATUS_GENERIC_REF_ONLY_LABEL_ZH = (
    "仅绑定 generic g_scene 引用，未绑定具体 scene_template；零号场景或待 Asset Supply 选择。"
)

# Operator action affordance — read-only pointer back to the PR-2 Asset
# Supply browse surface.
ASSET_SUPPLY_BROWSE_SCENE_HINT = (
    "通过 Asset Supply（资产 / 场景模板）浏览既有 scene_template；本工作台不创建或编辑模板。"
)


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_digital_anchor(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "digital_anchor"


def _scene_zone(zone_id: str, *, status_code: str, status_label_zh: str) -> dict[str, Any]:
    return {
        "zone_id": zone_id,
        "label_zh": SCENE_ZONE_LABELS_ZH[zone_id],
        "guidance_zh": SCENE_ZONE_GUIDANCE_ZH[zone_id],
        "status_code": status_code,
        "status_label_zh": status_label_zh,
    }


def _segment_scene_rows(role_speaker_surface: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Render the per-segment scene-binding rows from existing projection.

    The role-speaker surface already exposes
    ``scene_binding_projection.segments[]`` with
    ``{segment_id, script_ref}``. This view re-renders those rows so the
    operator can confirm scene-segment join coverage.
    """
    projection = _safe_mapping(role_speaker_surface.get("scene_binding_projection"))
    rows: list[dict[str, Any]] = []
    for segment in _safe_list(projection.get("segments")):
        if not isinstance(segment, Mapping):
            continue
        rows.append(
            {
                "segment_id": segment.get("segment_id"),
                "script_ref": segment.get("script_ref"),
            }
        )
    return rows


def _scene_status(
    *,
    scene_binding_hint: str,
    scene_contract_ref_present: bool,
) -> tuple[str, str]:
    """Compute the operator-language scene status based on resolved truth."""
    if scene_binding_hint:
        return STATUS_TEMPLATE_BOUND, STATUS_TEMPLATE_BOUND_LABEL_ZH
    if scene_contract_ref_present:
        return STATUS_GENERIC_REF_ONLY, STATUS_GENERIC_REF_ONLY_LABEL_ZH
    return STATUS_TEMPLATE_PENDING, STATUS_TEMPLATE_PENDING_LABEL_ZH


def derive_digital_anchor_scene_template_view(
    task: Mapping[str, Any] | None,
    role_speaker_surface: Mapping[str, Any] | None,
    line_specific_panel: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the Digital Anchor Workbench C 场景模板面 read-view bundle.

    Returns ``{}`` when the panel is not Digital Anchor, so the caller
    can attach the result without further gating.
    """
    panel = _safe_mapping(line_specific_panel)
    if not _is_digital_anchor(panel):
        return {}

    task_map = _safe_mapping(task)
    config = _safe_mapping(task_map.get("config"))
    entry = _safe_mapping(config.get("entry"))
    scene_binding_hint = str(entry.get("scene_binding_hint") or "").strip()

    surface = _safe_mapping(role_speaker_surface)
    scene_projection = _safe_mapping(surface.get("scene_binding_projection"))
    scene_contract_ref_present = bool(scene_projection.get("scene_contract_ref"))
    scene_writeback = scene_projection.get("scene_binding_writeback")

    status_code, status_label_zh = _scene_status(
        scene_binding_hint=scene_binding_hint,
        scene_contract_ref_present=scene_contract_ref_present,
    )

    zones = [
        _scene_zone(
            zone_id,
            status_code=status_code,
            status_label_zh=status_label_zh,
        )
        for zone_id in SCENE_ZONE_ORDER
    ]

    return {
        "is_digital_anchor": True,
        "panel_title_zh": "Workbench C · 场景模板面",
        "panel_subtitle_zh": (
            "只读视图；Scene Plan / 布局 / 背景 / 信息区 / 标题区 / 辅助区 由所选 "
            "scene_template 提供，本面板不创建或编辑模板。"
        ),
        "scene_plan_label_zh": "Scene Plan（场景计划）",
        "scene_template_ref_label_zh": "场景模板句柄（scene_template_ref / entry.scene_binding_hint）",
        "scene_template_ref_value": scene_binding_hint or None,
        "scene_template_ref_status_code": status_code,
        "scene_template_ref_status_label_zh": status_label_zh,
        "generic_scene_ref_present": scene_contract_ref_present,
        "scene_binding_writeback_status": scene_writeback,
        "scene_zones_label_zh": "场景五区",
        "scene_zones": zones,
        "segment_scene_rows_label_zh": "段落-场景绑定",
        "segment_scene_rows": _segment_scene_rows(surface),
        "asset_supply_browse_label_zh": "Asset Supply（场景模板浏览）",
        "asset_supply_browse_scene_hint_zh": ASSET_SUPPLY_BROWSE_SCENE_HINT,
        "scene_authoring_forbidden_label_zh": (
            "本面板不授权 scene_template 创作；OWC-DA gate spec §4.4 / §3 DA-W5 禁止"
            "在工作台层引入场景作者平台或 catalog UI。"
        ),
    }


__all__ = [
    "ASSET_SUPPLY_BROWSE_SCENE_HINT",
    "SCENE_ZONE_AUX",
    "SCENE_ZONE_BACKGROUND",
    "SCENE_ZONE_GUIDANCE_ZH",
    "SCENE_ZONE_INFO",
    "SCENE_ZONE_LABELS_ZH",
    "SCENE_ZONE_LAYOUT",
    "SCENE_ZONE_ORDER",
    "SCENE_ZONE_TITLE",
    "STATUS_GENERIC_REF_ONLY",
    "STATUS_GENERIC_REF_ONLY_LABEL_ZH",
    "STATUS_TEMPLATE_BOUND",
    "STATUS_TEMPLATE_BOUND_LABEL_ZH",
    "STATUS_TEMPLATE_PENDING",
    "STATUS_TEMPLATE_PENDING_LABEL_ZH",
    "derive_digital_anchor_scene_template_view",
]
