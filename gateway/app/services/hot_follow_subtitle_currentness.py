from __future__ import annotations

import re
from typing import Iterable


def _normalize_subtitle_compare_text(text: str | None) -> str:
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


def _matches_any_source(target_text: str | None, source_texts: Iterable[str | None]) -> bool:
    normalized_target = _normalize_subtitle_compare_text(target_text)
    if not normalized_target:
        return False
    for source_text in source_texts:
        normalized_source = _normalize_subtitle_compare_text(source_text)
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
    target_exists = bool(_normalize_subtitle_compare_text(target_text))
    authoritative_source = bool(
        subtitle_artifact_exists
        and expected_subtitle_source
        and actual_subtitle_source
        and str(expected_subtitle_source).strip() == str(actual_subtitle_source).strip()
    )
    source_copy = _matches_any_source(target_text, source_texts)

    if not subtitle_artifact_exists or not expected_subtitle_source or not actual_subtitle_source:
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
