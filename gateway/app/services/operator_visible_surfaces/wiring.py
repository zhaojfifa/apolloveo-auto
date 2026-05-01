"""Phase 3B presenter-side wiring for operator-visible surface projections.

Pure adapter layer. Takes whatever shape the existing presenters already
produce (task dict, authoritative state, publish surface payload) and
calls into the Phase 3A projection module to derive the four
operator-visible surface payloads.

Strict additive contract:

- Reads only fields that already exist upstream (`ready_gate`,
  `final`/`final_stale_reason`, `line_specific_refs`, task-side closure).
- Never mutates the inputs. Returns new dicts only.
- Never recomputes the gate, current attempt, or any line-specific truth.
- Never carries vendor / model / provider / engine identifiers — the
  projection module's `sanitize_operator_payload` is applied at every
  surface boundary that exposes ref payloads.
- B-roll is intentionally not consumed here — the projection module has
  no B-roll surface and this wiring layer adds none.

Authority cited:
- ``docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md``
- ``docs/reviews/operator_visible_surface_wiring_feasibility_v1.md``
- ``docs/reviews/architect_phase2_lowfi_review_v1.md``
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from .projections import (
    derive_board_publishable,
    derive_delivery_publish_gate,
    derive_delivery_publish_status_mirror,
    project_operator_surfaces,
    resolve_line_specific_panel,
)


def _packet_view(task: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the minimal packet view the projection module needs.

    Tasks today rarely carry a full factory packet; the projection
    resolver only requires `line_specific_refs`. Fall back to an empty
    list so the resolver returns ``panel_kind=None`` cleanly.
    """
    if not isinstance(task, Mapping):
        return {"line_specific_refs": []}
    refs = task.get("line_specific_refs")
    if not isinstance(refs, list):
        envelope = task.get("packet")
        if isinstance(envelope, Mapping):
            refs = envelope.get("line_specific_refs")
    if not isinstance(refs, list):
        refs = []
    return {"line_specific_refs": list(refs)}


def _l2_facts_from_state(
    state: Mapping[str, Any] | None,
    task: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapt authoritative state to the L2 facts shape the gate consumes.

    Falls back to the task dict when the state does not carry the field.
    """
    state_map = state if isinstance(state, Mapping) else {}
    task_map = task if isinstance(task, Mapping) else {}
    final = state_map.get("final")
    if not isinstance(final, Mapping):
        final = task_map.get("final") if isinstance(task_map.get("final"), Mapping) else {"exists": False}
    final_stale_reason = state_map.get("final_stale_reason")
    if final_stale_reason is None:
        final_stale_reason = task_map.get("final_stale_reason")
    return {
        "final": dict(final),
        "final_stale_reason": final_stale_reason,
    }


def build_board_row_projection(
    task: Mapping[str, Any],
    *,
    ready_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-row Board projection. Adds ``publishable`` + ``head_reason`` only.

    Reads ``ready_gate`` from the row when not passed explicitly.
    """
    gate = ready_gate
    if gate is None and isinstance(task, Mapping):
        gate = task.get("ready_gate") if isinstance(task.get("ready_gate"), Mapping) else {}
    return derive_board_publishable(gate or {})


def build_operator_surfaces_for_workbench(
    *,
    task: Mapping[str, Any],
    authoritative_state: Mapping[str, Any] | None,
    publish_feedback_closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Workbench-side projection bundle.

    Returns the full ``project_operator_surfaces`` shape so a single
    payload can drive the L3 strip, the line-specific panel mount, and
    the Hot Follow right-rail panel.
    """
    state = authoritative_state or {}
    ready_gate = state.get("ready_gate") if isinstance(state.get("ready_gate"), Mapping) else (
        task.get("ready_gate") if isinstance(task.get("ready_gate"), Mapping) else {}
    )
    return project_operator_surfaces(
        ready_gate=ready_gate or {},
        l2_facts=_l2_facts_from_state(state, task),
        packet=_packet_view(task),
        publish_feedback_closure=publish_feedback_closure,
    )


def build_operator_surfaces_for_publish_hub(
    *,
    task: Mapping[str, Any],
    authoritative_state: Mapping[str, Any],
    publish_feedback_closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Delivery-side projection bundle.

    Surfaces:
      - ``publish_gate`` + ``publish_gate_head_reason`` — single derived
        publish gate (Optional items never reach the AND inputs).
      - ``publish_status_mirror`` — read-only mirror of task-side closure.
      - ``line_specific_panel`` — same resolver shape so a Workbench-style
        right-rail mount could attach later.
    """
    ready_gate = (
        authoritative_state.get("ready_gate")
        if isinstance(authoritative_state.get("ready_gate"), Mapping)
        else (task.get("ready_gate") if isinstance(task.get("ready_gate"), Mapping) else {})
    )
    l2_facts = _l2_facts_from_state(authoritative_state, task)
    publish_gate = derive_delivery_publish_gate(ready_gate or {}, l2_facts)
    publish_status_mirror = derive_delivery_publish_status_mirror(publish_feedback_closure)
    panel = resolve_line_specific_panel(_packet_view(task))
    return {
        **publish_gate,
        "publish_status_mirror": publish_status_mirror,
        "line_specific_panel": panel,
    }


__all__ = [
    "build_board_row_projection",
    "build_operator_surfaces_for_workbench",
    "build_operator_surfaces_for_publish_hub",
]
