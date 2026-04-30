"""Guard-compat tests for M-05 zh_normalize.

Acceptance: `normalize_zh_text` must not break Apollo's existing
`gateway.app.services.dub_text_guard.clean_and_analyze_dub_text` semantics.

Donor commit pin: 62b6da0 (W1).
"""
from __future__ import annotations

from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
from gateway.app.services.media.zh_normalize import normalize_zh_text


def test_empty_input_returns_empty():
    assert normalize_zh_text("") == ""
    assert normalize_zh_text(None) == ""  # type: ignore[arg-type]


def test_trad_to_simp_mapping_applied():
    # 飛機 -> 飞机, 視訊 -> 视讯, 國 -> 国
    assert normalize_zh_text("\u98db\u6a5f") == "\u98de\u673a"
    assert normalize_zh_text("\u8996\u8a0a") == "\u89c6\u8baf"
    assert normalize_zh_text("\u570b") == "\u56fd"


def test_inch_and_cm_normalization():
    # 20吋 -> 20寸 ; 30 cm -> 30厘米
    assert normalize_zh_text("20\u540b") == "20\u5bf8"
    assert normalize_zh_text("30 cm") == "30\u5398\u7c73"


def test_fullwidth_punct_to_halfwidth_with_trailing_space():
    # Donor verbatim: punct gets a trailing space then trimmed at edges.
    assert normalize_zh_text("\u4f60\u597d\uff0c\u4e16\u754c\u3002") == "\u4f60\u597d, \u4e16\u754c."


def test_normalize_does_not_strip_cjk_so_guard_still_detects_it():
    """Guard-compat: when target_lang='my', dub_text_guard flags CJK lines.
    Running normalize_zh_text on CJK input must keep enough CJK codepoints
    that the guard's CJK detection still fires. If normalize ever stripped
    CJK characters, the guard would silently miss Burmese-vs-Chinese mix
    violations and ship wrong-language dubs.
    """
    raw = "\u4f60\u597d\u4e16\u754c"  # 你好世界 — 4 CJK chars
    normalized = normalize_zh_text(raw)
    report = clean_and_analyze_dub_text(normalized, target_lang="my")
    # Guard must still see CJK (>=2 chars) and flag the line.
    assert report["cjk_lines"], (
        "dub_text_guard lost CJK detection after zh_normalize — "
        "M-05 absorption violates guard-compat acceptance"
    )
    assert report["warning"] is not None


def test_normalize_preserves_srt_cue_index_lines_as_pure_text():
    """Sanity: zh_normalize is a plain-text helper, not an SRT processor.
    It does not invent SRT structure; callers are responsible for feeding
    cue text only. This test pins the contract by asserting that a digit-
    only line survives normalization unchanged (no spurious punctuation).
    """
    assert normalize_zh_text("1") == "1"
