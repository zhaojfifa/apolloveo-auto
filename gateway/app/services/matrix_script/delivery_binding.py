"""Matrix Script delivery binding projection.

Phase C only: read-only projection from a Matrix Script packet instance to
the delivery-center binding surface. No artifact lookup, publish feedback
write-back, provider routing, or packet mutation happens here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping

VARIATION_REF_ID = "matrix_script_variation_matrix"
SLOT_PACK_REF_ID = "matrix_script_slot_pack"


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


def _cell_slot_bindings(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    variation_delta = dict(_line_ref(packet, VARIATION_REF_ID).get("delta") or {})
    slot_delta = dict(_line_ref(packet, SLOT_PACK_REF_ID).get("delta") or {})
    slots = {item.get("slot_id"): item for item in slot_delta.get("slots", [])}

    bindings: list[dict[str, Any]] = []
    for cell in variation_delta.get("cells", []):
        slot_id = cell.get("script_slot_ref")
        slot = dict(slots.get(slot_id) or {})
        language_scope = dict(slot.get("language_scope") or {})
        bindings.append(
            {
                "cell_id": cell.get("cell_id"),
                "script_slot_ref": slot_id,
                "slot_id": slot.get("slot_id"),
                "body_ref": slot.get("body_ref"),
                "source_language": language_scope.get("source_language"),
                "target_language": deepcopy(language_scope.get("target_language") or []),
            }
        )
    return bindings


def project_delivery_binding(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Project packet truth into the Matrix Script Phase C delivery surface."""
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})
    metadata = deepcopy(packet.get("metadata") or {})
    capabilities = _capability_plan(packet)
    subtitles = _capability_by_kind(capabilities, "subtitles")
    dub = _capability_by_kind(capabilities, "dub")
    pack = _capability_by_kind(capabilities, "pack")
    generic_refs = _ref_ids(packet, "generic_refs")
    line_specific_refs = _ref_ids(packet, "line_specific_refs")

    deliverable_profile_ref = binding.get("deliverable_profile_ref")
    asset_sink_profile_ref = binding.get("asset_sink_profile_ref")

    deliverables = [
        {
            "deliverable_id": "matrix_script_variation_manifest",
            "kind": "variation_manifest",
            "required": True,
            "source_ref_id": VARIATION_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "matrix_script_slot_bundle",
            "kind": "script_slot_bundle",
            "required": True,
            "source_ref_id": SLOT_PACK_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "matrix_script_subtitle_bundle",
            "kind": "subtitle_bundle",
            "required": bool(subtitles.get("required", False)),
            "source_ref_id": SLOT_PACK_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "matrix_script_audio_preview",
            "kind": "audio_preview",
            "required": bool(dub.get("required", False)),
            "source_ref_id": "capability:dub",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": "not_implemented_phase_c",
        },
        {
            "deliverable_id": "matrix_script_scene_pack",
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
        "surface": "matrix_script_delivery_binding_v1",
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
            "cell_slot_bindings": _cell_slot_bindings(packet),
        },
        "manifest": {
            "manifest_id": "matrix_script_delivery_manifest_v1",
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
            "variation_id_feedback",
            "publish_url",
            "publish_status",
            "channel_metrics",
            "operator_publish_notes",
            "feedback_closure_records",
        ],
    }
