# Contract Editor Preparation Notes v1

Date: 2026-04-22

## Purpose

Prepare the object model that a future contract editor would manipulate.

This document does not propose a UI build now. It defines the editable contract
objects so future tooling can replace hardcoded state-control branches safely.

## Editable Object Families

### 1. Line Contract Refs

Editable objects:

- line id
- task kind
- line contract ref
- ready gate ref
- skills bundle ref
- worker profile ref
- deliverable profile ref
- asset sink profile ref
- confirmation policy ref

Why:

- this is the factory registration layer
- it must stay distinct from business truth and execution state

### 2. Deliverable Profile Rules

Editable objects:

- accepted deliverable kinds
- required deliverable kinds by route
- optional deliverable kinds
- current-vs-historical final policy
- display labels and surface aliases

Why:

- publish/workbench must stop embedding deliverable assumptions in code

### 3. State Machine Transitions

Editable objects:

- allowed L1 step states
- allowed transitions
- terminal failure states
- stale-current-final transition rules
- non-blocking scene-pack rules

Why:

- step execution and publishability need separate but linked contracts

### 4. Ready Gate Rules

Editable objects:

- signals
- override rules
- gate formulas
- blocking rules
- non-blocking advisory rules
- dominance rules such as current fresh final over stale compatibility hints

Why:

- this is the most direct replacement target for current scattered readiness
  conditionals

### 5. Publish / Workbench Projection Policies

Editable objects:

- projection source contract
- publish surface contract
- workbench surface contract
- alias/compatibility policy
- contract-adapter allowed mutations list, which should default to empty for
  authoritative truth objects

Why:

- one contract editor must be able to modify surface policy without making the
  surface a truth owner

### 6. Advisory / Blocking-Reason Mappings

Editable objects:

- blocking reason code
- operator-facing message
- advisory severity
- surface visibility
- non-blocking advisory classification

Why:

- advisory language should be contract-controlled rather than rebuilt in
  multiple presenter paths

## Editing Constraints For A Future Editor

The future editor must enforce:

- L4 may not write L2 or L3 truth
- compatibility mappings may not override valid final/subtitle/audio artifact
  truth
- helper translation state may not replace authoritative target subtitle truth
- scene-pack pending may not downgrade final-ready publishability
- line/runtime refs may not be silently edited without corresponding contract
  validation

## Suggested Storage Model

Suggested editable units:

- `line_contract_ref`
- `ready_gate_rule_set`
- `state_machine_rule_set`
- `projection_policy_set`
- `deliverable_profile_rule_set`
- `advisory_mapping_set`

Suggested editor workflow:

1. load contract refs
2. edit one rule family at a time
3. run contract validation
4. run publish/workbench regression probes
5. publish reviewed contract updates

## Not In Scope Yet

- no contract editor runtime UI
- no dynamic hot-reload of production contracts
- no new-line implementation
- no multi-role harness orchestration

## How This Reduces Silicon-Parallel Drift

- It defines one future editing surface for contract objects instead of letting
  multiple engineers keep encoding similar policy in different modules.
- It separates line registration, state-machine policy, ready-gate policy, and
  advisory mapping, which reduces accidental cross-layer edits.
- It turns later tooling work into contract-object editing rather than another
  round of router/service conditional growth.
