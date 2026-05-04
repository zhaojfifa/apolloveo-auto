"""Asset library read-only service tests
(Operator Capability Recovery, PR-2).

Authority:
- ``docs/contracts/asset_library_object_contract_v1.md``
- ``docs/product/broll_asset_supply_freeze_v1.md`` §1 (filter taxonomy)

Discipline: import-light. Tests the service module directly without
instantiating the FastAPI app or any router. Closed enums (kind, facet,
license, reuse_policy, quality_threshold, line_availability) are
asserted against the contract.
"""
from __future__ import annotations

import pytest

from gateway.app.services.asset import (
    FORBIDDEN_ASSET_KEYS,
    get_asset,
    list_assets,
    list_known_kinds,
    list_known_lines,
    list_known_quality_buckets,
    list_known_quality_threshold_values,
    reference_asset,
)
from gateway.app.services.asset.seed_data import (
    ASSET_KIND_ENUM,
    LINE_AVAILABILITY_ENUM,
    QUALITY_FILTER_BUCKET_ENUM,
)


# ---------- Schema conformance --------------------------------------------


_REQUIRED_TOP_LEVEL_FIELDS = {
    "asset_id",
    "kind",
    "line_availability",
    "tags",
    "provenance",
    "version",
    "quality_threshold",
    "quality",
    "usage_limits",
    "title",
    "created_at",
    "created_by",
    "badges",
}


def test_every_listed_asset_has_required_fields() -> None:
    for asset in list_assets(include_unsurfaced=True):
        missing = _REQUIRED_TOP_LEVEL_FIELDS - set(asset.keys())
        assert not missing, f"asset {asset.get('asset_id')!r} missing fields {missing}"


def test_every_kind_is_in_closed_enum() -> None:
    for asset in list_assets(include_unsurfaced=True):
        assert asset["kind"] in ASSET_KIND_ENUM


def test_every_line_availability_value_is_in_closed_enum() -> None:
    for asset in list_assets(include_unsurfaced=True):
        for line in asset["line_availability"]:
            assert line in LINE_AVAILABILITY_ENUM


def test_known_helpers_return_closed_sets() -> None:
    assert set(list_known_kinds()) == ASSET_KIND_ENUM
    assert set(list_known_lines()) == LINE_AVAILABILITY_ENUM
    assert set(list_known_quality_buckets()) == QUALITY_FILTER_BUCKET_ENUM
    assert set(list_known_quality_threshold_values()) == {"draft", "review", "approved"}


# ---------- Filter behavior ----------------------------------------------


def test_default_list_hides_draft_assets() -> None:
    surfaced = list_assets()
    for asset in surfaced:
        assert asset["quality_threshold"] != "draft"


def test_include_unsurfaced_returns_drafts_too() -> None:
    all_assets = list_assets(include_unsurfaced=True)
    surfaced = list_assets()
    assert len(all_assets) > len(surfaced)
    assert any(a["quality_threshold"] == "draft" for a in all_assets)


def test_filter_by_line_returns_only_matching_assets() -> None:
    for line in LINE_AVAILABILITY_ENUM:
        result = list_assets(line=line)
        for asset in result:
            assert line in asset["line_availability"], asset["asset_id"]


def test_filter_by_kind_returns_only_matching_assets() -> None:
    result = list_assets(kind="role_ref")
    assert len(result) >= 1
    for asset in result:
        assert asset["kind"] == "role_ref"


def test_filter_by_quality_bucket_lower_bound() -> None:
    # `>=0.75` is "approved only" per the freeze §1 lower-bound mapping.
    only_approved = list_assets(quality_filter=">=0.75", include_unsurfaced=True)
    for asset in only_approved:
        assert asset["quality_threshold"] == "approved"


def test_facet_value_filter_matches_tag_pair() -> None:
    result = list_assets(facet_values={"line": "matrix_script"})
    assert len(result) >= 1
    for asset in result:
        tag_pairs = {(t["facet"], t["value"]) for t in asset["tags"]}
        assert ("line", "matrix_script") in tag_pairs


def test_unknown_line_raises() -> None:
    with pytest.raises(ValueError):
        list_assets(line="not_a_real_line")


def test_unknown_kind_raises() -> None:
    with pytest.raises(ValueError):
        list_assets(kind="not_a_real_kind")


def test_unknown_quality_bucket_raises() -> None:
    with pytest.raises(ValueError):
        list_assets(quality_filter=">=99.9")


# ---------- Reference helper ----------------------------------------------


def test_reference_returns_opaque_handle_for_known_asset() -> None:
    handle = reference_asset("asset_seed_broll_outdoor_city_01")
    assert handle is not None
    assert handle["ref"] == "asset://asset_seed_broll_outdoor_city_01"
    assert handle["asset_id"] == "asset_seed_broll_outdoor_city_01"
    assert handle["kind"] == "broll"


def test_reference_returns_none_for_unknown_asset() -> None:
    assert reference_asset("does_not_exist") is None


def test_get_asset_returns_deep_copy() -> None:
    a = get_asset("asset_seed_broll_outdoor_city_01")
    assert a is not None
    a["title"] = "MUTATED"
    fresh = get_asset("asset_seed_broll_outdoor_city_01")
    assert fresh is not None
    assert fresh["title"] != "MUTATED"


# ---------- Forbidden vendor/model key sanitizer --------------------------


def test_no_forbidden_keys_appear_in_seeded_listing() -> None:
    for asset in list_assets(include_unsurfaced=True):

        def walk(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    assert key not in FORBIDDEN_ASSET_KEYS, (
                        f"forbidden key {key!r} leaked into asset {asset['asset_id']!r}"
                    )
                    walk(value)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(asset)


def test_sanitizer_drops_planted_forbidden_key(monkeypatch) -> None:
    """Defense-in-depth: even if a future seed entry sneaks in a vendor
    identifier, the library's `_sanitize_asset` MUST drop it before the
    object reaches a consumer.
    """
    from gateway.app.services.asset import library
    from gateway.app.services.asset import seed_data

    bad_seed = (
        {
            "asset_id": "asset_test_planted_vendor_id",
            "kind": "broll",
            "line_availability": ["hot_follow"],
            "tags": [{"facet": "line", "value": "hot_follow"}],
            "provenance": {
                "origin_kind": "admin_seeded",
                "origin_ref": "test:planted",
                "content_hash": "sha256:test",
                "promoted_from_artifact_ref": None,
                "vendor_id": "leaked_vendor",
            },
            "version": 1,
            "quality_threshold": "approved",
            "quality": {"summary": "test"},
            "usage_limits": {"license": "owned", "reuse_policy": "reuse_allowed"},
            "title": "Planted Test Asset",
            "created_at": "2026-05-04T00:00:00Z",
            "created_by": "test:planted",
            "badges": {"reusable": False, "canonical": False, "archived": False, "deprecated": False},
            "model_id": "leaked_model",
        },
    )
    monkeypatch.setattr(seed_data, "_SEED_ASSETS", bad_seed)
    monkeypatch.setattr(library, "get_seed_assets", lambda: bad_seed)

    asset = get_asset("asset_test_planted_vendor_id")
    assert asset is not None
    assert "model_id" not in asset
    assert "vendor_id" not in asset["provenance"]
