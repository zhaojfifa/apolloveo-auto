# VeoBase01 Sequential Execution Decision

Date: 2026-04-22

## Decision

VeoBase01 execution is now explicitly sequential across the next three phases.

Engineering reading is a frozen precondition for that sequence. Before any
state, projection, runtime, or contract change starts, read
`docs/contracts/engineering_reading_contract_v1.md` and record its Reading
Declaration in the execution note for the slice.

The frozen phase order is:

1. architecture closure first
2. code-debt cleanup second
3. new-line loading third

No parallel execution is allowed across these three phases.

## Why

Parallel execution across architecture closure, code-debt cleanup, and new-line
loading would blur ownership and weaken boundary enforcement again.

VeoBase01 must finish structural closure before cleanup begins, and cleanup must
stabilize before any new production line can start implementation.

## Frozen Rule

### Phase 1 — Architecture Closure

Goal:

- finish VeoBase01 structural closure
- keep the Hot Follow business baseline stable
- do not start new-line implementation

Focus:

1. line contract/runtime ref closure
2. skills / worker / deliverable / asset sink boundary freeze
3. four-layer state enforcement
4. workbench contract vs implementation alignment
5. task semantic convergence where still needed
6. docs/index/ADR/contract alignment

Acceptance:

- contracts no longer drift
- state layers are stable
- runtime refs are real, not ceremonial
- business baseline still passes

### Phase 2 — Code-Debt Cleanup

This phase may start only after Phase 1 passes.

Priority order:

1. `tasks.py`
2. `hot_follow_api.py`
3. `task_view.py`
4. `task_view_workbench_contract.py`

Goal:

- router thinning
- single-write ownership
- remove god-file behavior
- reduce compatibility residue
- no business behavior change

### Phase 3 — New-Line Loading

This phase may start only after Phase 1 and Phase 2 are both validated.

Allowed only then:

- new-line design continuation
- new-line minimum implementation
- multi-role harness introduction

## Current Gate

- new-line design may continue
- new-line implementation remains blocked
- multi-role harness remains blocked
