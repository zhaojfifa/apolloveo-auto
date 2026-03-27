from __future__ import annotations

import json
import logging

from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse

from gateway.adapters.task_repository_file import FileTaskRepository
from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router


def _make_repo(base):
    repo = object.__new__(FileTaskRepository)
    repo._tenant = "default"
    repo._base = base
    return repo


def test_list_tasks_skips_corrupted_json_and_logs_path(tmp_path, caplog):
    repo = _make_repo(tmp_path)

    valid_path = tmp_path / "tasks" / "default" / "hot_follow" / "good-task.json"
    valid_path.parent.mkdir(parents=True, exist_ok=True)
    valid_path.write_text(
        json.dumps(
            {
                "task_id": "good-task",
                "tenant": "default",
                "category_key": "hot_follow",
                "title": "good",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    bad_path = tmp_path / "tasks" / "default" / "hot_follow" / "bad-task.json"
    bad_path.write_text('{"task_id":"bad-task"}\n{"extra":true}', encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        items = repo.list()

    assert [item["task_id"] for item in items] == ["good-task"]
    assert any("TASK_REPO_SKIP_CORRUPTED_JSON" in record.message for record in caplog.records)
    assert any(str(bad_path) in record.message for record in caplog.records)


def test_get_task_returns_none_for_corrupted_json(tmp_path, caplog):
    repo = _make_repo(tmp_path)

    bad_path = tmp_path / "tasks" / "default" / "hot_follow" / "broken-task.json"
    bad_path.parent.mkdir(parents=True, exist_ok=True)
    bad_path.write_text('{"task_id":"broken-task"}\n{"extra":true}', encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        payload = repo.get("broken-task")

    assert payload is None
    assert any(str(bad_path) in record.message for record in caplog.records)


def test_create_task_writes_valid_json_atomically(tmp_path):
    repo = _make_repo(tmp_path)

    payload = {
        "task_id": "write-task",
        "tenant": "default",
        "category_key": "hot_follow",
        "title": "valid",
    }

    repo.create_task(payload)

    path = tmp_path / "tasks" / "default" / "hot_follow" / "write-task.json"
    written = json.loads(path.read_text(encoding="utf-8"))

    assert written["task_id"] == "write-task"
    assert written["title"] == "valid"
    assert not list(path.parent.glob("write-task.json.*.tmp"))


def test_tasks_page_returns_200_when_repo_skips_corrupted_json(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)

    valid_path = tmp_path / "tasks" / "default" / "hot_follow" / "good-task.json"
    valid_path.parent.mkdir(parents=True, exist_ok=True)
    valid_path.write_text(
        json.dumps(
            {
                "task_id": "good-task",
                "tenant": "default",
                "category_key": "hot_follow",
                "title": "good",
                "created_at": "2026-03-27T00:00:00+00:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (tmp_path / "tasks" / "default" / "hot_follow" / "bad-task.json").write_text(
        '{"task_id":"bad-task"}\n{"extra":true}',
        encoding="utf-8",
    )

    monkeypatch.setenv("AUTH_MODE", "off")
    monkeypatch.setattr(tasks_router, "_pack_path_for_list", lambda _task: None)
    monkeypatch.setattr(
        tasks_router,
        "render_template",
        lambda *, request, name, ctx=None, status_code=200, headers=None: HTMLResponse(
            content=" ".join(str(item.get("task_id") or "") for item in (ctx or {}).get("items", [])),
            status_code=status_code,
            headers=headers,
        ),
    )
    app.dependency_overrides[get_task_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/tasks")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "good-task" in response.text
