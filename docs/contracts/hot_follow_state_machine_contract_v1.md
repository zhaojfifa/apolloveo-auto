# Hot Follow State Machine Contract v1

Date: 2026-04-22
Status: Draft for Phase 2 contract-driven upgrade

## Purpose

This draft separates execution state, artifact state, current-attempt state,
and presentation state so Hot Follow can stop encoding publish/workbench truth
as router-local condition chains.

## Layer Separation

- L1 = Pipeline Step Status
- L2 = Artifact Facts
- L3 = Current Attempt
- L4 = Ready Gate / Operator Summary / Advisory / Presentation

Rule:

- L4 consumes L2/L3-derived truth and may not invent or override it.

## State Domains

### L1 Pipeline Step Status

Allowed step states:

- `never`
- `pending`
- `running`
- `done`
- `failed`
- `blocked`

Applies to:

- parse
- subtitles
- dub
- pack
- compose
- publish

### L2 Artifact Facts

Artifact-fact states are not step states. They are factual booleans and factual
metadata:

- raw exists / missing
- target subtitle exists / missing
- current audio exists / missing
- current final exists / missing
- current final fresh / stale
- scene pack exists / missing

### L3 Current Attempt

Allowed attempt states and flags:

- `audio_ready`
- `dub_current`
- `compose_input_ready`
- `compose_execute_allowed`
- `compose_blocked_terminal`
- `compose_input_derive_failed_terminal`
- `compose_exec_failed_terminal`
- `requires_redub`
- `requires_recompose`
- selected compose route

### L4 Presentation

Allowed derived outputs:

- `ready_gate`
- `operator_summary`
- `advisory`
- publish surface payload
- workbench surface payload

## Core Transition Rules

### Parse

- `pending -> running -> done`
- `pending -> running -> failed`

### Subtitles

- `pending -> running -> done`
- `pending -> running -> failed`
- helper translation failure does not force subtitle truth to failed when the
  authoritative target subtitle already exists and is current

### Dub / Audio

- `pending -> running -> done`
- `pending -> running -> failed`
- preserve-source or other no-TTS-allowed routes may keep compose legally
  reachable without TTS voiceover readiness

### Compose

- `pending -> running -> done`
- `pending -> blocked`
- `pending -> failed`
- `done -> pending` only when the current final becomes stale against current
  subtitle/audio truth

## Blocking Conditions

Blocking conditions are L3/L4 decisions derived from L2/L3 inputs, not direct
step writes.

Blocking:

- compose input blocked
- compose input derive failed
- current route requires TTS audio but `audio_ready=false`
- current final absent
- current final stale against current attempt

## Non-Blocking Conditions

Non-blocking:

- scene pack pending while current final is fresh and publishable
- helper translation failure after authoritative target subtitle truth is valid
- historical final presence when a current fresh final already exists

## Dominance Rules

### Final Dominance

Explicit rule:

- `final_exists + current_attempt ready` must dominate publish presentation
  truth.

Interpretation:

- if the current final is fresh and the current attempt is ready, L4 publish
  presentation must resolve ready
- compatibility fallbacks may not downgrade that result

### Scene-Pack Non-Downgrade Rule

Explicit rule:

- scene-pack pending does not downgrade final-ready publishability

Interpretation:

- scene-pack status may create advisory state
- it may not flip `publish_ready` to false when the final/current-attempt path
  is already ready

## Transition Matrix

| Domain | Allowed transition | Forbidden transition |
| --- | --- | --- |
| L1 step | `pending -> running -> done` | presenter forcing `pending -> done` without execution evidence |
| L2 artifact | `missing -> exists` | surface code overwriting artifact facts |
| L3 current attempt | `audio_ready=false -> true` when current audio is validated | presenter inferring `audio_ready=true` from historical fields |
| L3 current attempt | `requires_recompose=false -> true` when final becomes stale | contract adapter silently clearing stale state |
| L4 presentation | `publish_ready=false -> true` from ready gate on L2/L3 truth | router or presenter forcing ready from isolated one-off heuristics |

## Minimal Contract Shape

```yaml
hot_follow_state_machine:
  step_states: [never, pending, running, done, failed, blocked]
  artifact_facts:
    final_exists: boolean
    final_fresh: boolean
    subtitle_exists: boolean
    audio_exists: boolean
    scene_pack_exists: boolean
  current_attempt:
    audio_ready: boolean
    dub_current: boolean
    compose_input_ready: boolean
    compose_execute_allowed: boolean
    requires_redub: boolean
    requires_recompose: boolean
  presentation:
    publish_ready: derived
    blocking: derived
```

## How This Reduces Silicon-Parallel Drift

- It gives execution, artifact, and presentation work different state domains so
  they stop competing for the same truth fields.
- It encodes non-blocking paths explicitly, which prevents teams from
  reintroducing scene-pack or helper-translation downgrade drift.
- It makes dominance rules reviewable before runtime code changes, so the next
  cleanup slice can move more logic from conditionals into contracts.
