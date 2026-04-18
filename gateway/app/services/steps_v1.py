"""Reusable pipeline step functions shared by /v1 routes and background tasks."""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException
import httpx

from gateway.app.ports.storage_provider import get_storage_service
from gateway.app.core.workspace import (
    Workspace,
    deliver_dir,
    deliver_pack_zip_path,
    raw_path,
    relative_to_workspace,
    task_base_dir,
    translated_srt_path,
)
from gateway.app.db import SessionLocal
from gateway.app import config, models
from gateway.app.services.artifact_storage import upload_task_artifact, get_download_url, object_exists, object_head
from gateway.app.services.task_events import append_task_event as _append_task_event
from gateway.app.services.status_policy.registry import get_status_policy
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.dubbing import DubbingError, synthesize_voice
from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
from gateway.app.services.parse import detect_platform, parse_video
from gateway.app.services.publish_service import publish_task_pack
from gateway.app.services.scene_split import run_scenes_build
from gateway.app.services.hot_follow_language_profiles import (
    get_hot_follow_language_profile,
    hot_follow_subtitle_filename,
    hot_follow_subtitle_txt_filename,
)
from gateway.app.services.hot_follow_subtitle_currentness import (
    compute_hot_follow_target_subtitle_currentness,
)
from gateway.app.services.subtitles import generate_subtitles
from gateway.app.services.source_audio_policy import source_audio_policy_from_task
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang, resolve_tts_voice
from gateway.app.services.voice_state import (
    DRY_TTS_CONFIG_KEY,
    DRY_TTS_ROLE,
    is_dry_tts_voiceover_key,
)
from gateway.app.deps import get_task_repository
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage
from gateway.app.schemas import DubRequest, PackRequest, ParseRequest, SubtitlesRequest
from gateway.app.utils.timing import log_step_timing
from gateway.app.services.media_validation import (
    assert_local_audio_ok,
    assert_artifact_ready,
    deliver_key,
    media_meta_from_head,
)

logger = logging.getLogger(__name__)


def _append_event(repo, task_id: str, *, channel: str, code: str, message: str, extra=None) -> None:
    task = repo.get(task_id)
    if not task:
        return
    _append_task_event(
        task,
        channel=channel,
        code=code,
        message=message,
        extra=extra,
    )
    policy_upsert(
        repo,
        task_id,
        task,
        {"events": task.get("events") or []},
        step="steps_v1.event",
        force=False,
    )


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _truthy_env(name: str, default: str = "1") -> bool:
    v = os.getenv(name, default)
    return v is not None and v.strip().lower() not in ("0", "false", "no", "")


def _subtitle_result_contract(result: dict | None) -> tuple[str, str, str, dict[str, object]]:
    payload = dict(result or {})
    origin_text = str(payload.get("origin_srt") or "")
    normalized_origin_text = str(payload.get("origin_normalized_srt") or origin_text or "")
    target_text = str(payload.get("mm_srt") or "")
    translation_qa_raw = payload.get("translation_qa")
    translation_qa = dict(translation_qa_raw) if isinstance(translation_qa_raw, dict) else {}
    if "complete" not in translation_qa:
        translation_qa["complete"] = not bool(payload.get("translation_incomplete"))
    return origin_text, normalized_origin_text, target_text, translation_qa


async def _hydrate_raw_from_url(
    *,
    task_id: str,
    task: dict,
    final_video_url: str | None,
    repo,
    force: bool = False,
) -> str:
    raw_file = raw_path(task_id)
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_key = task.get("raw_path")

    if raw_key and not force:
        if raw_file.exists():
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="hydrate_raw.skip",
                message="Raw already present; skip hydrate",
                extra={"raw_key": raw_key},
            )
            return raw_key
        try:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="hydrate_raw.start",
                message="Hydrate raw from storage",
                extra={"raw_key": raw_key, "source": "storage"},
            )
            storage = get_storage_service()
            storage.download_file(raw_key, str(raw_file))
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="hydrate_raw.done",
                message="Hydrate raw done",
                extra={"raw_key": raw_key, "source": "storage"},
            )
            return raw_key
        except Exception as exc:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="hydrate_raw.error",
                message="Hydrate raw from storage failed",
                extra={"raw_key": raw_key, "source": "storage", "message": str(exc)},
            )
            if not final_video_url:
                raise

    if not final_video_url:
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="hydrate_raw.error",
            message="Missing final_video_url for raw hydrate",
        )
        raise RuntimeError("final_video_url missing for raw hydrate")

    host = urlparse(final_video_url).netloc if final_video_url else ""
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="hydrate_raw.start",
        message="Hydrate raw from url",
        extra={"source": "url", "source_host": host},
    )
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.get(final_video_url)
        resp.raise_for_status()
        raw_file.write_bytes(resp.content)
    raw_key = upload_task_artifact(task, raw_file, "raw.mp4", task_id=task_id)
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="hydrate_raw.done",
        message="Hydrate raw done",
        extra={"raw_key": raw_key, "source": "url", "source_host": host},
    )
    return raw_key


def _truthy_env(name: str, default: str = "1") -> bool:
    v = os.getenv(name, default)
    return v is not None and v.strip().lower() not in ("0", "false", "no", "")

# -------------------------
# Artifact name conventions
# -------------------------
# 寮哄埗鎵€鏈?key 閮借惤鍒?artifacts/ 涓嬶紝纭繚 /files/<key> 璺緞涓€鑷淬€佸彲棰勬湡
RAW_ARTIFACT = "raw/raw.mp4"
ORIGIN_SRT_ARTIFACT = "subs/origin.srt"
TRANSLATION_QA_ARTIFACT = "subs/translation_qa.json"
VOICE_ALIGNMENT_ARTIFACT = "dub/voice_alignment.json"

README_TEMPLATE = """CapCut pack usage

1. Create a new CapCut project and import the extracted zip files.
2. Place raw/raw.mp4 on the video track.
3. Import subs/{subtitle_filename} and adjust styling.
4. Place audio/{audio_filename} on the audio track and align with subtitles.
5. Add transitions or stickers as needed.
"""


class PackError(Exception):
    """Raised when packing fails."""


_SRT_TIME_RE = re.compile(
    r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}"
)


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


def _ensure_txt_from_srt(dst_txt: Path, src_srt: Path) -> None:
    srt_text = src_srt.read_text(encoding="utf-8")
    dst_txt.write_text(_srt_to_txt(srt_text), encoding="utf-8")


def _ensure_silence_audio_ffmpeg(out_path: Path, seconds: int = 1) -> None:
    """Create a silent WAV via ffmpeg."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PackError("ffmpeg not found in PATH (required). Please install ffmpeg.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=16000:cl=mono",
        "-t",
        str(seconds),
        "-acodec",
        "pcm_s16le",
        str(out_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        raise PackError(f"ffmpeg silence generation failed: {p.stderr[-800:]}")


def _ensure_mp3_audio(src_path: Path, dst_path: Path) -> Path:
    if src_path.suffix.lower() == ".mp3":
        return src_path

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PackError("ffmpeg not found in PATH (required for mp3 conversion).")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src_path),
        "-codec:a",
        "libmp3lame",
        str(dst_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not dst_path.exists() or dst_path.stat().st_size == 0:
        raise PackError(f"ffmpeg mp3 conversion failed: {p.stderr[-800:]}")
    return dst_path


def _parse_srt_time(value: str) -> float:
    h, m, rest = value.replace(",", ".").split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _parse_srt_cues(srt_text: str) -> list[dict]:
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
            start_sec = _parse_srt_time(left)
            end_sec = _parse_srt_time(right)
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


def _ffmpeg_concat_mp3(inputs: list[Path], output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise DubbingError("ffmpeg not found in PATH")
    if not inputs:
        raise DubbingError("no audio segments to concatenate")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_path = output_path.parent / "segments.concat.txt"
    with list_path.open("w", encoding="utf-8") as f:
        for item in inputs:
            f.write(f"file '{item.as_posix()}'\n")
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c:a",
        "libmp3lame",
        str(output_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        raise DubbingError(f"ffmpeg concat failed: {p.stderr[-800:]}")


def _build_atempo_chain(speed: float) -> str:
    value = max(0.5, float(speed))
    parts: list[str] = []
    while value > 2.0 + 1e-9:
        parts.append("atempo=2.0")
        value /= 2.0
    while value < 0.5 - 1e-9:
        parts.append("atempo=0.5")
        value /= 0.5
    parts.append(f"atempo={value:.6f}")
    return ",".join(parts)


def _ffmpeg_atempo(src_path: Path, dst_path: Path, speed: float) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise DubbingError("ffmpeg not found in PATH")
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src_path),
        "-filter:a",
        _build_atempo_chain(speed),
        "-c:a",
        "libmp3lame",
        str(dst_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not dst_path.exists() or dst_path.stat().st_size == 0:
        raise DubbingError(f"ffmpeg atempo failed: {p.stderr[-800:]}")


def _ffmpeg_silence_mp3(out_path: Path, duration_sec: float) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise DubbingError("ffmpeg not found in PATH")
    duration = max(0.0, float(duration_sec))
    if duration <= 0:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=24000:cl=mono",
        "-t",
        f"{duration:.6f}",
        "-c:a",
        "libmp3lame",
        str(out_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        raise DubbingError(f"ffmpeg silence failed: {p.stderr[-800:]}")


def _mix_with_bgm_if_configured(task_id: str, audio_file: Path, workspace: Workspace) -> Path:
    repo = get_task_repository()
    task = repo.get(task_id) or {}
    config = task.get("config") if isinstance(task, dict) else None
    if not isinstance(config, dict):
        return audio_file
    bgm = config.get("bgm")
    if not isinstance(bgm, dict):
        return audio_file

    bgm_key = str(bgm.get("bgm_key") or "").strip()
    if not bgm_key:
        return audio_file
    strategy = str(bgm.get("strategy") or "replace").strip().lower()
    if strategy == "mute":
        return audio_file

    mix_ratio = bgm.get("mix_ratio")
    try:
        ratio = float(mix_ratio if mix_ratio is not None else 0.8)
    except Exception:
        ratio = 0.8
    ratio = max(0.0, min(1.0, ratio))

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise PackError("ffmpeg not found in PATH (required for BGM mix).")

    bgm_ext = Path(bgm_key).suffix or ".mp3"
    bgm_local = workspace.audio_dir / f"user_bgm{bgm_ext}"
    bgm_local.parent.mkdir(parents=True, exist_ok=True)
    storage = get_storage_service()
    storage.download_file(bgm_key, str(bgm_local))

    output_audio = workspace.audio_dir / "voice_mix_pack.mp3"
    base_weight = max(0.0, 1.0 - ratio)
    bgm_weight = ratio
    filter_complex = (
        f"[0:a]volume={base_weight}[base];"
        f"[1:a]volume={bgm_weight}[bgm];"
        "[base][bgm]amix=inputs=2:duration=first:dropout_transition=2[mix]"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(audio_file),
        "-i",
        str(bgm_local),
        "-filter_complex",
        filter_complex,
        "-map",
        "[mix]",
        "-c:a",
        "libmp3lame",
        str(output_audio),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0 or not output_audio.exists() or output_audio.stat().st_size == 0:
        raise PackError(f"ffmpeg bgm mix failed: {proc.stderr[-800:]}")
    return output_audio


def _clean_text_for_dub(text: str) -> str:
    return re.sub(r"[\W_]+", "", text or "", flags=re.UNICODE)


def _pick_mm_text_fallback(
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
        txt = _srt_to_txt(srt_text).strip()
        if txt:
            return txt, "mm_srt"
    edited = str(edited_text or "").strip()
    if edited:
        return edited, "edited_text"
    return None, None


def _resolve_mm_txt_text(
    *,
    mm_txt_text: str | None,
    override_text: str | None,
    edited_text: str | None,
    mm_srt_text: str | None,
) -> tuple[str, bool, str | None]:
    current = str(mm_txt_text or "").strip()
    if current and current.lower() != "no subtitles":
        return current, False, "mm_txt"
    fallback_text, fallback_source = _pick_mm_text_fallback(
        override_text=override_text,
        edited_text=edited_text,
        mm_srt_text=mm_srt_text,
    )
    if fallback_text:
        return str(fallback_text).strip(), True, fallback_source
    return current, False, None


def _write_no_dub_note(task_id: str, reason: str) -> Path:
    note_path = task_base_dir(task_id) / "dub" / "no_dub.txt"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    note_path.write_text(f"{ts} reason={reason}\n", encoding="utf-8")
    return note_path


def _remove_no_dub_note(task_id: str) -> None:
    note_path = task_base_dir(task_id) / "dub" / "no_dub.txt"
    try:
        if note_path.exists():
            note_path.unlink()
    except Exception:
        logger.warning("DUB3_NO_DUB_NOTE_CLEAR_FAIL task=%s path=%s", task_id, note_path)


def _clear_no_dub_pipeline_flags(task_id: str, current_task: dict | None = None) -> dict[str, str]:
    repo = get_task_repository()
    task_obj = current_task if isinstance(current_task, dict) else (repo.get(task_id) or {})
    pipeline_config = parse_pipeline_config(task_obj.get("pipeline_config") if isinstance(task_obj, dict) else None)
    if "no_dub" not in pipeline_config and "dub_skip_reason" not in pipeline_config:
        _remove_no_dub_note(task_id)
        return pipeline_config
    pipeline_config.pop("no_dub", None)
    pipeline_config.pop("dub_skip_reason", None)
    _update_task(
        task_id,
        pipeline_config=pipeline_config_to_storage(pipeline_config),
        dub_skip_reason=None,
    )
    _remove_no_dub_note(task_id)
    return pipeline_config


def _ensure_silent_wav(path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=mono:sample_rate=24000",
            "-t",
            "0.2",
            "-q:a",
            "9",
            "-acodec",
            "pcm_s16le",
            str(path),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0 and path.exists():
            return
    # Fallback: create empty placeholder
    path.write_bytes(b"")


def _fail_dub(req: DubRequest, reason: str, provider: str | None, *, status_code: int = 500) -> None:
    try:
        repo = get_task_repository()
        _append_event(
            repo,
            req.task_id,
            channel="pipeline",
            code="post.dub.fail",
            message=reason,
            extra={"reason": reason, "provider": provider, "voice_id": req.voice_id},
        )
    except Exception:
        logger.exception("post.dub.fail event append failed", extra={"task_id": req.task_id})
    _update_task(
        req.task_id,
        last_step="dub",
        dub_status="failed",
        dub_error=reason,
        error_reason="dub_failed",
        mm_audio_key=None,
        mm_audio_path=None,
        mm_audio_bytes=None,
        mm_audio_duration_ms=None,
        mm_audio_mime=None,
    )
    logger.info(
        "DUB3_FAIL",
        extra={
            "task_id": req.task_id,
            "step": "dub",
            "stage": "DUB3_FAIL",
            "dub_provider": provider,
            "voice_id": req.voice_id,
            "reason": reason,
        },
    )
    raise HTTPException(status_code=status_code, detail=reason)


def _skip_empty_dub(req: DubRequest, reason: str, provider: str | None, current_task: dict | None = None) -> dict:
    repo = get_task_repository()
    task_obj = current_task if isinstance(current_task, dict) else (repo.get(req.task_id) or {})
    pipeline_config = parse_pipeline_config(task_obj.get("pipeline_config"))
    pipeline_config.update({"no_dub": "true", "dub_skip_reason": reason})
    current_config = dict(task_obj.get("config") or {})
    try:
        _write_no_dub_note(req.task_id, reason)
    except Exception:
        logger.exception("DUB3_NO_DUB_NOTE_FAIL", extra={"task_id": req.task_id, "reason": reason})
    try:
        _append_event(
            repo,
            req.task_id,
            channel="pipeline",
            code="post.dub.skip",
            message=reason,
            extra={"reason": reason, "provider": provider, "voice_id": req.voice_id},
        )
    except Exception:
        logger.exception("post.dub.skip event append failed", extra={"task_id": req.task_id})
    _update_task(
        req.task_id,
        last_step="dub",
        dub_status="skipped",
        dub_error=None,
        error_reason=None,
        compose_status="pending",
        mm_audio_key=None,
        mm_audio_path=None,
        mm_audio_bytes=None,
        mm_audio_duration_ms=None,
        mm_audio_mime=None,
        audio_sha256=None,
        pipeline_config=pipeline_config_to_storage(pipeline_config),
        config={
            **current_config,
            DRY_TTS_CONFIG_KEY: None,
            "tts_completed_token": None,
            "tts_voiceover_asset_role": None,
        },
    )
    logger.info(
        "DUB3_SKIP",
        extra={
            "task_id": req.task_id,
            "step": "dub",
            "stage": "DUB3_SKIP",
            "dub_provider": provider,
            "voice_id": req.voice_id,
            "reason": reason,
        },
    )
    return {
        "task_id": req.task_id,
        "voice_id": req.voice_id,
        "audio_mm_url": None,
        "duration_sec": None,
        "audio_path": None,
        "dub_status": "skipped",
        "dub_skip_reason": reason,
    }


def _maybe_fill_missing_for_pack(*, raw_path: Path, audio_path: Path, subs_path: Path) -> None:
    """Allow pack to proceed by generating silence audio if DUB_SKIP=1."""

    dub_skip = os.getenv("DUB_SKIP", "").strip().lower() in ("1", "true", "yes")
    if not dub_skip:
        return

    if audio_path and not audio_path.exists():
        _ensure_silence_audio_ffmpeg(audio_path, seconds=1)


async def run_parse_step(req: ParseRequest):
    """Run the parse step for the given request."""

    start_time = time.perf_counter()
    platform = None
    try:
        platform = detect_platform(req.link, req.platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await parse_video(req.task_id, req.link, platform_hint=platform)

        title = (result.get("title") if isinstance(result, dict) else None)
        cover = (result.get("cover") if isinstance(result, dict) else None)
        logger.info(
            "PARSE_RESULT task=%s keys=%s title=%s has_cover=%s cover_head=%s",
            req.task_id,
            sorted(list(result.keys())) if isinstance(result, dict) else str(type(result)),
            (title[:80] if isinstance(title, str) else title),
            bool(cover),
            (str(cover)[:80] if cover else None),
        )

        raw_file = raw_path(req.task_id)
        raw_key = None
        if raw_file.exists():
            raw_key = _upload_artifact(req.task_id, raw_file, RAW_ARTIFACT)

        title_from_parse = (title or "").strip() if isinstance(title, str) else ""
        cover_from_parse = (cover or "").strip() if isinstance(cover, str) else ""

        updates = {
            "raw_path": raw_key,
            "platform": (result.get("platform") or platform),
            "parse_status": "done",
            "last_step": "parse",
        }
        if title_from_parse:
            updates["title"] = title_from_parse
        if cover_from_parse:
            updates["cover_url"] = cover_from_parse

        logger.info(
            "PARSE_WRITEBACK_FIELDS task=%s keys=%s title=%s cover_url=%s",
            req.task_id,
            sorted(list(updates.keys())),
            updates.get("title"),
            updates.get("cover_url"),
        )

        _update_task(req.task_id, **updates)

        try:
            repo = get_task_repository()
            task = repo.get(req.task_id)
            logger.info(
                "AFTER_WRITEBACK_TASK_SHAPE task=%s title=%s cover_url=%s platform=%s last_step=%s",
                req.task_id,
                (task or {}).get("title"),
                (task or {}).get("cover_url"),
                (task or {}).get("platform"),
                (task or {}).get("last_step"),
            )
        except Exception:
            logger.exception("TASK_AFTER_PARSE_UPDATE_FAILED")
        return result

    except HTTPException as exc:
        _update_task(req.task_id, parse_status="error", parse_error=str(exc.detail))
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error in parse step for task %s", req.task_id)
        _update_task(req.task_id, parse_status="error", parse_error=str(exc))
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {exc}") from exc
    finally:
        log_step_timing(
            logger,
            task_id=req.task_id,
            step="parse",
            start_time=start_time,
            provider=platform,
        )


async def run_subtitles_step(req: SubtitlesRequest):
    """Run the subtitles step for the given request."""

    start_time = time.perf_counter()
    asr_backend = os.getenv("ASR_BACKEND") or "whisper"
    subtitles_backend = os.getenv("SUBTITLES_BACKEND") or "gemini"
    logger.info(
        "SUB2_START",
        extra={
            "task_id": req.task_id,
            "step": "subtitles",
            "stage": "SUB2_START",
            "asr_backend": asr_backend,
            "subtitles_backend": subtitles_backend,
            "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
        },
    )
    try:
        _update_task(req.task_id, subtitles_status="running", subtitles_error=None)
        repo = get_task_repository()
        task_before = repo.get(req.task_id) or {}
        source_audio_policy = source_audio_policy_from_task(task_before)
        parse_source_mode = (
            "preserved_source_audio_helper"
            if source_audio_policy == "preserve"
            else "raw_video_audio"
        )
        # Fast-path: skip Whisper when pipeline already recorded no_subtitles from a
        # previous run AND the caller did not explicitly force re-extraction.
        if not req.force:
            try:
                _fast_repo = get_task_repository()
                _fast_task = _fast_repo.get(req.task_id) or {}
                _fast_pc = parse_pipeline_config(_fast_task.get("pipeline_config"))
                if _fast_pc.get("no_subtitles") == "true":
                    from gateway.app.core.workspace import Workspace as _WS
                    from gateway.app.steps.subtitles import _write_no_subtitles_placeholders as _wnsp
                    _ws = _WS(req.task_id)
                    result = _wnsp(workspace=_ws, task_id=req.task_id, reason="cached_no_subtitles", log_stage=lambda *a, **k: None)
                    # fall through to normal result handling below
                else:
                    result = None
            except Exception:
                result = None
        else:
            result = None
        if result is None:
            step_timeout_sec = _env_int("SUBTITLES_STEP_TIMEOUT_SEC", 7200)
            result = await asyncio.wait_for(
                generate_subtitles(
                    task_id=req.task_id,
                    target_lang=req.target_lang,
                    force=req.force,
                    translate_enabled=req.translate,
                    use_ffmpeg_extract=True,
                    parse_source_mode=parse_source_mode,
                ),
                timeout=step_timeout_sec,
            )
        probe = result.get("stream_probe") if isinstance(result, dict) else None
        clean_generated = bool(result.get("clean_video_generated")) if isinstance(result, dict) else False
        no_subtitles_flag = bool(result.get("no_subtitles")) if isinstance(result, dict) else False
        translation_incomplete = bool(result.get("translation_incomplete")) if isinstance(result, dict) else False
        updates: dict[str, str] = {}
        if no_subtitles_flag:
            updates["no_subtitles"] = "true"
        if isinstance(result, dict) and "translation_incomplete" in result:
            updates["translation_incomplete"] = "true" if translation_incomplete else "false"
        if isinstance(result, dict):
            if result.get("parse_source_mode"):
                updates["parse_source_mode"] = str(result.get("parse_source_mode"))
            if result.get("parse_source_role"):
                updates["parse_source_role"] = str(result.get("parse_source_role"))
            if "parse_source_authoritative_for_target" in result:
                updates["parse_source_authoritative_for_target"] = (
                    "true" if bool(result.get("parse_source_authoritative_for_target")) else "false"
                )
            if "target_subtitle_authoritative" in result:
                updates["target_subtitle_authoritative"] = (
                    "true" if bool(result.get("target_subtitle_authoritative")) else "false"
                )
        if isinstance(probe, dict):
            has_audio = probe.get("has_audio")
            if has_audio is True:
                updates["has_audio"] = "true"
            elif has_audio is False:
                updates["has_audio"] = "false"
            has_sub = probe.get("has_subtitle_stream")
            if has_sub is True:
                updates["subtitle_stream"] = "true"
            elif has_sub is False:
                updates["subtitle_stream"] = "false"
            subtitle_codecs = probe.get("subtitle_codecs") or []
            if isinstance(subtitle_codecs, list) and subtitle_codecs:
                updates["subtitle_codecs"] = ",".join([str(v) for v in subtitle_codecs if str(v).strip()])
            audio_codecs = probe.get("audio_codecs") or []
            if isinstance(audio_codecs, list) and audio_codecs:
                updates["audio_codecs"] = ",".join([str(v) for v in audio_codecs if str(v).strip()])
        if clean_generated:
            updates["clean_video_generated"] = "true"
        _update_pipeline_config(req.task_id, updates)
        origin_text, normalized_origin_text, mm_text, translation_qa_payload = _subtitle_result_contract(result)
        target_subtitle_authoritative = bool(
            not isinstance(result, dict)
            or result.get("target_subtitle_authoritative", True)
        )

        workspace = Workspace(req.task_id, target_lang=req.target_lang)
        subtitle_filename = hot_follow_subtitle_filename(req.target_lang)
        subtitle_txt_filename = hot_follow_subtitle_txt_filename(req.target_lang)

        origin_key = None
        mm_key = None
        mm_txt_key = None
        translation_qa_key = None

        if workspace.origin_srt_path.exists():
            origin_key = _upload_artifact(req.task_id, workspace.origin_srt_path, ORIGIN_SRT_ARTIFACT)

        if target_subtitle_authoritative and workspace.mm_srt_path.exists():
            mm_key = _upload_artifact(req.task_id, workspace.mm_srt_path, f"subs/{subtitle_filename}")

            mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
            if mm_txt_path.exists():
                mm_txt_key = _upload_artifact(req.task_id, mm_txt_path, f"subs/{subtitle_txt_filename}")
        translation_qa_path = workspace.subtitles_dir / "translation_qa.json"
        if translation_qa_path.exists():
            translation_qa_key = _upload_artifact(req.task_id, translation_qa_path, TRANSLATION_QA_ARTIFACT)

        subtitles_dir = deliver_dir() / "subtitles" / req.task_id
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        if workspace.origin_srt_path.exists():
            shutil.copy2(workspace.origin_srt_path, subtitles_dir / "origin.srt")
        if target_subtitle_authoritative and workspace.mm_srt_path.exists():
            shutil.copy2(workspace.mm_srt_path, subtitles_dir / subtitle_filename)
        if translation_qa_path.exists():
            shutil.copy2(translation_qa_path, subtitles_dir / "translation_qa.json")
        if workspace.segments_json.exists():
            shutil.copy2(workspace.segments_json, subtitles_dir / "subtitles.json")
        subtitles_key = relative_to_workspace(subtitles_dir / "subtitles.json")
        target_subtitle_currentness = compute_hot_follow_target_subtitle_currentness(
            target_lang=req.target_lang,
            target_text=mm_text,
            source_texts=(normalized_origin_text, origin_text),
            subtitle_artifact_exists=bool(mm_key),
            expected_subtitle_source=subtitle_filename,
            actual_subtitle_source=subtitle_filename if mm_key else None,
            translation_incomplete=not bool(translation_qa_payload.get("complete")),
            has_saved_revision=False,
        )

        _update_task(
            req.task_id,
            origin_srt_path=origin_key,
            mm_srt_path=mm_key,
            last_step="subtitles",
            subtitles_status="ready",
            subtitles_key=subtitles_key,
            subtitle_structure_path=subtitles_key,
            subtitles_error=None,
            target_subtitle_current=bool(target_subtitle_currentness.get("target_subtitle_current")),
            target_subtitle_current_reason=target_subtitle_currentness.get("target_subtitle_current_reason"),
        )
        logger.info(
            "SUB2_DONE",
            extra={
                "task_id": req.task_id,
                "step": "subtitles",
                "stage": "SUB2_DONE",
                "asr_backend": asr_backend,
                "subtitles_backend": subtitles_backend,
                "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
                "origin_srt_key": origin_key,
                "mm_srt_key": mm_key,
                "mm_txt_key": mm_txt_key,
                "translation_qa_key": translation_qa_key,
                "subtitles_key": subtitles_key,
            },
        )
        return result

    except asyncio.TimeoutError:
        _update_task(req.task_id, subtitles_status="error", subtitles_error="timeout")
        raise HTTPException(status_code=504, detail="subtitles timeout")
    except asyncio.CancelledError:
        _update_task(req.task_id, subtitles_status="error", subtitles_error="cancelled")
        raise
    except HTTPException as exc:
        _update_task(
            req.task_id,
            subtitles_status="error",
            subtitles_error=f"{exc.status_code}: {exc.detail}",
        )
        logger.error(
            "Subtitles failed",
            extra={
                "task_id": req.task_id,
                "step": "subtitles",
                "phase": "exception",
                "provider": subtitles_backend,
            },
            exc_info=True,
        )
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error in subtitles step for task %s", req.task_id)
        _update_task(req.task_id, subtitles_status="error", subtitles_error=str(exc))
        raise HTTPException(status_code=500, detail="internal error") from exc
    finally:
        provider = os.getenv("SUBTITLES_BACKEND", None)
        log_step_timing(
            logger,
            task_id=req.task_id,
            step="subtitles",
            start_time=start_time,
            provider=provider,
        )


async def run_dub_step(req: DubRequest):
    """Run the dubbing step for the given request."""

    start_time = time.perf_counter()
    settings = config.get_settings()
    provider = normalize_provider(getattr(req, "provider", None) or os.getenv("DUB_PROVIDER", None))
    req.target_lang = normalize_target_lang(req.target_lang)
    resolved_voice_id, _ = resolve_tts_voice(
        settings=settings,
        provider=provider,
        target_lang=req.target_lang,
        requested_voice=req.voice_id,
    )
    if not resolved_voice_id:
        _fail_dub(req, "TTS_VOICE_MISSING", provider, status_code=422)
    req.voice_id = resolved_voice_id
    workspace = Workspace(req.task_id, target_lang=req.target_lang)
    subtitle_txt_artifact = f"subs/{hot_follow_subtitle_txt_filename(req.target_lang)}"
    origin_exists = workspace.origin_srt_path.exists()
    mm_exists = workspace.mm_srt_exists()

    logger.info(
        "Dub request",
        extra={
            "task_id": req.task_id,
            "origin_srt_exists": origin_exists,
            "mm_srt_exists": mm_exists,
            "mm_srt_path": str(workspace.mm_srt_path),
        },
    )
    logger.info(
        "DUB3_START",
        extra={
            "task_id": req.task_id,
            "step": "dub",
            "stage": "DUB3_START",
            "dub_provider": provider,
            "voice_id": req.voice_id,
            "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
        },
    )

    pipeline_config = {}
    db = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == req.task_id).first()
        if task:
            pipeline_config = parse_pipeline_config(task.pipeline_config)
    finally:
        db.close()

    if pipeline_config.get("no_subtitles") == "true":
        _fail_dub(req, "NO_SUBTITLES", provider)

    current_task = get_task_repository().get(req.task_id) or {}
    current_config = dict(current_task.get("config") or {}) if isinstance(current_task, dict) else {}
    existing_key_raw = str(current_config.get(DRY_TTS_CONFIG_KEY) or "").strip() or None
    existing_key = existing_key_raw if is_dry_tts_voiceover_key(existing_key_raw) else None
    existing_provider = normalize_provider(
        current_task.get("mm_audio_provider") if isinstance(current_task, dict) else None
    )
    existing_voice = str(
        current_task.get("mm_audio_voice_id") if isinstance(current_task, dict) else ""
    ).strip()
    if not req.force and existing_key:
        try:
            if existing_provider != provider or existing_voice != str(req.voice_id or "").strip():
                raise ValueError("existing dry TTS voice/provider mismatch")
            size, _ = assert_artifact_ready(
                kind="audio",
                key=existing_key,
                exists_fn=object_exists,
                head_fn=object_head,
            )
            logger.info(
                "DUB3_SKIP",
                extra={
                    "task_id": req.task_id,
                    "step": "dub",
                    "stage": "DUB3_SKIP",
                    "dub_provider": provider,
                    "voice_id": req.voice_id,
                    "reason": "VALID_EXISTING_AUDIO",
                    "size": size,
                    "key": existing_key,
                },
            )
            _update_task(
                req.task_id,
                mm_audio_path=existing_key,
                mm_audio_key=existing_key,
                last_step="dub",
                dub_status="ready",
                dub_error=None,
                config={
                    **current_config,
                    DRY_TTS_CONFIG_KEY: existing_key,
                    "tts_voiceover_asset_role": DRY_TTS_ROLE,
                },
            )
            return {
                "task_id": req.task_id,
                "voice_id": req.voice_id,
                "audio_mm_url": f"/v1/tasks/{req.task_id}/audio_mm",
                "duration_sec": None,
                "audio_path": None,
            }
        except Exception:
            meta = object_head(existing_key)
            size, _ = media_meta_from_head(meta)
        logger.info(
            "DUB3_REGEN",
            extra={
                "task_id": req.task_id,
                "step": "dub",
                "stage": "DUB3_REGEN",
                "dub_provider": provider,
                "voice_id": req.voice_id,
                "reason": "INVALID_EXISTING_AUDIO",
                "size": size,
                "key": existing_key,
            },
        )

    mm_txt_path = workspace.mm_txt_path
    mm_txt_exists = mm_txt_path.exists()
    mm_txt_text = ""
    if mm_txt_exists:
        try:
            mm_txt_text = mm_txt_path.read_text(encoding="utf-8")
        except Exception:
            mm_txt_text = ""
    mm_srt_text = ""
    if workspace.mm_srt_path.exists():
        try:
            mm_srt_text = workspace.mm_srt_path.read_text(encoding="utf-8")
        except Exception:
            mm_srt_text = ""
    mm_txt_resolved, used_fallback, fallback_source = _resolve_mm_txt_text(
        mm_txt_text=mm_txt_text,
        override_text=req.mm_text,
        edited_text=workspace.read_mm_edited_text(),
        mm_srt_text=mm_srt_text,
    )
    if used_fallback and mm_txt_resolved:
        mm_txt_path.parent.mkdir(parents=True, exist_ok=True)
        mm_txt_path.write_text(mm_txt_resolved + "\n", encoding="utf-8")
        mm_txt_key = _upload_artifact(req.task_id, mm_txt_path, subtitle_txt_artifact)
        if mm_txt_key:
            _update_task(req.task_id, mm_txt_path=mm_txt_key)
        logger.info(
            "DUB3_MM_TXT_FALLBACK",
            extra={
                "task_id": req.task_id,
                "step": "dub",
                "source": fallback_source,
                "mm_txt_path": str(mm_txt_path),
                "mm_txt_key": mm_txt_key,
            },
        )
    mm_txt_text = mm_txt_resolved
    if str(mm_txt_text or "").strip().lower() == "no subtitles":
        return _skip_empty_dub(req, "target_subtitle_empty", provider, current_task)
    if not mm_txt_text.strip():
        return _skip_empty_dub(req, "target_subtitle_empty", provider, current_task)

    override_text = (req.mm_text or "").strip()
    mm_text = override_text or mm_txt_text
    text_guard = clean_and_analyze_dub_text(mm_text, req.target_lang)
    mm_text = str(text_guard.get("cleaned_text") or "").strip()
    warning_text = str(text_guard.get("warning") or "").strip()
    if warning_text:
        logger.warning("DUB_TEXT_WARNING task=%s warning=%s", req.task_id, warning_text)
    logger.info(
        "DUB3_TEXT_SOURCE",
        extra={
            "task_id": req.task_id,
            "step": "dub",
            "stage": "DUB3_TEXT_SOURCE",
            "dub_provider": provider,
            "voice_id": req.voice_id,
            "text_source": "override" if override_text else "mm_srt",
            "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
            "text_len": len(mm_text or ""),
            "text_warning": warning_text or None,
        },
    )
    if not mm_text.strip() or not _clean_text_for_dub(mm_text):
        return _skip_empty_dub(req, "dub_input_empty", provider, current_task)
    _clear_no_dub_pipeline_flags(req.task_id, current_task)

    alignment_enabled = _truthy_env("DUB_SEGMENT_ALIGNMENT_ENABLED", "1")
    cues: list[dict] = []
    if alignment_enabled and not override_text and workspace.mm_srt_path.exists():
        try:
            cues = _parse_srt_cues(workspace.mm_srt_path.read_text(encoding="utf-8"))
        except Exception:
            cues = []
    use_segment_alignment = alignment_enabled and not override_text and bool(cues)

    step_timeout_sec = _env_int("DUB_STEP_TIMEOUT_SEC", 900)
    voice_alignment_payload: dict | None = None
    voice_alignment_path: Path | None = None
    try:
        if use_segment_alignment:
            async def _run_segmented_alignment() -> dict:
                segment_dir = workspace.base_dir / "audio" / "segments"
                segment_dir.mkdir(parents=True, exist_ok=True)
                provider_local = provider
                assembled: list[Path] = []
                stretch_samples: list[float] = []
                over_budget_cues = 0
                max_stretch_applied = 1.0

                for pos, cue in enumerate(cues, start=1):
                    cue_text = str(cue.get("text") or "").strip()
                    budget = float(cue.get("budget") or 0.0)

                    if not cue_text or not _clean_text_for_dub(cue_text):
                        if budget > 0:
                            silent_path = segment_dir / f"{pos:04d}_silent.mp3"
                            _ffmpeg_silence_mp3(silent_path, budget)
                            assembled.append(silent_path)
                        continue

                    cue_result = await synthesize_voice(
                        task_id=req.task_id,
                        target_lang=req.target_lang,
                        voice_id=req.voice_id,
                        provider=provider_local,
                        force=True,
                        mm_srt_text=cue_text,
                        workspace=workspace,
                    )
                    cue_provider = cue_result.get("provider") if isinstance(cue_result, dict) else None
                    if isinstance(cue_provider, str) and cue_provider.strip():
                        provider_local = cue_provider.strip()

                    cue_audio_value = cue_result.get("audio_path") if isinstance(cue_result, dict) else None
                    cue_audio_path = Path(cue_audio_value) if cue_audio_value else workspace.mm_audio_path
                    if not cue_audio_path.is_absolute():
                        cue_audio_path = workspace.mm_audio_path
                    if not cue_audio_path.exists():
                        raise DubbingError("TTS_EMPTY_AUDIO: missing per-cue output")

                    cue_raw_mp3 = segment_dir / f"{pos:04d}_raw.mp3"
                    cue_mp3 = _ensure_mp3_audio(cue_audio_path, cue_raw_mp3)
                    _, cue_duration = assert_local_audio_ok(cue_mp3)
                    aligned_segment = cue_mp3
                    applied_stretch = 1.0

                    if budget > 0:
                        applied_stretch = max(1.0, cue_duration / budget)
                        if cue_duration > budget:
                            applied_stretch = min(applied_stretch, 1.15)
                            # Over-budget cues must be sped up to fit, not slowed down.
                            speed = max(1.0, min(2.0, applied_stretch))
                            fitted_path = segment_dir / f"{pos:04d}_fit.mp3"
                            _ffmpeg_atempo(cue_mp3, fitted_path, speed)
                            aligned_segment = fitted_path
                            _, cue_duration = assert_local_audio_ok(aligned_segment)
                        max_stretch_applied = max(max_stretch_applied, applied_stretch)
                        stretch_samples.append(applied_stretch)
                        if cue_duration > budget + 0.02:
                            over_budget_cues += 1

                    assembled.append(aligned_segment)

                    if budget > 0 and cue_duration < budget - 0.02:
                        pad_path = segment_dir / f"{pos:04d}_pad.mp3"
                        _ffmpeg_silence_mp3(pad_path, budget - cue_duration)
                        assembled.append(pad_path)

                    if pos < len(cues):
                        next_start = float(cues[pos].get("start") or 0.0)
                        current_end = float(cue.get("end") or cue.get("start") or 0.0)
                        gap = max(0.0, next_start - current_end)
                        if gap > 0.02:
                            gap_path = segment_dir / f"{pos:04d}_gap.mp3"
                            _ffmpeg_silence_mp3(gap_path, gap)
                            assembled.append(gap_path)

                if not assembled:
                    raise DubbingError("TTS_EMPTY_AUDIO: no aligned segments")

                aligned_output = workspace.base_dir / "audio" / "mm_audio_aligned.mp3"
                _ffmpeg_concat_mp3(assembled, aligned_output)
                if aligned_output != workspace.mm_audio_mp3_path:
                    shutil.copy2(aligned_output, workspace.mm_audio_mp3_path)

                nonzero = [s for s in stretch_samples if s > 0]
                avg_rate = (sum(nonzero) / len(nonzero)) if nonzero else 1.0
                alignment_payload_local = {
                    "avg_rate": round(float(avg_rate), 4),
                    "over_budget_cues": int(over_budget_cues),
                    "max_stretch_applied": round(float(max_stretch_applied), 4),
                    "aligned": over_budget_cues == 0,
                }
                return {
                    "audio_path": str(aligned_output),
                    "provider": provider_local,
                    "voice_alignment": alignment_payload_local,
                }

            result = await asyncio.wait_for(_run_segmented_alignment(), timeout=step_timeout_sec)
            voice_alignment_payload = result.get("voice_alignment") if isinstance(result, dict) else None
        else:
            result = await asyncio.wait_for(
                synthesize_voice(
                    task_id=req.task_id,
                    target_lang=req.target_lang,
                    voice_id=req.voice_id,
                    provider=provider,
                    force=True,
                    mm_srt_text=mm_text,
                    workspace=workspace,
                ),
                timeout=step_timeout_sec,
            )
            voice_alignment_payload = {
                "avg_rate": 1.0,
                "over_budget_cues": 0,
                "max_stretch_applied": 1.0,
                "aligned": False,
            }
    except asyncio.TimeoutError:
        _fail_dub(req, "TTS_FAILED_TIMEOUT", provider)
    except asyncio.CancelledError:
        _fail_dub(req, "TTS_FAILED_CANCELLED", provider)
    except DubbingError as exc:
        reason = str(exc)[:160]
        if reason.startswith("TTS_EMPTY_TEXT"):
            _fail_dub(req, reason, provider, status_code=400)
        _fail_dub(req, reason if reason.startswith("TTS_") else f"TTS_FAILED:{reason}", provider)
    except HTTPException as exc:
        _fail_dub(req, f"TTS_FAILED_HTTP_{exc.status_code}", provider)
    except Exception as exc:  # pragma: no cover
        _fail_dub(req, f"TTS_FAILED:{str(exc)[:120]}", provider)

    if voice_alignment_payload is None:
        voice_alignment_payload = {
            "avg_rate": 1.0,
            "over_budget_cues": 0,
            "max_stretch_applied": 1.0,
            "aligned": False,
        }
    voice_alignment_path = workspace.base_dir / "dub" / "voice_alignment.json"
    voice_alignment_path.parent.mkdir(parents=True, exist_ok=True)
    voice_alignment_path.write_text(
        json.dumps(voice_alignment_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    provider_used = result.get("provider") if isinstance(result, dict) else None
    if isinstance(provider_used, str) and provider_used.strip():
        provider = provider_used.strip()
    audio_path_value = result.get("audio_path") if isinstance(result, dict) else None
    audio_key = None
    output_size = 0
    output_duration = 0.0

    if audio_path_value:
        p = Path(audio_path_value)
        if not p.is_absolute():
            p = workspace.mm_audio_path
        if p.exists():
            mp3_path = _ensure_mp3_audio(p, workspace.mm_audio_mp3_path)
            try:
                output_size, output_duration = assert_local_audio_ok(mp3_path)
            except ValueError:
                _fail_dub(req, "EMPTY_OR_INVALID_AUDIO", provider)
            out_key = deliver_key(req.task_id, "voiceover/audio_mm.dry.mp3")
            storage = get_storage_service()
            uploaded_key = storage.upload_file(
                str(mp3_path),
                out_key,
                content_type="audio/mpeg",
            )
            if not uploaded_key:
                _fail_dub(req, "EMPTY_OR_INVALID_AUDIO", provider)
            audio_key = out_key
            logger.info(
                "DUB3_UPLOAD_DONE",
                extra={
                    "task_id": req.task_id,
                    "step": "dub",
                    "stage": "DUB3_UPLOAD_DONE",
                    "dub_provider": provider,
                    "voice_id": req.voice_id,
                    "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
                    "audio_key": audio_key,
                    "output_path": str(mp3_path),
                    "output_size": output_size,
                    "duration_sec": output_duration,
                },
            )

    if not audio_key:
        _fail_dub(req, "EMPTY_OR_INVALID_AUDIO", provider)

    _update_task(
        req.task_id,
        mm_audio_path=audio_key,
        mm_audio_key=audio_key,
        mm_audio_provider=provider,
        dub_provider=provider,
        mm_audio_voice_id=req.voice_id,
        mm_audio_bytes=output_size,
        mm_audio_duration_ms=int(output_duration * 1000),
        mm_audio_mime="audio/mpeg",
        last_step="dub",
        dub_status="ready",
        dub_error=None,
        config={
            **current_config,
            DRY_TTS_CONFIG_KEY: audio_key,
            "tts_voiceover_asset_role": DRY_TTS_ROLE,
        },
    )

    edited_text = workspace.read_mm_edited_text()
    if edited_text and edited_text.strip():
        mm_txt_path = workspace.mm_txt_path
        mm_txt_path.parent.mkdir(parents=True, exist_ok=True)
        mm_txt_path.write_text(edited_text, encoding="utf-8")
        _upload_artifact(req.task_id, mm_txt_path, subtitle_txt_artifact)
    if voice_alignment_path and voice_alignment_path.exists():
        _upload_artifact(req.task_id, voice_alignment_path, VOICE_ALIGNMENT_ARTIFACT)
    _update_pipeline_config(
        req.task_id,
        {
            "voice_alignment_avg_rate": str(voice_alignment_payload.get("avg_rate")),
            "voice_alignment_over_budget_cues": str(voice_alignment_payload.get("over_budget_cues")),
            "voice_alignment_max_stretch_applied": str(voice_alignment_payload.get("max_stretch_applied")),
            "voice_alignment_aligned": "true" if voice_alignment_payload.get("aligned") else "false",
        },
    )

    try:
        audio_url = f"/v1/tasks/{req.task_id}/audio_mm"
        resp = {
            "task_id": req.task_id,
            "voice_id": req.voice_id,
            "audio_mm_url": audio_url,
            "duration_sec": output_duration,
            "audio_path": (result.get("audio_path") or result.get("path")) if isinstance(result, dict) else None,
            "voice_alignment": voice_alignment_payload,
        }
        logger.info(
            "DUB3_DONE",
            extra={
                "task_id": req.task_id,
                "step": "dub",
                "stage": "DUB3_DONE",
                "dub_provider": provider,
                "voice_id": req.voice_id,
                "elapsed_ms": int((time.perf_counter() - start_time) * 1000),
                "audio_key": audio_key,
                "output_size": output_size,
                "duration_sec": output_duration,
            },
        )
        return resp
    finally:
        log_step_timing(
            logger,
            task_id=req.task_id,
            step="dub",
            start_time=start_time,
            provider=provider,
            voice_id=req.voice_id,
        )


async def run_pack_step(req: PackRequest):
    start_time = time.perf_counter()
    task_id = req.task_id
    profile = get_hot_follow_language_profile(req.target_lang)
    workspace = Workspace(task_id, target_lang=req.target_lang)
    subtitle_filename = profile.subtitle_filename
    subtitle_txt_filename = profile.subtitle_txt_filename
    deliverable_audio_filename = profile.dub_filename

    raw_file = raw_path(task_id)
    zip_path = deliver_pack_zip_path(task_id)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # audio锛氫紭鍏?workspace.mm_audio_path锛堜綘鐨?dub 鍙兘杈撳嚭 mp3锛夛紝涓嶅瓨鍦ㄥ垯 fallback 鍒?wav 鍛藉悕
    audio_file = workspace.mm_audio_path
    audio_key = _get_task_mm_audio_key(task_id)
    if audio_key and not audio_file.exists():
        storage = get_storage_service()
        target_path = workspace.mm_audio_mp3_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        storage.download_file(audio_key, str(target_path))
        audio_file = target_path
    if not audio_file.exists():
        wav_candidate = (workspace.audio_dir / f"{task_id}_mm_vo.wav") if hasattr(workspace, "audio_dir") else None
        if wav_candidate and wav_candidate.exists():
            audio_file = wav_candidate
    if audio_file.exists():
        audio_file = _mix_with_bgm_if_configured(task_id, audio_file, workspace)

    subs_mm_srt = translated_srt_path(task_id, profile.internal_lang)
    if not subs_mm_srt.exists() and profile.internal_lang == "vi":
        subs_mm_srt = translated_srt_path(task_id, "mm")
    if not subs_mm_srt.exists():
        subs_mm_srt = translated_srt_path(task_id, "my")
    try:
        _maybe_fill_missing_for_pack(
            raw_path=raw_file,
            audio_path=audio_file,
            subs_path=subs_mm_srt,
        )

        required = [raw_file, audio_file, subs_mm_srt]
        missing = [p for p in required if not p.exists()]
        if missing:
            names = ", ".join(str(p) for p in missing)
            raise PackError(f"missing required files: {names}")

        audio_filename = audio_file.name

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / f"pack_{task_id}"
            tmp_path.mkdir(parents=True, exist_ok=True)

            raw_dir = tmp_path / "raw"
            audio_dir = tmp_path / "audio"
            subs_dir = tmp_path / "subs"
            scenes_dir = tmp_path / "scenes"
            for d in (raw_dir, audio_dir, subs_dir, scenes_dir):
                d.mkdir(parents=True, exist_ok=True)

            audio_filename = deliverable_audio_filename

            shutil.copy(raw_file, raw_dir / "raw.mp4")
            shutil.copy(audio_file, audio_dir / audio_filename)
            shutil.copy(subs_mm_srt, subs_dir / subtitle_filename)

            mm_txt_path = subs_mm_srt.with_suffix(".txt")
            if mm_txt_path.exists():
                shutil.copy(mm_txt_path, subs_dir / subtitle_txt_filename)
            else:
                _ensure_txt_from_srt(subs_dir / subtitle_txt_filename, subs_mm_srt)

            (scenes_dir / ".keep").write_text("", encoding="utf-8")

            manifest = {
                "version": "1.8",
                "pack_type": "capcut_v18",
                "task_id": task_id,
                "language": profile.internal_lang,
                "assets": {
                    "raw_video": "raw/raw.mp4",
                    "voice": f"audio/{audio_filename}",
                    "subtitle": f"subs/{subtitle_filename}",
                    "scenes_dir": "scenes/",
                },
            }
            (tmp_path / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (tmp_path / "README.md").write_text(
                README_TEMPLATE.format(audio_filename=audio_filename, subtitle_filename=subtitle_filename),
                encoding="utf-8",
            )

            pack_prefix = Path("deliver") / "packs" / task_id
            with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
                for item in tmp_path.rglob("*"):
                    if item.is_file():
                        arcname = (pack_prefix / item.relative_to(tmp_path)).as_posix()
                        zf.write(item, arcname=arcname)
    except PackError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not zip_path.exists():
        raise RuntimeError(f"Pack zip not found after packing: {zip_path}")

    zip_key = f"packs/{task_id}/capcut_pack.zip"
    storage = get_storage_service()
    storage.upload_file(str(zip_path), zip_key, content_type="application/zip")

    files = [
        f"deliver/packs/{task_id}/raw/raw.mp4",
        f"deliver/packs/{task_id}/audio/{audio_filename}",
        f"deliver/packs/{task_id}/subs/{subtitle_filename}",
        f"deliver/packs/{task_id}/subs/{subtitle_txt_filename}",
        f"deliver/packs/{task_id}/scenes/.keep",
        f"deliver/packs/{task_id}/manifest.json",
        f"deliver/packs/{task_id}/README.md",
    ]

    _update_task(
        task_id,
        pack_key=zip_key,
        pack_type="capcut_v18",
        pack_status="ready",
        pack_path=None,
        status="ready",
        last_step="pack",
        error_message=None,
        error_reason=None,
    )

    # 杩斿洖鍊煎 UI/璋冭瘯鍙嬪ソ锛氫繚鐣?zip_path/files
    zip_path_value = relative_to_workspace(zip_path) if zip_path.exists() else None
    try:
        download_url = storage.generate_presigned_url(
            zip_key,
            expiration=3600,
            content_type="application/zip",
            filename=f"{task_id}_capcut_pack.zip",
            disposition="attachment",
        )
    except TypeError:
        download_url = storage.generate_presigned_url(zip_key, expiration=3600)
    resp = {
        "task_id": task_id,
        "zip_key": zip_key,
        "pack_key": zip_key,
        "zip_path": zip_path_value,
        "download_url": download_url,
        "files": files,
    }
    try:
        return resp
    finally:
        log_step_timing(
            logger,
            task_id=req.task_id,
            step="pack",
            start_time=start_time,
        )


def compute_subtitles_params(task: dict, payload) -> tuple[str, bool, bool]:
    target_lang = (payload.target_lang if payload else None) or task.get("content_lang") or "my"
    force = payload.force if payload else False
    translate = payload.translate if payload else True
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    if pipeline_config.get("subtitles_mode") == "whisper-only":
        translate = False
    return target_lang, bool(force), bool(translate)


async def run_subtitles_step_entry(
    *,
    task_id: str,
    target_lang: str,
    force: bool,
    translate: bool,
):
    return await run_subtitles_step(
        SubtitlesRequest(
            task_id=task_id,
            target_lang=target_lang,
            force=force,
            translate=translate,
        )
    )


async def run_apollo_avatar_generate_step(
    *,
    task: dict,
    task_id: str,
    req,
    repo,
    live_enabled: bool,
    force: bool = False,
) -> dict:
    try:
        from gateway.app.services.apollo_avatar_service import ApolloAvatarService
    except Exception as e:
        append_task_event(
            repo,
            task_id,
            "AVATAR_IMPORT_ERROR",
            f"Import ApolloAvatarService failed: {e}",
            level="error",
        )
        raise
    provider_name = getattr(config.settings, "apollo_avatar_provider", "fal_wan26_flash")
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="prepare.start",
        message="Prepare start",
        extra={"task_id": task_id},
    )
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="generate.start",
        message="Generate start",
        extra={
            "provider": provider_name,
            "model": getattr(config.settings, "apollo_avatar_live_model", None),
            "target_duration_sec": getattr(req, "target_duration_sec", None),
            "seed": getattr(req, "seed", None),
            "live": bool(live_enabled),
        },
    )
    existing_final = (
        task.get("apollo_avatar_final_video_key")
        or (task.get("apollo_avatar") or {}).get("final_video_url")
        or (task.get("apollo_avatar") or {}).get("final_video_key")
    )
    if existing_final and not force:
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="generate.skip",
            message="Generate skipped (existing result)",
            extra={"final_video_url": existing_final, "provider": provider_name},
        )
        return {
            "ok": True,
            "task_id": task_id,
            "segments": (task.get("apollo_avatar") or {}).get("segments", []),
            "final_video_url": existing_final,
            "manifest_url": (task.get("apollo_avatar") or {}).get("manifest_url"),
        }
    service = ApolloAvatarService(repo=repo)
    try:
        artifacts = await service.generate_stitch_only(task, req, live_enabled=live_enabled)
    except Exception as exc:
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="generate.error",
            message="Generate error",
            extra={
                "provider": provider_name,
                "stage": "generate",
                "message": str(exc),
                "live": bool(live_enabled),
                "model": getattr(config.settings, "apollo_avatar_live_model", None),
            },
        )
        raise
    first_req_id = None
    if getattr(artifacts, "segments", None):
        for seg in artifacts.segments:
            if getattr(seg, "request_id", None):
                first_req_id = seg.request_id
                break
    if live_enabled and not first_req_id:
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="generate.error",
            message="Generate error: missing request_id",
            extra={
                "provider": provider_name,
                "stage": "generate",
                "message": "missing request_id",
                "live": True,
            },
        )
        raise RuntimeError("Live generate missing request_id")
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="generate.done",
        message="Generate done",
        extra={
            "provider": provider_name,
            "request_id": first_req_id,
            "final_video_url": getattr(artifacts, "final_video_url", None),
        },
    )

    plan = getattr(artifacts, "plan", None)
    segments = []
    if plan and getattr(plan, "segments", None):
        segments = [
            {"idx": s.idx, "duration_sec": s.duration_sec}
            for s in plan.segments
            if s is not None
        ]
    if segments:
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="slice.done",
            message="Slice done",
            extra={"segments": segments},
        )

    raw_key = None
    final_url = getattr(artifacts, "final_video_url", None)
    if final_url or task.get("raw_path"):
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="assemble.start",
            message="Assemble start",
        )
        try:
            raw_key = await _hydrate_raw_from_url(
                task_id=task_id,
                task=task,
                final_video_url=final_url,
                repo=repo,
                force=force,
            )
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="assemble.done",
                message="Assemble done",
                extra={"raw_key": raw_key},
            )
        except Exception as exc:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="assemble.error",
                message="Assemble error",
                extra={"error": str(exc)},
            )
            raise

    def _dump(obj):
        if obj is None:
            return None
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    policy_upsert(
        repo,
        task_id,
        task,
        {
            "last_step": "apollo_avatar_generate",
            "status": "processing",
            "apollo_avatar_manifest_key": artifacts.manifest_url,
            "apollo_avatar_final_video_key": artifacts.final_video_url,
            "apollo_avatar": _dump(artifacts),
            "raw_path": raw_key,
        },
        step="steps_v1.apollo_avatar_generate",
        force=force,
    )
    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="prepare.done",
        message="Prepare done",
        extra={"raw_key": raw_key},
    )
    return {
        "ok": True,
        "task_id": task_id,
        "segments": [_dump(s) for s in (getattr(artifacts, "segments", None) or [])],
        "final_video_url": artifacts.final_video_url,
        "manifest_url": artifacts.manifest_url,
    }


async def run_post_generate_pipeline(
    *,
    task_id: str,
    repo,
    target_lang: str | None = None,
    translate: bool | None = None,
    voice_id: str | None = None,
    force: bool = False,
):
    """
    After a task got its raw.mp4 hydrated (apollo_avatar_generate),
    run subtitles -> dub -> pack in order.

    - Idempotent: skips steps already ready.
    - Extensible: centralized orchestration for future kinds/steps.
    """

    if not _truthy_env("AUTO_RUN_PIPELINE_AFTER_GENERATE", "1"):
        logger.info(
            "AUTO_RUN_PIPELINE_AFTER_GENERATE disabled; skip post-generate pipeline",
            extra={"task_id": task_id},
        )
        return

    task = repo.get(task_id)
    if not task:
        logger.warning("Task not found in post-generate pipeline", extra={"task_id": task_id})
        return

    is_apollo = str(task.get("kind") or task.get("category_key") or task.get("platform") or "").lower() == "apollo_avatar"
    pack_key = task.get("pack_key") or task.get("pack_path")
    pack_status = str(task.get("pack_status") or "").lower()
    if pack_key and pack_status in {"ready"} and not force:
        task = policy_upsert(
            repo,
            task_id,
            task,
            {
                "status": "ready",
                "last_step": task.get("last_step") or "pack",
            },
            step="steps_v1.post_pipeline",
            force=force,
        )
        return

    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    raw_key = task.get("raw_path")
    raw_file = raw_path(task_id)
    if raw_key and not raw_file.exists():
        try:
            storage = get_storage_service()
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            storage.download_file(raw_key, str(raw_file))
        except Exception as exc:
            logger.exception(
                "Failed to hydrate raw file from raw_key before post pipeline",
                extra={"task_id": task_id, "raw_key": raw_key, "error": str(exc)},
            )
            return

    _target_lang = target_lang or task.get("content_lang") or "my"
    _translate = True if translate is None else bool(translate)
    if pipeline_config.get("subtitles_mode") == "whisper-only":
        _translate = False

    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="post.start",
        message="Post pipeline start",
    )

    # Status policy hook (no-op by default; apollo_avatar prevents READY regression when publish bundle exists)
    _policy, _policy_kind = get_status_policy(task)

    def _update(fields: dict) -> None:
        nonlocal task
        task = policy_upsert(
            repo,
            task_id,
            task,
            dict(fields or {}),
            step="steps_v1.update",
            force=force,
        )
        # refresh local cache to avoid stale merges across steps
        task = repo.get(task_id) or task

    # --------- Step 1: Subtitles ---------
    subtitles_ready = (task.get("subtitles_status") == "ready") and bool(task.get("subtitles_key"))
    if not subtitles_ready or force:
        try:
            await run_subtitles_step_entry(
                task_id=task_id,
                target_lang=_target_lang,
                force=force,
                translate=_translate,
            )
        except Exception:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.error",
                message="Subtitles failed",
                extra={"stage": "subtitles"},
            )
            logger.exception("Post-generate subtitles failed", extra={"task_id": task_id})
            _update(
                {
                    "subtitles_status": "failed",
                    "status": "failed",
                    "last_step": "subtitles",
                    "error_message": "subtitles_failed",
                    "error_reason": "subtitles_failed",
                }
            )
            return
    else:
        logger.info("Post-generate: subtitles already ready; skip", extra={"task_id": task_id})

    task = repo.get(task_id) or task
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    subtitles_key = task.get("subtitles_key") or task.get("mm_srt_path")
    if subtitles_key:
        _update(
            {
                "subtitles_key": subtitles_key,
                "subtitles_status": "ready",
                "subtitles_provider": task.get("subtitles_provider") or "gemini",
            }
        )

    # --------- Step 2: Dub ---------
    audio_key = task.get("mm_audio_key") or task.get("mm_audio_path")
    dub_ready = (task.get("dub_status") == "ready") and bool(audio_key)
    if not dub_ready or force:
        try:
            _voice_id = voice_id or pipeline_config.get("voice_id") or pipeline_config.get("dub_voice_id")
            await run_dub_step(
                DubRequest(
                    task_id=task_id,
                    voice_id=_voice_id,
                    force=force,
                )
            )
        except Exception:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.error",
                message="Dub failed",
                extra={"stage": "dub"},
            )
            logger.exception("Post-generate dub failed", extra={"task_id": task_id})
            _update(
                {
                    "dub_status": "failed",
                    "status": "failed",
                    "last_step": "dub",
                    "error_message": "dub_failed",
                    "error_reason": "dub_failed",
                }
            )
            return
    else:
        logger.info("Post-generate: dub already ready; skip", extra={"task_id": task_id})

    task = repo.get(task_id) or task
    audio_key = task.get("mm_audio_key") or task.get("mm_audio_path")
    if audio_key:
        _update(
            {
                "dub_status": "ready",
                "dub_provider": task.get("dub_provider") or "edge-tts",
            }
        )

    # --------- Step 3: Scenes ---------
    scenes_key = task.get("scenes_key")
    scenes_ready = (task.get("scenes_status") == "ready") and bool(scenes_key)
    if is_apollo:
        _update({"scenes_status": "skipped", "scenes_error": None})
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="post.scenes.skip",
            message="Scenes skipped (not applicable)",
        )
    elif not scenes_ready or force:
        logger.info("APOLLO_AVATAR_BUILD_SCENES_START", extra={"task_id": task_id})
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="post.scenes.start",
            message="Scenes build start",
        )
        try:
            res = run_scenes_build(task_id, _update)
            scenes_key = res.get("scenes_key")
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.scenes.done",
                message="Scenes build done",
                extra={"scenes_key": scenes_key},
            )
            logger.info(
                "APOLLO_AVATAR_BUILD_SCENES_DONE",
                extra={"task_id": task_id, "scenes_key": scenes_key},
            )
        except Exception as exc:
            _update({"scenes_status": "failed", "scenes_error": str(exc)})
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.scenes.error",
                message="Scenes build failed",
                extra={"stage": "scenes"},
            )
            logger.exception("Post-generate scenes failed", extra={"task_id": task_id})
    else:
        logger.info("Post-generate: scenes already ready; skip", extra={"task_id": task_id})

    task = repo.get(task_id) or task
    if str(task.get("scenes_status") or "").lower() == "ready":
        _update({"scenes_status": "ready"})

    # --------- Step 3: Pack ---------
    pack_key = task.get("pack_key") or task.get("pack_path")
    pack_ready = (task.get("pack_status") == "ready") and bool(pack_key)
    if not pack_ready or force:
        logger.info("APOLLO_AVATAR_BUILD_PACK_START", extra={"task_id": task_id})
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="post.pack.start",
            message="Pack build start",
        )
        try:
            pack_resp = await run_pack_step(PackRequest(task_id=task_id))
            task = repo.get(task_id) or task
            pack_key = (
                (pack_resp or {}).get("pack_key")
                or task.get("pack_key")
                or task.get("pack_path")
            )
            if pack_key:
                _update(
                    {
                        "pack_key": pack_key,
                        "pack_status": "ready",
                        "pack_provider": task.get("pack_provider") or "capcut",
                    }
                )
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.pack.done",
                message="Pack build done",
                extra={"pack_key": pack_key},
            )
            logger.info(
                "APOLLO_AVATAR_BUILD_PACK_DONE",
                extra={"task_id": task_id, "pack_key": pack_key},
            )
        except Exception:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.error",
                message="Pack failed",
                extra={"stage": "pack"},
            )
            logger.exception("Post-generate pack failed", extra={"task_id": task_id})
            _update(
                {
                    "pack_status": "failed",
                    "status": "failed",
                    "last_step": "pack",
                    "error_message": "pack_failed",
                    "error_reason": "pack_failed",
                }
            )
            return
    else:
        logger.info("Post-generate: pack already ready; skip", extra={"task_id": task_id})

    task = repo.get(task_id) or task
    if str(task.get("pack_status") or "").lower() == "ready":
        _update({"pack_status": "ready", "pack_provider": task.get("pack_provider") or "capcut"})

    # --------- Step 4: Publish bundle ---------
    publish_key = task.get("publish_key")
    publish_ready = (task.get("publish_status") == "ready") and bool(publish_key)
    if not publish_ready or force:
        logger.info("APOLLO_AVATAR_BUILD_PUBLISH_BUNDLE_START", extra={"task_id": task_id})
        _append_event(
            repo,
            task_id,
            channel="apollo_avatar",
            code="post.publish.start",
            message="Publish bundle build start",
        )
        db = SessionLocal()
        try:
            res = publish_task_pack(task_id, db, task_repo=repo, provider=None, force=force)
            publish_key = res.get("publish_key")
            publish_provider = res.get("provider")
            publish_url = res.get("download_url") or ""
            uploaded = False
            if publish_key and not object_exists(str(publish_key)):
                local_path = Path(str(publish_key))
                if local_path.exists():
                    uploaded_key = upload_task_artifact(
                        task, local_path, "deliver/publish/capcut_pack.zip", task_id=task_id
                    )
                    publish_key = uploaded_key
                    publish_provider = "artifact"
                    publish_url = get_download_url(str(uploaded_key))
                    uploaded = True
            task_db = db.query(models.Task).filter(models.Task.id == task_id).first()
            if task_db and not uploaded:
                _update(
                    {
                        "publish_provider": task_db.publish_provider,
                        "publish_key": task_db.publish_key,
                        "publish_url": task_db.publish_url,
                        "publish_status": task_db.publish_status,
                        "published_at": task_db.published_at,
                    }
                )
            else:
                _update(
                    {
                        "publish_provider": publish_provider,
                        "publish_key": publish_key,
                        "publish_url": publish_url,
                        "publish_status": "ready" if publish_key else "failed",
                    }
                )
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.publish.done",
                message="Publish bundle build done",
                extra={"publish_key": publish_key},
            )
            logger.info(
                "APOLLO_AVATAR_BUILD_PUBLISH_BUNDLE_DONE",
                extra={"task_id": task_id, "publish_key": publish_key},
            )
        except Exception as exc:
            _append_event(
                repo,
                task_id,
                channel="apollo_avatar",
                code="post.error",
                message="Publish bundle failed",
                extra={"stage": "publish_bundle"},
            )
            logger.exception("Post-generate publish bundle failed", extra={"task_id": task_id})
            _update({"publish_status": "failed", "publish_error": str(exc)})
            # non-blocking for apollo_avatar
            if not is_apollo:
                return
        finally:
            db.close()
    else:
        logger.info("Post-generate: publish bundle already ready; skip", extra={"task_id": task_id})

    task = repo.get(task_id) or task
    if is_apollo:
        cur_status = str(task.get("status") or "").lower()
        pack_status = str(task.get("pack_status") or "").lower()
        pub_status = str(task.get("publish_status") or "").lower()
        if cur_status not in ("failed", "error"):
            updates = {}
            if pack_status not in ("failed", "error"):
                updates["pack_status"] = "ready"
            if pub_status not in ("failed", "error"):
                updates["publish_status"] = "ready"
            if updates:
                updates["status"] = "ready"
                task = policy_upsert(
                    repo,
                    task_id,
                    task,
                    updates,
                    step="steps_v1.post_pipeline",
                    force=force,
                )
            task = repo.get(task_id) or task
    pack_key = task.get("pack_key") or task.get("pack_path")
    if pack_key:
        if is_apollo:
            _update(
                {
                    "status": "ready",
                    "last_step": "publish" if task.get("publish_key") else "pack",
                    "error_message": None,
                    "error_reason": None,
                }
            )
        else:
            _update(
                {
                    "status": "ready",
                    "last_step": "publish" if task.get("publish_key") else "pack",
                    "error_message": None,
                    "error_reason": None,
                }
            )
    if str(task.get("publish_status") or "").lower() == "ready":
        if not is_apollo:
            _update({"publish_status": "ready"})

    _append_event(
        repo,
        task_id,
        channel="apollo_avatar",
        code="post.done",
        message="Post pipeline done",
        extra={
            "subtitles_status": task.get("subtitles_status"),
            "dub_status": task.get("dub_status"),
            "pack_status": task.get("pack_status"),
            "scenes_status": task.get("scenes_status"),
            "publish_status": task.get("publish_status"),
        },
    )
    logger.info("Post-generate pipeline done", extra={"task_id": task_id})


def _update_task(task_id: str, **fields) -> None:
    """
    娉ㄦ剰锛氳繖閲屽厑璁告妸瀛楁鏄惧紡鏇存柊涓?None锛堜緥濡傛竻鐞?error_message / error_reason锛夈€?    鍙璋冪敤鏂逛紶浜?key锛屽氨浼氬啓鍏ユ暟鎹簱銆?    """
    repo = get_task_repository()
    logger.info(
        "UPDATE_TASK_REPO_BACKEND task=%s repo=%s keys=%s",
        task_id,
        repo.__class__.__name__,
        sorted(list(fields.keys())),
    )
    current = repo.get(task_id) or {}
    policy, _kind = get_status_policy(current)
    updates = policy.reconcile_after_step(
        current,
        step="steps_v1._update_task",
        updates=dict(fields),
        force=True,
    )
    repo.update(task_id, updates)


def _update_pipeline_config(task_id: str, updates: dict[str, str]) -> None:
    if not updates:
        return
    db = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return
        current = parse_pipeline_config(task.pipeline_config)
        current.update(updates)
        repo = get_task_repository()
        policy_upsert(repo, task_id, None, {"pipeline_config": pipeline_config_to_storage(current)}, step="pipeline_config")
    finally:
        db.close()


def _upload_artifact(task_id: str, local_path: Path, artifact_name: str) -> str | None:
    """
    杩斿洖 storage key锛堜緥濡?default/default/<task_id>/artifacts/xxx锛夈€?    """
    db = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return None

        # 鍏抽敭锛氫笉瑕佸啀棰濆浼?task_id=...锛岄伩鍏?wrapper 鍐呴儴绛惧悕鍙樺寲瀵艰嚧閲嶅鍙傛暟
        return upload_task_artifact(task, local_path, artifact_name)
    finally:
        db.close()


def _get_task_mm_audio_key(task_id: str) -> str | None:
    db = SessionLocal()
    try:
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if not task:
            return None
        return getattr(task, "mm_audio_key", None) or getattr(task, "mm_audio_path", None)
    finally:
        db.close()
