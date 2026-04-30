# ApolloVeo 2.0 P2 Gate Checklist v1

Date: 2026-04-25
Status: P2 pre-execution gate checklist

## Gate Status Legend

- Pass: concrete artifact exists and can be cited as current authority.
- Partial: rules or references exist, but a P2-specific artifact or signoff is missing.
- Missing: required artifact does not exist.
- Blocked: implementation must not start.

## Gate Checklist

| Gate | Required artifact | Current status | Blocking for P2 implementation | Evidence |
| --- | --- | --- | --- | --- |
| Authority gate | unified authority map | Pass after this review | No if kept current | `docs/reviews/APOLLOVEO_2_0_P2_READINESS_UNIFIED_REVIEW.md` |
| Execution-base gate | P2 pre-execution base | Pass after this doc | No if signed off | `docs/execution/apolloveo_2_0_p2_execution_base_v1.md` |
| Role gate | multi-role matrix | Pass after this doc | No if accepted by review owner | `docs/execution/apolloveo_2_0_role_matrix_v1.md` |
| Evidence gate | evidence index | Pass after this doc | No if kept current | `docs/execution/apolloveo_2_0_evidence_index_v1.md` |
| Business-flow gate | top-level factory flow diagram | Pass after this doc | No if accepted as shared baseline | `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` |
| Packet gate | factory packet envelope + validator rules + line packet schema/sample | Partial | Yes | envelope/rules + validator skeleton + onboarding gate + Hot Follow green evidence (`docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`); Matrix Script / Digital Anchor `schemas/packets/<line>/packet.schema.json` + sample still missing |
| Surface gate | versioned intake/planning/delivery response contracts | Partial | Yes for implementation | workbench contract and design handoff exist; factory-wide surface contracts missing |
| Donor gate | donor boundary + capability mapping + adapter-base precondition | Partial | Yes for donor-based implementation | boundary/mapping/ADR exist; capability adapter base and donor absorption signoff missing |
| Runtime gate | router/service implementation plan after packet/surface gates | Blocked | Yes | current gate forbids runtime work |
| Hot Follow reference gate | Hot Follow remains frozen reference line | Pass | No if not reopened | `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md` |

## Must Pass Before P2 Implementation

1. Packet gate: deliver target line packet schema and sample instance using the frozen envelope.
2. Packet validator gate: run or produce a validator report against the frozen R1-R5 / E1-E5 rules.
3. Surface gate: define versioned response contracts for intake, planning/workbench, delivery/publish.
4. Donor gate: complete capability adapter base before any absorption PR and confirm no donor code absorption in planning pass.
5. Reviewer gate: Review / Merge Owner signs off that P2 implementation can start.

## Must Remain Blocked

- new route stack
- new production line runtime
- donor code copy or direct import
- UI implementation
- runtime packet validator
- runtime response rewiring
- Hot Follow behavior change
- OpenClaw runtime integration

## Gate Owner Expectations

| Gate | Owner |
| --- | --- |
| Authority / execution base | Architect + Reviewer |
| Packet | Product + Architect |
| Surface | Designer + Backend/Platform |
| Donor | Architect + Reviewer |
| Runtime entry | Backend/Platform + Reviewer |
| Merge readiness | Reviewer / Merge Owner |

## Review Rule

If any Must gate is Partial, Missing, or Blocked, P2 implementation must not start. Planning artifacts may continue only if they do not change runtime behavior.
