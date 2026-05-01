"""Additive projections for the four operator-visible surfaces.

Phase 3A minimal wiring. All functions are pure: they read existing
projection truth and produce derived view payloads. They never write
back to L2/L3, never mutate packet truth, and never carry vendor /
model / provider / engine identifiers.

Sources of truth honored:
- ready_gate (`gateway/app/services/contract_runtime/ready_gate_runtime.py`)
- L2 artifact facts (`gateway/app/services/status_policy/hot_follow_state.py`,
  `docs/contracts/four_layer_state_contract.md`)
- task-side publish-feedback closure
  (`gateway/app/services/matrix_script/publish_feedback_closure.py`,
   `gateway/app/services/digital_anchor/publish_feedback_closure.py`)
- packet `line_specific_refs[]`
  (`schemas/packets/<line>/packet.schema.json`)
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

# ---------- Forbidden operator-visible payload keys (validator R3) ----------

FORBIDDEN_OPERATOR_KEYS = frozenset(
    {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
    }
)


def sanitize_operator_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Strip forbidden vendor/provider/engine keys before operator render.

    This is a defense-in-depth check. The packet validator already enforces
    the same forbidden set at envelope time
    (`gateway/app/services/packet/validator.py:202`); this function applies
    the same rule once more at the surface boundary so a leak in any
    upstream projection cannot reach the operator.
    """
    return {k: v for k, v in dict(payload).items() if k not in FORBIDDEN_OPERATOR_KEYS}


# ---------- Gap A1: Board per-packet `publishable` boolean ----------


def derive_board_publishable(ready_gate: Mapping[str, Any]) -> dict[str, Any]:
    """Project the Board card `publishable` field plus head reason.

    Derived only from `ready_gate.*`. No new truth, no new field on the
    packet. If `ready_gate` is missing or empty, returns `publishable=False`
    with `head_reason=None` so the Board's `publishable` bucket renders
    empty per the design's deferral path.
    """
    gate = dict(ready_gate or {})
    blocking = list(gate.get("blocking") or [])
    publishable = (
        bool(gate.get("publish_ready"))
        and bool(gate.get("compose_ready"))
        and not blocking
    )
    head_reason: Optional[str] = None
    if not publishable:
        if blocking:
            head_reason = blocking[0]
        else:
            for key in ("compose_reason", "compose_blocked_reason"):
                value = gate.get(key)
                if isinstance(value, str) and value.strip():
                    head_reason = value
                    break
    return {
        "publishable": publishable,
        "head_reason": head_reason,
    }


# ---------- Gap A2: Single derived Delivery publish gate ----------


def _final_fresh(l2_facts: Mapping[str, Any]) -> bool:
    facts = dict(l2_facts or {})
    final = dict(facts.get("final") or {})
    if not bool(final.get("exists")):
        return False
    if str(facts.get("final_stale_reason") or "").strip():
        return False
    return True


def derive_delivery_publish_gate(
    ready_gate: Mapping[str, Any],
    l2_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Project a single Delivery publish-gate boolean.

    Inputs: existing L4 `ready_gate` + existing L2 artifact facts. Optional
    items (`scene_pack`, `pack_zip`, `edit_bundle_zip`, helper / attribution
    exports) are excluded from the AND inputs by construction — they are
    enumerated separately on the Delivery contract via the per-deliverable
    `required: bool` flag, never reaching this gate.
    """
    gate = dict(ready_gate or {})
    publish_ready = bool(gate.get("publish_ready"))
    compose_ready = bool(gate.get("compose_ready"))
    final_fresh = _final_fresh(l2_facts)
    blocking = list(gate.get("blocking") or [])
    publish_gate = publish_ready and compose_ready and final_fresh and not blocking
    head_reason: Optional[str] = None
    if not publish_gate:
        if blocking:
            head_reason = blocking[0]
        elif not final_fresh:
            head_reason = (
                str((l2_facts or {}).get("final_stale_reason") or "").strip()
                or "final_missing"
            )
        else:
            compose_reason = gate.get("compose_reason")
            if isinstance(compose_reason, str) and compose_reason.strip():
                head_reason = compose_reason
            else:
                head_reason = "publish_not_ready"
    return {
        "publish_gate": publish_gate,
        "publish_gate_head_reason": head_reason,
    }


# ---------- Gap A3: Delivery last-publish-status mirror ----------

# Per `docs/contracts/status_ownership_matrix.md:39`, publish-status truth lives
# on the task / closure, never on the packet envelope. This helper reads the
# closure shape produced by the existing per-line publish_feedback_closure
# modules. It returns a flat read-only mirror; it never writes.

_KNOWN_PUBLISH_STATUSES = frozenset(
    {"pending", "published", "failed", "retracted", "not_published"}
)


def _last_record_at(closure: Mapping[str, Any]) -> Optional[str]:
    records = list(closure.get("feedback_closure_records") or [])
    last_at: Optional[str] = None
    for record in records:
        recorded_at = record.get("recorded_at")
        if isinstance(recorded_at, str) and recorded_at:
            if last_at is None or recorded_at > last_at:
                last_at = recorded_at
    return last_at


def _matrix_script_aggregate_status(closure: Mapping[str, Any]) -> str:
    rows = list(closure.get("variation_feedback") or [])
    if not rows:
        return "not_published"
    statuses = {str(row.get("publish_status") or "pending") for row in rows}
    if statuses == {"published"}:
        return "published"
    if "failed" in statuses:
        return "failed"
    if "retracted" in statuses and statuses <= {"retracted"}:
        return "retracted"
    if "pending" in statuses:
        return "pending"
    return "pending"


def derive_delivery_publish_status_mirror(
    closure: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    """Read-only mirror of task-side publish-feedback closure for Delivery.

    Returns a flat shape:
        last_published_at: str | None
        publish_status: str
        publish_url: str | None
        publish_channel: str | None

    `publish_channel` is taken from `channel_metrics.channel_id` when the
    closure exposes it (Digital Anchor / Matrix Script Phase D.1 shape).
    Returns the empty mirror when no closure exists.
    """
    empty = {
        "last_published_at": None,
        "publish_status": "not_published",
        "publish_url": None,
        "publish_channel": None,
    }
    if not closure:
        return empty
    closure_map = dict(closure)
    line_id = str(closure_map.get("line_id") or "").strip()

    if line_id == "matrix_script":
        publish_status = _matrix_script_aggregate_status(closure_map)
        rows = list(closure_map.get("variation_feedback") or [])
        publish_url = next(
            (row.get("publish_url") for row in rows if row.get("publish_url")),
            None,
        )
        # Channel mirrored only when uniform across rows; else None.
        channels = {
            (cm.get("channel_id") if isinstance(cm, Mapping) else None)
            for row in rows
            for cm in (row.get("channel_metrics") or [])
        }
        channels.discard(None)
        publish_channel = next(iter(channels)) if len(channels) == 1 else None
    else:
        publish_status = str(closure_map.get("publish_status") or "not_published")
        publish_url = closure_map.get("publish_url")
        channel_metrics = closure_map.get("channel_metrics") or {}
        publish_channel = (
            channel_metrics.get("channel_id")
            if isinstance(channel_metrics, Mapping)
            else None
        )

    if publish_status not in _KNOWN_PUBLISH_STATUSES:
        publish_status = "pending"

    return {
        "last_published_at": _last_record_at(closure_map),
        "publish_status": publish_status,
        "publish_url": publish_url,
        "publish_channel": publish_channel,
    }


# ---------- Workbench `line_specific_refs[]` mount resolver ----------

# Frozen ref_id → panel_kind dispatch (per architect review §"Engineering
# Wiring Confirmation Items" item 3 and the three line panel docs).
PANEL_REF_DISPATCH: dict[str, str] = {
    "matrix_script_variation_matrix": "matrix_script",
    "matrix_script_slot_pack": "matrix_script",
    "digital_anchor_role_pack": "digital_anchor",
    "digital_anchor_speaker_plan": "digital_anchor",
    "hot_follow_subtitle_authority": "hot_follow",
    "hot_follow_dub_compose_legality": "hot_follow",
}


def resolve_line_specific_panel(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve which Workbench line-specific panel to mount.

    Returns:
        {
            "panel_kind": "matrix_script" | "digital_anchor" | "hot_follow" | None,
            "refs": [{"ref_id": str, "ref_payload": Mapping}, ...]
        }

    Dispatch is purely on `line_specific_refs[].ref_id` — Workbench has no
    other authority to mount a line panel. If no known ref_id is present
    the slot stays empty (panel_kind=None), per the rule that Workbench
    must not invent UI truth.
    """
    refs_in = list((packet or {}).get("line_specific_refs") or [])
    matched: list[dict[str, Any]] = []
    panel_kinds: list[str] = []
    for ref in refs_in:
        ref_id = ref.get("ref_id") if isinstance(ref, Mapping) else None
        if not ref_id or ref_id not in PANEL_REF_DISPATCH:
            continue
        panel_kinds.append(PANEL_REF_DISPATCH[ref_id])
        matched.append(
            {
                "ref_id": ref_id,
                "ref_payload": sanitize_operator_payload(ref),
            }
        )
    panel_kind = panel_kinds[0] if panel_kinds else None
    if panel_kind is not None and any(k != panel_kind for k in panel_kinds):
        # Mixed-line refs is a packet-validator concern; surface chooses
        # the first match and leaves the rest visible in `refs` for diagnosis.
        pass
    return {
        "panel_kind": panel_kind,
        "refs": matched,
    }


# ---------- Convenience: shape the four surface projections together ----------


def project_operator_surfaces(
    *,
    ready_gate: Mapping[str, Any],
    l2_facts: Mapping[str, Any],
    packet: Mapping[str, Any],
    publish_feedback_closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Single entry point that returns all four operator-visible surface payloads.

    Each surface field is itself a derived projection over inputs already
    owned elsewhere; this function only assembles them.
    """
    board = derive_board_publishable(ready_gate)
    delivery_gate = derive_delivery_publish_gate(ready_gate, l2_facts)
    delivery_mirror = derive_delivery_publish_status_mirror(publish_feedback_closure)
    workbench_mount = resolve_line_specific_panel(packet)
    return {
        "board": board,
        "workbench": {"line_specific_panel": workbench_mount},
        "delivery": {
            **delivery_gate,
            "publish_status_mirror": delivery_mirror,
        },
        "hot_follow_panel": {
            # Hot Follow panel mounts via the same Workbench resolver; this
            # field is `True` only if a hot_follow ref was present.
            "mounted": workbench_mount["panel_kind"] == "hot_follow",
            "refs": [
                ref
                for ref in workbench_mount["refs"]
                if PANEL_REF_DISPATCH.get(ref["ref_id"]) == "hot_follow"
            ],
        },
    }


__all__ = [
    "FORBIDDEN_OPERATOR_KEYS",
    "PANEL_REF_DISPATCH",
    "derive_board_publishable",
    "derive_delivery_publish_gate",
    "derive_delivery_publish_status_mirror",
    "project_operator_surfaces",
    "resolve_line_specific_panel",
    "sanitize_operator_payload",
]


# Silence unused-import warning for Iterable in some linters.
_ = Iterable
