"""Matrix Script — initial-preview-status polling auth regression (BLOCKED_AUTH_POLLING fix).

The deployed operator page polled ``GET /api/matrix-script/{task_id}/initial-preview-status``
and got repeated 401s while the page itself loaded — leaving it stuck at "主视频预览生成中".

Root cause (proven by these tests): the poll endpoint shares the app auth middleware with the
task page, so it accepts BOTH the ``X-OP-KEY`` header AND the ``op_session`` cookie — but the
browser ``fetch`` omitted ``credentials``, so the session cookie was not sent and the request
was unauthenticated (401). The fix sends ``credentials: 'same-origin'`` on the poller fetch.

These tests pin: (1) no-auth → 401; (2) header auth → 200; (3) **session-cookie auth → 200, not
401** (the regression — the exact seam the page already uses); (4) the template poller fetches
send credentials so the browser actually transmits the cookie. No provider / schema / contract /
delivery-truth change.
"""
from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from gateway.app.deps import get_task_repository
from gateway.app.main import app

_KEY = "test-op-key-abc123"
_SECRET = "test-session-secret-xyz789"
_TASK = {"task_id": "auth-poll-1", "kind": "matrix_script", "config": {}}
_URL = f"/api/matrix-script/{_TASK['task_id']}/initial-preview-status"


class _Repo:
    def get(self, task_id):
        return dict(_TASK) if task_id == _TASK["task_id"] else None


def _auth_client(monkeypatch) -> TestClient:
    # auth_mode=both so BOTH header and session-cookie auth are live (mirrors deploy).
    monkeypatch.setenv("AUTH_MODE", "both")
    monkeypatch.setenv("OP_ACCESS_KEY", _KEY)
    monkeypatch.setenv("SESSION_SECRET", _SECRET)
    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    # https base_url so the Secure op_session cookie is actually sent on later requests
    # (a Secure cookie is dropped over http — exactly the deployment is HTTPS).
    return TestClient(app, base_url="https://testserver")


def test_initial_preview_status_401_without_auth(monkeypatch) -> None:
    client = _auth_client(monkeypatch)
    try:
        r = client.get(_URL, headers={"Accept": "application/json"})
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_initial_preview_status_authes_via_header(monkeypatch) -> None:
    client = _auth_client(monkeypatch)
    try:
        r = client.get(_URL, headers={"X-OP-KEY": _KEY, "Accept": "application/json"})
        assert r.status_code == 200, r.status_code
        body = r.json()
        assert body.get("official_publish_ready") is False
        assert "status" in body and "poll" in body
    finally:
        app.dependency_overrides.clear()


def test_initial_preview_status_authes_via_session_cookie(monkeypatch) -> None:
    """REGRESSION: the operator page authenticates via the op_session cookie; the poll
    endpoint must accept that SAME cookie. Before the fix the browser fetch dropped the
    cookie (no credentials) and got 401; here we prove the seam itself accepts the cookie."""
    client = _auth_client(monkeypatch)
    try:
        login = client.post("/api/auth/login", json={"username": "ops", "key": _KEY})
        assert login.status_code == 200, login.status_code
        assert "op_session" in client.cookies
        # The page authenticates with this cookie...
        page = client.get(f"/tasks/{_TASK['task_id']}", follow_redirects=False)
        assert page.status_code == 200, ("page should auth via cookie", page.status_code)
        # ...and so must the poll endpoint (same middleware) — NOT 401.
        r = client.get(_URL, headers={"Accept": "application/json"})
        assert r.status_code == 200, ("poll must accept the session cookie", r.status_code)
        assert r.json().get("official_publish_ready") is False
    finally:
        app.dependency_overrides.clear()


def test_poller_fetches_send_credentials_same_origin() -> None:
    """The browser poller must send the session cookie, or the deployed page 401s and
    stays '生成中'. Assert the broken no-credentials pattern is gone and both pollers
    (initial-preview + regen) send credentials."""
    html = pathlib.Path("gateway/app/templates/task_workbench.html").read_text(encoding="utf-8")
    assert "initial-preview-status" in html
    # The old broken pattern (fetch on statusUrl with only headers) must not remain.
    assert "fetch(statusUrl, { headers: { 'Accept': 'application/json' } })" not in html
    # Both pollers now explicitly send same-origin credentials (the session cookie).
    assert html.count("credentials: 'same-origin'") >= 2
