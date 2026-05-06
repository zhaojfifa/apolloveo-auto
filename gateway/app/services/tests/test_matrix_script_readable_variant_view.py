"""Tests for RC PR-2 — Matrix Script Result-Capability Recovery (RC-R1+R2+R3).

Covers ``gateway.app.services.matrix_script.readable_variant_view`` per
``docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md``
§3 RC-R1 + RC-R2 + RC-R3 + §5 RC PR-2.

Test floor per gate spec §5.2: ≥35 cases. This file lands 38.

Hard discipline checked:

- The helper returns ``{}`` for non-Matrix-Script panels so the caller's
  gating preserves Hot Follow / Digital Anchor / baseline bytewise
  unchanged.
- Each per-variation card always carries Hook + Body + CTA section rows
  in the canonical order (RC-R2 — structure preserved); empty sections
  render the closed unresolved sentinel.
- Per-variation Hook / Body / CTA expose readable strings (RC-R1) when
  the underlying entry + Phase B truth has signal.
- One-line per-variant summary names the localized axis selections +
  slot id + length hint (RC-R3); differentiator names the differing
  axes relative to invariant ones.
- No fake ``final_video`` — no media URL, no ``.mp4``, no ``preview_url``,
  no synthesised publish artifact.
- No vendor / model / provider / engine identifier leakage; the helper
  passes operator-visible entry strings through the same forbidden-token
  scrub used by MS-W7.
- The helper consumes the existing variation surface + entry truth +
  preview_compare diff_hints verbatim; no new producer.
"""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.readable_variant_view import (
    AUDIENCE_LABELS_ZH,
    STATUS_STRUCTURAL_ONLY,
    STATUS_STRUCTURAL_ONLY_LABEL_ZH,
    TONE_LABELS_ZH,
    derive_matrix_script_readable_variants,
)


def _ms_panel() -> dict:
    return {"panel_kind": "matrix_script"}


def _entry(
    *,
    topic: str = "春季新品上线",
    tone_hint: str = "active",
    audience_hint: str = "young",
    target_platform: str = "tiktok",
) -> dict:
    return {
        "topic": topic,
        "tone_hint": tone_hint,
        "audience_hint": audience_hint,
        "target_platform": target_platform,
        "language_scope": {"source_language": "zh", "target_language": ["en"]},
    }


def _task(*, entry: dict | None = None, kind: str = "matrix_script") -> dict:
    return {
        "task_id": "task_rc_pr2",
        "kind": kind,
        "config": {"entry": entry or _entry(), "line_id": "matrix_script"},
    }


def _variation_surface(
    *,
    cells: list[dict] | None = None,
    slots: list[dict] | None = None,
) -> dict:
    cells = cells if cells is not None else [
        {
            "cell_id": "cell_001",
            "axis_selections": {"tone": "casual", "audience": "b2c", "length": 60},
            "script_slot_ref": "slot_001",
        },
        {
            "cell_id": "cell_002",
            "axis_selections": {"tone": "playful", "audience": "b2c", "length": 60},
            "script_slot_ref": "slot_002",
        },
    ]
    slots = slots if slots is not None else [
        {
            "slot_id": "slot_001",
            "binds_cell_id": "cell_001",
            "body_ref": "content://matrix-script/task_rc_pr2/slot/slot_001",
            "length_hint": 60,
        },
        {
            "slot_id": "slot_002",
            "binds_cell_id": "cell_002",
            "body_ref": "content://matrix-script/task_rc_pr2/slot/slot_002",
            "length_hint": 60,
        },
    ]
    return {"variation_plan": {"cells": cells}, "copy_bundle": {"slots": slots}}


def _preview_compare(*, diff_hints: list[dict] | None = None) -> dict:
    return {
        "diff_hints": diff_hints
        or [
            {"axis_id": "tone", "is_differing": True, "distinct_value_count": 2},
            {"axis_id": "audience", "is_differing": False, "distinct_value_count": 1},
            {"axis_id": "length", "is_differing": False, "distinct_value_count": 1},
        ]
    }


# ---------------------------------------------------------------------------
# Panel gating — non-Matrix-Script must return {}
# ---------------------------------------------------------------------------


def test_returns_empty_when_panel_is_hot_follow() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), {"panel_kind": "hot_follow"}
    )
    assert out == {}


def test_returns_empty_when_panel_is_digital_anchor() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), {"panel_kind": "digital_anchor"}
    )
    assert out == {}


def test_returns_empty_when_panel_missing() -> None:
    assert derive_matrix_script_readable_variants(_task(), _variation_surface(), None) == {}


# ---------------------------------------------------------------------------
# Shared sections (RC-R2 task-level structure)
# ---------------------------------------------------------------------------


def test_shared_sections_have_three_rows_in_canonical_order() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel(), preview_compare=_preview_compare()
    )
    section_ids = [s["section_id"] for s in out["shared_sections"]]
    assert section_ids == ["hook", "body", "cta"]


def test_shared_hook_resolves_when_topic_present() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(topic="春季新品上线")),
        _variation_surface(),
        _ms_panel(),
    )
    hook = out["shared_sections"][0]
    assert hook["body_status_code"] == "resolved_from_source_content"
    assert "春季新品上线" in (hook["body_text"] or "")


def test_shared_hook_unresolved_when_topic_missing() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(topic="")),
        _variation_surface(),
        _ms_panel(),
    )
    hook = out["shared_sections"][0]
    assert hook["body_status_code"] == "unresolved_pending_outline_contract"
    assert hook["body_text"] is None


def test_shared_body_is_structural_only_with_canonical_structure() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    body = out["shared_sections"][1]
    # Shared Body never carries actual readable body text in this wave
    # (slot bodies remain opaque content:// handles per §8.F). The
    # operator must be able to distinguish this from real readable
    # content — hence the dedicated structural-only status code.
    assert body["body_status_code"] == STATUS_STRUCTURAL_ONLY
    assert body["body_status_label_zh"] == STATUS_STRUCTURAL_ONLY_LABEL_ZH
    assert "Hook" in body["body_text"]
    assert "CTA" in body["body_text"]


def test_shared_cta_unresolved_when_target_platform_missing() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(target_platform="")),
        _variation_surface(),
        _ms_panel(),
    )
    cta = out["shared_sections"][2]
    assert cta["body_status_code"] == "unresolved_pending_outline_contract"


# ---------------------------------------------------------------------------
# Per-variation readable sections (RC-R1 + RC-R2)
# ---------------------------------------------------------------------------


def test_each_variant_has_three_readable_sections_in_order() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    assert len(out["variant_candidates"]) == 2
    for variant in out["variant_candidates"]:
        ids = [s["section_id"] for s in variant["readable_sections"]]
        assert ids == ["hook", "body", "cta"]


def test_per_variation_hook_resolves_with_localized_tone_and_audience() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    hook = out["variant_candidates"][0]["readable_sections"][0]
    assert hook["body_status_code"] == "resolved_from_source_content"
    text = hook["body_text"]
    assert "轻松" in text  # tone=casual → 轻松
    assert "面向消费者" in text  # audience=b2c → 面向消费者


def test_per_variation_hook_unresolved_when_topic_missing() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(topic="")),
        _variation_surface(),
        _ms_panel(),
    )
    hook = out["variant_candidates"][0]["readable_sections"][0]
    assert hook["body_status_code"] == "unresolved_pending_outline_contract"


def test_per_variation_body_is_structural_only_with_length_and_tone() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    body = out["variant_candidates"][0]["readable_sections"][1]
    # The per-variation Body is honestly labelled as structural only
    # because slot bodies remain opaque handles in this wave. The
    # operator-visible text carries length + tone + canonical outline
    # but is NOT presented as resolved readable body.
    assert body["body_status_code"] == STATUS_STRUCTURAL_ONLY
    assert body["body_status_label_zh"] == STATUS_STRUCTURAL_ONLY_LABEL_ZH
    assert "60s" in body["body_text"]
    assert "轻松" in body["body_text"]
    # Raw slot identifier MUST NOT appear in operator-visible body text.
    assert "slot=slot_001" not in body["body_text"]
    assert "slot_001" not in body["body_text"]


def test_per_variation_body_unresolved_when_axis_and_slot_absent() -> None:
    cells = [{"cell_id": "cell_x", "axis_selections": {}, "script_slot_ref": ""}]
    slots: list[dict] = []
    out = derive_matrix_script_readable_variants(
        _task(),
        _variation_surface(cells=cells, slots=slots),
        _ms_panel(),
    )
    body = out["variant_candidates"][0]["readable_sections"][1]
    assert body["body_status_code"] == "unresolved_pending_outline_contract"


def test_per_variation_cta_resolves_from_target_platform() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(target_platform="douyin")),
        _variation_surface(),
        _ms_panel(),
    )
    cta = out["variant_candidates"][0]["readable_sections"][2]
    assert cta["body_status_code"] == "resolved_from_source_content"
    assert "douyin" in cta["body_text"]


def test_per_variation_cta_unresolved_when_target_platform_missing() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(target_platform="")),
        _variation_surface(),
        _ms_panel(),
    )
    cta = out["variant_candidates"][0]["readable_sections"][2]
    assert cta["body_status_code"] == "unresolved_pending_outline_contract"


# ---------------------------------------------------------------------------
# One-line per-variant summary + differentiator (RC-R3)
# ---------------------------------------------------------------------------


def test_one_line_axis_summary_uses_localized_labels() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    summary = out["variant_candidates"][0]["axis_summary_zh"]
    assert "语气=" in summary
    assert "轻松" in summary
    assert "受众=" in summary
    assert "面向消费者" in summary
    assert "时长=60s" in summary


def test_axis_summary_em_dash_when_no_axes() -> None:
    out = derive_matrix_script_readable_variants(
        _task(),
        _variation_surface(
            cells=[{"cell_id": "cell_x", "axis_selections": {}, "script_slot_ref": "s"}],
            slots=[{"slot_id": "s", "body_ref": "content://x"}],
        ),
        _ms_panel(),
    )
    assert out["variant_candidates"][0]["axis_summary_zh"] == "—"


def test_differentiator_names_differing_axes_only() -> None:
    out = derive_matrix_script_readable_variants(
        _task(),
        _variation_surface(),
        _ms_panel(),
        preview_compare=_preview_compare(),
    )
    diff = out["variant_candidates"][0]["differentiator_zh"]
    assert "tone=" in diff
    # audience and length are invariant in the fixture preview_compare;
    # they must NOT appear in the differentiator string.
    assert "audience=" not in diff
    assert "length=" not in diff


def test_differentiator_when_no_axes_differ() -> None:
    pc = _preview_compare(
        diff_hints=[
            {"axis_id": "tone", "is_differing": False, "distinct_value_count": 1},
            {"axis_id": "audience", "is_differing": False, "distinct_value_count": 1},
            {"axis_id": "length", "is_differing": False, "distinct_value_count": 1},
        ]
    )
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel(), preview_compare=pc
    )
    assert "完全一致" in out["variant_candidates"][0]["differentiator_zh"]


def test_differing_and_invariant_axes_forwarded_from_preview_compare() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel(), preview_compare=_preview_compare()
    )
    assert out["differing_axes"] == ["tone"]
    assert sorted(out["invariant_axes"]) == ["audience", "length"]


def test_variant_count_matches_cells() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    assert out["variant_count"] == 2
    assert len(out["variant_candidates"]) == 2


def test_variant_dict_does_not_expose_raw_slot_identifiers() -> None:
    """Raw internal handles MUST NOT leak into the operator-visible payload.

    This is a structural assertion: the helper output dict must not
    carry `script_slot_ref` or `slot_body_ref` keys, so the template
    physically cannot render them.
    """
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    for variant in out["variant_candidates"]:
        assert "script_slot_ref" not in variant
        assert "slot_body_ref" not in variant
        assert "slot_body_ref_note_zh" not in variant


def test_variant_dict_does_not_carry_content_scheme_strings() -> None:
    """Defensive: no `content://...` substring anywhere in the per-
    variant payload, even nested.
    """
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    for variant in out["variant_candidates"]:
        assert "content://" not in repr(variant)
    # And no raw slot id (e.g. "slot_001") anywhere in the variant.
    for variant in out["variant_candidates"]:
        blob = repr(variant)
        assert "slot_001" not in blob
        assert "slot_002" not in blob


def test_each_variant_has_bound_slot_boolean_and_label() -> None:
    """The operator sees only an operator-language indicator that a slot
    is bound; never the raw identifier.
    """
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    for variant in out["variant_candidates"]:
        assert variant["has_bound_slot"] is True
        assert "已绑定脚本片段" in variant["bound_slot_label_zh"]


def test_unbound_slot_renders_unbound_label() -> None:
    cells = [
        {
            "cell_id": "cell_x",
            "axis_selections": {"tone": "casual", "audience": "b2c", "length": 60},
            "script_slot_ref": "",
        }
    ]
    out = derive_matrix_script_readable_variants(
        _task(),
        _variation_surface(cells=cells, slots=[]),
        _ms_panel(),
    )
    variant = out["variant_candidates"][0]
    assert variant["has_bound_slot"] is False
    assert variant["bound_slot_label_zh"] == "尚未绑定脚本片段"


def test_each_variant_carries_opacity_note() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    note = out["variant_candidates"][0]["slot_body_opacity_note_zh"]
    assert "opaque" in note
    assert "不解引用" in note
    # The note itself names neither slot ids nor content:// scheme.
    assert "slot_" not in note
    assert "content://" not in note


def test_length_hint_zh_fallback_em_dash_when_slot_lacks_hint() -> None:
    cells = [
        {
            "cell_id": "cell_001",
            "axis_selections": {"tone": "casual", "audience": "b2c"},
            "script_slot_ref": "slot_001",
        }
    ]
    slots = [{"slot_id": "slot_001", "body_ref": "content://x"}]
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(cells=cells, slots=slots), _ms_panel()
    )
    assert out["variant_candidates"][0]["length_hint_zh"] == "—"


# ---------------------------------------------------------------------------
# RC-R8 forerunner: no fake final_video / no synthesised media
# ---------------------------------------------------------------------------


def test_no_fake_final_video_in_payload() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
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


def test_no_fake_final_video_note_present() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    assert "RC PR-4" in out["no_fake_final_video_note_zh"]
    assert "final_video" in out["no_fake_final_video_note_zh"]


def test_no_phase_b_authoring_note_present() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    assert "Phase B" in out["no_phase_b_authoring_note_zh"]


# ---------------------------------------------------------------------------
# Forbidden-token scrub (no vendor / model / provider / engine leakage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "topic",
    ["my vendor demo", "Provider review", "MODEL_ID test", "engine showcase"],
)
def test_forbidden_token_scrub_drops_vendor_strings_in_topic(topic: str) -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(topic=topic)),
        _variation_surface(),
        _ms_panel(),
    )
    hook = out["variant_candidates"][0]["readable_sections"][0]
    # Scrub returns "" for forbidden topic; helper falls back to
    # unresolved sentinel so the operator never sees a leaked value.
    assert hook["body_status_code"] == "unresolved_pending_outline_contract"


@pytest.mark.parametrize(
    "platform",
    ["vendor-platform", "model_id-platform", "Provider-channel", "ENGINE-x"],
)
def test_forbidden_token_scrub_drops_vendor_strings_in_target_platform(
    platform: str,
) -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(target_platform=platform)),
        _variation_surface(),
        _ms_panel(),
    )
    cta = out["variant_candidates"][0]["readable_sections"][2]
    assert cta["body_status_code"] == "unresolved_pending_outline_contract"


def test_no_vendor_or_model_strings_in_payload() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    blob = repr(out).lower()
    for forbidden in ("vendor", "model_id", "provider", "engine", "swiftcraft"):
        assert forbidden not in blob


# ---------------------------------------------------------------------------
# Localization tables — closed enum coverage
# ---------------------------------------------------------------------------


def test_tone_labels_cover_every_phase_b_value() -> None:
    from gateway.app.services.matrix_script.phase_b_authoring import TONES

    for tone in TONES:
        assert tone in TONE_LABELS_ZH


def test_audience_labels_cover_every_phase_b_value() -> None:
    from gateway.app.services.matrix_script.phase_b_authoring import AUDIENCES

    for audience in AUDIENCES:
        assert audience in AUDIENCE_LABELS_ZH


# ---------------------------------------------------------------------------
# Robustness — defensive degradation
# ---------------------------------------------------------------------------


def test_returns_empty_panel_payload_with_no_variation_surface() -> None:
    out = derive_matrix_script_readable_variants(_task(), None, _ms_panel())
    assert out["is_matrix_script"] is True
    assert out["variant_candidates"] == []
    assert out["variant_count"] == 0


def test_skips_non_mapping_cell_entries() -> None:
    out = derive_matrix_script_readable_variants(
        _task(),
        {
            "variation_plan": {
                "cells": [
                    None,
                    "junk",
                    {"cell_id": "cell_a", "axis_selections": {"tone": "casual"}},
                ]
            },
            "copy_bundle": {"slots": []},
        },
        _ms_panel(),
    )
    ids = [v["variation_id"] for v in out["variant_candidates"]]
    assert ids == ["cell_a"]


def test_skips_cells_without_id() -> None:
    out = derive_matrix_script_readable_variants(
        _task(),
        {
            "variation_plan": {
                "cells": [
                    {"cell_id": "", "axis_selections": {}},
                    {"cell_id": "cell_b", "axis_selections": {"tone": "playful"}},
                ]
            },
            "copy_bundle": {"slots": []},
        },
        _ms_panel(),
    )
    ids = [v["variation_id"] for v in out["variant_candidates"]]
    assert ids == ["cell_b"]


def test_unknown_axis_value_renders_raw_string_via_summary() -> None:
    cells = [
        {
            "cell_id": "cell_001",
            "axis_selections": {"tone": "future_unknown", "audience": "b2c", "length": 45},
            "script_slot_ref": "slot_001",
        }
    ]
    slots = [{"slot_id": "slot_001", "body_ref": "content://x", "length_hint": 45}]
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(cells=cells, slots=slots), _ms_panel()
    )
    summary = out["variant_candidates"][0]["axis_summary_zh"]
    # Unknown enum value falls through verbatim — never raises and never
    # synthesises a translation.
    assert "future_unknown" in summary


def test_consumes_variation_surface_verbatim_no_re_derivation() -> None:
    cells = [
        {
            "cell_id": "cell_zzz",
            "axis_selections": {"tone": "formal", "audience": "b2b", "length": 90},
            "script_slot_ref": "slot_z",
        }
    ]
    slots = [{"slot_id": "slot_z", "body_ref": "content://opaque", "length_hint": 90}]
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(cells=cells, slots=slots), _ms_panel()
    )
    variant = out["variant_candidates"][0]
    # Operator-visible identity is the variation_id only; the slot id
    # and body_ref are internal handles and must not appear in the
    # output payload.
    assert variant["variation_id"] == "cell_zzz"
    assert variant["axis_selections"] == {"tone": "formal", "audience": "b2b", "length": 90}
    assert variant["has_bound_slot"] is True
    # Defensive: `slot_z` and `content://opaque` MUST NOT leak.
    assert "slot_z" not in repr(variant)
    assert "content://" not in repr(variant)


def test_helper_does_not_call_publish_readiness() -> None:
    # The function signature has no publish_readiness parameter — this
    # is the structural assertion that we cannot accidentally produce a
    # second truth source for publishability or recommended-version
    # reasoning.
    import inspect

    sig = inspect.signature(derive_matrix_script_readable_variants)
    assert "publish_readiness" not in sig.parameters


def test_helper_does_not_call_compute_publish_readiness() -> None:
    import gateway.app.services.matrix_script.readable_variant_view as mod

    src = open(mod.__file__).read()
    assert "compute_publish_readiness" not in src


def test_helper_signature_only_takes_documented_inputs() -> None:
    import inspect

    sig = inspect.signature(derive_matrix_script_readable_variants)
    assert set(sig.parameters.keys()) == {
        "task",
        "variation_surface",
        "line_specific_panel",
        "preview_compare",
    }


# ---------------------------------------------------------------------------
# Conditional-pass corrections — three-state operator distinction +
# raw-handle non-leakage (this PR's blockers)
# ---------------------------------------------------------------------------


def test_three_state_distinction_in_per_variation_sections() -> None:
    """The operator must be able to distinguish three states per
    section: readable / structural placeholder / unresolved.
    """
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    variant = out["variant_candidates"][0]
    sections_by_id = {s["section_id"]: s for s in variant["readable_sections"]}
    # Hook resolves from entry truth → readable.
    assert sections_by_id["hook"]["body_status_code"] == "resolved_from_source_content"
    # Body never has actual readable text in this wave → structural-only.
    assert sections_by_id["body"]["body_status_code"] == STATUS_STRUCTURAL_ONLY
    # CTA resolves from entry.target_platform → readable.
    assert sections_by_id["cta"]["body_status_code"] == "resolved_from_source_content"


def test_three_state_distinction_when_topic_and_platform_missing() -> None:
    out = derive_matrix_script_readable_variants(
        _task(entry=_entry(topic="", target_platform="")),
        _variation_surface(),
        _ms_panel(),
    )
    variant = out["variant_candidates"][0]
    sections_by_id = {s["section_id"]: s for s in variant["readable_sections"]}
    # Hook + CTA fall back to unresolved tracked-gap sentinel.
    assert sections_by_id["hook"]["body_status_code"] == "unresolved_pending_outline_contract"
    assert sections_by_id["cta"]["body_status_code"] == "unresolved_pending_outline_contract"
    # Body retains its structural-only framing because length / tone /
    # bound-slot are still present.
    assert sections_by_id["body"]["body_status_code"] == STATUS_STRUCTURAL_ONLY


def test_body_unresolved_when_no_structural_signals() -> None:
    cells = [{"cell_id": "cell_x", "axis_selections": {}, "script_slot_ref": ""}]
    out = derive_matrix_script_readable_variants(
        _task(),
        _variation_surface(cells=cells, slots=[]),
        _ms_panel(),
    )
    variant = out["variant_candidates"][0]
    body = variant["readable_sections"][1]
    assert body["body_status_code"] == "unresolved_pending_outline_contract"


def test_structural_only_status_label_is_honest_about_opaque_handle() -> None:
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    body = out["variant_candidates"][0]["readable_sections"][1]
    label = body["body_status_label_zh"]
    # Honest framing: structural placeholder, opaque handle, future
    # resolution gated on Outline Contract.
    assert "结构性占位" in label
    assert "opaque" in label
    assert "Outline Contract" in label


def test_no_raw_slot_or_body_ref_anywhere_in_payload() -> None:
    """Top-level structural assertion: scan the entire payload repr for
    forbidden internal-handle substrings.
    """
    out = derive_matrix_script_readable_variants(
        _task(), _variation_surface(), _ms_panel()
    )
    blob = repr(out)
    # No raw slot ids that came from the variation surface fixture.
    assert "slot_001" not in blob
    assert "slot_002" not in blob
    # No `content://` scheme strings.
    assert "content://" not in blob
    # No removed-field key names in payload.
    assert "script_slot_ref" not in blob
    assert "slot_body_ref" not in blob


def test_template_does_not_render_raw_handles() -> None:
    """Template-level no-leakage: scan the rendered Jinja template
    source for the removed handle-rendering directives.
    """
    template_path = (
        "gateway/app/templates/task_workbench.html"
    )
    with open(template_path) as fh:
        template = fh.read()
    # Find the readable-variants panel block by its data-role anchor.
    start = template.index("matrix-script-readable-variants-panel")
    # Bound the search to a generous window covering the panel + its
    # successor (`matrix-script-review-zone-panel`).
    end = template.index("matrix-script-review-zone-panel", start)
    panel = template[start:end]
    # Forbidden rendering directives (the prior CONDITIONAL-PASS
    # leakage points).
    assert "variant.script_slot_ref" not in panel
    assert "variant.slot_body_ref" not in panel
    assert "script_slot_ref：" not in panel
    assert "body_ref：" not in panel
    # The replacement operator-language anchors must be present.
    assert "ms-readable-variant-slot-bound" in panel
    assert "bound_slot_label_zh" in panel
    assert "slot_body_opacity_note_zh" in panel


def test_template_renders_three_section_states_distinctly() -> None:
    """The operator-visible HTML must render readable / structural /
    unresolved with distinct anchors so the operator (and a reviewer
    walking the surface) can tell them apart.
    """
    template_path = "gateway/app/templates/task_workbench.html"
    with open(template_path) as fh:
        template = fh.read()
    start = template.index("matrix-script-readable-variants-panel")
    end = template.index("matrix-script-review-zone-panel", start)
    panel = template[start:end]
    # Three distinct render branches with three distinct data-role anchors.
    assert "ms-readable-variant-section-readable" in panel
    assert "ms-readable-variant-section-structural" in panel
    assert "ms-readable-variant-section-unresolved" in panel
    assert "ms-readable-shared-section-readable" in panel
    assert "ms-readable-shared-section-structural" in panel
    assert "ms-readable-shared-section-unresolved" in panel
