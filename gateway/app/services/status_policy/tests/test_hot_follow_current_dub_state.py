import asyncio
from pathlib import Path
import sys
import types
from types import SimpleNamespace
from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import tasks as tasks_router
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import task_view_helpers
from gateway.app.services import voice_state as voice_state_service
from gateway.app.utils.pipeline_config import parse_pipeline_config


def _settings():
    return SimpleNamespace(
        edge_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
            "vi_female_1": "vi-VN-HoaiMyNeural",
            "vi_male_1": "vi-VN-NamMinhNeural",
        },
        azure_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
            "vi_female_1": "vi-VN-HoaiMyNeural",
            "vi_male_1": "vi-VN-NamMinhNeural",
        },
        dub_provider="azure-speech",
        azure_speech_key="test-key",
        azure_speech_region="eastasia",
    )


def _patch_voice_storage(monkeypatch, exists_fn, head_fn, meta_fn):
    monkeypatch.setattr(voice_state_service, "object_exists", exists_fn)
    monkeypatch.setattr(voice_state_service, "object_head", head_fn)
    monkeypatch.setattr(voice_state_service, "media_meta_from_head", meta_fn)


def test_fresh_matching_male_artifact_is_current_even_if_tokens_are_stale(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-male",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/hf-male/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-ThihaNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
            "tts_request_token": "newer",
            "tts_completed_token": "older",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["requested_voice"] == "mm_male_1"
    assert state["resolved_voice"] == "my-MM-ThihaNeural"
    assert state["actual_provider"] == "azure-speech"
    assert state["audio_ready"] is True
    assert state["audio_ready_reason"] == "ready"
    assert state["dub_current"] is True
    assert state["dub_current_reason"] == "ready"
    assert str(state["voiceover_url"]).endswith("/v1/tasks/hf-male/audio_mm")
    assert state["deliverable_audio_done"] is True


def test_stale_female_artifact_is_not_current_for_male_request(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-stale",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "failed",
        "mm_audio_key": "deliver/tasks/hf-stale/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
            "tts_request_token": "newer",
            "tts_completed_token": "older",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "dub_not_done"
    assert state["dub_current"] is False
    assert state["voiceover_url"] is None
    assert state["deliverable_audio_done"] is True


def test_preserved_bgm_artifact_does_not_count_as_current_tts_dub(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-source-audio-not-dub",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/hf-source-audio-not-dub/bgm/user_bgm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "bgm": {
                "strategy": "keep",
                "bgm_key": "deliver/tasks/hf-source-audio-not-dub/bgm/user_bgm.mp3",
                "mix_ratio": 0.4,
            },
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "voiceover_artifact_not_tts"
    assert state["dub_current"] is False
    assert state["voiceover_url"] is None
    assert state["audio_artifact_role"] == "source_audio"


def test_dub_download_route_rejects_preserved_bgm_audio_key(monkeypatch):
    task_id = "hf-source-audio-download-not-dub"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": f"deliver/tasks/{task_id}/bgm/user_bgm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "source_audio_policy": "preserve",
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
            "bgm": {
                "strategy": "keep",
                "bgm_key": f"deliver/tasks/{task_id}/bgm/user_bgm.mp3",
            },
        },
    }

    class _Repo:
        def get(self, requested_id):
            assert requested_id == task_id
            return task

    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"content_length": "4096", "content_type": "audio/mpeg"})
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    with pytest.raises(Exception) as exc:
        tasks_router._resolve_audio_meta(task_id, _Repo())

    assert getattr(exc.value, "status_code", None) == 404


def test_dub_download_route_uses_current_tts_voiceover_key(monkeypatch):
    task_id = "hf-tts-download"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": f"deliver/tasks/{task_id}/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "mm_audio_mime": "audio/mpeg",
        "config": {
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
        },
    }

    class _Repo:
        def get(self, requested_id):
            assert requested_id == task_id
            return task

    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda key: str(key).endswith("audio_mm.mp3"))
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"content_length": "4096", "content_type": "audio/mpeg"})
    _patch_voice_storage(
        monkeypatch,
        lambda key: str(key).endswith("audio_mm.mp3"),
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    key, size, content_type = tasks_router._resolve_audio_meta(task_id, _Repo())

    assert key == f"deliver/tasks/{task_id}/audio_mm.mp3"
    assert size == 4096
    assert content_type == "audio/mpeg"


def test_dub_download_route_prefers_dry_tts_key_over_source_audio_lane(monkeypatch):
    task_id = "hf-dry-tts-download"
    dry_key = f"deliver/tasks/{task_id}/voiceover/audio_mm.dry.mp3"
    source_key = f"deliver/tasks/{task_id}/bgm/source_audio.mp3"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": source_key,
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "mm_audio_mime": "audio/mpeg",
        "config": {
            "source_audio_policy": "preserve",
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
            "tts_voiceover_key": dry_key,
            "bgm": {"strategy": "keep", "bgm_key": source_key},
        },
    }

    class _Repo:
        def get(self, requested_id):
            assert requested_id == task_id
            return task

    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda key: str(key) == dry_key)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"content_length": "4096", "content_type": "audio/mpeg"})
    _patch_voice_storage(
        monkeypatch,
        lambda key: str(key) == dry_key,
        lambda _key: {"content_length": "4096", "content_type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    state = tasks_router._collect_voice_execution_state(task, _settings())
    key, size, content_type = tasks_router._resolve_audio_meta(task_id, _Repo())

    assert state["audio_ready"] is True
    assert state["dub_current"] is True
    assert state["audio_artifact_role"] == "tts_voiceover"
    assert key == dry_key
    assert size == 4096
    assert content_type == "audio/mpeg"


def test_task_detail_audio_urls_hide_source_audio_artifact(monkeypatch):
    task_id = "hf-detail-source-audio-not-dub"
    task = {
        "task_id": task_id,
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": f"deliver/tasks/{task_id}/bgm/user_bgm.mp3",
        "mm_audio_path": f"deliver/tasks/{task_id}/bgm/user_bgm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "source_audio_policy": "preserve",
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
            "bgm": {
                "strategy": "keep",
                "bgm_key": f"deliver/tasks/{task_id}/bgm/user_bgm.mp3",
            },
        },
    }
    monkeypatch.setattr(task_view_helpers, "get_settings", _settings)
    monkeypatch.setattr(task_view_helpers, "object_exists", lambda _key: True)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    paths = task_view_helpers.resolve_download_urls(task)

    assert paths["mm_audio_path"] is None
    assert paths["mm_audio_download_url"] is None


def test_audio_config_marks_preserved_source_audio_as_not_tts_preview(monkeypatch):
    monkeypatch.setattr(hf_router, "get_download_url", lambda key: f"/download/{key}")
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "expected_provider": "azure-speech",
            "resolved_voice": "my-MM-NilarNeural",
            "requested_voice": "mm_female_1",
            "audio_ready": False,
            "audio_ready_reason": "audio_missing",
            "dub_current": False,
            "dub_current_reason": "audio_missing",
            "voiceover_url": None,
        },
    )

    task = {
        "task_id": "hf-preserve-no-tts-preview",
        "kind": "hot_follow",
        "target_lang": "mm",
        "config": {
            "bgm": {
                "strategy": "keep",
                "bgm_key": "deliver/tasks/hf-preserve-no-tts-preview/bgm/source.mp3",
                "mix_ratio": 0.4,
            }
        },
    }

    audio_cfg = hf_router._hf_audio_config(task)

    assert audio_cfg["source_audio_policy"] == "preserve"
    assert audio_cfg["source_audio_preserved"] is True
    assert audio_cfg["tts_voiceover_ready"] is False
    assert audio_cfg["audio_flow_mode"] == "source_audio_preserved_no_tts"
    assert audio_cfg["voiceover_url"] is None
    assert audio_cfg["audio_url"] is None
    assert audio_cfg["dub_preview_url"] is None


def test_audio_config_marks_tts_plus_preserved_source_audio_when_voiceover_current(monkeypatch):
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "expected_provider": "azure-speech",
            "resolved_voice": "my-MM-NilarNeural",
            "requested_voice": "mm_female_1",
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "voiceover_url": "/v1/tasks/hf-tts-preserve/audio_mm",
        },
    )

    task = {
        "task_id": "hf-tts-preserve",
        "kind": "hot_follow",
        "target_lang": "mm",
        "config": {"bgm": {"strategy": "keep", "mix_ratio": 0.4}},
    }

    audio_cfg = hf_router._hf_audio_config(task)

    assert audio_cfg["source_audio_policy"] == "preserve"
    assert audio_cfg["source_audio_preserved"] is True
    assert audio_cfg["tts_voiceover_ready"] is True
    assert audio_cfg["audio_flow_mode"] == "tts_voiceover_plus_source_audio"
    assert audio_cfg["dub_preview_url"] == "/v1/tasks/hf-tts-preserve/audio_mm"
    assert audio_cfg["voiceover_url"] == "/v1/tasks/hf-tts-preserve/audio_mm"


def test_audio_config_keeps_mute_tts_only_semantics(monkeypatch):
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "expected_provider": "azure-speech",
            "resolved_voice": "my-MM-NilarNeural",
            "requested_voice": "mm_female_1",
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "voiceover_url": "/v1/tasks/hf-tts-mute/audio_mm",
        },
    )

    task = {
        "task_id": "hf-tts-mute",
        "kind": "hot_follow",
        "target_lang": "mm",
        "config": {"bgm": {"strategy": "replace", "mix_ratio": 0.0}},
    }

    audio_cfg = hf_router._hf_audio_config(task)

    assert audio_cfg["source_audio_policy"] == "mute"
    assert audio_cfg["source_audio_preserved"] is False
    assert audio_cfg["tts_voiceover_ready"] is True
    assert audio_cfg["audio_flow_mode"] == "tts_voiceover_only"
    assert audio_cfg["dub_preview_url"] == "/v1/tasks/hf-tts-mute/audio_mm"


def test_previous_final_can_coexist_with_failed_current_redub(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    _patch_voice_storage(
        monkeypatch,
        lambda key: str(key).endswith(("audio_mm.mp3", "final.mp4")),
        lambda key: {
            "ContentLength": "4096" if str(key).endswith("audio_mm.mp3") else "8192",
            "Content-Type": "audio/mpeg" if str(key).endswith("audio_mm.mp3") else "video/mp4",
        },
        lambda meta: (int(meta.get("ContentLength") or 0), str(meta.get("Content-Type") or "")),
    )
    # Also patch on hf_router since _collect_hot_follow_workbench_ui lives there
    monkeypatch.setattr(hf_router, "get_settings", _settings)
    monkeypatch.setattr(hf_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda key: str(key).endswith(("audio_mm.mp3", "final.mp4")))
    monkeypatch.setattr(
        hf_router,
        "object_head",
        lambda key: {
            "ContentLength": "4096" if str(key).endswith("audio_mm.mp3") else "8192",
            "Content-Type": "audio/mpeg" if str(key).endswith("audio_mm.mp3") else "video/mp4",
        },
    )
    monkeypatch.setattr(
        hf_router,
        "media_meta_from_head",
        lambda meta: (int(meta.get("ContentLength") or 0), str(meta.get("Content-Type") or "")),
    )

    task = {
        "task_id": "hf-rerun",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "failed",
        "compose_status": "done",
        "final_video_key": "deliver/tasks/hf-rerun/final.mp4",
        "mm_audio_key": "deliver/tasks/hf-rerun/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
        },
    }

    payload = hf_router._collect_hot_follow_workbench_ui(task, _settings())
    assert payload["final_exists"] is True
    assert payload["audio_ready"] is False
    assert payload["dub_current"] is False


def test_vi_voice_options_and_burn_source_follow_profile(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(hf_router, "task_base_dir", lambda task_id: Path("/tmp") / task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda _key: b"1\n00:00:00,000 --> 00:00:02,000\nXin chao\n")
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )
    task = {
        "task_id": "hf-vi",
        "kind": "hot_follow",
        "target_lang": "vi",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/hf-vi/audio_vi.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "vi-VN-HoaiMyNeural",
        "mm_srt_path": "deliver/tasks/hf-vi/vi.srt",
        "config": {
            "tts_requested_voice": "vi_female_1",
            "tts_resolved_voice": "vi-VN-HoaiMyNeural",
            "tts_provider": "azure-speech",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())
    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-vi", task)

    assert state["requested_voice"] == "vi_female_1"
    assert state["resolved_voice"] == "vi-VN-HoaiMyNeural"
    assert [item["value"] for item in state["voice_options_by_provider"]["azure_speech"]] == [
        "vi_female_1",
        "vi_male_1",
    ]
    assert subtitle_lane["actual_burn_subtitle_source"] == "vi.srt"


def test_rerun_presentation_reports_last_final_and_current_failure():
    task = {
        "task_id": "hf-rerun-presentation",
        "updated_at": "2026-03-14T10:00:00+00:00",
    }
    voice_state = {
        "audio_ready": False,
        "audio_ready_reason": "dub_not_done",
        "dub_current": False,
        "dub_current_reason": "dub_not_done",
        "requested_voice": "mm_male_1",
        "resolved_voice": "my-MM-ThihaNeural",
        "actual_provider": "azure-speech",
    }
    final_info = {
        "exists": True,
        "url": "/v1/tasks/hf-rerun-presentation/final",
        "asset_version": "etag-123",
        "updated_at": "2026-03-14T09:55:00+00:00",
    }

    presentation = hf_router._hf_rerun_presentation_state(task, voice_state, final_info, final_info, "failed")

    assert presentation["last_successful_output"]["final_exists"] is True
    assert presentation["last_successful_output"]["final_url"] == "/v1/tasks/hf-rerun-presentation/final"
    assert presentation["current_attempt"]["dub_status"] == "failed"
    assert presentation["current_attempt"]["audio_ready"] is False
    assert presentation["current_attempt"]["dub_current"] is False
    assert presentation["current_attempt"]["requested_voice"] == "mm_male_1"


def test_rerun_presentation_reports_current_success_without_regressing_baseline():
    task = {
        "task_id": "hf-success-presentation",
        "updated_at": "2026-03-14T10:00:00+00:00",
    }
    voice_state = {
        "audio_ready": True,
        "audio_ready_reason": "ready",
        "dub_current": True,
        "dub_current_reason": "ready",
        "requested_voice": "mm_female_1",
        "resolved_voice": "my-MM-NilarNeural",
        "actual_provider": "azure-speech",
    }
    final_info = {
        "exists": True,
        "url": "/v1/tasks/hf-success-presentation/final",
        "asset_version": "etag-456",
        "updated_at": "2026-03-14T09:58:00+00:00",
    }

    presentation = hf_router._hf_rerun_presentation_state(task, voice_state, final_info, final_info, "done")

    assert presentation["last_successful_output"]["final_exists"] is True
    assert presentation["current_attempt"]["dub_status"] == "done"
    assert presentation["current_attempt"]["audio_ready"] is True
    assert presentation["current_attempt"]["dub_current"] is True
    assert presentation["current_attempt"]["resolved_voice"] == "my-MM-NilarNeural"


def test_subtitle_lane_uses_final_composed_vi_burn_source_when_present(monkeypatch):
    monkeypatch.setattr(hf_router, "task_base_dir", lambda task_id: Path("/tmp") / task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "get_object_bytes", lambda _key: b"1\n00:00:00,000 --> 00:00:02,000\nXin chao\n")

    task = {
        "task_id": "hf-vi-final",
        "kind": "hot_follow",
        "target_lang": "vi",
        "mm_srt_path": "deliver/tasks/hf-vi-final/vi.srt",
        "final_source_subtitle_storage_key": "deliver/tasks/hf-vi-final/vi.srt",
    }

    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-vi-final", task)

    assert subtitle_lane["actual_burn_subtitle_source"] == "vi.srt"


def test_vi_subtitle_lane_blocks_source_copy_until_real_target_is_current(monkeypatch):
    monkeypatch.setattr(hf_router, "task_base_dir", lambda task_id: Path("/tmp") / task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)

    def _fake_bytes(key):
        text = "1\n00:00:00,000 --> 00:00:02,000\n原始文案\n"
        return text.encode("utf-8")

    monkeypatch.setattr(hf_router, "get_object_bytes", _fake_bytes)

    task = {
        "task_id": "hf-vi-source-copy",
        "kind": "hot_follow",
        "target_lang": "vi",
        "origin_srt_path": "deliver/tasks/hf-vi-source-copy/origin.srt",
        "mm_srt_path": "deliver/tasks/hf-vi-source-copy/vi.srt",
        "pipeline_config": {"translation_incomplete": "true"},
    }

    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-vi-source-copy", task)

    assert subtitle_lane["target_subtitle_current"] is False
    assert subtitle_lane["subtitle_ready"] is False
    assert subtitle_lane["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"


def test_myanmar_subtitle_lane_blocks_source_copy_target_as_not_current(monkeypatch):
    monkeypatch.setattr(hf_router, "task_base_dir", lambda task_id: Path("/tmp") / task_id)
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)

    def _fake_bytes(key):
        text = "1\n00:00:00,000 --> 00:00:02,000\n原始文案\n"
        return text.encode("utf-8")

    monkeypatch.setattr(hf_router, "get_object_bytes", _fake_bytes)

    task = {
        "task_id": "hf-mm-source-copy",
        "kind": "hot_follow",
        "target_lang": "mm",
        "origin_srt_path": "deliver/tasks/hf-mm-source-copy/origin.srt",
        "mm_srt_path": "deliver/tasks/hf-mm-source-copy/mm.srt",
        "pipeline_config": {"translation_incomplete": "false"},
    }

    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-mm-source-copy", task)

    assert subtitle_lane["target_subtitle_current"] is False
    assert subtitle_lane["subtitle_ready"] is False
    assert subtitle_lane["target_subtitle_current_reason"] == "target_subtitle_source_copy"


def test_vi_voice_state_requires_current_target_subtitle(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-vi-audio-stale",
        "kind": "hot_follow",
        "target_lang": "vi",
        "dub_status": "done",
        "target_subtitle_current": False,
        "target_subtitle_current_reason": "target_subtitle_source_copy",
        "mm_audio_key": "deliver/tasks/hf-vi-audio-stale/audio_vi.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "vi-VN-NamMinhNeural",
        "config": {
            "tts_requested_voice": "vi_male_1",
            "tts_resolved_voice": "vi-VN-NamMinhNeural",
            "tts_provider": "azure-speech",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["deliverable_audio_done"] is True
    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "target_subtitle_source_copy"
    assert state["dub_current"] is False


def test_mm_voice_state_invalidates_stale_dub_after_subtitle_edit(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-mm-dub-stale",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "target_subtitle_current": True,
        "target_subtitle_current_reason": "ready",
        "subtitles_content_hash": "HASH_B",
        "dub_source_subtitles_content_hash": "HASH_A",
        "mm_audio_key": "deliver/tasks/hf-mm-dub-stale/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-ThihaNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["deliverable_audio_done"] is True
    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "dub_stale_after_subtitles"
    assert state["dub_current"] is False
    assert state["dub_matches_current_subtitle"] is False


def test_mm_voice_state_invalidates_stale_dub_after_speed_change(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )

    task = {
        "task_id": "hf-mm-speed-stale",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "target_subtitle_current": True,
        "target_subtitle_current_reason": "ready",
        "pipeline_config": {"audio_fit_max_speed": "1.45"},
        "dub_source_audio_fit_max_speed": "1.25",
        "mm_audio_key": "deliver/tasks/hf-mm-speed-stale/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-ThihaNeural",
        "config": {
            "tts_requested_voice": "mm_male_1",
            "tts_resolved_voice": "my-MM-ThihaNeural",
            "tts_provider": "azure-speech",
        },
    }

    state = tasks_router._collect_voice_execution_state(task, _settings())

    assert state["audio_ready"] is False
    assert state["audio_ready_reason"] == "dub_stale_after_speed_change"
    assert state["dub_current"] is False
    assert state["current_audio_fit_max_speed"] == "1.45"
    assert state["dub_source_audio_fit_max_speed"] == "1.25"


def test_artifact_facts_and_operator_summary_keep_previous_final_visible():
    artifact_facts = hf_router._hf_artifact_facts(
        "hf-rerun-presentation",
        {},
        final_info={
            "exists": True,
            "url": "/v1/tasks/hf-rerun-presentation/final",
            "asset_version": "etag-123",
            "updated_at": "2026-03-14T09:55:00+00:00",
        },
        historical_final={
            "exists": True,
            "url": "/v1/tasks/hf-rerun-presentation/final",
            "asset_version": "etag-123",
            "updated_at": "2026-03-14T09:55:00+00:00",
        },
        persisted_audio={"exists": False, "voiceover_url": None},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack={"download_url": "/v1/tasks/hf-rerun-presentation/pack"},
    )
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "dub_current_reason": "dub_not_done",
            "requested_voice": "mm_male_1",
            "resolved_voice": "my-MM-ThihaNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={"actual_burn_subtitle_source": "mm.srt"},
        dub_status="failed",
        compose_status="pending",
        composed_reason="audio_not_ready",
    )
    operator_summary = hf_router._hf_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
    )

    assert artifact_facts["final_exists"] is True
    assert artifact_facts["final_url"] == "/v1/tasks/hf-rerun-presentation/final"
    assert artifact_facts["audio_exists"] is False
    assert artifact_facts["subtitle_exists"] is True
    assert artifact_facts["pack_exists"] is True
    assert current_attempt["dub_status"] == "failed"
    assert current_attempt["compose_status"] == "pending"
    assert current_attempt["current_subtitle_source"] == "mm.srt"
    assert operator_summary["last_successful_output_available"] is True
    assert operator_summary["current_attempt_failed"] is True
    assert operator_summary["show_previous_final_as_primary"] is True


def test_artifact_facts_and_operator_summary_preserve_voice_led_success_baseline():
    artifact_facts = hf_router._hf_artifact_facts(
        "hf-success-presentation",
        {},
        final_info={
            "exists": True,
            "url": "/v1/tasks/hf-success-presentation/final",
            "asset_version": "etag-456",
            "updated_at": "2026-03-14T09:58:00+00:00",
        },
        historical_final={
            "exists": True,
            "url": "/v1/tasks/hf-success-presentation/final",
            "asset_version": "etag-456",
            "updated_at": "2026-03-14T09:58:00+00:00",
        },
        persisted_audio={"exists": True, "voiceover_url": "/v1/tasks/hf-success-presentation/audio_mm"},
        subtitle_lane={"subtitle_artifact_exists": True},
        scene_pack=None,
    )
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": True,
            "audio_ready_reason": "ready",
            "dub_current": True,
            "dub_current_reason": "ready",
            "requested_voice": "mm_female_1",
            "resolved_voice": "my-MM-NilarNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={"actual_burn_subtitle_source": "mm.srt"},
        dub_status="done",
        compose_status="done",
        composed_reason="ready",
    )
    operator_summary = hf_router._hf_operator_summary(
        artifact_facts=artifact_facts,
        current_attempt=current_attempt,
        no_dub=False,
    )

    assert artifact_facts["audio_exists"] is True
    assert artifact_facts["audio_url"] == "/v1/tasks/hf-success-presentation/audio_mm"
    assert current_attempt["requires_recompose"] is False
    assert current_attempt["compose_reason"] == "ready"
    assert operator_summary["last_successful_output_available"] is True
    assert operator_summary["current_attempt_failed"] is False
    assert operator_summary["show_previous_final_as_primary"] is False


def test_operator_summary_requires_redub_when_subtitles_changed():
    current_attempt = hf_router._hf_current_attempt_summary(
        voice_state={
            "audio_ready": False,
            "audio_ready_reason": "dub_stale_after_subtitles",
            "dub_current": False,
            "dub_current_reason": "dub_stale_after_subtitles",
            "requested_voice": "mm_male_1",
            "resolved_voice": "my-MM-ThihaNeural",
            "actual_provider": "azure-speech",
        },
        subtitle_lane={
            "subtitle_ready": True,
            "actual_burn_subtitle_source": "mm.srt",
        },
        dub_status="done",
        compose_status="pending",
        composed_reason="audio_not_ready",
    )
    operator_summary = hf_router._hf_operator_summary(
        artifact_facts={"final_exists": False},
        current_attempt=current_attempt,
        no_dub=False,
        subtitle_ready=True,
    )

    assert current_attempt["requires_redub"] is True
    assert operator_summary["recommended_next_action"] == "当前目标字幕已更新，需重新配音后才能继续合成最新成片。"


def test_source_audio_lane_summary_distinguishes_voice_led_and_silent_candidates():
    voice_led = hf_router._hf_source_audio_lane_summary(
        {"title": "standard talking head"},
        {"content_mode": "voice_led", "speech_detected": True},
    )
    silent = hf_router._hf_source_audio_lane_summary(
        {"title": "ASMR product showcase"},
        {"content_mode": "silent_candidate", "speech_detected": False},
    )

    assert voice_led["source_audio_lane"] == "speech_primary"
    assert voice_led["speech_presence"] == "high"
    assert silent["source_audio_lane"] == "silent_candidate"
    assert silent["audio_mix_mode"] == "silent_or_fx"


def test_screen_text_candidate_summary_prefers_normalized_text_for_subtitle_led():
    candidate = hf_router._hf_screen_text_candidate_summary(
        {
            "normalized_source_text": "候选字幕",
            "raw_source_text": "原始文本",
        },
        {
            "onscreen_text_detected": True,
            "onscreen_text_density": "high",
            "content_mode": "subtitle_led",
        },
    )

    assert candidate["screen_text_candidate"] == "候选字幕"
    assert candidate["screen_text_candidate_source"] == "normalized_source"
    assert candidate["screen_text_candidate_confidence"] == "high"
    assert candidate["screen_text_candidate_mode"] == "subtitle_led"


def test_collect_hot_follow_workbench_ui_does_not_keep_no_dub_when_audio_is_current(monkeypatch):
    monkeypatch.setattr(hf_router, "get_settings", _settings)
    _patch_voice_storage(
        monkeypatch,
        lambda _key: True,
        lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"},
        lambda _meta: (4096, "audio/mpeg"),
    )
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        hf_router,
        "_hf_load_subtitles_text",
        lambda _task_id, _task: "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n",
    )

    task = {
        "task_id": "hf-a9-ui",
        "kind": "hot_follow",
        "target_lang": "mm",
        "title": "silent candidate but current dub exists",
        "dub_status": "done",
        "voice_id": "mm_female_1",
        "dub_provider": "azure-speech",
        "mm_audio_key": "deliver/tasks/hf-a9-ui/audio_mm.mp3",
        "mm_audio_provider": "azure-speech",
        "mm_audio_voice_id": "my-MM-NilarNeural",
        "mm_srt_path": "deliver/tasks/hf-a9-ui/mm.srt",
        "config": {
            "tts_requested_voice": "mm_female_1",
            "tts_resolved_voice": "my-MM-NilarNeural",
            "tts_provider": "azure-speech",
        },
        "pipeline_config": {"no_dub": "true"},
    }

    payload = hf_router._collect_hot_follow_workbench_ui(task, _settings())

    assert payload["audio_ready"] is True
    assert payload["dub_current"] is True
    assert payload["subtitle_artifact_exists"] is True
    assert payload["actual_burn_subtitle_source"] == "mm.srt"
    assert payload["no_dub"] is False
    assert payload["no_dub_reason"] is None


def test_sync_saved_target_subtitle_artifact_writes_canonical_mm_srt(monkeypatch, tmp_path):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (0, None))

    class _Workspace:
        def __init__(self, task_id, target_lang: str | None = None):
            _ = target_lang
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    uploaded = []

    def _fake_upload(task, local_path, artifact_name, task_id=None, **_kwargs):
        uploaded.append((artifact_name, Path(local_path).read_text(encoding="utf-8")))
        return f"deliver/tasks/{task_id}/{artifact_name}"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "upload_task_artifact", _fake_upload)

    task = {"task_id": "hf-sync", "kind": "hot_follow"}
    key = hf_router._hf_sync_saved_target_subtitle_artifact(
        "hf-sync",
        task,
        "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n",
    )

    assert key == "deliver/tasks/hf-sync/mm.srt"
    assert task["mm_srt_path"] == "deliver/tasks/hf-sync/mm.srt"
    assert uploaded[0][0] == "mm.srt"
    assert "မင်္ဂလာပါ" in uploaded[0][1]
    assert uploaded[1][0] == "mm.txt"
    assert "မင်္ဂလာပါ" in uploaded[1][1]


def test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt(monkeypatch, tmp_path):
    class _Repo:
        def __init__(self):
            self.task = {"task_id": "hf-save", "kind": "hot_follow", "subtitles_status": "pending"}

        def get(self, task_id):
            assert task_id == "hf-save"
            return dict(self.task)

    repo = _Repo()

    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "object_head", lambda _key: None)
    monkeypatch.setattr(hf_router, "media_meta_from_head", lambda _meta: (0, None))

    class _Workspace:
        def __init__(self, task_id, target_lang: str | None = None):
            _ = target_lang
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.mm_srt_path = base / "mm.srt"

    monkeypatch.setattr(hf_router, "Workspace", _Workspace)
    monkeypatch.setattr(hf_router, "_hf_subtitles_override_path", lambda task_id: tmp_path / task_id / "override.srt")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, task: Path(tmp_path / "hf-save" / "override.srt").read_text(encoding="utf-8"))
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_policy_upsert", lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates))
    monkeypatch.setattr(hf_router, "upload_task_artifact", lambda _task, _local_path, artifact_name, task_id=None, **_kwargs: f"deliver/tasks/{task_id}/{artifact_name}")

    payload = hf_router.HotFollowSubtitlesRequest(
        srt_text="1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n"
    )
    result = hf_router.patch_hot_follow_subtitles("hf-save", payload, repo=repo)

    assert repo.task["mm_srt_path"] == "deliver/tasks/hf-save/mm.srt"
    assert repo.task["compose_status"] == "pending"
    assert result["subtitles"]["srt_text"].strip().endswith("မင်္ဂလာပါ")


def test_patch_hot_follow_source_url_updates_workbench_metadata(monkeypatch):
    class _Repo:
        def __init__(self):
            self.task = {"task_id": "hf-source-edit", "kind": "hot_follow", "source_url": "https://old.example/video"}

        def get(self, task_id):
            assert task_id == "hf-source-edit"
            return dict(self.task)

    repo = _Repo()
    monkeypatch.setattr(hf_router, "_policy_upsert", lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates))

    payload = hf_router.HotFollowSourceUrlPatchRequest(source_url="https://new.example/video?id=1")
    result = hf_router.patch_hot_follow_source_url("hf-source-edit", payload, repo=repo)

    assert repo.task["source_url"] == "https://new.example/video?id=1"
    assert result["source_url"] == "https://new.example/video?id=1"


def test_patch_hot_follow_source_url_does_not_invalidate_compose_freshness(monkeypatch):
    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-source-non-stale",
                "kind": "hot_follow",
                "source_url": "https://old.example/video",
                "compose_status": "done",
                "compose_last_status": "done",
                "subtitles_content_hash": "HASH_A",
                "final_source_subtitles_content_hash": "HASH_A",
                "audio_sha256": "SHA_A",
                "final_source_audio_sha256": "SHA_A",
            }

        def get(self, task_id):
            assert task_id == "hf-source-non-stale"
            return dict(self.task)

    repo = _Repo()
    monkeypatch.setattr(hf_router, "_policy_upsert", lambda _repo, _task_id, updates, **_kwargs: repo.task.update(updates))

    payload = hf_router.HotFollowSourceUrlPatchRequest(source_url="https://new.example/video")
    hf_router.patch_hot_follow_source_url("hf-source-non-stale", payload, repo=repo)

    assert repo.task["compose_status"] == "done"
    assert repo.task["compose_last_status"] == "done"
    assert repo.task["subtitles_content_hash"] == "HASH_A"
    assert repo.task["final_source_subtitles_content_hash"] == "HASH_A"
    assert repo.task["audio_sha256"] == "SHA_A"
    assert repo.task["final_source_audio_sha256"] == "SHA_A"


def test_hot_follow_rerun_forces_redub_even_when_voice_is_unchanged(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_subtitle_lane_state", lambda *_args, **_kwargs: {"dub_input_text": "မင်္ဂလာပါ"})
    monkeypatch.setattr(tasks_router, "_compat_hot_follow_dual_channel_state", lambda *_args, **_kwargs: {"content_mode": "voice_led"})

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.base_dir = base
            self.mm_audio_primary_path = base / "audio_primary.wav"
            self.mm_audio_mp3_path = base / "audio.mp3"
            self.mm_audio_legacy_path = base / "audio_legacy.wav"
            self.mm_audio_path = base / "audio.wav"

        def mm_audio_exists(self):
            return False

    monkeypatch.setattr(tasks_router, "Workspace", _Workspace)

    def _fake_upsert(repo, task_id, updates, **_kwargs):
        assert task_id == repo.task["task_id"]
        repo.task.update(updates)
        return repo.task

    monkeypatch.setattr(tasks_router, "_policy_upsert", _fake_upsert)

    captured = {}

    async def _fake_run_dub_step_ssot(task_adapter):
        captured["force_dub"] = bool(getattr(task_adapter, "force_dub", False))
        raise RuntimeError("stop_after_force_capture")

    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", _fake_run_dub_step_ssot)

    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-force",
                "kind": "hot_follow",
                "target_lang": "mm",
                "voice_id": "mm_female_1",
                "dub_provider": "azure-speech",
                "mm_audio_key": "deliver/tasks/hf-force/audio_mm.mp3",
                "config": {
                    "tts_requested_voice": "mm_female_1",
                    "tts_resolved_voice": "my-MM-NilarNeural",
                    "tts_provider": "azure-speech",
                },
            }
            self.session = SimpleNamespace(expire_all=lambda: None)

        def get(self, _task_id):
            return self.task

    repo = _Repo()
    payload = tasks_router.DubProviderRequest(
        provider="azure-speech",
        voice_id="mm_female_1",
        mm_text="မင်္ဂလာပါ",
        force=True,
    )

    with pytest.raises(tasks_router.HTTPException) as exc:
        asyncio.run(tasks_router._run_dub_job("hf-force", payload, repo))

    assert exc.value.status_code == 500
    assert captured["force_dub"] is True


def test_successful_redub_persists_current_subtitle_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(
        tasks_router,
        "_compat_hot_follow_dub_route_state",
        lambda *_args, **_kwargs: {
            "subtitle_lane": {
                "target_subtitle_current": True,
                "subtitle_ready": True,
            },
            "route_state": {"content_mode": "voice_led"},
            "no_dub_candidate": False,
            "dub_input_text": "မင်္ဂလာပါ",
        },
    )
    monkeypatch.setattr(
        tasks_router,
        "_compat_hot_follow_target_lang_gate",
        lambda *_args, **_kwargs: {"allow": True},
    )

    class _Workspace:
        def __init__(self, task_id):
            base = tmp_path / task_id
            base.mkdir(parents=True, exist_ok=True)
            self.base_dir = base
            self.mm_audio_primary_path = base / "audio_primary.wav"
            self.mm_audio_mp3_path = base / "audio.mp3"
            self.mm_audio_legacy_path = base / "audio_legacy.wav"
            self.mm_audio_path = base / "audio.wav"

        def mm_audio_exists(self):
            return self.mm_audio_mp3_path.exists() or self.mm_audio_path.exists()

    monkeypatch.setattr(tasks_router, "Workspace", _Workspace)
    monkeypatch.setattr(tasks_router, "task_base_dir", lambda task_id: tmp_path / task_id)
    monkeypatch.setattr(tasks_router, "_repo_refresh_task", lambda repo, _task_id: dict(repo.task))
    monkeypatch.setattr(
        tasks_router,
        "_task_to_detail",
        lambda stored: SimpleNamespace(
            dict=lambda exclude=None: {
                "task_id": stored["task_id"],
                "kind": stored.get("kind"),
                "category_key": stored.get("category_key", "hot_follow"),
                "content_lang": stored.get("content_lang", "mm"),
                "ui_lang": stored.get("ui_lang", "zh"),
                "face_swap_enabled": False,
                "status": stored.get("status", "ready"),
                "created_at": stored.get("created_at", datetime.now(timezone.utc)),
                "updated_at": stored.get("updated_at", datetime.now(timezone.utc)),
                "dub_status": stored.get("dub_status"),
                "dub_provider": stored.get("dub_provider"),
                "voice_id": stored.get("voice_id"),
                "pipeline_config": parse_pipeline_config(stored.get("pipeline_config")),
                "mm_audio_path": stored.get("mm_audio_path"),
            }
        ),
    )
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: None)
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (0, "audio/mpeg"))
    monkeypatch.setattr(tasks_router, "assert_local_audio_ok", lambda _path: (4096, 2.5))
    monkeypatch.setattr(tasks_router, "_sha256_file", lambda _path: "SHA_DUB")

    class _Storage:
        def upload_file(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(tasks_router, "get_storage_service", lambda: _Storage())

    def _fake_upsert(repo, task_id, updates, **_kwargs):
        assert task_id == repo.task["task_id"]
        repo.task.update(updates)
        return repo.task

    monkeypatch.setattr(tasks_router, "_policy_upsert", _fake_upsert)

    async def _fake_run_dub_step_ssot(task_adapter):
        ws = _Workspace(task_adapter.task_id)
        ws.mm_audio_mp3_path.write_bytes(b"fake-mp3")

    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", _fake_run_dub_step_ssot)

    class _Repo:
        def __init__(self):
            self.task = {
                "task_id": "hf-redub-snapshot",
                "kind": "hot_follow",
                "target_lang": "mm",
                "voice_id": "mm_female_1",
                "dub_provider": "azure-speech",
                "subtitles_content_hash": "HASH_LATEST",
                "subtitles_override_updated_at": "2026-04-04T10:00:00+00:00",
                "pipeline_config": {"audio_fit_max_speed": "1.45"},
                "config": {
                    "tts_requested_voice": "mm_female_1",
                    "tts_resolved_voice": "my-MM-NilarNeural",
                    "tts_provider": "azure-speech",
                },
            }
            self.session = SimpleNamespace(expire_all=lambda: None)

        def get(self, _task_id):
            return dict(self.task)

    repo = _Repo()
    payload = tasks_router.DubProviderRequest(
        provider="azure-speech",
        voice_id="mm_female_1",
        mm_text="မင်္ဂလာပါ",
        tts_speed=1.45,
        force=True,
    )

    result = asyncio.run(tasks_router._run_dub_job("hf-redub-snapshot", payload, repo))

    assert result.audio_sha256 == "SHA_DUB"
    assert repo.task["dub_status"] == "ready"
    assert repo.task["dub_source_subtitles_content_hash"] == "HASH_LATEST"
    assert repo.task["dub_source_subtitle_updated_at"] == "2026-04-04T10:00:00+00:00"
    assert repo.task["dub_source_audio_fit_max_speed"] == "1.45"
