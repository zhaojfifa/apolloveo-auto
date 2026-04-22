# Engineering Index

This file is the docs-level business/runtime/contract navigation entry point for every engineering PR.

Root governance files remain the highest authority. `ENGINEERING_CONSTRAINTS_INDEX.md` is the root-level engineering constraint entry and defines how engineering work must be done. This file defines how business, runtime, contract, line, skill, and architecture work must be understood and navigated.

`docs/README.md` is the docs structure and placement entry. Use it before adding, moving, or reclassifying documentation.

Before any future PR slice, read both:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`

## Document Priority

Read and apply documents in this order:

1. Root governance: `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`.
2. Root engineering constraints: `ENGINEERING_CONSTRAINTS_INDEX.md`.
3. Baseline and gate docs: `docs/baseline/PROJECT_BASELINE_INDEX.md`, active verification and recovery gate notes.
4. Contracts: `docs/contracts/*`.
5. Architecture docs: `docs/architecture/*`.
6. ADRs: `docs/adr/*`.
7. Execution logs: `docs/execution/*`.
8. Reviews: active review docs only when they are named by the task.
9. Archive: `docs/archive/*` for historical context only.

When documents conflict, the higher priority document wins. Lower priority docs
may explain history, but they do not override governance, baselines, contracts,
or active architecture decisions.

## Authoritative Files By Concern

| Concern | Authoritative Entry |
| --- | --- |
| Engineering rules | `ENGINEERING_RULES.md` |
| Engineering constraints | `ENGINEERING_CONSTRAINTS_INDEX.md` |
| Docs placement | `docs/README.md` |
| Current focus | `CURRENT_ENGINEERING_FOCUS.md` |
| Project baseline | `docs/baseline/PROJECT_BASELINE_INDEX.md` |
| VeoBase01 reconstruction | `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md` |
| Line contract | `docs/contracts/line_contract.schema.json` |
| Unified glossary | `docs/contracts/veobase01_glossary.md` |
| Four-layer state | `docs/contracts/four_layer_state_contract.md` |
| Workbench response | `docs/contracts/workbench_hub_response.contract.md` |
| Status ownership | `docs/contracts/status_ownership_matrix.md` |
| Runtime execution log | `docs/execution/VEOBASE01_EXECUTION_LOG.md` |
| VeoBase01 ADR | `docs/adr/ADR-VEOBASE01-LINE-STATE-CONTRACT.md` |
| Docs shared logic review | `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md` |

## Task-Oriented Reading Map

### Hot Follow Business-Line Changes

Read root governance, `docs/baseline/PROJECT_BASELINE_INDEX.md`,
`ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/status_ownership_matrix.md`,
and the latest active Hot Follow execution note. Business-line changes must
include regression validation for normal translation, helper translation, dub,
compose, and final availability.

### Four-Layer State Changes

Read `docs/contracts/four_layer_state_contract.md`,
`docs/contracts/status_ownership_matrix.md`, and
`docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`. Changes must preserve:

- L1 as step execution status only.
- L2 as artifact facts only.
- L3 as current attempt/runtime resolution only.
- L4 as ready gate, operator summary, advisory, and presentation only.

### Workbench/Presenter Changes

Read `docs/contracts/workbench_hub_response.contract.md`,
`docs/contracts/four_layer_state_contract.md`, and
`docs/contracts/status_ownership_matrix.md`. Presenter and advisory code must
consume L2/L3 outputs and must not redefine artifact truth or attempt truth.

### Router/Service Ownership Changes

Read this index, `ENGINEERING_CONSTRAINTS_INDEX.md`,
`docs/contracts/status_ownership_matrix.md`, and
`docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`. Routers may validate
HTTP inputs, call services, and shape HTTP responses. Services own reusable
state, view, policy, and artifact-fact evaluation. Router extraction must not
change wire response shape unless the PR explicitly declares and validates it.

### Line/Skill/Worker/Deliverable Contract Changes

Read `docs/contracts/line_contract.schema.json`,
`docs/adr/ADR-VEOBASE01-LINE-STATE-CONTRACT.md`, and
`docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`. Skills are advisory
readers, workers are execution resources, deliverable profiles declare accepted
outputs, and asset sinks are downstream of accepted deliverable truth.

### New-Line Onboarding Preparation

Read all VeoBase01 reconstruction entry docs listed below. New-line work cannot
start until the new-line gate in this file is satisfied.

Required preparation docs:

- `docs/contracts/veobase01_glossary.md`
- `docs/contracts/new_line_onboarding_template.md`
- `docs/contracts/line_job_state_machine.md`
- `docs/contracts/skills_bundle_boundary.md`
- example schemas under `docs/contracts/*.example.yaml`

## VeoBase01 Reconstruction Entry

Before any VeoBase01 engineering PR, read:

- Root governance: `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/line_contract.schema.json`
- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- Active review gate docs named by the task, including current Hot Follow recovery or alignment notes when applicable

## Forbidden Doc Misuse

- Review docs are not runtime contracts.
- Execution logs are not permanent architecture rules.
- Archive docs are not active implementation sources.
- Presenter code may not redefine business truth.
- Skills may not become truth-write owners.
- ADRs record decisions; they do not grant scope beyond the active PR mission.
- Future-state docs cannot justify code that bypasses current contracts.

## PR Pre-Read Checklist

Before starting an engineering PR:

1. Read root governance.
2. Read `ENGINEERING_CONSTRAINTS_INDEX.md`.
3. Read `docs/README.md` when adding, moving, or classifying docs.
4. Read this docs-level engineering index.
5. Read the baseline/gate docs for the task.
6. Read the relevant contracts and architecture docs from the task-oriented map.
7. Confirm the branch base requested by the task.
8. Confirm forbidden scope before editing code.
9. Identify required tests and business guardrails before implementation.

## PR Write-Back Checklist

Before closing an engineering PR:

1. Update contracts if behavior or ownership boundaries changed.
2. Update architecture docs if a boundary or runtime path changed.
3. Update execution logs with branch, scope, files changed, tests, and validation evidence.
4. Record whether wire response shape changed.
5. Record whether business runtime behavior changed.
6. Record follow-up scope without starting unrelated work.

## New-Line Gate

A new production line may not be implemented until these gates pass:

1. Four-layer state contract is frozen.
2. Workbench response contract is frozen.
3. Line contract is explicit and consumed in runtime.
4. Skills boundary is frozen.
5. Worker, deliverable, and asset sink profiles are explicit.
6. Business regression validation has passed for the existing Hot Follow line.
7. Router/service ownership boundaries are stable enough that the new line does
   not copy router orchestration drift.
8. A new-line onboarding packet is complete, but remains blocked until a later
   implementation PR explicitly lifts the gate.
