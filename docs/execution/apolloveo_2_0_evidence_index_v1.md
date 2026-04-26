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
| skills/worker/planning ADR | `docs/adr/ADR-phase2-skills-worker-planning.md` |
| task router decomposition ADR | `docs/adr/ADR-task-router-decomposition.md` |

## Current Known Evidence Gaps

| Gap | Effect |
| --- | --- |
| Matrix Script / Digital Anchor packet schema and sample instances missing | packet gate cannot pass for P2 implementation (validation entry path exists; awaiting product handoff at `schemas/packets/<line>/`) |
| packet validator runtime/report missing | RESOLVED for Hot Follow reference (`docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`); still pending for new lines |
| capability adapter base missing | RESOLVED at base wave (`gateway/app/services/capability/adapters/base.py`); W1 (Media helpers M-01..M-05) now Absorbed; W2 (ASR/translate/TTS) requires prerequisites in `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3 |
| factory-wide versioned surface response contracts missing | surface gate remains partial |
| some indexed future authority files do not exist | must be resolved before they are used as P2 evidence |

## Use Rule

When a P2-adjacent task cites evidence, it should cite the original evidence file and this index. This index helps navigation; it does not override the source document.
