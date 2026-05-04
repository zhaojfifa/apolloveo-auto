"""Service-layer tests for the Digital Anchor closure binding (Recovery PR-4).

Authority:
- ``docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md``
- ``docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md``

Scope: lazy creation from packet + delivery projection, idempotent
``get_or_create_for_task``, contract-driven role / segment / publish-
closure write-back, closed-enum rejection, packet-mutation absence.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.digital_anchor import closure_binding


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


def _digital_anchor_task(task_id: str = "da_task_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "digital_anchor",
        "category_key": "digital_anchor",
        "platform": "digital_anchor",
        "packet": _packet_sample(),
    }


def _role_ids(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "digital_anchor_role_pack":
            return [r["role_id"] for r in ref["delta"]["roles"]]
    raise AssertionError("role_pack missing in sample")


def _segment_ids(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "digital_anchor_speaker_plan":
            return [s["segment_id"] for s in ref["delta"]["segments"]]
    raise AssertionError("speaker_plan missing in sample")


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def test_get_or_create_initializes_closure():
    task = _digital_anchor_task()
    closure = closure_binding.get_or_create_for_task(task)
    assert closure["surface"] == "digital_anchor_publish_feedback_closure_v1"
    assert closure["line_id"] == "digital_anchor"
    assert closure["publish_status"] == "not_published"
    assert closure["role_feedback"] == []
    assert closure["segment_feedback"] == []


def test_get_or_create_is_idempotent():
    task = _digital_anchor_task()
    a = closure_binding.get_or_create_for_task(task)
    b = closure_binding.get_or_create_for_task(task)
    assert a["closure_id"] == b["closure_id"]


def test_non_digital_anchor_task_rejected():
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.get_or_create_for_task(
            {"task_id": "x", "kind": "matrix_script", "packet": {"line_id": "matrix_script"}}
        )


def test_get_closure_view_returns_none_until_create():
    assert closure_binding.get_closure_view_for_task("nope") is None


def test_role_feedback_writeback():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    result = closure_binding.write_role_feedback_for_task(
        task,
        role_id=role,
        role_feedback_kind="needs_revision",
        role_feedback_note="re-record opening",
    )
    closure = result["closure"]
    rows = closure["role_feedback"]
    assert len(rows) == 1
    assert rows[0]["role_id"] == role
    assert rows[0]["role_feedback_kind"] == "needs_revision"


def test_role_feedback_unknown_role_rejected():
    task = _digital_anchor_task()
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.write_role_feedback_for_task(
            task,
            role_id="not_a_real_role",
            role_feedback_kind="accepted",
        )


def test_role_feedback_unknown_kind_rejected():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.write_role_feedback_for_task(
            task, role_id=role, role_feedback_kind="great"
        )


def test_segment_feedback_writeback():
    task = _digital_anchor_task()
    segment = _segment_ids(task["packet"])[0]
    result = closure_binding.write_segment_feedback_for_task(
        task,
        segment_id=segment,
        segment_feedback_kind="accepted",
        audio_feedback_note="ok",
    )
    closure = result["closure"]
    rows = closure["segment_feedback"]
    assert len(rows) == 1
    assert rows[0]["segment_id"] == segment
    assert rows[0]["audio_feedback_note"] == "ok"


def test_d1_publish_attempted_sets_row_pending():
    """D.1 path is the active truth path; per-row publish_status uses
    the closed enum {pending, published, failed, retracted}."""
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    result = closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_attempted",
        row_scope="role",
        row_id=role,
        actor_kind="operator",
    )
    closure = result["closure"]
    row = next(r for r in closure["role_feedback"] if r["role_id"] == role)
    assert row["publish_status"] == "pending"


def test_d1_publish_accepted_sets_row_published_with_url():
    task = _digital_anchor_task()
    segment = _segment_ids(task["packet"])[0]
    result = closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_accepted",
        row_scope="segment",
        row_id=segment,
        actor_kind="platform",
        payload={"publish_url": "https://example.test/da/seg"},
    )
    closure = result["closure"]
    row = next(r for r in closure["segment_feedback"] if r["segment_id"] == segment)
    assert row["publish_status"] == "published"
    assert row["publish_url"] == "https://example.test/da/seg"


def test_d1_publish_rejected_sets_row_failed():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    result = closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_rejected",
        row_scope="role",
        row_id=role,
        actor_kind="platform",
    )
    closure = result["closure"]
    row = next(r for r in closure["role_feedback"] if r["role_id"] == role)
    assert row["publish_status"] == "failed"


def test_d1_publish_retracted_sets_row_retracted():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    result = closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="publish_retracted",
        row_scope="role",
        row_id=role,
        actor_kind="operator",
    )
    closure = result["closure"]
    row = next(r for r in closure["role_feedback"] if r["role_id"] == role)
    assert row["publish_status"] == "retracted"


def test_d1_unknown_event_kind_rejected():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_writeback_event_for_task(
            task,
            event_kind="brand_new_kind",
            row_scope="role",
            row_id=role,
        )


def test_d1_actor_must_match_event_kind():
    """publish_accepted is platform-only; operator actor is rejected."""
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    with pytest.raises(closure_binding.ClosureValidationError):
        closure_binding.apply_writeback_event_for_task(
            task,
            event_kind="publish_accepted",
            row_scope="role",
            row_id=role,
            actor_kind="operator",
        )


def test_d1_metrics_snapshot_appends_to_row_channel_metrics():
    task = _digital_anchor_task()
    role = _role_ids(task["packet"])[0]
    closure_binding.apply_writeback_event_for_task(
        task,
        event_kind="metrics_snapshot",
        row_scope="role",
        row_id=role,
        actor_kind="platform",
        payload={"views": 100, "captured_at": "2026-05-04T12:00:00Z"},
    )
    closure = closure_binding.get_closure_view_for_task(task["task_id"])
    row = next(r for r in closure["role_feedback"] if r["role_id"] == role)
    assert row["channel_metrics"] and row["channel_metrics"][-1]["views"] == 100


def test_d1_old_write_publish_closure_for_task_no_longer_exported():
    """Reviewer-fix #3: the older D.0-style API must not be the active
    operator path. It is removed from the closure_binding public surface."""
    assert not hasattr(closure_binding, "write_publish_closure_for_task")


def test_closure_does_not_mutate_packet():
    task = _digital_anchor_task()
    snapshot = deepcopy(task["packet"])
    closure_binding.get_or_create_for_task(task)
    role = _role_ids(task["packet"])[0]
    closure_binding.write_role_feedback_for_task(
        task, role_id=role, role_feedback_kind="accepted"
    )
    assert task["packet"] == snapshot
