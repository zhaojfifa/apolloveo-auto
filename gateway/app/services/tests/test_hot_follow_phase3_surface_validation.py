from __future__ import annotations

from types import SimpleNamespace

from gateway.app.services.task_view_presenters import (
    _build_hot_follow_publish_surface_payload,
    build_hot_follow_publish_hub,
    build_hot_follow_workbench_hub,
)
from gateway.app.services.task_view_projection import hf_deliverables


URL_SAMPLE_ID = "hf-phase3-url-origin-only"
LOCAL_SAMPLE_ID = "hf-phase3-local-helper-telemetry"
MANUAL_SAVE_SAMPLE_ID = "hf-phase3-manual-save-vi-materialized"


ZH_SRT = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
VI_SRT = "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"


class _Repo:
    def __init__(self, samples: dict[str, dict]):
        self.samples = {task_id: dict(task) for task_id, task in samples.items()}

    def get(self, task_id: str):
        task = self.samples.get(task_id)
        return dict(task) if task else None

    def upsert(self, task_id: str, updates: dict):
        self.samples[task_id].update(updates)


def _settings():
    return SimpleNamespace(
        dub_provider="azure-speech",
        edge_tts_voice_map={"vi_female_1": "vi-VN-HoaiMyNeural"},
        azure_tts_voice_map={"vi_female_1": "vi-VN-HoaiMyNeural"},
    )


def _sample_tasks() -> dict[str, dict]:
    return {
        URL_SAMPLE_ID: {
            "task_id": URL_SAMPLE_ID,
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "platform": "douyin",
            "source_url": "https://example.test/hot-follow/url-origin-only",
            "target_lang": "vi",
            "content_lang": "vi",
            "raw_path": f"deliver/tasks/{URL_SAMPLE_ID}/raw.mp4",
            "origin_srt_path": f"deliver/tasks/{URL_SAMPLE_ID}/origin.srt",
            "mm_srt_path": f"deliver/tasks/{URL_SAMPLE_ID}/stale-legacy-vi.srt",
            "subtitles_status": "ready",
            "subtitles_error": None,
            "subtitle_stage_owner": "hot_follow_subtitle_stage_v1",
            "origin_subtitle_artifact_exists": True,
            "target_subtitle_artifact_exists": False,
            "target_subtitle_materialized": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
            "subtitle_helper_status": "helper_output_pending",
        },
        LOCAL_SAMPLE_ID: {
            "task_id": LOCAL_SAMPLE_ID,
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "platform": "local",
            "source_type": "local",
            "source_filename": "operator-local-upload.mp4",
            "target_lang": "vi",
            "content_lang": "vi",
            "raw_path": f"deliver/tasks/{LOCAL_SAMPLE_ID}/raw.mp4",
            "origin_srt_path": f"deliver/tasks/{LOCAL_SAMPLE_ID}/origin.srt",
            "subtitles_status": "running",
            "subtitle_stage_owner": "hot_follow_subtitle_stage_v1",
            "origin_subtitle_artifact_exists": True,
            "target_subtitle_artifact_exists": False,
            "target_subtitle_materialized": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "subtitle_helper_status": "failed",
            "subtitle_helper_error_reason": "helper_translate_provider_exhausted",
            "subtitle_helper_error_message": "quota exhausted",
            "subtitle_helper_input_text": ZH_SRT,
        },
        MANUAL_SAVE_SAMPLE_ID: {
            "task_id": MANUAL_SAVE_SAMPLE_ID,
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "platform": "hot_follow",
            "source_url": "https://example.test/hot-follow/manual-save",
            "target_lang": "vi",
            "content_lang": "vi",
            "raw_path": f"deliver/tasks/{MANUAL_SAVE_SAMPLE_ID}/raw.mp4",
            "origin_srt_path": f"deliver/tasks/{MANUAL_SAVE_SAMPLE_ID}/origin.srt",
            "mm_srt_path": f"deliver/tasks/{MANUAL_SAVE_SAMPLE_ID}/vi.srt",
            "vi_srt_path": f"deliver/tasks/{MANUAL_SAVE_SAMPLE_ID}/vi.srt",
            "subtitles_status": "ready",
            "subtitles_error": None,
            "subtitle_stage_owner": "hot_follow_subtitle_stage_v1",
            "subtitle_stage_action": "manual_target_subtitle_materialize",
            "subtitle_stage_materialized_at": "2026-04-30T01:00:00+00:00",
            "origin_subtitle_artifact_exists": True,
            "target_subtitle_artifact_exists": True,
            "target_subtitle_materialized": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current": True,
            "target_subtitle_current_reason": "ready",
            "subtitles_content_hash": "HASH_VI_NEW",
            "dub_status": "pending",
            "dub_source_subtitles_content_hash": None,
            "dub_source_subtitle_updated_at": None,
            "compose_status": "pending",
            "compose_error": None,
            "final_video_key": f"deliver/tasks/{MANUAL_SAVE_SAMPLE_ID}/final.mp4",
            "final_fresh": False,
            "final_stale_reason": "dub_stale_after_subtitles",
        },
    }


def _object_exists(key: str) -> bool:
    return bool(str(key or "").strip())


def _task_endpoint(task_id: str, kind: str) -> str:
    return f"/v1/tasks/{task_id}/{kind}"


def _signed_url(task_id: str, kind: str) -> str:
    return f"/op/tasks/{task_id}/{kind}"


def _download_url(key: str) -> str:
    return f"/download/{key}"


def _deliverable_url(task_id: str, task: dict, kind: str) -> str | None:
    if kind == "mm_txt":
        key = str(task.get("mm_srt_path") or "").strip()
        return f"/op/tasks/{task_id}/mm_txt" if key and task.get("target_subtitle_current") else None
    if kind == "edit_bundle_zip":
        return f"/op/tasks/{task_id}/publish_bundle"
    if kind == "final_mp4":
        return f"/op/tasks/{task_id}/final_mp4" if task.get("final_fresh") else None
    return None


def _subtitle_lane(task_id: str, task: dict) -> dict:
    has_target = bool(task.get("target_subtitle_artifact_exists") and task.get("target_subtitle_current"))
    helper_status = str(task.get("subtitle_helper_status") or "").strip() or None
    return {
        "raw_source_text": ZH_SRT,
        "normalized_source_text": ZH_SRT,
        "parse_source_text": ZH_SRT,
        "edited_text": VI_SRT if has_target else "",
        "srt_text": VI_SRT if has_target else "",
        "primary_editable_text": VI_SRT if has_target else "",
        "primary_editable_format": "srt",
        "dub_input_text": VI_SRT if has_target else "",
        "dub_input_source": "target_subtitle" if has_target else None,
        "actual_burn_subtitle_source": "vi.srt" if has_target else None,
        "subtitle_artifact_exists": bool(has_target),
        "subtitle_ready": bool(has_target),
        "subtitle_ready_reason": str(task.get("target_subtitle_current_reason") or "subtitle_missing"),
        "target_subtitle_current": bool(task.get("target_subtitle_current")),
        "target_subtitle_current_reason": str(task.get("target_subtitle_current_reason") or "subtitle_missing"),
        "target_subtitle_authoritative_source": bool(task.get("target_subtitle_authoritative_source")),
        "target_subtitle_source_copy": False,
        "helper_translate_status": helper_status,
        "helper_translate_output_state": helper_status,
        "helper_translate_provider_health": "provider_retryable_failure" if task.get("subtitle_helper_error_reason") else "provider_ok",
        "helper_translate_failed": bool(task.get("subtitle_helper_error_reason")),
        "helper_translate_error_reason": task.get("subtitle_helper_error_reason"),
        "helper_translate_error_message": task.get("subtitle_helper_error_message"),
        "helper_translate_retryable": bool(helper_status),
        "helper_translate_terminal": False,
        "helper_translate_warning_only": False,
        "helper_translate_input_text": task.get("subtitle_helper_input_text"),
        "helper_translate_translated_text": None,
        "helper_translate_target_lang": task.get("target_lang"),
    }


def _voice_state(task: dict, _settings) -> dict:
    target_ready = bool(task.get("target_subtitle_current") and task.get("target_subtitle_authoritative_source"))
    audio_key = str(((task.get("config") or {}).get("tts_voiceover_key")) or "").strip() or None
    audio_ready = bool(target_ready and audio_key and task.get("dub_status") in {"ready", "done"})
    reason = "ready" if audio_ready else ("audio_missing" if target_ready else str(task.get("target_subtitle_current_reason") or "subtitle_missing"))
    return {
        "audio_ready": audio_ready,
        "audio_ready_reason": reason,
        "dub_current": audio_ready,
        "dub_current_reason": "ready" if audio_ready else reason,
        "voiceover_url": f"/v1/tasks/{task['task_id']}/audio_mm" if audio_ready else None,
        "deliverable_audio_done": audio_ready,
        "actual_provider": "azure-speech",
        "resolved_voice": "vi-VN-HoaiMyNeural",
        "requested_voice": "vi_female_1",
    }


def _audio_cfg(task: dict) -> dict:
    voice = _voice_state(task, _settings())
    return {
        "tts_engine": "azure-speech",
        "tts_voice": "vi-VN-HoaiMyNeural",
        "voiceover_url": voice["voiceover_url"],
        "tts_voiceover_url": voice["voiceover_url"],
        "source_audio_policy": "mute",
        "source_audio_preserved": False,
        "tts_voiceover_ready": bool(voice["audio_ready"]),
    }


def _persisted_audio(task_id: str, task: dict) -> dict:
    voice = _voice_state(task, _settings())
    return {
        "exists": bool(voice["audio_ready"]),
        "voiceover_url": voice["voiceover_url"],
        "audio_key": ((task.get("config") or {}).get("tts_voiceover_key")),
    }


def _composed_state(task: dict, task_id: str) -> dict:
    fresh = bool(task.get("final_video_key") and task.get("final_fresh"))
    stale = task.get("final_stale_reason") if not fresh else None
    return {
        "composed_ready": fresh,
        "composed_reason": "ready" if fresh else (stale or "final_missing"),
        "final": {
            "exists": fresh,
            "fresh": fresh,
            "key": task.get("final_video_key") if fresh else None,
            "url": f"/v1/tasks/{task_id}/final" if fresh else None,
        },
        "historical_final": {
            "exists": bool(task.get("final_video_key") and not fresh),
            "key": task.get("final_video_key") if not fresh else None,
            "url": f"/v1/tasks/{task_id}/final" if task.get("final_video_key") and not fresh else None,
        },
        "final_fresh": fresh,
        "final_stale_reason": stale,
        "raw_exists": bool(task.get("raw_path")),
        "voice_exists": bool(_voice_state(task, _settings())["audio_ready"]),
    }


def _deliverables(task_id: str, task: dict) -> list[dict]:
    return hf_deliverables(
        task_id,
        task,
        subtitle_lane_loader=_subtitle_lane,
        current_voiceover_asset_loader=lambda tid, current_task, settings: {
            "key": ((current_task.get("config") or {}).get("tts_voiceover_key")),
            "exists": _voice_state(current_task, settings)["audio_ready"],
        },
        object_exists_fn=_object_exists,
        task_endpoint_loader=_task_endpoint,
        signed_op_url_loader=_signed_url,
        download_url_loader=_download_url,
        settings=_settings(),
    )


def _build_workbench(task_id: str, repo: _Repo) -> dict:
    return build_hot_follow_workbench_hub(
        task_id,
        repo,
        settings=_settings(),
        object_exists_fn=_object_exists,
        task_endpoint_loader=_task_endpoint,
        subtitle_lane_loader=_subtitle_lane,
        composed_state_loader=_composed_state,
        scene_pack_info_loader=lambda task, tid: {"exists": False, "download_url": None},
        subtitles_text_loader=lambda tid, task: VI_SRT if task.get("target_subtitle_current") else "",
        origin_subtitles_text_loader=lambda task: ZH_SRT,
        normalized_source_text_loader=lambda tid, task: ZH_SRT,
        audio_config_loader=_audio_cfg,
        voice_execution_state_loader=_voice_state,
        persisted_audio_state_loader=_persisted_audio,
        deliverables_loader=_deliverables,
        backfill_compose_done=lambda *_args, **_kwargs: False,
        workbench_ui_loader=lambda *_args, **_kwargs: {},
    )


def _build_publish(task_id: str, repo: _Repo) -> dict:
    return build_hot_follow_publish_hub(
        task_id,
        repo,
        settings=_settings(),
        object_exists_fn=_object_exists,
        task_endpoint_loader=_task_endpoint,
        subtitle_lane_loader=_subtitle_lane,
        composed_state_loader=_composed_state,
        scene_pack_info_loader=lambda task, tid: {"exists": False, "download_url": None},
        subtitles_text_loader=lambda tid, task: VI_SRT if task.get("target_subtitle_current") else "",
        origin_subtitles_text_loader=lambda task: ZH_SRT,
        normalized_source_text_loader=lambda tid, task: ZH_SRT,
        audio_config_loader=_audio_cfg,
        voice_execution_state_loader=_voice_state,
        persisted_audio_state_loader=_persisted_audio,
        deliverables_loader=_deliverables,
        backfill_compose_done=lambda *_args, **_kwargs: False,
        publish_surface_builder=lambda tid, task, state, **kwargs: _build_hot_follow_publish_surface_payload(
            tid,
            task,
            state,
            deliverable_url_loader=_deliverable_url,
            download_code_loader=lambda current_task_id: current_task_id,
            copy_bundle_builder=lambda current_task: {},
            **kwargs,
        ),
    )


def _entry(payload: dict, kind: str) -> dict:
    return next(row for row in payload["deliverables"] if row["kind"] == kind)


def _assert_no_subtitle_split_brain(payload: dict) -> None:
    subtitles = payload["subtitles"]
    gate = payload["ready_gate"]
    subtitle_entry = _entry(payload, "subtitle")
    business_ready = bool(
        subtitles["subtitle_ready"]
        and subtitles["target_subtitle_current"]
        and subtitles["target_subtitle_authoritative_source"]
    )
    assert gate["subtitle_ready"] is business_ready
    assert (subtitle_entry["state"] == "done") is business_ready
    if not business_ready:
        assert subtitles["dub_input_text"] == ""
        assert payload["current_attempt"].get("current_subtitle_source") is None


def test_phase3_url_lane_origin_only_does_not_promote_target_subtitle_closure():
    repo = _Repo(_sample_tasks())
    payload = _build_workbench(URL_SAMPLE_ID, repo)
    publish = _build_publish(URL_SAMPLE_ID, repo)

    _assert_no_subtitle_split_brain(payload)
    assert _entry(payload, "origin_subtitle")["state"] == "done"
    assert payload["subtitles"]["target_subtitle_current"] is False
    assert payload["subtitles"]["helper_translation"]["status"] == "helper_output_pending"
    assert payload["ready_gate"]["audio_ready"] is False
    assert payload["ready_gate"]["compose_ready"] is False
    assert publish["ready_gate"]["compose_ready"] is False
    assert "mm_srt" not in publish["deliverables"]
    assert "vi_srt" not in publish["deliverables"]
    assert "mm_txt" not in publish["deliverables"]


def test_phase3_local_upload_helper_telemetry_stays_out_of_business_truth():
    repo = _Repo(_sample_tasks())
    payload = _build_workbench(LOCAL_SAMPLE_ID, repo)
    publish = _build_publish(LOCAL_SAMPLE_ID, repo)

    _assert_no_subtitle_split_brain(payload)
    assert payload["task"]["platform"] == "local"
    assert payload["subtitles"]["helper_translation"]["reason"] == "helper_translate_provider_exhausted"
    assert payload["subtitles"]["subtitle_ready"] is False
    assert payload["ready_gate"]["subtitle_ready"] is False
    assert payload["ready_gate"]["audio_ready"] is False
    assert payload["ready_gate"]["compose_ready"] is False
    assert "subtitle" not in publish["deliverables"]


def test_phase3_manual_save_surface_projects_vi_srt_and_blocks_stale_audio_compose():
    repo = _Repo(_sample_tasks())
    payload = _build_workbench(MANUAL_SAVE_SAMPLE_ID, repo)
    publish = _build_publish(MANUAL_SAVE_SAMPLE_ID, repo)

    _assert_no_subtitle_split_brain(payload)
    assert payload["subtitles"]["target_subtitle_current"] is True
    assert payload["subtitles"]["target_subtitle_authoritative_source"] is True
    assert payload["subtitles"]["actual_burn_subtitle_source"] == "vi.srt"
    assert _entry(payload, "subtitle")["state"] == "done"
    assert payload["ready_gate"]["audio_ready"] is False
    assert payload["ready_gate"]["audio_ready_reason"] == "audio_missing"
    assert payload["ready_gate"]["compose_ready"] is False
    assert payload["historical_final"]["exists"] is True
    assert publish["deliverables"]["vi_srt"]["url"]
    assert "audio_mp3" not in publish["deliverables"]
    assert publish["ready_gate"]["compose_ready"] is False
