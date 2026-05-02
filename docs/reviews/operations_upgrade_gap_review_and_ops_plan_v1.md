# Operations Upgrade Gap Review & Operator Plan v1

> Reviewer: ApolloVeo 2.0 Chief Architect
> Date: 2026-05-02
> Scope: architecture-only review; no code, no UI, no runtime work authorized by this document.

## 1. Executive Conclusion

The current engineering branch is **inside** the Operator-Visible Surface Validation Wave (the "Operations Upgrade Alignment" wave under its formal name in the master plan), not past it. Matrix Script and Hot Follow are on-spec: Matrix Script Phases A–D.1 have landed as packet-first contracts with read-only projections, and Hot Follow remains frozen as the runtime-boundary reference. Digital Anchor, in contrast, has Phases A–D.0 contracts frozen but lacks a Phase D.1 write-back implementation and a formal `/tasks/digital-anchor/new` create-entry payload builder; its New-Tasks card and workbench panel placeholder were exposed in commits `f753d42 → b370e46` ahead of packet truth, which is the textbook 数字人 UI 拼盘 (digital-anchor UI patchwork) failure mode the wave authority exists to prevent.

Two cross-line gaps further block "operator trial readiness":

1. **Asset Supply / B-roll has product freeze but no contract.** [docs/product/broll_asset_supply_freeze_v1.md](docs/product/broll_asset_supply_freeze_v1.md) lists facets, promote semantics, and review gates, but no `asset_library_object_contract`, no `promote_request_contract`, no `promote_feedback_closure_contract` exist. The B-roll surface cannot reach packet truth without these.
2. **Projection has soft seams.** Board `publishable`, Workbench `current attempt` strip, and Delivery `publish_gate` are each derived independently from `ready_gate` + L2 freshness, with no unified L4 `publish_readiness` contract. L4 advisories are frozen in documentation but no runtime producer emits them. Scene-pack non-blocking is implicit (absence from `blocking[]`), not an explicit contract field.

Resolution: Plan A–E in §11. Platform Runtime Assembly remains BLOCKED; the next allowed work is documentation/contract, not UI.

## 2. Reading Declaration

The Authority Set listed in the review brief includes one file path that does not exist in this repository: `docs/execution/ApolloVeo_2.0_Operations_Upgrade_Alignment_Wave_指挥单_v1.md`. The active wave authority under master plan v1.1 (line 137) is [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md). This review treats the two as the same authority under different names ("Operations Upgrade Alignment" being the master-plan-level label; "Operator-Visible Surface Validation Wave" being the wave-charter file). All citations below resolve to files actually present in the repo.

Files read for this review:
- [docs/architecture/apolloveo_2_0_master_plan_v1_1.md](docs/architecture/apolloveo_2_0_master_plan_v1_1.md)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md)
- [docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md](docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md)
- [docs/architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md](docs/architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md)
- [docs/architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md](docs/architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md)
- [docs/architecture/factory_four_layer_architecture_baseline_v1.md](docs/architecture/factory_four_layer_architecture_baseline_v1.md)
- [docs/architecture/factory_runtime_boundary_design_v1.md](docs/architecture/factory_runtime_boundary_design_v1.md)
- [docs/architecture/factory_workbench_mapping_v1.md](docs/architecture/factory_workbench_mapping_v1.md)
- [docs/architecture/factory_line_template_design_v1.md](docs/architecture/factory_line_template_design_v1.md)
- [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md)
- [docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md](docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md)
- `docs/contracts/matrix_script/*` and `docs/contracts/digital_anchor/*`
- `docs/contracts/hot_follow_*.md`, [docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md](docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md), [docs/contracts/status_ownership_matrix.md](docs/contracts/status_ownership_matrix.md)
- [docs/product/asset_supply_matrix_v1.md](docs/product/asset_supply_matrix_v1.md), [docs/product/broll_asset_supply_freeze_v1.md](docs/product/broll_asset_supply_freeze_v1.md)
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md) and the five low-fi surface specs and three line panel specs
- [docs/execution/evidence/operator_visible_surfaces_phase_3a_minimal_wiring_v1.md](docs/execution/evidence/operator_visible_surfaces_phase_3a_minimal_wiring_v1.md) and [..._phase_3b_ui_presenter_wiring_v1.md](docs/execution/evidence/operator_visible_surfaces_phase_3b_ui_presenter_wiring_v1.md)
- [docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md](docs/execution/evidence/new_tasks_line_first_surface_wiring_v1.md) and [matrix_script_operator_visible_slice_merge_note_v1.md](docs/execution/evidence/matrix_script_operator_visible_slice_merge_note_v1.md)
- Code references (read-only): `gateway/app/services/operator_visible_surfaces/projections.py`, `gateway/app/services/{matrix_script,digital_anchor}/*`, `gateway/app/templates/{tasks,task_workbench}.html`

## 3. Current Phase Judgment

**Phase = Operator-Visible Surface Validation Wave (a.k.a. Operations Upgrade Alignment Wave).** Master plan v1.1 line 137 states: "Current execution focus is ApolloVeo 2.0 Operator-Visible Surface Validation. Do not expand into a third production line yet. Do not mutate the closed truth of Matrix Script or Digital Anchor."

The phase is **not**:
- Platform Runtime Assembly Wave — admission requires this wave green; not signed off.
- Capability Expansion Gate (W2.2 / W2.3) — Capability Expansion Gate Wave §3–10: "仅在 Platform Runtime Assembly Wave 签收后启用…W2.2/W2.3/durable persistence/runtime API 不得提前执行".
- New-line runtime loading — third-line commissioning is on the BLOCKED list of the current wave (Operator-Visible Surface Validation Wave lines 105–114).

Implication: any work that loads a new line, expands a provider, persists workbench mutations, or rewrites packet truth is out of scope for this branch.

## 4. Engineering Progress vs Authority Alignment

| Authority requirement                                                | Status     | Evidence                                                                                                            |
| -------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| Hot Follow boundary frozen as runtime reference                      | ✅ on-spec | `factory_runtime_boundary_design_v1.md:4`; no business-logic commits since Wave 0 close (`ca20c60`, 2026-02-17)     |
| Matrix Script Phase A–D contracts frozen                             | ✅ on-spec | `docs/contracts/matrix_script/*` complete (packet, task_entry, variation_matrix, slot_pack, workbench, delivery, publish_feedback) |
| Matrix Script formal `/tasks/matrix-script/new` create-entry         | ✅ on-spec | Commit `4896f7c`; `gateway/app/services/matrix_script/create_entry.py` seeds `line_specific_refs[matrix_script_*]`  |
| Matrix Script workbench panel renders Phase B variation surface      | ✅ on-spec | Commit `b370e46` (#77); `matrix_script_operator_visible_slice_merge_note_v1.md` scope fence holds                   |
| Digital Anchor Phase A–D.0 contracts frozen                          | ✅ on-spec | `docs/contracts/digital_anchor/*` complete through `publish_feedback_closure_contract_v1.md`                        |
| Digital Anchor Phase D.1 write-back implementation                   | ❌ missing | `DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md` references test file; no service code in `gateway/app/services/digital_anchor/` |
| Digital Anchor formal `/tasks/digital-anchor/new` create-entry       | ❌ missing | New-Tasks card routes to generic `/tasks/connect/digital_anchor/new` temp; no payload builder seeds `line_specific_refs[digital_anchor_*]` |
| Operator-visible surfaces sanitize forbidden vendor keys             | ✅ on-spec | `gateway/app/services/operator_visible_surfaces/projections.py:24-33`; tested                                       |
| Asset Supply / B-roll product freeze                                 | ⚠ partial | `docs/product/broll_asset_supply_freeze_v1.md` exists; **no contract object** (Asset Library, promote-request, promote-closure) |
| L4 advisory producer                                                 | ❌ missing | `hot_follow_projection_rules_v1.md:272-335` defines advisory taxonomy; no service emits                              |
| Unified L4 `publish_readiness` contract                              | ❌ missing | Board/Workbench/Delivery each re-derive from `ready_gate` + `final_fresh`                                            |
| W2.2 / W2.3 / new-line runtime loading                               | ⛔ correctly not started | None on branch                                                                                              |

The on-spec column is the load-bearing finding: **Matrix Script and Hot Follow are correct, and the wave's blocking constraints are observed.** The miss is concentrated in Digital Anchor Phase D.1 + create-entry and in two cross-line absences (Asset Library contract, unified L4 publish-readiness).

## 5. Operator Goals Preserved from Premature UI Push

The Phase 3B + New-Tasks-card commits (`f753d42 → b370e46`) reveal what the design has been chasing under the surface — these are the **operator goals** the wave authority intends to deliver and which must not be lost just because the UI got ahead:

1. **A single landing surface where operators see all three lines as siblings.** New-Tasks taxonomy with line cards is the right shape; the gap is that only one card (Matrix Script) has packet truth behind it.
2. **Line-specific entry forms with closed field sets.** `/tasks/matrix-script/new` is the model: closed enum, no provider/model/vendor, packet seeded by builder. Digital Anchor needs the same.
3. **Workbench panel mounts that show line-specific evidence without reinventing zones.** PANEL_REF_DISPATCH approach is correct in principle; it must be contract-frozen so a third line cannot break the dispatch silently.
4. **Delivery Center that distinguishes final / required / optional.** The low-fi splits zones; the contract does not yet pin the `required` flag.
5. **Asset Supply Area as a queryable inventory across lines.** B-roll product freeze articulates this; contract layer is empty.
6. **Read-only projections everywhere downstream of L2 truth.** This is the most important goal and it has been correctly held — no UI fabricates state on the branch.

These goals stand. The plan in §11 keeps them; what changes is the order of work (contract before more UI).

## 6. Discovery-only Frontend Classification

A frontend artifact is **discovery-only** when it surfaces a shape the contract layer has not yet frozen. It must not be treated as authority and must not be relied on for operator trial. Classification:

| Surface                                                                | Classification          | Reason                                                                                              |
| ---------------------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| `/tasks` Board (Hot Follow + Matrix Script rows)                       | Production-eligible     | `derive_board_publishable` on `ready_gate`; tested                                                  |
| `/tasks/matrix-script/new` create-entry form                           | Production-eligible     | Closed packet payload builder; matches `task_entry_contract_v1`                                     |
| Workbench panel — Hot Follow                                           | Production-eligible     | L3 `current_attempt` consumed via packet refs                                                       |
| Workbench panel — Matrix Script (Phase B variation surface)            | Production-eligible (read-only) | Read-only projection of `line_specific_refs[matrix_script_variation_matrix/slot_pack].delta` |
| New-Tasks card — Digital Anchor                                        | **Discovery-only**      | Routes to generic temp; no payload builder; packet `line_specific_refs[digital_anchor_*]` not seeded |
| `/tasks/connect/digital_anchor/new` (generic temp route)               | **Discovery-only**      | Temp barrier route; not the formal entry contract                                                   |
| Workbench panel — Digital Anchor (placeholder branch in `task_workbench.html`) | **Discovery-only** | `elif panel_kind == "digital_anchor"` exists but no production rendering path                       |
| Delivery Center per-deliverable zoning                                 | **Discovery-only**      | UI infers zone from `kind`; no `required: boolean` in `factory_delivery_contract_v1`               |
| B-roll / Asset Supply page                                             | **Discovery-only** (if rendered) | No Asset Library object contract; facets defined only in product freeze doc                  |
| Promote intent submit                                                  | **Discovery-only**      | No promote-request schema; no promote-closure contract                                              |

Operator trial **must not** drive any discovery-only surface. Either the surface is hidden or the operator is told explicitly it is for shape preview only.

## 7. Line-by-line Gap Review

### 7.1 Hot Follow

- **Role:** stable runtime boundary reference and operator-visible projection sample. `factory_runtime_boundary_design_v1.md:4` and Wave 0 freeze note govern.
- **Risk of being reopened for business behavior:** **none observed.** No commit on branch touches `tasks.py` or `hot_follow_api.py` business logic since `ca20c60` (2026-02-17). Per `HOT_FOLLOW_RUNTIME_CONTRACT.md:179` this is the explicit rule.
- **Fitness as projection sample:** ✓. `hot_follow_current_attempt_contract_v1.md` (L3) and `hot_follow_projection_rules_v1.md` (L4) give Matrix Script and Digital Anchor the projection template they should both echo.
- **Gap:** none in this wave. Hot Follow is the reference; it should not move.

### 7.2 Matrix Script

- **Page-first vs packet-first:** **packet-first.** Phase A → packet contract frozen → projector → UI. Evidence: `MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` Phase B notes "read-only packet projection"; merge note at `matrix_script_operator_visible_slice_merge_note_v1.md` explicitly fences scope to Matrix Script and to read-only.
- **Line-object coverage:**
  - `script` / `outline` — ⚠ partially folded into `task_entry_contract_v1` (`topic`, `source_script_ref`); no separate outline contract object. Acceptable for first-line operator trial.
  - `variation_plan` — ✅ `variation_matrix_contract_v1.md`, projected via workbench panel.
  - `copy_bundle` — ✅ `slot_pack_contract_v1.md`, projected.
  - `publish_feedback` — ✅ `publish_feedback_closure_contract_v1.md`, Phase D.1 write-back landed.
  - `result_packet_binding` — ⚠ `delivery_binding_contract_v1.md` exists but `artifact_lookup` is `not_implemented_phase_c` in code; deliverable-side projection not yet rendered in Delivery Center.
  - `asset_supply_matrix` — ⚠ generic `docs/product/asset_supply_matrix_v1.md` lists Matrix Script asset kinds (`broll`, `product_shot`, `background`, `template`, `variation_axis`) but no per-line contract enforces them.
- **Workbench fitness for ops 跑量 trial:** ✓ for shape inspection; ✗ for end-to-end runs because delivery binding is `not_implemented_phase_c`. Operator can issue `variation_plan + copy_bundle` and inspect — they cannot yet treat Delivery Center output as truth for this line.

### 7.3 Digital Anchor

- **Page-first vs packet-first:** **page-first risk is real.** New-Tasks card and workbench placeholder exist; formal create-entry builder and Phase D.1 write-back do not. This is the 数字人 UI 拼盘 pattern.
- **Line-object coverage:**
  - `role_profile` — ✅ `role_pack_contract_v1.md`.
  - `scene_plan_binding` — ⚠ scenes flow through `role_pack` and `delivery_binding`; no standalone `scene_plan_binding_contract_v1.md`.
  - `speaker_plan` — ✅ `speaker_plan_contract_v1.md`.
  - `language_output` — ⚠ language is a field in `task_entry_contract_v1` and `delivery_binding`; no dedicated `language_output_contract_v1.md`.
  - `delivery_pack_binding` — ✅ `delivery_binding_contract_v1.md` (read-only, `not_implemented_phase_c` artifact lookup).
  - `publish_feedback` — ✅ Phase D.0 contract; ❌ Phase D.1 write-back not landed.
- **Create-entry gap:** New-Tasks card → `/tasks/connect/digital_anchor/new` (generic temp). No `gateway/app/services/digital_anchor/create_entry.py` to mirror Matrix Script's payload builder. **This is the highest-priority single gap on the branch.**
- **Workbench fitness for ops trial:** ✗. Panel placeholder branch has no rendering path; running an operator on Digital Anchor today would expose unfinished surfaces.

## 8. Five-Surface Gap Review

### 8.1 Task Area

- **Contract-level today:** `gateway/app/services/operator_visible_surfaces/projections.py:24-33` enforces `FORBIDDEN_OPERATOR_KEYS` (`vendor_id`, `model_id`, `provider_id`, `engine_id`, `raw_provider_route`); tested.
- **Discovery-only:** Digital Anchor card route; absence of a per-line entry-builder contract.
- **Out of scope this wave:** task-list cross-tenant filters; bulk operations.

### 8.2 Workbench

- **Contract-level today:** Hot Follow + Matrix Script panels; `derive_board_publishable` over `ready_gate`.
- **Missing contract:** Workbench L2/L3 display strip (the "current attempt vs historical artifact" zone, `ApolloVeo_Operator_Visible_Surfaces_v1.md:228`). The design mandates the distinction; the L3 contract has no `final_provenance: current | historical` field. Today the UI infers from `final_fresh` plus timestamps. **Inference, not a contract — must be promoted to L3.**
- **Missing contract:** PANEL_REF_DISPATCH (`projections.py:182-250`) — six `ref_id → panel_kind` entries are an in-code enum, not a frozen contract object. A third line will silently fall off the dispatch.
- **Out of scope this wave:** workbench mutations / writeback beyond what the closure contracts already permit.

### 8.3 Delivery Center

- **Contract-level today:** `factory_delivery_contract_v1` exists.
- **Missing contract field:** per-deliverable `required: boolean` (and `blocking_publish: boolean`). `surface_delivery_center_lowfi_v1.md` zones A/B/C; UI hardcodes mapping by `kind`. **A flag in the contract closes this.**
- **Missing contract:** unified L4 `publish_readiness` (combining `ready_gate.publish_ready` with L2 `final_fresh`). Today `projections.py:95-131` `derive_delivery_publish_gate` re-derives. Board re-derives separately. Drift risk over time.
- **Discovery-only:** scene-pack zoning. Non-blocking is implicit (absence from `blocking[]`); should be an explicit contract field.

### 8.4 Asset Supply Area

- **Product freeze present:** `docs/product/broll_asset_supply_freeze_v1.md` (facets `line/topic/style/language/role_id/scene/variation_axis/quality_threshold`), `asset_supply_matrix_v1.md` (per-line asset kinds), promote semantics articulated.
- **Contract layer empty:** no `asset_library_object_contract_v1.md` (asset metadata, provenance, hash, version, tags, usage limits, available_to_lines), no `promote_request_contract_v1.md`, no `promote_feedback_closure_contract_v1.md`.
- **Out of scope this wave:** asset CRUD UI implementation, asset DB schema migration. **In scope this wave:** the contract objects above (documentation only).

### 8.5 Tool Backend

- **Status:** correctly out of scope. Master plan v1.1 lines 75–82 + 186–187 forbid donor namespace import; Capability Expansion Gate Wave forbids provider/model/vendor consoles before Platform Runtime Assembly. No work allowed here.

## 9. B-roll / Asset / Promote Gap Review

The semantic ladder is the right one and is already articulated in product docs:

| Concept            | Definition                                                                                              | Contract status                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **source asset**   | Operator-supplied input (source video, source script, role appearance, variation axes decl)             | Field-level only inside `task_entry_contract_v1` per line; no asset object contract |
| **task artifact**  | Output of a task run; ephemeral; tied to one task                                                       | Implicit in line-specific delivery binding; no artifact-vs-asset contract |
| **B-roll**         | Reusable secondary footage available across tasks                                                        | Product-frozen; **no asset-library object contract**                      |
| **reusable asset** | Promoted task artifact made available across tasks                                                       | Promote semantics articulated; **no promote contract**                    |
| **promote**        | Operator-initiated, admin-reviewed transition: task artifact → reusable asset                            | Async review-gated intent in product freeze; **no request/closure contract** |
| **scene pack**     | Optional secondary derivative; non-blocking once current final exists                                   | Non-blocking is correct rule per `factory_line_template_design_v1.md:174-190`; **non-blocking-ness is implicit (absence from `blocking[]`), not a contract field** |

Per-line role of B-roll:
- **Hot Follow**: B-roll is reference footage for compose; scene-pack residue is advisory (already correct).
- **Matrix Script**: B-roll is variation slot fill; categorized by `variation_axis` and `slot`.
- **Digital Anchor**: B-roll is scene/background fill behind the role; categorized by `scene` and `role_id`.

These categorizations exist as narrative in `asset_supply_matrix_v1.md`; they need contract pinning before Asset Supply is operator-trial-eligible.

**Minimum viable asset supply for ops trial (contract-only, no UI in this wave):**
- `asset_library_object_contract_v1.md` — closed metadata schema (id, kind, line_availability[], tags[], provenance, hash, version, quality_score, usage_limits).
- `promote_request_contract_v1.md` — closed request schema (artifact_ref, target_kind, target_tags, target_line_availability, license_metadata, requested_by).
- `promote_feedback_closure_contract_v1.md` — promote audit trail mirror (states: requested / approved / rejected; reviewer; timestamps).
- Explicit contract field on `factory_delivery_contract_v1`: `scene_pack_blocking_allowed: false` (or equivalent) so scene-pack non-blocking-ness is explicit, not inferred.

## 10. Projection Boundary Gap Review

The four-layer model:

| Layer | Name              | Authority owner                                                       |
| ----- | ----------------- | --------------------------------------------------------------------- |
| L1    | step status       | line state machine (Hot Follow: `hot_follow_state_machine_contract_v1.md`) |
| L2    | artifact facts    | line packets and artifact services                                     |
| L3    | current attempt   | `hot_follow_current_attempt_contract_v1.md` and analogues              |
| L4    | operator projection | `hot_follow_projection_rules_v1.md`, ready-gate, advisory taxonomy   |

Boundary risks observed:

1. **UI invents state — risk = LOW today, MEDIUM after a third line.** Current Board / Workbench / Delivery code computes its outputs from L1+L2+L3 inputs; no fabrication. The risk is that the absence of a unified L4 `publish_readiness` contract lets each surface re-derive locally, which **will** drift if the rule moves.
2. **Delivery derives from contract / artifact?** Yes today — `derive_delivery_publish_gate` reads `ready_gate` (L4) and L2 `final_fresh`. Risk: re-derivation pattern.
3. **Workbench mixes historical and current?** **Yes — by inference.** The L3 contract does not carry `final_provenance: current | historical`. UI distinguishes via `final_fresh` boolean + comparing artifact timestamps. Design mandates the distinction (`ApolloVeo_Operator_Visible_Surfaces_v1.md:228`); contract does not pin it. **Promote `final_provenance` to L3.**
4. **Scene Pack as publish blocker?** No, today — `scene_pack_pending` is enumerated as `non_blocking` in `hot_follow_projection_rules_v1.md` and is absent from `ready_gate.blocking[]`. Risk: this is implicit. A future line could add scene_pack to its blocking array. **Add explicit `scene_pack_blocking_allowed: false` to ready-gate or delivery contract.**
5. **L4 advisory contract has no producer.** `hot_follow_projection_rules_v1.md:272-335` defines the advisory taxonomy (`hf_advisory_translation_waiting_retryable`, `hf_advisory_final_ready`, `hf_advisory_retriable_dub_failure`, etc.); no service emits them; Workbench/Publish cannot consume. **Producer must land before any UI claims to render advisories.**
6. **Board / Workbench / Delivery re-derive `publishable`.** `task_router_presenters.py::build_tasks_page_rows` calls `derive_board_publishable`. `projections.py::project_operator_surfaces` is a separate path. Delivery re-combines `ready_gate + final_fresh` to compute `publish_gate`. **Promote to a single `publish_readiness_contract_v1.md` consumed by all three.**

## 11. Operator-facing Plan

The plans are ordered B → C → D → A → E. B/C/D may run in parallel; A waits on B+C+D; E waits on A.

### Plan A — Ops Trial Readiness

Goal: tell operators what they may try and what they must not, with the minimal explanation surface.

**Operator-eligible trial scope:**
- Hot Follow end-to-end (intake → publish), as a baseline.
- Matrix Script end-to-end **except** Delivery Center binding: operators may submit, inspect workbench Phase B variation surface, and exercise publish-feedback closure. Delivery Center for this line is **inspect-only** until `artifact_lookup: not_implemented_phase_c` is resolved.
- Cross-line inspection of `/tasks` Board.

**Forbidden operator scope (must be hidden or labeled "preview"):**
- Digital Anchor end-to-end runs (Phase D.1 not landed; create-entry routes to temp).
- Asset Supply page (no contract behind facets).
- Promote intent submission (no contract behind request).
- Any vendor/model/provider control or selection.
- Any "third line" entry.

**Minimum operator-explanation口径 per surface:**
- Task Area: "Three lines listed; Hot Follow and Matrix Script accept new tasks; Digital Anchor card is preview only."
- Workbench: "Read-only projection of current attempt and accepted artifacts; historical artifacts are timestamped — they are not current truth."
- Delivery Center: "Lists final / required / optional deliverables. Optional items (e.g., scene pack) never block publish."

**Suggested trial sample types:**
- Hot Follow: short clip with a known good source, full subtitle + dub + compose + publish path.
- Matrix Script: 2–3 axis × 4–6 slot variation plan against a fixed topic; observe variation surface and feedback closure.
- Inspection-only: open Digital Anchor preview card, confirm operator does not submit.

### Plan B — Contract / Packet Completion

Goal: return Matrix Script and Digital Anchor to packet truth.

**Matrix Script must-add fields:**
- Promote `result_packet_binding` from `not_implemented_phase_c` placeholder to a real artifact-lookup; freeze the lookup contract (delivery binding artifact resolution).
- Pin per-line `asset_supply_matrix` rows (closed enum of asset kinds, available_to_line=`matrix_script`).
- (Optional, if outline becomes load-bearing in trial) Split `outline` into a dedicated contract object distinct from `task_entry_contract_v1`.

**Digital Anchor must-add (highest priority):**
- `create_entry_payload_builder` — a builder that seeds `line_specific_refs[digital_anchor_role_pack]` and `[digital_anchor_speaker_plan]` from a closed entry form.
- `/tasks/digital-anchor/new` formal route contract (analog to Matrix Script alignment doc).
- Phase D.1 write-back implementation behind `publish_feedback_closure_contract_v1`.
- (If trial requires) `scene_plan_binding_contract_v1.md` and `language_output_contract_v1.md` as standalone objects.

**Reference relations to factory-generic contracts:**
- All line packets continue to extend `factory_packet_contract_v1` (envelope).
- `result_packet_binding`, `delivery_binding` per line must project into `factory_delivery_contract_v1`.
- `publish_feedback_closure` per line must mirror its closure into the operator-visible publish-status mirror.

**Validator gate (machine-checkable):**
- Schema validator on `line_specific_refs` per line: required ref ids present.
- Validator on Delivery Center output: every item carries `kind` ∈ closed enum and (after Plan D) `required: boolean`.
- Validator on packet envelope: forbidden vendor keys absent (already enforced).

### Plan C — Asset Supply & B-roll Preparation

Goal: turn B-roll from a UI accessory into a contract-backed operator supply system.

**Per-line asset kinds (frozen in contract, not narrative):**
- Hot Follow: `reference_video`, `broll`, `style`.
- Matrix Script: `broll`, `product_shot`, `background`, `template`, `variation_axis`.
- Digital Anchor: `role_ref`, `background`, `template`, `scene`, `language`.

**Tag taxonomy (closed sets per facet):**
- `line` ∈ `{hot_follow, matrix_script, digital_anchor}`.
- `topic`, `style`, `language`, `role_id`, `scene`, `variation_axis` — closed value lists per `broll_asset_supply_freeze_v1.md`.
- `quality_threshold` ∈ `{draft, review, approved}`.

**Quality thresholds:**
- `draft` = uploaded, untagged, not surfaced to non-author operators.
- `review` = tagged and submitted for promote review.
- `approved` = admin-reviewed; surfaced to all lines listed in `available_to_lines`.

**Promote rules:**
- Promote is a **separate intent flow** (not artifact mutation). Source artifact remains immutable.
- Required fields in `promote_request_contract_v1`: `artifact_ref`, `target_kind`, `target_tags[]`, `target_line_availability[]`, `license_metadata`, `requested_by`.
- Closure mirror in `promote_feedback_closure_contract_v1` with states `{requested, approved, rejected}` and timestamps.

**Scene Pack non-blocking rule (explicit, not inferred):**
- Add `scene_pack_blocking_allowed: false` field to ready-gate / delivery contract.
- Validator rejects any line that adds `scene_pack` (or descendant) to `ready_gate.blocking[]`.

### Plan D — Projection Reconciliation

Goal: anchor Workbench / Delivery to L2/L3/L4 derivations of one shared contract object, not three.

**Workbench projection rules:**
- Promote `final_provenance: "current" | "historical"` field into L3 `current_attempt` contract.
- Workbench L2/L3 display strip contract: enumerate mandatory fields (current attempt id, route, fresh booleans, advisory list, historical artifact pointer + timestamp).
- PANEL_REF_DISPATCH frozen as `workbench_panel_dispatch_contract_v1.md` (closed map of `ref_id → panel_kind`).

**Delivery projection rules:**
- Add per-deliverable `required: boolean` and `blocking_publish: boolean` to `factory_delivery_contract_v1`.
- Single L4 `publish_readiness_contract_v1.md`: takes `ready_gate` (L4) + L2 `final_fresh` + L2 `final_provenance`, returns `publishable: boolean` and `head_reason`. Board, Workbench, Delivery all consume the same producer.

**`final_video` / `required_deliverables` / `scene_pack` distinction:**
- `final_video` = `kind=final_video`, `required=true`, `blocking_publish=true`.
- `required_deliverables` = `required=true`, `blocking_publish` per kind.
- `scene_pack` = `required=false`, `blocking_publish=false`, `scene_pack_blocking_allowed=false` enforced.

**Current attempt vs historical deliverable explanation rule:**
- L3 emits `final_provenance`.
- Workbench renders both: "Current attempt: <route, fresh>" and "Last accepted final: <timestamp> (historical, may be replaced)".
- Delivery shows only items consistent with current `publish_readiness`; historical items are visible but tagged `historical`.

**L4 advisory producer:**
- New service: `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (one file; emits the taxonomy frozen in `hot_follow_projection_rules_v1.md`). Pure projection from L3 + ready-gate; no truth invention. *Note: implementation lands in Plan E gate, but the contract for the producer's output shape is part of Plan D.*

### Plan E — Next Operator-visible Implementation Gate

Goal: define when a next round of frontend work may start.

**Pre-conditions to start:**
1. Plan B closed (Digital Anchor create-entry + Phase D.1; Matrix Script `result_packet_binding` resolved).
2. Plan C closed (Asset Library + promote contracts frozen; scene-pack non-blocking explicit).
3. Plan D closed (unified `publish_readiness_contract_v1`; `final_provenance` in L3; PANEL_REF_DISPATCH contract; `required` + `blocking_publish` in delivery).
4. Plan A trial executed and write-up filed.

**Forbidden until pre-conditions met:**
- New line implementation.
- W2.2 / W2.3 capability work.
- Platform Runtime Assembly.
- Provider/model/vendor consoles.
- Workbench writeback beyond closure contracts.
- Donor namespace import.

**Permitted scope when gate opens:**
- Asset Library page (read-only) backed by `asset_library_object_contract_v1`.
- Promote intent UI backed by `promote_request_contract_v1`.
- Delivery Center per-deliverable zoning rendered from `required` + `blocking_publish`.
- Workbench `final_provenance` strip rendered from L3.
- Board / Workbench / Delivery consuming `publish_readiness_contract_v1` (single source).
- L4 advisory producer emitting; surfaces consuming.

**Acceptance for the next gate:**
- All five surfaces consume contract-backed projections; no in-code derivations of `publishable` or `publish_gate`.
- Three-line symmetry: each line has a formal `/tasks/<line>/new` route, a workbench panel mount via the dispatch contract, and a delivery binding without `not_implemented_phase_*` placeholders.
- Asset Supply trial-ready: operators can submit a promote intent and see it tracked.

## 12. Risks and Blockers

- **R1 — Digital Anchor 数字人 UI 拼盘 drift.** New-Tasks card and workbench placeholder visible without packet truth behind them. Mitigation: hide / label preview during ops trial; close in Plan B.
- **R2 — Re-derivation drift across surfaces.** Three independent paths compute "publishable" from `ready_gate` + `final_fresh`. Mitigation: Plan D unified contract.
- **R3 — Asset Supply unmoored.** Product freeze without contract is a contradiction the next surface push will fall through. Mitigation: Plan C contract layer first.
- **R4 — Scene Pack mis-treated as blocker by a future line.** Non-blocking is implicit. Mitigation: Plan C explicit field.
- **R5 — L4 advisory producer absent.** Workbench/Publish cannot render advisories; the contract is documentation-only. Mitigation: Plan D producer (contract) + Plan E producer (implementation).
- **R6 — Authority file naming inconsistency.** "Operations Upgrade Alignment Wave" referenced in this review's brief does not exist as a distinct file; merged with Operator-Visible Surface Validation Wave. Mitigation: this review's §2 declares the merge; operations team must be told the canonical file path.
- **B1 — No work on Platform Runtime Assembly until this wave green.** Authority restated; do not bypass.
- **B2 — No reopening of Hot Follow business behavior.** Authority restated; do not bypass.

## 13. Final Gate Decision

- **Platform Runtime Assembly:** BLOCKED
- **Capability Expansion:** BLOCKED
- **Frontend patching:** BLOCKED
- **Operations Upgrade Alignment:** APPROVED
- **Next allowed work:**
  1. **Plan B** — Digital Anchor `create_entry_payload_builder` + `/tasks/digital-anchor/new` formal route contract + Phase D.1 publish-feedback write-back; Matrix Script `result_packet_binding` artifact-lookup contract; per-line `asset_supply_matrix` enum freeze.
  2. **Plan C** — `asset_library_object_contract_v1.md`, `promote_request_contract_v1.md`, `promote_feedback_closure_contract_v1.md`, explicit `scene_pack_blocking_allowed: false` field on ready-gate / delivery contract.
  3. **Plan D** — `publish_readiness_contract_v1.md` (unified L4); `final_provenance` field promoted to L3 `current_attempt` contract; `workbench_panel_dispatch_contract_v1.md`; `required` + `blocking_publish` fields on `factory_delivery_contract_v1`; L4 advisory producer output-shape contract.
  4. **Plan A** — Ops trial scope freeze document (operator-eligible vs forbidden scope; surface explanation 口径; sample suggestions). Waits on B + C + D.
  5. **Plan E** — Next operator-visible implementation gate spec (pre-conditions, forbidden scope, permitted scope, acceptance). Waits on A.

No code, no UI, no runtime work is authorized by this document. All five plan items above are documentation/contract artifacts.
