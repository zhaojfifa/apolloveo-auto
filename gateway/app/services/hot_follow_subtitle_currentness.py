from __future__ import annotations

import re
from typing import Iterable


def _normalize_subtitle_source_name(target_lang: str | None, source_name: str | None) -> str:
    name = str(source_name or "").strip().lower()
    if not name:
        return ""
    if str(target_lang or "").strip().lower() in {"my", "mm"} and name == "my.srt":
        return "mm.srt"
    return name


def normalize_subtitle_semantic_text(text: str | None) -> str:
    source = str(text or "")
    if not source:
        return ""
    lines: list[str] = []
    for raw_line in source.splitlines():
        line = str(raw_line or "").strip()
        if not line:
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"\s+", " ", line)
        if line:
            lines.append(line)
    return "\n".join(lines).strip().lower()


def has_semantic_target_subtitle_text(text: str | None) -> bool:
    return bool(normalize_subtitle_semantic_text(text))


def _matches_any_source(target_text: str | None, source_texts: Iterable[str | None]) -> bool:
    normalized_target = normalize_subtitle_semantic_text(target_text)
    if not normalized_target:
        return False
    for source_text in source_texts:
        normalized_source = normalize_subtitle_semantic_text(source_text)
        if normalized_source and normalized_source == normalized_target:
            return True
    return False


def compute_hot_follow_target_subtitle_currentness(
    *,
    target_lang: str | None,
    target_text: str | None,
    source_texts: Iterable[str | None],
    subtitle_artifact_exists: bool,
    expected_subtitle_source: str | None,
    actual_subtitle_source: str | None,
    translation_incomplete: bool = False,
    has_saved_revision: bool = False,
) -> dict[str, object]:
    target_exists = has_semantic_target_subtitle_text(target_text)
    normalized_expected = _normalize_subtitle_source_name(target_lang, expected_subtitle_source)
    normalized_actual = _normalize_subtitle_source_name(target_lang, actual_subtitle_source)
    authoritative_source = bool(
        subtitle_artifact_exists
        and normalized_expected
        and normalized_actual
        and normalized_expected == normalized_actual
    )
    source_copy = _matches_any_source(target_text, source_texts)

    if not subtitle_artifact_exists or not normalized_expected or not normalized_actual:
        current = False
        reason = "subtitle_missing"
    elif not authoritative_source:
        current = False
        reason = "target_subtitle_source_mismatch"
    elif translation_incomplete:
        current = False
        reason = "target_subtitle_translation_incomplete"
    elif not target_exists:
        current = False
        reason = "target_subtitle_empty"
    elif source_copy:
        current = False
        reason = "target_subtitle_source_copy"
    else:
        current = True
        reason = "ready"

    return {
        "target_subtitle_current": current,
        "target_subtitle_current_reason": reason,
        "target_subtitle_authoritative_source": authoritative_source,
        "target_subtitle_source_copy": source_copy,
    }
