from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/debug/panels/matrix-script", tags=["debug-panels"])

REPO_ROOT = Path(__file__).resolve().parents[3]
STATIC_HTML = REPO_ROOT / "gateway" / "app" / "static" / "panel_html.html"
SAMPLE_PACKET = (
    REPO_ROOT
    / "schemas"
    / "packets"
    / "matrix_script"
    / "sample"
    / "matrix_script_packet_v1.sample.json"
)


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def _project_panel_data(packet: Mapping[str, Any]) -> Dict[str, Any]:
    variation_ref = _line_ref(packet, "matrix_script_variation_matrix")
    slot_ref = _line_ref(packet, "matrix_script_slot_pack")
    variation_delta = dict(variation_ref.get("delta") or {})
    slot_delta = dict(slot_ref.get("delta") or {})
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})

    return {
        "sourceMode": "live sample projection",
        "packetVersion": packet.get("packet_version"),
        "readyState": evidence.get("ready_state"),
        "variation_plan": {
            "axis_kind_set": variation_delta.get("axis_kind_set", []),
            "axes": variation_delta.get("axes", []),
            "cells": variation_delta.get("cells", []),
        },
        "copy_bundle": {
            "slot_kind_set": slot_delta.get("slot_kind_set", []),
            "slots": slot_delta.get("slots", []),
        },
        "publish_feedback": {
            "reference_line": evidence.get("reference_line"),
            "validator_report_path": evidence.get("validator_report_path"),
            "ready_state": evidence.get("ready_state"),
            "deliverable_profile_ref": binding.get("deliverable_profile_ref"),
            "asset_sink_profile_ref": binding.get("asset_sink_profile_ref"),
        },
        "result_packet_binding": {
            "generic_refs": [item.get("ref_id") for item in packet.get("generic_refs", [])],
            "line_specific_refs": [
                item.get("ref_id") for item in packet.get("line_specific_refs", [])
            ],
            "capability_plan": [
                item.get("kind") for item in binding.get("capability_plan", [])
            ],
            "worker_profile_ref": binding.get("worker_profile_ref"),
        },
    }


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def matrix_script_panel() -> HTMLResponse:
    html = STATIC_HTML.read_text(encoding="utf-8")
    html = html.replace('href="panel_css.css"', 'href="/static/panel_css.css"')
    html = html.replace('src="panel_js.js"', 'src="/static/panel_js.js"')
    return HTMLResponse(html)


@router.get("/data")
def matrix_script_panel_data() -> Dict[str, Any]:
    packet = json.loads(SAMPLE_PACKET.read_text(encoding="utf-8"))
    return {
        "source": "schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json",
        "packet_instance": packet,
        "panel_data": _project_panel_data(packet),
    }
