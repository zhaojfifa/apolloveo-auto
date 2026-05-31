"""Matrix Script ingest auth/JSON-boundary P0 fix — scoped regression tests.

Covers the 2026-05-30 P0 fix on branch
``fix/veomatrixvoice05-ms-ingest-auth-json-boundary-20260530``.

Bug: on ``/tasks/matrix-script/new`` the frontend fetch to
``POST /tasks/matrix-script/source-script-refs/ingest`` received the HTML
login page (302 → ``<!doctype html>``) when the session had expired, so
``response.json()`` failed with "Unexpected token '<'". Secondary bug: the
login page derived ``nextUrl`` from an unsafe ``next`` that pointed at the
POST-only ingest endpoint.

Fix (defense in depth):
  A. Frontend guards on status/redirected/content-type before ``resp.json()``.
  B. Middleware returns 401 JSON (``auth_required``) for JSON/XHR callers under
     non-/api paths instead of a 302 to HTML.
  C. ``/auth/login`` sanitizes ``next`` via ``_safe_next``.

These tests assert the fix WITHOUT changing the Matrix Script POST contract,
the source_script_ref scheme, any packet, schema, or closed enum.
"""

from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from gateway.app.main import app, _safe_next
from gateway.app.services.matrix_script.source_script_ref_minting import (
    MATRIX_SCRIPT_INGEST_ROUTE,
)


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_TEMPLATES = _REPO_ROOT / "gateway" / "app" / "templates"
_NEW_TASK_TEMPLATE = _TEMPLATES / "matrix_script_new.html"


def _both_mode_env(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "both")
    monkeypatch.setenv("OP_ACCESS_KEY", "test-op-key")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")


def _header_mode_env(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "header")
    monkeypatch.setenv("OP_ACCESS_KEY", "test-op-key")
    monkeypatch.delenv("SESSION_SECRET", raising=False)


# ---------------------------------------------------------------------------
# (1) Unauthenticated ingest with Accept: application/json → 401 JSON, NOT 302.
# ---------------------------------------------------------------------------
def test_unauthenticated_ingest_returns_401_json_not_302_html(monkeypatch):
    _both_mode_env(monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        MATRIX_SCRIPT_INGEST_ROUTE,
        headers={"Accept": "application/json"},
        json={"source_kind": "operator_paste", "body": "脚本正文"},
        follow_redirects=False,
    )
    assert resp.status_code == 401
    assert resp.status_code != 302
    payload = resp.json()
    assert payload["ok"] is False
    assert payload["error"] == "auth_required"
    assert payload["message"] == "登录已失效，请重新登录后再提交脚本。"


# ---------------------------------------------------------------------------
# (2) The 401 body is JSON — it must NOT be the HTML login document.
# ---------------------------------------------------------------------------
def test_unauthenticated_ingest_body_is_not_html_doctype(monkeypatch):
    _both_mode_env(monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        MATRIX_SCRIPT_INGEST_ROUTE,
        headers={"Accept": "application/json"},
        json={"source_kind": "operator_paste", "body": "脚本正文"},
        follow_redirects=False,
    )
    assert not resp.text.lstrip().lower().startswith("<!doctype")
    assert "application/json" in resp.headers.get("content-type", "").lower()


# ---------------------------------------------------------------------------
# (3) Frontend JS guards before resp.json() — source-level assertion.
# ---------------------------------------------------------------------------
def test_frontend_does_not_call_json_blindly_on_redirect_or_html():
    src = _NEW_TASK_TEMPLATE.read_text(encoding="utf-8")
    # The auth/redirect/html guard must appear, and it must short-circuit
    # (throw) before any resp.json() is reached.
    assert "resp.redirected" in src
    assert "text/html" in src
    assert "resp.status === 401" in src and "resp.status === 403" in src
    guard_idx = src.index("resp.redirected")
    # Anchor on the actual JSON-parse call (not the explanatory comment).
    json_idx = src.index("return resp.json().then")
    assert guard_idx < json_idx, "redirect/html guard must precede resp.json()"
    assert "登录已失效，请重新登录后再提交脚本。" in src


# ---------------------------------------------------------------------------
# (4) Login default nextUrl is never the ingest endpoint.
# ---------------------------------------------------------------------------
def test_login_default_next_is_not_ingest_endpoint(monkeypatch):
    _both_mode_env(monkeypatch)
    # _safe_next neutralizes a malicious/incorrect ingest next.
    assert _safe_next(MATRIX_SCRIPT_INGEST_ROUTE) == "/tasks"
    assert _safe_next("") == "/tasks"
    assert _safe_next(None) == "/tasks"  # type: ignore[arg-type]

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(
        f"/auth/login?next={MATRIX_SCRIPT_INGEST_ROUTE}",
        follow_redirects=False,
    )
    assert resp.status_code == 200
    assert MATRIX_SCRIPT_INGEST_ROUTE not in resp.text


# ---------------------------------------------------------------------------
# (5) next sanitization rejects external + protocol-relative URLs.
# ---------------------------------------------------------------------------
def test_safe_next_rejects_external_and_unsafe_targets():
    assert _safe_next("https://evil.example.com/x") == "/tasks"
    assert _safe_next("//evil.example.com") == "/tasks"
    assert _safe_next("http://evil.example.com") == "/tasks"
    assert _safe_next("/tasks/matrix-script/source-script-refs/mint") == "/tasks"
    assert _safe_next("/api/auth/login") == "/tasks"
    assert _safe_next("javascript:alert(1)") == "/tasks"
    # A legitimate same-origin operator path is preserved.
    assert _safe_next("/tasks/matrix-script/new?ui_locale=zh") == (
        "/tasks/matrix-script/new?ui_locale=zh"
    )


# ---------------------------------------------------------------------------
# (6) Authenticated ingest with operator_paste + body returns valid JSON.
# ---------------------------------------------------------------------------
def test_authenticated_ingest_returns_valid_json_envelope(monkeypatch):
    _header_mode_env(monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        MATRIX_SCRIPT_INGEST_ROUTE,
        headers={"Accept": "application/json", "X-OP-KEY": "test-op-key"},
        json={"source_kind": "operator_paste", "body": "美女手中捧着一碗番茄。"},
        follow_redirects=False,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload.get("source_script_ref"), str)
    assert payload["source_script_ref"].startswith("content://matrix-script/source/")
    assert payload.get("has_body") is True
    assert payload.get("body_char_count", 0) > 0


# ---------------------------------------------------------------------------
# (7) Matrix Script New Task keeps the five-card structure + CTA.
# ---------------------------------------------------------------------------
def test_new_task_five_card_structure_and_cta_preserved():
    src = _NEW_TASK_TEMPLATE.read_text(encoding="utf-8")
    for anchor in (
        "ms-new-card-source",
        "ms-new-card-product-material",
        "ms-new-card-target-aspect-language",
        "ms-new-card-role-voice-subtitle",
        "ms-new-card-variant-strategy",
    ):
        assert anchor in src, f"missing card anchor {anchor}"
    assert 'data-role="ms-new-submit"' in src
    assert "生成视频方案" in src


# ---------------------------------------------------------------------------
# (8) No VoiceTrans iframe / raw embed in the New Task page.
# ---------------------------------------------------------------------------
def test_no_voicetrans_iframe_or_raw_embed():
    src = _NEW_TASK_TEMPLATE.read_text(encoding="utf-8")
    assert "<iframe" not in src.lower()


# ---------------------------------------------------------------------------
# (9) Ingest POST contract / scheme unchanged (no packet/schema/enum drift).
# ---------------------------------------------------------------------------
def test_ingest_contract_and_scheme_unchanged():
    # The route constant must remain the documented value.
    assert (
        MATRIX_SCRIPT_INGEST_ROUTE
        == "/tasks/matrix-script/source-script-refs/ingest"
    )
    # The frontend still posts the exact preserved payload shape.
    src = _NEW_TASK_TEMPLATE.read_text(encoding="utf-8")
    assert "body: body" in src or "body: JSON.stringify" in src
    assert "source_kind: sourceKind" in src
    assert "operator_paste" in src
    assert "operator_upload" in src
