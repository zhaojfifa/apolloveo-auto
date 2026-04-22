# Engineering Reading Contract v1

Date: 2026-04-22

## Purpose

This contract freezes mandatory reading as a formal engineering precondition for
state, projection, runtime, and contract work in VeoBase01.

No state/projection/runtime change may begin until the required authority set
has been read in order and the execution note for the work records a Reading
Declaration.

## Mandatory Reading Order Before Code Changes

### 1. Repository Authority

1. `README.md`
2. `ENGINEERING_CONSTRAINTS_INDEX.md`
3. `PROJECT_RULES.md`
4. `ENGINEERING_RULES.md`
5. `ENGINEERING_STATUS.md`
6. `CURRENT_ENGINEERING_FOCUS.md`

### 2. Docs / Phase Authority

1. `docs/README.md`
2. `docs/ENGINEERING_INDEX.md`
3. `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
4. `docs/execution/VEOBASE01_EXECUTION_LOG.md`
5. `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

### 3. State / Contract / Runtime Authority

1. `docs/contracts/four_layer_state_contract.md`
2. `docs/contracts/workbench_hub_response.contract.md`
3. `docs/contracts/hot_follow_line_contract.md`
4. `docs/contracts/skills_runtime_contract.md`
5. `docs/contracts/status_ownership_matrix.md`
6. `docs/contracts/worker_gateway_runtime_contract.md`
7. `docs/contracts/hot_follow_ready_gate.yaml`
8. `docs/architecture/line_contracts/hot_follow_line.yaml`
9. `apolloveo_current_architecture_and_state_baseline.md`

## Required Enforcement

- No state/projection/runtime change is allowed before reading the authority
  set above.
- Router, presenter, ready-gate, contract-adapter, and runtime changes all fall
  under this reading requirement.
- If a task changes docs only, this reading contract still applies when the docs
  redefine state, projection, line, or runtime ownership.

## Reading Declaration Requirement

Every engineering execution note must include a `Reading Declaration` section
that records:

- which authority files were read
- which file defined the current phase
- which file defined state truth
- which file defined line/runtime/ready-gate ownership
- any authority-path mismatch discovered during the read

## Conflict Rule

If code conflicts with authority docs:

1. stop
2. document the conflict
3. resolve against contract, baseline, and active review authority before
   changing behavior

Code may not silently win over contracts for state/projection/runtime changes
unless the conflict is first documented and the authority set is updated in the
same slice.

## Current Workspace Conflict Record

The following authority paths are named by current engineering prompts and
indexes but are missing in this workspace as of 2026-04-22:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

Until those paths are restored or replaced by an explicit authority update, each
execution note must document the active fallback sources actually read.

Current observed fallback sources:

- four-layer state fallback: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- active publish/workbench alignment guidance: `docs/contracts/status_ownership_matrix.md`
- active line/runtime/ready-gate guidance:
  - `docs/contracts/hot_follow_line_contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/architecture/line_contracts/hot_follow_line.yaml`
  - `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

## Why This Exists

VeoBase01 is operating under a frozen sequence:

1. architecture closure
2. code-debt cleanup
3. new-line loading

That sequence fails if engineers begin from local code impressions, stale review
memory, or partial contract reading. This contract reduces state/projection
drift by making the authority read itself an explicit part of execution.
