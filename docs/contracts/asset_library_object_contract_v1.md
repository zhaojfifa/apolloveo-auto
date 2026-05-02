# Asset Library Object Contract v1

Date: 2026-05-02
Status: Plan C contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **no asset-library implementation, no schema migration, no UI in this wave**.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan C
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/product/broll_asset_supply_freeze_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`

## Purpose

Pin the **closed metadata schema** for an Asset Library object. Today, the B-roll / Asset Supply surface is "discovery-only" (gap review §6) because the product freeze enumerates facets and promote semantics but no contract object exists. This contract closes that gap at the contract layer.

The Asset Library is **separate from the Artifact Store**. An Artifact is task-owned, ephemeral, and immutable. An Asset is reusable, library-owned, and only created via the explicit promote intent flow (Plan C contracts `promote_request_contract_v1.md` and `promote_feedback_closure_contract_v1.md`).

This contract does not implement asset CRUD, does not author DB schema, and does not introduce a UI. It pins the metadata shape that any future asset-library implementation MUST honor.

## Ownership

- Owner: contract layer (Plan C).
- Future runtime consumer: an asset-library service (gated behind Plan E acceptance).
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend platform, packet validator (assets are not packet truth).

## Boundary

Asset Library objects are **read-only across line packets**. A packet may reference an `asset_id` via existing `factory_input_contract_v1` ref shapes, but the asset metadata itself is owned by the Asset Library, never by the packet. Per `broll_asset_supply_freeze_v1.md` §"Boundary": "A task artifact can become an asset only through an explicit promote flow."

## Closed metadata schema

Every Asset Library object carries the following fields. The set is closed at v1; additions require a re-version.

| Field                          | Type                            | Required | Notes                                                                                                          |
| ------------------------------ | ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `asset_id`                     | opaque string                   | yes      | Asset namespace; distinct from `artifact_id`.                                                                  |
| `kind`                         | enum (closed; see below)        | yes      | The cross-line asset kind.                                                                                     |
| `line_availability[]`          | subset of `{hot_follow, matrix_script, digital_anchor}` | yes | Lines this asset MAY be referenced from. Empty = available to none (admin-pending).                          |
| `tags[]`                       | array of `{facet, value}` pairs | yes      | Facet drawn from the closed facet set (see below); value drawn from the closed value list per facet.          |
| `provenance.origin_kind`       | enum: `{operator_upload, task_artifact_promote, external_reference, licensed_stock, admin_seeded}` | yes | Mirrors `broll_asset_supply_freeze_v1.md` §3 `source` enum. |
| `provenance.origin_ref`        | opaque string                   | yes      | The originating handle (artifact id, external URL handle, etc.). Opaque only.                                  |
| `provenance.content_hash`      | string                          | yes      | Stable content hash; basis for de-duplication.                                                                 |
| `provenance.promoted_from_artifact_ref` | opaque string \| null  | optional | Set when `origin_kind=task_artifact_promote`; references the source artifact handle.                          |
| `version`                      | integer ≥ 1                     | yes      | Asset version; see "Versioning rule" below.                                                                    |
| `quality_threshold`            | enum: `{draft, review, approved}` | yes    | Surfacing gate per `broll_asset_supply_freeze_v1.md`.                                                          |
| `quality.summary`              | string                          | yes      | Human-readable quality summary; no provider/model identifier.                                                  |
| `usage_limits.license`         | enum: `{owned, licensed_reuse_allowed, licensed_single_use, public_domain, unknown_review_required}` | yes | Per product freeze §3.                                                                                |
| `usage_limits.reuse_policy`    | enum: `{reuse_allowed, line_limited, task_limited, review_required, blocked}` | yes | Per product freeze §3.                                                                                |
| `usage_limits.reuse_notes`     | string                          | optional | Operator-visible restriction notes.                                                                            |
| `title`                        | string                          | yes      | Operator-visible label.                                                                                        |
| `created_at`                   | ISO-8601 UTC                    | yes      | Creation timestamp.                                                                                            |
| `created_by`                   | opaque actor ref                | yes      | Operator or admin actor reference.                                                                             |
| `badges`                       | object: `{reusable: bool, canonical: bool, archived: bool, deprecated: bool}` | yes | Admin-owned read-only badges; operator-visible per product freeze §4 / §5. |

### Closed `kind` enum (cross-line aggregation)

```
{ reference_video, broll, style, product_shot, background, template,
  variation_axis, role_ref, scene, language, source_script,
  source_audio, source_subtitle, scene_pack_ref, audio_ref }
```

The kind set aggregates the per-line asset kinds enumerated in `asset_supply_matrix_v1.md` §"Input asset kinds" and `broll_asset_supply_freeze_v1.md` §7 "Reference Into Task Pre-population Mapping". A future line-onboarding wave that needs a new kind MUST re-version this contract; donor modules MUST NOT widen the set (per asset_supply_matrix v1 §"Decoupling rules" item 3).

### Closed facet set for `tags[]`

| Facet               | Closed value source                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------- |
| `line`              | `{hot_follow, matrix_script, digital_anchor}` (mirrors `line_availability[]` for filtering)  |
| `topic`             | Asset Library catalog ids (closed list owned by the library; free text is search-only)       |
| `style`             | Controlled style tags per `broll_asset_supply_freeze_v1.md` §1                                |
| `language`          | BCP-47-like public language codes per product freeze §1                                       |
| `role_id`           | Opaque Digital Anchor role catalog ids                                                        |
| `scene`             | Controlled scene taxonomy per product freeze §1                                               |
| `variation_axis`    | Controlled Matrix Script axis ids per product freeze §1                                       |
| `quality_threshold` | `{any, >=0.6, >=0.75, >=0.9}` (filter facet) — note: the asset-side `quality_threshold` field carries `{draft, review, approved}` per product freeze §1 / §3 |

### Quality threshold semantics

- `draft` — uploaded, untagged, not surfaced to non-author operators (per gap review §11 Plan C).
- `review` — tagged and submitted for promote review.
- `approved` — admin-reviewed; surfaced to all lines listed in `line_availability[]`.

These three values are the asset-side surfacing gate. The filter facet `quality_threshold` (with bucketed numeric values) is a UI-side lower-bound filter; it is not a quality truth editor (per product freeze §1).

### Versioning rule

- A new asset version is created when content_hash changes.
- `version` is monotonic per `asset_id`.
- An older version is NOT mutated when a newer version lands; old versions remain queryable.
- Promote of a content-divergent artifact creates a NEW asset (new `asset_id`), not a new version, per product freeze §2: "Promote is not versioning in this first product pass."

## Forbidden

- vendor / model / provider / engine / avatar-engine / TTS-provider / lip-sync-engine identifiers in any field, tag, or provenance subtree;
- raw asset payloads (assets carry opaque references only);
- storage URLs or backend paths (operator-visible only as opaque handles);
- truth-shape state fields (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`);
- donor (SwiftCraft) module identifiers;
- per-task ownership fields (assets are reusable, not task-bound);
- packet truth fields (assets are not packet truth — packets reference them by `asset_id` only).

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier appears in any closed-set field.
- Validator R5: no truth-shape state field on the asset object; the `quality_threshold` enum is a surfacing gate, not a packet readiness field.
- Cross-check vs `asset_supply_matrix_v1.md`: every `kind` listed here is reachable from the per-line operator-supplied / line-produced matrix.

## Acceptance

This contract is green when:

1. The metadata schema is closed at v1; no field is added or omitted from the table above.
2. The `kind` enum, facet enum, license enum, reuse_policy enum, and quality_threshold enum are closed and trace to the product freeze + asset supply matrix.
3. The asset/artifact boundary is binding: assets are not artifacts; promote is the only crossing path.
4. No forbidden field appears anywhere in the schema.

## What this contract does NOT do

- Does not implement asset CRUD, DB schema, or migrations (Plan E gate).
- Does not author the asset-library UI.
- Does not author the promote flow — that lives in `promote_request_contract_v1.md` and `promote_feedback_closure_contract_v1.md`.
- Does not change packet schema or sample.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/product/broll_asset_supply_freeze_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/promote_request_contract_v1.md`
- `docs/contracts/promote_feedback_closure_contract_v1.md`
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
