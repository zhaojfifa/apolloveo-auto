"""Matrix Script Workbench primary operator flow tests.

This suite enforces the post-cleanup operator order:

主视频预览 → 背景素材配乐调整 → 交付入口 → 视频变体 →
脚本理解 / 故事理解 → 技术诊断.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"


@pytest.fixture(scope="module")
def source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


def _matrix_branch(source: str) -> str:
    start = source.index('ops_workbench_panel.panel_kind == "matrix_script"')
    end = source.index(
        "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}",
        start,
    )
    return source[start:end]


def _primary_flow(source: str) -> str:
    branch = _matrix_branch(source)
    end = branch.index('data-role="op-console-ms-technical-diagnostics-fold"')
    return branch[:end]


def _render_primary(source: str, *, generated: bool, material_changed: bool = False) -> str:
    pytest.importorskip("jinja2")
    from jinja2 import ChainableUndefined, Environment

    branch = _primary_flow(source)
    start = branch.index("{% if ms_main_video_result.is_matrix_script %}")
    end = branch.index("{# Phase 2C", start)
    template = branch[start:end]
    result = {
        "operator_usable": generated,
        "technical_preview": False,
        "preview_url": "/api/matrix-script/ms-1/tomato-real-result/preview/final.mp4" if generated else "",
        "status": "operator_usable" if generated else "not_generated",
        "status_label_zh": "运营可用" if generated else "未生成",
        "visual_semantic_match": "partial_pass" if generated else "",
        "shot_match_count": 3 if generated else 0,
        "shot_count": 5 if generated else 0,
        "real_visual_count": 3 if generated else 0,
        "delivery_candidate": generated,
        "blocked_reason": None,
    }
    overlay = {
        "main_result": result,
        "has_pr_a_result": generated,
        "delivery": {
            "delivery_candidate": generated,
            "preview_url": result["preview_url"],
        },
        "material_changed": material_changed,
        "shots": [
            {
                "shot_id": f"shot-{idx}",
                "order": idx,
                "title": title,
                "asset_name": asset,
                "source": source_kind,
                "semantic_status": semantic,
                "included_in_current_video": True,
            }
            for idx, title, asset, source_kind, semantic in (
                (1, "海边开场", "01_beach_hook.png", "local_real_asset", "pass"),
                (2, "圣女果碗", "02_tomato_bowl.png", "local_real_asset", "pass"),
                (3, "采摘特写", "03_pick_tomato.png", "local_real_asset", "pass"),
                (4, "品尝镜头", "02_tomato_bowl.png", "fallback_semantic_reuse", "partial"),
                (5, "递镜收尾", "01_beach_hook.png", "fallback_semantic_reuse", "partial"),
            )
        ],
    }
    html = Environment(undefined=ChainableUndefined, autoescape=True).from_string(template).render(
        ms_main_video_result={
            "is_matrix_script": True,
            "state_kind": "blocked",
            "state_label_zh": "未生成",
            "preview": {"available": False},
            "primary_actions": [],
        },
        ms_overlay_mr=result,
        ms_overlay_has=generated,
        ms_overlay=overlay,
        ms_preview_compare={"is_matrix_script": True},
        ms_script_structure={
            "is_matrix_script": True,
            "topic_value": "海边与圣女果",
            "target_platform_value": "TikTok",
            "target_audience_value": "水果爱好者",
            "sections": [
                {"section_label_zh": "Hook", "body_text": "海边开场"},
                {"section_label_zh": "Body", "body_text": "圣女果卖点"},
                {"section_label_zh": "CTA", "body_text": "点击购买"},
            ],
        },
        task={"task_id": "ms-1", "title": "海边与圣女果"},
    )
    return html


def _a_section(rendered: str) -> str:
    start = rendered.index('id="matrix-script-main-video-result"')
    end = rendered.index('data-role="matrix-script-primary-material-music"', start)
    return rendered[start:end]


def test_visible_primary_section_order(source: str) -> None:
    primary = _matrix_branch(source)
    roles = [
        "matrix-script-main-video-result",
        "matrix-script-primary-material-music",
        "matrix-script-primary-delivery-entry",
        "matrix-script-primary-video-variants",
        "matrix-script-primary-script-story",
        "op-console-ms-technical-diagnostics-fold",
    ]
    positions = [primary.index(f'data-role="{role}"') for role in roles]
    assert positions == sorted(positions)
    assert primary.index('data-role="matrix-script-primary-material-music"') < primary.index(
        'data-role="matrix-script-primary-script-story"'
    )


def test_legacy_phase2b_cards_are_not_primary_visible(source: str) -> None:
    primary = _primary_flow(source)
    for role in (
        "matrix-script-section-script-understanding",
        "matrix-script-section-generation-plan",
        "matrix-script-section-visual-materials",
        "matrix-script-section-role-voice",
        "matrix-script-section-subtitle-music",
        "matrix-script-section-optional-variants",
        "matrix-script-section-delivery-entry",
    ):
        marker = f'data-role="{role}"'
        idx = primary.index(marker)
        tag = primary[primary.rfind("<div", 0, idx) : primary.find(">", idx) + 1]
        assert "hidden" in tag
        assert 'aria-hidden="true"' in tag


def test_ungenerated_state_has_single_generate_preview_action(source: str) -> None:
    section = _a_section(_render_primary(source, generated=False))
    assert "主视频预览" in section
    assert "未生成" in section
    assert "请先确认素材与配乐，然后生成视频预览" in section
    assert 'data-role="ms-main-video-material-readiness"' in section
    assert "真实素材镜头" in section
    assert "待补素材镜头" in section
    assert "配乐" in section
    assert "旁白" in section
    assert "字幕承载 / 语音合成待接入" in section
    assert section.count("生成视频预览") >= 1
    for forbidden in ("重新生成", "再次生成", "确认为主版本", "前往交付", "前往交付页面", "打开视频", "主成片缺失"):
        assert forbidden not in section


def test_generated_state_has_inline_video_and_no_duplicate_actions(source: str) -> None:
    section = _a_section(_render_primary(source, generated=True))
    assert '<video controls preload="metadata" src="/api/matrix-script/ms-1/tomato-real-result/preview/final.mp4"' in section
    assert "运营可用" in section
    assert "当前版本" in section
    assert "V1 主视频预览" in section
    assert "partial_pass" in section
    assert "匹配镜头数" in section
    assert "真实视觉镜头数" in section
    assert "待补素材镜头" in section
    assert "正式交付就绪：false" in section
    assert section.count("再次生成预览") == 1
    assert section.count("确认为主版本") == 1
    assert section.count("前往交付") == 1
    assert section.count("打开视频") == 1
    assert 'data-role="ms-main-video-result-actions"' not in section
    assert 'data-role="legacy-main-video-compat-anchor"' in section
    compat_idx = section.index('data-role="legacy-main-video-compat-anchor"')
    compat_tag = section[section.rfind("<div", 0, compat_idx) : section.find(">", compat_idx) + 1]
    assert "hidden" in compat_tag
    assert 'aria-hidden="true"' in compat_tag
    assert "inert" in compat_tag


def test_raw_rendered_primary_has_no_old_hidden_action_text(source: str) -> None:
    for generated in (False, True):
        html = _render_primary(source, generated=generated)
        primary_end = html.find('data-role="op-console-ms-technical-diagnostics-fold"')
        primary = html[:primary_end] if primary_end != -1 else html
        assert 'data-role="ms-main-video-result-actions"' not in primary
        assert 'data-role="legacy-main-video-compat-anchor"' in primary
        compat_idx = primary.index('data-role="legacy-main-video-compat-anchor"')
        compat_tag = primary[
            primary.rfind("<div", 0, compat_idx) : primary.find(">", compat_idx) + 1
        ]
        assert "hidden" in compat_tag
        assert 'aria-hidden="true"' in compat_tag
        assert "inert" in compat_tag
        assert "</div>" in primary[compat_idx : compat_idx + 120]
        for forbidden in (
            "前往交付页面",
            "主成片缺失",
        ):
            assert forbidden not in primary
        compat_block = primary[primary.rfind("<div", 0, compat_idx) : primary.find("</div>", compat_idx) + len("</div>")]
        for forbidden in (
            "重新生成",
            "确认为主版本",
            "前往交付",
            "前往交付页面",
            "生成主视频",
            "打开视频",
            "主成片缺失",
        ):
            assert forbidden not in compat_block
        if not generated:
            a_section = _a_section(primary)
            for forbidden in ("确认为主版本", "前往交付", "打开视频", "再次生成"):
                assert forbidden not in a_section
            for forbidden in ("确认为主版本", "前往交付", "打开视频"):
                assert forbidden not in primary


def test_material_delivery_and_folded_sections_render(source: str) -> None:
    html = _render_primary(source, generated=True)
    assert 'data-role="matrix-script-primary-material-music"' in html
    assert html.count('data-role="ms-primary-shot-card"') == 5
    assert html.count('data-role="ms-primary-shot-replace-action"') == 5
    assert "素材来源：真实素材" in html
    assert "素材来源：复用素材" in html
    assert "语义状态：通过" in html
    assert "语义状态：部分通过" in html
    assert "当前为复用素材，建议补充真实品尝素材。" in html
    assert "当前为复用素材，建议补充递向镜头素材。" in html
    assert "上传/替换 Shot 04 素材" in html
    assert "上传/替换 Shot 05 素材" in html
    assert "替换配乐" in html
    assert "重新匹配素材" in html
    assert "替换素材或配乐后，请返回主视频区点击“再次生成预览”。新预览不会自动成为正式发布版本。" in html
    assert "当前配乐" in html
    assert "字幕" in html
    assert "旁白" in html
    assert "当前交付候选：主视频 V1" in html
    assert "official_publish_ready=false" in html
    assert 'data-role="ms-primary-delivery-cta"' in html
    assert 'data-role="ms-primary-video-variants-fold"' in html
    assert 'data-role="ms-primary-script-story-fold"' in html


def test_delivery_button_hidden_until_candidate(source: str) -> None:
    html = _render_primary(source, generated=False)
    delivery = html[html.index('data-role="matrix-script-primary-delivery-entry"') :]
    delivery = delivery[: delivery.index('data-role="matrix-script-primary-video-variants"')]
    assert "生成视频预览后可进入交付" in delivery
    assert 'data-role="ms-primary-delivery-cta"' not in delivery
    assert "前往交付页" not in delivery


def test_primary_flow_has_no_backend_or_provider_leakage(source: str) -> None:
    rendered = _render_primary(source, generated=True)
    diagnostics_start = rendered.find('data-role="op-console-ms-technical-diagnostics-fold"')
    primary = rendered[:diagnostics_start] if diagnostics_start != -1 else rendered
    for token in (
        "SOURCE",
        "SEMANTIC_STATUS",
        "INCLUDED_IN_CURRENT_VIDEO",
        "provider_url",
        "publish_url",
        "Akool",
        "akool",
        "model_id",
        "credit",
    ):
        assert token not in primary


def test_material_changed_state_prompts_regenerate_preview(source: str) -> None:
    rendered = _render_primary(source, generated=True, material_changed=True)
    assert "素材已更新，需要再次生成预览" in rendered
    assert "重新生成预览" in rendered
