"""HTTP-boundary tests for the Matrix Script closure router (Recovery PR-3).

Authority:
- ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``
- ``docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`` §6
- Router: ``gateway/app/routers/matrix_script_closure.py``

Tests run only when FastAPI's TestClient is importable. Service-level
behavior is already covered by ``test_matrix_script_closure_binding.py``;
this file proves that the contract-backed path is reachable via the
operator-visible HTTP surface and that boundary discipline holds (404 on
unknown task, 400 on non-matrix_script task, 400 on forbidden payload
keys, 201 on contract-shaped event submit).
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


def _cells(packet: Dict[str, Any]) -> list[str]:
    for ref in packet.get("line_specific_refs", []):
        if ref.get("ref_id") == "matrix_script_variation_matrix":
            return [c["cell_id"] for c in ref["delta"]["cells"]]
    raise AssertionError("variation cells missing from packet sample")


class _StubRepo:
    """Minimal in-memory ITaskRepository compatible with `assets`-style tests."""

    def __init__(self, tasks: Dict[str, Dict[str, Any]]):
        self._tasks = tasks

    def get(self, task_id: str) -> Dict[str, Any] | None:
        return self._tasks.get(task_id)

    # Other ITaskRepository methods are not exercised by the closure router.
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


def _matrix_script_task(task_id: str = "ms_e2e_001") -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "category_key": "matrix_script",
        "platform": "matrix_script",
        "packet": _packet_sample(),
    }


def test_get_closure_creates_lazily_via_http():
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["surface"] == "matrix_script_publish_feedback_closure_v1"
    assert body["line_id"] == "matrix_script"
    assert {row["variation_id"] for row in body["variation_feedback"]} == set(
        _cells(task["packet"])
    )


def test_unknown_task_returns_404():
    client = _try_build_client(_StubRepo({}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get("/api/matrix-script/closures/nope")
    assert resp.status_code == 404


def test_non_matrix_script_task_rejected():
    task = {
        "task_id": "hf_001",
        "kind": "hot_follow",
        "packet": _packet_sample(),
    }
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}")
    assert resp.status_code == 400
    assert "matrix_script" in resp.json()["detail"]


def test_post_event_operator_publish_201():
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    cell = _cells(task["packet"])[0]
    body = {
        "event_kind": "operator_publish",
        "variation_id": cell,
        "actor_kind": "operator",
        "recorded_at": "2026-05-04T11:00:00Z",
        "payload": {
            "publish_url": "https://example.test/p/1",
            "publish_status": "pending",
        },
    }
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json=body,
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["event_id"].startswith("evt_")
    closure = payload["closure"]
    row = next(r for r in closure["variation_feedback"] if r["variation_id"] == cell)
    assert row["publish_url"] == "https://example.test/p/1"
    assert row["publish_status"] == "pending"


def test_post_event_rejects_forbidden_provider_keys():
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    cell = _cells(task["packet"])[0]
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_publish",
            "variation_id": cell,
            "actor_kind": "operator",
            "payload": {
                "publish_status": "pending",
                "vendor_id": "tencent",
            },
        },
    )
    assert resp.status_code == 400
    assert "forbidden_payload_key" in resp.json()["detail"]


def test_post_event_rejects_unknown_event_kind():
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    cell = _cells(task["packet"])[0]
    resp = client.post(
        f"/api/matrix-script/closures/{task['task_id']}/events",
        json={
            "event_kind": "operator_dance",
            "variation_id": cell,
            "actor_kind": "operator",
        },
    )
    assert resp.status_code == 400


def test_peek_returns_null_until_first_create():
    task = _matrix_script_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    resp = client.get(f"/api/matrix-script/closures/{task['task_id']}/peek")
    assert resp.status_code == 200
    assert resp.json() == {"closure": None}

    # After GET (lazy create), peek returns the closure.
    client.get(f"/api/matrix-script/closures/{task['task_id']}")
    resp2 = client.get(f"/api/matrix-script/closures/{task['task_id']}/peek")
    assert resp2.status_code == 200
    assert resp2.json()["closure"]["surface"] == (
        "matrix_script_publish_feedback_closure_v1"
    )
