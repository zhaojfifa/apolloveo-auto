"""Tests for RC PR-4 — Matrix Script Result-Capability Recovery (RC-R7 + RC-R8).

Covers
``gateway.app.services.matrix_script.publish_backfill_readiness_view``
per
``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R7 + §3 RC-R8 + §5 RC PR-4.

Hard discipline checked:

- Helper returns ``{}`` for non-Matrix-Script readable variants OR for
  closures whose surface is not Matrix Script — Hot Follow / Digital
  Anchor publish hubs never receive the bundle.
- Per-variant readiness is one of the closed enum values
  (``publishable_now`` / ``gated_pending_publish_readiness`` /
  ``already_published_backfill_pending_metrics`` /
  ``already_failed_pending_retry`` / ``tracked_gap_no_artifact``).
- No fake ``final_video`` / publish_url / media URL is rendered in the
  payload — even when the closure carries a real ``publish_url``,
  the helper does NOT echo that string out (the caller's
  multi-channel backfill panel renders it via its own field).
- No second authoritative producer — publishability is read verbatim
  from publish_readiness; closure publish_status is read verbatim
  from the closed enum.
- No closed-enum widening — out-of-enum publish_status values are
  ignored.
- No raw internal handles or vendor / model identifiers leak into
  the payload.
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script.publish_backfill_readiness_view import (
    FORBIDDEN_TOKEN_FRAGMENTS,
    FORBIDDEN_URL_FRAGMENTS,
    NO_FAKE_FINAL_VIDEO_NOTE_ZH,
    READINESS_ALREADY_FAILED,
    READINESS_ALREADY_PUBLISHED,
    READINESS_GATED,
    READINESS_LABELS_ZH,
    READINESS_PUBLISHABLE_NOW,
    READINESS_TRACKED_GAP,
    derive_matrix_script_publish_backfill_readiness,
)


def _readable_variants(*, variants: list[dict] | None = None) -> dict:
    if variants is None:
        variants = [
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "—",
                "has_bound_slot": True,
            }
        ]
    return {"is_matrix_script": True, "variant_candidates": variants}


def _delivery_comprehension(*, with_required_lane: bool = True, all_current: bool = False) -> dict:
    rows = []
    if with_required_lane:
        rows.append(
            {
                "deliverable_id": "d1",
                "kind": "variation_manifest",
                "kind_label_zh": "变体清单",
                "required": True,
                "blocking_publish": True,
                "artifact_status_code": "current_fresh" if all_current else "unresolved",
            }
        )
    return {
        "is_matrix_script": True,
        "lanes": {
            "required_blocking": {"rows": rows, "row_count": len(rows)},
            "required_non_blocking": {"rows": [], "row_count": 0},
            "optional_non_blocking": {"rows": [], "row_count": 0},
        },
    }


def _publish_readiness(*, publishable: bool = True, head_reason: str | None = None) -> dict:
    return {"publishable": publishable, "head_reason": head_reason}


def _closure(*, variation_status: dict[str, str] | None = None) -> dict:
    rows = []
    for vid, status in (variation_status or {}).items():
        rows.append({"variation_id": vid, "publish_status": status})
    return {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "line_id": "matrix_script",
        "variation_feedback": rows,
        "feedback_closure_records": [],
        "channel_metrics": [],
    }


def _strip_meta(payload):
    if not isinstance(payload, dict):
        return payload
    META = {"no_final_video_url_note_zh", "panel_subtitle_zh"}
    cleaned = {}
    for k, v in payload.items():
        if k in META:
            continue
        if isinstance(v, dict):
            cleaned[k] = _strip_meta(v)
        elif isinstance(v, list):
            cleaned[k] = [_strip_meta(i) for i in v]
        else:
            cleaned[k] = v
    return cleaned


# ─────────────────────────────────────────────────────────────────
# 1. Cross-line / non-MS isolation
# ─────────────────────────────────────────────────────────────────


def test_returns_empty_for_non_ms_readable_variants():
    out = derive_matrix_script_publish_backfill_readiness(
        {"variant_candidates": [{"variation_id": "x"}]},
        _delivery_comprehension(),
        _publish_readiness(),
        _closure(),
    )
    assert out == {}


def test_returns_empty_for_non_ms_closure_surface():
    closure = {"surface": "digital_anchor_publish_feedback_closure_v1", "variation_feedback": []}
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(),
        closure,
    )
    assert out == {}


def test_handles_missing_closure_as_no_publish_records():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(publishable=True), None
    )
    row = out["rows"][0]
    assert row["readiness_kind"] == READINESS_PUBLISHABLE_NOW


def test_handles_missing_inputs_returns_empty_for_no_variants():
    out = derive_matrix_script_publish_backfill_readiness(None, None, None, None)
    assert out == {}


# ─────────────────────────────────────────────────────────────────
# 2. Readiness classification
# ─────────────────────────────────────────────────────────────────


def test_publishable_now_when_publishable_and_no_closure_record():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_PUBLISHABLE_NOW


def test_gated_when_publish_readiness_blocked():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _closure(),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_GATED


def test_already_published_when_closure_status_published():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "published"}),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_ALREADY_PUBLISHED


def test_already_published_when_retracted():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "retracted"}),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_ALREADY_PUBLISHED


def test_already_failed_when_closure_status_failed():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "failed"}),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_ALREADY_FAILED


def test_tracked_gap_when_no_slot_and_no_required_lane():
    variants = _readable_variants(
        variants=[{"variation_id": "x", "axis_summary_zh": "—", "has_bound_slot": False}]
    )
    out = derive_matrix_script_publish_backfill_readiness(
        variants,
        _delivery_comprehension(with_required_lane=False),
        _publish_readiness(publishable=False, head_reason="compose_not_ready"),
        _closure(),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_TRACKED_GAP


def test_pending_status_in_closure_does_not_count_as_published():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "pending"}),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_PUBLISHABLE_NOW


def test_out_of_enum_status_ignored():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "moonshot_state"}),
    )
    # Out-of-enum value treated as no record → publishable_now.
    assert out["rows"][0]["readiness_kind"] == READINESS_PUBLISHABLE_NOW


# ─────────────────────────────────────────────────────────────────
# 3. Counter rollup
# ─────────────────────────────────────────────────────────────────


def test_counters_sum_to_row_count():
    variants = _readable_variants(
        variants=[
            {"variation_id": "a", "has_bound_slot": True, "axis_summary_zh": "—"},
            {"variation_id": "b", "has_bound_slot": True, "axis_summary_zh": "—"},
            {"variation_id": "c", "has_bound_slot": True, "axis_summary_zh": "—"},
        ]
    )
    closure = _closure(variation_status={"a": "published", "b": "failed"})
    out = derive_matrix_script_publish_backfill_readiness(
        variants, _delivery_comprehension(), _publish_readiness(publishable=True), closure
    )
    total = (
        out["publishable_now_count"]
        + out["gated_count"]
        + out["already_published_count"]
        + out["already_failed_count"]
        + out["tracked_gap_count"]
    )
    assert total == out["row_count"] == 3
    assert out["already_published_count"] == 1
    assert out["already_failed_count"] == 1
    assert out["publishable_now_count"] == 1


def test_legend_lists_all_five_statuses():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert len(out["readiness_legend_zh"]) == 5
    for kind in (
        READINESS_PUBLISHABLE_NOW,
        READINESS_GATED,
        READINESS_ALREADY_PUBLISHED,
        READINESS_ALREADY_FAILED,
        READINESS_TRACKED_GAP,
    ):
        assert READINESS_LABELS_ZH[kind] in out["readiness_legend_zh"]


def test_zero_rows_when_no_variants():
    out = derive_matrix_script_publish_backfill_readiness(
        {"is_matrix_script": True, "variant_candidates": []},
        _delivery_comprehension(),
        _publish_readiness(),
        _closure(),
    )
    assert out["row_count"] == 0


# ─────────────────────────────────────────────────────────────────
# 4. RC-R8 — no fake final_video / no publish_url echo
# ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "publishable, head_reason, status",
    [
        (True, None, None),
        (False, "compose_not_ready", None),
        (True, None, "published"),
        (True, None, "failed"),
    ],
)
def test_no_fake_final_video_or_media_url(publishable, head_reason, status):
    closure = _closure(variation_status={"cell_001": status} if status else None)
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=publishable, head_reason=head_reason),
        closure,
    )
    blob = json.dumps(_strip_meta(out), ensure_ascii=False).lower()
    for forbidden in (
        "http://",
        "https://",
        ".mp4",
        ".mov",
        "final_video_url",
        "preview_url",
    ):
        assert forbidden not in blob, f"{forbidden} leaked into payload"


def test_publish_url_from_closure_is_not_echoed_in_payload():
    """Even when the closure variation_feedback row carries a real
    publish_url, this helper MUST NOT echo it to the payload — the
    multi-channel backfill panel renders publish_url via its own field.
    """
    closure = {
        "surface": "matrix_script_publish_feedback_closure_v1",
        "line_id": "matrix_script",
        "variation_feedback": [
            {
                "variation_id": "cell_001",
                "publish_status": "published",
                "publish_url": "https://example.test/published.mp4",
            }
        ],
    }
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        closure,
    )
    blob = json.dumps(_strip_meta(out), ensure_ascii=False).lower()
    assert "https://" not in blob
    assert "example.test" not in blob


def test_no_final_video_note_present_at_panel_level():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["no_final_video_url_note_zh"] == NO_FAKE_FINAL_VIDEO_NOTE_ZH


def test_no_final_video_note_present_per_row():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["rows"][0]["no_final_video_url_note_zh"] == NO_FAKE_FINAL_VIDEO_NOTE_ZH


# ─────────────────────────────────────────────────────────────────
# 5. R3 — no vendor / model / engine / provider leakage
# ─────────────────────────────────────────────────────────────────


def test_no_vendor_or_model_strings_in_payload():
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "vendor=acme provider=foo model_id=42 engine=evil",
                "has_bound_slot": True,
            }
        ]
    )
    out = derive_matrix_script_publish_backfill_readiness(
        variants, _delivery_comprehension(), _publish_readiness(), _closure()
    )
    blob = json.dumps(_strip_meta(out), ensure_ascii=False).lower()
    for forbidden in FORBIDDEN_TOKEN_FRAGMENTS:
        assert forbidden not in blob


def test_no_content_handle_leakage():
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "content://matrix-script/source/abc",
                "has_bound_slot": True,
            }
        ]
    )
    out = derive_matrix_script_publish_backfill_readiness(
        variants, _delivery_comprehension(), _publish_readiness(), _closure()
    )
    blob = json.dumps(_strip_meta(out), ensure_ascii=False).lower()
    assert "content://" not in blob


# ─────────────────────────────────────────────────────────────────
# 6. Single-source / no-second-producer discipline
# ─────────────────────────────────────────────────────────────────


def test_helper_signature_only_takes_documented_inputs():
    sig = inspect.signature(derive_matrix_script_publish_backfill_readiness)
    assert list(sig.parameters.keys()) == [
        "readable_variants",
        "delivery_comprehension",
        "publish_readiness",
        "closure",
    ]


def test_helper_does_not_call_compute_publish_readiness():
    src = inspect.getsource(
        __import__(
            "gateway.app.services.matrix_script.publish_backfill_readiness_view",
            fromlist=["__source__"],
        )
    )
    assert "compute_publish_readiness(" not in src


def test_consumes_publishable_field_verbatim_when_blocked():
    # publish_readiness.publishable=False MUST classify as gated even
    # if the variation row has a faux publishable=True attribute.
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "—",
                "has_bound_slot": True,
                "publishable": True,
            }
        ]
    )
    out = derive_matrix_script_publish_backfill_readiness(
        variants,
        _delivery_comprehension(),
        _publish_readiness(publishable=False, head_reason="final_stale"),
        _closure(),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_GATED


# ─────────────────────────────────────────────────────────────────
# 7. Operator-language assembly
# ─────────────────────────────────────────────────────────────────


def test_label_matches_kind():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _closure(),
    )
    row = out["rows"][0]
    assert row["readiness_label_zh"] == READINESS_LABELS_ZH[row["readiness_kind"]]


def test_gated_row_emits_head_reason_label():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _closure(),
    )
    row = out["rows"][0]
    assert row["head_reason"] == "final_missing"
    assert row["head_reason_label_zh"]


def test_publishable_row_suppresses_head_reason():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(),
    )
    row = out["rows"][0]
    assert row["head_reason"] is None
    assert row["head_reason_label_zh"] is None


def test_closure_status_label_zh_emitted_for_published_row():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"cell_001": "published"}),
    )
    assert out["rows"][0]["closure_publish_status"] == "published"
    assert out["rows"][0]["closure_publish_status_label_zh"] == "已发布"


def test_gap_summary_for_gated_row_names_required_kinds():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(with_required_lane=True, all_current=False),
        _publish_readiness(publishable=False, head_reason="required_deliverable_missing"),
        _closure(),
    )
    gap = out["rows"][0]["gap_summary_zh"]
    assert "必交付分区缺口" in gap or "head_reason" in gap


def test_axis_summary_passthrough():
    variants = _readable_variants(
        variants=[
            {"variation_id": "z", "axis_summary_zh": "语气=轻松", "has_bound_slot": True}
        ]
    )
    out = derive_matrix_script_publish_backfill_readiness(
        variants, _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["rows"][0]["axis_summary_zh"] == "语气=轻松"


# ─────────────────────────────────────────────────────────────────
# 8. Defensive handling
# ─────────────────────────────────────────────────────────────────


def test_handles_garbage_variant_rows():
    variants = {
        "is_matrix_script": True,
        "variant_candidates": [None, "bad", 1, {"variation_id": "ok", "has_bound_slot": True, "axis_summary_zh": "—"}],
    }
    out = derive_matrix_script_publish_backfill_readiness(
        variants, _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["row_count"] == 1
    assert out["rows"][0]["variation_id"] == "ok"


def test_panel_marks_is_matrix_script():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["is_matrix_script"] is True


def test_panel_title_and_subtitle_present():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(), _closure()
    )
    assert out["panel_title_zh"]
    assert out["panel_subtitle_zh"]


def test_closure_with_unrelated_variation_does_not_match():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(),
        _publish_readiness(publishable=True),
        _closure(variation_status={"some_other_cell": "published"}),
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_PUBLISHABLE_NOW


def test_closure_line_id_only_match_works():
    closure = {
        "surface": "",
        "line_id": "matrix_script",
        "variation_feedback": [{"variation_id": "cell_001", "publish_status": "published"}],
    }
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(), _delivery_comprehension(), _publish_readiness(publishable=True), closure
    )
    assert out["rows"][0]["readiness_kind"] == READINESS_ALREADY_PUBLISHED


def test_required_artifact_gap_kinds_listed():
    out = derive_matrix_script_publish_backfill_readiness(
        _readable_variants(),
        _delivery_comprehension(with_required_lane=True, all_current=False),
        _publish_readiness(publishable=False, head_reason="required_deliverable_missing"),
        _closure(),
    )
    row = out["rows"][0]
    assert isinstance(row["required_artifact_gap_kinds_zh"], list)
    assert any("变体清单" in g for g in row["required_artifact_gap_kinds_zh"])
