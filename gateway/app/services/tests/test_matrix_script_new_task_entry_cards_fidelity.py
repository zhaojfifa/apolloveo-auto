"""New Task entry-card fidelity tests (2026-05-30b).

Authority: user mission [SYSTEM OVERRIDE] 2026-05-30 (Matrix Script
New Task Entry Card Fidelity Fixer). Locks the four new entry cards
the Phase 2B fidelity fix added per the Phase 1 mock §① and the
presenter alignment spec §5.1.

Twelve mission assertions plus a thirteenth POST-compatibility audit.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[4]
_NEW_TASK = _REPO_ROOT / "gateway" / "app" / "templates" / "matrix_script_new.html"


@pytest.fixture(scope="module")
def source() -> str:
    return _NEW_TASK.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# (1) - (4) Four new entry cards present
# --------------------------------------------------------------------------


CARD_ANCHORS = [
    ("Card 2 素材",      "ms-new-card-product-material",     "产品 / 素材"),
    ("Card 3 目标",      "ms-new-card-target-aspect-language","目标 · 画幅 · 语言"),
    ("Card 4 角色",      "ms-new-card-role-voice-subtitle",  "角色 · 声音 · 字幕"),
    ("Card 5 变体",      "ms-new-card-variant-strategy",     "变体策略"),
]


@pytest.mark.parametrize("label,data_role,title", CARD_ANCHORS)
def test_new_task_card_present(
    source: str, label: str, data_role: str, title: str
) -> None:
    """Each of the four new entry cards is present with the expected
    data-role anchor AND operator-language title."""

    assert f'data-role="{data_role}"' in source, f"{label} anchor missing"
    # The card title appears inside <h2 class="op-section-title">…</h2>.
    pattern = rf'data-role="{re.escape(data_role)}".*?<h2 class="op-section-title">([^<]+)</h2>'
    block = re.search(pattern, source, flags=re.DOTALL)
    assert block is not None, f"{label} card title block not found"
    assert block.group(1).strip() == title, (
        f"{label} title mismatch: expected {title!r}, got {block.group(1)!r}"
    )


def test_cards_render_in_design_order(source: str) -> None:
    """Cards render in operator scan order: Card 1 (脚本) is preserved
    above; Cards 2 / 3 / 4 / 5 follow in order; CTA after."""

    positions = [
        source.find(f'data-role="{role}"')
        for _, role, _ in CARD_ANCHORS
    ]
    assert all(p > 0 for p in positions), f"Card anchor missing: {positions}"
    assert positions == sorted(positions), (
        f"Cards out of order: {positions}"
    )
    # Card 1 (脚本源) is BEFORE Card 2 (素材).
    card1 = source.find('data-role="ms-new-card-source"')
    card2 = source.find('data-role="ms-new-card-product-material"')
    assert -1 < card1 < card2


# --------------------------------------------------------------------------
# (5) Legacy "任务基本信息" card title NOT in primary UI
# --------------------------------------------------------------------------


def test_legacy_task_meta_card_title_absent(source: str) -> None:
    """Legacy `任务基本信息` card title and `ms-new-card-task-meta`
    data-role are gone from operator-visible primary copy. The phrase
    may survive only inside Jinja `{# … #}` comments."""

    # Strip Jinja comments before the assertion.
    no_comments = re.sub(r"{#.*?#}", "", source, flags=re.DOTALL)
    assert '<h2 class="op-section-title">任务基本信息</h2>' not in no_comments
    assert 'data-role="ms-new-card-task-meta"' not in no_comments
    # And the substring 任务基本信息 must not appear in operator copy
    # outside of Jinja comments.
    assert "任务基本信息" not in no_comments


# --------------------------------------------------------------------------
# (6) Primary CTA remains 生成视频方案
# --------------------------------------------------------------------------


def test_primary_cta_is_generate_video_plan(source: str) -> None:
    btn = re.search(
        r'<button[^>]*data-role="ms-new-submit"[^>]*>(.*?)</button>',
        source,
        flags=re.DOTALL,
    )
    assert btn is not None
    inner = btn.group(1).strip()
    assert "生成视频方案" in inner
    assert "创建任务" not in inner
    assert "创建并进入工作台" not in inner


# --------------------------------------------------------------------------
# (7) source_script_ref hidden in operator mode
# --------------------------------------------------------------------------


def test_source_script_ref_hidden_in_operator_mode(source: str) -> None:
    """The opaque `source_script_ref` field is rendered as a hidden
    input in operator mode (PR-1 gating discipline); architect controls
    only appear under `?technical=1`."""

    # Hidden input present.
    assert re.search(
        r'<input[^>]*name="source_script_ref"[^>]*type="hidden"',
        source,
    ) is not None or re.search(
        r'<input[^>]*type="hidden"[^>]*name="source_script_ref"',
        source,
    ) is not None


# --------------------------------------------------------------------------
# (8) Technical mode exposes architect source-ref controls
# --------------------------------------------------------------------------


def test_technical_mode_exposes_architect_controls(source: str) -> None:
    """The technical-mode gate (`?technical=1`) reveals the mint button +
    technical reference fold; the gating Jinja remains intact."""

    assert "technical_mode" in source
    assert 'data-role="ms-new-mint-button"' in source
    assert 'data-role="ms-new-technical-ref"' in source or 'data-role="ms-new-route-map-technical"' in source


# --------------------------------------------------------------------------
# (9) No VoiceTrans iframe / raw VoiceTrans form
# --------------------------------------------------------------------------


def test_no_voicetrans_iframe_or_raw_form(source: str) -> None:
    assert "<iframe" not in source
    assert 'action="/api/voice-tool' not in source
    assert 'action="/voice-tool' not in source
    # The future-provider label is present as a tech-note disclaimer.
    assert 'data-role="ms-new-voicetrans-future-provider-note"' in source


# --------------------------------------------------------------------------
# (10) No provider / model / vendor / engine form controls
# --------------------------------------------------------------------------


def test_no_provider_model_vendor_engine_controls(source: str) -> None:
    for noun in ("provider", "model", "vendor", "engine"):
        pattern = rf'<(?:select|input)[^>]*name="{noun}"'
        assert not re.search(pattern, source, flags=re.IGNORECASE), (
            f"Forbidden form control found: name='{noun}'"
        )
    # Strip non-rendered Jinja + comments; then check vendor names in
    # operator-visible text. Architect / engineer technical fold may
    # still mention these as labels.
    no_jinja = re.sub(r"{%.*?%}", "", re.sub(r"{#.*?#}", "", source, flags=re.DOTALL), flags=re.DOTALL)
    for vendor in ("azure", "akool", "seedance", "openai", "anthropic", "elevenlabs"):
        assert not re.search(rf"\b{vendor}\b", no_jinja, flags=re.IGNORECASE), (
            f"Vendor name leaked into operator copy: {vendor}"
        )


# --------------------------------------------------------------------------
# (11) No fake media / publish URL
# --------------------------------------------------------------------------


def test_no_fake_media_or_publish_url(source: str) -> None:
    for fake in (
        ".mp4", ".m3u8", ".webm",
        "youtu.be/", "youtube.com/watch",
        "tiktok.com/", "douyin.com/",
        "instagram.com/p/",
    ):
        assert fake not in source, f"Fake media / URL leaked: {fake}"


# --------------------------------------------------------------------------
# (12) Existing POST-compatible field names preserved
# --------------------------------------------------------------------------


REQUIRED_POST_FIELDS = [
    "topic",
    "source_language",
    "target_language",
    "target_platform",
    "variation_target_count",
    "audience_hint",
    "tone_hint",
    "length_hint",
    "product_ref",
    "operator_notes",
    "source_script_ref",
    "existing_source_script_ref",
    "script_body",
]


@pytest.mark.parametrize("field", REQUIRED_POST_FIELDS)
def test_post_field_preserved(source: str, field: str) -> None:
    """The fidelity fix MUST preserve every existing POST-required
    name= attribute so `build_matrix_script_task_payload` continues to
    receive the same shape."""

    assert f'name="{field}"' in source, (
        f"POST-required field name=\"{field}\" was lost during the fidelity fix"
    )


def test_form_action_path_preserved(source: str) -> None:
    """The form action remains the existing matrix_script-new POST path
    (no new endpoint introduced)."""

    form_open = re.search(
        r'<form[^>]*data-role="matrix-script-create-form"[^>]*>',
        source,
    )
    assert form_open is not None
    # The form is multipart (file upload supported) and posts to
    # /tasks/matrix-script/new (the existing safe path).
    assert "/tasks/matrix-script/new" in form_open.group(0) or "/tasks/matrix-script/new" in source


# --------------------------------------------------------------------------
# Bonus: card subfield expectations per mission
# --------------------------------------------------------------------------


def test_card2_product_material_has_required_subfields(source: str) -> None:
    card_open = source.find('data-role="ms-new-card-product-material"')
    card_close = source.find('data-role="ms-new-card-target-aspect-language"', card_open)
    body = source[card_open:card_close]
    # 产品名称 / SKU / 资料链接 — single input.
    assert 'name="product_ref"' in body
    # 上传商品图 / 商品视频片段 placeholder.
    assert 'data-role="ms-new-product-material-upload-slot"' in body
    assert 'data-status-code="materials_pending_upstream"' in body
    # 素材说明 textarea.
    assert 'data-role="ms-new-product-material-description"' in body
    # 背景 / B-Roll 偏好 selector.
    assert 'data-role="ms-new-broll-preference"' in body
    assert "这里先填写产品与素材说明，作为系统生成视频方案和匹配素材的依据" in body
    assert "进入 Workbench 后，可按镜头补充或替换素材" in body
    assert "素材上传入口将逐步接入；当前可以先使用说明和示例素材完成预览" in body
    assert "后台待接入" not in body
    assert "worker 尚未接入" not in body


def test_card3_target_aspect_language_has_required_subfields(source: str) -> None:
    card_open = source.find('data-role="ms-new-card-target-aspect-language"')
    card_close = source.find('data-role="ms-new-card-role-voice-subtitle"', card_open)
    body = source[card_open:card_close]
    assert 'name="topic"' in body
    assert 'name="target_platform"' in body
    assert 'data-role="ms-new-platform-suggestions"' in body
    assert 'data-role="ms-new-aspect-ratio-group"' in body
    assert 'data-role="ms-new-aspect-ratio-option"' in body
    assert 'name="source_language"' in body
    assert 'name="target_language"' in body
    assert 'name="length_hint"' in body
    assert 'name="audience_hint"' in body


def test_card4_role_voice_subtitle_has_required_subfields(source: str) -> None:
    card_open = source.find('data-role="ms-new-card-role-voice-subtitle"')
    card_close = source.find('data-role="ms-new-card-variant-strategy"', card_open)
    body = source[card_open:card_close]
    assert 'data-role="ms-new-role-preference"' in body
    assert 'data-role="ms-new-voice-preference"' in body
    assert 'data-role="ms-new-subtitle-style"' in body
    assert 'name="tone_hint"' in body
    assert 'data-role="ms-new-voicetrans-future-provider-note"' in body


def test_card5_variant_strategy_has_required_subfields(source: str) -> None:
    card_open = source.find('data-role="ms-new-card-variant-strategy"')
    # Card 5 is the last card before </form>; bound by the form-close.
    card_close = source.find('</form>', card_open)
    body = source[card_open:card_close]
    assert 'name="variation_target_count"' in body
    assert 'data-role="ms-new-variant-axes-group"' in body
    # Eight axis checkboxes per mission §6.
    axes = re.findall(r'data-role="ms-new-variant-axis"', body)
    assert len(axes) == 8, f"Expected 8 variant axes, got {len(axes)}"
    # operator_notes textarea sits inside Card 5 (operator footer).
    assert 'name="operator_notes"' in body
