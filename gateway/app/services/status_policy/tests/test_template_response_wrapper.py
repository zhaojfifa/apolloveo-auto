from gateway.app.web import templates as templates_module


class _FakeTemplates:
    def __init__(self):
        self.calls = []

    def TemplateResponse(self, **kwargs):
        self.calls.append(kwargs)
        return kwargs


def test_render_template_uses_explicit_template_response_kwargs(monkeypatch):
    fake_templates = _FakeTemplates()
    request = object()

    monkeypatch.setattr(templates_module, "get_templates", lambda: fake_templates)
    monkeypatch.setattr(
        templates_module,
        "get_template_globals",
        lambda req: {"ui_locale": "zh", "t": "translator", "request_seen": req},
    )

    response = templates_module.render_template(
        request=request,
        name="auth_login.html",
        ctx={"next": "/tasks"},
        status_code=201,
        headers={"X-Test": "1"},
    )

    assert response["request"] is request
    assert response["name"] == "auth_login.html"
    assert response["status_code"] == 201
    assert response["headers"] == {"X-Test": "1"}
    assert response["context"]["request"] is request
    assert response["context"]["next"] == "/tasks"
    assert response["context"]["ui_locale"] == "zh"
    assert response["context"]["request_seen"] is request
