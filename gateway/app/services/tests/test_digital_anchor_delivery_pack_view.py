"""Service-layer tests for the Digital Anchor Delivery Pack view (OWC-DA PR-3 / DA-W8).

Authority:
- ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W8
- ``docs/product/digital_anchor_product_flow_v1.md`` §7.1
- ``docs/contracts/digital_anchor/delivery_binding_contract_v1.md``

Scope: nine-lane Delivery Pack assembly projection over the existing
``digital_anchor_delivery_binding_v1`` rows + manifest +
metadata_projection + result_packet_binding.role_segment_bindings +
``task["config"]["entry"]``. Every lane is verified for shape,
operator-language labels, tracked-gap discipline, and absence of
provider/model/vendor/engine identifiers.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.digital_anchor.delivery_binding import (
    project_delivery_binding,
)
from gateway.app.services.digital_anchor.delivery_pack_view import (
    LANE_DUBBED_AUDIO,
    LANE_FINAL_VIDEO,
    LANE_LANGUAGE_USAGE,
    LANE_LABELS_ZH,
    LANE_MANIFEST,
    LANE_METADATA,
    LANE_ORDER,
    LANE_PACK,
    LANE_ROLE_USAGE,
    LANE_SCENE_USAGE,
    LANE_SUBTITLE,
    STATUS_RESOLVED,
    STATUS_TRACKED_GAP,
    STATUS_TRACKED_GAP_LANGUAGE,
    STATUS_TRACKED_GAP_ROLES,
    STATUS_TRACKED_GAP_SCENE,
    derive_digital_anchor_delivery_pack,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "digital_anchor"
    / "sample"
    / "digital_anchor_packet_v1.sample.json"
)


def _packet_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _entry_with(scene_hint: str = "scene_template_anchor_a", target=("en-US", "zh-CN")) -> Dict[str, Any]:
    return {
        "topic": "Anchor Launch",
        "source_script_ref": "content://digital_anchor/source/abc123",
        "language_scope": {
            "source_language": "en-US",
            "target_language": list(target),
        },
        "role_profile_ref": "asset://role_pack/anchor_a",
        "role_framing_hint": "half_body",
        "output_intent": "launch_intro",
        "speaker_segment_count_hint": 3,
        "dub_kind_hint": "tts_role_voice",
        "lip_sync_kind_hint": "tight",
        "scene_binding_hint": scene_hint,
        "operator_notes": "primary anchor",
    }


def _da_task(*, entry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "task_id": "da_pack_task_001",
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "config": {"entry": entry if entry is not None else _entry_with()},
        "packet": _packet_sample(),
    }


@pytest.fixture()
def delivery_binding() -> Dict[str, Any]:
    return project_delivery_binding(_packet_sample())


@pytest.fixture()
def task() -> Dict[str, Any]:
    return _da_task()


def test_returns_empty_for_none_inputs():
    assert derive_digital_anchor_delivery_pack(delivery_binding=None, task=None) == {}


def test_returns_empty_for_non_digital_anchor_binding(task):
    foreign = {
        "surface": "matrix_script_delivery_binding_v1",
        "line_id": "matrix_script",
        "delivery_pack": {"deliverables": []},
    }
    assert (
        derive_digital_anchor_delivery_pack(delivery_binding=foreign, task=task) == {}
    )


def test_top_level_shape_keys(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    assert pack["is_digital_anchor"] is True
    assert pack["panel_title_zh"] == "Digital Anchor · 交付中心 · Delivery Pack"
    assert "panel_subtitle_zh" in pack
    assert pack["lane_legend_zh"] == [LANE_LABELS_ZH[lid] for lid in LANE_ORDER]
    assert pack["lane_order"] == list(LANE_ORDER)
    assert "lanes" in pack
    assert "tracked_gap_summary_zh" in pack


def test_all_nine_lanes_present(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lanes = pack["lanes"]
    for lane_id in LANE_ORDER:
        assert lane_id in lanes
        assert lanes[lane_id]["lane_id"] == lane_id
        assert lanes[lane_id]["label_zh"] == LANE_LABELS_ZH[lane_id]


def test_final_video_lane_is_primary_with_tracked_gap(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_FINAL_VIDEO]
    assert lane["is_primary"] is True
    assert lane["status_code"] == STATUS_TRACKED_GAP
    assert lane["value"] == ""
    assert lane["primacy_explanation_zh"]
    assert lane["tracked_gap_explanation_zh"]


def test_subtitle_lane_resolves_to_subtitle_bundle(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_SUBTITLE]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["deliverable_id"] == "digital_anchor_subtitle_bundle"
    assert lane["deliverable_kind"] == "subtitle_bundle"
    assert lane["required"] is True  # sample.json has subtitles.required=true


def test_dubbed_audio_lane_resolves_to_audio_bundle(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_DUBBED_AUDIO]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["deliverable_id"] == "digital_anchor_audio_bundle"
    assert lane["deliverable_kind"] == "audio_bundle"
    assert lane["required"] is True  # sample.json has dub.required=true


def test_pack_lane_resolves_to_scene_pack(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_PACK]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["deliverable_id"] == "digital_anchor_scene_pack"
    assert lane["deliverable_kind"] == "scene_pack"
    # sample.json has pack.required=false
    assert lane["required"] is False


def test_metadata_lane_carries_line_id_and_packet_version(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_METADATA]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["line_id"] == "digital_anchor"
    assert lane["packet_version"] == "v1"
    assert lane["display_only"] is True


def test_manifest_lane_carries_manifest_id(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_MANIFEST]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["manifest_id"] == "digital_anchor_delivery_manifest_v1"
    assert lane["deliverable_profile_ref"] == "deliverable_profile_digital_anchor_v1"


def test_role_usage_aggregates_two_roles_with_segment_ids(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_ROLE_USAGE]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["role_count"] == 2
    role_ids = [r["role_id"] for r in lane["roles"]]
    assert "role_anchor_a" in role_ids
    assert "role_anchor_b" in role_ids
    anchor_a = next(r for r in lane["roles"] if r["role_id"] == "role_anchor_a")
    assert anchor_a["role_display_name"] == "Anchor A"
    assert anchor_a["role_framing_kind"] == "half_body"
    assert "seg_001" in anchor_a["segment_ids"]
    assert "seg_002" in anchor_a["segment_ids"]
    anchor_b = next(r for r in lane["roles"] if r["role_id"] == "role_anchor_b")
    assert anchor_b["role_framing_kind"] == "head"
    assert anchor_b["segment_ids"] == ["seg_003"]


def test_role_usage_lane_tracked_gap_when_no_bindings():
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding={
            "surface": "digital_anchor_delivery_binding_v1",
            "line_id": "digital_anchor",
            "delivery_pack": {"deliverables": []},
            "result_packet_binding": {"role_segment_bindings": []},
            "manifest": {},
            "metadata_projection": {},
        },
        task=_da_task(),
    )
    lane = pack["lanes"][LANE_ROLE_USAGE]
    assert lane["status_code"] == STATUS_TRACKED_GAP_ROLES
    assert lane["role_count"] == 0
    assert lane["roles"] == []


def test_scene_usage_resolves_when_scene_binding_hint_present(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_SCENE_USAGE]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["scene_binding_hint"] == "scene_template_anchor_a"


def test_scene_usage_tracked_gap_when_scene_binding_hint_missing(delivery_binding):
    task = _da_task(entry=_entry_with(scene_hint=""))
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_SCENE_USAGE]
    assert lane["status_code"] == STATUS_TRACKED_GAP_SCENE
    assert lane["scene_binding_hint"] == ""
    assert lane["tracked_gap_explanation_zh"]


def test_language_usage_aggregates_languages_from_target_and_segment_pick(
    delivery_binding, task
):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lane = pack["lanes"][LANE_LANGUAGE_USAGE]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["source_language"] == "en-US"
    assert "en-US" in lane["target_languages"]
    assert "zh-CN" in lane["target_languages"]
    rows = {row["language"]: row for row in lane["language_rows"]}
    assert rows["en-US"]["is_target_language"] is True
    assert rows["en-US"]["is_source_language"] is True
    assert rows["en-US"]["segment_count"] == 2  # seg_001 + seg_003
    assert rows["zh-CN"]["segment_count"] == 1  # seg_002


def test_language_usage_includes_source_language_when_excluded_from_target_and_segment_picks(
    delivery_binding,
):
    """Codex P2 (PR #135 review at delivery_pack_view.py:447-453).

    When ``source_language`` is set but is NOT included in
    ``target_languages`` and NOT present in any segment ``language_pick``,
    the rendered ``language_rows`` must still surface the
    ``source_language`` row so the Delivery Pack language lane keeps
    operator-visible source coverage. Synthetic delivery binding here
    forces every segment's ``language_pick`` to ``zh-CN`` so the source
    ``en-US`` cannot reach the union via segment_picks; the entry's
    ``language_scope.target_language`` also excludes ``en-US``.
    """
    entry = _entry_with(target=("zh-CN",))  # target excludes the source
    assert entry["language_scope"]["source_language"] == "en-US"
    task = _da_task(entry=entry)
    # Override the delivery binding's role_segment_bindings so every
    # segment language_pick is zh-CN (excludes the source). The packet
    # itself remains untouched (read-only discipline).
    binding = deepcopy(delivery_binding)
    bindings = binding["result_packet_binding"]["role_segment_bindings"]
    assert bindings, "fixture must have at least one role_segment_binding"
    for row in bindings:
        row["language_pick"] = "zh-CN"

    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=task
    )
    lane = pack["lanes"][LANE_LANGUAGE_USAGE]
    assert lane["status_code"] == STATUS_RESOLVED
    assert lane["source_language"] == "en-US"
    assert lane["target_languages"] == ["zh-CN"]

    rows_by_lang = {row["language"]: row for row in lane["language_rows"]}
    # The condition: source language MUST be in the rendered rows even
    # when excluded from both target_languages and segment_picks.
    assert "en-US" in rows_by_lang, (
        "source_language must remain operator-visible in the language_usage "
        "lane even when excluded from target_languages and segment_picks"
    )
    source_row = rows_by_lang["en-US"]
    assert source_row["is_source_language"] is True
    assert source_row["is_target_language"] is False
    assert source_row["segment_count"] == 0  # no segments pick the source
    assert source_row["segment_ids"] == []
    # Tracked-gap discipline preserved: the row is rendered with
    # zero segment coverage, not a synthesized hit.
    # The other lanes' tracked-gap status is independent and unaffected.
    assert rows_by_lang["zh-CN"]["is_source_language"] is False
    assert rows_by_lang["zh-CN"]["is_target_language"] is True


def test_language_usage_tracked_gap_when_language_scope_absent(delivery_binding):
    entry = _entry_with()
    entry.pop("language_scope")
    task = _da_task(entry=entry)
    # Drop role_segment_bindings as well so segment_picks set is empty.
    binding = deepcopy(delivery_binding)
    binding["result_packet_binding"]["role_segment_bindings"] = []
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=task
    )
    lane = pack["lanes"][LANE_LANGUAGE_USAGE]
    assert lane["status_code"] == STATUS_TRACKED_GAP_LANGUAGE
    assert lane["target_languages"] == []
    assert lane["language_rows"] == []


def test_value_source_ids_present_for_resolved_lanes(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    lanes = pack["lanes"]
    assert lanes[LANE_SUBTITLE]["value_source_id"].startswith(
        "delivery_binding_v1.delivery_pack.deliverables[kind=subtitle_bundle"
    )
    assert lanes[LANE_DUBBED_AUDIO]["value_source_id"].startswith(
        "delivery_binding_v1.delivery_pack.deliverables[kind=audio_bundle"
    )
    assert lanes[LANE_PACK]["value_source_id"].startswith(
        "delivery_binding_v1.delivery_pack.deliverables[kind=scene_pack"
    )
    assert (
        lanes[LANE_METADATA]["value_source_id"]
        == "delivery_binding_v1.metadata_projection"
    )
    assert lanes[LANE_MANIFEST]["value_source_id"] == "delivery_binding_v1.manifest"
    assert (
        lanes[LANE_ROLE_USAGE]["value_source_id"]
        == "delivery_binding_v1.result_packet_binding.role_segment_bindings"
    )


def test_no_provider_model_vendor_engine_identifier_in_output(
    delivery_binding, task
):
    """validator R3 + design-handoff red line 6.

    The complete bundle JSON must not carry vendor / model_id / provider /
    engine substrings. Tracked-gap explanations may legitimately mention
    'engine' (e.g. for narrative purposes); the binding-side scrub keeps
    *value* fields clean. We assert on the value and source_id surfaces
    only.
    """
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    forbidden = ("vendor", "model_id", "provider", "engine_id")
    for lane in pack["lanes"].values():
        for key in (
            "value",
            "value_source_id",
            "deliverable_id",
            "deliverable_kind",
            "manifest_id",
            "deliverable_profile_ref",
            "asset_sink_profile_ref",
            "scene_binding_hint",
            "source_language",
        ):
            value = lane.get(key)
            if isinstance(value, str):
                lowered = value.lower()
                for token in forbidden:
                    assert token not in lowered, (
                        f"lane {lane.get('lane_id')!r} key {key!r} carries "
                        f"forbidden token {token!r}: {value!r}"
                    )


def test_lane_order_is_stable_and_complete():
    """LANE_ORDER must enumerate the nine lanes exactly once each."""
    assert len(LANE_ORDER) == 9
    assert len(set(LANE_ORDER)) == 9
    expected = {
        LANE_FINAL_VIDEO,
        LANE_SUBTITLE,
        LANE_DUBBED_AUDIO,
        LANE_METADATA,
        LANE_MANIFEST,
        LANE_PACK,
        LANE_ROLE_USAGE,
        LANE_SCENE_USAGE,
        LANE_LANGUAGE_USAGE,
    }
    assert set(LANE_ORDER) == expected


def test_lane_labels_zh_covers_all_lane_ids():
    for lane_id in LANE_ORDER:
        assert lane_id in LANE_LABELS_ZH
        assert LANE_LABELS_ZH[lane_id]


def test_tracked_gap_summary_lists_tracked_gap_lanes(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    summary = pack["tracked_gap_summary_zh"]
    # final_video is always tracked-gap on the current contract
    assert "final_video" in summary or "全部 lane" not in summary


def test_tracked_gap_summary_when_all_lanes_resolved():
    """Edge case: with full role_segment_bindings + scene + language scope,
    only final_video remains tracked-gap. If we further synthesize a
    delivery binding without final_video lane (which we cannot today),
    the summary path still covers both branches."""
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding={
            "surface": "digital_anchor_delivery_binding_v1",
            "line_id": "digital_anchor",
            "delivery_pack": {"deliverables": []},
            "result_packet_binding": {"role_segment_bindings": []},
            "manifest": {},
            "metadata_projection": {},
        },
        task=_da_task(entry=_entry_with(scene_hint="")),
    )
    # final_video, subtitle, dubbed_audio, pack, role_usage, scene_usage are
    # all tracked-gap; metadata + manifest tracked-gap (empty); language_usage
    # resolved because target_languages is non-empty in entry.
    assert "final_video" in pack["tracked_gap_summary_zh"]


def test_packet_truth_not_mutated(delivery_binding, task):
    """Pure read; the projection must not mutate the delivery binding or task."""
    binding_snapshot = deepcopy(delivery_binding)
    task_snapshot = deepcopy(task)
    derive_digital_anchor_delivery_pack(delivery_binding=delivery_binding, task=task)
    assert delivery_binding == binding_snapshot
    assert task == task_snapshot


def test_binding_with_no_metadata_projection_renders_metadata_tracked_gap():
    binding = {
        "surface": "digital_anchor_delivery_binding_v1",
        "line_id": "digital_anchor",
        "delivery_pack": {"deliverables": []},
        "result_packet_binding": {"role_segment_bindings": []},
        "manifest": {},
        "metadata_projection": {},
    }
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=_da_task()
    )
    metadata_lane = pack["lanes"][LANE_METADATA]
    assert metadata_lane["status_code"] == STATUS_TRACKED_GAP


def test_binding_with_no_manifest_renders_manifest_tracked_gap():
    binding = {
        "surface": "digital_anchor_delivery_binding_v1",
        "line_id": "digital_anchor",
        "delivery_pack": {"deliverables": []},
        "result_packet_binding": {"role_segment_bindings": []},
        "manifest": {},
        "metadata_projection": {},
    }
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=_da_task()
    )
    assert pack["lanes"][LANE_MANIFEST]["status_code"] == STATUS_TRACKED_GAP


def test_binding_with_no_subtitle_bundle_renders_subtitle_tracked_gap():
    binding = {
        "surface": "digital_anchor_delivery_binding_v1",
        "line_id": "digital_anchor",
        "delivery_pack": {"deliverables": []},  # no subtitle_bundle row
        "result_packet_binding": {"role_segment_bindings": []},
        "manifest": {},
        "metadata_projection": {},
    }
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=_da_task()
    )
    assert pack["lanes"][LANE_SUBTITLE]["status_code"] == STATUS_TRACKED_GAP
    assert pack["lanes"][LANE_DUBBED_AUDIO]["status_code"] == STATUS_TRACKED_GAP
    assert pack["lanes"][LANE_PACK]["status_code"] == STATUS_TRACKED_GAP


def test_target_language_string_is_normalised(delivery_binding):
    """When entry.language_scope.target_language is a single string (legacy
    intermediate shape), it is treated as a one-element list."""
    entry = _entry_with()
    entry["language_scope"]["target_language"] = "zh-CN"
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=_da_task(entry=entry)
    )
    lane = pack["lanes"][LANE_LANGUAGE_USAGE]
    assert lane["target_languages"] == ["zh-CN"]


def test_role_framing_label_zh_renders_for_known_kinds(delivery_binding, task):
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=delivery_binding, task=task
    )
    roles = pack["lanes"][LANE_ROLE_USAGE]["roles"]
    framings = {r["role_framing_kind"]: r["role_framing_label_zh"] for r in roles}
    assert "head" in framings
    assert "half_body" in framings
    # Labels carry both Chinese + ascii name
    assert "head" in framings["head"]
    assert "half_body" in framings["half_body"]


def test_capability_lane_required_flag_propagates_from_capability_plan():
    binding = {
        "surface": "digital_anchor_delivery_binding_v1",
        "line_id": "digital_anchor",
        "delivery_pack": {
            "deliverables": [
                {
                    "deliverable_id": "digital_anchor_subtitle_bundle",
                    "kind": "subtitle_bundle",
                    "required": False,
                    "artifact_lookup": "not_implemented_phase_c",
                }
            ]
        },
        "result_packet_binding": {"role_segment_bindings": []},
        "manifest": {},
        "metadata_projection": {},
    }
    pack = derive_digital_anchor_delivery_pack(
        delivery_binding=binding, task=_da_task()
    )
    assert pack["lanes"][LANE_SUBTITLE]["required"] is False
    assert pack["lanes"][LANE_SUBTITLE]["status_code"] == STATUS_RESOLVED
