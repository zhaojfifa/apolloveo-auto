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
from gateway.app.services.parse import detect_platform
from gateway.app.providers.xiongmao import XiongmaoError, parse_with_xiongmao


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
    object_exists,
)
from gateway.app.ports.storage_provider import get_storage_service
from gateway.app.services.scene_split import enqueue_scenes_build
from gateway.app.services.publish_service import publish_task_pack, resolve_download_url
from gateway.app.services.task_state_service import TaskStateService
from gateway.app.db import SessionLocal

from gateway.app.task_repo_utils import normalize_task_payload, sort_tasks_by_created
from gateway.app.services.task_cleanup import delete_task_record, purge_task_artifacts
from gateway.app.utils.pipeline_config import parse_pipeline_config, pipeline_config_to_storage
from gateway.app.utils.subtitle_probe import probe_subtitles
from gateway.app.services.task_semantics import derive_task_semantics

from ..core.workspace import (
    Workspace,
    origin_srt_path,
    deliver_pack_zip_path,
    raw_path,
    relative_to_workspace,
    task_base_dir,
)

logger = logging.getLogger(__name__)

AUDIO_MM_KEY_TEMPLATE = "deliver/tasks/{task_id}/audio_mm.mp3"
OP_HEADER_KEY = "X-OP-KEY"


class DubProviderRequest(BaseModel):
    provider: str | None = None
    voice_id: str | None = None
    mm_text: str | None = None
    subtitles_srt: str | None = None
    tts_engine: str | None = None
    tts_voice: str | None = None


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


class HotFollowSubtitlesRequest(BaseModel):
    srt_text: str = ""


class ComposeTaskRequest(BaseModel):
    voiceover_url: str | None = None
    bgm_url: str | None = None
    bgm_mix: float | None = None
    force: bool = False


pages_router = APIRouter()
api_router = APIRouter(prefix="/api", tags=["tasks"])
api_key_header = APIKeyHeader(name=OP_HEADER_KEY, auto_error=False)
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


@pages_router.get("/v1/tasks/{task_id}/audio_mm")
def download_audio_mm(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="dubbed audio not found")
    key = _task_value(task, "mm_audio_key")
    if not key or not object_exists(str(key)):
        return _not_ready_response(task, "audio_mm", ["mm_audio_key"])
    logger.info("audio_mm download: task_id=%s key=%s", task_id, key)
    return RedirectResponse(url=get_download_url(str(key)), status_code=302)


@pages_router.get("/v1/tasks/{task_id}/final")
def download_final_video(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="final video not found")
    key = _task_value(task, "final_video_key") or _task_value(task, "final_video_path")
    if not key or not object_exists(str(key)):
        return _not_ready_response(task, "final", ["final_video_key"])
    return RedirectResponse(url=get_download_url(str(key)), status_code=302)


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
    scenes_key = _task_value(task, "scenes_key")
    scenes_status = str(_task_value(task, "scenes_status") or "").lower()
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
    scenes_key = _task_key(task, "scenes_key")

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
        scenes_key = _task_value(task, "scenes_key")
        scenes_path = _task_value(task, "scenes_path")
        scenes_status = str(_task_value(task, "scenes_status") or "").lower()
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


def _publish_hub_payload(task: dict) -> dict[str, object]:
    task_id = str(_task_value(task, "task_id") or _task_value(task, "id") or "")
    deliverables = {}
    for key, label in (
        ("pack_zip", "pack.zip"),
        ("scenes_zip", "scenes.zip"),
        ("origin_srt", "origin.srt"),
        ("mm_srt", "mm.srt"),
        ("mm_txt", "mm.txt"),
        ("mm_audio", "mm_audio"),
        ("edit_bundle_zip", "edit_bundle.zip"),
    ):
        url = _deliverable_url(task_id, task, key)
        if url:
            deliverables[key] = {"label": label, "url": url}
    short_code = _download_code(task_id)
    short_url = f"/d/{short_code}"

    return {
        "task_id": task_id,
        "gate_enabled": _op_gate_enabled(),
        "deliverables": deliverables,
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
    if p == "lovo":
        return "lovo"
    return "none"


def _hf_engine_internal(engine: str | None) -> str | None:
    e = str(engine or "").strip().lower()
    if e in {"edge", "edge-tts", "edge_tts"}:
        return "edge-tts"
    if e == "lovo":
        return "lovo"
    if e in {"none", ""}:
        return None
    return None


def _hf_audio_config(task: dict) -> dict[str, Any]:
    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    mix = bgm.get("mix_ratio")
    try:
        mix_val = float(mix if mix is not None else 0.3)
    except Exception:
        mix_val = 0.3
    task_id = str(task.get("task_id") or task.get("id") or "")
    voice_url = _task_endpoint(task_id, "audio") if (task.get("mm_audio_key") or task.get("mm_audio_path")) else None
    bust = task.get("audio_sha256") or task.get("dub_generated_at") or task.get("updated_at")
    if voice_url and bust:
        sep = "&" if "?" in voice_url else "?"
        voice_url = f"{voice_url}{sep}v={bust}"
    return {
        "tts_engine": _hf_engine_public(task.get("dub_provider")),
        "tts_voice": task.get("voice_id") or "zh-CN-XiaoxiaoNeural",
        "bgm_key": bgm.get("bgm_key"),
        "bgm_mix": max(0.0, min(1.0, mix_val)),
        "bgm_url": get_download_url(str(bgm.get("bgm_key"))) if bgm.get("bgm_key") else None,
        "voiceover_url": voice_url,
        "audio_url": voice_url,
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
        if status == "pending" and (task.get("mm_audio_key") or task.get("mm_audio_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "dub":
            status = "running"
        summary = f"dub_provider={task.get('dub_provider') or '-'} voice={task.get('voice_id') or '-'}"
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
            _hf_deliverable_state(task, scenes_key, "scenes_status"),
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
        return task.get(field)
    return getattr(task, field, None)


def _task_key(task: dict, field: str) -> Optional[str]:
    value = _task_value(task, field)
    return str(value) if value else None


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
    scenes_url = _task_endpoint(task_id, "scenes") if task.get("scenes_key") else None

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
        "scenes_status": task.get("scenes_status"),
        "scenes_key": task.get("scenes_key"),
        "scenes_error": task.get("scenes_error"),
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
            audio_key = AUDIO_MM_KEY_TEMPLATE.format(task_id=task_id)
            storage = get_storage_service()
            uploaded_key = storage.upload_file(
                str(mp3_path), audio_key, content_type="audio/mpeg"
            )
            if not uploaded_key:
                raise HTTPException(
                    status_code=500,
                    detail="Audio upload failed; no storage key returned",
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
    task_view = {"source_url_open": _extract_first_http_url(task.get("source_url"))}

    spec = resolve_workbench_spec(task)
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


@api_router.get("/contracts/hot_follow_workbench_v1")
def get_hot_follow_workbench_contract_v1():
    return {
        "name": "hot_follow_workbench",
        "version": "v1",
        "endpoints": {
            "hub": "/api/hot_follow/tasks/{task_id}/workbench_hub",
            "rerun_audio": "/api/hot_follow/tasks/{task_id}/dub",
            "compose_final": "/api/hot_follow/tasks/{task_id}/compose",
            "raw_video": "/v1/tasks/{task_id}/raw",
            "final_video": "/v1/tasks/{task_id}/final",
            "audio_mm": "/v1/tasks/{task_id}/audio_mm",
        },
        "tts": {
            "engines": ["edge_tts", "lovo", "none"],
            "voices": [
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural",
                "my-MM-NilarNeural",
                "mm_female_1",
            ],
        },
        "bgm": {
            "mix_range": [0.0, 1.0],
            "mix_step": 0.05,
            "accept": "audio/*",
        },
    }


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
    return _publish_hub_payload(task)


@api_router.get("/hot_follow/tasks/{task_id}/workbench_hub")
def get_hot_follow_workbench_hub(
    task_id: str,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("hot_follow_hub_hit task=%s kind=%s", task_id, task.get("kind"))
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    parse_state, parse_summary = _hf_pipeline_state(task, "parse")
    subtitles_state, subtitles_summary = _hf_pipeline_state(task, "subtitles")
    dub_state, dub_summary = _hf_pipeline_state(task, "audio")
    pack_state, pack_summary = _hf_pipeline_state(task, "pack")
    compose_state, compose_summary = _hf_pipeline_state(task, "compose")

    raw_key = _task_key(task, "raw_path")
    raw_url = _task_endpoint(task_id, "raw") if raw_key and object_exists(raw_key) else None
    mute_key = _task_key(task, "mute_video_key") or _task_key(task, "mute_video_path")
    mute_url = _task_endpoint(task_id, "raw") if mute_key and object_exists(str(mute_key)) else raw_url
    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
    final_url = _task_endpoint(task_id, "final") if final_key and object_exists(str(final_key)) else None
    scene_key = _task_key(task, "scenes_key")
    scenes_url = _task_endpoint(task_id, "scenes") if scene_key and object_exists(scene_key) else None
    subtitles_text = _hf_load_subtitles_text(task_id, task)
    origin_text = _hf_load_origin_subtitles_text(task)
    audio_cfg = _hf_audio_config(task)
    deliverables = _hf_deliverables(task_id, task)

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
            "target_lang": task.get("content_lang") or "zh",
            "subtitles_mode": pipeline_config.get("subtitles_mode") or "whisper+gemini",
        },
        "media": {
            "raw_url": raw_url,
            "source_video_url": raw_url,
            "mute_video_url": mute_url,
            "voiceover_url": audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
            "bgm_url": audio_cfg.get("bgm_url"),
            "final_video_url": final_url,
        },
        "pipeline": pipeline,
        "subtitles": {
            "origin_text": origin_text or "",
            "edited_text": subtitles_text or "",
            "srt_text": subtitles_text or "",
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
            "sha256": task.get("audio_sha256"),
        },
        "scene_pack": {
            "status": _hf_deliverable_state(task, scene_key, "scenes_status"),
            "download_url": scenes_url,
            "scenes_url": scenes_url,
        },
        "deliverables": deliverables if isinstance(deliverables, list) else [],
        "events": task.get("events") or [],
        "errors": {
            "audio": {"reason": task.get("error_reason"), "message": task.get("dub_error")},
            "pack": {"reason": task.get("error_reason"), "message": task.get("pack_error")},
            "compose": {"reason": task.get("error_reason"), "message": task.get("compose_error")},
        },
    }

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
        updates["dub_provider"] = provider
    if payload.tts_voice is not None:
        updates["voice_id"] = payload.tts_voice.strip() or None

    if updates:
        _policy_upsert(repo, task_id, updates)

    current = repo.get(task_id) or task
    return {
        "task_id": task_id,
        "audio_config": _hf_audio_config(current),
    }


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
            "edited_text": _hf_load_subtitles_text(task_id, repo.get(task_id) or task),
            "editable": True,
        },
    }


def _hf_compose_final_video(
    task_id: str,
    task: dict,
    *,
    audio_key_override: str | None = None,
    bgm_key_override: str | None = None,
    bgm_mix_override: float | None = None,
) -> dict[str, Any]:
    storage = get_storage_service()
    video_key = (
        _task_key(task, "mute_video_key")
        or _task_key(task, "mute_video_path")
        or _task_key(task, "raw_path")
    )
    audio_key = audio_key_override or _task_key(task, "mm_audio_key") or _task_key(task, "mm_audio_path")
    if not video_key:
        raise HTTPException(status_code=409, detail="missing video source for compose")
    if not audio_key:
        raise HTTPException(status_code=409, detail="missing voiceover audio for compose")
    if not object_exists(str(video_key)):
        raise HTTPException(status_code=409, detail="video source not ready")
    if not object_exists(str(audio_key)):
        raise HTTPException(status_code=409, detail="voiceover audio not ready")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise HTTPException(status_code=500, detail="ffmpeg not found in PATH")

    config = dict(task.get("config") or {})
    bgm = dict(config.get("bgm") or {})
    bgm_key = bgm_key_override or (str(bgm.get("bgm_key") or "").strip() or None)
    if bgm_key and not object_exists(bgm_key):
        bgm_key = None
    if bgm_mix_override is not None:
        bgm_mix = bgm_mix_override
    else:
        try:
            bgm_mix = float(bgm.get("mix_ratio") if bgm.get("mix_ratio") is not None else 0.3)
        except Exception:
            bgm_mix = 0.3
    bgm_mix = max(0.0, min(1.0, bgm_mix))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / "video_input.mp4"
        voice_path = tmp / "voice_input.mp3"
        final_path = tmp / "final_compose.mp4"
        storage.download_file(str(video_key), str(video_path))
        storage.download_file(str(audio_key), str(voice_path))

        bgm_path = None
        if bgm_key:
            bgm_path = tmp / "bgm_input.mp3"
            storage.download_file(str(bgm_key), str(bgm_path))

        if bgm_path and bgm_path.exists():
            filter_complex = (
                f"[1:a]volume=1.0[voice];"
                f"[2:a]volume={bgm_mix}[bgm];"
                "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2[mix]"
            )
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(voice_path),
                "-i",
                str(bgm_path),
                "-filter_complex",
                filter_complex,
                "-map",
                "0:v:0",
                "-map",
                "[mix]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                str(final_path),
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                raise HTTPException(status_code=500, detail=f"compose ffmpeg failed: {proc.stderr[-800:]}")
        else:
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(voice_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                str(final_path),
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                cmd_fallback = [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_path),
                    "-i",
                    str(voice_path),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(final_path),
                ]
                proc2 = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc2.returncode != 0 or not final_path.exists() or final_path.stat().st_size == 0:
                    raise HTTPException(status_code=500, detail=f"compose ffmpeg failed: {proc2.stderr[-800:]}")

        final_key = upload_task_artifact(task, final_path, "final_compose.mp4", task_id=task_id)
        if not final_key:
            raise HTTPException(status_code=500, detail="compose upload failed")
        return {
            "final_video_key": final_key,
            "final_video_path": final_key,
            "final_video_sha256": _sha256_file(final_path),
            "compose_provider": "ffmpeg",
            "compose_status": "ready",
            "compose_error": None,
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
    _policy_upsert(
        repo,
        task_id,
        {
            "status": "processing",
            "last_step": "compose",
            "compose_status": "running",
            "compose_error": None,
        },
    )
    try:
        updates = _hf_compose_final_video(task_id, repo.get(task_id) or task)
        _policy_upsert(repo, task_id, updates)
        latest = repo.get(task_id) or task
        return {
            "ok": True,
            "task_id": task_id,
            "final_video_url": _task_endpoint(task_id, "final"),
            "hub": get_hot_follow_workbench_hub(task_id, repo=repo),
            "compose_status": latest.get("compose_status"),
        }
    except HTTPException as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "error",
                "compose_error": str(exc.detail),
                "status": "failed",
                "last_step": "compose",
            },
        )
        raise
    except Exception as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "error",
                "compose_error": str(exc),
                "status": "failed",
                "last_step": "compose",
            },
        )
        raise HTTPException(status_code=500, detail=f"compose failed: {exc}") from exc


def _resolve_compose_storage_key(candidate: str | None) -> str | None:
    value = str(candidate or "").strip()
    if not value:
        return None
    if object_exists(value):
        return value
    return None


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
    final_key = _task_key(task, "final_video_key") or _task_key(task, "final_video_path")
    if final_key and object_exists(str(final_key)) and not req.force:
        return {
            "task_id": task_id,
            "final_video_url": _task_endpoint(task_id, "final"),
            "final_key": str(final_key),
        }

    bgm_mix = None
    if req.bgm_mix is not None:
        bgm_mix = max(0.0, min(1.0, float(req.bgm_mix)))
        config = dict(task.get("config") or {})
        bgm_cfg = dict(config.get("bgm") or {})
        bgm_cfg["mix_ratio"] = bgm_mix
        config["bgm"] = bgm_cfg
        _policy_upsert(repo, task_id, {"config": config})

    audio_key_override = _resolve_compose_storage_key(req.voiceover_url)
    bgm_key_override = _resolve_compose_storage_key(req.bgm_url)
    if bgm_key_override:
        latest_cfg = dict((repo.get(task_id) or task).get("config") or {})
        bgm_cfg = dict(latest_cfg.get("bgm") or {})
        bgm_cfg["bgm_key"] = bgm_key_override
        latest_cfg["bgm"] = bgm_cfg
        _policy_upsert(repo, task_id, {"config": latest_cfg})

    _policy_upsert(
        repo,
        task_id,
        {
            "status": "processing",
            "last_step": "compose",
            "compose_status": "running",
            "compose_error": None,
        },
    )
    try:
        updates = _hf_compose_final_video(
            task_id,
            repo.get(task_id) or task,
            audio_key_override=audio_key_override,
            bgm_key_override=bgm_key_override,
            bgm_mix_override=bgm_mix,
        )
        _policy_upsert(repo, task_id, updates)
    except HTTPException as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "error",
                "compose_error": str(exc.detail),
                "status": "failed",
                "last_step": "compose",
            },
        )
        raise
    except Exception as exc:
        _policy_upsert(
            repo,
            task_id,
            {
                "compose_status": "error",
                "compose_error": str(exc),
                "status": "failed",
                "last_step": "compose",
            },
        )
        raise HTTPException(status_code=500, detail=f"compose failed: {exc}") from exc

    latest = repo.get(task_id) or {}
    latest_final_key = _task_key(latest, "final_video_key") or _task_key(latest, "final_video_path")
    return {
        "task_id": task_id,
        "final_video_url": _task_endpoint(task_id, "final"),
        "final_key": str(latest_final_key or ""),
    }


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
    provider = payload.provider or _hf_engine_internal(payload.tts_engine)
    voice = payload.voice_id or payload.tts_voice
    target_text = (payload.subtitles_srt or payload.mm_text or "").strip()
    if not target_text:
        target_text = _hf_load_subtitles_text(task_id, task).strip()
    if not target_text:
        target_text = _hf_load_origin_subtitles_text(task).strip()
    if target_text:
        override_path = _hf_subtitles_override_path(task_id)
        override_path.parent.mkdir(parents=True, exist_ok=True)
        override_path.write_text(target_text + ("\n" if target_text else ""), encoding="utf-8")
        _policy_upsert(
            repo,
            task_id,
            {
                "subtitles_status": "ready",
                "last_step": "subtitles",
                "subtitles_override_updated_at": datetime.now(timezone.utc).isoformat(),
                "error_message": None,
                "error_reason": None,
            },
        )
    payload = DubProviderRequest(
        provider=provider,
        voice_id=voice,
        mm_text=target_text or None,
        subtitles_srt=payload.subtitles_srt,
        tts_engine=payload.tts_engine,
        tts_voice=payload.tts_voice,
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
    provider_raw = payload.provider
    if not provider_raw:
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        dub_mode = pipeline_config.get("dub_mode")
        if dub_mode == "edge":
            provider_raw = "edge-tts"
        elif dub_mode == "lovo":
            provider_raw = "lovo"
        else:
            provider_raw = "lovo" if getattr(settings, "lovo_api_key", None) else "edge-tts"
    if not provider_raw:
        provider_raw = "edge-tts"
    provider_norm = provider_raw.lower().replace("-", "_")
    if provider_norm == "edge":
        provider_norm = "edge_tts"
    if provider_norm not in {"edge_tts", "lovo"}:
        raise HTTPException(status_code=400, detail="Unsupported dub provider")
    provider = "edge-tts" if provider_norm == "edge_tts" else "lovo"

    if provider == "lovo" and not getattr(settings, "lovo_api_key", None):
        raise HTTPException(status_code=400, detail="LOVO_API_KEY is not configured")

    req_voice_id = payload.voice_id or None
    prev_voice_id = task.get("voice_id") if isinstance(task, dict) else getattr(task, "voice_id", None)
    final_voice_id = req_voice_id or prev_voice_id or "mm_female_1"
    mm_text_override = (payload.mm_text or "").strip() or None
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

    logger.info(
        "dub: task=%s req_voice_id=%s prev_voice_id=%s final_voice_id=%s edge_voice=%s",
        task_id,
        req_voice_id,
        prev_voice_id,
        final_voice_id,
        edge_voice,
    )

    try:
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
                self.target_lang = t.get("target_lang") or t.get("content_lang") or "my"
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
        pipeline_config = parse_pipeline_config(task_after.get("pipeline_config"))
        no_dub_flag = pipeline_config.get("no_dub") == "true"
        no_dub_note = (task_base_dir(task_id) / "dub" / "no_dub.txt").exists()
        if no_dub_flag or no_dub_note:
            audio_key = task_after.get("mm_audio_key") or task_after.get("mm_audio_path")
            audio_sha256 = None
            if not audio_key:
                audio_path = (
                    workspace.mm_audio_mp3_path
                    if workspace.mm_audio_mp3_path.exists()
                    else workspace.mm_audio_path
                )
                if audio_path.exists():
                    audio_key = AUDIO_MM_KEY_TEMPLATE.format(task_id=task_id)
                    storage = get_storage_service()
                    storage.upload_file(str(audio_path), audio_key, content_type="audio/mpeg")
                    audio_sha256 = _sha256_file(audio_path)
            _policy_upsert(repo, 
                task_id,
                {
                    "mm_audio_path": audio_key,
                    "mm_audio_key": audio_key,
                    "dub_provider": provider,
                    "last_step": "dubbing",
                    "voice_id": final_voice_id,
                    "dub_status": "ready",
                    "dub_error": None,
                    "audio_sha256": audio_sha256,
                    "dub_generated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            stored = repo.get(task_id)
            detail = _task_to_detail(stored)
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
        if not audio_path.exists():
            raise HTTPException(status_code=500, detail="Dubbing output missing")

        audio_key = AUDIO_MM_KEY_TEMPLATE.format(task_id=task_id)
        storage = get_storage_service()
        storage.upload_file(str(audio_path), audio_key, content_type="audio/mpeg")
        audio_sha256 = _sha256_file(audio_path)

    except HTTPException as exc:
        _policy_upsert(repo, task_id, {"dub_status": "error", "dub_error": f"{exc.status_code}: {exc.detail}"})
        raise
    except Exception as exc:
        _policy_upsert(repo, task_id, {"dub_status": "error", "dub_error": str(exc)})
        logger.exception("DUB3_FAIL", extra={"task_id": task_id, "step": "dub", "phase": "exception"})
        raise HTTPException(status_code=500, detail=f"Dubbing step failed: {exc}")

    # repo.update 鏈繀瀛樺湪锛涚敤 upsert 鏇寸ǔ
    _policy_upsert(repo, 
        task_id,
        {
            "mm_audio_path": audio_key,
            "mm_audio_key": audio_key,
            "dub_provider": provider,
            "last_step": "dubbing",
            "voice_id": final_voice_id,
            "dub_status": "ready",
            "dub_error": None,
            "audio_sha256": audio_sha256,
            "dub_generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    stored = repo.get(task_id)
    detail = _task_to_detail(stored)
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

    def _update(task_id: str, fields: dict) -> None:
        _policy_upsert(repo, task_id, fields)

    return enqueue_scenes_build(
        task_id,
        task=task,
        object_exists=object_exists,
        update_task=_update,
        background_tasks=background_tasks,
    )

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

        provider = payload.provider or _hf_engine_internal(payload.tts_engine)
        voice = payload.voice_id or payload.tts_voice
        mm_text = payload.mm_text
        if not (mm_text or "").strip():
            mm_text = payload.subtitles_srt
        payload = DubProviderRequest(
            provider=provider,
            voice_id=voice,
            mm_text=mm_text,
            subtitles_srt=payload.subtitles_srt,
            tts_engine=payload.tts_engine,
            tts_voice=payload.tts_voice,
        )
        if (payload.mm_text or "").strip() and str(task.get("kind") or "").strip().lower() == "hot_follow":
            active_text = (payload.mm_text or "").strip()
            override_path = _hf_subtitles_override_path(task_id)
            override_path.parent.mkdir(parents=True, exist_ok=True)
            override_path.write_text(active_text + "\n", encoding="utf-8")
            _policy_upsert(
                repo,
                task_id,
                {
                    "subtitles_status": "ready",
                    "subtitles_override_updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

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
