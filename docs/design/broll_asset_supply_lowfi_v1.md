# Surface 4 — B-roll / Asset Supply (Low-fi v1 — FROZEN)

> **Status: product-frozen for B-roll wiring.** Layout and contract boundaries remain as designed. Product decisions are now frozen by `docs/product/broll_asset_supply_freeze_v1.md`; any non-frozen future expansion is explicitly marked deferred below.

Implements `ApolloVeo_Operator_Visible_Surfaces_v1.md` §5.5. Operator-visible asset supply page corresponding to the Asset Library, **not** to the task-area's file-attachment view. Asset and Artifact remain strictly separated.

## Page Goal

- Browse and search the standard asset library.
- Reference an asset into a task (handoff to New Tasks).
- Promote a task artifact into a reusable asset (intent only — UI does not author the promote).
- Show provenance, license, quality, and reuse constraints.
- Enable the "asset reuse flywheel" for all three lines.

## Low-fi layout

```
┌───────────────────────────────────────────────────────────────────────────┐
│  B-ROLL / ASSET LIBRARY                                                    │
├───────────────────────────────────────────────────────────────────────────┤
│  SEARCH / FILTER BAR                                                       │
│  [ search _____________ ]   line ▾   topic ▾   style ▾   language ▾        │
│                              role ▾   scene ▾   variation_axis ▾           │
│                              quality ≥ ▾                                   │
├──────────────────────────────────────────┬────────────────────────────────┤
│  ASSET LIST (left-main)                  │  DETAIL DRAWER (side panel)     │
│  ───────────────────                     │  ───────────────                 │
│  ┌── Asset card ────────────────┐         │  asset_id                       │
│  │ thumbnail · asset_type       │  ←──    │  thumbnail / preview            │
│  │ tags                         │         │  asset_type                     │
│  │ quality summary              │         │  tags                           │
│  │ source / license             │         │  provenance (origin, hash, ver) │
│  │ last used line               │         │  quality                        │
│  └──────────────────────────────┘         │  usage / reuse constraints      │
│  ┌── Asset card ────────────────┐         │  available to lines: …          │
│  │ ...                          │         │                                  │
│  └──────────────────────────────┘         │  ACTION AREA                     │
│  …                                         │   [ Reference into task ]      │
│                                            │   [ Promote intent ]            │
│                                            │   [ Mark reusable / canonical ] │
│                                            │   [ Link to template / role ]   │
└──────────────────────────────────────────┴────────────────────────────────┘
```

### A. Asset list

Per-card fields (per §5.5.A): `asset_id`, thumbnail / preview, `asset_type`, tags, quality summary, source / license, last used line. The card is a strict projection of the asset library object; the list never composes a card from artifact-store data.

First-batch supported `asset_type` values (per §5.5):

`broll`, `reference_video`, `product_shot`, `background`, `template`, `role_ref`, `scene_pack_ref`, `audio_ref`.

### B. Search / filter bar

Per §5.5.B and `docs/product/broll_asset_supply_freeze_v1.md` §1.
Frozen first-class facets: `line`, `topic`, `style`, `language`, `role_id`,
`scene`, `variation_axis`, `quality_threshold`.

- `line`: closed line ids `hot_follow`, `matrix_script`, `digital_anchor`; multi-select; operator-visible.
- `topic`: product taxonomy tags from Asset Library metadata; multi-select; operator-visible.
- `style`: controlled style tags from Asset Library metadata; multi-select; operator-visible.
- `language`: public language codes used by product surfaces; multi-select; operator-visible.
- `role_id`: opaque role catalog ids; multi-select; operator-visible only when role-capable assets are in result scope.
- `scene`: controlled scene taxonomy ids; multi-select; operator-visible.
- `variation_axis`: controlled Matrix Script axis ids; multi-select; operator-visible only when Matrix Script/template assets are in result scope.
- `quality_threshold`: minimum quality bucket `any`, `>=0.6`, `>=0.75`, `>=0.9`; single-select; operator-visible.

The bar emits filter intent only; the asset list re-projects from the library response. Operators cannot create new facet values from this page.

### C. Detail drawer

Per §5.5.C. Read-only view of `provenance`, `hash`/`version`, `quality`, `tags`, usage limits, available-to-lines list. No edit affordances on this drawer.

### D. Action area

Per §5.5.D, with strict UI-emits-intent-only semantics:

| Action | UI role | Truth boundary |
|---|---|---|
| Reference into task | Routes to New Tasks pre-populated with this asset's reference | New Tasks owns packet creation; B-roll only carries the asset_id forward. |
| Promote intent | Posts an async review-gated promote request to create a new asset | Promote is owned by the asset promote boundary; UI never writes the new asset object. The button surfaces request status only (`submitted` / `under_review` / `accepted` / `rejected`). |
| Mark reusable / canonical | Emits request intent only; state change is admin-only | Admin/governance ownership; UI never authors reusable or canonical flags. |
| Link to template / role | Emits link intent | Linkage is stored against the asset library object; UI does not synthesize the linkage. |

## Per-line usage (informational only)

Filter facets must support the per-line patterns defined in §5.5:

| Line | Likely facets used |
|---|---|
| Hot Follow | `reference_video`, `broll`, `style`, `language` |
| Matrix Script | `broll`, `product_shot`, `background`, `template`, `variation_axis` |
| Digital Anchor | `role_ref`, `background`, `template`, `scene`, `language` |

These are usage hints; the page does not branch its layout per line.

## Forbidden on this page

Per §5.5 page red lines:

- Do not equate Artifact with Asset — they are distinct stores.
- Do not show task state on this page — that is the Board's job.
- Do not author deliverable truth — Delivery owns it.
- Do not become a tool / vendor / provider page — no vendor/model/provider selectors anywhere.
- No direct write to the asset library from outside the promote flow.

## Contract Mapping

| UI element | Contract / source | Notes |
|---|---|---|
| Asset card | asset library object | Projection only, never artifact-store data. |
| Tags / facets | asset metadata / tags | Filter facets read from the library's metadata schema. |
| Provenance / quality / usage | asset provenance + quality + usage fields | Read-only view. |
| Reference-into-task action | New Tasks intake (Hot Follow / Matrix Script / Digital Anchor `reference_assets[]`) | B-roll page does not create the packet. |
| Promote action | async review-gated asset promote boundary | UI emits intent; Asset Library object is authored downstream after review. |
| Available-to-lines display | asset library object's line-allowlist | Read-only. |

## Frozen Product Decisions

Authority: `docs/product/broll_asset_supply_freeze_v1.md`.

1. **Filter taxonomy**: all eight candidate facets are first-class for the first wiring pass: `line`, `topic`, `style`, `language`, `role_id`, `scene`, `variation_axis`, `quality_threshold`. All except `quality_threshold` allow multi-select. All are operator-visible, with `role_id` and `variation_axis` hidden by context when not applicable.
2. **Promote target semantics**: Promote creates a new asset through an async review-gated promote intent. It does not version an existing asset in this round. Operator receives request status, not immediate reusable asset truth.
3. **License / source / reuse policy fields**: mandatory fields, `source` enum, `license` enum, and `reuse_policy` enum are frozen in the product freeze doc. Reuse restriction is operator-visible as read-only policy; raw license/audit/internal-risk fields are admin-only.
4. **Canonical / reusable marking**: admin-only state with operator-visible read-only badges. Canonical is not equal to reusable; every canonical asset must be reusable, but reusable assets need not be canonical.
5. **Detail actions**: `archive`, `deprecate`, `supersede`, `unlink`, and `replace_preview` are not operator-visible actions. They move to the backend/admin management control page.
6. **Artifact -> Asset hand-off**: UI can initiate promote intent only. Admin/review-gated promote creates a new Asset Library object; artifact remains in Artifact Store and keeps task/delivery ownership.
7. **Reference-into-task pre-population**: mapping table is frozen in the product freeze doc, including `role_ref`, `reference_video`, `template`, `variation_axis`, `background`, `broll`, `product_shot`, `scene_pack_ref`, and `audio_ref`.

## Deferred Items

Deferred beyond this product freeze and not required for first B-roll wiring:

- Facet value administration UI.
- Bulk asset import.
- Bulk promote.
- Asset versioning as the primary promote path.
- Operator-side archive / deprecate / supersede / unlink / replace-preview.
- Provider/tool/runtime metadata on the asset surface.

No deferred item may be treated as implicit wiring scope.

---

## Phase 2 close-out — review summary across all four deliverables

Phase 2 outputs:

1. [Board & New Tasks low-fi](surface_task_area_lowfi_v1.md) — extended with state buckets, line-first New Tasks form, Mermaid state transitions, consolidated contract mapping.
2. [Workbench core low-fi](surface_workbench_lowfi_v1.md) — extended with the four named generic panels (`content_structure` / `scene_plan` / `audio_plan` / `language_plan`), L2 artifact-facts strip, L3 attempt/gate/advisory strip, single line-specific slot serving all three lines.
3. [Delivery center low-fi](surface_delivery_center_lowfi_v1.md) — extended with explicit Final / Required / Optional / Publish Action zoning, manifest+metadata display, publish feedback visibility, derived-publish-gate-driven enablement.
4. [Hot Follow line panel low-fi](panel_hot_follow_subtitle_authority_lowfi_v1.md) — new file completing the line-panel set alongside the Matrix Script and Digital Anchor panels.
5. This file — B-roll / Asset Supply low-fi (product-frozen).

### Ready for evaluation review

- Board + New Tasks IA: state buckets, line-first creation, post-create routing.
- Workbench skeleton with all three line-specific panels mounted into a single right-rail slot.
- Delivery zoning with Optional non-blocking guarantee.
- Hot Follow line panel structure (subtitle authority / current source / dub-compose legality / helper explanation).

### Product field freeze

- B-roll filter taxonomy is frozen in `docs/product/broll_asset_supply_freeze_v1.md`.
- B-roll promote target semantics are frozen as async review-gated create-new-asset intent.
- B-roll license / source / reuse policy field set is frozen.
- B-roll canonical / reusable marking is frozen as admin-only state with operator-visible read-only badges.
- Reference-into-task pre-population mapping per `asset_type` is frozen.

### Pending engineering wiring confirmation

- Derived publish gate exposure on packet evidence (Delivery `Publish Action` enablement).
- Derived `publishable` projection feeding the Board's third state bucket.
- L2 artifact-facts payload shape for the Workbench top strip.
- L3 `current_attempt` field shape for the Workbench right-rail strip and Hot Follow panel.
- `line_specific_refs[]` resolution for the unified Workbench slot mount key, including Hot Follow's `hot_follow_subtitle_authority` / `hot_follow_dub_compose_legality` ref ids.
- Validator head-reason field for the Board blocked-chip and Delivery "Why disabled?" hint.

### Discipline check (red lines, all four files)

- No provider / model / vendor / engine selector anywhere.
- No UI-authored truth — every chip cites L2 / L3 / derived gate / contract field.
- Tool backstage and operator surfaces remain separate.
- Optional / Scene Pack items never block publish.
- All three line-specific panels mount inside the unified Workbench skeleton, not as standalone pages.
- Asset and Artifact stores remain strictly separated.
