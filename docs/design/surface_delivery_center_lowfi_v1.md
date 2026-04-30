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
