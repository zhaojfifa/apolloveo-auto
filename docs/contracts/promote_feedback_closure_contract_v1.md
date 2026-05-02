# Promote Feedback Closure Contract v1

Date: 2026-05-02
Status: Plan C contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan C
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/product/broll_asset_supply_freeze_v1.md` §2 (Promote semantics)
- `docs/contracts/promote_request_contract_v1.md` (sibling Plan C)
- `docs/contracts/asset_library_object_contract_v1.md` (sibling Plan C)

## Purpose

Pin the **append-only audit trail and closure mirror** for promote requests. Each promote request (`promote_request_contract_v1`) has exactly one closure object that records its lifecycle from `requested` to terminal state (`approved` or `rejected`).

Mirrors the per-line publish-feedback closure pattern (e.g. `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md`) — append-only audit trail + small mutable cached-current view.

This contract does not implement the closure store, persistence, or admin review UI. It pins the shape any future implementation MUST honor.

## Ownership

- Owner: contract layer (Plan C).
- Future runtime consumer: a promote-closure service (gated behind Plan E acceptance).
- Non-owners: routers, presenters, frontend, donor modules, packet validator.

## Boundary

- The closure does not own asset truth — accepted requests result in a NEW Asset Library object (per asset library contract). The closure references the resulting `asset_id` once accepted; it does not embed asset state.
- The closure does not own artifact truth — the source artifact remains immutable.
- The closure does not mutate any packet, deliverable, ready_gate, or workbench surface.

## Closure object shape

```
{
  closure_id:           string,                        # 1:1 with request_id
  request_id:           string,                        # ref to promote_request_contract_v1
  artifact_ref:         opaque,                        # copied from request at creation
  request_state:        "requested" | "approved" | "rejected",
  resulting_asset_id:   opaque | null,                 # set when request_state=approved
  rejection_reason:     enum (closed; below) | null,   # set when request_state=rejected
  reviewer_ref:         opaque actor ref | null,       # set when state transitions away from requested
  reviewer_notes:       string | null,
  request_timestamp_utc: ISO-8601 UTC,                 # copied from request
  resolved_timestamp_utc: ISO-8601 UTC | null,         # set when terminal
  closure_records[]:    array of records (append-only) # see below
}
```

### Closed `request_state` enum

```
{ requested, approved, rejected }
```

Terminal states: `approved`, `rejected`. A closure in a terminal state MUST NOT transition again; corrections are recorded by a NEW promote request and a NEW closure (per product freeze §2 — "Promote is not versioning").

### Closed `rejection_reason` enum (immutable taxonomy)

```
{
  license_not_eligible,
  reuse_policy_conflict,
  duplicate_of_existing_asset,
  quality_below_threshold,
  metadata_incomplete,
  source_artifact_unresolvable,
  policy_violation,
  reviewer_discretion
}
```

Reviewer notes (`reviewer_notes` field) carry free-text context. The enum value is the structured truth; the note is the human-readable elaboration.

### `closure_records[]` row

```
{
  event_id:        string,                              # stable id within this closure
  event_kind:      enum (closed; below),
  recorded_at:     ISO-8601 UTC,
  actor_kind:      "operator" | "reviewer" | "system",
  actor_ref:       opaque actor ref,
  payload_ref:     opaque | null                        # per-event payload pointer; not embedded
}
```

### Closed `event_kind` enum

```
{ submitted, review_started, approved, rejected, withdrawn, system_note }
```

`withdrawn` is operator-initiated cancellation before terminal state; it transitions `request_state` to `rejected` with `rejection_reason=null` and `reviewer_ref=null` (operator-side withdrawal, not reviewer rejection).

## Append-only discipline

- `closure_records[]` is append-only. Edits and deletes are forbidden.
- Per-row mutable fields (`request_state`, `resulting_asset_id`, `rejection_reason`, `reviewer_ref`, `reviewer_notes`, `resolved_timestamp_utc`) follow last-write-wins per closure event. The audit trail is the source of truth; mutable fields are the cached current view.
- `recorded_at` MUST be UTC ISO-8601 and monotonic non-decreasing within a closure object.

## Source-of-truth rules

1. **Source artifact is immutable.** No event in this closure mutates the source artifact, its task, or its packet.
2. **Asset object is owned by the asset library.** When `request_state=approved`, the resulting asset object is created in the Asset Library; the closure references it by `resulting_asset_id`. The asset object's metadata is governed by `asset_library_object_contract_v1.md`, not this contract.
3. **Cross-line scope is forbidden.** A promote closure references one request, one source artifact, and (if approved) one resulting asset. It does NOT aggregate across lines or across requests.
4. **No truth-shape state writes outside this closure.** `request_state` is closure-side state; it MUST NOT appear on any packet, deliverable, workbench surface, or asset object.

## Forbidden

- vendor / model / provider / engine identifiers anywhere;
- mutation of source artifact, source task, source packet, or any deliverable / readiness surface;
- creation of an asset object directly from this closure (the asset object is owned by the asset library; this closure references it once created);
- new advisory codes (advisory truth lives behind Plan D `l4_advisory_producer_output_contract_v1.md`);
- ACL / auth model (declared in implementation gate);
- donor (SwiftCraft) module identifiers;
- truth-shape state writes outside the scoped `request_state` enum.

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in any field or event payload.
- Validator R5: the scoped `request_state` enum lives only inside this closure; outside the closure, `status`/`ready`/etc. remain banned.

## Acceptance

This contract is green when:

1. Every closed enum (`request_state`, `rejection_reason`, `event_kind`, `actor_kind`) is exactly the set declared above.
2. `closure_records[]` is append-only; per-row mutable fields are cached-current views derived from the audit trail.
3. Source artifact and source packet are never mutated by any path through this closure.
4. The closure references `resulting_asset_id` only after the asset object is created in the Asset Library (asset library contract owns the object).

## What this contract does NOT do

- Does not implement closure persistence, transport, or admin review UI (Plan E only).
- Does not define ACL / auth.
- Does not author promote requests (sibling `promote_request_contract_v1.md`).
- Does not author the asset object (sibling `asset_library_object_contract_v1.md`).
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/product/broll_asset_supply_freeze_v1.md`
- `docs/contracts/promote_request_contract_v1.md`
- `docs/contracts/asset_library_object_contract_v1.md`
- `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` (closure pattern reference)
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
