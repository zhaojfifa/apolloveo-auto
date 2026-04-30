# Digital Anchor Second Production Line Wave — Phase A Task / Role Entry (v1)

- Date: 2026-04-28
- Wave: ApolloVeo 2.0 **Digital Anchor Second Production Line Wave** — Phase A (Task / Role Entry)
- Status: Phase A landed; awaiting architect + reviewer signoff
- Authority:
  - `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Part III P2
  - `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
  - `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
  - `docs/baseline/PRODUCT_BASELINE.md`
  - `docs/contracts/digital_anchor/packet_v1.md`
  - `docs/contracts/digital_anchor/role_pack_contract_v1.md`
  - `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
  - `schemas/packets/digital_anchor/packet.schema.json`
  - `schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json`
  - `docs/product/asset_supply_matrix_v1.md` (digital_anchor row)
  - `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
  - `docs/design/surface_task_area_lowfi_v1.md`
  - `docs/contracts/factory_input_contract_v1.md`
  - `docs/contracts/factory_language_plan_contract_v1.md`
  - `docs/contracts/factory_scene_plan_contract_v1.md`
  - `docs/contracts/factory_audio_plan_contract_v1.md`
  - `docs/contracts/factory_packet_envelope_contract_v1.md`
  - `docs/contracts/factory_packet_validator_rules_v1.md`

---

## 1. Scope

This evidence note covers Phase A of the Digital Anchor Second Production Line Wave: the **task / role entry surface** is established as a contract-driven landing that maps cleanly onto the frozen Digital Anchor packet truth (the line packet, role pack, and speaker plan contracts), without authoring any new line truth.

In scope:
- declaring the closed set of operator-facing entry fields the Digital Anchor line accepts at task creation time;
- declaring which entry fields are line truth vs operator hint;
- declaring required vs optional vs deferred discipline;
- declaring the entry → packet mapping rule;
- minimum validation tests proving the contract's discipline;
- evidence / log / index write-back.

Out of scope (explicitly):
- workbench role / speaker authoring surface (Phase B);
- delivery center binding (Phase C);
- publish feedback closure (Phase D);
- provider / model / vendor / avatar-engine / TTS-provider / lip-sync-engine selection (forbidden at all phases);
- Matrix Script contract mutation (Matrix Script First Production Line Wave is closed PASS);
- Hot Follow business-logic changes;
- W2.2 / W2.3 advancement;
- packet / schema / sample re-versioning;
- frontend platform rebuild;
- runtime task-creation code implementation (this Phase A is a docs-first / surface-first landing).

---

## 2. What Phase A adds

1. **Task Entry Contract v1** — `docs/contracts/digital_anchor/task_entry_contract_v1.md`:
   - closed set of entry fields: `topic`, `source_script_ref`, `language_scope`, `role_profile_ref`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint`, `dub_kind_hint`, `lip_sync_kind_hint`, `scene_binding_hint`, `operator_notes`;
   - per-field classification (line truth vs operator hint; required vs optional);
   - mapping note from each entry field to the Digital Anchor packet path (or to Phase B authoring scaffolding for hints);
   - explicit deferral table (Phase B / C / D / never);
   - explicit forbidden-field list aligned to validator R3 / R5 and `metadata.not.anyOf`.

2. **Phase A validation tests** — `tests/contracts/digital_anchor/test_task_entry_phase_a.py`:
   - asserts the task entry contract document exists at the canonical path;
   - asserts the entry surface accepts the intended input shape (closed entry-field set is present in the contract);
   - asserts every line-truth entry maps to a packet field reachable from the frozen Digital Anchor schema (`schemas/packets/digital_anchor/packet.schema.json`) or its line-specific contracts;
   - asserts no forbidden vendor/model/provider/engine token appears anywhere in the entry contract;
   - asserts no truth-shape state field is collected at entry;
   - asserts Matrix Script / Hot Follow / W2.2 / W2.3 surfaces are NOT introduced as in-scope by the Phase A contract.

3. **Evidence + log + index write-back**:
   - this evidence note;
   - `docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md` (active execution log for this wave);
   - row added to `docs/execution/apolloveo_2_0_evidence_index_v1.md`.

---

## 3. What Phase A intentionally does NOT add

- no workbench role / speaker authoring surface;
- no role detail authoring (`roles[]` enumeration);
- no segment detail authoring (`segments[]` enumeration, `binds_role_id`, `script_ref`, `dub_kind`, `lip_sync_kind`, `language_pick`);
- no delivery center binding;
- no `result_packet_binding` deliverable wiring;
- no publish feedback projection;
- no provider / model / vendor / avatar-engine / TTS-provider / lip-sync-engine selection of any shape;
- no donor (SwiftCraft) module identity exposure;
- no new packet schema, sample, or contract re-version;
- no Matrix Script contract mutation;
- no Hot Follow change;
- no W2.2 / W2.3 advancement;
- no frontend platform / React/Vite migration work;
- no runtime task-creation code: this is a docs-first / surface-first landing, sufficient for engineering handoff for Phase B.

---

## 4. Discipline checks

- Validator R3 (no vendor pin): the entry contract introduces no `vendor_id`, `model_id`, `provider_id`, `engine_id`, avatar-engine, TTS-provider, or lip-sync-engine identifier. The Phase A test asserts this by name-scan over the entry contract.
- Validator R5 (no truth-shape state field): the entry contract introduces no `current_attempt`, `delivery_ready`, `final_ready`, `publishable` field attached to any entry. The Phase A test asserts this by name-scan over the entry contract.
- `metadata.not.anyOf` (envelope §metadata): all entry fields that map non-truth-side land only in `metadata.notes`, which is a permitted free-form field; no entry maps to `metadata.status` / `metadata.state` / `metadata.phase` / `metadata.ready` / `metadata.done` / `metadata.current_attempt` / `metadata.delivery_ready` / `metadata.final_ready` / `metadata.publishable`.
- Closed kind-sets (`framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`): the entry contract widens none of them. Operator hints select among existing values only.
- Single authority baseline: this contract sits beside the frozen packet contract; it does not redeclare or override packet truth.
- Task Area gate truth rule: `evidence.ready_state` is one-way projection from validator output and is NOT writable from the entry surface (`docs/design/surface_task_area_lowfi_v1.md` §Gate Truth Rule).
- Asset supply matrix discipline: `source_script_ref`, `language_scope`, and `role_profile_ref` are required at entry, matching the `digital_anchor` column of `docs/product/asset_supply_matrix_v1.md` for the `source_script`, `language_scope_decl`, and `role_appearance_ref` rows.
- Cross-binding rule (`segments[].binds_role_id` ↔ `roles[].role_id`) is deferred to Phase B authoring; the entry surface MUST NOT collect either id.

---

## 5. Mapping verification (entry → packet)

| entry field                  | line truth?       | seeds                                                                                                                          | packet path reachable? |
| ---------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| `topic`                      | no                | `metadata.notes`                                                                                                                | yes (`metadata.notes` ∈ schema) |
| `source_script_ref`          | yes (opaque)      | `digital_anchor_speaker_plan.delta.segments[*].script_ref`                                                                      | yes (`speaker_plan` line-specific contract) |
| `language_scope`             | yes               | `digital_anchor_role_pack.delta.roles[*].language_scope_ref` + `digital_anchor_speaker_plan.delta.segments[*].language_pick`     | yes (rooted in `g_lang`; bound at both line-specific contracts) |
| `role_profile_ref`           | yes (opaque)      | `digital_anchor_role_pack.delta.roles[*].appearance_ref`                                                                        | yes (`role_pack` line-specific contract) |
| `role_framing_hint`          | no                | Phase B selection within `digital_anchor_role_pack.delta.framing_kind_set`                                                       | n/a (selection only; values are line-specific contract truth, hint is not) |
| `output_intent`              | no                | `metadata.notes` (delivery binding deferred to Phase C)                                                                          | yes (`metadata.notes` ∈ schema) |
| `speaker_segment_count_hint` | no                | Phase B authoring scaffold for `digital_anchor_speaker_plan.delta.segments[]` cardinality                                        | n/a (does not become a packet field) |
| `dub_kind_hint`              | no                | Phase B selection within `digital_anchor_speaker_plan.delta.dub_kind_set`                                                        | n/a |
| `lip_sync_kind_hint`         | no                | Phase B selection within `digital_anchor_speaker_plan.delta.lip_sync_kind_set`                                                   | n/a |
| `scene_binding_hint`         | no                | Phase B per-segment binding into `g_scene`                                                                                       | n/a (hint only) |
| `operator_notes`             | no                | `metadata.notes`                                                                                                                | yes (`metadata.notes` ∈ schema) |

No entry field projects onto `binding.capability_plan[*]`, `binding.worker_profile_ref`, `binding.deliverable_profile_ref`, `binding.asset_sink_profile_ref`, or `evidence.*`. Those are static-by-line per `docs/contracts/digital_anchor/packet_v1.md` §Capability plan / §Binding profiles / §Evidence.

---

## 6. Tests run

- `tests/contracts/digital_anchor/test_task_entry_phase_a.py` — Phase A validation suite (presence, closed entry-field set, mapping reachability, no forbidden tokens, no truth-shape fields, no out-of-wave scope leakage).

---

## 7. What Phase A now freezes

- the closed set of Digital Anchor task / role entry fields (v1);
- the per-field line-truth vs operator-hint classification;
- the required / optional / deferred discipline at entry time;
- the entry → packet mapping rule;
- the explicit deferral of role / segment authoring (Phase B), delivery binding (Phase C), publish feedback (Phase D);
- the explicit forbidden-field list at entry surface.

Phase A becomes the authority for the operator-supplied seed feeding Phase B workbench role / speaker authoring. Phase B MUST start from this seed; Phase B MUST NOT re-author the entry surface.

---

## 8. Remaining blockers before Phase B

1. architect signoff that this Phase A entry contract sits cleanly beside the frozen Digital Anchor packet truth (no second source of task / state truth);
2. reviewer signoff that the Phase A change is reviewable as one isolated unit (no Matrix Script contract mutation, no Hot Follow change, no W2.2 / W2.3, no provider/adapter touch);
3. Phase B (Workbench Role / Speaker Surface) MUST be opened by an explicit next instruction; it is NOT auto-unlocked by Phase A acceptance.

---

## 9. Hard stop

After Phase A: stop. Do not start Phase B. Do not start any new provider work. Do not touch Matrix Script, Hot Follow, W2.2, or W2.3. Wait for review / next instruction.
