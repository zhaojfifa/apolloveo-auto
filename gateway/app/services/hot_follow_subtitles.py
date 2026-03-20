from __future__ import annotations

from typing import Iterable

from gateway.app.core.subtitle_utils import segments_to_srt
from gateway.app.steps.subtitles import _parse_srt_to_segments


def is_srt_text(text: str) -> bool:
    source = str(text or "").strip()
    if not source or "-->" not in source:
        return False
    try:
        return bool(_parse_srt_to_segments(source))
    except Exception:
        return False


def plain_text_to_single_srt(text: str, *, duration_sec: float | None) -> str:
    content_lines = [str(line or "").rstrip() for line in str(text or "").splitlines()]
    content = "\n".join(line for line in content_lines if line.strip()).strip()
    if not content:
        return ""
    try:
        dur = float(duration_sec) if duration_sec is not None else 0.0
    except Exception:
        dur = 0.0
    if dur <= 0:
        dur = 8.0
    dur = max(2.0, min(dur, 60.0))
    return segments_to_srt(
        [
            {
                "index": 1,
                "start": 0.0,
                "end": dur,
                "origin": content,
            }
        ],
        "origin",
    )


def _segment_overlap(a: dict, b: dict) -> float:
    start = max(float(a.get("start") or 0.0), float(b.get("start") or 0.0))
    end = min(float(a.get("end") or 0.0), float(b.get("end") or 0.0))
    return max(0.0, end - start)


def _segments_match(base_seg: dict, overlay_seg: dict) -> bool:
    base_start = float(base_seg.get("start") or 0.0)
    base_end = float(base_seg.get("end") or base_start)
    overlay_start = float(overlay_seg.get("start") or 0.0)
    overlay_end = float(overlay_seg.get("end") or overlay_start)
    if abs(base_start - overlay_start) <= 0.12 and abs(base_end - overlay_end) <= 0.18:
        return True
    overlap = _segment_overlap(base_seg, overlay_seg)
    if overlap <= 0:
        return False
    shorter = min(max(0.0, base_end - base_start), max(0.0, overlay_end - overlay_start))
    return shorter > 0 and overlap >= shorter * 0.7


def _normalize_segments(segments: Iterable[dict]) -> list[dict]:
    normalized: list[dict] = []
    for idx, seg in enumerate(segments, start=1):
        row = dict(seg or {})
        row["index"] = idx
        row["origin"] = str(row.get("origin") or "").strip()
        normalized.append(row)
    return normalized


def merge_target_srt(base_text: str, overlay_text: str) -> str:
    if not is_srt_text(overlay_text):
        return str(overlay_text or "").strip()
    overlay_segments = _normalize_segments(_parse_srt_to_segments(overlay_text))
    if not overlay_segments:
        return ""
    if not is_srt_text(base_text):
        return segments_to_srt(overlay_segments, "origin")

    base_segments = _normalize_segments(_parse_srt_to_segments(base_text))
    used_overlay_indexes: set[int] = set()
    merged: list[dict] = []

    for base_seg in base_segments:
        replacement_index = next(
            (
                idx
                for idx, overlay_seg in enumerate(overlay_segments)
                if idx not in used_overlay_indexes and _segments_match(base_seg, overlay_seg)
            ),
            None,
        )
        if replacement_index is None:
            merged.append(dict(base_seg))
            continue
        used_overlay_indexes.add(replacement_index)
        merged.append(dict(overlay_segments[replacement_index]))

    for idx, overlay_seg in enumerate(overlay_segments):
        if idx not in used_overlay_indexes:
            merged.append(dict(overlay_seg))

    merged.sort(key=lambda seg: (float(seg.get("start") or 0.0), float(seg.get("end") or 0.0)))
    return segments_to_srt(_normalize_segments(merged), "origin")


def normalize_target_subtitles_for_save(
    raw_text: str,
    *,
    duration_sec: float | None,
    current_target_srt: str = "",
) -> tuple[str, str]:
    text = str(raw_text or "").strip()
    if not text:
        return "", "empty"
    if is_srt_text(text):
        merged = merge_target_srt(current_target_srt, text)
        mode = "srt_merged" if is_srt_text(current_target_srt) and merged.strip() != text.strip() else "srt"
        return merged, mode
    return plain_text_to_single_srt(text, duration_sec=duration_sec) + "\n", "plain_text_wrapped"
