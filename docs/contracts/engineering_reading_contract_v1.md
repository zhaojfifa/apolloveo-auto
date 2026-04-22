# Engineering Reading Contract v1

Date: 2026-04-22

## Purpose

This contract freezes mandatory reading as a formal engineering precondition for
state, projection, runtime, and contract work in VeoBase01.

No state/projection/runtime change may begin until the required authority set
has been read in order and the execution note for the work records a Reading
Declaration.

This contract now points only at canonical authority files that exist in the
repo. Historical mismatch notes remain in execution history, but the active
reading list below is the current canonical set.

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

State truth is defined by:

- primary state-layer authority: `docs/contracts/four_layer_state_contract.md`
- ownership/write-path authority: `docs/contracts/status_ownership_matrix.md`
- drafting/fallback template only:
  `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`

Workbench/publish response authority is defined by:

- `docs/contracts/workbench_hub_response.contract.md`

Architecture/state baseline authority is defined by:

- `apolloveo_current_architecture_and_state_baseline.md`

Current phase is defined by:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

Line / runtime / ready-gate ownership is defined by:

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
memory, or partial contract reading. This contract reduces state/projection
drift by making the authority read itself an explicit part of execution.
