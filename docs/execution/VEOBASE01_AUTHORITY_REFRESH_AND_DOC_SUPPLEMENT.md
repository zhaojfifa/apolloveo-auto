# VeoBase01 Authority Refresh And Doc Supplement

Date: 2026-04-22
Branch: `VeoBase01`
Base branch: `VeoBase01`
Merge baseline SHA before this refresh: `8908df79aa5ea8013e2ae92b9575b7469ebe8341`

## Purpose

Repair the mismatch between the Engineering Reading Contract, the engineering
indexes, and the actual authority files present in the repo.

## Missing Authority Files Before This Refresh

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

## Decision

Option A was chosen: reconstruct the missing files as real canonical
authorities.

Reason:

- the engineering index and reading contract already treated these paths as
  first-class authorities
- the repo did not show a stronger moved canonical replacement for the same
  authority role
- the existing fallback materials were complementary, not equivalent:
  - `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md` is a reusable template
  - `docs/contracts/status_ownership_matrix.md` is an ownership/write-path
    authority

## Reconstructed Canonical Files

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

## Final Canonical Authority Set

Repository / engineering entry:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Current phase:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

State truth:

- primary layer authority: `docs/contracts/four_layer_state_contract.md`
- ownership/write-path authority: `docs/contracts/status_ownership_matrix.md`
- drafting/fallback template only: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`

Workbench / publish response truth discipline:

- `docs/contracts/workbench_hub_response.contract.md`

Architecture / state baseline:

- `apolloveo_current_architecture_and_state_baseline.md`

Line / runtime / ready-gate ownership:

- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Files Updated

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

## Why This Reduces Future Engineering Drift

- the reading contract now points only at real canonical files
- four-layer semantics, workbench/publish response truth discipline, and the
  architecture/state baseline are no longer implied through fallback notes
- the template and ownership matrix remain available but are now clearly marked
  as companion sources, not silent replacements for missing authority docs

## Rollback Path

- revert the reconstructed authority docs
- restore the prior reading-contract/index wording if the repo later adopts a
  different explicit canonical replacement set
- if reverted, do not leave the indexes pointing at missing paths again without
  a new explicit replacement decision
