from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse

from gateway.app.deps import get_task_repository
from gateway.app.main import app
from gateway.app.routers import hot_follow_ui
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
        "digital_anchor": "/tasks/connect/digital_anchor/new",
        "hot_follow": "/tasks/hot/new",
        "matrix_script": "/tasks/connect/matrix_script/new",
        "baseline": "/tasks/baseline/new",
    }
    for line_id, href in expected_targets.items():
        assert f'data-line-id="{line_id}"' in template
        assert f'href="{href}' in template

    assert "/tasks/avatar/new" not in template
    assert "/tasks/apollo-avatar/new" not in template


def test_newtasks_temporary_connected_card_targets_load_without_disabled_avatar(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "tasks_connected_placeholder.html"
        return HTMLResponse(
            content=f"loaded:{name}:{ctx['line_id']}:{ctx['page_role']}",
            status_code=status_code,
            headers=headers,
        )

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    for line_id in ("digital_anchor", "matrix_script"):
        response = client.get(f"/tasks/connect/{line_id}/new?ui_locale=zh")

        assert response.status_code == 200
        assert f"loaded:tasks_connected_placeholder.html:{line_id}:create" in response.text
        assert "ApolloAvatar is disabled" not in response.text


def test_hot_follow_newtasks_target_uses_formal_create_entry(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "hot_follow_new.html"
        return HTMLResponse(content=f"loaded:{name}", status_code=status_code, headers=headers)

    monkeypatch.setattr(hot_follow_ui, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/hot/new?ui_locale=zh")

    assert response.status_code == 200
    assert "loaded:hot_follow_new.html" in response.text


def test_temporary_connected_lines_expose_workbench_and_delivery(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "tasks_connected_placeholder.html"
        return HTMLResponse(
            content=(
                f"{ctx['line_id']} {ctx['page_role']} 当前接通版本 "
                f"{ctx['workbench_href']} {ctx['delivery_href']}"
            ),
            status_code=status_code,
            headers=headers,
        )

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    for line_id in ("matrix_script", "digital_anchor"):
        workbench = client.get(f"/tasks/connect/{line_id}/workbench?ui_locale=zh")
        delivery = client.get(f"/tasks/connect/{line_id}/publish?ui_locale=zh")

        assert workbench.status_code == 200
        assert delivery.status_code == 200
        assert f"{line_id} workbench 当前接通版本" in workbench.text
        assert f"{line_id} delivery 当前接通版本" in delivery.text


def test_hot_follow_task_chain_uses_formal_workbench_and_delivery(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    class _Repo:
        def get(self, task_id):
            assert task_id == "hf-connected"
            return {
                "task_id": "hf-connected",
                "kind": "hot_follow",
                "category_key": "hot_follow",
                "platform": "hot_follow",
                "title": "Hot Follow Connected",
                "status": "processing",
            }

    def fake_workbench_context(*args, **kwargs):
        return {"task": {"task_id": "hf-connected"}, "task_json": {"task_id": "hf-connected"}}

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        return HTMLResponse(content=f"loaded:{name}", status_code=status_code, headers=headers)

    monkeypatch.setattr(tasks_router, "_build_task_workbench_page_context", fake_workbench_context)
    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        workbench = client.get("/tasks/hf-connected?ui_locale=zh")
        delivery = client.get("/tasks/hf-connected/publish?ui_locale=zh")
    finally:
        app.dependency_overrides.clear()

    assert workbench.status_code == 200
    assert delivery.status_code == 200
    assert "loaded:hot_follow_workbench.html" in workbench.text
    assert "loaded:hot_follow_publish.html" in delivery.text
