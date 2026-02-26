from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.deps import get_task_repository
from gateway.app.routers import tasks as tasks_router


class _Repo:
    def __init__(self):
        self._rows = {}

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row

    def upsert(self, task_id, fields):
        cur = dict(self._rows.get(task_id) or {})
        cur.update(fields or {})
        self._rows[task_id] = cur
        return cur


def test_hot_follow_workbench_ready_gate_backfills_compose_when_final_exists(monkeypatch):
    task_id = "hf-workbench-ready-gate-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "compose_status": "pending",
            "compose_last_status": "pending",
            "final": {"exists": True},
        },
    )

    def _fake_composed(_task, _task_id):
        return {
            "composed_ready": False,
            "composed_reason": "final_missing",
            "final": {"exists": True, "url": None, "size_bytes": 0},
            "compose_error_reason": None,
            "compose_error_message": None,
            "raw_exists": True,
            "voice_exists": True,
        }

    monkeypatch.setattr(tasks_router, "_compute_composed_state", _fake_composed)
    monkeypatch.setattr(tasks_router, "object_exists", lambda _key: False)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/workbench_hub")
        assert res.status_code == 200
        data = res.json()

    assert data.get("ready_gate", {}).get("compose_ready") is True
    assert data.get("ready_gate", {}).get("publish_ready") is True
    assert data.get("composed_ready") is True
    assert data.get("composed_reason") == "ready"
    assert str(data.get("final_video_url") or "").endswith(f"/v1/tasks/{task_id}/final")

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"

