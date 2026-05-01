from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse

from gateway.app.main import app
from gateway.app.routers import tasks as tasks_router


TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def test_tasks_board_primary_new_task_link_targets_newtasks():
    template = (TEMPLATE_DIR / "tasks.html").read_text(encoding="utf-8")

    assert 'href="/tasks/newtasks"' in template


def test_newtasks_route_renders_frozen_line_ids(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    template = (TEMPLATE_DIR / "tasks_newtasks.html").read_text(encoding="utf-8")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "tasks_newtasks.html"
        return HTMLResponse(content=template, status_code=status_code, headers=headers)

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/newtasks")

    assert response.status_code == 200
    assert 'data-role="operator-new-tasks"' in response.text
    assert "hot_follow" in response.text
    assert "matrix_script" in response.text
    assert "digital_anchor" in response.text


def test_newtasks_template_no_longer_uses_legacy_scene_wizard_semantics():
    template = (TEMPLATE_DIR / "tasks_newtasks.html").read_text(encoding="utf-8")

    assert "/tasks/avatar/new" not in template
    assert "/tasks/hot/new" not in template
    assert "/tasks/baseline/new" not in template
    assert "tasks.scene.avatar" not in template
    assert "tasks.scene.hot" not in template
    assert "tasks.scene.baseline" not in template
    assert ">AVATAR<" not in template
    assert ">HOT<" not in template
    assert ">BASELINE<" not in template
