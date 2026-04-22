"""Thin compatibility facade for Hot Follow task-view helpers.

Authoritative projection lives in ``task_view_projection.py``.
Surface presenters live in ``task_view_presenters.py``.
This module remains as an import-stable shell for existing callers.
"""

from __future__ import annotations

from gateway.app.services.artifact_storage import object_exists
from gateway.app.services.subtitle_helpers import hf_dual_channel_state, hf_subtitle_lane_state
from gateway.app.services.task_view_presenters import (
    build_hot_follow_publish_hub,
    build_hot_follow_workbench_hub,
    hf_artifact_facts,
    hf_current_attempt_summary,
    hf_operator_summary,
    hf_rerun_presentation_state,
    hf_safe_presentation_aggregates,
    hot_follow_operational_defaults,
    collect_hot_follow_workbench_ui as _svc_collect_hot_follow_workbench_ui,
    safe_collect_hot_follow_workbench_ui as _svc_safe_collect_hot_follow_workbench_ui,
)
from gateway.app.services.task_view_projection import (
    build_hot_follow_workbench_projection,
    hf_deliverable_state,
    hf_deliverables,
    hf_pipeline_state,
    hf_shape_from_events,
    hf_task_status_shape,
)
from gateway.app.services.voice_service import (
    hf_screen_text_candidate_summary,
    hf_source_audio_lane_summary,
    hf_source_audio_semantics,
)
from gateway.app.services.voice_state import build_hot_follow_voice_options, collect_voice_execution_state


def collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    subtitle_lane_loader=None,
    dual_channel_state_loader=None,
    source_audio_lane_loader=None,
    screen_text_candidate_loader=None,
    voice_execution_state_loader=None,
    pipeline_state_loader=None,
    object_exists_fn=None,
    source_audio_semantics_loader=None,
) -> dict:
    return _svc_collect_hot_follow_workbench_ui(
        task,
        settings,
        subtitle_lane_loader=subtitle_lane_loader or hf_subtitle_lane_state,
        dual_channel_state_loader=dual_channel_state_loader or hf_dual_channel_state,
        source_audio_lane_loader=source_audio_lane_loader or hf_source_audio_lane_summary,
        screen_text_candidate_loader=screen_text_candidate_loader or hf_screen_text_candidate_summary,
        voice_execution_state_loader=voice_execution_state_loader or collect_voice_execution_state,
        pipeline_state_loader=pipeline_state_loader or hf_pipeline_state,
        object_exists_fn=object_exists_fn or object_exists,
        source_audio_semantics_loader=source_audio_semantics_loader or hf_source_audio_semantics,
    )


def safe_collect_hot_follow_workbench_ui(
    task: dict,
    settings,
    *,
    workbench_ui_loader=None,
    voice_options_builder=None,
) -> dict:
    return _svc_safe_collect_hot_follow_workbench_ui(
        task,
        settings,
        workbench_ui_loader=workbench_ui_loader or collect_hot_follow_workbench_ui,
        voice_options_builder=voice_options_builder or build_hot_follow_voice_options,
    )

__all__ = [
    "build_hot_follow_publish_hub",
    "build_hot_follow_workbench_hub",
    "build_hot_follow_workbench_projection",
    "collect_hot_follow_workbench_ui",
    "hf_artifact_facts",
    "hf_current_attempt_summary",
    "hf_deliverable_state",
    "hf_deliverables",
    "hf_operator_summary",
    "hf_pipeline_state",
    "hf_rerun_presentation_state",
    "hf_safe_presentation_aggregates",
    "hf_shape_from_events",
    "hf_task_status_shape",
    "hf_subtitle_lane_state",
    "hot_follow_operational_defaults",
    "object_exists",
    "safe_collect_hot_follow_workbench_ui",
    "collect_voice_execution_state",
]
