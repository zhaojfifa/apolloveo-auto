from __future__ import annotations

import re

from gateway.app.services.tts_policy import normalize_target_lang

_MYANMAR_RE = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]")
_CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")
_LATIN_RE = re.compile(r"[A-Za-z]")
_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)
_BRACKET_TAG_RE = re.compile(r"\[[^\]]+\]")


def _iter_srt_text_lines(text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    blocks = [b for b in (text or "").split("\n\n") if b.strip()]
    for idx, block in enumerate(blocks, start=1):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        cue_index = idx
        if lines[0].strip().isdigit():
            try:
                cue_index = int(lines[0].strip())
            except Exception:
                cue_index = idx
        line_start = 1 if lines and lines[0].strip().isdigit() else 0
        for line in lines[line_start:]:
            s = line.strip()
            if not s:
                continue
            if "-->" in s or _SRT_TIME_RE.search(s):
                continue
            rows.append((cue_index, s))
    return rows


def _count_scripts(text: str) -> dict[str, int]:
    return {
        "myanmar": len(_MYANMAR_RE.findall(text)),
        "cjk": len(_CJK_RE.findall(text)),
        "latin": len(_LATIN_RE.findall(text)),
    }


def clean_and_analyze_dub_text(text: str, target_lang: str | None) -> dict[str, object]:
    rows = _iter_srt_text_lines(text)
    if not rows:
        rows = [(idx, line.strip()) for idx, line in enumerate((text or "").splitlines(), start=1) if line.strip()]

    normalized_lang = normalize_target_lang(target_lang)
    cjk_lines: list[int] = []
    cleaned_lines: list[str] = []
    total = {"myanmar": 0, "cjk": 0, "latin": 0}

    for line_no, raw_line in rows:
        line = _BRACKET_TAG_RE.sub("", raw_line).strip()
        if not line:
            continue
        counts = _count_scripts(line)
        total["myanmar"] += counts["myanmar"]
        total["cjk"] += counts["cjk"]
        total["latin"] += counts["latin"]
        cjk_heavy = counts["cjk"] >= 2 and counts["cjk"] >= counts["myanmar"]
        if normalized_lang == "my" and cjk_heavy:
            cjk_lines.append(line_no)
            continue
        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines).strip()
    script_total = total["myanmar"] + total["cjk"] + total["latin"]
    myanmar_ratio = (float(total["myanmar"]) / float(script_total)) if script_total > 0 else 0.0
    warning = None
    if normalized_lang == "my":
        warning_parts: list[str] = []
        if cjk_lines:
            sample = ",".join(str(n) for n in cjk_lines[:8])
            warning_parts.append(f"detected CJK in mm subtitles (lines: {sample})")
        if myanmar_ratio < 0.6:
            warning_parts.append(f"Myanmar ratio low ({myanmar_ratio:.0%})")
        if warning_parts:
            warning = "; ".join(warning_parts)

    return {
        "cleaned_text": cleaned_text or text.strip(),
        "warning": warning,
        "cjk_lines": cjk_lines,
        "myanmar_ratio": myanmar_ratio,
    }
