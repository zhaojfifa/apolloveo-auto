"""Service-layer tests for the Matrix Script closure binding (Recovery PR-3).

Authority:
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
- ``docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`` §7 PR-3
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §6

Scope: lazy creation of the closure from the task packet, idempotent
``get_or_create_for_task``, contract-driven ``apply_event_for_task``
(operator_publish / retract / note paths + closed-enum rejections), and
read-only peek for surfaces that should display "not_published" until the
closure exists.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.matrix_script import closure_binding


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


def _matrix_script_task(task_id: str = "ms_task_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "packet": _packet_sample(),
    }


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def _cells_in_packet(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    raise AssertionError("variation cells missing from packet sample")


def test_get_or_create_for_task_creates_one_row_per_cell():
    task = _matrix_script_task()
    expected_cells = _cells_in_packet(task["packet"])

    closure = closure_binding.get_or_create_for_task(task)

    assert closure["surface"] == "matrix_script_publish_feedback_closure_v1"
    assert closure["line_id"] == "matrix_script"
    rows = closure["variation_feedback"]
    assert [row["variation_id"] for row in rows] == expected_cells
    for row in rows:
        assert row["publish_status"] == "pending"
        assert row["publish_url"] is None


def test_get_or_create_for_task_is_idempotent():
    task = _matrix_script_task()
    a = closure_binding.get_or_create_for_task(task)
    b = closure_binding.get_or_create_for_task(task)
    assert a["closure_id"] == b["closure_id"]


def test_get_or_create_for_task_rejects_non_matrix_script():
    task = {
        "task_id": "hf_001",
        "kind": "hot_follow",
        "packet": _packet_sample(),
    }
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.get_or_create_for_task(task)


def test_get_closure_view_for_task_returns_none_before_create():
    assert closure_binding.get_closure_view_for_task("ms_task_002") is None


def test_apply_event_operator_publish_round_trips():
    task = _matrix_script_task()
    cells = _cells_in_packet(task["packet"])
    result = closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "recorded_at": "2026-05-04T10:00:00Z",
            "payload": {
                "publish_url": "https://example.test/published/x",
                "publish_status": "pending",
            },
        },
    )

    assert result["event_id"].startswith("evt_")
    closure = result["closure"]
    row = next(r for r in closure["variation_feedback"] if r["variation_id"] == cells[0])
    assert row["publish_url"] == "https://example.test/published/x"
    assert row["publish_status"] == "pending"
    assert row["last_event_id"] == result["event_id"]
    assert closure["feedback_closure_records"][-1]["event_kind"] == "operator_publish"


def test_apply_event_operator_retract_sets_retracted():
    task = _matrix_script_task()
    cells = _cells_in_packet(task["packet"])
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "recorded_at": "2026-05-04T10:00:00Z",
            "payload": {"publish_status": "pending"},
        },
    )
    result = closure_binding.apply_event_for_task(
        task["task_id"],
        {
            "event_kind": "operator_retract",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "recorded_at": "2026-05-04T10:05:00Z",
        },
    )
    closure = result["closure"]
    row = next(r for r in closure["variation_feedback"] if r["variation_id"] == cells[0])
    assert row["publish_status"] == "retracted"


def test_apply_event_operator_note_records_text():
    task = _matrix_script_task()
    cells = _cells_in_packet(task["packet"])
    result = closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_note",
            "variation_id": cells[0],
            "actor_kind": "operator",
            "recorded_at": "2026-05-04T10:00:00Z",
            "payload": {"operator_publish_notes": "checked legal"},
        },
    )
    closure = result["closure"]
    row = next(r for r in closure["variation_feedback"] if r["variation_id"] == cells[0])
    assert row["operator_publish_notes"] == "checked legal"


def test_apply_event_unknown_event_kind_rejected():
    task = _matrix_script_task()
    cells = _cells_in_packet(task["packet"])
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_event_for_task(
            task,
            {
                "event_kind": "operator_dance",
                "variation_id": cells[0],
                "actor_kind": "operator",
            },
        )


def test_apply_event_operator_cannot_publish_with_platform_status():
    """Origin rule: operator_* may only set status in {pending, retracted}."""
    task = _matrix_script_task()
    cells = _cells_in_packet(task["packet"])
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_event_for_task(
            task,
            {
                "event_kind": "operator_publish",
                "variation_id": cells[0],
                "actor_kind": "operator",
                "payload": {"publish_status": "published"},
            },
        )


def test_apply_event_unknown_variation_rejected():
    task = _matrix_script_task()
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_event_for_task(
            task,
            {
                "event_kind": "operator_publish",
                "variation_id": "not_a_real_cell",
                "actor_kind": "operator",
                "payload": {"publish_status": "pending"},
            },
        )


def test_closure_does_not_mutate_packet():
    """Closure ownership is separate from packet truth (Phase D boundary)."""
    task = _matrix_script_task()
    snapshot = deepcopy(task["packet"])
    closure_binding.get_or_create_for_task(task)
    closure_binding.apply_event_for_task(
        task,
        {
            "event_kind": "operator_publish",
            "variation_id": _cells_in_packet(task["packet"])[0],
            "actor_kind": "operator",
            "payload": {"publish_status": "pending"},
        },
    )
    assert task["packet"] == snapshot
