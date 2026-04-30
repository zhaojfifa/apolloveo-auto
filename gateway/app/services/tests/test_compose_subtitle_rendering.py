from pathlib import Path

from gateway.app.services.compose_subtitle_rendering import (
    compose_subtitle_vf,
    optimize_hot_follow_subtitle_layout_srt,
    subtitle_render_signature,
)


def test_subtitle_render_signature_uses_compact_vi_profile_policy():
    signature = subtitle_render_signature(target_lang="vi", cleanup_mode="none")

    assert "profile=hot_follow_compact_default" in signature
    assert "lang=vi" in signature
    assert "size=13.2" in signature
    assert "margin_v=18" in signature
    assert "line_width=22.00" in signature
    assert "safe_margin=preserve_existing_bottom_safe_area" in signature


def test_compose_subtitle_vf_uses_compact_myanmar_force_style_policy(tmp_path):
    subtitle_path = tmp_path / "mm.srt"
    subtitle_path.write_text("1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n", encoding="utf-8")

    vf = compose_subtitle_vf(subtitle_path, tmp_path, "none", "my")

    assert "Alignment=2" in vf
    assert "FontSize=14.0" in vf
    assert "Spacing=0.0" in vf
    assert "WrapStyle=1" in vf


def test_compact_profile_keeps_chinese_wrapping_readable():
    srt_text = "1\n00:00:00,000 --> 00:00:02,000\n这是一个用于验证默认字幕更紧凑但仍可读的中文样例\n"

    result = optimize_hot_follow_subtitle_layout_srt(srt_text, "zh")

    body_lines = [
        line
        for line in result.splitlines()
        if line and not line.isdigit() and "-->" not in line
    ]
    assert 1 <= len(body_lines) <= 2
    assert "这是" in "".join(body_lines)


def test_optimize_hot_follow_subtitle_layout_srt_preserves_srt_shape():
    srt_text = "1\n00:00:00,000 --> 00:00:02,000\nHello subtitle layout helper\n"

    result = optimize_hot_follow_subtitle_layout_srt(srt_text, "en")

    assert result.startswith("1\n00:00:00,000 --> 00:00:02,000\n")
    assert result.endswith("\n")
