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

from gateway.app.services.matrix_script.workbench_variation_surface import (
    project_workbench_variation_surface,
)

from .projections import (
    derive_board_publishable,
    derive_delivery_publish_gate,
    derive_delivery_publish_status_mirror,
    project_operator_surfaces,
    resolve_line_specific_panel,
)
from .publish_readiness import compute_publish_readiness


_PACKET_PASSTHROUGH_KEYS = (
    "line_id",
    "packet_version",
    "binding",
    "evidence",
    "generic_refs",
    "metadata",
)


def _packet_view(task: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the packet view the projection modules need.

    The line-specific resolver only requires `line_specific_refs`. The
    Matrix Script workbench variation projection additionally consumes
    `binding`, `evidence`, `generic_refs`, and packet identity. We surface
    those fields when the task carries an attached `packet` envelope so
    the projection has authoritative inputs; otherwise the projection
    falls back to empty deltas cleanly.
    """
    if not isinstance(task, Mapping):
        return {"line_specific_refs": []}
    envelope: Mapping[str, Any] = (
        task.get("packet") if isinstance(task.get("packet"), Mapping) else {}
    )
    refs = task.get("line_specific_refs")
    if not isinstance(refs, list):
        refs = envelope.get("line_specific_refs") if envelope else None
    if not isinstance(refs, list):
        refs = []
    view: dict[str, Any] = {"line_specific_refs": list(refs)}
    for key in _PACKET_PASSTHROUGH_KEYS:
        value = task.get(key)
        if value is None and envelope:
            value = envelope.get(key)
        if value is not None:
            view[key] = value
    return view


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


def _l3_current_attempt_from_state(
    state: Mapping[str, Any] | None,
    task: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    """Locate the L3 CurrentAttempt dict on either the state or the task.

    Returns None when neither carries the structure; the unified producer
    treats `None` provenance as "not declared" and falls back to ready_gate
    + L2 truth without raising final_provenance_historical.
    """
    for source in (state, task):
        if isinstance(source, Mapping):
            attempt = source.get("current_attempt")
            if isinstance(attempt, Mapping):
                return attempt
    return None


def build_operator_surfaces_for_workbench(
    *,
    task: Mapping[str, Any],
    authoritative_state: Mapping[str, Any] | None,
    publish_feedback_closure: Optional[Mapping[str, Any]] = None,
    delivery_rows: Optional[Any] = None,
) -> dict[str, Any]:
    """Workbench-side projection bundle.

    Returns the full ``project_operator_surfaces`` shape so a single
    payload can drive the L3 strip, the line-specific panel mount, and
    the Hot Follow right-rail panel. PR-1 additionally exposes the
    unified ``publish_readiness`` projection on the bundle so the
    Workbench renders the same publishability truth Board and Delivery
    consume — no per-surface re-derivation.
    """
    state = authoritative_state or {}
    ready_gate = state.get("ready_gate") if isinstance(state.get("ready_gate"), Mapping) else (
        task.get("ready_gate") if isinstance(task.get("ready_gate"), Mapping) else {}
    )
    packet_view = _packet_view(task)
    l2_facts = _l2_facts_from_state(state, task)
    l3_current_attempt = _l3_current_attempt_from_state(state, task)
    bundle = project_operator_surfaces(
        ready_gate=ready_gate or {},
        l2_facts=l2_facts,
        packet=packet_view,
        publish_feedback_closure=publish_feedback_closure,
    )
    bundle["publish_readiness"] = compute_publish_readiness(
        ready_gate=ready_gate or {},
        l2_facts=l2_facts,
        l3_current_attempt=l3_current_attempt,
        delivery_rows=delivery_rows,
    )
    # Phase B: when the Workbench mounts the Matrix Script line-specific
    # panel, attach the formal `matrix_script_workbench_variation_surface_v1`
    # projection so the panel renders axes / cells / slot detail / attribution
    # refs from authoritative packet truth. The projection is a pure read of
    # `line_specific_refs[].delta` and never mutates packet truth.
    workbench_panel = bundle.get("workbench", {}).get("line_specific_panel", {}) or {}
    if workbench_panel.get("panel_kind") == "matrix_script":
        variation_surface = project_workbench_variation_surface(packet_view)
        bundle["workbench"]["matrix_script_variation_surface"] = variation_surface
        # PR-U2: Matrix Script Workbench operator-comprehension bundle.
        # Pure presentation-layer projection over the variation surface +
        # panel resolver shape. No projection mutation; no contract
        # mutation; no `panel_kind` enum widening; no provider/model/vendor
        # control. Hot Follow / Digital Anchor / Baseline workbench
        # surfaces never enter this branch. Authority:
        # docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md
        from gateway.app.services.matrix_script.workbench_comprehension import (
            derive_matrix_script_workbench_comprehension,
        )
        bundle["workbench"]["matrix_script_comprehension"] = (
            derive_matrix_script_workbench_comprehension(
                variation_surface,
                workbench_panel,
            )
        )
    return bundle


def _matrix_script_delivery_rows(packet_view: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """Best-effort extraction of Matrix Script delivery binding rows.

    Returns ``None`` when the task is not Matrix Script or when the
    projection raises (defense-in-depth: presentation-layer must never
    crash the publish hub). Each row carries ``kind`` /
    ``required`` / ``blocking_publish`` plus
    ``artifact_lookup`` per the Matrix Script delivery binding contract.
    The unified `publish_readiness` producer consumes these rows for
    `required_deliverable_*` head reasons.
    """
    line_id = str(packet_view.get("line_id") or "").strip()
    if line_id != "matrix_script":
        return None
    try:
        from gateway.app.services.matrix_script.delivery_binding import (
            project_delivery_binding,
        )

        binding = project_delivery_binding(packet_view)
    except Exception:
        return None
    rows = binding.get("deliverables") if isinstance(binding, Mapping) else None
    if not isinstance(rows, list):
        return None
    return [row for row in rows if isinstance(row, Mapping)]


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
      - ``publish_readiness`` — full unified producer output (Operator
        Capability Recovery PR-1). Board / Workbench / Delivery all read
        the same shape; the legacy two-field gate above is preserved for
        existing template/HTTP consumers.
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
    l3_current_attempt = _l3_current_attempt_from_state(authoritative_state, task)
    packet_view = _packet_view(task)
    delivery_rows = _matrix_script_delivery_rows(packet_view)
    publish_readiness = compute_publish_readiness(
        ready_gate=ready_gate or {},
        l2_facts=l2_facts,
        l3_current_attempt=l3_current_attempt,
        delivery_rows=delivery_rows,
    )
    publish_status_mirror = derive_delivery_publish_status_mirror(publish_feedback_closure)
    panel = resolve_line_specific_panel(packet_view)
    return {
        # Legacy two-field shape preserved for byte-compatibility with the
        # existing publish-hub template + JSON consumers. Both fields are
        # now derived from the unified producer above.
        "publish_gate": publish_readiness["publishable"],
        "publish_gate_head_reason": publish_readiness["head_reason"],
        "publish_readiness": publish_readiness,
        "publish_status_mirror": publish_status_mirror,
        "line_specific_panel": panel,
    }


__all__ = [
    "build_board_row_projection",
    "build_operator_surfaces_for_workbench",
    "build_operator_surfaces_for_publish_hub",
]
