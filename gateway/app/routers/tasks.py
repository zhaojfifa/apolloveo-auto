"""Task API and HTML routers for the gateway application."""

import asyncio
import json
import hashlib
import hmac
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, Security, UploadFile
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from pydantic import BaseModel

from ..config import get_settings
from ..core.features import get_features
from ..schemas import (
    DubRequest,
    DubResponse,
    PackRequest,
    ParseRequest,
    SubtitlesRequest,
    TaskCreate,
    TaskDetail,
    TaskListResponse,
    TaskSummary,
    TaskUpdate,
)

from gateway.app.web.templates import render_template
from gateway.app.services.workbench_registry import resolve_workbench_spec
from gateway.app.deps import get_task_repository
from gateway.app.ports.storage_provider import get_storage_service  # 鍙繚鐣欒繖涓€澶勪緷璧栨敞鍏ュ叆鍙?
# Ports / typing
from gateway.ports.repository import ITaskRepository  # 濡傝矾寰勪笉瀵癸紝鎸変綘浠?ports 瀹為檯鏂囦欢淇?
# Canonical SSOT dubbing step (v1.62+)
from gateway.app.steps.dubbing import run_dub_step as run_dub_step_ssot

# Legacy v1 pipeline steps (parse/subtitles/pack). Dubbing 淇濈暀 v1 鍚嶇О浣嗗繀椤绘樉寮忓埆鍚嶏紝閬垮厤瑕嗙洊 SSOT
from ..services.steps_v1 import (
    compute_subtitles_params,
    run_pack_step as run_pack_step_v1,
    run_parse_step as run_parse_step_v1,
    run_subtitles_step as run_subtitles_step_v1,
    run_subtitles_step_entry,
    run_dub_step as run_dub_step_v1,
)
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.parse import detect_platform
from gateway.app.providers.xiongmao import XiongmaoError, parse_with_xiongmao
from gateway.app.services.tts_policy import (
    normalize_provider,
    normalize_target_lang,
    public_target_lang,
    resolve_tts_voice,
)
from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text


def _policy_upsert(repo, task_id: str, updates: dict, *, task: dict | None = None, step: str = "router.tasks", force: bool = False):
    return policy_upsert(repo, task_id, task, updates, step=step, force=force)
def coerce_datetime(v: Any) -> Optional[datetime]:
    """
    Best-effort convert repository stored value into a timezone-aware datetime.
    Accepts:
      - datetime (naive/aware)
      - ISO8601 string (with/without 'Z', with/without timezone)
      - epoch seconds/ms (int/float or numeric string)
    Returns:
      - datetime (tz-aware, UTC) or None if cannot parse
    """
    if v is None:
        return None

    # already datetime
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)

    # epoch seconds / milliseconds
    if isinstance(v, (int, float)):
        ts = float(v)
        if ts > 1e12:  # ms
            ts = ts / 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None

    # strings
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None

        # numeric string -> epoch
        if s.isdigit():
            try:
                ts = float(s)
                if ts > 1e12:
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                return None

        # ISO8601 variants
        # handle "Z"
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        # allow "YYYY-mm-dd HH:MM:SS" -> fromisoformat can parse, but ensure 'T' optional ok
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    # unknown type
    return None


def coerce_datetime_or_epoch(v: Any) -> datetime:
    """
    Safe non-null datetime for response models that disallow None.
    """
    return coerce_datetime(v) or datetime(1970, 1, 1, tzinfo=timezone.utc)

from gateway.app.services.artifact_storage import (
    upload_task_artifact,
    get_download_url,
    get_object_bytes,
    object_head,
    object_exists,
    stream_object_range,
)
from gateway.app.ports.storage_provider import get_storage_service
from gateway.app.services.scenes_service import build_scenes_for_task
from gateway.app.services.publish_service import publish_task_pack, resolve_download_url
from gateway.app.services.task_state_service import TaskStateService
from gateway.app.db import SessionLocal

from gateway.app.task_repo_utils import normalize_task_payload, sort_tasks_by_created
from gateway.app.services.task_cleanup import delete_task_record, purge_task_artifacts
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage
from gateway.app.utils.subtitle_probe import probe_subtitles
from gateway.app.services.task_semantics import derive_task_semantics
from gateway.app.services.media_validation import (
    MIN_AUDIO_BYTES,
    MIN_VIDEO_BYTES,
    assert_artifact_ready,
    assert_local_audio_ok,
    assert_local_video_ok,
    deliver_key,
    media_meta_from_head,
)

from ..core.workspace import (
    Workspace,
    origin_srt_path,
    deliver_pack_zip_path,
    raw_path,
    relative_to_workspace,
    task_base_dir,
)

logger = logging.getLogger(__name__)

OP_HEADER_KEY = "X-OP-KEY"
COMPOSE_RETRY_AFTER_MS = 1500
_COMPOSE_LOCKS_GUARD = threading.Lock()
_COMPOSE_LOCKS: dict[str, threading.Lock] = {}


def _task_compose_lock(task_id: str) -> threading.Lock:
    with _COMPOSE_LOCKS_GUARD:
        lock = _COMPOSE_LOCKS.get(task_id)
        if lock is None:
            lock = threading.Lock()
            _COMPOSE_LOCKS[task_id] = lock
        return lock


def _compose_in_progress_response(task_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "compose_in_progress",
            "status": "running",
            "retry_after_ms": COMPOSE_RETRY_AFTER_MS,
            "task_id": task_id,
        },
    )


def _run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> dict[str, Any]:
    if not enabled:
        return {
            "enabled": False,
            "status": "off",
            "warning": None,
            "compose_video_source": "basic",
        }
    soft_fail = os.getenv("HF_LIPSYNC_SOFT_FAIL", "1").strip().lower() not in ("0", "false", "no")
    message = "Lipsync stub enabled, but no provider is wired in v1.9; continuing basic compose."
    if soft_fail:
        logger.warning("HF_LIPSYNC_STUB_SOFT_FAIL task=%s message=%s", task_id, message)
        return {
            "enabled": True,
            "status": "fallback_basic",
            "warning": message,
            "compose_video_source": "basic",
        }
    raise HTTPException(
        status_code=409,
        detail={"reason": "lipsync_stub_blocked", "message": message},
    )


def _build_atempo_chain(speed: float) -> str:
    try:
        value = float(speed)
    except Exception:
        value = 1.0
    value = max(0.5, min(100.0, value))
    factors: list[float] = []
    while value > 2.0:
        factors.append(2.0)
        value /= 2.0
    while value < 0.5:
        factors.append(0.5)
        value /= 0.5
    factors.append(value)
    parts: list[str] = []
    for factor in factors:
        if abs(factor - 2.0) < 1e-9:
            parts.append("atempo=2.0")
        elif abs(factor - 0.5) < 1e-9:
            parts.append("atempo=0.5")
        else:
            parts.append(f"atempo={factor:.6f}")
    return ",".join(parts)


def _resolve_audio_fit_max_speed(pipeline_config: dict | None) -> tuple[float, str]:
    cfg = pipeline_config or {}
    raw = cfg.get("audio_fit_max_speed")
    source = "default"
    if raw in (None, "", "null"):
        speed = 1.25
    else:
        source = "operator"
        try:
            speed = float(raw)
        except Exception:
            speed = 1.25
    speed = max(1.0, min(2.0, speed))
    return speed, source


def _compute_audio_fit_speeds(source_duration_sec: float, dubbed_duration_sec: float, max_speed: float) -> tuple[float, float]:
    try:
        source = float(source_duration_sec)
    except Exception:
        source = 0.0
    try:
        dubbed = float(dubbed_duration_sec)
    except Exception:
        dubbed = 0.0
    safe_source = max(source, 1e-6)
    need_speed = max(1.0, dubbed / safe_source)
    applied_speed = min(max(1.0, float(max_speed or 1.25)), need_speed)
    return need_speed, applied_speed


def _count_srt_cues(srt_text: str | None) -> int:
    text = str(srt_text or "")
    if not text.strip():
        return 0
    return len(re.findall(r"(?m)^\s*\d+\s*\r?\n\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}", text))


def _build_translation_qa_summary(origin_srt_text: str | None, translated_srt_text: str | None) -> dict:
    source_count = _count_srt_cues(origin_srt_text)
    translated_count = _count_srt_cues(translated_srt_text)
    return {
        "source_count": source_count,
        "translated_count": translated_count,
        "has_mismatch": source_count != translated_count,
    }


def _build_workbench_debug_payload(show_debug: bool, scene_outputs: list[dict] | None, compose_last: dict | None) -> dict:
    if not show_debug:
        return {}
    compose = compose_last or {}
    return {
        "scene_outputs": list(scene_outputs or []),
        "compose_last_ffmpeg_cmd": compose.get("ffmpeg_cmd"),
    }


class DubProviderRequest(BaseModel):
    provider: str | None = None
    voice_id: str | None = None
    mm_text: str | None = None
    tts_speed: float | None = None


class EditedTextRequest(BaseModel):
    text: str


class ScenesRequest(BaseModel):
    force: bool = False


class SubtitlesTaskRequest(BaseModel):
    target_lang: str | None = None
    force: bool = False
    translate: bool = True


class ParseTaskRequest(BaseModel):
    platform: str | None = None


class ProbeTaskRequest(BaseModel):
    platform: str | None = None
    url: str


class PublishTaskRequest(BaseModel):
    provider: str | None = None
    force: bool = False
    published: bool | None = None
    published_url: str | None = None
    notes: str | None = None


class PublishBackfillRequest(BaseModel):
    publish_url: str | None = None
    note: str | None = None
    status: str | None = None


class HotFollowAudioConfigRequest(BaseModel):
    tts_engine: str | None = None
    tts_voice: str | None = None
    bgm_mix: float | None = None
    audio_fit_max_speed: float | None = None


class HotFollowSubtitlesRequest(BaseModel):
    srt_text: str = ""


class ComposeTaskRequest(BaseModel):
    voiceover_url: str | None = None
    bgm_url: str | None = None
    bgm_mix: float | None = None
    overlay_subtitles: bool | None = None
    freeze_tail_enabled: bool | None = None
    force: bool = False


class ComposePlanPatchRequest(BaseModel):
    overlay_subtitles: bool | None = None
    target_lang: str | None = None
    freeze_tail_enabled: bool | None = None
    freeze_tail_cap_sec: int | None = None
    source_subtitle_cover_enabled: bool | None = None
    source_subtitle_cover_mode: str | None = None


pages_router = APIRouter()
api_router = APIRouter(prefix="/api", tags=["tasks"])
api_key_header = APIKeyHeader(name=OP_HEADER_KEY, auto_error=False)


@pages_router.get("/favicon.ico", include_in_schema=False)
def favicon_noop():
    return Response(status_code=204)
def _coerce_datetime(value) -> datetime:
    # Pydantic TaskDetail.created_at expects datetime, so guarantee it.
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return datetime.now(timezone.utc)

        # unix seconds in string
        if s.isdigit():
            return datetime.fromtimestamp(int(s), tz=timezone.utc)

        # ISO with Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"

        # Try ISO formats
        try:
            dt = datetime.fromisoformat(s)
            # If naive, assume UTC
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        # Common fallback: "YYYY-MM-DD HH:MM:SS"
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    return datetime.now(timezone.utc)


def _infer_platform_from_url(url: str) -> Optional[str]:
    url_lower = url.lower()
    if "douyin.com" in url_lower:
        return "douyin"
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
        return "xhs"
    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    return None


def _is_storage_key(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = value.lower()
    return lowered.startswith(("http://", "https://", "s3://", "r2://"))


def _pack_path_for_list(task: dict) -> Optional[str]:
    task_id = str(_task_value(task, "task_id") or _task_value(task, "id") or "")
    pack_type = _task_value(task, "pack_type")
    pack_key = _task_value(task, "pack_key")
    pack_path = _task_value(task, "pack_path")
    if pack_type == "capcut_v18" and pack_key:
        return str(pack_key)
    if pack_path:
        pack_path = str(pack_path)
        if pack_path.startswith(("pack/", "published/")) and not _is_storage_key(pack_path):
            return pack_path
    pack_file = deliver_pack_zip_path(task_id)
    if pack_file.exists():
        return relative_to_workspace(pack_file)
    return None


def _mm_edited_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "mm_edited.txt"


def _load_dub_text(task_id: str) -> tuple[str, str]:
    edited_path = _mm_edited_path(task_id)
    if edited_path.exists():
        text = edited_path.read_text(encoding="utf-8").strip()
        if text:
            return text, "mm_edited"
    workspace = Workspace(task_id)
    mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
    if mm_txt_path.exists():
        return mm_txt_path.read_text(encoding="utf-8"), "mm_txt"
    return "", "mm_txt"


def _resolve_text_path(task_id: str, kind: str) -> Path | None:
    td = task_base_dir(task_id)
    ws = Workspace(task_id)

    if kind == "mm_edited":
        p = _mm_edited_path(task_id)
        return p if p.exists() else None

    if kind == "mm_txt":
        p = ws.mm_srt_path.with_suffix(".txt")
        if p.exists():
            return p
        p2 = td / "mm.txt"
        return p2 if p2.exists() else None

    if kind == "origin_srt":
        candidates: list[Path] = []
        origin_attr = getattr(ws, "origin_srt_path", None)
        if isinstance(origin_attr, Path):
            candidates.append(origin_attr)
        candidates.extend(
            [
                td / "origin.srt",
                td / "subs_origin.srt",
                td / "subs_origin.txt",
            ]
        )
        for c in candidates:
            if c and c.exists():
                return c
        return None

    if kind == "mm_srt":
        p = ws.mm_srt_path
        if p.exists():
            return p
        p2 = td / "mm.srt"
        return p2 if p2.exists() else None

    return None


@pages_router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    kind: str | None = Query(default=None),
    repo=Depends(get_task_repository),
):
    """Render the task board HTML page."""

    db_tasks = sort_tasks_by_created(repo.list())
    kind_norm = (kind or "").strip().lower()
    if kind_norm == "apollo_avatar":
        db_tasks = [
            t
            for t in db_tasks
            if (str(t.get("platform") or "").lower() == "apollo_avatar")
            or (str(t.get("category_key") or "").lower() == "apollo_avatar")
        ]

    rows: list[dict] = []
    for t in db_tasks[:limit]:
        rows.append(
            {
                "task_id": t.get("task_id") or t.get("id"),
                "platform": t.get("platform"),
                "source_url": t.get("source_url"),
                "title": t.get("title") or "",
                "category_key": t.get("category_key") or "",
                "content_lang": t.get("content_lang") or "",
                "status": t.get("status") or "pending",
                "created_at": t.get("created_at") or "",
                "pack_path": _pack_path_for_list(t),
                "pack_key": t.get("pack_key"),
                "pack_url": t.get("pack_url"),
                "deliver_pack_key": t.get("deliver_pack_key"),
                "cover_url": t.get("cover_url"),
                "thumb_url": t.get("thumb_url"),
                "raw_path": t.get("raw_path"),
                "raw_key": t.get("raw_key"),
                "raw_url": t.get("raw_url"),
                "video_url": t.get("video_url"),
                "preview_url": t.get("preview_url"),
                "ui_lang": t.get("ui_lang") or "",
                "selected_tool_ids": _normalize_selected_tool_ids(t.get("selected_tool_ids")),
            }
        )

    items = [derive_task_semantics(row) for row in rows]

    if rows:
        x = rows[0]
        logger.info(
            "TASKS_PAGE_SAMPLE",
            extra={
                "sample_task_id": x.get("task_id") or x.get("id"),
                "sample_title": x.get("title"),
                "sample_cover_url": x.get("cover_url"),
                "sample_kind": x.get("kind"),
                "sample_status": x.get("status"),
                "sample_pack_path": x.get("pack_path"),
            },
        )

    return render_template(
        request=request,
        name="tasks.html",
        ctx={
            "items": items,
            "features": get_features(),
            "tasks_kind": kind_norm or "tasks",
        },
    )


@pages_router.get("/tasks/new", response_class=HTMLResponse)
async def tasks_new(request: Request) -> HTMLResponse:
    """Render suitcase quick-create page."""

    return render_template(
        request=request,
        name="tasks_new.html",
        ctx={"features": get_features()},
    )


@pages_router.get("/tasks/baseline/new", response_class=HTMLResponse)
async def tasks_baseline_new(request: Request) -> HTMLResponse:
    return await tasks_new(request)


@pages_router.get("/tasks/newtasks", response_class=HTMLResponse)
async def tasks_newtasks(request: Request) -> HTMLResponse:
    """Render tasks wizard selection page."""

    return render_template(
        request=request,
        name="tasks_newtasks.html",
        ctx={"features": get_features()},
    )


@pages_router.get("/tasks/apollo-avatar/new", response_class=HTMLResponse)
async def tasks_apollo_avatar_new(request: Request) -> HTMLResponse:
    settings = get_settings()
    if not bool(getattr(settings, "enable_apollo_avatar", False)):
        raise HTTPException(status_code=404, detail="ApolloAvatar is disabled")
    return render_template(
        request=request,
        name="tasks_apollo_avatar_new.html",
        ctx={
            "apollo_avatar_live_enabled": bool(
                getattr(settings, "apollo_avatar_live_enabled", False)
            ),
            "demo_asset_base_url": getattr(settings, "demo_asset_base_url", "") or "",
        },
    )


@pages_router.get("/tasks/avatar/new", response_class=HTMLResponse)
async def tasks_avatar_new(request: Request) -> HTMLResponse:
    return await tasks_apollo_avatar_new(request)


@pages_router.get("/ui", response_class=HTMLResponse)
async def pipeline_lab(request: Request) -> HTMLResponse:
    settings = get_settings()
    env_summary = {
        "workspace_root": settings.workspace_root,
        "douyin_api_base": getattr(settings, "douyin_api_base", ""),
        "whisper_model": getattr(settings, "whisper_model", ""),
        "gpt_model": getattr(settings, "gpt_model", ""),
        "asr_backend": getattr(settings, "asr_backend", None) or "whisper",
        "subtitles_backend": getattr(settings, "subtitles_backend", None) or "gemini",
        "gemini_model": getattr(settings, "gemini_model", ""),
    }
    return render_template(
        request=request,
        name="pipeline_lab.html",
        ctx={"env_summary": env_summary},
    )


@pages_router.get("/tools/hub", response_class=HTMLResponse)
async def tools_hub_page(request: Request) -> HTMLResponse:
    """Render tools hub list page."""

    return render_template(
        request=request,
        name="tools_hub.html",
        ctx={},
    )


@pages_router.get("/tools/{tool_id}", response_class=HTMLResponse)
async def tool_detail_page(request: Request, tool_id: str) -> HTMLResponse:
    """Render tool detail page."""

    return render_template(
        request=request,
        name="tool_detail.html",
        ctx={"tool_id": tool_id},
    )


@pages_router.get("/v1/tasks/{task_id}/raw")
def download_raw(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="raw video not found")
    key = _require_storage_key(task, "raw_path", "raw video not found")
    return RedirectResponse(url=get_download_url(key), status_code=302)


@pages_router.get("/v1/tasks/{task_id}/subs_origin")
def download_origin_subs(
    task_id: str,
    inline: bool = Query(default=False),
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="origin subtitles not found")
    key = _require_storage_key(task, "origin_srt_path", "origin subtitles not found")
    return _text_or_redirect(key, inline=inline)


@pages_router.get("/v1/tasks/{task_id}/subs_mm")
def download_mm_subs(
    task_id: str,
    inline: bool = Query(default=False),
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="burmese subtitles not found")
    key = _task_key(task, "mm_srt_path")
    if not key or not object_exists(key):
        return _not_ready_response(task, "subs_mm", ["mm_srt_path"])
    return _text_or_redirect(key, inline=inline)


@pages_router.get("/v1/tasks/{task_id}/mm_txt")
def download_mm_txt(
    task_id: str,
    inline: bool = Query(default=False),
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="mm txt not found")
    mm_key = _task_key(task, "mm_srt_path")
    if not mm_key or not object_exists(mm_key):
        return _not_ready_response(task, "mm_txt", ["mm_srt_path"])
    txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
    if not object_exists(txt_key):
        return _not_ready_response(task, "mm_txt", ["mm_txt_path"])
    return _text_or_redirect(txt_key, inline=inline)


def _resolve_audio_meta(task_id: str, repo) -> tuple[str, int, str]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="dubbed audio not found")
    preferred = _task_value(task, "mm_audio_key") or _task_value(task, "mm_audio_path")
    candidates = [str(k) for k in [preferred] if k]
    seen = set()
    chosen_key = None
    chosen_size = 0
    chosen_type = None
    dub_status = str(_task_value(task, "dub_status") or "")
    for key in candidates:
        if key in seen:
            continue
        seen.add(key)
        try:
            size, ctype = assert_artifact_ready(
                kind="audio",
                key=key,
                exists_fn=object_exists,
                head_fn=object_head,
            )
            chosen_key = key
            chosen_size = size
            chosen_type = ctype
            break
        except Exception:
            continue
    if not chosen_key:
        raise HTTPException(status_code=404, detail="voiceover_not_ready")
    content_type = str(chosen_type or _task_value(task, "mm_audio_mime") or "audio/mpeg")
    return chosen_key, int(chosen_size), content_type


@pages_router.head("/v1/tasks/{task_id}/audio_mm")
def head_audio_mm(task_id: str, repo=Depends(get_task_repository)):
    try:
        _, total, content_type = _resolve_audio_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception("audio_head_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "audio head failed"})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type or "audio/mpeg",
        "Content-Length": str(total),
    }
    logger.info(
        "AUDIO_STREAM",
        extra={
            "task_id": task_id,
            "has_range": False,
            "start": 0,
            "end": total - 1,
            "total": total,
            "status": 200,
            "content_type": headers["Content-Type"],
        },
    )
    return Response(status_code=200, headers=headers)


@pages_router.get("/v1/tasks/{task_id}/audio_mm")
def download_audio_mm(task_id: str, request: Request, repo=Depends(get_task_repository)):
    try:
        key, total, content_type = _resolve_audio_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception("audio_get_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "audio get failed"})

    range_header = request.headers.get("range")
    start = 0
    end = total - 1
    status_code = 200
    if range_header:
        try:
            start, end = _parse_http_range(range_header, total)
        except Exception:
            logger.info(
                "AUDIO_STREAM",
                extra={
                    "task_id": task_id,
                    "has_range": True,
                    "range_in": range_header,
                    "start": None,
                    "end": None,
                    "total": total,
                    "status": 416,
                    "content_type": content_type,
                },
            )
            return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
        status_code = 206
    try:
        stream, length = stream_object_range(str(key), start=start, end=end)
    except ValueError:
        logger.info(
            "AUDIO_STREAM",
            extra={
                "task_id": task_id,
                "has_range": bool(range_header),
                "range_in": range_header,
                "start": start,
                "end": end,
                "total": total,
                "status": 416,
                "content_type": content_type,
            },
        )
        return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
    except Exception as exc:
        logger.exception("audio_stream_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "audio stream failed"})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
        "Content-Length": str(length),
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    logger.info(
        "AUDIO_STREAM",
        extra={
            "task_id": task_id,
            "has_range": bool(range_header),
            "range_in": range_header,
            "start": start,
            "end": end,
            "total": total,
            "status": status_code,
            "content_type": content_type,
        },
    )
    return StreamingResponse(stream, status_code=status_code, headers=headers, media_type=content_type)


def _resolve_final_meta(task_id: str, repo) -> tuple[str, int, str]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="final video not found")
    key = _task_value(task, "final_video_key") or _task_value(task, "final_video_path") or deliver_key(task_id, "final.mp4")
    if not key or not object_exists(str(key)):
        raise HTTPException(status_code=404, detail="final video not found")
    head = object_head(str(key))
    total, ctype = media_meta_from_head(head)
    if total <= 0:
        raise HTTPException(status_code=404, detail="final video not found")
    content_type = str(_task_value(task, "final_mime") or ctype or "video/mp4")
    return str(key), int(total), content_type


def _parse_http_range(range_header: str, total: int) -> tuple[int, int]:
    m = re.match(r"bytes=(\d*)-(\d*)", (range_header or "").strip())
    if not m:
        raise ValueError("invalid_range")
    start_raw, end_raw = m.group(1), m.group(2)
    if start_raw == "" and end_raw == "":
        raise ValueError("invalid_range")
    if start_raw == "":
        suffix = int(end_raw)
        if suffix <= 0:
            raise ValueError("invalid_range")
        start = max(total - suffix, 0)
        end = total - 1
    else:
        start = int(start_raw)
        end = int(end_raw) if end_raw else total - 1
    if start >= total or start < 0 or end < start:
        raise ValueError("range_not_satisfiable")
    end = min(end, total - 1)
    return start, end


@pages_router.head("/v1/tasks/{task_id}/final")
def head_final_video(task_id: str, repo=Depends(get_task_repository)):
    try:
        _, total, content_type = _resolve_final_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception("final_head_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "final head failed"})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type or "video/mp4",
        "Content-Length": str(total),
    }
    logger.info(
        "FINAL_STREAM",
        extra={
            "task_id": task_id,
            "has_range": False,
            "range_in": None,
            "start": 0,
            "end": total - 1,
            "total": total,
            "status": 200,
            "content_type": headers["Content-Type"],
        },
    )
    return Response(status_code=200, headers=headers)


@pages_router.get("/v1/tasks/{task_id}/final")
def download_final_video(task_id: str, request: Request, repo=Depends(get_task_repository)):
    try:
        key, total, content_type = _resolve_final_meta(task_id, repo)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
    except Exception as exc:
        logger.exception("final_get_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "final get failed"})

    range_header = request.headers.get("range")
    start = 0
    end = total - 1
    status_code = 200
    if range_header:
        try:
            start, end = _parse_http_range(range_header, total)
        except Exception:
            logger.info(
                "FINAL_STREAM",
                extra={
                    "task_id": task_id,
                    "has_range": True,
                    "range_in": range_header,
                    "start": None,
                    "end": None,
                    "total": total,
                    "status": 416,
                    "content_type": content_type,
                },
            )
            return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
        status_code = 206
    try:
        stream, length = stream_object_range(str(key), start=start, end=end)
    except ValueError:
        logger.info(
            "FINAL_STREAM",
            extra={
                "task_id": task_id,
                "has_range": bool(range_header),
                "range_in": range_header,
                "start": start,
                "end": end,
                "total": total,
                "status": 416,
                "content_type": content_type,
            },
        )
        return Response(status_code=416, headers={"Content-Range": f"bytes */{total}"})
    except Exception as exc:
        logger.exception("final_stream_failed", extra={"task_id": task_id, "error": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "final stream failed"})
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
        "Content-Length": str(length),
    }
    if status_code == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    logger.info(
        "FINAL_STREAM",
        extra={
            "task_id": task_id,
            "has_range": bool(range_header),
            "range_in": range_header,
            "start": start,
            "end": end,
            "total": total,
            "status": status_code,
            "content_type": content_type,
        },
    )
    return StreamingResponse(stream, status_code=status_code, headers=headers, media_type=content_type)


@pages_router.get("/v1/tasks/{task_id}/pack")
def download_pack(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Pack not found")
    pack_key = _task_value(task, "pack_key") or _task_value(task, "pack_path")
    if pack_key and object_exists(str(pack_key)):
        return RedirectResponse(url=get_download_url(str(pack_key)), status_code=302)

    status = derive_status(task)
    if status in ("ready", "packed", "published"):
        fresh = repo.get(task_id) or task
        repair_key = (
            _task_value(fresh, "pack_key")
            or _task_value(fresh, "pack_path")
            or _task_value(fresh, "zip_key")
        )
        if repair_key and object_exists(str(repair_key)):
            return RedirectResponse(url=get_download_url(str(repair_key)), status_code=302)
        return _not_ready_response(
            fresh,
            "pack",
            ["pack_key"],
            reason="repair_attempted",
            status_code=202,
            extra={"repair_attempted": True},
        )

    return _not_ready_response(task, "pack", ["pack_key"])


@pages_router.get("/v1/tasks/{task_id}/scenes")
def download_scenes(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scenes not found")
    scenes_key = _task_value(task, "scenes_pack_key") or _task_value(task, "scenes_key")
    scenes_status = str(_task_value(task, "scenes_pack_status") or _task_value(task, "scenes_status") or "").lower()
    if scenes_status == "skipped":
        return _not_ready_response(task, "scenes", ["scenes_skipped"], reason="not_applicable")
    if scenes_status == "failed":
        return _not_ready_response(task, "scenes", ["scenes_failed"], reason="failed")
    if not scenes_key or not object_exists(str(scenes_key)):
        return _not_ready_response(task, "scenes", ["scenes_key"])
    return RedirectResponse(url=get_download_url(str(scenes_key)), status_code=302)


@pages_router.get("/v1/tasks/{task_id}/publish_bundle")
def download_publish_bundle(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tmpdir = tempfile.TemporaryDirectory()
    storage = get_storage_service()

    def _download_if_exists(key: str | None, dest: Path) -> bool:
        if not key or not object_exists(str(key)):
            return False
        try:
            storage.download_file(str(key), str(dest))
            return dest.exists()
        except Exception:
            return False

    pack_key = _task_value(task, "pack_key") or _task_value(task, "pack_path")
    scenes_key = _task_value(task, "scenes_key")
    missing = []
    if not pack_key or not object_exists(str(pack_key)):
        missing.append("pack_key")
    if str(_task_value(task, "scenes_status") or "").lower() != "skipped":
        if not scenes_key or not object_exists(str(scenes_key)):
            missing.append("scenes_key")
    if missing:
        return _not_ready_response(task, "publish_bundle", missing)
    pack_local = Path(tmpdir.name) / "pack.zip"
    scenes_local = Path(tmpdir.name) / "scenes.zip"

    _download_if_exists(str(pack_key) if pack_key else None, pack_local)
    _download_if_exists(str(scenes_key) if scenes_key else None, scenes_local)

    bundle = _build_copy_bundle(task)
    zip_path = Path(tmpdir.name) / f"publish_bundle_{task_id}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if pack_local.exists():
            zf.write(pack_local, arcname="pack.zip")
        if scenes_local.exists():
            zf.write(scenes_local, arcname="scenes.zip")
        zf.writestr("copy/caption.txt", bundle.get("caption", ""))
        zf.writestr("copy/hashtags.txt", bundle.get("hashtags", ""))
        zf.writestr("copy/comment_cta.txt", bundle.get("comment_cta", ""))
        zf.writestr("copy/link_text.txt", bundle.get("link_text", ""))
        zf.writestr(
            "copy/publish_time_suggestion.txt",
            bundle.get("publish_time_suggestion", ""),
        )
        zf.writestr("SOP.md", _publish_sop_markdown())
        zf.writestr(
            "README.md",
            "This is the edit bundle. Final publish bundle will be available in v2.0.\n",
        )

    def iterfile():
        with zip_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                yield chunk
        tmpdir.cleanup()

    headers = {
        "Content-Disposition": f"attachment; filename=publish_bundle_{task_id}.zip"
    }
    return StreamingResponse(iterfile(), media_type="application/zip", headers=headers)


@pages_router.get("/v1/tasks/{task_id}/publish_hub")
def v1_task_publish_hub(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _publish_hub_payload(task)


@pages_router.get("/v1/tasks/{task_id}/status")
def task_status(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    raw_key = _task_key(task, "raw_path")
    origin_key = _task_key(task, "origin_srt_path")
    mm_key = _task_key(task, "mm_srt_path")
    mm_txt_key = None
    if mm_key and mm_key.endswith(".srt"):
        mm_txt_key = f"{mm_key[:-4]}.txt"
    audio_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    pack_key = _task_key(task, "pack_key") or _task_key(task, "pack_path")
    scenes_key = _task_key(task, "scenes_pack_key") or _task_key(task, "scenes_key")

    return {
        "task_id": str(_task_value(task, "task_id") or _task_value(task, "id") or task_id),
        "status": _task_value(task, "status"),
        "last_step": _task_value(task, "last_step"),
        "subtitles_status": _task_value(task, "subtitles_status"),
        "subtitles_error": _task_value(task, "subtitles_error"),
        "dub_status": _task_value(task, "dub_status"),
        "dub_error": _task_value(task, "dub_error"),
        "pack_status": _task_value(task, "pack_status"),
        "pack_error": _task_value(task, "pack_error"),
        "scenes_status": _task_value(task, "scenes_status"),
        "scenes_error": _task_value(task, "scenes_error"),
        "raw_exists": bool(raw_key and object_exists(raw_key)),
        "origin_srt_exists": bool(origin_key and object_exists(origin_key)),
        "mm_srt_exists": bool(mm_key and object_exists(mm_key)),
        "mm_txt_exists": bool(mm_txt_key and object_exists(mm_txt_key)),
        "mm_audio_exists": bool(audio_key and object_exists(audio_key)),
        "pack_exists": bool(pack_key and object_exists(pack_key)),
        "scenes_exists": bool(scenes_key and object_exists(scenes_key)),
    }




def _task_endpoint(task_id: str, kind: str) -> Optional[str]:
    safe_id = str(task_id)
    if kind == "raw":
        return f"/v1/tasks/{safe_id}/raw"
    if kind == "origin":
        return f"/v1/tasks/{safe_id}/subs_origin"
    if kind == "mm":
        return f"/v1/tasks/{safe_id}/subs_mm"
    if kind == "mm_txt":
        return f"/v1/tasks/{safe_id}/mm_txt"
    if kind == "audio":
        return f"/v1/tasks/{safe_id}/audio_mm"
    if kind == "pack":
        return f"/v1/tasks/{safe_id}/pack"
    if kind == "scenes":
        return f"/v1/tasks/{safe_id}/scenes"
    if kind == "final":
        return f"/v1/tasks/{safe_id}/final"
    if kind == "publish_bundle":
        return f"/v1/tasks/{safe_id}/publish_bundle"
    return None


def _get_op_access_key() -> Optional[str]:
    key = (os.getenv("OP_ACCESS_KEY") or "").strip()
    return key or None


def _op_gate_enabled() -> bool:
    return bool(_get_op_access_key())


def _op_key_valid(request: Request) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    header_val = (request.headers.get(OP_HEADER_KEY) or "").strip()
    return hmac.compare_digest(header_val, secret)

def _op_key_valid_value(op_key: str | None) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    if not op_key:
        return False
    return hmac.compare_digest(op_key, secret)


def _require_op_key(request: Request) -> None:
    if not _op_key_valid(request):
        raise HTTPException(status_code=401, detail="OP key required")


def _op_sign(task_id: str, kind: str, exp: int) -> str:
    secret = _get_op_access_key()
    if not secret:
        return ""
    msg = f"{task_id}:{kind}:{exp}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def _op_verify(task_id: str, kind: str, exp: int, sig: str) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    if not sig:
        return False
    expected = _op_sign(task_id, kind, exp)
    return hmac.compare_digest(expected, sig)


def _download_code(task_id: str) -> str:
    return str(task_id).upper()[:6]


def _signed_op_url(task_id: str, kind: str) -> str:
    exp = int(time.time()) + 86400
    sig = _op_sign(task_id, kind, exp)
    base = f"/op/dl/{task_id}?kind={kind}&exp={exp}"
    return f"{base}&sig={sig}" if sig else base


def _read_mm_txt_from_task(task: dict) -> str:
    mm_key = _task_key(task, "mm_srt_path")
    if not mm_key:
        return ""
    txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
    if not object_exists(txt_key):
        return ""
    data = get_object_bytes(txt_key)
    if not data:
        return ""
    try:
        return data.decode("utf-8").strip()
    except UnicodeDecodeError:
        return data.decode(errors="ignore").strip()


def _publish_sop_markdown() -> str:
    return (
        "# Publish SOP\n"
        "1) Download the edit bundle (pack.zip).\n"
        "2) Import into CapCut and finish edits.\n"
        "3) Copy caption and hashtags from Copy Bundle.\n"
        "4) Publish manually (publish bundle in v2.0).\n"
    )


def _build_copy_bundle(task: dict) -> dict[str, str]:
    caption = _read_mm_txt_from_task(task) or (task.get("title") or "")
    return {
        "caption": caption.strip(),
        "hashtags": "",
        "comment_cta": "",
        "link_text": task.get("publish_url") or "",
        "publish_time_suggestion": "",
    }


def _deliverable_url(task_id: str, task: dict, kind: str) -> Optional[str]:
    if kind == "final_mp4":
        key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
        return _signed_op_url(task_id, "final_mp4") if key and object_exists(str(key)) else None
    if kind == "pack_zip":
        pack_type = _task_value(task, "pack_type")
        pack_key = _task_value(task, "pack_key") or _task_value(task, "pack_path")
        if pack_type == "capcut_v18" and pack_key and object_exists(str(pack_key)):
            return _signed_op_url(task_id, "pack")
        if pack_key and object_exists(str(pack_key)):
            return _signed_op_url(task_id, "pack")
        return None
    if kind == "scenes_zip":
        scenes_key = _task_value(task, "scenes_pack_key") or _task_value(task, "scenes_key")
        scenes_path = _task_value(task, "scenes_path")
        scenes_status = str(_task_value(task, "scenes_pack_status") or _task_value(task, "scenes_status") or "").lower()
        if scenes_key and object_exists(str(scenes_key)):
            return _signed_op_url(task_id, "scenes")
        if scenes_path and scenes_status == "ready":
            return _signed_op_url(task_id, "scenes")
        return None
    if kind == "origin_srt":
        key = _task_key(task, "origin_srt_path")
        return _signed_op_url(task_id, "origin_srt") if key and object_exists(key) else None
    if kind == "mm_srt":
        key = _task_key(task, "mm_srt_path")
        return _signed_op_url(task_id, "mm_srt") if key and object_exists(key) else None
    if kind == "mm_txt":
        mm_key = _task_key(task, "mm_srt_path")
        if not mm_key:
            return None
        txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
        return _signed_op_url(task_id, "mm_txt") if object_exists(txt_key) else None
    if kind == "mm_audio":
        key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
        return _signed_op_url(task_id, "mm_audio") if key and object_exists(key) else None
    if kind == "edit_bundle_zip":
        return _signed_op_url(task_id, "publish_bundle")
    return None


def _compose_error_parts(task: dict) -> tuple[str | None, str | None]:
    reason_field = task.get("compose_error_reason")
    raw = task.get("compose_error")
    if not reason_field and not raw:
        return (None, None)
    if isinstance(raw, dict):
        reason = raw.get("reason")
        message = raw.get("message")
        resolved_reason = str(reason) if reason else (str(reason_field) if reason_field else None)
        resolved_message = str(message) if message else None
        return (resolved_reason, resolved_message)
    text = str(raw).strip() if raw is not None else ""
    if not text:
        return (None, None)
    return (str(reason_field) if reason_field else "compose_failed", text)


def _compute_composed_state(task: dict, task_id: str) -> dict[str, Any]:
    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path") or deliver_key(task_id, "final.mp4")
    final_meta = object_head(str(final_key)) if final_key and object_exists(str(final_key)) else None
    final_size, final_ctype = media_meta_from_head(final_meta)
    final_asset_version = (
        task.get("final_asset_version")
        or (final_meta.get("etag") if isinstance(final_meta, dict) else None)
        or task.get("final_video_sha256")
        or None
    )
    final_exists = bool(final_key and object_exists(str(final_key)) and int(final_size or 0) > 0)
    raw_key = _task_key(task, "raw_path")
    raw_exists = bool(raw_key and object_exists(str(raw_key)))
    voice_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    voice_exists = bool(voice_key and object_exists(str(voice_key)))
    voice_state = _collect_voice_execution_state(task, get_settings())
    no_dub_state = _hf_detect_no_dub_candidate(task_id, task)
    compose_status = str(task.get("compose_status") or "").lower()
    compose_last_status = str(task.get("compose_last_status") or compose_status).lower()
    compose_done = compose_last_status in {"done", "ready", "success", "completed"}
    compose_error_reason, compose_error_message = _compose_error_parts(task)

    composed_ready = bool(
        final_exists
        and compose_done
        and compose_error_reason is None
        and bool(voice_state.get("audio_ready"))
    )
    if composed_ready:
        composed_reason = "ready"
    elif not raw_exists:
        composed_reason = "missing_raw"
    elif not voice_exists:
        composed_reason = "missing_voiceover"
    elif not voice_state.get("audio_ready"):
        composed_reason = str(voice_state.get("audio_ready_reason") or "audio_not_ready")
    elif compose_status in {"running", "processing", "queued"}:
        composed_reason = "compose_in_progress"
    elif compose_error_reason in {"subtitles_missing", "font_missing"}:
        composed_reason = compose_error_reason
    elif compose_error_reason or compose_status in {"failed", "error"}:
        composed_reason = "compose_failed"
    else:
        composed_reason = "final_missing"

    final_info = {
        "exists": final_exists,
        "key": str(final_key) if final_key else None,
        "size_bytes": int(final_size) if final_size is not None else None,
        "duration_ms": int(task.get("final_duration_ms")) if task.get("final_duration_ms") is not None else None,
        "asset_version": str(final_asset_version) if final_asset_version else None,
        "updated_at": task.get("final_updated_at") or task.get("updated_at"),
        "content_type": task.get("final_mime") or final_ctype or "video/mp4",
        "url": _task_endpoint(task_id, "final") if final_exists and int(final_size or 0) >= MIN_VIDEO_BYTES else None,
    }
    return {
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final": final_info,
        "compose_error_reason": compose_error_reason,
        "compose_error_message": compose_error_message,
        "raw_exists": raw_exists,
        "voice_exists": voice_exists,
        "audio_ready": bool(voice_state.get("audio_ready")),
        "audio_ready_reason": voice_state.get("audio_ready_reason"),
    }


def _scene_pack_info(task: dict, task_id: str) -> dict[str, Any]:
    key = (
        _task_key(task, "scenes_key")
        or _task_key(task, "scenes_pack_key")
        or f"deliver/scenes/{task_id}/scenes.zip"
    )
    scenes_key_ready = bool(_task_key(task, "scenes_key"))
    exists = bool(key and object_exists(str(key)))
    if scenes_key_ready:
        exists = True
    meta = object_head(str(key)) if exists else None
    size_bytes, _ = media_meta_from_head(meta)
    status_raw = str(task.get("scenes_pack_last_status") or task.get("scenes_pack_status") or task.get("scenes_status") or "").lower()
    if status_raw in {"ready", "done", "success", "completed"}:
        status = "done"
    elif status_raw in {"running", "processing", "queued"}:
        status = "running"
    elif status_raw in {"failed", "error"}:
        status = "failed"
    else:
        status = "pending"
    if scenes_key_ready:
        status = "done"
    elif exists and status != "running":
        status = "done"
    return {
        "exists": exists,
        "key": str(key) if key else None,
        "url": _task_endpoint(task_id, "scenes") if exists else None,
        "size_bytes": int(size_bytes) if size_bytes is not None else None,
        "asset_version": (meta.get("etag") if isinstance(meta, dict) else None) or task.get("scenes_pack_asset_version"),
        "status": status,
        "started_at": task.get("scenes_pack_last_started_at"),
        "finished_at": task.get("scenes_pack_last_finished_at"),
        "error": task.get("scenes_pack_error") or task.get("scenes_error"),
        "error_reason": task.get("scenes_pack_error_reason"),
    }


def _compose_done_like(status: Any) -> bool:
    return str(status or "").strip().lower() in {"done", "ready", "success", "completed"}


def _deliverables_final_url(deliverables: Any) -> str | None:
    if isinstance(deliverables, dict):
        final_item = deliverables.get("final_mp4")
        if isinstance(final_item, dict):
            url = final_item.get("url")
            if url:
                return str(url)
    if isinstance(deliverables, list):
        for item in deliverables:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip().lower()
            key = str(item.get("key") or "").strip().lower()
            label = str(item.get("label") or item.get("title") or "").strip().lower()
            if kind == "final" or key.endswith("final.mp4") or "final video" in label or label == "final.mp4":
                url = item.get("url")
                if url:
                    return str(url)
    return None


def _resolve_hub_final_url(task_id: str, hub: dict[str, Any] | None = None) -> str | None:
    payload = hub or {}
    media = payload.get("media") if isinstance(payload.get("media"), dict) else {}
    extra = payload.get("extra") if isinstance(payload.get("extra"), dict) else {}
    url = (
        _deliverables_final_url(payload.get("deliverables"))
        or media.get("final_url")
        or media.get("final_video_url")
        or payload.get("final_url")
        or payload.get("final_video_url")
        or extra.get("final_video_url")
        or None
    )
    if url:
        return str(url)
    final_info = payload.get("final") if isinstance(payload.get("final"), dict) else {}
    final_exists_hint = bool(final_info.get("exists"))
    compose_like_done = _compose_done_like(payload.get("compose_status")) or _compose_done_like(payload.get("compose_last_status"))
    if final_exists_hint or compose_like_done:
        return _task_endpoint(task_id, "final")
    return None


def _backfill_compose_done_if_final_ready(repo, task_id: str, task: dict, composed_ready: bool) -> bool:
    if not composed_ready:
        return False
    compose_status = str(task.get("compose_status") or "").strip().lower()
    compose_last_status = str(task.get("compose_last_status") or "").strip().lower()
    pipeline_compose_status = ""
    pipeline = task.get("pipeline")
    if isinstance(pipeline, dict):
        compose_node = pipeline.get("compose")
        if isinstance(compose_node, dict):
            pipeline_compose_status = str(compose_node.get("status") or "").strip().lower()
    if _compose_done_like(compose_status) and _compose_done_like(compose_last_status or compose_status) and (
        not pipeline_compose_status or _compose_done_like(pipeline_compose_status)
    ):
        return False
    now = datetime.now(timezone.utc).isoformat()
    updates: dict[str, Any] = {
        "compose_status": "done",
        "compose_last_status": "done",
        "compose_error": None,
        "compose_error_reason": None,
        "compose_last_error": None,
        "compose_last_finished_at": now,
        "updated_at": now,
    }
    if not task.get("compose_last_started_at"):
        updates["compose_last_started_at"] = now
    task_status = str(task.get("status") or "").strip().lower()
    if task_status in {"", "pending", "processing", "running", "queued", "failed", "error"}:
        updates["status"] = "ready"
    if isinstance(pipeline, dict):
        patched_pipeline = dict(pipeline)
        compose_node = patched_pipeline.get("compose")
        compose_dict = dict(compose_node) if isinstance(compose_node, dict) else {}
        compose_dict["status"] = "done"
        compose_dict["state"] = "done"
        compose_dict["updated_at"] = now
        patched_pipeline["compose"] = compose_dict
        updates["pipeline"] = patched_pipeline
    _policy_upsert(repo, task_id, updates)
    logger.info("hot_follow_compose_backfill_done", extra={"task_id": task_id})
    return True


def _publish_hub_payload(task: dict) -> dict[str, object]:
    task_id = str(_task_value(task, "task_id") or _task_value(task, "id") or "")
    composed = _compute_composed_state(task, task_id)
    scene_pack = _scene_pack_info(task, task_id)

    deliverables = {}
    for key, label in (
        ("final_mp4", "final.mp4"),
        ("pack_zip", "pack.zip"),
        ("scenes_zip", "scenes.zip"),
        ("origin_srt", "origin.srt"),
        ("mm_srt", "mm.srt"),
        ("mm_txt", "mm.txt"),
        ("mm_audio", "mm_audio"),
        ("edit_bundle_zip", "scenes_bundle.zip"),
    ):
        url = _deliverable_url(task_id, task, key)
        if url:
            item = {"label": label, "url": url}
            if key == "edit_bundle_zip":
                item["artifact"] = "scenes_bundle"
                item["description"] = "Scenes package for re-editing / advanced workflow"
            deliverables[key] = item
    scene_pack_pending_reason = None
    if not bool(scene_pack.get("exists")):
        if scene_pack.get("status") == "running":
            scene_pack_pending_reason = "scenes.running"
        elif scene_pack.get("status") == "failed":
            scene_pack_pending_reason = "scenes.failed"
        else:
            scene_pack_pending_reason = "scenes.not_ready"
    short_code = _download_code(task_id)
    short_url = f"/d/{short_code}"
    final_payload_probe = {
        "deliverables": deliverables,
        "media": {"final_video_url": (composed.get("final") or {}).get("url"), "final_url": (composed.get("final") or {}).get("url")},
        "final": composed.get("final") or {"exists": False},
        "compose_status": task.get("compose_status"),
        "compose_last_status": task.get("compose_last_status"),
    }
    final_preview_url = _resolve_hub_final_url(task_id, final_payload_probe)
    composed_ready = bool(final_preview_url or (composed.get("final") or {}).get("exists"))
    composed_reason = "ready" if composed_ready else "not_ready"
    if final_preview_url:
        final_item = dict(deliverables.get("final_mp4") or {"label": "final.mp4"})
        final_item["url"] = final_preview_url
        deliverables["final_mp4"] = final_item

    return {
        "task_id": task_id,
        "gate_enabled": _op_gate_enabled(),
        "media": {
            "final_video_url": final_preview_url,
            "final_url": final_preview_url,
        },
        "final_url": final_preview_url,
        "final_video_url": final_preview_url,
        "deliverables": deliverables,
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final": composed.get("final") or {"exists": False},
        "scene_pack": scene_pack,
        "scene_pack_pending_reason": scene_pack_pending_reason,
        "scene_pack_action_url": f"/tasks/{task_id}",
        "copy_bundle": _build_copy_bundle(task),
        "download_code": short_code,
        "mobile": {
            "qr_target": short_url,
            "short_link": short_url,
            "short_url": short_url,
            "qr_url": short_url,
        },
        "sop_markdown": _publish_sop_markdown(),
        "archive": {
            "publish_provider": task.get("publish_provider") or "-",
            "publish_key": task.get("publish_key") or "-",
            "publish_status": task.get("publish_status") or "-",
            "publish_url": task.get("publish_url") or "-",
            "published_at": task.get("published_at") or "-",
        },
    }


def _hf_state_from_status(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in {"ready", "done", "success", "completed"}:
        return "done"
    if v in {"running", "processing", "queued"}:
        return "running"
    if v in {"failed", "error"}:
        return "failed"
    return "pending"


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
    voice_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    meta = object_head(str(voice_key)) if voice_key else None
    size, _ = media_meta_from_head(meta)
    voice_url = f"/v1/tasks/{task_id}/audio_mm" if task_id and size >= MIN_AUDIO_BYTES else None
    voice_state = _collect_voice_execution_state(task, settings)
    provider = normalize_provider(voice_state.get("expected_provider") or task.get("dub_provider") or getattr(settings, "dub_provider", None))
    return {
        "tts_engine": _hf_engine_public(provider),
        "tts_voice": voice_state.get("resolved_voice"),
        "bgm_key": bgm.get("bgm_key"),
        "bgm_mix": max(0.0, min(1.0, mix_val)),
        "bgm_url": get_download_url(str(bgm.get("bgm_key"))) if bgm.get("bgm_key") else None,
        "voiceover_url": voice_url,
        "audio_url": voice_url,
        "audio_fit_max_speed": audio_fit_max_speed,
    }


def _hf_subtitles_override_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "subtitles" / "subtitles_override.srt"


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
        normalized_path = task_base_dir(task_id) / "subtitles" / "origin_normalized.srt"
        if normalized_path.exists():
            try:
                return normalized_path.read_text(encoding="utf-8")
            except Exception:
                return normalized_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
    return _hf_load_origin_subtitles_text(task)


def _hf_dub_input_text(task_id: str, task: dict, manual_text: str | None = None) -> str:
    manual_value = str(manual_text or "").strip()
    if manual_value:
        return manual_value
    edited_text = _hf_load_subtitles_text(task_id, task)
    if str(edited_text or "").strip():
        return str(edited_text)
    normalized_text = _hf_load_normalized_source_text(task_id, task)
    if str(normalized_text or "").strip():
        return str(normalized_text)
    return _hf_load_origin_subtitles_text(task)


def _hf_source_subtitle_cover_filter(compose_plan: dict[str, Any] | None, config: dict[str, Any] | None = None) -> str | None:
    plan = dict(compose_plan or {})
    cfg = dict(config or {})
    enabled = (
        bool(plan.get("source_subtitle_cover_enabled"))
        or str(cfg.get("source_subtitle_cover_enabled") or os.getenv("HF_SUBTITLE_COVER_ENABLED", "0")).strip().lower() in {"1", "true", "yes"}
    )
    if not enabled:
        return None
    mode = str(plan.get("source_subtitle_cover_mode") or cfg.get("source_subtitle_cover_mode") or os.getenv("HF_SUBTITLE_COVER_MODE", "bottom_band")).strip().lower()
    if mode != "bottom_band":
        return None
    return "drawbox=x=0:y=ih*0.78:w=iw:h=ih*0.22:color=black@1.0:t=fill"


def _hf_no_dub_note_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "dub" / "no_dub.txt"


def _hf_write_no_dub_note(task_id: str, reason: str) -> None:
    note_path = _hf_no_dub_note_path(task_id)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(str(reason or "no_speech_detected").strip() + "\n", encoding="utf-8")


def _hf_clear_no_dub_note(task_id: str) -> None:
    note_path = _hf_no_dub_note_path(task_id)
    try:
        if note_path.exists():
            note_path.unlink()
    except Exception:
        logger.warning("HF_NO_DUB_NOTE_CLEAR_FAIL task=%s path=%s", task_id, note_path)


def _hf_plain_text_signal(text: str | None) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if value in {"NO_SUBTITLES_MARKER", "MM_TXT_MISSING"}:
        return ""
    if "NO_SUBTITLES_MARKER" in value or "MM_TXT_MISSING" in value:
        return ""
    return value


def _hf_has_usable_dub_text(text: str | None) -> bool:
    return bool(_hf_plain_text_signal(text))


def _hf_dual_channel_state(task_id: str, task: dict) -> dict[str, Any]:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    origin_text = _hf_load_origin_subtitles_text(task)
    normalized_source_text = _hf_load_normalized_source_text(task_id, task)
    edited_text = _hf_load_subtitles_text(task_id, task)
    title_hint = " ".join(
        [
            str(task.get("title") or ""),
            str(task.get("source_title") or ""),
            str(task.get("note") or ""),
            str(task.get("source_url") or ""),
        ]
    ).lower()
    speech_text = _hf_plain_text_signal(normalized_source_text) or _hf_plain_text_signal(origin_text)
    speech_text_compact = "".join(str(speech_text or "").split())
    subtitle_meta_hint = any(
        token in title_hint
        for token in ("字幕", "caption", "subtitle", "subtitles", "文案", "上字", "双语", "text-led", "text led")
    )
    subtitle_stream = pipeline_config.get("subtitle_stream") == "true" or bool(
        str(pipeline_config.get("subtitle_track_kind") or "").strip()
    )
    subtitle_basis = _hf_plain_text_signal(edited_text) or _hf_plain_text_signal(normalized_source_text) or _hf_plain_text_signal(origin_text)
    subtitle_basis_compact = "".join(str(subtitle_basis or "").split())

    speech_detected = len(speech_text_compact) >= 6
    if speech_detected:
        speech_confidence = "high" if len(speech_text_compact) >= 20 else "low"
    else:
        speech_confidence = "none"

    onscreen_text_detected = bool(
        subtitle_stream
        or subtitle_meta_hint
        or (not speech_detected and len(subtitle_basis_compact) >= 4)
    )
    if not onscreen_text_detected:
        onscreen_text_density = "none"
    else:
        onscreen_text_density = "high" if len(subtitle_basis_compact) >= 20 else "low"

    if speech_detected:
        content_mode = "voice_led"
    elif onscreen_text_detected:
        content_mode = "subtitle_led_candidate"
    else:
        content_mode = "silent_candidate"

    return {
        "speech_detected": speech_detected,
        "speech_confidence": speech_confidence,
        "onscreen_text_detected": onscreen_text_detected,
        "onscreen_text_density": onscreen_text_density,
        "content_mode": content_mode,
    }


def _hf_detect_no_dub_candidate(task_id: str, task: dict, manual_text: str | None = None) -> dict[str, Any]:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    origin_text = _hf_load_origin_subtitles_text(task)
    normalized_source_text = _hf_load_normalized_source_text(task_id, task)
    edited_text = _hf_load_subtitles_text(task_id, task)
    manual_value = _hf_dub_input_text(task_id, task, manual_text).strip() if manual_text is not None else str(manual_text or "").strip()
    title_hint = " ".join(
        [
            str(task.get("title") or ""),
            str(task.get("source_title") or ""),
            str(task.get("note") or ""),
        ]
    ).lower()
    silent_hint = any(token in title_hint for token in ("无人声", "asmr", "涂抹音", "无语音", "no voice"))
    no_subtitles_flag = pipeline_config.get("no_subtitles") == "true"
    no_dub_flag = pipeline_config.get("no_dub") == "true"
    no_marker = any(
        token in " ".join([origin_text, edited_text, manual_value])
        for token in ("NO_SUBTITLES_MARKER", "MM_TXT_MISSING")
    )
    if _hf_has_usable_dub_text(manual_value) or _hf_has_usable_dub_text(edited_text):
        return {"no_dub": False, "no_dub_reason": None, "no_dub_message": None}
    empty_transcript = (
        not _hf_has_usable_dub_text(origin_text)
        and not _hf_has_usable_dub_text(normalized_source_text)
        and not _hf_has_usable_dub_text(edited_text)
        and not _hf_has_usable_dub_text(manual_value)
    )
    channel_state = _hf_dual_channel_state(task_id, task)
    if channel_state.get("content_mode") == "subtitle_led_candidate" and empty_transcript:
        return {
            "no_dub": True,
            "no_dub_reason": "subtitle_led_candidate",
            "no_dub_message": "未检测到可靠语音，但疑似存在画面字幕/文字内容。当前版本不会默认自动 OCR，请先检查字幕或手工补充文本后再生成配音。",
        }
    if channel_state.get("content_mode") == "silent_candidate" or no_subtitles_flag or no_dub_flag or no_marker or silent_hint or empty_transcript:
        reason = "no_speech_detected" if (silent_hint or no_marker or no_subtitles_flag or no_dub_flag) else "silent_candidate"
        message = (
            "当前素材更像无人声 / ASMR 素材，已跳过配音。如需继续，请手工编辑字幕文本后再生成配音。"
            if reason in {"no_speech_detected", "silent_candidate"}
            else "未检测到可配音语音内容，已跳过配音。如需继续，请手工编辑字幕文本后再生成配音。"
        )
        return {"no_dub": True, "no_dub_reason": reason, "no_dub_message": message}
    return {"no_dub": False, "no_dub_reason": None, "no_dub_message": None}


def _hf_pipeline_state(task: dict, step: str) -> tuple[str, str]:
    last_step = str(task.get("last_step") or "").lower()
    task_status = str(task.get("status") or "").lower()
    if step == "parse":
        status = _hf_state_from_status(task.get("parse_status"))
        if status == "pending" and task.get("raw_path"):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "parse":
            status = "running"
        summary = "raw=ready" if task.get("raw_path") else "raw=none"
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
        if voice_state.get("no_dub"):
            status = "pending"
            return status, str(voice_state.get("no_dub_message") or "dubbing skipped")
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
        final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
        if status == "pending" and final_key and object_exists(str(final_key)):
            status = "done"
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
            _hf_deliverable_state(task, raw_key, "parse_status"),
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
def _task_value(task: dict, field: str) -> Optional[str]:
    if isinstance(task, dict):
        value = task.get(field)
        if value is None:
            deliverables = task.get("deliverables")
            if isinstance(deliverables, dict):
                value = deliverables.get(field)
        return value
    return getattr(task, field, None)


def _task_key(task: dict, field: str) -> Optional[str]:
    value = _task_value(task, field)
    return str(value) if value else None


def _scenes_status_from_ssot(task: dict) -> str:
    if _task_key(task, "scenes_key"):
        return "done"
    if _task_value(task, "scenes_error"):
        return "failed"
    started_at = _task_value(task, "scenes_started_at")
    finished_at = _task_value(task, "scenes_finished_at")
    if started_at and not finished_at:
        return "running"
    events = task.get("events") if isinstance(task, dict) else None
    if isinstance(events, list):
        for ev in reversed(events):
            if not isinstance(ev, dict):
                continue
            if str(ev.get("channel") or "").lower() != "scenes":
                continue
            code = str(ev.get("code") or "").upper()
            if code in {"SCENES_RUN_DONE"}:
                return "done"
            if code in {"SCENES_RUN_FAIL", "SCENES_RUN_FAILED"}:
                return "failed"
            if code in {"SCENES_ENQUEUE", "SCENES_RUN_START"}:
                return "running"
            break
    return "pending"


def derive_status(task: dict) -> str:
    pack_key = _task_value(task, "pack_key") or _task_value(task, "pack_path")
    if pack_key:
        try:
            if object_exists(str(pack_key)):
                return "ready"
        except Exception:
            pass
        return "ready"
    return task.get("status") or "processing"


def _require_storage_key(task: dict, field: str, not_found: str) -> str:
    key = _task_key(task, field)
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail=not_found)
    return key


def _not_ready_response(
    task: dict,
    artifact: str,
    missing: list[str],
    *,
    reason: str = "not_ready",
    status_code: int = 409,
    extra: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "reason": reason,
            "task_id": str(_task_value(task, "task_id") or _task_value(task, "id") or ""),
            "artifact": artifact,
            "missing": missing,
            "status": {
                "subtitles": _task_value(task, "subtitles_status"),
                "dub": _task_value(task, "dub_status"),
                "scenes": _task_value(task, "scenes_status"),
                "pack": _task_value(task, "pack_status"),
                "publish": _task_value(task, "publish_status"),
            },
            "hint": "Call generate or wait for pipeline to finish.",
            **(extra or {}),
        },
    )


def _text_or_redirect(key: str, inline: bool) -> Response:
    if inline:
        data = get_object_bytes(key)
        if data is None:
            raise HTTPException(status_code=404, detail="artifact not found")
        return Response(content=data, media_type="text/plain; charset=utf-8")
    return RedirectResponse(url=get_download_url(key), status_code=302)


def _ensure_mp3_audio(src_path: Path, dst_path: Path) -> Path:
    if src_path.suffix.lower() == ".mp3":
        return src_path

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise HTTPException(status_code=500, detail="ffmpeg not found for mp3 conversion")

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
        raise HTTPException(
            status_code=500,
            detail=f"ffmpeg mp3 conversion failed: {p.stderr[-800:]}",
        )
    return dst_path


def _subtitle_cache_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "subtitle_streams.json"


def _detect_subtitle_streams(raw_file: Path) -> dict[str, Any]:
    if not raw_file.exists():
        return {"status": "unknown", "reason": "raw_missing"}

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"status": "unknown", "reason": "ffprobe_missing"}

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        str(raw_file),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return {"status": "unknown", "reason": "ffprobe_failed"}

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "unknown", "reason": "ffprobe_bad_json"}

    streams = payload.get("streams", []) or []
    subtitle_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
    minimal_streams = [
        {
            "index": s.get("index"),
            "codec_name": s.get("codec_name"),
            "codec_type": s.get("codec_type"),
            "tags": s.get("tags") or {},
        }
        for s in subtitle_streams
    ]
    return {
        "status": "ok",
        "has_subtitle_stream": bool(subtitle_streams),
        "subtitle_streams": minimal_streams,
    }


def _get_subtitle_detection(task_id: str) -> dict[str, Any]:
    cache_path = _subtitle_cache_path(task_id)
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    raw_file = raw_path(task_id)
    result = _detect_subtitle_streams(raw_file)
    try:
        cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return result


def _resolve_download_urls(task: dict) -> dict[str, Optional[str]]:
    task_id = str(task.get("task_id") or task.get("id"))
    raw_url = _task_endpoint(task_id, "raw") if task.get("raw_path") else None
    origin_url = (
        _task_endpoint(task_id, "origin")
        if task.get("origin_srt_path")
        else None
    )
    mm_url = (
        _task_endpoint(task_id, "mm")
        if task.get("mm_srt_path")
        else None
    )
    audio_url = (
        _task_endpoint(task_id, "audio")
        if task.get("mm_audio_key") or task.get("mm_audio_path")
        else None
    )
    mm_txt_url = _task_endpoint(task_id, "mm_txt") if mm_url else None
    pack_key = task.get("pack_key")
    pack_type = task.get("pack_type")
    pack_url = None
    if pack_type == "capcut_v18" and pack_key:
        pack_url = _task_endpoint(task_id, "pack")
    elif task.get("pack_path"):
        pack_url = _task_endpoint(task_id, "pack")
    scenes_url = _task_endpoint(task_id, "scenes") if _task_value(task, "scenes_key") else None

    return {
        "raw_path": raw_url,
        "origin_srt_path": origin_url,
        "mm_srt_path": mm_url,
        "mm_audio_path": audio_url,
        "mm_txt_path": mm_txt_url,
        "pack_path": pack_url,
        "scenes_path": scenes_url,
    }

def _model_allowed_fields(model_cls) -> set[str]:
    # pydantic v2: model_fields; v1: __fields__
    if hasattr(model_cls, "model_fields"):
        return set(model_cls.model_fields.keys())
    if hasattr(model_cls, "__fields__"):
        return set(model_cls.__fields__.keys())
    return set()


def _normalize_selected_tool_ids(value: Any) -> Optional[list[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            decoded = json.loads(text)
        except Exception:
            decoded = None
        if isinstance(decoded, list):
            return [str(v) for v in decoded if str(v).strip()]
        return [v.strip() for v in text.split(",") if v.strip()]
    return None

def _task_to_detail(task: dict) -> TaskDetail:
    paths = _resolve_download_urls(task)
    status = derive_status(task)
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))

    payload = {
        "task_id": str(task.get("task_id") or task.get("id")),
        "title": task.get("title"),
        "kind": task.get("kind"),
        "source_url": str(task.get("source_url")) if task.get("source_url") else None,
        "source_link_url": _extract_first_http_url(task.get("source_url")),
        "platform": task.get("platform"),
        "account_id": task.get("account_id"),
        "account_name": task.get("account_name"),
        "video_type": task.get("video_type"),
        "template": task.get("template"),
        "category_key": task.get("category_key") or "beauty",
        "content_lang": task.get("content_lang") or "my",
        "ui_lang": task.get("ui_lang") or "en",
        "style_preset": task.get("style_preset"),
        "face_swap_enabled": bool(task.get("face_swap_enabled")),
        "status": status,
        "last_step": task.get("last_step"),
        "duration_sec": task.get("duration_sec"),
        "thumb_url": task.get("thumb_url"),

        "raw_path": paths.get("raw_path"),
        "origin_srt_path": paths.get("origin_srt_path"),
        "mm_srt_path": paths.get("mm_srt_path"),
        "mm_audio_path": paths.get("mm_audio_path"),
        "mm_audio_key": task.get("mm_audio_key"),
        "pack_path": paths.get("pack_path"),
        "scenes_path": paths.get("scenes_path"),
        "scenes_status": _scenes_status_from_ssot(task),
        "scenes_key": task.get("scenes_key"),
        "scenes_error": task.get("scenes_error"),
        "scenes_started_at": task.get("scenes_started_at"),
        "scenes_finished_at": task.get("scenes_finished_at"),
        "scenes_elapsed_ms": task.get("scenes_elapsed_ms"),
        "scenes_attempt": task.get("scenes_attempt"),
        "scenes_run_id": task.get("scenes_run_id"),
        "scenes_error_message": task.get("scenes_error_message"),
        "subtitles_status": task.get("subtitles_status"),
        "subtitles_key": task.get("subtitles_key"),
        "subtitles_error": task.get("subtitles_error"),

        "created_at": _coerce_datetime(task.get("created_at") or task.get("created") or task.get("createdAt")),
        "updated_at": _coerce_datetime(task.get("updated_at") or task.get("updatedAt")),
        "error_message": task.get("error_message"),
        "error_reason": task.get("error_reason"),

        # 涓嬮潰杩欎簺瀛楁濡傛灉 TaskDetail 娌″畾涔夛紝浼氳杩囨护鎺夛紝涓嶅啀瑙﹀彂 500
        "parse_provider": task.get("parse_provider"),
        "subtitles_provider": task.get("subtitles_provider"),
        "dub_provider": task.get("dub_provider"),
        "pack_provider": task.get("pack_provider"),
        "face_swap_provider": task.get("face_swap_provider"),
        "publish_status": task.get("publish_status"),
        "publish_provider": task.get("publish_provider"),
        "publish_key": task.get("publish_key"),
        "publish_url": task.get("publish_url"),
        "published_at": task.get("published_at"),
        "priority": task.get("priority"),
        "assignee": task.get("assignee"),
        "ops_notes": task.get("ops_notes"),
        "selected_tool_ids": _normalize_selected_tool_ids(task.get("selected_tool_ids")),
        "pipeline_config": pipeline_config,
        "no_dub": pipeline_config.get("no_dub") == "true",
        "dub_skip_reason": pipeline_config.get("dub_skip_reason"),
        "subtitle_track_kind": pipeline_config.get("subtitle_track_kind"),
    }

    allowed = _model_allowed_fields(TaskDetail)
    payload = {k: v for k, v in payload.items() if k in allowed}
    return TaskDetail(**payload)


def _extract_first_http_url(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"https?://\S+", text)
    return match.group(0) if match else None


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _repo_upsert(repo, task_id: str, patch: dict) -> None:
    _policy_upsert(repo, task_id, patch)


def _build_hot_follow_voice_options(settings, target_lang: str | None) -> dict[str, list[dict[str, str]]]:
    if normalize_target_lang(target_lang) != "my":
        return {"azure_speech": [], "edge_tts": []}

    options: dict[str, list[dict[str, str]]] = {"azure_speech": [], "edge_tts": []}
    azure_map = getattr(settings, "azure_tts_voice_map", {}) or {}
    if azure_map.get("mm_female_1"):
        options["azure_speech"].append({"value": "mm_female_1", "label": "缅语女声（标准）"})
    if azure_map.get("mm_male_1"):
        options["azure_speech"].append({"value": "mm_male_1", "label": "缅语男声（标准）"})

    edge_map = getattr(settings, "edge_tts_voice_map", {}) or {}
    if edge_map.get("mm_female_1"):
        options["edge_tts"].append({"value": "mm_female_1", "label": "缅语女声（标准）"})
    if edge_map.get("mm_male_1"):
        options["edge_tts"].append({"value": "mm_male_1", "label": "缅语男声（标准）"})
    return options


def _resolve_hot_follow_requested_voice(
    settings,
    task: dict,
    provider: str | None,
) -> str | None:
    config = dict(task.get("config") or {})
    requested = str(
        config.get("tts_requested_voice")
        or config.get("hot_follow_tts_requested_voice")
        or ""
    ).strip() or None
    if requested:
        return requested

    provider_norm = normalize_provider(provider)
    reverse_edge = {
        str(v).strip(): str(k).strip()
        for k, v in ((getattr(settings, "edge_tts_voice_map", {}) or {}).items())
        if str(k).strip() and str(v).strip()
    }
    reverse_azure = {
        str(v).strip(): str(k).strip()
        for k, v in ((getattr(settings, "azure_tts_voice_map", {}) or {}).items())
        if str(k).strip() and str(v).strip()
    }
    reverse_lovo = {}
    if getattr(settings, "lovo_speaker_mm_female_1", None):
        reverse_lovo[str(getattr(settings, "lovo_speaker_mm_female_1")).strip()] = "mm_female_1"
    if getattr(settings, "lovo_speaker_mm_male_1", None):
        reverse_lovo[str(getattr(settings, "lovo_speaker_mm_male_1")).strip()] = "mm_male_1"

    for candidate in (task.get("voice_id"), task.get("mm_audio_voice_id")):
        voice = str(candidate or "").strip() or None
        if not voice:
            continue
        if voice in {"mm_female_1", "mm_male_1", "mm_female_2"}:
            return voice
        if provider_norm == "edge-tts" and voice in reverse_edge:
            return reverse_edge[voice]
        if provider_norm == "azure-speech" and voice in reverse_azure:
            return reverse_azure[voice]
        if provider_norm == "lovo" and voice in reverse_lovo:
            return reverse_lovo[voice]
    return None


def _hot_follow_expected_provider(task: dict, requested_voice: str | None, default_provider: str | None) -> str:
    provider = normalize_provider(default_provider)
    target_lang = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    if str(task.get("kind") or "").strip().lower() == "hot_follow" and target_lang == "my":
        requested = str(requested_voice or "").strip()
        if not requested or requested in {"mm_female_1", "mm_male_1"}:
            return "azure-speech"
    return provider


def _voice_state_config(task: dict) -> dict[str, Any]:
    config = dict(task.get("config") or {})
    return {
        "requested_voice": str(config.get("tts_requested_voice") or config.get("hot_follow_tts_requested_voice") or "").strip() or None,
        "resolved_voice": str(config.get("tts_resolved_voice") or "").strip() or None,
        "provider": normalize_provider(config.get("tts_provider") or task.get("dub_provider") or get_settings().dub_provider),
        "request_token": str(config.get("tts_request_token") or "").strip() or None,
        "completed_token": str(config.get("tts_completed_token") or "").strip() or None,
    }


def _resolve_hot_follow_provider_voice(
    settings,
    provider: str | None,
    requested_voice: str | None,
    *,
    task: dict | None = None,
) -> str | None:
    if isinstance(task, dict):
        actual_voice = str(task.get("mm_audio_voice_id") or "").strip() or None
        if actual_voice:
            return actual_voice
    requested = str(requested_voice or "").strip() or None
    if not requested:
        return None
    provider_norm = normalize_provider(provider)
    if provider_norm == "edge-tts":
        return (getattr(settings, "edge_tts_voice_map", {}) or {}).get(requested, requested)
    if provider_norm == "azure-speech":
        return (getattr(settings, "azure_tts_voice_map", {}) or {}).get(requested, requested)
    if provider_norm == "lovo":
        if requested == "mm_female_1":
            return getattr(settings, "lovo_speaker_mm_female_1", None) or requested
        if requested == "mm_male_1":
            return getattr(settings, "lovo_speaker_mm_male_1", None) or requested
    return requested


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


def _collect_voice_execution_state(task: dict, settings) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    target_lang = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    voice_options_by_provider = _build_hot_follow_voice_options(settings, target_lang)
    config_state = _voice_state_config(task)
    requested_voice = config_state.get("requested_voice") or _resolve_hot_follow_requested_voice(settings, task, config_state.get("provider"))
    expected_provider = _hot_follow_expected_provider(
        task,
        requested_voice,
        config_state.get("provider") or task.get("dub_provider") or getattr(settings, "dub_provider", None),
    )
    actual_provider = normalize_provider(task.get("mm_audio_provider") or expected_provider)
    expected_resolved_voice, _ = resolve_tts_voice(
        settings=settings,
        provider=expected_provider,
        target_lang=target_lang,
        requested_voice=requested_voice,
    )
    resolved_voice = (
        str(task.get("mm_audio_voice_id") or "").strip()
        or str(config_state.get("resolved_voice") or "").strip()
        or _resolve_hot_follow_provider_voice(
            settings,
            actual_provider,
            requested_voice,
            task=task,
        )
    )
    audio_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    audio_exists = bool(audio_key and object_exists(str(audio_key)))
    dub_status = str(task.get("dub_status") or "").strip().lower()
    dub_running = dub_status in {"queued", "running", "processing"}
    dub_done = dub_status in {"ready", "done", "success", "completed"}
    no_dub_state = _hf_detect_no_dub_candidate(task_id, task)
    audio_ready_reason = "ready"
    if no_dub_state.get("no_dub"):
        audio_ready_reason = str(no_dub_state.get("no_dub_reason") or "no_dub_candidate")
    elif dub_running:
        audio_ready_reason = "dub_running"
    elif not audio_exists:
        audio_ready_reason = "audio_missing"
    elif not dub_done:
        audio_ready_reason = "dub_not_done"
    elif not expected_resolved_voice:
        audio_ready_reason = "voice_unresolved"
    elif not resolved_voice:
        audio_ready_reason = "resolved_voice_missing"
    elif normalize_provider(actual_provider) != normalize_provider(expected_provider):
        audio_ready_reason = "provider_mismatch"
    elif resolved_voice != expected_resolved_voice:
        audio_ready_reason = "voice_mismatch"
    elif config_state.get("request_token") and config_state.get("completed_token") != config_state.get("request_token"):
        audio_ready_reason = "dub_not_current"
    audio_ready = audio_ready_reason == "ready"
    return {
        "target_lang": target_lang,
        "voice_options_by_provider": voice_options_by_provider,
        "requested_voice": requested_voice,
        "actual_provider": actual_provider,
        "resolved_voice": resolved_voice,
        "expected_provider": expected_provider,
        "expected_resolved_voice": expected_resolved_voice,
        "audio_ready": audio_ready,
        "audio_ready_reason": audio_ready_reason,
        "no_dub": bool(no_dub_state.get("no_dub")),
        "no_dub_reason": no_dub_state.get("no_dub_reason"),
        "no_dub_message": no_dub_state.get("no_dub_message"),
    }


def _collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    voice_state = _collect_voice_execution_state(task, settings)
    task_id = str(task.get("task_id") or task.get("id") or "")
    channel_state = _hf_dual_channel_state(task_id, task) if task_id else {
        "speech_detected": False,
        "speech_confidence": "none",
        "onscreen_text_detected": False,
        "onscreen_text_density": "none",
        "content_mode": "silent_candidate",
    }
    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
    final_exists = bool(final_key and object_exists(str(final_key)))
    compose_status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip() or "never"
    actual_burn_subtitle_source = "mm.srt" if _task_key(task, "mm_srt_path") else None
    lipsync_enabled = os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in ("1", "true", "yes")
    lipsync_status = str(task.get("lipsync_status") or ("off" if not lipsync_enabled else "pending")).strip() or "off"
    compose_video_source = str(task.get("compose_video_source") or "basic").strip() or "basic"
    ocr_enabled = os.getenv("HF_OCR_ENABLED", "0").strip().lower() in ("1", "true", "yes")
    ocr_fallback_only = os.getenv("HF_OCR_FALLBACK_ONLY", "1").strip().lower() not in ("0", "false", "no")
    ocr_soft_fail = os.getenv("HF_OCR_SOFT_FAIL", "1").strip().lower() not in ("0", "false", "no")
    ocr_candidate = bool(ocr_enabled and channel_state.get("content_mode") == "subtitle_led_candidate")
    if not ocr_enabled:
        ocr_status = "off"
        ocr_warning = "OCR candidate path is disabled by default."
    elif ocr_candidate:
        ocr_status = "candidate"
        ocr_warning = "OCR candidate path is available as a fallback only. Current version does not auto-run OCR by default."
    else:
        ocr_status = "not_applicable"
        ocr_warning = None
    recommended_path = (
        "Voice dubbing"
        if channel_state.get("content_mode") == "voice_led"
        else ("OCR subtitle translation candidate" if channel_state.get("content_mode") == "subtitle_led_candidate" else "Manual text input required")
    )
    return {
        **voice_state,
        **channel_state,
        "compose_status": compose_status,
        "final_exists": final_exists,
        "actual_burn_subtitle_source": actual_burn_subtitle_source,
        "lipsync_enabled": lipsync_enabled,
        "lipsync_status": lipsync_status,
        "lipsync_warning": str(task.get("lipsync_warning") or "").strip() or None,
        "compose_video_source": compose_video_source,
        "ocr_enabled": ocr_enabled,
        "ocr_fallback_only": ocr_fallback_only,
        "ocr_soft_fail": ocr_soft_fail,
        "ocr_status": ocr_status,
        "ocr_candidate": ocr_candidate,
        "ocr_warning": ocr_warning,
        "recommended_path": recommended_path,
        "no_dub": voice_state.get("no_dub"),
        "no_dub_reason": voice_state.get("no_dub_reason"),
        "no_dub_message": voice_state.get("no_dub_message"),
    }


def _merge_probe_into_pipeline_config(
    pipeline_config: dict[str, str], probe: dict[str, Any] | None
) -> dict[str, str]:
    if not probe:
        return pipeline_config
    kind = probe.get("subtitle_track_kind")
    if isinstance(kind, str) and kind:
        pipeline_config["subtitle_track_kind"] = kind
    has_sub = probe.get("has_subtitle_stream")
    if has_sub is True:
        pipeline_config["subtitle_stream"] = "true"
    elif has_sub is False:
        pipeline_config["subtitle_stream"] = "false"
    subtitle_codecs = probe.get("subtitle_codecs") or []
    if isinstance(subtitle_codecs, list) and subtitle_codecs:
        pipeline_config["subtitle_codecs"] = ",".join(
            [str(v) for v in subtitle_codecs if str(v).strip()]
        )
    return pipeline_config


def _update_pipeline_probe(repo, task_id: str, probe: dict[str, Any] | None) -> None:
    if not probe:
        return
    task = repo.get(task_id)
    if not task:
        return
    current = parse_pipeline_config(task.get("pipeline_config"))
    updated = _merge_probe_into_pipeline_config(current, probe)
    if updated != current:
        _policy_upsert(repo, task_id, {"pipeline_config": pipeline_config_to_storage(updated)})


def _should_autostart(task: dict) -> bool:
    if not isinstance(task, dict):
        return False
    if task.get("status") in ("processing", "queued") and task.get("last_step"):
        return False
    if any(task.get(k) for k in ("subtitles_status", "dub_status", "pack_status")):
        return False
    return True


def _kickoff_autostart(
    *,
    task_id: str,
    start_step: str,
    reason: str,
    repo,
    background_tasks: BackgroundTasks,
) -> None:
    task = repo.get(task_id)
    if not task or not _should_autostart(task):
        return
    logger.info(
        "AUTO_START",
        extra={"task": task_id, "step": start_step, "phase": "enqueue", "reason": reason},
    )
    if start_step == "parse":
        background_tasks.add_task(_run_pipeline_background, task_id, repo)
        return
    if start_step in {"subtitles", "pipeline"}:
        background_tasks.add_task(auto_run_pipeline, task_id, repo)


def auto_run_pipeline(task_id: str, repo) -> None:
    logger.info("AUTO_PIPELINE_START", extra={"task_id": task_id})
    try:
        task = repo.get(task_id)
        if not task:
            logger.info("AUTO_PIPELINE_DONE", extra={"task_id": task_id, "reason": "missing_task"})
            return
        state_service = TaskStateService(repo=repo, step="router.tasks")

        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        default_lang = os.getenv("DEFAULT_MM_LANG", "my")
        target_lang = task.get("content_lang") or default_lang

        has_subs = bool(
            task.get("subtitles_status") == "ready"
            or task.get("origin_srt_path")
            or task.get("mm_srt_path")
        )
        if not has_subs:
            logger.info("AUTO_PIPELINE_STEP", extra={"task_id": task_id, "step": "subtitles"})
            _run_subtitles_job(
                task_id=task_id,
                target_lang=target_lang,
                force=False,
                translate=True,
                repo=repo,
            )
        else:
            logger.info("AUTO_PIPELINE_SKIP", extra={"task_id": task_id, "step": "subtitles"})

        task = repo.get(task_id) or task
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        no_dub = pipeline_config.get("no_dub") == "true"
        has_audio = bool(task.get("mm_audio_path") or task.get("mm_audio_key"))
        if not has_audio and not no_dub:
            logger.info("AUTO_PIPELINE_STEP", extra={"task_id": task_id, "step": "dub"})
            payload = DubProviderRequest()
            asyncio.run(_run_dub_job(task_id, payload, repo))
        else:
            logger.info("AUTO_PIPELINE_SKIP", extra={"task_id": task_id, "step": "dub"})

        task = repo.get(task_id) or task
        has_pack = bool(
            task.get("pack_status") == "ready"
            or task.get("pack_key")
            or task.get("pack_path")
        )
        if not has_pack:
            logger.info("AUTO_PIPELINE_STEP", extra={"task_id": task_id, "step": "pack"})
            state_service.update_fields(task_id, {"status": "processing", "last_step": "pack"})
            pack_req = PackRequest(task_id=task_id)
            pack_res = asyncio.run(run_pack_step_v1(pack_req))
            pack_key = None
            if isinstance(pack_res, dict):
                pack_key = pack_res.get("pack_key") or pack_res.get("zip_key")
            state_service.update_fields(
                task_id,
                {
                    "last_step": "pack",
                    "pack_key": pack_key,
                    "pack_type": "capcut_v18" if pack_key else None,
                    "pack_status": "ready" if pack_key else None,
                    "pack_error": None,
                    "status": "ready" if pack_key else "processing",
                },
            )
        else:
            logger.info("AUTO_PIPELINE_SKIP", extra={"task_id": task_id, "step": "pack"})
        logger.info("AUTO_PIPELINE_DONE", extra={"task_id": task_id})
    except Exception:
        logger.exception("AUTO_PIPELINE_FAIL", extra={"task_id": task_id})

def _run_pipeline_background(task_id: str, repo) -> None:
    task = repo.get(task_id)
    if not task:
        logger.error("Task %s not found in repository, abort pipeline", task_id)
        return

    status_update = {
        "status": "processing",
        "error_message": None,
        "error_reason": None,
    }

    default_lang = os.getenv("DEFAULT_MM_LANG", "my")
    default_voice = os.getenv("DEFAULT_MM_VOICE_ID", "mm_female_1")
    target_lang = task.get("content_lang") or default_lang
    voice_id = task.get("voice_id") or default_voice

    current_step = "parse"
    try:
        _repo_upsert(repo, task_id, {**status_update, "last_step": current_step})
        parse_req = ParseRequest(
            task_id=task_id,
            platform=task.get("platform"),
            link=task.get("source_url") or task.get("link") or "",
        )
        parse_res = asyncio.run(run_parse_step_v1(parse_req))
        raw_file = raw_path(task_id)
        raw_key = None
        if raw_file.exists():
            raw_key = upload_task_artifact(task, raw_file, "raw.mp4", task_id=task_id)
            try:
                probe = probe_subtitles(raw_file)
                _update_pipeline_probe(repo, task_id, probe)
            except Exception:
                logger.exception("SUBTITLE_PROBE_FAIL", extra={"task_id": task_id})
        duration_sec = parse_res.get("duration_sec") if isinstance(parse_res, dict) else None
        _repo_upsert(
            repo,
            task_id,
            {
                **status_update,
                "last_step": current_step,
                "raw_path": raw_key,
                "duration_sec": duration_sec,
            },
        )

        current_step = "subtitles"
        _repo_upsert(repo, task_id, {**status_update, "last_step": current_step})
        subs_req = SubtitlesRequest(
            task_id=task_id,
            target_lang=target_lang,
            force=False,
            translate=True,
            with_scenes=True,
        )
        asyncio.run(run_subtitles_step_v1(subs_req))
        workspace = Workspace(task_id)
        origin_key = (
            upload_task_artifact(task, workspace.origin_srt_path, "origin.srt", task_id=task_id)
            if workspace.origin_srt_path.exists()
            else None
        )
        mm_key = (
            upload_task_artifact(task, workspace.mm_srt_path, "mm.srt", task_id=task_id)
            if workspace.mm_srt_path.exists()
            else None
        )
        mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
        if mm_txt_path.exists():
            upload_task_artifact(task, mm_txt_path, "mm.txt", task_id=task_id)
        _repo_upsert(
            repo,
            task_id,
            {
                **status_update,
                "last_step": current_step,
                "origin_srt_path": origin_key,
                "mm_srt_path": mm_key,
            },
        )

        current_step = "dub"
        _repo_upsert(repo, task_id, {**status_update, "last_step": current_step})
        dub_req = DubRequest(
            task_id=task_id,
            voice_id=voice_id,
            force=False,
            target_lang=target_lang,
        )
        # Dubbing: force SSOT path (reads artifacts/subtitles.json)
        class TaskAdapter:
            def __init__(self, t: dict, voice_override: str | None, target_lang: str):
                self.task_id = t.get("task_id") or t.get("id")  # 蹇呴』鑳芥嬁鍒扮湡瀹?task_id
                self.id = self.task_id  # 鍏煎鏌愪簺 step 鍙 .id
                self.tenant_id = t.get("tenant_id") or t.get("tenant") or "default"
                self.project_id = t.get("project_id") or t.get("project") or "default"
                self.target_lang = target_lang
                self.voice_id = voice_override or t.get("voice_id")
                self.dub_provider = t.get("dub_provider") or "edge-tts"

        task_adapter = TaskAdapter(task, voice_override=voice_id, target_lang=target_lang)
        asyncio.run(run_dub_step_ssot(task_adapter))
        audio_key = None
        if workspace.mm_audio_exists():
            audio_path = workspace.mm_audio_path
            mp3_path = _ensure_mp3_audio(audio_path, workspace.mm_audio_mp3_path)
            try:
                local_size, local_duration = assert_local_audio_ok(mp3_path)
            except ValueError:
                raise HTTPException(status_code=500, detail="EMPTY_OR_INVALID_AUDIO")
            audio_key = deliver_key(task_id, "audio_mm.mp3")
            storage = get_storage_service()
            uploaded_key = storage.upload_file(
                str(mp3_path), audio_key, content_type="audio/mpeg"
            )
            if not uploaded_key:
                raise HTTPException(
                    status_code=500,
                    detail="Audio upload failed; no storage key returned",
                )
            logger.info(
                "DUB3_UPLOAD_DONE",
                extra={
                    "task_id": task_id,
                    "step": "dub",
                    "stage": "DUB3_UPLOAD_DONE",
                    "output_size": local_size,
                    "duration_sec": local_duration,
                    "uploaded_key": audio_key,
                },
            )
        _repo_upsert(
            repo,
            task_id,
            {
                **status_update,
                "last_step": current_step,
                "mm_audio_path": audio_key,
                "mm_audio_key": audio_key,
            },
        )

        current_step = "pack"
        state_service = TaskStateService(repo=repo, step="router.tasks")
        state_service.update_fields(task_id, {**status_update, "last_step": current_step})
        pack_req = PackRequest(task_id=task_id)
        pack_res = asyncio.run(run_pack_step_v1(pack_req))
        pack_key = None
        if isinstance(pack_res, dict):
            pack_key = pack_res.get("pack_key") or pack_res.get("zip_key")
        state_service.update_fields(
            task_id,
            {
                "status": "ready",
                "last_step": current_step,
                "pack_key": pack_key,
                "pack_type": "capcut_v18" if pack_key else None,
                "pack_status": "ready" if pack_key else None,
                "error_message": None,
                "error_reason": None,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Pipeline failed for task %s", task_id)
        _repo_upsert(
            repo,
            task_id,
            {
                "status": "failed",
                "last_step": current_step,
                "error_message": str(exc),
                "error_reason": "pipeline_failed",
            },
        )


@pages_router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_workbench_page(
    request: Request, task_id: str, repo=Depends(get_task_repository)
) -> HTMLResponse:
    """Render the per-task workbench page."""

    task = repo.get(task_id)
    if not task:
        resp = render_template(
            request=request,
            name="task_not_found.html",
            ctx={"task_id": task_id},
        )
        resp.status_code = 404
        return resp

    app_settings = get_settings()
    spec = resolve_workbench_spec(task)
    env_summary = {
        "workspace_root": app_settings.workspace_root,
        "douyin_api_base": getattr(app_settings, "douyin_api_base", ""),
        "whisper_model": getattr(app_settings, "whisper_model", ""),
        "gpt_model": getattr(app_settings, "gpt_model", ""),
        "asr_backend": getattr(app_settings, "asr_backend", None) or "whisper",
        "subtitles_backend": getattr(app_settings, "subtitles_backend", "gemini"),
        "gemini_model": getattr(app_settings, "gemini_model", ""),
    }
    try:
        from gateway.app.providers.registry import resolve_tool_providers

        env_summary["defaults"] = resolve_tool_providers().get("tools", {})
    except Exception:
        env_summary["defaults"] = {}

    paths = _resolve_download_urls(task)
    detail = _task_to_detail(task)
    task_json = {
        "task_id": detail.task_id,
        "status": detail.status,
        "platform": detail.platform,
        "category_key": detail.category_key,
        "content_lang": detail.content_lang,
        "ui_lang": detail.ui_lang,
        "source_url": detail.source_url,
        "pipeline_config": detail.pipeline_config,
        "no_dub": detail.no_dub,
        "dub_skip_reason": detail.dub_skip_reason,
        "raw_path": detail.raw_path,
        "origin_srt_path": detail.origin_srt_path,
        "mm_srt_path": detail.mm_srt_path,
        "mm_audio_path": detail.mm_audio_path,
        "mm_txt_path": paths.get("mm_txt_path"),
        "pack_path": detail.pack_path,
        "scenes_path": detail.scenes_path,
        "scenes_status": detail.scenes_status,
        "scenes_key": detail.scenes_key,
        "scenes_error": detail.scenes_error,
        "subtitles_status": detail.subtitles_status,
        "subtitles_key": detail.subtitles_key,
        "subtitles_error": detail.subtitles_error,
        "publish_status": detail.publish_status,
        "publish_provider": detail.publish_provider,
        "publish_key": detail.publish_key,
        "publish_url": detail.publish_url,
        "published_at": detail.published_at,
    }
    if spec.kind == "hot_follow":
        task_json.update(_collect_hot_follow_workbench_ui(task, app_settings))
    task_view = {"source_url_open": _extract_first_http_url(task.get("source_url"))}
    return render_template(
        request=request,
        name=spec.template,
        ctx={
            "task": detail,
            "task_json": task_json,
            "task_view": task_view,
            "env_summary": env_summary,
            "features": get_features(),
            "workbench_kind": spec.kind,
            "workbench_js": spec.js,
        },
    )


@pages_router.get("/tasks/{task_id}/publish", response_class=HTMLResponse)
async def task_publish_hub_page(
    request: Request, task_id: str, repo=Depends(get_task_repository)
) -> HTMLResponse:
    """Render the per-task publish hub page."""

    task = repo.get(task_id)
    if not task:
        resp = render_template(
            request=request,
            name="task_not_found.html",
            ctx={"task_id": task_id},
        )
        resp.status_code = 404
        return resp

    template_name = "task_publish_hub.html"
    if str(task.get("kind") or "").lower() == "hot_follow":
        template_name = "hot_follow_publish.html"

    detail = _task_to_detail(task)
    task_json = {"task_id": detail.task_id}
    return render_template(
        request=request,
        name=template_name,
        ctx={
            "task": detail,
            "task_json": task_json,
        },
    )


@pages_router.get("/op/dl/{task_id}")
def op_download_proxy(
    task_id: str,
    kind: str = Query(default=..., min_length=1),
    exp: int | None = Query(default=None),
    sig: str | None = Query(default=None),
    repo=Depends(get_task_repository),
):
    kind = (kind or "").strip().lower()
    kind_map = {
        "raw": "raw",
        "pack": "pack",
        "scenes": "scenes",
        "final_mp4": "final",
        "origin_srt": "origin",
        "mm_srt": "mm",
        "mm_txt": "mm_txt",
        "mm_audio": "audio",
        "publish_bundle": "publish_bundle",
    }
    if kind not in kind_map:
        raise HTTPException(status_code=400, detail="Unsupported kind")
    if _get_op_access_key():
        if exp is None or not sig:
            raise HTTPException(status_code=403, detail="Missing signature")
        now_ts = int(time.time())
        max_ttl = 7 * 24 * 3600
        if exp < now_ts or exp > now_ts + max_ttl:
            raise HTTPException(status_code=403, detail="Expired signature")
        if not _op_verify(task_id, kind, exp, sig):
            raise HTTPException(status_code=403, detail="Invalid signature")

    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    url = _task_endpoint(task_id, kind_map[kind])
    if not url:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    return RedirectResponse(url=url, status_code=302)


@pages_router.get("/d/{code}")
def resolve_download_code(code: str, repo=Depends(get_task_repository)):
    code = (code or "").strip().lower()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")

    items = sort_tasks_by_created(repo.list())
    for t in items[:200]:
        tid = str(t.get("task_id") or t.get("id") or "")
        if tid and tid.lower().startswith(code):
            signed = _signed_op_url(tid, "publish_bundle")
            return RedirectResponse(url=signed, status_code=302)

    raise HTTPException(status_code=404, detail="Code not found")


async def _probe_url_metadata(url: str, platform_hint: str | None = None) -> dict[str, Any]:
    url = _extract_first_http_url(url) or url
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    platform = (platform_hint or "").strip().lower() if platform_hint else "auto"
    if platform in ("", "auto"):
        platform = detect_platform(url) or "auto"

    try:
        meta = await parse_with_xiongmao(url)
    except XiongmaoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw = meta.get("raw") if isinstance(meta, dict) else None
    duration_sec = None
    if isinstance(raw, dict):
        for key in ("duration_sec", "duration", "durationSec"):
            if raw.get(key):
                try:
                    duration_sec = int(float(raw.get(key)))
                    break
                except Exception:
                    pass

    return {
        "platform": platform or meta.get("platform"),
        "url": url,
        "title": meta.get("title") if isinstance(meta, dict) else None,
        "cover": meta.get("cover") if isinstance(meta, dict) else None,
        "duration_sec": duration_sec,
        "source_id": raw.get("source_id") if isinstance(raw, dict) else None,
        "raw": raw,
        "raw_downloaded": False,
    }


@api_router.post("/tasks/probe")
async def probe_task(payload: ProbeTaskRequest):
    return await _probe_url_metadata(payload.url, payload.platform)


@api_router.post("/tasks", response_model=TaskDetail)
def create_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    """Create a Task record and kick off the V1 pipeline asynchronously."""

    source_text = payload.source_url.strip()
    platform = payload.platform or _infer_platform_from_url(source_text)
    task_id = uuid4().hex[:12]

    task_payload = {
        "task_id": task_id,
        "title": payload.title,
        "kind": payload.kind,
        "source_url": source_text,
        "platform": platform,
        "voice_id": payload.voice_id,
        "dub_provider": payload.dub_provider,
        "config": payload.config or {},
        "account_id": payload.account_id,
        "account_name": payload.account_name,
        "video_type": payload.video_type,
        "template": payload.template,
        "category_key": payload.category_key or "beauty",
        "content_lang": payload.content_lang or "my",
        "ui_lang": payload.ui_lang or "en",
        "style_preset": payload.style_preset,
        "face_swap_enabled": bool(payload.face_swap_enabled),
        "selected_tool_ids": _normalize_selected_tool_ids(payload.selected_tool_ids),
        "pipeline_config": pipeline_config_to_storage(payload.pipeline_config),
        "status": "pending",
        "last_step": None,
        "error_message": None,
    }
    task_payload = normalize_task_payload(task_payload, is_new=True)
    repo.create(task_payload)
    backend = os.getenv("TASK_REPO_BACKEND", "").lower() or "file"
    logger.info(
        "created task_id=%s tenant=%s backend=%s",
        task_id,
        task_payload.get("tenant", "default"),
        backend,
    )
    stored_task = repo.get(task_id)
    if not stored_task:
        raise HTTPException(
            status_code=500,
            detail=f"Task persistence failed for task_id={task_id}",
        )

    should_auto_start = bool(source_text) if payload.auto_start is None else bool(payload.auto_start)
    if source_text and should_auto_start:
        _kickoff_autostart(
            task_id=task_id,
            start_step="parse",
            reason="source_url",
            repo=repo,
            background_tasks=background_tasks,
        )

    return _task_to_detail(stored_task)


@api_router.post("/hot_follow/tasks", response_model=TaskDetail)
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
    return create_task(normalized, background_tasks=background_tasks, repo=repo)


def _save_upload_to_paths(
    *,
    upload: UploadFile,
    inputs_path: Path,
    raw_path_target: Path,
    max_bytes: int,
) -> int:
    inputs_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path_target.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with inputs_path.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                out.close()
                try:
                    inputs_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise HTTPException(status_code=413, detail="upload too large")
            out.write(chunk)
    if inputs_path != raw_path_target:
        shutil.copyfile(inputs_path, raw_path_target)
    return total


@api_router.post("/tasks/local_upload")
def create_task_local_upload(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    category: str | None = Form(default=None),
    language: str | None = Form(default=None),
    account: str | None = Form(default=None),
    platform: str | None = Form(default=None),
    account_id: str | None = Form(default=None),
    account_name: str | None = Form(default=None),
    video_type: str | None = Form(default=None),
    template: str | None = Form(default=None),
    title: str | None = Form(default=None),
    note: str | None = Form(default=None),
    style_preset: str | None = Form(default=None),
    subtitles_mode: str | None = Form(default=None),
    dub_mode: str | None = Form(default=None),
    repo=Depends(get_task_repository),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="file is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp4", ".mov", ".mkv"}:
        raise HTTPException(status_code=400, detail="unsupported file type")

    task_id = uuid4().hex[:12]
    max_mb = int(os.getenv("MAX_LOCAL_UPLOAD_MB", "200"))
    max_bytes = max_mb * 1024 * 1024

    raw_file_path = raw_path(task_id)
    _save_upload_to_paths(
        upload=file,
        inputs_path=raw_file_path,
        raw_path_target=raw_file_path,
        max_bytes=max_bytes,
    )
    probe = None
    try:
        probe = probe_subtitles(raw_file_path)
    except Exception:
        logger.exception("SUBTITLE_PROBE_FAIL", extra={"task_id": task_id})

    if account and not account_id:
        account_id = account
    if account and not account_name:
        account_name = account

    platform_value = platform or "local"
    pipeline_config = _merge_probe_into_pipeline_config(
        {
            "subtitles_mode": subtitles_mode or "whisper+gemini",
            "dub_mode": dub_mode or "auto-fallback",
            "ingest_mode": "local",
        },
        probe,
    )
    task_payload = {
        "task_id": task_id,
        "title": title,
        "source_url": None,
        "platform": platform_value,
        "account_id": account_id,
        "account_name": account_name,
        "video_type": video_type,
        "template": template,
        "category_key": category or "suitcase",
        "content_lang": language or "mm",
        "ui_lang": "zh",
        "style_preset": style_preset,
        "face_swap_enabled": False,
        "selected_tool_ids": None,
        "pipeline_config": pipeline_config_to_storage(pipeline_config),
        "status": "pending",
        "last_step": None,
        "error_message": None,
        "source_type": "local",
        "source_filename": file.filename,
        "note": note,
    }
    task_payload = normalize_task_payload(task_payload, is_new=True)
    repo.create(task_payload)
    stored_task = repo.get(task_id)
    if not stored_task:
        raise HTTPException(
            status_code=500,
            detail=f"Task persistence failed for task_id={task_id}",
        )
    if probe:
        _update_pipeline_probe(repo, task_id, probe)

    raw_key = upload_task_artifact(stored_task, raw_file_path, "raw.mp4", task_id=task_id)
    _policy_upsert(repo, 
        task_id,
        {
            "raw_path": raw_key,
            "error_message": None,
            "error_reason": None,
        },
    )

    if background_tasks is not None:
        _kickoff_autostart(
            task_id=task_id,
            start_step="pipeline",
            reason="local_upload",
            repo=repo,
            background_tasks=background_tasks,
        )

    return {"ok": True, "task_id": task_id, "redirect": f"/tasks/{task_id}"}


def _upload_task_bgm_impl(
    task_id: str,
    *,
    bgm_file: UploadFile,
    original_pct: int | None,
    bgm_pct: int | None,
    mix_ratio: float | None,
    strategy: str | None,
    repo,
) -> dict[str, Any]:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not bgm_file or not bgm_file.filename:
        raise HTTPException(status_code=400, detail="bgm_file is required")

    ext = Path(bgm_file.filename).suffix.lower()
    if ext not in {".mp3", ".wav"}:
        raise HTTPException(status_code=400, detail="unsupported file type")

    max_mb = int(os.getenv("MAX_BGM_UPLOAD_MB", "50"))
    max_bytes = max_mb * 1024 * 1024

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / f"user_bgm{ext}"
        _save_upload_to_paths(
            upload=bgm_file,
            inputs_path=tmp_path,
            raw_path_target=tmp_path,
            max_bytes=max_bytes,
        )
        artifact_name = f"bgm/user_bgm{ext}"
        bgm_key = upload_task_artifact(task, tmp_path, artifact_name, task_id=task_id)

    ratio = mix_ratio
    if ratio is None:
        if bgm_pct is not None and original_pct is not None:
            total = max(bgm_pct + original_pct, 0)
            ratio = (bgm_pct / total) if total > 0 else 0.5
        else:
            ratio = 0.8
    ratio = max(0.0, min(float(ratio), 1.0))

    config = dict(task.get("config") or {})
    config["bgm"] = {
        "strategy": strategy or "replace",
        "bgm_key": bgm_key,
        "mix_ratio": ratio,
    }
    _policy_upsert(repo, task_id, {"config": config})

    bgm_url = get_download_url(str(bgm_key)) if bgm_key else None
    return {
        "task_id": task_id,
        "bgm_key": bgm_key,
        "bgm_url": bgm_url,
        "mix_ratio": ratio,
        "strategy": config["bgm"]["strategy"],
    }

@api_router.post("/tasks/{task_id}/bgm")
def upload_task_bgm(
    task_id: str,
    bgm_file: UploadFile = File(...),
    original_pct: int | None = Form(default=None),
    bgm_pct: int | None = Form(default=None),
    mix_ratio: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    repo=Depends(get_task_repository),
):
    return _upload_task_bgm_impl(
        task_id,
        bgm_file=bgm_file,
        original_pct=original_pct,
        bgm_pct=bgm_pct,
        mix_ratio=mix_ratio,
        strategy=strategy,
        repo=repo,
    )


@api_router.post("/hot_follow/tasks/{task_id}/bgm")
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


@api_router.patch("/tasks/{task_id}", response_model=TaskDetail)
def update_task_selected_tools(
    task_id: str,
    payload: TaskUpdate,
    repo=Depends(get_task_repository),
):
    updates: dict[str, Any] = {}
    if payload.selected_tool_ids is not None:
        updates["selected_tool_ids"] = _normalize_selected_tool_ids(payload.selected_tool_ids)
    if payload.pipeline_config is not None:
        updates["pipeline_config"] = pipeline_config_to_storage(payload.pipeline_config)
    if not updates:
        raise HTTPException(status_code=400, detail="No updatable fields provided")

    _policy_upsert(repo, task_id, updates)
    updated = repo.get(task_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_detail(updated)


@api_router.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    account_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    kind: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500, alias="limit"),
    repo=Depends(get_task_repository),
):
    """List tasks with optional filtering by account or status."""

    filters = {}
    if account_id:
        filters["account_id"] = account_id
    if status:
        filters["status"] = status

    items = sort_tasks_by_created(repo.list(filters=filters))
    kind_norm = (kind or "").strip().lower()
    if kind_norm:
        if kind_norm == "apollo_avatar":
            items = [
                t
                for t in items
                if (str(t.get("platform") or "").lower() == "apollo_avatar")
                or (str(t.get("category_key") or "").lower() == "apollo_avatar")
            ]
        else:
            items = [
                t
                for t in items
                if str(t.get("category_key") or "").lower() == kind_norm
                or str(t.get("platform") or "").lower() == kind_norm
            ]
    total = len(items)
    items = items[(page - 1) * page_size : (page - 1) * page_size + page_size]

    summaries: list[TaskSummary] = []
    for t in items:
        download_paths = _resolve_download_urls(t)
        pack_path = download_paths.get("pack_path")
        scenes_path = download_paths.get("scenes_path")
        status = derive_status(t)
        summaries.append(
            TaskSummary(
                task_id=str(t.get("task_id") or t.get("id")),
                title=t.get("title"),
                kind=t.get("kind"),
                source_url=str(t.get("source_url")) if t.get("source_url") else None,
                source_link_url=_extract_first_http_url(t.get("source_url")),
                platform=t.get("platform"),
                account_id=t.get("account_id"),
                account_name=t.get("account_name"),
                video_type=t.get("video_type"),
                template=t.get("template"),
                category_key=t.get("category_key") or "beauty",
                content_lang=t.get("content_lang") or "my",
                ui_lang=t.get("ui_lang") or "en",
                style_preset=t.get("style_preset"),
                face_swap_enabled=bool(t.get("face_swap_enabled")),
                status=status,
                last_step=t.get("last_step"),
                duration_sec=t.get("duration_sec"),
                thumb_url=t.get("thumb_url"),
                cover_url=t.get("cover_url"),
                pack_path=pack_path,
                scenes_path=scenes_path,
                scenes_status=t.get("scenes_status"),
                scenes_key=t.get("scenes_key"),
                scenes_error=t.get("scenes_error"),
                subtitles_status=t.get("subtitles_status"),
                subtitles_key=t.get("subtitles_key"),
                subtitles_error=t.get("subtitles_error"),
                created_at=(coerce_datetime(t.get("created_at") or t.get("created") or t.get("createdAt")) or datetime(1970, 1, 1, tzinfo=timezone.utc)),
                updated_at=coerce_datetime(t.get("updated_at") or t.get("updatedAt")),
                error_message=t.get("error_message"),
                error_reason=t.get("error_reason"),
                parse_provider=t.get("parse_provider"),
                subtitles_provider=t.get("subtitles_provider"),
                dub_provider=t.get("dub_provider"),
                pack_provider=t.get("pack_provider"),
                face_swap_provider=t.get("face_swap_provider"),
                publish_status=t.get("publish_status"),
                publish_provider=t.get("publish_provider"),
                publish_key=t.get("publish_key"),
                publish_url=t.get("publish_url"),
                published_at=t.get("published_at"),
                priority=t.get("priority"),
                assignee=t.get("assignee"),
                ops_notes=t.get("ops_notes"),
                selected_tool_ids=_normalize_selected_tool_ids(t.get("selected_tool_ids")),
                pipeline_config=parse_pipeline_config(t.get("pipeline_config")),
            )
        )

    return TaskListResponse(items=summaries, page=page, page_size=page_size, total=total)


@api_router.get("/tasks/{task_id}/text", response_class=PlainTextResponse)
def get_task_text(
    task_id: str,
    kind: str = Query(default=..., pattern="^(origin_srt|mm_txt|mm_srt|mm_edited)$"),
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    if kind == "mm_edited":
        path = _mm_edited_path(task_id)
        if not path.exists():
            return PlainTextResponse(
                "",
                status_code=200,
                headers={"X-Text-Exists": "0"},
            )
        return PlainTextResponse(
            path.read_text(encoding="utf-8"),
            status_code=200,
            headers={"X-Text-Exists": "1"},
        )

    path = _resolve_text_path(task_id, kind)
    if not path:
        raise HTTPException(status_code=404, detail=f"{kind} not found")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="ignore")


@api_router.post("/tasks/{task_id}/mm_edited")
def save_mm_edited(task_id: str, payload: EditedTextRequest, repo=Depends(get_task_repository)):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is empty")
    path = _mm_edited_path(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text + "\n", encoding="utf-8")
        task = repo.get(task_id) if repo else None
        if task:
            workspace = Workspace(task_id)
            mm_txt_path = workspace.mm_txt_path
            mm_txt_path.parent.mkdir(parents=True, exist_ok=True)
            mm_txt_path.write_text(text + "\n", encoding="utf-8")
            mm_srt_key = _task_value(task, "mm_srt_path")
            artifact_name = "mm.txt"
            if isinstance(mm_srt_key, str):
                normalized_key = mm_srt_key.replace("\\", "/")
                if "subs/" in normalized_key:
                    artifact_name = "subs/mm.txt"
            mm_txt_key = upload_task_artifact(
                task,
                mm_txt_path,
                artifact_name,
                task_id=task_id,
            )
            if mm_txt_key and (
                (isinstance(task, dict) and "mm_txt_path" in task)
                or hasattr(task, "mm_txt_path")
            ):
                _policy_upsert(repo, task_id, {"mm_txt_path": mm_txt_key})
        return JSONResponse(
            {
                "ok": True,
                "task_id": task_id,
                "kind": "mm_edited",
                "bytes": len(text.encode("utf-8")),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"write mm_edited failed: {exc}") from exc




@api_router.get("/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: str, repo=Depends(get_task_repository)):
    """Retrieve a single task by id."""

    t = repo.get(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    detail = _task_to_detail(t)
    updated_at = getattr(detail, "updated_at", None)
    updated_ts = None
    if updated_at:
        try:
            updated_ts = (
                updated_at.replace(tzinfo=timezone.utc).timestamp()
                if updated_at.tzinfo is None
                else updated_at.timestamp()
            )
        except Exception:
            updated_ts = None
    now_ts = datetime.now(timezone.utc).timestamp()
    running = any(
        getattr(detail, key, None) == "running"
        for key in ("subtitles_status", "dub_status", "scenes_status", "pack_status")
    )
    stale_for = int(max(0, now_ts - updated_ts)) if updated_ts and running else 0
    stale = bool(running and updated_ts and stale_for > 1800)

    payload = detail.dict()
    for key in (
        "status",
        "last_step",
        "subtitles_status",
        "dub_status",
        "scenes_status",
        "pack_status",
        "subtitles_error",
        "dub_error",
        "scenes_error",
        "scenes_started_at",
        "scenes_finished_at",
        "scenes_elapsed_ms",
        "scenes_attempt",
        "scenes_run_id",
        "scenes_error_message",
        "pack_error",
        "raw_path",
        "origin_srt_path",
        "mm_srt_path",
        "mm_txt_path",
        "mm_audio_path",
        "pack_path",
        "scenes_path",
        "updated_at",
        "warnings",
        "warning_reasons",
    ):
        payload.setdefault(key, None)

    payload["stale"] = stale
    payload["stale_reason"] = "running_but_not_updated" if stale else None
    payload["stale_for_seconds"] = stale_for
    shape = _hf_task_status_shape(t)

    logger.info(
        "task_status_shape",
        extra={
            "task_id": task_id,
            "status": payload.get("status"),
            "last_step": payload.get("last_step"),
            "subtitles_status": payload.get("subtitles_status"),
            "dub_status": payload.get("dub_status"),
            "scenes_status": payload.get("scenes_status"),
            "pack_status": payload.get("pack_status"),
            "stale": payload.get("stale"),
            "step": shape.get("step"),
            "phase": shape.get("phase"),
            "provider": shape.get("provider"),
        },
    )

    return payload


@api_router.get("/tasks/{task_id}/events")
def get_task_events(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    kind = task.get("kind") if isinstance(task, dict) else getattr(task, "kind", None)
    return {"task_id": task_id, "kind": kind, "events": task.get("events") or []}


@api_router.get("/tasks/{task_id}/publish_hub")
def get_publish_hub(
    request: Request,
    task_id: str,
    repo=Depends(get_task_repository),
    op_key: str | None = Security(api_key_header),
):
    if not _op_key_valid_value(op_key):
        raise HTTPException(status_code=401, detail="OP key required")
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _publish_hub_payload(task)


@api_router.get("/hot_follow/tasks/{task_id}/publish_hub")
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


@api_router.get("/hot_follow/tasks/{task_id}/workbench_hub", response_model=None)
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
    compose_plan.setdefault("source_subtitle_cover_enabled", str(os.getenv("HF_SUBTITLE_COVER_ENABLED", "0")).strip().lower() in ("1", "true", "yes"))
    compose_plan.setdefault("source_subtitle_cover_mode", str(os.getenv("HF_SUBTITLE_COVER_MODE", "bottom_band")).strip() or "bottom_band")
    compose_plan["compose_policy"] = "freeze_tail" if bool(compose_plan.get("freeze_tail_enabled")) else "match_video"
    scene_outputs = task.get("scene_outputs")
    if not isinstance(scene_outputs, list):
        scene_outputs = []
    composed = _compute_composed_state(task, task_id)
    parse_state, parse_summary = _hf_pipeline_state(task, "parse")
    subtitles_state, subtitles_summary = _hf_pipeline_state(task, "subtitles")
    dub_state, dub_summary = _hf_pipeline_state(task, "audio")
    pack_state, pack_summary = _hf_pipeline_state(task, "pack")
    compose_state, compose_summary = _hf_pipeline_state(task, "compose")

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
    dub_input_text = _hf_dub_input_text(task_id, task)
    audio_cfg = _hf_audio_config(task)
    voice_state = _collect_voice_execution_state(task, get_settings())
    target_lang_internal = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    text_guard = clean_and_analyze_dub_text(subtitles_text or "", target_lang_internal)
    audio_warning = str(text_guard.get("warning") or "").strip() or None
    if not (audio_cfg.get("voiceover_url") or "").strip() and (task.get("mm_audio_key") or task.get("mm_audio_path")):
        dub_state = "failed"
        if not dub_summary:
            dub_summary = "voiceover artifact invalid"
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
        {"key": "dub", "label": "Dub", "status": dub_state, "updated_at": task.get("updated_at"), "error": task.get("dub_error"), "message": dub_summary},
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
            "raw_source_text": origin_text or "",
            "normalized_source_text": normalized_source_text or origin_text or "",
            "edited_text": subtitles_text or "",
            "srt_text": subtitles_text or "",
            "dub_input_text": dub_input_text or "",
            "actual_burn_subtitle_source": "mm.srt" if _task_key(task, "mm_srt_path") else None,
            "status": subtitles_state,
            "error": task.get("subtitles_error"),
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
            "error": task.get("dub_error"),
            "warning": audio_warning,
            "sha256": task.get("audio_sha256"),
            "audio_ready": bool(voice_state.get("audio_ready")),
            "audio_ready_reason": voice_state.get("audio_ready_reason"),
            "requested_voice": voice_state.get("requested_voice"),
            "actual_provider": voice_state.get("actual_provider"),
            "resolved_voice": voice_state.get("resolved_voice"),
            "dub_input_text": dub_input_text or "",
            "no_dub": bool(no_dub_state.get("no_dub")),
            "no_dub_reason": no_dub_state.get("no_dub_reason"),
            "no_dub_message": no_dub_state.get("no_dub_message"),
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
    final_url = _resolve_hub_final_url(task_id, payload)
    if final_url:
        payload["media"]["final_url"] = final_url
        payload["media"]["final_video_url"] = final_url
    payload["final_url"] = final_url
    payload["final_video_url"] = final_url
    final_exists = bool((payload.get("final") or {}).get("exists"))
    composed_ready = bool(composed_ready)
    payload["composed_ready"] = composed_ready
    payload["composed_reason"] = "ready" if composed_ready else "not_ready"
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
        latest = repo.get(task_id) or task
        payload = compute_hot_follow_state(latest, payload)
        task = latest

    # UI consistency guard: once final is ready, compose-facing fields must all read done.
    final_url = str(
        payload.get("final_url")
        or (payload.get("media", {}) or {}).get("final_url")
        or ""
    ).strip()
    final_exists = bool((payload.get("final") or {}).get("exists"))
    composed_ready = bool((payload.get("ready_gate") or {}).get("compose_ready"))
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
                    if final_url:
                        item["url"] = final_url
                    break

        media = payload.get("media")
        if isinstance(media, dict) and final_url:
            media["final_url"] = final_url
            media["final_video_url"] = final_url

        payload["composed_ready"] = True
        payload["composed_reason"] = "ready"
    else:
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

        compose = payload.get("compose")
        if isinstance(compose, dict):
            last = compose.get("last")
            if isinstance(last, dict):
                last["status"] = "pending"

        deliverables = payload.get("deliverables")
        if isinstance(deliverables, list):
            for item in deliverables:
                if not isinstance(item, dict):
                    continue
                if str(item.get("kind") or "").strip().lower() == "final":
                    item["status"] = "pending"
                    item["state"] = "pending"
                    break
    payload.update(_collect_hot_follow_workbench_ui(task, get_settings()))
    return payload


@api_router.patch("/hot_follow/tasks/{task_id}/audio_config")
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


@api_router.patch("/hot_follow/tasks/{task_id}/compose_plan")
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
    if "source_subtitle_cover_enabled" not in plan:
        plan["source_subtitle_cover_enabled"] = str(os.getenv("HF_SUBTITLE_COVER_ENABLED", "0")).strip().lower() in {"1", "true", "yes"}
    if "source_subtitle_cover_mode" not in plan:
        plan["source_subtitle_cover_mode"] = str(os.getenv("HF_SUBTITLE_COVER_MODE", "bottom_band")).strip() or "bottom_band"
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
    if payload.source_subtitle_cover_enabled is not None:
        plan["source_subtitle_cover_enabled"] = bool(payload.source_subtitle_cover_enabled)
    if payload.source_subtitle_cover_mode is not None and str(payload.source_subtitle_cover_mode).strip():
        plan["source_subtitle_cover_mode"] = str(payload.source_subtitle_cover_mode).strip().lower()
    plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
    _policy_upsert(repo, task_id, {"compose_plan": plan})
    return {"task_id": task_id, "compose_plan": plan}


@api_router.patch("/hot_follow/tasks/{task_id}/subtitles")
def patch_hot_follow_subtitles(
    task_id: str,
    payload: HotFollowSubtitlesRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text = (payload.srt_text or "").strip()
    override_path = _hf_subtitles_override_path(task_id)
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(text + ("\n" if text else ""), encoding="utf-8")
    _policy_upsert(
        repo,
        task_id,
        {
            "subtitles_status": "ready" if text else task.get("subtitles_status"),
            "last_step": "subtitles" if text else task.get("last_step"),
            "subtitles_override_updated_at": datetime.now(timezone.utc).isoformat(),
            "error_message": None,
            "error_reason": None,
        },
    )
    return {
        "task_id": task_id,
        "subtitles": {
            "srt_text": _hf_load_subtitles_text(task_id, repo.get(task_id) or task),
            "origin_text": _hf_load_origin_subtitles_text(repo.get(task_id) or task),
            "raw_source_text": _hf_load_origin_subtitles_text(repo.get(task_id) or task),
            "normalized_source_text": _hf_load_normalized_source_text(task_id, repo.get(task_id) or task),
            "edited_text": _hf_load_subtitles_text(task_id, repo.get(task_id) or task),
            "dub_input_text": _hf_dub_input_text(task_id, repo.get(task_id) or task),
            "editable": True,
        },
    }


def _hf_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    def _compose_fail(reason: str, message: str, status_code: int = 409, *, ffmpeg_cmd: str | None = None, stderr_tail: str | None = None):
        detail: dict[str, Any] = {"reason": reason, "message": message}
        if ffmpeg_cmd:
            detail["ffmpeg_cmd"] = ffmpeg_cmd
        if stderr_tail:
            detail["stderr_tail"] = stderr_tail
        raise HTTPException(status_code=status_code, detail=detail)

    def _normalize_target_lang(value: str | None) -> str:
        v = str(value or "").strip().lower()
        if not v:
            return "mm"
        return "mm" if v == "my" else v

    def _resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
        lang_norm = _normalize_target_lang(lang)
        candidates: list[str] = []
        if lang_norm == "mm":
            mm_path = _task_key(task_obj, "mm_srt_path")
            if mm_path:
                candidates.append(str(mm_path))
            candidates.append(deliver_key(task_code, "mm.srt"))
        else:
            lang_path = _task_key(task_obj, f"{lang_norm}_srt_path")
            if lang_path:
                candidates.append(str(lang_path))
            candidates.append(deliver_key(task_code, f"{lang_norm}.srt"))
            mm_path = _task_key(task_obj, "mm_srt_path")
            if mm_path:
                candidates.append(str(mm_path))
            candidates.append(deliver_key(task_code, "mm.srt"))
        for key in candidates:
            if key and object_exists(str(key)):
                return str(key)
        return None

    def _escape_subtitles_path(path: Path) -> str:
        # ffmpeg subtitles filter expects escaped path in filter expression
        raw = str(path).replace("\\", "/")
        return raw.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    def _bgm_filter_expr() -> str:
        base = f"[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={bgm_mix}"
        if compose_policy == "match_video":
            base += f",atrim=0:{video_duration:.3f}"
        return base + "[bgm];"

    def _assert_overlay_cmd(cmd_text: str):
        if overlay_subtitles and "subtitles=" not in cmd_text:
            _compose_fail("compose_failed", "overlay_subtitles enabled but ffmpeg cmd missing subtitles filter", ffmpeg_cmd=cmd_text)

    storage = get_storage_service()
    voice_state = _collect_voice_execution_state(task, get_settings())
    video_key = (
        _task_key(task, "mute_video_key")
        or _task_key(task, "mute_video_path")
        or _task_key(task, "raw_path")
    )
    audio_key = _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    if not video_key:
        _compose_fail("missing_raw", "missing video source for compose")
    if not audio_key:
        _compose_fail("missing_voiceover", "missing voiceover audio for compose")
    if not bool(voice_state.get("audio_ready")):
        _compose_fail(
            "missing_voiceover",
            f"voiceover audio not ready: {voice_state.get('audio_ready_reason') or 'audio_not_ready'}",
        )
    try:
        assert_artifact_ready(
            kind="video",
            key=str(video_key),
            exists_fn=object_exists,
            head_fn=object_head,
        )
    except Exception:
        _compose_fail("missing_raw", "video source not ready")
    try:
        assert_artifact_ready(
            kind="audio",
            key=str(audio_key),
            exists_fn=object_exists,
            head_fn=object_head,
        )
    except Exception:
        _compose_fail("missing_voiceover", "voiceover audio invalid")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        _compose_fail("compose_failed", "ffmpeg not found in PATH")

    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    bgm_key = str(bgm.get("bgm_key") or "").strip() or None
    if bgm_key and not object_exists(bgm_key):
        bgm_key = None
    if bgm_key:
        try:
            assert_artifact_ready(
                kind="audio",
                key=bgm_key,
                exists_fn=object_exists,
                head_fn=object_head,
            )
        except Exception:
            bgm_key = None
    try:
        bgm_mix = float(bgm.get("mix_ratio") if bgm.get("mix_ratio") is not None else 0.3)
    except Exception:
        bgm_mix = 0.3
    bgm_mix = max(0.0, min(1.0, bgm_mix))
    compose_plan = dict(task.get("compose_plan") or {})
    overlay_subtitles = bool(compose_plan.get("overlay_subtitles"))
    strip_subtitle_streams = bool(compose_plan.get("strip_subtitle_streams", True))
    target_lang = str(compose_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang") or "mm")
    freeze_tail_enabled = bool(compose_plan.get("freeze_tail_enabled", False))
    try:
        freeze_tail_cap_sec = max(1.0, min(30.0, float(compose_plan.get("freeze_tail_cap_sec") or 8.0)))
    except Exception:
        freeze_tail_cap_sec = 8.0
    compose_policy = "freeze_tail" if freeze_tail_enabled else "match_video"
    compose_warning = None
    source_subtitle_cover_filter = _hf_source_subtitle_cover_filter(compose_plan, config)
    logger.info(
        "COMPOSE_START",
        extra={
            "task_id": task_id,
            "raw_key": str(video_key),
            "audio_key": str(audio_key),
            "bgm_key": str(bgm_key) if bgm_key else None,
            "mix": bgm_mix,
            "overlay_subtitles": overlay_subtitles,
            "strip_subtitle_streams": strip_subtitle_streams,
            "target_lang": target_lang,
            "freeze_tail_enabled": freeze_tail_enabled,
            "freeze_tail_cap_sec": freeze_tail_cap_sec,
            "compose_policy": compose_policy,
            "source_subtitle_cover_enabled": bool(source_subtitle_cover_filter),
            "source_subtitle_cover_mode": compose_plan.get("source_subtitle_cover_mode"),
        },
    )

    compose_started_at = task.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat()
    ffmpeg_cmd_used = None
    bundled_fonts_dir = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    bundled_myanmar_ttf = bundled_fonts_dir / "NotoSansMyanmar-Regular.ttf"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / "video_input.mp4"
        voice_path = tmp / "voice_input.mp3"
        final_path = tmp / "final_compose.mp4"
        subtitle_path = tmp / "subs_target.srt"
        storage.download_file(str(video_key), str(video_path))
        storage.download_file(str(audio_key), str(voice_path))
        video_size, video_duration = assert_local_video_ok(video_path)
        try:
            _, voice_duration = assert_local_audio_ok(voice_path)
        except ValueError:
            _compose_fail("missing_voiceover", "voiceover audio invalid")

        video_input_path = video_path
        hold_sec = 0.0
        if freeze_tail_enabled and voice_duration > video_duration:
            required_hold = max(0.0, voice_duration - video_duration)
            if required_hold <= freeze_tail_cap_sec:
                hold_sec = required_hold
            else:
                compose_policy = "match_video"
                compose_warning = (
                    f"freeze tail required {required_hold:.2f}s > cap {freeze_tail_cap_sec:.2f}s; fallback to match_video"
                )
        else:
            compose_policy = "match_video" if not freeze_tail_enabled else compose_policy

        if hold_sec > 0:
            freeze_video_path = tmp / "video_input_freeze_tail.mp4"
            freeze_cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"tpad=stop_mode=clone:stop_duration={hold_sec:.3f}",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-pix_fmt",
                "yuv420p",
                str(freeze_video_path),
            ]
            freeze_proc = subprocess.run(freeze_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if freeze_proc.returncode == 0 and freeze_video_path.exists() and freeze_video_path.stat().st_size > 0:
                video_input_path = freeze_video_path
                compose_policy = "freeze_tail"
            else:
                compose_policy = "match_video"
                compose_warning = "freeze tail render failed; fallback to match_video"

        if overlay_subtitles:
            if not bundled_myanmar_ttf.exists() or bundled_myanmar_ttf.stat().st_size == 0:
                _compose_fail("font_missing", f"bundled Myanmar font missing: {bundled_myanmar_ttf}")
            subtitle_key = _resolve_target_srt_key(task, task_id, target_lang)
            if not subtitle_key:
                _compose_fail("subtitles_missing", "overlay_subtitles enabled but target subtitle key is missing")
            storage.download_file(str(subtitle_key), str(subtitle_path))
            if not subtitle_path.exists() or subtitle_path.stat().st_size == 0:
                _compose_fail("subtitles_missing", "overlay_subtitles enabled but subtitle file is empty")

        bgm_path = None
        if bgm_key:
            bgm_path = tmp / "bgm_input.mp3"
            storage.download_file(str(bgm_key), str(bgm_path))

        if bgm_path and bgm_path.exists():
            if overlay_subtitles:
                fontsdir = bundled_fonts_dir
                video_subtitle_input = "[base]" if source_subtitle_cover_filter else "[0:v]"
                subtitle_filter = (
                    f"subtitles='{_escape_subtitles_path(subtitle_path)}':"
                    "charenc=UTF-8:"
                    f"fontsdir='{_escape_subtitles_path(Path(fontsdir))}':"
                    "force_style='FontName=Noto Sans Myanmar,FontSize=18,Outline=2,Shadow=1,MarginV=40'"
                )
                filter_complex = (
                    (f"[0:v]{source_subtitle_cover_filter}[base];" if source_subtitle_cover_filter else "")
                    + f"{video_subtitle_input}{subtitle_filter}[v];"
                    + (
                        f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
                        + (
                            f",atrim=0:{video_duration:.3f},afade=t=out:st={max(video_duration-0.35,0.0):.3f}:d=0.35"
                            if compose_policy == "match_video" and voice_duration > video_duration
                            else ""
                        )
                        + "[voice];"
                    )
                    + _bgm_filter_expr()
                    +
                    "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
                )
                map_video = "[v]"
                video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
            else:
                filter_complex = (
                    (
                        "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
                        + (
                            f",atrim=0:{video_duration:.3f},afade=t=out:st={max(video_duration-0.35,0.0):.3f}:d=0.35"
                            if compose_policy == "match_video" and voice_duration > video_duration
                            else ""
                        )
                        + "[voice];"
                    )
                    + _bgm_filter_expr()
                    +
                    "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2,alimiter=limit=0.95[mix]"
                )
                map_video = "0:v:0"
                video_codec_args = ["-c:v", "copy"]
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(video_input_path),
                "-i",
                str(voice_path),
                "-i",
                str(bgm_path),
                "-filter_complex",
                filter_complex,
                "-map",
                map_video,
                "-map",
                "[mix]",
                *video_codec_args,
                "-c:a",
                "aac",
                "-shortest",
                "-movflags",
                "+faststart",
                *(["-sn"] if strip_subtitle_streams else []),
                str(final_path),
            ]
            logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", task_id, " ".join(cmd))
            ffmpeg_cmd_used = " ".join(cmd)
            _assert_overlay_cmd(ffmpeg_cmd_used)
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                _compose_fail("compose_failed", "compose ffmpeg failed", ffmpeg_cmd=ffmpeg_cmd_used, stderr_tail=(proc.stderr or "")[-800:])
        else:
            if overlay_subtitles:
                fontsdir = bundled_fonts_dir
                video_subtitle_input = "[base]" if source_subtitle_cover_filter else "[0:v]"
                subtitle_filter = (
                    f"subtitles='{_escape_subtitles_path(subtitle_path)}':"
                    "charenc=UTF-8:"
                    f"fontsdir='{_escape_subtitles_path(Path(fontsdir))}':"
                    "force_style='FontName=Noto Sans Myanmar,FontSize=18,Outline=2,Shadow=1,MarginV=40'"
                )
                filter_complex = (
                    (f"[0:v]{source_subtitle_cover_filter}[base];" if source_subtitle_cover_filter else "")
                    + f"{video_subtitle_input}{subtitle_filter}[v];"
                    + (
                        "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
                        + (
                            f",atrim=0:{video_duration:.3f},afade=t=out:st={max(video_duration-0.35,0.0):.3f}:d=0.35"
                            if compose_policy == "match_video" and voice_duration > video_duration
                            else ""
                        )
                        + ",alimiter=limit=0.95[mix]"
                    )
                )
                map_video = "[v]"
                video_codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
            else:
                filter_complex = (
                    "[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.0"
                    + (
                        f",atrim=0:{video_duration:.3f},afade=t=out:st={max(video_duration-0.35,0.0):.3f}:d=0.35"
                        if compose_policy == "match_video" and voice_duration > video_duration
                        else ""
                    )
                    + ",alimiter=limit=0.95[mix]"
                )
                map_video = "0:v:0"
                video_codec_args = ["-c:v", "copy"]
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(video_input_path),
                "-i",
                str(voice_path),
                "-filter_complex",
                filter_complex,
                "-map",
                map_video,
                "-map",
                "[mix]",
                *video_codec_args,
                "-c:a",
                "aac",
                "-shortest",
                "-movflags",
                "+faststart",
                *(["-sn"] if strip_subtitle_streams else []),
                str(final_path),
            ]
            logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", task_id, " ".join(cmd))
            ffmpeg_cmd_used = " ".join(cmd)
            _assert_overlay_cmd(ffmpeg_cmd_used)
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                cmd_fallback = [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_input_path),
                    "-i",
                    str(voice_path),
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    map_video,
                    "-map",
                    "[mix]",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-shortest",
                    "-movflags",
                    "+faststart",
                    *(["-sn"] if strip_subtitle_streams else []),
                    str(final_path),
                ]
                logger.info("COMPOSE_FFMPEG_CMD task=%s cmd=%s", task_id, " ".join(cmd_fallback))
                ffmpeg_cmd_used = " ".join(cmd_fallback)
                _assert_overlay_cmd(ffmpeg_cmd_used)
                proc2 = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc2.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                    _compose_fail("compose_failed", "compose ffmpeg failed", ffmpeg_cmd=ffmpeg_cmd_used, stderr_tail=(proc2.stderr or "")[-800:])

        try:
            final_size, final_duration = assert_local_video_ok(final_path)
        except ValueError:
            _compose_fail("compose_failed", "compose output invalid")

        ffprobe = shutil.which("ffprobe")
        if ffprobe:
            probe_cmd = [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(final_path),
            ]
            probe = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if probe.returncode == 0:
                try:
                    final_duration = float((probe.stdout or "").strip() or final_duration)
                except Exception:
                    pass

        if compose_policy == "match_video" and abs(float(final_duration) - float(video_duration)) > 1.0:
            logger.warning(
                "COMPOSE_DURATION_MISMATCH",
                extra={
                    "task_id": task_id,
                    "source_duration": video_duration,
                    "final_duration": final_duration,
                },
            )
            clamp_path = tmp / "final_compose_clamped.mp4"
            clamp_cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(final_path),
                "-t",
                f"{video_duration:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                str(clamp_path),
            ]
            clamp_proc = subprocess.run(clamp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if clamp_proc.returncode == 0 and clamp_path.exists() and clamp_path.stat().st_size > 0:
                final_path = clamp_path
                final_size, final_duration = assert_local_video_ok(final_path)
                compose_warning = "Duration mismatch detected; output was clamped to source duration."
        logger.info(
            "COMPOSE_OUTPUT_READY",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "output_path": str(final_path),
            },
        )

        final_key = deliver_key(task_id, "final.mp4")
        logger.info(
            "COMPOSE_UPLOAD_START",
            extra={
                "task_id": task_id,
                "final_key": final_key,
                "content_type": "video/mp4",
            },
        )
        uploaded_key = storage.upload_file(str(final_path), final_key, content_type="video/mp4")
        if not uploaded_key:
            _compose_fail("compose_failed", "compose upload failed")
        if not object_exists(final_key):
            _compose_fail("compose_failed", "compose upload verify failed: missing final object")
        uploaded_meta = object_head(final_key)
        uploaded_size, _ = media_meta_from_head(uploaded_meta)
        final_etag = uploaded_meta.get("etag") if isinstance(uploaded_meta, dict) else None
        if uploaded_size < MIN_VIDEO_BYTES:
            _compose_fail("compose_failed", "compose upload verify failed: invalid final object")
        logger.info(
            "COMPOSE_DONE",
            extra={
                "task_id": task_id,
                "output_size": final_size,
                "duration_sec": final_duration,
                "uploaded_key": final_key,
                "uploaded_size": uploaded_size,
            },
        )
        return {
            "final_video_key": final_key,
            "final_video_path": final_key,
            "final_video_sha256": _sha256_file(final_path),
            "final_asset_version": str(final_etag or _sha256_file(final_path) or datetime.now(timezone.utc).isoformat()),
            "final_updated_at": datetime.now(timezone.utc).isoformat(),
            "final_mime": "video/mp4",
            "final_duration_ms": int(final_duration * 1000),
            "final_video_bytes": int(uploaded_size),
            "compose_provider": "ffmpeg",
            "compose_version": int(task.get("compose_version") or 0) + 1,
            "compose_status": "done",
            "compose_error": None,
            "compose_error_reason": None,
            "compose_last_status": "done",
            "compose_last_started_at": compose_started_at,
            "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
            "compose_last_ffmpeg_cmd": ffmpeg_cmd_used,
            "compose_last_error": None,
            "compose_policy": compose_policy,
            "freeze_tail_enabled": bool(compose_policy == "freeze_tail"),
            "freeze_tail_cap_sec": int(freeze_tail_cap_sec),
            "compose_warning": compose_warning,
            "last_step": "compose",
            "status": "ready",
            "error_message": None,
            "error_reason": None,
        }


@api_router.post("/hot_follow/tasks/{task_id}/compose")
def compose_hot_follow_final_video(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    lock = _task_compose_lock(task_id)
    if not lock.acquire(blocking=False):
        current = repo.get(task_id) or task
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "running",
                "compose_last_status": "running",
                "compose_last_started_at": current.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat(),
                "compose_last_finished_at": None,
            },
        )
        return _compose_in_progress_response(task_id)
    current_for_plan = repo.get(task_id) or task
    current_plan = dict(current_for_plan.get("compose_plan") or {})
    compose_plan = {
        "mute": bool(current_plan.get("mute", True)),
        "overlay_subtitles": bool(current_plan.get("overlay_subtitles", True)),
        "strip_subtitle_streams": bool(current_plan.get("strip_subtitle_streams", True)),
        "cleanup_mode": str(current_plan.get("cleanup_mode") or "none"),
        "target_lang": str(current_plan.get("target_lang") or current_for_plan.get("target_lang") or current_for_plan.get("content_lang") or "mm"),
        "freeze_tail_enabled": bool(current_plan.get("freeze_tail_enabled", False)),
        "freeze_tail_cap_sec": int(current_plan.get("freeze_tail_cap_sec") or 8),
        "compose_policy": "freeze_tail" if bool(current_plan.get("freeze_tail_enabled", False)) else "match_video",
    }
    try:
        _policy_upsert(
            repo,
            task_id,
            {
                "status": "processing",
                "last_step": "compose",
                "compose_status": "running",
                "compose_error": None,
                "compose_error_reason": None,
                "compose_last_status": "running",
                "compose_last_started_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_finished_at": None,
                "compose_last_error": None,
                "compose_warning": None,
                "compose_plan": compose_plan,
                "scene_outputs": current_for_plan.get("scene_outputs") or [],
            },
        )
        lipsync_state = _run_hot_follow_lipsync_stub(
            task_id,
            os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in ("1", "true", "yes"),
        )
        _policy_upsert(
            repo,
            task_id,
            {
                "lipsync_status": lipsync_state.get("status"),
                "lipsync_warning": lipsync_state.get("warning"),
                "compose_video_source": lipsync_state.get("compose_video_source") or "basic",
            },
        )
        if lipsync_state.get("warning"):
            _policy_upsert(repo, task_id, {"compose_warning": lipsync_state.get("warning")})
        updates = _hf_compose_final_video(task_id, repo.get(task_id) or task)
        updates["lipsync_status"] = lipsync_state.get("status")
        updates["lipsync_warning"] = lipsync_state.get("warning")
        updates["compose_video_source"] = lipsync_state.get("compose_video_source") or "basic"
        if lipsync_state.get("warning"):
            current_warning = str(updates.get("compose_warning") or "").strip()
            updates["compose_warning"] = f"{current_warning} {lipsync_state.get('warning')}".strip() if current_warning else lipsync_state.get("warning")
        _policy_upsert(repo, task_id, updates)
        latest = repo.get(task_id) or task
        return {
            "ok": True,
            "task_id": task_id,
            "final_url": _task_endpoint(task_id, "final"),
            "final_video_url": _task_endpoint(task_id, "final"),
            "hub": get_hot_follow_workbench_hub(task_id, repo=repo),
            "compose_status": latest.get("compose_status"),
        }
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"reason": "compose_failed", "message": str(exc.detail)}
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "failed",
                "compose_error": detail,
                "compose_error_reason": detail.get("reason"),
                "compose_last_status": "failed",
                "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_error": detail.get("message") or str(exc.detail),
                "status": "failed",
                "last_step": "compose",
                "final_video_key": None,
                "final_video_path": None,
            },
        )
        raise
    except Exception as exc:
        detail = {"reason": "compose_failed", "message": str(exc)}
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "failed",
                "compose_error": detail,
                "compose_error_reason": detail.get("reason"),
                "compose_last_status": "failed",
                "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_error": detail.get("message"),
                "status": "failed",
                "last_step": "compose",
                "final_video_key": None,
                "final_video_path": None,
            },
        )
        raise HTTPException(status_code=409, detail=detail) from exc
    finally:
        lock.release()


@api_router.post("/tasks/{task_id}/compose")
def compose_task(
    task_id: str,
    payload: ComposeTaskRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    req = payload or ComposeTaskRequest()
    lock = _task_compose_lock(task_id)
    if not lock.acquire(blocking=False):
        current = repo.get(task_id) or task
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "running",
                "compose_last_status": "running",
                "compose_last_started_at": current.get("compose_last_started_at") or datetime.now(timezone.utc).isoformat(),
                "compose_last_finished_at": None,
            },
        )
        return _compose_in_progress_response(task_id)
    if req.bgm_mix is not None:
        mix = max(0.0, min(1.0, float(req.bgm_mix)))
        config = dict(task.get("config") or {})
        bgm = dict(config.get("bgm") or {})
        bgm["mix_ratio"] = mix
        config["bgm"] = bgm
        _policy_upsert(repo, task_id, {"config": config})
        task = repo.get(task_id) or task
    if req.overlay_subtitles is not None:
        plan = dict(task.get("compose_plan") or {})
        if "target_lang" not in plan:
            plan["target_lang"] = task.get("target_lang") or task.get("content_lang") or "mm"
        plan["overlay_subtitles"] = bool(req.overlay_subtitles)
        if "freeze_tail_enabled" not in plan:
            plan["freeze_tail_enabled"] = False
        if "freeze_tail_cap_sec" not in plan:
            plan["freeze_tail_cap_sec"] = 8
        plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
        _policy_upsert(repo, task_id, {"compose_plan": plan})
        task = repo.get(task_id) or task
    if req.freeze_tail_enabled is not None:
        plan = dict(task.get("compose_plan") or {})
        if "target_lang" not in plan:
            plan["target_lang"] = task.get("target_lang") or task.get("content_lang") or "mm"
        plan["freeze_tail_enabled"] = bool(req.freeze_tail_enabled)
        if "freeze_tail_cap_sec" not in plan:
            plan["freeze_tail_cap_sec"] = 8
        plan["compose_policy"] = "freeze_tail" if bool(plan.get("freeze_tail_enabled")) else "match_video"
        _policy_upsert(repo, task_id, {"compose_plan": plan})
        task = repo.get(task_id) or task

    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path") or deliver_key(task_id, "final.mp4")
    final_meta = object_head(str(final_key)) if final_key else None
    final_size, _ = media_meta_from_head(final_meta)
    if final_key and object_exists(str(final_key)) and final_size >= MIN_VIDEO_BYTES and not req.force:
        lock.release()
        return {
            "task_id": task_id,
            "final_url": _task_endpoint(task_id, "final"),
            "final_video_url": _task_endpoint(task_id, "final"),
            "final_key": str(final_key),
            "hub": get_hot_follow_workbench_hub(task_id, repo=repo),
        }

    current_for_plan = repo.get(task_id) or task
    current_plan = dict(current_for_plan.get("compose_plan") or {})
    compose_plan = {
        "mute": bool(current_plan.get("mute", True)),
        "overlay_subtitles": bool(current_plan.get("overlay_subtitles", True)),
        "strip_subtitle_streams": bool(current_plan.get("strip_subtitle_streams", True)),
        "cleanup_mode": str(current_plan.get("cleanup_mode") or "none"),
        "target_lang": str(current_plan.get("target_lang") or current_for_plan.get("target_lang") or current_for_plan.get("content_lang") or "mm"),
        "freeze_tail_enabled": bool(current_plan.get("freeze_tail_enabled", False)),
        "freeze_tail_cap_sec": int(current_plan.get("freeze_tail_cap_sec") or 8),
        "compose_policy": "freeze_tail" if bool(current_plan.get("freeze_tail_enabled", False)) else "match_video",
    }
    try:
        _policy_upsert(
            repo,
            task_id,
            {
                "status": "processing",
                "last_step": "compose",
                "compose_status": "running",
                "compose_error": None,
                "compose_error_reason": None,
                "compose_last_status": "running",
                "compose_last_started_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_finished_at": None,
                "compose_last_error": None,
                "compose_warning": None,
                "compose_plan": compose_plan,
                "scene_outputs": current_for_plan.get("scene_outputs") or [],
            },
        )
        lipsync_state = _run_hot_follow_lipsync_stub(
            task_id,
            os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in ("1", "true", "yes"),
        )
        _policy_upsert(
            repo,
            task_id,
            {
                "lipsync_status": lipsync_state.get("status"),
                "lipsync_warning": lipsync_state.get("warning"),
                "compose_video_source": lipsync_state.get("compose_video_source") or "basic",
            },
        )
        if lipsync_state.get("warning"):
            _policy_upsert(repo, task_id, {"compose_warning": lipsync_state.get("warning")})
        updates = _hf_compose_final_video(task_id, repo.get(task_id) or task)
        updates["lipsync_status"] = lipsync_state.get("status")
        updates["lipsync_warning"] = lipsync_state.get("warning")
        updates["compose_video_source"] = lipsync_state.get("compose_video_source") or "basic"
        if lipsync_state.get("warning"):
            current_warning = str(updates.get("compose_warning") or "").strip()
            updates["compose_warning"] = f"{current_warning} {lipsync_state.get('warning')}".strip() if current_warning else lipsync_state.get("warning")
        _policy_upsert(repo, task_id, updates)
        latest = repo.get(task_id) or task
        resolved_key = _task_key(latest, "final_video_key") or _task_key(latest, "final_video_path")
        return {
            "task_id": task_id,
            "final_url": _task_endpoint(task_id, "final"),
            "final_video_url": _task_endpoint(task_id, "final"),
            "final_key": str(resolved_key or ""),
            "hub": get_hot_follow_workbench_hub(task_id, repo=repo),
            "compose_status": latest.get("compose_status"),
        }
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"reason": "compose_failed", "message": str(exc.detail)}
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "failed",
                "compose_error": detail,
                "compose_error_reason": detail.get("reason"),
                "compose_last_status": "failed",
                "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_error": detail.get("message") or str(exc.detail),
                "status": "failed",
                "last_step": "compose",
                "final_video_key": None,
                "final_video_path": None,
            },
        )
        raise
    except Exception as exc:
        detail = {"reason": "compose_failed", "message": str(exc)}
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "failed",
                "compose_error": detail,
                "compose_error_reason": detail.get("reason"),
                "compose_last_status": "failed",
                "compose_last_finished_at": datetime.now(timezone.utc).isoformat(),
                "compose_last_error": detail.get("message"),
                "status": "failed",
                "last_step": "compose",
                "final_video_key": None,
                "final_video_path": None,
            },
        )
        raise HTTPException(status_code=409, detail=detail) from exc
    finally:
        lock.release()


@api_router.post("/hot_follow/tasks/{task_id}/dub", response_model=DubResponse)
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
    return await rerun_dub(
        task_id=task_id,
        payload=payload,
        background_tasks=background_tasks,
        repo=repo,
    )


@api_router.post("/hot_follow/tasks/{task_id}/probe")
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


@api_router.post("/tasks/{task_id}/run")
def run_task_pipeline(
    task_id: str,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _policy_upsert(
        repo,
        task_id,
        {"status": "processing", "last_step": task.get("last_step") or "parse", "error_message": None, "error_reason": None},
    )
    background_tasks.add_task(_run_pipeline_background, task_id, repo)
    return {"queued": True, "task_id": task_id}


@api_router.post("/hot_follow/tasks/{task_id}/run")
def run_hot_follow_pipeline(
    task_id: str,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    return run_task_pipeline(task_id, background_tasks=background_tasks, repo=repo)


@api_router.put("/hot_follow/tasks/{task_id}/publish_backfill")
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


@api_router.post("/tasks/{task_id}/parse")
def build_parse(
    task_id: str,
    payload: ParseTaskRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    if pipeline_config.get("ingest_mode") == "local":
        _policy_upsert(repo, 
            task_id,
            {
                "status": task.get("status") or "processing",
                "last_step": "parse",
                "error_message": None,
                "error_reason": None,
            },
        )
        stored = repo.get(task_id)
        return _task_to_detail(stored)

    link = task.get("source_url") or task.get("link")
    if not link:
        raise HTTPException(status_code=400, detail="source_url is empty; cannot parse")

    platform = (payload.platform if payload else None) or task.get("platform")
    _policy_upsert(repo, task_id, {"status": "processing", "last_step": "parse"})
    parse_req = ParseRequest(task_id=task_id, platform=platform, link=link)

    try:
        parse_res = asyncio.run(run_parse_step_v1(parse_req))
    except HTTPException as exc:
        _policy_upsert(repo, 
            task_id,
            {
                "status": "failed",
                "last_step": "parse",
                "error_message": str(exc.detail),
                "error_reason": "parse_failed",
            },
        )
        raise

    raw_file = raw_path(task_id)
    raw_key = None
    if raw_file.exists():
        raw_key = upload_task_artifact(task, raw_file, "raw.mp4", task_id=task_id)
        try:
            probe = probe_subtitles(raw_file)
            _update_pipeline_probe(repo, task_id, probe)
        except Exception:
            logger.exception("SUBTITLE_PROBE_FAIL", extra={"task_id": task_id})
    duration_sec = parse_res.get("duration_sec") if isinstance(parse_res, dict) else None
    _policy_upsert(repo, 
        task_id,
        {
            "status": "processing",
            "last_step": "parse",
            "raw_path": raw_key,
            "duration_sec": duration_sec,
            "error_message": None,
            "error_reason": None,
        },
    )

    stored = repo.get(task_id)
    return _task_to_detail(stored)


def _run_subtitles_job(
    *,
    task_id: str,
    target_lang: str,
    force: bool,
    translate: bool,
    repo,
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    asyncio.run(
        run_subtitles_step_entry(
            task_id=task_id,
            target_lang=target_lang,
            force=force,
            translate=translate,
        )
    )

    workspace = Workspace(task_id)
    origin_key = (
        upload_task_artifact(task, workspace.origin_srt_path, "origin.srt", task_id=task_id)
        if workspace.origin_srt_path.exists()
        else None
    )
    mm_key = (
        upload_task_artifact(task, workspace.mm_srt_path, "mm.srt", task_id=task_id)
        if workspace.mm_srt_path.exists()
        else None
    )
    mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
    if mm_txt_path.exists():
        upload_task_artifact(task, mm_txt_path, "mm.txt", task_id=task_id)

    subtitles_dir = Path("deliver") / "subtitles" / task_id
    subtitles_key = str(subtitles_dir / "subtitles.json")

    _policy_upsert(repo, 
        task_id,
        {
            "origin_srt_path": origin_key,
            "mm_srt_path": mm_key,
            "last_step": "subtitles",
            "subtitles_status": "ready",
            "subtitles_key": subtitles_key,
            "subtitle_structure_path": subtitles_key,
            "subtitles_error": None,
        },
    )

    stored = repo.get(task_id)
    return _task_to_detail(stored)


def _run_subtitles_background(
    task_id: str,
    target_lang: str,
    force: bool,
    translate: bool,
    repo,
) -> None:
    try:
        _run_subtitles_job(
            task_id=task_id,
            target_lang=target_lang,
            force=force,
            translate=translate,
            repo=repo,
        )
    except HTTPException as exc:
        _policy_upsert(repo, 
            task_id,
            {"subtitles_status": "error", "subtitles_error": f"{exc.status_code}: {exc.detail}"},
        )
        logger.exception(
            "SUB2_FAIL",
            extra={
                "task_id": task_id,
                "step": "subtitles",
                "phase": "exception",
            },
        )


async def _run_dub_job(task_id: str, payload: DubProviderRequest, repo: ITaskRepository) -> DubResponse:
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    settings = get_settings()
    target_lang = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    task_kind = str(task.get("kind") or "").strip().lower()
    provider_raw = payload.provider
    if not provider_raw:
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        dub_mode = pipeline_config.get("dub_mode")
        if dub_mode == "edge":
            provider_raw = "edge-tts"
        elif dub_mode == "lovo":
            provider_raw = "lovo"
        elif dub_mode in {"azure", "azure_tts", "azure-speech"}:
            provider_raw = "azure-speech"
        else:
            provider_raw = task.get("dub_provider") or getattr(settings, "dub_provider", None) or (
                "lovo" if getattr(settings, "lovo_api_key", None) else "edge-tts"
            )
    if not provider_raw:
        provider_raw = "edge-tts"
    provider_norm = provider_raw.lower().replace("-", "_")
    if provider_norm == "edge":
        provider_norm = "edge_tts"
    if provider_norm in {"azure", "azure_tts", "azure_speech"}:
        provider_norm = "azure_speech"
    if provider_norm not in {"edge_tts", "lovo", "azure_speech"}:
        raise HTTPException(status_code=400, detail="Unsupported dub provider")
    provider = (
        "edge-tts"
        if provider_norm == "edge_tts"
        else ("azure-speech" if provider_norm == "azure_speech" else "lovo")
    )
    provider = normalize_provider(provider)

    if provider == "lovo" and not getattr(settings, "lovo_api_key", None):
        raise HTTPException(status_code=400, detail="LOVO_API_KEY is not configured")
    if provider == "azure-speech":
        if (not getattr(settings, "azure_speech_key", None)) or (
            not getattr(settings, "azure_speech_region", None)
        ):
            raise HTTPException(
                status_code=400,
                detail="AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are required for azure-speech",
            )

    req_voice_id = (payload.voice_id or "").strip() or None
    req_tts_speed = None
    if payload.tts_speed is not None:
        try:
            req_tts_speed = max(1.0, min(1.6, float(payload.tts_speed)))
        except Exception:
            req_tts_speed = None
    prev_voice_id = task.get("voice_id") if isinstance(task, dict) else getattr(task, "voice_id", None)
    selected_voice_id = req_voice_id or _voice_state_config(task).get("requested_voice") or prev_voice_id
    provider = _hot_follow_expected_provider(task, selected_voice_id, provider)
    final_voice_id, voice_overridden = resolve_tts_voice(
        settings=settings,
        provider=provider,
        target_lang=target_lang,
        requested_voice=selected_voice_id,
    )
    if task_kind == "hot_follow" and provider == "lovo" and selected_voice_id == "mm_male_1":
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "unsupported_voice_provider_combo",
                "provider": provider,
                "requested_voice": selected_voice_id,
                "resolved_voice": final_voice_id,
                "supported_voices": ["mm_female_1"],
            },
        )
    if not final_voice_id:
        raise HTTPException(status_code=422, detail="TTS_VOICE_MISSING")
    if provider == "lovo":
        supported_voices = ["mm_female_1"]
        resolved_voice_norm = str(final_voice_id or "").strip()
        if resolved_voice_norm not in supported_voices:
            raise HTTPException(
                status_code=422,
                detail={
                    "reason": "unsupported_voice_provider_combo",
                    "provider": provider,
                    "requested_voice": selected_voice_id,
                    "resolved_voice": final_voice_id,
                    "supported_voices": supported_voices,
                },
            )
    if voice_overridden:
        logger.warning(
            "DUB_VOICE_OVERRIDE task=%s target_lang=%s requested=%s resolved=%s provider=%s",
            task_id,
            target_lang,
            req_voice_id or prev_voice_id,
            final_voice_id,
            provider,
        )
    mm_text_override = _hf_dub_input_text(task_id, task, payload.mm_text).strip() or None
    logger.info(
        "DUB3_TEXT_SOURCE",
        extra={
            "task_id": task_id,
            "step": "dub",
            "stage": "DUB3_TEXT_SOURCE",
            "text_source": "override" if (payload.mm_text or "").strip() else "subtitle_lane",
            "text_len": len(mm_text_override or ""),
            "dub_provider": provider,
            "voice_id": final_voice_id,
            "tts_speed": req_tts_speed,
        },
    )
    workspace = Workspace(task_id)
    audio_present = False
    if isinstance(task, dict):
        audio_present = bool(task.get("mm_audio_key") or task.get("mm_audio_path"))
    else:
        audio_present = bool(
            getattr(task, "mm_audio_key", None) or getattr(task, "mm_audio_path", None)
        )
    audio_present = audio_present or workspace.mm_audio_exists()
    voice_changed = bool(req_voice_id and req_voice_id != prev_voice_id)
    force_dub = bool(audio_present and voice_changed)

    edge_voice = None
    if provider == "edge-tts":
        edge_voice = settings.edge_tts_voice_map.get(final_voice_id, final_voice_id)

    request_token = datetime.now(timezone.utc).isoformat()
    config = dict(task.get("config") or {})
    config["tts_requested_voice"] = selected_voice_id
    config["hot_follow_tts_requested_voice"] = selected_voice_id
    config["tts_resolved_voice"] = final_voice_id
    config["tts_provider"] = provider
    config["tts_request_token"] = request_token
    config["tts_completed_token"] = None

    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))

    def _mark_hot_follow_no_dub(reason: str, message: str) -> DubResponse:
        pipeline_updates = dict(pipeline_config)
        pipeline_updates["no_dub"] = "true"
        pipeline_updates["dub_skip_reason"] = reason
        _hf_write_no_dub_note(task_id, reason)
        _policy_upsert(
            repo,
            task_id,
            {
                "config": config,
                "pipeline_config": pipeline_config_to_storage(pipeline_updates),
                "dub_provider": provider,
                "voice_id": selected_voice_id,
                "last_step": "dub",
                "dub_status": "skipped",
                "dub_error": None,
                "mm_audio_key": None,
                "mm_audio_path": None,
                "mm_audio_provider": None,
                "mm_audio_voice_id": None,
                "audio_sha256": None,
                "compose_status": "pending",
                "compose_last_status": "pending",
                "compose_error": {"reason": "no_dub_candidate", "message": message},
                "compose_error_reason": "no_dub_candidate",
                "compose_warning": message,
                "final_video_key": None,
                "final_video_path": None,
                "final_video_sha256": None,
            },
        )
        stored = repo.get(task_id)
        detail = _task_to_detail(stored)
        return DubResponse(
            **detail.dict(exclude={"mm_audio_key"}),
            resolved_voice_id=final_voice_id,
            resolved_edge_voice=edge_voice,
            audio_sha256=None,
            mm_audio_key=None,
        )

    no_dub_state = _hf_detect_no_dub_candidate(task_id, task, mm_text_override)
    if no_dub_state.get("no_dub"):
        logger.info(
            "DUB3_SKIP_NO_SPEECH",
            extra={
                "task_id": task_id,
                "reason": no_dub_state.get("no_dub_reason") or "no_speech_detected",
            },
        )
        return _mark_hot_follow_no_dub(
            str(no_dub_state.get("no_dub_reason") or "no_speech_detected"),
            str(no_dub_state.get("no_dub_message") or "No spoken speech detected in source video; dubbing is skipped."),
        )

    _hf_clear_no_dub_note(task_id)
    pipeline_config.pop("no_dub", None)
    pipeline_config.pop("dub_skip_reason", None)
    for stale_path in (
        workspace.mm_audio_primary_path,
        workspace.mm_audio_mp3_path,
        workspace.mm_audio_legacy_path,
    ):
        try:
            if stale_path.exists():
                stale_path.unlink()
        except Exception:
            logger.warning("DUB3_STALE_AUDIO_CLEANUP_FAIL task=%s path=%s", task_id, stale_path)
    _policy_upsert(
        repo,
        task_id,
        {
            "config": config,
            "pipeline_config": pipeline_config_to_storage(pipeline_config),
            "dub_provider": provider,
            "voice_id": selected_voice_id,
            "last_step": "dub",
            "dub_status": "running",
            "dub_error": None,
            "mm_audio_key": None,
            "mm_audio_path": None,
            "mm_audio_provider": None,
            "mm_audio_voice_id": None,
            "audio_sha256": None,
        },
    )
    task = repo.get(task_id) or task

    logger.info(
        "dub: task=%s req_voice_id=%s prev_voice_id=%s final_voice_id=%s edge_voice=%s",
        task_id,
        req_voice_id,
        prev_voice_id,
        final_voice_id,
        edge_voice,
    )

    try:
        if req_tts_speed is not None:
            pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
            pipeline_config["audio_fit_max_speed"] = f"{req_tts_speed:.2f}"
            _policy_upsert(
                repo,
                task_id,
                {"pipeline_config": pipeline_config_to_storage(pipeline_config)},
            )
            task = repo.get(task_id) or task

        class TaskAdapter:
            def __init__(
                self,
                t: dict,
                voice_override: str | None,
                provider: str,
                force_dub: bool,
                mm_text: str | None,
            ):
                self.task_id = t.get("task_id") or t.get("id")
                self.id = self.task_id
                self.tenant_id = t.get("tenant_id") or t.get("tenant") or "default"
                self.project_id = t.get("project_id") or t.get("project") or "default"
                self.target_lang = normalize_target_lang(
                    t.get("target_lang") or t.get("content_lang") or "my"
                )
                self.voice_id = voice_override or t.get("voice_id")
                self.dub_provider = provider
                self.force_dub = force_dub
                self.mm_text = mm_text

        task_adapter = TaskAdapter(
            task,
            voice_override=final_voice_id,
            provider=provider,
            force_dub=force_dub,
            mm_text=mm_text_override,
        )

        # 鏍稿績锛歋SOT dubbing
        await run_dub_step_ssot(task_adapter)

        task_after = repo.get(task_id) or {}
        existing_audio_key = task_after.get("mm_audio_key") or task_after.get("mm_audio_path")
        existing_audio_exists = bool(existing_audio_key and object_exists(str(existing_audio_key)))
        existing_audio_size = 0
        if existing_audio_key:
            head = object_head(str(existing_audio_key))
            existing_audio_size, _ = media_meta_from_head(head)
        pipeline_config = parse_pipeline_config(task_after.get("pipeline_config"))
        no_dub_flag = pipeline_config.get("no_dub") == "true"
        no_dub_note = (task_base_dir(task_id) / "dub" / "no_dub.txt").exists()
        logger.info(
            "DUB3_DECISION",
            extra={
                "task_id": task_id,
                "decision": "skipped" if (no_dub_flag or no_dub_note) else "executed",
                "reason": "no_dub_mode" if (no_dub_flag or no_dub_note) else "run_dub_step_ssot",
            },
        )
        if no_dub_flag or no_dub_note:
            logger.info(
                "DUB3_SKIP",
                extra={"task_id": task_id, "reason": "no_dub_mode"},
            )
            audio_key = task_after.get("mm_audio_key") or task_after.get("mm_audio_path")
            audio_sha256 = None
            if not audio_key:
                audio_path = (
                    workspace.mm_audio_mp3_path
                    if workspace.mm_audio_mp3_path.exists()
                    else workspace.mm_audio_path
                )
                if audio_path.exists():
                    try:
                        local_size, local_duration = assert_local_audio_ok(audio_path)
                    except ValueError:
                        local_size, local_duration = 0, 0.0
                    audio_key = deliver_key(task_id, "audio_mm.mp3")
                    storage = get_storage_service()
                    if local_size > 0:
                        storage.upload_file(str(audio_path), audio_key, content_type="audio/mpeg")
                        audio_sha256 = _sha256_file(audio_path)
                        logger.info(
                            "DUB3_UPLOAD_DONE",
                            extra={
                                "task_id": task_id,
                                "step": "dub",
                                "stage": "DUB3_UPLOAD_DONE",
                                "output_size": local_size,
                                "duration_sec": local_duration,
                                "uploaded_key": audio_key,
                            },
                        )
                    else:
                        audio_key = None
            logger.info(
                "DUB3_OUTPUT_CHECK",
                extra={
                    "task_id": task_id,
                    "decision": "skipped",
                    "key": audio_key or existing_audio_key,
                    "path": str(workspace.mm_audio_mp3_path if workspace.mm_audio_mp3_path.exists() else workspace.mm_audio_path),
                    "exists": bool(audio_key or existing_audio_exists),
                    "size": int(local_size if 'local_size' in locals() else existing_audio_size),
                },
            )
            if not audio_key:
                _policy_upsert(
                    repo,
                    task_id,
                    {
                        "dub_provider": provider,
                        "last_step": "dub",
                        "voice_id": selected_voice_id,
                        "dub_status": "failed",
                        "dub_error": "output_missing",
                        "dub_generated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                stored = repo.get(task_id)
                detail = _task_to_detail(stored)
                return DubResponse(
                    **detail.dict(exclude={"mm_audio_key"}),
                    resolved_voice_id=final_voice_id,
                    resolved_edge_voice=edge_voice,
                    audio_sha256=None,
                    mm_audio_key=None,
                )
            _policy_upsert(repo, 
                task_id,
                {
                    "mm_audio_path": audio_key,
                    "mm_audio_key": audio_key,
                    "mm_audio_provider": provider,
                    "mm_audio_voice_id": final_voice_id,
                    "mm_audio_bytes": local_size if 'local_size' in locals() else None,
                    "mm_audio_duration_ms": int(local_duration * 1000) if 'local_duration' in locals() else None,
                    "mm_audio_mime": "audio/mpeg" if audio_key else None,
                    "dub_provider": provider,
                    "last_step": "dubbing",
                    "voice_id": selected_voice_id,
                    "dub_status": "skipped",
                    "dub_error": None,
                    "audio_sha256": audio_sha256,
                    "dub_generated_at": datetime.now(timezone.utc).isoformat(),
                    "config": {**config, "tts_completed_token": request_token},
                },
            )
            stored = repo.get(task_id)
            detail = _task_to_detail(stored)
            logger.info(
                "DUB3_DONE",
                extra={
                    "task_id": task_id,
                    "step": "dub",
                    "stage": "DUB3_DONE",
                    "uploaded_key": audio_key,
                },
            )
            return DubResponse(
                **detail.dict(exclude={"mm_audio_key"}),
                resolved_voice_id=final_voice_id,
                resolved_edge_voice=edge_voice,
                audio_sha256=audio_sha256,
                mm_audio_key=audio_key,
            )

        audio_path = (
            workspace.mm_audio_mp3_path
            if workspace.mm_audio_mp3_path.exists()
            else workspace.mm_audio_path
        )
        executed = True
        skip_reason = None
        if not audio_path.exists():
            executed = False
            skip_reason = "output_missing_after_execute"
        logger.info(
            "DUB3_DECISION",
            extra={
                "task_id": task_id,
                "decision": "executed" if executed else "skipped",
                "reason": skip_reason or "fresh_output_expected",
            },
        )
        if not audio_path.exists():
            logger.info(
                "DUB3_OUTPUT_CHECK",
                extra={
                    "task_id": task_id,
                    "decision": "executed",
                    "key": existing_audio_key,
                    "path": str(audio_path),
                    "exists": existing_audio_exists,
                    "size": existing_audio_size,
                },
            )
            _policy_upsert(
                repo,
                task_id,
                {
                    "dub_status": "failed",
                    "dub_error": "output_missing",
                    "last_step": "dub",
                    "voice_id": selected_voice_id,
                },
            )
            stored = repo.get(task_id)
            detail = _task_to_detail(stored)
            return DubResponse(
                **detail.dict(exclude={"mm_audio_key"}),
                resolved_voice_id=final_voice_id,
                resolved_edge_voice=edge_voice,
                audio_sha256=task_after.get("audio_sha256"),
                mm_audio_key=task_after.get("mm_audio_key") or task_after.get("mm_audio_path"),
            )

        try:
            local_size, local_duration = assert_local_audio_ok(audio_path)
        except ValueError:
            _policy_upsert(
                repo,
                task_id,
                {
                    "dub_status": "failed",
                    "dub_error": "output_missing",
                    "last_step": "dub",
                    "voice_id": selected_voice_id,
                },
            )
            stored = repo.get(task_id)
            detail = _task_to_detail(stored)
            return DubResponse(
                **detail.dict(exclude={"mm_audio_key"}),
                resolved_voice_id=final_voice_id,
                resolved_edge_voice=edge_voice,
                audio_sha256=task_after.get("audio_sha256"),
                mm_audio_key=task_after.get("mm_audio_key") or task_after.get("mm_audio_path"),
            )
        audio_key = deliver_key(task_id, "audio_mm.mp3")
        storage = get_storage_service()
        storage.upload_file(str(audio_path), audio_key, content_type="audio/mpeg")
        audio_sha256 = _sha256_file(audio_path)
        logger.info(
            "DUB3_OUTPUT_CHECK",
            extra={
                "task_id": task_id,
                "decision": "executed",
                "key": audio_key,
                "path": str(audio_path),
                "exists": True,
                "size": local_size,
            },
        )
        logger.info(
            "DUB3_UPLOAD_DONE",
            extra={
                "task_id": task_id,
                "step": "dub",
                "stage": "DUB3_UPLOAD_DONE",
                "output_size": local_size,
                "duration_sec": local_duration,
                "uploaded_key": audio_key,
            },
        )

    except HTTPException as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "dub_status": "failed",
                "dub_error": f"{exc.status_code}: {exc.detail}",
                "mm_audio_key": None,
                "mm_audio_path": None,
            },
        )
        raise
    except Exception as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "dub_status": "failed",
                "dub_error": str(exc),
                "mm_audio_key": None,
                "mm_audio_path": None,
            },
        )
        logger.exception("DUB3_FAIL", extra={"task_id": task_id, "step": "dub", "phase": "exception"})
        raise HTTPException(status_code=500, detail=f"Dubbing step failed: {exc}")

    # repo.update 鏈繀瀛樺湪锛涚敤 upsert 鏇寸ǔ
    _policy_upsert(repo, 
        task_id,
        {
            "mm_audio_path": audio_key,
            "mm_audio_key": audio_key,
            "mm_audio_provider": provider,
            "mm_audio_voice_id": final_voice_id,
            "mm_audio_bytes": local_size,
            "mm_audio_duration_ms": int(local_duration * 1000),
            "mm_audio_mime": "audio/mpeg",
            "dub_provider": provider,
            "last_step": "dubbing",
            "voice_id": selected_voice_id,
            "dub_status": "ready",
            "dub_error": None,
            "audio_sha256": audio_sha256,
            "dub_generated_at": datetime.now(timezone.utc).isoformat(),
            "config": {**config, "tts_completed_token": request_token},
        },
    )

    stored = repo.get(task_id)
    detail = _task_to_detail(stored)
    logger.info(
        "DUB3_DONE",
        extra={
            "task_id": task_id,
            "step": "dub",
            "stage": "DUB3_DONE",
            "uploaded_key": audio_key,
        },
    )
    return DubResponse(
        **detail.dict(exclude={"mm_audio_key"}),
        resolved_voice_id=final_voice_id,
        resolved_edge_voice=edge_voice,
        audio_sha256=audio_sha256,
        mm_audio_key=audio_key,
    )


def _run_dub_background(task_id: str, payload: DubProviderRequest, repo: ITaskRepository) -> None:
    try:
        asyncio.run(_run_dub_job(task_id, payload, repo))
    except Exception:
        logger.exception("DUB3_FAIL", extra={"task_id": task_id, "step": "dub", "phase": "exception"})
    except Exception as exc:
        _policy_upsert(repo, task_id, {"subtitles_status": "error", "subtitles_error": str(exc)})
        logger.exception(
            "SUB2_FAIL",
            extra={
                "task_id": task_id,
                "step": "subtitles",
                "phase": "exception",
            },
        )


@api_router.post("/tasks/{task_id}/scenes")
def build_scenes(
    task_id: str,
    background_tasks: BackgroundTasks,
    payload: ScenesRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return build_scenes_for_task(task_id, repo=repo, background_tasks=background_tasks, payload=payload)


@api_router.post("/hot_follow/tasks/{task_id}/scene_pack", deprecated=True)
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

@api_router.post("/tasks/{task_id}/pack")
def build_pack(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    state_service = TaskStateService(repo=repo, step="router.tasks")
    state_service.update_fields(task_id, {"status": "processing", "last_step": "pack"})
    pack_req = PackRequest(task_id=task_id)
    try:
        pack_res = asyncio.run(run_pack_step_v1(pack_req))
    except HTTPException as exc:
        state_service.update_fields(
            task_id,
            {
                "status": "failed",
                "last_step": "pack",
                "error_message": str(exc.detail),
                "error_reason": "pack_failed",
            },
        )
        raise

    pack_key = None
    if isinstance(pack_res, dict):
        pack_key = pack_res.get("pack_key") or pack_res.get("zip_key")
    state_service.update_fields(
        task_id,
        {
            "status": "ready",
            "last_step": "pack",
            "pack_key": pack_key,
            "pack_type": "capcut_v18" if pack_key else None,
            "pack_status": "ready" if pack_key else None,
            "error_message": None,
            "error_reason": None,
        },
    )

    stored = repo.get(task_id)
    return _task_to_detail(stored)

@api_router.post("/tasks/{task_id}/dub", response_model=DubResponse)
async def rerun_dub(
    task_id: str,
    payload: DubProviderRequest,
    background_tasks: BackgroundTasks,
    repo: ITaskRepository = Depends(get_task_repository),
):
    """Re-run dubbing for a task (SSOT: reads artifacts/subtitles.json)."""

    t0 = time.perf_counter()
    try:
        task = repo.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        run_async = os.getenv("RUN_STEPS_ASYNC", "1").strip().lower() not in ("0", "false", "no")
        _policy_upsert(repo, task_id, {"dub_status": "running", "dub_error": None, "last_step": "dub"})

        if run_async:
            background_tasks.add_task(_run_dub_background, task_id, payload, repo)
            return JSONResponse(status_code=202, content={"queued": True, "task_id": task_id})

        return await _run_dub_job(task_id, payload, repo)
    finally:
        logger.info(
            "dub request finished",
            extra={
                "task_id": task_id,
                "step": "dub",
                "phase": "request_end",
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        )


@api_router.post("/tasks/{task_id}/publish")
def publish_task(
    task_id: str,
    payload: PublishTaskRequest | None = None,
    repo=Depends(get_task_repository),
):
    if payload and (payload.published or payload.published_url or payload.notes):
        published = bool(payload.published or payload.published_url)
        updates = {
            "publish_status": "ready" if published else None,
            "publish_url": payload.published_url or None,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "publish_meta": {
                "published": published,
                "published_url": payload.published_url,
                "notes": payload.notes,
            },
        }
        _policy_upsert(repo, task_id, updates)
        task = repo.get(task_id) or {}
        return {
            "task_id": task_id,
            "provider": "manual",
            "publish_key": task.get("publish_key"),
            "download_url": payload.published_url or task.get("publish_url") or "",
            "published_at": updates["published_at"],
        }

    db = SessionLocal()
    try:
        res = publish_task_pack(
            task_id,
            db,
            task_repo=repo,
            provider=(payload.provider if payload else None),
            force=(payload.force if payload else False),
        )
        task = db.query(models.Task).filter(models.Task.id == task_id).first()
        if task:
            _policy_upsert(repo, 
                task_id,
                {
                    "publish_provider": task.publish_provider,
                    "publish_key": task.publish_key,
                    "publish_url": task.publish_url,
                    "publish_status": task.publish_status,
                    "published_at": task.published_at,
                },
            )
        download_url = res.get("download_url") or (resolve_download_url(task) if task else "")
        return {
            "task_id": task_id,
            "provider": res.get("provider"),
            "publish_key": res.get("publish_key"),
            "download_url": download_url,
            "published_at": res.get("published_at"),
        }
    finally:
        db.close()


@api_router.post("/tasks/{task_id}/subtitles")
def build_subtitles(
    task_id: str,
    background_tasks: BackgroundTasks,
    payload: SubtitlesTaskRequest | None = None,
    repo=Depends(get_task_repository),
):
    t0 = time.perf_counter()
    try:
        task = repo.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.get("subtitles_status") == "ready" and task.get("subtitles_key"):
            return {
                "task_id": task_id,
                "status": "already_ready",
                "subtitles_key": task.get("subtitles_key"),
                "message": "Subtitles already ready",
                "error": None,
            }

        target_lang, force, translate = compute_subtitles_params(task, payload)

        run_async = os.getenv("RUN_STEPS_ASYNC", "1").strip().lower() not in ("0", "false", "no")
        _policy_upsert(repo, 
            task_id,
            {
                "subtitles_status": "running",
                "subtitles_error": None,
                "last_step": "subtitles",
            },
        )

        if run_async:
            background_tasks.add_task(
                _run_subtitles_background,
                task_id,
                target_lang,
                force,
                translate,
                repo,
            )
            return JSONResponse(status_code=202, content={"queued": True, "task_id": task_id})

        return _run_subtitles_job(
            task_id=task_id,
            target_lang=target_lang,
            force=force,
            translate=translate,
            repo=repo,
        )
    finally:
        logger.info(
            "subtitles request finished",
            extra={
                "task_id": task_id,
                "step": "subtitles",
                "phase": "request_end",
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        )



@api_router.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    delete_assets: bool = Query(default=False),
    repo=Depends(get_task_repository),
):
    """Delete a task record and optionally purge stored artifacts."""

    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if delete_assets:
        try:
            purged = purge_task_artifacts(task)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Asset purge failed: {exc}") from exc
    else:
        purged = 0

    try:
        delete_task_record(task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc

    return {"ok": True, "task_id": task_id, "deleted_assets": bool(delete_assets), "purged": purged}


router = api_router

__all__ = ["api_router", "pages_router", "router"]
