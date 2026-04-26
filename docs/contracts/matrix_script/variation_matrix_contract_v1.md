# Matrix Script · Variation Matrix Contract v1

Date: 2026-04-26
Status: Frozen for P2 entry review (line-specific delta contract; consumed by packet validator)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`; parent packet `docs/contracts/matrix_script/packet_v1.md`
Owner: Product
Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Purpose

Declare the **variation matrix delta** that the Matrix Script line adds on top of the factory-generic input and content-structure contracts. The matrix is the planning artifact that turns one source script into a grid of derivative scripts; runtime variation execution is out of scope.

This contract describes:

- the closed axis-kind set the matrix may use
- the shape of `axes[]` and `cells[]` declarations
- the binding from cells to `matrix_script_slot_pack` slots
- the prohibitions that keep the matrix free of state truth and vendor pins

This contract does NOT describe runtime planners, donor absorption, provider clients, or any second source of task / state truth.

## Identity

- `ref_id`: `matrix_script_variation_matrix`
- `binds_to`: `g_input`, `g_struct`
- Parent packet: `docs/contracts/matrix_script/packet_v1.md`
- Version: `v1`

## Closed sets

- `axis_kind_set`: `{categorical, range, enum}` — adding a kind requires a packet re-version

## Delta fields

### `axes[]`

Ordered list of variation axes. Each entry declares:

| field         | type                         | notes                                                                 |
| ------------- | ---------------------------- | --------------------------------------------------------------------- |
| `axis_id`     | string (stable)              | e.g. `tone`, `audience`, `length`, `cta_style`                        |
| `kind`        | enum (`axis_kind_set`)       | one of `categorical` / `range` / `enum`                               |
| `values`      | list (categorical/enum) OR object `{min, max, step}` (range) | drawn from line-declared tokens |
| `is_required` | boolean                      | required axes must have at least one selection per cell               |

Rules:

- `axis_id` MUST be unique within the packet
- `categorical` and `enum` axes MUST list at least one value
- `range` axes MUST declare `min`, `max`, and `step` as integers or numeric tokens
- The contract does NOT enumerate value tokens; tokens are line-declared and may evolve across packet versions

### `cells[]`

Declared variation cells. Each entry declares:

| field             | type            | notes                                                                          |
| ----------------- | --------------- | ------------------------------------------------------------------------------ |
| `cell_id`         | string (stable) | unique within the packet                                                       |
| `axis_selections` | object          | map `axis_id → value token (or range pick)` drawn from the matching axis decl  |
| `script_slot_ref` | string          | id of a `matrix_script_slot_pack.slots[]` entry that owns this cell's body     |
| `notes`           | string (opt.)   | non-truth descriptive string                                                   |

Rules:

- `cell_id` MUST be unique within the packet
- Every required axis MUST be present in `axis_selections`
- Every value in `axis_selections` MUST be drawn from the corresponding axis declaration (categorical/enum token, or a range pick consistent with `min`/`max`/`step`)
- `script_slot_ref` MUST resolve to a slot declared in the sibling `matrix_script_slot_pack`
- Two cells MAY share an `axis_selections` map only when their `script_slot_ref` differs (e.g. primary vs. alternate slot for the same selection)

## Cross-binding rules

- `axes[]` and `cells[]` jointly define the matrix; neither is meaningful alone
- The matrix is consumed by the slot pack via `slots[].binds_cell_id`; the back-reference MUST round-trip with `cells[].script_slot_ref`
- The matrix MUST NOT redeclare any field shape owned by `factory_input_contract_v1` or `factory_content_structure_contract_v1` (validator rule R2)

## Forbidden

- any `status` / `ready` / `done` / `phase` / `current_attempt` / `delivery_ready` field (validator rule R5)
- any `vendor_id` / `model_id` / `provider` / `engine` field (validator rule R3)
- any embed of the full `factory_input` or `factory_content_structure` record shape (validator rule R2)
- any donor (SwiftCraft) module path or module-level reference
- any second source of task / state truth

## Surface implications

For Phase B (Surface Freeze), design MUST:

- render axis selectors only for axes declared in `axes[]` of the active packet
- never expose `axis_kind_set` membership as user-visible terminology
- never surface `vendor`, `model`, `provider`, or `donor` as part of the matrix UI

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
