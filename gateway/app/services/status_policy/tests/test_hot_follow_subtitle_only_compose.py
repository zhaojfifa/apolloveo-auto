from pathlib import Path
import sys
import types

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


def test_allow_subtitle_only_compose_for_silent_hot_follow(monkeypatch):
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        tasks_router,
        "_hf_load_subtitles_text",
        lambda _task_id, _task: "1\n00:00:00,000 --> 00:00:02,000\n字幕版测试\n",
    )
    task = {
        "task_id": "hf_silent",
        "kind": "hot_follow",
        "title": "无人声涂抹音 ASMR",
        "pipeline_config": {"no_dub": "true"},
        "mm_srt_path": "deliver/tasks/hf_silent/mm.srt",
        "dub_skip_reason": "no_speech_detected",
    }
    assert tasks_router._hf_allow_subtitle_only_compose("hf_silent", task) is True


def test_do_not_allow_subtitle_only_compose_for_voice_led_hot_follow(monkeypatch):
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda _task: "标准口播测试")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "标准口播测试")
    monkeypatch.setattr(
        tasks_router,
        "_hf_load_subtitles_text",
        lambda _task_id, _task: "1\n00:00:00,000 --> 00:00:02,000\n标准口播测试\n",
    )
    task = {
        "task_id": "hf_voice",
        "kind": "hot_follow",
        "title": "标准口播视频",
        "pipeline_config": {},
        "mm_srt_path": "deliver/tasks/hf_voice/mm.srt",
    }
    assert tasks_router._hf_allow_subtitle_only_compose("hf_voice", task) is False
