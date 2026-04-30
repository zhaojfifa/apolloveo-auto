# ApolloVeo 2.0 Role Matrix v1

Date: 2026-04-25
Status: P2 pre-execution collaboration baseline

## Purpose

本矩阵定义 P2 前多角色协作基线。它不创建新组织结构，也不授权实现；它只明确每个角色如何读取 authority、产出什么 artifact、在哪里 handoff。

## Role Matrix

| Role | Owns | Must not own | Required P2-before evidence | Handoff to |
| --- | --- | --- | --- | --- |
| Product | factory business goal、line/goal selection、contract-object product intent、delivery expectations、line packet schema draft | runtime truth、ready-gate rule implementation、donor code import | product handoff deliverables and top-level business flow accepted | Architect, Designer |
| Architect | authority layering、factory packet shape、boundary model、gate definitions、truth ownership、donor gate | UI behavior implementation、provider-specific runtime branch | v1.1 master plan, packet envelope/rules, gate checklist signoff path | Backend/Platform, Reviewer |
| Designer | role-readable workbench flow、intake/planning/review/delivery surface model、handoff clarity、five-surface IA | source-of-truth rules、status policy、delivery truth | design handoff deliverables tied to factory flow and workbench mapping | Product, Backend/Platform |
| Backend/Platform | service boundary plan、packet validator design、surface response contract plan、capability/worker boundary plan、adapter base | product shell decisions、donor UI absorption、runtime change before gates | backend planning note references gate checklist; no code started | Implementer, Reviewer |
| Implementer | scoped implementation after gates pass、tests、behavior declaration | changing authority during implementation、starting P2 before signoff | no implementation until Reviewer confirms gates | Reviewer / Merge Owner |
| Reviewer / Merge Owner | gate enforcement、scope control、evidence validation、merge readiness | product intent invention、silent scope widening | gate checklist completed; evidence index current | All roles |

## Stage Handoffs

| Stage | Primary role | Supporting roles | Handoff artifact |
| --- | --- | --- | --- |
| line / goal selection | Product | Architect | packet product-intent section |
| content structure | Product | Architect, Designer | content structure contract mapping |
| scene plan | Product | Designer, Backend/Platform | scene plan contract mapping |
| audio plan | Product | Backend/Platform | audio plan contract mapping |
| language plan | Product | Backend/Platform | language plan contract mapping |
| generation boundary | Backend/Platform | Architect, Implementer | worker/capability boundary plan |
| quality check | Reviewer | Product, Designer, Backend/Platform | ready-gate and surface checklist |
| delivery / publish / archive | Product | Backend/Platform, Reviewer | delivery contract and publish-state evidence |

## Collaboration Rules

- Product defines what the factory should produce, not how runtime truth is written.
- Architect decides where rules live before Backend/Platform designs implementation.
- Designer may shape the workbench flow only from contract and projection truth.
- Backend/Platform may design validators and response contracts, but cannot implement them before P2 gates pass.
- Implementer starts only after Reviewer / Merge Owner confirms the gate checklist.
- Reviewer / Merge Owner blocks any PR that absorbs donor code, changes runtime behavior, or reopens Hot Follow outside an explicit accepted scope.

## Required Shared Reference

All roles must use `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` as the common top-level flow reference.

Hot Follow is used as reference evidence through `docs/architecture/hot_follow_business_flow_v1.md`; it is not a P2 feature-fix target.
