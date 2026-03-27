from pathlib import Path
import sys
import types

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
try:
    import pydantic_settings as _pydantic_settings  # noqa: F401
except Exception:
    shim = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        model_config = {"extra": "ignore"}

    shim.BaseSettings = _BaseSettings
    sys.modules["pydantic_settings"] = shim


def test_hot_follow_new_routes_render_without_template_signature_error():
    from gateway.app.routers import hot_follow_ui

    app = FastAPI()

    calls = []

    def _fake_render_template(*, request, name, ctx=None, status_code=200, headers=None):
        _ = (request, headers)
        calls.append({"name": name, "ctx": dict(ctx or {}), "status_code": status_code})
        return HTMLResponse("<div id='hf-create'></div>", status_code=status_code)

    hot_follow_ui.render_template = _fake_render_template
    app.include_router(hot_follow_ui.router)

    with TestClient(app) as client:
        res_primary = client.get("/tasks/hot/new")
        res_locale = client.get("/tasks/hot/new?ui_locale=zh")

    assert res_primary.status_code == 200
    assert res_locale.status_code == 200
    assert "hf-create" in res_primary.text
    assert "hf-create" in res_locale.text
    assert len(calls) == 2
    assert all(call["name"] == "hot_follow_new.html" for call in calls)
    assert all("language_profiles" in call["ctx"] for call in calls)
