# Engineering Reading Contract v1

Date: 2026-04-22

## Purpose

This contract freezes index-first mandatory reading as a formal engineering
precondition for state, projection, runtime, contract, and ownership work in
VeoBase01.

No state/projection/runtime change may begin until the root indexes and docs
indexes have been read first, the task has been classified through those
indexes, the minimum task-specific authority files have been selected, and the
execution note for the work records a Reading Declaration.

This contract now points at an index-first routing process. Historical mismatch
notes remain in execution history, but active engineering work must not start
from a long flat authority list.

## Mandatory Reading Order Before Code Changes

### 1. Root Engineering Indexes

1. `README.md`
2. `ENGINEERING_CONSTRAINTS_INDEX.md`

Purpose:

- determine whether the work is allowed now
- determine the current engineering phase
- determine the task class
- determine which docs index should be entered next

### 2. Docs Indexes

1. `docs/README.md`
2. `docs/ENGINEERING_INDEX.md`

Purpose:

- determine whether the task is execution, architecture, contracts, reviews, or
  product/business baseline work
- determine the minimum task-specific authority files needed for the task

### 3. Minimum Task-Specific Authority Files

Only after reading the indexes, read the minimum files selected through the
task-oriented map in `docs/ENGINEERING_INDEX.md`.

Do not start by reading a broad raw list of contracts, baselines, and reviews.
Do not read extra authority files "just in case." If an expected authority file
is missing, record the missing file and choose a fallback path through the
indexes.

## Task-Type Routing Defaults

These defaults guide selection after the indexes have been read. They do not
replace the indexes.

### Execution / Refactor / Implementation

Typical minimum next files:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

### State / Projection / Ready-Gate

Typical minimum next files:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`

Only when required by the indexed task class, add:

- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`

### Line / Runtime Assembly

Typical minimum next files:

- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

### Code De-Powering / Ownership Reduction

Typical minimum next file:

- `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`

### Architecture Baseline

Typical minimum next files:

- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`

## Required Enforcement

- No state/projection/runtime change is allowed before completing index-first
  reading and selecting the minimum task-specific authority files.
- Router, presenter, ready-gate, contract-adapter, and runtime changes all fall
  under this reading requirement.
- If a task changes docs only, this reading contract still applies when the docs
  redefine state, projection, line, or runtime ownership.
- Raw repo familiarity does not replace index-based routing.

## Reading Declaration Requirement

Every engineering execution note must include a `Reading Declaration` section
that records:

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from the indexes.
4. Why those files were sufficient for the task.
5. Missing-authority handling, if any:
   - missing file
   - fallback path selected through the indexes

If a file listed here is later replaced, the replacement must be explicit in
this contract and in the root/docs engineering indexes.

## Conflict Rule

If code conflicts with authority docs:

1. stop
2. document the conflict
3. resolve against contract, baseline, and active review authority before
   changing behavior

Code may not silently win over contracts for state/projection/runtime changes
unless the conflict is first documented and the authority set is updated in the
same slice.

## Canonical Authority Notes

State truth is commonly defined by:

- primary state-layer authority: `docs/contracts/four_layer_state_contract.md`
- ownership/write-path authority: `docs/contracts/status_ownership_matrix.md`
- drafting/fallback template only:
  `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`

Workbench/publish response authority is commonly defined by:

- `docs/contracts/workbench_hub_response.contract.md`

Architecture/state baseline authority is commonly defined by:

- `apolloveo_current_architecture_and_state_baseline.md`

Current phase is commonly defined by:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

Line / runtime / ready-gate ownership is commonly defined by:

- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Why This Exists

VeoBase01 is operating under a frozen sequence:

1. architecture closure
2. code-debt cleanup
3. new-line loading

That sequence fails if engineers begin from local code impressions, stale review
memory, partial contract reading, or different raw document lists. This
contract reduces state/projection drift by making index-first authority routing
an explicit part of execution.
