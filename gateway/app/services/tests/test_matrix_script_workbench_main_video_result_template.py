"""Template-source tests for the PR-2A 主视频结果 Workbench anchor block.

Verifies that the new block is wired at the TOP of the matrix_script
branch (above the existing Block A 任务摘要) and that it carries all
the required data-role markers + operator-language copy.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def test_main_video_result_block_data_role_present() -> None:
    source = _read()
    assert 'data-role="matrix-script-main-video-result"' in source


def test_main_video_result_block_is_above_block_a_in_template_source() -> None:
    """PR-2A Mission §B.1: main video result anchors the TOP of the
    Workbench matrix_script branch; it must appear in template source
    BEFORE the existing Block A 任务摘要."""

    source = _read()
    main_video_idx = source.find('data-role="matrix-script-main-video-result"')
    block_a_idx = source.find('data-role="matrix-script-block-a-goal-summary"')
    assert main_video_idx != -1
    assert block_a_idx != -1
    assert main_video_idx < block_a_idx


def test_state_pill_marker_present() -> None:
    source = _read()
    assert 'data-role="ms-main-video-result-state-pill"' in source


def test_preview_hero_renders_empty_state_marker_branch() -> None:
    source = _read()
    assert 'data-role="ms-main-video-result-preview-empty"' in source
    assert 'data-role="ms-main-video-result-preview-bound"' in source


def test_old_helper_action_loop_removed_from_primary_ui() -> None:
    """The old helper action loop must not remain as hidden primary markup.
    Section A now uses the operator preview action model only."""

    source = _read()
    assert 'for action in (ms_main_video_result.primary_actions or [])' not in source
    assert 'data-action-id="{{ action.action_id }}"' not in source
    assert 'data-role="ms-acc-generate"' in source


def _main_video_card_slice(source: str) -> str:
    """Return only the source between the main video block's opening
    data-role and its closing </div></{% endif %}>."""

    open_idx = source.find('data-role="matrix-script-main-video-result"')
    assert open_idx != -1
    # The card closes with </div> followed by {% endif %} (the {% if
    # ms_main_video_result.is_matrix_script %} terminator). Find the
    # FIRST {% endif %} after the opening data-role.
    endif_idx = source.find("{% endif %}", open_idx)
    assert endif_idx != -1
    return source[open_idx:endif_idx]


def test_old_blocker_and_next_action_markers_removed() -> None:
    source = _read()
    assert 'data-role="ms-main-video-result-blocker"' not in source
    assert 'data-role="ms-main-video-result-next-action"' not in source
    assert 'data-role="legacy-main-video-compat-anchor"' in source


def test_no_engineering_identifier_in_main_video_block_source() -> None:
    """The main video card itself (from its opening data-role through its
    closing {% endif %}) must not embed any engineering identifier as
    static text. The helper output carries operator-language only; the
    template just renders the helper's strings."""

    block_source = _main_video_card_slice(_read())
    # No raw enum values in the block source
    for forbidden in (
        "head_reason=",
        "publish_readiness.head_reason",
        "RC-R8",
        "final_video",
        "artifact_lookup",
        "slot_pack",
    ):
        assert forbidden not in block_source


def test_main_video_block_carries_redesign_wave_attribute() -> None:
    source = _read()
    assert 'data-redesign-wave="2026-05-28-pr2a"' in source


def test_confirm_main_closure_attributes_removed_from_primary_template() -> None:
    """The old confirm-main helper action loop is no longer retained as
    hidden primary markup."""

    source = _read()
    assert "data-closure-endpoint" not in source
    assert "data-confirm-note-prefix" not in source
