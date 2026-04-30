from __future__ import annotations

import re
from typing import Any

from gateway.app.utils.pipeline_config import parse_pipeline_config


_TIMECODE_RE = re.compile(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}")
_LYRIC_KEYWORDS = {
    "chorus",
    "verse",
    "refrain",
    "lyrics",
    "lyric",
    "singing",
    "sings",
    "song",
    "la la",
    "na na",
    "oh oh",
}


def is_hot_follow_local_upload(task: dict[str, Any] | None) -> bool:
    task_obj = task if isinstance(task, dict) else {}
    pipeline_config = parse_pipeline_config(task_obj.get("pipeline_config"))
    source_type = str(task_obj.get("source_type") or "").strip().lower()
    ingest_mode = str(pipeline_config.get("ingest_mode") or "").strip().lower()
    return source_type in {"local", "local_upload", "upload"} or ingest_mode in {"local", "local_upload"}


def subtitle_text_lines(text: str | None) -> list[str]:
    lines: list[str] = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.isdigit() or _TIMECODE_RE.search(line):
            continue
        lines.append(line)
    return lines


def is_lyric_bgm_like_subtitle_text(text: str | None) -> bool:
    lines = subtitle_text_lines(text)
    if not lines:
        return False
    lowered = "\n".join(lines).lower()
    if any(keyword in lowered for keyword in _LYRIC_KEYWORDS):
        return True
    if len(lines) < 4:
        return False
    normalized = [re.sub(r"\W+", " ", line.lower()).strip() for line in lines]
    normalized = [line for line in normalized if line]
    if not normalized:
        return False
    repeated = len(normalized) - len(set(normalized))
    if repeated / max(len(normalized), 1) >= 0.25:
        return True
    word_counts = [len(line.split()) for line in normalized]
    avg_words = sum(word_counts) / max(len(word_counts), 1)
    sentence_like = sum(1 for line in lines if line.endswith((".", "?", "!", "。", "？", "！")))
    return bool(avg_words <= 7 and sentence_like / max(len(lines), 1) < 0.25 and repeated > 0)


def local_upload_requires_manual_subtitle_first(task: dict[str, Any] | None, text: str | None) -> bool:
    return bool(is_hot_follow_local_upload(task) and is_lyric_bgm_like_subtitle_text(text))
