"""Hot Follow task/detail/workbench view assembly helpers.

These functions move shared view/presentation assembly out of router modules
without changing HTTP paths or truth ownership.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from gateway.app.config import get_settings
from gateway.app.services.artifact_storage import get_download_url, object_exists
from gateway.app.services.dub_text_guard import clean_and_analyze_dub_text
from gateway.app.services.hot_follow_language_profiles import get_hot_follow_language_profile
from gateway.app.services.hot_follow_skills_advisory import (
    maybe_build_hot_follow_advisory,
)
from gateway.app.services.hot_follow_workbench_presenter import (
    build_hot_follow_artifact_facts,
    build_hot_follow_current_attempt_summary,
    build_hot_follow_operator_summary,
)
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.scenes_service import build_scenes_for_task
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.subtitle_helpers import (
    hf_done_like,
    hf_dual_channel_state,
    hf_load_normalized_source_text,
    hf_load_origin_subtitles_text,
    hf_load_subtitles_text,
    hf_parse_artifact_ready,
    hf_state_from_status,
    hf_subtitle_lane_state,
)
from gateway.app.services.task_view_helpers import (
    backfill_compose_done_if_final_ready,
    compute_composed_state,
    deliverable_url,
    publish_hub_payload,
    resolve_hub_final_url,
    scene_pack_info,
    scenes_status_from_ssot,
    signed_op_url,
    task_endpoint,
    task_key,
)
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang, public_target_lang
from gateway.app.services.voice_service import (
    hf_audio_config,
    hf_audio_display_error,
    hf_screen_text_candidate_summary,
    hf_source_audio_lane_summary,
    hf_source_audio_semantics,
)
from gateway.app.services.voice_state import (
    build_hot_follow_voice_options,
    collect_voice_execution_state,
    hf_current_voiceover_asset,
    hf_persisted_audio_state,
)
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)


def hot_follow_operational_defaults() -> dict[str, Any]:
    return {
        "raw_source_text": "",
        "normalized_source_text": "",
        "parse_source_text": "",
        "parse_source_role": "none",
        "parse_source_authoritative_for_target": False,
        "dub_input_text": "",
        "dub_input_source": None,
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
        "target_subtitle_current": False,
        "target_subtitle_current_reason": "unknown",
        "target_subtitle_authoritative_source": False,
        "target_subtitle_source_copy": False,
    }


def collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    subtitle_lane = hf_subtitle_lane_state(task_id, task)
    task_runtime = dict(task)
    task_runtime["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    task_runtime["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    _sub_status_b, _ = hf_pipeline_state(task, "subtitles")
    _sub_done_b = _sub_status_b in ("done", "ready", "success", "completed", "failed", "error")
    route_state = hf_dual_channel_state(task_id, task_runtime, subtitle_lane, subtitles_step_done=_sub_done_b)
    audio_lane = hf_source_audio_lane_summary(task, route_state)
    screen_text_candidate = hf_screen_text_candidate_summary(subtitle_lane, route_state)
    voice_state = collect_voice_execution_state(task_runtime, settings)
    final_key = task_key(task_runtime, "final_video_key") or task_key(task_runtime, "final_video_path")
    final_exists = bool(final_key and object_exists(str(final_key)))
    compose_status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip() or "never"
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
        **hf_source_audio_semantics(task_runtime, voice_state),
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


def safe_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    try:
        return collect_hot_follow_workbench_ui(task, settings)
    except Exception:
        logger.exception("HF_WORKBENCH_UI_SAFE_FALLBACK task=%s", task.get("task_id") or task.get("id"))
        payload = hot_follow_operational_defaults()
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
                "voice_options_by_provider": build_hot_follow_voice_options(
                    settings, normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
                ),
                "compose_status": str(task.get("compose_status") or "never"),
                "final_exists": False,
                "lipsync_enabled": False,
                "lipsync_status": "off",
            }
        )
        return payload


def hf_pipeline_state(task: dict, step: str, *, composed: dict[str, Any] | None = None) -> tuple[str, str]:
    last_step = str(task.get("last_step") or "").lower()
    task_status = str(task.get("status") or "").lower()
    if step == "parse":
        status = hf_state_from_status(task.get("parse_status"))
        raw_ready = hf_parse_artifact_ready(task)
        if raw_ready:
            status = "done"
        elif status == "pending" and task_status == "processing" and last_step == "parse":
            status = "running"
        summary = "raw=ready" if raw_ready else "raw=none"
        return status, summary
    if step == "subtitles":
        status = hf_state_from_status(task.get("subtitles_status"))
        pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
        no_subtitles = str(pipeline_config.get("no_subtitles") or "").strip().lower() == "true"
        translation_incomplete = str(pipeline_config.get("translation_incomplete") or "").strip().lower() == "true"
        current_reason = str(task.get("target_subtitle_current_reason") or "").strip()
        summary = "origin/mm subtitles"
        if status == "pending" and (task.get("origin_srt_path") or task.get("mm_srt_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "subtitles":
            status = "running"
        if status == "error":
            summary = str(task.get("subtitles_error") or "subtitles_error")
        elif no_subtitles:
            summary = "no_subtitles"
        elif translation_incomplete:
            summary = "translation_incomplete"
        elif current_reason and current_reason not in {"ready", "unknown"}:
            summary = current_reason
        return status, summary
    if step == "audio":
        status = hf_state_from_status(task.get("dub_status"))
        voice_state = collect_voice_execution_state(task, get_settings())
        if status == "pending" and voice_state.get("audio_ready"):
            status = "done"
        if status == "done" and not voice_state.get("audio_ready"):
            status = "pending"
        if status == "pending" and task_status == "processing" and last_step == "dub":
            status = "running"
        audio_cfg = hf_audio_config(task)
        summary = (
            f"dub_provider={voice_state.get('actual_provider') or task.get('dub_provider') or get_settings().dub_provider} "
            f"voice={voice_state.get('resolved_voice') or audio_cfg.get('tts_voice') or 'missing'} "
            f"audio_ready={'yes' if voice_state.get('audio_ready') else 'no'}"
        )
        return status, summary
    if step == "pack":
        status = hf_state_from_status(task.get("pack_status"))
        if status == "pending" and (task.get("pack_key") or task.get("pack_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "pack":
            status = "running"
        summary = f"pack={task.get('pack_type') or '-'}"
        return status, summary
    if step == "compose":
        status = hf_state_from_status(task.get("compose_status"))
        composed_state = composed or compute_composed_state(
            task,
            str(task.get("task_id") or task.get("id") or ""),
        )
        target_lang = normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
        if status == "pending" and bool(composed_state.get("composed_ready")):
            status = "done"
        if status == "done" and target_lang in {"my", "vi"} and not bool(composed_state.get("composed_ready")):
            status = "pending"
        if status == "pending" and task_status == "processing" and last_step in {"compose", "final"}:
            status = "running"
        summary = "final video merge"
        return status, summary
    return "pending", ""


def hf_deliverable_state(task: dict, key: str | None, fallback_status_field: str | None = None) -> str:
    if key and object_exists(str(key)):
        return "done"
    if fallback_status_field and hf_state_from_status(task.get(fallback_status_field)) == "failed":
        return "failed"
    return "pending"


def hf_deliverables(task_id: str, task: dict) -> list[dict[str, Any]]:
    profile = get_hot_follow_language_profile(task.get("target_lang") or task.get("content_lang") or "mm")
    raw_key = task_key(task, "raw_path")
    origin_key = task_key(task, "origin_srt_path")
    mm_key = task_key(task, "mm_srt_path")
    audio_asset = hf_current_voiceover_asset(task_id, task, get_settings())
    audio_key = str(audio_asset.get("key") or "").strip() or None
    pack_key = task_key(task, "pack_key") or task_key(task, "pack_path")
    scenes_key = task_key(task, "scenes_key")
    final_key = task_key(task, "final_video_key") or task_key(task, "final_video_path")
    bgm_key = str(((task.get("config") or {}).get("bgm") or {}).get("bgm_key") or "").strip() or None

    def _entry(
        kind: str,
        title: str,
        key: str | None,
        open_url: str | None,
        download_url: str | None,
        state: str,
    ) -> dict[str, Any]:
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
            "url": open_url or download_url,
            "open_url": open_url,
            "download_url": download_url,
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
            task_endpoint(task_id, "raw") if raw_key and object_exists(raw_key) else None,
            signed_op_url(task_id, "raw") if raw_key and object_exists(raw_key) else None,
            "done" if hf_parse_artifact_ready(task) else hf_deliverable_state(task, raw_key, "parse_status"),
        ),
        _entry(
            "origin_subtitle",
            "origin.srt",
            origin_key,
            task_endpoint(task_id, "origin") if origin_key and object_exists(origin_key) else None,
            signed_op_url(task_id, "origin_srt") if origin_key and object_exists(origin_key) else None,
            hf_deliverable_state(task, origin_key, "subtitles_status"),
        ),
        _entry(
            "subtitle",
            profile.subtitle_filename,
            mm_key,
            task_endpoint(task_id, "mm") if mm_key and object_exists(mm_key) else None,
            signed_op_url(task_id, "mm_srt") if mm_key and object_exists(mm_key) else None,
            hf_deliverable_state(task, mm_key, "subtitles_status"),
        ),
        _entry(
            "audio",
            profile.dub_filename,
            audio_key,
            task_endpoint(task_id, "audio") if audio_key and object_exists(str(audio_key)) else None,
            signed_op_url(task_id, "mm_audio") if audio_key and object_exists(str(audio_key)) else None,
            "done" if audio_key and bool(audio_asset.get("exists")) else hf_deliverable_state(task, None, "dub_status"),
        ),
        _entry(
            "bgm",
            "BGM",
            bgm_key,
            get_download_url(str(bgm_key)) if bgm_key and object_exists(str(bgm_key)) else None,
            get_download_url(str(bgm_key)) if bgm_key and object_exists(str(bgm_key)) else None,
            "done" if bgm_key and object_exists(str(bgm_key)) else "pending",
        ),
        _entry(
            "pack",
            "Pack ZIP",
            pack_key,
            None,
            signed_op_url(task_id, "pack") if pack_key and object_exists(pack_key) else None,
            hf_deliverable_state(task, pack_key, "pack_status"),
        ),
        _entry(
            "scenes",
            "Scenes ZIP",
            scenes_key,
            None,
            signed_op_url(task_id, "scenes") if scenes_key and object_exists(scenes_key) else None,
            "done" if scenes_key else hf_deliverable_state(task, scenes_key, "scenes_status"),
        ),
        _entry(
            "final",
            "Final Video",
            final_key,
            task_endpoint(task_id, "final") if final_key and object_exists(str(final_key)) else None,
            signed_op_url(task_id, "final_mp4") if final_key and object_exists(str(final_key)) else None,
            hf_deliverable_state(task, final_key, "compose_status"),
        ),
    ]


def hf_shape_from_events(task: dict) -> dict[str, str]:
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


def hf_task_status_shape(task: dict) -> dict[str, str]:
    shape = hf_shape_from_events(task)
    step = shape.get("step") or ""
    phase = shape.get("phase") or ""
    provider = shape.get("provider") or ""

    if not step:
        last_step = str(task.get("last_step") or "").strip().lower()
        step_map = {"dubbing": "dub", "audio": "dub", "final": "compose"}
        step = step_map.get(last_step, last_step)
    if not step:
        for candidate in ("compose", "pack", "scenes", "dub", "subtitles", "parse"):
            status, _ = hf_pipeline_state(task, candidate)
            if status in {"running", "failed"}:
                step = candidate
                break
    if not step:
        for candidate in ("compose", "pack", "scenes", "dub", "subtitles", "parse"):
            status, _ = hf_pipeline_state(task, candidate)
            if status == "done":
                step = candidate
                break

    if not phase:
        if step:
            status, _ = hf_pipeline_state(task, step)
            phase = status
        else:
            phase = hf_state_from_status(task.get("status")) or "pending"

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


def hf_rerun_presentation_state(
    task: dict,
    voice_state: dict[str, Any] | None,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    dub_status: str | None,
) -> dict[str, Any]:
    voice = voice_state or {}
    final_payload = final_info or historical_final or {}
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


def hf_artifact_facts(
    task_id: str,
    task: dict,
    *,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    persisted_audio: dict[str, Any] | None,
    subtitle_lane: dict[str, Any] | None,
    scene_pack: dict[str, Any] | None,
) -> dict[str, Any]:
    return build_hot_follow_artifact_facts(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        deliverable_url=deliverable_url,
    )


def hf_current_attempt_summary(
    *,
    voice_state: dict[str, Any],
    subtitle_lane: dict[str, Any],
    dub_status: str,
    compose_status: str,
    composed_reason: str,
    final_stale_reason: str | None = None,
) -> dict[str, Any]:
    return build_hot_follow_current_attempt_summary(
        voice_state=voice_state,
        subtitle_lane=subtitle_lane,
        dub_status=dub_status,
        compose_status=compose_status,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
    )


def hf_operator_summary(
    *,
    artifact_facts: dict[str, Any],
    current_attempt: dict[str, Any],
    no_dub: bool,
    subtitle_ready: bool = False,
) -> dict[str, Any]:
    return build_hot_follow_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=no_dub,
        subtitle_ready=subtitle_ready,
    )


def hf_safe_presentation_aggregates(
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
    try:
        artifact_facts = hf_artifact_facts(
            task_id,
            task,
            final_info=final_info,
            historical_final=historical_final,
            persisted_audio=persisted_audio,
            subtitle_lane=subtitle_lane,
            scene_pack=scene_pack,
        )
        current_attempt = hf_current_attempt_summary(
            voice_state=voice_state,
            subtitle_lane=subtitle_lane or {},
            dub_status=dub_status,
            compose_status=compose_status,
            composed_reason=composed_reason,
            final_stale_reason=final_stale_reason,
        )
        operator_summary = hf_operator_summary(
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
            no_dub=no_dub,
            subtitle_ready=bool((subtitle_lane or {}).get("subtitle_ready")),
        )
        return artifact_facts, current_attempt, operator_summary
    except Exception:
        logger.exception("HF_PRESENTATION_AGGREGATES_SAFE_FALLBACK task=%s", task_id)
        return {}, {}, {}


def build_hot_follow_publish_hub(
    task_id: str,
    repo,
    *,
    publish_payload_builder=publish_hub_payload,
    state_computer=compute_hot_follow_state,
    backfill_compose_done=backfill_compose_done_if_final_ready,
    line_binding_loader=get_line_runtime_binding,
) -> dict[str, Any]:
    task = repo.get(task_id)
    if not task:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")
    payload = state_computer(task, publish_payload_builder(task))
    if backfill_compose_done(repo, task_id, task, bool(payload.get("composed_ready"))):
        task = repo.get(task_id) or task
        payload = state_computer(task, publish_payload_builder(task))
    payload["line"] = line_binding_loader(task).to_payload()
    return payload


def build_hot_follow_workbench_hub(
    task_id: str,
    repo,
    *,
    settings=None,
    object_exists_fn=object_exists,
    task_endpoint_loader=task_endpoint,
    subtitle_lane_loader=hf_subtitle_lane_state,
    composed_state_loader=compute_composed_state,
    pipeline_state_loader=hf_pipeline_state,
    scene_pack_info_loader=scene_pack_info,
    subtitles_text_loader=hf_load_subtitles_text,
    origin_subtitles_text_loader=hf_load_origin_subtitles_text,
    normalized_source_text_loader=hf_load_normalized_source_text,
    dual_channel_state_loader=hf_dual_channel_state,
    audio_config_loader=hf_audio_config,
    voice_execution_state_loader=collect_voice_execution_state,
    persisted_audio_state_loader=hf_persisted_audio_state,
    deliverables_loader=hf_deliverables,
    presentation_aggregates_loader=hf_safe_presentation_aggregates,
    presentation_state_loader=hf_rerun_presentation_state,
    resolve_final_url_loader=resolve_hub_final_url,
    operational_defaults_loader=hot_follow_operational_defaults,
    workbench_ui_loader=safe_collect_hot_follow_workbench_ui,
    state_computer=compute_hot_follow_state,
    backfill_compose_done=backfill_compose_done_if_final_ready,
    line_binding_loader=get_line_runtime_binding,
) -> dict[str, Any]:
    task = repo.get(task_id)
    if not task:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("hot_follow_hub_hit task=%s kind=%s", task_id, task.get("kind"))
    settings_obj = settings or get_settings()
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
    subtitle_lane = subtitle_lane_loader(task_id, task)
    task_runtime = dict(task)
    task_runtime["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    task_runtime["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    composed = composed_state_loader(task_runtime, task_id)
    parse_state, parse_summary = pipeline_state_loader(task_runtime, "parse")
    subtitles_state, subtitles_summary = pipeline_state_loader(task_runtime, "subtitles")
    dub_state, dub_summary = pipeline_state_loader(task_runtime, "audio")
    pack_state, pack_summary = pipeline_state_loader(task_runtime, "pack")
    compose_state, compose_summary = pipeline_state_loader(task_runtime, "compose", composed=composed)

    raw_key = task_key(task_runtime, "raw_path")
    raw_url = task_endpoint_loader(task_id, "raw") if raw_key and object_exists_fn(raw_key) else None
    mute_key = task_key(task_runtime, "mute_video_key") or task_key(task_runtime, "mute_video_path")
    mute_url = task_endpoint_loader(task_id, "raw") if mute_key and object_exists_fn(str(mute_key)) else raw_url
    final_info = composed.get("final") or {}
    historical_final = composed.get("historical_final") or {}
    scene_pack = scene_pack_info_loader(task_runtime, task_id)
    scenes_key = task_key(task_runtime, "scenes_key")
    scenes_status = scenes_status_from_ssot(task_runtime)
    scenes_url = signed_op_url(task_id, "scenes") if scenes_key else None
    subtitles_text = subtitles_text_loader(task_id, task_runtime)
    origin_text = origin_subtitles_text_loader(task_runtime)
    normalized_source_text = normalized_source_text_loader(task_id, task_runtime)
    _sub_step_done = str(subtitles_state).strip().lower() in ("done", "ready", "success", "completed", "failed", "error")
    route_state = dual_channel_state_loader(task_id, task_runtime, subtitle_lane, subtitles_step_done=_sub_step_done)
    audio_cfg = audio_config_loader(task_runtime)
    voice_state = voice_execution_state_loader(task_runtime, settings_obj)
    persisted_audio = persisted_audio_state_loader(task_id, task_runtime)
    target_lang_internal = normalize_target_lang(task_runtime.get("target_lang") or task_runtime.get("content_lang") or "mm")
    text_guard = clean_and_analyze_dub_text(subtitles_text or "", target_lang_internal)
    audio_warning = str(text_guard.get("warning") or "").strip() or None
    if (
        not (audio_cfg.get("voiceover_url") or "").strip()
        and (task_runtime.get("mm_audio_key") or task_runtime.get("mm_audio_path"))
        and str(dub_state).strip().lower() not in {"running", "processing", "queued"}
        and str(voice_state.get("dub_current_reason") or "").strip().lower() not in {"dub_running", "dub_not_done"}
    ):
        dub_state = "failed"
        if not dub_summary:
            dub_summary = "voiceover artifact invalid"
    audio_error = hf_audio_display_error(str(dub_state), task.get("dub_error"), voice_state)
    deliverables = deliverables_loader(task_id, task_runtime)
    target_profile = get_hot_follow_language_profile(target_lang_internal)
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
            "voiceover_url": audio_cfg.get("tts_voiceover_url") or audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
            "bgm_url": audio_cfg.get("bgm_url"),
            "final_url": None,
            "final_video_url": None,
        },
        "pipeline": pipeline,
        "subtitles": {
            "origin_text": origin_text or "",
            "raw_source_text": subtitle_lane.get("raw_source_text") or origin_text or "",
            "normalized_source_text": subtitle_lane.get("normalized_source_text") or normalized_source_text or "",
            "parse_source_text": subtitle_lane.get("parse_source_text") or "",
            "parse_source_role": subtitle_lane.get("parse_source_role") or "none",
            "parse_source_authoritative_for_target": bool(subtitle_lane.get("parse_source_authoritative_for_target")),
            "edited_text": subtitles_text or "",
            "srt_text": subtitles_text or "",
            "primary_editable_text": subtitle_lane.get("primary_editable_text") or subtitles_text or "",
            "primary_editable_format": subtitle_lane.get("primary_editable_format") or "srt",
            "dub_input_text": subtitle_lane.get("dub_input_text") or "",
            "dub_input_format": subtitle_lane.get("dub_input_format") or "plain_text",
            "dub_input_source": subtitle_lane.get("dub_input_source"),
            "status": subtitles_state,
            "error": task.get("subtitles_error"),
            "subtitle_ready": bool(subtitle_lane.get("subtitle_ready")),
            "subtitle_ready_reason": subtitle_lane.get("subtitle_ready_reason"),
            "target_subtitle_current": bool(subtitle_lane.get("target_subtitle_current")),
            "target_subtitle_current_reason": subtitle_lane.get("target_subtitle_current_reason"),
            "target_subtitle_authoritative_source": bool(subtitle_lane.get("target_subtitle_authoritative_source")),
            "target_subtitle_source_copy": bool(subtitle_lane.get("target_subtitle_source_copy")),
            "editable": True,
            "updated_at": task.get("subtitles_override_updated_at") or task.get("updated_at"),
        },
        "audio": {
            "tts_engine": audio_cfg.get("tts_engine"),
            "tts_voice": audio_cfg.get("tts_voice"),
            "audio_fit_max_speed": audio_cfg.get("audio_fit_max_speed"),
            "voiceover_url": audio_cfg.get("tts_voiceover_url") or audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
            "tts_voiceover_url": audio_cfg.get("tts_voiceover_url"),
            "dub_preview_url": audio_cfg.get("dub_preview_url"),
            "bgm_url": audio_cfg.get("bgm_url"),
            "bgm_mix": audio_cfg.get("bgm_mix"),
            "source_audio_policy": audio_cfg.get("source_audio_policy"),
            "source_audio_preserved": bool(audio_cfg.get("source_audio_preserved")),
            "tts_voiceover_ready": bool(audio_cfg.get("tts_voiceover_ready")),
            "audio_flow_mode": audio_cfg.get("audio_flow_mode"),
            "audio_flow_label": audio_cfg.get("audio_flow_label"),
            "audio_flow_reason": audio_cfg.get("audio_flow_reason"),
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
            "dub_source_audio_fit_max_speed": voice_state.get("dub_source_audio_fit_max_speed"),
            "current_audio_fit_max_speed": voice_state.get("current_audio_fit_max_speed"),
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
        "target_lang_profile": {
            "target_lang": target_profile.public_lang,
            "internal_lang": target_profile.internal_lang,
            "display_name": target_profile.display_name,
            "subtitle_filename": target_profile.subtitle_filename,
            "subtitle_txt_filename": target_profile.subtitle_txt_filename,
            "dub_filename": target_profile.dub_filename,
            "allowed_voice_options": list(target_profile.allowed_voice_options),
            "default_voice_by_provider": dict(target_profile.default_voice_by_provider),
        },
        "events": task.get("events") or [],
        "compose_plan": compose_plan,
        "scene_outputs": scene_outputs,
        "composed_ready": composed_ready,
        "composed_reason": composed_reason,
        "final": final_info,
        "historical_final": historical_final,
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
    final_stale_reason = composed.get("final_stale_reason") or None
    payload["final_stale_reason"] = final_stale_reason
    payload["final_fresh"] = bool(composed.get("final_fresh"))
    artifact_facts, current_attempt, operator_summary = presentation_aggregates_loader(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        voice_state=voice_state,
        dub_status=str(dub_state),
        compose_status=compose_state,
        composed_reason=composed_reason,
        final_stale_reason=final_stale_reason,
        no_dub=bool((payload.get("audio") or {}).get("no_dub")),
    )
    payload["artifact_facts"] = artifact_facts
    payload["current_attempt"] = current_attempt
    payload["operator_summary"] = operator_summary
    payload["presentation"] = presentation_state_loader(
        task,
        voice_state,
        final_info,
        historical_final,
        dub_state,
    )
    final_url = resolve_final_url_loader(task_id, payload)
    if final_url:
        payload["media"]["final_url"] = final_url
        payload["media"]["final_video_url"] = final_url
    payload["final_url"] = final_url
    payload["final_video_url"] = final_url
    composed_ready = bool(composed_ready)
    payload["composed_ready"] = composed_ready
    payload["composed_reason"] = "ready" if composed_ready else "not_ready"
    if isinstance(payload.get("deliverables"), list):
        for item in payload["deliverables"]:
            if not isinstance(item, dict):
                continue
            if str(item.get("kind") or "").strip().lower() == "final":
                item["url"] = final_url
                item["open_url"] = final_url
                if composed_ready:
                    item["status"] = "done"
                    item["state"] = "done"
                    item["historical"] = False
                else:
                    item["status"] = "pending"
                    item["state"] = "pending"
                    item["historical"] = bool((historical_final or {}).get("exists"))
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
    payload = state_computer(task_runtime, payload)
    if backfill_compose_done(repo, task_id, task, bool(payload.get("composed_ready"))):
        latest = repo.get(task_id) or task
        latest_runtime = dict(latest)
        latest_lane = subtitle_lane_loader(task_id, latest)
        latest_runtime["target_subtitle_current"] = bool(latest_lane.get("target_subtitle_current"))
        latest_runtime["target_subtitle_current_reason"] = latest_lane.get("target_subtitle_current_reason")
        payload = state_computer(latest_runtime, payload)
        task = latest

    final_url = str(
        payload.get("final_url")
        or (payload.get("media", {}) or {}).get("final_url")
        or ""
    ).strip()
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
                    item["historical"] = False
                    if final_url:
                        item["url"] = final_url
                        item["open_url"] = final_url
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
                    item["historical"] = bool((payload.get("historical_final") or {}).get("exists"))
                    item["url"] = None
                    item["open_url"] = None
                    break
    payload["line"] = line_binding_loader(task).to_payload()
    advisory = maybe_build_hot_follow_advisory(task, payload)
    if advisory is not None:
        payload["advisory"] = advisory
    payload.update(operational_defaults_loader())
    payload.update(workbench_ui_loader(task, settings_obj))
    return payload
