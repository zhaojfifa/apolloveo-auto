from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
pytest.importorskip("pydantic_settings")

from gateway.app.services import scenes_service


class _Repo:
    def __init__(self):
        self.rows = {}

    def get(self, task_id):
        row = self.rows.get(task_id)
        return dict(row) if isinstance(row, dict) else None

    def upsert(self, task_id, fields):
        row = dict(self.rows.get(task_id) or {})
        row.update(fields or {})
        self.rows[task_id] = row
        return row


class _ImmediateTasks:
    def add_task(self, fn, *args, **kwargs):
        fn(*args, **kwargs)


def test_hot_follow_scenes_build_writes_key_and_done(monkeypatch):
    task_id = "hf-scenes-ok"
    repo = _Repo()
    repo.upsert(
        task_id,
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "raw_path": "tasks/hf-scenes-ok/raw.mp4",
            "events": [],
        },
    )

    key = f"deliver/scenes/{task_id}/scenes.zip"
    monkeypatch.setattr(
        scenes_service,
        "generate_scenes_package",
        lambda _task_id: {"task_id": _task_id, "scenes_key": key, "scenes_count": 1},
    )

    out = scenes_service.build_scenes_for_task(task_id, repo, _ImmediateTasks())
    saved = repo.get(task_id) or {}
    assert out["status"] in {"queued", "already_ready"}
    assert saved.get("scenes_key") == key
    assert saved.get("scenes_status") in {"done", "ready"}


def test_missing_raw_sets_failed_and_error_message(monkeypatch):
    task_id = "hf-scenes-missing-raw"
    repo = _Repo()
    repo.upsert(task_id, {"task_id": task_id, "kind": "hot_follow", "events": []})

    monkeypatch.setattr(
        scenes_service,
        "generate_scenes_package",
        lambda _task_id: (_ for _ in ()).throw(RuntimeError("raw video not found")),
    )

    _ = scenes_service.build_scenes_for_task(task_id, repo, _ImmediateTasks())
    saved = repo.get(task_id) or {}
    assert saved.get("scenes_status") == "failed"
    assert isinstance(saved.get("scenes_error"), dict)
    assert "raw video not found" in str(saved.get("scenes_error_message") or "")
