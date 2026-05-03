# ApolloVeo 2.0 Unified Alignment Map v1

Date: 2026-05-03
Status: Permanent navigation document. **Documentation only. No code, no UI, no contract, no schema, no test, no template change. No file moves. No directory restructure.** This map is a navigation aid, not a replacement authority. Every load-bearing claim it makes points at an existing repo file by path; the existing file remains the truth.
Authority of creation: [docs/reviews/apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md](../reviews/apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md) §9.3 + §11.
Update cadence: only when a wave closes or a major identity / phase shift occurs (typically every 2–6 weeks). Not every PR triggers a map update.

---

## What this map IS

A single project-level orientation entry. A cold reader who hits this map first should answer the seven questions ApolloVeo work depends on:

1. What is ApolloVeo at the business level?
2. What is ApolloVeo 2.0 at the architecture level?
3. What wave is the repo in, and what is allowed vs blocked?
4. What is each of the three production lines, and what is their current status?
5. Where does B-roll / Asset Supply belong?
6. What is the accepted-truth baseline vs the missing operator surface?
7. What is the single frozen next engineering sequence?

After reading this map, the cold reader should know which bucket(s) under `docs/` to drill into and what scope is permitted for the current task.

## What this map is NOT (binding non-scope)

This map does not, and must not, become any of the following:

- **Not a review.** Reviews under [docs/reviews/](../reviews/) carry point-in-time judgments with verdicts and correction lists. This map has no verdict; it points at where verdicts live.
- **Not a contract.** Contracts under [docs/contracts/](../contracts/) define normative truth (a packet MUST have field X). This map has no normative power; it tells you where the contract is.
- **Not a product / handoff doc.** Product docs under [docs/product/](../product/) and handoffs under [docs/handoffs/](../handoffs/) are operator-facing or role-handoff specs. This map is engineering-facing only and must never be shown to operators.
- **Not an architecture design doc.** Architecture docs under [docs/architecture/](../architecture/) define structural design — the four layers, the line template, runtime boundaries, the workbench mapping, the top-level business flow. This map references them; it does not redefine them.
- **Not a wave 指挥单.** Wave 指挥单 under `docs/architecture/ApolloVeo_2.0_*_Wave_*指挥单*_v1.md` are wave-internal execution briefs with allowed actions, role assignments, and acceptance criteria. This map names the active 指挥单 by file path; it does not replicate or override its scope.
- **Not an execution log.** Execution logs under [docs/execution/](../execution/) carry per-PR / per-phase evidence. This map references the evidence index; it does not list per-PR logs.
- **Not the master plan.** [docs/architecture/apolloveo_2_0_master_plan_v1_1.md](apolloveo_2_0_master_plan_v1_1.md) is the architect's mother plan with phasing (P0 → P1 → P1.5 → P2 → P3), donor strategy, and verification rules. This map cites the master plan; it does not redefine its phasing.

If the navigation tier in this map ever conflicts with any of the above, the above wins. This map is updated, not the underlying authority.

---

## Section 1 · ApolloVeo Business Identity

ApolloVeo is **an AI 内容生产工厂** oriented to final-deliverable content production. It is organized around production lines, not around tools / models / vendors.

What the factory produces (closed deliverable set):

- `final.mp4`
- subtitles
- audio
- scene pack
- metadata / manifest
- publish status
- archive record

How the business chain runs (per [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](apolloveo_2_0_top_level_business_flow_v1.md)):

```
task creation → line / goal selection → input → parameter / config review
  → content structure → scene plan + language plan + audio plan
  → generate → quality check (ready gate + current attempt)
  → delivery contract (current final + accepted deliverables)
  → publish / scene pack feedback → archive
```

The unit of work is a **task** — not an editing session, not a model invocation, not a tool run. Operators are not asked to make vendor / model / provider / engine choices. Those are runtime concerns hidden behind capability kinds (`understanding`, `subtitles`, `dub`, `video_gen`, `avatar`, `face_swap`, `post_production`, `pack`, `variation`, `speaker`, `lip_sync`).

ApolloVeo is **not** a studio shell, not a tool catalog, not a model marketplace, not an orchestration framework, not a multi-tenant platform.

Authority pointers:

- [README.md](../../README.md) §"Current Reality"
- [docs/baseline/PRODUCT_BASELINE.md](../baseline/PRODUCT_BASELINE.md)
- [docs/baseline/PROJECT_BASELINE_INDEX.md](../baseline/PROJECT_BASELINE_INDEX.md)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](apolloveo_2_0_top_level_business_flow_v1.md)

---

## Section 2 · ApolloVeo 2.0 Architecture Identity

ApolloVeo 2.0 is **the factory-shaped architectural form of the same business** — i.e. how the business chain in §1 is laid out across software boundaries.

The 2.0 form has six load-bearing pieces:

### 2.1 Five operator-visible surfaces

Per [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md):

- Task Area
- Workbench
- Delivery Center
- Asset Supply
- Tool Backstage

Operator-visible payloads MUST NOT carry `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any donor namespace identifier. Sanitization is enforced at the operator boundary.

### 2.2 Ten backend domains + ops/env

Per [docs/architecture/apolloveo_2_0_master_plan_v1_1.md](apolloveo_2_0_master_plan_v1_1.md) Part IV:

- `capability_adapters`
- `worker_execution_envelope`
- `media_processing` (new sub-domain in v1.1)
- `delivery_response_modeling` (with sub-domains `manifest_shaping`, `artifact_shaping`)
- `packet_governance`
- `capability_routing_policy`
- `asset_supply`
- (... and the other three from the master plan)

`ops/env/` is an independent operations domain (not in the ten).

### 2.3 Six factory-generic content contracts

Per [docs/contracts/](../contracts/):

- [factory_input_contract_v1.md](../contracts/factory_input_contract_v1.md)
- [factory_content_structure_contract_v1.md](../contracts/factory_content_structure_contract_v1.md)
- [factory_scene_plan_contract_v1.md](../contracts/factory_scene_plan_contract_v1.md)
- [factory_audio_plan_contract_v1.md](../contracts/factory_audio_plan_contract_v1.md)
- [factory_language_plan_contract_v1.md](../contracts/factory_language_plan_contract_v1.md)
- [factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (with Plan C amendments: `required` / `blocking_publish` / `scene_pack_blocking_allowed: false`)

### 2.4 Packet envelope + 5 validator rules

Binding contract layer:

- [factory_packet_envelope_contract_v1.md](../contracts/factory_packet_envelope_contract_v1.md) — E1 line_id uniqueness / E2 generic-refs path purity / E3 binds_to resolution / E4 ready_state singleton / E5 capability kind closure.
- [factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md) — R1 generic_refs resolve / R2 no generic-shape duplication / R3 capability kind not vendors / R4 JSON Schema Draft 2020-12 loadable / R5 no truth-shape state fields.

### 2.5 Four architecture layers

Per [docs/architecture/factory_four_layer_architecture_baseline_v1.md](factory_four_layer_architecture_baseline_v1.md):

- Layer 0 — Engineering Entry & Authority Layer.
- Layer 1 — Production Line Contract Layer.
- Layer 2 — State & Projection Layer (four-layer state model L1 step status / L2 artifact facts / L3 current attempt / L4 ready gate / projection / advisory).
- Layer 3 — Surface & Execution Layer (routers, services, workbench, publish, workers).

### 2.6 Hot Follow as reference line; SwiftCraft as donor only

- Hot Follow is the **runtime reference line**, not the runtime template. New lines do not copy Hot Follow's router/service residue; they bind to the line template via [docs/contracts/production_line_runtime_assembly_rules_v1.md](../contracts/production_line_runtime_assembly_rules_v1.md).
- SwiftCraft is the **only authorized capability donor**. Code is absorbed via Apollo-native `capability_adapters` interfaces; SwiftCraft's `TaskService / TaskStore / TaskRecord / scenario truth / fallback-as-truth` are forbidden. Authority: [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md), [docs/donor/swiftcraft_donor_boundary_v1.md](../donor/swiftcraft_donor_boundary_v1.md), [docs/donor/swiftcraft_capability_mapping_v1.md](../donor/swiftcraft_capability_mapping_v1.md).

### 2.7 Phasing

Per master plan v1.1: **P0 守基线 → P1 Factory Generic 基座 → P1.5 Donor 吸收冻结 → P2 Line Packet 冻结 → P3 First New-Line Runtime**.

Inside P2 / P3 the live wave-charter sequence is: Multi-role Implementation 指挥单 → Matrix Script First Production Line Wave → Digital Anchor Second Production Line Wave → **Operator-Visible Surface Validation Wave (current)** → Platform Runtime Assembly Wave → Capability Expansion Gate Wave.

---

## Section 3 · Current Wave and Blocked Scope

### 3.1 Current wave

**ApolloVeo 2.0 Operator-Visible Surface Validation Wave** (a.k.a. "Operations Upgrade Alignment Wave" — same authority under different names; merge clarified in [operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) §2).

Wave authority: [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md).

Wave-internal sequence:

| Plan | Purpose | Status |
| --- | --- | --- |
| Plan B | Digital Anchor B1/B2/B3 + Matrix Script B4 — contract layer | ✅ COMPLETE (PR #80) |
| Plan C | Asset Library + promote request + promote closure + scene-pack non-blocking explicit field | ✅ COMPLETE (PR #80) |
| Plan D | Unified `publish_readiness` + L3 `final_provenance` + workbench panel dispatch contract object + delivery `required` / `blocking_publish` + L4 advisory producer output shape | ✅ COMPLETE (PR #80) |
| Plan A | Operations trial readiness — operator-eligible scope freeze + coordinator runbook + sample plan + risk watch | ⏳ Static verification PASS; **live-trial execution by ops team PENDING** |
| Plan E | Next operator-visible implementation gate spec | ⏸ Not yet opened — opens after Plan A live-trial executes and write-up filed |

Predecessor waves (all CLOSED):

- W1 Donor Absorption (M-01..M-05) — see [W1_COMPLETION_REVIEW_v1.md](../reviews/W1_COMPLETION_REVIEW_v1.md)
- W2 Admission Preparation (Phases A–E) — see [W2_ADMISSION_SIGNOFF_v1.md](../reviews/W2_ADMISSION_SIGNOFF_v1.md)
- W2.1 Base-only Adapter Preparation (B1–B4) — implementation green; awaiting architect+reviewer signoff (paperwork only)
- W2.1 First Provider Absorption (UnderstandingAdapter ← Gemini, A-03)
- Matrix Script First Production Line Wave + Plan A trial corrections §8.A → §8.H all PASS
- Digital Anchor Second Production Line Wave (Phases A–D.0 contracts only)

Successor waves (NOT STARTED):

- Platform Runtime Assembly Wave — gated on this wave green + Plan A live-trial executed
- Capability Expansion Gate Wave (W2.2 / W2.3 / durable persistence / runtime API / third line) — HOLD; gated on Platform Runtime Assembly signoff

### 3.2 Explicitly blocked in current wave

Per [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), the gap review §13, the Operator-Visible Surface Validation Wave 指挥单 §7, the Capability Expansion Gate Wave 指挥单 §"红线", and Plan A §4:

- Platform Runtime Assembly entry
- Capability Expansion (W2.2, W2.3, durable persistence, runtime API)
- Third production line commissioning
- Frontend patching beyond what is already shipped (no React/Vite full rebuild, no provider/model selector UI, no donor / supply concept exposure)
- Hot Follow business reopening
- Matrix Script / Digital Anchor closed-truth mutation
- Provider / model / vendor / engine controls (validator R3 + design-handoff red line 6)
- Donor namespace import (`from swiftcraft.*`)
- Matrix Script §8.A → §8.H reopening
- Discovery-only surface promotion to operator-eligible

### 3.3 Explicitly allowed in current wave

The wave-internal *only* allowed engineering action is:

- **Plan A live-trial execution by operations team** (coordinator runs `§2.1` hide/disable + `§2.2` 口径 + `§2.3` per-line runbook + `§11.4` and `§12.4` action items per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md); ops team appends live-run results to `§8` placeholder).

Always-allowed maintenance (no wave gate required):

- Documentation re-anchoring (this map and its execution log are instances).
- Evidence write-back on already-shipped corrections.
- Architect / reviewer signoff of W2.1 B1–B4 (implementation already green; paperwork only).

---

## Section 4 · Three Product Lines · Current Status Matrix

| Dimension | Hot Follow | Matrix Script | Digital Anchor |
| --- | --- | --- | --- |
| Role in 2.0 | Runtime reference line | First official 2.0 line | Second official 2.0 line |
| Packet contract | n/a (pre-2.0 line contract) | ✅ Phases A–D + §8.A / §8.C / §8.F addenda | ✅ Phases A–D.0 + Plan B B1/B2/B3 |
| Runtime impl | ✅ Full (LineRegistry / ready gate / status policy / state machine / projection rules) | ⏳ Partial (entry + Phase B variation surface + D.1 closure write-back; Delivery Center inspect-only / B4 gated) | ❌ None (formal route + payload builder + D.1 write-back + Phase B render NOT implemented) |
| Trial-ready | ✅ YES | ✅ CONDITIONAL — 8 binding sample-validity criteria (§0.1 of trial brief) | ❌ Inspection-only |
| Single next action | Serve as Plan A samples 1–2; no business reopen | Plan A samples 3–5; no code change | Plan A inspection-only sample (operator confirms preview-labeled card) |
| Blocked | Business behavior reopening; structural decomposition (deferred to Platform Runtime Assembly Wave) | Code change in this wave; B4 / Option F2 (gated to Plan E) | Submission attempt; B1 / B2 / B3 / D.1 implementation (gated to Plan E) |
| Authority pointer | [hot_follow_line_contract.md](../contracts/hot_follow_line_contract.md) | [matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md) | [digital_anchor/packet_v1.md](../contracts/digital_anchor/packet_v1.md) |

### 4.1 Hot Follow (full detail)

- Intended product goal: source short video → publishable localized final video; one operator-visible workbench, one runtime chain (`ingest → parse → adapt → dub → compose → review_gate → pack_publish_sink`); supports `mm` / `vi` target languages.
- Achieved: full runtime; Skills MVP v0 advisory closed; source-audio policy / target-subtitle currentness / dub currentness fixes closed; Hot Follow reference packet validation green ([hot_follow_reference_packet_validation_v1.md](../execution/evidence/hot_follow_reference_packet_validation_v1.md)); business-validated end-to-end.
- Missing (structural debt only): `tasks.py` (3,480 lines), `hot_follow_api.py` (2,325 lines), `task_view.py::build_hot_follow_workbench_hub()` (492 lines mixing layers); compatibility helpers; L4 advisory taxonomy authored but no producer; `final_provenance` inferred not L3-emitted; `publishable` re-derived in three places.
- Per-line authorities: [hot_follow_line_contract.md](../contracts/hot_follow_line_contract.md), [HOT_FOLLOW_RUNTIME_CONTRACT.md](../contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md), [hot_follow_ready_gate.yaml](../contracts/hot_follow_ready_gate.yaml), [hot_follow_projection_rules_v1.md](../contracts/hot_follow_projection_rules_v1.md), [hot_follow_state_machine_contract_v1.md](../contracts/hot_follow_state_machine_contract_v1.md), [hot_follow_current_attempt_contract_v1.md](../contracts/hot_follow_current_attempt_contract_v1.md), [hot_follow_business_flow_v1.md](hot_follow_business_flow_v1.md).

### 4.2 Matrix Script (full detail)

- Intended product goal: first official 2.0 line; script-driven matrix-of-variants → publishable final video; closed `task → workbench → delivery → publish_feedback` business loop. Per [Matrix Script First Production Line Wave 指挥单 v1](ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md): "先做出一条 task → workbench → delivery → publish feedback 完整闭环的工厂样板".
- Achieved: Phases A–D contracts frozen; Phase A formal `/tasks/matrix-script/new` route landed (commit `4896f7c`); Phase B variation panel mounted (`b370e46`); §8.C deterministic Phase B authoring (3 canonical axes — `tone`/`audience`/`length` — and `variation_target_count` cells); §8.A entry-form ref-shape guard; §8.B dispatch confirmation; §8.D operator brief; §8.E shell suppression (whitelist `{% if task.kind == "hot_follow" %}` around four contiguous Hot Follow-only template regions); §8.F opaque-ref tightening (8 schemes → 4: `{content, task, asset, ref}`; operator transitional convention `content://matrix-script/source/<token>`); §8.G Phase B Axes table render correctness (Jinja item-access); §8.H operator brief re-correction (§0.1 seven binding criteria + §0.2 product-meaning of `source_script_ref`); Phase D.1 write-back already shipped.
- Missing: B4 `result_packet_binding.artifact_lookup` (`not_implemented_phase_c` placeholder rows); Option F2 in-product minting flow (replaces operator-discipline `<token>`).
- Per-line authorities: [matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md), [task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with §8.A / §8.C / §8.F addenda), [variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md), [slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md), [workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md), [delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md), [publish_feedback_closure_contract_v1.md](../contracts/matrix_script/publish_feedback_closure_contract_v1.md), [result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md).
- Live-trial conditional gate: 8 sample-validity criteria in [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 + product-meaning §0.2.

### 4.3 Digital Anchor (full detail)

- Intended product goal: second official 2.0 line; script + role-driven 数字人口播成片 pipeline; closed `role_pack` (LS1) + `speaker_plan` (LS2) line-specific objects extending the six factory-generic refs.
- Achieved: Phase A task entry contract ([digital_anchor/task_entry_contract_v1.md](../contracts/digital_anchor/task_entry_contract_v1.md)); Phase B workbench role/speaker surface contract; Phase C delivery binding contract; Phase D.0 publish-feedback closure contract; Plan B B1 ([create_entry_payload_builder_contract_v1.md](../contracts/digital_anchor/create_entry_payload_builder_contract_v1.md)) + B2 ([new_task_route_contract_v1.md](../contracts/digital_anchor/new_task_route_contract_v1.md)) + B3 ([publish_feedback_writeback_contract_v1.md](../contracts/digital_anchor/publish_feedback_writeback_contract_v1.md)) all frozen.
- Missing: formal `/tasks/digital-anchor/new` route handler; create-entry payload builder code; Phase D.1 write-back code; Phase B render production path; identified by gap review §7.3 as "数字人 UI 拼盘 risk" (New-Tasks card and workbench placeholder exposed in commits `f753d42 → b370e46` ahead of packet truth).
- Operator hide guards (Plan A §2.1): Digital Anchor New-Tasks card click target ([gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html)) + temp `/tasks/connect/digital_anchor/new` MUST be hidden / disabled / preview-labeled in the trial environment.
- Per-line authorities: [digital_anchor/packet_v1.md](../contracts/digital_anchor/packet_v1.md), [task_entry_contract_v1.md](../contracts/digital_anchor/task_entry_contract_v1.md), [role_pack_contract_v1.md](../contracts/digital_anchor/role_pack_contract_v1.md), [speaker_plan_contract_v1.md](../contracts/digital_anchor/speaker_plan_contract_v1.md), [workbench_role_speaker_surface_contract_v1.md](../contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md), [delivery_binding_contract_v1.md](../contracts/digital_anchor/delivery_binding_contract_v1.md), [publish_feedback_closure_contract_v1.md](../contracts/digital_anchor/publish_feedback_closure_contract_v1.md).

---

## Section 5 · B-roll / Asset Supply Positioning

**Binding wording**: B-roll / Asset Supply has its **contract layer frozen**; **operator-workspace implementation is deferred to Plan E**.

### 5.1 Frozen contract layer (as of 2026-05-02)

Product authority:

- [docs/product/broll_asset_supply_freeze_v1.md](../product/broll_asset_supply_freeze_v1.md) — facets (8 first-class), promote semantics (admin-reviewed, async, intent-based), license / source / reuse policy field set, canonical/reusable badges (admin-only state with operator-visible badges), detail actions scope, artifact-to-asset hand-off boundary, reference-into-task pre-population mapping, deferred items.
- [docs/product/asset_supply_matrix_v1.md](../product/asset_supply_matrix_v1.md) — per-line operator-supplied input asset kinds × per-line line-produced deliverable kinds; closed kind sets; supply-truth-vs-donor decoupling rules.
- [docs/design/broll_asset_supply_lowfi_v1.md](../design/broll_asset_supply_lowfi_v1.md) — operator-visible surface low-fi.

Contract layer (landed 2026-05-02 in PR #80 / commit `6052014`):

- [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md) — closed metadata schema (15-kind closed enum, 8 facets, license enum, reuse_policy enum, quality_threshold enum, versioning rule, validator R3 / R5 alignment).
- [docs/contracts/promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md) — promote intent request schema.
- [docs/contracts/promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md) — promote audit trail mirror with closed states `{requested, approved, rejected}`.
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) — amended with `required` / `blocking_publish` / `scene_pack_blocking_allowed: false`.
- [docs/contracts/hot_follow_projection_rules_v1.md](../contracts/hot_follow_projection_rules_v1.md) — explicit scene-pack non-blocking.

### 5.2 Operator-workspace implementation deferred to Plan E

Not present, gated to Plan E (next operator-visible implementation gate):

- Asset-library service module (no `gateway/app/services/asset_library/` or `gateway/app/services/asset/` runtime).
- Promote intent service module.
- Promote closure service module.
- Operator-visible Asset Supply / B-roll page.
- Admin-side review surface.
- `mark_reusable_or_canonical_intent` flow.

### 5.3 Layer position

| Layer | Position | Status |
| --- | --- | --- |
| Layer 0 | Read-only consumer of root rules | n/a |
| Layer 1 — line-specific | `asset_supply_matrix` declarations (per-line input/deliverable kinds) | ✅ frozen |
| Layer 1 — cross-line | `asset_library_object` + `promote_request` + `promote_feedback_closure` | ✅ frozen 2026-05-02 |
| Layer 2 | Asset metadata is read-only across line packets; assets are not packet truth; promote intent state lives outside packets | ✅ defined |
| Layer 3 | Asset Supply page; promote intent UI; admin review UI; service code | ❌ deferred to Plan E |

### 5.4 Hard discipline (from `asset_supply_matrix_v1.md` §"Decoupling rules")

- Supply truth MUST NOT name a donor.
- Donor MUST NOT redeclare supply truth.
- Closed kind-sets are owned by supply.
- Capability `mode` is descriptive, not selective.
- Asset references are opaque across the boundary.
- No truth round-trip from donor to supply.
- Frontend MUST NOT cross the boundary.

This discipline is binding at every step of the future Plan E implementation.

---

## Section 6 · Accepted Truth Baseline vs Missing Operator Surface

### 6.1 Accepted truth baseline (read-only consumption permitted; no re-review needed)

**Root governance & entry discipline** — eight root files: [README.md](../../README.md), [PROJECT_RULES.md](../../PROJECT_RULES.md), [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md), [CHANGELOG_STAGE.md](../../CHANGELOG_STAGE.md), [apolloveo_current_architecture_and_state_baseline.md](../../apolloveo_current_architecture_and_state_baseline.md).

**Docs entry indexes** — [docs/README.md](../README.md), [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md).

**Architecture target** — [apolloveo_2_0_master_plan_v1_1.md](apolloveo_2_0_master_plan_v1_1.md), [apolloveo_2_0_top_level_business_flow_v1.md](apolloveo_2_0_top_level_business_flow_v1.md), [factory_four_layer_architecture_baseline_v1.md](factory_four_layer_architecture_baseline_v1.md), [factory_line_template_design_v1.md](factory_line_template_design_v1.md), [factory_runtime_boundary_design_v1.md](factory_runtime_boundary_design_v1.md), [factory_workbench_mapping_v1.md](factory_workbench_mapping_v1.md), [hot_follow_business_flow_v1.md](hot_follow_business_flow_v1.md).

**Factory contracts** — six generic + envelope + validator + production-line runtime assembly + four-layer state + status ownership matrix + workbench hub response.

**Per-line authority** — Hot Follow / Matrix Script / Digital Anchor full contract sets per §4.

**Plan B/C/D cross-line contracts** (landed 2026-05-02 PR #80 / commit `6052014`):

- B1/B2/B3 Digital Anchor; B4 Matrix Script result_packet_binding artifact lookup
- C1 asset_library_object; C2 promote_request; C3 promote_feedback_closure; C4 factory_delivery `required` / `blocking_publish` / `scene_pack_blocking_allowed: false`
- D1 [publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md); D2 final_provenance L3 amendment; D3 [workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) (with §8.E shared-shell-neutrality addendum); D4 [l4_advisory_producer_output_contract_v1.md](../contracts/l4_advisory_producer_output_contract_v1.md).

**Donor governance** — SwiftCraft donor boundary + capability mapping + ADR + host directory predisposition; W1 absorption complete (M-01..M-05); W2 admission Phases A–E closed.

**Operations trial readiness** — [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (with §0.1 seven sample-validity criteria + §0.2 product-meaning of `source_script_ref`); [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) (static verification PASS; §11 / §12 correction addenda).

**Operator transitional convention** — `content://matrix-script/source/<token>` for Plan A trial wave (Option F1).

### 6.2 Missing operator surface (gated to Plan E)

Concrete operator-facing missing pieces:

1. Digital Anchor end-to-end run.
2. Asset Supply browsing (closed-facet filter, license / reuse_policy / canonical / reusable badges, reference-into-task pre-population).
3. Promote intent submission (operator promotes task artifact → reusable Asset Library object; tracks `submitted` / `under_review` / `accepted` / `rejected`).
4. Unified `publishable` truth (Board / Workbench / Delivery agree because they consume one `publish_readiness_contract_v1` producer).
5. Current vs historical strip in Workbench (operator sees `final_provenance: current | historical` from L3).
6. Per-deliverable `required` / `blocking_publish` / `scene_pack` zoning rendered from contract fields.
7. L4 advisory rendering (Workbench / Publish surfaces consume Hot Follow advisory taxonomy emitted by a producer service).
8. Matrix Script Delivery binding artifact resolution (replacing `not_implemented_phase_c` placeholders).
9. In-product `content://` mint for Matrix Script (Option F2 — replaces operator-discipline `<token>` convention).

The order of these in Plan E is for the Plan E gate spec to fix; this map does not pre-decide it.

### 6.3 Discovery-only surfaces (must remain hidden during the trial)

Per Plan A §4.1:

- Digital Anchor New-Tasks card click target.
- Generic temp route `/tasks/connect/digital_anchor/new`.
- Digital Anchor workbench placeholder branch.
- Matrix Script Delivery Center per-row placeholders (`not_implemented_phase_c`) — visible to operator, **inspect-only**, never operate.
- Asset Supply / B-roll page.
- Promote intent submit affordance.

---

## Section 7 · Frozen Next Engineering Sequence

**One sequence. No parallel drift. No step starts before its predecessor signs off.**

```
Plan A live-trial execution
  → Plan E gate spec
  → Plan E implementation
  → Platform Runtime Assembly Wave
  → Capability Expansion Gate Wave
```

### 7.1 Step 1 — Plan A live-trial execution (single next allowed action)

Owner: Operations team coordinator + product / design / architect / reviewer roles per [docs/execution/apolloveo_2_0_role_matrix_v1.md](../execution/apolloveo_2_0_role_matrix_v1.md).

Authority: [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) + [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md).

Pre-conditions (verified):

- Plan B / C / D contracts frozen ✅ ([PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md))
- Matrix Script §8.A → §8.H all PASS ✅ ([ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) §"Current Completion")
- Plan A static verification PASS ✅
- Coordinator hide/disable guards achievable in trial environment

Action (summarized; see Plan A authorities for verbatim instructions):

- Coordinator runs §2.1 hide guards (Digital Anchor card + temp route + Asset Supply / B-roll page + promote intent submit).
- Coordinator briefs operators on §5.1 / §5.2 / §5.3 口径 + §0.1 sample-validity rule (seven criteria) + §0.2 product-meaning of `source_script_ref`.
- Operations team executes Plan A §7.1 samples 1–6 in order (Hot Follow golden + preserve-source × Matrix Script `mm` `vi` boundary check + cross-line Board inspection).
- Operations team appends live-run results to §8 placeholder of the coordinator write-up.
- Coordinator + architect + reviewer signoff.

Deliverable: at least one full sample-wave entry in §8 of the Plan A coordinator write-up; Plan E pre-condition #1 satisfied.

### 7.2 Step 2 — Plan E gate spec (after Step 1 lands)

Authored as a separate review document. Defines: pre-conditions / forbidden scope / permitted scope / acceptance for the next operator-visible implementation gate.

This map does **not** pre-decide Plan E's internal ordering.

### 7.3 Step 3 — Plan E implementation (after Step 2 spec)

Expected ordering per gap review §11 (final ordering owned by Plan E spec):

- Digital Anchor B1/B2/B3 + Phase D.1 write-back + Phase B render
- Asset Library + promote services + UI
- Unified `publish_readiness` producer + L3 `final_provenance` + workbench panel dispatch contract object + per-deliverable `required` / `blocking_publish` rendering + L4 advisory producer/emitter
- Matrix Script B4 artifact lookup
- Matrix Script Option F2 in-product minting flow

### 7.4 Step 4 — Platform Runtime Assembly Wave (after Plan E green)

Per [Platform Runtime Assembly Wave 指挥单 v1](ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) §6:

- Phase A — Shared Logic Port Merge
- Phase B — Compose / Large Service Extraction
- Phase C — Declarative Ready Gate
- Phase D — Runtime Assembly Skeleton
- Phase E — OpenClaw / External Control Stub (optional, postponed)

### 7.5 Step 5 — Capability Expansion Gate Wave (after Platform Runtime Assembly green)

Per [Capability Expansion Gate Wave 指挥单 v1](ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) §"解锁顺序建议":

1. W2.2 Subtitles / Dub Provider
2. W2.3 Avatar / VideoGen / Storage Provider
3. Durable persistence additive wave
4. Runtime API additive wave
5. Third production line commissioning

### 7.6 Hard red lines (sequence-wide)

- Do not skip Step 1 by running Plan E preparation in parallel — the Plan E gate spec depends on Plan A live-run findings.
- Do not preempt Step 4 by running W2.2 / W2.3 work — Capability Expansion is gated on Platform Runtime Assembly signoff.
- Do not treat any "discovery-only" surface as a milestone.
- Do not let any signoff document this map without re-reading the eight root files first.

---

## Section 8 · Review History — Five-Bucket Reclassification

For full per-file lists, see [apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md](../reviews/apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md) §8. Summarized here so future tasks classify reviews in one lookup:

| Bucket | Purpose | When to read | Examples |
| --- | --- | --- | --- |
| §8.1 Foundational architecture | Long-term gates / framework setting | Once per major task class | [2026-03-18-plus_factory_alignment_code_review.md](../reviews/2026-03-18-plus_factory_alignment_code_review.md), [VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md](../reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md), [review_jellyfish_importability_for_factory.md](../reviews/review_jellyfish_importability_for_factory.md), the four `appendix_*` files |
| §8.2 Current-wave gating | Gates / closes a current-wave decision | Read for the wave; archive at wave close | [APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md](../reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md), [APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md](../reviews/APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md), [operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md), [W1_COMPLETION_REVIEW_v1.md](../reviews/W1_COMPLETION_REVIEW_v1.md), [W2_ADMISSION_SIGNOFF_v1.md](../reviews/W2_ADMISSION_SIGNOFF_v1.md), [architect_signoff_packet_gate_v1.md](../reviews/architect_signoff_packet_gate_v1.md) |
| §8.3 Line-specific blocker | Blocks a specific line until corrections land | Read only for lines under active correction | [matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) (CLOSED), [matrix_script_followup_blocker_review_v1.md](../reviews/matrix_script_followup_blocker_review_v1.md) (CLOSED), Hot Follow blocker / freeze reviews |
| §8.4 Execution evidence | Proves a correction or wave landed | Verify shipped state; never plan from | [apolloveo_2_0_evidence_index_v1.md](../execution/apolloveo_2_0_evidence_index_v1.md), eight Matrix Script §8.A → §8.H execution logs, [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md), evidence files under [docs/execution/evidence/](../execution/evidence/) |
| §8.5 Discovery-only / historical | Useful for "how did we get here"; not authority | Never cite as current-wave authority | [docs/reviews/v1.9/](../reviews/v1.9/), [docs/archive/](../archive/), [REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md](../reviews/REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md), `TASK_*_*.md` historical analyses, [review_20260317.md](../reviews/review_20260317.md) |

---

## Section 9 · Reading Order (default project entry path)

Future engineering / docs / review tasks should read in this order:

1. **Root rules** — eight files in §6.1 (gov tier).
2. **Docs entry indexes** — [docs/README.md](../README.md), [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md).
3. **This unified alignment map** — confirm wave / line / surface / phase position before drilling further.
4. **Reading contract** — [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md) for index-first discipline + reading declaration template.
5. **Architecture target** — [apolloveo_2_0_master_plan_v1_1.md](apolloveo_2_0_master_plan_v1_1.md), [apolloveo_2_0_top_level_business_flow_v1.md](apolloveo_2_0_top_level_business_flow_v1.md), [factory_four_layer_architecture_baseline_v1.md](factory_four_layer_architecture_baseline_v1.md), [factory_line_template_design_v1.md](factory_line_template_design_v1.md), the active wave 指挥单.
6. **Per-line / per-surface contracts** — read for the specific line(s) / surface(s) the task touches.
7. **Factory-generic + envelope + validator + Plan B/C/D contracts** — read for cross-cutting truth.
8. **Plan A trial readiness + coordinator write-up** — read if the task touches operator trial scope.
9. **Current-wave gating reviews** — read for the wave's verdict and remaining blockers.
10. **Line-specific blocker reviews** — read only for lines under active correction.
11. **Execution evidence** — read for verification / write-back template.
12. **Foundational architecture reviews** — read for long-term gates.

Discovery-only / historical references — **do not read for current-wave decisions**.

---

## Map maintenance rules

- Update this map only when a wave closes or a major identity / phase shift occurs.
- Do not let the map become a replacement authority. Every load-bearing claim points at an existing repo file by path; the existing file remains the truth.
- Do not embed full contract field tables, full review content, or full execution evidence here. Reference; do not duplicate.
- Do not rewrite this map per PR. Edit only when the underlying truth shifts.
- Authority for changes to this map: Chief Architect or equivalent reviewer; merge to main only after the wave / phase shift that prompted the change has been signed off elsewhere.
