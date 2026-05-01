# Surface 3 — Delivery Center (Low-fi v1)

**Purpose**: The packaged-output surface. Renders what the packet's `binding.deliverable_profile_ref` and `binding.asset_sink_profile_ref` resolve to, projected through the generic delivery contract (`g_deliv`). It does **not** invent delivery state; it only renders the projection of contract objects already produced by the line.

## Layout (low-fi)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DELIVERY CENTER — matrix_script · v1               Gate: ● ready         │
├──────────────────────────────────────────────────────────────────────────┤
│  DELIVERABLE PROFILE                                                      │
│  ────────────────────                                                     │
│  ref: deliverable_profile_matrix_script_v1                                │
│  contract: factory_delivery_contract_v1                                   │
│                                                                           │
│  ┌─ Bundle ─────────────────────────────────────────────────────────┐    │
│  │  Items: <projected from delivery contract>                        │    │
│  │  (E.g., script slots, language variants, subtitle tracks…)        │    │
│  │  Each row: name · contract type · language · [view]               │    │
│  └───────────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────────┤
│  ASSET SINK                                                               │
│  ──────────                                                               │
│  ref: asset_sink_profile_matrix_script_v1                                 │
│  destination shape: <projected from delivery contract>                    │
│  [ Open sink view ]                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  EVIDENCE STRIP   reference_line: hot_follow   validator_report: [open]  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Regions

| Region | Role | Notes |
|---|---|---|
| Header | Identity + gate | Same `line_id` / `packet_version` / gate badge contract as Workbench. |
| Deliverable Profile | Projection of `deliverable_profile_ref` | A bundle list whose items come from the resolved delivery contract; UI does not author item shape. |
| Asset Sink | Projection of `asset_sink_profile_ref` | Read-only view of where assets land per the delivery contract. |
| Evidence Strip | Reference + validator report | Identical contract to Workbench. |

## What the Delivery Center renders

| UI element | Source |
|---|---|
| Deliverable profile reference label | `binding.deliverable_profile_ref` |
| Asset sink profile reference label | `binding.asset_sink_profile_ref` |
| Bundle items | Resolved via `factory_delivery_contract_v1` (path appears in `generic_refs[ref_id=g_deliv]`) |
| Per-item language column | Pulls from the resolved item's language scope, ultimately rooted in `factory_language_plan_contract_v1` |
| Gate badge | `evidence.ready_state` |
| Reference baseline | `evidence.reference_line` |

## What the Delivery Center forbids

- No `delivery_ready`, `final_ready`, `publishable`, `done`, `ready`, `state`, `phase`, `current_attempt` flags. The metadata schema's `not` clause forbids them; the surface honors that by never rendering or authoring such flags.
- No vendor / model / provider / engine column.
- No donor / supply / sourcing column.
- No "publish" CTA. Publishing is not in scope for the surface freeze; the Delivery Center is read-only.
- No retry / re-run controls. Re-runs (when allowed) are exposed in the Workbench, not here.

## Gate-state effect

| `evidence.ready_state` | Delivery Center behavior |
|---|---|
| `draft`, `validating`, `gated` | Show banner explaining gate is not cleared; bundle list still renders if any contract objects exist, all rows read-only. |
| `ready` | Full bundle visible, items linkable. |
| `frozen` | Full bundle visible, items linkable; banner: "Packet frozen — bundle is sealed." |

## Contract Mapping Notes

| UI element | Contract object | Contract path |
|---|---|---|
| Deliverable profile ref label | `binding.deliverable_profile_ref` | packet.schema.json `$defs.binding.properties.deliverable_profile_ref` |
| Asset sink profile ref label | `binding.asset_sink_profile_ref` | packet.schema.json `$defs.binding.properties.asset_sink_profile_ref` |
| Bundle item shape | `factory_delivery` generic ref | `generic_refs[ref_id=g_deliv].path = docs/contracts/factory_delivery_contract_v1.md` |
| Per-item language | `factory_language_plan` generic ref | `generic_refs[ref_id=g_lang].path = docs/contracts/factory_language_plan_contract_v1.md` |
| Gate badge | `evidence.ready_state` | `$defs.evidence.properties.ready_state.enum` |
| Reference badge | `evidence.reference_line` | `$defs.evidence.properties.reference_line.const` |

**Authority Rule**: Delivery Center is a *view*, not an *author*. If a field is not present in the resolved contract objects, the Delivery Center renders nothing — it never fabricates a row.

---

## Extension — Final / Required / Optional / Publish zoning

> Tightens the Delivery Center to match `ApolloVeo_Operator_Visible_Surfaces_v1.md` §5.4. Splits the page into four explicit zones plus a manifest/metadata display block and a publish-feedback visibility block. Optional items never block publish. Publish action is enabled only by a derived publish gate.

### Page Goal

Result-oriented surface: show the Final Video, list Required Deliverables, separate Optional / Non-blocking items as visually subordinate, and render Publish Action with derived-gate-driven enablement only. The page never invents publishability, never authors deliverable truth, and never offers vendor/model/provider controls.

### Extended low-fi layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  DELIVERY — <line> · <packet_version>      Gate: ●ready                    │
├────────────────────────────────────────────────────────────────────────────┤
│  A. FINAL VIDEO                                                             │
│  ─────────────                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │   [ video preview ]                                                  │  │
│  │   final.mp4 · resolution · duration · language                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────┤
│  B. REQUIRED DELIVERABLES (gate publish)                                    │
│  ──────────────────────────                                                 │
│   · subtitle track(s)        ✓                                              │
│   · audio track(s)           ✓                                              │
│   · metadata projection      ✓                                              │
│   · manifest                 ✓                                              │
│   · per-line required items  ✓ / pending                                   │
├────────────────────────────────────────────────────────────────────────────┤
│  C. OPTIONAL / NON-BLOCKING (never gate publish — visually subordinate)     │
│  ──────────────────────────                                                 │
│   · scene_pack    ◐ partial   (does NOT block publish)                      │
│   · helper exports                                                          │
│   · variation attribution exports                                           │
├────────────────────────────────────────────────────────────────────────────┤
│  D. PUBLISH ACTION                                                          │
│  ────────────────                                                           │
│   Publish gate: ● enabled  (Final ✓ + Required ✓)                           │
│   [ Publish ]                                                               │
│   Why disabled? — surfaces the head reason from the publish gate, never UI- │
│   composed.                                                                 │
├────────────────────────────────────────────────────────────────────────────┤
│  MANIFEST / METADATA DISPLAY (read-only)                                    │
│  ────────────────────────────                                               │
│   manifest: [view JSON]   metadata_projection: [view JSON]                  │
├────────────────────────────────────────────────────────────────────────────┤
│  PUBLISH FEEDBACK VISIBILITY (read-only mirror of L4 publish status)        │
│  ────────────────────────────                                               │
│   last publish: 2026-04-30T12:31Z · status: success · channel: <...>        │
│   variation attribution (matrix_script): see line panel                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Zone semantics

| Zone | Source | Gating role |
|---|---|---|
| A. Final Video | `factory_delivery_contract` → final video item | Required for publish — without it, publish gate is off. |
| B. Required Deliverables | `factory_delivery_contract` required items + per-line required outputs | All must resolve before publish gate can flip on. |
| C. Optional / Non-blocking | `factory_delivery_contract` optional items (`scene_pack`, helper exports, attribution exports) | **Never** affect publish gate; visually subordinate styling. |
| D. Publish Action | derived publish gate (read-only projection) | Button enablement is a pure projection, never UI-computed. |
| Manifest / metadata block | `manifest`, `metadata_projection` | Display only, no edit. |
| Publish feedback block | L4 publish status mirror | Read-only — UI never authors publish outcome. |

### Publish gate rule

The Publish button is enabled iff the gateway-exposed derived publish gate evaluates to true. The Delivery Center does not assemble that boolean from individual checkmarks — it consumes the projection. The "Why disabled?" hint is the head reason returned by the publish gate, rendered verbatim.

### Optional non-blocking — hard rule

Optional items render with subordinate styling (smaller, grayed) and never appear in the Required list. The publish gate does not consider them. This is the visual enforcement of the §5.4 red line that Scene Pack is explicitly non-blocking.

### Line-specific feedback

| Line | Publish feedback specifics rendered here |
|---|---|
| Hot Follow | Final + subtitles + dubbed audio + pack; current attempt vs. historical successful delivery deltas surfaced (link to Workbench). |
| Matrix Script | Multi-variation final list with `attribution_id` per row; publish feedback per variation. |
| Digital Anchor | Multi-language version list, `role_usage` / `scene_usage` / `language_usage`, delivery pack + manifest. |

### Extended Contract Mapping

| UI element | Contract object |
|---|---|
| Final Video | `factory_delivery_contract` final item |
| Required Deliverables list | `factory_delivery_contract` required items |
| Optional / Non-blocking list | `factory_delivery_contract` optional items |
| Publish gate / button enablement | derived publish gate (gateway projection) |
| Manifest display | `manifest` |
| Metadata display | `metadata_projection` |
| Publish feedback | L4 publish status (read-only mirror) |

### Notes / Known Deferrals
- **Publish target picker**: not in scope. The publish action posts to whatever channel the line's delivery contract resolves to.
- **Publish retry / unpublish controls**: deferred — out of §5.4 scope.
- **Variation attribution surfacing in Matrix Script**: detailed view lives in the line panel; Delivery Center shows per-row `attribution_id` only.
- **Wiring of derived publish gate**: needs engineering confirmation that the gateway exposes a single projected boolean + head reason; otherwise Publish Action zone renders disabled with a "publish gate not yet wired" notice.
