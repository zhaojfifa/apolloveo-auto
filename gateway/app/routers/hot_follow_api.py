"""Hot Follow API router — extracted from tasks.py (Phase 1.2 Router Split).

Phase 1.3 Port Merge: all shared helpers now imported from services/,
breaking the circular dependency with tasks.py.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import get_settings
from ..schemas import DubResponse, TaskCreate, TaskDetail

from gateway.app.deps import get_task_repository
from gateway.app.ports.storage_provider import get_storage_service
from gateway.ports.repository import ITaskRepository
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang, public_target_lang, resolve_tts_voice
from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
from gateway.app.services.hot_follow_subtitles import (
    is_srt_text as _service_is_srt_text,
    normalize_target_subtitles_for_save,
)
from gateway.app.steps.subtitles import _parse_srt_to_segments, segments_to_srt
from gateway.app.providers.gemini_subtitles import GeminiSubtitlesError, translate_segments_with_gemini
from gateway.app.services.artifact_storage import (
    upload_task_artifact,
    get_download_url,
    get_object_bytes,
    object_head,
    object_exists,
)
from gateway.app.services.media_validation import (
    MIN_AUDIO_BYTES,
    MIN_VIDEO_BYTES,
    assert_artifact_ready,
    assert_local_audio_ok,
    assert_local_video_ok,
    deliver_key,
    media_meta_from_head,
)
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage
from gateway.app.utils.subtitle_probe import probe_subtitles
from gateway.app.services.scenes_service import build_scenes_for_task
from ..services.steps_v1 import _srt_to_txt
from ..core.workspace import (
    Workspace,
    origin_srt_path,
    deliver_pack_zip_path,
    raw_path,
    relative_to_workspace,
    task_base_dir,
)

# ── Phase 1.3: shared helpers from service modules (NO more tasks.py imports) ─
from gateway.app.core.constants import (
    COMPOSE_RETRY_AFTER_MS,
    DubProviderRequest,
    OP_HEADER_KEY,
    PublishBackfillRequest,
    api_key_header,
)
from gateway.app.services.compose_helpers import (
    build_atempo_chain as _build_atempo_chain,
    compose_in_progress_response as _compose_in_progress_response,
    compute_audio_fit_speeds as _compute_audio_fit_speeds,
    resolve_audio_fit_max_speed as _resolve_audio_fit_max_speed,
    task_compose_lock as _task_compose_lock,
)
from gateway.app.services.media_helpers import (
    probe_url_metadata as _probe_url_metadata,
    sha256_file as _sha256_file,
    update_pipeline_probe as _update_pipeline_probe,
    upload_task_bgm_impl as _upload_task_bgm_impl,
)
from gateway.app.services.task_view_helpers import (
    backfill_compose_done_if_final_ready as _backfill_compose_done_if_final_ready,
    build_translation_qa_summary as _build_translation_qa_summary,
    build_workbench_debug_payload as _build_workbench_debug_payload,
    compose_error_parts as _compose_error_parts,
    compute_composed_state as _compute_composed_state,
    count_srt_cues as _count_srt_cues,
    deliverable_url as _deliverable_url,
    publish_hub_payload as _publish_hub_payload,
    resolve_hub_final_url as _resolve_hub_final_url,
    scene_pack_info as _scene_pack_info,
    scenes_status_from_ssot as _scenes_status_from_ssot,
    task_endpoint as _task_endpoint,
    task_key as _task_key,
    task_to_detail as _task_to_detail,
    task_value as _task_value,
)
from gateway.app.services.voice_state import (
    build_hot_follow_voice_options as _build_hot_follow_voice_options,
    collect_voice_execution_state as _collect_voice_execution_state,
    hf_audio_matches_expected as _hf_audio_matches_expected,
    hf_persisted_audio_state as _hf_persisted_audio_state,
    hot_follow_expected_provider as _hot_follow_expected_provider,
    resolve_hot_follow_provider_voice as _resolve_hot_follow_provider_voice,
    resolve_hot_follow_requested_voice as _resolve_hot_follow_requested_voice,
    voice_state_config as _voice_state_config,
)
from gateway.app.services.task_router_actions import (
    create_task_entry as _create_task_entry,
    rerun_dub_entry as _rerun_dub_entry,
    run_task_pipeline_entry as _run_task_pipeline_entry,
)
from gateway.app.services.compose_service import CompositionService, HotFollowComposeRequestContract


def _policy_upsert(repo, task_id, updates, *, task=None, step="router.hf_api", force=False):
    """Thin wrapper matching the old tasks.py signature."""
    return policy_upsert(repo, task_id, task, updates, step=step, force=force)


# Endpoint functions that remain in tasks.py are reached via
# gateway.app.services.task_router_actions, not direct router imports.


logger = logging.getLogger(__name__)

hot_follow_api_router = APIRouter(prefix="/api", tags=["hot-follow"])


class HotFollowAudioConfigRequest(BaseModel):
    tts_engine: str | None = None
    tts_voice: str | None = None
    bgm_mix: float | None = None
    audio_fit_max_speed: float | None = None



class HotFollowSubtitlesRequest(BaseModel):
    srt_text: str = ""



class HotFollowTranslateRequest(BaseModel):
    text: str = ""
    target_lang: str = "my"



class HotFollowComposeRequest(BaseModel):
    bgm_mix: float | None = None
    overlay_subtitles: bool | None = None
    freeze_tail_enabled: bool | None = None
    force: bool = False
    expected_subtitle_updated_at: str | None = None
    expected_audio_sha256: str | None = None



class ComposePlanPatchRequest(BaseModel):
    overlay_subtitles: bool | None = None
    target_lang: str | None = None
    freeze_tail_enabled: bool | None = None
    freeze_tail_cap_sec: int | None = None
    cleanup_mode: str | None = None




def _hf_compose_revision_snapshot(task: dict) -> dict[str, str | None]:
    return {
        "subtitle_updated_at": str(task.get("subtitles_override_updated_at") or task.get("updated_at") or "").strip() or None,
        "audio_sha256": str(task.get("audio_sha256") or "").strip() or None,
    }


def _maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    if not enabled:
        return None
    soft_fail = os.getenv("HF_LIPSYNC_SOFT_FAIL", "1").strip().lower() not in ("0", "false", "no")
    message = "Lipsync stub enabled, but no provider is wired in v1.9; continuing basic compose."
    if soft_fail:
        logger.warning("HF_LIPSYNC_STUB_SOFT_FAIL task=%s message=%s", task_id, message)
        return message
    raise HTTPException(
        status_code=409,
        detail={"reason": "lipsync_stub_blocked", "message": message},
    )



def _hf_is_srt_text(text: str) -> bool:
    return _service_is_srt_text(text)


def _hf_normalize_subtitles_save_text(task_id: str, task: dict, raw_text: str) -> tuple[str, str]:
    current_target_srt = _hf_load_subtitles_text(task_id, task)
    return normalize_target_subtitles_for_save(
        raw_text,
        duration_sec=task.get("duration_sec"),
        current_target_srt=current_target_srt,
    )


def _hf_text_for_script_analysis(text: str) -> str:
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
        lines.append(line)
    return "\n".join(lines).strip()


def _hf_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    normalized_lang = normalize_target_lang(target_lang or "my")
    content = _hf_text_for_script_analysis(text)
    if normalized_lang not in {"my", "mm"} or not content:
        return {"allow": True, "reason": None, "message": None}
    myanmar_matches = re.findall(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]", content)
    cjk_matches = re.findall(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]", content)
    latin_matches = re.findall(r"[A-Za-z]", content)
    total = len(myanmar_matches) + len(cjk_matches) + len(latin_matches)
    if total <= 0:
        return {"allow": True, "reason": None, "message": None}
    myanmar_ratio = len(myanmar_matches) / total
    non_myanmar = len(cjk_matches) + len(latin_matches)
    mostly_non_myanmar = non_myanmar >= max(4, len(myanmar_matches))
    if myanmar_ratio < 0.6 and mostly_non_myanmar and non_myanmar > 0:
        return {
            "allow": False,
            "reason": "target_lang_mismatch",
            "message": "当前文本尚未翻译为缅语，不建议直接生成缅语配音。请先翻译为缅语并保存字幕成品，或直接走字幕版合成。",
            "myanmar_ratio": myanmar_ratio,
        }
    return {"allow": True, "reason": None, "message": None, "myanmar_ratio": myanmar_ratio}


def _hf_translate_plain_lines(text: str, *, target_lang: str) -> str:
    lines = str(text or "").splitlines()
    segments: list[dict[str, Any]] = []
    mapping: list[int | None] = []
    for line in lines:
        content = str(line or "")
        if content.strip():
            idx = len(segments) + 1
            segments.append({"index": idx, "origin": content.strip()})
            mapping.append(idx)
        else:
            mapping.append(None)
    if not segments:
        return ""
    translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
    out: list[str] = []
    for line, idx in zip(lines, mapping):
        if idx is None:
            out.append("")
        else:
            out.append(str(translations.get(idx) or line or "").strip())
    return "\n".join(out)



def _hf_state_from_status(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in {"ready", "done", "success", "completed"}:
        return "done"
    if v in {"running", "processing", "queued"}:
        return "running"
    if v in {"failed", "error"}:
        return "failed"
    return "pending"


def _hf_done_like(value: Any) -> bool:
    return str(value or "").strip().lower() in {"done", "ready", "success", "completed"}


def _hf_parse_artifact_ready(task: dict) -> bool:
    if not isinstance(task, dict):
        return False

    if task.get("raw_url"):
        return True

    raw_key = _task_key(task, "raw_path") or _task_key(task, "raw_key")
    if raw_key:
        return True

    source_video = task.get("source_video")
    if isinstance(source_video, dict) and source_video.get("url"):
        return True

    media = task.get("media")
    if isinstance(media, dict) and (media.get("raw_url") or media.get("source_video_url")):
        return True

    deliverables = task.get("deliverables")
    if isinstance(deliverables, dict):
        raw_deliverable = deliverables.get("raw_video") or deliverables.get("raw") or deliverables.get("source_video")
        if isinstance(raw_deliverable, dict) and (
            _hf_done_like(raw_deliverable.get("status") or raw_deliverable.get("state"))
            or raw_deliverable.get("url")
            or raw_deliverable.get("key")
        ):
            return True
    elif isinstance(deliverables, list):
        for item in deliverables:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip().lower()
            if kind not in {"raw_video", "raw", "source_video"}:
                continue
            if _hf_done_like(item.get("status") or item.get("state")) or item.get("url") or item.get("key"):
                return True

    pipeline = task.get("pipeline")
    parse_row = None
    if isinstance(pipeline, dict):
        parse_row = pipeline.get("parse")
    elif isinstance(pipeline, list):
        parse_row = next(
            (
                item
                for item in pipeline
                if isinstance(item, dict) and str(item.get("key") or "").strip().lower() == "parse"
            ),
            None,
        )
    if isinstance(parse_row, dict):
        message = str(parse_row.get("message") or parse_row.get("summary") or "").strip().lower()
        if "raw=ready" in message:
            return True

    pipeline_legacy = task.get("pipeline_legacy")
    if isinstance(pipeline_legacy, dict):
        parse_legacy = pipeline_legacy.get("parse")
        if isinstance(parse_legacy, dict):
            message = str(parse_legacy.get("message") or parse_legacy.get("summary") or "").strip().lower()
            if "raw=ready" in message:
                return True

    return False


def _hf_engine_public(provider: str | None) -> str:
    p = str(provider or "").strip().lower()
    if p in {"edge", "edge-tts", "edge_tts"}:
        return "edge_tts"
    if p in {"azure", "azure-speech", "azure_tts", "azure-tts"}:
        return "azure_speech"
    if p == "lovo":
        return "lovo"
    return "none"


def _hf_engine_internal(engine: str | None) -> str | None:
    e = str(engine or "").strip().lower()
    if e in {"edge", "edge-tts", "edge_tts"}:
        return "edge-tts"
    if e in {"azure", "azure-speech", "azure_speech", "azure_tts", "azure-tts"}:
        return "azure-speech"
    if e == "lovo":
        return "lovo"
    if e in {"none", ""}:
        return None
    return None


def _hf_audio_config(task: dict) -> dict[str, Any]:
    settings = get_settings()
    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    mix = bgm.get("mix_ratio")
    try:
        mix_val = float(mix if mix is not None else 0.3)
    except Exception:
        mix_val = 0.3
    task_id = str(task.get("task_id") or task.get("id") or "")
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    try:
        audio_fit_max_speed = float(pipeline_config.get("audio_fit_max_speed") or 1.25)
    except Exception:
        audio_fit_max_speed = 1.25
    audio_fit_max_speed = max(1.0, min(1.6, audio_fit_max_speed))
    voice_state = _collect_voice_execution_state(task, settings)
    provider = normalize_provider(voice_state.get("expected_provider") or task.get("dub_provider") or getattr(settings, "dub_provider", None))
    return {
        "tts_engine": _hf_engine_public(provider),
        "tts_voice": voice_state.get("resolved_voice"),
        "bgm_key": bgm.get("bgm_key"),
        "bgm_mix": max(0.0, min(1.0, mix_val)),
        "bgm_url": get_download_url(str(bgm.get("bgm_key"))) if bgm.get("bgm_key") else None,
        "voiceover_url": voice_state.get("voiceover_url"),
        "audio_url": voice_state.get("voiceover_url"),
        "audio_fit_max_speed": audio_fit_max_speed,
    }


def _hf_subtitles_override_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "subtitles" / "subtitles_override.srt"


def _hf_sync_saved_target_subtitle_artifact(task_id: str, task: dict, saved_text: str | None = None) -> str | None:
    text = str(saved_text if saved_text is not None else _hf_load_subtitles_text(task_id, task) or "").strip()
    current_key = _task_key(task, "mm_srt_path")
    if saved_text is None and current_key and object_exists(str(current_key)):
        head = object_head(str(current_key))
        size, _ = media_meta_from_head(head)
        if int(size or 0) > 0:
            return str(current_key)
    if not text:
        return str(current_key) if current_key else None

    workspace = Workspace(task_id)
    workspace.mm_srt_path.parent.mkdir(parents=True, exist_ok=True)
    workspace.mm_srt_path.write_text(text, encoding="utf-8")
    synced_key = upload_task_artifact(task, workspace.mm_srt_path, "mm.srt", task_id=task_id)
    mm_txt_text = _srt_to_txt(text).strip()
    if mm_txt_text:
        mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
        mm_txt_path.write_text(mm_txt_text + "\n", encoding="utf-8")
        upload_task_artifact(task, mm_txt_path, "mm.txt", task_id=task_id)
    if synced_key and isinstance(task, dict):
        task["mm_srt_path"] = synced_key
    return str(synced_key) if synced_key else (str(current_key) if current_key else None)


def _hf_load_subtitles_text(task_id: str, task: dict) -> str:
    override_path = _hf_subtitles_override_path(task_id)
    if override_path.exists():
        try:
            return override_path.read_text(encoding="utf-8")
        except Exception:
            return override_path.read_text(encoding="utf-8", errors="ignore")

    mm_key = _task_key(task, "mm_srt_path")
    if mm_key and object_exists(mm_key):
        data = get_object_bytes(mm_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")

    origin_key = _task_key(task, "origin_srt_path")
    if origin_key and object_exists(origin_key):
        data = get_object_bytes(origin_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    return ""


def _hf_load_origin_subtitles_text(task: dict) -> str:
    origin_key = _task_key(task, "origin_srt_path")
    if origin_key and object_exists(origin_key):
        data = get_object_bytes(origin_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    return ""


def _hf_load_normalized_source_text(task_id: str, task: dict) -> str:
    try:
        normalized_path = task_base_dir(task_id) / "subs" / "origin_normalized.srt"
    except Exception:
        logger.warning("HF_NORMALIZED_SOURCE_FALLBACK task=%s", task_id)
        return _hf_load_origin_subtitles_text(task)
    if normalized_path.exists():
        try:
            return normalized_path.read_text(encoding="utf-8")
        except Exception:
            return normalized_path.read_text(encoding="utf-8", errors="ignore")
    return _hf_load_origin_subtitles_text(task)


def _hf_dub_input_text(task_id: str, task: dict) -> str:
    edited = _hf_load_subtitles_text(task_id, task)
    if str(edited or "").strip():
        return edited
    normalized = _hf_load_normalized_source_text(task_id, task)
    if str(normalized or "").strip():
        return normalized
    return _hf_load_origin_subtitles_text(task)


def _hf_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    raw_source_text = _hf_load_origin_subtitles_text(task)
    normalized_source_text = _hf_load_normalized_source_text(task_id, task)
    edited_text = _hf_load_subtitles_text(task_id, task)
    srt_text = edited_text or normalized_source_text or raw_source_text
    dub_input_text = _hf_dub_input_text(task_id, task) or ""
    actual_burn_subtitle_source = "mm.srt" if _task_key(task, "mm_srt_path") else None
    subtitle_artifact_exists = bool(_task_key(task, "mm_srt_path") and object_exists(str(_task_key(task, "mm_srt_path"))))
    subtitle_ready = bool(subtitle_artifact_exists or str(edited_text or normalized_source_text or raw_source_text).strip())
    subtitle_ready_reason = "ready" if subtitle_ready else "subtitle_missing"
    return {
        "raw_source_text": raw_source_text or "",
        "normalized_source_text": normalized_source_text or "",
        "edited_text": edited_text or "",
        "srt_text": srt_text or "",
        "primary_editable_text": srt_text or "",
        "primary_editable_format": "srt",
        "dub_input_text": dub_input_text,
        "dub_input_format": "srt" if _hf_is_srt_text(dub_input_text) else "plain_text",
        "actual_burn_subtitle_source": actual_burn_subtitle_source,
        "subtitle_artifact_exists": bool(subtitle_artifact_exists),
        "subtitle_ready": bool(subtitle_ready),
        "subtitle_ready_reason": subtitle_ready_reason,
    }


def _hf_dual_channel_state(task_id: str, task: dict, subtitle_lane: dict[str, Any] | None = None, *, subtitles_step_done: bool = True) -> dict[str, Any]:
    lane = subtitle_lane or _hf_subtitle_lane_state(task_id, task)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    raw_text = str(lane.get("raw_source_text") or "")
    normalized_text = str(lane.get("normalized_source_text") or "")
    has_text = bool(normalized_text.strip() or raw_text.strip())
    no_subtitles = pipeline_config.get("no_subtitles") == "true"
    title_hint = str(task.get("title") or "").lower()
    speech_detected = has_text and not no_subtitles
    speech_confidence = "high" if speech_detected else "none"
    subtitle_stream = pipeline_config.get("subtitle_stream") == "true"
    onscreen_text_detected = bool(subtitle_stream or (not speech_detected and has_text))
    onscreen_text_density = "high" if onscreen_text_detected and len(normalized_text.strip() or raw_text.strip()) >= 20 else ("low" if onscreen_text_detected else "none")
    # When subtitle extraction is still running and no text has been found yet,
    # do NOT conclude "silent_candidate" — speech detection is indeterminate.
    # Default to "voice_led" (standard dubbing path) until subtitles step completes.
    subtitle_still_pending = not subtitles_step_done and not has_text and not no_subtitles
    if speech_detected:
        content_mode = "voice_led"
    elif subtitle_still_pending:
        content_mode = "voice_led"
        speech_detected = True
        speech_confidence = "pending"
    elif onscreen_text_detected:
        content_mode = "subtitle_led"
    else:
        content_mode = "silent_candidate"
    _silent_kw_raw = getattr(get_settings(), "hot_follow_silent_keywords", "") or "asmr,无人声,涂抹音"
    _silent_keywords = [k.strip().lower() for k in _silent_kw_raw.split(",") if k.strip()]
    if any(kw in title_hint for kw in _silent_keywords):
        speech_detected = False
        speech_confidence = "none"
        content_mode = "silent_candidate" if not onscreen_text_detected else "subtitle_led"
    recommended_path = (
        "Voice dubbing"
        if content_mode == "voice_led"
        else ("OCR subtitle translation candidate" if content_mode == "subtitle_led" else "Manual text input required")
    )
    return {
        "speech_detected": bool(speech_detected),
        "speech_confidence": speech_confidence,
        "onscreen_text_detected": bool(onscreen_text_detected),
        "onscreen_text_density": onscreen_text_density,
        "content_mode": content_mode,
        "recommended_path": recommended_path,
    }


def _hf_source_audio_lane_summary(task: dict, route_state: dict[str, Any] | None = None) -> dict[str, Any]:
    route = route_state or {}
    content_mode = str(route.get("content_mode") or "").strip().lower()
    speech_detected = bool(route.get("speech_detected"))
    title_hint = str(task.get("title") or "").strip().lower()
    has_bgm_hint = any(token in title_hint for token in ("bgm", "音乐", "配乐", "商品", "展示"))

    if content_mode == "silent_candidate":
        return {
            "source_audio_lane": "silent_candidate",
            "source_audio_lane_reason": "未检测到稳定人声，建议优先字幕驱动。",
            "speech_presence": "none",
            "bgm_presence": "possible" if has_bgm_hint else "unknown",
            "audio_mix_mode": "silent_or_fx",
        }
    if content_mode == "subtitle_led":
        return {
            "source_audio_lane": "music_or_text_led",
            "source_audio_lane_reason": "画面文字线索更强，当前素材更像字幕或画面驱动。",
            "speech_presence": "low",
            "bgm_presence": "possible",
            "audio_mix_mode": "text_led",
        }
    if speech_detected and has_bgm_hint:
        return {
            "source_audio_lane": "mixed_audio",
            "source_audio_lane_reason": "检测到人声，同时素材特征显示可能带明显配乐。",
            "speech_presence": "high",
            "bgm_presence": "possible",
            "audio_mix_mode": "speech_plus_bgm",
        }
    if speech_detected:
        return {
            "source_audio_lane": "speech_primary",
            "source_audio_lane_reason": "检测到稳定人声，适合标准配音替换路径。",
            "speech_presence": "high",
            "bgm_presence": "low",
            "audio_mix_mode": "speech_primary",
        }
    return {
        "source_audio_lane": "unknown",
        "source_audio_lane_reason": "当前音频结构信息不足，建议先检查来源字幕和原视频。",
        "speech_presence": "unknown",
        "bgm_presence": "unknown",
        "audio_mix_mode": "unknown",
    }


def _hf_screen_text_candidate_summary(
    subtitle_lane: dict[str, Any] | None = None,
    route_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lane = subtitle_lane or {}
    route = route_state or {}
    normalized = str(lane.get("normalized_source_text") or "").strip()
    raw = str(lane.get("raw_source_text") or "").strip()
    content_mode = str(route.get("content_mode") or "").strip().lower()
    onscreen = bool(route.get("onscreen_text_detected"))
    density = str(route.get("onscreen_text_density") or "").strip().lower() or "none"

    candidate_text = normalized or raw
    if not candidate_text or (not onscreen and content_mode != "subtitle_led"):
        return {
            "screen_text_candidate": "",
            "screen_text_candidate_source": None,
            "screen_text_candidate_confidence": "none",
            "screen_text_candidate_mode": "unavailable",
        }
    return {
        "screen_text_candidate": candidate_text,
        "screen_text_candidate_source": "normalized_source" if normalized else "source_text",
        "screen_text_candidate_confidence": density if density in {"high", "low"} else "low",
        "screen_text_candidate_mode": "subtitle_led" if content_mode == "subtitle_led" else "assisted_candidate",
    }



def _hot_follow_operational_defaults() -> dict[str, Any]:
    return {
        "raw_source_text": "",
        "normalized_source_text": "",
        "dub_input_text": "",
        "subtitle_ready": False,
        "subtitle_ready_reason": "unknown",
        "speech_detected": False,
        "speech_confidence": "none",
        "onscreen_text_detected": False,
        "onscreen_text_density": "none",
        "content_mode": "unknown",
        "recommended_path": "Voice dubbing",
        "source_audio_lane": "unknown",
        "source_audio_lane_reason": "当前音频结构信息不足。",
        "speech_presence": "unknown",
        "bgm_presence": "unknown",
        "audio_mix_mode": "unknown",
        "screen_text_candidate": "",
        "screen_text_candidate_source": None,
        "screen_text_candidate_confidence": "none",
        "screen_text_candidate_mode": "unavailable",
        "no_dub": False,
        "no_dub_reason": None,
        "no_dub_message": None,
        "actual_burn_subtitle_source": None,
    }


def _safe_collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    composed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility-safe wrapper around the formal workbench UI builder.

    Keep this narrow while legacy callers still depend on a router-local helper.
    New presentation logic should prefer service/presenter paths instead of
    extending this fallback wrapper.
    """
    try:
        return _collect_hot_follow_workbench_ui(task, settings, composed=composed)
    except Exception:
        logger.exception("HF_WORKBENCH_UI_SAFE_FALLBACK task=%s", task.get("task_id") or task.get("id"))
        payload = _hot_follow_operational_defaults()
        payload.update(
            {
                "actual_provider": normalize_provider(task.get("dub_provider") or getattr(settings, "dub_provider", None)),
                "resolved_voice": None,
                "requested_voice": None,
                "audio_ready": False,
                "audio_ready_reason": "unknown",
                "deliverable_audio_done": False,
                "dub_current": False,
                "dub_current_reason": "unknown",
                "voice_options_by_provider": _build_hot_follow_voice_options(
                    settings, normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
                ),
                "compose_status": str(task.get("compose_status") or "never"),
                "final_exists": False,
                "lipsync_enabled": False,
                "lipsync_status": "off",
            }
        )
        return payload


def _merge_workbench_ui_overlay(
    payload: dict[str, Any],
    overlay: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(payload or {})
    ui = dict(overlay or {})
    blocked_keys = {
        "compose_status",
        "final_exists",
        "final_url",
        "final_video_url",
        "final",
        "composed_ready",
        "composed_reason",
        "final_fresh",
        "final_stale_reason",
        "current_attempt",
        "artifact_facts",
        "historical_final",
        "ready_gate",
        "pipeline",
        "deliverables",
        "compose",
        "media",
    }
    for key, value in ui.items():
        if key in blocked_keys:
            continue
        merged[key] = value
    return merged


def _reconcile_workbench_current_final(
    payload: dict[str, Any],
) -> dict[str, Any]:
    final_url = str(
        (payload.get("final") or {}).get("url")
        or payload.get("final_url")
        or (payload.get("media", {}) or {}).get("final_url")
        or ""
    ).strip() or None
    composed_ready = bool(payload.get("composed_ready"))
    historical_final = dict(payload.get("historical_final") or {})

    if composed_ready:
        pipeline = payload.get("pipeline")
        if isinstance(pipeline, list):
            for step in pipeline:
                if not isinstance(step, dict):
                    continue
                if str(step.get("key") or "").strip().lower() == "compose":
                    step["status"] = "done"
                    step["state"] = "done"
                    step["error"] = None
                    step["message"] = step.get("message") or "final video merge"

        pipeline_legacy = payload.get("pipeline_legacy")
        if isinstance(pipeline_legacy, dict):
            compose_legacy = pipeline_legacy.get("compose")
            if isinstance(compose_legacy, dict):
                compose_legacy["status"] = "done"

        compose = payload.get("compose")
        if isinstance(compose, dict):
            last = compose.get("last")
            if isinstance(last, dict):
                last["status"] = "done"

        deliverables = payload.get("deliverables")
        if isinstance(deliverables, list):
            for item in deliverables:
                if not isinstance(item, dict):
                    continue
                if str(item.get("kind") or "").strip().lower() == "final":
                    item["status"] = "done"
                    item["state"] = "done"
                    item["historical"] = False
                    if final_url:
                        item["url"] = final_url
                    break

        media = payload.get("media")
        if isinstance(media, dict):
            media["final_url"] = final_url or None
            media["final_video_url"] = final_url or None

        final_payload = dict(payload.get("final") or {})
        final_payload["exists"] = True
        if final_url:
            final_payload["url"] = final_url
        final_payload.pop("stale_reason", None)
        final_payload.pop("historical_available", None)
        payload["final"] = final_payload
        payload["composed_ready"] = True
        payload["composed_reason"] = "ready"
        payload["final_url"] = final_url or None
        payload["final_video_url"] = final_url or None
        payload["final_exists"] = True
        payload["compose_status"] = "done"
        return payload

    pipeline = payload.get("pipeline")
    if isinstance(pipeline, list):
        for step in pipeline:
            if not isinstance(step, dict):
                continue
            if str(step.get("key") or "").strip().lower() == "compose":
                step["status"] = "pending"
                step["state"] = "pending"

    pipeline_legacy = payload.get("pipeline_legacy")
    if isinstance(pipeline_legacy, dict):
        compose_legacy = pipeline_legacy.get("compose")
        if isinstance(compose_legacy, dict):
            compose_legacy["status"] = "pending"

    deliverables = payload.get("deliverables")
    if isinstance(deliverables, list):
        for item in deliverables:
            if not isinstance(item, dict):
                continue
            if str(item.get("kind") or "").strip().lower() == "final":
                item["status"] = "pending"
                item["state"] = "pending"
                item["historical"] = bool(final_url)
                break
    payload["composed_ready"] = False
    payload["composed_reason"] = str(payload.get("composed_reason") or "not_ready")
    payload["compose_status"] = "pending"
    payload["final"] = {
        "exists": False,
        "key": None,
        "size_bytes": None,
        "duration_ms": None,
        "asset_version": None,
        "updated_at": None,
        "content_type": "video/mp4",
        "url": None,
        "stale_reason": payload.get("final_stale_reason"),
        "historical_available": bool(historical_final.get("exists")),
    }
    payload["media"]["final_url"] = None
    payload["media"]["final_video_url"] = None
    payload["final_url"] = None
    payload["final_video_url"] = None
    payload["final_exists"] = False
    return payload


def _hf_allow_subtitle_only_compose(task_id: str, task: dict) -> bool:
    """Compatibility helper for subtitle-only compose fallback decisions.

    This remains router-local for behavior stability, but it is not the primary
    compose ownership point and must not absorb broader compose policy.
    """
    if str(task.get("kind") or "").strip().lower() != "hot_follow":
        return False
    subtitle_lane = _hf_subtitle_lane_state(task_id, task)
    route_state = _hf_dual_channel_state(task_id, task, subtitle_lane)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    no_dub = pipeline_config.get("no_dub") == "true"
    no_dub = no_dub or bool(
        str(route_state.get("content_mode") or "").strip().lower() == "silent_candidate"
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    return bool(
        subtitle_lane.get("subtitle_ready")
        and (str(route_state.get("content_mode") or "").strip().lower() == "silent_candidate" or no_dub)
        and (
            not bool(route_state.get("speech_detected"))
            or str(task.get("dub_skip_reason") or "").strip().lower() == "no_speech_detected"
        )
    )


def _hf_pipeline_state(
    task: dict,
    step: str,
    *,
    composed: dict[str, Any] | None = None,
) -> tuple[str, str]:
    last_step = str(task.get("last_step") or "").lower()
    task_status = str(task.get("status") or "").lower()
    if step == "parse":
        status = _hf_state_from_status(task.get("parse_status"))
        raw_ready = _hf_parse_artifact_ready(task)
        if raw_ready:
            status = "done"
        elif status == "pending" and task_status == "processing" and last_step == "parse":
            status = "running"
        summary = "raw=ready" if raw_ready else "raw=none"
        return status, summary
    if step == "subtitles":
        status = _hf_state_from_status(task.get("subtitles_status"))
        if status == "pending" and (task.get("origin_srt_path") or task.get("mm_srt_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "subtitles":
            status = "running"
        summary = "origin/mm subtitles"
        return status, summary
    if step == "audio":
        status = _hf_state_from_status(task.get("dub_status"))
        voice_state = _collect_voice_execution_state(task, get_settings())
        if status == "pending" and voice_state.get("audio_ready"):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "dub":
            status = "running"
        audio_cfg = _hf_audio_config(task)
        summary = (
            f"dub_provider={voice_state.get('actual_provider') or normalize_provider(task.get('dub_provider') or get_settings().dub_provider)} "
            f"voice={voice_state.get('resolved_voice') or audio_cfg.get('tts_voice') or 'missing'} "
            f"audio_ready={'yes' if voice_state.get('audio_ready') else 'no'}"
        )
        return status, summary
    if step == "pack":
        status = _hf_state_from_status(task.get("pack_status"))
        if status == "pending" and (task.get("pack_key") or task.get("pack_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "pack":
            status = "running"
        summary = f"pack={task.get('pack_type') or '-'}"
        return status, summary
    if step == "compose":
        status = _hf_state_from_status(task.get("compose_status"))
        composed_state = composed or {}
        if bool(composed_state.get("composed_ready")) or bool(composed_state.get("final_fresh")):
            status = "done"
        elif status not in {"running", "processing", "queued", "failed", "error"}:
            status = "pending"
        if status == "pending" and task_status == "processing" and last_step in {"compose", "final"}:
            status = "running"
        summary = "final video merge"
        return status, summary
    return "pending", ""


def _hf_deliverable_state(task: dict, key: str | None, fallback_status_field: str | None = None) -> str:
    if key and object_exists(str(key)):
        return "done"
    if fallback_status_field and _hf_state_from_status(task.get(fallback_status_field)) == "failed":
        return "failed"
    return "pending"


def _hf_deliverables(task_id: str, task: dict) -> list[dict[str, Any]]:
    raw_key = _task_key(task, "raw_path")
    origin_key = _task_key(task, "origin_srt_path")
    mm_key = _task_key(task, "mm_srt_path")
    audio_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    pack_key = _task_key(task, "pack_key") or _task_key(task, "pack_path")
    scenes_key = _task_key(task, "scenes_key")
    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
    bgm_key = str(((task.get("config") or {}).get("bgm") or {}).get("bgm_key") or "").strip() or None

    def _entry(kind: str, title: str, key: str | None, url: str | None, state: str) -> dict[str, Any]:
        sha = None
        if kind == "audio":
            sha = task.get("audio_sha256")
        elif kind == "final":
            sha = task.get("final_video_sha256")
        return {
            "kind": kind,
            "title": title,
            "label": title,
            "key": key,
            "url": url,
            "state": state,
            "status": state,
            "size": None,
            "sha256": sha,
        }

    return [
        _entry(
            "raw_video",
            "Raw Video",
            raw_key,
            _task_endpoint(task_id, "raw") if raw_key and object_exists(raw_key) else None,
            "done" if _hf_parse_artifact_ready(task) else _hf_deliverable_state(task, raw_key, "parse_status"),
        ),
        _entry(
            "origin_subtitle",
            "origin.srt",
            origin_key,
            _task_endpoint(task_id, "origin") if origin_key and object_exists(origin_key) else None,
            _hf_deliverable_state(task, origin_key, "subtitles_status"),
        ),
        _entry(
            "subtitle",
            "mm.srt",
            mm_key,
            _task_endpoint(task_id, "mm") if mm_key and object_exists(mm_key) else None,
            _hf_deliverable_state(task, mm_key, "subtitles_status"),
        ),
        _entry(
            "audio",
            "Voiceover",
            audio_key,
            _task_endpoint(task_id, "audio") if audio_key and object_exists(str(audio_key)) else None,
            _hf_deliverable_state(task, audio_key, "dub_status"),
        ),
        _entry(
            "bgm",
            "BGM",
            bgm_key,
            get_download_url(str(bgm_key)) if bgm_key and object_exists(str(bgm_key)) else None,
            "done" if bgm_key and object_exists(str(bgm_key)) else "pending",
        ),
        _entry(
            "pack",
            "Pack ZIP",
            pack_key,
            _task_endpoint(task_id, "pack") if pack_key and object_exists(pack_key) else None,
            _hf_deliverable_state(task, pack_key, "pack_status"),
        ),
        _entry(
            "scenes",
            "Scenes ZIP",
            scenes_key,
            _task_endpoint(task_id, "scenes") if scenes_key and object_exists(scenes_key) else None,
            "done" if scenes_key else _hf_deliverable_state(task, scenes_key, "scenes_status"),
        ),
        _entry(
            "final",
            "Final Video",
            final_key,
            _task_endpoint(task_id, "final") if final_key and object_exists(str(final_key)) else None,
            _hf_deliverable_state(task, final_key, "compose_status"),
        ),
    ]


def _hf_shape_from_events(task: dict) -> dict[str, str]:
    events = task.get("events") or []
    if not isinstance(events, list):
        return {"step": "", "phase": "", "provider": ""}
    for event in reversed(events):
        if not isinstance(event, dict):
            continue
        extra = event.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        step = str(extra.get("step") or event.get("step") or "").strip().lower()
        phase = str(extra.get("phase") or event.get("phase") or "").strip().lower()
        provider = str(extra.get("provider") or event.get("provider") or "").strip()
        if step in {"dubbing", "audio"}:
            step = "dub"
        if step or phase or provider:
            return {"step": step, "phase": phase, "provider": provider}
    return {"step": "", "phase": "", "provider": ""}


def _hf_task_status_shape(task: dict) -> dict[str, str]:
    """Compatibility presentation helper for legacy status-shape payloads."""
    shape = _hf_shape_from_events(task)
    step = shape.get("step") or ""
    phase = shape.get("phase") or ""
    provider = shape.get("provider") or ""

    if not step:
        last_step = str(task.get("last_step") or "").strip().lower()
        step_map = {"dubbing": "dub", "audio": "dub", "final": "compose"}
        step = step_map.get(last_step, last_step)
    if not step:
        for candidate in ("compose", "pack", "scenes", "dub", "subtitles", "parse"):
            status, _ = _hf_pipeline_state(task, candidate)
            if status in {"running", "failed"}:
                step = candidate
                break
    if not step:
        for candidate in ("compose", "pack", "scenes", "dub", "subtitles", "parse"):
            status, _ = _hf_pipeline_state(task, candidate)
            if status == "done":
                step = candidate
                break

    if not phase:
        if step:
            status, _ = _hf_pipeline_state(task, step)
            phase = status
        else:
            phase = _hf_state_from_status(task.get("status")) or "pending"

    if not provider:
        provider_map = {
            "parse": "parse_provider",
            "subtitles": "subtitles_provider",
            "dub": "dub_provider",
            "pack": "pack_provider",
            "compose": "compose_provider",
        }
        provider_field = provider_map.get(step)
        if provider_field:
            provider = str(task.get(provider_field) or "").strip()

    return {
        "step": step or "-",
        "phase": phase or "-",
        "provider": provider or "-",
    }


def _build_hot_follow_dub_warnings(task: dict) -> list[dict[str, str | None]]:
    warnings: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str, str]] = set()

    task_dub_error = str(task.get("dub_error") or "").strip()
    if task_dub_error:
        warnings.append(
            {
                "code": "dub_error",
                "message": task_dub_error,
                "provider": str(task.get("dub_provider") or "").strip() or None,
                "voice_id": str(task.get("voice_id") or "").strip() or None,
            }
        )

    events = task.get("events") or []
    if not isinstance(events, list):
        return warnings

    for ev in reversed(events):
        if not isinstance(ev, dict):
            continue
        code = str(ev.get("code") or "").strip()
        message = str(ev.get("message") or "").strip()
        extra = ev.get("extra") if isinstance(ev.get("extra"), dict) else {}
        haystack = " ".join(
            [
                code,
                message,
                str(extra.get("reason") or ""),
                str(extra.get("stage") or ""),
            ]
        ).lower()
        if not any(token in haystack for token in ("dub", "tts", "fallback", "retry")):
            continue
        if not any(token in haystack for token in ("fail", "fallback", "retry", "error", "timeout")):
            continue
        provider = str(extra.get("provider") or extra.get("dub_provider") or "").strip()
        voice_id = str(extra.get("voice_id") or "").strip()
        key = (code, message, provider, voice_id)
        if key in seen:
            continue
        seen.add(key)
        warnings.append(
            {
                "code": code or "dub_event",
                "message": message or str(extra.get("reason") or "").strip() or "dub warning",
                "provider": provider or None,
                "voice_id": voice_id or None,
            }
        )
        if len(warnings) >= 5:
            break
    return warnings


def _collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    composed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    subtitle_lane = _hf_subtitle_lane_state(task_id, task)
    _sub_status_b, _ = _hf_pipeline_state(task, "subtitles")
    _sub_done_b = _sub_status_b in ("done", "ready", "success", "completed", "failed", "error")
    route_state = _hf_dual_channel_state(task_id, task, subtitle_lane, subtitles_step_done=_sub_done_b)
    audio_lane = _hf_source_audio_lane_summary(task, route_state)
    screen_text_candidate = _hf_screen_text_candidate_summary(subtitle_lane, route_state)
    voice_state = _collect_voice_execution_state(task, settings)
    composed_state = composed or {}
    final_exists = bool(composed_state.get("composed_ready"))
    compose_status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip().lower() or "pending"
    if bool(composed_state.get("composed_ready")) or bool(composed_state.get("final_fresh")):
        compose_status = "done"
    elif compose_status not in {"running", "processing", "queued", "failed", "error"}:
        compose_status = "pending"
    lipsync_enabled = os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in ("1", "true", "yes")
    no_dub = route_state.get("content_mode") in {"silent_candidate", "subtitle_led"} and not str(subtitle_lane.get("dub_input_text") or "").strip()
    if voice_state.get("audio_ready") or voice_state.get("deliverable_audio_done") or voice_state.get("voiceover_url"):
        no_dub = False
    if route_state.get("content_mode") == "subtitle_led":
        no_dub_reason = "subtitle_led"
        no_dub_message = "No reliable speech detected. Review subtitles or provide text before dubbing."
    elif route_state.get("content_mode") == "silent_candidate":
        no_dub_reason = "no_speech_detected"
        no_dub_message = "No spoken speech detected in source video; dubbing is skipped."
    else:
        no_dub_reason = None
        no_dub_message = None
    if not no_dub:
        no_dub_reason = None
        no_dub_message = None
    return {
        **subtitle_lane,
        **route_state,
        **audio_lane,
        **screen_text_candidate,
        **voice_state,
        "subtitle_ready": bool(subtitle_lane.get("subtitle_ready")),
        "subtitle_ready_reason": subtitle_lane.get("subtitle_ready_reason"),
        "compose_status": compose_status,
        "final_exists": final_exists,
        "actual_burn_subtitle_source": subtitle_lane.get("actual_burn_subtitle_source"),
        "no_dub": bool(no_dub),
        "no_dub_reason": no_dub_reason,
        "no_dub_message": no_dub_message,
        "lipsync_enabled": lipsync_enabled,
        "lipsync_status": "enhanced_soft_fail" if lipsync_enabled else "off",
        "voiceover_url": voice_state.get("voiceover_url"),
        "deliverable_audio_done": bool(voice_state.get("deliverable_audio_done")),
        "dub_current": bool(voice_state.get("dub_current")),
        "dub_current_reason": voice_state.get("dub_current_reason"),
    }


def _hf_rerun_presentation_state(
    task: dict,
    voice_state: dict[str, Any] | None,
    final_info: dict[str, Any] | None,
    dub_status: str | None,
) -> dict[str, Any]:
    voice = voice_state or {}
    final_payload = final_info or {}
    final_exists = bool(final_payload.get("exists"))
    final_url = str(final_payload.get("url") or "").strip() or None
    final_asset_version = str(final_payload.get("asset_version") or "").strip() or None
    final_updated_at = final_payload.get("updated_at") or task.get("final_updated_at") or task.get("updated_at")
    return {
        "last_successful_output": {
            "final_exists": final_exists,
            "final_url": final_url,
            "final_asset_version": final_asset_version,
            "final_updated_at": final_updated_at,
        },
        "current_attempt": {
            "dub_status": str(dub_status or "").strip().lower() or "never",
            "audio_ready": bool(voice.get("audio_ready")),
            "audio_ready_reason": str(voice.get("audio_ready_reason") or "").strip() or "unknown",
            "dub_current": bool(voice.get("dub_current")),
            "dub_current_reason": str(voice.get("dub_current_reason") or "").strip() or "unknown",
            "requested_voice": str(voice.get("requested_voice") or "").strip() or None,
            "resolved_voice": str(voice.get("resolved_voice") or "").strip() or None,
            "actual_provider": str(voice.get("actual_provider") or "").strip() or None,
        },
    }


def _hf_artifact_facts(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
) -> dict[str, Any]:
    final_payload = final_info or {}
    audio_payload = persisted_audio or {}
    subtitle_payload = subtitle_lane or {}
    pack_payload = scene_pack or {}
    subtitle_url = _deliverable_url(task_id, task, "mm_srt")
    pack_url = _deliverable_url(task_id, task, "pack_zip") or pack_payload.get("download_url")
    return {
        "final_exists": bool(final_payload.get("exists")),
        "final_url": str(final_payload.get("url") or "").strip() or None,
        "final_updated_at": final_payload.get("updated_at") or task.get("final_updated_at") or task.get("updated_at"),
        "final_asset_version": str(final_payload.get("asset_version") or "").strip() or None,
        "audio_exists": bool(audio_payload.get("exists")),
        "audio_url": str(audio_payload.get("voiceover_url") or "").strip() or None,
        "subtitle_exists": bool(subtitle_payload.get("subtitle_artifact_exists")),
        "subtitle_url": str(subtitle_url or "").strip() or None,
        "pack_exists": bool(pack_url),
        "pack_url": str(pack_url or "").strip() or None,
    }


def _hf_current_attempt_summary(
    *,
    voice_state: dict[str, Any],
    subtitle_lane: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
) -> dict[str, Any]:
    compose_status_norm = str(compose_status or "").strip().lower() or "never"
    compose_reason_norm = str(composed_reason or "").strip().lower() or "unknown"
    requires_recompose = bool(
        voice_state.get("audio_ready")
        and voice_state.get("dub_current")
        and compose_reason_norm != "ready"
    )
    return {
        "dub_status": str(dub_status or "").strip().lower() or "never",
        "audio_ready": bool(voice_state.get("audio_ready")),
        "audio_ready_reason": str(voice_state.get("audio_ready_reason") or "").strip() or "unknown",
        "dub_current": bool(voice_state.get("dub_current")),
        "dub_current_reason": str(voice_state.get("dub_current_reason") or "").strip() or "unknown",
        "requested_voice": str(voice_state.get("requested_voice") or "").strip() or None,
        "resolved_voice": str(voice_state.get("resolved_voice") or "").strip() or None,
        "actual_provider": str(voice_state.get("actual_provider") or "").strip() or None,
        "compose_status": compose_status_norm,
        "compose_reason": compose_reason_norm,
        "requires_recompose": requires_recompose,
        "current_subtitle_source": str(subtitle_lane.get("actual_burn_subtitle_source") or "").strip() or None,
    }


def _hf_operator_summary(
    *,
    artifact_facts: dict[str, Any],
    current_attempt: dict[str, Any],
    no_dub: bool,
    subtitle_ready: bool = False,
) -> dict[str, Any]:
    last_successful_output_available = bool(artifact_facts.get("final_exists"))
    dub_status = str(current_attempt.get("dub_status") or "").strip().lower()
    compose_status = str(current_attempt.get("compose_status") or "").strip().lower()
    current_attempt_failed = dub_status in {"failed", "error"} or compose_status in {"failed", "error"}
    show_previous_final_as_primary = bool(
        last_successful_output_available
        and not bool(current_attempt.get("audio_ready"))
        and not no_dub
    )
    if no_dub and not subtitle_ready:
        recommended_next_action = "当前素材无可提取字幕，正在等待自动检测完成；也可直接在下方字幕编辑区手工输入缅语文字，保存后即可合成字幕版。"
    elif no_dub:
        recommended_next_action = "当前素材适合字幕驱动路径，可先保存字幕并直接合成字幕版。"
    elif current_attempt.get("requires_recompose"):
        recommended_next_action = "当前配音已更新，建议重新合成最终视频以生成最新版本。"
    elif show_previous_final_as_primary and current_attempt_failed:
        recommended_next_action = "当前重配音失败，但上一次成片仍可查看；请先修复当前配音后再重新合成。"
    elif show_previous_final_as_primary:
        recommended_next_action = "当前重配音未完成，上一次成片仍可查看；如需更新版本，请在当前配音完成后重新合成。"
    elif last_successful_output_available:
        recommended_next_action = "当前已有可用成片，可按需继续校对字幕、配音或重新合成。"
    else:
        recommended_next_action = "当前尚无可用成片，请先确保字幕和配音链路完成后再合成。"
    return {
        "last_successful_output_available": last_successful_output_available,
        "current_attempt_failed": current_attempt_failed,
        "show_previous_final_as_primary": show_previous_final_as_primary,
        "recommended_next_action": recommended_next_action,
    }


def _hf_safe_presentation_aggregates(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
    voice_state: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    no_dub: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        artifact_facts = _hf_artifact_facts(
            task_id,
            task,
            final_info=final_info,
            persisted_audio=persisted_audio,
            subtitle_lane=subtitle_lane,
            scene_pack=scene_pack,
        )
        current_attempt = _hf_current_attempt_summary(
            voice_state=voice_state,
            subtitle_lane=subtitle_lane or {},
            dub_status=dub_status,
            compose_status=compose_status,
            composed_reason=composed_reason,
        )
        operator_summary = _hf_operator_summary(
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
            no_dub=no_dub,
            subtitle_ready=bool((subtitle_lane or {}).get("subtitle_ready")),
        )
        return artifact_facts, current_attempt, operator_summary
    except Exception:
        logger.exception("HF_PRESENTATION_AGGREGATES_SAFE_FALLBACK task=%s", task_id)
        return {}, {}, {}


def _hf_audio_display_error(dub_state: str, dub_error: str | None, voice_state: dict[str, Any]) -> str | None:
    state = str(dub_state or "").strip().lower()
    reason = str(voice_state.get("dub_current_reason") or voice_state.get("audio_ready_reason") or "").strip().lower()
    if state in {"running", "processing", "queued"} or reason == "dub_running":
        return None
    if state == "failed":
        return str(dub_error or "").strip() or None
    return None


def _normalize_compose_target_lang(value: str | None) -> str:
    """Normalize a target language code for compose subtitle resolution."""
    v = str(value or "").strip().lower()
    if not v:
        return "mm"
    return "mm" if v == "my" else v


def _resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    """Compatibility subtitle resolver for remaining router-driven compose calls."""
    lang_norm = _normalize_compose_target_lang(lang)
    synced_mm_key = _hf_sync_saved_target_subtitle_artifact(task_code, task_obj)
    candidates: list[str] = []
    if lang_norm == "mm":
        if synced_mm_key:
            candidates.append(str(synced_mm_key))
        mm_path = _task_key(task_obj, "mm_srt_path")
        if mm_path:
            candidates.append(str(mm_path))
        candidates.append(deliver_key(task_code, "mm.srt"))
    else:
        lang_path = _task_key(task_obj, f"{lang_norm}_srt_path")
        if lang_path:
            candidates.append(str(lang_path))
        candidates.append(deliver_key(task_code, f"{lang_norm}.srt"))
        if synced_mm_key:
            candidates.append(str(synced_mm_key))
        mm_path = _task_key(task_obj, "mm_srt_path")
        if mm_path:
            candidates.append(str(mm_path))
        candidates.append(deliver_key(task_code, "mm.srt"))
    for key in candidates:
        if key and object_exists(str(key)):
            return str(key)
    return None


def _hf_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    """Delegate to CompositionService (TASK-2.0 extraction).

    Kept as a thin wrapper for backward compatibility with any remaining callers.
    """
    from gateway.app.services.compose_service import CompositionService  # noqa: PLC0415

    svc = CompositionService(storage=get_storage_service(), settings=get_settings())
    return svc.compose(
        task_id,
        task,
        subtitle_resolver=_resolve_target_srt_key,
        subtitle_only_check=_hf_allow_subtitle_only_compose,
    )


@hot_follow_api_router.post("/hot_follow/tasks", response_model=TaskDetail)
def create_hot_follow_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    data = payload.dict()
    data["kind"] = "hot_follow"
    data["category_key"] = data.get("category_key") or "hot_follow"
    if data.get("auto_start") is None:
        data["auto_start"] = True
    target_lang = normalize_target_lang(data.get("content_lang") or "my")
    if target_lang == "my":
        settings = get_settings()
        config = dict(data.get("config") or {})
        requested_voice = (
            str(data.get("voice_id") or "").strip()
            or str(config.get("tts_requested_voice") or config.get("hot_follow_tts_requested_voice") or "").strip()
            or os.getenv("DEFAULT_MM_VOICE_ID", "mm_female_1").strip()
            or "mm_female_1"
        )
        expected_provider = _hot_follow_expected_provider(
            {
                "kind": "hot_follow",
                "target_lang": target_lang,
                "content_lang": target_lang,
            },
            requested_voice,
            data.get("dub_provider") or config.get("tts_provider") or settings.dub_provider,
        )
        resolved_voice, _ = resolve_tts_voice(
            settings=settings,
            provider=expected_provider,
            target_lang=target_lang,
            requested_voice=requested_voice,
        )
        data["voice_id"] = requested_voice
        data["dub_provider"] = expected_provider
        if resolved_voice:
            config["tts_requested_voice"] = requested_voice
            config["hot_follow_tts_requested_voice"] = requested_voice
            config["tts_provider"] = expected_provider
            config["tts_resolved_voice"] = resolved_voice
            data["config"] = config
    normalized = TaskCreate(**data)
    return _create_task_entry(normalized, background_tasks, repo)


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/bgm")
def upload_hot_follow_bgm(
    task_id: str,
    file: UploadFile = File(...),
    mix_ratio: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    repo=Depends(get_task_repository),
):
    return _upload_task_bgm_impl(
        task_id,
        bgm_file=file,
        original_pct=None,
        bgm_pct=None,
        mix_ratio=mix_ratio,
        strategy=strategy,
        repo=repo,
    )


@hot_follow_api_router.get("/hot_follow/tasks/{task_id}/publish_hub")
def get_hot_follow_publish_hub(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    payload = compute_hot_follow_state(task, _publish_hub_payload(task))
    if _backfill_compose_done_if_final_ready(repo, task_id, task, bool(payload.get("composed_ready"))):
        task = repo.get(task_id) or task
        payload = compute_hot_follow_state(task, _publish_hub_payload(task))
    return payload


@hot_follow_api_router.get("/hot_follow/tasks/{task_id}/workbench_hub", response_model=None)
def get_hot_follow_workbench_hub(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("hot_follow_hub_hit task=%s kind=%s", task_id, task.get("kind"))
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    compose_plan = dict(task.get("compose_plan") or {})
    if not compose_plan:
        compose_plan = {
            "mute": True,
            "overlay_subtitles": True,
            "strip_subtitle_streams": True,
            "cleanup_mode": "none",
            "target_lang": task.get("target_lang") or task.get("content_lang") or "mm",
            "freeze_tail_enabled": False,
            "freeze_tail_cap_sec": 8,
            "compose_policy": "match_video",
        }
    compose_plan.setdefault("freeze_tail_enabled", False)
    compose_plan.setdefault("freeze_tail_cap_sec", 8)
    compose_plan["compose_policy"] = "freeze_tail" if bool(compose_plan.get("freeze_tail_enabled")) else "match_video"
    scene_outputs = task.get("scene_outputs")
    if not isinstance(scene_outputs, list):
        scene_outputs = []
    composed = _compute_composed_state(task, task_id)
    parse_state, parse_summary = _hf_pipeline_state(task, "parse")
    subtitles_state, subtitles_summary = _hf_pipeline_state(task, "subtitles")
    dub_state, dub_summary = _hf_pipeline_state(task, "audio")
    pack_state, pack_summary = _hf_pipeline_state(task, "pack")
    compose_state, compose_summary = _hf_pipeline_state(task, "compose", composed=composed)

    raw_key = _task_key(task, "raw_path")
    raw_url = _task_endpoint(task_id, "raw") if raw_key and object_exists(raw_key) else None
    mute_key = _task_key(task, "mute_video_key") or _task_key(task, "mute_video_path")
    mute_url = _task_endpoint(task_id, "raw") if mute_key and object_exists(str(mute_key)) else raw_url
    final_info = composed.get("final") or {}
    scene_pack = _scene_pack_info(task, task_id)
    scenes_key = _task_key(task, "scenes_key")
    scenes_status = _scenes_status_from_ssot(task)
    scenes_url = _task_endpoint(task_id, "scenes") if scenes_key else None
    subtitles_text = _hf_load_subtitles_text(task_id, task)
    origin_text = _hf_load_origin_subtitles_text(task)
    normalized_source_text = _hf_load_normalized_source_text(task_id, task)
    subtitle_lane = _hf_subtitle_lane_state(task_id, task)
    _sub_step_done = str(subtitles_state).strip().lower() in ("done", "ready", "success", "completed", "failed", "error")
    route_state = _hf_dual_channel_state(task_id, task, subtitle_lane, subtitles_step_done=_sub_step_done)
    audio_cfg = _hf_audio_config(task)
    voice_state = _collect_voice_execution_state(task, get_settings())
    persisted_audio = _hf_persisted_audio_state(task_id, task)
    target_lang_internal = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    text_guard = clean_and_analyze_dub_text(subtitles_text or "", target_lang_internal)
    audio_warning = str(text_guard.get("warning") or "").strip() or None
    if (
        not (audio_cfg.get("voiceover_url") or "").strip()
        and (task.get("mm_audio_key") or task.get("mm_audio_path"))
        and str(dub_state).strip().lower() not in {"running", "processing", "queued"}
        and str(voice_state.get("dub_current_reason") or "").strip().lower() not in {"dub_running", "dub_not_done"}
    ):
        dub_state = "failed"
        if not dub_summary:
            dub_summary = "voiceover artifact invalid"
    audio_error = _hf_audio_display_error(str(dub_state), task.get("dub_error"), voice_state)
    deliverables = _hf_deliverables(task_id, task)
    compose_last_status_raw = str(
        task.get("compose_last_status")
        or task.get("compose_status")
        or ""
    ).strip().lower()
    if compose_last_status_raw in {"", "none", "null"}:
        compose_last_status = "never"
    elif compose_last_status_raw in {"running", "processing", "queued"}:
        compose_last_status = "running"
    elif compose_last_status_raw in {"done", "ready", "success", "completed"}:
        compose_last_status = "done"
    elif compose_last_status_raw in {"failed", "error"}:
        compose_last_status = "failed"
    else:
        compose_last_status = "never"
    compose_last = {
        "status": compose_last_status,
        "started_at": task.get("compose_last_started_at"),
        "finished_at": task.get("compose_last_finished_at"),
        "ffmpeg_cmd": task.get("compose_last_ffmpeg_cmd"),
        "error": task.get("compose_last_error") or task.get("compose_error"),
    }
    composed_ready = bool(composed.get("composed_ready"))
    composed_reason = str(composed.get("composed_reason") or "final_missing")

    pipeline = [
        {"key": "parse", "label": "Parse", "status": parse_state, "updated_at": task.get("updated_at"), "error": task.get("error_message"), "message": parse_summary},
        {"key": "subtitles", "label": "Subtitles", "status": subtitles_state, "updated_at": task.get("updated_at"), "error": task.get("subtitles_error"), "message": subtitles_summary},
        {"key": "dub", "label": "Dub", "status": dub_state, "updated_at": task.get("updated_at"), "error": audio_error, "message": dub_summary},
        {"key": "pack", "label": "Pack", "status": pack_state, "updated_at": task.get("updated_at"), "error": task.get("pack_error"), "message": pack_summary},
        {"key": "compose", "label": "Compose", "status": compose_state, "updated_at": task.get("updated_at"), "error": task.get("compose_error"), "message": compose_summary},
    ]
    for item in pipeline:
        item["state"] = item["status"]

    payload = {
        "task_id": task_id,
        "kind": task.get("kind") or "hot_follow",
        "ui_locale": task.get("ui_lang") or "zh",
        "input": {
            "platform": task.get("platform") or "",
            "source_url": task.get("source_url") or "",
            "title": task.get("title") or "",
            "target_lang": public_target_lang(target_lang_internal),
            "subtitles_mode": pipeline_config.get("subtitles_mode") or "whisper+gemini",
        },
        "media": {
            "raw_url": raw_url,
            "source_video_url": raw_url,
            "mute_video_url": mute_url,
            "voiceover_url": audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
            "bgm_url": audio_cfg.get("bgm_url"),
            "final_url": None,
            "final_video_url": None,
        },
        "pipeline": pipeline,
        "subtitles": {
            "origin_text": origin_text or "",
            "raw_source_text": subtitle_lane.get("raw_source_text") or origin_text or "",
            "normalized_source_text": subtitle_lane.get("normalized_source_text") or normalized_source_text or "",
            "edited_text": subtitles_text or "",
            "srt_text": subtitles_text or "",
            "primary_editable_text": subtitle_lane.get("primary_editable_text") or subtitles_text or "",
            "primary_editable_format": subtitle_lane.get("primary_editable_format") or "srt",
            "dub_input_text": subtitle_lane.get("dub_input_text") or "",
            "dub_input_format": subtitle_lane.get("dub_input_format") or "plain_text",
            "status": subtitles_state,
            "error": task.get("subtitles_error"),
            "subtitle_ready": bool(subtitle_lane.get("subtitle_ready")),
            "subtitle_ready_reason": subtitle_lane.get("subtitle_ready_reason"),
            "editable": True,
            "updated_at": task.get("subtitles_override_updated_at") or task.get("updated_at"),
        },
        "audio": {
            "tts_engine": audio_cfg.get("tts_engine"),
            "tts_voice": audio_cfg.get("tts_voice"),
            "voiceover_url": audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
            "bgm_url": audio_cfg.get("bgm_url"),
            "bgm_mix": audio_cfg.get("bgm_mix"),
            "status": dub_state,
            "error": audio_error,
            "warning": audio_warning,
            "sha256": task.get("audio_sha256"),
            "audio_ready": bool(voice_state.get("audio_ready")),
            "audio_ready_reason": voice_state.get("audio_ready_reason"),
            "requested_voice": voice_state.get("requested_voice"),
            "actual_provider": voice_state.get("actual_provider"),
            "resolved_voice": voice_state.get("resolved_voice"),
            "deliverable_audio_done": bool(voice_state.get("deliverable_audio_done")),
            "dub_current": bool(voice_state.get("dub_current")),
            "dub_current_reason": voice_state.get("dub_current_reason"),
            "no_dub": bool(route_state.get("content_mode") in {"silent_candidate", "subtitle_led_candidate"} and not str(subtitle_lane.get("dub_input_text") or "").strip()),
            "no_dub_reason": (
                "subtitle_led" if route_state.get("content_mode") == "subtitle_led"
                else ("no_speech_detected" if route_state.get("content_mode") == "silent_candidate" else None)
            ),
        },
        "scenes": {
            "status": scenes_status,
            "scenes_key": scenes_key,
            "download_url": scenes_url,
        },
        "scene_pack": {
            "status": scenes_status,
            "exists": bool(scenes_key),
            "key": scenes_key,
            "asset_version": scene_pack.get("asset_version"),
            "error": task.get("scenes_error"),
            "error_reason": None,
            "download_url": scenes_url,
            "scenes_url": scenes_url,
            "deprecated": True,
        },
        "deliverables": deliverables if isinstance(deliverables, list) else [],
        "events": task.get("events") or [],
        "compose_plan": compose_plan,
        "scene_outputs": scene_outputs,
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final_fresh": bool(composed.get("final_fresh")),
        "final_stale_reason": composed.get("final_stale_reason"),
        "final": final_info,
        "compose": {
            "last": compose_last,
            "warning": task.get("compose_warning"),
        },
        "errors": {
            "audio": {"reason": task.get("error_reason"), "message": task.get("dub_error") or audio_warning},
            "pack": {"reason": task.get("error_reason"), "message": task.get("pack_error")},
            "compose": {"reason": composed.get("compose_error_reason"), "message": composed.get("compose_error_message")},
        },
    }
    payload["historical_final"] = dict(final_info or {})
    final_url = _resolve_hub_final_url(task_id, payload)
    if final_url:
        payload["media"]["final_url"] = final_url
        payload["media"]["final_video_url"] = final_url
    payload["final_url"] = final_url
    payload["final_video_url"] = final_url
    final_exists = bool((payload.get("final") or {}).get("exists"))
    composed_ready = bool(composed_ready)
    payload["composed_ready"] = composed_ready
    payload["composed_reason"] = "ready" if composed_ready else str(composed_reason or "not_ready")
    if isinstance(payload.get("deliverables"), list):
        for item in payload["deliverables"]:
            if not isinstance(item, dict):
                continue
            if str(item.get("kind") or "").strip().lower() == "final":
                item["url"] = final_url
                if composed_ready:
                    item["status"] = "done"
                    item["state"] = "done"
                else:
                    item["status"] = "pending"
                    item["state"] = "pending"
                break

    payload["task"] = {
        "id": task_id,
        "kind": payload["kind"],
        "title": payload["input"]["title"],
        "platform": payload["input"]["platform"],
        "source_url": payload["input"]["source_url"],
    }
    payload["source_video"] = {
        "url": payload["media"]["source_video_url"],
        "poster": task.get("cover_url") or task.get("cover") or task.get("thumb_url"),
    }
    payload["audio_config"] = payload["audio"]
    payload["title"] = payload["input"]["title"]
    payload["platform"] = payload["input"]["platform"]
    payload["pipeline_legacy"] = {
        "parse": {"status": parse_state, "summary": parse_summary, "updated_at": task.get("updated_at")},
        "subtitles": {"status": subtitles_state, "summary": subtitles_summary, "updated_at": task.get("updated_at")},
        "audio": {"status": dub_state, "summary": dub_summary, "updated_at": task.get("updated_at")},
        "synthesis": {"status": pack_state, "summary": pack_summary, "updated_at": task.get("updated_at")},
        "compose": {"status": compose_state, "summary": compose_summary, "updated_at": task.get("updated_at")},
    }
    payload = compute_hot_follow_state(task, payload)
    if _backfill_compose_done_if_final_ready(repo, task_id, task, bool(payload.get("composed_ready"))):
        task = repo.get(task_id) or task
        payload = compute_hot_follow_state(task, payload)

    composed = _compute_composed_state(task, task_id)
    payload["composed_ready"] = bool(composed.get("composed_ready"))
    payload["composed_reason"] = str(composed.get("composed_reason") or "final_missing")
    payload["final_fresh"] = bool(composed.get("final_fresh"))
    payload["final_stale_reason"] = composed.get("final_stale_reason")
    payload["final"] = dict(composed.get("final") or {})
    payload = compute_hot_follow_state(task, payload)
    payload["historical_final"] = dict(payload.get("final") or {})
    payload = _reconcile_workbench_current_final(payload)
    artifact_facts, current_attempt, operator_summary = _hf_safe_presentation_aggregates(
        task_id,
        task,
        final_info=payload.get("historical_final") or payload.get("final"),
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        voice_state=voice_state,
        dub_status=str(dub_state),
        compose_status=str(payload.get("compose_status") or compose_state),
        composed_reason=str(payload.get("composed_reason") or "final_missing"),
        no_dub=bool((payload.get("audio") or {}).get("no_dub")),
    )
    payload["artifact_facts"] = artifact_facts
    payload["current_attempt"] = current_attempt
    payload["operator_summary"] = operator_summary
    payload["presentation"] = _hf_rerun_presentation_state(
        task,
        voice_state,
        payload.get("historical_final") or payload.get("final"),
        dub_state,
    )
    payload.update(_hot_follow_operational_defaults())
    payload = _merge_workbench_ui_overlay(
        payload,
        _safe_collect_hot_follow_workbench_ui(task, get_settings(), composed=composed),
    )
    return payload


@hot_follow_api_router.patch("/hot_follow/tasks/{task_id}/audio_config")
def patch_hot_follow_audio_config(
    task_id: str,
    payload: HotFollowAudioConfigRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates: dict[str, Any] = {}
    settings = get_settings()
    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    if payload.bgm_mix is not None:
        mix = max(0.0, min(1.0, float(payload.bgm_mix)))
        bgm["mix_ratio"] = mix
    if bgm:
        config["bgm"] = bgm
        updates["config"] = config

    provider = _hf_engine_internal(payload.tts_engine)
    if payload.tts_engine is not None:
        updates["dub_provider"] = normalize_provider(provider)
    if payload.tts_voice is not None:
        requested_voice = payload.tts_voice.strip() or None
        effective_provider = _hot_follow_expected_provider(
            task,
            requested_voice,
            updates.get("dub_provider") or task.get("dub_provider") or settings.dub_provider,
        )
        target_lang = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
        resolved_voice, _ = resolve_tts_voice(
            settings=settings,
            provider=effective_provider,
            target_lang=target_lang,
            requested_voice=requested_voice,
        )
        if not resolved_voice:
            raise HTTPException(status_code=422, detail="TTS_VOICE_MISSING")
        config["tts_requested_voice"] = requested_voice
        config["hot_follow_tts_requested_voice"] = requested_voice
        config["tts_resolved_voice"] = resolved_voice
        config["tts_provider"] = effective_provider
        updates["config"] = config
        updates["voice_id"] = requested_voice
        updates["dub_provider"] = effective_provider
    if payload.audio_fit_max_speed is not None:
        speed = max(1.0, min(1.6, float(payload.audio_fit_max_speed)))
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        pipeline_config["audio_fit_max_speed"] = f"{speed:.2f}"
        updates["pipeline_config"] = pipeline_config_to_storage(pipeline_config)

    if updates:
        _policy_upsert(repo, task_id, updates)

    current = repo.get(task_id) or task
    return {
        "task_id": task_id,
        "audio_config": _hf_audio_config(current),
    }


@hot_follow_api_router.patch("/hot_follow/tasks/{task_id}/compose_plan")
def patch_hot_follow_compose_plan(
    task_id: str,
    payload: ComposePlanPatchRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    plan = dict(task.get("compose_plan") or {})
    if "overlay_subtitles" not in plan:
        plan["overlay_subtitles"] = True
    if "strip_subtitle_streams" not in plan:
        plan["strip_subtitle_streams"] = True
    if "target_lang" not in plan:
        plan["target_lang"] = task.get("target_lang") or task.get("content_lang") or "mm"
    if "freeze_tail_enabled" not in plan:
        plan["freeze_tail_enabled"] = False
    if "freeze_tail_cap_sec" not in plan:
        plan["freeze_tail_cap_sec"] = 8
    if "cleanup_mode" not in plan:
        plan["cleanup_mode"] = "none"
    if "compose_policy" not in plan:
        plan["compose_policy"] = "match_video"
    if payload.overlay_subtitles is not None:
        plan["overlay_subtitles"] = bool(payload.overlay_subtitles)
    if payload.target_lang is not None and str(payload.target_lang).strip():
        plan["target_lang"] = str(payload.target_lang).strip()
    if payload.freeze_tail_enabled is not None:
        plan["freeze_tail_enabled"] = bool(payload.freeze_tail_enabled)
    if payload.freeze_tail_cap_sec is not None:
        plan["freeze_tail_cap_sec"] = max(1, min(30, int(payload.freeze_tail_cap_sec)))
    if payload.cleanup_mode is not None:
        cleanup_mode = str(payload.cleanup_mode or "").strip().lower()
        if cleanup_mode not in {"none", "bottom_mask", "safe_band"}:
            raise HTTPException(status_code=400, detail="invalid cleanup_mode")
        plan["cleanup_mode"] = cleanup_mode
    plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
    _policy_upsert(repo, task_id, {"compose_plan": plan})
    return {"task_id": task_id, "compose_plan": plan}


@hot_follow_api_router.patch("/hot_follow/tasks/{task_id}/subtitles")
def patch_hot_follow_subtitles(
    task_id: str,
    payload: HotFollowSubtitlesRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text, text_mode = _hf_normalize_subtitles_save_text(task_id, task, payload.srt_text or "")
    # Phase 0.2: compute content hash for revision consistency
    _subtitle_content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else None
    override_path = _hf_subtitles_override_path(task_id)
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(text, encoding="utf-8")
    synced_mm_key = _hf_sync_saved_target_subtitle_artifact(task_id, task, text)
    _policy_upsert(
        repo,
        task_id,
        {
            "subtitles_status": "ready" if text else task.get("subtitles_status"),
            "last_step": "subtitles" if text else task.get("last_step"),
            "mm_srt_path": synced_mm_key or task.get("mm_srt_path"),
            "subtitles_override_updated_at": datetime.now(timezone.utc).isoformat(),
            "subtitles_override_mode": text_mode,
            "subtitles_content_hash": _subtitle_content_hash,
            "error_message": None,
            "error_reason": None,
        },
    )
    return {
        "task_id": task_id,
        "subtitles": {
            "srt_text": _hf_load_subtitles_text(task_id, repo.get(task_id) or task),
            "origin_text": _hf_load_origin_subtitles_text(repo.get(task_id) or task),
            "edited_text": _hf_load_subtitles_text(task_id, repo.get(task_id) or task),
            "editable": True,
        },
    }


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/translate_subtitles")
def translate_hot_follow_subtitles(
    task_id: str,
    payload: HotFollowTranslateRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    source_text = str(payload.text or "").strip()
    if not source_text:
        raise HTTPException(status_code=400, detail="text is empty")
    target_lang = normalize_target_lang(payload.target_lang or task.get("target_lang") or task.get("content_lang") or "mm")
    try:
        if "-->" in source_text:
            segments = _parse_srt_to_segments(source_text)
            if not segments:
                raise HTTPException(status_code=400, detail="invalid srt text")
            translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
            for seg in segments:
                idx = int(seg.get("index") or 0)
                seg["mm"] = str(translations.get(idx) or seg.get("origin") or "").strip()
            translated_text = segments_to_srt(segments, "mm")
        else:
            translated_text = _hf_translate_plain_lines(source_text, target_lang=target_lang)
    except GeminiSubtitlesError as exc:
        raise HTTPException(status_code=409, detail={"reason": "translate_failed", "message": str(exc)}) from exc
    return {
        "task_id": task_id,
        "target_lang": public_target_lang(target_lang),
        "translated_text": translated_text,
    }


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/compose")
def compose_hot_follow_final_video(
    task_id: str,
    payload: HotFollowComposeRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    req = payload or HotFollowComposeRequest()
    svc = CompositionService(storage=get_storage_service(), settings=get_settings())
    result = svc.run_hot_follow_compose(
        task_id,
        task,
        HotFollowComposeRequestContract(
            bgm_mix=req.bgm_mix,
            overlay_subtitles=req.overlay_subtitles,
            freeze_tail_enabled=req.freeze_tail_enabled,
            force=req.force,
            expected_subtitle_updated_at=req.expected_subtitle_updated_at,
            expected_audio_sha256=req.expected_audio_sha256,
        ),
        repo=repo,
        policy_upsert=_policy_upsert,
        hub_loader=lambda current_task_id, current_repo: get_hot_follow_workbench_hub(current_task_id, repo=current_repo),
        subtitle_resolver=_resolve_target_srt_key,
        subtitle_only_check=_hf_allow_subtitle_only_compose,
        revision_snapshot=_hf_compose_revision_snapshot,
        lipsync_runner=_maybe_run_hot_follow_lipsync_stub,
    )
    if result.status_code != 200:
        return JSONResponse(status_code=result.status_code, content=result.body)
    body = dict(result.body)
    body.setdefault("ok", True)
    return body



@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/dub", response_model=DubResponse)
async def rerun_hot_follow_dub(
    task_id: str,
    payload: DubProviderRequest,
    background_tasks: BackgroundTasks,
    repo: ITaskRepository = Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    kind = str(task.get("kind") or "").strip().lower()
    if kind and kind != "hot_follow":
        raise HTTPException(status_code=400, detail="task is not hot_follow")
    if not (payload.mm_text or "").strip():
        edited = _hf_load_subtitles_text(task_id, task).strip()
        if edited:
            payload = DubProviderRequest(
                provider=payload.provider,
                voice_id=payload.voice_id,
                mm_text=edited,
            )
    return await _rerun_dub_entry(task_id, payload, background_tasks, repo)


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/probe")
async def probe_hot_follow_task(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    source_url = (task.get("source_url") or "").strip()
    if not source_url:
        raise HTTPException(status_code=400, detail="source_url is empty")

    probe = await _probe_url_metadata(source_url, task.get("platform"))
    cover = probe.get("cover")
    duration = probe.get("duration_sec")
    source_title = probe.get("title")
    updates = {
        "platform": probe.get("platform") or task.get("platform"),
        "cover_url": cover or task.get("cover_url") or task.get("cover"),
        "duration_sec": duration if duration is not None else task.get("duration_sec"),
        "source_title": source_title,
        "error_message": None,
        "error_reason": None,
    }
    _policy_upsert(repo, task_id, updates)
    _update_pipeline_probe(repo, task_id, probe.get("raw"))
    current = repo.get(task_id) or {}
    return {
        "task_id": task_id,
        "status": current.get("status") or "pending",
        "cover": current.get("cover_url") or current.get("cover") or cover,
        "source_title": current.get("source_title") or source_title,
        "duration": current.get("duration_sec"),
        "platform": current.get("platform"),
    }


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/run")
def run_hot_follow_pipeline(
    task_id: str,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    return _run_task_pipeline_entry(task_id, background_tasks, repo)


@hot_follow_api_router.put("/hot_follow/tasks/{task_id}/publish_backfill")
def publish_backfill_hot_follow(
    task_id: str,
    payload: PublishBackfillRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    backfill = dict(task.get("publish_backfill") or {})
    if payload.publish_url is not None:
        backfill["publish_url"] = payload.publish_url
    if payload.note is not None:
        backfill["note"] = payload.note
    if payload.status is not None:
        backfill["status"] = payload.status
    backfill["updated_at"] = datetime.now(timezone.utc).isoformat()

    updates = {
        "publish_backfill": backfill,
        "publish_url": backfill.get("publish_url") or task.get("publish_url"),
        "published_at": backfill["updated_at"],
    }
    if backfill.get("status"):
        updates["publish_status"] = backfill.get("status")
    _policy_upsert(repo, task_id, updates)
    return {"task_id": task_id, "backfill": backfill}


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/scene_pack", deprecated=True)
def build_hot_follow_scene_pack(
    task_id: str,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.warning(
        "deprecated hot_follow scene_pack endpoint called; use /api/tasks/{task_id}/scenes instead",
        extra={"task_id": task_id},
    )
    result = build_scenes_for_task(task_id, repo=repo, background_tasks=background_tasks, payload=None)
    if isinstance(result, dict):
        result["deprecated_endpoint"] = "/api/hot_follow/tasks/{task_id}/scene_pack"
        result["use_endpoint"] = "/api/tasks/{task_id}/scenes"
    return result
