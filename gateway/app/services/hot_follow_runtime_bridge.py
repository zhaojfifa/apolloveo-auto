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

from gateway.app.config import get_settings
from gateway.app.ports.storage_provider import get_storage_service
from gateway.app.services.compose_service import CompositionService
from gateway.app.services.subtitle_helpers import (
    hf_allow_subtitle_only_compose as _svc_hf_allow_subtitle_only_compose,
    hf_dual_channel_state as _svc_hf_dual_channel_state,
    hf_subtitle_lane_state as _svc_hf_subtitle_lane_state,
    hf_target_lang_gate as _svc_hf_target_lang_gate,
    hot_follow_dub_route_state as _svc_hot_follow_dub_route_state,
    hot_follow_no_dub_updates as _svc_hot_follow_no_dub_updates,
    resolve_target_srt_key as _svc_resolve_target_srt_key,
)
from gateway.app.services.task_view import (
    build_hot_follow_workbench_hub as _svc_build_hot_follow_workbench_hub,
    hf_task_status_shape as _svc_hf_task_status_shape,
    hot_follow_operational_defaults as _svc_hot_follow_operational_defaults,
    safe_collect_hot_follow_workbench_ui as _svc_safe_collect_hot_follow_workbench_ui,
)
from gateway.app.services.voice_service import maybe_run_hot_follow_lipsync_stub as _svc_maybe_run_hot_follow_lipsync_stub


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
    return _svc_hot_follow_operational_defaults()


def compat_collect_hot_follow_workbench_ui(task: dict, settings) -> dict[str, Any]:
    return _svc_safe_collect_hot_follow_workbench_ui(task, settings)


def compat_hot_follow_task_status_shape(task: dict) -> dict[str, str]:
    return _svc_hf_task_status_shape(task)


def compat_maybe_run_hot_follow_lipsync_stub(task_id: str, enabled: bool = False) -> str | None:
    return _svc_maybe_run_hot_follow_lipsync_stub(task_id, enabled=enabled)


def compat_compose_final_video(task_id: str, task: dict) -> dict[str, Any]:
    svc = CompositionService(storage=get_storage_service(), settings=get_settings())
    return svc.compose(
        task_id,
        task,
        subtitle_resolver=_svc_resolve_target_srt_key,
        subtitle_only_check=_svc_hf_allow_subtitle_only_compose,
    )


def compat_get_hot_follow_workbench_hub(task_id: str, repo) -> dict[str, Any]:
    return _svc_build_hot_follow_workbench_hub(task_id, repo=repo)


def compat_hot_follow_subtitle_lane_state(task_id: str, task: dict) -> dict[str, Any]:
    return _svc_hf_subtitle_lane_state(task_id, task)


def compat_hot_follow_dual_channel_state(
    task_id: str,
    task: dict,
    subtitle_lane: dict[str, Any] | None = None,
    *,
    subtitles_step_done: bool = True,
) -> dict[str, Any]:
    return _svc_hf_dual_channel_state(
        task_id,
        task,
        subtitle_lane,
        subtitles_step_done=subtitles_step_done,
    )


def compat_hot_follow_target_lang_gate(text: str, *, target_lang: str) -> dict[str, Any]:
    return _svc_hf_target_lang_gate(text, target_lang=target_lang)


def compat_hot_follow_dub_route_state(
    task_id: str,
    task: dict[str, Any],
    *,
    mm_text_override: str | None = None,
    subtitle_lane_loader=None,
    dual_channel_loader=None,
) -> dict[str, Any]:
    return _svc_hot_follow_dub_route_state(
        task_id,
        task,
        mm_text_override=mm_text_override,
        subtitle_lane_loader=subtitle_lane_loader or compat_hot_follow_subtitle_lane_state,
        dual_channel_loader=dual_channel_loader or compat_hot_follow_dual_channel_state,
    )


def compat_hot_follow_no_dub_updates(route_state: dict[str, Any]) -> dict[str, Any]:
    return _svc_hot_follow_no_dub_updates(route_state)


def compat_allow_subtitle_only_compose(task_id: str, task: dict) -> bool:
    return _svc_hf_allow_subtitle_only_compose(task_id, task)


def compat_resolve_target_srt_key(task_obj: dict, task_code: str, lang: str) -> str | None:
    return _svc_resolve_target_srt_key(task_obj, task_code, lang)


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
