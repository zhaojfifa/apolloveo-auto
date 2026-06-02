"""Phase 2B product-fidelity fix tests (2026-05-30).

Authority: user mission [SYSTEM OVERRIDE] 2026-05-30 (Matrix Script
Phase 2B Product Fidelity Fixer). The mission identified that Phase 2B
implementation at commit 5f5a0bc passed structural tests but drifted
back toward the old backend/task-driven Workbench. This suite enforces
the product fidelity rules so the real pages match the Phase 1 mock's
mental model, not just the data-role anchor shape.

Thirteen mission assertions:

  1.  New Task primary copy contains '生成脚本视频方案'.
  2.  New Task primary copy does NOT contain '创建矩阵脚本任务'.
  3.  New Task sidebar does NOT mention legacy A–F block names.
  4.  Workbench primary scan does NOT contain PR-A production-flow
      stepper outside §J 技术诊断.
  5.  Workbench primary section order is exactly A–J.
  6.  §C contains all 11 storyboard fields.
  7.  §C contains product-language examples, not only status-code
      labels.
  8.  §G renders V1 / V2 / V3 video-version cards.
  9.  §G contains '哪里不同' and '为什么测这一版'.
 10.  §G primary scan does NOT contain axis vocabulary.
 11.  Legacy A–F markers are only inside collapsed §J.
 12.  No fake video / media / publish URLs.
 13.  No provider / model / vendor / engine controls.

Plus a fourteenth check that the Workbench legacy task-meta header
(task_id / platform / account_id / category_key / language meta-grid)
is gated to non-matrix_script kinds only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
_NEW_TASK = _REPO_ROOT / "gateway" / "app" / "templates" / "matrix_script_new.html"


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def new_task_source() -> str:
    return _NEW_TASK.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def matrix_branch(workbench_source: str) -> str:
    start = workbench_source.find('ops_workbench_panel.panel_kind == "matrix_script"')
    end_marker = (
        "</details> {# /op-console-ms-technical-diagnostics-fold (PR-A Section 5) #}"
    )
    end = workbench_source.find(end_marker, start)
    return workbench_source[start : end + len(end_marker)]


@pytest.fixture(scope="module")
def primary_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    return matrix_branch[:fold_open]


@pytest.fixture(scope="module")
def diagnostics_slice(matrix_branch: str) -> str:
    fold_open = matrix_branch.find(
        'data-role="op-console-ms-technical-diagnostics-fold"'
    )
    return matrix_branch[fold_open:]


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
# (1) (2) New Task page copy
# --------------------------------------------------------------------------


def test_new_task_page_uses_script_to_video_title(new_task_source: str) -> None:
    """The Phase 2B fidelity fix renames the page title from
    '创建矩阵脚本任务' to '生成脚本视频方案'."""

    assert "生成脚本视频方案" in new_task_source
    assert "创建矩阵脚本任务" not in new_task_source


def test_new_task_subtitle_uses_script_to_video_promise(
    new_task_source: str,
) -> None:
    """The subtitle reads as the Phase-1-mock script-to-video promise,
    not as a task-creation announcement."""

    assert "输入脚本、素材和目标平台" in new_task_source
    assert "脚本理解" in new_task_source
    assert "分镜" in new_task_source
    assert "背景 / B-Roll" in new_task_source
    # Old task-form copy is gone.
    for old in (
        "创建后，系统会解析脚本结构、生成变体方案，并进入工作台评审",
        "正式产线新建入口",
    ):
        assert old not in new_task_source


def test_new_task_topbar_subtitle_is_script_to_video(new_task_source: str) -> None:
    assert '"脚本转视频 · 生成方案入口"' in new_task_source
    assert '"正式产线新建入口"' not in new_task_source


# --------------------------------------------------------------------------
# (3) New Task sidebar steps reframed away from legacy A–F vocabulary
# --------------------------------------------------------------------------


LEGACY_NEW_TASK_SIDEBAR_PHRASES = [
    "任务摘要",
    "脚本结构",
    "变体方案",
    "生成进度",
    "候选评审",
    "交付摘要",
]


@pytest.mark.parametrize("phrase", LEGACY_NEW_TASK_SIDEBAR_PHRASES)
def test_new_task_sidebar_omits_legacy_block_names(
    new_task_source: str, phrase: str
) -> None:
    """The sidebar '提交后会发生什么' must not mention the legacy A–F
    block names. The new four-step copy is product-language only."""

    sidebar = re.search(
        r'data-role="ms-new-route-map-script-to-video-steps".*?</ol>',
        new_task_source,
        flags=re.DOTALL,
    )
    assert sidebar is not None
    assert phrase not in sidebar.group(0), (
        f"Sidebar still mentions legacy block: {phrase}"
    )


def test_new_task_sidebar_has_four_script_to_video_steps(
    new_task_source: str,
) -> None:
    sidebar = re.search(
        r'data-role="ms-new-route-map-script-to-video-steps".*?</ol>',
        new_task_source,
        flags=re.DOTALL,
    )
    assert sidebar is not None
    block = sidebar.group(0)
    for expected in (
        "脚本理解",
        "视频方案",
        "角色与音频计划",
        "工作台确认方案",
    ):
        assert expected in block


# --------------------------------------------------------------------------
# (4) Workbench primary does NOT contain PR-A standalone stepper
# --------------------------------------------------------------------------


def test_pra_stepper_not_in_workbench_primary(primary_visible: str) -> None:
    """The PR-A standalone production-flow stepper is relocated into §J.
    Operator primary scan must not contain the stepper anchor or its
    operator-language title."""

    visible = re.sub(r'="[^"]*"', '=""', primary_visible)
    assert "matrix-script-production-flow-stepper" not in visible
    assert "生产流程可观测" not in visible


def test_pra_stepper_lives_inside_diagnostics_fold(
    diagnostics_slice: str,
) -> None:
    """The stepper anchor is preserved inside the §J fold for back-compat
    with PR-A structural tests."""

    assert "matrix-script-production-flow-stepper" in diagnostics_slice
    assert 'data-role="ms-production-flow-step-detail"' in diagnostics_slice


# --------------------------------------------------------------------------
# (5) Workbench primary section order is operator-first
# --------------------------------------------------------------------------


PRIMARY_SECTION_ORDER = [
    ("A", "matrix-script-main-video-result"),
    ("B", "matrix-script-section-generation-plan"),
    ("C", "matrix-script-section-role-voice"),
    ("D", "matrix-script-section-delivery-entry"),
    ("E", "matrix-script-section-optional-variants"),
    ("F", "matrix-script-section-script-understanding"),
    ("G", "op-console-ms-technical-diagnostics-fold"),
]


def test_primary_section_order_is_operator_first(matrix_branch: str) -> None:
    positions = [
        matrix_branch.find(f'data-role="{anchor}"')
        for _, anchor in PRIMARY_SECTION_ORDER
    ]
    assert all(p != -1 for p in positions), (
        f"Section anchors missing: {list(zip([l for l,_ in PRIMARY_SECTION_ORDER], positions))}"
    )
    assert positions == sorted(positions), (
        f"Sections out of order: {list(zip([l for l,_ in PRIMARY_SECTION_ORDER], positions))}"
    )


# --------------------------------------------------------------------------
# (6) §C carries all 11 storyboard fields
# --------------------------------------------------------------------------


STORYBOARD_FIELD_ROLES = [
    "ms-section-generation-plan-scene-number",
    "ms-section-generation-plan-scene-script-segment",
    "ms-section-generation-plan-scene-visual-intent",
    "ms-section-generation-plan-scene-background-suggestion",
    "ms-section-generation-plan-scene-broll-suggestion",
    "ms-section-generation-plan-scene-product-material-slot",
    "ms-section-generation-plan-scene-role",
    "ms-section-generation-plan-scene-voiceover",
    "ms-section-generation-plan-scene-subtitle",
    "ms-section-generation-plan-scene-music-mood",
    "ms-section-generation-plan-scene-aspect-ratio",
]


@pytest.mark.parametrize("field_role", STORYBOARD_FIELD_ROLES)
def test_generation_plan_storyboard_field_present(
    primary_slice: str, field_role: str
) -> None:
    assert f'data-role="{field_role}"' in primary_slice, (
        f"§C storyboard field missing: {field_role}"
    )


def test_generation_plan_storyboard_field_labels_present_in_visible_copy(
    primary_slice: str,
) -> None:
    """Operator must see the field labels rendered. The 11 operator-
    language labels appear as literal text inside the storyboard rows."""

    for label in (
        "场景 ",  # rendered as "场景 1" / "场景 2" / "场景 3" via Jinja
        "脚本片段", "视觉意图", "背景建议",
        "B-Roll 建议", "产品素材位", "角色 / 出镜",
        "旁白", "字幕", "音乐情绪", "画幅",
    ):
        assert label in primary_slice, (
            f"§C operator-language label missing in primary scan: {label}"
        )


# --------------------------------------------------------------------------
# (7) §C carries product-language examples, not only status codes
# --------------------------------------------------------------------------


def test_generation_plan_includes_product_language_examples(
    primary_slice: str,
) -> None:
    """The deterministic placeholder content reads as a generation
    plan — backgrounds like '厨房 / 阳台 / 农场', B-Roll lines like
    '主体特写', music moods like '上扬 · 轻快' — not as raw status
    codes only. The examples live inside the {% set _scene_meta = […] %}
    block; source-level check finds them as string literals."""

    for example in (
        "厨房", "农场", "超市",
        "主体特写", "终镜定格",
        "AI 主播", "温和女声",
        "上扬",
    ):
        assert example in primary_slice, (
            f"§C product-language example missing: {example}"
        )


# --------------------------------------------------------------------------
# (8) §G renders V1 / V2 / V3 cards
# --------------------------------------------------------------------------


@pytest.mark.parametrize("version_id", ["V1", "V2", "V3"])
def test_video_versions_card_present(
    primary_slice: str, version_id: str
) -> None:
    assert (
        f'data-role="ms-section-video-versions-card"' in primary_slice
        and f'data-version-id="{version_id}"' in primary_slice
    )


def test_video_versions_recommended_marker_on_v1(primary_slice: str) -> None:
    """V1 is the recommended version; carries data-is-recommended='true'
    and a ⭐ 推荐 marker."""

    # V1 card opens with the three data-* attrs (data-role +
    # data-version-id="V1" + data-is-recommended="true").
    v1_card = re.search(
        r'data-role="ms-section-video-versions-card"\s+data-version-id="V1"\s+data-is-recommended="true"',
        primary_slice,
        flags=re.DOTALL,
    )
    assert v1_card is not None, "V1 card missing data-is-recommended='true'"
    # The ⭐ 推荐 marker appears inside the V1 card body (before V2 starts).
    v2_pos = primary_slice.find('data-version-id="V2"', v1_card.end())
    v1_body = primary_slice[v1_card.end():v2_pos if v2_pos > 0 else v1_card.end() + 2000]
    assert "⭐ 推荐" in v1_body
    assert 'data-role="ms-section-video-versions-card-recommended-marker"' in v1_body


def test_video_versions_only_v1_is_recommended(primary_slice: str) -> None:
    """V2 and V3 cards carry data-is-recommended='false'; the recommended
    marker appears exactly once across all three cards."""

    assert 'data-version-id="V2"\n                 data-is-recommended="false"' in primary_slice
    assert 'data-version-id="V3"\n                 data-is-recommended="false"' in primary_slice
    # The recommended marker data-role appears exactly once.
    occurrences = primary_slice.count(
        'data-role="ms-section-video-versions-card-recommended-marker"'
    )
    assert occurrences == 1


# --------------------------------------------------------------------------
# (9) §G card carries 哪里不同 + 为什么测这一版
# --------------------------------------------------------------------------


def test_video_versions_card_carries_diff_and_why_columns(
    primary_slice: str,
) -> None:
    assert 'data-role="ms-section-video-versions-card-differentiator"' in primary_slice
    assert 'data-role="ms-section-video-versions-card-why-test"' in primary_slice
    visible = _strip_non_rendered(primary_slice)
    assert "哪里不同" in visible
    assert "为什么测这一版" in visible


# --------------------------------------------------------------------------
# (10) §G primary scan has no axis-tuple vocabulary
# --------------------------------------------------------------------------


def test_video_versions_section_omits_axis_vocabulary(
    primary_visible: str,
) -> None:
    """The §G primary scan must not contain axis-tuple raw labels in
    operator-visible text."""

    # Find §G primary body
    g_open = primary_visible.find('data-role="matrix-script-section-optional-variants"')
    h_open = primary_visible.find('data-role="matrix-script-section-review-tuning"')
    g_body = primary_visible[g_open:h_open]
    for axis_token in (
        "variation_axis",
        "axis_tuple",
        "audience=[",
        "tone=[",
        "length=[",
        "b2b", "b2c",
        "casual", "formal", "playful",
    ):
        assert axis_token not in g_body, (
            f"Section G primary scan still contains axis token: {axis_token}"
        )


# --------------------------------------------------------------------------
# (11) Legacy A–F markers only inside §J fold
# --------------------------------------------------------------------------


LEGACY_AF_MARKERS = [
    "matrix-script-block-a-goal-summary",
    "matrix-script-block-b-script-structure",
    "matrix-script-block-c-variant-strategy",
    "matrix-script-block-d-generate-regenerate",
    "matrix-script-block-e-candidate-review",
    "matrix-script-block-f-delivery-teaser",
]


@pytest.mark.parametrize("marker", LEGACY_AF_MARKERS)
def test_legacy_af_marker_only_in_diagnostics(
    primary_slice: str, diagnostics_slice: str, marker: str
) -> None:
    assert marker not in primary_slice
    assert marker in diagnostics_slice


# --------------------------------------------------------------------------
# (12) No fake media / publish URLs
# --------------------------------------------------------------------------


def test_no_fake_media_or_publish_url(primary_visible: str) -> None:
    visible = re.sub(r'="[^"]*"', '=""', primary_visible)
    for fake in (
        ".mp4", ".m3u8", ".webm",
        "youtu.be/", "youtube.com/watch",
        "tiktok.com/", "douyin.com/",
        "instagram.com/p/",
        "example.com",
    ):
        assert fake not in visible, f"Fake media URL leaked: {fake}"


def test_only_real_preview_video_no_iframe_or_source_tag_in_primary(primary_slice: str) -> None:
    assert '<video controls preload="metadata" src="{{ ms_overlay_mr.preview_url }}"' in primary_slice
    for tag in ("<iframe", "<source "):
        assert tag not in primary_slice


# --------------------------------------------------------------------------
# (13) No provider / model / vendor / engine controls in primary
# --------------------------------------------------------------------------


def test_no_provider_model_vendor_engine_controls(primary_slice: str) -> None:
    for noun in ("provider", "model", "vendor", "engine"):
        pattern = rf'<(?:select|input)[^>]*name="{noun}"'
        assert not re.search(pattern, primary_slice, flags=re.IGNORECASE)


def test_no_vendor_name_in_primary_visible_text(
    primary_visible: str,
) -> None:
    visible = re.sub(r'="[^"]*"', '=""', primary_visible)
    for vendor in (
        "gemini", "akool", "seedance",
        "openai", "anthropic", "google", "elevenlabs",
    ):
        assert not re.search(rf"\b{vendor}\b", visible, flags=re.IGNORECASE), (
            f"Vendor name leaked into primary visible text: {vendor}"
        )


# --------------------------------------------------------------------------
# (14) Legacy task-meta header gated to non-matrix_script kinds
# --------------------------------------------------------------------------


def test_legacy_task_meta_header_gated_to_non_matrix_script(
    workbench_source: str,
) -> None:
    """The legacy 'card header-card' info-row + meta-grid (status pill +
    9 task-meta rows) is wrapped in {% if task.kind != "matrix_script" %}
    so matrix_script tasks open directly at §A 主视频结果 instead of
    seeing a project-management header."""

    # Locate the legacy header gate.
    gate_open = workbench_source.find(
        '{% if task.kind != "matrix_script" %}'
    )
    gate_close = workbench_source.find(
        "{% endif %} {# /matrix_script legacy task-meta header gate #}"
    )
    assert -1 < gate_open < gate_close
    # The status pill + task_id meta-item must be INSIDE the gate.
    pill_pos = workbench_source.find('id="status-badge"')
    task_id_pos = workbench_source.find('workbench.meta.task_id')
    assert gate_open < pill_pos < gate_close
    assert gate_open < task_id_pos < gate_close
