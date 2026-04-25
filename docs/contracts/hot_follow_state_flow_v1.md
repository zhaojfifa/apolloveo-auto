# Hot Follow State Flow v1

Date: 2026-04-25
Status: Frozen docs-only authority packet

## Purpose

This document freezes one explicit Hot Follow state progression from task
creation to publish-ready.

It does not change runtime behavior. It makes the state path reviewable before
the next pass adds minimal runtime enforcement.

This flow is downstream of:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Flow Principles

1. L1 step status never decides business truth by itself.
2. L2 artifact facts answer what exists.
3. L3 current-attempt state decides whether the current path is ready,
   blocked, retryable, or terminal.
4. L4 surfaces consume L2/L3 truth and may not invent a competing state path.
5. Helper side-channel state is explicit and separate from the mainline
   subtitle/audio/final path.
6. Historical event residue may remain visible, but it must not drive current
   route truth.

## Canonical State Sequence

The normal Hot Follow mainline is:

`task_created -> raw_ready -> parse_waiting -> parse_ready -> subtitle_waiting -> helper_sidechannel_waiting -> target_subtitle_ready -> dub_waiting -> dub_ready -> compose_waiting -> compose_ready -> final_ready -> publish_ready`

The explicit waiting/retry/manual/terminal branches are defined below.

## State Classes

### Normal Path

- `task_created`
- `raw_ready`
- `parse_waiting`
- `parse_ready`
- `subtitle_waiting`
- `target_subtitle_ready`
- `dub_waiting`
- `dub_ready`
- `compose_waiting`
- `compose_ready`
- `final_ready`
- `publish_ready`

### Waiting Path

- `parse_waiting`
- `subtitle_waiting`
- `helper_sidechannel_waiting`
- `parse_waiting`
- `dub_waiting`
- `compose_waiting`

Waiting means the current path is still live and has not become terminal.

### Retryable Path

- `translation_waiting_retryable`
- `helper_retryable_failure_warning_only`
- `helper_resolved_with_retryable_provider_warning`

Retryable means the intended mainline route remains active and the current
state must not be projected as a terminal no-dub/no-TTS route.

### Manual-Intervention Path

- `parse_manual_intervention_required`
- `subtitle_manual_intervention_required`
- `dub_manual_intervention_required`
- `compose_manual_intervention_required`
- `publish_manual_intervention_required`

Manual-intervention states are non-normal branches where operator action is
allowed or required before the next transition.

### Terminal Path

- `publish_ready`
- `parse_terminal_failed`
- `subtitle_terminal_failed`
- `dub_terminal_failed`
- `compose_terminal_failed`
- `publish_terminal_failed`

Terminal means the current attempt cannot progress without a new operator or
controller action that starts a new attempt path.

## Explicit Flow By Stage

### 1. Intake And Raw Materialization

`task_created -> raw_ready`

Conditions:

- L1: task exists, parse has not yet completed
- L2: raw/source video artifact exists or has been materialized
- L3: current attempt is still intake/parse pending
- L4: surfaces may show task created or waiting for parse

### 2. Parse

`raw_ready -> parse_waiting -> parse_ready`

Alternate exits:

- `parse_waiting -> parse_manual_intervention_required`
- `parse_waiting -> parse_terminal_failed`

Parse-ready means parse artifacts are materially available for subtitle lane
evaluation. It does not yet prove subtitle readiness.

### 3. Subtitle Formation

`parse_ready -> subtitle_waiting`

From `subtitle_waiting`, the allowed branches are:

- `subtitle_waiting -> helper_sidechannel_waiting`
- `subtitle_waiting -> translation_waiting_retryable`
- `subtitle_waiting -> target_subtitle_ready`
- `subtitle_waiting -> subtitle_manual_intervention_required`
- `subtitle_waiting -> subtitle_terminal_failed`

Rules:

- `translation_waiting_retryable` is a retryable subtitle-currentness shape.
- It must not be projected as `no_tts` / `no_dub` terminal truth.
- `helper_sidechannel_waiting` is explicit helper state, not helper null-state
  ambiguity.

### 4. Helper Side-Channel

`helper_sidechannel_waiting` may transition to:

- `target_subtitle_ready`
- `helper_retryable_failure_warning_only`
- `helper_resolved_with_retryable_provider_warning`
- `subtitle_manual_intervention_required`

Rules:

- helper/provider trouble is diagnostic side-channel truth unless helper output
  absence is the live blocking subtitle truth
- helper failure may remain visible after mainline success, but only as warning
  or advisory state
- helper state never overrides current authoritative target subtitle truth

### 5. Target Subtitle Currentness Boundary

The only legal exit into audio/compose progress is:

`target_subtitle_ready -> dub_waiting`

`target_subtitle_ready` requires all of the following:

- authoritative target subtitle exists in L2
- subtitle currentness is true in L3
- the current route does not still report missing subtitle authority in L4

Forbidden shortcut:

- `subtitle_waiting -> no_dub terminal route`

That shortcut is illegal unless explicit no-dub/no-TTS contract facts are
already satisfied.

### 6. Dub / Audio

`dub_waiting -> dub_ready`

Alternate exits:

- `dub_waiting -> translation_waiting_retryable`
- `dub_waiting -> dub_manual_intervention_required`
- `dub_waiting -> dub_terminal_failed`

Special retryable rule:

- on a TTS-expected route, `audio_ready=false` after a provider/audio failure
  keeps the route in the dub-retryable family
- it does not allow projection into `no_tts_compose_route`,
  `preserve_source_route`, or `bgm_only_route` unless explicit no-dub/no-TTS
  boundary facts are already true

### 7. Compose

`dub_ready -> compose_waiting -> compose_ready`

Alternate exits:

- `compose_waiting -> compose_manual_intervention_required`
- `compose_waiting -> compose_terminal_failed`

`compose_ready` means compose inputs and current-final conditions are satisfied
for the current route. A stale historical final is insufficient.

### 8. Final And Publish

`compose_ready -> final_ready -> publish_ready`

Alternate exits:

- `final_ready -> publish_manual_intervention_required`
- `final_ready -> publish_terminal_failed`

Rules:

- `final_ready` requires current fresh final truth
- `publish_ready` consumes ready-gate truth
- scene-pack pending may remain visible, but it is advisory only and may not
  downgrade `publish_ready`

## No-Dub / No-TTS Boundary Freeze

No-dub or no-TTS terminal projection is legal only when all of the following
are true:

1. the route is explicitly one of:
   - `preserve_source_route`
   - `bgm_only_route`
   - `no_tts_compose_route`
2. L2/L3 contain explicit no-dub/no-TTS allowance facts for the current path
3. the ready-gate and projection path agree on that route family
4. the shape is not merely subtitle waiting, translation incomplete, or helper
   retryable failure

Therefore:

- `subtitle_waiting`
- `translation_waiting_retryable`
- `helper_retryable_failure_warning_only`

must never be projected as terminal no-dub/no-TTS states unless the explicit
boundary conditions above are satisfied.

## Four-Layer Mapping By Major State

| State | L1 | L2 | L3 | L4 |
| --- | --- | --- | --- | --- |
| `task_created` | task created, no downstream done state yet | raw may be absent | no current-ready facts yet | created / pending projection only |
| `raw_ready` | intake complete, parse pending | raw exists | parse may start | parse pending |
| `parse_waiting` | `parse_status=pending/running` | raw exists | parse not yet resolved | parse waiting |
| `parse_ready` | `parse_status=done` | parse outputs exist | subtitle lane may start | subtitle entry enabled |
| `subtitle_waiting` | `subtitles_status=pending/running` | target subtitle absent or not yet authoritative | subtitle currentness false or pending | subtitle waiting / blocked |
| `helper_sidechannel_waiting` | helper side work running or unresolved | helper output absent or pending | helper state explicit, mainline unresolved | helper waiting advisory |
| `translation_waiting_retryable` | subtitle or dub lane not terminal | target subtitle authority not yet satisfied | retryable currentness failure | retry warning, not terminal no-dub |
| `target_subtitle_ready` | subtitle lane materially done | authoritative target subtitle exists | target subtitle current | subtitle ready |
| `dub_waiting` | `dub_status=pending/running` | current voiceover absent or incomplete | TTS route still intended | dub waiting |
| `dub_ready` | `dub_status=done` | current audio exists | `audio_ready=true`, `dub_current=true` | audio ready |
| `compose_waiting` | `compose_status=pending/running` | final absent or stale | compose not yet current-ready | compose waiting / blocking reasons |
| `compose_ready` | compose materially complete | current final exists | compose currentness true | compose ready |
| `final_ready` | compose done | final exists and fresh | current attempt ready | final-ready projection |
| `publish_ready` | publish gate eligible | final exists and fresh | current attempt still ready | ready gate publish-ready |

## Evidence Anchors

This flow packet is grounded in the observed regression classes already frozen
in branch discussion:

- clean success / closure shape
- early `no_tts` premature terminalization shape
- translation waiting retryable shape
- helper warning-only successful shape
- contradictory split shape

## Review Outcome

After this packet:

- Hot Follow has one explicit state flow
- waiting, retryable, manual, and terminal branches are named explicitly
- no-dub/no-TTS projection boundaries are frozen for the next enforcement pass
