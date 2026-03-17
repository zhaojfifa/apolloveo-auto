"""Hot Follow production line contract (RFC-0001 Phase A).

Importing this module registers HOT_FOLLOW_LINE into the LineRegistry.
"""
from __future__ import annotations

from .base import LineRegistry, ProductionLine

HOT_FOLLOW_LINE: ProductionLine = LineRegistry.register(
    ProductionLine(
        line_id="hot_follow_line",
        line_name="Hot Follow Line",
        line_version="1.9.0",
        target_result_type="final_video",
        task_kind="hot_follow",
        sop_profile_ref="docs/sop/hot_follow_v1.md",
        skills_bundle_ref="docs/skills/",
        deliverable_kinds=(
            "final_video",
            "subtitle",
            "audio",
            "pack",
        ),
        auto_sink_enabled=True,
        confirmation_before_publish=True,
    )
)
