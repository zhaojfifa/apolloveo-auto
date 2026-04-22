from pathlib import Path

from gateway.app.services.steps_text_support import (
    parse_srt_cues,
    resolve_mm_txt_text,
    srt_to_txt,
    subtitle_result_contract,
)


def test_subtitle_result_contract_defaults_complete_flag():
    origin, normalized, target, translation_qa = subtitle_result_contract(
        {
            "origin_srt": "origin",
            "mm_srt": "target",
            "translation_incomplete": False,
        }
    )

    assert origin == "origin"
    assert normalized == "origin"
    assert target == "target"
    assert translation_qa["complete"] is True


def test_srt_to_txt_and_parse_srt_cues_keep_current_shape():
    srt_text = "1\n00:00:00,000 --> 00:00:02,000\nhello\n\n2\n00:00:02,000 --> 00:00:04,000\nworld\n"

    assert srt_to_txt(srt_text) == "hello\nworld\n"

    cues = parse_srt_cues(srt_text)
    assert cues[0]["index"] == 1
    assert cues[0]["start"] == 0.0
    assert cues[0]["end"] == 2.0
    assert cues[1]["text"] == "world"


def test_resolve_mm_txt_text_falls_back_to_srt_when_mm_txt_missing():
    resolved, used_fallback, fallback_source = resolve_mm_txt_text(
        mm_txt_text="",
        override_text="",
        edited_text="",
        mm_srt_text="1\n00:00:00,000 --> 00:00:02,000\nfallback text\n",
    )

    assert resolved == "fallback text"
    assert used_fallback is True
    assert fallback_source == "mm_srt"


def test_ensure_txt_from_srt_writes_current_plain_text(tmp_path: Path):
    from gateway.app.services.steps_text_support import ensure_txt_from_srt

    src = tmp_path / "subs.srt"
    dst = tmp_path / "subs.txt"
    src.write_text("1\n00:00:00,000 --> 00:00:02,000\nhello there\n", encoding="utf-8")

    ensure_txt_from_srt(dst, src)

    assert dst.read_text(encoding="utf-8") == "hello there\n"
