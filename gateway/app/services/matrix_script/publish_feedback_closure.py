"""Matrix Script publish feedback closure — Phase D.1 minimal write-back.

This module owns the Phase D feedback truth surface
``matrix_script_publish_feedback_closure_v1``. It is intentionally separate
from the Phase C delivery binding projection: the delivery projection in
``delivery_binding.py`` remains a read-only consumer and never mutates
closure state.

The implementation is additive-only:

- no change to Matrix Script packet truth or schema;
- no change to Phase A/B/C contracts;
- no provider / model / vendor / engine controls;
- no Digital Anchor, Hot Follow, W2.2, W2.3 surfaces.

The store is a minimal in-process persistence surface. Events are
append-only; per-variation feedback fields are last-write-wins per the
origin rules in
``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional
from uuid import uuid4

VARIATION_REF_ID = "matrix_script_variation_matrix"
SURFACE_ID = "matrix_script_publish_feedback_closure_v1"

PUBLISH_STATUS_VALUES = frozenset({"pending", "published", "failed", "retracted"})
OPERATOR_STATUS_VALUES = frozenset({"pending", "retracted"})
PLATFORM_STATUS_VALUES = frozenset({"published", "failed"})

EVENT_KINDS = frozenset(
    {
        "operator_publish",
        "operator_retract",
        "operator_note",
        "platform_callback",
        "metrics_snapshot",
    }
)
ACTOR_KINDS = frozenset({"operator", "platform", "system"})

CHANNEL_METRICS_KEYS = frozenset(
    {
        "channel_id",
        "captured_at",
        "impressions",
        "views",
        "engagement_rate",
        "completion_rate",
        "raw_payload_ref",
    }
)
CHANNEL_METRICS_REQUIRED = frozenset({"channel_id", "captured_at"})

# OWC-MS PR-2 / MS-W5 — additive closed-set extension on the
# `operator_note` event payload per OWC-MS gate spec §3 MS-W5
# ("an enum closed-set extension on event payload is the only contract
# touch"). The four zones map 1:1 onto matrix_script_product_flow §6.1D
# (字幕 / 配音 / 文案 / CTA review affordances) and are recorded onto
# the appended `feedback_closure_records[]` entry as an optional field;
# legacy `operator_note` events without `review_zone` remain valid.
REVIEW_ZONE_VALUES = frozenset({"subtitle", "dub", "copy", "cta"})

EVENT_KIND_ACTOR = {
    "operator_publish": "operator",
    "operator_retract": "operator",
    "operator_note": "operator",
    "platform_callback": "platform",
    "metrics_snapshot": "system",
}


class ClosureValidationError(ValueError):
    """Raised when a closure write-back violates the Phase D.0 contract."""


def _packet_cell_ids(packet: Mapping[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == VARIATION_REF_ID:
            cells = (ref.get("delta") or {}).get("cells") or []
            return [cell.get("cell_id") for cell in cells if cell.get("cell_id")]
    return []


def create_closure(
    packet: Mapping[str, Any],
    *,
    closure_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new closure bound to a packet instance.

    Copies ``line_id`` and ``packet_version`` once at creation per the
    contract; these become immutable on the closure. ``variation_feedback``
    rows are pre-seeded one per ``cell_id`` from
    ``line_specific_refs[matrix_script_variation_matrix].delta.cells[]``.
    """
    if packet.get("line_id") != "matrix_script":
        raise ClosureValidationError("closure may only bind to a matrix_script packet")
    cell_ids = _packet_cell_ids(packet)
    if not cell_ids:
        raise ClosureValidationError(
            "packet has no variation cells; cannot create closure"
        )
    return {
        "surface": SURFACE_ID,
        "closure_id": closure_id or f"closure_{uuid4().hex[:12]}",
        "line_id": "matrix_script",
        "packet_version": packet.get("packet_version"),
        "variation_feedback": [
            {
                "variation_id": cell_id,
                "publish_url": None,
                "publish_status": "pending",
                "channel_metrics": [],
                "operator_publish_notes": None,
                "last_event_id": None,
            }
            for cell_id in cell_ids
        ],
        "feedback_closure_records": [],
    }


def _row(closure: MutableMapping[str, Any], variation_id: str) -> MutableMapping[str, Any]:
    for row in closure["variation_feedback"]:
        if row["variation_id"] == variation_id:
            return row
    raise ClosureValidationError(
        f"variation_id {variation_id!r} is not bound to this closure"
    )


def _validate_channel_metrics(payload: Mapping[str, Any]) -> Dict[str, Any]:
    extra = set(payload) - CHANNEL_METRICS_KEYS
    if extra:
        raise ClosureValidationError(
            f"channel_metrics has forbidden keys: {sorted(extra)}"
        )
    missing = CHANNEL_METRICS_REQUIRED - set(payload)
    if missing:
        raise ClosureValidationError(
            f"channel_metrics missing required keys: {sorted(missing)}"
        )
    snapshot = {key: payload[key] for key in payload if key in CHANNEL_METRICS_KEYS}
    for key in ("impressions", "views"):
        if key in snapshot and (not isinstance(snapshot[key], int) or snapshot[key] < 0):
            raise ClosureValidationError(f"{key} must be a non-negative integer")
    for key in ("engagement_rate", "completion_rate"):
        if key in snapshot:
            value = snapshot[key]
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                raise ClosureValidationError(f"{key} must be in [0, 1]")
    return snapshot


def apply_event(
    closure: MutableMapping[str, Any],
    event: Mapping[str, Any],
    *,
    event_id: Optional[str] = None,
) -> str:
    """Apply one closure event in place.

    Mutates ``closure`` per the contract:
      - appends one row to ``feedback_closure_records[]`` (append-only);
      - applies last-write-wins field updates on the matching
        ``variation_feedback`` row;
      - returns the new ``event_id``.

    Origin rules from the Phase D.0 contract are enforced:
      - ``publish_status`` ∈ {pending, retracted} for ``operator_*`` kinds;
      - ``publish_status`` ∈ {published, failed} for ``platform_callback``;
      - ``channel_metrics`` only via ``metrics_snapshot``;
      - ``operator_publish_notes`` only via ``operator_note``.
    """
    event_kind = event.get("event_kind")
    if event_kind not in EVENT_KINDS:
        raise ClosureValidationError(f"unknown event_kind: {event_kind!r}")
    actor_kind = event.get("actor_kind") or EVENT_KIND_ACTOR[event_kind]
    if actor_kind not in ACTOR_KINDS:
        raise ClosureValidationError(f"unknown actor_kind: {actor_kind!r}")
    if actor_kind != EVENT_KIND_ACTOR[event_kind]:
        raise ClosureValidationError(
            f"event_kind {event_kind!r} requires actor_kind "
            f"{EVENT_KIND_ACTOR[event_kind]!r}"
        )
    variation_id = event.get("variation_id")
    if not isinstance(variation_id, str) or not variation_id:
        raise ClosureValidationError("event.variation_id is required")

    row = _row(closure, variation_id)
    payload = event.get("payload") or {}
    new_event_id = event_id or f"evt_{uuid4().hex[:12]}"

    if event_kind == "operator_publish":
        url = payload.get("publish_url")
        if url is not None and not isinstance(url, str):
            raise ClosureValidationError("publish_url must be a string")
        status = payload.get("publish_status", "pending")
        if status not in OPERATOR_STATUS_VALUES:
            raise ClosureValidationError(
                "operator_publish may only set publish_status in "
                f"{sorted(OPERATOR_STATUS_VALUES)}"
            )
        if url is not None:
            row["publish_url"] = url
        row["publish_status"] = status
    elif event_kind == "operator_retract":
        row["publish_status"] = "retracted"
    elif event_kind == "operator_note":
        note = payload.get("operator_publish_notes")
        if not isinstance(note, str):
            raise ClosureValidationError("operator_publish_notes must be a string")
        row["operator_publish_notes"] = note
        # OWC-MS PR-2 / MS-W5 — optional `review_zone` tag (closed enum).
        # Validated in-place; recorded on the appended record below.
        if "review_zone" in payload and payload.get("review_zone") not in REVIEW_ZONE_VALUES:
            raise ClosureValidationError(
                "operator_note.review_zone must be in "
                f"{sorted(REVIEW_ZONE_VALUES)}"
            )
    elif event_kind == "platform_callback":
        status = payload.get("publish_status")
        if status not in PLATFORM_STATUS_VALUES:
            raise ClosureValidationError(
                "platform_callback must set publish_status in "
                f"{sorted(PLATFORM_STATUS_VALUES)}"
            )
        url = payload.get("publish_url")
        if url is not None:
            if not isinstance(url, str):
                raise ClosureValidationError("publish_url must be a string")
            row["publish_url"] = url
        row["publish_status"] = status
    elif event_kind == "metrics_snapshot":
        snapshot = _validate_channel_metrics(payload)
        row["channel_metrics"].append(snapshot)

    row["last_event_id"] = new_event_id
    record: Dict[str, Any] = {
        "event_id": new_event_id,
        "variation_id": variation_id,
        "event_kind": event_kind,
        "recorded_at": event.get("recorded_at"),
        "actor_kind": actor_kind,
        "payload_ref": event.get("payload_ref"),
    }
    # OWC-MS PR-2 / MS-W5 — optional `review_zone` tag flows through onto
    # the appended record only. The variation_feedback row shape is
    # unchanged; the closure-wide shape is unchanged.
    if event_kind == "operator_note" and payload.get("review_zone") in REVIEW_ZONE_VALUES:
        record["review_zone"] = payload["review_zone"]
    closure["feedback_closure_records"].append(record)
    return new_event_id


def project_closure_view(closure: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a deep-copy read-only view of the closure for display.

    The Phase C delivery projection consumes this surface as a read-only
    feedback view; it must not be allowed to write back.
    """
    return deepcopy(dict(closure))


class InMemoryClosureStore:
    """Minimal additive-only persistence surface for closures.

    Provides ``create``, ``get``, ``apply``, and ``snapshot`` operations.
    Backed by an in-process dict; intentionally not a database. A future
    persistence wave can swap this for a durable backend without
    redesigning the closure shape.
    """

    def __init__(self) -> None:
        self._closures: Dict[str, Dict[str, Any]] = {}

    def create(
        self,
        packet: Mapping[str, Any],
        *,
        closure_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        closure = create_closure(packet, closure_id=closure_id)
        if closure["closure_id"] in self._closures:
            raise ClosureValidationError(
                f"closure_id {closure['closure_id']!r} already exists"
            )
        self._closures[closure["closure_id"]] = closure
        return project_closure_view(closure)

    def get(self, closure_id: str) -> Dict[str, Any]:
        if closure_id not in self._closures:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        return project_closure_view(self._closures[closure_id])

    def apply(self, closure_id: str, event: Mapping[str, Any]) -> Dict[str, Any]:
        if closure_id not in self._closures:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        closure = self._closures[closure_id]
        event_id = apply_event(closure, event)
        return {"event_id": event_id, "closure": project_closure_view(closure)}

    def list_variation_ids(self, closure_id: str) -> list[str]:
        closure = self._closures.get(closure_id)
        if closure is None:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        return [row["variation_id"] for row in closure["variation_feedback"]]


__all__ = [
    "ACTOR_KINDS",
    "CHANNEL_METRICS_KEYS",
    "ClosureValidationError",
    "EVENT_KINDS",
    "InMemoryClosureStore",
    "PUBLISH_STATUS_VALUES",
    "REVIEW_ZONE_VALUES",
    "SURFACE_ID",
    "VARIATION_REF_ID",
    "apply_event",
    "create_closure",
    "project_closure_view",
]
