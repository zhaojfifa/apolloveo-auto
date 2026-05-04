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

    # Recovery PR-4: digital_anchor card now points at the formal create
    # route per docs/contracts/digital_anchor/new_task_route_contract_v1.md.
    expected_targets = {
        "digital_anchor": "/tasks/digital-anchor/new",
        "hot_follow": "/tasks/hot/new",
        "matrix_script": "/tasks/matrix-script/new",
        "baseline": "/tasks/baseline/new",
    }
    for line_id, href in expected_targets.items():
        assert f'data-line-id="{line_id}"' in template
        assert f'href="{href}' in template

    assert "/tasks/avatar/new" not in template
    assert "/tasks/apollo-avatar/new" not in template


def test_digital_anchor_formal_create_route_renders_template(monkeypatch):
    """Recovery PR-4: the formal /tasks/digital-anchor/new route renders
    digital_anchor_new.html. The temp /tasks/connect/digital_anchor/new
    placeholder is retired per
    docs/contracts/digital_anchor/new_task_route_contract_v1.md §3."""

    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "digital_anchor_new.html"
        return HTMLResponse(content=f"loaded:{name}", status_code=status_code, headers=headers)

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/digital-anchor/new?ui_locale=zh")
    assert response.status_code == 200
    assert "loaded:digital_anchor_new.html" in response.text


def test_temp_digital_anchor_connect_path_returns_404(monkeypatch):
    """Recovery PR-4: the /tasks/connect/digital_anchor/new placeholder is
    retired. The temp connect route only resolves for lines still listed in
    `_TEMP_CONNECTED_LINES`; digital_anchor was removed."""

    monkeypatch.setenv("AUTH_MODE", "off")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/connect/digital_anchor/new?ui_locale=zh")
    assert response.status_code == 404


def test_matrix_script_newtasks_target_uses_formal_create_entry(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    def fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        assert name == "matrix_script_new.html"
        return HTMLResponse(content=f"loaded:{name}", status_code=status_code, headers=headers)

    monkeypatch.setattr(tasks_router, "render_template", fake_render_template)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/matrix-script/new?ui_locale=zh")

    assert response.status_code == 200
    assert "loaded:matrix_script_new.html" in response.text


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


def test_temporary_connected_workbench_delivery_paths_404_after_pr4(monkeypatch):
    """Recovery PR-4: /tasks/connect/digital_anchor/workbench and /publish
    no longer have a registered line in `_TEMP_CONNECTED_LINES`, so the
    placeholder workbench / delivery surfaces return 404 for digital_anchor.
    Workbench / delivery for a created Digital Anchor task flow through
    /tasks/{task_id} and /tasks/{task_id}/publish per the new-task route
    contract `next_surfaces` block."""

    monkeypatch.setenv("AUTH_MODE", "off")
    client = TestClient(app, raise_server_exceptions=False)

    workbench = client.get("/tasks/connect/digital_anchor/workbench?ui_locale=zh")
    delivery = client.get("/tasks/connect/digital_anchor/publish?ui_locale=zh")
    assert workbench.status_code == 404
    assert delivery.status_code == 404


def test_matrix_script_temporary_create_is_removed_from_primary_path(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/tasks/connect/matrix_script/new?ui_locale=zh")

    assert response.status_code == 404


def test_matrix_script_formal_template_is_create_entry_only():
    template = (TEMPLATE_DIR / "matrix_script_new.html").read_text(encoding="utf-8")

    assert 'data-role="matrix-script-create-entry"' in template
    assert 'data-line-id="matrix_script"' in template
    for field in (
        "topic",
        "source_script_ref",
        "source_language",
        "target_language",
        "target_platform",
        "variation_target_count",
        "audience_hint",
        "tone_hint",
        "length_hint",
        "product_ref",
        "operator_notes",
    ):
        assert f'name="{field}"' in template
    assert "/debug/panels" not in template
    assert "vendor_id" not in template
    assert "model_id" not in template
    assert "provider_id" not in template
    assert "engine_id" not in template
    assert "digital_anchor" not in template


def test_matrix_script_form_post_creates_task_and_redirects_to_workbench(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")

    created = {}

    class _Repo:
        def create(self, payload):
            created.update(payload)
            return payload

        def get(self, task_id):
            if created.get("task_id") == task_id:
                return dict(created)
            return None

    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        response = client.post(
            "/tasks/matrix-script/new",
            data={
                "topic": "新品矩阵脚本",
                "source_script_ref": "content://matrix-script/source/001",
                "source_language": "zh",
                "target_language": "mm",
                "target_platform": "TikTok",
                "variation_target_count": "4",
                "audience_hint": "新用户",
                "tone_hint": "直接",
                "length_hint": "15秒",
                "product_ref": "SKU-001",
                "operator_notes": "入口备注",
            },
            follow_redirects=False,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 303
    assert response.headers["location"] == f"/tasks/{created['task_id']}?created=matrix_script"
    assert created["kind"] == "matrix_script"
    assert created["category_key"] == "matrix_script"
    assert created["platform"] == "matrix_script"
    assert created["source_url"] == "content://matrix-script/source/001"
    assert created["config"]["entry"]["topic"] == "新品矩阵脚本"
    assert created["config"]["next_surfaces"]["workbench"] == f"/tasks/{created['task_id']}"
    assert created["config"]["next_surfaces"]["delivery"] == f"/tasks/{created['task_id']}/publish"
    assert {ref["ref_id"] for ref in created["line_specific_refs"]} == {
        "matrix_script_variation_matrix",
        "matrix_script_slot_pack",
    }


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
