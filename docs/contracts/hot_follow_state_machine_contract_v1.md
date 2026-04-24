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
- `subtitle_translation_waiting_retryable`
- `compose_input_ready`
- `compose_execute_allowed`
- `compose_blocked_terminal`
- `compose_input_derive_failed_terminal`
- `compose_exec_failed_terminal`
- `retriable_dub_failure`
- `tts_lane_expected`
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
- `pending -> running -> pending` when target subtitle translation is still
  unresolved but parse/source evidence exists and no terminal contract evidence
  exists
- helper translation failure does not force subtitle truth to failed when the
  authoritative target subtitle already exists and is current

### Dub / Audio

- `pending -> running -> done`
- `pending -> running -> failed`
- `pending -> pending` when target subtitle translation is still unresolved
  and subtitle readiness is the only blocker
- preserve-source or other no-TTS-allowed routes may keep compose legally
  reachable without TTS voiceover readiness
- a failed TTS/provider/audio generation attempt on a subtitle-ready,
  TTS-expected path is retriable current-attempt failure, not no-dub terminal
  truth

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
- retriable TTS/provider/audio generation failure while the intended route is
  `tts_replace_route`
- current final absent
- current final stale against current attempt

## Non-Blocking Conditions

Non-blocking:

- scene pack pending while current final is fresh and publishable
- helper translation failure after authoritative target subtitle truth is valid
- historical final presence when a current fresh final already exists
- historical `post.dub.fail(target_subtitle_translation_incomplete)` events when
  current subtitle/audio truth says the task is still
  `translation_waiting_retryable`

## Frozen Non-Terminal Contract State

### `translation_waiting_retryable`

Definition:

- target subtitle translation unresolved
- helper/provider lane is pending or retryable
- non-terminal
- `no_dub=false`
- selected compose route remains `tts_replace_route`
- subtitle/audio are not ready yet
- compose is blocked only by the waiting state

L2 truth ownership:

- `helper_translation.status`
- `helper_translation.retryable`
- `helper_translation.terminal`
- `subtitle_ready`
- `subtitle_ready_reason`
- `audio_ready`
- `audio_ready_reason`
- `selected_compose_route`
- `no_dub`

L3/L4 derivation rule:

- `ready_gate`, `current_attempt`, `advisory`, `pipeline`, `deliverables`, and
  `operator_summary` must derive from the above truth set
- none of those L4 surfaces may keep stale failed projection once L2 says the
  task is `translation_waiting_retryable`

### `helper_side_channel_explicit_state`

Definition:

- helper translation is a side-channel contract lane
- helper lane may assist source understanding and manual subtitle fill
- helper lane does not become authoritative target subtitle truth unless the
  canonical target-subtitle save path succeeds

Frozen helper lane states:

- `helper_unavailable`
- `helper_pending`
- `helper_resolved`
- `helper_retryable_failure`
- `helper_terminal_failure`

Dominance rule:

- if `target_subtitle_current=true`
- and `target_subtitle_authoritative_source=true`
- and `subtitle_ready=true`
- and `audio_ready=true`
- and `final_exists=true`
- then helper retryable or terminal failure remains helper-side diagnostic
  truth only
- in that shape helper history may stay visible, but it must not become
  `subtitles.error`, `current_attempt_failed`, ready-gate failure, or publish
  blocking truth

## Dominance Rules

### TTS Expected Route Dominance

Explicit rule:

- `subtitle_ready + TTS lane expected + audio_ready=false + current TTS
  failure` must remain `tts_replace_route` and must not collapse into
  `no_tts_compose_route` unless an explicit no-dub/no-TTS terminal rule applies.

Interpretation:

- first-dub failures are retriable dub failures when Hot Follow still expects
  TTS audio
- L3 may mark `retriable_dub_failure=true`
- L3/L4 must not set `no_dub_route_terminal=true` or recommend
  `compose_no_tts` for that shape
- true no-dub/no-TTS terminal paths require explicit no-dub/no-TTS facts and
  route allowance

### Preserve-Source Route Separation

Explicit rule:

- `source_audio_policy=preserve` by itself does not decide the route
- preserve-source without target subtitle is legal only when an explicit
  preserve-source/no-target contract fact applies
- otherwise preserve-policy tasks remain on the standard dubbing route when the
  current subtitle/audio boundary says target subtitle is required or expected

Interpretation:

- `preserve_source_route_no_target_subtitle_required` is an explicit legal
  preserve-source boundary fact
- translation-incomplete / helper-failed voice-led shapes are not silently
  reclassified into preserve/no-TTS terminal just because preserve policy is
  enabled

### Helper Side-Channel Coexistence

Explicit rule:

- helper/provider failure remains diagnostic side-channel truth unless an
  explicit subtitle-formation rule says it blocks target subtitle formation
- once current subtitle/audio/final truth is ready, helper failure history may
  remain visible but must not downgrade route, current-attempt, or ready-gate
  truth
- helper input text and translated text remain helper-scoped and must not
  overwrite authoritative target subtitle fields unless canonical subtitle save
  succeeds

### Historical Event Isolation

Explicit rule:

- historical skip/failure events may remain in `events`
- they must not override current subtitle/audio/final truth once current truth
  is ready

Interpretation:

- stale `target_subtitle_empty` / `dub_input_empty` skip history may remain
  visible in logs
- it must not keep `no_dub`, `no_tts`, or terminal-route interpretation active
  after current subtitle/audio/final truth is ready

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
