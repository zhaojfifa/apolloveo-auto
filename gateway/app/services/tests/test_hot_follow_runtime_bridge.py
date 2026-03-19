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
