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
