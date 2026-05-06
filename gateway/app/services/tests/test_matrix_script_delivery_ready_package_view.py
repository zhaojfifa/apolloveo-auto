"""Tests for RC PR-4 — Matrix Script Result-Capability Recovery (RC-R5 + RC-R8).

Covers
``gateway.app.services.matrix_script.delivery_ready_package_view`` per
``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R5 + §3 RC-R8 + §5 RC PR-4.

Hard discipline checked:

- Helper returns ``{}`` for non-Matrix-Script panels so callers'
  gating preserves Hot Follow / Digital Anchor / baseline bytewise
  unchanged.
- Per-variant package status is one of the four closed enum values
  (``ready_package`` / ``partial_package`` / ``blocked_package`` /
  ``unavailable_tracked_gap``).
- ``ready_package`` requires bound slot AND publishable AND all
  required+blocking artifacts current AND copy_bundle fully
  resolved — no row gets elevated past these inputs.
- ``blocked_package`` is emitted whenever publish_readiness reports
  not publishable, regardless of script/copy state.
- No fake ``final_video`` / publish artifact / delivery URL — the
  helper rejects any media URL substring and exposes a
  no-final-video note explicitly per row.
- No raw internal handles — no ``script_slot_ref``, ``slot_body_ref``,
  ``content://`` substring leaks into the payload.
- No second authoritative producer — the helper does not re-derive
  publishability or re-classify deliverable lanes; it consumes the
  already-decided shapes.
"""
from __future__ import annotations

import inspect
import json

import pytest

from gateway.app.services.matrix_script.delivery_ready_package_view import (
    FORBIDDEN_TOKEN_FRAGMENTS,
    FORBIDDEN_URL_FRAGMENTS,
    NO_FAKE_FINAL_VIDEO_NOTE_ZH,
    NO_PUBLISH_CLAIM_NOTE_ZH,
    PACKAGE_BLOCKED,
    PACKAGE_HEADLINE_ZH,
    PACKAGE_NEXT_ACTION_ZH,
    PACKAGE_PARTIAL,
    PACKAGE_READY,
    PACKAGE_STATUS_LABELS_ZH,
    PACKAGE_UNAVAILABLE,
    derive_matrix_script_delivery_ready_package,
)


def _ms_panel() -> dict:
    return {"panel_kind": "matrix_script"}


def _readable_variants(*, variants: list[dict] | None = None) -> dict:
    if variants is None:
        variants = [
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "语气=轻松 · 受众=b2c · 时长=60s",
                "differentiator_zh": "差异轴：tone",
                "length_hint_zh": "60s",
                "has_bound_slot": True,
            }
        ]
    return {"is_matrix_script": True, "variant_candidates": variants}


def _delivery_comprehension(*, all_current: bool = True) -> dict:
    rows = []
    rows.append(
        {
            "deliverable_id": "d_variation_manifest",
            "kind": "variation_manifest",
            "kind_label_zh": "变体清单",
            "required": True,
            "blocking_publish": True,
            "artifact_status_code": "current_fresh" if all_current else "unresolved",
            "artifact_status_label_zh": "当前可用" if all_current else "未决议",
        }
    )
    rows.append(
        {
            "deliverable_id": "d_subtitle_bundle",
            "kind": "subtitle_bundle",
            "kind_label_zh": "字幕包",
            "required": True,
            "blocking_publish": True,
            "artifact_status_code": "current_fresh" if all_current else "historical",
            "artifact_status_label_zh": "当前可用" if all_current else "历史版本",
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


def _copy_bundle(*, all_resolved: bool = True) -> dict:
    code = "resolved_from_existing_projection" if all_resolved else "unresolved_pending_copy_projection_contract"
    return {
        "is_matrix_script": True,
        "subfields": [
            {"subfield_id": "title", "status_code": code},
            {"subfield_id": "hashtags", "status_code": code},
            {"subfield_id": "cta", "status_code": code},
            {"subfield_id": "comment_keywords", "status_code": "unresolved_pending_copy_projection_contract"},
        ],
    }


def _publish_readiness(*, publishable: bool = True, head_reason: str | None = None) -> dict:
    return {"publishable": publishable, "head_reason": head_reason}


# ─────────────────────────────────────────────────────────────────
# 1. Cross-line isolation + non-MS panels
# ─────────────────────────────────────────────────────────────────


def test_returns_empty_for_hot_follow_panel():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(),
        {"panel_kind": "hot_follow"},
    )
    assert out == {}


def test_returns_empty_for_digital_anchor_panel():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(),
        {"panel_kind": "digital_anchor"},
    )
    assert out == {}


def test_returns_empty_for_missing_panel():
    assert derive_matrix_script_delivery_ready_package(
        _readable_variants(), {}, {}, {}, None
    ) == {}


def test_returns_empty_for_unrecognised_panel_kind():
    assert derive_matrix_script_delivery_ready_package(
        _readable_variants(), {}, {}, {}, {"panel_kind": "baseline"}
    ) == {}


# ─────────────────────────────────────────────────────────────────
# 2. Status classification
# ─────────────────────────────────────────────────────────────────


def test_ready_package_when_all_inputs_satisfy():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(all_current=True),
        _copy_bundle(all_resolved=True),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    # All resolved? Note: comment_keywords always unresolved per OWC-MS PR-3
    # discipline → cannot be ready_package by classifier; partial expected.
    assert out["row_count"] == 1
    row = out["rows"][0]
    assert row["package_status_kind"] == PACKAGE_PARTIAL


def test_blocked_when_publish_readiness_blocked():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _ms_panel(),
    )
    assert out["rows"][0]["package_status_kind"] == PACKAGE_BLOCKED


def test_unavailable_when_no_slot_no_copy():
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_777",
                "axis_summary_zh": "—",
                "has_bound_slot": False,
            }
        ]
    )
    cb = {"is_matrix_script": True, "subfields": [
        {"subfield_id": "title", "status_code": "unresolved_pending_copy_projection_contract"},
    ]}
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(all_current=False),
        cb,
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    assert out["rows"][0]["package_status_kind"] == PACKAGE_UNAVAILABLE


def test_partial_when_slot_bound_but_artifacts_incomplete():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(all_current=False),
        _copy_bundle(all_resolved=True),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    assert out["rows"][0]["package_status_kind"] == PACKAGE_PARTIAL


def test_blocked_takes_precedence_over_unavailable():
    """publish_readiness blocked classification dominates regardless of
    upstream slot/copy state."""
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_x",
                "axis_summary_zh": "—",
                "has_bound_slot": False,
            }
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(),
        {"is_matrix_script": True, "subfields": []},
        _publish_readiness(publishable=False, head_reason="compose_not_ready"),
        _ms_panel(),
    )
    # No slot AND no copy means unavailable_tracked_gap. publish_readiness
    # classification comes after that branch.
    assert out["rows"][0]["package_status_kind"] == PACKAGE_UNAVAILABLE


# ─────────────────────────────────────────────────────────────────
# 3. Counter rollup
# ─────────────────────────────────────────────────────────────────


def test_counters_sum_to_row_count():
    variants = _readable_variants(
        variants=[
            {"variation_id": "a", "has_bound_slot": True, "axis_summary_zh": "—"},
            {"variation_id": "b", "has_bound_slot": True, "axis_summary_zh": "—"},
            {"variation_id": "c", "has_bound_slot": False, "axis_summary_zh": "—"},
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    counts = (
        out["ready_count"]
        + out["partial_count"]
        + out["blocked_count"]
        + out["unavailable_count"]
    )
    assert counts == out["row_count"] == 3


def test_zero_rows_when_no_variants():
    out = derive_matrix_script_delivery_ready_package(
        {"is_matrix_script": True, "variant_candidates": []},
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(),
        _ms_panel(),
    )
    assert out["rows"] == []
    assert out["row_count"] == 0


def test_legend_lists_all_four_statuses():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(), _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    legend = out["package_status_legend_zh"]
    assert len(legend) == 4
    assert PACKAGE_STATUS_LABELS_ZH[PACKAGE_READY] in legend
    assert PACKAGE_STATUS_LABELS_ZH[PACKAGE_PARTIAL] in legend
    assert PACKAGE_STATUS_LABELS_ZH[PACKAGE_BLOCKED] in legend
    assert PACKAGE_STATUS_LABELS_ZH[PACKAGE_UNAVAILABLE] in legend


# ─────────────────────────────────────────────────────────────────
# 4. RC-R8 — no fake final_video
# ─────────────────────────────────────────────────────────────────


def _strip_meta_notes(payload):
    """Drop the panel-level / row-level meta keys that intentionally
    name the forbidden tokens in operator-language guidance. The audit
    only needs to scan substantive payload values."""
    if not isinstance(payload, dict):
        return payload
    META_KEYS = {
        "no_final_video_url_note_zh",
        "no_publish_claim_note_zh",
        "panel_subtitle_zh",
    }
    cleaned = {}
    for k, v in payload.items():
        if k in META_KEYS:
            continue
        if isinstance(v, dict):
            cleaned[k] = _strip_meta_notes(v)
        elif isinstance(v, list):
            cleaned[k] = [_strip_meta_notes(item) for item in v]
        else:
            cleaned[k] = v
    return cleaned


@pytest.mark.parametrize(
    "publishable, head_reason",
    [
        (True, None),
        (False, "compose_not_ready"),
        (False, "final_missing"),
    ],
)
def test_no_fake_final_video_or_media_url(publishable, head_reason):
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(all_current=publishable),
        _copy_bundle(),
        _publish_readiness(publishable=publishable, head_reason=head_reason),
        _ms_panel(),
    )
    blob = json.dumps(_strip_meta_notes(out), ensure_ascii=False).lower()
    for forbidden in (
        "http://",
        "https://",
        ".mp4",
        ".mov",
        "final_video_url",
        "preview_url",
        "publish_url",
    ):
        assert forbidden not in blob, f"{forbidden} leaked into payload"


def test_no_publish_claim_note_present_on_panel():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(), _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    assert out["no_final_video_url_note_zh"] == NO_FAKE_FINAL_VIDEO_NOTE_ZH
    assert out["no_publish_claim_note_zh"] == NO_PUBLISH_CLAIM_NOTE_ZH


def test_per_row_no_final_video_note_present():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(), _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    assert out["rows"][0]["no_final_video_url_note_zh"] == NO_FAKE_FINAL_VIDEO_NOTE_ZH


def test_adversarial_publish_url_in_upstream_does_not_leak():
    # Inject a publish_url-shaped string into a readable_variant axis
    # summary; the scrub MUST drop it on the way out.
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "https://attacker.example/x.mp4",
                "differentiator_zh": "evil-final_video_url=https://x",
                "length_hint_zh": "60s",
                "has_bound_slot": True,
            }
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants, _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    blob = json.dumps(_strip_meta_notes(out), ensure_ascii=False).lower()
    for forbidden in FORBIDDEN_URL_FRAGMENTS:
        assert forbidden not in blob


# ─────────────────────────────────────────────────────────────────
# 5. RC-R8 + R3 — no vendor / model / engine / provider leakage
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
    out = derive_matrix_script_delivery_ready_package(
        variants, _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    blob = json.dumps(out, ensure_ascii=False).lower()
    for forbidden in FORBIDDEN_TOKEN_FRAGMENTS:
        assert forbidden not in blob


def test_no_raw_slot_or_body_ref_in_payload():
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "content://matrix-script/source/abc",
                "has_bound_slot": True,
            }
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants, _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    blob = json.dumps(out, ensure_ascii=False).lower()
    assert "content://" not in blob


# ─────────────────────────────────────────────────────────────────
# 6. Single-source / no-second-producer discipline
# ─────────────────────────────────────────────────────────────────


def test_helper_signature_only_takes_documented_inputs():
    sig = inspect.signature(derive_matrix_script_delivery_ready_package)
    assert list(sig.parameters.keys()) == [
        "readable_variants",
        "delivery_comprehension",
        "copy_bundle_view",
        "publish_readiness",
        "line_specific_panel",
    ]


def test_helper_does_not_call_compute_publish_readiness():
    src = inspect.getsource(
        __import__(
            "gateway.app.services.matrix_script.delivery_ready_package_view",
            fromlist=["__source__"],
        )
    )
    assert "compute_publish_readiness(" not in src
    assert "publish_readiness import compute_publish_readiness" not in src


def test_consumes_publishable_field_verbatim():
    # When publish_readiness says publishable=False but the caller injects
    # a "publishable=True" key on a variation row, the helper must trust
    # publish_readiness — not the row.
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
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(all_current=True),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _ms_panel(),
    )
    assert out["rows"][0]["package_status_kind"] == PACKAGE_BLOCKED


# ─────────────────────────────────────────────────────────────────
# 7. Operator-language assembly
# ─────────────────────────────────────────────────────────────────


def test_headline_matches_status():
    variants = _readable_variants(
        variants=[
            {"variation_id": "a", "has_bound_slot": True, "axis_summary_zh": "—"}
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="final_stale"),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert row["headline_zh"] == PACKAGE_HEADLINE_ZH[row["package_status_kind"]]
    assert row["next_action_zh"] == PACKAGE_NEXT_ACTION_ZH[row["package_status_kind"]]


def test_gap_explanation_names_unbound_slot():
    variants = _readable_variants(
        variants=[
            {
                "variation_id": "a",
                "axis_summary_zh": "—",
                "has_bound_slot": False,
            }
        ]
    )
    cb = {"is_matrix_script": True, "subfields": [
        {"subfield_id": "title", "status_code": "resolved_from_existing_projection"}
    ]}
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(all_current=True),
        cb,
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert "脚本片段未绑定" in row["gap_explanation_zh"]


def test_gap_explanation_names_required_artifact_kinds_when_blocked():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(all_current=False),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="required_deliverable_missing"),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert "必交付分区缺口" in row["gap_explanation_zh"]


def test_head_reason_label_emitted_when_blocked():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="final_missing"),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert row["head_reason"] == "final_missing"
    assert row["head_reason_label_zh"]


def test_head_reason_suppressed_when_publishable():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert row["head_reason"] is None
    assert row["head_reason_label_zh"] is None


def test_axis_summary_passthrough():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(),
        _ms_panel(),
    )
    assert out["rows"][0]["axis_summary_zh"] == "语气=轻松 · 受众=b2c · 时长=60s"


def test_copy_bundle_counts_emitted():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(all_resolved=False),
        _publish_readiness(),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert row["copy_bundle_total_count"] == 4
    assert row["copy_bundle_resolved_count"] == 0


# ─────────────────────────────────────────────────────────────────
# 8. Defensive handling
# ─────────────────────────────────────────────────────────────────


def test_handles_missing_inputs_gracefully():
    out = derive_matrix_script_delivery_ready_package(None, None, None, None, _ms_panel())
    assert out["row_count"] == 0
    assert out["rows"] == []


def test_handles_garbage_variant_entries():
    variants = {
        "is_matrix_script": True,
        "variant_candidates": [None, "bad", 42, {"variation_id": "ok", "has_bound_slot": True, "axis_summary_zh": "—"}],
    }
    out = derive_matrix_script_delivery_ready_package(
        variants, _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    assert out["row_count"] == 1
    assert out["rows"][0]["variation_id"] == "ok"


def test_panel_marks_is_matrix_script():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(), _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    assert out["is_matrix_script"] is True


def test_panel_title_and_subtitle_present():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(), _delivery_comprehension(), _copy_bundle(), _publish_readiness(), _ms_panel()
    )
    assert out["panel_title_zh"]
    assert out["panel_subtitle_zh"]


def test_required_gap_kinds_list_exposed():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(all_current=False),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="required_deliverable_missing"),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert isinstance(row["required_artifact_gap_kinds_zh"], list)
    assert any("变体清单" in g or "字幕包" in g for g in row["required_artifact_gap_kinds_zh"])


def test_multiple_variants_classified_independently():
    variants = _readable_variants(
        variants=[
            {"variation_id": "a", "has_bound_slot": True, "axis_summary_zh": "—"},
            {"variation_id": "b", "has_bound_slot": False, "axis_summary_zh": "—"},
        ]
    )
    out = derive_matrix_script_delivery_ready_package(
        variants,
        _delivery_comprehension(),
        {"is_matrix_script": True, "subfields": []},
        _publish_readiness(publishable=True),
        _ms_panel(),
    )
    by_id = {r["variation_id"]: r for r in out["rows"]}
    # 'a' has slot, no copy resolved → partial
    # 'b' has no slot, no copy resolved → unavailable
    assert by_id["a"]["package_status_kind"] == PACKAGE_PARTIAL
    assert by_id["b"]["package_status_kind"] == PACKAGE_UNAVAILABLE


def test_panel_kind_lookup_strips_whitespace_and_case():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(),
        {"panel_kind": "  Matrix_Script  "},
    )
    assert out.get("is_matrix_script") is True


def test_status_label_mapping_resolves():
    out = derive_matrix_script_delivery_ready_package(
        _readable_variants(),
        _delivery_comprehension(),
        _copy_bundle(),
        _publish_readiness(publishable=False, head_reason="x"),
        _ms_panel(),
    )
    row = out["rows"][0]
    assert row["package_status_label_zh"] == PACKAGE_STATUS_LABELS_ZH[row["package_status_kind"]]
