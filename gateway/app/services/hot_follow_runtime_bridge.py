"""Hot Follow runtime bridge.

PR-2 uses this module as the narrow service entry for helpers that still live
in ``hot_follow_api.py``. The goal is to break direct router-to-router imports
without changing business logic in the same patch.
"""

from __future__ import annotations

from typing import Any


def hot_follow_operational_defaults() -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hot_follow_operational_defaults

    return _hot_follow_operational_defaults()


def safe_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _safe_collect_hot_follow_workbench_ui

    return _safe_collect_hot_follow_workbench_ui(task, settings)


def hf_task_status_shape(task: dict) -> dict[str, str]:
    from gateway.app.routers.hot_follow_api import _hf_task_status_shape

    return _hf_task_status_shape(task)


def maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    from gateway.app.routers.hot_follow_api import _maybe_run_hot_follow_lipsync_stub

    return _maybe_run_hot_follow_lipsync_stub(task_id, enabled=enabled)


def hf_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_compose_final_video

    return _hf_compose_final_video(task_id, task)


def get_hot_follow_workbench_hub(task_id: str, repo) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import get_hot_follow_workbench_hub

    return get_hot_follow_workbench_hub(task_id, repo=repo)


def hf_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_subtitle_lane_state

    return _hf_subtitle_lane_state(task_id, task)


def hf_dual_channel_state(
    task_id: str,
    task: dict,
    subtitle_lane: dict[str, Any] | None = None,
    *,
    subtitles_step_done: bool = True,
) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_dual_channel_state

    return _hf_dual_channel_state(
        task_id,
        task,
        subtitle_lane,
        subtitles_step_done=subtitles_step_done,
    )


def hf_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_target_lang_gate

    return _hf_target_lang_gate(text, target_lang=target_lang)
