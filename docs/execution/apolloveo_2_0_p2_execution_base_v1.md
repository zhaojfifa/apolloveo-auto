# ApolloVeo 2.0 P2 Execution Base v1

Date: 2026-04-25
Status: Pre-execution base; does not authorize P2 implementation

## Purpose

本文件冻结 ApolloVeo 2.0 进入 P2 之前的统一执行基座。

它只允许 review、planning、gate、contract-envelope 级工作；不允许启动 P2 runtime implementation。

## Scope

Allowed before P2:

- authority unification review
- P2 gate checklist maintenance
- role matrix / handoff baseline
- top-level business flow diagram
- factory packet envelope / validator rules consumption
- donor capability mapping review
- surface response contract drafting
- evidence index maintenance

Forbidden before gates pass:

- runtime code changes
- router/service refactor
- donor code absorption
- UI implementation
- packet validator runtime implementation
- new production line onboarding
- OpenClaw integration
- Hot Follow feature-fix or behavior retune

## Reading Declaration

P2 pre-execution work must start with:

1. `README.md`
2. `ENGINEERING_CONSTRAINTS_INDEX.md`
3. `CURRENT_ENGINEERING_FOCUS.md`
4. `ENGINEERING_STATUS.md`
5. `docs/README.md`
6. `docs/ENGINEERING_INDEX.md`
7. `docs/contracts/engineering_reading_contract_v1.md`
8. `docs/baseline/PROJECT_BASELINE_INDEX.md`

Then read the P2-specific authority set:

1. `docs/reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md`
2. `docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md`
3. `docs/execution/apolloveo_2_0_role_matrix_v1.md`
4. `docs/execution/apolloveo_2_0_evidence_index_v1.md`
5. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`

## P2 Base Authority Set

| Area | Authority |
| --- | --- |
| Current gate | `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` |
| Factory layer model | `docs/architecture/factory_four_layer_architecture_baseline_v1.md` |
| v1.1 master plan | `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` |
| Runtime boundary | `docs/architecture/factory_runtime_boundary_design_v1.md` |
| Line template | `docs/architecture/factory_line_template_design_v1.md` |
| Workbench mapping | `docs/architecture/factory_workbench_mapping_v1.md` |
| Runtime assembly rules | `docs/contracts/production_line_runtime_assembly_rules_v1.md` |
| Workbench response truth | `docs/contracts/workbench_hub_response.contract.md` |
| State ownership | `docs/contracts/status_ownership_matrix.md` |
| Factory contracts | `docs/contracts/factory_*_contract_v1.md` |
| Packet envelope / validator | `docs/contracts/factory_packet_envelope_contract_v1.md`, `docs/contracts/factory_packet_validator_rules_v1.md` |
| Donor boundary | `docs/donor/swiftcraft_donor_boundary_v1.md`, `docs/donor/swiftcraft_capability_mapping_v1.md`, `docs/adr/ADR-donor-swiftcraft-capability-only.md` |
| Product / design handoff | `docs/handoffs/apolloveo_2_0_product_handoff_v1.md`, `docs/handoffs/apolloveo_2_0_design_handoff_v1.md` |
| Reference line flow | `docs/architecture/hot_follow_business_flow_v1.md` |
| Factory flow | `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` |

## P2 Preconditions

P2 implementation remains blocked until all Must gates in
`docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md` are signed off.

Minimum required preconditions:

1. packet envelope is specified
2. packet validator rules are specified
3. line packet schema + sample instance are delivered for the target line
4. surface response ownership is specified
5. donor boundary is signed off as capability donor only
6. capability adapter base is defined before any donor adapter absorption
7. role owners and handoffs are explicit
8. top-level business flow is accepted as role-readable baseline
9. Hot Follow remains frozen as reference line

## Execution Rules

- Every P2-adjacent artifact must state whether it is authority, checklist, reference, or historical evidence.
- No execution doc may convert donor code into implementation scope.
- No diagram may imply a new runtime route, UI, or service exists.
- No role may treat L4 surface wording as L2/L3 truth.
- Product planning may define business intent, but must not bypass packet/surface/donor gates.
- Backend/platform planning may define boundaries, but must not start implementation until reviewer gate passes.

## Exit Criteria

This execution base is ready for P2 planning when:

- the unified review exists
- the gate checklist exists
- the role matrix exists
- the evidence index exists
- the top-level business flow exists
- all documents point back to active authority rather than inventing new truth sources

This execution base does not by itself make the repo ready for P2 implementation.
