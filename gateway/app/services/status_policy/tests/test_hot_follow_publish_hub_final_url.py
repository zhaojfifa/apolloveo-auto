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


def test_hot_follow_publish_hub_includes_final_preview_url_and_ready(monkeypatch):
    task_id = "hf-publish-hub-final-01"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "status": "processing",
            "scenes_status": "running",
            "compose_status": "pending",
            "compose_last_status": "pending",
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

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/publish_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["media"]["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert data["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert data["composed_ready"] is True
    assert data["composed_reason"] == "ready"
    assert data["scene_pack_pending_reason"] in {"scenes.running", "scenes.not_ready", "scenes.failed"}
    assert (data.get("deliverables", {}).get("final_mp4") or {}).get("url") == data["final_video_url"]

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"
