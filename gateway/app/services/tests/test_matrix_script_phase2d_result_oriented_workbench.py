"""Phase 2D · Matrix Script result-oriented Workbench cleanup tests.

Authority: user mission [SYSTEM OVERRIDE] 2026-05-30 (ApolloVeo Matrix Script
Phase 2D Result-Oriented Workbench Cleanup Operator).

Phase 2D reorganizes the Matrix Script Workbench from a process-first A–I panel
stack into a result-oriented operator information architecture. The new primary
order is:

  ①  主视频结果        (§A · matrix-script-main-video-result)
  ②  生成方案确认      (NEW group header · ms-section-plan-confirm —
                        merges 脚本理解 §B + 视频生成计划 §C; storyboard dominant)
  ③  成片要素调整      (NEW group header · ms-section-final-elements —
                        画面与素材 §D / 角色与声音 §E / 字幕与音乐 §F subcards)
  ④  视频版本（可选）  (NEW group header · ms-section-video-versions-group —
                        demotes 视频变体 §G; V1 / V2 / V3 visible, optional)
  ⑤  交付入口          (§I · matrix-script-section-delivery-entry)
  —   技术诊断          (§J fold · default collapsed)

校对与微调 (§H) is demoted out of the primary section set into a default-closed
<details> (it only matters AFTER the main video lands).

This is a COPY / TEMPLATE-LAYOUT / presenter-shaping refinement ONLY. No backend
capability, worker, contract, schema, packet, closed enum, runtime, route, or
provider change. No fake media. These source-level assertions lock the
result-oriented shape so a future drift back into a process-first surface is
caught. All legacy container + sub-anchors are preserved (verified by the
Phase 2B / 2C suites still passing).
"""
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


_PROVIDER_VOCAB = (
    "provider",
    "vendor",
    "engine",
    "model_id",
    "azure",
    "akool",
    "seedance",
    "openai",
    "anthropic",
    "elevenlabs",
)


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(workbench_source: str) -> str:
    start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    end_marker = (
        "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}"
    )
    end = workbench_source.find(end_marker, start)
    assert start != -1 and end != -1
    return workbench_source[start : end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
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


# --------------------------------------------------------------------------
# (1) Primary visible order: 主视频结果 → 生成方案确认 → 成片要素调整 →
#     视频版本（可选）→ 交付入口 → 技术诊断 fold.
# --------------------------------------------------------------------------
def test_primary_section_order_is_result_oriented(matrix_branch: str) -> None:
    anchors = [
        'data-role="matrix-script-main-video-result"',       # ① 主视频结果
        'data-role="ms-section-plan-confirm"',               # ② 生成方案确认
        'data-role="ms-section-final-elements"',             # ③ 成片要素调整
        'data-role="ms-section-video-versions-group"',       # ④ 视频版本（可选）
        'data-role="matrix-script-section-delivery-entry"',  # ⑤ 交付入口
        'data-role="op-console-ms-technical-diagnostics-fold"',  # 技术诊断 fold
    ]
    positions = [matrix_branch.find(a) for a in anchors]
    for anchor, pos in zip(anchors, positions):
        assert pos != -1, f"missing primary anchor {anchor}"
    assert positions == sorted(positions), (
        "result-oriented primary order violated: " + str(list(zip(anchors, positions)))
    )


def test_primary_group_headers_render_operator_titles(primary_visible: str) -> None:
    assert ">生成方案确认</h2>" in primary_visible
    assert ">成片要素调整</h2>" in primary_visible
    assert ">视频版本（可选）</h2>" in primary_visible


# --------------------------------------------------------------------------
# (2) 校对与微调 is NOT a primary section before final_video.
# --------------------------------------------------------------------------
def test_review_tuning_not_a_primary_h2_section(primary_slice: str) -> None:
    # The review-tuning container anchor is preserved in place (between §G and
    # §I)…
    assert 'data-role="matrix-script-section-review-tuning"' in primary_slice
    # …but its title is NOT a primary <h2 class="op-section-title"> anymore —
    # it is demoted into a default-closed <details> with a subtitle heading.
    assert not re.search(
        r'<h2[^>]*data-role="ms-section-review-tuning-title"',
        primary_slice,
    ), "校对与微调 must not be a primary <h2> section before main video lands"
    assert 'data-role="ms-section-review-tuning-fold"' in primary_slice
    # The four review zones remain available (inside the fold) for back-compat.
    assert primary_slice.count('data-role="ms-section-review-tuning-zone"') == 4


# --------------------------------------------------------------------------
# (3) 脚本理解 / 视频生成计划 are no longer separate primary <h2> headings.
# --------------------------------------------------------------------------
def test_script_understanding_and_plan_not_primary_h2(primary_slice: str) -> None:
    for role in (
        "ms-section-script-understanding-title",
        "ms-section-generation-plan-title",
    ):
        assert not re.search(rf'<h2[^>]*data-role="{role}"', primary_slice), (
            f"{role} must not be a separate primary <h2> heading under Phase 2D"
        )
    # They survive as demoted <h3> supporting headings.
    assert re.search(
        r'<h3[^>]*data-role="ms-section-script-understanding-title"', primary_slice
    )
    assert re.search(
        r'<h3[^>]*data-role="ms-section-generation-plan-title"', primary_slice
    )


# --------------------------------------------------------------------------
# (4) Storyboard is visible INSIDE 生成方案确认 (after the group header).
# --------------------------------------------------------------------------
def test_storyboard_visible_inside_plan_confirm(primary_slice: str) -> None:
    confirm = primary_slice.find('data-role="ms-section-plan-confirm"')
    scene_list = primary_slice.find('data-role="ms-section-generation-plan-scene-list"')
    elements = primary_slice.find('data-role="ms-section-final-elements"')
    assert confirm != -1 and scene_list != -1 and elements != -1
    assert confirm < scene_list < elements, (
        "storyboard scene list must render inside 生成方案确认 (after the "
        "group header and before 成片要素调整)"
    )
    # The plan-confirm operator summary sentence is present.
    assert "系统已根据脚本整理出视频方向和分镜草案" in primary_slice


# --------------------------------------------------------------------------
# (5) Hook / Body / CTA + keywords + forbidden-words still exist as detail.
# --------------------------------------------------------------------------
def test_supporting_script_details_preserved(primary_slice: str) -> None:
    # Script-understanding sub-anchors survive (collapsed supporting detail).
    for role in (
        "ms-section-script-understanding-segment",
        "ms-section-script-understanding-selling-points",
        "ms-section-script-understanding-target-audience",
        "ms-section-script-understanding-tone",
        "ms-section-script-understanding-duration",
    ):
        assert f'data-role="{role}"' in primary_slice, f"missing {role}"
    # Hook / Body / CTA storyboard scaffold survives in the plan.
    assert "Hook" in primary_slice and "Body" in primary_slice and "CTA" in primary_slice
    # Keywords / forbidden-words framing survives in the supporting subtitle.
    assert "关键词" in primary_slice and "禁用词" in primary_slice


# --------------------------------------------------------------------------
# (6) 画面与素材 / 角色与声音 / 字幕与音乐 are subcards INSIDE 成片要素调整.
# --------------------------------------------------------------------------
def test_final_elements_three_subcards(primary_slice: str) -> None:
    group = primary_slice.find('data-role="ms-section-final-elements"')
    versions = primary_slice.find('data-role="ms-section-video-versions-group"')
    assert group != -1 and versions != -1
    for role in (
        "matrix-script-section-visual-materials",
        "matrix-script-section-role-voice",
        "matrix-script-section-subtitle-music",
    ):
        pos = primary_slice.find(f'data-role="{role}"')
        assert group < pos < versions, f"{role} must sit inside 成片要素调整"
    # The three legacy titles are demoted from <h2> to compact <h3> subcards.
    for role in (
        "ms-section-visual-materials-title",
        "ms-section-role-voice-title",
        "ms-section-subtitle-music-title",
    ):
        assert not re.search(rf'<h2[^>]*data-role="{role}"', primary_slice)
        assert re.search(rf'<h3[^>]*data-role="{role}"', primary_slice)
    assert "系统已给出默认成片配置，你可以按账号风格微调。" in primary_slice


# --------------------------------------------------------------------------
# (7) V1 / V2 / V3 visible under 视频版本（可选）.
# --------------------------------------------------------------------------
def test_video_versions_visible_under_optional_group(primary_slice: str) -> None:
    group = primary_slice.find('data-role="ms-section-video-versions-group"')
    assert group != -1
    # The locked legacy §G heading is preserved unchanged.
    assert re.search(
        r'<h2[^>]*data-role="ms-section-optional-variants-title">视频变体</h2>',
        primary_slice,
    )
    for vid in ("V1", "V2", "V3"):
        assert f'data-version-id="{vid}"' in primary_slice, f"missing {vid} card"
    # Optional framing copy present; no claim variants are already generated.
    assert "这一步是可选的" in primary_slice
    # All version cards still read 待生成 (not generated / not a fake render).
    assert primary_slice.count(
        'data-role="ms-section-video-versions-card-status">待生成'
    ) == 3


# --------------------------------------------------------------------------
# (8) No fake final_video / thumbnail / media URL / publish_url in primary.
# --------------------------------------------------------------------------
def test_no_fake_media_in_primary(primary_visible: str) -> None:
    lowered = primary_visible.lower()
    assert ".mp4" not in lowered
    assert ".mov" not in lowered
    assert "<video" not in lowered
    # No hard-coded external media / publish URLs (the only href is the
    # template-driven delivery link `/tasks/{{}}/publish`).
    assert "http://" not in lowered
    assert "https://" not in lowered


# --------------------------------------------------------------------------
# (9) No provider / model / vendor / engine controls in primary view.
# --------------------------------------------------------------------------
def test_no_provider_controls_in_primary(primary_visible: str) -> None:
    lowered = primary_visible.lower()
    for noun in _PROVIDER_VOCAB:
        assert noun.lower() not in lowered, f"primary view leaks {noun}"


# --------------------------------------------------------------------------
# (10) VoiceTrans is NOT embedded (no iframe) in the Workbench primary view.
# --------------------------------------------------------------------------
def test_no_voicetrans_iframe(primary_slice: str) -> None:
    assert "<iframe" not in primary_slice.lower()
    # The role/voice section keeps its no-iframe note.
    assert 'data-role="ms-section-role-voice-no-iframe-note"' in primary_slice


# --------------------------------------------------------------------------
# (11) Delivery Center (publish hub) unchanged except the nav label; the
#      Workbench delivery entry copy + CTA are preserved.
# --------------------------------------------------------------------------
def test_delivery_entry_preserved(primary_slice: str) -> None:
    assert 'data-role="ms-section-delivery-entry-cta"' in primary_slice
    assert "前往交付页面查看成片、字幕、音频、文案包与发布设置。" in primary_slice
    # Publish hub template is not touched by Phase 2D.
    publish_src = _PUBLISH_HUB.read_text(encoding="utf-8")
    assert 'data-redesign-wave="2026-05-30-phase2d"' not in publish_src


# --------------------------------------------------------------------------
# (12) Hot Follow and Digital Anchor templates are unchanged by Phase 2D.
# --------------------------------------------------------------------------
def test_other_line_templates_untouched() -> None:
    for tpl in (_HOT_FOLLOW_WORKBENCH, _DIGITAL_ANCHOR_NEW):
        src = tpl.read_text(encoding="utf-8")
        assert 'data-redesign-wave="2026-05-30-phase2d"' not in src
        assert "ms-section-plan-confirm" not in src
        assert "ms-section-final-elements" not in src
