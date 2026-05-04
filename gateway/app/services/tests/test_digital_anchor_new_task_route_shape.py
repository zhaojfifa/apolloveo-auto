"""Route-shape tests for the formal `/tasks/digital-anchor/new` POST
endpoint (Recovery PR-4 reviewer-fail correction §9.1.1 + §9.1.2).

Authority:
- ``docs/contracts/digital_anchor/new_task_route_contract_v1.md``
- ``docs/contracts/digital_anchor/task_entry_contract_v1.md``
- ``docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md``

Tests run only when FastAPI's TestClient is importable.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest


def _try_build_client():
    try:
        from fastapi.testclient import TestClient

        from gateway.app.deps import get_task_repository
        from gateway.app.main import app
    except Exception:
        return None, None

    captured: Dict[str, Dict[str, Any]] = {}

    class _Repo:
        def create(self, payload):
            captured.update(payload)
            return payload

        def get(self, task_id):
            if captured.get("task_id") == task_id:
                return dict(captured)
            return None

    app.dependency_overrides[get_task_repository] = lambda: _Repo()
    try:
        return TestClient(app, raise_server_exceptions=False), captured
    except Exception:
        return None, None


_GOOD_FORM = {
    "topic": "数字人 demo",
    "source_script_ref": "content://digital-anchor/source/abc-001",
    "language_scope[source_language]": "en",
    "language_scope[target_language]": "zh, mm",
    "role_profile_ref": "catalog://role_card/anchor_a_v1",
    "role_framing_hint": "half_body",
    "output_intent": "双语讲解短视频",
    "speaker_segment_count_hint": "2",
}

_GOOD_JSON = {
    "topic": "数字人 demo",
    "source_script_ref": "content://digital-anchor/source/abc-001",
    "language_scope": {"source_language": "en", "target_language": ["zh", "mm"]},
    "role_profile_ref": "catalog://role_card/anchor_a_v1",
    "role_framing_hint": "half_body",
    "output_intent": "双语讲解短视频",
    "speaker_segment_count_hint": 2,
}


def test_form_post_with_language_scope_brackets_creates_task(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    client, captured = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    resp = client.post(
        "/tasks/digital-anchor/new",
        data=_GOOD_FORM,
    )
    assert resp.status_code == 303, resp.text
    assert captured.get("kind") == "digital_anchor"
    assert captured["config"]["entry"]["language_scope"]["source_language"] == "en"
    assert captured["config"]["entry"]["language_scope"]["target_language"] == [
        "zh",
        "mm",
    ]


def test_json_post_with_nested_language_scope_creates_task(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    client, captured = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    resp = client.post("/tasks/digital-anchor/new", json=_GOOD_JSON)
    assert resp.status_code == 303, resp.text
    assert captured["config"]["entry"]["language_scope"]["target_language"] == [
        "zh",
        "mm",
    ]


def test_form_post_with_unknown_field_rejected(monkeypatch):
    """Reviewer-fix #2: unknown form keys → HTTP 400 at the route boundary."""
    monkeypatch.setenv("AUTH_MODE", "off")
    client, _ = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    bad = dict(_GOOD_FORM)
    bad["vendor_id"] = "tencent"
    resp = client.post("/tasks/digital-anchor/new", data=bad)
    assert resp.status_code == 400
    assert "unknown fields" in resp.json()["detail"]


def test_form_post_with_legacy_flat_language_field_rejected(monkeypatch):
    """Reviewer-fix #1: the flat `source_language` / `target_language`
    keys are no longer accepted at the route boundary; they must arrive
    as `language_scope[source_language]` / `language_scope[target_language]`."""
    monkeypatch.setenv("AUTH_MODE", "off")
    client, _ = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    bad = dict(_GOOD_FORM)
    bad["source_language"] = "en"  # legacy flat key
    resp = client.post("/tasks/digital-anchor/new", data=bad)
    assert resp.status_code == 400


def test_json_post_with_unknown_top_level_key_rejected(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    client, _ = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    bad = dict(_GOOD_JSON)
    bad["roles"] = []  # forbidden Phase B authoring leak
    resp = client.post("/tasks/digital-anchor/new", json=bad)
    assert resp.status_code == 400


def test_json_post_with_unknown_language_scope_subkey_rejected(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "off")
    client, _ = _try_build_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable.")
    bad = dict(_GOOD_JSON)
    bad["language_scope"] = {
        "source_language": "en",
        "target_language": ["zh"],
        "vendor_id": "tencent",
    }
    resp = client.post("/tasks/digital-anchor/new", json=bad)
    assert resp.status_code == 400
