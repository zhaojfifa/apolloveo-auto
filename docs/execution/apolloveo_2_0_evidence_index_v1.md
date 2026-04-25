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
| packet validator implementation | `gateway/app/services/packet/validator.py` |
| packet envelope dataclasses | `gateway/app/services/packet/envelope.py` |
| Matrix Script packet schema | `schemas/packets/matrix_script/packet.schema.json` |
| Matrix Script packet sample | `schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json` |
| Digital Anchor packet schema | `schemas/packets/digital_anchor/packet.schema.json` |
| Digital Anchor packet sample | `schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json` |
| Matrix Script validator report (green) | `docs/execution/logs/packet_validator_matrix_script_v1.json` |
| Digital Anchor validator report (green) | `docs/execution/logs/packet_validator_digital_anchor_v1.json` |
| packet validator pytest gate (6/6 green, 2026-04-26) | `tests/contracts/packet_validator/test_pm_samples.py` |

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

## Donor / Capability Mapping Evidence

| Concern | Evidence |
| --- | --- |
| Jellyfish donor importability | `docs/reviews/review_jellyfish_importability_for_factory.md` |
| SwiftCraft donor boundary | `docs/donor/swiftcraft_donor_boundary_v1.md` |
| SwiftCraft capability mapping | `docs/donor/swiftcraft_capability_mapping_v1.md` |
| SwiftCraft capability-only ADR | `docs/adr/ADR-donor-swiftcraft-capability-only.md` |
| skills/worker/planning ADR | `docs/adr/ADR-phase2-skills-worker-planning.md` |
| task router decomposition ADR | `docs/adr/ADR-task-router-decomposition.md` |

## Current Known Evidence Gaps

| Gap | Effect |
| --- | --- |
| Matrix Script / Digital Anchor packet schema and sample instances missing | RESOLVED 2026-04-26 — schemas + samples shipped, validator pytest green |
| packet validator runtime/report missing | RESOLVED 2026-04-26 — `gateway/app/services/packet/validator.py` + reports under `docs/execution/logs/packet_validator_*_v1.json` |
| capability adapter base missing | donor absorption remains blocked even though boundary/mapping docs exist |
| factory-wide versioned surface response contracts missing | surface gate remains partial |
| some indexed future authority files do not exist | must be resolved before they are used as P2 evidence |

## Use Rule

When a P2-adjacent task cites evidence, it should cite the original evidence file and this index. This index helps navigation; it does not override the source document.
