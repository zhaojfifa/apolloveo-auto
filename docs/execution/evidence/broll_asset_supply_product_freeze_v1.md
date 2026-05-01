# Evidence: B-roll / Asset Supply Product Freeze v1

Date: 2026-05-01
For: Product freeze of B-roll / Asset Supply open questions before wiring

## Authority Read

- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/design/broll_asset_supply_lowfi_v1.md`
- `docs/reviews/architect_phase2_lowfi_review_v1.md`
- `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## What Landed

Created the frozen B-roll product authority:

- `docs/product/broll_asset_supply_freeze_v1.md`

Updated the low-fi design:

- `docs/design/broll_asset_supply_lowfi_v1.md`

State sync:

- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## Frozen Decisions

1. Filter taxonomy keeps all eight first-class facets for first wiring:
   `line`, `topic`, `style`, `language`, `role_id`, `scene`,
   `variation_axis`, `quality_threshold`. All except `quality_threshold`
   are multi-select; all are operator-visible with context hiding for
   non-applicable role/variation facets.
2. Promote semantics are frozen as async review-gated create-new-asset
   intent. No asset versioning as the first path.
3. License/source/reuse field set is frozen, including mandatory fields,
   source enum, license enum, and reuse policy enum.
4. Canonical/reusable marking is frozen as admin-only state with
   operator-visible read-only badges. Canonical is not equal to reusable.
5. Detail actions `archive`, `deprecate`, `supersede`, `unlink`, and
   `replace_preview` are admin management controls, not operator-visible
   B-roll actions.
6. Artifact-to-asset hand-off is explicit promote intent only. UI cannot
   complete promote; Asset Library creation happens after review.
7. Reference-into-task pre-population mapping is frozen for role refs,
   reference video, template, variation axis, background, broll,
   product shot, scene pack refs, and audio refs.

## Boundary Checks

- Asset and Artifact remain strictly separated.
- B-roll remains an Asset Library surface, not a task-area or delivery
  truth surface.
- No provider/model/vendor/engine concepts were added.
- No runtime truth, packet/schema, UI, presenter, or wiring code changed.
- Tool backstage and admin/governance controls remain outside B-roll.

## Deferred Items

- Facet value administration UI.
- Bulk asset import.
- Bulk promote.
- Asset versioning as primary promote path.
- Operator-side archive/deprecate/supersede/unlink/replace-preview.
- Provider/tool/runtime metadata on the asset surface.

## Wiring Readiness

B-roll wiring may open next only after review accepts this freeze. The next
commissioning must remain projection/intent-only and must not start Platform
Runtime Assembly, W2.2/W2.3, packet/schema redesign, or provider/model/vendor
surface exposure.
