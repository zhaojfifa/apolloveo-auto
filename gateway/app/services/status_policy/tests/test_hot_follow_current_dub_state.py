from pathlib import Path
import sys
import types
from types import SimpleNamespace

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


def _settings():
    return SimpleNamespace(
        edge_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
        },
        azure_tts_voice_map={
            "mm_female_1": "my-MM-NilarNeural",
            "mm_male_1": "my-MM-ThihaNeural",
        },
        dub_provider="azure-speech",
    )


def test_fresh_matching_male_artifact_is_current_even_if_tokens_are_stale(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))

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
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))

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


def test_previous_final_can_coexist_with_failed_current_redub(monkeypatch, tmp_path):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "task_base_dir", lambda _task_id: tmp_path / _task_id)
    monkeypatch.setattr(tasks_router, "object_exists", lambda key: str(key).endswith(("audio_mm.mp3", "final.mp4")))
    monkeypatch.setattr(
        tasks_router,
        "object_head",
        lambda key: {"ContentLength": "4096" if str(key).endswith("audio_mm.mp3") else "8192", "Content-Type": "audio/mpeg" if str(key).endswith("audio_mm.mp3") else "video/mp4"},
    )
    monkeypatch.setattr(
        tasks_router,
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

    payload = tasks_router._collect_hot_follow_workbench_ui(task, _settings())
    assert payload["final_exists"] is True
    assert payload["audio_ready"] is False
    assert payload["dub_current"] is False


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

    presentation = tasks_router._hf_rerun_presentation_state(task, voice_state, final_info, "failed")

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

    presentation = tasks_router._hf_rerun_presentation_state(task, voice_state, final_info, "done")

    assert presentation["last_successful_output"]["final_exists"] is True
    assert presentation["current_attempt"]["dub_status"] == "done"
    assert presentation["current_attempt"]["audio_ready"] is True
    assert presentation["current_attempt"]["dub_current"] is True
    assert presentation["current_attempt"]["resolved_voice"] == "my-MM-NilarNeural"
