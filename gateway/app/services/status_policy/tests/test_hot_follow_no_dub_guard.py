import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    from pydantic import BaseModel

    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import tasks as tasks_router


def test_hot_follow_no_dub_guard_detects_empty_transcript(monkeypatch):
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda task: "")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda task_id: "")
    monkeypatch.setattr(tasks_router, "_hf_load_subtitles_text", lambda task_id, task: "")

    task = {
        "task_id": "hf-no-dub-01",
        "kind": "hot_follow",
        "title": "无人声涂抹音试色",
        "pipeline_config": {"no_subtitles": "true"},
    }

    state = tasks_router._hf_detect_no_dub_candidate("hf-no-dub-01", task)
    assert state["no_dub"] is True
    assert state["no_dub_reason"] == "no_speech_detected"


def test_hot_follow_no_dub_guard_allows_manual_override(monkeypatch):
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda task: "")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda task_id: "")
    monkeypatch.setattr(tasks_router, "_hf_load_subtitles_text", lambda task_id, task: "")

    task = {
        "task_id": "hf-no-dub-02",
        "kind": "hot_follow",
        "title": "无人声涂抹音试色",
        "pipeline_config": {"no_subtitles": "true"},
    }

    state = tasks_router._hf_detect_no_dub_candidate(
        "hf-no-dub-02",
        task,
        manual_text="1\n00:00:00,000 --> 00:00:01,000\n手工字幕\n",
    )
    assert state["no_dub"] is False
    assert state["manual_override_available"] is True


def test_hot_follow_dual_channel_state_marks_subtitle_led_candidate(monkeypatch):
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda task: "")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda task_id: "")
    monkeypatch.setattr(tasks_router, "_hf_load_subtitles_text", lambda task_id, task: "")

    task = {
        "task_id": "hf-route-01",
        "kind": "hot_follow",
        "title": "字幕版试色",
        "pipeline_config": {"subtitle_stream": "true"},
    }

    state = tasks_router._hf_dual_channel_state("hf-route-01", task)
    assert state["speech_detected"] is False
    assert state["onscreen_text_detected"] is True
    assert state["content_mode"] == "subtitle_led_candidate"


def test_hot_follow_dual_channel_state_marks_silent_candidate(monkeypatch):
    monkeypatch.setattr(tasks_router, "_hf_load_origin_subtitles_text", lambda task: "")
    monkeypatch.setattr(tasks_router, "_hf_load_normalized_source_text", lambda task_id: "")
    monkeypatch.setattr(tasks_router, "_hf_load_subtitles_text", lambda task_id, task: "")

    task = {
        "task_id": "hf-route-02",
        "kind": "hot_follow",
        "title": "无人声涂抹音",
        "pipeline_config": {},
    }

    state = tasks_router._hf_dual_channel_state("hf-route-02", task)
    assert state["speech_detected"] is False
    assert state["onscreen_text_detected"] is False
    assert state["content_mode"] == "silent_candidate"
