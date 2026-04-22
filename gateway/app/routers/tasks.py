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
    _srt_to_txt,
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
from gateway.app.steps.subtitles import _parse_srt_to_segments, segments_to_srt
from gateway.app.providers.gemini_subtitles import GeminiSubtitlesError, translate_segments_with_gemini


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

# ── Phase 1.3 Port Merge: import from service modules ─────────────────────────
from gateway.app.core.constants import (  # noqa: E402
    DubProviderRequest,
    OP_HEADER_KEY,
    PublishBackfillRequest,
    api_key_header,
)
from gateway.app.services.compose_helpers import (  # noqa: E402
    build_atempo_chain as _build_atempo_chain,
    compute_audio_fit_speeds as _compute_audio_fit_speeds,
    resolve_audio_fit_max_speed as _resolve_audio_fit_max_speed,
)
from gateway.app.services.media_helpers import (  # noqa: E402
    merge_probe_into_pipeline_config as _merge_probe_into_pipeline_config,
    probe_url_metadata as _probe_url_metadata,
    save_upload_to_paths as _save_upload_to_paths,
    sha256_file as _sha256_file,
    update_pipeline_probe as _update_pipeline_probe,
    upload_task_bgm_impl as _upload_task_bgm_impl,
)
from gateway.app.services.task_view_helpers import (  # noqa: E402
    _build_copy_bundle,
    _get_op_access_key,
    _op_sign,
    _publish_sop_markdown,
    backfill_compose_done_if_final_ready as _backfill_compose_done_if_final_ready,
    build_translation_qa_summary as _build_translation_qa_summary,
    build_workbench_debug_payload as _build_workbench_debug_payload,
    coerce_datetime as _coerce_datetime,
    compose_error_parts as _compose_error_parts,
    compute_composed_state as _compute_composed_state,
    count_srt_cues as _count_srt_cues,
    deliverable_url as _deliverable_url,
    derive_status,
    download_code as _download_code,
    extract_first_http_url as _extract_first_http_url,
    model_allowed_fields as _model_allowed_fields,
    normalize_selected_tool_ids as _normalize_selected_tool_ids,
    op_gate_enabled as _op_gate_enabled,
    publish_hub_payload as _publish_hub_payload,
    resolve_download_urls as _resolve_download_urls,
    resolve_hub_final_url as _resolve_hub_final_url,
    scene_pack_info as _scene_pack_info,
    scenes_status_from_ssot as _scenes_status_from_ssot,
    signed_op_url as _signed_op_url,
    task_endpoint as _task_endpoint,
    task_key as _task_key,
    task_to_detail as _task_to_detail,
    task_value as _task_value,
)
from gateway.app.services.task_router_presenters import (  # noqa: E402
    build_task_publish_hub as _build_task_publish_hub,
    build_task_summaries_page as _build_task_summaries_page,
    build_task_status_payload as _build_task_status_payload,
    build_v1_task_status_payload as _build_v1_task_status_payload,
    build_task_workbench_page_context as _build_task_workbench_page_context,
    build_tasks_page_rows as _build_tasks_page_rows,
    build_task_workbench_task_json as _build_task_workbench_task_json,
    build_task_workbench_view as _build_task_workbench_view,
)
from gateway.app.services.op_auth import (  # noqa: E402
    op_key_valid_request as _op_key_valid_request,
    op_key_valid_value as _service_op_key_valid_value,
)
from gateway.app.services.task_router_actions import (  # noqa: E402
    TaskRouterActionPorts,
    register_task_router_action_ports,
)
from gateway.app.services.voice_state import (  # noqa: E402
    DRY_TTS_CONFIG_KEY as _DRY_TTS_CONFIG_KEY,
    DRY_TTS_ROLE as _DRY_TTS_ROLE,
    build_hot_follow_voice_options as _build_hot_follow_voice_options,
    collect_voice_execution_state as _collect_voice_execution_state,
    hf_audio_matches_expected as _hf_audio_matches_expected,
    hf_current_voiceover_asset as _hf_current_voiceover_asset,
    hf_persisted_audio_state as _hf_persisted_audio_state,
    hot_follow_expected_provider as _hot_follow_expected_provider,
    resolve_hot_follow_provider_voice as _resolve_hot_follow_provider_voice,
    resolve_hot_follow_requested_voice as _resolve_hot_follow_requested_voice,
    voice_state_config as _voice_state_config,
)
from gateway.app.services.artifact_helpers import (  # noqa: E402
    is_storage_key as _artifact_is_storage_key,
    load_dub_text as _load_dub_text,
    mm_edited_path as _artifact_mm_edited_path,
    upload_target_subtitle_artifacts as _artifact_upload_target_subtitle_artifacts,
    pack_path_for_list as _artifact_pack_path_for_list,
)
from gateway.app.services.task_download_views import (  # noqa: E402
    build_deliverable_download_redirect as _build_deliverable_download_redirect,
    build_not_ready_response as _build_not_ready_response,
    require_storage_key as _require_storage_key,
    text_or_redirect as _text_or_redirect,
)
from gateway.app.services.task_stream_views import (  # noqa: E402
    build_stream_download_response as _build_stream_download_response,
    build_stream_head_response as _build_stream_head_response,
    parse_http_range as _svc_parse_http_range,
    resolve_audio_meta as _svc_resolve_audio_meta,
    resolve_final_meta as _svc_resolve_final_meta,
)
from gateway.app.services.task_subtitle_detection import (  # noqa: E402
    detect_subtitle_streams as _svc_detect_subtitle_streams,
    get_subtitle_detection as _svc_get_subtitle_detection,
    subtitle_cache_path as _svc_subtitle_cache_path,
)
from gateway.app.services.hot_follow_runtime_bridge import (  # noqa: E402
    compat_allow_subtitle_only_compose as _compat_allow_subtitle_only_compose,
    compat_hot_follow_compose_runtime as _compat_hot_follow_compose_runtime,
    compat_get_hot_follow_workbench_hub as _compat_get_hot_follow_workbench_hub,
    compat_hot_follow_dub_route_state as _compat_hot_follow_dub_route_state,
    compat_hot_follow_dual_channel_state as _compat_hot_follow_dual_channel_state,
    compat_hot_follow_no_dub_updates as _compat_hot_follow_no_dub_updates,
    compat_hot_follow_subtitle_lane_state as _compat_hot_follow_subtitle_lane_state,
    compat_hot_follow_target_lang_gate as _compat_hot_follow_target_lang_gate,
    compat_maybe_run_hot_follow_lipsync_stub as _compat_maybe_run_hot_follow_lipsync_stub,
    compat_resolve_target_srt_key as _compat_resolve_target_srt_key,
)
from gateway.app.services.compose_service import (  # noqa: E402
    CompositionService,
    HotFollowComposeRequestContract,
    HotFollowComposeResponseContract,
)
from gateway.app.services.task_view import (  # noqa: E402
    build_hot_follow_publish_hub as _build_hot_follow_publish_hub,
)


# _build_atempo_chain, _resolve_audio_fit_max_speed, _compute_audio_fit_speeds:
# moved to services/compose_helpers.py (Phase 1.3)


# _count_srt_cues, _build_translation_qa_summary, _build_workbench_debug_payload:
# moved to services/task_view_helpers.py (Phase 1.3)


# DubProviderRequest, PublishBackfillRequest: moved to core/constants.py (Phase 1.3)

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


# PublishBackfillRequest: moved to core/constants.py (Phase 1.3)

class ComposeTaskRequest(BaseModel):
    voiceover_url: str | None = None
    bgm_url: str | None = None
    bgm_mix: float | None = None
    overlay_subtitles: bool | None = None
    freeze_tail_enabled: bool | None = None
    force: bool = False


pages_router = APIRouter()
api_router = APIRouter(prefix="/api", tags=["tasks"])
# api_key_header: now imported from core/constants.py (Phase 1.3)


@pages_router.get("/favicon.ico", include_in_schema=False)
def favicon_noop():
    return Response(status_code=204)

# _coerce_datetime: moved to services/task_view_helpers.py (Phase 1.3)


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
    return _artifact_is_storage_key(value)


def _pack_path_for_list(task: dict) -> Optional[str]:
    return _artifact_pack_path_for_list(task, task_value=_task_value)


def _mm_edited_path(task_id: str) -> Path:
    return _artifact_mm_edited_path(task_id)


def _upload_target_subtitle_artifacts(task: dict, task_id: str, target_lang: str) -> tuple[str | None, str | None]:
    return _artifact_upload_target_subtitle_artifacts(
        task,
        task_id,
        target_lang,
        workspace_factory=Workspace,
        artifact_uploader=upload_task_artifact,
    )


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
    rows = _build_tasks_page_rows(
        db_tasks[:limit],
        kind_norm=kind_norm,
        pack_path_for_list=_pack_path_for_list,
        normalize_selected_tool_ids=_normalize_selected_tool_ids,
    )

    items = []
    for row in rows:
        item = derive_task_semantics(row)
        task_id = str(item.get("task_id") or "")
        download_kind = str(item.get("download_kind") or "").strip()
        item["pack_download_href"] = (
            _signed_op_url(task_id, download_kind) if task_id and download_kind else ""
        )
        items.append(item)

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
        return _build_not_ready_response(task, "subs_mm", ["mm_srt_path"])
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
        return _build_not_ready_response(task, "mm_txt", ["mm_srt_path"])
    txt_key = mm_key[:-4] + ".txt" if mm_key.endswith(".srt") else f"{mm_key}.txt"
    if not object_exists(txt_key):
        return _build_not_ready_response(task, "mm_txt", ["mm_txt_path"])
    return _text_or_redirect(txt_key, inline=inline)


def _resolve_audio_meta(task_id: str, repo) -> tuple[str, int, str]:
    return _svc_resolve_audio_meta(
        task_id,
        repo,
        task_value=_task_value,
        current_voiceover_asset_loader=_hf_current_voiceover_asset,
        settings_loader=get_settings,
        artifact_ready_assert=assert_artifact_ready,
        object_exists_fn=object_exists,
        object_head_fn=object_head,
    )


@pages_router.head("/v1/tasks/{task_id}/audio_mm")
def head_audio_mm(task_id: str, repo=Depends(get_task_repository)):
    return _build_stream_head_response(
        task_id,
        repo,
        resolve_meta=_resolve_audio_meta,
        logger=logger,
        event_name="AUDIO_STREAM",
        failure_log="audio_head_failed",
        failure_detail="audio head failed",
        default_content_type="audio/mpeg",
    )


@pages_router.get("/v1/tasks/{task_id}/audio_mm")
def download_audio_mm(task_id: str, request: Request, repo=Depends(get_task_repository)):
    return _build_stream_download_response(
        task_id,
        request,
        repo,
        resolve_meta=_resolve_audio_meta,
        parse_range=_parse_http_range,
        stream_object_range_loader=lambda key, start, end: stream_object_range(str(key), start=start, end=end),
        logger=logger,
        event_name="AUDIO_STREAM",
        resolve_failure_log="audio_get_failed",
        resolve_failure_detail="audio get failed",
        stream_failure_log="audio_stream_failed",
        stream_failure_detail="audio stream failed",
    )


def _resolve_final_meta(task_id: str, repo) -> tuple[str, int, str]:
    return _svc_resolve_final_meta(
        task_id,
        repo,
        task_value=_task_value,
        deliver_key_builder=deliver_key,
        object_exists_fn=object_exists,
        object_head_fn=object_head,
        media_meta_from_head_fn=media_meta_from_head,
    )


def _parse_http_range(range_header: str, total: int) -> tuple[int, int]:
    return _svc_parse_http_range(range_header, total)


@pages_router.head("/v1/tasks/{task_id}/final")
def head_final_video(task_id: str, repo=Depends(get_task_repository)):
    return _build_stream_head_response(
        task_id,
        repo,
        resolve_meta=_resolve_final_meta,
        logger=logger,
        event_name="FINAL_STREAM",
        failure_log="final_head_failed",
        failure_detail="final head failed",
        default_content_type="video/mp4",
    )


@pages_router.get("/v1/tasks/{task_id}/final")
def download_final_video(task_id: str, request: Request, repo=Depends(get_task_repository)):
    return _build_stream_download_response(
        task_id,
        request,
        repo,
        resolve_meta=_resolve_final_meta,
        parse_range=_parse_http_range,
        stream_object_range_loader=lambda key, start, end: stream_object_range(str(key), start=start, end=end),
        logger=logger,
        event_name="FINAL_STREAM",
        resolve_failure_log="final_get_failed",
        resolve_failure_detail="final get failed",
        stream_failure_log="final_stream_failed",
        stream_failure_detail="final stream failed",
    )


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
        return _build_not_ready_response(
            fresh,
            "pack",
            ["pack_key"],
            reason="repair_attempted",
            status_code=202,
            extra={"repair_attempted": True},
        )

    return _build_not_ready_response(task, "pack", ["pack_key"])


@pages_router.get("/v1/tasks/{task_id}/scenes")
def download_scenes(task_id: str, repo=Depends(get_task_repository)):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scenes not found")
    scenes_key = _task_value(task, "scenes_pack_key") or _task_value(task, "scenes_key")
    scenes_status = str(_task_value(task, "scenes_pack_status") or _task_value(task, "scenes_status") or "").lower()
    if scenes_status == "skipped":
        return _build_not_ready_response(task, "scenes", ["scenes_skipped"], reason="not_applicable")
    if scenes_status == "failed":
        return _build_not_ready_response(task, "scenes", ["scenes_failed"], reason="failed")
    if not scenes_key or not object_exists(str(scenes_key)):
        return _build_not_ready_response(task, "scenes", ["scenes_key"])
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
        return _build_not_ready_response(task, "publish_bundle", missing)
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
    return _build_task_publish_hub(
        task_id,
        repo,
        hot_follow_publish_hub_builder=_build_hot_follow_publish_hub,
        fallback_publish_payload_builder=_publish_hub_payload,
    )


@pages_router.get("/v1/tasks/{task_id}/status")
def task_status(task_id: str, repo=Depends(get_task_repository)):
    return _build_v1_task_status_payload(
        task_id,
        repo,
        task_key=_task_key,
        object_exists=object_exists,
    )





# _task_endpoint: moved to services/task_view_helpers.py (Phase 1.3)


# _get_op_access_key: moved to services/task_view_helpers.py (Phase 1.3)


# _op_gate_enabled: moved to services/task_view_helpers.py (Phase 1.3)


def _op_key_valid(request: Request) -> bool:
    return _op_key_valid_request(request)

def _op_key_valid_value(op_key: str | None) -> bool:
    return _service_op_key_valid_value(op_key)


def _require_op_key(request: Request) -> None:
    if not _op_key_valid(request):
        raise HTTPException(status_code=401, detail="OP key required")


# _op_sign: moved to services/task_view_helpers.py (Phase 1.3)


def _op_verify(task_id: str, kind: str, exp: int, sig: str) -> bool:
    secret = _get_op_access_key()
    if not secret:
        return True
    if not sig:
        return False
    expected = _op_sign(task_id, kind, exp)
    return hmac.compare_digest(expected, sig)


# _download_code: moved to services/task_view_helpers.py (Phase 1.3)


# _signed_op_url: moved to services/task_view_helpers.py (Phase 1.3)


# _read_mm_txt_from_task: moved to services/task_view_helpers.py (Phase 1.3)


# _publish_sop_markdown: moved to services/task_view_helpers.py (Phase 1.3)


# _build_copy_bundle: moved to services/task_view_helpers.py (Phase 1.3)


# _deliverable_url: moved to services/task_view_helpers.py (Phase 1.3)


# _compose_error_parts: moved to services/task_view_helpers.py (Phase 1.3)


# _compute_composed_state: moved to services/task_view_helpers.py (Phase 1.3)


# _scene_pack_info: moved to services/task_view_helpers.py (Phase 1.3)


# _compose_done_like: moved to services/task_view_helpers.py (Phase 1.3)


# _deliverables_final_url: moved to services/task_view_helpers.py (Phase 1.3)


# _resolve_hub_final_url: moved to services/task_view_helpers.py (Phase 1.3)


# _backfill_compose_done_if_final_ready: moved to services/task_view_helpers.py (Phase 1.3)


# _publish_hub_payload: moved to services/task_view_helpers.py (Phase 1.3)


# _task_value: moved to services/task_view_helpers.py (Phase 1.3)


# _task_key: moved to services/task_view_helpers.py (Phase 1.3)


# _scenes_status_from_ssot: moved to services/task_view_helpers.py (Phase 1.3)


# derive_status: moved to services/task_view_helpers.py (Phase 1.3)


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
    return _svc_subtitle_cache_path(task_id, task_base_dir_loader=task_base_dir)


def _detect_subtitle_streams(raw_file: Path) -> dict[str, Any]:
    return _svc_detect_subtitle_streams(
        raw_file,
        which=shutil.which,
        run=subprocess.run,
        json_loads=json.loads,
    )


def _get_subtitle_detection(task_id: str) -> dict[str, Any]:
    return _svc_get_subtitle_detection(
        task_id,
        cache_path_loader=_subtitle_cache_path,
        raw_path_loader=raw_path,
        detect_subtitle_streams_loader=_detect_subtitle_streams,
    )


# _resolve_download_urls: moved to services/task_view_helpers.py (Phase 1.3)

# _model_allowed_fields: moved to services/task_view_helpers.py (Phase 1.3)


# _normalize_selected_tool_ids: moved to services/task_view_helpers.py (Phase 1.3)

# _task_to_detail: moved to services/task_view_helpers.py (Phase 1.3)


# _extract_first_http_url: moved to services/task_view_helpers.py (Phase 1.3)


# _sha256_file: moved to services/media_helpers.py (Phase 1.3)


def _repo_upsert(repo, task_id: str, patch: dict) -> None:
    _policy_upsert(repo, task_id, patch)


def _repo_refresh_task(repo, task_id: str) -> Any:
    session = getattr(repo, "session", None)
    if session is not None:
        try:
            session.expire_all()
        except Exception:
            logger.warning("HF_REPO_REFRESH_FAIL task=%s", task_id)
    return repo.get(task_id)


# _build_hot_follow_voice_options: moved to services/voice_state.py (Phase 1.3)


# _resolve_hot_follow_requested_voice: moved to services/voice_state.py (Phase 1.3)


# _hot_follow_expected_provider: moved to services/voice_state.py (Phase 1.3)


# _voice_state_config: moved to services/voice_state.py (Phase 1.3)


# _resolve_hot_follow_provider_voice: moved to services/voice_state.py (Phase 1.3)


# _hf_persisted_audio_state: moved to services/voice_state.py (Phase 1.3)


# _hf_audio_matches_expected: moved to services/voice_state.py (Phase 1.3)


# _collect_voice_execution_state: moved to services/voice_state.py (Phase 1.3)


# _merge_probe_into_pipeline_config: moved to services/media_helpers.py (Phase 1.3)


# _update_pipeline_probe: moved to services/media_helpers.py (Phase 1.3)


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


def _is_local_ingest_task(task: dict) -> bool:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    if str(pipeline_config.get("ingest_mode") or "").strip().lower() == "local":
        return True
    if str(task.get("source_type") or "").strip().lower() == "local":
        return True
    return str(task.get("platform") or "").strip().lower() == "local"


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
    workspace = Workspace(task_id, target_lang=target_lang)

    current_step = "parse"
    try:
        _repo_upsert(repo, task_id, {**status_update, "last_step": current_step})
        raw_file = raw_path(task_id)
        parse_res = None
        raw_key = task.get("raw_path")
        local_ingest = _is_local_ingest_task(task)
        if not (local_ingest and (bool(raw_key) or raw_file.exists())):
            parse_req = ParseRequest(
                task_id=task_id,
                platform=task.get("platform"),
                link=task.get("source_url") or task.get("link") or "",
            )
            parse_res = asyncio.run(run_parse_step_v1(parse_req))
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
                "parse_status": "done" if raw_key else None,
                "parse_error": None,
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
        origin_key, mm_key = _upload_target_subtitle_artifacts(task, task_id, target_lang)
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
    ctx = _build_task_workbench_page_context(
        task,
        spec=spec,
        settings=app_settings,
        task_to_detail=_task_to_detail,
        resolve_download_urls=_resolve_download_urls,
        build_task_workbench_task_json=_build_task_workbench_task_json,
        build_task_workbench_view=_build_task_workbench_view,
        extract_first_http_url=_extract_first_http_url,
        features=get_features(),
    )
    return render_template(
        request=request,
        name=spec.template,
        ctx=ctx,
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
    allowed_kinds = {
        "raw",
        "pack",
        "scenes",
        "final_mp4",
        "origin_srt",
        "mm_srt",
        "mm_txt",
        "mm_audio",
        "publish_bundle",
    }
    if kind not in allowed_kinds:
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
    return _build_deliverable_download_redirect(task_id, task, kind)


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


# _probe_url_metadata: moved to services/media_helpers.py (Phase 1.3)


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


# _save_upload_to_paths: moved to services/media_helpers.py (Phase 1.3)


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


# _upload_task_bgm_impl: moved to services/media_helpers.py (Phase 1.3)

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
    summaries, total = _build_task_summaries_page(
        items,
        kind_norm=kind_norm,
        page=page,
        page_size=page_size,
        resolve_download_urls=_resolve_download_urls,
        derive_status=derive_status,
        extract_first_http_url=_extract_first_http_url,
        coerce_datetime=coerce_datetime,
        parse_pipeline_config=parse_pipeline_config,
        normalize_selected_tool_ids=_normalize_selected_tool_ids,
        task_summary_cls=TaskSummary,
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
    payload, log_extra = _build_task_status_payload(
        task_id,
        t,
        detail,
    )

    logger.info(
        "task_status_shape",
        extra=log_extra,
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
    return _build_task_publish_hub(
        task_id,
        repo,
        hot_follow_publish_hub_builder=_build_hot_follow_publish_hub,
        fallback_publish_payload_builder=_publish_hub_payload,
    )


def _execute_compose_task_contract(
    task_id: str,
    task: dict,
    request: HotFollowComposeRequestContract,
    *,
    repo,
    hub_loader,
    subtitle_resolver,
    subtitle_only_check,
    revision_snapshot=None,
    lipsync_runner=None,
) -> HotFollowComposeResponseContract:
    svc = CompositionService(storage=get_storage_service(), settings=get_settings())
    return svc.execute_hot_follow_compose_contract(
        task_id,
        task,
        request,
        repo=repo,
        hub_loader=hub_loader,
        subtitle_resolver=subtitle_resolver,
        subtitle_only_check=subtitle_only_check,
        revision_snapshot=revision_snapshot,
        lipsync_runner=lipsync_runner,
    )


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
    compose_runtime = _compat_hot_follow_compose_runtime(
        repo,
        hub_loader=_compat_get_hot_follow_workbench_hub,
        subtitle_resolver=_compat_resolve_target_srt_key,
        subtitle_only_check=_compat_allow_subtitle_only_compose,
        lipsync_runner=_compat_maybe_run_hot_follow_lipsync_stub,
    )
    result = _execute_compose_task_contract(
        task_id,
        task,
        request=HotFollowComposeRequestContract(
            bgm_mix=req.bgm_mix,
            overlay_subtitles=req.overlay_subtitles,
            freeze_tail_enabled=req.freeze_tail_enabled,
            force=req.force,
        ),
        repo=repo,
        hub_loader=compose_runtime["hub_loader"],
        subtitle_resolver=compose_runtime["subtitle_resolver"],
        subtitle_only_check=compose_runtime["subtitle_only_check"],
        lipsync_runner=compose_runtime["lipsync_runner"],
    )
    if result.status_code != 200:
        return JSONResponse(status_code=result.status_code, content=result.body)
    return result.body


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
                "parse_status": "done" if task.get("raw_path") else task.get("parse_status"),
                "parse_error": None,
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

    origin_key, mm_key = _upload_target_subtitle_artifacts(task, task_id, target_lang)

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
    mm_text_override = (payload.mm_text or "").strip() or None
    dub_route_state = _compat_hot_follow_dub_route_state(
        task_id,
        task,
        mm_text_override=mm_text_override,
        subtitle_lane_loader=_compat_hot_follow_subtitle_lane_state,
        dual_channel_loader=_compat_hot_follow_dual_channel_state,
    )
    subtitle_lane = dub_route_state["subtitle_lane"]
    route_state = dub_route_state["route_state"]
    no_dub_candidate = bool(dub_route_state["no_dub_candidate"])
    if no_dub_candidate:
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        no_dub_updates = _compat_hot_follow_no_dub_updates(route_state)
        pipeline_config.update(no_dub_updates["pipeline_config_updates"])
        _policy_upsert(
            repo,
            task_id,
            {
                "pipeline_config": pipeline_config_to_storage(pipeline_config),
                "last_step": no_dub_updates["last_step"],
                "dub_status": no_dub_updates["dub_status"],
                "dub_error": no_dub_updates["dub_error"],
                "compose_status": no_dub_updates["compose_status"],
            },
        )
        stored = repo.get(task_id) or task
        detail = _task_to_detail(stored)
        return DubResponse(
            **detail.dict(exclude={"mm_audio_key"}),
            resolved_voice_id=final_voice_id,
            resolved_edge_voice=None,
            audio_sha256=None,
            mm_audio_key=None,
        )
    dub_input_text = str(dub_route_state["dub_input_text"] or "").strip()
    target_subtitle_current = subtitle_lane.get("target_subtitle_current")
    subtitle_not_current = target_subtitle_current is False or (
        target_subtitle_current is None
        and "subtitle_ready" in subtitle_lane
        and not bool(subtitle_lane.get("subtitle_ready"))
    )
    if normalize_target_lang(target_lang) in {"my", "vi"} and subtitle_not_current:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": subtitle_lane.get("target_subtitle_current_reason") or "target_subtitle_not_current",
                "message": "当前目标字幕尚未成为真实当前版本，请先完成并保存目标字幕，再生成配音。",
                "target_lang": target_lang,
            },
        )
    target_lang_gate = _compat_hot_follow_target_lang_gate(dub_input_text, target_lang=target_lang)
    if not target_lang_gate.get("allow", True):
        raise HTTPException(
            status_code=422,
            detail={
                "reason": target_lang_gate.get("reason") or "target_lang_mismatch",
                "message": target_lang_gate.get("message"),
                "target_lang": target_lang,
            },
        )
    logger.info(
        "DUB3_TEXT_SOURCE",
        extra={
            "task_id": task_id,
            "step": "dub",
            "stage": "DUB3_TEXT_SOURCE",
            "text_source": "override" if mm_text_override else "workspace",
            "text_len": len(dub_input_text or ""),
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
    force_dub = bool(payload.force or (audio_present and voice_changed))

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
    config[_DRY_TTS_CONFIG_KEY] = None
    config["tts_voiceover_asset_role"] = None
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
            "dub_source_subtitles_content_hash": None,
            "dub_source_subtitle_updated_at": None,
            "dub_source_audio_fit_max_speed": None,
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

        dub_subtitle_snapshot = {
            "dub_source_subtitles_content_hash": str(task.get("subtitles_content_hash") or "").strip() or None,
            "dub_source_subtitle_updated_at": str(task.get("subtitles_override_updated_at") or "").strip() or None,
            "dub_source_audio_fit_max_speed": str(
                parse_pipeline_config(task.get("pipeline_config")).get("audio_fit_max_speed") or "1.25"
            ).strip()
            or "1.25",
        }

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

        task_after = _repo_refresh_task(repo, task_id) or {}
        existing_audio_key = task_after.get("mm_audio_key") or task_after.get("mm_audio_path")
        existing_audio_exists = bool(existing_audio_key and object_exists(str(existing_audio_key)))
        existing_audio_size = 0
        if existing_audio_key:
            head = object_head(str(existing_audio_key))
            existing_audio_size, _ = media_meta_from_head(head)
        persisted_audio = _hf_persisted_audio_state(task_id, task_after)
        persisted_provider = normalize_provider(task_after.get("mm_audio_provider") or provider)
        persisted_voice = str(task_after.get("mm_audio_voice_id") or "").strip() or None
        persisted_matches_expected, persisted_match_reason = _hf_audio_matches_expected(
            actual_provider=persisted_provider,
            expected_provider=provider,
            resolved_voice=persisted_voice,
            expected_resolved_voice=final_voice_id,
        )
        pipeline_config = parse_pipeline_config(task_after.get("pipeline_config"))
        no_dub_flag = pipeline_config.get("no_dub") == "true"
        no_dub_note = no_dub_flag and (task_base_dir(task_id) / "dub" / "no_dub.txt").exists()
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
            logger.info(
                "DUB3_OUTPUT_CHECK",
                extra={
                    "task_id": task_id,
                    "decision": "skipped",
                    "key": None,
                    "path": None,
                    "exists": False,
                    "size": 0,
                    "reason": "no_real_dry_tts",
                },
            )
            _policy_upsert(repo, 
                task_id,
                {
                    "mm_audio_path": None,
                    "mm_audio_key": None,
                    "mm_audio_provider": provider,
                    "mm_audio_voice_id": final_voice_id,
                    "mm_audio_bytes": None,
                    "mm_audio_duration_ms": None,
                    "mm_audio_mime": None,
                    "dub_provider": provider,
                    "last_step": "dubbing",
                    "voice_id": selected_voice_id,
                    "dub_status": "skipped",
                    "dub_error": None,
                    "audio_sha256": None,
                    "dub_generated_at": None,
                    "compose_status": "pending",
                    "compose_error": None,
                    "compose_error_reason": None,
                    "dub_source_subtitles_content_hash": None,
                    "dub_source_subtitle_updated_at": None,
                    "dub_source_audio_fit_max_speed": None,
                    "config": {
                        **config,
                        "tts_completed_token": None,
                        _DRY_TTS_CONFIG_KEY: None,
                        "tts_voiceover_asset_role": None,
                    },
                },
            )
            stored = _repo_refresh_task(repo, task_id)
            detail = _task_to_detail(stored)
            logger.info(
                "DUB3_DONE",
                extra={
                    "task_id": task_id,
                    "step": "dub",
                    "stage": "DUB3_DONE",
                    "uploaded_key": None,
                },
            )
            return DubResponse(
                **detail.dict(exclude={"mm_audio_key"}),
                resolved_voice_id=final_voice_id,
                resolved_edge_voice=edge_voice,
                audio_sha256=None,
                mm_audio_key=None,
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
            if persisted_audio.get("exists") and persisted_matches_expected:
                audio_key = str(persisted_audio.get("audio_key"))
                local_size = int(persisted_audio.get("size_bytes") or 0)
                local_duration_ms = task_after.get("mm_audio_duration_ms")
                local_duration = float(local_duration_ms or 0) / 1000.0 if local_duration_ms is not None else 0.0
                audio_sha256 = task_after.get("audio_sha256")
                logger.info(
                    "HF_DUB_ARTIFACT",
                    extra={
                        "task_id": task_id,
                        "requested_voice": selected_voice_id,
                        "resolved_voice": final_voice_id,
                        "provider": provider,
                        "fresh_artifact_persisted": True,
                        "audio_key": audio_key,
                    },
                )
                _policy_upsert(
                    repo,
                    task_id,
                    {
                        "mm_audio_path": audio_key,
                        "mm_audio_key": audio_key,
                        "mm_audio_provider": provider,
                        "mm_audio_voice_id": final_voice_id,
                        "mm_audio_bytes": local_size or None,
                        "mm_audio_duration_ms": int(local_duration * 1000) if local_duration > 0 else local_duration_ms,
                        "mm_audio_mime": "audio/mpeg",
                        "dub_provider": provider,
                        "last_step": "dubbing",
                        "voice_id": selected_voice_id,
                        "dub_status": "ready",
                        "dub_error": None,
                        "audio_sha256": audio_sha256,
                        "dub_generated_at": datetime.now(timezone.utc).isoformat(),
                        "compose_status": "pending",
                        "compose_error": None,
                        "compose_error_reason": None,
                        **dub_subtitle_snapshot,
                        "config": {
                            **dict(task_after.get("config") or config),
                            "tts_completed_token": request_token,
                            _DRY_TTS_CONFIG_KEY: audio_key,
                            "tts_voiceover_asset_role": _DRY_TTS_ROLE,
                        },
                    },
                )
                stored = _repo_refresh_task(repo, task_id)
                detail = _task_to_detail(stored)
                return DubResponse(
                    **detail.dict(exclude={"mm_audio_key"}),
                    resolved_voice_id=final_voice_id,
                    resolved_edge_voice=edge_voice,
                    audio_sha256=audio_sha256,
                    mm_audio_key=audio_key,
                )
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
            if existing_audio_key:
                logger.warning(
                    "HF_STALE_AUDIO_REJECT",
                    extra={
                        "task_id": task_id,
                        "requested_voice": selected_voice_id,
                        "resolved_voice": final_voice_id,
                        "provider": provider,
                        "persisted_provider": persisted_provider,
                        "persisted_voice": persisted_voice,
                        "reason": persisted_match_reason,
                        "audio_key": existing_audio_key,
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
                    "mm_audio_key": None,
                    "mm_audio_path": None,
                    "mm_audio_provider": None,
                    "mm_audio_voice_id": None,
                    "audio_sha256": None,
                    "dub_source_subtitles_content_hash": None,
                    "dub_source_subtitle_updated_at": None,
                    "dub_source_audio_fit_max_speed": None,
                },
            )
            stored = _repo_refresh_task(repo, task_id)
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
            if existing_audio_key:
                logger.warning(
                    "HF_STALE_AUDIO_REJECT",
                    extra={
                        "task_id": task_id,
                        "requested_voice": selected_voice_id,
                        "resolved_voice": final_voice_id,
                        "provider": provider,
                        "persisted_provider": persisted_provider,
                        "persisted_voice": persisted_voice,
                        "reason": persisted_match_reason,
                        "audio_key": existing_audio_key,
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
                    "mm_audio_key": None,
                    "mm_audio_path": None,
                    "mm_audio_provider": None,
                    "mm_audio_voice_id": None,
                    "audio_sha256": None,
                    "dub_source_subtitles_content_hash": None,
                    "dub_source_subtitle_updated_at": None,
                    "dub_source_audio_fit_max_speed": None,
                },
            )
            stored = _repo_refresh_task(repo, task_id)
            detail = _task_to_detail(stored)
            return DubResponse(
                **detail.dict(exclude={"mm_audio_key"}),
                resolved_voice_id=final_voice_id,
                resolved_edge_voice=edge_voice,
                audio_sha256=task_after.get("audio_sha256"),
                mm_audio_key=task_after.get("mm_audio_key") or task_after.get("mm_audio_path"),
            )
        audio_key = deliver_key(task_id, "voiceover/audio_mm.dry.mp3")
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
        logger.info(
            "HF_DUB_ARTIFACT",
            extra={
                "task_id": task_id,
                "requested_voice": selected_voice_id,
                "resolved_voice": final_voice_id,
                "provider": provider,
                "fresh_artifact_persisted": True,
                "audio_key": audio_key,
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
            "compose_status": "pending",
            "compose_error": None,
            "compose_error_reason": None,
            **dub_subtitle_snapshot,
            "config": {
                **config,
                "tts_completed_token": request_token,
                _DRY_TTS_CONFIG_KEY: audio_key,
                "tts_voiceover_asset_role": _DRY_TTS_ROLE,
            },
        },
    )

    stored = _repo_refresh_task(repo, task_id)
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
    except Exception as exc:
        try:
            _policy_upsert(repo, task_id, {"dub_status": "failed", "dub_error": str(exc)})
        except Exception:
            logger.exception("DUB3_FAIL_STATUS_UPDATE_FAILED", extra={"task_id": task_id})
        logger.exception("DUB3_FAIL", extra={"task_id": task_id, "step": "dub", "phase": "exception"})


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


register_task_router_action_ports(
    TaskRouterActionPorts(
        create_task=lambda payload, background_tasks, repo: create_task(
            payload,
            background_tasks=background_tasks,
            repo=repo,
        ),
        run_task_pipeline=lambda task_id, background_tasks, repo: run_task_pipeline(
            task_id,
            background_tasks=background_tasks,
            repo=repo,
        ),
        rerun_dub=lambda task_id, payload, background_tasks, repo: rerun_dub(
            task_id,
            payload=payload,
            background_tasks=background_tasks,
            repo=repo,
        ),
    )
)


__all__ = ["api_router", "pages_router", "router"]
