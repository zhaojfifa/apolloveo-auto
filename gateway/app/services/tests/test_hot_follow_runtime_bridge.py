from pathlib import Path
import sys
import types

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim

from gateway.app.routers import hot_follow_api as hf_router
from gateway.app.services import hot_follow_runtime_bridge as compat_bridge


def test_explicit_compat_workbench_bridge_matches_legacy_alias(monkeypatch):
    task = {"task_id": "hf-compat", "kind": "hot_follow"}
    settings = object()
    expected = {"content_mode": "voice_led", "audio_ready": True}

    monkeypatch.setattr(
        hf_router,
        "_safe_collect_hot_follow_workbench_ui",
        lambda current_task, current_settings: expected
        if current_task is task and current_settings is settings
        else {},
    )

    assert compat_bridge.compat_collect_hot_follow_workbench_ui(task, settings) == expected
    assert compat_bridge.safe_collect_hot_follow_workbench_ui(task, settings) == expected


def test_explicit_compat_subtitle_compose_bridge_matches_legacy_alias(monkeypatch):
    task = {"task_id": "hf-compat-compose", "kind": "hot_follow"}

    monkeypatch.setattr(
        hf_router,
        "_hf_allow_subtitle_only_compose",
        lambda current_task_id, current_task: current_task_id == "hf-compat-compose" and current_task is task,
    )
    monkeypatch.setattr(
        hf_router,
        "_resolve_target_srt_key",
        lambda current_task, task_code, lang: f"{task_code}:{lang}"
        if current_task is task
        else None,
    )

    assert compat_bridge.compat_allow_subtitle_only_compose("hf-compat-compose", task) is True
    assert compat_bridge.hf_allow_subtitle_only_compose("hf-compat-compose", task) is True
    assert compat_bridge.compat_resolve_target_srt_key(task, "hf-compat-compose", "mm") == "hf-compat-compose:mm"
    assert compat_bridge.resolve_target_srt_key(task, "hf-compat-compose", "mm") == "hf-compat-compose:mm"


def test_compose_runtime_groups_existing_compat_hooks(monkeypatch):
    calls = {}

    monkeypatch.setattr(
        compat_bridge,
        "compat_get_hot_follow_workbench_hub",
        lambda task_id, repo: {"task_id": task_id, "repo": repo},
    )
    monkeypatch.setattr(
        compat_bridge,
        "compat_resolve_target_srt_key",
        lambda task, task_code, lang: f"{task_code}:{lang}:{task['task_id']}",
    )
    monkeypatch.setattr(
        compat_bridge,
        "compat_allow_subtitle_only_compose",
        lambda task_id, task: task_id == task["task_id"],
    )
    monkeypatch.setattr(
        compat_bridge,
        "compat_maybe_run_hot_follow_lipsync_stub",
        lambda task_id, enabled=False: f"{task_id}:{enabled}",
    )

    repo = object()
    runtime = compat_bridge.compat_hot_follow_compose_runtime(repo)
    task = {"task_id": "hf-runtime"}

    assert runtime["hub_loader"]("hf-runtime") == {"task_id": "hf-runtime", "repo": repo}
    assert runtime["subtitle_resolver"](task, "hf-runtime", "mm") == "hf-runtime:mm:hf-runtime"
    assert runtime["subtitle_only_check"]("hf-runtime", task) is True
    assert runtime["lipsync_runner"]("hf-runtime", enabled=True) == "hf-runtime:True"


def test_dub_route_state_and_no_dub_updates_preserve_existing_compat_logic(monkeypatch):
    monkeypatch.setattr(
        compat_bridge,
        "compat_hot_follow_subtitle_lane_state",
        lambda *_args, **_kwargs: {"dub_input_text": "  ", "lane": "subtitle"},
    )
    monkeypatch.setattr(
        compat_bridge,
        "compat_hot_follow_dual_channel_state",
        lambda *_args, **_kwargs: {"content_mode": "subtitle_led"},
    )

    state = compat_bridge.compat_hot_follow_dub_route_state("hf-dub", {"task_id": "hf-dub"})

    assert state["subtitle_lane"]["lane"] == "subtitle"
    assert state["route_state"]["content_mode"] == "subtitle_led"
    assert state["dub_input_text"] == ""
    assert state["no_dub_candidate"] is True

    updates = compat_bridge.compat_hot_follow_no_dub_updates(state["route_state"])
    assert updates["last_step"] == "dub"
    assert updates["dub_status"] == "skipped"
    assert updates["compose_status"] == "pending"
    assert updates["pipeline_config_updates"]["no_dub"] == "true"
    assert updates["pipeline_config_updates"]["dub_skip_reason"] == "subtitle_led"
