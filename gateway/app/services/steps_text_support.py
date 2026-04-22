"""Neutral text/SRT helpers used by steps_v1.

These helpers are intentionally stateless and non-orchestrating.  They exist
to keep ``steps_v1.py`` focused on step sequencing and side-effectful runtime
work rather than reusable subtitle/text compatibility logic.
"""

from __future__ import annotations

import re
from pathlib import Path

_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)


def subtitle_result_contract(result: dict | None) -> tuple[str, str, str, dict[str, object]]:
    payload = dict(result or {})
    origin_text = str(payload.get("origin_srt") or "")
    normalized_origin_text = str(payload.get("origin_normalized_srt") or origin_text or "")
    target_text = str(payload.get("mm_srt") or "")
    translation_qa_raw = payload.get("translation_qa")
    translation_qa = dict(translation_qa_raw) if isinstance(translation_qa_raw, dict) else {}
    if "complete" not in translation_qa:
        translation_qa["complete"] = not bool(payload.get("translation_incomplete"))
    return origin_text, normalized_origin_text, target_text, translation_qa


def srt_to_txt(srt_text: str) -> str:
    blocks = [b for b in srt_text.split("\n\n") if b.strip()]
    lines_out: list[str] = []
    for block in blocks:
        text_lines: list[str] = []
        for line in block.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.isdigit():
                continue
            if "-->" in s or _SRT_TIME_RE.search(s):
                continue
            text_lines.append(s)
        if text_lines:
            lines_out.append(" ".join(text_lines))
    return "\n".join(lines_out).strip() + ("\n" if lines_out else "")


def ensure_txt_from_srt(dst_txt: Path, src_srt: Path) -> None:
    srt_text = src_srt.read_text(encoding="utf-8")
    dst_txt.write_text(srt_to_txt(srt_text), encoding="utf-8")


def parse_srt_time(value: str) -> float:
    h, m, rest = value.replace(",", ".").split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt_cues(srt_text: str) -> list[dict]:
    blocks = [b for b in (srt_text or "").split("\n\n") if b.strip()]
    cues: list[dict] = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        first = lines[0].strip()
        has_index = first.isdigit()
        time_line = lines[1].strip() if has_index else lines[0].strip()
        if "-->" not in time_line:
            continue
        left, right = [x.strip() for x in time_line.split("-->", 1)]
        try:
            start_sec = parse_srt_time(left)
            end_sec = parse_srt_time(right)
        except Exception:
            continue
        text_lines = lines[2:] if has_index else lines[1:]
        text = "\n".join([t for t in text_lines if t.strip()]).strip()
        if not text:
            continue
        cues.append(
            {
                "index": int(first) if has_index else len(cues) + 1,
                "start": start_sec,
                "end": end_sec,
                "text": text,
                "budget": max(0.0, end_sec - start_sec),
            }
        )
    return cues


def clean_text_for_dub(text: str) -> str:
    return re.sub(r"[\W_]+", "", text or "", flags=re.UNICODE)


def pick_mm_text_fallback(
    *,
    override_text: str | None,
    edited_text: str | None,
    mm_srt_text: str | None,
) -> tuple[str | None, str | None]:
    override = str(override_text or "").strip()
    if override:
        return override, "override"
    srt_text = str(mm_srt_text or "").strip()
    if srt_text:
        txt = srt_to_txt(srt_text).strip()
        if txt:
            return txt, "mm_srt"
    edited = str(edited_text or "").strip()
    if edited:
        return edited, "edited_text"
    return None, None


def resolve_mm_txt_text(
    *,
    mm_txt_text: str | None,
    override_text: str | None,
    edited_text: str | None,
    mm_srt_text: str | None,
) -> tuple[str, bool, str | None]:
    current = str(mm_txt_text or "").strip()
    if current and current.lower() != "no subtitles":
        return current, False, "mm_txt"
    fallback_text, fallback_source = pick_mm_text_fallback(
        override_text=override_text,
        edited_text=edited_text,
        mm_srt_text=mm_srt_text,
    )
    if fallback_text:
        return str(fallback_text).strip(), True, fallback_source
    return current, False, None


__all__ = [
    "clean_text_for_dub",
    "ensure_txt_from_srt",
    "parse_srt_cues",
    "parse_srt_time",
    "pick_mm_text_fallback",
    "resolve_mm_txt_text",
    "srt_to_txt",
    "subtitle_result_contract",
]
