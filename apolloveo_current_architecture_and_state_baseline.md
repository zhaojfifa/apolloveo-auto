# ApolloVeo Current Architecture And State Baseline

Date: 2026-04-22
Status: Canonical authority

## Purpose

This document is the current architecture/state baseline authority referenced by
the VeoBase01 reading contract.

It is a concise baseline entry that ties together the active reconstruction
phase, the four-layer state model, and the Hot Follow production-line baseline.

## Current Baseline

- `main` is the stable operational branch
- `VeoBase01` is the primary refactor integration branch
- Hot Follow is the current baseline production line
- new-line runtime implementation remains blocked until the sequential gate is
  explicitly lifted

## Frozen Phase Sequence

The active sequence is:

1. architecture closure
2. code-debt cleanup
3. new-line loading

Authority:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

## Current State Baseline

ApolloVeo currently preserves this four-layer state model:

- L1 Pipeline Step Status
- L2 Artifact Facts
- L3 Current Attempt
- L4 Ready Gate / Operator Summary / Advisory / Presentation

Authority:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`

## Hot Follow Baseline Rule

Hot Follow publish/workbench surfaces must consume the same authoritative
projection path.

This baseline includes:

- current final vs historical final separation
- ready-gate truth derived from L2/L3 inputs
- scene-pack pending as non-blocking when the current final is fresh and
  publishable

Supporting authorities:

- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`

## Runtime Boundary Baseline

- routers are transport/adaptation layers
- services own reusable state/projection/runtime logic
- status policy and ready gate own derived readiness
- skills are advisory readers, not truth writers
- workers execute jobs but do not directly own repo truth

Supporting authorities:

- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/status_ownership_matrix.md`

## What This Baseline Does Not Permit

- no new-line runtime implementation yet
- no multi-role harness introduction yet
- no surface-specific truth path that bypasses the authoritative projection
- no compatibility field overriding current valid final/audio/subtitle truth
