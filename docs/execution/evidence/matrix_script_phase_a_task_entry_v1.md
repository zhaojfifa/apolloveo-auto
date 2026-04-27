# Matrix Script First Production Line Wave — Phase A Task Entry (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **Matrix Script First Production Line Wave** — Phase A (Task Entry)
- Status: Phase A landed; awaiting architect + reviewer signoff
- Authority:
  - `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §3, §4, §6 Phase A, §7, §8, §10
  - `docs/contracts/matrix_script/packet_v1.md`
  - `schemas/packets/matrix_script/packet.schema.json`
  - `schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json`
  - `docs/product/asset_supply_matrix_v1.md` (matrix_script row)
  - `docs/design/surface_task_area_lowfi_v1.md`
  - `docs/contracts/factory_input_contract_v1.md`
  - `docs/contracts/factory_language_plan_contract_v1.md`
  - `docs/contracts/factory_packet_envelope_contract_v1.md`
  - `docs/contracts/factory_packet_validator_rules_v1.md`

---

## 1. Scope

This evidence note covers Phase A of the Matrix Script First Production Line Wave: the **task entry surface** is established as a contract-driven landing that maps cleanly onto the frozen Matrix Script packet truth, without authoring any new line truth.

In scope:
- declaring the closed set of operator-facing entry fields the Matrix Script line accepts at task creation time;
- declaring which entry fields are line truth vs operator hint;
- declaring required vs optional vs deferred discipline;
- declaring the entry → packet mapping rule;
- minimum validation tests proving the contract's discipline;
- evidence / log / index write-back.

Out of scope (explicitly):
- workbench variation authoring surface (Phase B);
- delivery center binding (Phase C);
- publish feedback closure (Phase D);
- provider / model / vendor selection (forbidden at all phases);
- Digital Anchor;
- W2.2 / W2.3;
- Hot Follow business-logic changes;
- packet / schema / sample re-versioning;
- frontend platform rebuild;
- runtime task-creation code implementation (this Phase A is a docs-first / surface-first landing).

---

## 2. What Phase A adds

1. **Task Entry Contract v1** — `docs/contracts/matrix_script/task_entry_contract_v1.md`:
   - closed set of entry fields: `topic`, `source_script_ref`, `language_scope`, `target_platform`, `variation_target_count`, `audience_hint`, `tone_hint`, `length_hint`, `product_ref`, `operator_notes`;
   - per-field classification (line truth vs operator hint; required vs optional);
   - mapping note from each entry field to the Matrix Script packet path (or to Phase B authoring scaffolding for hints);
   - explicit deferral table (Phase B / C / D / never);
   - explicit forbidden-field list aligned to validator R3 / R5 and `metadata.not.anyOf`.

2. **Phase A validation tests** — `tests/contracts/matrix_script/test_task_entry_phase_a.py`:
   - asserts the task entry contract document exists at the canonical path;
   - asserts the entry surface accepts the intended input shape (closed entry-field set is present in the contract);
   - asserts every line-truth entry maps to a packet field reachable from the frozen Matrix Script schema (`schemas/packets/matrix_script/packet.schema.json`) or its line-specific contracts;
   - asserts no forbidden vendor/model/provider/engine token appears anywhere in the entry contract;
   - asserts no truth-shape state field (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`) is collected at entry;
   - asserts Digital Anchor / W2.2 / W2.3 / Hot Follow business surfaces are NOT introduced as in-scope by the Phase A contract.

3. **Evidence + log + index write-back**:
   - this evidence note;
   - `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` (active execution log for this wave);
   - row added to `docs/execution/apolloveo_2_0_evidence_index_v1.md`.

---

## 3. What Phase A intentionally does NOT add

- no workbench variation authoring surface;
- no slot detail authoring;
- no delivery center binding;
- no `result_packet_binding` deliverable wiring;
- no publish feedback projection;
- no `variation_matrix.delta.cells[]` or `slot_pack.delta.slots[]` materialization;
- no provider / model / vendor / engine selection of any shape;
- no donor (SwiftCraft) module identity exposure;
- no new packet schema, sample, or contract re-version;
- no Digital Anchor entry surface;
- no Hot Follow change;
- no W2.2 / W2.3 advancement;
- no frontend platform / React/Vite migration work;
- no runtime task-creation code: this is a docs-first / surface-first landing, sufficient for engineering handoff for Phase B.

---

## 4. Discipline checks

- Validator R3 (no vendor pin): the entry contract introduces no `vendor_id`, `model_id`, `provider`, `provider_id`, `engine_id`. The Phase A test asserts this by name-scan over the entry contract.
- Validator R5 (no truth-shape state field): the entry contract introduces no `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`, attached to any entry. The Phase A test asserts this by name-scan over the entry contract.
- `metadata.not.anyOf` (envelope §metadata): all entry fields that map non-truth-side land only in `metadata.notes`, which is a permitted free-form field; no entry maps to `metadata.status` / `metadata.state` / `metadata.phase` / `metadata.ready` / `metadata.done` / `metadata.current_attempt` / `metadata.delivery_ready` / `metadata.final_ready` / `metadata.publishable`.
- Closed kind-sets (`axis_kind_set`, `slot_kind_set`): the entry contract widens neither set. Operator hints select among existing values only.
- Single authority baseline: this contract sits beside the frozen packet contract; it does not redeclare or override packet truth.
- Task Area gate truth rule: `evidence.ready_state` is one-way projection from validator output and is NOT writable from the entry surface (`docs/design/surface_task_area_lowfi_v1.md` §Gate Truth Rule).
- Asset supply matrix discipline: `source_script_ref` and `language_scope` are required at entry, matching the `matrix_script` column of `docs/product/asset_supply_matrix_v1.md` for `source_script` and `language_scope_decl`.

---

## 5. Mapping verification (entry → packet)

| entry field           | line truth? | seeds                                                                                       | packet path reachable? |
| --------------------- | ----------- | ------------------------------------------------------------------------------------------- | ---------------------- |
| `topic`               | no          | `metadata.notes`                                                                              | yes (`metadata.notes` ∈ schema) |
| `source_script_ref`   | yes (opaque) | `slot_pack.delta.slots[*].body_ref`                                                          | yes (`slot_pack` line-specific contract) |
| `language_scope`      | yes         | `slot_pack.delta.slots[*].language_scope`                                                    | yes (`slot_pack` line-specific contract; rooted in `g_lang`) |
| `target_platform`     | no          | `metadata.notes` (delivery binding deferred to Phase C)                                       | yes (`metadata.notes` ∈ schema) |
| `variation_target_count` | no       | Phase B authoring scaffold for `variation_matrix.delta.cells[]` cardinality                  | n/a (does not become a packet field) |
| `audience_hint`       | no          | Phase B selection within `variation_matrix.delta.axes[axis_id="audience"].values[]`          | n/a (selection only; values are packet truth, hint is not) |
| `tone_hint`           | no          | Phase B selection within `variation_matrix.delta.axes[axis_id="tone"].values[]`              | n/a |
| `length_hint`         | no          | Phase B selection within `variation_matrix.delta.axes[axis_id="length"]` range / `slots[*].length_hint` | n/a |
| `product_ref`         | no          | `metadata.notes`                                                                              | yes (`metadata.notes` ∈ schema) |
| `operator_notes`      | no          | `metadata.notes`                                                                              | yes (`metadata.notes` ∈ schema) |

No entry field projects onto `binding.capability_plan[*]`, `binding.worker_profile_ref`, `binding.deliverable_profile_ref`, `binding.asset_sink_profile_ref`, or `evidence.*`. Those are static-by-line per `docs/contracts/matrix_script/packet_v1.md` §Capability plan / §Binding profiles / §Evidence.

---

## 6. Tests run

- `tests/contracts/matrix_script/test_task_entry_phase_a.py` — Phase A validation suite (presence, closed entry-field set, mapping reachability, no forbidden tokens, no truth-shape fields, no out-of-wave scope).

---

## 7. What Phase A now freezes

- the closed set of Matrix Script task entry fields (v1);
- the per-field line-truth vs operator-hint classification;
- the required / optional / deferred discipline at entry time;
- the entry → packet mapping rule;
- the explicit deferral of cells/slots authoring (Phase B), delivery binding (Phase C), publish feedback (Phase D);
- the explicit forbidden-field list at entry surface.

Phase A becomes the authority for the operator-supplied seed feeding Phase B workbench authoring. Phase B MUST start from this seed; Phase B MUST NOT re-author the entry surface.

---

## 8. Remaining blockers before Phase B

1. architect signoff that this Phase A entry contract sits cleanly beside the frozen Matrix Script packet truth (no second source of task / state truth);
2. reviewer signoff that the Phase A change is reviewable as one isolated unit (no Digital Anchor, no W2.2 / W2.3, no Hot Follow, no provider/adapter touch);
3. Phase B (Workbench Variation Surface) MUST be opened by an explicit next instruction; it is NOT auto-unlocked by Phase A acceptance.

---

## 9. Hard stop

After Phase A: stop. Do not start Phase B. Do not start Digital Anchor. Do not start any new provider work. Wait for review / next instruction.
