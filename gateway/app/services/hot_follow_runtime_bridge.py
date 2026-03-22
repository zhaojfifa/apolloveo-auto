"""Hot Follow compatibility bridge.

This module is intentionally a compatibility-only boundary for helpers that
still live in ``hot_follow_api.py``. It exists to keep ``tasks.py`` from
depending on router internals directly while the remaining Hot Follow cleanup
continues.

Rules for this module:
- do not add new business orchestration here
- do not treat these exports as primary runtime ownership
- keep any remaining helpers thin and transitional
"""

from __future__ import annotations

from typing import Any


def compat_hot_follow_compose_runtime(
    repo,
    *,
    hub_loader=None,
    subtitle_resolver=None,
    subtitle_only_check=None,
    lipsync_runner=None,
) -> dict[str, Any]:
    return {
        "hub_loader": lambda task_id, current_repo=repo, loader=(hub_loader or compat_get_hot_follow_workbench_hub): loader(
            task_id,
            repo=current_repo,
        ),
        "subtitle_resolver": subtitle_resolver or compat_resolve_target_srt_key,
        "subtitle_only_check": subtitle_only_check or compat_allow_subtitle_only_compose,
        "lipsync_runner": lipsync_runner or compat_maybe_run_hot_follow_lipsync_stub,
    }


def compat_hot_follow_operational_defaults() -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hot_follow_operational_defaults

    return _hot_follow_operational_defaults()


def compat_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _safe_collect_hot_follow_workbench_ui

    return _safe_collect_hot_follow_workbench_ui(task, settings)


def compat_hot_follow_task_status_shape(task: dict) -> dict[str, str]:
    from gateway.app.routers.hot_follow_api import _hf_task_status_shape

    return _hf_task_status_shape(task)


def compat_maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    from gateway.app.routers.hot_follow_api import _maybe_run_hot_follow_lipsync_stub

    return _maybe_run_hot_follow_lipsync_stub(task_id, enabled=enabled)


def compat_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_compose_final_video

    return _hf_compose_final_video(task_id, task)


def compat_get_hot_follow_workbench_hub(task_id: str, repo) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import get_hot_follow_workbench_hub

    return get_hot_follow_workbench_hub(task_id, repo=repo)


def compat_hot_follow_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_subtitle_lane_state

    return _hf_subtitle_lane_state(task_id, task)


def compat_hot_follow_dual_channel_state(
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


def compat_hot_follow_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    from gateway.app.routers.hot_follow_api import _hf_target_lang_gate

    return _hf_target_lang_gate(text, target_lang=target_lang)


def compat_hot_follow_dub_route_state(
    task_id: str,
    task: dict[str, Any],
    *,
    mm_text_override: str | None = None,
    subtitle_lane_loader=None,
    dual_channel_loader=None,
) -> dict[str, Any]:
    subtitle_lane = (subtitle_lane_loader or compat_hot_follow_subtitle_lane_state)(task_id, task)
    route_state = (dual_channel_loader or compat_hot_follow_dual_channel_state)(task_id, task, subtitle_lane)
    lane_text = str(subtitle_lane.get("dub_input_text") or "").strip()
    override_text = str(mm_text_override or "").strip()
    dub_input_text = override_text or lane_text
    no_dub_candidate = (
        route_state.get("content_mode") in {"silent_candidate", "subtitle_led"}
        and not override_text
        and not lane_text
    )
    return {
        "subtitle_lane": subtitle_lane,
        "route_state": route_state,
        "dub_input_text": dub_input_text,
        "no_dub_candidate": no_dub_candidate,
    }


def compat_hot_follow_no_dub_updates(route_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_step": "dub",
        "dub_status": "skipped",
        "dub_error": None,
        "compose_status": "pending",
        "pipeline_config_updates": {
            "no_dub": "true",
            "dub_skip_reason": (
                "subtitle_led"
                if route_state.get("content_mode") == "subtitle_led"
                else "no_speech_detected"
            ),
        },
    }


def compat_allow_subtitle_only_compose(task_id: str, task: dict) -> bool:
    from gateway.app.routers.hot_follow_api import _hf_allow_subtitle_only_compose

    return _hf_allow_subtitle_only_compose(task_id, task)


def compat_resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    from gateway.app.routers.hot_follow_api import _resolve_target_srt_key

    return _resolve_target_srt_key(task_obj, task_code, lang)


# Deprecated aliases kept for behavior stability while callers migrate to the
# explicit compatibility surface above.
def hot_follow_operational_defaults() -> dict[str, Any]:
    return compat_hot_follow_operational_defaults()


def hot_follow_compose_runtime(repo) -> dict[str, Any]:
    return compat_hot_follow_compose_runtime(repo)


def safe_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    return compat_collect_hot_follow_workbench_ui(task, settings)


def hf_task_status_shape(task: dict) -> dict[str, str]:
    return compat_hot_follow_task_status_shape(task)


def maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    return compat_maybe_run_hot_follow_lipsync_stub(task_id, enabled=enabled)


def hf_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    return compat_compose_final_video(task_id, task)


def get_hot_follow_workbench_hub(task_id: str, repo) -> dict[str, Any]:
    return compat_get_hot_follow_workbench_hub(task_id, repo=repo)


def hf_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    return compat_hot_follow_subtitle_lane_state(task_id, task)


def hf_dual_channel_state(
    task_id: str,
    task: dict,
    subtitle_lane: dict[str, Any] | None = None,
    *,
    subtitles_step_done: bool = True,
) -> dict[str, Any]:
    return compat_hot_follow_dual_channel_state(
        task_id,
        task,
        subtitle_lane,
        subtitles_step_done=subtitles_step_done,
    )


def hf_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    return compat_hot_follow_target_lang_gate(text, target_lang=target_lang)


def hf_dub_route_state(
    task_id: str,
    task: dict[str, Any],
    *,
    mm_text_override: str | None = None,
    subtitle_lane_loader=None,
    dual_channel_loader=None,
) -> dict[str, Any]:
    return compat_hot_follow_dub_route_state(
        task_id,
        task,
        mm_text_override=mm_text_override,
        subtitle_lane_loader=subtitle_lane_loader,
        dual_channel_loader=dual_channel_loader,
    )


def hf_no_dub_updates(route_state: dict[str, Any]) -> dict[str, Any]:
    return compat_hot_follow_no_dub_updates(route_state)


def hf_allow_subtitle_only_compose(task_id: str, task: dict) -> bool:
    return compat_allow_subtitle_only_compose(task_id, task)


def resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    return compat_resolve_target_srt_key(task_obj, task_code, lang)
