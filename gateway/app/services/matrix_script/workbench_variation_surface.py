"""Matrix Script workbench variation surface projection.

Phase B only: read-only projection from a Matrix Script packet instance to
the formal workbench surface. No provider routing, delivery binding, publish
feedback write-back, or packet mutation happens here.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

VARIATION_REF_ID = "matrix_script_variation_matrix"
SLOT_PACK_REF_ID = "matrix_script_slot_pack"


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def project_workbench_variation_surface(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Project packet truth into the Matrix Script Phase B workbench surface."""
    variation_ref = _line_ref(packet, VARIATION_REF_ID)
    slot_ref = _line_ref(packet, SLOT_PACK_REF_ID)
    variation_delta = dict(variation_ref.get("delta") or {})
    slot_delta = dict(slot_ref.get("delta") or {})
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})

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
        "sourceMode": "workbench variation projection",
        "packetVersion": packet.get("packet_version"),
        "readyState": evidence.get("ready_state"),
        "variation_plan": {
            "axis_kind_set": deepcopy(variation_delta.get("axis_kind_set") or []),
            "axes": deepcopy(variation_delta.get("axes") or []),
            "cells": deepcopy(variation_delta.get("cells") or []),
        },
        "copy_bundle": {
            "slot_kind_set": deepcopy(slot_delta.get("slot_kind_set") or []),
            "slots": deepcopy(slot_delta.get("slots") or []),
        },
        "slot_detail_surface": {
            "join_rule": "variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id",
            "slots": deepcopy(slot_delta.get("slots") or []),
        },
        "attribution_refs": {
            "generic_refs": generic_refs,
            "line_specific_refs": line_specific_refs,
            "capability_plan": capability_plan,
            "worker_profile_ref": binding.get("worker_profile_ref"),
        },
        "publish_feedback_projection": {
            "reference_line": evidence.get("reference_line"),
            "validator_report_path": evidence.get("validator_report_path"),
            "ready_state": evidence.get("ready_state"),
            "feedback_writeback": "not_implemented_phase_b",
        },
        # Backward-compatible aliases for the current lightweight preview.
        "publish_feedback": {
            "reference_line": evidence.get("reference_line"),
            "validator_report_path": evidence.get("validator_report_path"),
            "ready_state": evidence.get("ready_state"),
            "feedback_writeback": "not_implemented_phase_b",
        },
        "result_packet_binding": {
            "generic_refs": [item["ref_id"] for item in generic_refs],
            "line_specific_refs": [item["ref_id"] for item in line_specific_refs],
            "capability_plan": [item["kind"] for item in capability_plan],
            "worker_profile_ref": binding.get("worker_profile_ref"),
            "delivery_binding": "not_implemented_phase_b",
        },
    }
