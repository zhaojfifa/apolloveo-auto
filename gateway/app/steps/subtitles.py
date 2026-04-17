"""Subtitles dispatcher for /v1/subtitles with Gemini as default backend."""

from __future__ import annotations

import asyncio
import json
import os
import logging
import re
import shutil
import subprocess
import time
import wave
from math import ceil
from pathlib import Path

from fastapi import HTTPException

from gateway.app.config import get_settings
from gateway.app.core.subtitle_utils import preview_lines, segments_to_srt
from gateway.app.core.workspace import (
    Workspace,
    audio_wav_path,
    raw_clean_path,
    relative_to_workspace,
    subs_dir,
)
from gateway.app.providers.gemini_subtitles import (
    GeminiSubtitlesError,
    translate_segments_with_gemini,
)
from gateway.app.providers.whisper_singleton import transcribe

logger = logging.getLogger(__name__)


_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)

_HOT_FOLLOW_DOMAIN_TERM_REPLACEMENTS: dict[str, str] = {
    "布灵布灵": "bling bling",
    "雅光": "哑光",
    "亚光": "哑光",
    "亮闪": "爆闪",
    "细钻": "细闪",
    "沉膜": "成膜",
    "速干沉膜": "速干成膜",
    "不粘杯": "不沾杯",
    "不占杯": "不沾杯",
    "双头口红": "双头唇釉",
    "hagard": "haggard",
    "哈格德": "haggard",
}

_HOT_FOLLOW_PROTECTED_TERMS: tuple[str, ...] = (
    "haggard",
    "bling bling",
    "matte",
    "gloss",
    "lip gloss",
    "lip glaze",
    "lip mud",
    "lip tint",
    "velvet",
    "mirror gloss",
    "shimmer",
    "glitter",
    "dual-ended",
    "double-ended",
    "cushion",
    "primer",
    "setting spray",
    "spf",
    "pa+++",
    "爆闪",
    "细闪",
    "珠光",
    "镜面",
    "哑光",
    "丝绒",
    "水光",
    "唇釉",
    "唇蜜",
    "唇泥",
    "口红",
    "染唇",
    "双头唇釉",
    "速干成膜",
    "不沾杯",
    "显白",
    "提气色",
    "薄涂",
    "厚涂",
    "叠涂",
    "氛围感",
    "千金感",
    "试色",
    "上嘴",
    "持妆",
    "luggage",
    "carry on",
    "spinner",
    "waterproof",
    "coupon",
    "flash sale",
    "free shipping",
)

PARSE_SOURCE_RAW_VIDEO_AUDIO = "raw_video_audio"
PARSE_SOURCE_PRESERVED_AUDIO_HELPER = "preserved_source_audio_helper"


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _wav_duration_seconds(wav_path: Path) -> float | None:
    try:
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return None
            return frames / float(rate)
    except Exception:
        return None


def _compute_asr_timeout_sec(audio_sec: float | None) -> int:
    fixed = _env_int("SUBTITLES_ASR_TIMEOUT_SEC", 600)
    audio_sec = _safe_non_negative_float(audio_sec, 0.0)
    if not audio_sec or audio_sec <= 0:
        return fixed

    min_sec = _env_int("SUBTITLES_ASR_TIMEOUT_MIN_SEC", 600)
    max_sec = _env_int("SUBTITLES_ASR_TIMEOUT_MAX_SEC", 7200)
    slack = _env_int("SUBTITLES_ASR_TIMEOUT_SLACK_SEC", 120)
    try:
        rtf = float(os.getenv("SUBTITLES_ASR_TIMEOUT_RTF", "3.0"))
    except ValueError:
        rtf = 3.0

    dynamic = int(ceil(audio_sec * rtf + slack))
    return max(min_sec, min(dynamic, max_sec))


def _safe_non_negative_float(value: float | int | str | None, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except Exception:
        return float(default)
    if parsed < 0:
        return float(default)
    return parsed


def _sanitize_segment_timing(segments: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    for seg in segments or []:
        row = dict(seg or {})
        start = _safe_non_negative_float(row.get("start"), 0.0)
        end = _safe_non_negative_float(row.get("end"), start)
        if end < start:
            end = start
        row["start"] = start
        row["end"] = end
        sanitized.append(row)
    return sanitized


def _normalize_hot_follow_origin_text(text: str) -> str:
    normalized = str(text or "")
    if not normalized.strip():
        return ""
    for source, target in _HOT_FOLLOW_DOMAIN_TERM_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    for term in _HOT_FOLLOW_PROTECTED_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        normalized = pattern.sub(term, normalized)
    return normalized


def _normalized_segments(segments: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for seg in segments or []:
        row = dict(seg or {})
        row["origin_normalized"] = _normalize_hot_follow_origin_text(str(seg.get("origin") or ""))
        normalized.append(row)
    return normalized


def _probe_streams(video_path: Path) -> dict:
    if not video_path.exists():
        return {
            "status": "missing",
            "has_audio": None,
            "has_subtitle_stream": None,
            "subtitle_codecs": [],
            "audio_codecs": [],
        }

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {
            "status": "no_ffprobe",
            "has_audio": None,
            "has_subtitle_stream": None,
            "subtitle_codecs": [],
            "audio_codecs": [],
        }

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        str(video_path),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return {
            "status": "ffprobe_failed",
            "has_audio": None,
            "has_subtitle_stream": None,
            "subtitle_codecs": [],
            "audio_codecs": [],
        }
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "status": "ffprobe_bad_json",
            "has_audio": None,
            "has_subtitle_stream": None,
            "subtitle_codecs": [],
            "audio_codecs": [],
        }

    streams = payload.get("streams", []) or []
    audio_codecs = [
        s.get("codec_name")
        for s in streams
        if s.get("codec_type") == "audio" and s.get("codec_name")
    ]
    subtitle_codecs = [
        s.get("codec_name")
        for s in streams
        if s.get("codec_type") == "subtitle" and s.get("codec_name")
    ]
    return {
        "status": "ok",
        "has_audio": bool(audio_codecs),
        "has_subtitle_stream": bool(subtitle_codecs),
        "subtitle_codecs": subtitle_codecs,
        "audio_codecs": audio_codecs,
    }


def _strip_subtitle_streams(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    if dst.exists() and dst.stat().st_size > 0:
        return True
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c",
        "copy",
        str(dst),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode == 0 and dst.exists() and dst.stat().st_size > 0


def _srt_to_txt(srt_text: str) -> str:
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


def _write_txt_from_srt(target_path, srt_text: str) -> None:
    target_path.write_text(_srt_to_txt(srt_text), encoding="utf-8")


def build_preview(text: str | None) -> list[str]:
    if not text:
        return []
    return preview_lines(text)


def _collect_missing_translation_indexes(
    segments: list[dict],
    translations: dict[int, str],
) -> list[int]:
    source_indexes: list[int] = []
    for seg in segments:
        try:
            source_indexes.append(int(seg.get("index", 0)))
        except Exception:
            continue

    translated_indexes = {
        int(idx)
        for idx, text in (translations or {}).items()
        if isinstance(text, str) and text.strip()
    }
    return [idx for idx in source_indexes if idx not in translated_indexes]


def _build_translation_qa_payload(
    *,
    source_count: int,
    translated_count: int,
    missing_indexes: list[int],
    retry_count: int,
) -> dict:
    return {
        "source_count": int(source_count),
        "translated_count": int(translated_count),
        "missing_indexes": [int(i) for i in missing_indexes],
        "retry_count": int(retry_count),
        "complete": len(missing_indexes) == 0,
    }


def _write_no_subtitles_placeholders(
    *, workspace: Workspace, task_id: str, reason: str, log_stage
) -> dict:
    origin_srt_path = workspace.origin_srt_path
    mm_srt_path = workspace.mm_srt_path
    mm_txt_path = workspace.mm_txt_path

    origin_srt_path.parent.mkdir(parents=True, exist_ok=True)
    origin_srt_path.write_text("", encoding="utf-8")
    mm_srt_path.parent.mkdir(parents=True, exist_ok=True)
    mm_srt_path.write_text("", encoding="utf-8")
    mm_txt_path.parent.mkdir(parents=True, exist_ok=True)
    mm_txt_path.write_text("no Subtitles", encoding="utf-8")
    translation_qa_path = workspace.subtitles_dir / "translation_qa.json"
    translation_qa_payload = _build_translation_qa_payload(
        source_count=0,
        translated_count=0,
        missing_indexes=[],
        retry_count=0,
    )
    translation_qa_path.write_text(
        json.dumps(translation_qa_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "SUB2_SKIP_NO_SUBTITLES",
        extra={
            "task_id": task_id,
            "step": "subtitles",
            "stage": "SUB2_SKIP_NO_SUBTITLES",
            "reason": reason,
        },
    )
    log_stage("SUB2_SKIP_NO_SUBTITLES", reason=reason)
    log_stage(
        "SUB2_WRITE_DONE",
        origin_srt_path=str(origin_srt_path),
        origin_srt_size=origin_srt_path.stat().st_size if origin_srt_path.exists() else None,
        mm_srt_path=str(mm_srt_path),
        mm_srt_size=mm_srt_path.stat().st_size if mm_srt_path.exists() else None,
        mm_txt_path=str(mm_txt_path),
        mm_txt_size=mm_txt_path.stat().st_size if mm_txt_path.exists() else None,
    )
    log_stage(
        "SUB2_DONE",
        origin_srt_len=0,
        mm_srt_len=0,
        segments_count=0,
    )
    return {
        "task_id": task_id,
        "origin_srt": "",
        "mm_srt": "",
        "mm_txt_path": relative_to_workspace(mm_txt_path),
        "translation_qa_path": relative_to_workspace(translation_qa_path),
        "translation_qa": translation_qa_payload,
        "translation_incomplete": False,
        "segments_json": {"scenes": []},
        "origin_preview": [],
        "mm_preview": [],
        "no_subtitles": True,
    }


def _ffmpeg_path() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found in PATH")
    return ffmpeg


def _extract_audio(video_path: Path, wav_path: Path, timeout_sec: int | None = None) -> None:
    ffmpeg = _ffmpeg_path()
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(wav_path),
    ]
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffmpeg audio extract timeout") from exc
    if p.returncode != 0 or not wav_path.exists():
        raise RuntimeError(f"ffmpeg audio extract failed: {p.stderr[-800:]}")


def _transcribe_with_faster_whisper(
    audio_path: Path,
    language_hint: str | None = None,
) -> tuple[list[dict], str | None]:
    kwargs = {}
    if language_hint:
        kwargs["language"] = language_hint
    segments_iter, info = transcribe(str(audio_path), **kwargs)
    segments = []
    for idx, seg in enumerate(segments_iter, start=1):
        text = (seg.text or "").strip()
        segments.append(
            {
                "index": idx,
                "start": _safe_non_negative_float(getattr(seg, "start", None), 0.0),
                "end": _safe_non_negative_float(getattr(seg, "end", None), _safe_non_negative_float(getattr(seg, "start", None), 0.0)),
                "origin": text,
            }
        )
    detected_lang = getattr(info, "language", None)
    return segments, detected_lang


def _parse_srt_to_segments(srt_text: str) -> list[dict]:
    blocks = [b for b in (srt_text or "").split("\n\n") if b.strip()]
    segments = []
    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        time_line = lines[1] if lines[0].strip().isdigit() else lines[0]
        match = _SRT_TIME_RE.search(time_line)
        if not match:
            continue
        start, end = time_line.split("-->")
        start = start.strip()
        end = end.strip()
        start_sec = _safe_non_negative_float(_parse_srt_time(start), 0.0)
        end_sec = _safe_non_negative_float(_parse_srt_time(end), start_sec)
        if end_sec < start_sec:
            end_sec = start_sec
        text_lines = lines[2:] if lines[0].strip().isdigit() else lines[1:]
        segments.append(
            {
                "index": len(segments) + 1,
                "start": start_sec,
                "end": end_sec,
                "origin": "\n".join(text_lines),
            }
        )
    return segments


def _parse_srt_time(value: str) -> float:
    h, m, rest = value.replace(",", ".").split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _segments_to_normalized_srt(segments: list[dict]) -> str:
    normalized_segments = []
    for seg in segments or []:
        row = dict(seg or {})
        row["origin"] = str(seg.get("origin_normalized") or seg.get("origin") or "")
        normalized_segments.append(row)
    return segments_to_srt(normalized_segments, "origin")


async def generate_subtitles(
    task_id: str,
    target_lang: str = "my",
    force: bool = False,
    translate_enabled: bool = True,
    use_ffmpeg_extract: bool = True,
    parse_source_mode: str | None = None,
) -> dict:
    """Unified subtitles entry point used by the FastAPI route."""

    start_time = time.perf_counter()
    settings = get_settings()
    backend = (settings.subtitles_backend or "").lower()
    asr_backend = settings.asr_backend
    asr_lang_hint = (os.getenv("SUBTITLES_ASR_LANG_HINT") or "").strip() or None
    parse_source_mode = str(parse_source_mode or PARSE_SOURCE_RAW_VIDEO_AUDIO).strip() or PARSE_SOURCE_RAW_VIDEO_AUDIO
    helper_only_parse_source = parse_source_mode == PARSE_SOURCE_PRESERVED_AUDIO_HELPER

    def log_stage(stage: str, **fields) -> None:
        logger.info(
            stage,
            extra={
                "task_id": task_id,
                "step": "subtitles",
                "stage": stage,
                "asr_backend": asr_backend,
                "subtitles_backend": backend,
                "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
                **fields,
            },
        )

    log_stage("SUB2_START")
    log_stage(
        "SUB2_PARSE_SOURCE_SELECTED",
        parse_source_mode=parse_source_mode,
        parse_source_authoritative_for_target=not helper_only_parse_source,
    )
    logger.info(
        "Subtitles request started",
        extra={
            "task_id": task_id,
            "asr_backend": settings.asr_backend,
            "subtitles_backend": backend,
        },
    )

    target_lang = target_lang or "my"
    workspace = Workspace(task_id, target_lang=target_lang)
    probe_result: dict = {
        "status": "unknown",
        "has_audio": None,
        "has_subtitle_stream": None,
        "subtitle_codecs": [],
        "audio_codecs": [],
    }
    clean_generated = False
    raw_for_asr: Path | None = None

    if workspace.raw_video_exists():
        raw_source = workspace.raw_video_path
        probe_result = _probe_streams(raw_source)
        if probe_result.get("has_audio") is False:
            return _write_no_subtitles_placeholders(
                workspace=workspace,
                task_id=task_id,
                reason="no_audio",
                log_stage=log_stage,
            )
        clean_path = raw_clean_path(task_id)
        if clean_path.exists() and clean_path.stat().st_size > 0:
            clean_generated = True
            raw_for_asr = clean_path
        elif probe_result.get("has_subtitle_stream") is True:
            clean_generated = _strip_subtitle_streams(raw_source, clean_path)
            if clean_generated:
                raw_for_asr = clean_path
        if raw_for_asr is None:
            raw_for_asr = raw_source
    else:
        origin_srt_text = workspace.read_origin_srt_text()
        if not origin_srt_text:
            return _write_no_subtitles_placeholders(
                workspace=workspace,
                task_id=task_id,
                reason="missing_origin_or_raw",
                log_stage=log_stage,
            )

    if backend == "gemini":
        try:
            logger.info(
                "Using Gemini subtitles backend",
                extra={
                    "task_id": task_id,
                    "raw_exists": workspace.raw_video_exists(),
                },
            )

            segments: list[dict] = []
            detected_lang = None
            if workspace.raw_video_exists():
                wav_path = audio_wav_path(task_id)
                raw_path = raw_for_asr or workspace.raw_video_path
                raw_size = raw_path.stat().st_size if raw_path.exists() else None
                log_stage(
                    "SUB2_WAV_EXTRACT_START",
                    raw_path=str(raw_path),
                    raw_size=raw_size,
                    wav_path=str(wav_path),
                )
                fixed_asr_timeout_sec = _env_int("SUBTITLES_ASR_TIMEOUT_SEC", 600)
                ffmpeg_timeout_sec = _env_int("SUBTITLES_FFMPEG_TIMEOUT_SEC", fixed_asr_timeout_sec)
                wav_start = time.perf_counter()
                _extract_audio(raw_path, wav_path, timeout_sec=ffmpeg_timeout_sec)
                log_stage(
                    "SUB2_WAV_EXTRACT_DONE",
                    wav_path=str(wav_path),
                    wav_size=wav_path.stat().st_size if wav_path.exists() else None,
                    duration_ms=int((time.perf_counter() - wav_start) * 1000),
                )
                audio_sec = _wav_duration_seconds(wav_path)
                if not audio_sec or audio_sec <= 0:
                    return _write_no_subtitles_placeholders(
                        workspace=workspace,
                        task_id=task_id,
                        reason="no_audio",
                        log_stage=log_stage,
                    )
                asr_timeout_sec = _compute_asr_timeout_sec(audio_sec)
                log_stage(
                    "SUB2_ASR_TIMEOUT",
                    audio_sec=audio_sec,
                    asr_timeout_sec=asr_timeout_sec,
                )
                asr_start = time.perf_counter()
                log_stage(
                    "SUB2_ASR_START",
                    wav_path=str(wav_path),
                    wav_size=wav_path.stat().st_size if wav_path.exists() else None,
                    asr_lang_hint=asr_lang_hint,
                )
                try:
                    segments, detected_lang = await asyncio.wait_for(
                        asyncio.to_thread(
                            _transcribe_with_faster_whisper,
                            wav_path,
                            asr_lang_hint,
                        ),
                        timeout=asr_timeout_sec,
                    )
                    log_stage(
                        "SUB2_ASR_DONE",
                        segments_count=len(segments),
                        detected_lang=detected_lang,
                        duration_ms=int((time.perf_counter() - asr_start) * 1000),
                    )
                except asyncio.TimeoutError:
                    log_stage(
                        "SUB2_ASR_FAIL",
                        error="timeout",
                        duration_ms=int((time.perf_counter() - asr_start) * 1000),
                    )
                    raise HTTPException(status_code=504, detail="ASR timeout")
                except Exception as exc:
                    log_stage(
                        "SUB2_ASR_FAIL",
                        error=str(exc),
                        duration_ms=int((time.perf_counter() - asr_start) * 1000),
                    )
                    raise
            else:
                origin_srt_text = workspace.read_origin_srt_text()
                if not origin_srt_text:
                    return _write_no_subtitles_placeholders(
                        workspace=workspace,
                        task_id=task_id,
                        reason="missing_origin_or_raw",
                        log_stage=log_stage,
                    )
                segments = _parse_srt_to_segments(origin_srt_text)

            if not segments:
                return _write_no_subtitles_placeholders(
                    workspace=workspace,
                    task_id=task_id,
                    reason="empty_segments",
                    log_stage=log_stage,
                )

            segments = _sanitize_segment_timing(_normalized_segments(segments))
            origin_text = segments_to_srt(segments, "origin")
            normalized_origin_text = _segments_to_normalized_srt(segments)
            translations: dict[int, str] = {}
            translation_retry_count = 0
            translate_enabled_local = translate_enabled
            if (
                translate_enabled_local
                and detected_lang
                and target_lang
                and detected_lang.lower() == target_lang.lower()
            ):
                translate_enabled_local = False
                log_stage(
                    "SUB2_TR_SKIPPED_SAME_LANG",
                    detected_lang=detected_lang,
                    target_lang=target_lang,
                )

            if translate_enabled_local:
                if helper_only_parse_source:
                    translate_enabled_local = False
                    log_stage(
                        "SUB2_TR_SKIPPED_HELPER_ONLY_SOURCE",
                        parse_source_mode=parse_source_mode,
                    )
            if translate_enabled_local:
                tr_timeout_sec = _env_int("SUBTITLES_TR_TIMEOUT_SEC", 120)
                tr_retries = _env_int("SUBTITLES_TR_RETRIES", 1)
                for attempt in range(tr_retries + 1):
                    tr_start = time.perf_counter()
                    log_stage(
                        "SUB2_TR_START",
                        attempt=attempt + 1,
                    )
                    try:
                        translations = await asyncio.wait_for(
                            asyncio.to_thread(
                                translate_segments_with_gemini,
                                segments=[
                                    {
                                        **seg,
                                        "origin": str(seg.get("origin_normalized") or seg.get("origin") or ""),
                                    }
                                    for seg in segments
                                ],
                                target_lang=target_lang,
                                debug_dir=subs_dir(task_id),
                            ),
                            timeout=tr_timeout_sec,
                        )
                        log_stage(
                            "SUB2_TR_DONE",
                            attempt=attempt + 1,
                            translations_count=len(translations),
                            duration_ms=int((time.perf_counter() - tr_start) * 1000),
                        )
                        break
                    except asyncio.TimeoutError:
                        log_stage(
                            "SUB2_TR_FAIL",
                            attempt=attempt + 1,
                            error="timeout",
                            duration_ms=int((time.perf_counter() - tr_start) * 1000),
                        )
                        if attempt < tr_retries:
                            continue
                        translations = {}
                    except GeminiSubtitlesError as exc:
                        status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
                        retryable = status in (429,) or (isinstance(status, int) and status >= 500)
                        log_stage(
                            "SUB2_TR_FAIL",
                            attempt=attempt + 1,
                            error=str(exc),
                            status_code=status,
                            duration_ms=int((time.perf_counter() - tr_start) * 1000),
                        )
                        if retryable and attempt < tr_retries:
                            continue
                        translations = {}
                    except ValueError as exc:
                        log_stage(
                            "SUB2_TR_FAIL",
                            attempt=attempt + 1,
                            error=str(exc),
                            duration_ms=int((time.perf_counter() - tr_start) * 1000),
                        )
                        translations = {}
                    break
                if not translations:
                    logger.warning("Gemini translation failed; fallback to origin only.")

            missing_indexes = (
                _collect_missing_translation_indexes(segments, translations)
                if translate_enabled_local or helper_only_parse_source
                else []
            )
            if translate_enabled_local and missing_indexes:
                translation_retry_count = 1
                retry_start = time.perf_counter()
                missing_set = set(missing_indexes)
                missing_segments = [
                    seg for seg in segments if int(seg.get("index", 0)) in missing_set
                ]
                log_stage(
                    "SUB2_TR_RETRY_MISSING_START",
                    missing_count=len(missing_segments),
                )
                try:
                    retry_translations = await asyncio.wait_for(
                        asyncio.to_thread(
                            translate_segments_with_gemini,
                            segments=[
                                {
                                    **seg,
                                    "origin": str(seg.get("origin_normalized") or seg.get("origin") or ""),
                                }
                                for seg in missing_segments
                            ],
                            target_lang=target_lang,
                            debug_dir=subs_dir(task_id),
                        ),
                        timeout=_env_int("SUBTITLES_TR_TIMEOUT_SEC", 120),
                    )
                    for idx, text in retry_translations.items():
                        if isinstance(text, str) and text.strip():
                            translations[int(idx)] = text
                    log_stage(
                        "SUB2_TR_RETRY_MISSING_DONE",
                        filled_count=len(retry_translations),
                        duration_ms=int((time.perf_counter() - retry_start) * 1000),
                    )
                except Exception as exc:
                    log_stage(
                        "SUB2_TR_RETRY_MISSING_FAIL",
                        error=str(exc),
                        duration_ms=int((time.perf_counter() - retry_start) * 1000),
                    )

            missing_indexes = (
                _collect_missing_translation_indexes(segments, translations)
                if translate_enabled_local or helper_only_parse_source
                else []
            )
            translated_count = len(segments) - len(missing_indexes)
            translation_qa_payload = _build_translation_qa_payload(
                source_count=len(segments),
                translated_count=translated_count,
                missing_indexes=missing_indexes,
                retry_count=translation_retry_count,
            )
            translation_qa_path = workspace.subtitles_dir / "translation_qa.json"
            translation_qa_path.write_text(
                json.dumps(translation_qa_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            log_stage(
                "SUB2_TR_QA_DONE",
                source_count=translation_qa_payload["source_count"],
                translated_count=translation_qa_payload["translated_count"],
                retry_count=translation_qa_payload["retry_count"],
                complete=translation_qa_payload["complete"],
            )

            for seg in segments:
                idx = int(seg.get("index", 0))
                translated_text = (translations.get(idx) or "").strip() if translations else ""
                if helper_only_parse_source:
                    seg["mm"] = ""
                elif translate_enabled_local:
                    seg["mm"] = translated_text
                else:
                    seg["mm"] = str(seg.get("origin") or "")

            mm_text = "" if helper_only_parse_source else segments_to_srt(segments, "mm")
            if not mm_text.strip() and not translate_enabled_local:
                mm_text = "" if helper_only_parse_source else origin_text

            scenes_payload = {
                "version": "1.8",
                "language": "origin",
                "segments": segments,
                "scenes": [
                    {
                        "scene_id": 1,
                        "start": segments[0]["start"],
                        "end": segments[-1]["end"],
                        "title": "",
                        "mm_title": "",
                    }
                ],
            }
            workspace.write_segments_json(scenes_payload)

            origin_srt_path = workspace.write_origin_srt(origin_text)
            mm_srt_path = workspace.write_mm_srt(mm_text)
            origin_normalized_srt_path = workspace.subtitles_dir / "origin_normalized.srt"
            origin_normalized_txt_path = workspace.subtitles_dir / "origin_normalized.txt"
            origin_txt_path = origin_srt_path.with_suffix(".txt")
            mm_txt_path = mm_srt_path.with_suffix(".txt")
            origin_normalized_srt_path.write_text(normalized_origin_text, encoding="utf-8")
            _write_txt_from_srt(origin_normalized_txt_path, normalized_origin_text)
            _write_txt_from_srt(origin_txt_path, origin_text)
            _write_txt_from_srt(mm_txt_path, mm_text)
            log_stage(
                "SUB2_WRITE_DONE",
                origin_srt_path=str(origin_srt_path),
                origin_srt_size=origin_srt_path.stat().st_size if origin_srt_path.exists() else None,
                origin_normalized_srt_path=str(origin_normalized_srt_path),
                origin_normalized_srt_size=origin_normalized_srt_path.stat().st_size if origin_normalized_srt_path.exists() else None,
                mm_srt_path=str(mm_srt_path),
                mm_srt_size=mm_srt_path.stat().st_size if mm_srt_path.exists() else None,
                mm_txt_path=str(mm_txt_path),
                mm_txt_size=mm_txt_path.stat().st_size if mm_txt_path.exists() else None,
            )

            logger.info(
                "Subtitles summary",
                extra={
                    "task_id": task_id,
                    "origin_srt_len": len(origin_text or ""),
                    "mm_srt_len": len(mm_text or ""),
                    "segments_count": len(segments),
                },
            )
            log_stage(
                "SUB2_DONE",
                origin_srt_len=len(origin_text or ""),
                mm_srt_len=len(mm_text or ""),
                segments_count=len(segments),
            )
            return {
                "task_id": task_id,
                "origin_srt": origin_text,
                "origin_normalized_srt": normalized_origin_text,
                "mm_srt": mm_text,
                "mm_txt_path": relative_to_workspace(mm_txt_path),
                "origin_normalized_srt_path": relative_to_workspace(origin_normalized_srt_path),
                "segments_json": scenes_payload,
                "origin_preview": build_preview(origin_text),
                "origin_normalized_preview": build_preview(normalized_origin_text),
                "mm_preview": build_preview(mm_text),
                "stream_probe": probe_result,
                "clean_video_generated": clean_generated,
                "translation_qa_path": relative_to_workspace(translation_qa_path),
                "translation_qa": translation_qa_payload,
                "translation_incomplete": not bool(translation_qa_payload["complete"]),
                "parse_source_mode": parse_source_mode,
                "parse_source_role": (
                    "preserved_source_audio_helper"
                    if helper_only_parse_source
                    else "subtitle_source_helper"
                ),
                "parse_source_authoritative_for_target": not helper_only_parse_source,
                "target_subtitle_authoritative": not helper_only_parse_source,
            }
        except Exception as exc:
            log_stage("SUB2_FAIL", error=str(exc))
            logger.exception(
                "SUB2_FAIL",
                extra={
                    "task_id": task_id,
                    "step": "subtitles",
                    "stage": "SUB2_FAIL",
                    "asr_backend": asr_backend,
                    "subtitles_backend": backend,
                },
            )
            raise

    if backend == "openai":
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=400,
                detail="OPENAI_API_KEY is not configured for Whisper ASR",
            )

        try:
            from gateway.app.services import subtitles_openai

            if helper_only_parse_source:
                log_stage(
                    "SUB2_TR_SKIPPED_HELPER_ONLY_SOURCE",
                    parse_source_mode=parse_source_mode,
                )
            result = await subtitles_openai.generate_with_openai(
                task_id=task_id,
                target_lang=target_lang,
                force=force,
                translate_enabled=translate_enabled and not helper_only_parse_source,
                use_ffmpeg_extract=use_ffmpeg_extract,
            )
            result["stream_probe"] = probe_result
            result["clean_video_generated"] = clean_generated
            result["parse_source_mode"] = parse_source_mode
            result["parse_source_role"] = (
                "preserved_source_audio_helper"
                if helper_only_parse_source
                else "subtitle_source_helper"
            )
            result["parse_source_authoritative_for_target"] = not helper_only_parse_source
            result["target_subtitle_authoritative"] = not helper_only_parse_source
            return result
        except subtitles_openai.SubtitleError as exc:
            return _write_no_subtitles_placeholders(
                workspace=workspace,
                task_id=task_id,
                reason="openai_subtitles_failed",
                log_stage=log_stage,
            )

    raise HTTPException(status_code=400, detail=f"Unsupported SUBTITLES_BACKEND: {settings.subtitles_backend}")
