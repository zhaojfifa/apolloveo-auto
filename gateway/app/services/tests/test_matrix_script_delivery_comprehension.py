"""PR-U3 — Matrix Script Delivery Center comprehension projection tests.

Authority:
- ``docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md``
  (signed UI-alignment gate spec; PR-U3 implements the user-mandated
  Delivery Center comprehension narrowing).
- ``gateway/app/services/matrix_script/delivery_comprehension.py`` (helper under test).
- ``gateway/app/services/matrix_script/delivery_binding.py`` (input projection shape).

Import-light: exercises the pure helper
``derive_matrix_script_delivery_comprehension`` over hand-built inputs
that mirror the shapes produced by ``project_delivery_binding``.

What is proved:

1. Returns ``{}`` for non-Matrix-Script bindings (Hot Follow / Digital
   Anchor / unknown surfaces never receive the bundle).
2. ``final_video`` is highlighted as the primary deliverable in a
   dedicated block — distinct from the structural rows.
3. The five canonical deliverables (variation_manifest / slot_bundle /
   subtitle_bundle / audio_preview / scene_pack) are zoned correctly:
   ``required_blocking`` for variation_manifest + slot_bundle;
   ``required_non_blocking`` if any required-but-non-blocking row appears
   (defensive); ``optional_non_blocking`` for scene_pack regardless of
   the per-task ``pack`` capability flag.
4. Operator-language zoning labels per `(required, blocking_publish)`
   tuple match the binding spec.
5. ``artifact_lookup`` translation: ``artifact_lookup_unresolved`` → 尚未解析;
   ArtifactHandle with ``freshness == "fresh"`` → 当前 · 最新;
   ``freshness == "historical"`` or ``provenance.attempt_id`` set →
   历史成功 · 非当前 — never collapsed into a single "exists" boolean.
6. Publish-blocking explanation: when any required+blocking row is not
   ``current_fresh`` the bundle reports ``is_blocked=True`` with operator
   language naming the failing rows; otherwise reports unblocked.
7. Validator R3 alignment — no vendor / model / provider / engine
   identifier anywhere in the bundle.
8. Helper does not mutate inputs.
"""
from __future__ import annotations

from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.delivery_comprehension import (
    DELIVERABLE_KIND_LABELS_ZH,
    derive_matrix_script_delivery_comprehension,
)


def _ms_delivery_binding(
    *,
    subtitles_required: bool = True,
    dub_required: bool = True,
    artifact_lookups: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mirror the contract-pinned shape from
    ``project_delivery_binding(packet)`` — five deliverable rows in the
    closed order produced by the binding."""
    artifact_lookups = artifact_lookups or {}
    rows = [
        {
            "deliverable_id": "matrix_script_variation_manifest",
            "kind": "variation_manifest",
            "required": True,
            "blocking_publish": True,
            "source_ref_id": "matrix_script_variation_matrix",
            "artifact_lookup": artifact_lookups.get(
                "variation_manifest", "artifact_lookup_unresolved"
            ),
        },
        {
            "deliverable_id": "matrix_script_slot_bundle",
            "kind": "script_slot_bundle",
            "required": True,
            "blocking_publish": True,
            "source_ref_id": "matrix_script_slot_pack",
            "artifact_lookup": artifact_lookups.get(
                "slot_bundle", "artifact_lookup_unresolved"
            ),
        },
        {
            "deliverable_id": "matrix_script_subtitle_bundle",
            "kind": "subtitle_bundle",
            "required": subtitles_required,
            "blocking_publish": subtitles_required,
            "source_ref_id": "matrix_script_slot_pack",
            "artifact_lookup": artifact_lookups.get(
                "subtitle_bundle", "artifact_lookup_unresolved"
            ),
        },
        {
            "deliverable_id": "matrix_script_audio_preview",
            "kind": "audio_preview",
            "required": dub_required,
            "blocking_publish": dub_required,
            "source_ref_id": "capability:dub",
            "artifact_lookup": artifact_lookups.get(
                "audio_preview", "artifact_lookup_unresolved"
            ),
        },
        {
            "deliverable_id": "matrix_script_scene_pack",
            "kind": "scene_pack",
            "required": False,
            "blocking_publish": False,
            "source_ref_id": "capability:pack",
            "artifact_lookup": artifact_lookups.get(
                "scene_pack", "artifact_lookup_unresolved"
            ),
        },
    ]
    return {
        "line_id": "matrix_script",
        "packet_version": "v1",
        "surface": "matrix_script_delivery_binding_v1",
        "delivery_pack": {
            "deliverable_profile_ref": None,
            "asset_sink_profile_ref": None,
            "deliverables": rows,
        },
    }


# -- 1. Non-Matrix-Script bindings get empty bundle ---------------------


def test_returns_empty_for_non_matrix_script_surface() -> None:
    binding = _ms_delivery_binding()
    binding["surface"] = "hot_follow_delivery_binding_v1"
    binding["line_id"] = "hot_follow"
    assert derive_matrix_script_delivery_comprehension(binding) == {}


def test_returns_empty_for_none_or_empty_input() -> None:
    assert derive_matrix_script_delivery_comprehension(None) == {}
    assert derive_matrix_script_delivery_comprehension({}) == {}


def test_recognizes_matrix_script_surface_or_line_id() -> None:
    only_line_id = {
        "line_id": "matrix_script",
        "delivery_pack": {"deliverables": []},
    }
    bundle = derive_matrix_script_delivery_comprehension(only_line_id)
    assert bundle.get("is_matrix_script") is True


# -- 2. final_video primary highlighting --------------------------------


def test_final_video_primary_block_present_and_marked_primary() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    fv = bundle["final_video_primary"]
    assert fv["is_primary"] is True
    assert "final_video" in fv["title_zh"]
    assert "主体" in fv["primacy_explanation_zh"] or "核心" in fv["subtitle_zh"]


# -- 3. Lane classification ---------------------------------------------


def test_variation_manifest_and_slot_bundle_in_required_blocking_lane() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    rb = bundle["lanes"]["required_blocking"]["rows"]
    deliverable_ids = {r["deliverable_id"] for r in rb}
    assert "matrix_script_variation_manifest" in deliverable_ids
    assert "matrix_script_slot_bundle" in deliverable_ids


def test_scene_pack_always_in_optional_non_blocking_lane() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    onb = bundle["lanes"]["optional_non_blocking"]["rows"]
    deliverable_ids = {r["deliverable_id"] for r in onb}
    assert "matrix_script_scene_pack" in deliverable_ids


def test_subtitle_and_audio_required_status_follows_capability_flags() -> None:
    # Both required → both in required_blocking.
    bundle_both_required = derive_matrix_script_delivery_comprehension(
        _ms_delivery_binding(subtitles_required=True, dub_required=True)
    )
    rb_ids = {
        r["deliverable_id"] for r in bundle_both_required["lanes"]["required_blocking"]["rows"]
    }
    assert "matrix_script_subtitle_bundle" in rb_ids
    assert "matrix_script_audio_preview" in rb_ids

    # Both optional → both move to optional_non_blocking.
    bundle_both_optional = derive_matrix_script_delivery_comprehension(
        _ms_delivery_binding(subtitles_required=False, dub_required=False)
    )
    onb_ids = {
        r["deliverable_id"]
        for r in bundle_both_optional["lanes"]["optional_non_blocking"]["rows"]
    }
    assert "matrix_script_subtitle_bundle" in onb_ids
    assert "matrix_script_audio_preview" in onb_ids


def test_lane_row_counts_match() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    lanes = bundle["lanes"]
    total = (
        lanes["required_blocking"]["row_count"]
        + lanes["required_non_blocking"]["row_count"]
        + lanes["optional_non_blocking"]["row_count"]
    )
    assert total == 5


# -- 4. Operator-language zoning labels ---------------------------------


def test_zoning_labels_for_each_combination() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    rb = bundle["lanes"]["required_blocking"]["rows"][0]
    onb = bundle["lanes"]["optional_non_blocking"]["rows"][0]
    assert rb["zoning_label_zh"] == "必交付 · 阻塞发布"
    assert onb["zoning_label_zh"] == "可选 · 不阻塞发布"


def test_kind_labels_translate_to_chinese() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    all_rows = (
        bundle["lanes"]["required_blocking"]["rows"]
        + bundle["lanes"]["required_non_blocking"]["rows"]
        + bundle["lanes"]["optional_non_blocking"]["rows"]
    )
    for row in all_rows:
        kind = row["kind"]
        if kind in DELIVERABLE_KIND_LABELS_ZH:
            assert row["kind_label_zh"] == DELIVERABLE_KIND_LABELS_ZH[kind]


# -- 5. artifact_lookup translation -------------------------------------


def test_unresolved_artifact_lookup_translates_to_pending() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    rb = bundle["lanes"]["required_blocking"]["rows"][0]
    assert rb["artifact_status_code"] == "unresolved"
    assert rb["artifact_status_label_zh"] == "尚未解析"


def test_fresh_artifact_translates_to_current_fresh() -> None:
    binding = _ms_delivery_binding(
        artifact_lookups={
            "variation_manifest": {
                "ref_id": "matrix_script_variation_matrix",
                "freshness": "fresh",
                "provenance": {"attempt_id": "current"},
            },
        }
    )
    bundle = derive_matrix_script_delivery_comprehension(binding)
    rb = bundle["lanes"]["required_blocking"]["rows"][0]
    assert rb["artifact_status_code"] == "current_fresh"
    assert rb["artifact_status_label_zh"] == "当前 · 最新"


def test_historical_freshness_kept_separate_from_current() -> None:
    binding = _ms_delivery_binding(
        artifact_lookups={
            "variation_manifest": {
                "ref_id": "matrix_script_variation_matrix",
                "freshness": "historical",
                "provenance": {"attempt_id": "prev"},
            },
        }
    )
    bundle = derive_matrix_script_delivery_comprehension(binding)
    rb = bundle["lanes"]["required_blocking"]["rows"][0]
    assert rb["artifact_status_code"] == "historical"
    assert "历史成功" in rb["artifact_status_label_zh"]
    assert "非当前" in rb["artifact_status_label_zh"]


def test_provenance_attempt_id_alone_classifies_historical() -> None:
    # No explicit freshness key but provenance.attempt_id present →
    # comprehension classifies as historical (lane is kept separate from
    # current — never collapsed).
    binding = _ms_delivery_binding(
        artifact_lookups={
            "slot_bundle": {
                "ref_id": "matrix_script_slot_pack",
                "provenance": {"attempt_id": "prev"},
            },
        }
    )
    bundle = derive_matrix_script_delivery_comprehension(binding)
    slot_row = next(
        r
        for r in bundle["lanes"]["required_blocking"]["rows"]
        if r["deliverable_id"] == "matrix_script_slot_bundle"
    )
    assert slot_row["artifact_status_code"] == "historical"


# -- 6. Publish-blocking explanation ------------------------------------


def test_publish_blocked_when_required_blocking_row_unresolved() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    pb = bundle["publish_blocking_explanation"]
    assert pb["is_blocked"] is True
    assert "保持禁用" in pb["reason_label_zh"]
    assert len(pb["blocking_rows"]) >= 2  # variation_manifest + slot_bundle at least


def test_publish_unblocked_when_all_required_rows_current_fresh() -> None:
    fresh_lookup = lambda ref: {
        "ref_id": ref,
        "freshness": "fresh",
        "provenance": {"attempt_id": "current"},
    }
    binding = _ms_delivery_binding(
        subtitles_required=False,
        dub_required=False,
        artifact_lookups={
            "variation_manifest": fresh_lookup("matrix_script_variation_matrix"),
            "slot_bundle": fresh_lookup("matrix_script_slot_pack"),
        },
    )
    bundle = derive_matrix_script_delivery_comprehension(binding)
    pb = bundle["publish_blocking_explanation"]
    assert pb["is_blocked"] is False
    assert pb["blocking_rows"] == []
    assert "可启用" in pb["reason_label_zh"]


def test_historical_required_row_still_blocks_publish() -> None:
    """Historical success on a required+blocking row must still block
    publish — historical-vs-current is a comprehension distinction, not
    a publish-readiness fast path."""
    historical_lookup = lambda ref: {
        "ref_id": ref,
        "freshness": "historical",
        "provenance": {"attempt_id": "prev"},
    }
    binding = _ms_delivery_binding(
        subtitles_required=False,
        dub_required=False,
        artifact_lookups={
            "variation_manifest": historical_lookup("matrix_script_variation_matrix"),
            "slot_bundle": historical_lookup("matrix_script_slot_pack"),
        },
    )
    bundle = derive_matrix_script_delivery_comprehension(binding)
    pb = bundle["publish_blocking_explanation"]
    assert pb["is_blocked"] is True
    assert len(pb["blocking_rows"]) == 2


# -- 7. Validator R3 alignment ------------------------------------------


def test_bundle_carries_no_vendor_model_provider_engine_keys() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    forbidden = {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
    }

    def _walk_forbidden(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value.keys()) & forbidden)
            for v in value.values():
                _walk_forbidden(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _walk_forbidden(v)

    _walk_forbidden(bundle)


# -- 8. Helper does not mutate inputs ----------------------------------


def test_helper_does_not_mutate_input() -> None:
    binding = _ms_delivery_binding(
        artifact_lookups={
            "variation_manifest": {
                "ref_id": "matrix_script_variation_matrix",
                "freshness": "fresh",
                "provenance": {"attempt_id": "current"},
            }
        }
    )
    snapshot = repr(binding)
    derive_matrix_script_delivery_comprehension(binding)
    assert repr(binding) == snapshot


# -- 9. Top-level bundle keys + section labels --------------------------


def test_top_level_bundle_carries_all_section_labels() -> None:
    bundle = derive_matrix_script_delivery_comprehension(_ms_delivery_binding())
    assert bundle["panel_title_zh"] == "Matrix Script · 交付中心理解"
    assert bundle["lanes_label_zh"] == "交付分区"
    assert bundle["publish_blocking_explanation_label_zh"] == "发布阻塞解释"
    assert bundle["history_vs_current_label_zh"] == "历史成功 vs 当前尝试"
    assert "折叠" in bundle["history_vs_current_explanation_zh"]
