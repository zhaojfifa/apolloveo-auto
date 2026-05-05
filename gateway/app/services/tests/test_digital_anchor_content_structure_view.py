"""OWC-DA PR-2 / DA-W4 — Workbench B 内容结构面 read-view tests.

Authority: docs/reviews/owc_da_gate_spec_v1.md §3 DA-W4 +
docs/product/digital_anchor_product_flow_v1.md §6.1B.

Hard discipline asserted by these cases:
- Non-digital_anchor panels return ``{}``.
- Source script ref is rendered as opaque handle (never dereferenced).
- Section bodies degrade gracefully to closed unresolved sentinel.
- Helper does not author roles[] / segments[] enumeration.
- Helper does not mutate inputs.
"""
from __future__ import annotations

from copy import deepcopy

from gateway.app.services.digital_anchor.content_structure_view import (
    SECTION_EMPHASIS,
    SECTION_OUTLINE,
    SECTION_PARAGRAPH,
    SECTION_RHYTHM,
    STATUS_RESOLVED,
    STATUS_UNRESOLVED,
    derive_digital_anchor_content_structure_view,
)


_DA_PANEL = {"panel_kind": "digital_anchor"}
_MS_PANEL = {"panel_kind": "matrix_script"}

_TASK = {
    "task_id": "t_da_002",
    "kind": "digital_anchor",
    "config": {
        "line_id": "digital_anchor",
        "entry": {
            "topic": "Q2 培训说明",
            "source_script_ref": "content://digital-anchor/source/abc123",
            "language_scope": {
                "source_language": "zh-CN",
                "target_language": ["en-US", "ja-JP"],
            },
            "output_intent": "培训说明口播",
            "operator_notes": "术语保持一致",
            "role_framing_hint": "half_body",
            "dub_kind_hint": "tts_role_voice",
            "lip_sync_kind_hint": "tight",
            "speaker_segment_count_hint": 4,
        },
    },
}

_ROLE_SPEAKER_SURFACE = {
    "role_surface": {
        "roles": [
            {"role_id": "r1", "framing_kind": "half_body"},
        ],
    },
    "speaker_surface": {
        "segments": [
            {"segment_id": "seg_01", "binds_role_id": "r1"},
            {"segment_id": "seg_02", "binds_role_id": "r1"},
        ],
    },
}


def test_returns_empty_for_matrix_script_panel() -> None:
    assert derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _MS_PANEL) == {}


def test_returns_empty_for_missing_panel() -> None:
    assert derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, None) == {}


def test_basic_render_emits_is_digital_anchor_marker() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert bundle["is_digital_anchor"] is True


def test_source_script_ref_is_rendered_opaque_not_dereferenced() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert bundle["source_script_ref_value"] == "content://digital-anchor/source/abc123"
    assert "opaque" in bundle["source_script_ref_status_code"]


def test_outline_section_resolved_when_topic_and_intent_present() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_OUTLINE)
    assert section["body_status_code"] == STATUS_RESOLVED
    assert "Q2 培训说明" in section["body_text"]


def test_outline_section_unresolved_when_topic_missing() -> None:
    task = deepcopy(_TASK)
    task["config"]["entry"]["topic"] = ""
    bundle = derive_digital_anchor_content_structure_view(task, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_OUTLINE)
    assert section["body_status_code"] == STATUS_UNRESOLVED


def test_paragraph_section_uses_segments_when_present() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_PARAGRAPH)
    assert section["body_status_code"] == STATUS_RESOLVED
    assert "已规划 2 段" in section["body_text"]


def test_paragraph_section_falls_back_to_hint_when_no_segments() -> None:
    surface = {"role_surface": {"roles": []}, "speaker_surface": {"segments": []}}
    bundle = derive_digital_anchor_content_structure_view(_TASK, surface, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_PARAGRAPH)
    assert section["body_status_code"] == STATUS_RESOLVED
    assert "计划段数：4" in section["body_text"]


def test_paragraph_section_unresolved_when_no_segments_no_hint() -> None:
    task = deepcopy(_TASK)
    task["config"]["entry"]["speaker_segment_count_hint"] = None
    surface = {"role_surface": {"roles": []}, "speaker_surface": {"segments": []}}
    bundle = derive_digital_anchor_content_structure_view(task, surface, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_PARAGRAPH)
    assert section["body_status_code"] == STATUS_UNRESOLVED


def test_emphasis_section_resolved_with_target_languages() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_EMPHASIS)
    assert section["body_status_code"] == STATUS_RESOLVED
    assert "en-US" in section["body_text"]


def test_rhythm_section_uses_entry_hints() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_RHYTHM)
    assert section["body_status_code"] == STATUS_RESOLVED
    assert "tts_role_voice" in section["body_text"]


def test_rhythm_section_unresolved_when_no_hints() -> None:
    task = deepcopy(_TASK)
    task["config"]["entry"]["role_framing_hint"] = ""
    task["config"]["entry"]["dub_kind_hint"] = ""
    task["config"]["entry"]["lip_sync_kind_hint"] = ""
    bundle = derive_digital_anchor_content_structure_view(task, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    section = next(s for s in bundle["sections"] if s["section_id"] == SECTION_RHYTHM)
    assert section["body_status_code"] == STATUS_UNRESOLVED


def test_language_scope_carries_target_language_list() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert bundle["language_scope"]["source_language"] == "zh-CN"
    assert bundle["language_scope"]["target_language"] == ["en-US", "ja-JP"]


def test_helper_emits_no_provider_or_swiftcraft_identifier() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    rendered = repr(bundle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in rendered


def test_helper_does_not_mutate_inputs() -> None:
    snapshot_task = deepcopy(_TASK)
    snapshot_surface = deepcopy(_ROLE_SPEAKER_SURFACE)
    derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert _TASK == snapshot_task
    assert _ROLE_SPEAKER_SURFACE == snapshot_surface


def test_phase_b_authoring_forbidden_message_present() -> None:
    bundle = derive_digital_anchor_content_structure_view(_TASK, _ROLE_SPEAKER_SURFACE, _DA_PANEL)
    assert "OWC-DA gate spec §4.1 / §3 DA-W4" in bundle["phase_b_authoring_forbidden_label_zh"]
