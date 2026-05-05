"""OWC-DA PR-2 / DA-W3 — Workbench A 角色绑定面 read-view tests.

Authority: docs/reviews/owc_da_gate_spec_v1.md §3 DA-W3 +
docs/product/digital_anchor_product_flow_v1.md §6.1A.

Hard discipline asserted by these cases:
- Non-digital_anchor panels return ``{}``.
- Five facets present in the closed order.
- No vendor / model / provider / engine / swiftcraft tokens leak through.
- Helper does not mutate inputs.
- Closed kind-sets surface read-only (no widening at presentation).
"""
from __future__ import annotations

from copy import deepcopy

from gateway.app.services.digital_anchor.role_binding_view import (
    ROLE_FACET_ORDER,
    derive_digital_anchor_role_binding_view,
)


_ROLE_SPEAKER_SURFACE = {
    "line_id": "digital_anchor",
    "role_surface": {
        "framing_kind_set": ["head", "half_body", "full_body"],
        "appearance_ref_kind_set": ["preset"],
        "roles": [
            {
                "role_id": "host_lead",
                "display_name": "主播",
                "framing_kind": "half_body",
                "appearance_ref": "asset://da/role/host_lead",
            },
            {
                "role_id": "host_aux",
                "display_name": "副播",
                "framing_kind": "head",
                "appearance_ref": "asset://da/role/host_aux",
            },
        ],
    },
    "speaker_surface": {
        "dub_kind_set": ["tts_neutral", "tts_role_voice", "source_passthrough"],
        "lip_sync_kind_set": ["tight", "loose", "none"],
        "segments": [
            {
                "segment_id": "seg_01",
                "binds_role_id": "host_lead",
                "dub_kind": "tts_role_voice",
                "lip_sync_kind": "tight",
                "language_pick": "en-US",
            },
            {
                "segment_id": "seg_02",
                "binds_role_id": "host_aux",
                "dub_kind": "tts_role_voice",
                "lip_sync_kind": "loose",
                "language_pick": "ja-JP",
            },
        ],
    },
}

_TASK = {
    "task_id": "t_da_001",
    "kind": "digital_anchor",
    "config": {
        "line_id": "digital_anchor",
        "entry": {
            "topic": "Q1 产品介绍",
            "role_profile_ref": "ref://da/role_profile/host_lead",
            "role_framing_hint": "half_body",
            "output_intent": "产品介绍口播",
            "operator_notes": "保持品牌口吻",
            "speaker_segment_count_hint": 2,
            "dub_kind_hint": "tts_role_voice",
            "lip_sync_kind_hint": "tight",
        },
    },
}

_DA_PANEL = {"panel_kind": "digital_anchor"}
_MS_PANEL = {"panel_kind": "matrix_script"}
_HF_PANEL = {"panel_kind": "hot_follow"}


def test_returns_empty_when_panel_is_matrix_script() -> None:
    assert derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _MS_PANEL) == {}


def test_returns_empty_when_panel_is_hot_follow() -> None:
    assert derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _HF_PANEL) == {}


def test_returns_empty_when_panel_is_none() -> None:
    assert derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, None) == {}


def test_returns_empty_when_panel_kind_missing() -> None:
    assert derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, {}) == {}


def test_basic_render_emits_is_digital_anchor_marker() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert bundle["is_digital_anchor"] is True


def test_facets_emitted_in_closed_order() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    facet_ids = [facet["facet_id"] for facet in bundle["role_facets"]]
    assert facet_ids == list(ROLE_FACET_ORDER)


def test_role_profile_facet_uses_entry_role_profile_ref() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    role_facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "role_profile")
    assert role_facet["value"] == "ref://da/role_profile/host_lead"
    assert role_facet["is_resolved"] is True


def test_appearance_style_facet_aggregates_distinct_framings() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "appearance_style")
    assert facet["value"] == ["half_body", "head"]
    assert "head" in (facet["value_label_zh"] or "")


def test_voice_preset_facet_collapses_when_segments_share_dub_kind() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "voice_preset")
    assert facet["value"] == "tts_role_voice"


def test_voice_preset_facet_falls_back_to_entry_hint_when_no_segments() -> None:
    surface = {"role_surface": {"roles": []}, "speaker_surface": {"segments": []}}
    bundle = derive_digital_anchor_role_binding_view(_TASK, surface, _DA_PANEL)
    facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "voice_preset")
    assert facet["value"] == "tts_role_voice"
    assert "entry.dub_kind_hint" in (facet["value_label_zh"] or "")


def test_expression_style_facet_aggregates_distinct_lip_sync() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "expression_style")
    assert facet["value"] == ["loose", "tight"]


def test_emotion_facet_emits_role_count_and_intent() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "emotion")
    assert facet["value"]["role_count"] == 2
    assert "output_intent" in (facet["value_label_zh"] or "")


def test_role_summary_rows_carry_framing_label() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    rows = bundle["role_summary_rows"]
    assert {row["role_id"] for row in rows} == {"host_lead", "host_aux"}
    framings = {row["framing_kind_label_zh"] for row in rows}
    assert any("半身" in label for label in framings)


def test_speaker_summary_rows_carry_dub_and_lip_sync_labels() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    rows = bundle["speaker_summary_rows"]
    assert any(row["dub_kind"] == "tts_role_voice" for row in rows)
    assert any("强对位" in (row["lip_sync_kind_label_zh"] or "") for row in rows)


def test_helper_emits_no_provider_or_swiftcraft_identifier() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    rendered = repr(bundle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in rendered


def test_helper_does_not_mutate_inputs() -> None:
    snapshot_task = deepcopy(_TASK)
    snapshot_surface = deepcopy(_ROLE_SPEAKER_SURFACE)
    derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert _TASK == snapshot_task
    assert _ROLE_SPEAKER_SURFACE == snapshot_surface


def test_closed_kind_sets_surface_in_bundle() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert "head" in bundle["framing_kind_set"]
    assert "tts_role_voice" in bundle["dub_kind_set"]
    assert "tight" in bundle["lip_sync_kind_set"]


def test_asset_supply_pointer_present_and_read_only() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    text = bundle["asset_supply_browse_role_pack_hint_zh"]
    assert "Asset Supply" in text
    assert "本工作台不创建或编辑" in text


def test_phase_b_authoring_forbidden_message_present() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert "OWC-DA gate spec §4.1" in bundle["phase_b_authoring_forbidden_label_zh"]


def test_handles_missing_role_profile_ref_gracefully() -> None:
    task = {
        "kind": "digital_anchor",
        "config": {"entry": {"topic": "x", "speaker_segment_count_hint": 1}},
    }
    bundle = derive_digital_anchor_role_binding_view(task, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    role_facet = next(f for f in bundle["role_facets"] if f["facet_id"] == "role_profile")
    assert role_facet["value"] is None
    assert role_facet["is_resolved"] is False


def test_handles_empty_role_speaker_surface() -> None:
    bundle = derive_digital_anchor_role_binding_view(_TASK, {}, _DA_PANEL)
    appearance = next(
        f for f in bundle["role_facets"] if f["facet_id"] == "appearance_style"
    )
    assert appearance["value"] is None
