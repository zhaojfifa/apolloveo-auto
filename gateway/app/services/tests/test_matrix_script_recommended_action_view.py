"""Tests for RC PR-3 — Matrix Script Result-Capability Recovery (RC-R4).

Covers ``gateway.app.services.matrix_script.recommended_action_view`` per
``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R4 + §5 RC PR-3.

Test floor per gate spec §5.2: ≥25 cases. This file lands 35.

Hard discipline checked:

- Helper returns ``{}`` for non-Matrix-Script panels so callers'
  gating preserves Hot Follow / Digital Anchor / baseline bytewise
  unchanged.
- Recommended variant is named only when at least one MS-W4 variation
  is in the closed ``publishable_candidate`` bucket; never elevates a
  blocked or undetermined variant into a publishable claim.
- Operator-language reason for blocked / undetermined cases is
  sourced from the existing closed ``HEAD_REASON_LABELS_ZH`` map; no
  new producer.
- No fake ``final_video`` / publish artifact / delivery claim — the
  helper rejects any media URL substring and exposes a no-publish-
  claim note explicitly.
- No raw internal handles — no ``script_slot_ref``, ``slot_body_ref``,
  ``content://`` substring, or raw slot id leaks into the payload.
- Helper signature has no ``publish_readiness`` parameter — no second
  truth source structurally possible.
"""
from __future__ import annotations

import inspect

import pytest

from gateway.app.services.matrix_script.preview_compare_view import (
    RECOMMENDED_BUCKET_BLOCKED,
    RECOMMENDED_BUCKET_PUBLISHABLE,
    RECOMMENDED_BUCKET_UNDETERMINED,
)
from gateway.app.services.matrix_script.recommended_action_view import (
    HEADLINE_BLOCKED_ZH,
    HEADLINE_PUBLISHABLE_ZH,
    HEADLINE_UNDETERMINED_ZH,
    NEXT_ACTION_BLOCKED_ZH,
    NEXT_ACTION_PUBLISHABLE_ZH,
    NEXT_ACTION_UNDETERMINED_ZH,
    derive_matrix_script_recommended_action,
)


def _ms_panel() -> dict:
    return {"panel_kind": "matrix_script"}


def _variation_row(
    *,
    variation_id: str = "cell_001",
    bucket: str = RECOMMENDED_BUCKET_PUBLISHABLE,
    head_reason: str | None = None,
    label: str | None = None,
    explanation: str = "",
) -> dict:
    return {
        "variation_id": variation_id,
        "recommended_bucket": bucket,
        "recommended_label_zh": label
        or {
            RECOMMENDED_BUCKET_PUBLISHABLE: "推荐 · 可发布候选",
            RECOMMENDED_BUCKET_BLOCKED: "暂不推荐 · 发布门禁阻塞",
            RECOMMENDED_BUCKET_UNDETERMINED: "—",
        }[bucket],
        "recommended_explanation_zh": explanation,
        "recommended_head_reason": head_reason,
    }


def _preview(*, variations: list[dict]) -> dict:
    return {"is_matrix_script": True, "variations": variations}


def _readable_variants(*, variants: list[dict] | None = None) -> dict:
    return {
        "is_matrix_script": True,
        "variant_candidates": variants
        or [
            {
                "variation_id": "cell_001",
                "axis_summary_zh": "语气=轻松（casual） · 受众=面向消费者（b2c） · 时长=60s",
                "differentiator_zh": "差异轴 · tone=轻松（casual）",
                "length_hint_zh": "60s",
                "has_bound_slot": True,
            },
            {
                "variation_id": "cell_002",
                "axis_summary_zh": "语气=俏皮（playful） · 受众=面向消费者（b2c） · 时长=60s",
                "differentiator_zh": "差异轴 · tone=俏皮（playful）",
                "length_hint_zh": "60s",
                "has_bound_slot": True,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Panel gating
# ---------------------------------------------------------------------------


def test_returns_empty_for_hot_follow_panel() -> None:
    assert (
        derive_matrix_script_recommended_action(
            _preview(variations=[_variation_row()]),
            _readable_variants(),
            {"panel_kind": "hot_follow"},
        )
        == {}
    )


def test_returns_empty_for_digital_anchor_panel() -> None:
    assert (
        derive_matrix_script_recommended_action(
            _preview(variations=[_variation_row()]),
            _readable_variants(),
            {"panel_kind": "digital_anchor"},
        )
        == {}
    )


def test_returns_empty_when_panel_missing() -> None:
    assert (
        derive_matrix_script_recommended_action(
            _preview(variations=[_variation_row()]), _readable_variants(), None
        )
        == {}
    )


# ---------------------------------------------------------------------------
# Publishable case — recommended variant named
# ---------------------------------------------------------------------------


def test_publishable_picks_first_publishable_variant() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(variation_id="cell_001", bucket=RECOMMENDED_BUCKET_PUBLISHABLE),
                _variation_row(variation_id="cell_002", bucket=RECOMMENDED_BUCKET_PUBLISHABLE),
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_PUBLISHABLE
    assert out["recommended_variant"]["variation_id"] == "cell_001"


def test_publishable_carries_axis_summary_and_differentiator_from_readable_variants() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(variation_id="cell_001", bucket=RECOMMENDED_BUCKET_PUBLISHABLE)]),
        _readable_variants(),
        _ms_panel(),
    )
    rec = out["recommended_variant"]
    assert "轻松（casual）" in rec["axis_summary_zh"]
    assert "面向消费者（b2c）" in rec["axis_summary_zh"]
    assert "60s" in rec["axis_summary_zh"]
    assert "tone=轻松（casual）" in rec["differentiator_zh"]


def test_publishable_headline_and_next_action_are_actionable() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)]),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["headline_zh"] == HEADLINE_PUBLISHABLE_ZH
    assert out["next_action_zh"] == NEXT_ACTION_PUBLISHABLE_ZH
    assert "Delivery Center" in out["next_action_zh"]


def test_publishable_picks_first_publishable_when_blocked_appears_first() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(
                    variation_id="cell_b",
                    bucket=RECOMMENDED_BUCKET_BLOCKED,
                    head_reason="ready_gate_blocking",
                ),
                _variation_row(
                    variation_id="cell_p", bucket=RECOMMENDED_BUCKET_PUBLISHABLE
                ),
            ]
        ),
        _readable_variants(
            variants=[
                {
                    "variation_id": "cell_p",
                    "axis_summary_zh": "语气=正式（formal）",
                    "differentiator_zh": "",
                    "length_hint_zh": "—",
                    "has_bound_slot": True,
                }
            ]
        ),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_PUBLISHABLE
    assert out["recommended_variant"]["variation_id"] == "cell_p"


def test_publishable_candidate_count_reports_total_publishable() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(variation_id="a", bucket=RECOMMENDED_BUCKET_PUBLISHABLE),
                _variation_row(variation_id="b", bucket=RECOMMENDED_BUCKET_BLOCKED),
                _variation_row(variation_id="c", bucket=RECOMMENDED_BUCKET_PUBLISHABLE),
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["candidate_count"] == 2


def test_publishable_when_readable_variants_lacks_entry_falls_back_to_em_dash() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(variation_id="cell_unknown", bucket=RECOMMENDED_BUCKET_PUBLISHABLE)]),
        _readable_variants(),  # fixture has cell_001 / cell_002 only
        _ms_panel(),
    )
    rec = out["recommended_variant"]
    assert rec["variation_id"] == "cell_unknown"
    assert rec["axis_summary_zh"] == "—"
    assert rec["differentiator_zh"] == ""


# ---------------------------------------------------------------------------
# Blocked case — operator-language reason from head_reason
# ---------------------------------------------------------------------------


def test_blocked_status_kind_when_no_publishable_variant() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(
                    bucket=RECOMMENDED_BUCKET_BLOCKED,
                    head_reason="ready_gate_blocking",
                )
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_BLOCKED


def test_blocked_recommended_variant_is_none() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="compose_not_ready")
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["recommended_variant"] is None


def test_blocked_headline_and_next_action() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="final_missing")]),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["headline_zh"] == HEADLINE_BLOCKED_ZH
    assert out["next_action_zh"] == NEXT_ACTION_BLOCKED_ZH


def test_blocked_head_reason_label_is_operator_language() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="compose_not_ready")]),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["head_reason"] == "compose_not_ready"
    assert out["head_reason_label_zh"] == "合成前置项未就绪"
    assert "合成前置项未就绪" in out["reason_zh"]


def test_blocked_unknown_head_reason_falls_through_verbatim() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(
                    bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="future_unknown"
                )
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["head_reason_label_zh"] == "future_unknown"


# ---------------------------------------------------------------------------
# Undetermined case
# ---------------------------------------------------------------------------


def test_undetermined_when_no_variations() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[]), _readable_variants(variants=[]), _ms_panel()
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_UNDETERMINED
    assert out["recommended_variant"] is None
    assert out["candidate_count"] == 0


def test_undetermined_when_all_variations_undetermined() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                _variation_row(bucket=RECOMMENDED_BUCKET_UNDETERMINED),
                _variation_row(variation_id="cell_002", bucket=RECOMMENDED_BUCKET_UNDETERMINED),
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_UNDETERMINED
    assert out["headline_zh"] == HEADLINE_UNDETERMINED_ZH
    assert out["next_action_zh"] == NEXT_ACTION_UNDETERMINED_ZH


def test_undetermined_does_not_claim_publishable() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[]), _readable_variants(variants=[]), _ms_panel()
    )
    assert out["recommended_variant"] is None
    assert "publishable" not in out["headline_zh"].lower()
    assert "publishable" not in out["status_label_zh"].lower()


# ---------------------------------------------------------------------------
# No fake publish / delivery / final_video
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bucket,head_reason",
    [
        (RECOMMENDED_BUCKET_PUBLISHABLE, "publishable_ok"),
        (RECOMMENDED_BUCKET_BLOCKED, "ready_gate_blocking"),
        (RECOMMENDED_BUCKET_BLOCKED, "final_missing"),
        (RECOMMENDED_BUCKET_BLOCKED, "compose_not_ready"),
        (RECOMMENDED_BUCKET_UNDETERMINED, None),
    ],
)
def test_no_fake_final_video_or_media_url(bucket: str, head_reason: str | None) -> None:
    variations = (
        [_variation_row(bucket=bucket, head_reason=head_reason)] if bucket else []
    )
    out = derive_matrix_script_recommended_action(
        _preview(variations=variations), _readable_variants(), _ms_panel()
    )
    blob = repr(out).lower()
    for forbidden in (
        "https://",
        "http://",
        ".mp4",
        ".mov",
        "final_video_url",
        "preview_url",
        "publish_url",
    ):
        assert forbidden not in blob


def test_no_publish_claim_note_present_in_every_status() -> None:
    for variations in (
        [_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)],
        [_variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="final_missing")],
        [],
    ):
        out = derive_matrix_script_recommended_action(
            _preview(variations=variations), _readable_variants(), _ms_panel()
        )
        assert "RC PR-4" in out["no_publish_claim_note_zh"]
        assert "final_video" in out["no_publish_claim_note_zh"]


# ---------------------------------------------------------------------------
# No raw internal handles in payload
# ---------------------------------------------------------------------------


def test_no_raw_slot_or_body_ref_in_payload() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                {
                    "variation_id": "cell_001",
                    "recommended_bucket": RECOMMENDED_BUCKET_PUBLISHABLE,
                    "recommended_label_zh": "推荐 · 可发布候选",
                    "recommended_explanation_zh": "",
                    "recommended_head_reason": None,
                    # The MS-W4 surface carries these for its own table;
                    # the recommended-action lane MUST NOT pass them through.
                    "script_slot_ref": "slot_001",
                    "slot_body_ref": "content://matrix-script/x/slot/slot_001",
                }
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    blob = repr(out)
    assert "slot_001" not in blob
    assert "content://" not in blob
    assert "script_slot_ref" not in blob
    assert "slot_body_ref" not in blob


def test_no_vendor_or_model_strings_in_payload() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)]),
        _readable_variants(),
        _ms_panel(),
    )
    blob = repr(out).lower()
    for forbidden in ("vendor", "model_id", "provider", "engine", "swiftcraft"):
        assert forbidden not in blob


# ---------------------------------------------------------------------------
# No second truth source — structural assertions
# ---------------------------------------------------------------------------


def test_helper_signature_has_no_publish_readiness_parameter() -> None:
    sig = inspect.signature(derive_matrix_script_recommended_action)
    assert "publish_readiness" not in sig.parameters


def test_helper_does_not_call_compute_publish_readiness() -> None:
    """Module must not invoke or import the unified producer.

    Docstrings can mention the producer name as authority context;
    what we forbid is an actual call site or import statement.
    """
    import gateway.app.services.matrix_script.recommended_action_view as mod

    src = open(mod.__file__).read()
    assert "compute_publish_readiness(" not in src
    assert "import compute_publish_readiness" not in src
    assert "from gateway.app.services.operator_visible_surfaces.publish_readiness" not in src


def test_helper_signature_only_takes_documented_inputs() -> None:
    sig = inspect.signature(derive_matrix_script_recommended_action)
    assert set(sig.parameters.keys()) == {
        "preview_compare",
        "readable_variants",
        "line_specific_panel",
    }


def test_helper_consumes_recommended_bucket_verbatim() -> None:
    """When `recommended_bucket` says blocked, the lane must NOT
    elevate the variant into a publishable claim regardless of any
    other field on the row.
    """
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                {
                    "variation_id": "cell_x",
                    "recommended_bucket": RECOMMENDED_BUCKET_BLOCKED,
                    "recommended_label_zh": "暂不推荐 · 发布门禁阻塞",
                    "recommended_explanation_zh": "",
                    "recommended_head_reason": "publish_not_ready",
                    "publishable": True,  # adversarial: never trusted
                    "publish_url": "https://attacker.example/x.mp4",
                }
            ]
        ),
        _readable_variants(),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_BLOCKED
    assert out["recommended_variant"] is None
    blob = repr(out).lower()
    assert "https://" not in blob
    assert "attacker" not in blob


# ---------------------------------------------------------------------------
# Defensive degradation
# ---------------------------------------------------------------------------


def test_handles_missing_preview_compare() -> None:
    out = derive_matrix_script_recommended_action(None, _readable_variants(), _ms_panel())
    assert out["status_kind"] == RECOMMENDED_BUCKET_UNDETERMINED


def test_handles_missing_readable_variants() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(variations=[_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)]),
        None,
        _ms_panel(),
    )
    rec = out["recommended_variant"]
    assert rec["axis_summary_zh"] == "—"


def test_skips_non_mapping_variation_entries() -> None:
    out = derive_matrix_script_recommended_action(
        _preview(
            variations=[
                None,
                "junk",
                _variation_row(variation_id="cell_x", bucket=RECOMMENDED_BUCKET_PUBLISHABLE),
            ]
        ),
        _readable_variants(
            variants=[
                {
                    "variation_id": "cell_x",
                    "axis_summary_zh": "—",
                    "differentiator_zh": "",
                    "length_hint_zh": "—",
                    "has_bound_slot": False,
                }
            ]
        ),
        _ms_panel(),
    )
    assert out["status_kind"] == RECOMMENDED_BUCKET_PUBLISHABLE
    assert out["recommended_variant"]["variation_id"] == "cell_x"


def test_panel_title_subtitle_present_in_every_status() -> None:
    for variations in (
        [_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)],
        [_variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="ready_gate_blocking")],
        [],
    ):
        out = derive_matrix_script_recommended_action(
            _preview(variations=variations), _readable_variants(), _ms_panel()
        )
        assert out["panel_title_zh"] == "推荐版本与下一步动作"
        assert out["panel_subtitle_zh"]
        assert out["is_matrix_script"] is True


def test_status_kind_belongs_to_existing_closed_enum() -> None:
    closed = {
        RECOMMENDED_BUCKET_PUBLISHABLE,
        RECOMMENDED_BUCKET_BLOCKED,
        RECOMMENDED_BUCKET_UNDETERMINED,
    }
    for variations in (
        [_variation_row(bucket=RECOMMENDED_BUCKET_PUBLISHABLE)],
        [_variation_row(bucket=RECOMMENDED_BUCKET_BLOCKED, head_reason="x")],
        [],
    ):
        out = derive_matrix_script_recommended_action(
            _preview(variations=variations), _readable_variants(), _ms_panel()
        )
        assert out["status_kind"] in closed


def test_template_renders_three_recommended_action_states_distinctly() -> None:
    """Template-level: confirm three distinct render branches +
    `data-status-kind` anchor on the recommended-action panel.
    """
    template_path = "gateway/app/templates/task_workbench.html"
    with open(template_path) as fh:
        template = fh.read()
    start = template.index("matrix-script-recommended-action-panel")
    end = template.index("matrix-script-readable-variants-panel", start)
    panel = template[start:end]
    # `data-status-kind` exposes the closed bucket on the panel root.
    assert "data-status-kind=" in panel
    # Variant card only renders when a recommended_variant is present.
    assert "ms_recommended_action.recommended_variant" in panel
    # No raw-handle render directives.
    assert "script_slot_ref" not in panel
    assert "slot_body_ref" not in panel
    # Operator-language anchors present.
    assert "ms-recommended-action-headline" in panel
    assert "ms-recommended-action-next-action" in panel
    assert "ms-recommended-action-no-publish-claim-note" in panel
