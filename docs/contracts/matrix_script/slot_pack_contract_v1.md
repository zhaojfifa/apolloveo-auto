# Matrix Script · Slot Pack Contract v1

Date: 2026-04-26
Status: Frozen for P2 entry review (line-specific delta contract; consumed by packet validator)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`; parent packet `docs/contracts/matrix_script/packet_v1.md`
Owner: Product
Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Purpose

Declare the **slot pack delta** that the Matrix Script line adds on top of the factory-generic content-structure and language-plan contracts. The slot pack holds derivative script bodies by reference, declares per-slot language scope, and binds each slot to the variation matrix cell that consumes it.

This contract describes:

- the closed slot-kind set the pack may use
- the shape of `slots[]` declarations
- the binding from slots to `matrix_script_variation_matrix` cells and to language scope
- the prohibitions that keep the slot pack free of state truth, vendor pins, and embedded body text

This contract does NOT describe runtime body rendering, donor absorption, provider clients, or any second source of task / state truth.

## Identity

- `ref_id`: `matrix_script_slot_pack`
- `binds_to`: `g_struct`, `g_lang`
- Parent packet: `docs/contracts/matrix_script/packet_v1.md`
- Version: `v1`

## Closed sets

- `slot_kind_set`: `{primary, alternate, fallback}` — adding a kind requires a packet re-version

## Delta fields

### `slots[]`

Ordered list of script slots. Each entry declares:

| field             | type            | notes                                                                          |
| ----------------- | --------------- | ------------------------------------------------------------------------------ |
| `slot_id`         | string (stable) | unique within the packet                                                       |
| `binds_cell_id`   | string          | id of the `matrix_script_variation_matrix.cells[]` entry that owns this slot   |
| `language_scope`  | object          | `{source_language, target_language[]}` drawn from `g_lang` allowed values      |
| `body_ref`        | string (opaque) | content reference (e.g. content storage key); body text MUST NOT be embedded   |
| `length_hint`     | integer / range | non-truth hint for downstream planners                                         |
| `slot_kind`       | enum (opt.)     | one of `slot_kind_set`; default `primary` when omitted                         |

Rules:

- `slot_id` MUST be unique within the packet
- `binds_cell_id` MUST resolve to a cell declared in the sibling `matrix_script_variation_matrix`
- `language_scope.source_language` and each `target_language[]` token MUST be drawn from the values allowed by `factory_language_plan_contract_v1`
- Subtitle authority follows `g_lang`'s single-owner rule; the slot pack MUST NOT override it
- `body_ref` MUST be opaque and dereferenceable by content storage — the pack does not embed body text

## Cross-binding rules

- Every cell in `matrix_script_variation_matrix` with a `script_slot_ref` MUST resolve to a slot declared here; conversely, every slot's `binds_cell_id` MUST resolve to a declared cell
- A slot MAY be referenced by at most one cell as the `script_slot_ref` value; multi-cell binding is expressed by adding additional `alternate` / `fallback` slots
- The slot pack MUST NOT redeclare any field shape owned by `factory_content_structure_contract_v1` or `factory_language_plan_contract_v1` (validator rule R2)

## Forbidden

- any subtitle `authority` override that contradicts `g_lang`'s single-owner rule
- any `delivery_ready` / `publishable` / `final_ready` / `status` / `ready` / `done` field (validator rule R5)
- any `vendor_id` / `model_id` / `provider` / `engine` field (validator rule R3)
- any embed of the full `factory_content_structure` or `factory_language_plan` record shape (validator rule R2)
- any embedded body text — bodies are referenced by `body_ref` only
- any donor (SwiftCraft) module path or module-level reference

## Surface implications

For Phase B (Surface Freeze), design MUST:

- render slot collection slots only for the slot-kinds declared in the active packet
- expose `body_ref` only as a resolved content handle, never as a vendor or storage-provider id
- never surface `slot_kind_set` membership as user-visible terminology

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
