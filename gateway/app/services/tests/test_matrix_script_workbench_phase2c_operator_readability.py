"""Phase 2C · Matrix Script operator-readability refinement tests.

Authority: docs/design/matrix_script_phase2c_operator_readability_plan_v1.md;
user mission [SYSTEM OVERRIDE] 2026-05-30 (Matrix Script Phase 2C Operator
Readability Implementer brief) under Codex CONDITIONAL GO.

Phase 2C is a copy / template-layout / presenter-shaping refinement ONLY.
No backend capability, worker, contract, schema, packet, closed enum,
runtime, or route change. These source-level assertions lock the
operator-readability shape so a future drift back into a backend / status
placeholder surface is caught.

Twenty assertions:

  1. ONE top-level capability banner present (matrix-script-capability-banner).
  2. Capability banner copy is operator-language (no forbidden vocab).
  3. §B selling-points line no longer leaks `content_structure`.
  4. §B exposes operator labels 目标受众 / 语气 / 时长.
  5. §C status pill no longer reads `后台待接入`.
  6. §C honest disclaimer no longer leaks `后端`.
  7. §D renders a single operator-facing intent panel.
  8. §D preserves the three back-compat slot anchors (bg / broll / product).
  9. §D differentiates the three disabled-button tooltips.
 10. §E preview placeholder demoted to a chip (试听能力接入后开放).
 11. §E primary copy no longer leaks VoiceTrans / 供应方 / 桥接.
 12. §F subtitle / BGM controls are selectable <select> elements.
 13. §F selects carry NO name= attribute (no submitted truth).
 14. §F preview chip present (预览生成后生效).
 15. §G every version card carries 适合哪些账号 / 场景 (audience).
 16. §G recommended marker (⭐) appears exactly once (V1 only).
 17. §G V2 / V3 carry a 备选 alt-marker; status reads 待生成 (not 当前占位).
 18. Forbidden backend vocab absent from primary visible slice.
 19. Delivery Center §6 metrics placeholder rewritten to future-metrics copy.
 20. New Task Card 4 options carry operator usage hints (推荐：…).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_WORKBENCH = _REPO_ROOT / "gateway" / "app" / "templates" / "task_workbench.html"
_NEW_TASK = _REPO_ROOT / "gateway" / "app" / "templates" / "matrix_script_new.html"
_PUBLISH_HUB = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


_FORBIDDEN_VOCAB = (
    "content_structure",
    "后端",
    "backend",
    "compose",
    "producer",
    "桥接",
    "provider",
    "vendor",
    "engine",
    "azure",
    "akool",
    "seedance",
    "openai",
    "anthropic",
    "elevenlabs",
    "VoiceTrans",
)


@pytest.fixture(scope="module")
def workbench_source() -> str:
    return _WORKBENCH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def new_task_source() -> str:
    return _NEW_TASK.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def publish_hub_source() -> str:
    return _PUBLISH_HUB.read_text(encoding="utf-8")


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
# (1) (2) Capability banner
# --------------------------------------------------------------------------


def test_capability_banner_present(primary_slice: str) -> None:
    assert 'data-role="matrix-script-capability-banner"' in primary_slice
    assert 'data-role="matrix-script-capability-banner-body"' in primary_slice
    # Exactly one top-level banner.
    assert primary_slice.count('data-role="matrix-script-capability-banner"') == 1


def test_capability_banner_copy_is_operator_language(primary_visible: str) -> None:
    body = re.search(
        r'data-role="matrix-script-capability-banner-body"[^>]*>([^<]*)<',
        primary_visible,
    )
    assert body is not None
    text = body.group(1)
    assert "脚本" in text or "视频" in text
    for noun in _FORBIDDEN_VOCAB:
        assert noun.lower() not in text.lower(), f"banner leaks {noun}"


# --------------------------------------------------------------------------
# (3) (4) §B 脚本理解
# --------------------------------------------------------------------------


def test_section_b_no_content_structure_leak(primary_visible: str) -> None:
    selling = re.search(
        r'data-role="ms-section-script-understanding-selling-points".*?</div>',
        primary_visible,
        flags=re.DOTALL,
    )
    assert selling is not None
    assert "content_structure" not in selling.group(0)


def test_section_b_exposes_audience_tone_duration(primary_slice: str) -> None:
    assert 'data-role="ms-section-script-understanding-target-audience"' in primary_slice
    assert 'data-role="ms-section-script-understanding-tone"' in primary_slice
    assert 'data-role="ms-section-script-understanding-duration"' in primary_slice
    for label in ("目标受众", "语气", "时长"):
        assert label in primary_slice


# --------------------------------------------------------------------------
# (5) (6) §C 视频生成计划
# --------------------------------------------------------------------------


def test_section_c_status_pill_not_backstage(primary_visible: str) -> None:
    pill = re.search(
        r'data-role="ms-section-generation-plan-status-pill"[^>]*>([^<]*)<',
        primary_visible,
    )
    assert pill is not None
    assert "后台待接入" not in pill.group(1)
    assert "后端" not in pill.group(1)


def test_section_c_disclaimer_no_backend_leak(primary_visible: str) -> None:
    disclaimer = re.search(
        r'data-role="ms-section-generation-plan-honest-disclaimer"[^>]*>(.*?)</p>',
        primary_visible,
        flags=re.DOTALL,
    )
    assert disclaimer is not None
    assert "后端" not in disclaimer.group(1)
    # Honesty is preserved.
    assert "占位草案" in disclaimer.group(1)


# --------------------------------------------------------------------------
# (7) (8) (9) §D 画面与素材
# --------------------------------------------------------------------------


def test_section_d_intent_panel_present(primary_slice: str) -> None:
    assert 'data-role="ms-section-visual-materials-intent-panel"' in primary_slice


def test_section_d_preserves_slot_anchors(primary_slice: str) -> None:
    for anchor in (
        "ms-section-visual-materials-bg-slot",
        "ms-section-visual-materials-broll-slot",
        "ms-section-visual-materials-product-slot",
    ):
        assert f'data-role="{anchor}"' in primary_slice


def test_section_d_differentiated_tooltips(primary_slice: str) -> None:
    assert 'title="背景候选接入后开放替换。"' in primary_slice
    assert 'title="B-Roll 候选接入后开放替换。"' in primary_slice
    assert 'title="素材匹配能力接入后开放。"' in primary_slice


# --------------------------------------------------------------------------
# (10) (11) §E 角色与声音
# --------------------------------------------------------------------------


def test_section_e_preview_demoted_to_chip(primary_slice: str) -> None:
    label = re.search(
        r'data-role="ms-section-role-voice-preview-label"[^>]*>([^<]*)<',
        primary_slice,
    )
    assert label is not None
    assert "试听能力接入后开放" in label.group(1)


def test_section_e_no_voicetrans_leak_in_primary(primary_visible: str) -> None:
    # Isolate §E card text in the rendered-visible slice.
    e_start = primary_visible.find('data-role="matrix-script-section-role-voice"')
    e_end = primary_visible.find(
        'data-role="matrix-script-section-subtitle-music"', e_start
    )
    assert e_start != -1 and e_end != -1
    e_text = primary_visible[e_start:e_end]
    for noun in ("VoiceTrans", "供应方", "桥接", "供应商"):
        assert noun not in e_text, f"§E leaks {noun}"


# --------------------------------------------------------------------------
# (12) (13) (14) §F 字幕与音乐
# --------------------------------------------------------------------------


def test_section_f_controls_are_selectable(primary_slice: str) -> None:
    for anchor in (
        "ms-section-subtitle-music-font-select",
        "ms-section-subtitle-music-position-select",
        "ms-section-subtitle-music-bgm-mood-select",
        "ms-section-subtitle-music-bgm-volume-select",
    ):
        assert f'data-role="{anchor}"' in primary_slice
        # Each anchor lives on a <select>.
        m = re.search(rf'<select[^>]*data-role="{anchor}"', primary_slice)
        assert m is not None, f"{anchor} is not a <select>"


def test_section_f_selects_have_no_name_attr(primary_slice: str) -> None:
    f_start = primary_slice.find('data-role="matrix-script-section-subtitle-music"')
    f_end = primary_slice.find(
        'data-role="matrix-script-section-optional-variants"', f_start
    )
    f_text = primary_slice[f_start:f_end]
    # No <select name="..."> inside §F — UI-only, nothing submitted.
    assert not re.search(r"<select[^>]*\bname=", f_text)


def test_section_f_preview_chip_present(primary_slice: str) -> None:
    chip = re.search(
        r'data-role="ms-section-subtitle-music-preview-chip"[^>]*>([^<]*)<',
        primary_slice,
    )
    assert chip is not None
    assert "预览生成后生效" in chip.group(1)


# --------------------------------------------------------------------------
# (15) (16) (17) §G 视频变体
# --------------------------------------------------------------------------


def test_section_g_audience_column_on_every_card(primary_slice: str) -> None:
    # Three version cards → three audience meta-items.
    assert (
        primary_slice.count('data-role="ms-section-video-versions-card-audience"') == 3
    )
    assert primary_slice.count("适合哪些账号 / 场景") == 3


def test_section_g_recommended_marker_exactly_once(primary_slice: str) -> None:
    assert (
        primary_slice.count(
            'data-role="ms-section-video-versions-card-recommended-marker"'
        )
        == 1
    )


def test_section_g_alt_marker_and_state_pill(primary_slice: str) -> None:
    # V2 + V3 carry the 备选 alt-marker.
    assert (
        primary_slice.count('data-role="ms-section-video-versions-card-alt-marker"')
        == 2
    )
    # Status text no longer reads the placeholder-y 当前占位 inside cards.
    statuses = re.findall(
        r'data-role="ms-section-video-versions-card-status"[^>]*>([^<]*)<',
        primary_slice,
    )
    assert len(statuses) == 3
    for s in statuses:
        assert s.strip() == "待生成"


# --------------------------------------------------------------------------
# (18) Forbidden vocab absent from primary visible slice
# --------------------------------------------------------------------------


def test_no_forbidden_vocab_in_primary_visible(primary_visible: str) -> None:
    # Strip attribute values so data-status-code values (which legitimately
    # carry closed status codes containing e.g. "compose" / "voicetrans")
    # do not false-positive. Operator-visible copy is what matters.
    no_attrs = re.sub(r'="[^"]*"', '=""', primary_visible)
    for noun in _FORBIDDEN_VOCAB:
        assert noun.lower() not in no_attrs.lower(), (
            f"forbidden vocab '{noun}' visible in §B–§I primary copy"
        )


# --------------------------------------------------------------------------
# (19) Delivery Center §6 metrics placeholder
# --------------------------------------------------------------------------


def test_delivery_metrics_placeholder_rewritten(publish_hub_source: str) -> None:
    placeholder = re.search(
        r'data-role="ms-dc-section-publish-backfill-metrics-placeholder"[^>]*>([^<]*)<',
        publish_hub_source,
    )
    assert placeholder is not None
    text = placeholder.group(1)
    assert "指标投射尚未上线" not in text
    assert "完播率" in text


# --------------------------------------------------------------------------
# (20) New Task Card 4 usage hints
# --------------------------------------------------------------------------


def test_new_task_card4_usage_hints(new_task_source: str) -> None:
    assert "（推荐：纯 B-Roll + 字幕）" in new_task_source
    assert "（推荐：讲解型短视频）" in new_task_source
    assert "（推荐：本地化投放）" in new_task_source
    assert "（推荐：生活种草）" in new_task_source
    assert "（推荐：测评说明）" in new_task_source
    assert "大字高亮（推荐：短视频首屏）" in new_task_source
