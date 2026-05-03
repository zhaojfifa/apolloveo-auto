# ApolloVeo 2.0 Unified Cognition and Document Re-anchoring Review v1

Date: 2026-05-03
Status: Authority-only re-anchoring review. **Documentation only. No code, no UI, no contract, no schema, no test changes.** This review does not implement, patch, or open a new engineering wave. It restores a single shared project-level understanding so that future task slices stop drifting against fragmented authority.
Reviewer: ApolloVeo 2.0 Chief Architect / Unified Alignment Reviewer
Authority surface: see §2.

---

## 1. Executive Conclusion

ApolloVeo 2.0 does not lack documents. It lacks a unified cognition layer.

The repo currently carries (a) frozen business / product identity authority, (b) a single mother architecture plan with a P0 → P1 → P1.5 → P2 → P3 sequence, (c) line-design closure for three production lines, (d) factory-generic + line-specific + Plan B/C/D contracts, (e) a richly indexed execution evidence trail, and (f) two stacked layers of current-wave reviews (P2 readiness + Operations Upgrade gap). What it does not carry is a single authority that ties all of those into one map and answers, in one place, the seven questions a cold reader needs answered before doing anything: what the project is at the business level, what it is at the 2.0 architecture level, what wave the repo is currently in, what each line is and is not, where B-roll / Asset Supply belongs, what is already stable, and what the next engineering action is.

The seven answers are not contradictory across the existing authority set. They are scattered. The cost of that scattering is not theoretical — the Matrix Script trial blocker review v1 and its follow-up review (`§8.A` through `§8.H`) consumed eight gated correction cycles in part because the team was reading individual contracts without the cross-cutting cognition that "Plan A is operator-trial only; Delivery Center is inspect-only this wave; B-roll is contract-frozen but not operational; Digital Anchor is inspect-only; the only single-line live-trial path is Matrix Script under eight binding sample-validity criteria." Each of those facts was already true in the repo at the time the trial was attempted. None of them were in one place.

**Verdict on the questions**:

- **Unified identity**: ApolloVeo at the business level is an AI 内容生产工厂 with final-deliverable orientation. ApolloVeo 2.0 at the architecture level is a factory-organized platform base — five operator surfaces × ten backend domains × six factory-generic contract objects + envelope + validator + four architecture layers — with Hot Follow as the runtime reference line and SwiftCraft as a capability donor only.
- **Current wave**: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave"). Plan B / C / D contract layer is complete. **Plan A live-trial execution by the operations team is the single next allowed engineering action.** Platform Runtime Assembly is BLOCKED until Plan A is executed and written up.
- **Three product lines**:
  - **Hot Follow** — runtime-implemented reference line; business-validated end-to-end; trial-ready ✓; structurally still hotspot-heavy (`tasks.py` / `hot_follow_api.py` / `task_view.py`); MUST NOT be reopened for business behavior in this wave.
  - **Matrix Script** — first official 2.0 line; Phases A–D.0 contracts frozen; Phase D.1 write-back landed; Plan A trial corrections `§8.A` → `§8.H` all PASS; live-trial BLOCK released subject to the eight conditions in the trial brief `§12`; Delivery Center inspect-only; live-trial execution remains Plan E pre-condition #1.
  - **Digital Anchor** — second official 2.0 line; Phases A–D.0 contracts frozen; Phase D.1 NOT implemented; formal `/tasks/digital-anchor/new` route NOT implemented; create-entry payload builder NOT implemented; **inspection-only** for this wave; "数字人 UI 拼盘" risk identified by the Operations Upgrade gap review and held by coordinator-side hide guards.
- **B-roll / Asset Supply**: the wording in the brief ("product freeze only, no contract") was correct as of the gap review (2026-05-02 morning). It is now superseded — contract layer landed in PR #80 / commit `6052014` on 2026-05-02:
  - [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md) (C1)
  - [docs/contracts/promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md) (C2)
  - [docs/contracts/promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md) (C3)
  - amendments to [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (`required` / `blocking_publish` / `scene_pack_blocking_allowed: false`)
  - The remaining gap is **operator-workspace implementation** — no asset-library service, no promote service, no closure service, no UI. B-roll surface stays "discovery-only" until Plan E.
- **Current accepted baseline**: large. See `§7.1` for the stabilized set. The frontier is well-defined. The "next engineering path" is unambiguous.
- **Review history**: classifiable into five clean buckets (foundational architecture / current-wave gating / line-specific blocker / execution evidence / discovery-only). See `§8`.
- **Documentation re-anchoring**: required. See `§9` for the read-order. A new permanent navigation document at [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) is recommended. See `§11` for what it should and should not be.

**Gate recommendation** (full text in `§11`):

- Current cognition restored: **YES**, by this review.
- Current docs need re-anchoring: **YES** — not by rewriting them, but by adding the unified alignment map and updating root entry-discipline to point at it before the docs index.
- New unified map should become default entry: **YES** — recommended at the same authority tier as `docs/README.md` and `docs/ENGINEERING_INDEX.md`, between root rules and the docs index.

**Hard red lines re-stated** (none of the following are authorized by this review):

- no code, UI, contract, schema, sample, test, or template change;
- no reopening of any closed Matrix Script correction step (`§8.A` through `§8.H`);
- no drift into Platform Runtime Assembly (next stage; gated on Plan A live-trial execution);
- no drift into Capability Expansion (gated on Platform Runtime Assembly signoff);
- no treatment of any discovery-only surface as final authority;
- no fragmented secondary review covering only one local issue.

---

## 2. Reading Declaration

Repo entry discipline followed. There is no top-level `CLAUDE.md`; the equivalent root-discipline chain is the eight-file root rule set + the docs index + the engineering reading contract.

**Root authority read** (in order):

- [README.md](../../README.md)
- [ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md)
- [PROJECT_RULES.md](../../PROJECT_RULES.md)
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)
- [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md)
- [CHANGELOG_STAGE.md](../../CHANGELOG_STAGE.md)
- [apolloveo_current_architecture_and_state_baseline.md](../../apolloveo_current_architecture_and_state_baseline.md)

**Docs entry indexes read**:

- [docs/README.md](../README.md)
- [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md)
- [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md)
- [docs/baseline/PROJECT_BASELINE_INDEX.md](../baseline/PROJECT_BASELINE_INDEX.md)
- [docs/baseline/PRODUCT_BASELINE.md](../baseline/PRODUCT_BASELINE.md)
- [docs/baseline/ARCHITECTURE_BASELINE.md](../baseline/ARCHITECTURE_BASELINE.md)
- [docs/baseline/EXECUTION_BASELINE.md](../baseline/EXECUTION_BASELINE.md)

**2.0 architecture target read**:

- [docs/architecture/apolloveo_2_0_master_plan_v1_1.md](../architecture/apolloveo_2_0_master_plan_v1_1.md) (mother plan)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- [docs/architecture/factory_four_layer_architecture_baseline_v1.md](../architecture/factory_four_layer_architecture_baseline_v1.md)
- [docs/architecture/factory_line_template_design_v1.md](../architecture/factory_line_template_design_v1.md)
- [docs/architecture/factory_runtime_boundary_design_v1.md](../architecture/factory_runtime_boundary_design_v1.md)
- [docs/architecture/factory_workbench_mapping_v1.md](../architecture/factory_workbench_mapping_v1.md)
- [docs/architecture/hot_follow_business_flow_v1.md](../architecture/hot_follow_business_flow_v1.md)
- All five 2.0 wave 指挥单 (Multi-role / Matrix Script First Production Line / Operator-Visible Surface Validation / Platform Runtime Assembly / Capability Expansion Gate / W2 Admission / W2.1 First Provider / W2.1 Base-Only Adapter)

**Factory contracts read**:

- [docs/contracts/production_line_runtime_assembly_rules_v1.md](../contracts/production_line_runtime_assembly_rules_v1.md)
- [docs/contracts/factory_input_contract_v1.md](../contracts/factory_input_contract_v1.md), [factory_content_structure_contract_v1.md](../contracts/factory_content_structure_contract_v1.md), [factory_scene_plan_contract_v1.md](../contracts/factory_scene_plan_contract_v1.md), [factory_audio_plan_contract_v1.md](../contracts/factory_audio_plan_contract_v1.md), [factory_language_plan_contract_v1.md](../contracts/factory_language_plan_contract_v1.md), [factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md)
- [docs/contracts/factory_packet_envelope_contract_v1.md](../contracts/factory_packet_envelope_contract_v1.md)
- [docs/contracts/factory_packet_validator_rules_v1.md](../contracts/factory_packet_validator_rules_v1.md)
- [docs/contracts/four_layer_state_contract.md](../contracts/four_layer_state_contract.md), [status_ownership_matrix.md](../contracts/status_ownership_matrix.md), [workbench_hub_response.contract.md](../contracts/workbench_hub_response.contract.md)

**Per-line contracts read**:

- [docs/contracts/hot_follow_line_contract.md](../contracts/hot_follow_line_contract.md), [HOT_FOLLOW_RUNTIME_CONTRACT.md](../contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md), [hot_follow_ready_gate.yaml](../contracts/hot_follow_ready_gate.yaml), [hot_follow_projection_rules_v1.md](../contracts/hot_follow_projection_rules_v1.md), [hot_follow_state_machine_contract_v1.md](../contracts/hot_follow_state_machine_contract_v1.md), [hot_follow_current_attempt_contract_v1.md](../contracts/hot_follow_current_attempt_contract_v1.md)
- [docs/contracts/matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md), [task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with `§8.A` / `§8.C` / `§8.F` addenda), [variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md), [slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md), [workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md), [delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md), [publish_feedback_closure_contract_v1.md](../contracts/matrix_script/publish_feedback_closure_contract_v1.md), [result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md)
- [docs/contracts/digital_anchor/packet_v1.md](../contracts/digital_anchor/packet_v1.md), [task_entry_contract_v1.md](../contracts/digital_anchor/task_entry_contract_v1.md), [role_pack_contract_v1.md](../contracts/digital_anchor/role_pack_contract_v1.md), [speaker_plan_contract_v1.md](../contracts/digital_anchor/speaker_plan_contract_v1.md), [workbench_role_speaker_surface_contract_v1.md](../contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md), [delivery_binding_contract_v1.md](../contracts/digital_anchor/delivery_binding_contract_v1.md), [publish_feedback_closure_contract_v1.md](../contracts/digital_anchor/publish_feedback_closure_contract_v1.md), [create_entry_payload_builder_contract_v1.md](../contracts/digital_anchor/create_entry_payload_builder_contract_v1.md), [new_task_route_contract_v1.md](../contracts/digital_anchor/new_task_route_contract_v1.md), [publish_feedback_writeback_contract_v1.md](../contracts/digital_anchor/publish_feedback_writeback_contract_v1.md)

**Plan B / C / D cross-line contracts read**:

- [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md), [promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md), [promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md)
- [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md), [workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md), [l4_advisory_producer_output_contract_v1.md](../contracts/l4_advisory_producer_output_contract_v1.md)

**Product / design / handoff read**:

- [docs/handoffs/apolloveo_2_0_product_handoff_v1.md](../handoffs/apolloveo_2_0_product_handoff_v1.md), [apolloveo_2_0_design_handoff_v1.md](../handoffs/apolloveo_2_0_design_handoff_v1.md)
- [docs/product/asset_supply_matrix_v1.md](../product/asset_supply_matrix_v1.md), [broll_asset_supply_freeze_v1.md](../product/broll_asset_supply_freeze_v1.md), [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md), [surface_task_area_lowfi_v1.md](../design/surface_task_area_lowfi_v1.md), [surface_workbench_lowfi_v1.md](../design/surface_workbench_lowfi_v1.md), [surface_delivery_center_lowfi_v1.md](../design/surface_delivery_center_lowfi_v1.md), [panel_matrix_script_variation_lowfi_v1.md](../design/panel_matrix_script_variation_lowfi_v1.md), [panel_digital_anchor_role_speaker_lowfi_v1.md](../design/panel_digital_anchor_role_speaker_lowfi_v1.md), [broll_asset_supply_lowfi_v1.md](../design/broll_asset_supply_lowfi_v1.md), [panel_hot_follow_subtitle_authority_lowfi_v1.md](../design/panel_hot_follow_subtitle_authority_lowfi_v1.md)

**Reviews read**:

- [docs/reviews/2026-03-18-plus_factory_alignment_code_review.md](2026-03-18-plus_factory_alignment_code_review.md) and its [summary](2026-03-18-plus_factory_alignment_code_review_summary.md)
- [docs/reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md](APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md)
- [docs/reviews/APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md](APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md)
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](operations_upgrade_gap_review_and_ops_plan_v1.md)
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](matrix_script_trial_blocker_and_realign_review_v1.md)
- [docs/reviews/matrix_script_followup_blocker_review_v1.md](matrix_script_followup_blocker_review_v1.md)
- [docs/reviews/operator_visible_surface_wiring_feasibility_v1.md](operator_visible_surface_wiring_feasibility_v1.md)
- [docs/reviews/W1_COMPLETION_REVIEW_v1.md](W1_COMPLETION_REVIEW_v1.md), [W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md](W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md), [W2_ADMISSION_SIGNOFF_v1.md](W2_ADMISSION_SIGNOFF_v1.md), [architect_signoff_packet_gate_v1.md](architect_signoff_packet_gate_v1.md)

**Execution evidence read**:

- [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) (Plan A coordinator write-up; static-pass + `§11` and `§12` correction addenda)
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md)
- All eight Matrix Script `§8.A` → `§8.H` execution logs
- [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](../execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md](../execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md)
- [docs/execution/apolloveo_2_0_evidence_index_v1.md](../execution/apolloveo_2_0_evidence_index_v1.md), [apolloveo_2_0_p2_execution_base_v1.md](../execution/apolloveo_2_0_p2_execution_base_v1.md), [apolloveo_2_0_p2_gate_checklist_v1.md](../execution/apolloveo_2_0_p2_gate_checklist_v1.md), [apolloveo_2_0_role_matrix_v1.md](../execution/apolloveo_2_0_role_matrix_v1.md)

**Reasons this minimum authority set was sufficient**: this review's task is re-anchoring, not first-principles design. Each statement below traces back to one of the read documents. No new truth is invented; nothing is taken from training-data memory of what the project "ought to be." Where the brief named a document by a Chinese label that does not exactly match a repo file, the closest concrete repo file was substituted and named explicitly; no fall-through to imagined authority.

**Missing-authority handling**: the review brief named two RFC labels (`RFC-0001 Production Line Contract`, `RFC-0002 Skills Runtime & Production Agent Framework`, `RFC-0003 OpenClaw Control Mesh Integration`) that do not exist in the repo as standalone RFC files. The substantive content of those concepts is folded into existing repo authorities — `production_line_runtime_assembly_rules_v1.md` (RFC-0001 equivalent), `skills_runtime_contract.md` + `worker_gateway_runtime_contract.md` + `ADR-phase2-skills-worker-planning.md` (RFC-0002 equivalent), and the OpenClaw concept is currently postponed (Capability Expansion Gate Wave §"红线" lists OpenClaw control mesh formalization as gated; the Platform Runtime Assembly wave Phase E names it as optional / postponed). This substitution is recorded here so future reads do not chase missing files. The brief also named `_drafts/C.1`, `_drafts/C.5`, `_drafts/E.1`; the `_drafts/` directory does not exist in the current repo (its conclusions were absorbed into `docs/baseline/` per the docs README). Treating those as historical-only is consistent with `docs/README.md` and `docs/baseline/PROJECT_BASELINE_INDEX.md`.

---

## 3. ApolloVeo Unified Identity

The team's confusion centers on conflating "what the product produces" with "how the platform is organized." This section separates them once.

### 3.1 Business-level identity

ApolloVeo is **an AI 内容生产工厂 oriented to final-deliverable content production**. Specifically (per [docs/baseline/PRODUCT_BASELINE.md](../baseline/PRODUCT_BASELINE.md) and [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)):

- the product produces a closed set of business deliverables: `final.mp4`, subtitles, audio, scene pack, metadata / manifest, publish status, archive record;
- production is organized as a chain (task creation → line/goal selection → input → parameter review → content structure → scene/audio/language plan → generate → quality check → delivery → publish → archive);
- the unit of work is a **task**, not an editing session, not a model invocation, not a tool run;
- operators are not asked to make vendor / model / provider / engine choices — those are runtime concerns hidden behind capability kinds (`understanding`, `subtitles`, `dub`, `video_gen`, `avatar`, `face_swap`, `post_production`, `pack`, `variation`, `speaker`, `lip_sync`).

ApolloVeo is **not** a studio shell, not a tool catalog, not a model marketplace, not an orchestration framework, not a multi-tenant platform. The repo's [README.md](../../README.md) and [PRODUCT_BASELINE.md](../baseline/PRODUCT_BASELINE.md) are explicit on this discipline.

### 3.2 2.0 architecture-level identity

ApolloVeo 2.0 is **the factory-shaped architectural form of the same business** — that is, the way the product's business chain is laid out across software boundaries. It is defined in [docs/architecture/apolloveo_2_0_master_plan_v1_1.md](../architecture/apolloveo_2_0_master_plan_v1_1.md) and operationalized through:

- **Five operator-visible surfaces** (per [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md)):
  Task Area / Workbench / Delivery Center / Asset Supply / Tool Backstage.
- **Ten backend domains** (per master plan v1.1 Part IV):
  `capability_adapters`, `worker_execution_envelope`, `media_processing`, `delivery_response_modeling` (with sub-domains `manifest_shaping`, `artifact_shaping`), `packet_governance`, `capability_routing_policy`, `asset_supply`, plus `ops/env/` as an independent operations domain (not in the ten).
- **Six factory-generic contract objects** (the content contracts):
  `factory_input_contract_v1`, `factory_content_structure_contract_v1`, `factory_scene_plan_contract_v1`, `factory_audio_plan_contract_v1`, `factory_language_plan_contract_v1`, `factory_delivery_contract_v1`.
- **One packet envelope + five validator rules** (the binding contract):
  `factory_packet_envelope_contract_v1.md` (E1 line_id uniqueness / E2 generic-refs path purity / E3 binds_to resolution / E4 ready_state singleton / E5 capability kind closure) + `factory_packet_validator_rules_v1.md` (R1 generic_refs resolve / R2 no generic-shape duplication / R3 capability_kind not vendors / R4 JSON Schema Draft 2020-12 loadable / R5 no truth-shape state fields).
- **Four architecture layers** (per [docs/architecture/factory_four_layer_architecture_baseline_v1.md](../architecture/factory_four_layer_architecture_baseline_v1.md)):
  Layer 0 entry / Layer 1 production line contract / Layer 2 state & projection / Layer 3 surface & execution.
- **Hot Follow as the runtime reference line, not the runtime template**: Hot Follow's runtime is the only live one; new lines do not copy its router/service residue but instead bind to the line template via the assembly rules in `production_line_runtime_assembly_rules_v1.md`.
- **SwiftCraft as capability donor only**: per [docs/adr/ADR-donor-swiftcraft-capability-only.md](../adr/ADR-donor-swiftcraft-capability-only.md) and the donor boundary / capability mapping documents — code is absorbed, never the task / state / delivery semantics.
- **Phasing**: P0 守基线 → P1 Factory Generic 基座 → P1.5 Donor 吸收冻结 → P2 Line Packet 冻结 → P3 First New-Line Runtime.
- **Inside P2 / P3 the live wave-charter sequence**: Multi-role Implementation 指挥单 → Matrix Script First Production Line Wave → Digital Anchor Second Production Line Wave → Operator-Visible Surface Validation Wave (current) → Platform Runtime Assembly Wave → Capability Expansion Gate Wave.

### 3.3 Why the team is currently confusing them

The two identities are routinely conflated because most engineering tasks touch both at once:

- A Matrix Script task creation flow is simultaneously a **business** moment (an operator submits a script) and an **architecture** moment (the form binds to a closed entry-field set, which projects into a packet, which is validated by the factory envelope and validator rules).
- A B-roll page is simultaneously a **business** affordance (operator browses a reusable asset library) and an **architecture** position (Layer 1 declarative `asset_library_object` contract + Layer 3 surface bound to the asset taxonomy + clean separation from the artifact store).
- A Hot Follow trial is simultaneously a **business** activity (operator publishes a localized video) and an **architecture** statement (Hot Follow is the reference line whose four-layer state discipline new lines must echo).

Reading a single contract or a single review answers one of those moments and not the other. The team has been reading contracts like product specs ("what the user sees") and reading reviews like architecture docs ("what we should build next") — neither reading is wrong; both readings together would be correct, but no one document gives both readings at once.

The unified alignment map proposed in `§9.3` and `§10` is the document that gives both readings together at the entry tier of every task.

---

## 4. Current Phase Judgment

### 4.1 Current wave

The current wave is the **ApolloVeo 2.0 Operator-Visible Surface Validation Wave**, also referred to in the master plan body as the "Operations Upgrade Alignment Wave" (the two are the same authority under different names; the wave-charter file is [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md), and the named clarification was made by the gap review `§2`).

Where the wave sits in the v1.1 sequence:

| Predecessor wave | Status |
| --- | --- |
| W1 Donor Absorption (M-01..M-05) | CLOSED ([W1_COMPLETION_REVIEW_v1.md](W1_COMPLETION_REVIEW_v1.md)) |
| W2 Admission Preparation (Phases A–E) | CLOSED ([W2_ADMISSION_SIGNOFF_v1.md](W2_ADMISSION_SIGNOFF_v1.md)) |
| W2.1 Base-only Adapter Preparation (B1–B4) | Implementation green; awaiting architect+reviewer signoff per evidence index |
| W2.1 First Provider Absorption (UnderstandingAdapter ← Gemini, A-03) | CLOSED |
| Matrix Script First Production Line Wave (Phases A–D) | CLOSED + Plan A trial corrections `§8.A` → `§8.H` PASS |
| Digital Anchor Second Production Line Wave (Phases A–D.0) | CLOSED at contract layer; D.1 NOT implemented |
| **Operator-Visible Surface Validation Wave** | **CURRENT** — Plan B/C/D contract layer COMPLETE; **Plan A live-trial execution PENDING** |
| Platform Runtime Assembly Wave | NOT STARTED — gated on this wave green + Plan A executed |
| Capability Expansion Gate Wave (W2.2 / W2.3 / durable persistence / runtime API / third line) | HOLD — gated on Platform Runtime Assembly signoff |

The wave-internal sequence (per gap review `§11` and `§13`):

- **Plan B** — Digital Anchor B1/B2/B3 + Matrix Script B4: contract layer **COMPLETE**; implementation gated to Plan E.
- **Plan C** — Asset Library + promote request + promote closure + scene-pack non-blocking explicit field: contract layer **COMPLETE**; implementation gated to Plan E.
- **Plan D** — Unified `publish_readiness` contract + L3 `final_provenance` + workbench panel dispatch contract + `required` / `blocking_publish` deliverable fields + L4 advisory producer output shape: contract layer **COMPLETE**; producer / runtime implementation gated to Plan E.
- **Plan A** — Operations trial readiness (operator-eligible scope freeze + coordinator runbook + sample plan + risk watch): brief **FROZEN**; static verification pass **PASS**; **live-trial execution by operations team is the single next allowed engineering action**; Plan E pre-condition #1.
- **Plan E** — next operator-visible implementation gate spec: **NOT YET OPENED**; opens only after Plan A executed and `§8` of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) carries at least one full sample-wave entry.

### 4.2 Explicitly blocked

Per [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), the gap review `§13`, the Operator-Visible Surface Validation Wave 指挥单 `§7`, the Capability Expansion Gate Wave 指挥单 §"红线", and Plan A `§4`:

- **Platform Runtime Assembly** — entry not authorized until this wave green.
- **Capability Expansion** — W2.2 (Subtitles / Dub Provider), W2.3 (Avatar / VideoGen / Storage Provider), durable persistence formalization, runtime API formalization — all on HOLD.
- **Third production line commissioning** — out of scope for this wave.
- **Frontend patching beyond what is already shipped** — no React/Vite full rebuild, no provider/model selector UI, no donor / supply concept exposure to operators.
- **Hot Follow business reopening** — Hot Follow is the runtime reference line; its A/B/C/D truth definitions MUST NOT be moved.
- **Matrix Script / Digital Anchor closed-truth mutation** — packet truth, projection truth, closure truth are all frozen for this wave.
- **Provider / model / vendor / engine controls** — forbidden at all phases by validator R3 and by the design-handoff red line 6.
- **Donor namespace import** (`from swiftcraft.*`) — forbidden by master plan v1.1 §"Verification" red line.
- **Matrix Script `§8.A` through `§8.H` reopening** — closed corrections; no retraction in this wave.
- **Discovery-only surface promotion to operator-eligible** — Digital Anchor New-Tasks card → temp route, Digital Anchor workbench placeholder, Asset Supply / B-roll page, promote intent submit, Matrix Script Delivery rows must all remain hidden / inspect-only / preview-labeled during the trial.

### 4.3 Explicitly allowed

The wave-internal *only* allowed engineering action is:

- **Plan A live-trial execution by operations team** — coordinator runs `§2.1` hide/disable guards + `§2.2` explanation 口径 + `§2.3` per-line runbook + `§11.4` and `§12.4` action items from [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md); operations team appends live-run results to `§8` placeholder; coordinator+architect+reviewer signoff on the live-trial write-up.

Adjacent always-allowed maintenance (does not require new wave authorization):

- **Documentation re-anchoring** — adding/updating root rules pointers, docs index entries, evidence index rows, review write-back; this very review is an instance of that maintenance and is authorized by the standing rule that docs do not need a wave gate when the change is purely re-anchoring.
- **Evidence write-back on already-shipped corrections** — adding execution logs, evidence files, signoff notes for work already landed.
- **Architect / reviewer signoff** of W2.1 base-only adapter B1–B4 (implementation already green; awaiting paperwork only — see evidence index "Current Known Evidence Gaps" row 3).

Nothing else is allowed in this wave. Any task that does not fit the above two buckets is out of scope and should be deferred until Plan A live-trial completes and Plan E gate opens.

---

## 5. Three Product-Line Status Map

This is the canonical per-line summary. It supersedes any earlier ad-hoc "where is line X" answer.

### 5.1 Hot Follow

- **Intended product goal** — turn a source short video into a publishable localized final video through one operator-visible workbench and one runtime chain (`ingest → parse → adapt → dub → compose → review_gate → pack_publish_sink`); singular line even when supporting multiple target-language profiles (Myanmar `mm`, Vietnamese `vi`).
- **Current achieved baseline** — runtime is real and complete:
  - `LineRegistry` + `hot_follow_line` runtime registered ([gateway/app/lines/hot_follow.py](../../gateway/app/lines/hot_follow.py));
  - Ready gate engine + status policy runtime binding live;
  - Compose service contract behind `CompositionService`;
  - Skills MVP v0 advisory closed (`skills/hot_follow`);
  - Source-audio policy / target-subtitle currentness / dub currentness fixes all closed for the active path;
  - Hot Follow reference packet validation green ([docs/execution/evidence/hot_follow_reference_packet_validation_v1.md](../execution/evidence/hot_follow_reference_packet_validation_v1.md));
  - Business-validated end-to-end (intake → publish);
  - First contract-driven production-line baseline.
- **Current missing pieces** — structural debt only, no business gap:
  - `tasks.py` (3,480 lines / 87 functions / 47 route handlers / 37 `_policy_upsert` references) still oversized; new line-specific logic forbidden;
  - `hot_follow_api.py` (2,325 lines / 71 functions / 18 `_policy_upsert`) still oversized;
  - `task_view.py::build_hot_follow_workbench_hub()` (492 lines) still mixes object facts / attempt facts / derived state / projection / advisory / line metadata / compatibility repair;
  - Compatibility helpers (e.g. `mm_*` naming) still resident; deferred to scoped follow-ups;
  - L4 advisory taxonomy authored but no producer emits the advisories (D4 contract-frozen, no service);
  - Inferred current-vs-historical via `final_fresh` + timestamps; `final_provenance` field promotion to L3 contract gated to Plan E (D2);
  - `publishable` re-derived independently in three places (Board / Workbench / Delivery); unification gated to Plan E (D1).
- **Operator-trial-ready** — **YES**. Plan A trial sample 1 (short clip golden path) and sample 2 (preserve-source route) both authorized.
- **Runtime-ready** — **YES** at Layer 3 surface; **partial** at Layer 1 (line contract metadata still partially metadata-only) and Layer 2 (4-layer projection has soft seams).
- **What must happen next** — **nothing in this wave** beyond serving as the runtime reference line for Plan A samples 1 and 2. Hot Follow MUST NOT be reopened for business behavior. Plan E will then unify Board/Workbench/Delivery `publishable` derivation, promote `final_provenance` to L3, and emit L4 advisories. Platform Runtime Assembly Wave will then handle the structural decomposition of `tasks.py` / `hot_follow_api.py` / `task_view.py`.

### 5.2 Matrix Script

- **Intended product goal** — the first official 2.0 production line; a script-driven matrix-of-variants → publishable final video pipeline, with closed `task → workbench → delivery → publish_feedback` business loop. Per the Matrix Script First Production Line Wave 指挥单 v1, the goal is "先做出一条 task → workbench → delivery → publish feedback 完整闭环的工厂样板", not a full multi-product platform.
- **Current achieved baseline** — packet-first, contract-frozen, partially runtime:
  - **Phase A** task entry contract closed; closed entry-field set (`topic`, `source_script_ref`, `language_scope`, `target_platform`, `variation_target_count` required + `audience_hint`, `tone_hint`, `length_hint`, `product_ref`, `operator_notes` optional); formal `/tasks/matrix-script/new` route landed (commit `4896f7c`); `target_language ∈ {mm, vi}`;
  - **Phase B** workbench variation surface mounted ([gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py)); panel dispatch via `panel_kind="matrix_script"` confirmed; `§8.C` deterministic Phase B authoring (3 canonical axes — `tone` / `audience` / `length` — and `variation_target_count` cells; one slot per cell; opaque `body_ref="content://matrix-script/{task_id}/slot/{slot_id}"`);
  - **Phase C** delivery binding contract frozen; `not_implemented_phase_c` placeholder rows by design ([gateway/app/services/matrix_script/delivery_binding.py:93-125](../../gateway/app/services/matrix_script/delivery_binding.py));
  - **Phase D.0** publish-feedback closure contract frozen; **D.1** write-back already shipped (per Matrix Script production-line log §"Phase D.1");
  - **`§8.A`** entry-form ref-shape guard landed (PR #83 / commit `f6125aa`);
  - **`§8.B`** workbench panel dispatch confirmation PASS (commit `970b4dc`; no narrow fix required);
  - **`§8.C`** Phase B deterministic authoring landed (Option C1; commit `9f25b89`);
  - **`§8.D`** operator brief correction landed (commit `530855c`; documentation-only);
  - **`§8.G`** Phase B panel render correctness landed (PR #88; Jinja item-access fix);
  - **`§8.E`** workbench shell suppression landed (PR #89; whitelist `{% if task.kind == "hot_follow" %}` gates around four contiguous Hot Follow-only template regions; closed list of 28 forbidden Hot Follow control tokens absent in visible HTML);
  - **`§8.F`** opaque-ref discipline tightening landed (PR #90; Option F1 only — accepted scheme set tightened from 8 to 4: `{content, task, asset, ref}`; `https`/`http`/`s3`/`gs` rejected at HTTP 400; operator transitional convention `content://matrix-script/source/<token>` pinned for Plan A trial wave; Options F2 in-product minting and F3 slippage-acceptance explicitly REJECTED in this wave);
  - **`§8.H`** operator brief re-correction landed (PR #91; documentation-only; `§0.1` sample-validity rule expanded to seven binding criteria; new `§0.2` product-meaning of `source_script_ref` as asset identity handle, not body-input, not publisher-URL ingestion, not currently dereferenced).
- **Current missing pieces**:
  - **B4** `result_packet_binding.artifact_lookup` — contract frozen ([result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md)); code change gated to Plan E. Delivery Center remains inspect-only this wave.
  - In-product minting flow (Option F2) — would replace the operator-discipline `<token>` convention; gated to Plan E.
- **Operator-trial-ready** — **YES, CONDITIONAL**. Per Plan A `§3` and `§6.2`: live-trial BLOCK released by virtue of `§8.H` land, subject to the eight conditions enumerated in trial brief `§12` (formal route + opaque ref shape + transitional convention + populated Phase B truth + mounted readable Phase B panel + shared-shell suppression intact + operator brief in force + Plan E pre-condition #1 still pending). Coordinator runs `§2.1` hide/disable + `§2.2` 口径 + `§2.3` per-line runbook + `§11.4` and `§12.4` action items before any operator session.
- **Runtime-ready** — **YES** at Layer 3 surface for entry / workbench Phase B inspection / publish-feedback closure write-back; **inspect-only** at Layer 3 surface for Delivery Center (B4 gated).
- **What must happen next** — operations team executes Plan A trial samples 3 / 4 / 5 against Matrix Script per `§7.1` of the Plan A brief; coordinator appends live-run results to `§8` placeholder of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md). No Matrix Script code change is authorized in this wave.

### 5.3 Digital Anchor

- **Intended product goal** — second official 2.0 production line; a script + role-driven digital-anchor口播成片 pipeline; closed `role_pack` (LS1) + `speaker_plan` (LS2) line-specific objects extending the six factory-generic refs; capability kinds `understanding` / `avatar` / `speaker` / `subtitles` / `dub` / `lip_sync` (optional) / `pack` (optional).
- **Current achieved baseline** — contract-only, no operator-eligible runtime:
  - **Phase A** task entry contract closed ([docs/contracts/digital_anchor/task_entry_contract_v1.md](../contracts/digital_anchor/task_entry_contract_v1.md)); closed entry-field set (`topic`, `source_script_ref`, `language_scope`, `role_profile_ref`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint` required + `dub_kind_hint`, `lip_sync_kind_hint`, `scene_binding_hint`, `operator_notes` optional);
  - **Phase B** workbench role/speaker surface contract frozen;
  - **Phase C** delivery binding contract frozen;
  - **Phase D.0** publish-feedback closure contract frozen;
  - **Plan B contracts** all frozen on 2026-05-02:
    - **B1** [create_entry_payload_builder_contract_v1.md](../contracts/digital_anchor/create_entry_payload_builder_contract_v1.md) — frozen, NOT implemented;
    - **B2** [new_task_route_contract_v1.md](../contracts/digital_anchor/new_task_route_contract_v1.md) — frozen, NOT implemented;
    - **B3** [publish_feedback_writeback_contract_v1.md](../contracts/digital_anchor/publish_feedback_writeback_contract_v1.md) — frozen, NOT implemented;
  - **Phase D.1** publish-feedback closure write-back — NOT implemented (gap review `§4` row "Digital Anchor Phase D.1" = ❌ missing).
- **Current missing pieces**:
  - Formal `/tasks/digital-anchor/new` route handler — NOT in [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py); only the generic temp `/tasks/connect/digital_anchor/new` is reachable via `_TEMP_CONNECTED_LINES`;
  - Create-entry payload builder code — no [gateway/app/services/digital_anchor/create_entry.py](../../gateway/app/services/digital_anchor/) module;
  - Phase D.1 write-back code — `publish_feedback_closure.py` exists with closure shape but no write-back path;
  - Workbench role/speaker render code — placeholder branch in [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html); no production rendering path;
  - Standalone `scene_plan_binding` and `language_output` contracts — folded into other contracts, optional standalone if trial requires;
  - Identified by gap review `§7.3` as **"数字人 UI 拼盘 risk"** — New-Tasks card and workbench placeholder exposed in commits `f753d42 → b370e46` ahead of packet truth.
- **Operator-trial-ready** — **NO**. Inspection-only this wave per Plan A `§3.1` and `§6.3`. Operators may open the New-Tasks landing page and confirm the Digital Anchor card exists; they MUST NOT click through to submit. Coordinator MUST hide both the card click target and the temp URL.
- **Runtime-ready** — **NO**. Contract-frozen everywhere; runtime gated to Plan E.
- **What must happen next** — **nothing in this wave** beyond Plan A inspection-only sample (operator confirms preview-labeled card). Plan E will then implement B1 + B2 + B3 + Phase D.1 write-back + Phase B render, in that order, before Digital Anchor becomes trial-eligible. After Plan E green and Platform Runtime Assembly green, Digital Anchor moves to first-class line status.

---

## 6. B-roll / Asset Supply Positioning

### 6.1 Current product freeze status

B-roll / Asset Supply has product-level authority frozen:

- [docs/product/broll_asset_supply_freeze_v1.md](../product/broll_asset_supply_freeze_v1.md) — facets (8 first-class), promote semantics (admin-reviewed, async, intent-based), license / source / reuse policy field set, canonical/reusable badges (admin-only state with operator-visible badges), detail actions scope, artifact-to-asset hand-off boundary, reference-into-task pre-population mapping, deferred items.
- [docs/product/asset_supply_matrix_v1.md](../product/asset_supply_matrix_v1.md) — per-line operator-supplied input asset kinds × per-line line-produced deliverable kinds; closed kind sets; supply-truth-vs-donor decoupling rules; per-line application table.
- [docs/design/broll_asset_supply_lowfi_v1.md](../design/broll_asset_supply_lowfi_v1.md) — operator-visible surface low-fi.

### 6.2 Contract layer status (corrected)

The wording of the gap review `§9` ("Contract layer empty: no `asset_library_object_contract_v1.md`, no `promote_request_contract_v1.md`, no `promote_feedback_closure_contract_v1.md`") was correct **as of 2026-05-02 morning**. It is now **superseded** — Plan C contracts landed in PR #80 / commit `6052014` on 2026-05-02 the same day:

- ✅ [docs/contracts/asset_library_object_contract_v1.md](../contracts/asset_library_object_contract_v1.md) — closed metadata schema (`asset_id`, `kind`, `line_availability[]`, `tags[]`, `provenance.{origin_kind, origin_ref, content_hash, promoted_from_artifact_ref}`, `version`, `quality_threshold`, `quality.summary`, `usage_limits.{license, reuse_policy, reuse_notes}`, `title`, `created_at`, `created_by`, `badges`); closed `kind` enum (15 kinds); closed facet set (8 facets); license enum (5 values); reuse_policy enum (5 values); quality_threshold enum (`{draft, review, approved}`); versioning rule; validator alignment (R3 / R5).
- ✅ [docs/contracts/promote_request_contract_v1.md](../contracts/promote_request_contract_v1.md) — promote intent request schema.
- ✅ [docs/contracts/promote_feedback_closure_contract_v1.md](../contracts/promote_feedback_closure_contract_v1.md) — promote audit trail mirror with closed states.
- ✅ amendments to [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (`required: boolean` + `blocking_publish: boolean` per-deliverable + `scene_pack_blocking_allowed: false` explicit field) and to [docs/contracts/hot_follow_projection_rules_v1.md](../contracts/hot_follow_projection_rules_v1.md) (explicit scene-pack non-blocking).

The remaining gap is **operator-workspace implementation only**:

- no asset-library service module ([gateway/app/services/asset_library/](../../gateway/app/services/) does not exist);
- no promote intent service module;
- no promote closure service module;
- no operator-visible Asset Supply / B-roll page;
- no admin-side review surface;
- no `mark_reusable_or_canonical_intent` flow.

### 6.3 Correct future insertion point

B-roll / Asset Supply is positioned in three architecture layers:

| Layer | Position | Status |
| --- | --- | --- |
| Layer 0 entry & authority | Read-only consumer of root rules | n/a |
| Layer 1 production line contract | `asset_supply_matrix` declarations (per-line input/deliverable kinds) + `factory_input_contract_v1`'s `business_metadata` envelope reference | ✅ frozen |
| Layer 1 cross-line contract | `asset_library_object_contract_v1` + `promote_request_contract_v1` + `promote_feedback_closure_contract_v1` | ✅ frozen on 2026-05-02 |
| Layer 2 state & projection | Asset metadata is read-only across line packets; assets are not packet truth; promote intent state lives outside packets | ✅ defined |
| Layer 3 surface & execution | Asset Supply page (read-only); promote intent UI; admin review UI; asset-library service code | ❌ all gated to Plan E |

The correct **insertion sequence**:

1. **NOT in this wave**. The Asset Supply / B-roll page is "discovery-only" per gap review `§6` and Plan A `§4.1` — it MUST be hidden during the trial. No surface implementation, no service implementation, no asset CRUD, no promote service.
2. **In Plan E** (next operator-visible implementation gate, opens after Plan A live-trial executed and write-up filed):
   - Asset Library page (read-only) backed by `asset_library_object_contract_v1`;
   - Promote intent UI backed by `promote_request_contract_v1`;
   - Promote closure surface backed by `promote_feedback_closure_contract_v1`;
   - Asset-library service module under `gateway/app/services/asset_library/` (new directory; per master plan v1.1 Part IV.1 the host path is `gateway/app/services/asset/`);
   - Cross-checks against `asset_supply_matrix_v1.md` per-line declarations;
   - Validator R3 enforcement (no vendor/model/provider/engine identifiers in any field).
3. **NOT in Platform Runtime Assembly Wave**. Asset library is at Layer 1 cross-line surface — it does not require runtime decomposition of `tasks.py`. It needs Plan E surface implementation, not platform runtime assembly.
4. **Possibly extended in Capability Expansion Gate Wave** if asset CRUD UI / bulk import / facet value administration / asset versioning as primary promote path are needed (per `broll_asset_supply_freeze_v1.md` §"Deferred Items").

The decoupling rule from `asset_supply_matrix_v1.md` §"Decoupling rules" remains binding at every step: **supply truth MUST NOT name a donor; donor MUST NOT redeclare supply truth; closed kind-sets are owned by supply; capability mode is descriptive not selective; asset references are opaque across the boundary; no truth round-trip from donor to supply; frontend MUST NOT cross the boundary.**

---

## 7. Current Accepted Baseline vs Missing Product Surface

### 7.1 What is truly stabilized

These authorities are accepted truth for this wave and the next. Future tasks may consume them without re-reviewing.

**Root governance & entry discipline**:

- Root rules ([README](../../README.md), [PROJECT_RULES](../../PROJECT_RULES.md), [ENGINEERING_RULES](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS](../../ENGINEERING_STATUS.md), [ENGINEERING_CONSTRAINTS_INDEX](../../ENGINEERING_CONSTRAINTS_INDEX.md), [CHANGELOG_STAGE](../../CHANGELOG_STAGE.md), [apolloveo_current_architecture_and_state_baseline](../../apolloveo_current_architecture_and_state_baseline.md)).
- Docs entry indexes ([docs/README](../README.md), [docs/ENGINEERING_INDEX](../ENGINEERING_INDEX.md), [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md)).
- Project / product / architecture / execution baselines under [docs/baseline/](../baseline/).

**Architecture target**:

- v1.1 master plan ([apolloveo_2_0_master_plan_v1_1.md](../architecture/apolloveo_2_0_master_plan_v1_1.md)) — the only repo-level mother plan.
- Top-level business flow ([apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)).
- Factory four-layer baseline ([factory_four_layer_architecture_baseline_v1.md](../architecture/factory_four_layer_architecture_baseline_v1.md)).
- Factory line template + runtime boundary + workbench mapping.
- Hot Follow business flow as reference.

**Factory contracts** (the six generic + envelope + validator + state-model surface):

- All six factory-generic content contracts.
- Packet envelope (E1–E5) + validator rules (R1–R5).
- Production-line runtime assembly rules.
- Four-layer state contract + status ownership matrix + workbench hub response contract.
- Line template design.

**Per-line authority**:

- Hot Follow line contract + ready gate + projection rules + state machine + current-attempt contract + runtime contract + reference packet validation evidence.
- Matrix Script Phases A–D contracts + `§8.A` / `§8.C` / `§8.F` addenda + Phase D.1 implementation.
- Digital Anchor Phases A–D.0 contracts + Plan B B1/B2/B3 contracts.

**Plan B / C / D cross-line contracts** (landed 2026-05-02, PR #80 / commit `6052014`):

- B1 / B2 / B3 Digital Anchor; B4 Matrix Script result_packet_binding artifact lookup.
- C1 asset_library_object; C2 promote_request; C3 promote_feedback_closure; C4 factory_delivery `required` / `blocking_publish` / `scene_pack_blocking_allowed: false`.
- D1 publish_readiness; D2 final_provenance L3 amendment to hot_follow_current_attempt; D3 workbench_panel_dispatch (with `§8.E` shared-shell-neutrality addendum on 2026-05-03); D4 l4_advisory_producer_output.

**Donor governance**:

- SwiftCraft donor boundary, capability mapping, ADR, host directory predisposition.
- W1 absorption complete (M-01..M-05).
- W2 admission Phases A–E closed.

**Operations trial readiness**:

- Plan A operations trial brief ([OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)) — frozen with `§0.1` (seven sample-validity criteria) + `§0.2` (product-meaning of `source_script_ref`) + `§3` / `§4` / `§5` / `§6` / `§7` / `§8` operator-eligible vs forbidden scope.
- Plan A coordinator write-up ([PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md)) — static verification PASS; `§11` `§8.D` addendum + `§12` `§8.E`/`§8.F`/`§8.G`/`§8.H` follow-up addendum.

**Operator transitional convention**:

- `content://matrix-script/source/<token>` for Plan A trial wave (Option F1; Plan E Option F2 minting flow is the future replacement).

### 7.2 What is only contract / projection-valid (not yet operator-valid)

These have contract truth; their producers / services / runtime do not yet exist. Operators MUST NOT see these as features:

- Digital Anchor B1 create-entry payload builder.
- Digital Anchor B2 formal `/tasks/digital-anchor/new` route handler.
- Digital Anchor B3 publish-feedback write-back implementation.
- Digital Anchor Phase D.1 closure write-back implementation.
- Digital Anchor Phase B workbench role/speaker render production path.
- Matrix Script B4 result_packet_binding artifact lookup.
- Matrix Script Plan E Option F2 in-product minting flow (replaces operator transitional `<token>` convention).
- Asset Library service / page (C1).
- Promote intent service / UI (C2).
- Promote closure service / admin review UI (C3).
- Unified `publish_readiness` producer (D1) — Board / Workbench / Delivery still re-derive locally.
- L3 `final_provenance` field producer / emitter (D2) — UI still infers current-vs-historical.
- Workbench panel dispatch as runtime contract object (D3) — still in-code dict at `gateway/app/services/operator_visible_surfaces/projections.py:239-246`.
- L4 advisory producer / emitter (D4) — taxonomy frozen; no service emits.
- W2.1 base-only adapter B1–B4 architect+reviewer signoff (implementation green; paperwork only).

### 7.3 What is still discovery-only

These surfaces exist in the deployed branch but expose shapes whose contract / runtime is not yet operator-eligible. Plan A `§4.1` lists them; coordinator MUST hide / disable / preview-label during the trial:

- Digital Anchor New-Tasks card click target ([gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html)).
- Generic temp route `/tasks/connect/digital_anchor/new` (via `_TEMP_CONNECTED_LINES`).
- Digital Anchor workbench placeholder branch.
- Matrix Script Delivery Center per-row placeholders (`not_implemented_phase_c`) — visible to operator, but **inspect-only**, never operate.
- Asset Supply / B-roll page (no template/route shipped; if one is added without a contract-backed service, treat as discovery-only).
- Promote intent submit affordance.

### 7.4 What is still missing at the operator-workspace level

Concrete operator-facing missing pieces (gated to Plan E):

1. **Digital Anchor end-to-end run** — operator submits a Digital Anchor task and proceeds through workbench role/speaker authoring + delivery binding + publish-feedback closure.
2. **Asset Supply browsing** — operator filters the B-roll library by closed facets, sees license / reuse_policy / canonical / reusable badges, references an asset into a task.
3. **Promote intent submission** — operator promotes a task artifact to a reusable Asset Library object; tracks status (`submitted` / `under_review` / `accepted` / `rejected`).
4. **Unified `publishable` truth** — Board, Workbench, Delivery agree because they consume one `publish_readiness_contract_v1` producer.
5. **Current vs historical strip in Workbench** — operator sees `final_provenance: current | historical` from L3 truth, not inferred from `final_fresh` + timestamps.
6. **Per-deliverable required vs optional vs scene_pack zoning** — Delivery Center renders `required` / `blocking_publish` from contract fields, not in-code mapping.
7. **L4 advisory rendering** — Workbench / Publish surfaces render the Hot Follow advisory taxonomy (`hf_advisory_*`) emitted by a producer service.
8. **Matrix Script Delivery binding artifact resolution** — operator sees real deliverable rows for Matrix Script (replacing `not_implemented_phase_c` placeholders).
9. **In-product `content://` mint for Matrix Script** — operator obtains opaque ref handles from a product service, replacing the operator-discipline `<token>` convention (Option F2).

The order of these in Plan E is for the Plan E gate spec to fix; this review does not pre-decide it.

---

## 8. Review History Reclassification

The team has been experiencing the `docs/reviews/` directory as an undifferentiated pile of 30+ files. The classification below replaces that pile with five clean buckets. Each future task should know which bucket(s) the relevant review lives in.

### 8.1 Foundational architecture reviews

Long-term gates and framework-setting documents. These do not expire when a wave closes. They are read once per major task.

- [docs/reviews/2026-03-18-plus_factory_alignment_code_review.md](2026-03-18-plus_factory_alignment_code_review.md) — **the active code-validation gate**; required citation for any PR touching new-line onboarding / `tasks.py` / `hot_follow_api.py` / `task_view.py` structural / 4-layer state / ready gate / deliverables SSOT / Skills / Worker Gateway / line contract runtime binding / publish/workbench contracts.
- [docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md](2026-03-18-plus_factory_alignment_code_review_summary.md) — short verdict + ten ordered prerequisites.
- [docs/reviews/ALIGNMENT_BASELINE_20260318.md](ALIGNMENT_BASELINE_20260318.md) — predecessor architecture alignment baseline.
- [docs/reviews/ALIGNMENT_EXECUTION_REVIEW_20260321.md](ALIGNMENT_EXECUTION_REVIEW_20260321.md) — execution-boundary follow-up.
- [docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md](VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md) — docs structure and shared-logic foundation.
- [docs/reviews/VEOBASE01_POST_PR5_GATE_REVIEW.md](VEOBASE01_POST_PR5_GATE_REVIEW.md) — VeoBase01 reconstruction gate.
- [docs/reviews/architect_phase2_lowfi_review_v1.md](architect_phase2_lowfi_review_v1.md) — Phase 2 operator-visible surfaces architect CONDITIONAL PASS review.
- [docs/reviews/review_jellyfish_importability_for_factory.md](review_jellyfish_importability_for_factory.md) — Jellyfish donor importability constraints (intermediate planning structures only; not studio shell).
- [docs/reviews/appendix_code_inventory.md](appendix_code_inventory.md), [appendix_four_layer_state_map.md](appendix_four_layer_state_map.md), [appendix_line_contract_skill_readiness.md](appendix_line_contract_skill_readiness.md), [appendix_router_service_state_dependency_map.md](appendix_router_service_state_dependency_map.md) — foundational appendices to the factory alignment review.

### 8.2 Current-wave gating reviews

Reviews that gate or close a specific current-wave decision. Read for the wave they belong to; archive once the wave closes.

**P2-readiness phase** (Phase A of the multi-role 指挥单, gating P2 entry):

- [docs/reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md](APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md) — P2 pre-readiness review.
- [docs/reviews/APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md](APOLLOVE0_2_0_PLAN_CONCLUSION_CONFIRMATION_REVIEW.md) — confirms latest `main` is consistent with v1.1 master plan; B/Mostly aligned.

**Operator-Visible Surface Validation Wave gating** (current wave):

- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](operations_upgrade_gap_review_and_ops_plan_v1.md) — **THE current-wave authority review**; defines Plan A → B → C → D → E sequence; identifies B-roll contract gap, Digital Anchor 数字人 UI 拼盘 risk, projection drift risks; gives line-by-line / surface-by-surface scope; recommends; final gate decision.
- [docs/reviews/operator_visible_surface_wiring_feasibility_v1.md](operator_visible_surface_wiring_feasibility_v1.md) — engineering wiring feasibility memo for the wave.

**Donor / W1 / W2 wave gating**:

- [docs/reviews/W1_COMPLETION_REVIEW_v1.md](W1_COMPLETION_REVIEW_v1.md) — W1 donor absorption closure.
- [docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md](W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md) — W2 admission AdapterBase lifecycle review.
- [docs/reviews/W2_ADMISSION_SIGNOFF_v1.md](W2_ADMISSION_SIGNOFF_v1.md) — W2 admission Phase E signoff.
- [docs/reviews/architect_signoff_packet_gate_v1.md](architect_signoff_packet_gate_v1.md) — packet gate architect signoff.
- [docs/reviews/b6_adapter_signoff.md](b6_adapter_signoff.md) — adapter signoff.

### 8.3 Line-specific blocker reviews

Reviews that block a specific line until specific corrections land. Closed when the named correction items PASS.

**Matrix Script blocker chain**:

- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](matrix_script_trial_blocker_and_realign_review_v1.md) — `§8.A` entry-form ref-shape + `§8.B` panel dispatch + `§8.C` Phase B authoring + `§8.D` operator brief; all four PASS.
- [docs/reviews/matrix_script_followup_blocker_review_v1.md](matrix_script_followup_blocker_review_v1.md) — `§8.E` shell suppression + `§8.F` opaque-ref discipline + `§8.G` Phase B render correctness + `§8.H` operator brief re-correction (successor); all four PASS.
- (No third Matrix Script blocker is open. The chain is closed.)

**Hot Follow blocker / freeze reviews**:

- [docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md](HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md) — Hot Follow current-branch final acceptance freeze.
- [docs/reviews/HOT_FOLLOW_LINE_FOUR_STATE_REVIEW.md](HOT_FOLLOW_LINE_FOUR_STATE_REVIEW.md) — four-layer state review for Hot Follow line.
- [docs/reviews/HOT_FOLLOW_COMPOSE_GUARD_ROLLBACK_REVIEW.md](HOT_FOLLOW_COMPOSE_GUARD_ROLLBACK_REVIEW.md) — Hot Follow compose guard rollback review.
- [docs/reviews/HOT_FOLLOW_COMPOSE_NARROW_REWORK_PLAN.md](HOT_FOLLOW_COMPOSE_NARROW_REWORK_PLAN.md) — narrow rework plan.
- [docs/reviews/HOT_FOLLOW_URL_STATE_INSTABILITY_REVIEW_v1.md](HOT_FOLLOW_URL_STATE_INSTABILITY_REVIEW_v1.md) — URL state instability review.
- [docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md](VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md) — Hot Follow subtitle authority review.

### 8.4 Execution evidence

Not strictly reviews — these are the evidence files that prove a correction or wave landed. Read when verifying that something is actually shipped, not for future planning.

- [docs/execution/apolloveo_2_0_evidence_index_v1.md](../execution/apolloveo_2_0_evidence_index_v1.md) — **the evidence index entry**; consume this before any per-evidence file.
- All eight Matrix Script `§8.A` → `§8.H` execution logs under [docs/execution/](../execution/).
- [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) — Plan A coordinator write-up (static-pass + `§11` + `§12` addenda).
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) — Plan B/C/D contract freeze.
- [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](../execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md](../execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md) — per-line wave logs.
- All [docs/execution/evidence/*.md](../execution/evidence/) files — per-phase evidence.
- [docs/execution/logs/PHASE2_PROGRESS_LOG.md](../execution/logs/PHASE2_PROGRESS_LOG.md), [VEOSOP05_PROGRESS_LOG.md](../execution/logs/VEOSOP05_PROGRESS_LOG.md) — long-running progress logs.

### 8.5 Discovery-only / historical references

Useful for "how did we get here" but not for "what should we do next." Should NOT be cited as authority in any current-wave PR.

- [docs/reviews/v1.9/REVIEW_REPORT_v1.9.md](v1.9/REVIEW_REPORT_v1.9.md) — v1.9 review package.
- [docs/archive/v1.9/REVIEW_v1.9_BASELINE.md](../archive/v1.9/REVIEW_v1.9_BASELINE.md) — historical v1.9 baseline.
- [docs/archive/](../archive/) — superseded / legacy contracts.
- [docs/reviews/REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md](REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md) — post-VeoSOP04 demining review.
- [docs/reviews/TASK_1_3_PORT_MERGE_PLAN.md](TASK_1_3_PORT_MERGE_PLAN.md), [docs/reviews/TASK_2_0_COMPOSE_SURGERY.md](TASK_2_0_COMPOSE_SURGERY.md), [docs/reviews/TASK_2_3_READY_GATE_REPORT.md](TASK_2_3_READY_GATE_REPORT.md) — one-off task-specific historical analyses.
- [docs/reviews/review_20260317.md](review_20260317.md) — pre-2026-03-18 review (superseded by the active gate).
- [_drafts/](../../_drafts/) — does not exist; conclusions absorbed into `docs/baseline/`. If anyone references `_drafts/C.1` or similar, the equivalent is now in `docs/baseline/PRODUCT_BASELINE.md` §"Historical Material" pointers.

---

## 9. Documentation Re-anchoring Plan

The repo's documentation is well-organized at the bucket level (per [docs/README.md](../README.md)). The re-anchoring is not about moving files; it is about adding a single navigation tier between root rules and the docs index, and updating the read-order so that index-first reading consumes the unified alignment map before drilling into per-bucket authority.

### 9.1 Root-level rules

Stay as-is. The eight root files form a coherent governance tier and should not be expanded:

- [README.md](../../README.md) — repo intro + Start Here.
- [PROJECT_RULES.md](../../PROJECT_RULES.md) — doc-usage / merge / engineering / validation / forbidden-until-gate-clears.
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) — file/function size / router/service ownership / import / contract-first / compatibility / truth-source / factory-alignment-gate / validation / scope-control.
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — current main line + allowed/forbidden + merge gates + structural risks.
- [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) — current stage + active gate + completion log + remaining structural risks.
- [ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md) — engineering-only constraints + big-file / router-service / single-writer / PR-slicing / validation / write-back rules.
- [CHANGELOG_STAGE.md](../../CHANGELOG_STAGE.md) — freeze points + closure points + recent milestones.
- [apolloveo_current_architecture_and_state_baseline.md](../../apolloveo_current_architecture_and_state_baseline.md) — current architecture + state baseline.

**Recommended additive change** (single line each in [README.md](../../README.md) `Start Here` and [ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md) "Required Future Pre-Read"): add a pointer to the unified alignment map between item 5 (`docs/contracts/engineering_reading_contract_v1.md`) and item 6 (existing minimum task-specific authority pointer). Wording: "5.5. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` (cross-cutting cognition map; consume before drilling into per-bucket authority)." — that is, if `§11` accepts the recommendation to create the map. If not, no change.

### 9.2 Docs indexes

Stay as-is in placement; receive one additive pointer.

- [docs/README.md](../README.md) — directory map + bucket purpose + read-discipline.
- [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md) — document priority + authoritative files by concern + task-oriented reading map + VeoBase01 reconstruction entry + forbidden doc misuse + PR pre-read / write-back checklist + new-line gate.
- [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md) — index-first mandatory reading order + task-type routing defaults + reading declaration requirement.

**Recommended additive change** (one row each): in [docs/README.md](../README.md) §"Current Source-Of-Truth Reading Discipline" add the unified alignment map between step 3 (reading contract) and step 4 (minimum task-specific authority); same in [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md) §"Document Priority". Both changes are conditional on `§11` accepting the new map.

### 9.3 Unified cognition document

**Recommendation**: create [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) as a permanent navigation document. It is **not** a review (point-in-time judgment), **not** a contract (truth definition), **not** a product spec (operator-facing), **not** an execution log (evidence). It is a navigation map.

**Purpose**:

- Give the cold reader the seven answers (`§1` of this review) in one place.
- Anchor task classification: a task hits the map first, and the map points to the bucket(s).
- Avoid the situation where the team rebuilds cognition every wave by re-reading 30+ docs.

**Content** (proposed structure; details for the document author, not this review):

1. **Identity** — business-level + 2.0 architecture-level + the difference (per `§3` here).
2. **Current wave** — name, phase position in v1.1 sequence, what is allowed, what is blocked, what is the single next action (per `§4` here).
3. **Three-line status matrix** — single table: `line | trial-ready | runtime-ready | next action | authority pointer` (per `§5` here).
4. **B-roll / Asset Supply position** — at which layers; what is contract-frozen vs operator-eligible (per `§6` here).
5. **Five review buckets** — pointer to `§8` here.
6. **Read-order** — root rules → docs index → unified alignment map → reading contract → bucket-specific authority (per `§9.4` here).
7. **What this map IS NOT** — explicit list to prevent misuse (see "Differs from" below).

**Differs from**:

- **Reviews** (under `docs/reviews/`) are point-in-time judgments with a verdict and a correction list. The map has no verdict; it points at where verdicts live.
- **Contracts** (under `docs/contracts/`) are normative truth (a packet MUST have field X). The map has no normative power; it tells you where the contract is.
- **Product docs** (under `docs/product/` + `docs/handoffs/`) are operator-facing or role-handoff specs. The map is engineering-facing only and never seen by operators.
- **Architecture docs** (under `docs/architecture/`) define structural design (four layers, line template, runtime boundary). The map references them; it does not redefine them.
- **Wave 指挥单** (under `docs/architecture/ApolloVeo_2.0_*_Wave_*指挥单*_v1.md`) are wave-internal execution briefs. The map names the active 指挥单 by file path; it does not replicate or override its scope.
- **Execution logs** (under `docs/execution/`) are evidence. The map references the evidence index; it does not list per-PR logs.
- **Master plan v1.1** is the architect's mother plan with phasing, donor strategy, and verification rules. The map cites the master plan; it does not redefine the phasing.

The map is a thin meta-document. Estimated length: 200–400 lines. It is updated only when a wave closes or a major identity / phase shift occurs (perhaps every 2–6 weeks). Not every PR triggers a map update.

### 9.4 Product / architecture / contracts / execution / reviews reading order

The recommended read-order for any future engineering / docs / review task:

1. **Root rules** — eight files in [§9.1](#91-root-level-rules). Read once per task class to confirm scope is allowed.
2. **Docs entry indexes** — three files in [§9.2](#92-docs-indexes). Read to determine the bucket.
3. **Unified alignment map** ([docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md)) — **NEW**; consume to confirm what wave / line / surface the task touches.
4. **Reading contract** ([docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md)) — read for index-first discipline + reading declaration template.
5. **Architecture target** — read what the task MUST conform to ([master plan v1.1](../architecture/apolloveo_2_0_master_plan_v1_1.md), [top-level flow](../architecture/apolloveo_2_0_top_level_business_flow_v1.md), [factory four-layer baseline](../architecture/factory_four_layer_architecture_baseline_v1.md), [line template](../architecture/factory_line_template_design_v1.md), the active wave 指挥单).
6. **Per-line / per-surface contracts** — read for the specific line(s) / surface(s) the task touches.
7. **Factory-generic + envelope + validator + Plan B/C/D contracts** — read for cross-cutting truth.
8. **Plan A trial readiness + coordinator write-up** — read if the task touches operator trial scope.
9. **Current-wave gating reviews** — read for the wave's verdict and remaining blockers (currently the gap review is the load-bearing one).
10. **Line-specific blocker reviews** — read only for lines under active correction (currently Matrix Script `§8.A` → `§8.H` chain is closed; no open chains).
11. **Execution evidence** — read for verification / write-back template.
12. **Foundational architecture reviews** — read for long-term gates (factory alignment 2026-03-18+ is the active code-validation gate).

Discovery-only / historical references — **do not read for current-wave decisions**.

---

## 10. Recommended Next Engineering Sequence

Frozen. One sequence. No parallel drift.

### Step 1. Plan A live-trial execution (single next allowed action)

**Owner**: Operations team coordinator + product / design / architect / reviewer roles per the role matrix in [docs/execution/apolloveo_2_0_role_matrix_v1.md](../execution/apolloveo_2_0_role_matrix_v1.md).

**Pre-conditions** (all must hold; verify before kickoff):

- Plan B / C / D contracts frozen — ✅ verified by [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) §"Final gate".
- Matrix Script `§8.A` → `§8.H` corrections all PASS — ✅ verified by ENGINEERING_STATUS.md "Current Completion" + Plan A write-up `§12.2` table.
- Plan A static verification PASS — ✅ verified by [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) `§3` and `§9`.
- Coordinator hide/disable guards (`§2.1` of write-up) achievable in trial environment — coordinator-side check.
- Coordinator explanation 口径 (`§2.2`) and per-line runbook (`§2.3`) and `§11.4` + `§12.4` action items prepared — coordinator-side check.

**Action**:

- Coordinator runs `§2.1` hide guards: Digital Anchor card click target + temp `/tasks/connect/digital_anchor/new` + Asset Supply / B-roll page + promote intent submit affordance — all hidden / disabled / preview-labeled in the trial environment.
- Coordinator briefs operators on `§5.1` Task Area / `§5.2` Workbench / `§5.3` Delivery Center 口径 verbatim, plus `§0.1` Matrix Script sample-validity rule (seven binding criteria) and `§0.2` product-meaning of `source_script_ref` (asset identity handle, not body-input, not URL ingestion, not currently dereferenced).
- Operations team executes Plan A `§7.1` samples 1–6 in order:
  1. Hot Follow short-clip golden path.
  2. Hot Follow preserve-source route.
  3. Matrix Script fresh contract-clean small variation plan (`variation_target_count=4`, `target_language=mm`, `source_script_ref=content://matrix-script/source/<token>`).
  4. Matrix Script multi-language target (`target_language=vi`).
  5. Matrix Script variation count boundary check (`variation_target_count=1` and `=12`).
  6. Cross-line `/tasks` Board inspection.
- Plan A `§7.2` samples are explicitly excluded; coordinator stops the trial if any `§7.2` pattern is observed.
- Coordinator monitors Plan A `§5` Risk Watch: Digital Anchor card reaches a create form / vendor selector appears / scene-pack treated as blocker / Workbench panel mount fails / Board ↔ Workbench ↔ Delivery `publishable` divergence is operator-confusing — pause + file regression.
- Operations team appends live-run results to `§8` placeholder of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) using the prescribed format.
- Coordinator + architect + reviewer signoff on the live-trial entry.

**Deliverable**: at least one full sample-wave entry in `§8` of the Plan A coordinator write-up; Plan E pre-condition #1 satisfied.

**Hard red lines for Step 1**:

- no code, UI, contract, schema, sample, or template change as a result of trial findings (regressions become Plan E or Platform Runtime Assembly tasks);
- no Hot Follow business reopening triggered by trial observations;
- no Matrix Script `§8.A` → `§8.H` retraction;
- no Digital Anchor submission attempt;
- no Asset Supply / promote operation;
- no vendor / model / provider / engine selector exposure;
- no third-line entry.

### After Step 1 lands — what becomes allowed

After the Plan A live-trial write-up is signed off:

- **Step 2 — Plan E gate spec** (next operator-visible implementation gate): authored as a separate review document; defines pre-conditions, forbidden scope, permitted scope, acceptance.
- **Step 3 — Plan E implementation** (in the order Plan E spec dictates; expected ordering per gap review `§11`): Digital Anchor B1/B2/B3 + Phase D.1 write-back + Phase B render → Asset Library + promote services + UI → unified `publish_readiness` producer + L3 `final_provenance` + workbench panel dispatch contract object + per-deliverable `required` / `blocking_publish` rendering + L4 advisory producer/emitter → Matrix Script B4 artifact lookup → Matrix Script Option F2 in-product minting flow.

This review does **not** pre-decide Plan E's internal ordering. The Plan E gate spec authors decide that, after Plan A executes.

After Plan E green:

- **Step 4 — Platform Runtime Assembly Wave** (per [Platform Runtime Assembly Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Platform_Runtime_Assembly_Wave_指挥单_v1.md) §6): Phase A shared logic port merge → Phase B compose / large service extraction → Phase C declarative ready gate → Phase D runtime assembly skeleton → Phase E OpenClaw / external control stub (optional, postponed).

After Platform Runtime Assembly green:

- **Step 5 — Capability Expansion Gate Wave** (per [Capability Expansion Gate Wave 指挥单 v1](../architecture/ApolloVeo_2.0_Capability_Expansion_Gate_Wave_指挥单_v1.md) §"解锁顺序建议"): W2.2 → W2.3 → durable persistence → runtime API → third production line commissioning.

The sequence is sequential. No step is allowed to start before its predecessor signs off.

### Hard red lines (sequence-wide)

- do not skip Step 1 by running Plan E preparation in parallel — the Plan E gate spec depends on Plan A live-run findings;
- do not preempt Step 4 by running W2.2 / W2.3 work — Capability Expansion is gated on Platform Runtime Assembly signoff per Capability Expansion Gate Wave §"解锁条件";
- do not treat any "discovery-only" surface as a milestone — Plan A `§4.1` says they MUST be hidden during the trial;
- do not let any signoff document this review without re-reading the eight root files first.

---

## 11. Gate Recommendation

### Current cognition restored: **YES**

This review consolidates `§1` through `§10` into a single coherent map of:

- what ApolloVeo is at the business level;
- what ApolloVeo 2.0 is at the architecture level;
- what wave the repo is currently in;
- what each line is and is not;
- where B-roll / Asset Supply belongs (with the contract layer correction);
- what is already stable;
- what is still missing at the operator-workspace level;
- what the next single engineering action is.

Cognition is restored at the document level. Whether each role's individual cognition is restored requires those roles to read this review (or the unified alignment map proposed below) before their next task slice.

### Current docs need re-anchoring: **YES** (additive only)

The recommended re-anchoring is **additive**, not destructive:

- **Add** a permanent navigation document at [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) (see `§9.3` for purpose / content / what-it-is-not).
- **Add one pointer** to the unified alignment map in [README.md](../../README.md) `Start Here`, in [docs/README.md](../README.md) §"Current Source-Of-Truth Reading Discipline", in [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md) §"Document Priority", and in [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md) §"Mandatory Reading Order Before Code Changes".
- **Add** a pointer to this review (`§8` Review History Reclassification) so future readers can look up which bucket a review file lives in without re-classifying every time.
- **No file moves, no file deletes, no file rewrites** — the docs structure already cleanly separates `baseline/`, `execution/`, `reviews/`, `contracts/`, `adr/`, `architecture/`, `runbooks/`, `skills/`, `archive/`, `product/`, `design/`, `handoffs/`, `donor/`. The bucket organization is correct.

The re-anchoring is one small PR, documentation-only, no scope drift.

### New unified map should become default entry: **YES**

The proposed unified alignment map at [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) should be added at the same authority tier as [docs/README.md](../README.md) and [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), positioned **between** the docs entry indexes and the engineering reading contract.

The justification:

- Without it, future tasks will continue to rebuild cognition by re-reading 30+ documents — the same failure mode that produced the eight-step Matrix Script correction chain.
- With it at the default-entry tier, any task hits a single 200–400 line navigation document first, classifies its scope against the map, and only then drills into per-bucket authority.
- It is shorter than the docs index (which is bucket-organized) and the engineering reading contract (which is task-class-organized) — it is wave / line / phase / surface organized, which is the missing organizational axis.

The map should be created as a separate documentation-only PR, not bundled with this review. This review is the authority that authorizes the map's creation; the map itself is the next deliverable.

---

## 12. What This Review Does Not Do

Restated explicitly, so future readers do not extend it:

- This review does not implement any code, UI, template, schema, sample, test, or contract change.
- This review does not retract or extend any closed Matrix Script correction step (`§8.A` through `§8.H`).
- This review does not authorize Platform Runtime Assembly Wave entry — gated on Plan A live-trial execution.
- This review does not authorize Capability Expansion Gate Wave entry — gated on Platform Runtime Assembly signoff.
- This review does not promote any discovery-only surface to operator-eligible.
- This review does not drift into a fragmented secondary review of one local issue — its purpose is unification.
- This review does not redefine any contract — every contract reference is by file path, not by re-quoted field.
- This review does not replace any wave 指挥单 — the active wave authority is still the Operator-Visible Surface Validation Wave 指挥单 v1.
- This review does not pre-decide Plan E's internal ordering — that is the Plan E gate spec's job, after Plan A live-trial executes.
- This review does not name any vendor, model, provider, or engine — validator R3 applies to review content too.

---

## 13. Final Statement

ApolloVeo's authority surface is rich, frozen, and largely correct. The single missing piece is a navigation map that ties identity, wave, lines, B-roll position, baseline, missing surfaces, review history, and next engineering path into one place. This review is that navigation pass. The follow-up is the permanent navigation map at [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), authored as a separate documentation-only PR.

The next allowed engineering action is **Plan A live-trial execution by the operations team**, exactly as specified by [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) and [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md). Nothing else is authorized in this wave.

End of v1.
