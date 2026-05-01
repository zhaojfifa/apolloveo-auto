# Surface 4 — B-roll / Asset Supply (Low-fi v1 — DRAFT)

> **Status: low-fi-draft pending product field freeze.** Layout and contract boundaries below are stable enough for review; the filter taxonomy, promote target semantics, and license/source policy are explicitly enumerated as open questions for the next freeze pass.

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

Per §5.5.B. Filter facets (subject to product freeze — see open questions): `line`, `topic`, `style`, `language`, `role_id`, `scene`, `variation_axis`, `quality_threshold`. The bar emits filter intent only; the asset list re-projects from the library response.

### C. Detail drawer

Per §5.5.C. Read-only view of `provenance`, `hash`/`version`, `quality`, `tags`, usage limits, available-to-lines list. No edit affordances on this drawer.

### D. Action area

Per §5.5.D, with strict UI-emits-intent-only semantics:

| Action | UI role | Truth boundary |
|---|---|---|
| Reference into task | Routes to New Tasks pre-populated with this asset's reference | New Tasks owns packet creation; B-roll only carries the asset_id forward. |
| Promote intent | Posts a promote request | Promote is owned by L2 ingestion / asset sink; UI never writes the new asset object. The button surfaces success/failure as a read-only mirror of the resulting library state. |
| Mark reusable / canonical | Placeholder per §5.5.D — emits intent only, may be admin-gated | Admin/governance ownership; UI never authors the canonical flag. |
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
| Promote action | promote flow boundary owned by L2 ingestion | UI emits intent; library object is authored downstream. |
| Available-to-lines display | asset library object's line-allowlist | Read-only. |

## Notes / Known Deferrals — open questions for product freeze

1. **Filter taxonomy**: which axes are first-class? §5.5.B lists 8 facets; freeze the canonical set and their value vocabularies before engineering wires the filter API.
2. **Promote target semantics**: does Promote attach to an existing asset (versioning) or seed a new asset object? Does Promote require admin review (§5.7 mentions asset promote audit) or can it ship asynchronously?
3. **License / source / reuse policy fields**: what fields are mandatory on every asset? what `source` / `license` enums are in scope this round?
4. **Canonical / reusable marking**: is this a single boolean, a workflow (proposed → canonical), or admin-only? §5.5.D marks it as a placeholder.
5. **Asset detail action set beyond Promote**: archive, deprecate, supersede — all currently out of scope; should they be admin-only (§5.7) or never operator-visible?
6. **Artifact → Asset boundary mechanics**: §2.3 and §5.5 require strict separation; the precise hand-off contract for promote should be confirmed before this page is wired.
7. **Reference-into-task pre-population**: which fields of the New Tasks form get pre-filled per `asset_type`? (e.g., `role_ref` → Digital Anchor role binding).

Until these are frozen, this page should be treated as a structural skeleton suitable for IA/UX review but not for engineering wiring of the action area.

---

## Phase 2 close-out — review summary across all four deliverables

Phase 2 outputs:

1. [Board & New Tasks low-fi](surface_task_area_lowfi_v1.md) — extended with state buckets, line-first New Tasks form, Mermaid state transitions, consolidated contract mapping.
2. [Workbench core low-fi](surface_workbench_lowfi_v1.md) — extended with the four named generic panels (`content_structure` / `scene_plan` / `audio_plan` / `language_plan`), L2 artifact-facts strip, L3 attempt/gate/advisory strip, single line-specific slot serving all three lines.
3. [Delivery center low-fi](surface_delivery_center_lowfi_v1.md) — extended with explicit Final / Required / Optional / Publish Action zoning, manifest+metadata display, publish feedback visibility, derived-publish-gate-driven enablement.
4. [Hot Follow line panel low-fi](panel_hot_follow_subtitle_authority_lowfi_v1.md) — new file completing the line-panel set alongside the Matrix Script and Digital Anchor panels.
5. This file — B-roll / Asset Supply low-fi (draft).

### Ready for evaluation review

- Board + New Tasks IA: state buckets, line-first creation, post-create routing.
- Workbench skeleton with all three line-specific panels mounted into a single right-rail slot.
- Delivery zoning with Optional non-blocking guarantee.
- Hot Follow line panel structure (subtitle authority / current source / dub-compose legality / helper explanation).

### Pending product field freeze

- B-roll filter taxonomy (which facets are first-class, what enums each takes).
- B-roll promote target semantics (versioning vs. new asset, admin gating).
- B-roll license / source / reuse policy field set.
- B-roll canonical / reusable marking workflow.
- Reference-into-task pre-population mapping per `asset_type`.

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

