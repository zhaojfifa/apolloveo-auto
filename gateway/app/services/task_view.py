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
from gateway.app.services.contracts.hot_follow_workbench import (
    validate_hot_follow_workbench_response,
)
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
from gateway.app.services.task_view_workbench_contract import (
    apply_ready_gate_composed_projection,
    apply_ready_gate_compose_projection,
    attach_final_url,
    attach_task_aliases,
    build_hot_follow_compose_plan,
    build_hot_follow_workbench_payload,
    build_pipeline_legacy,
    build_pipeline_rows,
    normalize_compose_last,
    sync_final_deliverable_projection,
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


def collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    subtitle_lane_loader=hf_subtitle_lane_state,
    pipeline_state_loader=None,
    dual_channel_loader=hf_dual_channel_state,
    source_audio_lane_loader=hf_source_audio_lane_summary,
    screen_text_candidate_loader=hf_screen_text_candidate_summary,
    voice_state_loader=collect_voice_execution_state,
    task_key_loader=task_key,
    object_exists_fn=object_exists,
    source_audio_semantics_loader=hf_source_audio_semantics,
    pipeline_config_loader=parse_pipeline_config,
) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    subtitle_lane = subtitle_lane_loader(task_id, task)
    task_runtime = dict(task)
    task_runtime["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    task_runtime["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    pipeline_state_loader = pipeline_state_loader or hf_pipeline_state
    _sub_status_b, _ = pipeline_state_loader(task, "subtitles")
    _sub_done_b = _sub_status_b in ("done", "ready", "success", "completed", "failed", "error")
    route_state = dual_channel_loader(task_id, task_runtime, subtitle_lane, subtitles_step_done=_sub_done_b)
    audio_lane = source_audio_lane_loader(task, route_state)
    screen_text_candidate = screen_text_candidate_loader(subtitle_lane, route_state)
    voice_state = voice_state_loader(task_runtime, settings)
    final_key = task_key_loader(task_runtime, "final_video_key") or task_key_loader(task_runtime, "final_video_path")
    final_exists = bool(final_key and object_exists_fn(str(final_key)))
    compose_status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip() or "never"
    lipsync_enabled = os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in ("1", "true", "yes")
    pipeline_config = pipeline_config_loader(task.get("pipeline_config"))
    stored_no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task.get("dub_skip_reason") or ""
    ).strip()
    no_dub = bool(pipeline_config.get("no_dub") == "true") or (
        route_state.get("content_mode") in {"silent_candidate", "subtitle_led"}
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    helper_translate_failed_voice_led = bool(
        subtitle_lane.get("helper_translate_failed")
        and not bool(subtitle_lane.get("subtitle_ready"))
        and str(route_state.get("content_mode") or "").strip().lower() == "voice_led"
    )
    if helper_translate_failed_voice_led:
        no_dub = False
    if bool(subtitle_lane.get("subtitle_ready")) and stored_no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}:
        no_dub = False
    if voice_state.get("audio_ready") or voice_state.get("deliverable_audio_done") or voice_state.get("voiceover_url"):
        no_dub = False
    if stored_no_dub_reason == "target_subtitle_empty":
        no_dub_reason = "target_subtitle_empty"
        no_dub_message = "Target subtitle is empty; dubbing is skipped."
    elif stored_no_dub_reason == "dub_input_empty":
        no_dub_reason = "dub_input_empty"
        no_dub_message = "Dub input is empty; dubbing is skipped."
    elif route_state.get("content_mode") == "subtitle_led":
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
        **source_audio_semantics_loader(task_runtime, voice_state),
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


def safe_collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    collector=collect_hot_follow_workbench_ui,
    operational_defaults_loader=hot_follow_operational_defaults,
    provider_normalizer=normalize_provider,
    target_lang_normalizer=normalize_target_lang,
    voice_options_loader=build_hot_follow_voice_options,
) -> dict[str, Any]:
    try:
        return collector(task, settings)
    except Exception:
        logger.exception("HF_WORKBENCH_UI_SAFE_FALLBACK task=%s", task.get("task_id") or task.get("id"))
        payload = operational_defaults_loader()
        payload.update(
            {
                "actual_provider": provider_normalizer(task.get("dub_provider") or getattr(settings, "dub_provider", None)),
                "resolved_voice": None,
                "requested_voice": None,
                "audio_ready": False,
                "audio_ready_reason": "unknown",
                "deliverable_audio_done": False,
                "dub_current": False,
                "dub_current_reason": "unknown",
                "voice_options_by_provider": voice_options_loader(
                    settings, target_lang_normalizer(task.get("target_lang") or task.get("content_lang") or "mm")
                ),
                "compose_status": str(task.get("compose_status") or "never"),
                "final_exists": False,
                "lipsync_enabled": False,
                "lipsync_status": "off",
            }
        )
        return payload


def hf_pipeline_state(
    task: dict,
    step: str,
    *,
    composed: dict[str, Any] | None = None,
    state_from_status=hf_state_from_status,
    parse_artifact_ready_loader=hf_parse_artifact_ready,
    voice_state_loader=collect_voice_execution_state,
    settings_loader=get_settings,
    audio_config_loader=hf_audio_config,
    composed_state_loader=compute_composed_state,
) -> tuple[str, str]:
    last_step = str(task.get("last_step") or "").lower()
    task_status = str(task.get("status") or "").lower()
    if step == "parse":
        status = state_from_status(task.get("parse_status"))
        raw_ready = parse_artifact_ready_loader(task)
        if raw_ready:
            status = "done"
        elif status == "pending" and task_status == "processing" and last_step == "parse":
            status = "running"
        summary = "raw=ready" if raw_ready else "raw=none"
        return status, summary
    if step == "subtitles":
        status = state_from_status(task.get("subtitles_status"))
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
        status = state_from_status(task.get("dub_status"))
        settings = settings_loader()
        voice_state = voice_state_loader(task, settings)
        if status == "pending" and voice_state.get("audio_ready"):
            status = "done"
        if status == "done" and not voice_state.get("audio_ready"):
            status = "pending"
        if status == "pending" and task_status == "processing" and last_step == "dub":
            status = "running"
        audio_cfg = audio_config_loader(task)
        summary = (
            f"dub_provider={voice_state.get('actual_provider') or task.get('dub_provider') or settings.dub_provider} "
            f"voice={voice_state.get('resolved_voice') or audio_cfg.get('tts_voice') or 'missing'} "
            f"audio_ready={'yes' if voice_state.get('audio_ready') else 'no'}"
        )
        return status, summary
    if step == "pack":
        status = state_from_status(task.get("pack_status"))
        if status == "pending" and (task.get("pack_key") or task.get("pack_path")):
            status = "done"
        if status == "pending" and task_status == "processing" and last_step == "pack":
            status = "running"
        summary = f"pack={task.get('pack_type') or '-'}"
        return status, summary
    if step == "compose":
        status = state_from_status(task.get("compose_status"))
        composed_state = composed or composed_state_loader(
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


def hf_deliverable_state(
    task: dict,
    key: str | None,
    fallback_status_field: str | None = None,
    *,
    object_exists_fn=object_exists,
    state_from_status=hf_state_from_status,
) -> str:
    if key and object_exists_fn(str(key)):
        return "done"
    if fallback_status_field and state_from_status(task.get(fallback_status_field)) == "failed":
        return "failed"
    return "pending"


def hf_deliverables(
    task_id: str,
    task: dict,
    *,
    task_key_loader=task_key,
    subtitle_lane_loader=hf_subtitle_lane_state,
    voiceover_asset_loader=hf_current_voiceover_asset,
    settings_loader=get_settings,
    object_exists_fn=object_exists,
    download_url_loader=get_download_url,
    task_endpoint_loader=task_endpoint,
    signed_op_url_loader=signed_op_url,
    parse_artifact_ready_loader=hf_parse_artifact_ready,
    deliverable_state_loader=None,
) -> list[dict[str, Any]]:
    profile = get_hot_follow_language_profile(task.get("target_lang") or task.get("content_lang") or "mm")
    raw_key = task_key_loader(task, "raw_path")
    origin_key = task_key_loader(task, "origin_srt_path")
    mm_key = task_key_loader(task, "mm_srt_path")
    subtitle_lane = subtitle_lane_loader(task_id, task)
    target_subtitle_exists = bool(subtitle_lane.get("subtitle_artifact_exists"))
    audio_asset = voiceover_asset_loader(task_id, task, settings_loader())
    audio_key = str(audio_asset.get("key") or "").strip() or None
    pack_key = task_key_loader(task, "pack_key") or task_key_loader(task, "pack_path")
    scenes_key = task_key_loader(task, "scenes_key")
    final_key = task_key_loader(task, "final_video_key") or task_key_loader(task, "final_video_path")
    bgm_key = str(((task.get("config") or {}).get("bgm") or {}).get("bgm_key") or "").strip() or None
    deliverable_state_loader = deliverable_state_loader or (
        lambda task_obj, key, fallback_status_field=None: hf_deliverable_state(
            task_obj,
            key,
            fallback_status_field,
            object_exists_fn=object_exists_fn,
        )
    )

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
            task_endpoint_loader(task_id, "raw") if raw_key and object_exists_fn(raw_key) else None,
            signed_op_url_loader(task_id, "raw") if raw_key and object_exists_fn(raw_key) else None,
            "done" if parse_artifact_ready_loader(task) else deliverable_state_loader(task, raw_key, "parse_status"),
        ),
        _entry(
            "origin_subtitle",
            "origin.srt",
            origin_key,
            task_endpoint_loader(task_id, "origin") if origin_key and object_exists_fn(origin_key) else None,
            signed_op_url_loader(task_id, "origin_srt") if origin_key and object_exists_fn(origin_key) else None,
            deliverable_state_loader(task, origin_key, "subtitles_status"),
        ),
        _entry(
            "subtitle",
            profile.subtitle_filename,
            mm_key,
            task_endpoint_loader(task_id, "mm") if target_subtitle_exists and mm_key and object_exists_fn(mm_key) else None,
            signed_op_url_loader(task_id, "mm_srt") if target_subtitle_exists and mm_key and object_exists_fn(mm_key) else None,
            "done" if target_subtitle_exists else deliverable_state_loader(task, None, "subtitles_status"),
        ),
        _entry(
            "audio",
            profile.dub_filename,
            audio_key,
            task_endpoint_loader(task_id, "audio") if audio_key and object_exists_fn(str(audio_key)) else None,
            signed_op_url_loader(task_id, "mm_audio") if audio_key and object_exists_fn(str(audio_key)) else None,
            "done" if audio_key and bool(audio_asset.get("exists")) else deliverable_state_loader(task, None, "dub_status"),
        ),
        _entry(
            "bgm",
            "BGM",
            bgm_key,
            download_url_loader(str(bgm_key)) if bgm_key and object_exists_fn(str(bgm_key)) else None,
            download_url_loader(str(bgm_key)) if bgm_key and object_exists_fn(str(bgm_key)) else None,
            "done" if bgm_key and object_exists_fn(str(bgm_key)) else "pending",
        ),
        _entry(
            "pack",
            "Pack ZIP",
            pack_key,
            None,
            signed_op_url_loader(task_id, "pack") if pack_key and object_exists_fn(pack_key) else None,
            deliverable_state_loader(task, pack_key, "pack_status"),
        ),
        _entry(
            "scenes",
            "Scenes ZIP",
            scenes_key,
            None,
            signed_op_url_loader(task_id, "scenes") if scenes_key and object_exists_fn(scenes_key) else None,
            "done" if scenes_key else deliverable_state_loader(task, scenes_key, "scenes_status"),
        ),
        _entry(
            "final",
            "Final Video",
            final_key,
            task_endpoint_loader(task_id, "final") if final_key and object_exists_fn(str(final_key)) else None,
            signed_op_url_loader(task_id, "final_mp4") if final_key and object_exists_fn(str(final_key)) else None,
            deliverable_state_loader(task, final_key, "compose_status"),
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


def hf_task_status_shape(
    task: dict,
    *,
    pipeline_state_loader=hf_pipeline_state,
    state_from_status=hf_state_from_status,
) -> dict[str, str]:
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
            status, _ = pipeline_state_loader(task, candidate)
            if status in {"running", "failed"}:
                step = candidate
                break
    if not step:
        for candidate in ("compose", "pack", "scenes", "dub", "subtitles", "parse"):
            status, _ = pipeline_state_loader(task, candidate)
            if status == "done":
                step = candidate
                break

    if not phase:
        if step:
            status, _ = pipeline_state_loader(task, step)
            phase = status
        else:
            phase = state_from_status(task.get("status")) or "pending"

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
    artifact_facts: dict[str, Any] | None = None,
    no_dub: bool = False,
    no_dub_compose_allowed: bool = False,
) -> dict[str, Any]:
    return build_hot_follow_current_attempt_summary(
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
            artifact_facts=artifact_facts,
            no_dub=no_dub,
            no_dub_compose_allowed=bool((artifact_facts.get("selected_compose_route") or {}).get("name") in {
                "preserve_source_route",
                "bgm_only_route",
                "no_tts_compose_route",
            })
            if isinstance(artifact_facts.get("selected_compose_route"), dict)
            else False,
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
    compose_plan = build_hot_follow_compose_plan(task, pipeline_config)
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
    stored_no_dub_reason = str(
        pipeline_config.get("dub_skip_reason") or task_runtime.get("dub_skip_reason") or ""
    ).strip()
    no_dub = bool(pipeline_config.get("no_dub") == "true") or (
        route_state.get("content_mode") in {"silent_candidate", "subtitle_led"}
        and not str(subtitle_lane.get("dub_input_text") or "").strip()
    )
    if voice_state.get("audio_ready") or voice_state.get("deliverable_audio_done") or voice_state.get("voiceover_url"):
        no_dub = False
    if stored_no_dub_reason in {"target_subtitle_empty", "dub_input_empty"}:
        no_dub_reason = stored_no_dub_reason
    elif route_state.get("content_mode") == "subtitle_led":
        no_dub_reason = "subtitle_led"
    elif route_state.get("content_mode") == "silent_candidate":
        no_dub_reason = "no_speech_detected"
    else:
        no_dub_reason = None
    if not no_dub:
        no_dub_reason = None
    no_dub_compose_allowed = bool(
        no_dub and str(no_dub_reason or "").strip().lower() in {"target_subtitle_empty", "dub_input_empty"}
    )
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
    compose_last = normalize_compose_last(task)
    composed_ready = bool(composed.get("composed_ready"))
    composed_reason = str(composed.get("composed_reason") or "final_missing")

    parse_error = task.get("parse_error") if str(parse_state).strip().lower() in {"failed", "error"} else None
    subtitles_error = task.get("subtitles_error") if str(subtitles_state).strip().lower() in {"failed", "error"} else None
    dub_error = audio_error if str(dub_state).strip().lower() in {"failed", "error"} else None
    pack_error = task.get("pack_error") if str(pack_state).strip().lower() in {"failed", "error"} else None
    compose_error = task.get("compose_error") if str(compose_state).strip().lower() in {"failed", "error"} else None
    pipeline = build_pipeline_rows(
        task,
        parse_state=parse_state,
        parse_summary=parse_summary,
        subtitles_state=subtitles_state,
        subtitles_summary=subtitles_summary,
        dub_state=dub_state,
        dub_summary=dub_summary,
        pack_state=pack_state,
        pack_summary=pack_summary,
        compose_state=compose_state,
        compose_summary=compose_summary,
        parse_error=parse_error,
        subtitles_error=subtitles_error,
        dub_error=dub_error,
        pack_error=pack_error,
        compose_error=compose_error,
    )
    pipeline_legacy = build_pipeline_legacy(
        task,
        parse_state=parse_state,
        parse_summary=parse_summary,
        subtitles_state=subtitles_state,
        subtitles_summary=subtitles_summary,
        dub_state=dub_state,
        dub_summary=dub_summary,
        pack_state=pack_state,
        pack_summary=pack_summary,
        compose_state=compose_state,
        compose_summary=compose_summary,
    )
    payload = build_hot_follow_workbench_payload(
        task_id=task_id,
        task=task,
        pipeline_config=pipeline_config,
        compose_plan=compose_plan,
        scene_outputs=scene_outputs,
        subtitle_lane=subtitle_lane,
        target_lang_public=public_target_lang(target_lang_internal),
        raw_url=raw_url,
        mute_url=mute_url,
        audio_cfg=audio_cfg,
        voice_state=voice_state,
        subtitles_state=subtitles_state,
        dub_state=dub_state,
        pack_state=pack_state,
        compose_state=compose_state,
        pipeline=pipeline,
        pipeline_legacy=pipeline_legacy,
        scenes_status=scenes_status,
        scenes_key=scenes_key,
        scenes_url=scenes_url,
        scene_pack=scene_pack,
        deliverables=deliverables,
        target_profile=target_profile,
        origin_text=origin_text,
        subtitles_text=subtitles_text,
        normalized_source_text=normalized_source_text,
        text_audio_warning=audio_warning,
        audio_error=audio_error,
        no_dub=no_dub,
        no_dub_reason=no_dub_reason,
        no_dub_compose_allowed=no_dub_compose_allowed,
        composed_ready=composed_ready,
        composed_reason=composed_reason,
        final_info=final_info,
        historical_final=historical_final,
        compose_last=compose_last,
        composed=composed,
    )
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
    attach_final_url(payload, final_url)
    composed_ready = bool(composed_ready)
    payload["composed_ready"] = composed_ready
    payload["composed_reason"] = "ready" if composed_ready else "not_ready"
    sync_final_deliverable_projection(
        payload,
        composed_ready=composed_ready,
        final_url=final_url,
        historical_final=historical_final,
    )
    attach_task_aliases(payload, task, task_id)
    payload = state_computer(task_runtime, payload)
    apply_ready_gate_compose_projection(payload)
    if backfill_compose_done(repo, task_id, task, bool(payload.get("composed_ready"))):
        latest = repo.get(task_id) or task
        latest_runtime = dict(latest)
        latest_lane = subtitle_lane_loader(task_id, latest)
        latest_runtime["target_subtitle_current"] = bool(latest_lane.get("target_subtitle_current"))
        latest_runtime["target_subtitle_current_reason"] = latest_lane.get("target_subtitle_current_reason")
        payload = state_computer(latest_runtime, payload)
        apply_ready_gate_compose_projection(payload)
        task = latest

    final_url = str(
        payload.get("final_url")
        or (payload.get("media", {}) or {}).get("final_url")
        or ""
    ).strip()
    apply_ready_gate_composed_projection(payload, final_url=final_url)
    payload["line"] = line_binding_loader(task).to_payload()
    advisory = maybe_build_hot_follow_advisory(task, payload)
    if advisory is not None:
        payload["advisory"] = advisory
    payload.update(operational_defaults_loader())
    payload.update(workbench_ui_loader(task, settings_obj))
    return validate_hot_follow_workbench_response(payload)
