# Workbench Hub Response Contract

Date: 2026-04-22
Status: Canonical authority

## Purpose

This document freezes the authority rules for Hot Follow workbench and related
surface responses.

It is the contract authority for response truth discipline, not a duplicate of
every current payload field in implementation. The runtime adapter remains in
`gateway/app/services/task_view_workbench_contract.py`, but that adapter is not
allowed to replace authoritative truth.

## Surface Discipline

Workbench, publish, and task-detail surfaces must all consume the same
authoritative projection path before any surface-specific shape adaptation.

The canonical path is:

1. projection assembly from task/runtime/artifact inputs
2. L2 artifact facts + L3 current-attempt derivation
3. ready-gate evaluation
4. surface shaping / compatibility aliases

## Required Sections

Hot Follow workbench responses must expose, directly or through stable aliases,
these semantic sections:

- task identity / line identity
- input summary
- media summary
- pipeline status rows
- subtitles section
- audio section
- deliverables section
- final / historical final distinction
- compose summary
- ready gate
- artifact facts
- current attempt
- operator summary
- advisory when available

## Truth Rules

1. `artifact_facts`, `current_attempt`, `final`, `historical_final`, and
   `ready_gate` are authoritative response truth inputs.
2. Presenters may normalize shape, labels, and aliases but may not recompute a
   separate business truth path.
3. Publish and workbench must not diverge on final-ready truth when they are
   consuming the same authoritative projection.
4. Contract adapters may not downgrade valid current final/audio/subtitle truth
   through legacy fallback fields.

## Final / Historical Final Rule

- `final` means the current fresh final deliverable
- `historical_final` means a previously successful physical output
- historical output may be shown, but it must not satisfy current-ready truth
  when the current final is stale or absent

## Ready Gate Rule

Ready gate is the surface-ready summary of L2/L3 truth.

Rules:

- workbench and publish must consume ready-gate outputs rather than recomputing
  competing readiness
- scene-pack pending may remain visible but must not downgrade final-ready
  publishability
- helper translation failure may be advisory, but it must not override valid
  target-subtitle truth

## Compatibility Rule

Compatibility fields may exist during staged cleanup, but they are adapters
only.

Forbidden:

- recomputing `compose_status`, `audio_ready`, or `publish_ready` from legacy
  publish/workbench-only helpers after authoritative projection is built
- rewriting deliverable truth after ready-gate computation
- silently promoting or demoting current readiness from alias fields

## Relationship To Implementation

- Contract authority: this document
- Runtime adapter/shaping module:
  `gateway/app/services/task_view_workbench_contract.py`
- Authoritative projection/presenter modules:
  - `gateway/app/services/task_view_projection.py`
  - `gateway/app/services/task_view_presenters.py`

Implementation may evolve, but it must preserve this truth discipline.
