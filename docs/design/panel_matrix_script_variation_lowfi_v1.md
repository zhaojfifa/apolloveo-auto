# Panel — Matrix Script Variation (Low-fi v1)

**Embedded in**: Workbench Active Capability Pane, when the selected `capability_plan[].kind` is `variation`.
**Line**: `matrix_script`
**Backed by**: `line_specific_refs[ref_id=matrix_script_variation_matrix]` and `line_specific_refs[ref_id=matrix_script_slot_pack]`.

## Layout (low-fi)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MATRIX SCRIPT — Variation Panel                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  AXES                                                                        │
│  ─────                                                                       │
│  ┌──────────┬─────────────┬──────────────────────────┬──────────┐           │
│  │ axis_id  │ kind        │ values                   │ required │           │
│  ├──────────┼─────────────┼──────────────────────────┼──────────┤           │
│  │ tone     │ categorical │ formal · casual · playful│   yes    │           │
│  │ audience │ enum        │ b2b · b2c · internal     │   yes    │           │
│  │ length   │ range       │ {min:30, max:120, step:15│   no     │           │
│  └──────────┴─────────────┴──────────────────────────┴──────────┘           │
├─────────────────────────────────────────────────────────────────────────────┤
│  CELLS  ×  SLOTS                                                             │
│  ───────────────                                                             │
│  ┌──────────┬───────────────────────────────────┬──────────────┬─────────┐ │
│  │ cell_id  │ axis selections                   │ script_slot  │ notes   │ │
│  ├──────────┼───────────────────────────────────┼──────────────┼─────────┤ │
│  │ cell_001 │ tone=formal · audience=b2b · 60   │ slot_001 ↗   │ …       │ │
│  │ cell_002 │ tone=casual · audience=b2c · 45   │ slot_002 ↗   │         │ │
│  └──────────┴───────────────────────────────────┴──────────────┴─────────┘ │
│                                                                              │
│  Slot detail (when a row is expanded):                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │ slot_id: slot_001     binds_cell_id: cell_001     length_hint: 60      ││
│  │ language_scope:                                                         ││
│  │   source: en-US                                                         ││
│  │   target: zh-CN, ja-JP                                                  ││
│  │ body_ref: content://matrix_script/v1/slot_001          [open]           ││
│  └────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Regions

| Region | Role | Notes |
|---|---|---|
| Axes table | Renders `variation_matrix.delta.axes[]` | One row per axis. Read-mostly: when `ready_state ∈ {ready}`, axes are addable/removable; otherwise read-only. |
| Cells × Slots table | Renders `variation_matrix.delta.cells[]` joined to `slot_pack.delta.slots[]` via `script_slot_ref` ↔ `slot_id` | Each cell row links to exactly one slot via `cells[].script_slot_ref`. |
| Slot detail (expand) | Renders `slot_pack.delta.slots[]` | Shows `language_scope`, `body_ref`, `length_hint`. |

## Axis row binding

| Column | Source |
|---|---|
| `axis_id` | `variation_matrix.delta.axes[].axis_id` |
| `kind` | `variation_matrix.delta.axes[].kind` (allowed values per `axis_kind_set`) |
| `values` | `variation_matrix.delta.axes[].values` (rendered shape varies by `kind`: list for categorical/enum, `{min,max,step}` block for range) |
| `required` | `variation_matrix.delta.axes[].is_required` |

## Cell row binding

| Column | Source |
|---|---|
| `cell_id` | `variation_matrix.delta.cells[].cell_id` |
| Axis selections | `variation_matrix.delta.cells[].axis_selections` (rendered key=value per axis) |
| Script slot link | `variation_matrix.delta.cells[].script_slot_ref` (clickable jump to `slot_pack.delta.slots[slot_id=...]`) |
| Notes | `variation_matrix.delta.cells[].notes` |

## Slot detail binding

| Field | Source |
|---|---|
| `slot_id` | `slot_pack.delta.slots[].slot_id` |
| `binds_cell_id` | `slot_pack.delta.slots[].binds_cell_id` |
| `language_scope.source_language` | `slot_pack.delta.slots[].language_scope.source_language` |
| `language_scope.target_language` | `slot_pack.delta.slots[].language_scope.target_language` |
| `body_ref` | `slot_pack.delta.slots[].body_ref` |
| `length_hint` | `slot_pack.delta.slots[].length_hint` |

## Discipline

- The panel renders only `delta` content carried by the two `lineSpecificRef` entries. It never fabricates axes, cells, or slots that are not in the contract object.
- `axis_kind_set` and `slot_kind_set` come from the contract delta and constrain which values are pickable in the (gated) authoring affordance — the panel **does not** widen these sets.
- The integrity rule "every `cells[].script_slot_ref` resolves to a `slots[].slot_id`" is shown as a non-blocking inline warning when violated; it is **not** authored as a new state — the badge color follows `evidence.ready_state`.
- No vendor / model / provider / engine fields. No "tone engine" or "voice provider" affordance.
- No donor / supply UI.

## Contract Mapping Notes

| UI element | Contract object | Contract path |
|---|---|---|
| Axes table | `variation_matrix.delta.axes` | matrix_script `$defs.lineSpecificRef.properties.delta` (line contract: `docs/contracts/matrix_script/variation_matrix_contract_v1.md`) |
| Axis kind constraint | `variation_matrix.delta.axis_kind_set` | same |
| Cells table | `variation_matrix.delta.cells` | same |
| Cell→Slot link | `cells[].script_slot_ref` ↔ `slots[].slot_id` | matrix_script variation_matrix + slot_pack |
| Slot detail | `slot_pack.delta.slots` | `docs/contracts/matrix_script/slot_pack_contract_v1.md` |
| Slot kind constraint | `slot_pack.delta.slot_kind_set` | same |
| Language scope | `slot_pack.delta.slots[].language_scope` | same; ultimately rooted in `factory_language_plan_contract_v1` (`g_lang`) |
| Embedding capability | `binding.capability_plan[kind=variation]` | packet.schema.json `$defs.capabilityEntry.properties.kind.enum` |

**Embedding rule**: This panel is mounted only when the active spine row's `kind === "variation"`. It never appears in any other line's Workbench.
