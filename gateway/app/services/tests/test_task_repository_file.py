from __future__ import annotations

import json
import logging
from pathlib import Path

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


def test_tasks_page_enables_download_when_final_video_exists_without_pack(monkeypatch):
    class _Repo:
        def list(self):
            return [
                {
                    "task_id": "final-only",
                    "tenant": "default",
                    "category_key": "hot_follow",
                    "title": "final only",
                    "created_at": "2026-03-28T00:00:00+00:00",
                    "final_video_key": "deliver/tasks/final-only/final.mp4",
                }
            ]

    monkeypatch.setenv("AUTH_MODE", "off")
    monkeypatch.setattr(tasks_router, "_pack_path_for_list", lambda _task: None)
    monkeypatch.setattr(tasks_router, "_signed_op_url", lambda task_id, kind: f"/signed/{task_id}/{kind}")
    monkeypatch.setattr(
        tasks_router,
        "render_template",
        lambda *, request, name, ctx=None, status_code=200, headers=None: HTMLResponse(
            content="|".join(
                f"{item.get('task_id')}:{item.get('pack_download_href')}:{bool(item.get('download_class'))}"
                for item in (ctx or {}).get("items", [])
            ),
            status_code=status_code,
            headers=headers,
        ),
    )
    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/tasks")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "/signed/final-only/final_mp4" in response.text
    assert response.text.endswith(":True")


def test_tasks_page_hot_follow_returns_200_without_storage_probe(monkeypatch):
    class _Repo:
        def list(self):
            return [
                {
                    "task_id": "hf-board-stable",
                    "tenant": "default",
                    "kind": "hot_follow",
                    "platform": "hot_follow",
                    "category_key": "hot_follow",
                    "title": "stable board",
                    "created_at": "2026-04-03T00:00:00+00:00",
                    "final_video_key": "deliver/tasks/hf-board-stable/final.mp4",
                    "status": "processing",
                }
            ]

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
    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/tasks")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "hf-board-stable" in response.text


def test_tasks_template_no_longer_depends_on_tailwind_cdn():
    template = (Path(__file__).resolve().parents[2] / "templates" / "tasks.html").read_text(encoding="utf-8")
    assert "cdn.tailwindcss.com" not in template


def test_op_download_proxy_uses_attachment_redirect_for_final_video(monkeypatch):
    class _Repo:
        def get(self, task_id):
            return {
                "task_id": task_id,
                "target_lang": "vi",
                "final_video_key": f"deliver/tasks/{task_id}/final.mp4",
            }

    monkeypatch.setenv("AUTH_MODE", "off")
    monkeypatch.delenv("OP_ACCESS_KEY", raising=False)
    monkeypatch.setattr(tasks_router, "object_exists", lambda key: str(key).endswith("/final.mp4"))
    monkeypatch.setattr(
        tasks_router,
        "get_download_url",
        lambda key, **kwargs: f"https://cdn.example/{kwargs.get('filename')}?disposition={kwargs.get('disposition')}&key={key}",
    )
    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/op/dl/final-only?kind=final_mp4", follow_redirects=False)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 302
    assert response.headers["location"].startswith("https://cdn.example/final.mp4")
    assert "disposition=attachment" in response.headers["location"]
