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
        input_contract_ref="docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md",
        deliverable_profile_ref="docs/architecture/line_contracts/hot_follow_line.yaml",
        sop_profile_ref="docs/runbooks/hot_follow_sop.md",
        skills_bundle_ref="docs/skills/",
        worker_profile_ref="docs/contracts/worker_gateway_contract.md",
        asset_sink_profile_ref="docs/contracts/status_ownership_matrix.md",
        ready_gate_ref="docs/contracts/hot_follow_ready_gate.yaml",
        status_policy_ref="gateway/app/services/status_policy/hot_follow_state.py",
        deliverable_kinds=(
            "final_video",
            "subtitle",
            "audio",
            "pack",
        ),
        auto_sink_enabled=True,
        confirmation_before_execute=False,
        confirmation_before_result_accept=False,
        confirmation_before_publish=True,
        confirmation_before_retry=False,
    )
)
