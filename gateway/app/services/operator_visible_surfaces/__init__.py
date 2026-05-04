"""Operator-visible surface projections (Phase 3A minimal wiring).

This package contains the additive read-only projections that the four
operator-visible surfaces (Board, Workbench, Delivery, Hot Follow panel)
consume. It does not own truth, mutate the packet, or write into L2/L3.

Scope is bound by `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`:
B-roll surfaces are explicitly out of scope until product freeze.
"""
from .advisory_emitter import emit_advisories
from .projections import (
    PANEL_REF_DISPATCH,
    derive_board_publishable,
    derive_delivery_publish_gate,
    derive_delivery_publish_status_mirror,
    project_operator_surfaces,
    resolve_line_specific_panel,
    sanitize_operator_payload,
)
from .publish_readiness import (
    CLOSED_HEAD_REASON_ENUM,
    compute_publish_readiness,
)
from .wiring import (
    build_board_row_projection,
    build_operator_surfaces_for_publish_hub,
    build_operator_surfaces_for_workbench,
)

__all__ = [
    "CLOSED_HEAD_REASON_ENUM",
    "PANEL_REF_DISPATCH",
    "build_board_row_projection",
    "build_operator_surfaces_for_publish_hub",
    "build_operator_surfaces_for_workbench",
    "compute_publish_readiness",
    "derive_board_publishable",
    "derive_delivery_publish_gate",
    "derive_delivery_publish_status_mirror",
    "emit_advisories",
    "project_operator_surfaces",
    "resolve_line_specific_panel",
    "sanitize_operator_payload",
]
