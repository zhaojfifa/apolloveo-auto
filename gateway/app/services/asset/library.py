"""Asset Library read-only service (Operator Capability Recovery, PR-2).

Minimum usable read-only capability per the Recovery Decision §4.1 +
Global Action §5. Backed by the seed catalog in
[seed_data.py](seed_data.py); no DB, no upload, no admin tooling. All
returned objects conform verbatim to
`docs/contracts/asset_library_object_contract_v1.md` §"Closed metadata
schema".

Surface boundary discipline (per `broll_asset_supply_freeze_v1.md` §0
"Boundary"):

- Asset Library is distinct from Task Area, Delivery Center, and Tool
  Backstage. This service does not read packet truth, does not mutate
  artifacts, and does not expose vendor / model / provider / engine
  identifiers. A defensive sanitizer (`_sanitize_asset`) drops any
  forbidden key before returning to a consumer — so a future seed-data
  bug or test fixture cannot leak a forbidden identifier through this
  surface.
"""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping, Optional

from .seed_data import (
    ASSET_KIND_ENUM,
    LINE_AVAILABILITY_ENUM,
    QUALITY_FILTER_BUCKET_ENUM,
    QUALITY_THRESHOLD_ENUM,
    get_seed_assets,
)

# Per `gateway/app/services/operator_visible_surfaces/projections.py`
# `FORBIDDEN_OPERATOR_KEYS` and validator R3. We re-declare here so this
# service does not depend on the publish-readiness module; the set is
# the cross-surface canonical list.
FORBIDDEN_ASSET_KEYS: frozenset[str] = frozenset(
    {
        "vendor_id",
        "model_id",
        "provider",
        "provider_id",
        "engine_id",
        "raw_provider_route",
        "avatar_engine_id",
        "tts_provider_id",
        "lip_sync_engine_id",
    }
)


def _sanitize_asset(asset: Mapping[str, Any]) -> dict[str, Any]:
    """Deep-copy an asset and drop any forbidden vendor/model key.

    Defense-in-depth: if a future seed entry or test fixture accidentally
    introduces a forbidden identifier, this layer drops it before the
    asset reaches an operator surface or consumer.
    """
    cleaned: dict[str, Any] = {}
    for key, value in asset.items():
        if key in FORBIDDEN_ASSET_KEYS:
            continue
        if isinstance(value, Mapping):
            cleaned[key] = _sanitize_asset(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _sanitize_asset(item) if isinstance(item, Mapping) else copy.deepcopy(item)
                for item in value
            ]
        else:
            cleaned[key] = copy.deepcopy(value)
    return cleaned


def _quality_threshold_satisfies(asset_quality: str, filter_bucket: str) -> bool:
    """Apply the bucketed `quality_threshold` filter facet.

    Per `broll_asset_supply_freeze_v1.md` §1, the filter bucket is a
    UI-side **lower bound**; the asset-side `quality_threshold` enum is
    `{draft, review, approved}`. Mapping (lower-bound semantics):

    - filter `any`     → all rows pass
    - filter `>=0.6`   → review or approved
    - filter `>=0.75`  → approved
    - filter `>=0.9`   → approved (no finer asset-side gate exists today)
    """
    if filter_bucket not in QUALITY_FILTER_BUCKET_ENUM:
        return False
    if filter_bucket == "any":
        return True
    if filter_bucket == ">=0.6":
        return asset_quality in {"review", "approved"}
    return asset_quality == "approved"


def _matches_filters(
    asset: Mapping[str, Any],
    *,
    line: Optional[str],
    kind: Optional[str],
    quality_filter: Optional[str],
    facet_values: Optional[Mapping[str, str]],
) -> bool:
    if line is not None:
        if line not in (asset.get("line_availability") or []):
            return False
    if kind is not None:
        if str(asset.get("kind") or "") != kind:
            return False
    if quality_filter is not None:
        if not _quality_threshold_satisfies(
            str(asset.get("quality_threshold") or ""), quality_filter
        ):
            return False
    if facet_values:
        tags = list(asset.get("tags") or [])
        for facet, value in facet_values.items():
            if not any(
                isinstance(t, Mapping)
                and str(t.get("facet") or "") == facet
                and str(t.get("value") or "") == value
                for t in tags
            ):
                return False
    return True


def list_assets(
    *,
    line: Optional[str] = None,
    kind: Optional[str] = None,
    quality_filter: Optional[str] = None,
    facet_values: Optional[Mapping[str, str]] = None,
    include_unsurfaced: bool = False,
) -> list[dict[str, Any]]:
    """Read-only list with closed-facet filters.

    Args:
        line: Restrict to assets whose `line_availability` includes this
            line id. MUST be a member of the closed line enum or `None`.
        kind: Restrict to assets of this `kind`. MUST be a member of the
            closed `kind` enum or `None`.
        quality_filter: Bucketed quality-threshold lower bound. MUST be a
            member of `QUALITY_FILTER_BUCKET_ENUM` or `None`.
        facet_values: Additional closed-facet equality filters. Each
            facet name MUST belong to the closed facet enum.
        include_unsurfaced: When False (default), `quality_threshold ==
            "draft"` rows are hidden from non-author operators per gap
            review §11 Plan C. Set True only for admin/test paths.

    Returns:
        Sanitized deep-copied asset dicts conforming to
        `asset_library_object_contract_v1` §"Closed metadata schema".
    """
    if line is not None and line not in LINE_AVAILABILITY_ENUM:
        raise ValueError(f"unknown line: {line!r}")
    if kind is not None and kind not in ASSET_KIND_ENUM:
        raise ValueError(f"unknown kind: {kind!r}")
    if quality_filter is not None and quality_filter not in QUALITY_FILTER_BUCKET_ENUM:
        raise ValueError(f"unknown quality_filter bucket: {quality_filter!r}")

    out: list[dict[str, Any]] = []
    for asset in get_seed_assets():
        if not include_unsurfaced and str(asset.get("quality_threshold") or "") == "draft":
            continue
        if not _matches_filters(
            asset,
            line=line,
            kind=kind,
            quality_filter=quality_filter,
            facet_values=facet_values,
        ):
            continue
        out.append(_sanitize_asset(asset))
    return out


def get_asset(asset_id: str) -> Optional[dict[str, Any]]:
    """Single-asset lookup by `asset_id`.

    Returns `None` when no seeded asset matches. Returns a sanitized
    deep copy when found. Draft assets are returned (lookup is
    by-id; surfacing-gate filtering happens in `list_assets`).
    """
    for asset in get_seed_assets():
        if str(asset.get("asset_id") or "") == asset_id:
            return _sanitize_asset(asset)
    return None


def reference_asset(asset_id: str) -> Optional[dict[str, str]]:
    """Return the opaque reference handle for cross-task referencing.

    Per `broll_asset_supply_freeze_v1.md` §0 "Boundary" the reference
    surface is opaque-handle-only: a packet may reference an `asset_id`
    via existing `factory_input_contract_v1` ref shapes, never the asset
    metadata itself. This helper formalizes the handle so a Workbench /
    Task Area caller cannot accidentally embed asset metadata into a
    packet ref.
    """
    asset = get_asset(asset_id)
    if not asset:
        return None
    return {
        "ref": f"asset://{asset_id}",
        "asset_id": asset_id,
        "kind": str(asset.get("kind") or ""),
    }


def list_known_lines() -> list[str]:
    return sorted(LINE_AVAILABILITY_ENUM)


def list_known_kinds() -> list[str]:
    return sorted(ASSET_KIND_ENUM)


def list_known_quality_buckets() -> list[str]:
    # Stable display order (`any` first, then ascending lower bounds).
    return ["any", ">=0.6", ">=0.75", ">=0.9"]


def list_known_quality_threshold_values() -> list[str]:
    # `draft, review, approved` per the asset-side enum.
    return ["draft", "review", "approved"]


__all__ = [
    "FORBIDDEN_ASSET_KEYS",
    "get_asset",
    "list_assets",
    "list_known_kinds",
    "list_known_lines",
    "list_known_quality_buckets",
    "list_known_quality_threshold_values",
    "reference_asset",
]


# Silence unused import.
_ = (Iterable, QUALITY_THRESHOLD_ENUM)
