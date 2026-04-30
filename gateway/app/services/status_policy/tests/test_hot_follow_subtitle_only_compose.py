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

from gateway.app.routers import tasks as tasks_router  # noqa: F401
from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import subtitle_helpers as subtitle_helpers_module
from gateway.app.services import task_view as task_view_module
from gateway.app.services import task_view_helpers as task_view_helpers_module
from gateway.app.services import voice_state as voice_state_module
from gateway.app.services.status_policy.hot_follow_state import compute_hot_follow_state


def test_allow_subtitle_only_compose_for_silent_hot_follow(monkeypatch):
    monkeypatch.setattr(hf_router, "object_exists", lambda _key: True)
    monkeypatch.setattr(hf_router, "_hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(hf_router, "_hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        hf_router,
        "_hf_load_subtitles_text",
        lambda _task_id, _task: "1\n00:00:00,000 --> 00:00:02,000\n字幕版测试\n",
    )
    monkeypatch.setattr(subtitle_helpers_module, "object_exists", lambda _key: True)
    monkeypatch.setattr(subtitle_helpers_module, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(
        subtitle_helpers_module,
        "hf_load_subtitles_text",
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
    monkeypatch.setattr(subtitle_helpers_module, "object_exists", lambda _key: True)
    monkeypatch.setattr(subtitle_helpers_module, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_origin_subtitles_text", lambda _task: "标准口播测试")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_normalized_source_text", lambda _task_id, _task: "标准口播测试")
    monkeypatch.setattr(
        subtitle_helpers_module,
        "hf_load_subtitles_text",
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
    monkeypatch.setattr(subtitle_helpers_module, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers_module, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_subtitles_text", lambda _task_id, _task: "")
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
    monkeypatch.setattr(subtitle_helpers_module, "object_exists", lambda _key: False)
    monkeypatch.setattr(subtitle_helpers_module, "task_base_dir", lambda _task_id: Path("/tmp") / _task_id)
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_origin_subtitles_text", lambda _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_normalized_source_text", lambda _task_id, _task: "")
    monkeypatch.setattr(subtitle_helpers_module, "hf_load_subtitles_text", lambda _task_id, _task: "")
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


def test_ready_gate_allows_empty_no_dub_compose_reason_without_audio_or_subtitle():
    state = compute_hot_follow_state(
        {"task_id": "hf_empty_no_dub_gate", "kind": "hot_follow"},
        {
            "task_id": "hf_empty_no_dub_gate",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
            },
            "audio": {
                "status": "skipped",
                "audio_ready": False,
                "audio_ready_reason": "dub_not_done",
                "dub_current": False,
                "no_dub": True,
                "no_dub_reason": "target_subtitle_empty",
            },
        },
    )

    gate = state.get("ready_gate") or {}
    assert gate["audio_ready"] is False
    assert gate["subtitle_ready"] is False
    assert gate["no_dub"] is True
    assert gate["no_dub_compose_allowed"] is True
    assert gate["compose_ready"] is False
    assert gate["compose_reason"] == "compose_not_done"
    assert "subtitle_not_ready" not in (gate.get("blocking") or [])
    assert "target_subtitle_empty" not in (gate.get("blocking") or [])


def test_ready_gate_keeps_non_empty_no_dub_reason_blocking_when_subtitle_missing():
    state = compute_hot_follow_state(
        {"task_id": "hf_no_dub_subtitle_led_gate", "kind": "hot_follow"},
        {
            "task_id": "hf_no_dub_subtitle_led_gate",
            "final": {"exists": False},
            "subtitles": {
                "subtitle_ready": False,
                "subtitle_ready_reason": "subtitle_missing",
            },
            "audio": {
                "status": "skipped",
                "audio_ready": False,
                "audio_ready_reason": "dub_not_done",
                "dub_current": False,
                "no_dub": True,
                "no_dub_reason": "subtitle_led",
            },
        },
    )

    gate = state.get("ready_gate") or {}
    assert gate["no_dub_compose_allowed"] is False
    assert gate["compose_reason"] == "subtitle_led"
    assert "subtitle_led" in (gate.get("blocking") or [])


def test_composed_state_no_dub_empty_reason_does_not_report_missing_voiceover(monkeypatch):
    monkeypatch.setattr(task_view_helpers_module, "object_exists", lambda key: key.endswith("/raw.mp4"))
    monkeypatch.setattr(
        voice_state_module,
        "collect_voice_execution_state",
        lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "voiceover_url": None,
        },
    )

    state = task_view_helpers_module.compute_composed_state(
        {
            "task_id": "hf_empty_no_dub_composed",
            "kind": "hot_follow",
            "raw_path": "deliver/tasks/hf_empty_no_dub_composed/raw.mp4",
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "dub_input_empty",
            },
        },
        "hf_empty_no_dub_composed",
    )

    assert state["voice_exists"] is False
    assert state["composed_ready"] is False
    assert state["composed_reason"] == "final_missing"


def test_workbench_hub_allows_no_dub_compose_without_marking_dub_ready():
    task_id = "hf_empty_no_dub_hub"

    class _Repo:
        def get(self, _task_id):
            return {
                "task_id": task_id,
                "kind": "hot_follow",
                "raw_path": f"deliver/tasks/{task_id}/raw.mp4",
                "mute_video_key": f"deliver/tasks/{task_id}/mute.mp4",
                "dub_status": "skipped",
                "pipeline_config": {
                    "no_dub": "true",
                    "dub_skip_reason": "target_subtitle_empty",
                    "source_audio_policy": "mute",
                },
            }

    payload = task_view_module.build_hot_follow_workbench_hub(
        task_id,
        _Repo(),
        settings=object(),
        object_exists_fn=lambda key: str(key).endswith(("/raw.mp4", "/mute.mp4")),
        task_endpoint_loader=lambda current_task_id, endpoint: f"/v1/tasks/{current_task_id}/{endpoint}",
        subtitle_lane_loader=lambda *_args, **_kwargs: {
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
        composed_state_loader=lambda *_args, **_kwargs: {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": False},
            "historical_final": {"exists": False},
            "final_fresh": False,
            "final_stale_reason": None,
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": False,
        },
        pipeline_state_loader=lambda _task, step, **_kwargs: (
            ("skipped", "empty target subtitle") if step == "audio" else ("pending", "")
        ),
        scene_pack_info_loader=lambda *_args, **_kwargs: {},
        subtitles_text_loader=lambda *_args, **_kwargs: "",
        origin_subtitles_text_loader=lambda *_args, **_kwargs: "",
        normalized_source_text_loader=lambda *_args, **_kwargs: "",
        dual_channel_state_loader=lambda *_args, **_kwargs: {"content_mode": "unknown"},
        audio_config_loader=lambda _task: {"source_audio_policy": "mute"},
        voice_execution_state_loader=lambda *_args, **_kwargs: {
            "audio_ready": False,
            "audio_ready_reason": "dub_not_done",
            "dub_current": False,
            "dub_current_reason": "dub_not_done",
            "voiceover_url": None,
            "deliverable_audio_done": False,
        },
        persisted_audio_state_loader=lambda *_args, **_kwargs: {},
        deliverables_loader=lambda *_args, **_kwargs: [],
        presentation_aggregates_loader=lambda *_args, **_kwargs: ({}, {}, {}),
        presentation_state_loader=lambda *_args, **_kwargs: {},
        resolve_final_url_loader=lambda *_args, **_kwargs: None,
        operational_defaults_loader=lambda: {},
        workbench_ui_loader=lambda *_args, **_kwargs: {
            "no_dub": True,
            "no_dub_reason": "target_subtitle_empty",
            "audio_ready": False,
            "dub_current": False,
        },
        backfill_compose_done=lambda *_args, **_kwargs: False,
        line_binding_loader=lambda _task: SimpleNamespace(to_payload=lambda: {"line_id": "hot_follow_line"}),
    )

    ready_gate = payload.get("ready_gate") or {}
    assert payload["audio"]["no_dub"] is True
    assert payload["audio"]["no_dub_compose_allowed"] is True
    assert payload["compose_allowed"] is True
    assert payload["compose_allowed_reason"] == "no_dub_inputs_ready"
    assert ready_gate["audio_ready"] is False
    assert ready_gate["no_dub_compose_allowed"] is True
    assert ready_gate["compose_allowed"] is True
    assert ready_gate["compose_ready"] is False
