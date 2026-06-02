"""PR-A · Matrix Script Workbench product-flow cleanup template tests.

Authority: ``docs/design/matrix_script_workbench_product_flow_reset_v1.md``
§4 (target Workbench IA), §5 (forbidden primary UI vocabulary), §8 PR-A
(scope + ≥30 test requirement), §9 (acceptance criteria).

The PR-A reset is *subtractive*: it retires the legacy A/B/C/D/E/F
operator-visible blocks from the Workbench primary scan and reduces the
operator-visible content to exactly five sections — four primary
(主视频结果 / 生产流程可观测 / 可选变体 / 交付入口) + one collapsed
diagnostic fold (技术诊断). The retired legacy blocks survive only inside
the diagnostic fold for back-compat with prior structural tests; they
must NOT render as visible primary operator content.

This suite asserts the source-level shape of that reset: the four
primary sections are present at the matrix_script branch, their order
matches the design, the diagnostic fold is collapsed by default, the
legacy blocks A–F live INSIDE the fold (not above it), and the §5
forbidden-vocabulary list does not appear in the primary slice of the
template (Sections 1–4 — i.e. anywhere between the matrix_script gate
and the Section 5 fold opening).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


@pytest.fixture(scope="module")
def source() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(source: str) -> str:
    """The complete matrix_script branch (gate → closing endif)."""
    start = source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    assert start != -1
    # Find the closing {% endif %} that pairs with the matrix_script gate.
    end_marker = (
        '</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}'
    )
    end = source.find(end_marker, start)
    assert end != -1, "PR-A Section 5 fold close not found"
    return source[start:end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    """The primary operator slice — everything from the matrix_script gate
    up to (but NOT including) the Section 5 fold opening.
    Sections 1–4 must live here; nothing from the §5 forbidden list may."""
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    assert fold_open != -1, "Section 5 fold marker missing"
    return matrix_branch[:fold_open]


def _strip_non_rendered(text: str) -> str:
    """Strip everything that would not reach the operator's browser as
    visible text — Jinja comments `{# … #}`, HTML comments `<!-- … -->`,
    Jinja statement blocks `{% … %}` (control flow, no output), and the
    contents of Jinja expressions `{{ … }}` (variable names like
    `ms_publish_readiness` are not operator-visible; their VALUES are).

    What remains is the static HTML scaffolding + the empty `{{}}` slots
    where helper values flow in. Forbidden-vocabulary checks against
    that slice catch literal operator-visible copy without false
    positives on Jinja machinery."""

    no_jinja_comment = re.sub(r"{#.*?#}", "", text, flags=re.DOTALL)
    no_html_comment = re.sub(r"<!--.*?-->", "", no_jinja_comment, flags=re.DOTALL)
    no_jinja_stmt = re.sub(r"{%.*?%}", "", no_html_comment, flags=re.DOTALL)
    no_jinja_expr = re.sub(r"{{.*?}}", "{{}}", no_jinja_stmt, flags=re.DOTALL)
    return no_jinja_expr


@pytest.fixture(scope="module")
def primary_slice_no_comments(primary_slice: str) -> str:
    return _strip_non_rendered(primary_slice)


@pytest.fixture(scope="module")
def section5_slice(matrix_branch: str) -> str:
    """The Section 5 (技术诊断) slice — everything from the Section 5 fold
    opening to the end of the matrix_script branch."""
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    return matrix_branch[fold_open:]


# --------------------------------------------------------------------------
# §9.1 / §9.3 — four primary sections present, ordering, Section 5 below
# --------------------------------------------------------------------------


def test_section1_main_video_result_present(primary_slice: str) -> None:
    assert 'data-role="matrix-script-main-video-result"' in primary_slice


def test_section2_production_flow_stepper_present(matrix_branch: str) -> None:
    """Phase 2B fidelity fix (2026-05-30): the PR-A production-flow
    stepper was relocated from the operator primary scan into the §J
    technical-diagnostics fold (architect view). The anchor remains in
    the matrix_script gate for back-compat with downstream structural
    tests; it just no longer competes with the new script-to-video IA
    for first-screen attention."""

    assert 'data-role="matrix-script-production-flow-stepper"' in matrix_branch


def test_section3_optional_variants_present(primary_slice: str) -> None:
    assert 'data-role="matrix-script-section-optional-variants"' in primary_slice


def test_section4_delivery_entry_present(primary_slice: str) -> None:
    assert 'data-role="matrix-script-section-delivery-entry"' in primary_slice


def test_section5_diagnostics_fold_present(matrix_branch: str) -> None:
    assert 'data-role="op-console-ms-technical-diagnostics-fold"' in matrix_branch


def test_primary_sections_in_design_order(primary_slice: str) -> None:
    """Phase 2B fidelity fix (2026-05-30) ordering: §A 主视频结果 → §G
    视频变体 (= legacy matrix-script-section-optional-variants anchor) →
    §I 交付入口. The PR-A standalone production-flow-stepper has been
    relocated into §J (architect view); ordering is now A → G → I."""

    pos1 = primary_slice.find('data-role="matrix-script-main-video-result"')
    pos3 = primary_slice.find('data-role="matrix-script-section-optional-variants"')
    pos4 = primary_slice.find('data-role="matrix-script-section-delivery-entry"')
    assert -1 < pos1 < pos3 < pos4


def test_section5_fold_after_all_primary_sections(matrix_branch: str) -> None:
    pos4 = matrix_branch.find('data-role="matrix-script-section-delivery-entry"')
    pos5 = matrix_branch.find('data-role="op-console-ms-technical-diagnostics-fold"')
    assert -1 < pos4 < pos5


# --------------------------------------------------------------------------
# §9.1 — Section 1 dominance: 主视频结果 is the first content card
# --------------------------------------------------------------------------


def test_section1_is_first_op_card_in_branch(primary_slice: str) -> None:
    """The first op-card / data-role anchor encountered after the
    matrix_script gate is the main-video-result anchor (Section 1)."""

    first_anchor = re.search(r'data-role="matrix-script-[a-z0-9\-]+"', primary_slice)
    assert first_anchor is not None
    assert first_anchor.group(0) == 'data-role="matrix-script-main-video-result"'


def test_section1_carries_state_pill(primary_slice: str) -> None:
    assert 'data-role="ms-main-video-result-state-pill"' in primary_slice


def test_section1_uses_preview_action_model(primary_slice: str) -> None:
    assert 'data-role="ms-main-video-result-actions"' not in primary_slice
    assert 'data-role="ms-acc-generate"' in primary_slice
    assert 'data-role="legacy-main-video-compat-anchor"' in primary_slice
    assert 'inert' in primary_slice


def test_section1_empty_state_copy_present_in_helper_contract(
    primary_slice: str,
) -> None:
    """The operator-first empty state is a direct single-action instruction,
    not the old helper's task-status blocker copy."""

    assert "请先确认素材与配乐，然后生成视频预览" in primary_slice
    assert "ms_main_video_result.preview.empty_state_message_zh" not in primary_slice


# --------------------------------------------------------------------------
# §4 Section 2 — inline-expandable stepper with three step details
# --------------------------------------------------------------------------


def test_stepper_has_three_inline_details(matrix_branch: str) -> None:
    """Phase 2B fidelity fix: the PR-A stepper now lives inside §J fold,
    so its three inline details are part of the matrix_script gate but
    not the operator primary scan."""

    occurrences = matrix_branch.count('data-role="ms-production-flow-step-detail"')
    assert occurrences == 3


def test_stepper_step_ids_match_design_order(matrix_branch: str) -> None:
    """Step-id ordering preserved inside the §J fold."""

    pos_script = matrix_branch.find('data-step-id="script_structure"')
    pos_variant = matrix_branch.find('data-step-id="variant_selection"')
    pos_generation = matrix_branch.find('data-step-id="generation"')
    assert -1 < pos_script < pos_variant < pos_generation


def test_step1_detail_renders_hook_body_cta_sections(matrix_branch: str) -> None:
    assert 'data-role="ms-step1-detail-section"' in matrix_branch
    assert 'data-role="ms-step1-detail-section-body"' in matrix_branch


def test_step2_detail_carries_main_version_and_count(matrix_branch: str) -> None:
    assert 'data-role="ms-step2-detail-main-version"' in matrix_branch
    assert 'data-role="ms-step2-detail-variant-count"' in matrix_branch
    assert 'data-role="ms-step2-detail-differentiator-dimensions"' in matrix_branch


def test_step2_detail_uses_operator_language_axes(matrix_branch: str) -> None:
    """The five differentiator dimensions are operator-language only:
    语气 / 时长 / 受众 / 开头方式 / 画面方向. NO raw axis tuples."""

    assert "语气 / 时长 / 受众 / 开头方式 / 画面方向" in matrix_branch


def test_step3_detail_mirrors_section1_pill_text(matrix_branch: str) -> None:
    assert 'data-role="ms-step3-detail-state"' in matrix_branch
    assert 'data-role="ms-step3-detail-blocker"' in matrix_branch
    assert 'data-role="ms-step3-detail-next-action"' in matrix_branch


# --------------------------------------------------------------------------
# §4 Section 3 — compact optional variants; empty-state ONE message
# --------------------------------------------------------------------------


def test_section3_empty_state_uses_design_verbatim_copy(primary_slice: str) -> None:
    """Design §4 Section 3 verbatim empty-state copy."""

    assert "暂未生成变体视频" in primary_slice
    assert "你可以先完成主预览，或选择同时准备多个变体。" in primary_slice


def test_section3_has_add_and_batch_actions(primary_slice: str) -> None:
    assert 'data-role="ms-section-optional-variants-action-add"' in primary_slice
    assert 'data-role="ms-section-optional-variants-action-batch"' in primary_slice


def test_section3_others_fold_collapsed_by_default(primary_slice: str) -> None:
    """The "其他变体" list lives inside a <details> that is collapsed by
    default (no `open` attribute)."""

    others_marker = 'data-role="ms-section-optional-variants-others-fold"'
    pos = primary_slice.find(others_marker)
    assert pos != -1
    # Find the <details that owns this marker (look back from `pos`).
    details_open = primary_slice.rfind("<details", 0, pos)
    assert details_open != -1
    # The `open` attribute would appear between <details and the marker.
    details_tag = primary_slice[details_open:pos]
    assert " open" not in details_tag


def test_section3_does_not_render_four_empty_candidate_cards(
    primary_slice: str,
) -> None:
    """Design §4 Section 3: "Do not render four empty candidate cards."
    The new section uses a single empty-state message OR a compact
    main + others-fold layout; no per-card candidate panels render
    inside the new section data-role."""

    s3_open = primary_slice.find('data-role="matrix-script-section-optional-variants"')
    assert s3_open != -1
    s3_close = primary_slice.find("</div>\n        </div>\n      {% endif %}", s3_open)
    # Section 3 must not contain a `ms-block-e-candidate-card` row.
    s3_body = primary_slice[s3_open : s3_close if s3_close > 0 else len(primary_slice)]
    assert "ms-block-e-candidate-card" not in s3_body


def test_section3_does_not_render_large_variant_table(primary_slice: str) -> None:
    """Design §4 Section 3: "Do not render large backend-like variation
    tables." The new Section 3 has no <table>; the legacy Block C table
    lives in Section 5 only."""

    s3_open = primary_slice.find('data-role="matrix-script-section-optional-variants"')
    s3_close = primary_slice.find("</div>\n        </div>\n      {% endif %}", s3_open)
    s3_body = primary_slice[s3_open : s3_close if s3_close > 0 else len(primary_slice)]
    assert "<table" not in s3_body


# --------------------------------------------------------------------------
# §4 Section 4 — lightweight delivery entry, no deliverable rows / forms
# --------------------------------------------------------------------------


def test_section4_has_two_lines_and_cta(primary_slice: str) -> None:
    assert 'data-role="ms-section-delivery-entry-line1"' in primary_slice
    assert 'data-role="ms-section-delivery-entry-line2"' in primary_slice
    assert 'data-role="ms-section-delivery-entry-cta"' in primary_slice


def test_section4_default_copy_when_not_publishable(primary_slice: str) -> None:
    """Design §4 Section 4 default (not publishable) copy verbatim."""

    assert "当前不能交付：尚未完成主预览。" in primary_slice
    assert (
        "预览完成后，可进入交付检查查看成片、字幕、音频、文案包与发布设置。"
        in primary_slice
    )


def test_section4_publishable_branch_copy_present(primary_slice: str) -> None:
    """Design §4 Section 4 publishable copy verbatim."""

    assert "可交付 · 已确认主版本。" in primary_slice
    assert "进入交付检查填写发布设置或回填发布状态。" in primary_slice


def test_section4_contains_no_deliverable_rows(primary_slice: str) -> None:
    """Section 4 MUST NOT render per-row deliverable detail. Those live in
    Delivery Center only."""

    s4_open = primary_slice.find('data-role="matrix-script-section-delivery-entry"')
    assert s4_open != -1
    # The block ends at the next "</div>\n      {% endif %}" closure or the fold open.
    fold_open = primary_slice.find(
        'data-role="op-console-ms-technical-diagnostics-fold"', s4_open
    )
    end = fold_open if fold_open != -1 else len(primary_slice)
    s4_body = primary_slice[s4_open:end]
    for forbidden in (
        "ms-block-f-required-row",
        "ms-block-f-optional-row",
        "publish-feedback",
        "操作记录",
        "<form",
        "<table",
    ):
        assert forbidden not in s4_body, (
            f"Section 4 must not contain '{forbidden}'"
        )


def test_section4_cta_points_to_delivery_center(primary_slice: str) -> None:
    assert "/tasks/{{ task.task_id }}/publish" in primary_slice


# --------------------------------------------------------------------------
# §9.7 — backend vocabulary quarantine: §5 forbidden list NOT in primary
# --------------------------------------------------------------------------


FORBIDDEN_TOKENS_PRIMARY = [
    "source_script_ref",
    "content://",
    "publish_readiness",
    "head_reason",
    "artifact_lookup",
    "RC-R8",
    "slot_pack",
    "provenance",
    "variation_axis",
    "audience=[b2b",
    "tone=[casual",
    "length=[30",
]


@pytest.mark.parametrize("token", FORBIDDEN_TOKENS_PRIMARY)
def test_forbidden_token_not_in_primary_slice(
    primary_slice_no_comments: str, token: str
) -> None:
    """§5 forbidden primary-UI vocabulary must NOT appear in Sections 1–4.
    Comments are stripped first — design §5 explicitly permits the tokens
    inside HTML / Jinja comments since they never reach the operator."""

    assert token not in primary_slice_no_comments, (
        f"Forbidden token leaked into primary slice: {token!r}"
    )


def test_no_provider_model_vendor_engine_selector_in_primary(
    primary_slice_no_comments: str,
) -> None:
    """Validator R3 red line: no provider/model/vendor/engine selector
    control. Pattern checks the four nouns as standalone words in the
    primary slice (case-insensitive, comments stripped)."""

    for noun in ("provider", "model", "vendor", "engine"):
        matches = re.findall(
            rf"\b{noun}\b", primary_slice_no_comments, flags=re.IGNORECASE
        )
        assert not matches, (
            f"Validator R3 violation: '{noun}' appears in primary slice"
        )


def test_task_id_not_a_heading_in_primary(primary_slice: str) -> None:
    """§5 forbids 任务 ID as a heading-tier element in primary view."""

    for marker in (
        "<h1>任务 ID",
        "<h2>任务 ID",
        '<h2 class="op-section-title">任务 ID',
    ):
        assert marker not in primary_slice


# --------------------------------------------------------------------------
# §9.9 — no fake media output anywhere in the primary slice
# --------------------------------------------------------------------------


def test_no_fake_video_url_in_primary(primary_slice: str) -> None:
    """No fabricated mp4 / m3u8 / publish URL in the primary slice. The
    Section 1 preview hero either binds a real artifact (via helper
    bound_variation_id) or renders the honest empty-state copy."""

    for fake in (".mp4", ".m3u8", "youtu.be/", "tiktok.com/", "douyin.com/"):
        assert fake not in primary_slice


def test_no_placeholder_video_player_in_primary(primary_slice: str) -> None:
    """The primary slice may only contain the real PR-A preview player."""

    assert '<video controls preload="metadata" src="{{ ms_overlay_mr.preview_url }}"' in primary_slice
    for tag in ("<source ", "<iframe"):
        assert tag not in primary_slice


def test_no_raw_final_video_field_in_primary(
    primary_slice_no_comments: str,
) -> None:
    """The raw `final_video` field name must not appear in Sections 1–4
    (it survives only in helper-internal data-attrs and Section 5
    notes). Comments are stripped — the primary slice's operator-
    visible copy uses '主视频' / '成片' instead."""

    assert "final_video" not in primary_slice_no_comments


# --------------------------------------------------------------------------
# §9.3 — legacy A/B/C/D/E/F headings not in primary view; inside Section 5
# --------------------------------------------------------------------------


LEGACY_BLOCK_MARKERS = [
    "matrix-script-block-a-goal-summary",
    "matrix-script-block-b-script-structure",
    "matrix-script-block-c-variant-strategy",
    "matrix-script-block-d-generate-regenerate",
    "matrix-script-block-e-candidate-review",
    "matrix-script-block-f-delivery-teaser",
]


@pytest.mark.parametrize("marker", LEGACY_BLOCK_MARKERS)
def test_legacy_block_marker_inside_section5_only(
    primary_slice: str, section5_slice: str, marker: str
) -> None:
    """Each legacy A–F op-card marker survives ONLY inside the Section 5
    diagnostics fold — never in the primary scan."""

    assert marker not in primary_slice, (
        f"Legacy block leaked into primary slice: {marker}"
    )
    assert marker in section5_slice, (
        f"Legacy block missing from Section 5 fold (back-compat broken): {marker}"
    )


def test_legacy_block_a_visible_title_not_in_primary(primary_slice: str) -> None:
    """The legacy "任务摘要" heading must not appear as a primary heading."""

    assert (
        '<h2 class="op-section-title" data-role="ms-block-a-title">任务摘要</h2>'
        not in primary_slice
    )


def test_legacy_block_b_visible_title_not_in_primary(primary_slice: str) -> None:
    """The legacy standalone Block B title is not a primary heading. The
    primary slice's only "脚本结构" reference is the stepper step label."""

    assert (
        '<h2 class="op-section-title" data-role="ms-block-b-title">脚本结构</h2>'
        not in primary_slice
    )


def test_legacy_block_c_visible_title_not_in_primary(primary_slice: str) -> None:
    assert (
        '<h2 class="op-section-title" data-role="ms-block-c-title">变体方案</h2>'
        not in primary_slice
    )


def test_legacy_block_d_visible_title_not_in_primary(primary_slice: str) -> None:
    assert (
        '<h2 class="op-section-title" data-role="ms-block-d-title">生成进度</h2>'
        not in primary_slice
    )


def test_legacy_block_f_visible_title_not_in_primary(primary_slice: str) -> None:
    assert (
        '<h2 class="op-section-title" data-role="ms-block-f-title">交付摘要</h2>'
        not in primary_slice
    )


# --------------------------------------------------------------------------
# §9.8 — Section 5 fold collapsed by default
# --------------------------------------------------------------------------


def test_section5_details_collapsed_by_default(matrix_branch: str) -> None:
    """The Section 5 <details> opens WITHOUT an `open` attribute, so it
    is collapsed by default on the operator's first scan."""

    fold_open = matrix_branch.find(
        '<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    head_end = matrix_branch.find(">", fold_open)
    details_tag = matrix_branch[fold_open : head_end + 1]
    assert " open" not in details_tag


# --------------------------------------------------------------------------
# §9.11 — operator can answer the 5 anchor questions from Section 1 + 2
# --------------------------------------------------------------------------


def test_anchor_questions_answered_in_section1_and_section2(
    primary_slice: str,
) -> None:
    """Q1 main video identity → Section 1 title + subtitle.
    Q2 generated? → Section 1 state pill (mirrored in step 3 detail).
    Q3 generated? → Section 1 acceptance status + generate preview action.
    Q4 next action? → Section 1 preview action.
    Q5 delivery? → Section 4 CTA."""

    for marker in (
        'data-role="ms-main-video-result-title"',
        'data-role="ms-main-video-result-subtitle"',
        'data-role="ms-main-video-result-state-pill"',
        'data-role="ms-main-video-result-acceptance"',
        'data-role="ms-acc-generate"',
        'data-role="ms-section-delivery-entry-cta"',
    ):
        assert marker in primary_slice


# --------------------------------------------------------------------------
# §9.12 — per-section data-role anchor presence in matrix_script branch
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "anchor",
    [
        "matrix-script-main-video-result",
        "matrix-script-production-flow-stepper",
        "matrix-script-section-optional-variants",
        "matrix-script-section-delivery-entry",
        "op-console-ms-technical-diagnostics-fold",
    ],
)
def test_each_section_has_data_role_anchor(matrix_branch: str, anchor: str) -> None:
    assert f'data-role="{anchor}"' in matrix_branch


# --------------------------------------------------------------------------
# Hot Follow / Digital Anchor byte-isolation
# --------------------------------------------------------------------------


def test_pra_changes_scoped_to_matrix_script_branch(source: str) -> None:
    """The new PR-A sections only render inside the matrix_script
    panel_kind branch — Hot Follow / Digital Anchor surfaces are not
    touched."""

    for anchor in (
        "matrix-script-section-optional-variants",
        "matrix-script-section-delivery-entry",
        "op-console-ms-technical-diagnostics-fold",
    ):
        # The anchor appears in source exactly once, inside the matrix_script branch.
        positions = [m.start() for m in re.finditer(re.escape(anchor), source)]
        assert positions, f"{anchor} missing from template"
        gate = source.find('ops_workbench_panel.panel_kind == "matrix_script"')
        da_gate = source.find('ops_workbench_panel.panel_kind == "digital_anchor"')
        assert gate != -1 and da_gate != -1
        for pos in positions:
            assert pos > gate, f"{anchor} found OUTSIDE matrix_script gate"
            assert pos < da_gate, f"{anchor} found in/after digital_anchor branch"
