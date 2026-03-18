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
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.steps import subtitles as subtitles_step


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


def test_hot_follow_translation_normalizes_beauty_terms():
    text = "这个亚光唇釉真的布灵布灵，还有hagard色号"
    normalized = subtitles_step._normalize_hot_follow_origin_text(text)
    assert "哑光" in normalized
    assert "bling bling" in normalized
    assert "haggard" in normalized


def test_dual_channel_uses_voice_led_when_text_exists(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "Hello brand matte lip glaze")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "Hello brand matte lip glaze")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, _task: "")
    task = {
        "task_id": "hf-a2",
        "kind": "hot_follow",
        "platform": "douyin",
        "pipeline_config": "",
    }
    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-a2", task)
    route = hf_router._hf_dual_channel_state("hf-a2", task, subtitle_lane)
    assert route["speech_detected"] is True
    assert route["content_mode"] == "voice_led"
    assert route["recommended_path"] == "Voice dubbing"


def test_dual_channel_uses_silent_candidate_for_asmr_title(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, _task: "")
    task = {
        "task_id": "hf-a2-silent",
        "kind": "hot_follow",
        "title": "无人声涂抹音 asmr",
        "pipeline_config": "",
    }
    subtitle_lane = hf_router._hf_subtitle_lane_state("hf-a2-silent", task)
    route = hf_router._hf_dual_channel_state("hf-a2-silent", task, subtitle_lane)
    assert route["speech_detected"] is False
    assert route["content_mode"] == "silent_candidate"


def test_artifact_first_audio_ready_keeps_current_matching_audio(monkeypatch):
    monkeypatch.setattr(tasks_router, "get_settings", _settings)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "object_head", lambda _key: {"ContentLength": "4096", "Content-Type": "audio/mpeg"})
    monkeypatch.setattr(tasks_router, "media_meta_from_head", lambda _meta: (4096, "audio/mpeg"))
    task = {
        "task_id": "hf-a3",
        "kind": "hot_follow",
        "target_lang": "mm",
        "dub_status": "done",
        "mm_audio_key": "deliver/tasks/hf-a3/audio_mm.mp3",
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
    assert state["audio_ready"] is True
    assert state["audio_ready_reason"] == "ready"
    assert state["dub_current"] is True


def test_safe_workbench_ui_returns_defaults_on_builder_error(monkeypatch):
    monkeypatch.setattr(hf_router, "_collect_hot_follow_workbench_ui", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    task = {"task_id": "hf-a4", "kind": "hot_follow", "target_lang": "mm"}
    payload = hf_router._safe_collect_hot_follow_workbench_ui(task, _settings())
    assert payload["content_mode"] == "unknown"
    assert payload["lipsync_status"] == "off"
    assert payload["audio_ready"] is False
