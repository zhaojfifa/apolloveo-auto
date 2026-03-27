from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router


class _Repo:
    def get(self, task_id: str):
        if task_id == "4d1bb00bdfd3":
            return {
                "task_id": task_id,
                "kind": "hot_follow",
                "category_key": "hot_follow",
                "platform": "douyin",
                "content_lang": "vi",
                "ui_lang": "zh",
                "source_url": "https://example.com/video",
            }
        return None

    def list(self):
        return []


def test_auth_middleware_returns_503_for_html_when_auth_env_missing(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "both")
    monkeypatch.delenv("OP_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    app.dependency_overrides[tasks_router.get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/tasks/4d1bb00bdfd3?ui_locale=zh")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "AUTH misconfigured" in response.text
    assert "OP_ACCESS_KEY" in response.text


def test_auth_middleware_returns_503_json_for_api_when_auth_env_missing(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "both")
    monkeypatch.delenv("OP_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    app.dependency_overrides[tasks_router.get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.get("/api/tasks/4d1bb00bdfd3")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"].startswith("AUTH misconfigured:")
