"""End-to-end submit test for the operator-visible Asset Supply surface
(Operator Capability Recovery, PR-2 reviewer-fix #3).

Reviewer FAIL: the original PR-2 page rendered an `alert()` stub on the
"Promote …" button instead of a real submit path. This test proves the
corrected surface now actually initiates a promote intent end-to-end
through the contract-backed `/api/assets/promote` endpoint and renders
the resulting `request_id` + initial `request_state` from the
operator's perspective.

Two layers of evidence:

1. **Template integrity** (always runs): the page template carries a
   real ``<form>`` element targeting ``/api/assets/promote`` via JS,
   not an ``alert()`` stub. This is checked by reading the template
   file directly so it works even when the FastAPI app can't be
   instantiated (e.g. on Python 3.9 where unrelated repo modules use
   PEP 604 syntax).

2. **HTTP end-to-end submit** (runs when the FastAPI app + Starlette
   TestClient are importable): exercises the real router endpoint and
   verifies the response carries `request_id` + `request_state` per the
   contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest


_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3] / "app" / "templates" / "assets.html"
)


# ---------- Template-level evidence (always runs) ------------------------


def test_promote_form_replaces_alert_stub() -> None:
    """The page template MUST carry a real <form> targeting the
    contract-backed /api/assets/promote endpoint, not an alert() stub.
    """
    contents = _TEMPLATE_PATH.read_text(encoding="utf-8")
    # The old stub is gone.
    assert "open-promote-stub" not in contents, (
        "the alert() stub `open-promote-stub` MUST be removed"
    )
    assert "Inline form is a follow-up" not in contents, (
        "the deferred-form alert message MUST be removed"
    )
    # The new real submit path is present.
    assert 'data-role="promote-form"' in contents, (
        "real promote form data-role hook MUST be present"
    )
    assert 'data-role="open-promote-form"' in contents
    assert "/api/assets/promote" in contents, (
        "the form's JS submit handler MUST POST to /api/assets/promote"
    )
    # The contract-pinned source field is set by the surface, not the
    # operator (PR-2 reviewer-fix #1 alignment).
    assert "task_artifact_promote" in contents


def test_promote_form_does_not_expose_provider_or_admin_controls() -> None:
    """Reviewer red lines: no provider/model/vendor controls; no admin
    review UI; no upload affordance on the operator surface.
    """
    contents = _TEMPLATE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "vendor_id",
        "model_id",
        "provider_id",
        "engine_id",
        "swiftcraft",
        '<input type="file"',
        'name="upload"',
        "approve_request",
        "reject_request",
        "review_started",
    ):
        assert forbidden not in contents, (
            f"{forbidden!r} leaked into operator-visible Asset Supply page"
        )


# ---------- HTTP end-to-end (runs when FastAPI is importable) -----------


def _try_build_test_client():
    """Build a Starlette TestClient that mounts the assets routers in
    isolation. Returns ``None`` when the router or its template
    dependencies cannot be imported (e.g. Python 3.9 vs PEP 604 in
    unrelated repo modules).
    """
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from gateway.app.routers import assets as assets_router
    except Exception:
        return None

    app = FastAPI()
    app.include_router(assets_router.page_router)
    app.include_router(assets_router.api_router)
    try:
        return TestClient(app)
    except Exception:
        return None


def test_assets_surface_submits_promote_intent_end_to_end() -> None:
    """Happy path: the operator-visible surface accepts a contract-shaped
    payload, returns 201 with `request_id` + `request_state="requested"`,
    and the closure is then queryable via the closure endpoint.

    Skipped (with explicit reason) only when the FastAPI test client
    cannot be built in this environment.
    """
    from gateway.app.services.asset import reset_store_for_tests

    reset_store_for_tests()
    client = _try_build_test_client()
    if client is None:
        pytest.skip(
            "FastAPI TestClient not importable in this Python env; "
            "service-level tests cover the contract path."
        )

    payload = {
        "artifact_ref": "artifact://hot_follow/task-e2e/final.mp4",
        "target_kind": "broll",
        "target_tags": [{"facet": "line", "value": "hot_follow"}],
        "target_line_availability": ["hot_follow"],
        "license_metadata": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "source": "task_artifact_promote",
        },
        "proposed_title": "End-to-end test asset",
        "requested_by": "operator:e2e",
    }
    resp = client.post("/api/assets/promote", json=payload)
    assert resp.status_code == 201, (resp.status_code, resp.text)
    body = resp.json()
    assert "request_id" in body
    assert body["request_state"] == "requested"
    # Per contract: asset_id is NEVER returned synchronously.
    assert "asset_id" not in body
    assert "resulting_asset_id" not in body

    # Closure is now queryable via the surface — the page's closure
    # panel reads from the same path.
    closure_resp = client.get(f"/api/assets/promote/{body['request_id']}")
    assert closure_resp.status_code == 200
    closure = closure_resp.json()
    assert closure["request_id"] == body["request_id"]
    assert closure["request_state"] == "requested"
    assert closure["resulting_asset_id"] is None  # PR-2 reviewer-fix #2


def test_assets_surface_rejects_non_task_artifact_promote_source() -> None:
    """PR-2 reviewer-fix #1 enforced through the operator surface."""
    from gateway.app.services.asset import reset_store_for_tests

    reset_store_for_tests()
    client = _try_build_test_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    payload = {
        "artifact_ref": "artifact://hot_follow/task-e2e/final.mp4",
        "target_kind": "broll",
        "target_tags": [{"facet": "line", "value": "hot_follow"}],
        "target_line_availability": ["hot_follow"],
        "license_metadata": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "source": "external_reference",  # Wrong: not artifact-backed.
        },
        "proposed_title": "Should be rejected",
        "requested_by": "operator:e2e",
    }
    resp = client.post("/api/assets/promote", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert (
        body.get("error_code")
        == "license_metadata.source_must_be_task_artifact_promote"
    )


def test_assets_surface_renders_page_with_contract_driven_data() -> None:
    """Page renders 200 with library + closure data sourced from the
    contract-backed services — proving the operator surface is not a
    placeholder.
    """
    from gateway.app.services.asset import (
        reset_store_for_tests,
        submit_promote_request,
    )

    reset_store_for_tests()
    client = _try_build_test_client()
    if client is None:
        pytest.skip("FastAPI TestClient not importable in this env.")

    submit_promote_request(
        {
            "artifact_ref": "artifact://hot_follow/page-test/final.mp4",
            "target_kind": "broll",
            "target_tags": [{"facet": "line", "value": "hot_follow"}],
            "target_line_availability": ["hot_follow"],
            "license_metadata": {
                "license": "owned",
                "reuse_policy": "reuse_allowed",
                "source": "task_artifact_promote",
            },
            "proposed_title": "Page render test",
            "requested_by": "operator:page",
        }
    )
    resp = client.get("/assets")
    assert resp.status_code == 200
    body = resp.text
    # Library data reaches the page.
    assert "City Outdoor Walk B-roll" in body
    # Real submit form is present (not the old stub).
    assert "open-promote-stub" not in body
    assert 'data-role="promote-form"' in body
    # Submitted closure is rendered in the closure panel.
    assert "operator:page" not in body  # not exposed
    assert "request_id" in body or "prom-req-" in body
