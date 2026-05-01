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


def test_tasks_board_uses_unified_line_taxonomy():
    template = (TEMPLATE_DIR / "tasks.html").read_text(encoding="utf-8")

    for line_id in ("hot_follow", "matrix_script", "digital_anchor", "baseline"):
        assert f'"id": "{line_id}"' in template
        assert f'data-line="{{{{ line.id }}}}"' in template

    assert "热点跟拍" in template
    assert "矩阵脚本" in template
    assert "数字人IP" in template
    assert "基础剪辑" in template
    assert 'data-scene="' not in template
    assert 'dataset.scene' not in template
    assert "tasks.filter.scene.avatar" not in template


def test_newtasks_route_renders_card_based_line_selection(monkeypatch):
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
    assert 'data-surface="card-line-selection"' in response.text
    assert "hot_follow" in response.text
    assert "matrix_script" in response.text
    assert "digital_anchor" in response.text
    assert "baseline" in response.text
    assert "热点跟拍" in response.text
    assert "矩阵脚本" in response.text
    assert "数字人IP" in response.text
    assert "基础剪辑" in response.text


def test_newtasks_template_is_selection_only_not_workbench_like():
    template = (TEMPLATE_DIR / "tasks_newtasks.html").read_text(encoding="utf-8")

    assert "/tasks/newtasks" in (TEMPLATE_DIR / "tasks.html").read_text(encoding="utf-8")
    assert "wizard-wrap" in template
    assert "wizard-card" in template
    assert "icon-box" in template
    assert "text-4xl font-bold tracking-tight" in template
    assert "grid grid-cols-1 gap-6 md:grid-cols-3" in template
    assert "shadow-sm ring-1 ring-gray-200" in template
    assert "rounded-2xl p-6" in template
    assert "uppercase tracking-wide" in template
    assert "开始创建" in template
    assert 't("tasks.wizard.hint_title")' in template
    assert "tasks.scene.avatar" not in template
    assert "tasks.scene.hot" not in template
    assert "tasks.scene.baseline" not in template
    assert ">AVATAR<" not in template
    assert ">HOT<" not in template
    assert "target_language" not in template
    assert "helper_translation" not in template
    assert "generic_refs" not in template
    assert "line_specific_refs" not in template
    assert "Envelope completeness" not in template
    assert "<input" not in template
    assert "<textarea" not in template
    assert "line-card" not in template
    assert "newtasks-header" not in template
    assert "page-shell" not in template


def test_newtasks_card_links_target_active_create_route():
    template = (TEMPLATE_DIR / "tasks_newtasks.html").read_text(encoding="utf-8")

    expected_targets = {
        "digital_anchor": "/tasks/new?line=digital_anchor",
        "hot_follow": "/tasks/new?line=hot_follow",
        "matrix_script": "/tasks/new?line=matrix_script",
        "baseline": "/tasks/new?line=baseline",
    }
    for line_id, href in expected_targets.items():
        assert f'data-line-id="{line_id}"' in template
        assert f'href="{href}' in template

    assert "/tasks/avatar/new" not in template
    assert "/tasks/apollo-avatar/new" not in template
    assert "/tasks/hot/new" not in template
    assert "/tasks/baseline/new" not in template


def test_newtasks_card_targets_load_without_disabled_avatar(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "tasks_new.html"
        return HTMLResponse(content=f"loaded:{name}", status_code=status_code, headers=headers)

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    for line_id in ("digital_anchor", "hot_follow", "matrix_script", "baseline"):
        response = client.get(f"/tasks/new?line={line_id}&ui_locale=zh")

        assert response.status_code == 200
        assert "loaded:tasks_new.html" in response.text
        assert "ApolloAvatar is disabled" not in response.text
