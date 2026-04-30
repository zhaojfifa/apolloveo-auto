"""Digital Anchor workbench role / speaker surface projection.

Phase B only: read-only projection from a Digital Anchor packet instance to
the formal workbench surface. No provider routing, delivery binding, publish
feedback write-back, or packet mutation happens here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

ROLE_PACK_REF_ID = "digital_anchor_role_pack"
SPEAKER_PLAN_REF_ID = "digital_anchor_speaker_plan"


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def _generic_ref_ids(packet: Mapping[str, Any]) -> set[str]:
    return {
        item.get("ref_id")
        for item in packet.get("generic_refs", [])
        if item.get("ref_id")
    }


def project_workbench_role_speaker_surface(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Project packet truth into the Digital Anchor Phase B workbench surface."""
    role_ref = _line_ref(packet, ROLE_PACK_REF_ID)
    speaker_ref = _line_ref(packet, SPEAKER_PLAN_REF_ID)
    role_delta = dict(role_ref.get("delta") or {})
    speaker_delta = dict(speaker_ref.get("delta") or {})
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})

    roles = deepcopy(role_delta.get("roles") or [])
    segments = deepcopy(speaker_delta.get("segments") or [])
    roles_by_id = {role.get("role_id"): role for role in roles}

    role_segment_bindings = []
    for segment in segments:
        role = dict(roles_by_id.get(segment.get("binds_role_id")) or {})
        role_segment_bindings.append(
            {
                "segment_id": segment.get("segment_id"),
                "binds_role_id": segment.get("binds_role_id"),
                "role_resolved": bool(role),
                "role_display_name": role.get("display_name"),
                "role_framing_kind": role.get("framing_kind"),
                "script_ref": segment.get("script_ref"),
                "dub_kind": segment.get("dub_kind"),
                "lip_sync_kind": segment.get("lip_sync_kind"),
                "language_pick": segment.get("language_pick"),
            }
        )

    generic_refs = [
        {
            "ref_id": item.get("ref_id"),
            "path": item.get("path"),
            "version": item.get("version"),
        }
        for item in packet.get("generic_refs", [])
    ]
    line_specific_refs = [
        {
            "ref_id": item.get("ref_id"),
            "path": item.get("path"),
            "version": item.get("version"),
            "binds_to": list(item.get("binds_to") or []),
        }
        for item in packet.get("line_specific_refs", [])
    ]
    capability_plan = [
        {
            "kind": item.get("kind"),
            "mode": item.get("mode"),
            "required": bool(item.get("required", False)),
        }
        for item in binding.get("capability_plan", [])
    ]

    return {
        "line_id": packet.get("line_id"),
        "packet_version": packet.get("packet_version"),
        "surface": "digital_anchor_workbench_role_speaker_surface_v1",
        "ready_state": evidence.get("ready_state"),
        "role_surface": {
            "framing_kind_set": deepcopy(role_delta.get("framing_kind_set") or []),
            "appearance_ref_kind_set": deepcopy(
                role_delta.get("appearance_ref_kind_set") or []
            ),
            "roles": roles,
        },
        "speaker_surface": {
            "dub_kind_set": deepcopy(speaker_delta.get("dub_kind_set") or []),
            "lip_sync_kind_set": deepcopy(speaker_delta.get("lip_sync_kind_set") or []),
            "segments": segments,
        },
        "role_segment_binding_surface": {
            "join_rule": "speaker_plan.segments[].binds_role_id == role_pack.roles[].role_id",
            "bindings": role_segment_bindings,
        },
        "scene_binding_projection": {
            "scene_contract_ref": "g_scene" in _generic_ref_ids(packet),
            "segments": [
                {
                    "segment_id": segment.get("segment_id"),
                    "script_ref": segment.get("script_ref"),
                }
                for segment in segments
            ],
            "scene_binding_writeback": "not_implemented_phase_b",
        },
        "attribution_refs": {
            "generic_refs": generic_refs,
            "line_specific_refs": line_specific_refs,
            "capability_plan": capability_plan,
            "worker_profile_ref": binding.get("worker_profile_ref"),
        },
        "phase_c_deferred": [
            "delivery_binding",
            "result_packet_binding",
            "manifest",
            "metadata_projection",
            "publish_feedback_projection",
        ],
    }
