# Engineering Index

This file is the docs-level business/runtime/contract navigation entry point for every engineering PR.

Root governance files remain the highest authority. `ENGINEERING_CONSTRAINTS_INDEX.md` is the root-level engineering constraint entry and defines how engineering work must be done. This file defines how business, runtime, contract, line, skill, and architecture work must be understood and navigated.

`docs/README.md` is the docs structure and placement entry. Use it before adding, moving, or reclassifying documentation.

Before any future PR slice, use index-first reading:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Then classify the task through this index and read only the minimum
task-specific authority files needed for that task.

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
| Architecture/state baseline | `apolloveo_current_architecture_and_state_baseline.md` |
| Factory four-layer architecture | `docs/architecture/factory_four_layer_architecture_baseline_v1.md` |
| Line contract | `docs/contracts/line_contract.schema.json` |
| Unified glossary | `docs/contracts/veobase01_glossary.md` |
| Four-layer state | `docs/contracts/four_layer_state_contract.md` |
| Contract-driven state baseline | `docs/contracts/contract_driven_four_layer_state_baseline_v1.md` |
| Workbench response | `docs/contracts/workbench_hub_response.contract.md` |
| Runtime assembly rules | `docs/contracts/production_line_runtime_assembly_rules_v1.md` |
| Factory contract-object baseline | `docs/contracts/factory_input_contract_v1.md` |
| Factory line template | `docs/architecture/factory_line_template_design_v1.md` |
| Status ownership | `docs/contracts/status_ownership_matrix.md` |
| Runtime execution log | `docs/execution/VEOBASE01_EXECUTION_LOG.md` |
| VeoBase01 ADR | `docs/adr/ADR-VEOBASE01-LINE-STATE-CONTRACT.md` |
| Docs shared logic review | `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md` |
| Matrix Script design authority | `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` |

## Task-Oriented Reading Map

### Hot Follow Business-Line Changes

Read root governance, `docs/baseline/PROJECT_BASELINE_INDEX.md`,
`ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/status_ownership_matrix.md`,
and the latest active Hot Follow execution note. Business-line changes must
include regression validation for normal translation, helper translation, dub,
compose, and final availability.

### Matrix Script Changes

Read `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` before any Matrix
Script UI, presenter, result-line, delivery-entry, or production-action work.
That index selects the accepted script-to-video mock and result baseline.
Execution logs are evidence only and must not be used as implementation
authority unless they are explicitly named by that index.

Current Matrix Script work must then read the Bucket A authority set selected
by `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`, starting with:

1. `docs/product/matrix_script_product_flow_v2_delta.md`
2. `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
3. `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
4. `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`

Matrix Script P0 is **closed** (async state machine, 2026-06-04). The current
baseline is `docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md`
(#202 artifact-truth + #203 async lifecycle/polling/stale guard). Any future
Matrix Script PR must preserve the result-first layout (A main video, B
material/music, C delivery, D/E folded, diagnostics collapsed) and the
operator-only primary UI.

**Matrix Script P1 / P1-2 / P1-3 established** (operator edit loop + uploaded
material bytes):

- P1 PR-1 (#206) material replacement intent · P1 PR-2 (#207) regenerate V1/V2
  versioning · P1 closure docs (#208).
- P1-2 PR-A (#209) Shot Material Attachment Handle · P1-2 PR-B (#210) regenerate
  records the attached material as `based_on_assets`. `material_bytes_consumed`
  remained **false** because `asset://` bytes were not yet resolvable.
- Matrix Script P1-3 PR-C (#211) Shot Material Upload / Storage Handle —
  uploaded material is resolvable (`msmaterial://`,
  `storage_scope=local_workspace`, `bytes_resolvable=true`).
- P1-3 PR-D (#212) Regenerate Consumes Uploaded Material Bytes — V2 consumes the
  uploaded bytes (image used directly; video first frame when extraction
  succeeds). `material_bytes_consumed=true` only when the renderer actually
  consumed an uploaded file; honest copy otherwise.
- P1-3 closure: `docs/execution/MATRIX_SCRIPT_P1_3_MATERIAL_BYTES_CLOSURE_20260606.md`
  (state note: `docs/execution/MATRIX_SCRIPT_P1_2_STATE_AND_P1_3_FOCUS_20260606.md`).

**Next recommended phase — production browser validation, then P2.** Prove the
end-to-end operator flow in a real browser (upload Shot material → regenerate V2
from uploaded bytes → confirm V2 → delivery follows V2, with honest usage copy
and V1 protection observed live). Provider / quality integration (and any Akool
surface) stays out of scope until the uploaded-material operator loop is
validated in production. `official_publish_ready` stays false.

For Workbench, New Task, Delivery, result-line, or state/projection changes,
also read the four-layer state authorities named in this index. Matrix Script
UI may show L4 operator summary and necessary L3 acceptance facts; it must not
promote L2 raw artifacts, raw manifests, provider fields, or execution-log
temporary reports into the primary operator flow.

### Four-Layer State Changes

Read `docs/contracts/four_layer_state_contract.md`,
`docs/contracts/contract_driven_four_layer_state_baseline_v1.md`,
`docs/contracts/status_ownership_matrix.md`, and
`docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`. Use
`docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md` only as a drafting
template, not as the primary authority. Changes must preserve:

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
`docs/contracts/production_line_runtime_assembly_rules_v1.md`, and
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

### Factory-Level Contract Object Design

Read `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`,
`docs/contracts/factory_input_contract_v1.md`,
`docs/contracts/factory_content_structure_contract_v1.md`,
`docs/contracts/factory_scene_plan_contract_v1.md`,
`docs/contracts/factory_audio_plan_contract_v1.md`,
`docs/contracts/factory_language_plan_contract_v1.md`,
`docs/contracts/factory_delivery_contract_v1.md`, and
`docs/architecture/factory_line_template_design_v1.md`.

Use this path only for contract/design work above the frozen Hot Follow
baseline. It does not authorize new-line runtime onboarding or scenario runtime
implementation.

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

Before any VeoBase01 engineering PR, read indexes first:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Then classify the work through the task-oriented map and read the minimum
task-specific authority files. Do not start every VeoBase01 task by reading the
full reconstruction, state, runtime, baseline, and review set.

Examples:

- execution/refactor work usually adds
  `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md` and
  `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- state/projection work usually adds
  `docs/contracts/four_layer_state_contract.md` and
  `docs/contracts/status_ownership_matrix.md`
- line/runtime assembly work usually adds
  `docs/contracts/production_line_runtime_assembly_rules_v1.md` and
  `docs/architecture/line_contracts/hot_follow_line.yaml`
- ownership-reduction work usually adds
  `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`

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

1. Read root indexes first: `README.md`, then `ENGINEERING_CONSTRAINTS_INDEX.md`.
2. Read docs indexes second: `docs/README.md`, then `docs/ENGINEERING_INDEX.md`.
3. Read `docs/contracts/engineering_reading_contract_v1.md`.
4. Classify the task through the task-oriented map.
5. Read only the minimum task-specific authority files selected from the indexes.
6. Record why the selected authority set was sufficient.
7. Record missing-authority fallback handling, if any.
8. Confirm the branch base requested by the task.
9. Confirm forbidden scope before editing code.
10. Identify required tests and business guardrails before implementation.

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
8. Hot Follow remains frozen as the first contract-driven production-line
   baseline while factory-level contract objects and line-template design are
   lifted above it.
9. A new-line onboarding packet is complete, but remains blocked until a later
   implementation PR explicitly lifts the gate.
