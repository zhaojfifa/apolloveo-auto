"""Digital Anchor delivery binding projection.

Phase C only: read-only projection from a Digital Anchor packet instance to
the delivery-center binding surface. No artifact lookup, publish feedback
write-back, provider routing, or packet mutation happens here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping

ROLE_PACK_REF_ID = "digital_anchor_role_pack"
SPEAKER_PLAN_REF_ID = "digital_anchor_speaker_plan"


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def _capability_plan(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    binding = dict(packet.get("binding") or {})
    return [
        {
            "kind": item.get("kind"),
            "mode": item.get("mode"),
            "required": bool(item.get("required", False)),
        }
        for item in binding.get("capability_plan", [])
    ]


def _capability_by_kind(
    capability_plan: Iterable[Mapping[str, Any]], kind: str
) -> Mapping[str, Any]:
    for item in capability_plan:
        if item.get("kind") == kind:
            return item
    return {}


def _ref_ids(packet: Mapping[str, Any], key: str) -> list[str]:
    return [item.get("ref_id") for item in packet.get(key, []) if item.get("ref_id")]


def _role_segment_bindings(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    role_delta = dict(_line_ref(packet, ROLE_PACK_REF_ID).get("delta") or {})
    speaker_delta = dict(_line_ref(packet, SPEAKER_PLAN_REF_ID).get("delta") or {})
    roles = {item.get("role_id"): item for item in role_delta.get("roles", [])}

    bindings: list[dict[str, Any]] = []
    for segment in speaker_delta.get("segments", []):
        role = dict(roles.get(segment.get("binds_role_id")) or {})
        bindings.append(
            {
                "segment_id": segment.get("segment_id"),
                "binds_role_id": segment.get("binds_role_id"),
                "role_id": role.get("role_id"),
                "role_display_name": role.get("display_name"),
                "role_framing_kind": role.get("framing_kind"),
                "appearance_ref": role.get("appearance_ref"),
                "script_ref": segment.get("script_ref"),
                "dub_kind": segment.get("dub_kind"),
                "lip_sync_kind": segment.get("lip_sync_kind"),
                "language_pick": segment.get("language_pick"),
            }
        )
    return bindings


def project_delivery_binding(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Project packet truth into the Digital Anchor Phase C delivery surface."""
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})
    metadata = deepcopy(packet.get("metadata") or {})
    capabilities = _capability_plan(packet)
    subtitles = _capability_by_kind(capabilities, "subtitles")
    dub = _capability_by_kind(capabilities, "dub")
    lip_sync = _capability_by_kind(capabilities, "lip_sync")
    pack = _capability_by_kind(capabilities, "pack")
    generic_refs = _ref_ids(packet, "generic_refs")
    line_specific_refs = _ref_ids(packet, "line_specific_refs")

    deliverable_profile_ref = binding.get("deliverable_profile_ref")
    asset_sink_profile_ref = binding.get("asset_sink_profile_ref")

    deliverables = [
        {
            "deliverable_id": "digital_anchor_role_manifest",
            "kind": "role_manifest",
            "required": True,
            "source_ref_id": ROLE_PACK_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "digital_anchor_speaker_segment_bundle",
            "kind": "speaker_segment_bundle",
            "required": True,
            "source_ref_id": SPEAKER_PLAN_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "digital_anchor_subtitle_bundle",
            "kind": "subtitle_bundle",
            "required": bool(subtitles.get("required", False)),
            "source_ref_id": "capability:subtitles",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "digital_anchor_audio_bundle",
            "kind": "audio_bundle",
            "required": bool(dub.get("required", False)),
            "source_ref_id": "capability:dub",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "digital_anchor_lip_sync_bundle",
            "kind": "lip_sync_bundle",
            "required": bool(lip_sync.get("required", False)),
            "source_ref_id": "capability:lip_sync",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "digital_anchor_scene_pack",
            "kind": "scene_pack",
            "required": bool(pack.get("required", False)),
            "source_ref_id": "capability:pack",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
    ]

    binding_profile_refs = {
        "worker_profile_ref": binding.get("worker_profile_ref"),
        "deliverable_profile_ref": deliverable_profile_ref,
        "asset_sink_profile_ref": asset_sink_profile_ref,
    }

    return {
        "line_id": packet.get("line_id"),
        "packet_version": packet.get("packet_version"),
        "surface": "digital_anchor_delivery_binding_v1",
        "delivery_pack": {
            "deliverable_profile_ref": deliverable_profile_ref,
            "asset_sink_profile_ref": asset_sink_profile_ref,
            "deliverables": deliverables,
        },
        "result_packet_binding": {
            "generic_refs": generic_refs,
            "line_specific_refs": line_specific_refs,
            "binding_profile_refs": binding_profile_refs,
            "capability_plan": capabilities,
            "role_segment_bindings": _role_segment_bindings(packet),
        },
        "manifest": {
            "manifest_id": "digital_anchor_delivery_manifest_v1",
            "line_id": packet.get("line_id"),
            "packet_version": packet.get("packet_version"),
            "deliverable_profile_ref": deliverable_profile_ref,
            "asset_sink_profile_ref": asset_sink_profile_ref,
            "source_refs": {
                "generic": generic_refs,
                "line_specific": line_specific_refs,
            },
            "metadata": metadata,
            "validator_report_path": evidence.get("validator_report_path"),
            "packet_ready_state": evidence.get("ready_state"),
            "write_policy": "read_only_phase_c",
        },
        "metadata_projection": {
            "line_id": packet.get("line_id"),
            "packet_version": packet.get("packet_version"),
            "metadata": metadata,
            "display_only": True,
        },
        "phase_d_deferred": [
            "role_feedback",
            "segment_feedback",
            "publish_url",
            "publish_status",
            "channel_metrics",
            "operator_publish_notes",
            "feedback_closure_records",
        ],
    }
