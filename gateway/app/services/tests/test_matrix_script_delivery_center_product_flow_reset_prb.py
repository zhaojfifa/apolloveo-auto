"""PR-B · Matrix Script Delivery Center product-flow cleanup template tests.

Authority: ``docs/design/matrix_script_workbench_product_flow_reset_v1.md``
§6 (Delivery Center reset), §8 PR-B scope; user mission `[SYSTEM
OVERRIDE]` 2026-05-29 Delivery Center implementer brief (six-section
IA + strict boundaries).

The PR-B reset is *subtractive*: it reframes the Matrix Script Delivery
Center as a result + publish surface. The operator-visible primary scan
is exactly six sections:

  1. 交付结果介绍
  2. 主视频
  3. 必需交付物 (字幕 / 音频 / 文案包 / manifest / 交付包)
  4. 可选交付物 (其他变体 / scene pack / supporting material)
  5. 发布设置 (platform / account / title / copy / hashtags / scheduled time)
  6. 发布回填 (publish URL / publish status / operator note / metrics)

A seventh collapsed `<details>` (技术诊断) holds the retired PR-3 / PR-4
Block A–F op-cards + the Recovery PR-3 closure block + the pre-existing
JS-hydrated diagnostic shells, preserving their data-role markers for
back-compat with prior wave tests. The primary scan must NOT contain
generation controls, production-flow panels, raw event_kind / closure /
publish_readiness / artifact_lookup / final_video, or fake URLs.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


@pytest.fixture(scope="module")
def source() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(source: str) -> str:
    """The complete matrix_script branch (gate → closing endif)."""

    start = source.find('{% if _ms_kind == "matrix_script" %}')
    assert start != -1
    end_marker = (
        '</details> {# /op-console-ms-dc-technical-diagnostics-fold '
        '(PR-B Section 7) #}'
    )
    end = source.find(end_marker, start)
    assert end != -1, "PR-B Section 7 fold close not found"
    return source[start : end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    """Everything from the matrix_script gate up to (but NOT including) the
    PR-B Section 7 fold opening. Sections 1–6 live here; the legacy
    diagnostic content lives BELOW (inside the fold) and must not leak
    into the primary scan."""

    fold_open = matrix_branch.find(
        'data-role="op-console-ms-dc-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    return matrix_branch[:fold_open]


@pytest.fixture(scope="module")
def diagnostics_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-dc-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    return matrix_branch[fold_open:]


def _strip_non_rendered(text: str) -> str:
    """Strip Jinja comments / HTML comments / Jinja statement blocks /
    Jinja expression contents — leaves only the static HTML scaffolding
    + empty `{{}}` slots. Used for forbidden-vocabulary checks against
    operator-visible primary copy."""

    no_jinja_comment = re.sub(r"{#.*?#}", "", text, flags=re.DOTALL)
    no_html_comment = re.sub(r"<!--.*?-->", "", no_jinja_comment, flags=re.DOTALL)
    no_jinja_stmt = re.sub(r"{%.*?%}", "", no_html_comment, flags=re.DOTALL)
    no_jinja_expr = re.sub(r"{{.*?}}", "{{}}", no_jinja_stmt, flags=re.DOTALL)
    return no_jinja_expr


@pytest.fixture(scope="module")
def primary_visible(primary_slice: str) -> str:
    return _strip_non_rendered(primary_slice)


# --------------------------------------------------------------------------
# Six sections present + ordered per design
# --------------------------------------------------------------------------


SECTION_ANCHORS = [
    "matrix-script-dc-section-intro",
    "matrix-script-dc-section-main-video",
    "matrix-script-dc-section-required-deliverables",
    "matrix-script-dc-section-optional-deliverables",
    "matrix-script-dc-section-publish-settings",
    "matrix-script-dc-section-publish-backfill",
]


@pytest.mark.parametrize("anchor", SECTION_ANCHORS)
def test_section_anchor_present_in_primary(primary_slice: str, anchor: str) -> None:
    assert f'data-role="{anchor}"' in primary_slice


def test_sections_in_design_order(primary_slice: str) -> None:
    positions = [
        primary_slice.find(f'data-role="{anchor}"') for anchor in SECTION_ANCHORS
    ]
    assert all(p != -1 for p in positions)
    assert positions == sorted(positions)


def test_technical_diagnostics_fold_after_section_6(matrix_branch: str) -> None:
    pos_s6 = matrix_branch.find(
        'data-role="matrix-script-dc-section-publish-backfill"'
    )
    pos_fold = matrix_branch.find(
        'data-role="op-console-ms-dc-technical-diagnostics-fold"'
    )
    assert -1 < pos_s6 < pos_fold


def test_technical_diagnostics_fold_collapsed_by_default(
    matrix_branch: str,
) -> None:
    fold_open = matrix_branch.find(
        '<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold"'
    )
    assert fold_open != -1
    tag_end = matrix_branch.find(">", fold_open)
    assert " open" not in matrix_branch[fold_open : tag_end + 1]


# --------------------------------------------------------------------------
# Section 1 · 交付结果介绍 — operator-language paragraph
# --------------------------------------------------------------------------


def test_section1_has_paragraph_and_pill(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-intro-title"' in primary_slice
    assert 'data-role="ms-dc-section-intro-paragraph"' in primary_slice
    assert 'data-role="ms-dc-section-intro-result-pill"' in primary_slice


def test_section1_paragraph_uses_operator_language(primary_slice: str) -> None:
    assert "本任务当前可交付" in primary_slice
    assert "本任务当前不能交付" in primary_slice


def test_section1_is_first_dc_section(primary_slice: str) -> None:
    """The first `matrix-script-dc-section-*` op-card in the primary
    slice is the intro section."""

    first = re.search(r'data-role="matrix-script-dc-section-[a-z\-]+"', primary_slice)
    assert first is not None
    assert first.group(0) == 'data-role="matrix-script-dc-section-intro"'


# --------------------------------------------------------------------------
# Section 2 · 主视频 — preview hero + honest empty state, no raw final_video
# --------------------------------------------------------------------------


def test_section2_preview_and_empty_state_present(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-main-video-preview"' in primary_slice
    assert 'data-role="ms-dc-section-main-video-preview-bound"' in primary_slice
    assert 'data-role="ms-dc-section-main-video-preview-empty"' in primary_slice


def test_section2_empty_state_copy_present(primary_slice: str) -> None:
    assert (
        "当前尚未生成主视频。已完成脚本结构与生成方案准备，"
        "成片生成能力接入后将在这里展示视频结果。"
        in primary_slice
    )


def test_section2_title_does_not_use_raw_final_video(
    primary_visible: str,
) -> None:
    """Section 2 heading reads '主视频', not '最终成片 · final_video'.
    The raw `final_video` field name lives only in Section 7 diagnostics."""

    s2_open = primary_visible.find('data-role="matrix-script-dc-section-main-video"')
    assert s2_open != -1
    s2_close = primary_visible.find(
        'data-role="matrix-script-dc-section-required-deliverables"', s2_open
    )
    s2_body = primary_visible[s2_open:s2_close]
    assert "final_video" not in s2_body
    assert "最终成片" not in s2_body


# --------------------------------------------------------------------------
# Section 3 · 必需交付物 — five fixed operator-language rows
# --------------------------------------------------------------------------


REQUIRED_KIND_LABELS = ["字幕", "音频", "文案包", "manifest", "交付包"]


def test_section3_lists_required_deliverables(primary_slice: str) -> None:
    """The five required-deliverable kinds are sourced from the template's
    `_prb_required_kinds_zh` dict literal; the dict iteration emits one
    row per kind via `data-deliverable-kind="{{ kind_key }}"`. The kind
    keys appear in the template as Jinja dict literal strings."""

    assert 'data-role="ms-dc-section-required-list"' in primary_slice
    for kind in ("subtitle", "dub", "copy_bundle", "manifest", "delivery_pack"):
        assert f'"{kind}"' in primary_slice, (
            f"Required deliverable kind {kind!r} missing from primary slice"
        )


@pytest.mark.parametrize("label", REQUIRED_KIND_LABELS)
def test_section3_required_label_uses_operator_language(
    primary_slice: str, label: str
) -> None:
    assert label in primary_slice


def test_section3_missing_row_links_back_to_workbench(primary_slice: str) -> None:
    """Per design §6 row 3: the CTA for missing required deliverables is
    'in Workbench 重新生成', linking BACK to the workbench rather than
    triggering generation here."""

    assert 'data-role="ms-dc-section-required-row-regenerate-cta"' in primary_slice
    assert "在 Workbench 重新生成" in primary_slice
    assert "/workbench" in primary_slice


# --------------------------------------------------------------------------
# Section 4 · 可选交付物 — 其他变体 / scene pack / supporting material
# --------------------------------------------------------------------------


def test_section4_has_three_sub_groups(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-optional-other-variants-fold"' in primary_slice
    assert 'data-role="ms-dc-section-optional-scene-pack"' in primary_slice
    assert 'data-role="ms-dc-section-optional-supporting-material"' in primary_slice


def test_section4_other_variants_collapsed_by_default(primary_slice: str) -> None:
    marker = 'data-role="ms-dc-section-optional-other-variants-fold"'
    pos = primary_slice.find(marker)
    details_open = primary_slice.rfind("<details", 0, pos)
    assert details_open != -1
    assert " open" not in primary_slice[details_open:pos]


def test_section4_scene_pack_label_is_operator_language(
    primary_visible: str,
) -> None:
    """Section 4 heading uses '场景包' (operator) rather than 'scene_pack'
    (engineering)."""

    s4_open = primary_visible.find(
        'data-role="matrix-script-dc-section-optional-deliverables"'
    )
    s4_close = primary_visible.find(
        'data-role="matrix-script-dc-section-publish-settings"', s4_open
    )
    s4_body = primary_visible[s4_open:s4_close]
    assert "场景包" in s4_body
    assert "scene_pack" not in s4_body


# --------------------------------------------------------------------------
# Section 5 · 发布设置 — form with six fields
# --------------------------------------------------------------------------


def test_section5_form_present(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-publish-settings-form"' in primary_slice


@pytest.mark.parametrize(
    "field_role",
    [
        "ms-dc-section-publish-settings-platform",
        "ms-dc-section-publish-settings-account",
        "ms-dc-section-publish-settings-title-input",
        "ms-dc-section-publish-settings-caption",
        "ms-dc-section-publish-settings-tags",
        "ms-dc-section-publish-settings-scheduled",
    ],
)
def test_section5_form_has_required_field(primary_slice: str, field_role: str) -> None:
    assert f'data-role="{field_role}"' in primary_slice


def test_section5_form_posts_to_existing_closure_endpoint(
    primary_slice: str,
) -> None:
    """No new endpoint. The form posts to the existing closure events
    endpoint."""

    assert (
        'action="/api/matrix-script/closures/{{ task.task_id }}/events"'
        in primary_slice
    )


def test_section5_form_carries_operator_publish_event_kind(
    primary_slice: str,
) -> None:
    """The form's event_kind is the closed-enum value `operator_publish`.
    This appears in a hidden form input (not as operator-visible text)."""

    s5_open = primary_slice.find(
        'data-role="matrix-script-dc-section-publish-settings"'
    )
    s5_close = primary_slice.find(
        'data-role="matrix-script-dc-section-publish-backfill"', s5_open
    )
    s5_body = primary_slice[s5_open:s5_close]
    assert 'name="event_kind" value="operator_publish"' in s5_body


def test_section5_has_honesty_note(primary_slice: str) -> None:
    assert "本表单不直接对外发布" in primary_slice


# --------------------------------------------------------------------------
# Section 6 · 发布回填 — operator-language rows, no raw event_kind values
# --------------------------------------------------------------------------


def test_section6_has_list_and_empty_state(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-publish-backfill-list"' in primary_slice
    assert 'data-role="ms-dc-section-publish-backfill-empty"' in primary_slice


def test_section6_row_carries_url_status_note_columns(primary_slice: str) -> None:
    for role in (
        "ms-dc-section-publish-backfill-row-url",
        "ms-dc-section-publish-backfill-row-status",
        "ms-dc-section-publish-backfill-row-note",
    ):
        assert f'data-role="{role}"' in primary_slice


def test_section6_metrics_placeholder_present(primary_slice: str) -> None:
    assert 'data-role="ms-dc-section-publish-backfill-metrics"' in primary_slice
    assert 'data-role="ms-dc-section-publish-backfill-metrics-placeholder"' in primary_slice


def test_section6_status_words_are_operator_language(
    primary_visible: str,
) -> None:
    """Section 6 status column uses operator-language words ('已发布' /
    '失败' / '已撤回' / '待发布'), not the raw closed-enum values
    ('published' / 'failed' / 'retracted' / 'pending') as visible text."""

    s6_open = primary_visible.find(
        'data-role="matrix-script-dc-section-publish-backfill"'
    )
    s6_body = primary_visible[s6_open:]
    for word in ("已发布", "失败", "已撤回", "待发布"):
        assert word in s6_body


# --------------------------------------------------------------------------
# Boundary: no generation controls in Delivery Center primary
# --------------------------------------------------------------------------


def test_no_generation_buttons_in_primary(primary_slice: str) -> None:
    """No generation-trigger <button>s appear in the primary slice. The
    only '生成' reference allowed is Section 3's '在 Workbench 重新
    生成' anchor (an <a>, not a <button>, that links BACK to the
    Workbench instead of triggering generation here)."""

    # Find every <button …>…</button> in the primary slice and assert
    # none of them carry a generation-trigger label.
    button_blocks = re.findall(
        r"<button[^>]*>(.*?)</button>", primary_slice, flags=re.DOTALL
    )
    for content in button_blocks:
        for forbidden in (
            "生成主视频",
            "立即生成",
            "触发生成",
            "重新生成此变体",
            "生成 ",
            "⚡ 生成",
        ):
            assert forbidden not in content, (
                f"Forbidden generation-trigger button found: {forbidden!r}"
            )


def test_no_production_flow_stepper_in_primary(primary_slice: str) -> None:
    """No production-flow stepper anchors live in Delivery Center
    primary. The 生产流程可观测 stepper is a Workbench surface only."""

    for forbidden in (
        "matrix-script-production-flow-stepper",
        "ms-production-flow-stepper",
        "matrix-script-block-d-generate-regenerate",
    ):
        assert forbidden not in primary_slice


def test_no_task_creation_controls_in_primary(primary_visible: str) -> None:
    for forbidden in ("新建任务", "创建任务", "+ 任务"):
        assert forbidden not in primary_visible


# --------------------------------------------------------------------------
# Forbidden backend vocabulary quarantine
# --------------------------------------------------------------------------


FORBIDDEN_TOKENS = [
    "publish_readiness",
    "head_reason",
    "artifact_lookup",
    "RC-R8",
    "final_video",  # raw field name
    "source_script_ref",
    "content://",
    "slot_pack",
    "provenance",
]


@pytest.mark.parametrize("token", FORBIDDEN_TOKENS)
def test_forbidden_token_not_in_primary(primary_visible: str, token: str) -> None:
    assert token not in primary_visible, (
        f"Forbidden token leaked into Delivery Center primary slice: {token!r}"
    )


def test_no_raw_event_kind_enum_values_as_visible_text(
    primary_visible: str,
) -> None:
    """The raw closed-enum values `operator_publish` / `operator_retract` /
    `operator_note` must not appear as VISIBLE text in the primary slice.
    They may appear inside hidden form inputs (Section 5 uses
    `operator_publish` as the form's event_kind value, which is hidden)
    — those occurrences are inside `value="..."` attributes and that's
    fine. The audit forbids them appearing as `<code>` blocks, dropdown
    options, or column data."""

    # Strip attribute values too (anything inside `="..."`).
    visible_text = re.sub(r'="[^"]*"', "=\"\"", primary_visible)
    for token in ("operator_publish", "operator_retract", "operator_note"):
        assert token not in visible_text, (
            f"Raw event_kind enum value {token!r} appears as visible text"
        )


def test_no_closure_as_raw_english_visible_text(primary_visible: str) -> None:
    """The word 'closure' in raw English must not appear as visible
    operator copy in the primary slice. Operator-language label is
    '反馈回填' / '操作记录'."""

    visible_text = re.sub(r'="[^"]*"', "=\"\"", primary_visible)
    # Allow `data-role="...closure..."` attribute markers (already stripped
    # by the regex above). What remains is operator-visible body text.
    matches = re.findall(r"\bclosure\b", visible_text)
    assert not matches, f"'closure' appears as visible text: {len(matches)} times"


def test_no_provider_model_vendor_engine_in_primary(primary_visible: str) -> None:
    visible_text = re.sub(r'="[^"]*"', "=\"\"", primary_visible)
    for noun in ("provider", "model", "vendor", "engine"):
        matches = re.findall(rf"\b{noun}\b", visible_text, flags=re.IGNORECASE)
        assert not matches, f"Validator R3: '{noun}' appears in primary slice"


# --------------------------------------------------------------------------
# No fake media URL / publish URL in primary
# --------------------------------------------------------------------------


def test_no_fake_video_url_in_primary(primary_visible: str) -> None:
    for fake in (".mp4", ".m3u8", "tiktok.com/", "douyin.com/", "youtu.be/"):
        assert fake not in primary_visible


def test_no_placeholder_video_player_in_primary(primary_visible: str) -> None:
    for tag in ("<video", "<source ", "<iframe"):
        assert tag not in primary_visible


def test_no_fake_publish_url_in_primary(primary_visible: str) -> None:
    """The publish-URL column in Section 6 either renders an actual
    href from the helper (`row.publish_url`) or '—'. No placeholder
    'https://example.com' or similar."""

    visible_text = re.sub(r'="[^"]*"', "=\"\"", primary_visible)
    for fake_host in ("example.com", "youtube.com/watch", "instagram.com/p/"):
        assert fake_host not in visible_text


# --------------------------------------------------------------------------
# Legacy markers preserved inside Section 7 diagnostic fold (back-compat)
# --------------------------------------------------------------------------


LEGACY_MARKERS_IN_DIAGNOSTICS = [
    "matrix-script-delivery-center-header",
    "matrix-script-block-a-final-video-primary",
    "matrix-script-block-b-required-deliverables",
    "matrix-script-block-c-scene-pack",
    "matrix-script-block-d-copy-bundle",
    "matrix-script-block-publish-settings",
    "matrix-script-block-e-publish-feedback",
    "matrix-script-block-f-iteration-archive",
    "matrix-script-closure",
    "op-console-ms-secondary-shells-fold",
    "op-console-ms-delivery-comprehension-fold",
]


@pytest.mark.parametrize("marker", LEGACY_MARKERS_IN_DIAGNOSTICS)
def test_legacy_marker_inside_diagnostics_fold_only(
    primary_slice: str, diagnostics_slice: str, marker: str
) -> None:
    assert marker not in primary_slice, (
        f"Legacy marker leaked into Delivery Center primary slice: {marker}"
    )
    assert marker in diagnostics_slice, (
        f"Legacy marker missing from Section 7 diagnostics fold "
        f"(back-compat broken): {marker}"
    )


# --------------------------------------------------------------------------
# Branch isolation: PR-B changes do not leak into Digital Anchor branch
# --------------------------------------------------------------------------


def test_prb_section_anchors_scoped_to_matrix_script_branch(source: str) -> None:
    da_gate = source.find('{% if _da_kind == "digital_anchor" %}')
    assert da_gate != -1
    for anchor in SECTION_ANCHORS + ["op-console-ms-dc-technical-diagnostics-fold"]:
        positions = [m.start() for m in re.finditer(re.escape(anchor), source)]
        assert positions
        for pos in positions:
            assert pos < da_gate, (
                f"{anchor} leaked into / past Digital Anchor branch"
            )
