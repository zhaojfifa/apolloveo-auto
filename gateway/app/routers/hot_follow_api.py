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
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import get_settings
from ..schemas import DubResponse, TaskCreate, TaskDetail

from gateway.app.deps import get_task_repository
from gateway.app.ports.storage_provider import get_storage_service
from gateway.ports.repository import ITaskRepository
from gateway.app.services.status_policy.service import policy_upsert
from gateway.app.services.source_audio_policy import normalize_source_audio_policy, source_audio_policy_from_task
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang, public_target_lang, resolve_tts_voice
from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
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
    DubProviderRequest,
    OP_HEADER_KEY,
    PublishBackfillRequest,
    api_key_header,
)
from gateway.app.services.compose_helpers import (
    build_atempo_chain as _build_atempo_chain,
    compute_audio_fit_speeds as _compute_audio_fit_speeds,
    resolve_audio_fit_max_speed as _resolve_audio_fit_max_speed,
)
from gateway.app.services.media_helpers import (
    merge_probe_into_pipeline_config as _merge_probe_into_pipeline_config,
    probe_url_metadata as _probe_url_metadata,
    save_upload_to_paths as _save_upload_to_paths,
    sha256_file as _sha256_file,
    update_pipeline_probe as _update_pipeline_probe,
    upload_task_bgm_impl as _upload_task_bgm_impl,
)
from gateway.app.services.hot_follow_media_policy import (
    hot_follow_local_upload_source_selection_guard,
    hot_follow_media_input_policy,
)
from gateway.app.services.hot_follow_flow_actions import (
    LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW,
    MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
    TargetSubtitleMaterializationFailure,
    local_preserve_to_subtitle_dub_flow,
    materialize_target_subtitle_from_origin,
)
from gateway.app.services.hot_follow_translation_pending import hot_follow_translation_waiting_diagnostic
from gateway.app.services.task_view_helpers import (
    backfill_compose_done_if_final_ready as _backfill_compose_done_if_final_ready,
    build_translation_qa_summary as _build_translation_qa_summary,
    build_workbench_debug_payload as _build_workbench_debug_payload,
    compose_error_parts as _compose_error_parts,
    compute_composed_state as _compute_composed_state,
    count_srt_cues as _count_srt_cues,
    deliverable_url as _deliverable_url,
    scene_pack_info as _scene_pack_info,
    scenes_status_from_ssot as _scenes_status_from_ssot,
    signed_op_url as _signed_op_url,
    task_endpoint as _task_endpoint,
    task_key as _task_key,
    task_to_detail as _task_to_detail,
    task_value as _task_value,
)
from gateway.app.services.voice_state import (
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
from gateway.app.services.task_router_actions import (
    create_task_entry as _create_task_entry,
    rerun_dub_entry as _rerun_dub_entry,
    run_task_pipeline_entry as _run_task_pipeline_entry,
)
from gateway.app.task_repo_utils import normalize_task_payload
from gateway.app.services.compose_service import (
    ComposeResult,
    CompositionService,
    HotFollowComposeRequestContract,
    HotFollowComposeResponseContract,
    subtitle_render_signature,
)
from gateway.app.services.hot_follow_language_profiles import (
    get_hot_follow_language_profile,
    hot_follow_internal_lang,
    hot_follow_subtitle_filename,
    hot_follow_subtitle_txt_filename,
    resolve_hot_follow_voice_id,
)
from gateway.app.services.hot_follow_subtitle_currentness import (
    compute_hot_follow_target_subtitle_currentness,
    has_semantic_target_subtitle_text,
)
from gateway.app.services.hot_follow_helper_translation import helper_translate_lane_state
from gateway.app.services.hot_follow_subtitle_authority import (
    helper_translation_telemetry_updates,
    persist_hot_follow_authoritative_target_subtitle,
)
from gateway.app.services.hot_follow_helper_translation import (
    helper_translate_failure_updates,
    helper_translate_success_updates,
    sanitize_helper_translate_error,
)
from gateway.app.services.subtitle_helpers import (
    hf_dual_channel_state as _svc_hf_dual_channel_state,
    hf_done_like as _svc_hf_done_like,
    hf_parse_artifact_ready as _svc_hf_parse_artifact_ready,
    hf_state_from_status as _svc_hf_state_from_status,
    hf_subtitle_lane_state as _svc_hf_subtitle_lane_state,
)
from gateway.app.services.task_view import (
    build_hot_follow_publish_hub as _svc_build_hot_follow_publish_hub,
    build_hot_follow_workbench_hub as _svc_build_hot_follow_workbench_hub,
    collect_hot_follow_workbench_ui as _svc_collect_hot_follow_workbench_ui,
    hf_artifact_facts as _svc_hf_artifact_facts,
    hf_current_attempt_summary as _svc_hf_current_attempt_summary,
    hf_deliverables as _svc_hf_deliverables,
    hf_operator_summary as _svc_hf_operator_summary,
    hf_pipeline_state as _svc_hf_pipeline_state,
    hf_rerun_presentation_state as _svc_hf_rerun_presentation_state,
    hf_safe_presentation_aggregates as _svc_hf_safe_presentation_aggregates,
    hf_task_status_shape as _svc_hf_task_status_shape,
    hot_follow_operational_defaults as _svc_hot_follow_operational_defaults,
    safe_collect_hot_follow_workbench_ui as _svc_safe_collect_hot_follow_workbench_ui,
)
from gateway.app.services.voice_service import (
    hf_source_audio_semantics,
    maybe_run_hot_follow_lipsync_stub as _svc_maybe_run_hot_follow_lipsync_stub,
)


def _policy_upsert(repo, task_id, updates, *, task=None, step="router.hf_api", force=False):
    """Thin wrapper matching the old tasks.py signature."""
    return policy_upsert(repo, task_id, task, updates, step=step, force=force)


# Endpoint functions that remain in tasks.py are reached via
# gateway.app.services.task_router_actions, not direct router imports.


logger = logging.getLogger(__name__)

_HELPER_TRANSLATE_LOCKS_GUARD = threading.Lock()
_HELPER_TRANSLATE_LOCKS: dict[str, threading.Lock] = {}

hot_follow_api_router = APIRouter(prefix="/api", tags=["hot-follow"])


class HotFollowAudioConfigRequest(BaseModel):
    tts_engine: str | None = None
    tts_voice: str | None = None
    bgm_mix: float | None = None
    audio_fit_max_speed: float | None = None


class HotFollowSourceUrlPatchRequest(BaseModel):
    source_url: str = ""



class HotFollowSubtitlesRequest(BaseModel):
    srt_text: str = ""



class HotFollowTranslateRequest(BaseModel):
    text: str = ""
    target_lang: str = "my"
    input_source: str = "helper_only_text"



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


class HotFollowMaterializeTargetSubtitleRequest(BaseModel):
    expected_origin_key: str | None = None


class HotFollowLocalPreserveToSubtitleDubRequest(BaseModel):
    reason: str | None = None


def _hf_helper_translate_request_fingerprint(
    *,
    task_id: str,
    source_text: str,
    target_lang: str,
    input_source: str,
) -> str:
    digest = hashlib.sha256(
        f"{task_id}\n{input_source}\n{target_lang}\n{str(source_text or '').strip()}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{task_id}:{input_source}:{target_lang}:{digest}"


def _hf_helper_translate_request_lock(fingerprint: str) -> threading.Lock:
    with _HELPER_TRANSLATE_LOCKS_GUARD:
        lock = _HELPER_TRANSLATE_LOCKS.get(fingerprint)
        if lock is None:
            lock = threading.Lock()
            _HELPER_TRANSLATE_LOCKS[fingerprint] = lock
        return lock


def _hf_helper_repeat_success_payload(
    *,
    task_id: str,
    task: dict[str, Any],
    target_lang: str,
    source_text: str,
) -> dict[str, Any] | None:
    if not (
        bool(task.get("target_subtitle_current"))
        and bool(task.get("target_subtitle_authoritative_source"))
        and str(task.get("subtitle_helper_input_text") or "").strip() == str(source_text or "").strip()
        and str(task.get("subtitle_helper_target_lang") or "").strip() == str(target_lang or "").strip()
        and str(task.get("subtitle_helper_translated_text") or "").strip()
    ):
        return None
    helper_lane = helper_translate_lane_state(
        task,
        translation_waiting=False,
        helper_source_text=source_text,
        helper_output_consumed=True,
    )
    result = (
        "resolved_with_warning"
        if helper_lane.get("composite_state") == "helper_resolved_with_retryable_provider_warning"
        else "already_current"
    )
    return {
        "task_id": task_id,
        "target_lang": public_target_lang(target_lang),
        "input_source": "helper_only_text",
        "persisted": False,
        "result": result,
        "single_flight": "noop_cached",
        "translated_text": task.get("subtitle_helper_translated_text"),
        "helper_translation": {
            "status": helper_lane.get("status"),
            "output_state": helper_lane.get("output_state"),
            "provider_health": helper_lane.get("provider_health"),
            "composite_state": helper_lane.get("composite_state"),
            "warning_only": bool(helper_lane.get("warning_only")),
            "failed": bool(helper_lane.get("failed")),
            "reason": helper_lane.get("reason"),
            "message": helper_lane.get("message"),
        },
    }




def _hf_compose_revision_snapshot(task: dict) -> dict[str, str | None]:
    compose_plan = dict(task.get("compose_plan") or {})
    return {
        "subtitle_updated_at": str(task.get("subtitles_override_updated_at") or "").strip() or None,
        "subtitle_content_hash": str(task.get("subtitles_content_hash") or "").strip() or None,
        "audio_sha256": str(task.get("audio_sha256") or "").strip() or None,
        "source_audio_policy": source_audio_policy_from_task(task),
        "render_signature": subtitle_render_signature(
            target_lang=compose_plan.get("target_lang") or task.get("target_lang") or task.get("content_lang"),
            cleanup_mode=compose_plan.get("cleanup_mode"),
        ),
    }


def _maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    return _svc_maybe_run_hot_follow_lipsync_stub(task_id, enabled=enabled)


def _execute_hot_follow_compose_contract(
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



def _hf_is_srt_text(text: str) -> bool:
    source = str(text or "").strip()
    if not source or "-->" not in source:
        return False
    try:
        segments = _parse_srt_to_segments(source)
    except Exception:
        return False
    return bool(segments)



def _hf_plain_text_to_single_srt(text: str, *, duration_sec: float | None) -> str:
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
    seg = {
        "index": 1,
        "start": 0.0,
        "end": dur,
        "mm": content,
        "origin": content,
    }
    return segments_to_srt([seg], "mm")


def _hf_normalize_subtitles_save_text(task: dict, raw_text: str) -> tuple[str, str]:
    text = str(raw_text or "").strip()
    if not text:
        return "", "empty"
    if _hf_is_srt_text(text):
        return text + ("\n" if not text.endswith("\n") else ""), "srt"
    return _hf_plain_text_to_single_srt(text, duration_sec=task.get("duration_sec")) + "\n", "plain_text_wrapped"


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


def _hf_save_authoritative_target_subtitle(
    task_id: str,
    task: dict,
    *,
    text: str,
    text_mode: str,
    repo,
) -> dict:
    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    return persist_hot_follow_authoritative_target_subtitle(
        task_id,
        task,
        repo=repo,
        text=text,
        text_mode=text_mode,
        target_lang=target_lang,
        source_texts=(
            _hf_load_normalized_source_text(task_id, task),
            _hf_load_origin_subtitles_text(task),
        ),
        expected_subtitle_source=_hf_expected_subtitle_filename(target_lang),
        persist_artifact_fn=lambda saved_text: _hf_sync_saved_target_subtitle_artifact(task_id, task, saved_text),
        write_override_fn=lambda saved_text: _hf_subtitles_override_path(task_id).parent.mkdir(parents=True, exist_ok=True)
        or _hf_subtitles_override_path(task_id).write_text(saved_text, encoding="utf-8"),
        content_hash_fn=_hf_subtitle_content_hash,
        extra_updates=_hf_empty_dub_recovery_updates(
            task_id,
            task,
            text,
            {},
        ),
        resolve_helper_state=bool(str(text or "").strip()),
    )


def _hf_authoritative_target_subtitle_current(task_id: str, task: dict) -> bool:
    if bool(task.get("target_subtitle_current")):
        return True
    try:
        lane = _hf_subtitle_lane_state(task_id, task)
    except Exception:
        return False
    return bool(lane.get("target_subtitle_current"))


def _hf_source_subtitle_translation_failure_updates(
    task_id: str,
    task: dict,
    *,
    detail: dict,
    source_text: str,
    target_lang: str,
) -> dict:
    return helper_translation_telemetry_updates(
        task_id,
        task,
        helper_updates=helper_translate_failure_updates(
            detail,
            input_text=source_text,
            target_lang=target_lang,
        ),
    )


def _hf_translate_source_subtitle_lane(task_id: str, task: dict, *, target_lang: str, repo) -> tuple[str, dict]:
    normalized_source_text = _hf_load_normalized_source_text(task_id, task).strip()
    origin_source_text = _hf_load_origin_subtitles_text(task).strip()
    source_text = normalized_source_text if "-->" in normalized_source_text else origin_source_text
    if not source_text:
        raise HTTPException(
            status_code=400,
            detail={
                "reason": "source_subtitle_lane_empty",
                "message": "来源字幕为空，无法执行完整字幕翻译。",
            },
        )
    if "-->" not in source_text:
        raise HTTPException(
            status_code=400,
            detail={
                "reason": "source_subtitle_lane_not_srt",
                "message": "来源字幕不是 SRT，无法保留时间轴执行完整字幕翻译。",
            },
        )
    segments = _parse_srt_to_segments(source_text)
    if not segments:
        raise HTTPException(
            status_code=400,
            detail={
                "reason": "source_subtitle_lane_invalid_srt",
                "message": "来源字幕 SRT 无法解析，未写入目标字幕。",
            },
        )
    try:
        translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
    except GeminiSubtitlesError as exc:
        detail = sanitize_helper_translate_error(exc)
        _policy_upsert(
            repo,
            task_id,
            _hf_source_subtitle_translation_failure_updates(
                task_id,
                task,
                detail=detail,
                source_text=source_text,
                target_lang=target_lang,
            ),
        )
        raise
    for seg in segments:
        idx = int(seg.get("index") or 0)
        seg[target_lang] = str(translations.get(idx) or seg.get("origin") or "").strip()
    translated_text = segments_to_srt(segments, target_lang)
    try:
        saved_task = materialize_target_subtitle_from_origin(
            task_id,
            task,
            repo=repo,
            origin_text=source_text,
            target_lang=target_lang,
            expected_origin_key=task.get("origin_srt_path"),
            expected_subtitle_source=_hf_expected_subtitle_filename(target_lang),
            translate_origin_srt_fn=lambda _origin_text, _target_lang: translated_text,
            persist_artifact_fn=lambda saved_text: _hf_sync_saved_target_subtitle_artifact(task_id, task, saved_text),
            write_override_fn=lambda saved_text: _hf_subtitles_override_path(task_id).parent.mkdir(parents=True, exist_ok=True)
            or _hf_subtitles_override_path(task_id).write_text(saved_text, encoding="utf-8"),
            content_hash_fn=_hf_subtitle_content_hash,
        )
    except TargetSubtitleMaterializationFailure as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
                "reason": exc.code,
                "message": exc.message,
            },
        ) from exc
    return translated_text, saved_task

def _hf_state_from_status(value: Any) -> str:
    return _svc_hf_state_from_status(value)


def _hf_done_like(value: Any) -> bool:
    return _svc_hf_done_like(value)


def _hf_parse_artifact_ready(task: dict) -> bool:
    return _svc_hf_parse_artifact_ready(task)


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
    provider = normalize_provider(
        voice_state.get("expected_provider") or task.get("dub_provider") or getattr(settings, "dub_provider", None)
    )
    semantics = hf_source_audio_semantics(task, voice_state)
    preview_url = (
        str(voice_state.get("voiceover_url") or "").strip()
        or str(semantics.get("tts_voiceover_url") or semantics.get("dub_preview_url") or "").strip()
        or None
    )
    return {
        "tts_engine": _hf_engine_public(provider),
        "tts_voice": voice_state.get("resolved_voice"),
        "requested_voice": voice_state.get("requested_voice"),
        "bgm_key": bgm.get("bgm_key"),
        "bgm_mix": max(0.0, min(1.0, mix_val)),
        "bgm_url": get_download_url(str(bgm.get("bgm_key"))) if bgm.get("bgm_key") else None,
        **semantics,
        "voiceover_url": preview_url,
        "audio_url": preview_url,
        "audio_fit_max_speed": audio_fit_max_speed,
    }


def _hf_subtitles_override_path(task_id: str) -> Path:
    return task_base_dir(task_id) / "subtitles" / "subtitles_override.srt"


def _hf_read_text_file(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _hf_local_target_subtitle_path(task_id: str, target_lang: str | None) -> Path | None:
    try:
        workspace = Workspace(task_id, target_lang=hot_follow_internal_lang(target_lang or "mm"))
        return workspace.mm_srt_path
    except Exception:
        return None


def _hf_local_origin_subtitle_path(task_id: str) -> Path | None:
    try:
        workspace = Workspace(task_id)
        return workspace.origin_srt_path
    except Exception:
        return None


def _hf_expected_subtitle_filename(target_lang: str | None) -> str:
    return hot_follow_subtitle_filename(target_lang or "mm")


def _hf_task_target_subtitle_key(task: dict, target_lang: str | None) -> str | None:
    expected_name = _hf_expected_subtitle_filename(target_lang)
    lang_norm = hot_follow_internal_lang(target_lang)
    candidates = [
        _task_key(task, f"{lang_norm}_srt_path"),
        _task_key(task, "mm_srt_path"),
    ]
    for key in candidates:
        if key and Path(str(key)).name == expected_name:
            return str(key)
    return None


def _hf_subtitle_content_hash(text: str | None) -> str | None:
    source = "" if text is None else str(text)
    if not source:
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def _hf_sync_saved_target_subtitle_artifact(task_id: str, task: dict, saved_text: str | None = None) -> str | None:
    text = str(saved_text if saved_text is not None else _hf_load_subtitles_text(task_id, task) or "")
    if not has_semantic_target_subtitle_text(text):
        return None
    desired_hash = _hf_subtitle_content_hash(text)
    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    current_key = _hf_task_target_subtitle_key(task, target_lang) or _task_key(task, "mm_srt_path")
    subtitle_filename = hot_follow_subtitle_filename(target_lang)
    subtitle_txt_filename = hot_follow_subtitle_txt_filename(target_lang)
    if current_key and object_exists(str(current_key)):
        head = object_head(str(current_key))
        size, _ = media_meta_from_head(head)
        if int(size or 0) > 0:
            current_bytes = get_object_bytes(str(current_key))
            current_text = None
            if current_bytes:
                try:
                    current_text = current_bytes.decode("utf-8")
                except Exception:
                    current_text = current_bytes.decode("utf-8", errors="ignore")
            current_hash = _hf_subtitle_content_hash(current_text)
            if desired_hash and current_hash == desired_hash:
                return str(current_key)
    if not text.strip():
        return str(current_key) if current_key else None

    workspace = Workspace(task_id, target_lang=target_lang)
    workspace.mm_srt_path.parent.mkdir(parents=True, exist_ok=True)
    workspace.mm_srt_path.write_text(text, encoding="utf-8")
    synced_key = upload_task_artifact(task, workspace.mm_srt_path, subtitle_filename, task_id=task_id)
    mm_txt_text = _srt_to_txt(text).strip()
    if mm_txt_text:
        mm_txt_path = workspace.mm_srt_path.with_suffix(".txt")
        mm_txt_path.write_text(mm_txt_text + "\n", encoding="utf-8")
        upload_task_artifact(task, mm_txt_path, subtitle_txt_filename, task_id=task_id)
    if synced_key and isinstance(task, dict):
        task["mm_srt_path"] = synced_key
    return str(synced_key) if synced_key else (str(current_key) if current_key else None)


def _hf_remove_no_dub_note(task_id: str) -> None:
    try:
        note_path = task_base_dir(task_id) / "dub" / "no_dub.txt"
        if note_path.exists():
            note_path.unlink()
    except Exception:
        logger.warning("HF_NO_DUB_NOTE_CLEAR_FAIL task=%s", task_id)


def _hf_empty_dub_recovery_updates(task_id: str, task: dict, text: str, target_currentness: dict[str, Any]) -> dict[str, Any]:
    _ = target_currentness
    if not str(text or "").strip():
        return {}
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip().lower()
    if reason not in {"target_subtitle_empty", "dub_input_empty"}:
        return {}
    pipeline_config.pop("no_dub", None)
    pipeline_config.pop("dub_skip_reason", None)
    updates: dict[str, Any] = {
        "pipeline_config": pipeline_config_to_storage(pipeline_config),
        "dub_skip_reason": None,
    }
    if str(task.get("dub_status") or "").strip().lower() == "skipped":
        updates["dub_status"] = "pending"
    _hf_remove_no_dub_note(task_id)
    return updates


def _hf_load_subtitles_text(task_id: str, task: dict) -> str:
    override_path = _hf_subtitles_override_path(task_id)
    if override_path.exists():
        return _hf_read_text_file(override_path)

    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    mm_key = _hf_task_target_subtitle_key(task, target_lang) or _task_key(task, "mm_srt_path")
    if mm_key and object_exists(mm_key):
        data = get_object_bytes(mm_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    local_target_path = _hf_local_target_subtitle_path(task_id, target_lang)
    local_text = _hf_read_text_file(local_target_path)
    if local_text:
        return local_text
    return ""


def _hf_load_origin_subtitles_text(task: dict) -> str:
    task_id = str(task.get("task_id") or task.get("id") or "")
    origin_key = _task_key(task, "origin_srt_path")
    if origin_key and object_exists(origin_key):
        data = get_object_bytes(origin_key)
        if data:
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("utf-8", errors="ignore")
    if task_id:
        local_origin_path = _hf_local_origin_subtitle_path(task_id)
        local_text = _hf_read_text_file(local_origin_path)
        if local_text:
            return local_text
    return ""


def _hf_target_subtitle_currentness_state(
    task: dict,
    *,
    target_lang: str,
    raw_source_text: str,
    normalized_source_text: str,
    edited_text: str,
    subtitle_artifact_exists: bool,
    expected_key: str | None,
) -> dict[str, object]:
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    return compute_hot_follow_target_subtitle_currentness(
        target_lang=target_lang,
        target_text=edited_text,
        source_texts=(normalized_source_text, raw_source_text),
        subtitle_artifact_exists=subtitle_artifact_exists,
        expected_subtitle_source=_hf_expected_subtitle_filename(target_lang),
        actual_subtitle_source=(Path(str(expected_key)).name if expected_key else None),
        translation_incomplete=str(pipeline_config.get("translation_incomplete") or "").strip().lower() == "true",
        has_saved_revision=bool(
            str(task.get("subtitles_content_hash") or "").strip()
            or str(task.get("subtitles_override_updated_at") or "").strip()
        ),
    )


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
    if has_semantic_target_subtitle_text(edited):
        return edited
    return ""


def _hf_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    return _svc_hf_subtitle_lane_state(task_id, task)


def _hf_dual_channel_state(task_id: str, task: dict, subtitle_lane: dict[str, Any] | None = None, *, subtitles_step_done: bool = True) -> dict[str, Any]:
    return _svc_hf_dual_channel_state(
        task_id,
        task,
        subtitle_lane,
        subtitles_step_done=subtitles_step_done,
    )


def _hf_source_audio_lane_summary(task: dict, route_state: dict[str, Any] | None = None) -> dict[str, Any]:
    route = route_state or {}
    source_audio_policy = source_audio_policy_from_task(task)
    content_mode = str(route.get("content_mode") or "").strip().lower()
    speech_detected = bool(route.get("speech_detected"))
    title_hint = str(task.get("title") or "").strip().lower()
    has_bgm_hint = any(token in title_hint for token in ("bgm", "音乐", "配乐", "商品", "展示"))

    if content_mode == "silent_candidate":
        return {
            "source_audio_lane": "silent_candidate",
            "source_audio_lane_reason": "未检测到稳定人声，建议优先字幕驱动。",
            "source_audio_policy": source_audio_policy,
            "speech_presence": "none",
            "bgm_presence": "possible" if has_bgm_hint else "unknown",
            "audio_mix_mode": "silent_or_fx",
        }
    if content_mode == "subtitle_led":
        return {
            "source_audio_lane": "music_or_text_led",
            "source_audio_lane_reason": "画面文字线索更强，当前素材更像字幕或画面驱动。",
            "source_audio_policy": source_audio_policy,
            "speech_presence": "low",
            "bgm_presence": "possible",
            "audio_mix_mode": "text_led",
        }
    if speech_detected and has_bgm_hint:
        return {
            "source_audio_lane": "mixed_audio",
            "source_audio_lane_reason": "检测到人声，同时素材特征显示可能带明显配乐。",
            "source_audio_policy": source_audio_policy,
            "speech_presence": "high",
            "bgm_presence": "possible",
            "audio_mix_mode": "speech_plus_bgm",
        }
    if speech_detected:
        return {
            "source_audio_lane": "speech_primary",
            "source_audio_lane_reason": "检测到稳定人声，适合标准配音替换路径。",
            "source_audio_policy": source_audio_policy,
            "speech_presence": "high",
            "bgm_presence": "low",
            "audio_mix_mode": "speech_primary",
        }
    return {
        "source_audio_lane": "unknown",
        "source_audio_lane_reason": "当前音频结构信息不足，建议先检查来源字幕和原视频。",
        "source_audio_policy": source_audio_policy,
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
    return _svc_hot_follow_operational_defaults()


def _collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    return _svc_collect_hot_follow_workbench_ui(
        task,
        settings,
        subtitle_lane_loader=_hf_subtitle_lane_state,
        pipeline_state_loader=_hf_pipeline_state,
        dual_channel_state_loader=_hf_dual_channel_state,
        source_audio_lane_loader=_hf_source_audio_lane_summary,
        screen_text_candidate_loader=_hf_screen_text_candidate_summary,
        voice_execution_state_loader=_collect_voice_execution_state,
        object_exists_fn=object_exists,
        source_audio_semantics_loader=hf_source_audio_semantics,
    )


def _safe_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    return _svc_safe_collect_hot_follow_workbench_ui(
        task,
        settings,
        workbench_ui_loader=_collect_hot_follow_workbench_ui,
        voice_options_builder=_build_hot_follow_voice_options,
    )


def _hf_pipeline_state(
    task: dict,
    step: str,
    *,
    composed: dict[str, Any] | None = None,
    subtitle_lane: dict[str, Any] | None = None,
) -> tuple[str, str]:
    return _svc_hf_pipeline_state(
        task,
        step,
        composed=composed,
        subtitle_lane=subtitle_lane,
        parse_artifact_ready_loader=_hf_parse_artifact_ready,
        voice_execution_state_loader=_collect_voice_execution_state,
        audio_config_loader=_hf_audio_config,
        settings=get_settings(),
    )


def _hf_deliverables(task_id: str, task: dict) -> list[dict[str, Any]]:
    return _svc_hf_deliverables(
        task_id,
        task,
        subtitle_lane_loader=_hf_subtitle_lane_state,
        current_voiceover_asset_loader=_hf_current_voiceover_asset,
        object_exists_fn=object_exists,
        task_endpoint_loader=_task_endpoint,
        signed_op_url_loader=_signed_op_url,
        download_url_loader=get_download_url,
        settings=get_settings(),
    )


def _hf_task_status_shape(task: dict) -> dict[str, str]:
    return _svc_hf_task_status_shape(task, pipeline_state_loader=_hf_pipeline_state)


def _hf_rerun_presentation_state(
    task: dict,
    voice_state: dict[str, Any] | None,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    dub_status: str | None,
    current_attempt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _svc_hf_rerun_presentation_state(
        task,
        voice_state,
        final_info,
        historical_final,
        dub_status,
        current_attempt=current_attempt,
    )


def _hf_artifact_facts(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
) -> dict[str, Any]:
    return _svc_hf_artifact_facts(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        deliverable_url_loader=_deliverable_url,
    )


def _hf_current_attempt_summary(
    *,
    voice_state: dict[str, Any],
    subtitle_lane: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    final_stale_reason: str | None = None,
    artifact_facts: dict[str, Any] | None = None,
    no_dub: bool = False,
    no_dub_compose_allowed: bool = False,
) -> dict[str, Any]:
    return _svc_hf_current_attempt_summary(
        voice_state=voice_state,
        subtitle_lane=subtitle_lane,
        dub_status=dub_status,
        compose_status=compose_status,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
        artifact_facts=artifact_facts,
        no_dub=no_dub,
        no_dub_compose_allowed=no_dub_compose_allowed,
    )


def _hf_operator_summary(
    *,
    artifact_facts: dict[str, Any],
    current_attempt: dict[str, Any],
    no_dub: bool,
    subtitle_ready: bool = False,
) -> dict[str, Any]:
    return _svc_hf_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=no_dub,
        subtitle_ready=subtitle_ready,
    )


def _hf_safe_presentation_aggregates(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
    voice_state: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    final_stale_reason: str | None = None,
    no_dub: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _svc_hf_safe_presentation_aggregates(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        voice_state=voice_state,
        dub_status=dub_status,
        compose_status=compose_status,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
        no_dub=no_dub,
        artifact_facts_loader=_hf_artifact_facts,
        current_attempt_loader=_hf_current_attempt_summary,
        operator_summary_loader=_hf_operator_summary,
    )

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
    no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip().lower()
    if no_dub and no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}:
        return True
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
    return hot_follow_internal_lang(value or "mm")


def _resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    """Compatibility subtitle resolver for remaining router-driven compose calls."""
    lang_norm = _normalize_compose_target_lang(lang)
    if lang_norm == "vi":
        explicit_current = task_obj.get("target_subtitle_current")
        if explicit_current is False:
            return None
        if explicit_current is not True:
            subtitle_lane = _hf_subtitle_lane_state(task_code, task_obj)
            if not bool(subtitle_lane.get("target_subtitle_current")):
                return None
    synced_mm_key = _hf_sync_saved_target_subtitle_artifact(task_code, task_obj)
    subtitle_filename = hot_follow_subtitle_filename(lang_norm)
    candidates: list[str] = []
    current_target_key = _hf_task_target_subtitle_key(task_obj, lang_norm)
    if current_target_key:
        candidates.append(str(current_target_key))
    if lang_norm == "my":
        if synced_mm_key:
            candidates.append(str(synced_mm_key))
        mm_path = _task_key(task_obj, "mm_srt_path")
        if mm_path:
            candidates.append(str(mm_path))
        candidates.append(deliver_key(task_code, subtitle_filename))
    else:
        lang_path = _task_key(task_obj, f"{lang_norm}_srt_path")
        if lang_path:
            candidates.append(str(lang_path))
        candidates.append(deliver_key(task_code, subtitle_filename))
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


def _hf_compose_final_video(task_id: str, task: dict) -> ComposeResult:
    svc = CompositionService(storage=get_storage_service(), settings=get_settings())
    return svc.compose(
        task_id,
        task,
        subtitle_resolver=_resolve_target_srt_key,
        subtitle_only_check=_hf_allow_subtitle_only_compose,
    )


def _build_hot_follow_create_data(data: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(data or {})
    prepared["kind"] = "hot_follow"
    prepared["category_key"] = prepared.get("category_key") or "hot_follow"
    if prepared.get("auto_start") is None:
        prepared["auto_start"] = True

    target_lang = hot_follow_internal_lang(prepared.get("content_lang") or prepared.get("target_lang") or "my")
    prepared["target_lang"] = target_lang
    prepared["content_lang"] = target_lang

    settings = get_settings()
    config = dict(prepared.get("config") or {})
    pipeline_config = parse_pipeline_config(prepared.get("pipeline_config"))
    config["source_audio_policy"] = normalize_source_audio_policy(
        config.get("source_audio_policy")
        or pipeline_config.get("source_audio_policy")
        or pipeline_config.get("bgm_strategy")
        or pipeline_config.get("audio_strategy")
    )
    profile = get_hot_follow_language_profile(target_lang)
    requested_voice = resolve_hot_follow_voice_id(
        target_lang,
        str(prepared.get("voice_id") or "").strip()
        or str(config.get("tts_requested_voice") or config.get("hot_follow_tts_requested_voice") or "").strip()
        or os.getenv("DEFAULT_MM_VOICE_ID", profile.default_voice_id("azure-speech")).strip(),
        prepared.get("dub_provider") or config.get("tts_provider") or settings.dub_provider,
    )
    expected_provider = _hot_follow_expected_provider(
        {
            "kind": "hot_follow",
            "target_lang": target_lang,
            "content_lang": target_lang,
        },
        requested_voice,
        prepared.get("dub_provider") or config.get("tts_provider") or settings.dub_provider,
    )
    resolved_voice, _ = resolve_tts_voice(
        settings=settings,
        provider=expected_provider,
        target_lang=target_lang,
        requested_voice=requested_voice,
    )
    prepared["voice_id"] = requested_voice
    prepared["dub_provider"] = expected_provider
    if resolved_voice:
        config["tts_requested_voice"] = requested_voice
        config["hot_follow_tts_requested_voice"] = requested_voice
        config["tts_provider"] = expected_provider
        config["tts_resolved_voice"] = resolved_voice
    prepared["config"] = config
    return prepared


@hot_follow_api_router.post("/hot_follow/tasks", response_model=TaskDetail)
def create_hot_follow_task(
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    repo=Depends(get_task_repository),
):
    normalized = TaskCreate(**_build_hot_follow_create_data(payload.dict()))
    return _create_task_entry(normalized, background_tasks, repo)


@hot_follow_api_router.post("/hot_follow/tasks/local_upload", response_model=TaskDetail)
def create_hot_follow_task_local_upload(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    target_lang: str = Form(default="mm"),
    source_lang: str = Form(default="zh"),
    voice_id: str | None = Form(default=None),
    process_mode: str | None = Form(default=None),
    publish_account: str | None = Form(default=None),
    source_audio_policy: str | None = Form(default=None),
    platform: str | None = Form(default=None),
    task_title: str | None = Form(default=None),
    ui_lang: str | None = Form(default=None),
    auto_start: bool = Form(default=False),
    repo=Depends(get_task_repository),
):
    _ = background_tasks
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="file is required")

    media_policy = hot_follow_media_input_policy()
    ext = Path(file.filename).suffix.lower()
    if ext not in set(media_policy.accepted_extensions):
        raise HTTPException(status_code=400, detail="unsupported file type")

    source_lang_norm = str(source_lang or "zh").strip().lower()
    if source_lang_norm not in {"zh", "en"}:
        raise HTTPException(status_code=400, detail="unsupported source language")
    source_audio_policy_norm = normalize_source_audio_policy(source_audio_policy)
    source_guard = hot_follow_local_upload_source_selection_guard(
        filename=file.filename,
        title=task_title,
        source_audio_policy=source_audio_policy_norm,
    )
    if not source_guard.get("allow", True):
        raise HTTPException(
            status_code=400,
            detail={
                "reason": source_guard.get("reason"),
                "message": source_guard.get("message"),
            },
        )

    task_id = uuid4().hex[:12]
    max_bytes = media_policy.max_upload_size_bytes
    raw_file_path = raw_path(task_id)
    _save_upload_to_paths(
        upload=file,
        inputs_path=raw_file_path,
        raw_path_target=raw_file_path,
        max_bytes=max_bytes,
    )
    try:
        assert_local_video_ok(raw_file_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid local video: {exc}") from exc

    probe = None
    try:
        probe = probe_subtitles(raw_file_path)
    except Exception:
        logger.exception("HOT_FOLLOW_LOCAL_SUBTITLE_PROBE_FAIL", extra={"task_id": task_id})

    prepared = _build_hot_follow_create_data(
        {
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "content_lang": target_lang,
            "ui_lang": ui_lang or "zh",
            "title": task_title or Path(file.filename).stem,
            "voice_id": voice_id,
            "auto_start": bool(auto_start),
            "pipeline_config": _merge_probe_into_pipeline_config(
                {
                    "ingest_mode": "local",
                    "max_upload_size_mb": str(media_policy.max_upload_size_mb),
                    "quality_tier_default": media_policy.quality_tier_default,
                    "target_output_band": media_policy.target_output_band,
                    "prefer_source_quality_preservation": (
                        "true" if media_policy.prefer_source_quality_preservation else "false"
                    ),
                    "oversize_handling_policy": media_policy.oversize_handling_policy,
                    "source_language_hint": source_lang_norm,
                    "process_mode": str(process_mode or "fast_clone"),
                    "publish_account": str(publish_account or "default"),
                    "source_audio_policy": source_audio_policy_norm,
                    "bgm_strategy": (
                        "keep"
                        if source_audio_policy_norm == "preserve"
                        else "replace"
                    ),
                },
                probe,
            ),
        }
    )
    task_payload = {
        "task_id": task_id,
        "title": prepared.get("title"),
        "kind": "hot_follow",
        "source_url": None,
        "platform": platform or "local",
        "voice_id": prepared.get("voice_id"),
        "dub_provider": prepared.get("dub_provider"),
        "config": prepared.get("config") or {},
        "account_id": None,
        "account_name": None,
        "video_type": None,
        "template": None,
        "category_key": "hot_follow",
        "content_lang": prepared.get("content_lang") or "my",
        "target_lang": prepared.get("target_lang") or prepared.get("content_lang") or "my",
        "ui_lang": prepared.get("ui_lang") or "zh",
        "style_preset": None,
        "face_swap_enabled": False,
        "selected_tool_ids": None,
        "pipeline_config": pipeline_config_to_storage(prepared.get("pipeline_config") or {}),
        "status": "pending",
        "last_step": None,
        "error_message": None,
        "source_type": "local",
        "source_filename": file.filename,
    }
    task_payload = normalize_task_payload(task_payload, is_new=True)
    repo.create(task_payload)
    stored_task = repo.get(task_id)
    if not stored_task:
        raise HTTPException(status_code=500, detail=f"Task persistence failed for task_id={task_id}")

    if probe:
        _update_pipeline_probe(repo, task_id, probe)

    raw_key = upload_task_artifact(stored_task, raw_file_path, "raw.mp4", task_id=task_id)
    policy_upsert(
        repo,
        task_id,
        stored_task,
        {
            "raw_path": raw_key,
            "error_message": None,
            "error_reason": None,
        },
        step="router.hot_follow_api.local_upload",
    )
    latest = repo.get(task_id)
    return _task_to_detail(latest or stored_task)


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


def _service_build_hot_follow_publish_hub(task_id: str, repo):
    return _svc_build_hot_follow_publish_hub(
        task_id,
        repo=repo,
        backfill_compose_done=_backfill_compose_done_if_final_ready,
    )


def _service_build_hot_follow_workbench_hub(task_id: str, repo):
    return _svc_build_hot_follow_workbench_hub(
        task_id,
        repo=repo,
        settings=get_settings(),
        object_exists_fn=object_exists,
        task_endpoint_loader=_task_endpoint,
        subtitle_lane_loader=_hf_subtitle_lane_state,
        composed_state_loader=_compute_composed_state,
        pipeline_state_loader=_hf_pipeline_state,
        scene_pack_info_loader=_scene_pack_info,
        subtitles_text_loader=_hf_load_subtitles_text,
        origin_subtitles_text_loader=_hf_load_origin_subtitles_text,
        normalized_source_text_loader=_hf_load_normalized_source_text,
        dual_channel_state_loader=_hf_dual_channel_state,
        audio_config_loader=_hf_audio_config,
        voice_execution_state_loader=_collect_voice_execution_state,
        persisted_audio_state_loader=_hf_persisted_audio_state,
        deliverables_loader=_hf_deliverables,
        presentation_aggregates_loader=_hf_safe_presentation_aggregates,
        presentation_state_loader=_hf_rerun_presentation_state,
        operational_defaults_loader=_hot_follow_operational_defaults,
        workbench_ui_loader=_safe_collect_hot_follow_workbench_ui,
        backfill_compose_done=_backfill_compose_done_if_final_ready,
    )


@hot_follow_api_router.get("/hot_follow/tasks/{task_id}/publish_hub")
def get_hot_follow_publish_hub(
    task_id: str,
    repo=Depends(get_task_repository),
):
    return _service_build_hot_follow_publish_hub(task_id, repo=repo)


@hot_follow_api_router.get("/hot_follow/tasks/{task_id}/workbench_hub", response_model=None)
def get_hot_follow_workbench_hub(
    task_id: str,
    repo=Depends(get_task_repository),
):
    payload = _service_build_hot_follow_workbench_hub(task_id, repo=repo)
    task = repo.get(task_id) or {}
    diagnostics = dict(payload.get("diagnostics") or {})
    diagnostics["translation_waiting"] = hot_follow_translation_waiting_diagnostic(task)
    payload["diagnostics"] = diagnostics
    return payload


def _translate_origin_srt_for_materialization(origin_text: str, target_lang: str) -> str:
    segments = _parse_srt_to_segments(origin_text)
    if not segments:
        return ""
    translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
    for seg in segments:
        idx = int(seg.get("index") or 0)
        seg[target_lang] = str(translations.get(idx) or "").strip()
    return segments_to_srt(segments, target_lang)


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/materialize_target_subtitle_from_origin")
def post_hot_follow_materialize_target_subtitle_from_origin(
    task_id: str,
    payload: HotFollowMaterializeTargetSubtitleRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
    origin_text = _hf_load_origin_subtitles_text(task)
    try:
        saved = materialize_target_subtitle_from_origin(
            task_id,
            task,
            repo=repo,
            origin_text=origin_text,
            target_lang=target_lang,
            expected_origin_key=(payload.expected_origin_key if payload else None),
            expected_subtitle_source=_hf_expected_subtitle_filename(target_lang),
            translate_origin_srt_fn=_translate_origin_srt_for_materialization,
            persist_artifact_fn=lambda saved_text: _hf_sync_saved_target_subtitle_artifact(task_id, task, saved_text),
            write_override_fn=lambda saved_text: _hf_subtitles_override_path(task_id).parent.mkdir(parents=True, exist_ok=True)
            or _hf_subtitles_override_path(task_id).write_text(saved_text, encoding="utf-8"),
            content_hash_fn=_hf_subtitle_content_hash,
        )
    except TargetSubtitleMaterializationFailure as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
                "reason": exc.code,
                "message": exc.message,
            },
        ) from exc
    return {
        "task_id": task_id,
        "action": MATERIALIZE_TARGET_SUBTITLE_FROM_ORIGIN,
        "target_lang": public_target_lang(target_lang),
        "target_subtitle_current": bool(saved.get("target_subtitle_current")),
        "target_subtitle_current_reason": saved.get("target_subtitle_current_reason"),
        "target_subtitle_key": saved.get("mm_srt_path"),
    }


@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/local_preserve_to_subtitle_dub_flow")
def post_hot_follow_local_preserve_to_subtitle_dub_flow(
    task_id: str,
    payload: HotFollowLocalPreserveToSubtitleDubRequest | None = None,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        updated = local_preserve_to_subtitle_dub_flow(
            repo,
            task_id,
            task,
            reason=payload.reason if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "task_id": task_id,
        "action": LOCAL_PRESERVE_TO_SUBTITLE_DUB_FLOW,
        "target_subtitle_materialization_action": updated.get("target_subtitle_materialization_action"),
        "target_subtitle_materialization_status": updated.get("target_subtitle_materialization_status"),
        "task": _task_to_detail(updated),
    }


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
    current_audio_config = _hf_audio_config(task)
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
        target_lang = hot_follow_internal_lang(task.get("target_lang") or task.get("content_lang") or "mm")
        requested_voice = resolve_hot_follow_voice_id(
            target_lang,
            payload.tts_voice.strip() or None,
            updates.get("dub_provider") or task.get("dub_provider") or settings.dub_provider,
        )
        effective_provider = _hot_follow_expected_provider(
            task,
            requested_voice,
            updates.get("dub_provider") or task.get("dub_provider") or settings.dub_provider,
        )
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
        current_speed = f"{float(current_audio_config.get('audio_fit_max_speed') or 1.25):.2f}"
        if (
            f"{speed:.2f}" != current_speed
            and not str(task.get("dub_source_audio_fit_max_speed") or "").strip()
            and bool(task.get("mm_audio_key") or task.get("mm_audio_path"))
        ):
            updates["dub_source_audio_fit_max_speed"] = current_speed

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


@hot_follow_api_router.patch("/hot_follow/tasks/{task_id}/source_url")
def patch_hot_follow_source_url(
    task_id: str,
    payload: HotFollowSourceUrlPatchRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    source_url = str(payload.source_url or "").strip()
    _policy_upsert(repo, task_id, {"source_url": source_url})
    latest = repo.get(task_id) or task
    return {
        "task_id": task_id,
        "source_url": str(latest.get("source_url") or ""),
    }


@hot_follow_api_router.patch("/hot_follow/tasks/{task_id}/subtitles")
def patch_hot_follow_subtitles(
    task_id: str,
    payload: HotFollowSubtitlesRequest,
    repo=Depends(get_task_repository),
):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    text, text_mode = _hf_normalize_subtitles_save_text(task, payload.srt_text or "")
    _hf_save_authoritative_target_subtitle(task_id, task, text=text, text_mode=text_mode, repo=repo)
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
    target_lang = normalize_target_lang(payload.target_lang or task.get("target_lang") or task.get("content_lang") or "mm")
    input_source = str(payload.input_source or "helper_only_text").strip().lower()
    if input_source not in {"helper_only_text", "source_subtitle_lane"}:
        raise HTTPException(
            status_code=400,
            detail={
                "reason": "unsupported_translation_input_source",
                "message": "Unsupported translation input source.",
            },
        )
    if input_source == "source_subtitle_lane":
        try:
            translated_text, saved_task = _hf_translate_source_subtitle_lane(
                task_id,
                task,
                target_lang=target_lang,
                repo=repo,
            )
        except GeminiSubtitlesError as exc:
            detail = sanitize_helper_translate_error(exc)
            raise HTTPException(status_code=409, detail=detail) from exc
        return {
            "task_id": task_id,
            "target_lang": public_target_lang(target_lang),
            "input_source": "source_subtitle_lane",
            "persisted": True,
            "translated_text": translated_text,
            "subtitles": {
                "srt_text": _hf_load_subtitles_text(task_id, saved_task),
                "origin_text": _hf_load_origin_subtitles_text(saved_task),
                "edited_text": _hf_load_subtitles_text(task_id, saved_task),
                "editable": True,
            },
        }
    try:
        source_text = str(payload.text or "").strip()
        if not source_text:
            raise HTTPException(status_code=400, detail="text is empty")
        request_fingerprint = _hf_helper_translate_request_fingerprint(
            task_id=task_id,
            source_text=source_text,
            target_lang=target_lang,
            input_source=input_source,
        )
        request_lock = _hf_helper_translate_request_lock(request_fingerprint)
        request_lock_acquired = request_lock.acquire(blocking=False)
        if not request_lock_acquired:
            latest = repo.get(task_id) or task
            repeated_success = _hf_helper_repeat_success_payload(
                task_id=task_id,
                task=latest,
                target_lang=target_lang,
                source_text=source_text,
            )
            if repeated_success is not None:
                repeated_success["single_flight"] = "deduped_in_flight"
                return repeated_success
            return {
                "task_id": task_id,
                "target_lang": public_target_lang(target_lang),
                "input_source": "helper_only_text",
                "persisted": False,
                "result": "request_in_flight",
                "single_flight": "deduped_in_flight",
                "translated_text": str(latest.get("subtitle_helper_translated_text") or "").strip() or None,
            }
        repeated_success = _hf_helper_repeat_success_payload(
            task_id=task_id,
            task=task,
            target_lang=target_lang,
            source_text=source_text,
        )
        if repeated_success is not None:
            return repeated_success
        if "-->" in source_text:
            try:
                segments = _parse_srt_to_segments(source_text)
                if not segments:
                    raise HTTPException(status_code=400, detail="invalid srt text")
                translations = translate_segments_with_gemini(segments=segments, target_lang=target_lang)
                for seg in segments:
                    idx = int(seg.get("index") or 0)
                    seg[target_lang] = str(translations.get(idx) or seg.get("origin") or "").strip()
                translated_text = segments_to_srt(segments, target_lang)
            except GeminiSubtitlesError as exc:
                detail = sanitize_helper_translate_error(exc)
                latest = repo.get(task_id) or task
                repeated_success = _hf_helper_repeat_success_payload(
                    task_id=task_id,
                    task=latest,
                    target_lang=target_lang,
                    source_text=source_text,
                )
                if repeated_success is not None:
                    repeated_success["result"] = "resolved_with_warning"
                    repeated_success["single_flight"] = "noop_cached"
                    return repeated_success
                _policy_upsert(
                    repo,
                    task_id,
                    helper_translate_failure_updates(
                        detail,
                        input_text=source_text,
                        target_lang=target_lang,
                    ),
                )
                raise HTTPException(status_code=409, detail=detail) from exc
        else:
            try:
                translated_text = _hf_translate_plain_lines(source_text, target_lang=target_lang)
            except GeminiSubtitlesError as exc:
                detail = sanitize_helper_translate_error(exc)
                latest = repo.get(task_id) or task
                repeated_success = _hf_helper_repeat_success_payload(
                    task_id=task_id,
                    task=latest,
                    target_lang=target_lang,
                    source_text=source_text,
                )
                if repeated_success is not None:
                    repeated_success["result"] = "resolved_with_warning"
                    repeated_success["single_flight"] = "noop_cached"
                    return repeated_success
                _policy_upsert(
                    repo,
                    task_id,
                    helper_translate_failure_updates(
                        detail,
                        input_text=source_text,
                        target_lang=target_lang,
                    ),
                )
                raise HTTPException(status_code=409, detail=detail) from exc
    finally:
        if locals().get("request_lock_acquired"):
            request_lock.release()
    _policy_upsert(
        repo,
        task_id,
        helper_translate_success_updates(
            input_text=source_text,
            translated_text=translated_text,
            target_lang=target_lang,
        ),
    )
    return {
        "task_id": task_id,
        "target_lang": public_target_lang(target_lang),
        "input_source": "helper_only_text",
        "persisted": False,
        "result": "resolved",
        "single_flight": "executed",
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
    result = _execute_hot_follow_compose_contract(
        task_id,
        task,
        request=HotFollowComposeRequestContract(
            bgm_mix=req.bgm_mix,
            overlay_subtitles=req.overlay_subtitles,
            freeze_tail_enabled=req.freeze_tail_enabled,
            force=req.force,
            expected_subtitle_updated_at=req.expected_subtitle_updated_at,
            expected_audio_sha256=req.expected_audio_sha256,
        ),
        repo=repo,
        hub_loader=lambda current_task_id, current_repo: _service_build_hot_follow_workbench_hub(current_task_id, repo=current_repo),
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
