from fastapi.testclient import TestClient

from gateway.app.main import app


def test_auth_login_route_renders_without_jinja2():
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/auth/login?next=/tasks")

    assert response.status_code == 200
    assert "Operator Login" in response.text
    assert 'const nextUrl = "/tasks";' in response.text
