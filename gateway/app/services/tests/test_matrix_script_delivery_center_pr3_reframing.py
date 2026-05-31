"""Tests for PR-3 · Delivery Center result + publish reframing.

Authority: approved design plan §7 + Mission §C (six sections in
canonical order ① 交付结果介绍 / ② 主视频 / ③ 必需交付物 /
④ 可选交付物 / ⑤ 发布设置 / ⑥ 发布回填) + product decision #3
(发布平台 uses <datalist> with 7 suggestions; free-text allowed; no
closed enum on contract layer).
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE = _REPO_ROOT / "gateway" / "app" / "templates" / "task_publish_hub.html"


def _read() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Mission §C section numbering
# ---------------------------------------------------------------------------


def test_section_index_one_introduction_present() -> None:
    """Mission §C ① 交付结果介绍 — the header card is relabelled."""

    source = _read()
    assert "① · 介绍" in source
    assert "交付结果介绍 · " in source  # header title prefix


def test_section_index_two_main_video_present() -> None:
    source = _read()
    assert "② · 主视频" in source
    # And the old "A · 主交付" label is retired.
    assert "A · 主交付" not in source


def test_section_index_three_required_deliverables_present() -> None:
    source = _read()
    assert "③ · 必需" in source
    assert "B · 必交付" not in source


def test_section_index_four_optional_deliverables_present() -> None:
    source = _read()
    assert "④ · 可选" in source
    assert "④ · 文案包" in source
    # Old C/D labels retired
    assert ">C · 可选<" not in source
    assert ">D · 文案<" not in source


def test_section_index_five_publish_settings_present() -> None:
    source = _read()
    assert "⑤ · 发布" in source
    assert "data-role=\"matrix-script-block-publish-settings\"" in source


def test_section_index_six_backfill_present() -> None:
    source = _read()
    assert "⑥ · 回填" in source
    # And the old "E · 发布反馈" op-section-index label is retired
    # from the visible span. (The phrase may survive in Jinja comments
    # documenting the rename — that's acceptable architect context.)
    assert '<span class="op-section-index op-section-index--violet">E · 发布反馈</span>' not in source


def test_section_index_six_archive_alias_present() -> None:
    """Block F 迭代归档 stays as a sub-section of ⑥, relabelled."""

    source = _read()
    assert "⑥ · 归档" in source
    assert "F · 迭代" not in source


# ---------------------------------------------------------------------------
# ⑤ 发布设置 form — closed key set, datalist with 7 suggestions
# ---------------------------------------------------------------------------


def test_publish_settings_form_present_with_closure_endpoint() -> None:
    source = _read()
    assert 'data-role="ms-dc-publish-settings-form"' in source
    # Posts to the existing closure events endpoint — no new endpoint.
    assert 'action="/api/matrix-script/closures/{{ task.task_id }}/events"' in source


def test_publish_settings_form_writes_operator_publish_event_kind() -> None:
    """The closed event_kind=operator_publish is reused; no enum widening."""

    source = _read()
    assert 'value="operator_publish"' in source
    assert 'data-role="ms-dc-publish-settings-event-kind"' in source


def test_publish_settings_form_carries_all_six_fields() -> None:
    """Mission §C ⑤ requires: platform / account / title / caption /
    tags / scheduled time."""

    source = _read()
    for field_role in (
        "ms-dc-publish-settings-platform",
        "ms-dc-publish-settings-account",
        "ms-dc-publish-settings-title-input",
        "ms-dc-publish-settings-caption",
        "ms-dc-publish-settings-tags",
        "ms-dc-publish-settings-scheduled",
    ):
        assert f'data-role="{field_role}"' in source


def test_publish_settings_form_has_two_main_actions() -> None:
    """标记为已发布 (submit) + 跳过发布 (secondary). Mission §C."""

    source = _read()
    assert 'data-role="ms-dc-publish-settings-submit"' in source
    assert 'data-role="ms-dc-publish-settings-skip"' in source
    assert "标记为已发布" in source
    assert "跳过发布" in source


def test_publish_platform_datalist_carries_seven_product_approved_suggestions() -> None:
    """Approved product decision #3: TikTok / YouTube Shorts /
    Instagram Reels / 抖音 / 视频号 / 小红书 / 快手. Free-text allowed.
    The datalist is a UI suggestion; the field is NOT a closed enum on
    the contract layer."""

    source = _read()
    assert 'list="ms-publish-platform-suggestions"' in source
    assert 'id="ms-publish-platform-suggestions"' in source
    assert 'data-role="ms-dc-publish-settings-platform-suggestions"' in source
    for platform in (
        "TikTok",
        "YouTube Shorts",
        "Instagram Reels",
        "抖音",
        "视频号",
        "小红书",
        "快手",
    ):
        assert f'<option value="{platform}"></option>' in source


def test_publish_settings_form_no_outbound_publish_promise() -> None:
    """The honesty note makes clear the system does NOT publish
    externally; the form just records an in-system event."""

    source = _read()
    assert 'data-role="ms-dc-publish-settings-honesty-note"' in source
    assert "本表单不直接对外发布" in source


def test_publish_settings_form_no_provider_or_model_selector() -> None:
    """validator R3 preserved across the new form."""

    source = _read()
    publish_settings_open = source.find('data-role="matrix-script-block-publish-settings"')
    publish_settings_end = source.find(
        '<div class="op-card op-card--accent-violet" data-role="matrix-script-block-e-publish-feedback"',
        publish_settings_open,
    )
    block_source = (
        source[publish_settings_open:publish_settings_end]
        if publish_settings_end != -1
        else source[publish_settings_open:publish_settings_open + 6000]
    )
    for forbidden in (
        "vendor_id",
        "model_id",
        "provider_id",
        "engine_id",
        "select provider",
        "select model",
    ):
        assert forbidden not in block_source.lower() if isinstance(forbidden, str) else True


def test_publish_settings_carries_redesign_wave_attribute() -> None:
    source = _read()
    assert 'data-redesign-wave="2026-05-28-pr3"' in source


# ---------------------------------------------------------------------------
# Ordering: ⑤ 发布设置 comes BEFORE ⑥ 发布回填 in template source
# ---------------------------------------------------------------------------


def test_publish_settings_block_appears_before_publish_feedback_block() -> None:
    source = _read()
    settings = source.find('data-role="matrix-script-block-publish-settings"')
    feedback = source.find('data-role="matrix-script-block-e-publish-feedback"')
    assert settings != -1 < feedback
    assert settings < feedback
