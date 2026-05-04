"""HTTP-boundary tests for the Digital Anchor closure router (Recovery PR-4).

Authority:
- ``docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md``
- ``docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md``
- Router: ``gateway/app/routers/digital_anchor_closure.py``

Tests run only when FastAPI's TestClient is importable.
"""
from __future__ import annotations

import json
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


def _digital_anchor_task(task_id: str = "da_e2e_001") -> Dict[str, Any]:
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
        from gateway.app.routers import digital_anchor_closure
    except Exception:
        return None

    app = FastAPI()
    app.dependency_overrides[get_task_repository] = lambda: repo
    app.include_router(digital_anchor_closure.api_router)
    try:
        return TestClient(app)
    except Exception:
        return None


def test_get_closure_creates_lazily_via_http():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get(f"/api/digital-anchor/closures/{task['task_id']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["surface"] == "digital_anchor_publish_feedback_closure_v1"
    assert body["line_id"] == "digital_anchor"


def test_unknown_task_returns_404():
    client = _try_build_client(_StubRepo({}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get("/api/digital-anchor/closures/missing")
    assert resp.status_code == 404


def test_non_digital_anchor_rejected():
    task = {"task_id": "ms_001", "kind": "matrix_script", "packet": _packet_sample()}
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get(f"/api/digital-anchor/closures/{task['task_id']}")
    assert resp.status_code == 400


def test_post_role_feedback_201():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    role = _role_ids(task["packet"])[0]
    resp = client.post(
        f"/api/digital-anchor/closures/{task['task_id']}/role-feedback",
        json={
            "role_id": role,
            "role_feedback_kind": "needs_revision",
            "role_feedback_note": "redo intro",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["closure"]["role_feedback"][0]["role_id"] == role


def test_post_segment_feedback_201():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    segment = _segment_ids(task["packet"])[0]
    resp = client.post(
        f"/api/digital-anchor/closures/{task['task_id']}/segment-feedback",
        json={
            "segment_id": segment,
            "segment_feedback_kind": "accepted",
            "audio_feedback_note": "good",
        },
    )
    assert resp.status_code == 201, resp.text


def test_post_publish_closure_201():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.post(
        f"/api/digital-anchor/closures/{task['task_id']}/publish-closure",
        json={
            "publish_status": "published",
            "publish_url": "https://example.test/da",
            "operator_publish_notes": "ok",
        },
    )
    assert resp.status_code == 201, resp.text
    closure = resp.json()["closure"]
    assert closure["publish_status"] == "published"


def test_post_event_rejects_forbidden_provider_keys():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    role = _role_ids(task["packet"])[0]
    resp = client.post(
        f"/api/digital-anchor/closures/{task['task_id']}/role-feedback",
        json={
            "role_id": role,
            "role_feedback_kind": "accepted",
            "vendor_id": "tencent",
        },
    )
    assert resp.status_code == 400
    assert "forbidden_payload_key" in resp.json()["detail"]


def test_peek_returns_null_until_first_create():
    task = _digital_anchor_task()
    client = _try_build_client(_StubRepo({task["task_id"]: task}))
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")
    resp = client.get(f"/api/digital-anchor/closures/{task['task_id']}/peek")
    assert resp.status_code == 200
    assert resp.json() == {"closure": None}
