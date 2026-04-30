# HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1

Status: Approved for execution  
Target branch: `VeoBase03`  
Execution mode: Contract-first, wave-based rebuild  
Decision baseline: Rebuild on stable backend service layer; reject both another patch round and a full-scratch rebuild.

---

## 1. Directive Purpose

This directive starts the Hot Follow rebuild using the approved architecture review baseline.

This is **not** another stabilization patch cycle.

This is a controlled rebuild that:

- preserves stable backend execution and artifact-producing services
- rebuilds the broken L3 aggregation and L4 projection/surface layers
- enforces single-source truth for route, current attempt, and compose readiness
- proceeds in verifiable waves with explicit stop/go gates

If this directive is not followed as written, the rebuild is considered out of contract.

---

## 2. Executive Decision

### 2.1 Go / No-Go

**GO — rebuild on stable backend service layer.**

Rejected options:

- another incremental patch round on the old surface/state blob
- full line rebuild from scratch at this stage

### 2.2 Architectural Judgment

Preserve:

- L1 execution modules
- L2 artifact-fact producers
- L3 subtitle anchors
- gate engine and YAML contracts
- skills, line registry, and contract-aligned tests

Rebuild:

- L3 CurrentAttempt aggregation
- L4 ready-gate signal extraction
- L4 presenter / workbench / response projection
- route ownership and route event persistence
- hot follow router size/orchestration shape as a later workstream

---

## 3. Rebuild Boundary

### 3.1 Stable backend service layer to preserve

Preserve these categories unless an explicit exception is approved:

- steps / providers / workers / compose / media execution
- artifact-facts producers
- voice state producers
- subtitle currentness and subtitle authority anchors
- ready-gate engine and YAML
- skills
- line registry
- existing contract-aligned test suite

### 3.2 Layers to rebuild

Rebuild these categories:

- L3 CurrentAttempt single producer
- L4 signal extraction, projection, presenter shaping
- route event ownership
- workbench/task/delivery response contracts
- direct frontend consumption model

### 3.3 Explicitly forbidden

- no old-line patch cycle
- no broad provider redesign
- no compose/post optimization expansion
- no UI redesign outside surface-contract alignment
- no L4 truth invention
- no post-gate mutation
- no silent route migration
- no helper-owned truth
- no frontend dependency on legacy mixed runtime blobs

---

## 4. Frozen Business Paths

Only these business paths are formal unless this directive is amended.

### Path A — URL main flow

`raw -> origin.srt -> target subtitle -> dub -> compose`

### Path B — Local preserve flow

`raw -> preserve_source_route -> compose`

### Path C — Explicit local re-entry

`preserve_source_route -> tts_replace_route subtitle/dub flow`

Rules:

1. A task belongs to exactly one canonical route at a time.
2. Route is persisted by explicit command/event, not silently derived on read.
3. Downstream consumers may not reinterpret the route.
4. Helper may assist subtitle production but may not own route switching or subtitle truth.
5. `origin.srt` existing does not mean `vi.srt` exists.
6. `vi.srt` must be created through formal target subtitle materialization.

---

## 5. Contract Additions Required

### 5.1 Route Event Contract

Add explicit route events / commands:

- `enter_preserve_source_route`
- `enter_tts_replace_route`

These are L1 route-truth writers.

The L3 aggregator must read persisted route truth and must not override it.

### 5.2 CurrentAttempt Contract

Add a typed L3 `CurrentAttempt` contract as the **single producer** of at least:

- `selected_compose_route`
- `route_allowed`
- `subtitle_required`
- `subtitle_process_state`
- `dub_process_state`
- `audio_ready`
- `dub_current`
- `compose_allowed`
- `compose_execute_allowed`
- `compose_reason`
- `requires_redub`
- `requires_recompose`

### 5.3 Response Projection Contract

L4 response projector must:

- consume L2 + L3 only
- never mutate persisted task state
- never rewrite post-gate truth
- never recompute business truth separately from the L3 CurrentAttempt producer

---

## 6. Wave Plan

Implementation must proceed in the following waves and may not skip ahead.

---

## Wave 0 — Directive + contract freeze

### Objective
Freeze rebuild boundary, contracts, and execution order before runtime changes.

### Scope
- create and freeze this directive
- create route event contract
- create CurrentAttempt contract
- create surface consumption contract
- define preserved vs rebuilt component inventory

### Deliverables
- `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`
- route event contract doc
- CurrentAttempt contract doc
- surface response contract mapping note

### Acceptance
- preserved backend inventory listed
- rebuilt components listed
- frozen business paths listed
- event-sourced route rule frozen
- wave order frozen

### Stop rule
No Wave 1 work starts until Wave 0 is frozen.

---

## Wave 1 — L3 CurrentAttempt aggregator rebuild

### Objective
Replace multi-producer route/current-attempt truth with one typed L3 producer.

### Scope
- replace legacy route/current-attempt aggregation with a single L3 aggregator
- aggregator reads:
  - persisted route truth
  - artifact facts
  - subtitle currentness
  - subtitle authority
  - voice/audio state
- aggregator does not mutate inputs
- helper remains auxiliary only

### Core rule
These fields must have one producer only:

- `selected_compose_route`
- `compose_allowed`
- `subtitle_required`
- `dub_current`

### Acceptance
- one producer for route/current-attempt truth
- no silent route migration
- no fallback chain that overrides persisted route
- URL path and local preserve path both resolve through the same L3 contract

### Stop rule
If any consumer still derives a conflicting route truth, Wave 2 cannot start.

---

## Wave 2 — L4 projection / gate / presenter rebuild

### Objective
Make L4 a true consumer-only layer.

### Scope
- rewrite ready-gate signal extractors to consume L3 only
- remove post-gate mutation helpers
- replace mutating status-policy side effects with pure response projection
- presenter/workbench only format and surface truth; never recompute it

### Acceptance
- no L4 mutation of L1 or L2 truth
- no post-gate mutation of `compose_allowed`
- ready gate, presenter, workbench, operator summary all resolve to the same route/current-attempt truth
- no preserve-route vs tts-route split-brain on the same task

### Stop rule
If any UI/state surface still shows conflicting route interpretations, Wave 3 cannot start.

---

## Wave 3 — Router shrink + end-to-end operational validation

### Objective
Reduce router orchestration weight and validate real operator behavior.

### Scope
- shrink `hot_follow_api.py` as a parallel workstream
- move business orchestration into services where required
- run end-to-end validation across three scenarios:
  1. URL main flow
  2. local preserve flow
  3. local preserve -> explicit re-entry -> subtitle/dub flow

### Acceptance
- URL flow can reach authoritative `vi.srt`, then dub, then compose
- local preserve remains operable and stable
- helper failure does not invalidate preserve-source compose legality
- explicit re-entry works only by command/event, never by silent route migration
- operator-visible surface is green and consistent

### Stop rule
If Wave 3 cannot produce stable operator-visible behavior, escalate for deprecation review.

---

## 7. Component Preservation / Rebuild Inventory

### 7.1 Preserve

Preserve as stable backend service layer:

- L1 execution modules
- L2 artifact-facts producers
- `hot_follow_subtitle_currentness.py`
- `hot_follow_subtitle_authority.py`
- gate engine + YAML contracts
- skills
- line registry
- contract-aligned test suite

### 7.2 Rebuild

Rebuild or replace:

- `gateway/app/services/hot_follow_process_state.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- post-gate mutation helper in `task_view_workbench_contract.py`
- `gateway/app/services/hot_follow_runtime_bridge.py`
- `gateway/app/services/ready_gate/hot_follow_rules.py` extractors
- truth-recomputing presenter logic
- router orchestration shape in `hot_follow_api.py` (parallel workstream)

---

## 8. Validation Matrix

### URL main flow
Must prove:

- `origin.srt` exists
- authoritative `vi.srt` is materialized through formal stage logic
- active running vs stale pending is distinguishable
- dub and compose consume authoritative/current subtitle truth only

### Local preserve flow
Must prove:

- preserve route remains valid
- compose CTA is enabled when business truth allows it
- helper failure does not kill preserve route legality
- no surface tries to reinterpret preserve route as tts route

### Local re-entry
Must prove:

- explicit operator command persists route change
- reducer reads route change instead of inventing it
- subtitle/dub flow starts only after formal re-entry
- no silent migration from subtitle readiness alone

### Single-source-of-truth check
For every passing scenario, all consumers of:

- `selected_compose_route`
- `compose_allowed`
- `subtitle_required`
- `dub_current`

must resolve to the same L3 output.

---

## 9. Engineering Rhythm

### Required execution rhythm
- one wave at a time
- directive-first
- contracts-first
- validation before next wave
- stop on failed acceptance gate

### Reporting format per wave
Each wave report must include:

1. files changed
2. contracts added/updated
3. runtime behavior changed
4. tests added/updated
5. validation samples run
6. pass/fail against wave gate
7. explicit go/no-go for the next wave

---

## 10. Codex Execution Order

Codex must execute in this exact order:

1. write/freeze directive and contract docs
2. implement Wave 1
3. validate Wave 1
4. implement Wave 2
5. validate Wave 2
6. implement Wave 3 parallel router shrink + scenario validation
7. produce final go/no-go report

Codex must not:
- add extra scope
- patch outside the frozen rebuild boundary
- silently keep legacy fallback semantics
- treat helper telemetry as truth
- introduce a new patch round under rebuild naming

---

## 11. Final Success Criteria

This rebuild is successful only if:

1. Hot Follow runs on a preserved stable backend service layer
2. L3 CurrentAttempt becomes the single producer of route/current-attempt truth
3. L4 becomes a pure consumer layer
4. preserve route and tts route can no longer coexist as competing truths on one task
5. operator-visible behavior becomes stable and contract-aligned
6. no additional patch round is required to make the rebuilt surface usable

If these criteria are not met, escalate to deprecation review.

---

## 12. Execution Command

**Start rebuild on stable backend service layer. Preserve backend producers. Rebuild L3 aggregator and L4 projection/surfaces in waves. No patch round. No silent route migration. No helper-owned truth.**
