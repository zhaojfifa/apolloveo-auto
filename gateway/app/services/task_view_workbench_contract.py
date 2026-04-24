"""Hot Follow workbench payload contract builders.

This module is limited to schema shaping and compatibility aliases for the
Hot Follow workbench hub. It does not read storage, write task truth, or
rewrite authoritative projection after ready-gate evaluation; callers must
pass already-derived L1/L2/L3 facts and state snapshots.
"""

from __future__ import annotations

from typing import Any


def build_hot_follow_compose_plan(task: dict[str, Any], pipeline_config: dict[str, Any]) -> dict[str, Any]:
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
    return compose_plan


def normalize_compose_last(task: dict[str, Any]) -> dict[str, Any]:
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
    return {
        "status": compose_last_status,
        "started_at": task.get("compose_last_started_at"),
        "finished_at": task.get("compose_last_finished_at"),
        "ffmpeg_cmd": task.get("compose_last_ffmpeg_cmd"),
        "error": task.get("compose_last_error") or task.get("compose_error"),
    }


def build_pipeline_rows(
    task: dict[str, Any],
    *,
    parse_state: str,
    parse_summary: str,
    subtitles_state: str,
    subtitles_summary: str,
    dub_state: str,
    dub_summary: str,
    pack_state: str,
    pack_summary: str,
    compose_state: str,
    compose_summary: str,
    parse_error: Any,
    subtitles_error: Any,
    dub_error: Any,
    pack_error: Any,
    compose_error: Any,
) -> list[dict[str, Any]]:
    pipeline = [
        {"key": "parse", "label": "Parse", "status": parse_state, "updated_at": task.get("updated_at"), "error": parse_error, "message": parse_summary},
        {"key": "subtitles", "label": "Subtitles", "status": subtitles_state, "updated_at": task.get("updated_at"), "error": subtitles_error, "message": subtitles_summary},
        {"key": "dub", "label": "Dub", "status": dub_state, "updated_at": task.get("updated_at"), "error": dub_error, "message": dub_summary},
        {"key": "pack", "label": "Pack", "status": pack_state, "updated_at": task.get("updated_at"), "error": pack_error, "message": pack_summary},
        {"key": "compose", "label": "Compose", "status": compose_state, "updated_at": task.get("updated_at"), "error": compose_error, "message": compose_summary},
    ]
    for item in pipeline:
        item["state"] = item["status"]
    return pipeline


def build_pipeline_legacy(
    task: dict[str, Any],
    *,
    parse_state: str,
    parse_summary: str,
    subtitles_state: str,
    subtitles_summary: str,
    dub_state: str,
    dub_summary: str,
    pack_state: str,
    pack_summary: str,
    compose_state: str,
    compose_summary: str,
) -> dict[str, Any]:
    return {
        "parse": {"status": parse_state, "summary": parse_summary, "updated_at": task.get("updated_at")},
        "subtitles": {"status": subtitles_state, "summary": subtitles_summary, "updated_at": task.get("updated_at")},
        "audio": {"status": dub_state, "summary": dub_summary, "updated_at": task.get("updated_at")},
        "synthesis": {"status": pack_state, "summary": pack_summary, "updated_at": task.get("updated_at")},
        "compose": {"status": compose_state, "summary": compose_summary, "updated_at": task.get("updated_at")},
    }


def build_hot_follow_workbench_payload(
    *,
    task_id: str,
    task: dict[str, Any],
    pipeline_config: dict[str, Any],
    compose_plan: dict[str, Any],
    scene_outputs: list[Any],
    subtitle_lane: dict[str, Any],
    target_lang_public: str,
    raw_url: str | None,
    mute_url: str | None,
    audio_cfg: dict[str, Any],
    voice_state: dict[str, Any],
    subtitles_state: str,
    dub_state: str,
    pack_state: str,
    compose_state: str,
    pipeline: list[dict[str, Any]],
    pipeline_legacy: dict[str, Any],
    scenes_status: str,
    scenes_key: str | None,
    scenes_url: str | None,
    scene_pack: dict[str, Any],
    deliverables: list[dict[str, Any]] | Any,
    target_profile,
    origin_text: str | None,
    subtitles_text: str | None,
    normalized_source_text: str | None,
    text_audio_warning: str | None,
    audio_error: str | None,
    no_dub: bool,
    no_dub_reason: str | None,
    no_dub_compose_allowed: bool,
    composed_ready: bool,
    composed_reason: str,
    final_info: dict[str, Any],
    historical_final: dict[str, Any],
    compose_last: dict[str, Any],
    composed: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "kind": task.get("kind") or "hot_follow",
        "ui_locale": task.get("ui_lang") or "zh",
        "input": _input_section(task, pipeline_config, target_lang_public),
        "media": _media_section(raw_url=raw_url, mute_url=mute_url, audio_cfg=audio_cfg),
        "pipeline": pipeline,
        "subtitles": _subtitles_section(
            task=task,
            subtitle_lane=subtitle_lane,
            subtitles_state=subtitles_state,
            origin_text=origin_text,
            subtitles_text=subtitles_text,
            normalized_source_text=normalized_source_text,
        ),
        "audio": _audio_section(
            task=task,
            audio_cfg=audio_cfg,
            voice_state=voice_state,
            dub_state=dub_state,
            audio_error=audio_error,
            text_audio_warning=text_audio_warning,
            no_dub=no_dub,
            no_dub_reason=no_dub_reason,
            no_dub_compose_allowed=no_dub_compose_allowed,
        ),
        "scenes": _scenes_section(scenes_status=scenes_status, scenes_key=scenes_key, scenes_url=scenes_url),
        "scene_pack": _scene_pack_section(
            task=task,
            scenes_status=scenes_status,
            scenes_key=scenes_key,
            scenes_url=scenes_url,
            scene_pack=scene_pack,
        ),
        "deliverables": deliverables if isinstance(deliverables, list) else [],
        "target_lang_profile": _target_lang_profile_section(target_profile),
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
        "errors": _errors_section(task=task, composed=composed, text_audio_warning=text_audio_warning),
        "pipeline_legacy": pipeline_legacy,
    }


def _input_section(
    task: dict[str, Any],
    pipeline_config: dict[str, Any],
    target_lang_public: str,
) -> dict[str, Any]:
    return {
        "platform": task.get("platform") or "",
        "source_url": task.get("source_url") or "",
        "title": task.get("title") or "",
        "target_lang": target_lang_public,
        "subtitles_mode": pipeline_config.get("subtitles_mode") or "whisper+gemini",
    }


def _media_section(
    *,
    raw_url: str | None,
    mute_url: str | None,
    audio_cfg: dict[str, Any],
) -> dict[str, Any]:
    return {
        "raw_url": raw_url,
        "source_video_url": raw_url,
        "mute_video_url": mute_url,
        "voiceover_url": audio_cfg.get("tts_voiceover_url") or audio_cfg.get("voiceover_url") or audio_cfg.get("audio_url"),
        "bgm_url": audio_cfg.get("bgm_url"),
        "final_url": None,
        "final_video_url": None,
    }


def _subtitles_section(
    *,
    task: dict[str, Any],
    subtitle_lane: dict[str, Any],
    subtitles_state: str,
    origin_text: str | None,
    subtitles_text: str | None,
    normalized_source_text: str | None,
) -> dict[str, Any]:
    primary_text = str(subtitle_lane.get("primary_editable_text") or "")
    srt_text = primary_text if str(subtitle_lane.get("primary_editable_format") or "srt").strip().lower() == "srt" else ""
    return {
        "origin_text": origin_text or "",
        "raw_source_text": subtitle_lane.get("raw_source_text") or origin_text or "",
        "normalized_source_text": subtitle_lane.get("normalized_source_text") or normalized_source_text or "",
        "parse_source_text": subtitle_lane.get("parse_source_text") or "",
        "parse_source_role": subtitle_lane.get("parse_source_role") or "none",
        "parse_source_authoritative_for_target": bool(subtitle_lane.get("parse_source_authoritative_for_target")),
        "helper_translation": {
            "status": subtitle_lane.get("helper_translate_status"),
            "failed": bool(subtitle_lane.get("helper_translate_failed")),
            "reason": subtitle_lane.get("helper_translate_error_reason"),
            "message": subtitle_lane.get("helper_translate_error_message"),
            "provider": subtitle_lane.get("helper_translate_provider"),
            "visibility": subtitle_lane.get("helper_translate_visibility"),
            "retryable": bool(subtitle_lane.get("helper_translate_retryable")),
            "terminal": bool(subtitle_lane.get("helper_translate_terminal")),
            "input_text": subtitle_lane.get("helper_translate_input_text"),
            "translated_text": subtitle_lane.get("helper_translate_translated_text"),
            "target_lang": subtitle_lane.get("helper_translate_target_lang"),
        },
        "edited_text": primary_text,
        "srt_text": srt_text,
        "primary_editable_text": primary_text,
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
    }


def _audio_section(
    *,
    task: dict[str, Any],
    audio_cfg: dict[str, Any],
    voice_state: dict[str, Any],
    dub_state: str,
    audio_error: str | None,
    text_audio_warning: str | None,
    no_dub: bool,
    no_dub_reason: str | None,
    no_dub_compose_allowed: bool,
) -> dict[str, Any]:
    return {
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
        "warning": text_audio_warning,
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
        "no_dub": bool(no_dub),
        "no_dub_reason": no_dub_reason,
        "no_dub_compose_allowed": no_dub_compose_allowed,
    }


def _scenes_section(
    *,
    scenes_status: str,
    scenes_key: str | None,
    scenes_url: str | None,
) -> dict[str, Any]:
    return {
        "status": scenes_status,
        "scenes_key": scenes_key,
        "download_url": scenes_url,
    }


def _scene_pack_section(
    *,
    task: dict[str, Any],
    scenes_status: str,
    scenes_key: str | None,
    scenes_url: str | None,
    scene_pack: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": scenes_status,
        "exists": bool(scenes_key),
        "key": scenes_key,
        "asset_version": scene_pack.get("asset_version"),
        "error": task.get("scenes_error"),
        "error_reason": None,
        "download_url": scenes_url,
        "scenes_url": scenes_url,
        "deprecated": True,
    }


def _target_lang_profile_section(target_profile) -> dict[str, Any]:
    return {
        "target_lang": target_profile.public_lang,
        "internal_lang": target_profile.internal_lang,
        "display_name": target_profile.display_name,
        "subtitle_filename": target_profile.subtitle_filename,
        "subtitle_txt_filename": target_profile.subtitle_txt_filename,
        "dub_filename": target_profile.dub_filename,
        "allowed_voice_options": list(target_profile.allowed_voice_options),
        "default_voice_by_provider": dict(target_profile.default_voice_by_provider),
    }


def _errors_section(
    *,
    task: dict[str, Any],
    composed: dict[str, Any],
    text_audio_warning: str | None,
) -> dict[str, Any]:
    return {
        "audio": {"reason": task.get("error_reason"), "message": task.get("dub_error") or text_audio_warning},
        "pack": {"reason": task.get("error_reason"), "message": task.get("pack_error")},
        "compose": {"reason": composed.get("compose_error_reason"), "message": composed.get("compose_error_message")},
    }


def attach_task_aliases(payload: dict[str, Any], task: dict[str, Any], task_id: str) -> None:
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


def apply_ready_gate_compose_projection(payload: dict[str, Any]) -> None:
    ready_gate = payload.get("ready_gate") if isinstance(payload.get("ready_gate"), dict) else {}
    compose_allowed = bool(ready_gate.get("compose_allowed"))
    compose_allowed_reason = str(
        ready_gate.get("compose_allowed_reason")
        or ready_gate.get("compose_reason")
        or "route_not_allowed"
    )
    payload["compose_allowed"] = compose_allowed
    payload["compose_allowed_reason"] = compose_allowed_reason
    if isinstance(payload.get("ready_gate"), dict):
        payload["ready_gate"]["compose_allowed"] = compose_allowed
        payload["ready_gate"]["compose_allowed_reason"] = compose_allowed_reason
