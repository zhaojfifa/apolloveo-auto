"""Promote intent service (Operator Capability Recovery, PR-2).

Minimum operator capability for the promote-intent flow per
`docs/contracts/promote_request_contract_v1.md` (request submit) and
`docs/contracts/promote_feedback_closure_contract_v1.md` (append-only
audit + closure). No DB; in-process store. PR-2 ships only the minimum
needed for an operator to:

    1. submit an intent against a real artifact ref;
    2. observe the request closure mirror (state + records);
    3. withdraw their own request before terminal state.

Reviewer-side approve/reject is exposed as a service-level API for
testing and for whatever admin-side surface lands later under Plan E
or Platform Runtime Assembly Wave; PR-2 does NOT ship an admin review
UI per Recovery red lines.

All inputs are validated against the closed enums declared in the
sibling contracts. Vendor / model / provider / engine identifiers are
forbidden everywhere (validator R3); truth-shape state fields are
forbidden everywhere except the scoped `request_state` enum on the
closure (validator R5).
"""
from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from .seed_data import (
    ASSET_KIND_ENUM,
    ASSET_FACET_ENUM,
    LICENSE_ENUM,
    LINE_AVAILABILITY_ENUM,
    ORIGIN_KIND_ENUM,
    REUSE_POLICY_ENUM,
)

# Per `promote_feedback_closure_contract_v1.md` §"Closed `request_state` enum".
REQUEST_STATE_ENUM: frozenset[str] = frozenset({"requested", "approved", "rejected"})

# Per the same contract §"Closed `rejection_reason` enum".
REJECTION_REASON_ENUM: frozenset[str] = frozenset(
    {
        "license_not_eligible",
        "reuse_policy_conflict",
        "duplicate_of_existing_asset",
        "quality_below_threshold",
        "metadata_incomplete",
        "source_artifact_unresolvable",
        "policy_violation",
        "reviewer_discretion",
    }
)

# Per the same contract §"Closed `event_kind` enum".
EVENT_KIND_ENUM: frozenset[str] = frozenset(
    {"submitted", "review_started", "approved", "rejected", "withdrawn", "system_note"}
)

ACTOR_KIND_ENUM: frozenset[str] = frozenset({"operator", "reviewer", "system"})

# Validator R3 cross-surface.
FORBIDDEN_PROMOTE_KEYS: frozenset[str] = frozenset(
    {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
        "avatar_engine_id",
        "tts_provider_id",
        "lip_sync_engine_id",
    }
)

# Validator R5 cross-surface (no truth-shape state field on the request).
FORBIDDEN_REQUEST_STATE_FIELDS: frozenset[str] = frozenset(
    {
        "status",
        "ready",
        "done",
        "phase",
        "current_attempt",
        "delivery_ready",
        "final_ready",
        "publishable",
    }
)


class PromoteRequestRejected(ValueError):
    """Raised when a promote request fails closed-schema validation.

    Carries an `error_code` member so the router and tests can assert
    the precise reason without parsing free text.
    """

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


def _utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _walk_for_forbidden(payload: Any, *, path: str = "") -> Optional[str]:
    """Recursively walk for forbidden vendor/model keys or state fields."""
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if key in FORBIDDEN_PROMOTE_KEYS:
                return f"forbidden_vendor_or_model_key:{path or '<root>'}.{key}"
            if key in FORBIDDEN_REQUEST_STATE_FIELDS:
                return f"forbidden_state_field:{path or '<root>'}.{key}"
            sub = _walk_for_forbidden(value, path=f"{path}.{key}" if path else key)
            if sub:
                return sub
    elif isinstance(payload, list):
        for idx, item in enumerate(payload):
            sub = _walk_for_forbidden(item, path=f"{path}[{idx}]")
            if sub:
                return sub
    return None


def _validate_closed_enum(field: str, value: Any, enum: frozenset[str]) -> None:
    if value not in enum:
        raise PromoteRequestRejected(
            error_code=f"closed_enum_violation:{field}",
            message=f"{field}={value!r} is not a member of the closed enum.",
        )


def _validate_tags(tags: Any) -> list[dict[str, str]]:
    if not isinstance(tags, list):
        raise PromoteRequestRejected(
            error_code="target_tags_shape",
            message="target_tags MUST be a list of {facet, value} pairs.",
        )
    out: list[dict[str, str]] = []
    for idx, tag in enumerate(tags):
        if not isinstance(tag, Mapping) or "facet" not in tag or "value" not in tag:
            raise PromoteRequestRejected(
                error_code=f"target_tags_shape[{idx}]",
                message="Every target_tags entry MUST be {facet, value}.",
            )
        facet = str(tag["facet"])
        value = str(tag["value"])
        if facet not in ASSET_FACET_ENUM:
            raise PromoteRequestRejected(
                error_code=f"target_tags_facet[{idx}]",
                message=f"facet {facet!r} is not in the closed facet enum.",
            )
        out.append({"facet": facet, "value": value})
    return out


def _validate_line_availability(values: Any) -> list[str]:
    if not isinstance(values, list):
        raise PromoteRequestRejected(
            error_code="target_line_availability_shape",
            message="target_line_availability MUST be a list of line ids.",
        )
    seen: list[str] = []
    for line in values:
        line_str = str(line)
        if line_str not in LINE_AVAILABILITY_ENUM:
            raise PromoteRequestRejected(
                error_code="target_line_availability_value",
                message=f"line {line_str!r} is not in the closed line enum.",
            )
        if line_str not in seen:
            seen.append(line_str)
    return seen


def _validate_request_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate against `promote_request_contract_v1.md` §"Closed request schema".

    Returns a sanitized deep-copied request dict on success; raises
    `PromoteRequestRejected` on any closed-schema violation.
    """
    if not isinstance(payload, Mapping):
        raise PromoteRequestRejected(
            error_code="payload_shape",
            message="promote request payload MUST be a mapping.",
        )

    # Reject vendor/model/provider/engine + truth-shape state field leaks
    # before any other field-level validation.
    leak = _walk_for_forbidden(payload)
    if leak:
        raise PromoteRequestRejected(
            error_code="forbidden_field",
            message=leak,
        )

    artifact_ref = payload.get("artifact_ref")
    if not isinstance(artifact_ref, str) or not artifact_ref.strip():
        raise PromoteRequestRejected(
            error_code="artifact_ref_required",
            message="artifact_ref is required and MUST be a non-empty opaque handle.",
        )

    target_kind = payload.get("target_kind")
    _validate_closed_enum("target_kind", target_kind, ASSET_KIND_ENUM)

    target_tags = _validate_tags(payload.get("target_tags"))
    target_line_availability = _validate_line_availability(
        payload.get("target_line_availability")
    )

    license_metadata = payload.get("license_metadata")
    if not isinstance(license_metadata, Mapping):
        raise PromoteRequestRejected(
            error_code="license_metadata_shape",
            message="license_metadata MUST be a mapping.",
        )
    _validate_closed_enum("license_metadata.license", license_metadata.get("license"), LICENSE_ENUM)
    _validate_closed_enum(
        "license_metadata.reuse_policy", license_metadata.get("reuse_policy"), REUSE_POLICY_ENUM
    )
    _validate_closed_enum(
        "license_metadata.source", license_metadata.get("source"), ORIGIN_KIND_ENUM
    )
    # PR-2 reviewer-fix #1: per `promote_request_contract_v1.md`
    # §"Submit-time discipline" item 5 + §"Closed request schema" notes —
    # `license_metadata.source` MUST be `task_artifact_promote` for
    # promote-from-artifact requests. The original PR-2 implementation
    # accepted any ORIGIN_KIND_ENUM value here, which silently allowed
    # `external_reference` / `licensed_stock` / `admin_seeded` to substitute
    # for task-artifact promote semantics. Submit only takes an
    # `artifact_ref` so the request is by construction artifact-backed;
    # any other source is a contract violation.
    if license_metadata.get("source") != "task_artifact_promote":
        raise PromoteRequestRejected(
            error_code="license_metadata.source_must_be_task_artifact_promote",
            message=(
                "Submit accepts only artifact-backed promote intents; "
                "license_metadata.source MUST be 'task_artifact_promote' "
                "(per promote_request_contract_v1 §'Closed request schema')."
            ),
        )
    source_label = license_metadata.get("source_label")
    if source_label is not None and not isinstance(source_label, str):
        raise PromoteRequestRejected(
            error_code="license_metadata.source_label_shape",
            message="license_metadata.source_label MUST be a string when present.",
        )

    proposed_title = payload.get("proposed_title")
    if not isinstance(proposed_title, str) or not proposed_title.strip():
        raise PromoteRequestRejected(
            error_code="proposed_title_required",
            message="proposed_title is required and MUST be a non-empty string.",
        )

    requested_by = payload.get("requested_by")
    if not isinstance(requested_by, str) or not requested_by.strip():
        raise PromoteRequestRejected(
            error_code="requested_by_required",
            message="requested_by is required and MUST be a non-empty actor ref.",
        )

    operator_notes = payload.get("operator_notes")
    if operator_notes is not None and not isinstance(operator_notes, str):
        raise PromoteRequestRejected(
            error_code="operator_notes_shape",
            message="operator_notes MUST be a string when present.",
        )

    provenance = payload.get("provenance") or {}
    content_hash = provenance.get("content_hash") if isinstance(provenance, Mapping) else None
    if content_hash is not None and not isinstance(content_hash, str):
        raise PromoteRequestRejected(
            error_code="provenance.content_hash_shape",
            message="provenance.content_hash MUST be a string when present.",
        )

    sanitized: dict[str, Any] = {
        "artifact_ref": artifact_ref.strip(),
        "target_kind": target_kind,
        "target_tags": target_tags,
        "target_line_availability": target_line_availability,
        "license_metadata": {
            "license": license_metadata.get("license"),
            "reuse_policy": license_metadata.get("reuse_policy"),
            "source": license_metadata.get("source"),
            "source_label": source_label,
        },
        "proposed_title": proposed_title.strip(),
        "provenance": {"content_hash": content_hash},
        "requested_by": requested_by.strip(),
        "operator_notes": operator_notes,
    }
    return sanitized


# ---- In-process store (PR-2 minimum; durable persistence is out of scope) -----

_LOCK = threading.RLock()
_REQUESTS: dict[str, dict[str, Any]] = {}
_CLOSURES: dict[str, dict[str, Any]] = {}


def reset_store_for_tests() -> None:
    """Clear the in-process store. Test-only helper."""
    with _LOCK:
        _REQUESTS.clear()
        _CLOSURES.clear()


def _new_request_id() -> str:
    return f"prom-req-{uuid.uuid4().hex[:16]}"


def _new_closure_id(request_id: str) -> str:
    # Per the closure contract: `closure_id` is 1:1 with `request_id`.
    return f"prom-clo-{request_id[len('prom-req-'):]}"


def _new_event_id(closure_id: str, sequence: int) -> str:
    return f"{closure_id}-event-{sequence:04d}"


def _append_event(
    closure: dict[str, Any],
    *,
    event_kind: str,
    actor_kind: str,
    actor_ref: str,
    payload_ref: Optional[str] = None,
) -> None:
    if event_kind not in EVENT_KIND_ENUM:
        raise ValueError(f"event_kind {event_kind!r} not in closed enum")
    if actor_kind not in ACTOR_KIND_ENUM:
        raise ValueError(f"actor_kind {actor_kind!r} not in closed enum")
    records = closure.setdefault("closure_records", [])
    records.append(
        {
            "event_id": _new_event_id(closure["closure_id"], len(records) + 1),
            "event_kind": event_kind,
            "recorded_at": _utcnow_iso(),
            "actor_kind": actor_kind,
            "actor_ref": actor_ref,
            "payload_ref": payload_ref,
        }
    )


def submit_promote_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Submit a promote intent.

    Returns ``{"request_id": str, "request_state": "requested"}`` per the
    contract — the asset_id is decided asynchronously and is never
    returned synchronously. Raises `PromoteRequestRejected` on any
    closed-schema violation.
    """
    sanitized = _validate_request_payload(payload)

    with _LOCK:
        request_id = _new_request_id()
        timestamp = _utcnow_iso()
        request: dict[str, Any] = {
            "request_id": request_id,
            **sanitized,
            "request_timestamp_utc": timestamp,
        }
        # `license_metadata.source` MUST be `task_artifact_promote` per
        # the request contract §"Submit-time discipline" item 5 paraphrase.
        # We accept other origin_kinds so admin-seeded promotes can be
        # exercised in tests; the contract only mandates
        # `task_artifact_promote` for promote-from-artifact requests, and
        # this PR-2 minimum supports that variant plus admin-seeded.
        _REQUESTS[request_id] = copy.deepcopy(request)

        closure_id = _new_closure_id(request_id)
        closure: dict[str, Any] = {
            "closure_id": closure_id,
            "request_id": request_id,
            "artifact_ref": sanitized["artifact_ref"],
            "request_state": "requested",
            "resulting_asset_id": None,
            "rejection_reason": None,
            "reviewer_ref": None,
            "reviewer_notes": None,
            "request_timestamp_utc": timestamp,
            "resolved_timestamp_utc": None,
            "closure_records": [],
        }
        _append_event(
            closure,
            event_kind="submitted",
            actor_kind="operator",
            actor_ref=sanitized["requested_by"],
        )
        _CLOSURES[request_id] = closure

    return {"request_id": request_id, "request_state": "requested"}


def get_request(request_id: str) -> Optional[dict[str, Any]]:
    """Return the sanitized request payload (deep copy) or `None`."""
    with _LOCK:
        request = _REQUESTS.get(request_id)
        return copy.deepcopy(request) if request else None


def get_closure(request_id: str) -> Optional[dict[str, Any]]:
    """Return the closure mirror (deep copy) or `None`.

    The returned closure conforms to
    `promote_feedback_closure_contract_v1.md` §"Closure object shape".
    The caller MUST treat `closure_records[]` as append-only per the
    contract; this helper returns a deep copy so caller mutations
    cannot corrupt the store.
    """
    with _LOCK:
        closure = _CLOSURES.get(request_id)
        return copy.deepcopy(closure) if closure else None


def list_closures(*, requested_by: Optional[str] = None) -> list[dict[str, Any]]:
    """List closures, optionally filtered by requesting operator."""
    with _LOCK:
        out: list[dict[str, Any]] = []
        for request_id, closure in _CLOSURES.items():
            if requested_by is not None:
                request = _REQUESTS.get(request_id) or {}
                if str(request.get("requested_by") or "") != requested_by:
                    continue
            out.append(copy.deepcopy(closure))
        out.sort(key=lambda c: c.get("request_timestamp_utc") or "")
        return out


def withdraw_request(request_id: str, *, actor_ref: str) -> dict[str, Any]:
    """Operator-initiated withdrawal before terminal state.

    Per the closure contract §"Closed `event_kind` enum": `withdrawn`
    transitions `request_state` to `rejected` with `rejection_reason=null`
    and `reviewer_ref=null` (operator-side withdrawal, not reviewer
    rejection). Idempotent re-withdraw on a terminal closure raises.
    """
    with _LOCK:
        closure = _CLOSURES.get(request_id)
        if closure is None:
            raise PromoteRequestRejected(
                error_code="closure_not_found", message=f"unknown request_id {request_id!r}"
            )
        if closure["request_state"] != "requested":
            raise PromoteRequestRejected(
                error_code="closure_terminal",
                message=f"closure for {request_id!r} is already terminal "
                f"({closure['request_state']!r}); withdrawal not permitted.",
            )
        _append_event(
            closure,
            event_kind="withdrawn",
            actor_kind="operator",
            actor_ref=actor_ref,
        )
        closure["request_state"] = "rejected"
        closure["rejection_reason"] = None
        closure["reviewer_ref"] = None
        closure["resolved_timestamp_utc"] = _utcnow_iso()
        return copy.deepcopy(closure)


class AssetLibraryWriteUnavailable(PromoteRequestRejected):
    """Raised when approval is requested but no Asset Library write path
    exists to materialize the resulting asset object.

    PR-2 reviewer-fix #2: per `promote_feedback_closure_contract_v1.md`
    §"Source-of-truth rules" item 2, the closure may reference
    `resulting_asset_id` ONLY after the asset object exists in the
    Asset Library truth path. PR-2 ships no asset-library write path
    (deferred to Platform Runtime Assembly Wave or a later Recovery
    iteration); therefore approval cannot be honored here without
    inventing asset truth that does not exist. The narrow contract-safe
    correction is to refuse approval at the service surface entirely
    until a real asset-library write path lands.
    """

    def __init__(self) -> None:
        super().__init__(
            error_code="asset_library_write_unavailable",
            message=(
                "Promote approval is not available in PR-2: closure cannot "
                "reference `resulting_asset_id` because the Asset Library "
                "write path is not yet implemented. The closure remains in "
                "`requested` state until withdrawn (operator) or rejected "
                "(reviewer)."
            ),
        )


def approve_request(
    request_id: str,
    *,
    reviewer_ref: str = "",
    resulting_asset_id: str = "",
    reviewer_notes: Optional[str] = None,
) -> dict[str, Any]:
    """Reviewer-side approve — DISABLED in PR-2.

    PR-2 reviewer-fix #2: the original PR-2 implementation accepted a
    caller-provided `resulting_asset_id` and wrote it to the closure
    without verifying that an Asset Library object existed at that id.
    This violated `promote_feedback_closure_contract_v1.md`
    §"Source-of-truth rules" item 2 ("the resulting asset object is
    created in the Asset Library; the closure references it by
    `resulting_asset_id`") because PR-2 ships no asset-library write
    path — so no asset object could possibly exist at the supplied id.

    Narrow correction: refuse approval at the service surface. The
    closure contract's `requested` and `rejected` (including operator
    `withdrawn` → `rejected` transition) terminal semantics remain
    fully honored. Approval is deferred until a real asset-library
    write path lands in a later wave.
    """
    raise AssetLibraryWriteUnavailable()


def reject_request(
    request_id: str,
    *,
    reviewer_ref: str,
    rejection_reason: str,
    reviewer_notes: Optional[str] = None,
) -> dict[str, Any]:
    """Reviewer-side reject. Service API only — PR-2 ships no admin UI.

    `rejection_reason` MUST be a member of the closed enum.
    """
    if rejection_reason not in REJECTION_REASON_ENUM:
        raise PromoteRequestRejected(
            error_code="rejection_reason_closed_enum",
            message=f"rejection_reason {rejection_reason!r} is not in the closed enum.",
        )
    with _LOCK:
        closure = _CLOSURES.get(request_id)
        if closure is None:
            raise PromoteRequestRejected(
                error_code="closure_not_found", message=f"unknown request_id {request_id!r}"
            )
        if closure["request_state"] != "requested":
            raise PromoteRequestRejected(
                error_code="closure_terminal",
                message=f"closure for {request_id!r} is already terminal.",
            )
        _append_event(
            closure,
            event_kind="review_started",
            actor_kind="reviewer",
            actor_ref=reviewer_ref,
        )
        _append_event(
            closure,
            event_kind="rejected",
            actor_kind="reviewer",
            actor_ref=reviewer_ref,
            payload_ref=rejection_reason,
        )
        closure["request_state"] = "rejected"
        closure["rejection_reason"] = rejection_reason
        closure["reviewer_ref"] = reviewer_ref
        closure["reviewer_notes"] = reviewer_notes
        closure["resolved_timestamp_utc"] = _utcnow_iso()
        return copy.deepcopy(closure)


__all__ = [
    "ACTOR_KIND_ENUM",
    "EVENT_KIND_ENUM",
    "FORBIDDEN_PROMOTE_KEYS",
    "FORBIDDEN_REQUEST_STATE_FIELDS",
    "AssetLibraryWriteUnavailable",
    "PromoteRequestRejected",
    "REJECTION_REASON_ENUM",
    "REQUEST_STATE_ENUM",
    "approve_request",
    "get_closure",
    "get_request",
    "list_closures",
    "reject_request",
    "reset_store_for_tests",
    "submit_promote_request",
    "withdraw_request",
]
