"""Template-source tests for PR-2C 可选变体 (Block E rename + restructure).

Authority: approved design plan §6.4 + Mission §B.3 + approved product
decision #2 (empty state is a single message, not N empty cards;
verbatim wording "暂未生成变体视频。你可以先生成主视频，或选择同时
生成多个变体。").
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def test_block_e_visible_title_renamed_to_optional_variants() -> None:
    """Mission §B.3: 候选评审 → 可选变体. The data-role marker is
    preserved (matrix-script-block-e-candidate-review) for back-compat
    with prior tests; only the visible title changes."""

    source = _read()
    assert '<h2 class="op-section-title" data-role="ms-block-e-title">可选变体</h2>' in source
    # The old title is retired from operator-facing copy.
    assert '<h2 class="op-section-title" data-role="ms-block-e-title">候选评审</h2>' not in source


def test_block_e_op_section_index_uses_variant_label() -> None:
    """The op-section-index next to the title shifts from "E · 评审" to
    "E · 变体" reflecting the new emphasis on variants-as-optional."""

    source = _read()
    block_e_open = source.find('data-role="matrix-script-block-e-candidate-review"')
    assert block_e_open != -1
    next_block = source.find('data-role="matrix-script-block-f', block_e_open)
    block_e_source = source[block_e_open:next_block] if next_block != -1 else source[block_e_open:block_e_open + 6000]
    assert "E · 变体" in block_e_source


def test_block_e_empty_state_uses_mission_b3_verbatim_wording() -> None:
    """Mission §B.3 verbatim: replaces the PR-0 wording per approved
    product decision #2."""

    source = _read()
    assert ">暂未生成变体视频<" in source
    assert "你可以先生成主视频，或选择同时生成多个变体。" in source
    # The PR-0 wording is retired from primary operator copy.
    # (The substring "当前暂无可预览成片" may survive elsewhere in
    # operator-facing copy as a generic phrase; the specific PR-0
    # banner title MUST be gone.)
    assert ">当前暂无可预览成片<" not in source


def test_block_e_pill_renamed_when_empty() -> None:
    source = _read()
    # PR-0 pill said "暂无可预览成片". PR-2C says simply "暂未生成".
    assert 'data-role="ms-block-e-no-preview-pill">暂未生成<' in source


def test_block_e_pill_when_resolved_says_main_plus_optional() -> None:
    """When at least one variation has fresh media, pill carries the
    new "1 主推 + N 备选" framing instead of the old "N 候选并排"."""

    source = _read()
    assert "1 主推 +" in source
    assert "备选</span>" in source


def test_block_e_subtitle_uses_operator_main_recommendation_language() -> None:
    source = _read()
    assert "主视频的备选脚本变体在这里展开；主推版本由 publish_readiness 与 closure 操作决定。" in source


def test_block_e_empty_state_tech_note_uses_operator_language_only() -> None:
    """The empty-state tech note for the PR-2C rewrite replaces the
    PR-0 "本面板不展示 final_video / 媒体链接..." engineering-
    vocabulary disclaimer with an operator-language equivalent."""

    source = _read()
    # The new operator-language tech-note appears in the empty branch
    assert "本面板不展示完整成片或外部链接；完整成片在交付页面。" in source


def test_block_e_carries_redesign_wave_attribute() -> None:
    source = _read()
    assert 'data-redesign-wave="2026-05-28-pr2c"' in source


def test_block_e_per_card_review_zone_forms_still_present_in_resolved_branch() -> None:
    """PR-2C preserves the per-zone review forms inside the expanded
    variant cards branch — they are the operator's only way to submit
    review feedback per zone."""

    source = _read()
    assert 'data-role="ms-block-e-card-zone-form-panel"' in source
    assert 'data-role="ms-block-e-card-zone-form"' in source
    # The per-card "提交分区评审意见" action is preserved (the button
    # label has surrounding whitespace; check the data-role marker +
    # the literal action label both appear).
    assert 'data-role="ms-block-e-card-action-submit-review"' in source
    assert "提交分区评审意见" in source


def test_block_e_data_role_marker_preserved_for_back_compat() -> None:
    """The container data-role MUST stay bytewise stable so prior wave
    tests (test_matrix_script_workbench_blocks_d_e_f.py etc.) still
    resolve the block."""

    source = _read()
    assert 'data-role="matrix-script-block-e-candidate-review"' in source
