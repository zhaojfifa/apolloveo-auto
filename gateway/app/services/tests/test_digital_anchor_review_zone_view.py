"""OWC-DA PR-2 / DA-W7 — Workbench E 预览与校对面 read-view tests.

Authority: docs/reviews/owc_da_gate_spec_v1.md §3 DA-W7 +
docs/product/digital_anchor_product_flow_v1.md §6.1E.

Hard discipline asserted by these cases:
- Non-digital_anchor panels return ``{}``.
- Five review zones present in the closed order
  ``audition / video_preview / subtitle / cadence / qc``.
- Review-zone enum surfaces sorted on the bundle.
- No new endpoint introduced.
- Helper does not mutate inputs.
- Submit form binds to the existing DA D.1 closure events endpoint.
"""
from __future__ import annotations

from copy import deepcopy

from gateway.app.services.digital_anchor.publish_feedback_closure import REVIEW_ZONE_VALUES
from gateway.app.services.digital_anchor.review_zone_view import (
    REVIEW_EVENT_ENDPOINT_TEMPLATE,
    REVIEW_ZONE_ORDER,
    derive_digital_anchor_review_zone_view,
)


_DA_PANEL = {"panel_kind": "digital_anchor"}
_MS_PANEL = {"panel_kind": "matrix_script"}

_ROLE_SPEAKER_SURFACE = {
    "role_surface": {
        "roles": [
            {"role_id": "host_lead", "display_name": "主播", "framing_kind": "half_body"},
            {"role_id": "host_aux", "display_name": "副播", "framing_kind": "head"},
        ],
    },
    "speaker_surface": {
        "segments": [
            {"segment_id": "seg_01", "binds_role_id": "host_lead", "language_pick": "en-US", "dub_kind": "tts_role_voice"},
            {"segment_id": "seg_02", "binds_role_id": "host_aux", "language_pick": "ja-JP", "dub_kind": "tts_role_voice"},
        ],
    },
}

_CLOSURE_WITH_REVIEW = {
    "feedback_closure_records": [
        {
            "record_id": "rec_001",
            "event_kind": "operator_note",
            "row_scope": "role",
            "row_id": "host_lead",
            "review_zone": "audition",
            "actor_kind": "operator",
            "recorded_at": "2026-05-05T10:00:00Z",
        },
        {
            "record_id": "rec_002",
            "event_kind": "operator_note",
            "row_scope": "segment",
            "row_id": "seg_01",
            "review_zone": "subtitle",
            "actor_kind": "operator",
            "recorded_at": "2026-05-05T10:05:00Z",
        },
        {
            "record_id": "rec_003",
            "event_kind": "operator_note",
            "row_scope": "segment",
            "row_id": "seg_01",
            # legacy unzoned record
            "actor_kind": "operator",
            "recorded_at": "2026-05-05T10:10:00Z",
        },
    ],
}


def test_returns_empty_for_matrix_script_panel() -> None:
    assert derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _MS_PANEL) == {}


def test_returns_empty_when_panel_is_none() -> None:
    assert derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, None) == {}


def test_basic_render_emits_is_digital_anchor_marker() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert bundle["is_digital_anchor"] is True


def test_zones_emitted_in_closed_order() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    zone_ids = [zone["zone_id"] for zone in bundle["zones"]]
    assert zone_ids == list(REVIEW_ZONE_ORDER)


def test_review_zone_enum_surfaces_sorted_on_bundle() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert bundle["review_zone_enum"] == sorted(REVIEW_ZONE_VALUES)


def test_review_zone_enum_size_is_five() -> None:
    assert len(REVIEW_ZONE_VALUES) == 5


def test_row_scope_enum_carries_role_and_segment_only() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert bundle["row_scope_enum"] == ["role", "segment"]


def test_role_review_rows_one_per_role() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert {row["row_id"] for row in bundle["role_review_rows"]} == {"host_lead", "host_aux"}


def test_segment_review_rows_one_per_segment() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert {row["row_id"] for row in bundle["segment_review_rows"]} == {"seg_01", "seg_02"}


def test_endpoint_template_constant_resolves_to_da_closures_path() -> None:
    assert REVIEW_EVENT_ENDPOINT_TEMPLATE == "/api/digital-anchor/closures/{task_id}/events"


def test_endpoint_url_is_none_when_no_task_id() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert bundle["closure_endpoint_url"] is None


def test_endpoint_url_resolves_when_task_id_provided() -> None:
    bundle = derive_digital_anchor_review_zone_view(
        _ROLE_SPEAKER_SURFACE, None, _DA_PANEL, task_id="task_abc"
    )
    assert bundle["closure_endpoint_url"] == "/api/digital-anchor/closures/task_abc/events"


def test_submit_form_present_per_role_per_zone_when_task_id_set() -> None:
    bundle = derive_digital_anchor_review_zone_view(
        _ROLE_SPEAKER_SURFACE, None, _DA_PANEL, task_id="task_abc"
    )
    role_row = next(r for r in bundle["role_review_rows"] if r["row_id"] == "host_lead")
    audition = role_row["per_zone"]["audition"]
    assert audition["submit_form"]["row_scope"] == "role"
    assert audition["submit_form"]["row_id"] == "host_lead"
    assert audition["submit_form"]["review_zone"] == "audition"
    assert audition["submit_form"]["event_kind"] == "operator_note"


def test_submit_form_omitted_per_zone_when_no_task_id() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    role_row = bundle["role_review_rows"][0]
    assert role_row["per_zone"]["audition"]["submit_form"] is None


def test_history_count_reflects_existing_closure_records() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, _CLOSURE_WITH_REVIEW, _DA_PANEL)
    role_row = next(r for r in bundle["role_review_rows"] if r["row_id"] == "host_lead")
    assert role_row["per_zone"]["audition"]["history_count"] == 1
    assert role_row["per_zone"]["audition"]["is_reviewed"] is True


def test_legacy_unzoned_history_count_separates_untagged_records() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, _CLOSURE_WITH_REVIEW, _DA_PANEL)
    seg_row = next(r for r in bundle["segment_review_rows"] if r["row_id"] == "seg_01")
    assert seg_row["legacy_unzoned_history_count"] == 1


def test_helper_does_not_mutate_inputs() -> None:
    snapshot_surface = deepcopy(_ROLE_SPEAKER_SURFACE)
    snapshot_closure = deepcopy(_CLOSURE_WITH_REVIEW)
    derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, _CLOSURE_WITH_REVIEW, _DA_PANEL, task_id="task_abc")
    assert _ROLE_SPEAKER_SURFACE == snapshot_surface
    assert _CLOSURE_WITH_REVIEW == snapshot_closure


def test_helper_emits_no_provider_or_swiftcraft_identifier() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, _CLOSURE_WITH_REVIEW, _DA_PANEL, task_id="task_abc")
    rendered = repr(bundle).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in rendered


def test_phase_b_authoring_forbidden_message_present() -> None:
    bundle = derive_digital_anchor_review_zone_view(_ROLE_SPEAKER_SURFACE, None, _DA_PANEL)
    assert "OWC-DA gate spec §4.1" in bundle["phase_b_authoring_forbidden_label_zh"]
