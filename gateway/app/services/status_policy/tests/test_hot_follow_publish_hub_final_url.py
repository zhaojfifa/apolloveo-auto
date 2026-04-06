from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.deps import get_task_repository
from gateway.app.routers import tasks as tasks_router
from gateway.app.routers import hot_follow_api as hf_router


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

    monkeypatch.setattr(
        hf_router,
        "_publish_hub_payload",
        lambda _task: {
            "task_id": task_id,
            "media": {
                "final_video_url": f"/v1/tasks/{task_id}/final",
                "final_url": f"/v1/tasks/{task_id}/final",
                "voiceover_url": f"/v1/tasks/{task_id}/audio_mm",
            },
            "final_url": f"/v1/tasks/{task_id}/final",
            "final_video_url": f"/v1/tasks/{task_id}/final",
            "deliverables": {
                "final_mp4": {"label": "final.mp4", "url": f"/v1/tasks/{task_id}/final"},
            },
            "composed_ready": True,
            "composed_reason": "ready",
            "final": {"exists": True, "fresh": True, "url": f"/v1/tasks/{task_id}/final"},
            "historical_final": {"exists": True, "url": f"/v1/tasks/{task_id}/final"},
            "final_fresh": True,
            "final_stale_reason": None,
            "audio": {
                "status": "done",
                "audio_ready": True,
                "audio_ready_reason": "ready",
                "tts_voice": "mm_female_1",
            },
            "subtitles": {
                "subtitle_ready": True,
                "subtitle_ready_reason": "ready",
                "edited_text": "stub subtitle",
            },
            "scene_pack": {"exists": False, "status": "running"},
            "scene_pack_pending_reason": "scenes.running",
        },
    )

    app = FastAPI()
    app.include_router(tasks_router.api_router)
    app.include_router(hf_router.hot_follow_api_router)
    app.dependency_overrides[get_task_repository] = lambda: repo

    with TestClient(app) as client:
        res = client.get(f"/api/hot_follow/tasks/{task_id}/publish_hub")
        assert res.status_code == 200
        data = res.json()

    assert data["media"]["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert data["final_video_url"].endswith(f"/v1/tasks/{task_id}/final")
    assert (data.get("line") or {}).get("line_id") == "hot_follow_line"
    assert (data.get("line") or {}).get("sop_profile_ref") == "docs/runbooks/hot_follow_sop.md"
    assert data["composed_ready"] is True
    assert data["composed_reason"] == "ready"
    assert data.get("ready_gate", {}).get("publish_ready") is True
    assert data["scene_pack_pending_reason"] in {"scenes.running", "scenes.not_ready", "scenes.failed"}
    assert (data.get("deliverables", {}).get("final_mp4") or {}).get("url") == data["final_video_url"]

    saved = repo.get(task_id) or {}
    assert str(saved.get("compose_status")).lower() == "done"
    assert str(saved.get("compose_last_status")).lower() == "done"
