"""Thin compatibility facade for Hot Follow task-view helpers.

Authoritative projection lives in ``task_view_projection.py``.
Surface presenters live in ``task_view_presenters.py``.
This module remains as an import-stable shell for existing callers.
"""

from __future__ import annotations

from gateway.app.services.task_view_presenters import (
    build_hot_follow_publish_hub,
    build_hot_follow_workbench_hub,
    collect_hot_follow_workbench_ui,
    hf_artifact_facts,
    hf_current_attempt_summary,
    hf_operator_summary,
    hf_rerun_presentation_state,
    hf_safe_presentation_aggregates,
    hot_follow_operational_defaults,
    safe_collect_hot_follow_workbench_ui,
)
from gateway.app.services.task_view_projection import (
    build_hot_follow_workbench_projection,
    hf_deliverable_state,
    hf_deliverables,
    hf_pipeline_state,
    hf_shape_from_events,
    hf_task_status_shape,
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
    "hot_follow_operational_defaults",
    "safe_collect_hot_follow_workbench_ui",
]
