# VeoBase01 Reading Contract And Hotfix Plan

Date: 2026-04-22
Branch: `VeoBase01-reading-contract-publish-hotfix`
Base branch: `VeoBase01`
Base SHA: `6931530953933cd4720cae804e48f91c9f628449`

## Purpose

Freeze authority-file reading as a formal precondition, then repair the current
Hot Follow publish final-ready regression through the authoritative projection
path rather than another compatibility patch.

## Reading Declaration

Authority files read before any code change:

### Repository Authority

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `PROJECT_RULES.md`
- `ENGINEERING_RULES.md`
- `ENGINEERING_STATUS.md`
- `CURRENT_ENGINEERING_FOCUS.md`

### Docs / Phase Authority

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

### State / Contract / Runtime Authority Read

- requested path missing: `docs/contracts/four_layer_state_contract.md`
- requested path missing: `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- requested path missing: `apolloveo_current_architecture_and_state_baseline.md`

### Review Authority Read

- `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`
- `docs/reviews/VEOBASE01_POST_PR5_GATE_REVIEW.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

Current phase defined by:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

State truth defined by:

- requested path missing: `docs/contracts/four_layer_state_contract.md`
- active fallback used: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/status_ownership_matrix.md`

Line / runtime / ready-gate ownership defined by:

- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Authority Conflict Record

Missing authority paths in this workspace:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

Action for this slice:

- freeze the conflict in `docs/contracts/engineering_reading_contract_v1.md`
- do not silently invent replacement authority
- use the active fallback sources listed above and record them in each execution
  note

## Planned Sequence

1. Stage 0: create and wire the reading contract
2. Stage 1: identify the stale publish-side derivation path and replace it with
   authoritative projection consumption
3. Stage 1: add regression coverage for final-ready contradiction classes
4. Stage 2: write Hot Follow flow/state/projection contract drafts after the
   hotfix root cause and fix are clear

## Scope

- reading-contract freeze and entry wiring
- publish final-ready regression diagnosis and narrow projection-safe fix
- regression tests for publish/workbench alignment
- flow/state/projection design documents

## Non-Goals

- no new-line implementation
- no multi-role harness
- no Hot Follow business behavior change
- no translation, helper translation, subtitle-save, dub, compose, ffmpeg, or
  worker runtime redesign
- no API contract redesign unless a hidden internal adapter must change to stop
  stale projection drift

## Risks

- stale publish compatibility paths may be split across router, service, and
  contract-adapter layers
- current index docs still point at missing authority files, which can create
  future drift if not made explicit

## Rollback Path

- revert this branch to base SHA `6931530953933cd4720cae804e48f91c9f628449`
- discard the reading contract wiring if Stage 1 root cause does not justify a
  code change

## Acceptance Judgment

Stage 0 is accepted when:

- `docs/contracts/engineering_reading_contract_v1.md` exists
- the required entry points refer to it
- this execution note records the Reading Declaration
- no Stage 1 code edit starts before Stage 0 is written
