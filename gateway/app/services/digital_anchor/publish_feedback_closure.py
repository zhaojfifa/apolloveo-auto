"""Digital Anchor publish feedback closure write-back.

Phase D.1 owns only the separate
``digital_anchor_publish_feedback_closure_v1`` object. It does not mutate the
Digital Anchor packet, Phase B workbench projection, or Phase C delivery
binding projection.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, MutableMapping, Optional
from uuid import uuid4

ROLE_PACK_REF_ID = "digital_anchor_role_pack"
SPEAKER_PLAN_REF_ID = "digital_anchor_speaker_plan"
SURFACE_ID = "digital_anchor_publish_feedback_closure_v1"

ROLE_FEEDBACK_KINDS = frozenset({"accepted", "needs_revision", "not_used"})
SEGMENT_FEEDBACK_KINDS = frozenset({"accepted", "needs_revision", "not_used"})
PUBLISH_STATUS_VALUES = frozenset(
    {"not_published", "published", "publish_failed", "archived"}
)
RECORD_KINDS = frozenset(
    {"operator_review", "publish_callback", "archive_action", "correction_note"}
)
CHANNEL_METRICS_KEYS = frozenset(
    {"views", "likes", "shares", "comments", "watch_seconds", "captured_at"}
)


class ClosureValidationError(ValueError):
    """Raised when a feedback closure write violates the Phase D contract."""


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def _roles(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    delta = dict(_line_ref(packet, ROLE_PACK_REF_ID).get("delta") or {})
    return {
        item.get("role_id"): item
        for item in delta.get("roles", [])
        if item.get("role_id")
    }


def _segments(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    delta = dict(_line_ref(packet, SPEAKER_PLAN_REF_ID).get("delta") or {})
    return {
        item.get("segment_id"): item
        for item in delta.get("segments", [])
        if item.get("segment_id")
    }


def _linked_segments(packet: Mapping[str, Any], role_id: str) -> list[str]:
    return [
        segment["segment_id"]
        for segment in _segments(packet).values()
        if segment.get("binds_role_id") == role_id and segment.get("segment_id")
    ]


def _validate_role_ids(packet: Mapping[str, Any], role_ids: list[str]) -> None:
    known = _roles(packet)
    missing = [role_id for role_id in role_ids if role_id not in known]
    if missing:
        raise ClosureValidationError(f"unknown role_id values: {missing}")


def _validate_segment_ids(packet: Mapping[str, Any], segment_ids: list[str]) -> None:
    known = _segments(packet)
    missing = [segment_id for segment_id in segment_ids if segment_id not in known]
    if missing:
        raise ClosureValidationError(f"unknown segment_id values: {missing}")


def _validate_role_segment_join(
    packet: Mapping[str, Any], role_ids: list[str], segment_ids: list[str]
) -> None:
    if not role_ids or not segment_ids:
        return
    segments = _segments(packet)
    mismatched = [
        segment_id
        for segment_id in segment_ids
        if segments[segment_id].get("binds_role_id") not in role_ids
    ]
    if mismatched:
        raise ClosureValidationError(
            f"segment_id values do not bind to supplied role_ids: {mismatched}"
        )


def _validate_channel_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    extra = set(metrics) - CHANNEL_METRICS_KEYS
    if extra:
        raise ClosureValidationError(
            f"channel_metrics has forbidden keys: {sorted(extra)}"
        )
    snapshot = {key: metrics[key] for key in metrics if key in CHANNEL_METRICS_KEYS}
    for key in ("views", "likes", "shares", "comments", "watch_seconds"):
        if key in snapshot and (
            not isinstance(snapshot[key], int) or snapshot[key] < 0
        ):
            raise ClosureValidationError(f"{key} must be a non-negative integer")
    return snapshot


def _upsert_row(
    rows: list[dict[str, Any]], key: str, value: str, row: dict[str, Any]
) -> None:
    for index, current in enumerate(rows):
        if current.get(key) == value:
            rows[index] = row
            return
    rows.append(row)


def _record(
    *,
    record_kind: str,
    recorded_by: str,
    role_ids: Optional[list[str]] = None,
    segment_ids: Optional[list[str]] = None,
    note: Optional[str] = None,
    record_id: Optional[str] = None,
    recorded_at: Optional[str] = None,
) -> dict[str, Any]:
    if record_kind not in RECORD_KINDS:
        raise ClosureValidationError(f"unknown record_kind: {record_kind!r}")
    return {
        "record_id": record_id or f"rec_{uuid4().hex[:12]}",
        "recorded_at": recorded_at,
        "recorded_by": recorded_by,
        "record_kind": record_kind,
        "role_ids": role_ids or [],
        "segment_ids": segment_ids or [],
        "note": note,
    }


def create_closure(
    packet: Mapping[str, Any],
    delivery_projection: Mapping[str, Any],
    *,
    closure_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a separate Digital Anchor Phase D closure object."""
    if packet.get("line_id") != "digital_anchor":
        raise ClosureValidationError("closure may only bind to a digital_anchor packet")
    manifest = dict(delivery_projection.get("manifest") or {})
    if manifest.get("manifest_id") != "digital_anchor_delivery_manifest_v1":
        raise ClosureValidationError("delivery projection manifest is not Digital Anchor")
    if manifest.get("line_id") != packet.get("line_id"):
        raise ClosureValidationError("delivery projection line_id does not match packet")
    return {
        "surface": SURFACE_ID,
        "closure_id": closure_id or f"closure_{uuid4().hex[:12]}",
        "line_id": "digital_anchor",
        "packet_version": packet.get("packet_version"),
        "delivery_manifest_id": manifest.get("manifest_id"),
        "deliverable_profile_ref": manifest.get("deliverable_profile_ref"),
        "asset_sink_profile_ref": manifest.get("asset_sink_profile_ref"),
        "role_feedback": [],
        "segment_feedback": [],
        "publish_url": None,
        "publish_status": "not_published",
        "channel_metrics": {},
        "operator_publish_notes": None,
        "feedback_closure_records": [],
    }


def write_role_feedback(
    closure: MutableMapping[str, Any],
    packet: Mapping[str, Any],
    *,
    role_id: str,
    role_feedback_kind: str,
    role_feedback_note: Optional[str] = None,
    recorded_by: str = "operator",
    record_id: Optional[str] = None,
    recorded_at: Optional[str] = None,
) -> str:
    """Write role-level feedback and append one closure record."""
    roles = _roles(packet)
    if role_id not in roles:
        raise ClosureValidationError(f"unknown role_id: {role_id!r}")
    if role_feedback_kind not in ROLE_FEEDBACK_KINDS:
        raise ClosureValidationError(
            f"unknown role_feedback_kind: {role_feedback_kind!r}"
        )
    role = roles[role_id]
    row = {
        "role_id": role_id,
        "role_display_name": role.get("display_name"),
        "role_feedback_kind": role_feedback_kind,
        "role_feedback_note": role_feedback_note,
        "linked_segments": _linked_segments(packet, role_id),
    }
    _upsert_row(closure["role_feedback"], "role_id", role_id, row)
    record = _record(
        record_kind="operator_review",
        recorded_by=recorded_by,
        role_ids=[role_id],
        note=role_feedback_note,
        record_id=record_id,
        recorded_at=recorded_at,
    )
    closure["feedback_closure_records"].append(record)
    return record["record_id"]


def write_segment_feedback(
    closure: MutableMapping[str, Any],
    packet: Mapping[str, Any],
    *,
    segment_id: str,
    segment_feedback_kind: str,
    audio_feedback_note: Optional[str] = None,
    lip_sync_feedback_note: Optional[str] = None,
    subtitle_feedback_note: Optional[str] = None,
    recorded_by: str = "operator",
    record_id: Optional[str] = None,
    recorded_at: Optional[str] = None,
) -> str:
    """Write segment-level feedback and append one closure record."""
    segments = _segments(packet)
    if segment_id not in segments:
        raise ClosureValidationError(f"unknown segment_id: {segment_id!r}")
    if segment_feedback_kind not in SEGMENT_FEEDBACK_KINDS:
        raise ClosureValidationError(
            f"unknown segment_feedback_kind: {segment_feedback_kind!r}"
        )
    segment = segments[segment_id]
    _validate_role_ids(packet, [segment.get("binds_role_id")])
    row = {
        "segment_id": segment_id,
        "binds_role_id": segment.get("binds_role_id"),
        "script_ref": segment.get("script_ref"),
        "segment_feedback_kind": segment_feedback_kind,
        "audio_feedback_note": audio_feedback_note,
        "lip_sync_feedback_note": lip_sync_feedback_note,
        "subtitle_feedback_note": subtitle_feedback_note,
    }
    _upsert_row(closure["segment_feedback"], "segment_id", segment_id, row)
    record_note = audio_feedback_note or lip_sync_feedback_note or subtitle_feedback_note
    record = _record(
        record_kind="operator_review",
        recorded_by=recorded_by,
        role_ids=[segment.get("binds_role_id")],
        segment_ids=[segment_id],
        note=record_note,
        record_id=record_id,
        recorded_at=recorded_at,
    )
    closure["feedback_closure_records"].append(record)
    return record["record_id"]


def write_publish_closure(
    closure: MutableMapping[str, Any],
    packet: Mapping[str, Any],
    *,
    publish_status: str,
    publish_url: Optional[str] = None,
    channel_metrics: Optional[Mapping[str, Any]] = None,
    operator_publish_notes: Optional[str] = None,
    role_ids: Optional[list[str]] = None,
    segment_ids: Optional[list[str]] = None,
    recorded_by: str = "operator",
    record_kind: str = "publish_callback",
    record_id: Optional[str] = None,
    recorded_at: Optional[str] = None,
) -> str:
    """Write scoped publish closure fields and append one closure record."""
    if publish_status not in PUBLISH_STATUS_VALUES:
        raise ClosureValidationError(f"unknown publish_status: {publish_status!r}")
    if publish_url is not None and not isinstance(publish_url, str):
        raise ClosureValidationError("publish_url must be a string")
    affected_role_ids = role_ids or []
    affected_segment_ids = segment_ids or []
    _validate_role_ids(packet, affected_role_ids)
    _validate_segment_ids(packet, affected_segment_ids)
    _validate_role_segment_join(packet, affected_role_ids, affected_segment_ids)

    closure["publish_status"] = publish_status
    if publish_url is not None:
        closure["publish_url"] = publish_url
    if channel_metrics is not None:
        closure["channel_metrics"] = _validate_channel_metrics(channel_metrics)
    if operator_publish_notes is not None:
        if not isinstance(operator_publish_notes, str):
            raise ClosureValidationError("operator_publish_notes must be a string")
        closure["operator_publish_notes"] = operator_publish_notes

    record = _record(
        record_kind=record_kind,
        recorded_by=recorded_by,
        role_ids=affected_role_ids,
        segment_ids=affected_segment_ids,
        note=operator_publish_notes,
        record_id=record_id,
        recorded_at=recorded_at,
    )
    closure["feedback_closure_records"].append(record)
    return record["record_id"]


def append_feedback_closure_record(
    closure: MutableMapping[str, Any],
    packet: Mapping[str, Any],
    *,
    record_kind: str,
    recorded_by: str,
    role_ids: Optional[list[str]] = None,
    segment_ids: Optional[list[str]] = None,
    note: Optional[str] = None,
    record_id: Optional[str] = None,
    recorded_at: Optional[str] = None,
) -> str:
    """Append one explicit corrective/archive record without rewriting prior rows."""
    affected_role_ids = role_ids or []
    affected_segment_ids = segment_ids or []
    _validate_role_ids(packet, affected_role_ids)
    _validate_segment_ids(packet, affected_segment_ids)
    _validate_role_segment_join(packet, affected_role_ids, affected_segment_ids)
    record = _record(
        record_kind=record_kind,
        recorded_by=recorded_by,
        role_ids=affected_role_ids,
        segment_ids=affected_segment_ids,
        note=note,
        record_id=record_id,
        recorded_at=recorded_at,
    )
    closure["feedback_closure_records"].append(record)
    return record["record_id"]


def project_closure_view(closure: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a deep-copy display view of the separate closure object."""
    return deepcopy(dict(closure))


class InMemoryClosureStore:
    """Minimal in-process persistence surface for closure objects."""

    def __init__(self) -> None:
        self._closures: Dict[str, Dict[str, Any]] = {}

    def create(
        self,
        packet: Mapping[str, Any],
        delivery_projection: Mapping[str, Any],
        *,
        closure_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        closure = create_closure(packet, delivery_projection, closure_id=closure_id)
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

    def write_role_feedback(
        self, closure_id: str, packet: Mapping[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        if closure_id not in self._closures:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        record_id = write_role_feedback(self._closures[closure_id], packet, **kwargs)
        return {"record_id": record_id, "closure": self.get(closure_id)}

    def write_segment_feedback(
        self, closure_id: str, packet: Mapping[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        if closure_id not in self._closures:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        record_id = write_segment_feedback(self._closures[closure_id], packet, **kwargs)
        return {"record_id": record_id, "closure": self.get(closure_id)}

    def write_publish_closure(
        self, closure_id: str, packet: Mapping[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        if closure_id not in self._closures:
            raise ClosureValidationError(f"unknown closure_id: {closure_id!r}")
        record_id = write_publish_closure(self._closures[closure_id], packet, **kwargs)
        return {"record_id": record_id, "closure": self.get(closure_id)}


__all__ = [
    "CHANNEL_METRICS_KEYS",
    "ClosureValidationError",
    "InMemoryClosureStore",
    "PUBLISH_STATUS_VALUES",
    "RECORD_KINDS",
    "ROLE_FEEDBACK_KINDS",
    "SEGMENT_FEEDBACK_KINDS",
    "SURFACE_ID",
    "append_feedback_closure_record",
    "create_closure",
    "project_closure_view",
    "write_publish_closure",
    "write_role_feedback",
    "write_segment_feedback",
]
