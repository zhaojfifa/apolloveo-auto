"""Service-layer tests for the Digital Anchor create-entry payload builder
(Recovery PR-4).

Authority:
- ``docs/contracts/digital_anchor/task_entry_contract_v1.md``
- ``docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §7

Scope: closed-set validation, opaque-ref shape enforcement, hint-vs-truth
discipline (operator hints flow into ``metadata.notes``; no `roles[]` /
`segments[]` enumeration), forbidden-key rejection, and the closed
output payload shape.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from gateway.app.services.digital_anchor.create_entry import (
    DIGITAL_ANCHOR_LINE_ID,
    build_digital_anchor_entry,
    build_digital_anchor_task_payload,
)


def _good_kwargs(**overrides):
    base = {
        "topic": "数字人 demo",
        "source_script_ref": "content://digital-anchor/source/abc-001",
        # PR-4 reviewer-fix: contract-shaped `language_scope` mapping
        # replaces the flat `source_language` / `target_language`
        # arguments per `task_entry_contract_v1` §"Entry field set".
        "language_scope": {
            "source_language": "en",
            "target_language": ["zh", "mm"],
        },
        "role_profile_ref": "catalog://role_card/anchor_a_v1",
        "role_framing_hint": "half_body",
        "output_intent": "双语讲解短视频",
        "speaker_segment_count_hint": "2",
        "dub_kind_hint": "tts_role_voice",
        "lip_sync_kind_hint": "tight",
        "scene_binding_hint": "intro->seg1",
        "operator_notes": "note",
    }
    base.update(overrides)
    return base


def test_required_fields_round_trip():
    entry = build_digital_anchor_entry(**_good_kwargs())
    assert entry.topic == "数字人 demo"
    assert entry.source_language == "en"
    assert entry.target_language == ("zh", "mm")
    assert entry.role_framing_hint == "half_body"
    assert entry.speaker_segment_count_hint == 2


def test_language_scope_must_be_mapping():
    """Reviewer-fix #1: builder rejects flat source/target_language args
    and requires the contract-shaped `language_scope` mapping."""
    bad = _good_kwargs(language_scope="not-a-mapping")
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**bad)


def test_language_scope_unknown_subkey_rejected():
    """Reviewer-fix #1: only `source_language` + `target_language` are
    permitted as `language_scope` sub-keys."""
    bad = _good_kwargs(
        language_scope={
            "source_language": "en",
            "target_language": ["zh"],
            "vendor_id": "tencent",
        }
    )
    with pytest.raises(HTTPException) as exc:
        build_digital_anchor_entry(**bad)
    assert "language_scope" in exc.value.detail


def test_language_scope_target_language_accepts_list_or_csv():
    a = build_digital_anchor_entry(**_good_kwargs(
        language_scope={"source_language": "en", "target_language": ["zh", "mm"]}
    ))
    b = build_digital_anchor_entry(**_good_kwargs(
        language_scope={"source_language": "en", "target_language": "zh, mm"}
    ))
    assert a.target_language == ("zh", "mm")
    assert b.target_language == ("zh", "mm")


def test_payload_shape_matches_closed_output():
    entry = build_digital_anchor_entry(**_good_kwargs())
    payload = build_digital_anchor_task_payload(entry)

    assert payload["kind"] == DIGITAL_ANCHOR_LINE_ID
    assert payload["category_key"] == DIGITAL_ANCHOR_LINE_ID
    assert payload["status"] == "pending"
    assert payload["title"] == "数字人 demo"
    assert payload["source_url"] == "content://digital-anchor/source/abc-001"

    config = payload["config"]
    assert config["line_id"] == DIGITAL_ANCHOR_LINE_ID
    assert config["entry_contract"] == "digital_anchor_task_entry_v1"
    assert config["next_surfaces"] == {
        "workbench": f"/tasks/{payload['task_id']}",
        "delivery": f"/tasks/{payload['task_id']}/publish",
    }
    config_entry = config["entry"]
    assert set(config_entry.keys()) == {
        "topic",
        "source_script_ref",
        "language_scope",
        "role_profile_ref",
        "role_framing_hint",
        "output_intent",
        "speaker_segment_count_hint",
        "dub_kind_hint",
        "lip_sync_kind_hint",
        "scene_binding_hint",
        "operator_notes",
    }


def test_packet_seeds_only_two_line_specific_refs():
    """Builder seeds exactly two `line_specific_refs[]` skeletons (no roles[] / segments[])."""
    entry = build_digital_anchor_entry(**_good_kwargs())
    payload = build_digital_anchor_task_payload(entry)
    refs = payload["packet"]["line_specific_refs"]
    assert {ref["ref_id"] for ref in refs} == {
        "digital_anchor_role_pack",
        "digital_anchor_speaker_plan",
    }
    for ref in refs:
        assert "delta" not in ref, "builder must NOT author roles[] / segments[]"


def test_metadata_notes_carries_operator_hints():
    entry = build_digital_anchor_entry(**_good_kwargs())
    payload = build_digital_anchor_task_payload(entry)
    notes = payload["packet"]["metadata"]["notes"]
    for fragment in (
        "topic=数字人 demo",
        "output_intent=双语讲解短视频",
        "role_framing_hint=half_body",
        "speaker_segment_count_hint=2",
        "dub_kind_hint=tts_role_voice",
    ):
        assert fragment in notes


def test_unknown_role_framing_rejected():
    with pytest.raises(HTTPException) as exc:
        build_digital_anchor_entry(**_good_kwargs(role_framing_hint="silhouette"))
    assert "role_framing_hint" in exc.value.detail


def test_unknown_dub_kind_rejected():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(dub_kind_hint="cinema_voice"))


def test_unknown_lip_sync_kind_rejected():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(lip_sync_kind_hint="ultra"))


def test_segment_count_out_of_range_rejected():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(speaker_segment_count_hint="0"))
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(speaker_segment_count_hint="100"))


def test_source_script_ref_must_be_opaque():
    """Pasted body text or URL with disallowed scheme must be rejected."""
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(
            **_good_kwargs(source_script_ref="https://example.com/article")
        )
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(
            **_good_kwargs(source_script_ref="this is body text not a ref")
        )


def test_role_profile_ref_must_be_opaque():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(
            **_good_kwargs(role_profile_ref="https://cdn.example/avatar.png")
        )


def test_topic_with_vendor_substring_rejected():
    """Free-form text must not name a vendor / model / provider / engine."""
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(topic="use vendor X for this"))
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(
            **_good_kwargs(operator_notes="prefer engine_id=tencent")
        )


def test_extra_unknown_field_rejected():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(
            **_good_kwargs(),
            extra_fields=["roles", "segments", "vendor_id"],
        )


def test_target_language_required():
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(
            language_scope={"source_language": "en", "target_language": ""}
        ))
    with pytest.raises(HTTPException):
        build_digital_anchor_entry(**_good_kwargs(
            language_scope={"source_language": "en", "target_language": []}
        ))


def test_payload_does_not_carry_provider_identifiers():
    """Closed output payload audit — no vendor/model/provider/engine/donor key."""
    import json

    entry = build_digital_anchor_entry(**_good_kwargs())
    payload = build_digital_anchor_task_payload(entry)
    flat = json.dumps(payload, default=str).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert forbidden not in flat
