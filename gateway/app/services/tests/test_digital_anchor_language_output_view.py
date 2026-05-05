"""OWC-DA PR-2 / DA-W6 — Workbench D 语言输出面 + multi-language navigator tests.

Authority: docs/reviews/owc_da_gate_spec_v1.md §3 DA-W6 +
docs/product/digital_anchor_product_flow_v1.md §6.1D + §7.3.

Hard discipline asserted by these cases:
- Non-digital_anchor panels return ``{}``.
- Read-only over language_scope and per-language artifact rows.
- No provider / model / vendor / engine identifier surfaces.
- Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy

from gateway.app.services.digital_anchor.language_output_view import (
    LANGUAGE_FACET_ORDER,
    STATUS_LANGUAGE_BOUND,
    STATUS_LANGUAGE_UNRESOLVED,
    SUBTITLE_STRATEGY_DISABLED,
    SUBTITLE_STRATEGY_OPTIONAL,
    SUBTITLE_STRATEGY_REQUIRED,
    derive_digital_anchor_language_output_view,
)


_DA_PANEL = {"panel_kind": "digital_anchor"}
_MS_PANEL = {"panel_kind": "matrix_script"}

_TASK = {
    "task_id": "t_da_004",
    "kind": "digital_anchor",
    "config": {
        "line_id": "digital_anchor",
        "entry": {
            "topic": "Q4 多语言宣传片",
            "language_scope": {
                "source_language": "zh-CN",
                "target_language": ["en-US", "ja-JP", "es-ES"],
            },
            "operator_notes": "保持术语一致：产品名 / 品牌名",
        },
    },
}

_ROLE_SPEAKER_SURFACE = {
    "role_surface": {"roles": []},
    "speaker_surface": {
        "segments": [
            {"segment_id": "seg_01", "language_pick": "en-US"},
            {"segment_id": "seg_02", "language_pick": "ja-JP"},
        ],
    },
}

_DELIVERY_BINDING_REQUIRED = {
    "delivery_pack": {
        "deliverables": [
            {"deliverable_id": "da_subtitle", "kind": "subtitle_bundle", "required": True, "artifact_lookup": "not_implemented_phase_c"},
            {"deliverable_id": "da_audio", "kind": "audio_bundle", "required": True, "artifact_lookup": "not_implemented_phase_c"},
            {"deliverable_id": "da_lip_sync", "kind": "lip_sync_bundle", "required": False, "artifact_lookup": "not_implemented_phase_c"},
        ],
    },
    "result_packet_binding": {
        "capability_plan": [
            {"kind": "subtitles", "mode": "required", "required": True},
            {"kind": "dub", "mode": "required", "required": True},
        ],
    },
}

_DELIVERY_BINDING_OPTIONAL = {
    "delivery_pack": {
        "deliverables": [
            {"deliverable_id": "da_subtitle", "kind": "subtitle_bundle", "required": False, "artifact_lookup": "not_implemented_phase_c"},
        ],
    },
    "result_packet_binding": {
        "capability_plan": [
            {"kind": "subtitles", "mode": "optional", "required": False},
        ],
    },
}

_DELIVERY_BINDING_NO_SUBTITLES = {
    "delivery_pack": {"deliverables": []},
    "result_packet_binding": {"capability_plan": [{"kind": "dub", "mode": "required", "required": True}]},
}


def test_returns_empty_for_matrix_script_panel() -> None:
    assert derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _MS_PANEL) == {}


def test_returns_empty_when_panel_is_none() -> None:
    assert derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, None) == {}


def test_basic_render_emits_is_digital_anchor_marker() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert bundle["is_digital_anchor"] is True


def test_target_languages_carried_through() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert bundle["language_scope"]["target_language"] == ["en-US", "ja-JP", "es-ES"]


def test_subtitle_strategy_required_when_capability_required() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert bundle["subtitle_strategy_code"] == SUBTITLE_STRATEGY_REQUIRED


def test_subtitle_strategy_optional_when_capability_not_required() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_OPTIONAL, _DA_PANEL)
    assert bundle["subtitle_strategy_code"] == SUBTITLE_STRATEGY_OPTIONAL


def test_subtitle_strategy_disabled_when_no_subtitles_capability() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_NO_SUBTITLES, _DA_PANEL)
    assert bundle["subtitle_strategy_code"] == SUBTITLE_STRATEGY_DISABLED


def test_per_language_rows_mark_segment_picked_languages() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    by_language = {row["language"]: row for row in bundle["per_language_rows"]}
    assert by_language["en-US"]["status_code"] == STATUS_LANGUAGE_BOUND
    assert by_language["ja-JP"]["status_code"] == STATUS_LANGUAGE_BOUND
    assert by_language["es-ES"]["status_code"] == STATUS_LANGUAGE_UNRESOLVED


def test_per_language_rows_carry_required_flags_from_capability_plan() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    row = bundle["per_language_rows"][0]
    assert row["subtitle_required"] is True
    assert row["dub_required"] is True


def test_navigator_rows_render_per_kind_artifact_lookup() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    nav_row = bundle["navigator_rows"][0]
    assert "subtitle_bundle" in nav_row["per_kind"]
    assert nav_row["per_kind"]["subtitle_bundle"]["artifact_lookup"] == "not_implemented_phase_c"


def test_terminology_falls_back_to_operator_notes() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert bundle["terminology_value"] == "保持术语一致：产品名 / 品牌名"


def test_facets_emitted_in_closed_order() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    facet_ids = [facet["facet_id"] for facet in bundle["facets"]]
    assert facet_ids == list(LANGUAGE_FACET_ORDER)


def test_helper_emits_no_provider_or_swiftcraft_identifier() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    rendered = repr(bundle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in rendered


def test_helper_does_not_mutate_inputs() -> None:
    snapshot_task = deepcopy(_TASK)
    snapshot_surface = deepcopy(_ROLE_SPEAKER_SURFACE)
    snapshot_binding = deepcopy(_DELIVERY_BINDING_REQUIRED)
    derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert _TASK == snapshot_task
    assert _ROLE_SPEAKER_SURFACE == snapshot_surface
    assert _DELIVERY_BINDING_REQUIRED == snapshot_binding


def test_phase_b_authoring_forbidden_message_present() -> None:
    bundle = derive_digital_anchor_language_output_view(_TASK, _ROLE_SPEAKER_SURFACE, _DELIVERY_BINDING_REQUIRED, _DA_PANEL)
    assert "OWC-DA gate spec §4.1 / §3 DA-W6" in bundle["phase_b_authoring_forbidden_label_zh"]
