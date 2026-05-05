"""OWC-MS PR-2 / MS-W5 — Real operator review submit HTTP path test.

Authority:
- ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W5 (review actions write
  through existing closure path only; no second truth path; no new
  endpoint).
- Re-review blocker 1: "actual Matrix Script review submit path test
  through the existing closure endpoint".

Drives the existing Recovery PR-3 router
``POST /api/matrix-script/closures/{task_id}/events`` with ``event_kind=
operator_note`` + ``payload.review_zone`` from the OWC-MS PR-2 closed
enum, and asserts the closure side records the tag onto the appended
``feedback_closure_records[]`` entry. Skips cleanly when FastAPI's
TestClient is not importable in the local Python 3.9 import-light
environment; CI on Python 3.10+ runs the real HTTP path.

What is proved:

1. The submit form's `action` URL resolves to a real endpoint that
   exists today (no new endpoint added by PR-2).
2. The submit body shape from
   ``derive_matrix_script_review_zone_view`` POSTs successfully (HTTP
   201) when followed verbatim.
3. The ``review_zone`` tag is recorded on the appended record.
4. Posting an unknown ``review_zone`` returns HTTP 400 with the
   validation error from ``ClosureValidationError``.
5. Hot Follow / Digital Anchor tasks cannot use the route (HTTP 400
   from the existing matrix_script gate — ensures PR-2 did not widen
   the route's accepted line set).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from gateway.app.services.matrix_script import closure_binding
from gateway.app.services.matrix_script.review_zone_view import (
    REVIEW_EVENT_ENDPOINT_TEMPLATE,
    derive_matrix_script_review_zone_view,
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


def _cells(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    raise AssertionError("variation cells missing from packet sample")


class _StubRepo:
    def __init__(self, tasks: Dict[str, Dict[str, Any]]):
        self._tasks = tasks

    def get(self, task_id: str) -> Dict[str, Any] | None:
        return self._tasks.get(task_id)

    def create(self, task):  # pragma: no cover
        raise NotImplementedError

    def update(self, task_id, patch):  # pragma: no cover
        raise NotImplementedError

    def list(self):  # pragma: no cover
        return list(self._tasks.values())


@pytest.fixture(autouse=True)
def _reset_store():
    closure_binding.reset_for_tests()
    yield
    closure_binding.reset_for_tests()


def _try_build_client(repo: _StubRepo):
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from gateway.app.deps import get_task_repository
        from gateway.app.routers import matrix_script_closure
    except Exception:
        return None

    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(matrix_script_closure.api_router)
    try:
        return TestClient(app)
    except Exception:
        return None


def _matrix_script_task(task_id: str = "ms_w5_submit_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "packet": _packet_sample(),
    }


# -- 1. Submit form action is a real endpoint that exists today --------


def test_submit_form_action_url_matches_existing_router_route_template() -> None:
    """No new endpoint introduced by PR-2; template matches Recovery PR-3."""
    try:
        from gateway.app.routers import matrix_script_closure as router_module
    except Exception:
        pytest.skip(
            "Router import requires Python 3.10+ for the existing PEP-604 "
            "annotations in `gateway/app/config.py:43`."
        )

    routes = [getattr(r, "path", "") for r in router_module.api_router.routes]
    # Existing route from Recovery PR-3 is `/api/matrix-script/closures/{task_id}/events`
    assert any(path.endswith("/{task_id}/events") for path in routes)
    assert REVIEW_EVENT_ENDPOINT_TEMPLATE.endswith("/{task_id}/events")


# -- 2-3. POST through the real route succeeds + records review_zone ---


def test_real_submit_posts_through_existing_closure_endpoint_and_records_tag() -> None:
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    # Use the helper to build the bundle with task_id so the form action
    # is the real resolved URL — this proves the bundle's submit_form
    # shape is the same shape the operator browser would post.
    bundle = derive_matrix_script_review_zone_view(
        {
            "variation_plan": {
                "cells": [{"cell_id": cell_id} for cell_id in _cells(task["packet"])]
            }
        },
        None,
        {"panel_kind": "matrix_script"},
        task_id=task["task_id"],
    )
    cell_id = _cells(task["packet"])[0]
    submit_form = next(
        r for r in bundle["review_status_rows"] if r["variation_id"] == cell_id
    )["per_zone"]["subtitle"]["submit_form"]
    assert submit_form is not None

    body = {
        "event_kind": submit_form["event_kind"],
        "actor_kind": submit_form["actor_kind"],
        "variation_id": submit_form["variation_id"],
        "payload": {
            "operator_publish_notes": "字幕翻译需要复核（来自 MS-W5 真实提交测试）",
            "review_zone": submit_form["review_zone"],
        },
    }

    resp = client.post(submit_form["action"], json=body)
    assert resp.status_code == 201, resp.text

    payload = resp.json()
    closure = payload["closure"]
    # The appended record carries the review_zone tag (per closure
    # contract addendum §"Operator review zone tag (additive, OWC-MS
    # PR-2)"). Look up the most recent record.
    records = closure["feedback_closure_records"]
    assert records, "expected closure to record the operator_note event"
    last = records[-1]
    assert last["event_kind"] == "operator_note"
    assert last["variation_id"] == cell_id
    assert last["review_zone"] == "subtitle"
    # The variation row received the operator_publish_notes field,
    # confirming the existing operator_note write path was honored.
    row = next(
        r for r in closure["variation_feedback"] if r["variation_id"] == cell_id
    )
    assert "字幕翻译需要复核" in (row["operator_publish_notes"] or "")


def test_all_four_review_zones_post_successfully_through_real_endpoint() -> None:
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    cell_id = _cells(task["packet"])[0]
    for zone in ("subtitle", "dub", "copy", "cta"):
        resp = client.post(
            f"/api/matrix-script/closures/{task['task_id']}/events",
            json={
                "event_kind": "operator_note",
                "actor_kind": "operator",
                "variation_id": cell_id,
                "payload": {
                    "operator_publish_notes": f"{zone} review note",
                    "review_zone": zone,
                },
            },
        )
        assert resp.status_code == 201, f"{zone} → {resp.text}"


# -- 4. Unknown review_zone rejected through the real endpoint ---------


def test_unknown_review_zone_rejected_via_real_endpoint() -> None:
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    cell_id = _cells(task["packet"])[0]
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "actor_kind": "operator",
            "variation_id": cell_id,
            "payload": {
                "operator_publish_notes": "x",
                "review_zone": "audio",  # not in the closed enum
            },
        },
    )
    assert resp.status_code == 400, resp.text
    assert "review_zone" in resp.json()["detail"]


# -- 5. Hot Follow / Digital Anchor tasks cannot use the route ---------


def test_hot_follow_task_rejected_at_route_boundary() -> None:
    task = {
        "task_id": "hf_w5_001",
        "kind": "hot_follow",
        "packet": _packet_sample(),
    }
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "actor_kind": "operator",
            "variation_id": "cell_001",
            "payload": {
                "operator_publish_notes": "x",
                "review_zone": "subtitle",
            },
        },
    )
    assert resp.status_code == 400
    assert "matrix_script" in resp.json()["detail"]


def test_digital_anchor_task_rejected_at_route_boundary() -> None:
    task = {
        "task_id": "da_w5_001",
        "kind": "digital_anchor",
        "packet": _packet_sample(),
    }
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_note",
            "actor_kind": "operator",
            "variation_id": "cell_001",
            "payload": {
                "operator_publish_notes": "x",
                "review_zone": "subtitle",
            },
        },
    )
    assert resp.status_code == 400
    assert "matrix_script" in resp.json()["detail"]
