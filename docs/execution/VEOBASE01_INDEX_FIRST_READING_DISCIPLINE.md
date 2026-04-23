# VEOBASE01 Index-First Reading Discipline

Date: 2026-04-23
Branch: `VeoBase01-index-first-reading-discipline`
Base SHA: `2a825cdfd260850ef75700ea84f6315e878bf1a2`

## Purpose

Correct the engineering reading discipline so future VeoBase01 work starts from
indexes, classifies the task, and then reads only the minimum task-specific
authority files selected through those indexes.

## Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`

2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`

3. Minimum task-specific authority files selected from the indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/execution/VEOBASE01_EXECUTION_LOG.md`

4. Sufficiency note:
   - This task changes reading/governance discipline only. It does not change
     runtime behavior, state truth, projection logic, ready-gate behavior, line
     contracts, or ownership boundaries in code. The reading contract was the
     only contract authority needed, and the execution log was needed to record
     the change.

5. Missing-authority handling:
   - none

## Scope

- update `docs/contracts/engineering_reading_contract_v1.md` to make
  index-first routing the active rule
- update root/docs entry points so they no longer imply broad raw authority
  pre-reads
- create this execution note and update the VeoBase01 execution log

## Non-Goals

- no runtime code changes
- no state/projection/ready-gate semantic changes
- no line/runtime assembly changes
- no new-line implementation
- no multi-role harness

## Files Changed

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_INDEX_FIRST_READING_DISCIPLINE.md`

## Validation

- `git diff --check`: passed
- `ls README.md ENGINEERING_CONSTRAINTS_INDEX.md docs/README.md docs/ENGINEERING_INDEX.md docs/contracts/engineering_reading_contract_v1.md docs/execution/VEOBASE01_EXECUTION_LOG.md docs/execution/VEOBASE01_INDEX_FIRST_READING_DISCIPLINE.md docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md docs/contracts/four_layer_state_contract.md docs/contracts/status_ownership_matrix.md docs/contracts/workbench_hub_response.contract.md docs/contracts/hot_follow_ready_gate.yaml docs/contracts/hot_follow_projection_rules_v1.md docs/contracts/production_line_runtime_assembly_rules_v1.md docs/architecture/line_contracts/hot_follow_line.yaml docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md docs/architecture/factory_four_layer_architecture_baseline_v1.md docs/contracts/contract_driven_four_layer_state_baseline_v1.md`: passed

## Risks

- Some historical execution notes still contain the older broad reading style.
  They remain historical evidence and are not active reading rules.

## Rollback Path

- Revert the documentation commit on
  `VeoBase01-index-first-reading-discipline`.

## Acceptance Judgment

Accepted if future engineering notes can follow this declaration shape:

- root indexes first
- docs indexes second
- minimum task-specific authority files selected from the indexes
- sufficiency note
- explicit missing-authority handling
