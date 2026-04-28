# ApolloVeo 2.0 P2 Evidence Index v1

Date: 2026-04-25
Status: P2 pre-execution evidence index

## Purpose

本文件把 P2-readiness review 依赖的证据聚合到一个入口。它不是新的 truth source；每条证据仍以原文件为准。

## Authority Evidence

| Concern | Evidence |
| --- | --- |
| root scope | `README.md` |
| engineering constraints | `ENGINEERING_CONSTRAINTS_INDEX.md` |
| current focus | `CURRENT_ENGINEERING_FOCUS.md` |
| current stage/status | `ENGINEERING_STATUS.md` |
| docs placement | `docs/README.md` |
| engineering reading map | `docs/ENGINEERING_INDEX.md` |
| reading discipline | `docs/contracts/engineering_reading_contract_v1.md` |
| project baseline | `docs/baseline/PROJECT_BASELINE_INDEX.md` |
| v1.1 master plan | `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` |

## Gate Evidence

| Concern | Evidence |
| --- | --- |
| active factory alignment gate | `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` |
| factory alignment summary | `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md` |
| P2 unified review | `docs/reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md` |
| P2 execution base | `docs/execution/apolloveo_2_0_p2_execution_base_v1.md` |
| P2 gate checklist | `docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md` |
| P2 pre-unlock wave log | `docs/execution/apolloveo_2_0_p2_pre_unlock_wave_v1.md` |
| product handoff | `docs/handoffs/apolloveo_2_0_product_handoff_v1.md` |
| design handoff | `docs/handoffs/apolloveo_2_0_design_handoff_v1.md` |

## Factory Contract Evidence

| Contract object | Evidence |
| --- | --- |
| input contract | `docs/contracts/factory_input_contract_v1.md` |
| content structure contract | `docs/contracts/factory_content_structure_contract_v1.md` |
| scene plan contract | `docs/contracts/factory_scene_plan_contract_v1.md` |
| audio plan contract | `docs/contracts/factory_audio_plan_contract_v1.md` |
| language plan contract | `docs/contracts/factory_language_plan_contract_v1.md` |
| delivery contract | `docs/contracts/factory_delivery_contract_v1.md` |
| runtime assembly | `docs/contracts/production_line_runtime_assembly_rules_v1.md` |
| packet envelope | `docs/contracts/factory_packet_envelope_contract_v1.md` |
| packet validator rules | `docs/contracts/factory_packet_validator_rules_v1.md` |

## Architecture / Flow Evidence

| Concern | Evidence |
| --- | --- |
| factory four-layer baseline | `docs/architecture/factory_four_layer_architecture_baseline_v1.md` |
| line template | `docs/architecture/factory_line_template_design_v1.md` |
| runtime boundaries | `docs/architecture/factory_runtime_boundary_design_v1.md` |
| workbench mapping | `docs/architecture/factory_workbench_mapping_v1.md` |
| top-level ApolloVeo 2.0 flow | `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` |
| Hot Follow business flow | `docs/architecture/hot_follow_business_flow_v1.md` |

## Hot Follow Reference-Line Evidence

| Concern | Evidence |
| --- | --- |
| freeze judgment | `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md` |
| ready gate | `docs/contracts/hot_follow_ready_gate.yaml` |
| projection rules | `docs/contracts/hot_follow_projection_rules_v1.md` |
| state machine | `docs/contracts/hot_follow_state_machine_contract_v1.md` |
| line contract | `docs/contracts/hot_follow_line_contract.md` |
| YAML line binding | `docs/architecture/line_contracts/hot_follow_line.yaml` |
| reference packet instance | `schemas/packets/hot_follow/sample/reference_packet_v1.json` |
| reference validator + onboarding gate green evidence | `docs/execution/evidence/hot_follow_reference_packet_validation_v1.md` |

## Packet Onboarding Evidence

| Concern | Evidence |
| --- | --- |
| packet validator skeleton | `gateway/app/services/packet/validator.py` |
| envelope shapes | `gateway/app/services/packet/envelope.py` |
| onboarding gate skeleton | `gateway/app/services/packet/onboarding_gate.py` |
| validation entry helpers | `gateway/app/services/packet/entry.py` |
| packet sample scaffolding | `schemas/packets/README.md` |
| validator + onboarding gate tests | `tests/contracts/packet_validator/` |

## Donor / Capability Mapping Evidence

| Concern | Evidence |
| --- | --- |
| Jellyfish donor importability | `docs/reviews/review_jellyfish_importability_for_factory.md` |
| SwiftCraft donor boundary | `docs/donor/swiftcraft_donor_boundary_v1.md` |
| SwiftCraft capability mapping | `docs/donor/swiftcraft_capability_mapping_v1.md` |
| SwiftCraft capability-only ADR | `docs/adr/ADR-donor-swiftcraft-capability-only.md` |
| W1 absorption evidence (M-04/M-05) | `docs/execution/evidence/donor_absorption_w1_m04_m05_v1.md` |
| W1 absorption evidence (M-01/M-02/M-03) | `docs/execution/evidence/donor_absorption_w1_m01_m02_m03_v1.md` |
| W1 completion review | `docs/reviews/W1_COMPLETION_REVIEW_v1.md` |
| W2 admission Phase A — guardrail foundation | `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md` |
| W2 guardrail host (tests) | `tests/guardrails/` |
| W2 admission Phase B — env / secret matrix | `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md` |
| W2 env matrix (O-01) | `ops/env/env_matrix_v1.md` |
| W2 storage layout (O-02) | `ops/env/storage_layout_v1.md` |
| W2 secret loading baseline | `ops/env/secret_loading_baseline_v1.md` |
| W2 admission Phase C — donor / lifecycle freeze | `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md` |
| W2 admission Phase C — AdapterBase lifecycle review | `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` |
| W2 admission Phase D — Hot Follow regression baseline freeze | `docs/execution/evidence/w2_admission_phase_d_hot_follow_regression_freeze_v1.md` |
| W2 admission Phase E — admission signoff | `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` |
| W2.1 base-only adapter preparation — execution log | `docs/execution/W2_1_BASE_ONLY_ADAPTER_PREPARATION_LOG.md` |
| W2.1 first provider absorption — execution log | `docs/execution/W2_1_FIRST_PROVIDER_ABSORPTION_LOG.md` |
| W2.1 base-only adapter preparation — B3 error envelope | `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md` |
| W2.1 base-only adapter preparation — B1 auth/credential surface | `docs/execution/evidence/w2_1_b1_adapter_credential_surface_v1.md` |
| W2.1 base-only adapter preparation — B2 retry/timeout/cancellation | `docs/execution/evidence/w2_1_b2_adapter_execution_context_v1.md` |
| W2.1 base-only adapter preparation — B4 construction-vs-invocation lifecycle | `docs/execution/evidence/w2_1_b4_adapter_lifecycle_boundary_v1.md` |
| W2.1 first provider absorption — UnderstandingAdapter ← Gemini text translate (A-03) | `docs/execution/evidence/w2_1_first_provider_absorption_understanding_gemini_v1.md` |
| Matrix Script First Production Line Wave — execution log | `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` |
| Matrix Script First Production Line — Phase A (Task Entry) — contract | `docs/contracts/matrix_script/task_entry_contract_v1.md` |
| Matrix Script First Production Line — Phase A (Task Entry) — evidence | `docs/execution/evidence/matrix_script_phase_a_task_entry_v1.md` |
| Matrix Script First Production Line — Phase A (Task Entry) — tests | `tests/contracts/matrix_script/test_task_entry_phase_a.py` |
| Matrix Script First Production Line — Phase B (Workbench Variation Surface) — contract | `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md` |
| Matrix Script First Production Line — Phase B (Workbench Variation Surface) — evidence | `docs/execution/evidence/matrix_script_phase_b_workbench_variation_surface_v1.md` |
| Matrix Script First Production Line — Phase B (Workbench Variation Surface) — tests | `tests/contracts/matrix_script/test_workbench_variation_phase_b.py` |
| Matrix Script First Production Line — Phase C (Delivery Binding) — contract | `docs/contracts/matrix_script/delivery_binding_contract_v1.md` |
| Matrix Script First Production Line — Phase C (Delivery Binding) — evidence | `docs/execution/evidence/matrix_script_phase_c_delivery_binding_v1.md` |
| Matrix Script First Production Line — Phase C (Delivery Binding) — tests | `tests/contracts/matrix_script/test_delivery_binding_phase_c.py` |
| Matrix Script First Production Line — Phase D.0 (Publish Feedback Closure Contract Freeze) — contract | `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md` |
| Matrix Script First Production Line — Phase D.0 (Publish Feedback Closure Contract Freeze) — evidence | `docs/execution/evidence/matrix_script_phase_d_publish_feedback_closure_contract_v1.md` |
| Matrix Script First Production Line — Phase D.1 (Publish Feedback Closure Write-Back) — evidence | `docs/execution/evidence/matrix_script_phase_d1_publish_feedback_closure_writeback_v1.md` |
| Matrix Script First Production Line — Phase D.1 (Publish Feedback Closure Write-Back) — tests | `tests/contracts/matrix_script/test_publish_feedback_closure_phase_d1.py` |
| Digital Anchor Second Production Line Wave — execution log | `docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md` |
| Digital Anchor Second Production Line — Phase A (Task / Role Entry) — contract | `docs/contracts/digital_anchor/task_entry_contract_v1.md` |
| Digital Anchor Second Production Line — Phase A (Task / Role Entry) — evidence | `docs/execution/evidence/digital_anchor_phase_a_task_entry_v1.md` |
| Digital Anchor Second Production Line — Phase A (Task / Role Entry) — tests | `tests/contracts/digital_anchor/test_task_entry_phase_a.py` |
| Digital Anchor Second Production Line — Phase B (Workbench Role / Speaker Surface) — contract | `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md` |
| Digital Anchor Second Production Line — Phase B (Workbench Role / Speaker Surface) — evidence | `docs/execution/evidence/digital_anchor_phase_b_workbench_role_speaker_surface_v1.md` |
| Digital Anchor Second Production Line — Phase B (Workbench Role / Speaker Surface) — tests | `tests/contracts/digital_anchor/test_workbench_role_speaker_phase_b.py` |
| skills/worker/planning ADR | `docs/adr/ADR-phase2-skills-worker-planning.md` |
| task router decomposition ADR | `docs/adr/ADR-task-router-decomposition.md` |

## Current Known Evidence Gaps

| Gap | Effect |
| --- | --- |
| Matrix Script / Digital Anchor packet schema and sample instances missing | packet gate cannot pass for P2 implementation (validation entry path exists; awaiting product handoff at `schemas/packets/<line>/`) |
| packet validator runtime/report missing | RESOLVED for Hot Follow reference (`docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`); still pending for new lines |
| capability adapter base missing | RESOLVED at base wave (`gateway/app/services/capability/adapters/base.py`); W1 (Media helpers M-01..M-05) now Absorbed; W2 admission Phases A–E are closed and indexed (`docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`, `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md`, `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md`, `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`, `docs/execution/evidence/w2_admission_phase_d_hot_follow_regression_freeze_v1.md`, `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md`). Phase E admission = PASS; W2.1 implementation remains BLOCKED on four base-only AdapterBase gap-closing PRs (auth/credential [B1 implementation green 2026-04-27 — see `docs/execution/evidence/w2_1_b1_adapter_credential_surface_v1.md`, awaiting architect+reviewer signoff], retry/timeout/cancellation [B2 implementation green 2026-04-27 — see `docs/execution/evidence/w2_1_b2_adapter_execution_context_v1.md`, awaiting architect+reviewer signoff], error envelope [B3 implementation green 2026-04-27 — see `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md`, awaiting architect+reviewer signoff], construction-vs-invocation [B4 implementation green 2026-04-27 — see `docs/execution/evidence/w2_1_b4_adapter_lifecycle_boundary_v1.md`, awaiting architect+reviewer signoff]) per `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §5 and `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2; W2.2 remains BLOCKED on the Hot Follow known-red/W2.2 prerequisites in `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.3; W2.3 is NOT EVALUATED. |
| factory-wide versioned surface response contracts missing | surface gate remains partial |
| some indexed future authority files do not exist | must be resolved before they are used as P2 evidence |

## Use Rule

When a P2-adjacent task cites evidence, it should cite the original evidence file and this index. This index helps navigation; it does not override the source document.
