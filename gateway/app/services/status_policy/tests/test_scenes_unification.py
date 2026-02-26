from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.deps import get_task_repository
from gateway.app.routers import tasks as tasks_router
from gateway.app.services import scene_split


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


def test_post_scenes_writes_deliverables_scenes_key(monkeypatch):
    task_id = "hf-scenes-test-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "deliverables": {},
        },
    )

    scenes_key = f"deliver/scenes/{task_id}/scenes.zip"

    def _fake_generate(_task_id: str):
        return {"task_id": _task_id, "scenes_key": scenes_key, "scenes_count": 2}

    monkeypatch.setattr(scene_split, "generate_scenes_package", _fake_generate)

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.post(f"/api/tasks/{task_id}/scenes")
        assert res.status_code == 200

    saved = repo.get(task_id) or {}
    deliverables = saved.get("deliverables") or {}
    assert deliverables.get("scenes_key") == scenes_key
