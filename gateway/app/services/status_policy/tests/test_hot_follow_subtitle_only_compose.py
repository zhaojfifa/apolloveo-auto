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

from gateway.app.routers import tasks as tasks_router  # noqa: F401
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import subtitle_helpers as subtitle_helpers_module
from gateway.app.services import task_view as task_view_module


def test_allow_subtitle_only_compose_for_silent_hot_follow(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        hf_router,
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
    assert hf_router._hf_allow_subtitle_only_compose("hf_silent", task) is True


def test_do_not_allow_subtitle_only_compose_for_voice_led_hot_follow(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "标准口播测试")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "标准口播测试")
    monkeypatch.setattr(
        hf_router,
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
    assert hf_router._hf_allow_subtitle_only_compose("hf_voice", task) is False


def test_allow_no_dub_empty_target_subtitle_compose_even_without_subtitle_ready(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, _task: "")
    task = {
        "task_id": "hf_empty_dub",
        "kind": "hot_follow",
        "title": "standard video with intentionally empty target subtitle",
        "pipeline_config": {
            "no_dub": "true",
            "dub_skip_reason": "target_subtitle_empty",
        },
        "dub_status": "skipped",
    }

    assert hf_router._hf_allow_subtitle_only_compose("hf_empty_dub", task) is True


def test_service_allows_no_dub_empty_target_subtitle_compose(monkeypatch):
    monkeypatch.setattr(subtitle_helpers_module, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_subtitles_text", lambda _task_id, _task: "")

    assert subtitle_helpers_module.hf_allow_subtitle_only_compose(
        "hf_empty_dub_service",
        {
            "task_id": "hf_empty_dub_service",
            "kind": "hot_follow",
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
            },
            "dub_status": "skipped",
        },
    ) is True


def test_workbench_projects_empty_dub_as_skipped_not_failed(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: False)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_subtitles_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        hf_router,
        "_collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "voiceover_url": None,
            "deliverable_audio_done": False,
        },
    )

    payload = hf_router._collect_hot_follow_workbench_ui(
        {
            "task_id": "hf_empty_dub_ui",
            "kind": "hot_follow",
            "dub_status": "skipped",
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
            },
        },
        settings=object(),
    )

    assert payload["no_dub"] is True
    assert payload["no_dub_reason"] == "target_subtitle_empty"
    assert payload["audio_ready"] is False
    assert payload["dub_current"] is False


def test_service_workbench_projects_empty_dub_reason(monkeypatch):
    monkeypatch.setattr(task_view_module, "object_exists", lambda _key: False)
    monkeypatch.setattr(
        task_view_module,
        "hf_subtitle_lane_state",
        lambda _task_id, _task: {
            "raw_source_text": "",
            "normalized_source_text": "",
            "parse_source_text": "",
            "edited_text": "",
            "dub_input_text": "",
            "subtitle_ready": False,
            "subtitle_ready_reason": "subtitle_missing",
            "target_subtitle_current": False,
            "target_subtitle_current_reason": "subtitle_missing",
        },
    )
    monkeypatch.setattr(
        task_view_module,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "voiceover_url": None,
            "deliverable_audio_done": False,
        },
    )

    payload = task_view_module.collect_hot_follow_workbench_ui(
        {
            "task_id": "hf_empty_dub_service_ui",
            "kind": "hot_follow",
            "dub_status": "skipped",
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "dub_input_empty",
            },
        },
        settings=object(),
    )

    assert payload["no_dub"] is True
    assert payload["no_dub_reason"] == "dub_input_empty"
    assert payload["audio_ready"] is False
    assert payload["dub_current"] is False
