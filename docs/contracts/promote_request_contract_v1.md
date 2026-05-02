# Promote Request Contract v1

Date: 2026-05-02
Status: Plan C contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan C
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/product/broll_asset_supply_freeze_v1.md` §2 (Promote semantics)
- `docs/contracts/asset_library_object_contract_v1.md` (Plan C sibling)
- `docs/contracts/promote_feedback_closure_contract_v1.md` (Plan C sibling)

## Purpose

Pin the **closed request schema** for an operator-initiated promote intent. Promote is the **only** path by which a task artifact may become a reusable Asset Library object (per `broll_asset_supply_freeze_v1.md` §2 + §6). The promote request is a **request object, not an asset** — it does not guarantee an asset id.

This contract does not implement the promote flow. It pins the request shape that any future implementation MUST honor.

## Ownership

- Owner: contract layer (Plan C).
- Future runtime consumer: a promote-intent service (gated behind Plan E acceptance).
- Non-owners: routers (carry the request through but do not own its shape), workbench presenters, delivery surfaces, packet validator (promote requests are not packet truth), donor modules, frontend platform.

## Request scope (intent flow)

Per product freeze §2: promote is **always** an intent — the source artifact remains immutable and untouched. The request never mutates artifact, packet, deliverable, or readiness truth. A successful submit returns a synchronous request id only; the asset id is decided asynchronously by the review-gated promote process.

## Closed request schema

| Field                          | Type                          | Required | Notes                                                                                              |
| ------------------------------ | ----------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| `request_id`                   | opaque string                 | yes      | Synchronous request id; assigned at submit; namespaced separately from `asset_id` and `artifact_id`. |
| `artifact_ref`                 | opaque artifact handle        | yes      | The source artifact (immutable); MUST resolve to a real artifact at submit time.                   |
| `target_kind`                  | enum from asset library       | yes      | Subset of the closed `kind` enum in [docs/contracts/asset_library_object_contract_v1.md](asset_library_object_contract_v1.md). |
| `target_tags[]`                | array of `{facet, value}`     | yes      | Drawn from the closed facet set in the asset library contract.                                     |
| `target_line_availability[]`   | subset of `{hot_follow, matrix_script, digital_anchor}` | yes | The lines the resulting asset (if accepted) should be available to.                       |
| `license_metadata.license`     | enum from asset library       | yes      | Same closed enum as `usage_limits.license`.                                                        |
| `license_metadata.reuse_policy`| enum from asset library       | yes      | Same closed enum as `usage_limits.reuse_policy`.                                                   |
| `license_metadata.source`      | enum from asset library       | yes      | Same closed enum as `provenance.origin_kind`; MUST be `task_artifact_promote` for promote-from-artifact requests. |
| `license_metadata.source_label`| string                        | optional | Operator-visible source label.                                                                     |
| `proposed_title`               | string                        | yes      | Operator-proposed asset title (admin may amend during review).                                     |
| `provenance.content_hash`      | string                        | optional | When available; otherwise computed by the promote service from `artifact_ref`.                     |
| `requested_by`                 | opaque actor ref              | yes      | Operator identity ref.                                                                             |
| `request_timestamp_utc`        | ISO-8601 UTC                  | yes      | Submit timestamp; basis for monotonic ordering in the closure.                                     |
| `operator_notes`               | string                        | optional | Free-text note for the reviewer.                                                                   |

## Submit-time discipline

1. **Source artifact remains immutable.** Submit MUST NOT touch the artifact, its task, its packet, or any deliverable referenced by the artifact.
2. **Closed `target_kind`.** A request with `target_kind` outside the asset library `kind` enum MUST be rejected at submit; widening the enum requires re-versioning the asset library contract.
3. **Closed facets / values for `target_tags[]`.** Tag facets and values MUST trace to the asset library contract's closed facet set; unknown facets or values MUST be rejected at submit.
4. **`target_line_availability[]` MUST be a subset** of the three lines; a request listing an unknown line MUST be rejected.
5. **No vendor/model/provider/engine identifier** in any field, tag, license metadata, or note (validator R3 reasserted).
6. **No state field.** The request never carries `status`, `ready`, `done`, `delivery_ready`, `final_ready`, `publishable`, or any other truth-shape state field (validator R5 reasserted).
7. **No asset id is returned synchronously.** Submit returns `request_id` only. The asset id (if accepted) is materialized in the closure (`promote_feedback_closure_contract_v1`).

## Forbidden

- vendor / model / provider / engine identifiers anywhere;
- raw artifact payloads or storage URLs (only opaque `artifact_ref`);
- mutation of the source artifact, its task, or any packet ref;
- direct asset creation (the asset object exists only as the closure outcome of an accepted request);
- cross-line side effects;
- donor (SwiftCraft) module identifiers;
- ACL / auth model (out of scope; declared in implementation gate).

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in input/output schema.
- Validator R5: no truth-shape state field; the only state-like concept lives in the sibling `promote_feedback_closure_contract_v1.md` as the closed `request_state` enum.

## Acceptance

This contract is green when:

1. The closed schema is the exact set of fields above; no addition.
2. Every closed enum (`target_kind`, facets, license, reuse_policy, source, line_availability) traces verbatim to the asset library contract or product freeze.
3. Submit is intent-only — no mutation of artifact, packet, deliverable, or readiness truth.
4. No forbidden field appears anywhere in the schema or in any envisioned response.

## What this contract does NOT do

- Does not implement the promote flow (Plan E only).
- Does not define ACL / auth.
- Does not return an asset object synchronously.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/product/broll_asset_supply_freeze_v1.md`
- `docs/contracts/asset_library_object_contract_v1.md`
- `docs/contracts/promote_feedback_closure_contract_v1.md`
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
