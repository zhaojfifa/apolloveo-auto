"""Hot Follow task-view presenters.

Presenter layers consume authoritative projection data and shape surface
payloads without recomputing separate business truths.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Mapping

from gateway.app.config import get_settings
from gateway.app.services.artifact_storage import object_exists
from gateway.app.services.contract_runtime import (
    apply_projection_runtime,
    get_contract_runtime_refs,
    get_projection_rules_runtime,
    select_presentation_final,
)
from gateway.app.services.hot_follow_skills_advisory import (
    maybe_build_hot_follow_advisory,
)
from gateway.app.services.hot_follow_workbench_presenter import (
    build_hot_follow_artifact_facts,
    build_hot_follow_current_attempt_summary,
    build_hot_follow_operator_summary,
)
from gateway.app.services.line_binding_service import get_line_runtime_binding
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state
from gateway.app.services.task_view_helpers import (
    _build_copy_bundle,
    _publish_sop_markdown,
    backfill_compose_done_if_final_ready,
    deliverable_url,
    download_code,
    hot_follow_terminal_no_dub_projection,
    op_gate_enabled,
)
from gateway.app.services.task_view_projection import (
    build_hot_follow_workbench_projection,
    hf_deliverables,
    hf_pipeline_state,
)
from gateway.app.services.task_view_workbench_contract import (
    apply_ready_gate_compose_projection,
    attach_task_aliases,
    build_hot_follow_workbench_payload,
    build_pipeline_legacy,
    build_pipeline_rows,
)
from gateway.app.services.tts_policy import normalize_provider, normalize_target_lang, public_target_lang
from gateway.app.services.subtitle_helpers import (
    hf_dual_channel_state,
    hf_load_normalized_source_text,
    hf_load_origin_subtitles_text,
    hf_load_subtitles_text,
    hf_subtitle_terminal_success,
    hf_subtitle_lane_state,
)
from gateway.app.services.task_view_helpers import (
    compute_composed_state,
    resolve_hub_final_url,
    scene_pack_info,
    task_endpoint,
)
from gateway.app.services.voice_service import (
    hf_audio_config,
    hf_screen_text_candidate_summary,
    hf_source_audio_lane_summary,
    hf_source_audio_semantics,
)
from gateway.app.services.voice_state import (
    build_hot_follow_voice_options,
    collect_voice_execution_state,
    hf_persisted_audio_state,
)
from gateway.app.utils.pipeline_config import parse_pipeline_config

logger = logging.getLogger(__name__)

_PUBLISH_DELIVERABLE_LABELS = {
    "pack": "pack.zip",
    "scenes": "scenes.zip",
    "origin_subtitle": "origin.srt",
    "subtitle": "mm.srt",
    "audio": "mm_audio",
    "final": "final.mp4",
}

_PUBLISH_DELIVERABLE_KEYS = {
    "pack": "pack_zip",
    "scenes": "scenes_zip",
    "origin_subtitle": "origin_srt",
    "subtitle": "mm_srt",
    "audio": "mm_audio",
    "final": "final_mp4",
}


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
    dual_channel_state_loader=hf_dual_channel_state,
    source_audio_lane_loader=hf_source_audio_lane_summary,
    screen_text_candidate_loader=hf_screen_text_candidate_summary,
    voice_execution_state_loader=collect_voice_execution_state,
    pipeline_state_loader=hf_pipeline_state,
    object_exists_fn=object_exists,
    source_audio_semantics_loader=hf_source_audio_semantics,
) -> dict[str, Any]:
    task_id = str(task.get("task_id") or task.get("id") or "")
    subtitle_lane = subtitle_lane_loader(task_id, task)
    task_runtime = dict(task)
    task_runtime["target_subtitle_current"] = bool(subtitle_lane.get("target_subtitle_current"))
    task_runtime["target_subtitle_current_reason"] = subtitle_lane.get("target_subtitle_current_reason")
    if hf_subtitle_terminal_success(subtitle_lane):
        task_runtime["subtitles_status"] = "ready"
        task_runtime["subtitles_error"] = None
        task_runtime["subtitles_error_reason"] = None
    subtitles_state, _ = pipeline_state_loader(task_runtime, "subtitles", subtitle_lane=subtitle_lane)
    subtitles_step_done = subtitles_state in {"done", "ready", "success", "completed", "failed", "error"}
    route_state = dual_channel_state_loader(task_id, task_runtime, subtitle_lane, subtitles_step_done=subtitles_step_done)
    audio_lane = source_audio_lane_loader(task, route_state)
    screen_text_candidate = screen_text_candidate_loader(subtitle_lane, route_state)
    voice_state = voice_execution_state_loader(task_runtime, settings)
    final_key = str(task_runtime.get("final_video_key") or task_runtime.get("final_video_path") or "").strip()
    final_exists = bool(final_key and object_exists_fn(final_key))
    compose_status = str(task.get("compose_status") or task.get("compose_last_status") or "").strip() or "never"
    lipsync_enabled = os.getenv("HF_LIPSYNC_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    pipeline_config = parse_pipeline_config(task.get("pipeline_config"))
    no_dub, no_dub_reason, no_dub_message = hot_follow_terminal_no_dub_projection(
        pipeline_config=pipeline_config,
        task=task,
        route_state=route_state,
        subtitle_lane=subtitle_lane,
        voice_state=voice_state,
    )
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
    workbench_ui_loader=collect_hot_follow_workbench_ui,
    voice_options_builder=build_hot_follow_voice_options,
) -> dict[str, Any]:
    try:
        return workbench_ui_loader(task, settings)
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
                "voice_options_by_provider": voice_options_builder(
                    settings, normalize_target_lang(task.get("target_lang") or task.get("content_lang") or "mm")
                ),
                "compose_status": str(task.get("compose_status") or "never"),
                "final_exists": False,
                "lipsync_enabled": False,
                "lipsync_status": "off",
            }
        )
        return payload


def hf_rerun_presentation_state(
    task: dict,
    voice_state: dict[str, Any] | None,
    final_info: dict[str, Any] | None,
    historical_final: dict[str, Any] | None,
    dub_status: str | None,
    current_attempt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    voice = voice_state or {}
    l3_current_attempt = current_attempt or {}
    refs = get_contract_runtime_refs(task)
    projection_runtime = (
        get_projection_rules_runtime(refs.projection_rules_ref)
        if refs.projection_rules_ref
        else None
    )
    final_payload = select_presentation_final(
        final_info,
        historical_final,
        projection_runtime=projection_runtime,
    )
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
            "dub_status": str(l3_current_attempt.get("dub_status") or dub_status or "").strip().lower() or "never",
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
    deliverable_url_loader=deliverable_url,
) -> dict[str, Any]:
    return build_hot_follow_artifact_facts(
        task_id,
        task,
        final_info=final_info,
        historical_final=historical_final,
        persisted_audio=persisted_audio,
        subtitle_lane=subtitle_lane,
        scene_pack=scene_pack,
        deliverable_url=deliverable_url_loader,
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
    artifact_facts_loader=hf_artifact_facts,
    current_attempt_loader=hf_current_attempt_summary,
    operator_summary_loader=hf_operator_summary,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    try:
        artifact_facts = artifact_facts_loader(
            task_id,
            task,
            final_info=final_info,
            historical_final=historical_final,
            persisted_audio=persisted_audio,
            subtitle_lane=subtitle_lane,
            scene_pack=scene_pack,
        )
        current_attempt = current_attempt_loader(
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
        operator_summary = operator_summary_loader(
            artifact_facts=artifact_facts,
            current_attempt=current_attempt,
            no_dub=no_dub,
            subtitle_ready=bool((subtitle_lane or {}).get("subtitle_ready")),
        )
        return artifact_facts, current_attempt, operator_summary
    except Exception:
        logger.exception("HF_PRESENTATION_AGGREGATES_SAFE_FALLBACK task=%s", task_id)
        return {}, {}, {}


def _build_hot_follow_authoritative_state(
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
    state_computer=compute_hot_follow_state,
    projection_builder=build_hot_follow_workbench_projection,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    projection = projection_builder(
        task_id,
        repo,
        settings=settings,
        object_exists_fn=object_exists_fn,
        task_endpoint_loader=task_endpoint_loader,
        subtitle_lane_loader=subtitle_lane_loader,
        composed_state_loader=composed_state_loader,
        pipeline_state_loader=pipeline_state_loader,
        scene_pack_info_loader=scene_pack_info_loader,
        subtitles_text_loader=subtitles_text_loader,
        origin_subtitles_text_loader=origin_subtitles_text_loader,
        normalized_source_text_loader=normalized_source_text_loader,
        dual_channel_state_loader=dual_channel_state_loader,
        audio_config_loader=audio_config_loader,
        voice_execution_state_loader=voice_execution_state_loader,
        persisted_audio_state_loader=persisted_audio_state_loader,
        deliverables_loader=deliverables_loader,
        resolve_final_url_loader=resolve_final_url_loader,
    )
    task = projection["task"]
    task_runtime = projection["task_runtime"]
    pipeline = build_pipeline_rows(
        task,
        parse_state=projection["parse_state"],
        parse_summary=projection["parse_summary"],
        subtitles_state=projection["subtitles_state"],
        subtitles_summary=projection["subtitles_summary"],
        dub_state=projection["dub_state"],
        dub_summary=projection["dub_summary"],
        pack_state=projection["pack_state"],
        pack_summary=projection["pack_summary"],
        compose_state=projection["compose_state"],
        compose_summary=projection["compose_summary"],
        parse_error=projection["parse_error"],
        subtitles_error=projection["subtitles_error"],
        dub_error=projection["dub_error"],
        pack_error=projection["pack_error"],
        compose_error=projection["compose_error"],
    )
    pipeline_legacy = build_pipeline_legacy(
        task,
        parse_state=projection["parse_state"],
        parse_summary=projection["parse_summary"],
        subtitles_state=projection["subtitles_state"],
        subtitles_summary=projection["subtitles_summary"],
        dub_state=projection["dub_state"],
        dub_summary=projection["dub_summary"],
        pack_state=projection["pack_state"],
        pack_summary=projection["pack_summary"],
        compose_state=projection["compose_state"],
        compose_summary=projection["compose_summary"],
    )
    payload = build_hot_follow_workbench_payload(
        task_id=task_id,
        task=task,
        pipeline_config=projection["pipeline_config"],
        compose_plan=projection["compose_plan"],
        scene_outputs=projection["scene_outputs"],
        subtitle_lane=projection["subtitle_lane"],
        target_lang_public=public_target_lang(projection["target_lang_internal"]),
        raw_url=projection["raw_url"],
        mute_url=projection["mute_url"],
        audio_cfg=projection["audio_cfg"],
        voice_state=projection["voice_state"],
        subtitles_state=projection["subtitles_state"],
        dub_state=projection["dub_state"],
        pack_state=projection["pack_state"],
        compose_state=projection["compose_state"],
        pipeline=pipeline,
        pipeline_legacy=pipeline_legacy,
        scenes_status=projection["scenes_status"],
        scenes_key=projection["scenes_key"],
        scenes_url=projection["scenes_url"],
        scene_pack=projection["scene_pack"],
        deliverables=projection["deliverables"],
        target_profile=projection["target_profile"],
        origin_text=projection["origin_text"],
        subtitles_text=projection["subtitles_text"],
        normalized_source_text=projection["normalized_source_text"],
        text_audio_warning=projection["audio_warning"],
        audio_error=projection["audio_error"],
        no_dub=projection["no_dub"],
        no_dub_reason=projection["no_dub_reason"],
        no_dub_compose_allowed=projection["no_dub_compose_allowed"],
        composed_ready=projection["composed_ready"],
        composed_reason=projection["composed_reason"],
        final_info=projection["final_info"],
        historical_final=projection["historical_final"],
        compose_last=projection["compose_last"],
        composed=projection["composed"],
    )
    payload["final_stale_reason"] = projection["final_stale_reason"]
    payload["final_fresh"] = bool(projection["composed"].get("final_fresh"))
    artifact_facts, current_attempt, operator_summary = presentation_aggregates_loader(
        task_id,
        projection["task_runtime"],
        final_info=projection["final_info"],
        historical_final=projection["historical_final"],
        persisted_audio=projection["persisted_audio"],
        subtitle_lane=projection["subtitle_lane"],
        scene_pack=projection["scene_pack"],
        voice_state=projection["voice_state"],
        dub_status=str(projection["dub_state"]),
        compose_status=projection["compose_state"],
        composed_reason=projection["composed_reason"],
        final_stale_reason=projection["final_stale_reason"],
        no_dub=bool((payload.get("audio") or {}).get("no_dub")),
    )
    payload["artifact_facts"] = artifact_facts
    payload["current_attempt"] = current_attempt
    payload["operator_summary"] = operator_summary
    payload["presentation"] = presentation_state_loader(
        task,
        projection["voice_state"],
        projection["final_info"],
        projection["historical_final"],
        projection["dub_state"],
        current_attempt=current_attempt,
    )
    return task, projection, state_computer(task_runtime, payload)


def _publish_hub_deliverables(
    task_id: str,
    task: dict[str, Any],
    authoritative_state: dict[str, Any],
) -> dict[str, Any]:
    deliverables: dict[str, Any] = {}
    for row in authoritative_state.get("deliverables") or []:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or "").strip().lower()
        key = _PUBLISH_DELIVERABLE_KEYS.get(kind)
        label = _PUBLISH_DELIVERABLE_LABELS.get(kind)
        if not key or not label:
            continue
        url = row.get("url") or row.get("open_url") or row.get("download_url")
        if not url:
            continue
        item = {
            "label": label,
            "url": url,
            "open_url": row.get("open_url") or row.get("url"),
            "download_url": row.get("download_url"),
        }
        if kind == "final":
            item["status"] = row.get("status")
            item["state"] = row.get("state")
        deliverables[key] = item

    for key, label in (
        ("mm_txt", "mm.txt"),
        ("edit_bundle_zip", "scenes_bundle.zip"),
    ):
        download_url = deliverable_url(task_id, task, key)
        open_url = None
        if key == "edit_bundle_zip":
            open_url = deliverable_url(task_id, task, key)
        if not download_url and not open_url:
            continue
        item = {"label": label, "url": download_url or open_url}
        item["download_url"] = download_url
        item["open_url"] = open_url
        if key == "edit_bundle_zip":
            item["artifact"] = "scenes_bundle"
            item["description"] = "Scenes package for re-editing / advanced workflow"
        deliverables[key] = item
    return deliverables


def _apply_hot_follow_projection_runtime(
    task: dict[str, Any],
    payload: dict[str, Any],
    *,
    surface: str,
) -> dict[str, Any]:
    refs = get_contract_runtime_refs(task)
    if not refs.projection_rules_ref:
        return dict(payload)
    runtime = get_projection_rules_runtime(refs.projection_rules_ref)
    return apply_projection_runtime(dict(payload), surface=surface, projection_runtime=runtime)


def _operator_surfaces_for_publish_hub(
    task: dict[str, Any],
    authoritative_state: dict[str, Any],
) -> dict[str, Any]:
    """Phase 3B Delivery projection. Additive, read-only.

    Lazy import keeps the projection module out of every cold import path
    of this presenter (the wiring layer pulls in the full projection
    package).
    """
    from gateway.app.services.operator_visible_surfaces import (
        build_operator_surfaces_for_publish_hub,
    )

    # Recovery PR-3: Matrix Script tasks read their persisted publish-feedback
    # closure (if any) via the binding layer so `publish_status_mirror` becomes
    # operator-meaningful for matrix_script. Hot Follow / Digital Anchor / other
    # lines preserve the legacy `None` (empty `not_published` mirror) — the
    # binding service is matrix_script-only and read-only at this seam.
    closure: Mapping[str, Any] | None = None
    kind = str(
        task.get("kind") or task.get("category_key") or task.get("platform") or ""
    ).strip().lower()
    if kind == "matrix_script":
        try:
            from gateway.app.services.matrix_script.closure_binding import (
                get_closure_view_for_task,
            )

            task_id = str(task.get("task_id") or task.get("id") or "")
            if task_id:
                closure = get_closure_view_for_task(task_id)
        except Exception:
            # Defense-in-depth: presenter must never crash the publish hub if
            # the closure binding raises.
            closure = None
    elif kind == "digital_anchor":
        try:
            from gateway.app.services.digital_anchor.closure_binding import (
                get_closure_view_for_task as _da_get_closure_view_for_task,
            )

            task_id = str(task.get("task_id") or task.get("id") or "")
            if task_id:
                closure = _da_get_closure_view_for_task(task_id)
        except Exception:
            closure = None
    return build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state=authoritative_state,
        publish_feedback_closure=closure,
    )


def _build_hot_follow_publish_surface_payload(
    task_id: str,
    task: dict[str, Any],
    authoritative_state: dict[str, Any],
    *,
    resolve_final_url_loader=resolve_hub_final_url,
    copy_bundle_builder=_build_copy_bundle,
    sop_markdown_builder=_publish_sop_markdown,
    download_code_loader=download_code,
) -> dict[str, Any]:
    deliverables = _publish_hub_deliverables(task_id, task, authoritative_state)
    final_preview_url = resolve_final_url_loader(task_id, authoritative_state)
    if final_preview_url:
        final_item = dict(deliverables.get("final_mp4") or {"label": "final.mp4"})
        final_item["url"] = final_preview_url
        final_item["open_url"] = final_preview_url
        if not final_item.get("download_url"):
            final_item["download_url"] = deliverable_url(task_id, task, "final_mp4")
        deliverables["final_mp4"] = final_item

    short_code = download_code_loader(task_id)
    short_url = f"/d/{short_code}"
    scene_pack = authoritative_state.get("scene_pack") if isinstance(authoritative_state.get("scene_pack"), dict) else {}
    return {
        "task_id": task_id,
        "gate_enabled": op_gate_enabled(),
        "media": {
            "final_video_url": final_preview_url,
            "final_url": final_preview_url,
        },
        "final_url": final_preview_url,
        "final_video_url": final_preview_url,
        "deliverables": deliverables,
        "composed_ready": bool(authoritative_state.get("composed_ready")),
        "composed_reason": str(
            authoritative_state.get("composed_reason")
            or ("ready" if authoritative_state.get("composed_ready") else "not_ready")
        ),
        "compose_status": authoritative_state.get("compose_status"),
        "ready_gate": dict(authoritative_state.get("ready_gate") or {}),
        "final": authoritative_state.get("final") or {"exists": False},
        "historical_final": authoritative_state.get("historical_final") or {"exists": False},
        "final_fresh": bool(authoritative_state.get("final_fresh")),
        "final_stale_reason": authoritative_state.get("final_stale_reason"),
        "scene_pack": scene_pack,
        "scene_pack_pending_reason": authoritative_state.get("scene_pack_pending_reason"),
        "scene_pack_action_url": f"/tasks/{task_id}",
        "copy_bundle": copy_bundle_builder(task),
        "download_code": short_code,
        "mobile": {
            "qr_target": short_url,
            "short_link": short_url,
            "short_url": short_url,
            "qr_url": short_url,
        },
        "sop_markdown": sop_markdown_builder(),
        "archive": {
            "publish_provider": task.get("publish_provider") or "-",
            "publish_key": task.get("publish_key") or "-",
            "publish_status": task.get("publish_status") or "-",
            "publish_url": task.get("publish_url") or "-",
            "published_at": task.get("published_at") or "-",
        },
        # Phase 3B operator-visible surface projection. Single derived
        # publish gate + read-only publish-status mirror. Optional items
        # never reach this gate (enumerated separately on `deliverables`).
        "operator_surfaces": _operator_surfaces_for_publish_hub(task, authoritative_state),
    }


def build_hot_follow_publish_hub(
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
    state_computer=compute_hot_follow_state,
    backfill_compose_done=backfill_compose_done_if_final_ready,
    line_binding_loader=get_line_runtime_binding,
    projection_builder=build_hot_follow_workbench_projection,
    publish_surface_builder=_build_hot_follow_publish_surface_payload,
) -> dict[str, Any]:
    task, _projection, authoritative_state = _build_hot_follow_authoritative_state(
        task_id,
        repo,
        settings=settings,
        object_exists_fn=object_exists_fn,
        task_endpoint_loader=task_endpoint_loader,
        subtitle_lane_loader=subtitle_lane_loader,
        composed_state_loader=composed_state_loader,
        pipeline_state_loader=pipeline_state_loader,
        scene_pack_info_loader=scene_pack_info_loader,
        subtitles_text_loader=subtitles_text_loader,
        origin_subtitles_text_loader=origin_subtitles_text_loader,
        normalized_source_text_loader=normalized_source_text_loader,
        dual_channel_state_loader=dual_channel_state_loader,
        audio_config_loader=audio_config_loader,
        voice_execution_state_loader=voice_execution_state_loader,
        persisted_audio_state_loader=persisted_audio_state_loader,
        deliverables_loader=deliverables_loader,
        presentation_aggregates_loader=presentation_aggregates_loader,
        presentation_state_loader=presentation_state_loader,
        resolve_final_url_loader=resolve_final_url_loader,
        state_computer=state_computer,
        projection_builder=projection_builder,
    )
    if backfill_compose_done(repo, task_id, task, bool(authoritative_state.get("composed_ready"))):
        task, _projection, authoritative_state = _build_hot_follow_authoritative_state(
            task_id,
            repo,
            settings=settings,
            object_exists_fn=object_exists_fn,
            task_endpoint_loader=task_endpoint_loader,
            subtitle_lane_loader=subtitle_lane_loader,
            composed_state_loader=composed_state_loader,
            pipeline_state_loader=pipeline_state_loader,
            scene_pack_info_loader=scene_pack_info_loader,
            subtitles_text_loader=subtitles_text_loader,
            origin_subtitles_text_loader=origin_subtitles_text_loader,
            normalized_source_text_loader=normalized_source_text_loader,
            dual_channel_state_loader=dual_channel_state_loader,
            audio_config_loader=audio_config_loader,
            voice_execution_state_loader=voice_execution_state_loader,
            persisted_audio_state_loader=persisted_audio_state_loader,
            deliverables_loader=deliverables_loader,
            presentation_aggregates_loader=presentation_aggregates_loader,
            presentation_state_loader=presentation_state_loader,
            resolve_final_url_loader=resolve_final_url_loader,
            state_computer=state_computer,
            projection_builder=projection_builder,
        )
    authoritative_state = _apply_hot_follow_projection_runtime(
        task,
        authoritative_state,
        surface="publish",
    )
    payload = publish_surface_builder(
        task_id,
        task,
        authoritative_state,
        resolve_final_url_loader=resolve_final_url_loader,
    )
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
    task, projection, payload = _build_hot_follow_authoritative_state(
        task_id,
        repo,
        settings=settings,
        object_exists_fn=object_exists_fn,
        task_endpoint_loader=task_endpoint_loader,
        subtitle_lane_loader=subtitle_lane_loader,
        composed_state_loader=composed_state_loader,
        pipeline_state_loader=pipeline_state_loader,
        scene_pack_info_loader=scene_pack_info_loader,
        subtitles_text_loader=subtitles_text_loader,
        origin_subtitles_text_loader=origin_subtitles_text_loader,
        normalized_source_text_loader=normalized_source_text_loader,
        dual_channel_state_loader=dual_channel_state_loader,
        audio_config_loader=audio_config_loader,
        voice_execution_state_loader=voice_execution_state_loader,
        persisted_audio_state_loader=persisted_audio_state_loader,
        deliverables_loader=deliverables_loader,
        presentation_aggregates_loader=presentation_aggregates_loader,
        presentation_state_loader=presentation_state_loader,
        resolve_final_url_loader=resolve_final_url_loader,
        state_computer=state_computer,
    )
    if backfill_compose_done(repo, task_id, task, bool(payload.get("composed_ready"))):
        task, projection, payload = _build_hot_follow_authoritative_state(
            task_id,
            repo,
            settings=settings,
            object_exists_fn=object_exists_fn,
            task_endpoint_loader=task_endpoint_loader,
            subtitle_lane_loader=subtitle_lane_loader,
            composed_state_loader=composed_state_loader,
            pipeline_state_loader=pipeline_state_loader,
            scene_pack_info_loader=scene_pack_info_loader,
            subtitles_text_loader=subtitles_text_loader,
            origin_subtitles_text_loader=origin_subtitles_text_loader,
            normalized_source_text_loader=normalized_source_text_loader,
            dual_channel_state_loader=dual_channel_state_loader,
            audio_config_loader=audio_config_loader,
            voice_execution_state_loader=voice_execution_state_loader,
            persisted_audio_state_loader=persisted_audio_state_loader,
            deliverables_loader=deliverables_loader,
            presentation_aggregates_loader=presentation_aggregates_loader,
            presentation_state_loader=presentation_state_loader,
            resolve_final_url_loader=resolve_final_url_loader,
            state_computer=state_computer,
        )
    payload = _apply_hot_follow_projection_runtime(task, payload, surface="workbench")
    apply_ready_gate_compose_projection(payload)
    attach_task_aliases(payload, task, task_id)
    payload["line"] = line_binding_loader(task).to_payload()
    advisory = maybe_build_hot_follow_advisory(task, payload)
    if advisory is not None:
        payload["advisory"] = advisory
    payload.update(operational_defaults_loader())
    payload.update(workbench_ui_loader(task, projection["settings"]))
    return payload
