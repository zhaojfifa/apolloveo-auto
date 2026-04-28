"""Pure subtitle rendering and layout helpers for compose service.

This module intentionally contains stateless helpers only.  It exists to keep
``compose_service.py`` focused on orchestration, workspace handling, and FFmpeg
execution rather than subtitle layout policy details.
"""

from __future__ import annotations

import re
from pathlib import Path

from gateway.app.services.hot_follow_media_policy import (
    hot_follow_subtitle_style_profile,
    normalize_hot_follow_layout_lang,
)

_CJK_CHAR_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_MYANMAR_CHAR_RE = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]")
_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)


def escape_subtitles_path(path: Path) -> str:
    """Escape a path for use in FFmpeg subtitles filter expressions."""
    raw = str(path).replace("\\", "/")
    return raw.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _feathered_bottom_band_filter(
    *,
    core_start: float,
    core_height: float,
    core_alpha: float,
    feather_bands: list[tuple[float, float, float]],
) -> str:
    filters = [
        (
            "drawbox="
            f"x=0:y=ih*{core_start:.3f}:w=iw:h=ih*{core_height:.3f}:"
            f"color=black@{core_alpha:.2f}:t=fill"
        )
    ]
    for start, height, alpha in feather_bands:
        filters.append(
            "drawbox="
            f"x=0:y=ih*{start:.3f}:w=iw:h=ih*{height:.3f}:"
            f"color=black@{alpha:.2f}:t=fill"
        )
    return ",".join(filters)


def subtitle_render_signature(*, target_lang: str | None, cleanup_mode: str | None) -> str:
    profile = hot_follow_subtitle_style_profile(target_lang)
    lang = normalize_hot_follow_layout_lang(target_lang)
    cleanup = str(cleanup_mode or "none").strip().lower() or "none"
    return "|".join(profile.to_signature_parts(lang=lang, cleanup=cleanup))


def _text_display_width(text: str) -> float:
    width = 0.0
    for ch in str(text or ""):
        if not ch or ch.isspace():
            width += 0.35
        elif _CJK_CHAR_RE.match(ch) or _MYANMAR_CHAR_RE.match(ch):
            width += 1.0
        elif ch.isascii() and ch.isalnum():
            width += 0.58
        else:
            width += 0.72
    return width


def _compact_subtitle_text(text: str) -> str:
    lines = [str(line or "").strip() for line in str(text or "").splitlines() if str(line or "").strip()]
    if not lines:
        return ""
    return " ".join(lines)


def _tokenize_subtitle_text(text: str, target_lang: str | None) -> tuple[list[str], str]:
    compact = _compact_subtitle_text(text)
    if not compact:
        return [], "words"
    lang = normalize_hot_follow_layout_lang(target_lang)
    if lang == "zh":
        return [ch for ch in compact if ch.strip()], "chars"
    if not re.search(r"\s", compact) and (_CJK_CHAR_RE.search(compact) or _MYANMAR_CHAR_RE.search(compact)):
        return [ch for ch in compact if ch.strip()], "chars"
    return compact.split(), "words"


def _join_subtitle_tokens(tokens: list[str], mode: str) -> str:
    if mode == "chars":
        return "".join(tokens).strip()
    return " ".join(token for token in tokens if token).strip()


def _break_bonus(left: str, right: str, mode: str) -> float:
    bonus = 0.0
    if left.endswith(("。", "！", "？", "，", "、", ".", "!", "?", ",", ";", "；", ":", "：")):
        bonus -= 1.2
    if right.startswith(("，", "。", "！", "？", ",", ".", "!", "?", ";", "；", ":", "：")):
        bonus += 0.8
    if mode == "words" and left.endswith(("-", "/")):
        bonus += 0.4
    return bonus


def _best_two_line_layout(text: str, target_lang: str | None) -> str:
    profile = hot_follow_subtitle_style_profile(target_lang)
    max_width = float(profile.line_width)
    tokens, mode = _tokenize_subtitle_text(text, target_lang)
    if not tokens:
        return ""

    single_line = _join_subtitle_tokens(tokens, mode)
    if _text_display_width(single_line) <= max_width:
        return single_line

    best_lines: tuple[str, str] | None = None
    best_penalty: float | None = None
    total_width = _text_display_width(single_line)
    for idx in range(1, len(tokens)):
        left = _join_subtitle_tokens(tokens[:idx], mode)
        right = _join_subtitle_tokens(tokens[idx:], mode)
        if not left or not right:
            continue
        left_width = _text_display_width(left)
        right_width = _text_display_width(right)
        overflow = max(0.0, left_width - max_width) + max(0.0, right_width - max_width)
        penalty = overflow * 12.0 + abs(left_width - right_width) + _break_bonus(left, right, mode)
        if total_width > max_width * 2:
            penalty += max(0.0, total_width - max_width * 2) * 3.0
        if best_penalty is None or penalty < best_penalty:
            best_penalty = penalty
            best_lines = (left, right)

    if best_lines is None:
        return single_line
    return f"{best_lines[0]}\n{best_lines[1]}"


def optimize_hot_follow_subtitle_layout_srt(srt_text: str, target_lang: str | None) -> str:
    blocks = [block for block in str(srt_text or "").split("\n\n") if block.strip()]
    if not blocks:
        return str(srt_text or "")

    normalized_blocks: list[str] = []
    changed = False
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            normalized_blocks.append(block.strip())
            continue
        has_index = lines[0].strip().isdigit()
        index_line = lines[0].strip() if has_index else None
        time_line = lines[1].strip() if has_index else lines[0].strip()
        if not _SRT_TIME_RE.search(time_line):
            normalized_blocks.append(block.strip())
            continue
        text_lines = lines[2:] if has_index else lines[1:]
        wrapped_text = _best_two_line_layout("\n".join(text_lines), target_lang)
        if wrapped_text and wrapped_text != "\n".join(text_lines).strip():
            changed = True
        out_lines: list[str] = []
        if index_line:
            out_lines.append(index_line)
        out_lines.append(time_line)
        if wrapped_text:
            out_lines.extend(wrapped_text.splitlines())
        normalized_blocks.append("\n".join(out_lines))

    result = "\n\n".join(normalized_blocks).strip()
    if not result:
        return str(srt_text or "")
    return result + "\n" if changed or not str(srt_text or "").endswith("\n") else result + "\n"


def source_subtitle_cover_filter(cleanup_mode: str, target_lang: str | None = None) -> str:
    """Return an FFmpeg drawbox filter for subtitle area masking."""
    mode = str(cleanup_mode or "").strip().lower()
    if mode == "bottom_mask":
        return _feathered_bottom_band_filter(
            core_start=0.850,
            core_height=0.150,
            core_alpha=0.68,
            feather_bands=[
                (0.825, 0.025, 0.22),
                (0.803, 0.022, 0.12),
                (0.785, 0.018, 0.06),
            ],
        )
    if mode == "safe_band":
        return _feathered_bottom_band_filter(
            core_start=0.820,
            core_height=0.180,
            core_alpha=0.56,
            feather_bands=[
                (0.790, 0.030, 0.20),
                (0.765, 0.025, 0.10),
                (0.745, 0.020, 0.05),
            ],
        )
    return ""


def compose_subtitle_vf(
    subtitle_path_obj: Path,
    fontsdir: Path,
    cleanup_mode: str,
    target_lang: str | None = None,
) -> str:
    """Build the complete subtitle video-filter string for FFmpeg."""
    profile = hot_follow_subtitle_style_profile(target_lang)
    subtitle_filter = (
        f"subtitles='{escape_subtitles_path(subtitle_path_obj)}':"
        "charenc=UTF-8:"
        f"fontsdir='{escape_subtitles_path(Path(fontsdir))}':"
        "force_style='"
        f"FontName={profile.font_name},"
        f"FontSize={profile.font_size_ass()},"
        "Outline=2,"
        "Shadow=1,"
        f"Alignment={int(profile.alignment)},"
        f"MarginV={int(profile.margin_v)},"
        f"Spacing={float(profile.line_spacing):.1f},"
        f"WrapStyle={int(profile.wrap_style)}'"
    )
    cover_filter = source_subtitle_cover_filter(cleanup_mode, target_lang=target_lang)
    return f"{cover_filter},{subtitle_filter}" if cover_filter else subtitle_filter


__all__ = [
    "compose_subtitle_vf",
    "escape_subtitles_path",
    "optimize_hot_follow_subtitle_layout_srt",
    "source_subtitle_cover_filter",
    "subtitle_render_signature",
]
