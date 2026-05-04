"""Seed catalog of Asset Library objects for PR-2 minimum operator capability.

Per the Recovery Decision §4.1 + Global Action §5, PR-2 ships the
**minimum usable** Asset Supply capability — not a full DAM. There is
no DB schema and no upload flow in this wave (per Plan C contract
gating + Recovery red lines). The minimum read-only catalog ships as
seed data so operators can browse, filter, reference, and trigger
promote intent against contract-shaped objects today; durable
persistence is Platform Runtime Assembly Wave or later.

Every seed object conforms verbatim to the closed metadata schema in
`docs/contracts/asset_library_object_contract_v1.md` §"Closed metadata
schema". The seeds carry NO vendor / model / provider / engine
identifiers (validator R3) and NO truth-shape state fields (validator
R5). The `kind` enum, facet enum, license enum, reuse_policy enum, and
quality_threshold enum are exactly the closed sets declared in the
contract.
"""
from __future__ import annotations

from typing import Any


# Mirrors `asset_library_object_contract_v1.md` §"Closed `kind` enum".
ASSET_KIND_ENUM: frozenset[str] = frozenset(
    {
        "reference_video",
        "broll",
        "style",
        "product_shot",
        "background",
        "template",
        "variation_axis",
        "role_ref",
        "scene",
        "language",
        "source_script",
        "source_audio",
        "source_subtitle",
        "scene_pack_ref",
        "audio_ref",
    }
)

# Mirrors `asset_library_object_contract_v1.md` §"Closed facet set".
ASSET_FACET_ENUM: frozenset[str] = frozenset(
    {
        "line",
        "topic",
        "style",
        "language",
        "role_id",
        "scene",
        "variation_axis",
        "quality_threshold",
    }
)

LINE_AVAILABILITY_ENUM: frozenset[str] = frozenset(
    {"hot_follow", "matrix_script", "digital_anchor"}
)

LICENSE_ENUM: frozenset[str] = frozenset(
    {
        "owned",
        "licensed_reuse_allowed",
        "licensed_single_use",
        "public_domain",
        "unknown_review_required",
    }
)

REUSE_POLICY_ENUM: frozenset[str] = frozenset(
    {
        "reuse_allowed",
        "line_limited",
        "task_limited",
        "review_required",
        "blocked",
    }
)

QUALITY_THRESHOLD_ENUM: frozenset[str] = frozenset({"draft", "review", "approved"})

QUALITY_FILTER_BUCKET_ENUM: frozenset[str] = frozenset(
    {"any", ">=0.6", ">=0.75", ">=0.9"}
)

ORIGIN_KIND_ENUM: frozenset[str] = frozenset(
    {
        "operator_upload",
        "task_artifact_promote",
        "external_reference",
        "licensed_stock",
        "admin_seeded",
    }
)


# Seed catalog. Shapes are exactly the closed schema in
# asset_library_object_contract_v1.md §"Closed metadata schema". Each
# entry exists at `quality_threshold="approved"` so the minimum
# operator-visible capability can demonstrate browsing, filtering, and
# referencing against admin-approved assets. Operators cannot mutate
# `quality_threshold` from the surface (per product freeze §1).
_SEED_ASSETS: tuple[dict[str, Any], ...] = (
    {
        "asset_id": "asset_seed_broll_outdoor_city_01",
        "kind": "broll",
        "line_availability": ["hot_follow", "matrix_script"],
        "tags": [
            {"facet": "line", "value": "hot_follow"},
            {"facet": "line", "value": "matrix_script"},
            {"facet": "scene", "value": "outdoor"},
            {"facet": "style", "value": "documentary"},
            {"facet": "topic", "value": "city_life"},
        ],
        "provenance": {
            "origin_kind": "admin_seeded",
            "origin_ref": "seed:broll/outdoor_city_01",
            "content_hash": "sha256:seed-broll-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "approved",
        "quality": {"summary": "Steady wide-angle city walk-through, color-balanced."},
        "usage_limits": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "reuse_notes": None,
        },
        "title": "City Outdoor Walk B-roll",
        "created_at": "2026-04-01T00:00:00Z",
        "created_by": "admin:seed",
        "badges": {"reusable": True, "canonical": True, "archived": False, "deprecated": False},
    },
    {
        "asset_id": "asset_seed_role_anchor_female_01",
        "kind": "role_ref",
        "line_availability": ["digital_anchor"],
        "tags": [
            {"facet": "line", "value": "digital_anchor"},
            {"facet": "role_id", "value": "anchor_female_01"},
            {"facet": "language", "value": "zh"},
        ],
        "provenance": {
            "origin_kind": "admin_seeded",
            "origin_ref": "seed:role/anchor_female_01",
            "content_hash": "sha256:seed-role-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "approved",
        "quality": {"summary": "Standard female anchor role; neutral business attire."},
        "usage_limits": {
            "license": "licensed_reuse_allowed",
            "reuse_policy": "line_limited",
            "reuse_notes": "Digital Anchor only.",
        },
        "title": "Anchor Role · Female 01",
        "created_at": "2026-04-02T00:00:00Z",
        "created_by": "admin:seed",
        "badges": {"reusable": True, "canonical": True, "archived": False, "deprecated": False},
    },
    {
        "asset_id": "asset_seed_variation_axis_hook_01",
        "kind": "variation_axis",
        "line_availability": ["matrix_script"],
        "tags": [
            {"facet": "line", "value": "matrix_script"},
            {"facet": "variation_axis", "value": "hook"},
        ],
        "provenance": {
            "origin_kind": "admin_seeded",
            "origin_ref": "seed:variation_axis/hook_01",
            "content_hash": "sha256:seed-axis-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "approved",
        "quality": {"summary": "Canonical hook axis values for Matrix Script variation."},
        "usage_limits": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "reuse_notes": None,
        },
        "title": "Matrix Script Hook Axis",
        "created_at": "2026-04-03T00:00:00Z",
        "created_by": "admin:seed",
        "badges": {"reusable": True, "canonical": True, "archived": False, "deprecated": False},
    },
    {
        "asset_id": "asset_seed_source_script_demo_01",
        "kind": "source_script",
        "line_availability": ["matrix_script"],
        "tags": [
            {"facet": "line", "value": "matrix_script"},
            {"facet": "language", "value": "zh"},
            {"facet": "topic", "value": "product_demo"},
        ],
        "provenance": {
            "origin_kind": "admin_seeded",
            "origin_ref": "seed:source_script/demo_01",
            "content_hash": "sha256:seed-script-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "approved",
        "quality": {"summary": "Reference product-demo script; neutral tone, 60-second target."},
        "usage_limits": {
            "license": "owned",
            "reuse_policy": "reuse_allowed",
            "reuse_notes": None,
        },
        "title": "Demo Source Script · Product",
        "created_at": "2026-04-04T00:00:00Z",
        "created_by": "admin:seed",
        "badges": {"reusable": True, "canonical": False, "archived": False, "deprecated": False},
    },
    {
        "asset_id": "asset_seed_background_studio_01",
        "kind": "background",
        "line_availability": ["digital_anchor", "matrix_script"],
        "tags": [
            {"facet": "line", "value": "digital_anchor"},
            {"facet": "line", "value": "matrix_script"},
            {"facet": "scene", "value": "studio"},
            {"facet": "style", "value": "neutral"},
        ],
        "provenance": {
            "origin_kind": "licensed_stock",
            "origin_ref": "stock:background/studio_01",
            "content_hash": "sha256:seed-bg-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "approved",
        "quality": {"summary": "Neutral studio background; suitable for anchor render."},
        "usage_limits": {
            "license": "licensed_reuse_allowed",
            "reuse_policy": "reuse_allowed",
            "reuse_notes": "Stock background; attribution not required.",
        },
        "title": "Studio Neutral Background",
        "created_at": "2026-04-05T00:00:00Z",
        "created_by": "admin:seed",
        "badges": {"reusable": True, "canonical": False, "archived": False, "deprecated": False},
    },
    {
        "asset_id": "asset_seed_draft_pending_review_01",
        "kind": "broll",
        "line_availability": [],
        "tags": [
            {"facet": "topic", "value": "untagged_draft"},
        ],
        "provenance": {
            "origin_kind": "operator_upload",
            "origin_ref": "upload:pending/01",
            "content_hash": "sha256:seed-draft-01",
            "promoted_from_artifact_ref": None,
        },
        "version": 1,
        "quality_threshold": "draft",
        "quality": {"summary": "Operator upload pending tagging and promote review."},
        "usage_limits": {
            "license": "unknown_review_required",
            "reuse_policy": "review_required",
            "reuse_notes": None,
        },
        "title": "Draft Upload (pending review)",
        "created_at": "2026-04-06T00:00:00Z",
        "created_by": "operator:demo",
        "badges": {"reusable": False, "canonical": False, "archived": False, "deprecated": False},
    },
)


def get_seed_assets() -> tuple[dict[str, Any], ...]:
    """Return the immutable seed catalog tuple. Callers MUST treat
    individual asset dicts as read-only; the library service returns
    deep copies before exposing them.
    """
    return _SEED_ASSETS


__all__ = [
    "ASSET_FACET_ENUM",
    "ASSET_KIND_ENUM",
    "LICENSE_ENUM",
    "LINE_AVAILABILITY_ENUM",
    "ORIGIN_KIND_ENUM",
    "QUALITY_FILTER_BUCKET_ENUM",
    "QUALITY_THRESHOLD_ENUM",
    "REUSE_POLICY_ENUM",
    "get_seed_assets",
]
