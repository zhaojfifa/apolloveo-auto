"""Unit tests for M-03 subtitle_builder.

Plain-text SRT path is the Hot Follow frozen rule — do NOT relax it without
a contract change. ASS output remains a styled subtitle stream.

Donor commit pin: 62b6da0 (W1).
"""
from __future__ import annotations

from gateway.app.services.media import subtitle_builder as sb


def test_srt_ts_zero_pads():
    assert sb._srt_ts(0) == "00:00:00,000"
    assert sb._srt_ts(3.5) == "00:00:03,500"
    assert sb._srt_ts(3661.125) == "01:01:01,125"


def test_ass_ts_centiseconds():
    assert sb._ass_ts(0) == "0:00:00.00"
    assert sb._ass_ts(3.5) == "0:00:03.50"
    # Banker's rounding on .5 → centiseconds == 12 (366112), not 13.
    assert sb._ass_ts(3661.125) == "1:01:01.12"


def test_split_max_two_lines_short_text_unchanged():
    assert sb._split_max_two_lines("short") == "short"
    assert sb._split_max_two_lines("") == ""
    assert sb._split_max_two_lines(None) == ""  # type: ignore[arg-type]


def test_split_max_two_lines_breaks_at_space():
    txt = "this is a fairly long sentence that should split"
    out = sb._split_max_two_lines(txt, max_chars_per_line=24)
    assert "\\N" in out


def test_ass_escape_text_escapes_braces_and_backslash():
    assert sb._ass_escape_text("a{b}c") == r"a\{b\}c"
    assert sb._ass_escape_text("a\\b") == r"a\\b"
    assert sb._ass_escape_text("") == ""


def test_resolve_ass_font_env_override(monkeypatch):
    monkeypatch.setenv("ASS_FONT_NAME", "MyFont")
    monkeypatch.setenv("ASS_FONTS_DIR", "")
    name, path, fallback = sb.resolve_ass_font()
    assert name == "MyFont"
    assert path is None
    assert fallback is False


def test_build_srt_skips_zero_index_and_uses_translation_final():
    rows = [
        {"index": 0, "start": 0.0, "end": 1.0, "translated": "skipped"},
        {"index": 1, "start": 1.0, "end": 2.0, "translation_subtitle_final": "hello"},
        {"index": 2, "start": 2.0, "end": 2.5, "translated": "world"},
    ]
    out = sb.build_srt_from_segments(rows)
    assert "skipped" not in out
    assert "hello" in out
    assert "world" in out
    # Plain-text SRT: numeric index lines + timestamp arrow + text. No HTML/style tags.
    assert "-->" in out
    assert "<font" not in out and "<i>" not in out and "<b>" not in out


def test_build_srt_falls_back_to_untranslated_marker():
    rows = [{"index": 1, "start": 0.0, "end": 1.0}]
    out = sb.build_srt_from_segments(rows)
    assert "[UNTRANSLATED]" in out


def test_build_srt_end_clamped_above_start():
    rows = [{"index": 1, "start": 5.0, "end": 5.0, "translated": "x"}]
    out = sb.build_srt_from_segments(rows)
    # end is clamped to start + 0.1s
    assert "00:00:05,100" in out


def test_build_ass_contains_header_and_dialogue():
    rows = [
        {"index": 1, "start": 0.0, "end": 1.5, "translated": "hi {there}"},
    ]
    out = sb.build_ass_from_segments(rows, title="Apollo Test", font_name="MyFont")
    assert "[Script Info]" in out
    assert "Title: Apollo Test" in out
    assert "MyFont" in out
    assert "Dialogue:" in out
    # Brace escape applied
    assert r"\{there\}" in out


def test_build_ass_default_title_is_apollo_branded():
    out = sb.build_ass_from_segments([], font_name="X")
    # Donor said "SwiftCraft Localization"; absorption rebrands to Apollo.
    assert "ApolloVeo" in out
    assert "SwiftCraft" not in out
