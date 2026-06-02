"""PR-B (revised overlay) · Matrix Script Workbench flow alignment tests.

Proves PR-B is a thin OVERLAY of the PR-A real result into the EXISTING
result-oriented Workbench sections — not a second parallel flow. Asserts there
is exactly one of each section, that the overlay feeds operator-usable acceptance
into the existing ① main result (suppressing 未生成/主成片缺失), that the existing
② storyboard carries the per-shot acceptance overlay, and that the existing
script-understanding / variants stay presenter-bound (no tomato fixtures
rendered as task truth).
"""
from __future__ import annotations

import re

import pytest

from gateway.app.services.matrix_script.operator_workbench_view import (
    build_matrix_script_operator_workbench_view,
)

TEMPLATE = "gateway/app/templates/task_workbench.html"
TASK = {"task_id": "ms-flow-1", "kind": "matrix_script", "config": {"entry": {}}}

USABLE_RESULT = {
    "has_result": True, "operator_usable": True, "technical_preview": False,
    "delivery_candidate": True, "official_publish_ready": False,
    "visual_semantic_match": "partial_pass", "shot_count": 5, "shot_match_count": 3,
    "real_visual_count": 3, "blocked_reason": None, "caption_mode": "burned_in",
    "preview_url": "/api/matrix-script/ms-flow-1/tomato-real-result/preview/final.mp4",
}


def _template_src() -> str:
    return open(TEMPLATE, encoding="utf-8").read()


def _count(role: str) -> int:
    return _template_src().count('data-role="%s"' % role)


# 1-5. exactly one of each section (single flow, no duplicate ms-flow-*)
def test_single_main_result_anchor() -> None:
    assert _count("matrix-script-main-video-result") == 1
    assert _count("ms-flow-main-result") == 0  # the parallel flow is gone


def test_single_script_understanding_section() -> None:
    assert _count("matrix-script-section-script-understanding") == 1
    assert _count("ms-flow-script-understanding") == 0


def test_single_generation_plan_section() -> None:
    assert _count("matrix-script-section-generation-plan") == 1
    assert _count("ms-flow-storyboard") == 0


def test_single_variants_section() -> None:
    src = _template_src()
    # the existing variants sections (optional-variants / video-versions) remain;
    # the parallel ms-flow-variants is gone.
    assert 'data-role="ms-flow-variants"' not in src
    assert src.count('data-role="matrix-script-section-optional-variants"') == 1


def test_single_delivery_entry_section() -> None:
    assert _count("matrix-script-section-delivery-entry") == 1
    assert _count("ms-flow-delivery") == 0


# 6. overlay feeds the PR-A acceptance
def test_overlay_main_result_uses_pr_a_acceptance() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    mr = v["main_result"]
    assert mr["operator_usable"] is True
    assert mr["status"] == "operator_usable"
    assert mr["visual_semantic_match"] == "partial_pass"
    assert mr["shot_match_count"] == 3 and mr["shot_count"] == 5
    assert mr["real_visual_count"] == 3
    assert mr["preview_url"].endswith("/tomato-real-result/preview/final.mp4")
    assert mr["official_publish_ready"] is False
    assert v["has_pr_a_result"] is True


def test_overlay_inert_without_result() -> None:
    v = build_matrix_script_operator_workbench_view(TASK, result=None, env={})
    assert v["has_pr_a_result"] is False
    assert v["main_result"]["status"] == "not_generated"


def _block(src: str, start_marker: str, end_marker: str) -> str:
    a = src.index(start_marker)
    b = src.index(end_marker, a)
    return src[a:b]


# 7. existing ① main result suppresses 未生成 / 主成片缺失 when operator_usable.
#    The empty-state sits in an {% else %} AFTER an {% elif ms_overlay_mr.operator_usable %}
#    branch, and the blocker banner is wrapped in {% if not ms_overlay_mr.operator_usable %},
#    so neither renders in the operator-usable state.
def test_existing_main_result_suppresses_empty_state_when_usable() -> None:
    src = _template_src()
    block = _block(src, 'id="matrix-script-main-video-result"', '{# Phase 2C')
    # empty-state is gated behind the operator-usable elif
    assert "{% elif ms_overlay_mr.operator_usable %}" in block
    assert block.index("{% elif ms_overlay_mr.operator_usable %}") < block.index('data-role="ms-main-video-result-preview-empty"')
    # blocker banner only renders when NOT operator-usable
    banner_idx = block.index('data-role="ms-main-video-result-banner"')
    guard = block.rindex("{% if not ms_overlay_mr.operator_usable %}", 0, banner_idx)
    assert guard < banner_idx
    # acceptance overlay is inside this same ① block (no separate section)
    assert 'data-role="ms-main-video-result-acceptance"' in block
    assert 'data-bind="visual_semantic_match"' in block
    assert 'data-role="ms-acc-open-video"' in block
    assert 'data-role="ms-acc-preview-url"' in block


# 8. existing ② storyboard carries the per-shot acceptance overlay (loop over
#    ms_overlay.shots) INSIDE the existing generation-plan section.
def test_existing_storyboard_has_shot_acceptance_overlay() -> None:
    src = _template_src()
    block = _block(src, 'data-role="matrix-script-section-generation-plan"',
                   'data-role="matrix-script-section-visual-materials"')
    assert 'data-role="ms-section-generation-plan-shot-acceptance-overlay"' in block
    assert "{% for s in ms_overlay.shots %}" in block
    assert 'data-role="ms-shot-acceptance"' in block
    assert "{{ s.semantic_status }}" in block and "{{ s.source }}" in block


# overlay render proof (block-extraction render with a usable result)
def test_overlay_main_result_renders_operator_usable() -> None:
    pytest.importorskip("jinja2")
    from jinja2 import Environment, ChainableUndefined
    src = _template_src()
    block = _block(src, "{% if ms_main_video_result.is_matrix_script %}", "{# Phase 2C")
    overlay = build_matrix_script_operator_workbench_view(TASK, result=USABLE_RESULT, env={})
    env = Environment(undefined=ChainableUndefined, autoescape=True)
    html = env.from_string(block).render(
        ms_main_video_result={"is_matrix_script": True, "preview": {"available": False, "empty_state_message_zh": "当前尚未生成主视频，主成片缺失"}, "primary_actions": [], "state_kind": "blocked"},
        ms_overlay_mr=overlay["main_result"], ms_overlay_has=True, ms_overlay=overlay, task=TASK,
    )
    assert "当前尚未生成主视频" not in html  # empty-state suppressed
    assert "主成片缺失" not in html
    assert "运营可用" in html and "partial_pass" in html
    assert "/tomato-real-result/preview/final.mp4" in html


# 9. existing script-understanding stays presenter-bound, no tomato fixture
def test_script_understanding_presenter_bound_not_fixture() -> None:
    src = _template_src()
    su = src[src.index('data-role="matrix-script-section-script-understanding"'):]
    su = su[:su.index('data-role="matrix-script-section-generation-plan"')]
    assert "ms_script_structure" in su  # bound to the per-task presenter
    # the removed hardcoded fixture is not rendered anywhere
    assert "TOMATO_SCRIPT_UNDERSTANDING" not in src
    # the helper module no longer defines the fixture
    from gateway.app.services.matrix_script import tomato_real_result_plan as p
    assert not hasattr(p, "TOMATO_SCRIPT_UNDERSTANDING")


# 10. existing variants stay presenter-bound, no tomato fixture
def test_variants_presenter_bound_not_fixture() -> None:
    src = _template_src()
    assert "ms_readable_variants" in src
    assert "TOMATO_VARIANTS" not in src
    from gateway.app.services.matrix_script import tomato_real_result_plan as p
    assert not hasattr(p, "TOMATO_VARIANTS")


# 11. existing delivery entry keeps /tasks/{task_id}/publish
def test_delivery_entry_keeps_publish_cta() -> None:
    src = _template_src()
    dse = src[src.index('data-role="matrix-script-section-delivery-entry"'):]
    dse = dse[:dse.index('技术诊断')]
    assert "/tasks/{{ task.task_id }}/publish" in dse
    assert "/tasks/connect/matrix_script/publish" not in dse


def test_temporary_result_cards_removed_from_primary_workbench() -> None:
    src = _template_src()
    for role in (
        "matrix-script-minimal-result",
        "matrix-script-minimal-result-action",
        "matrix-script-staged-preview-action",
        "matrix-script-archived-temp-preview-fold",
        "ms-section-plan-confirm",
        "ms-section-final-elements",
        "ms-section-video-versions-group",
    ):
        assert f'data-role="{role}"' not in src
    for label in ("本地最小成片", "暂存并预览", "生成本地最小成片", "生成并暂存"):
        assert label not in src


# 12. no provider/publish/vendor leakage in the overlay view
def test_no_forbidden_token_leakage() -> None:
    for res in (None, USABLE_RESULT):
        v = build_matrix_script_operator_workbench_view(TASK, result=res, env={})
        blob = str(v).lower()
        for token in ("provider_url", "temporary_url", "download_url", "akool",
                      "vendor", "model_id", "credit", "publish_url", "publish_status",
                      "http://", "https://"):
            assert token not in blob


def test_overlay_from_staged_candidate_on_config() -> None:
    task = {"task_id": "ms-2", "kind": "matrix_script",
            "config": {"matrix_script_staged_candidate": USABLE_RESULT}}
    v = build_matrix_script_operator_workbench_view(task, env={})
    assert v["main_result"]["operator_usable"] is True
