"""OWC-DA PR-2 / DA-W5 — Workbench C 场景模板面 read-view tests.

Authority: docs/reviews/owc_da_gate_spec_v1.md §3 DA-W5 +
docs/product/digital_anchor_product_flow_v1.md §6.1C.

Hard discipline asserted by these cases:
- Non-digital_anchor panels return ``{}``.
- Five scene zones present in the closed order.
- Asset Supply browse pointer is present and read-only.
- No scene authoring affordance leaks into the bundle.
"""
from __future__ import annotations

from copy import deepcopy

from gateway.app.services.digital_anchor.scene_template_view import (
    SCENE_ZONE_AUX,
    SCENE_ZONE_BACKGROUND,
    SCENE_ZONE_INFO,
    SCENE_ZONE_LAYOUT,
    SCENE_ZONE_ORDER,
    SCENE_ZONE_TITLE,
    STATUS_GENERIC_REF_ONLY,
    STATUS_TEMPLATE_BOUND,
    STATUS_TEMPLATE_PENDING,
    derive_digital_anchor_scene_template_view,
)


_DA_PANEL = {"panel_kind": "digital_anchor"}
_MS_PANEL = {"panel_kind": "matrix_script"}

_TASK_WITH_SCENE = {
    "task_id": "t_da_003",
    "kind": "digital_anchor",
    "config": {
        "line_id": "digital_anchor",
        "entry": {
            "topic": "Q3 产品介绍",
            "scene_binding_hint": "asset://da/scene_template/news_desk_v1",
        },
    },
}

_ROLE_SPEAKER_SURFACE_WITH_GENERIC = {
    "role_surface": {"roles": []},
    "speaker_surface": {
        "segments": [
            {"segment_id": "seg_01", "script_ref": "content://da/seg/seg_01"},
            {"segment_id": "seg_02", "script_ref": "content://da/seg/seg_02"},
        ],
    },
    "scene_binding_projection": {
        "scene_contract_ref": True,
        "segments": [
            {"segment_id": "seg_01", "script_ref": "content://da/seg/seg_01"},
            {"segment_id": "seg_02", "script_ref": "content://da/seg/seg_02"},
        ],
        "scene_binding_writeback": "not_implemented_phase_b",
    },
}


def test_returns_empty_for_matrix_script_panel() -> None:
    assert derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _MS_PANEL) == {}


def test_returns_empty_when_panel_is_none() -> None:
    assert derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, None) == {}


def test_basic_render_emits_is_digital_anchor_marker() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert bundle["is_digital_anchor"] is True


def test_scene_zones_emitted_in_closed_order() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    zone_ids = [zone["zone_id"] for zone in bundle["scene_zones"]]
    assert zone_ids == list(SCENE_ZONE_ORDER)


def test_scene_template_bound_status_when_hint_present() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert bundle["scene_template_ref_status_code"] == STATUS_TEMPLATE_BOUND


def test_generic_scene_ref_only_status_when_only_g_scene_present() -> None:
    task = deepcopy(_TASK_WITH_SCENE)
    task["config"]["entry"]["scene_binding_hint"] = ""
    bundle = derive_digital_anchor_scene_template_view(task, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert bundle["scene_template_ref_status_code"] == STATUS_GENERIC_REF_ONLY


def test_scene_template_pending_status_when_neither_present() -> None:
    task = deepcopy(_TASK_WITH_SCENE)
    task["config"]["entry"]["scene_binding_hint"] = ""
    surface = deepcopy(_ROLE_SPEAKER_SURFACE_WITH_GENERIC)
    surface["scene_binding_projection"]["scene_contract_ref"] = False
    bundle = derive_digital_anchor_scene_template_view(task, surface, _DA_PANEL)
    assert bundle["scene_template_ref_status_code"] == STATUS_TEMPLATE_PENDING


def test_segment_scene_rows_render_each_segment() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    rows = bundle["segment_scene_rows"]
    assert {row["segment_id"] for row in rows} == {"seg_01", "seg_02"}


def test_zone_set_includes_all_five_facets() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    facet_ids = {zone["zone_id"] for zone in bundle["scene_zones"]}
    assert facet_ids == {SCENE_ZONE_LAYOUT, SCENE_ZONE_BACKGROUND, SCENE_ZONE_INFO, SCENE_ZONE_TITLE, SCENE_ZONE_AUX}


def test_asset_supply_browse_pointer_present() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert "Asset Supply" in bundle["asset_supply_browse_scene_hint_zh"]


def test_scene_authoring_forbidden_message_present() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert "scene_template 创作" in bundle["scene_authoring_forbidden_label_zh"]


def test_helper_emits_no_provider_or_swiftcraft_identifier() -> None:
    bundle = derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    rendered = repr(bundle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in rendered


def test_helper_does_not_mutate_inputs() -> None:
    snapshot_task = deepcopy(_TASK_WITH_SCENE)
    snapshot_surface = deepcopy(_ROLE_SPEAKER_SURFACE_WITH_GENERIC)
    derive_digital_anchor_scene_template_view(_TASK_WITH_SCENE, _ROLE_SPEAKER_SURFACE_WITH_GENERIC, _DA_PANEL)
    assert _TASK_WITH_SCENE == snapshot_task
    assert _ROLE_SPEAKER_SURFACE_WITH_GENERIC == snapshot_surface
