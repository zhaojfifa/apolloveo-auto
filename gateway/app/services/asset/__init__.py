"""Asset supply host (Operator Capability Recovery PR-2 minimum).

Implements the minimum operator-visible Asset Supply / B-roll capability
per `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
§4.1 + Global Action §5. Backed by the Plan C frozen contracts:

- `docs/contracts/asset_library_object_contract_v1.md`
- `docs/contracts/promote_request_contract_v1.md`
- `docs/contracts/promote_feedback_closure_contract_v1.md`

What this module is NOT (per Recovery red lines):

- Not a full DAM / asset platform.
- Not an upload-heavy admin console.
- Not a fingerprinting / dedup platform.
- Not a vendor / model / provider / engine catalog.
- Not coupled to Task Area or Tool Backstage surfaces.

See `library.py` for the read-only browse / filter / reference path and
`promote.py` for the contract-backed promote intent + closure flow.
"""
from .library import (
    FORBIDDEN_ASSET_KEYS,
    get_asset,
    list_assets,
    list_known_kinds,
    list_known_lines,
    list_known_quality_buckets,
    list_known_quality_threshold_values,
    reference_asset,
)
from .promote import (
    ACTOR_KIND_ENUM,
    EVENT_KIND_ENUM,
    FORBIDDEN_PROMOTE_KEYS,
    PromoteRequestRejected,
    REJECTION_REASON_ENUM,
    REQUEST_STATE_ENUM,
    approve_request,
    get_closure,
    get_request,
    list_closures,
    reject_request,
    reset_store_for_tests,
    submit_promote_request,
    withdraw_request,
)

__all__ = [
    "ACTOR_KIND_ENUM",
    "EVENT_KIND_ENUM",
    "FORBIDDEN_ASSET_KEYS",
    "FORBIDDEN_PROMOTE_KEYS",
    "PromoteRequestRejected",
    "REJECTION_REASON_ENUM",
    "REQUEST_STATE_ENUM",
    "approve_request",
    "get_asset",
    "get_closure",
    "get_request",
    "list_assets",
    "list_closures",
    "list_known_kinds",
    "list_known_lines",
    "list_known_quality_buckets",
    "list_known_quality_threshold_values",
    "reference_asset",
    "reject_request",
    "reset_store_for_tests",
    "submit_promote_request",
    "withdraw_request",
]
