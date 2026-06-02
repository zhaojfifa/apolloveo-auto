"""Matrix Script cleanup tests for the accepted A-J Workbench flow."""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "gateway" / "app" / "templates"
_WORKBENCH = _TEMPLATES / "task_workbench.html"
_PUBLISH_HUB = _TEMPLATES / "task_publish_hub.html"
_HOT_FOLLOW_WORKBENCH = _TEMPLATES / "hot_follow_workbench.html"
_DIGITAL_ANCHOR_NEW = _TEMPLATES / "digital_anchor_new.html"


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(workbench_source: str) -> str:
    start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    end_marker = "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}"
    end = workbench_source.find(end_marker, start)
    assert start != -1 and end != -1
    return workbench_source[start : end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find('data-role="op-console-ms-technical-diagnostics-fold"')
    assert fold_open != -1
    return matrix_branch[:fold_open]


def _strip_non_rendered(text: str) -> str:
    no_j = re.sub(r"{#.*?#}", "", text, flags=re.DOTALL)
    no_h = re.sub(r"<!--.*?-->", "", no_j, flags=re.DOTALL)
    no_s = re.sub(r"{%.*?%}", "", no_h, flags=re.DOTALL)
    no_e = re.sub(r"{{.*?}}", "{{}}", no_s, flags=re.DOTALL)
    return no_e


@pytest.fixture(scope="module")
def primary_visible(primary_slice: str) -> str:
    return _strip_non_rendered(primary_slice)


def test_primary_section_order_is_accepted_a_to_j(matrix_branch: str) -> None:
    anchors = [
        'data-role="matrix-script-main-video-result"',
        'data-role="matrix-script-section-script-understanding"',
        'data-role="matrix-script-section-generation-plan"',
        'data-role="matrix-script-section-visual-materials"',
        'data-role="matrix-script-section-role-voice"',
        'data-role="matrix-script-section-subtitle-music"',
        'data-role="matrix-script-section-video-versions"',
        'data-role="matrix-script-section-review-tuning"',
        'data-role="matrix-script-section-delivery-entry"',
        'data-role="op-console-ms-technical-diagnostics-fold"',
    ]
    positions = [matrix_branch.find(a) for a in anchors]
    for anchor, pos in zip(anchors, positions):
        assert pos != -1, f"missing primary anchor {anchor}"
    assert positions == sorted(positions)


def test_removed_group_headers_and_temp_cards_are_absent(workbench_source: str) -> None:
    for role in (
        "ms-section-plan-confirm",
        "ms-section-final-elements",
        "ms-section-video-versions-group",
        "matrix-script-minimal-result",
        "matrix-script-minimal-result-action",
        "matrix-script-staged-preview-action",
        "matrix-script-archived-temp-preview-fold",
    ):
        assert f'data-role="{role}"' not in workbench_source
    for label in ("本地最小成片", "暂存并预览", "生成本地最小成片", "生成并暂存"):
        assert label not in workbench_source


def test_a_to_j_operator_titles_are_direct(primary_visible: str) -> None:
    for title in (
        "A · 主视频结果",
        "B · 脚本理解",
        "C · 视频生成计划",
        "D · 画面与素材",
        "E · 角色与声音",
        "F · 字幕与音乐",
        "G · 视频变体",
        "H · 校对与微调",
        "I · 交付入口",
        "J · 技术诊断",
    ):
        assert title in primary_visible or title == "J · 技术诊断"


def test_review_tuning_is_collapsed(primary_slice: str) -> None:
    assert 'data-role="matrix-script-section-review-tuning"' in primary_slice
    assert 'data-role="ms-section-review-tuning-fold"' in primary_slice
    assert primary_slice.count('data-role="ms-section-review-tuning-zone"') == 4


def test_storyboard_has_shot_acceptance_overlay(primary_slice: str) -> None:
    assert 'data-role="ms-section-generation-plan-scene-list"' in primary_slice
    assert 'data-role="ms-section-generation-plan-shot-acceptance-overlay"' in primary_slice
    assert 'data-role="ms-shot-acceptance"' in primary_slice
    assert "{{ s.source }}" in primary_slice
    assert "{{ s.semantic_status }}" in primary_slice


def test_delivery_entry_projects_preview_candidate(primary_slice: str) -> None:
    assert 'data-role="ms-section-delivery-entry-acceptance"' in primary_slice
    assert 'data-role="ms-delivery-acc-candidate"' in primary_slice
    assert 'data-role="ms-delivery-acc-preview-url"' in primary_slice
    assert "official_publish_ready=false" in primary_slice
    assert 'href="/tasks/{{ task.task_id }}/publish"' in primary_slice


def test_no_fake_or_forbidden_primary_media(primary_visible: str) -> None:
    lowered = primary_visible.lower()
    for token in (
        "provider_url", "temporary_url", "download_url", "publish_url",
        "publish_status", "artifact_key", "r2_key", "model_id", "credit",
        "<video", "<iframe", "http://", "https://",
    ):
        assert token not in lowered


def test_no_voicetrans_iframe(primary_slice: str) -> None:
    assert "<iframe" not in primary_slice.lower()
    assert 'data-role="ms-section-role-voice-no-iframe-note"' in primary_slice


def test_publish_hub_not_part_of_cleanup_wave() -> None:
    publish_src = _PUBLISH_HUB.read_text(encoding="utf-8")
    assert "ms-section-plan-confirm" not in publish_src
    assert "matrix-script-staged-preview-action" not in publish_src


def test_other_line_templates_untouched() -> None:
    for tpl in (_HOT_FOLLOW_WORKBENCH, _DIGITAL_ANCHOR_NEW):
        src = tpl.read_text(encoding="utf-8")
        assert "ms-section-plan-confirm" not in src
        assert "matrix-script-staged-preview-action" not in src
