"""Unified publish_readiness producer (Operator Capability Recovery, PR-1).

Single L4 producer for `publishable` per
`docs/contracts/publish_readiness_contract_v1.md`. Board, Workbench, and
Delivery surfaces consume this producer's output instead of re-deriving
publishability from `ready_gate` + L2 facts independently.

Authority:
- `docs/contracts/publish_readiness_contract_v1.md` (output shape, closed
  `head_reason` enum, single-producer rule)
- `docs/contracts/factory_delivery_contract_v1.md`
  §"Per-Deliverable Required / Blocking Fields (Plan D Amendment)"
  §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)"
- `docs/contracts/hot_follow_current_attempt_contract_v1.md`
  §"`final_provenance` Field (Plan D Amendment)"
- `docs/contracts/l4_advisory_producer_output_contract_v1.md`
  (`blocking_advisories[]` references this taxonomy via the advisory emitter)
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §4

Pure projection. Reads only the declared inputs. No vendor/model/provider
identifier touches input/output. No packet, closure, or worker mutation.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from .advisory_emitter import emit_advisories

# Closed `head_reason` enum (publish_readiness_contract_v1 §"Closed `head_reason` enum").
HEAD_REASON_PUBLISHABLE_OK = "publishable_ok"
HEAD_REASON_READY_GATE_BLOCKING = "ready_gate_blocking"
HEAD_REASON_PUBLISH_NOT_READY = "publish_not_ready"
HEAD_REASON_COMPOSE_NOT_READY = "compose_not_ready"
HEAD_REASON_FINAL_MISSING = "final_missing"
HEAD_REASON_FINAL_STALE = "final_stale"
HEAD_REASON_FINAL_PROVENANCE_HISTORICAL = "final_provenance_historical"
HEAD_REASON_REQUIRED_DELIVERABLE_MISSING = "required_deliverable_missing"
HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING = "required_deliverable_blocking"
HEAD_REASON_UNRESOLVED = "unresolved"

CLOSED_HEAD_REASON_ENUM = frozenset(
    {
        HEAD_REASON_PUBLISHABLE_OK,
        HEAD_REASON_READY_GATE_BLOCKING,
        HEAD_REASON_PUBLISH_NOT_READY,
        HEAD_REASON_COMPOSE_NOT_READY,
        HEAD_REASON_FINAL_MISSING,
        HEAD_REASON_FINAL_STALE,
        HEAD_REASON_FINAL_PROVENANCE_HISTORICAL,
        HEAD_REASON_REQUIRED_DELIVERABLE_MISSING,
        HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING,
        HEAD_REASON_UNRESOLVED,
    }
)

# Per `factory_delivery_contract_v1.md` §"Scene-Pack Non-Blocking Rule" — kind
# values that must never assert blocking publish. Used to defensively clamp
# malformed deliverable rows even if a line policy slipped a non-required row
# through `blocking_publish=true`.
_SCENE_PACK_KIND_PREFIXES = ("scene_pack",)


# `ready_gate.blocking[]` carries free-form line-specific reason strings (see
# `hot_follow_projection_rules_v1.md` §"Blocking-Reason Mapping Contract" —
# names like `voiceover_missing`, `compose_input_blocked`, `subtitle_missing`,
# etc.). Per `publish_readiness_contract_v1.md` §"Output discipline":
#
#     "Every `head_reason` value MUST be reachable from the input shape; the
#      producer MUST NOT invent a reason outside this enum."
#
# We map each known ready-gate reason family into the closed `head_reason`
# enum. Unknown / future reasons degrade safely to `ready_gate_blocking`
# (an enum member declared explicitly for this purpose) rather than escape
# the contract. The original ready-gate string is preserved on
# `consumed_inputs.first_blocking_reason` so the operator surface can render
# operator-readable text; `head_reason` itself stays inside the enum.
_BLOCKING_REASON_TO_HEAD_REASON: dict[str, str] = {
    # compose-not-ready family
    "compose_not_done": "compose_not_ready",
    "compose_not_ready": "compose_not_ready",
    "compose_input_not_ready": "compose_not_ready",
    "compose_input_blocked": "compose_not_ready",
    "compose_input_derive_failed": "compose_not_ready",
    "compose_exec_failed": "compose_not_ready",
    # publish-not-ready family
    "audio_not_ready": "publish_not_ready",
    "audio_not_done": "publish_not_ready",
    "voiceover_missing": "publish_not_ready",
    "missing_voiceover": "publish_not_ready",
    "subtitle_missing": "publish_not_ready",
    "subtitle_not_ready": "publish_not_ready",
    # final-stale family
    "final_stale": "final_stale",
}


def _map_ready_gate_blocking_to_head_reason(reason: str) -> str:
    """Normalize a ready-gate blocking string into the closed head_reason enum.

    Returns `ready_gate_blocking` for any unrecognized value so the producer
    output never contains a string outside `CLOSED_HEAD_REASON_ENUM`.
    """
    norm = str(reason or "").strip().lower()
    if not norm:
        return HEAD_REASON_READY_GATE_BLOCKING
    return _BLOCKING_REASON_TO_HEAD_REASON.get(norm, HEAD_REASON_READY_GATE_BLOCKING)


def _final_fresh(l2_facts: Mapping[str, Any]) -> bool:
    facts = dict(l2_facts or {})
    final = dict(facts.get("final") or {})
    if not bool(final.get("exists")):
        return False
    return not str(facts.get("final_stale_reason") or "").strip()


def _final_exists(l2_facts: Mapping[str, Any]) -> bool:
    final = dict((l2_facts or {}).get("final") or {})
    return bool(final.get("exists"))


def _is_scene_pack_kind(kind: str) -> bool:
    norm = str(kind or "").strip().lower()
    return any(norm.startswith(p) for p in _SCENE_PACK_KIND_PREFIXES)


def _row_status(row: Mapping[str, Any]) -> str:
    """Read a deliverable row's resolved status if exposed.

    Matrix Script delivery binding rows expose ``artifact_lookup.status``
    today. Hot Follow does not surface zoning rows at all (rows=None or
    empty), so this helper is best-effort. A row with no observable status
    is treated as ``unresolved`` for the purpose of required-row gating.
    """
    artifact_lookup = row.get("artifact_lookup") if isinstance(row, Mapping) else None
    if isinstance(artifact_lookup, Mapping):
        status = str(artifact_lookup.get("status") or "").strip().lower()
        if status:
            return status
    direct = str(row.get("status") or "").strip().lower()
    return direct or "unresolved"


_RESOLVED_ROW_STATUSES = frozenset({"resolved", "ready", "done", "ok"})


def _row_resolved(row: Mapping[str, Any]) -> bool:
    return _row_status(row) in _RESOLVED_ROW_STATUSES


def _evaluate_required_rows(
    delivery_rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[bool, str | None]:
    """Inspect deliverable rows for required / blocking_publish gating.

    Returns ``(blocked, head_reason)`` where ``blocked`` is True when any
    row marked ``required=true`` is unresolved or any row marked
    ``blocking_publish=true`` is in a blocking state. Defensive against the
    scene-pack non-blocking rule: a scene-pack row that asserts
    ``blocking_publish=true`` is treated as a contract violation and
    ignored (clamped to non-blocking) rather than allowed to pass through.
    """
    if not delivery_rows:
        return False, None
    for row in delivery_rows:
        if not isinstance(row, Mapping):
            continue
        kind = str(row.get("kind") or "").strip().lower()
        required = bool(row.get("required", False))
        blocking_publish = bool(row.get("blocking_publish", False))
        if _is_scene_pack_kind(kind):
            # Scene-pack family is normatively non-blocking — clamp.
            blocking_publish = False
            required = False
        if required and not _row_resolved(row):
            return True, HEAD_REASON_REQUIRED_DELIVERABLE_MISSING
        if blocking_publish and not _row_resolved(row):
            return True, HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING
    return False, None


def _final_provenance_value(
    l3_current_attempt: Mapping[str, Any] | None,
) -> Optional[str]:
    if not isinstance(l3_current_attempt, Mapping):
        return None
    raw = l3_current_attempt.get("final_provenance")
    if raw not in {"current", "historical"}:
        return None
    return str(raw)


def compute_publish_readiness(
    *,
    ready_gate: Mapping[str, Any] | None,
    l2_facts: Mapping[str, Any] | None,
    l3_current_attempt: Mapping[str, Any] | None = None,
    delivery_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Single L4 producer for `publishable`.

    Inputs:
        ready_gate           — L4 ready gate output (per-line ready gate yaml).
        l2_facts             — L2 artifact facts (`final.exists`, `final_stale_reason`).
        l3_current_attempt   — L3 current attempt (`final_provenance` consumed).
        delivery_rows        — line delivery binding rows; each row carries
                               at minimum `kind`, `required`, `blocking_publish`,
                               and optionally `artifact_lookup.status`. May be
                               None when the line surface has no row-level zoning.

    Output (per `publish_readiness_contract_v1.md` §"Output"):
        {
            "publishable": bool,
            "head_reason": str | None,            # closed enum
            "blocking_advisories": list[Advisory],# from L4 advisory emitter
            "consumed_inputs": {
                "ready_gate_publish_ready": bool,
                "ready_gate_compose_ready": bool,
                "final_fresh": bool,
                "final_provenance": "current" | "historical" | None,
                "blocking_count": int,
            },
        }
    """
    gate = dict(ready_gate or {})
    facts = dict(l2_facts or {})

    publish_ready = bool(gate.get("publish_ready"))
    compose_ready = bool(gate.get("compose_ready"))
    blocking = list(gate.get("blocking") or [])
    # `l2_facts is None` means the caller (typically the Board list surface)
    # is consuming `ready_gate` truth alone and has not hydrated L2 facts.
    # In that mode, defer freshness gating to the ready_gate, since the gate
    # is already L4 and was computed from L2 upstream. When L2 is provided
    # (Workbench, Delivery) the producer enforces freshness directly.
    l2_provided = isinstance(l2_facts, Mapping) and len(facts) > 0
    final_fresh = _final_fresh(facts) if l2_provided else True
    final_exists = _final_exists(facts) if l2_provided else True
    provenance = _final_provenance_value(l3_current_attempt)

    head_reason: Optional[str] = None
    publishable = False

    # Order of head_reason evaluation: ready-gate blocking dominates because the
    # ready gate is the closed source of blocking[]. Final freshness then
    # dominates compose readiness (a stale final means publish cannot proceed
    # even if compose is theoretically ready). Provenance dominates when L3
    # explicitly says "historical". Required-deliverable gating runs last so
    # the most surface-specific reason wins only when the upstream gate is
    # already green.
    first_blocking_reason: Optional[str] = None
    if blocking:
        first = blocking[0] if isinstance(blocking[0], str) else ""
        first_blocking_reason = first or None
        head_reason = _map_ready_gate_blocking_to_head_reason(first)
    elif l2_provided and not final_fresh and not final_exists:
        head_reason = HEAD_REASON_FINAL_MISSING
    elif l2_provided and not final_fresh:
        head_reason = HEAD_REASON_FINAL_STALE
    elif not publish_ready:
        head_reason = HEAD_REASON_PUBLISH_NOT_READY
    elif not compose_ready:
        head_reason = HEAD_REASON_COMPOSE_NOT_READY
    elif provenance == "historical":
        head_reason = HEAD_REASON_FINAL_PROVENANCE_HISTORICAL
    else:
        deliv_blocked, deliv_reason = _evaluate_required_rows(delivery_rows)
        if deliv_blocked:
            head_reason = deliv_reason
        else:
            publishable = True
            head_reason = HEAD_REASON_PUBLISHABLE_OK

    blocking_advisories = emit_advisories(l3_current_attempt or {}, gate)

    return {
        "publishable": publishable,
        # `publishable=true` MAY carry `publishable_ok` or null per contract.
        # We emit `publishable_ok` for explicitness; legacy callers that only
        # render `head_reason` when `publishable=false` ignore it cleanly.
        "head_reason": head_reason,
        "blocking_advisories": list(blocking_advisories),
        "consumed_inputs": {
            "ready_gate_publish_ready": publish_ready,
            "ready_gate_compose_ready": compose_ready,
            "final_fresh": final_fresh,
            "final_provenance": provenance,
            "blocking_count": len(blocking),
            # Original first ready_gate.blocking[] string (or None) — surfaces
            # render this for the operator-visible reason text; `head_reason`
            # above stays inside the closed enum.
            "first_blocking_reason": first_blocking_reason,
        },
    }


__all__ = [
    "CLOSED_HEAD_REASON_ENUM",
    "HEAD_REASON_COMPOSE_NOT_READY",
    "HEAD_REASON_FINAL_MISSING",
    "HEAD_REASON_FINAL_PROVENANCE_HISTORICAL",
    "HEAD_REASON_FINAL_STALE",
    "HEAD_REASON_PUBLISHABLE_OK",
    "HEAD_REASON_PUBLISH_NOT_READY",
    "HEAD_REASON_READY_GATE_BLOCKING",
    "HEAD_REASON_REQUIRED_DELIVERABLE_BLOCKING",
    "HEAD_REASON_REQUIRED_DELIVERABLE_MISSING",
    "HEAD_REASON_UNRESOLVED",
    "compute_publish_readiness",
]
