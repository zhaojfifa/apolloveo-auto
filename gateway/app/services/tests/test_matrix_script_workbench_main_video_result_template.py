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


def test_four_action_buttons_carry_data_action_id() -> None:
    """The template renders ``data-action-id="{{ action.action_id }}"`` via
    Jinja interpolation; assert the loop + the data-action-id attribute
    are wired so all four actions get individual markers at render time.
    The action_id values themselves are pinned in the helper module
    constants tested in test_matrix_script_main_video_result_view."""

    source = _read()
    # The loop iterates over primary_actions and renders the marker:
    assert 'for action in (ms_main_video_result.primary_actions or [])' in source
    assert 'data-action-id="{{ action.action_id }}"' in source


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


def test_blocker_and_next_action_markers_present() -> None:
    source = _read()
    assert 'data-role="ms-main-video-result-blocker"' in source
    assert 'data-role="ms-main-video-result-next-action"' in source


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


def test_confirm_main_button_carries_closure_endpoint_attribute_when_enabled() -> None:
    """The closure endpoint + note prefix attributes only render when
    the confirm-main action is enabled (so JS can do the write-back)."""

    source = _read()
    # The data-closure-endpoint attribute IS in the template (rendered
    # conditionally inside the action loop).
    assert "data-closure-endpoint" in source
    assert "data-confirm-note-prefix" in source
