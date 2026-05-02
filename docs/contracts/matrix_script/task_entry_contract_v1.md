# Matrix Script Task Entry Contract v1

Date: 2026-04-27
Status: Phase A landing (Matrix Script First Production Line Wave — `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §6 Phase A)
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §3, §4, §6 Phase A, §7
- `docs/contracts/matrix_script/packet_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md` (matrix_script row)
- `docs/design/surface_task_area_lowfi_v1.md`

## Purpose

Declare the **operator-facing entry surface** by which a Matrix Script task is initiated, and the **mapping rule** by which that entry projects onto the frozen Matrix Script packet truth (`schemas/packets/matrix_script/packet.schema.json` + `docs/contracts/matrix_script/packet_v1.md`).

This contract is the Phase A deliverable of the Matrix Script First Production Line Wave. It does not author packet truth; it declares which operator inputs are accepted at task creation, and which packet fields each input is allowed to seed.

## Ownership

- Owner: product (entry-surface author) + design (surface mapping)
- Runtime consumers: future task-creation path (Phase B+), packet validator (rejects vendor pins / state fields regardless of entry origin)
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, provider adapters, frontend platform

## Scope discipline (normative)

This contract:
1. defines the **closed set** of fields the Matrix Script task entry MAY accept;
2. classifies each field as **line truth** (projects onto a packet field) or **operator hint** (seeds a packet authoring step but is itself non-truth);
3. classifies each field as **required**, **optional**, or **deferred**;
4. names what entry-time inputs are explicitly **forbidden** (provider/model selection, status-shape fields, donor-side concepts);
5. names what is **deferred** to Phase B (Workbench Variation Surface), Phase C (Delivery Binding), Phase D (Publish Feedback Closure).

This contract does NOT:
- define runtime task creation behavior;
- redeclare packet truth;
- introduce a second source of state or task truth;
- name vendors / models / providers / engines (validator rule R3);
- attach truth-shape state fields (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`) to any entry field (validator rule R5);
- re-version the Matrix Script packet, schema, or sample.

## Entry field set (closed)

The Matrix Script task entry accepts exactly the fields below. The set is closed at v1; additions require a re-version of this contract.

| entry field         | discipline | classification     | line truth? | seeds (packet path)                                                         | authority (generic contract)                                       |
| ------------------- | ---------- | ------------------ | ----------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `topic`             | required   | operator hint      | no          | `metadata.notes` (free-form trail) + downstream Phase B authoring seed       | `factory_input_contract_v1` (operator metadata envelope)           |
| `source_script_ref` | required   | line truth (asset) | yes (opaque ref) | downstream `slot_pack.delta.slots[].body_ref` (resolved by Phase B authoring; entry only carries the opaque handle) | `factory_input_contract_v1` (`source_script` per `asset_supply_matrix_v1`) |
| `language_scope`    | required   | line truth         | yes         | `slot_pack.delta.slots[].language_scope` (`source_language`, `target_language[]`) | `factory_language_plan_contract_v1` (`g_lang`)                      |
| `target_platform`   | required   | operator hint      | no          | `metadata.notes` (free-form trail); does NOT bind delivery — delivery binding is Phase C | `factory_input_contract_v1` (operator metadata envelope)           |
| `variation_target_count` | required | operator hint  | no          | seeds Phase B authoring of `variation_matrix.delta.cells[]` cardinality; does NOT itself become a packet field | `factory_input_contract_v1` (operator metadata envelope)           |
| `audience_hint`     | optional   | operator hint      | no          | seeds Phase B selection within `variation_matrix.delta.axes[axis_id="audience"].values[]` (axis values are packet truth; the hint is not) | `factory_input_contract_v1` (operator metadata envelope)           |
| `tone_hint`         | optional   | operator hint      | no          | seeds Phase B selection within `variation_matrix.delta.axes[axis_id="tone"].values[]`     | `factory_input_contract_v1` (operator metadata envelope)           |
| `length_hint`       | optional   | operator hint      | no          | seeds Phase B `slot_pack.delta.slots[].length_hint` and/or `variation_matrix.delta.axes[axis_id="length"]` range pick | `factory_input_contract_v1` (operator metadata envelope)           |
| `product_ref`       | optional   | operator hint      | no          | `metadata.notes` (free-form trail)                                            | `factory_input_contract_v1` (operator metadata envelope)           |
| `operator_notes`    | optional   | operator hint      | no          | `metadata.notes`                                                              | `factory_input_contract_v1` (operator metadata envelope)            |

Required vs optional discipline matches the `matrix_script` column of `docs/product/asset_supply_matrix_v1.md` for the `source_script` and `language_scope_decl` rows. Other entry fields are operator hints and are required only as authoring scaffolding for Phase B; they never become packet line truth.

## Line-truth vs operator-hint rule

- **Line truth** entries are the only entries that appear (after Phase B authoring) inside the packet's `line_specific_refs[].delta` blocks or generic-ref shapes. Line-truth content is owned by the packet, never by the entry surface.
- **Operator hint** entries seed Phase B authoring decisions but are themselves stored only as free-form trail in `metadata.notes` (or carried in an out-of-packet authoring scratch — to be defined in Phase B). They MUST NOT mutate any closed kind-set (`axis_kind_set`, `slot_kind_set`).
- An entry surface that promotes an operator hint into a packet truth field without going through Phase B authoring is a **violation** of this contract.

## Required vs optional (entry-time)

- Required: `topic`, `source_script_ref`, `language_scope`, `target_platform`, `variation_target_count`.
  - `source_script_ref` and `language_scope` are required by the asset supply matrix for the `matrix_script` line; absence MUST block task creation.
  - `topic`, `target_platform`, `variation_target_count` are required by this entry contract as the minimum operator-hint scaffolding so Phase B authoring has enough seed to construct a non-trivial variation matrix; absence MUST block task creation at the entry surface, but their absence is NOT a packet-truth gate (the packet validator does not see them).
- Optional: `audience_hint`, `tone_hint`, `length_hint`, `product_ref`, `operator_notes`.

## Deferred to later phases (entry surface MUST NOT collect)

The following are explicitly out of scope for Phase A entry. Any attempt to collect them at task entry is a violation of this contract.

| concern                          | deferred to                                                       |
| -------------------------------- | ----------------------------------------------------------------- |
| explicit `variation_matrix.delta.cells[]` enumeration | Phase B (Workbench Variation Surface)              |
| explicit `variation_matrix.delta.axes[]` authoring   | Phase B (Workbench Variation Surface)              |
| `slot_pack.delta.slots[]` authoring (slot_id, binds_cell_id) | Phase B (Workbench Variation Surface)      |
| `delivery` binding, manifest, deliverable selection           | Phase C (Delivery Binding)                |
| `result_packet_binding` deliverable wiring                    | Phase C (Delivery Binding)                |
| `publish_feedback` projection / variation_id-level feedback   | Phase D (Publish Feedback Closure)        |
| provider / model / vendor / engine selection                  | **never** at entry surface (validator R3) |
| status / ready / done / delivery_ready / final_ready / publishable | **never** at entry surface (validator R5) |
| donor (SwiftCraft) module identity                            | **never** at entry surface                |
| Digital Anchor, W2.2, W2.3 concerns                           | out of this wave entirely                  |

## Forbidden at entry surface

- Any field named or shaped as `vendor_id`, `model_id`, `provider`, `provider_id`, `engine_id` (validator R3).
- Any field named or shaped as `status`, `state`, `phase`, `ready`, `done`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable` (validator R5; restated by packet schema `metadata.not.anyOf`).
- Any donor-side concept: `donor_*`, `swiftcraft_*`, absorption-module names.
- Any second source of task / state truth (envelope §Forbidden).
- Any cross-line concern (Hot Follow, Digital Anchor, Avatar, VideoGen).
- Any frontend exposure of `vendor_id` / `model_id` / `donor_*` per `docs/product/asset_supply_matrix_v1.md` §Decoupling rules item 7.

## Mapping note (entry → packet)

Notation: `entry.<field>  →  packet.<json-pointer-ish path>`.

```
entry.topic                    →  metadata.notes (appended; non-truth trail)
entry.source_script_ref        →  (Phase B authoring) line_specific_refs[ref_id="matrix_script_slot_pack"].delta.slots[*].body_ref
                                  (entry carries opaque handle only; resolution to slot bodies is Phase B)
entry.language_scope           →  (Phase B authoring) line_specific_refs[ref_id="matrix_script_slot_pack"].delta.slots[*].language_scope
                                  bound by g_lang allowed values
entry.target_platform          →  metadata.notes (appended; non-truth trail)
                                  (delivery target binding is Phase C)
entry.variation_target_count   →  (Phase B authoring scaffold) drives count of
                                  line_specific_refs[ref_id="matrix_script_variation_matrix"].delta.cells[]
                                  (does NOT appear as a packet field)
entry.audience_hint            →  (Phase B authoring scaffold) selection within
                                  line_specific_refs[ref_id="matrix_script_variation_matrix"].delta.axes[axis_id="audience"].values[]
entry.tone_hint                →  (Phase B authoring scaffold) selection within
                                  .delta.axes[axis_id="tone"].values[]
entry.length_hint              →  (Phase B authoring scaffold) either
                                  .delta.axes[axis_id="length"] range pick
                                  and/or slot_pack.delta.slots[*].length_hint
entry.product_ref              →  metadata.notes (appended; non-truth trail)
entry.operator_notes           →  metadata.notes (appended; non-truth trail)
```

Mapping discipline:

- Only `entry.source_script_ref` and `entry.language_scope` cross from entry surface to packet **truth** (line-specific delta). All other entries cross only to `metadata.notes` (non-truth trail) or to Phase B authoring scaffolding (out of packet entirely).
- Closed kind-sets (`axis_kind_set`, `slot_kind_set`) are NOT widened by any entry field. Hints select among existing values; they never add values.
- `binding.capability_plan[]`, `binding.worker_profile_ref`, `binding.deliverable_profile_ref`, `binding.asset_sink_profile_ref` are **NOT** populated from the entry surface. They are static for the Matrix Script line per `docs/contracts/matrix_script/packet_v1.md` §Capability plan and §Binding profiles.
- `evidence.ready_state` is **NOT** writable from the entry surface. `ready_state` is one-way projection from validator output (`docs/design/surface_task_area_lowfi_v1.md` §Gate Truth Rule).

## Source script ref shape (addendum, 2026-05-02)

Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.A.

`source_script_ref` is an opaque reference handle. The entry surface MUST reject any value that carries script body text, document prose, or any other non-reference payload. The server-side guard at `gateway/app/services/matrix_script/create_entry.py` enforces the closed shape declared here; the operator-facing input at `gateway/app/templates/matrix_script_new.html` mirrors the same shape via `pattern` / `maxlength`.

A submitted value is accepted only when it matches one of the two closed shapes below.

1. **URI with closed scheme.** Scheme prefix from the closed set followed by `://` and at least one non-whitespace character.
   - Closed scheme set: `content`, `task`, `asset`, `ref`, `s3`, `gs`, `https`, `http`.
   - Example: `content://matrix-script/source/001`.
2. **Bare token id.** `^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$`. No whitespace, no embedded scheme separator (`://`). Used for short opaque content storage handles or external system ids.
   - Example: `MS-SRC-2026-04-001`.

Independent of the shape match, the value MUST also satisfy:

- single line (no `\n` or `\r`);
- no whitespace anywhere;
- length ≤ 512 characters.

On any rejection the entry surface raises the existing entry-validation error type (HTTP 400) with a localised message that names the field and the constraint. The rejection MUST happen before `build_matrix_script_task_payload` runs, so the payload-builder never sees body text.

The closed scheme set is exhaustive at v1; widening it requires a re-version of this contract. Narrowing it is permitted only if no live trial sample relies on the removed scheme.

## Acceptance (Phase A)

Phase A is green only when:

1. The entry field set above is the exact closed set used by any Matrix Script task-creation surface.
2. Every required entry field is collected; absence blocks task creation at entry.
3. No forbidden field is collected, displayed, or stored at entry.
4. Every line-truth entry maps onto a packet path that is reachable from the existing Matrix Script schema/contract; no new packet field is invented.
5. Every operator-hint entry maps either to `metadata.notes` or to Phase B authoring scaffolding; none is promoted to packet truth at entry time.
6. Implementation, if any, is Matrix-Script-only; no code path under `digital_anchor`, no provider/adapter touch, no Hot Follow business-logic change.

## What Phase A intentionally does NOT add

- No workbench variation authoring surface (Phase B).
- No delivery center binding (Phase C).
- No publish feedback projection (Phase D).
- No provider/model selection control (forbidden at all phases).
- No new packet schema / sample / contract version.
- No Digital Anchor entry (out of this wave).
- No Hot Follow change.
- No frontend platform rebuild.
- No runtime task-creation implementation in this Phase A landing — this contract is the surface-first definition; engineering implementation is sequenced separately and bounded by this contract.

## Remaining blockers before Phase B

1. Phase B requires this Phase A entry contract to be reviewed and accepted as the authority for the operator-supplied seed feeding workbench authoring.
2. Phase B requires the workbench authoring surface to consume the `entry.*` seed without re-authoring it — i.e. the workbench MUST start from this entry's projection into `metadata.notes` and Phase B authoring scaffolding, not from a freshly invented form.
3. Phase B requires `axis_kind_set` and `slot_kind_set` to remain frozen as declared in `docs/contracts/matrix_script/packet_v1.md` §LS1 / §LS2; this Phase A contract relies on that freeze to keep `audience_hint` / `tone_hint` / `length_hint` mapping stable.

## References

- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`
