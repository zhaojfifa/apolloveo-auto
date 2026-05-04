"""Asset Supply surface-boundary integrity tests
(Operator Capability Recovery, PR-2).

Authority:
- ``docs/product/broll_asset_supply_freeze_v1.md`` §0 "Boundary"
- ``docs/contracts/asset_library_object_contract_v1.md`` §"Forbidden"
- ``docs/contracts/promote_request_contract_v1.md`` §"Forbidden"
- ``docs/contracts/promote_feedback_closure_contract_v1.md`` §"Forbidden"

These tests prove the surface boundary: Asset Supply is distinct from
Task Area / Tool Backstage; no vendor / model / provider / engine
identifier reaches any returned object; the asset library is read-only
across line packets (no packet-truth mutation path); the promote intent
returns request_id only and never the asset object synchronously.

Discipline: import-light. No FastAPI app instantiation; the router
module is imported only to assert URL-prefix discipline.
"""
from __future__ import annotations

import pytest

from gateway.app.services.asset import (
    FORBIDDEN_ASSET_KEYS,
    FORBIDDEN_PROMOTE_KEYS,
    PromoteRequestRejected,
    get_closure,
    list_assets,
    reset_store_for_tests,
    submit_promote_request,
)


@pytest.fixture(autouse=True)
def _reset_store():
    reset_store_for_tests()
    yield
    reset_store_for_tests()


# ---------- Surface URL distinct from Task Area / Tool Backstage ---------


def test_asset_router_prefix_is_distinct_from_task_and_admin() -> None:
    """The Asset Supply router MUST mount under `/assets` and
    `/api/assets`, never under `/tasks*` (Task Area) or `/admin/*` /
    `/tools/*` (Tool Backstage). Hard-asserted to prevent accidental
    surface merge during refactor.
    """
    from gateway.app.routers import assets as assets_router

    page_prefix = assets_router.page_router.prefix
    api_prefix = assets_router.api_router.prefix
    assert page_prefix == "/assets"
    assert api_prefix == "/api/assets"
    assert not page_prefix.startswith("/tasks")
    assert not page_prefix.startswith("/admin")
    assert not page_prefix.startswith("/tools")
    assert not api_prefix.startswith("/api/tasks")
    assert not api_prefix.startswith("/admin")


def test_asset_router_has_no_packet_mutation_path() -> None:
    """Asset Supply MUST NOT expose any path that mutates packet truth.

    The contract requires assets to be read-only across line packets;
    any future endpoint with a packet-mutation verb on the assets
    surface would violate the freeze §0 boundary. We assert the
    declared paths are all on the assets surface AND that no path name
    contains the words `packet`, `task`, `compose`, or `publish` —
    those would indicate a leak across surface boundary.
    """
    from gateway.app.routers import assets as assets_router

    forbidden_path_substrings = ("/packet", "/task", "/compose", "/publish", "/admin")
    for route in list(assets_router.page_router.routes) + list(assets_router.api_router.routes):
        path = getattr(route, "path", "")
        for needle in forbidden_path_substrings:
            assert needle not in path, (
                f"Asset Supply route {path!r} crosses surface boundary "
                f"(contains forbidden substring {needle!r})"
            )


# ---------- No vendor/model identifier reaches operator-visible output ---


def test_list_assets_carries_no_forbidden_vendor_model_keys() -> None:
    for asset in list_assets(include_unsurfaced=True):

        def walk(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    assert key not in FORBIDDEN_ASSET_KEYS, (
                        f"forbidden asset key {key!r} leaked"
                    )
                    walk(value)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(asset)


def test_promote_closure_carries_no_forbidden_vendor_model_keys() -> None:
    payload = {
        "artifact_ref": "artifact://hot_follow/test/final.mp4",
        "target_kind": "broll",
        "target_tags": [{"facet": "line", "value": "hot_follow"}],
        "target_line_availability": ["hot_follow"],
        "license_metadata": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "source": "task_artifact_promote",
        },
        "proposed_title": "Test",
        "requested_by": "operator:test",
    }
    result = submit_promote_request(payload)
    closure = get_closure(result["request_id"])
    assert closure is not None

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                assert key not in FORBIDDEN_PROMOTE_KEYS, (
                    f"forbidden promote key {key!r} leaked into closure"
                )
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(closure)


# ---------- Promote returns request_id only, never asset_id sync ---------


def test_submit_response_never_returns_asset_object_synchronously() -> None:
    """Per `promote_request_contract_v1.md` §"Submit-time discipline" 7:
    submit returns request_id only; the asset id is materialized only
    after the closure transitions to `approved`.
    """
    payload = {
        "artifact_ref": "artifact://hot_follow/test/final.mp4",
        "target_kind": "broll",
        "target_tags": [{"facet": "line", "value": "hot_follow"}],
        "target_line_availability": ["hot_follow"],
        "license_metadata": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "source": "task_artifact_promote",
        },
        "proposed_title": "Test",
        "requested_by": "operator:test",
    }
    result = submit_promote_request(payload)
    forbidden = {"asset_id", "resulting_asset_id", "asset_object", "asset"}
    assert not (set(result.keys()) & forbidden)


# ---------- Closure boundary: source artifact never mutated --------------


def test_closure_does_not_carry_artifact_payload_or_packet_truth() -> None:
    """Per closure contract §"Boundary": the closure references the
    source artifact by handle only and never embeds artifact payload or
    packet truth.
    """
    payload = {
        "artifact_ref": "artifact://hot_follow/test/final.mp4",
        "target_kind": "broll",
        "target_tags": [{"facet": "line", "value": "hot_follow"}],
        "target_line_availability": ["hot_follow"],
        "license_metadata": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "source": "task_artifact_promote",
        },
        "proposed_title": "Test",
        "requested_by": "operator:test",
    }
    result = submit_promote_request(payload)
    closure = get_closure(result["request_id"])
    assert closure is not None
    forbidden_top_level = {
        "packet",
        "ready_gate",
        "current_attempt",
        "deliverables",
        "publishable",
        "artifact_payload",
        "artifact_blob",
    }
    assert not (set(closure.keys()) & forbidden_top_level)


# ---------- Operator-visible asset surface integrity ---------------------


def test_assets_template_exists_on_disk() -> None:
    """The operator-visible page MUST exist as a real template file —
    not a dynamic placeholder synthesized at render time.
    """
    from pathlib import Path

    template_path = (
        Path(__file__).resolve().parents[3] / "app" / "templates" / "assets.html"
    )
    assert template_path.exists(), f"missing operator-visible page template: {template_path}"
    contents = template_path.read_text(encoding="utf-8")
    # Operator-visible label is the surface name; a placeholder-only
    # page would not name the surface or describe its boundary.
    assert "Asset Supply" in contents
    assert "promote_feedback_closure_contract_v1" in contents


def test_assets_template_has_no_vendor_model_strings() -> None:
    """The page template MUST NOT contain any vendor/model/provider/
    engine identifier in plain text (defense-in-depth against
    template-side leaks).
    """
    from pathlib import Path

    template_path = (
        Path(__file__).resolve().parents[3] / "app" / "templates" / "assets.html"
    )
    contents = template_path.read_text(encoding="utf-8").lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in contents, f"{forbidden!r} leaked into assets.html template"
