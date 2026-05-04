"""Verify Digital Anchor publish-hub + workbench wiring (Recovery PR-4)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.digital_anchor import closure_binding
from gateway.app.services.operator_visible_surfaces.wiring import (
    build_operator_surfaces_for_publish_hub,
    build_operator_surfaces_for_workbench,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "digital_anchor"
    / "sample"
    / "digital_anchor_packet_v1.sample.json"
)


def _packet_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _digital_anchor_task() -> Dict[str, Any]:
    packet = _packet_sample()
    return {
        "task_id": "da_wiring_001",
        "id": "da_wiring_001",
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "ready_gate": {"publishable": True, "blocking": []},
        "packet": packet,
        "line_specific_refs": packet["line_specific_refs"],
        "line_id": "digital_anchor",
        "binding": packet.get("binding") or {},
    }


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def test_publish_hub_bundle_with_no_closure_yields_empty_mirror():
    task = _digital_anchor_task()
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=None,
    )
    mirror = bundle["publish_status_mirror"]
    assert mirror["publish_status"] == "not_published"


def test_publish_hub_bundle_consumes_closure_after_publish_writeback():
    task = _digital_anchor_task()
    closure_binding.write_publish_closure_for_task(
        task,
        publish_status="published",
        publish_url="https://example.test/da/wiring",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=closure,
    )
    mirror = bundle["publish_status_mirror"]
    assert mirror["publish_status"] == "published"
    assert mirror["publish_url"] == "https://example.test/da/wiring"


def test_workbench_bundle_attaches_role_speaker_surface():
    task = _digital_anchor_task()
    bundle = build_operator_surfaces_for_workbench(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
    )
    panel = bundle.get("workbench", {}).get("line_specific_panel", {})
    assert panel.get("panel_kind") == "digital_anchor"
    surface = bundle["workbench"]["digital_anchor_role_speaker_surface"]
    assert surface["surface"] == "digital_anchor_workbench_role_speaker_surface_v1"
    assert "role_surface" in surface
    assert "speaker_surface" in surface


def test_publish_hub_bundle_does_not_carry_provider_identifiers():
    task = _digital_anchor_task()
    closure_binding.write_publish_closure_for_task(
        task,
        publish_status="published",
        publish_url="https://example.test/da",
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=closure,
    )
    flat = json.dumps(bundle, default=str).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert forbidden not in flat
