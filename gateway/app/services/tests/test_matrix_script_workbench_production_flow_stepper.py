"""Template-source tests for the PR-2B 生产流程可观测 stepper.

Authority: approved design plan §6.3 + Mission §B.2 (compact 3-step
horizontal stepper 脚本结构 → 变体选择 → 生成; navigation aid only;
≤120px when collapsed; operator-language only).
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


def _read() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


def test_production_flow_stepper_block_data_role_present() -> None:
    source = _read()
    assert 'data-role="matrix-script-production-flow-stepper"' in source


def test_stepper_renders_after_main_video_result_and_before_block_a() -> None:
    source = _read()
    main_video = source.find('data-role="matrix-script-main-video-result"')
    stepper = source.find('data-role="matrix-script-production-flow-stepper"')
    block_a = source.find('data-role="matrix-script-block-a-goal-summary"')
    assert main_video != -1 < stepper != -1 < block_a
    assert main_video < stepper < block_a


def test_three_step_anchors_present_in_canonical_order() -> None:
    source = _read()
    stepper_open = source.find('data-role="matrix-script-production-flow-stepper"')
    # Find each step marker after the stepper opens
    step_1 = source.find('data-step-id="script_structure"', stepper_open)
    step_2 = source.find('data-step-id="variant_selection"', stepper_open)
    step_3 = source.find('data-step-id="generation"', stepper_open)
    assert -1 < step_1 < step_2 < step_3


def test_stepper_anchor_targets_have_ids() -> None:
    """The stepper steps link to #matrix-script-main-video-result /
    #matrix-script-block-b-script-structure /
    #matrix-script-block-c-variant-strategy. The target blocks MUST
    carry matching id attributes for the in-page anchor to scroll."""

    source = _read()
    assert 'id="matrix-script-main-video-result"' in source
    assert 'id="matrix-script-block-b-script-structure"' in source
    assert 'id="matrix-script-block-c-variant-strategy"' in source


def test_stepper_uses_operator_language_only_no_engineering_identifiers() -> None:
    source = _read()
    stepper_open = source.find('data-role="matrix-script-production-flow-stepper"')
    stepper_end = source.find("</div>\n      {% endif %}", stepper_open)
    block_source = source[stepper_open:stepper_end] if stepper_end != -1 else source[stepper_open:stepper_open + 4000]
    for forbidden in (
        "head_reason",
        "publish_readiness ",
        "publish_readiness.",
        "RC-R8",
        "final_video",
        "artifact_lookup",
        "slot_pack",
        "variation_axis",
    ):
        assert forbidden not in block_source


def test_stepper_step_labels_are_operator_language() -> None:
    source = _read()
    stepper_open = source.find('data-role="matrix-script-production-flow-stepper"')
    block_source = source[stepper_open:stepper_open + 4000]
    # The three step labels per Mission §B.2 exactly
    assert ">脚本结构<" in block_source
    assert ">变体选择<" in block_source
    assert ">生成<" in block_source


def test_stepper_helper_subtitle_uses_arrow_flow_notation() -> None:
    source = _read()
    assert "脚本结构 → 变体选择 → 生成。" in source


def test_stepper_step_state_attribute_set_per_step() -> None:
    """Each step carries a data-step-state attribute (done / active /
    todo) so structural tests can verify the operator's current
    position in the flow."""

    source = _read()
    assert 'data-step-state="{{ ms_step1_state }}"' in source
    assert 'data-step-state="{{ ms_step2_state }}"' in source
    assert 'data-step-state="{{ ms_step3_state }}"' in source


def test_stepper_carries_redesign_wave_attribute() -> None:
    """PR-A reset (2026-05-29) replaces the PR-2B anchor strip with an
    inline-expandable stepper; the wave attribute is updated accordingly."""

    source = _read()
    assert 'data-redesign-wave="2026-05-29-pra"' in source
