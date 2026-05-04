"""Verify that the Matrix Script publish hub presenter consumes the
contract-backed closure (Recovery PR-3) and that the operator-visible
``publish_status_mirror`` reflects closure state for matrix_script tasks.

Authority:
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §6
- Wiring: ``gateway/app/services/operator_visible_surfaces/wiring.py`` +
  ``gateway/app/services/task_view_helpers.py::publish_hub_payload``
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.matrix_script import closure_binding
from gateway.app.services.operator_visible_surfaces.wiring import (
    build_operator_surfaces_for_publish_hub,
)


SAMPLE_PACKET_PATH = (
    Path(__file__).resolve().parents[4]
    / "schemas"
    / "packets"
    / "matrix_script"
    / "sample"
    / "matrix_script_packet_v1.sample.json"
)


def _packet_sample() -> Dict[str, Any]:
    return json.loads(SAMPLE_PACKET_PATH.read_text())


def _matrix_script_task() -> Dict[str, Any]:
    packet = _packet_sample()
    return {
        "task_id": "ms_wiring_001",
        "id": "ms_wiring_001",
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "ready_gate": {"publishable": True, "blocking": []},
        "packet": packet,
        "line_specific_refs": packet["line_specific_refs"],
        "line_id": "matrix_script",
        "binding": packet.get("binding") or {},
    }


def _cells(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    raise AssertionError("variation cells missing from packet sample")


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def test_publish_hub_bundle_with_no_closure_yields_empty_mirror():
    task = _matrix_script_task()
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=None,
    )
    mirror = bundle["publish_status_mirror"]
    assert mirror["publish_status"] == "not_published"
    assert mirror["publish_url"] is None


def test_publish_hub_bundle_consumes_closure_after_operator_publish():
    task = _matrix_script_task()
    cells = _cells(task["packet"])
    closure_binding.get_or_create_for_task(task)
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "recorded_at": "2026-05-04T12:00:00Z",
            "payload": {
                "publish_url": "https://example.test/wiring/1",
                "publish_status": "pending",
            },
        },
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=closure,
    )
    mirror = bundle["publish_status_mirror"]
    # Single-cell pending → aggregate "pending"; URL surfaces from the row.
    assert mirror["publish_status"] == "pending"
    assert mirror["publish_url"] == "https://example.test/wiring/1"


def test_publish_hub_bundle_aggregates_all_published():
    task = _matrix_script_task()
    cells = _cells(task["packet"])
    closure_binding.get_or_create_for_task(task)
    for cell in cells:
        closure_binding.apply_event_for_task(
            task,
            {
                "event_kind": "platform_callback",
                "variation_id": cell,
                "actor_kind": "platform",
                "recorded_at": "2026-05-04T13:00:00Z",
                "payload": {
                    "publish_status": "published",
                    "publish_url": f"https://example.test/done/{cell}",
                },
            },
        )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=closure,
    )
    assert bundle["publish_status_mirror"]["publish_status"] == "published"


def test_publish_hub_bundle_does_not_carry_provider_identifiers():
    """Operator-visible payload red line: no vendor / model / provider /
    engine identifier may flow through the publish hub bundle."""
    task = _matrix_script_task()
    cells = _cells(task["packet"])
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "payload": {
                "publish_url": "https://example.test/p",
                "publish_status": "pending",
            },
        },
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    bundle = build_operator_surfaces_for_publish_hub(
        task=task,
        authoritative_state={"ready_gate": task["ready_gate"]},
        publish_feedback_closure=closure,
    )
    flat = json.dumps(bundle, default=str).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id"):
        assert forbidden not in flat, f"{forbidden} leaked into operator bundle"
