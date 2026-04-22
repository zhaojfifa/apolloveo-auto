# Production-Line Runtime Assembly Rules v1

Date: 2026-04-23
Status: Rules-first baseline

## Purpose

This document defines the minimum runtime assembly object set for a production
line and freezes the rule that routers do not directly own line business rules.

## Minimum Runtime-Assembly Object Set

- `line_id`
- `input_contract_ref`
- `deliverable_profile_ref`
- `worker_profile_ref`
- `ready_gate_ref`
- `projection_rules_ref`
- `status_policy_ref`
- optional `skills_bundle_ref`
- optional `asset_sink_profile_ref`

## Router Rule

Routers must not directly decide line business rules.

Routers may only:

- authenticate
- parse request
- resolve `task_kind` / `line_id`
- load contract/runtime objects
- dispatch to services
- return response

Routers must not:

- decide publish-ready rules
- decide final/currentness precedence
- own compatibility-heavy business fallback logic
- act as hidden line policy registries

## Runtime Assembly Sequence

1. Resolve `task_kind` / `line_id`.
2. Load the line contract refs.
3. Load ready-gate and projection rule refs.
4. Load status-policy and worker profile refs.
5. Dispatch to services that apply the loaded rules.
6. Return surface responses shaped from authoritative state/projection results.

## Ready Gate Loading

Ready gate is loaded from `ready_gate_ref`.

Rules:

- the line contract declares which ready gate to use
- services/status-policy consume that ready gate
- routers do not hardcode line-specific ready logic

## Projection Rules Loading

Projection rules are loaded from `projection_rules_ref`.

Rules:

- projection rules define how surfaces consume authoritative state
- publish/workbench/task detail must share one projection truth path
- routers and contract adapters must not become alternate projection rule owners

## Blocking-Reason Mapping Loading

Blocking-reason mapping is loaded as part of the projection / ready-gate rule
set, not as router-local string logic.

Rules:

- blocking reasons originate from state/projection rules
- surfaces may display or map them, but do not define their business meaning

## Ownership Rules

State truth owner:

- Layer 2 state/projection rules and status-policy path own derived readiness
  truth

Write authority owner:

- execution/controller/service path owns persisted writes
- worker execution may return results but must not directly own repo truth
- surface/presentation code has no truth-write authority

## Service Responsibility

Services are the runtime consumers of loaded line objects.

They may:

- combine loaded contract refs with task/runtime inputs
- assemble authoritative state
- invoke status policy and ready gate
- produce surface-safe payloads

They may not:

- absorb rules that should instead be loaded from declared contract/rule refs

## Minimal Future Line Entry Model

Any future line discussion must begin with this assembly shape:

1. declare the line object set
2. define the state/projection rules
3. bind services to loaded rule objects
4. keep routers as adapters

No new line should begin from “add another route branch”.

## How This Becomes The Base For Future Contract Editor Work

- The future editor can manipulate line refs, ready-gate refs, projection-rule
  refs, and blocking-reason mappings as first-class objects.
- Because routers are not the rule owners, editing those objects later does not
  require moving business logic back out of transport code again.
- This document defines the minimum object model needed before an editor can be
  meaningful.
