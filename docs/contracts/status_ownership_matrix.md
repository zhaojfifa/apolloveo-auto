# Status Ownership Matrix

## 1. Purpose

This matrix freezes who owns which kind of state in ApolloVeo, with Hot Follow as the first concrete line.

The goal is to keep three things separate:

- truth
- derived state
- display-only projection

## 2. Ownership Rules

### 2.1 Truth

Truth means fields that are persisted as the record of what actually happened or what artifact actually exists.

Truth writers must be explicit and limited.

### 2.2 Derived

Derived state is computed from truth and may be cached for compatibility, but it is not an independent authority.

### 2.3 Display-Only

Display-only fields exist for board/workbench/publish presentation and must never be treated as source-of-truth.

## 3. Ownership Matrix

| Field Family | Example Fields | Class | Primary Owner | Allowed Write Path | Not Allowed To Write | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| primary task attempt status | `status` | operational truth | controller/router state write path | explicit repo/state-service updates after step execution | worker, skills, frontend | `status` is coarse operational truth; for Hot Follow board primary state it must not outrank ready gate + deliverable truth |
| current step pointer | `last_step` | operational truth | controller/router state write path | explicit repo/state-service updates during step orchestration | worker, skills, presenter | indicates attempt progress, not publishable truth |
| coarse pipeline errors | `error_reason`, `error_message` | operational truth | controller/router state write path | explicit failure handling branch | worker direct writes, frontend | worker may return structured error, but controller decides persisted task error |
| step sub-status: subtitles | `subtitles_status`, `subtitle_error`, subtitle step messages | operational truth | subtitle controller/service write path | step completion/failure persistence | worker, skills, presenters | must not be confused with target subtitle currentness |
| step sub-status: dub | `dub_status`, `dub_error` | operational truth | dub controller/service write path | step completion/failure persistence | worker, skills, presenters | must not be treated as current dub truth by itself |
| step sub-status: compose | `compose_status`, `compose_error_reason` | operational truth | compose controller/service write path | step completion/failure persistence | worker, skills, presenters | does not by itself prove final is current |
| step sub-status: pack/publish | `pack_status`, `publish_status` | operational truth | pack/publish controller path | explicit pack/publish persistence | worker, skills, presenters | optional artifacts must not downgrade a completed main deliverable |
| deliverable artifact truth | `raw_path`, `origin_srt_path`, `mm_srt_path`, `vi.srt` storage keys, final video key/path/url | artifact truth | deliverable write path / repository persistence | service/controller after artifact validation | worker direct writes, skills, presenters | artifact truth answers “what exists” |
| freshness input snapshots | `subtitles_content_hash`, `subtitles_override_updated_at`, `dub_source_subtitles_content_hash`, `dub_source_subtitle_updated_at`, `dub_source_audio_fit_max_speed`, compose render signature/snapshots | truth inputs for derivation | service/controller for the relevant step | persisted together with accepted step outputs | worker direct writes, presenters | these are the facts used to derive stale/current judgments |
| authoritative target subtitle source | target subtitle key/path + selected target subtitle artifact | artifact truth | subtitle/service write path | accepted subtitle save/generation | worker direct writes, frontend-only state | target subtitle truth is not whatever the page is currently showing |
| helper side-channel facts | helper output state, helper provider health, helper input/output text, helper retryable failure evidence | derived side-channel facts | subtitle/service + presenter-safe derivation | helper execution result and projection-safe derivation | helper path rewriting mainline subtitle/audio truth | helper facts may explain current blocking subtitle formation, but they do not outrank authoritative current subtitle/audio truth |
| ready gate fields | `ready_gate.compose_ready`, `ready_gate.publish_ready`, `ready_gate.blocking`, `ready_gate.*_reason` | derived | status policy / ready gate engine | computed from task + state facts | worker, skills, frontend manual writes | derived authority for readiness; should be consumed by board/workbench/publish |
| stale/currentness fields | `target_subtitle_current`, `target_subtitle_current_reason`, `dub_current`, `audio_ready`, `audio_ready_reason`, `final_stale_reason`, `composed_ready` | derived | status policy / freshness evaluators | computed from artifact truth + freshness inputs | worker, skills, presenters | may be cached on task for compatibility, but ownership stays derived |
| board/workbench/publish labels | `filter_status`, chips, CTA enabled flags, badge text, summary rows | display-only | presenter / route assembly / frontend | computed at presentation time | worker, skills, repo direct writes | must not be written back as truth |

## 4. Hot Follow-Specific Interpretation

### 4.1 Main Deliverable Truth

For Hot Follow, the main completion judgment must come from:

- final deliverable existence/freshness
- current dub truth when dub is required
- current target subtitle truth
- ready gate output

It must not come from:

- raw `status=processing`
- optional pack/scenes pending
- stale compatibility fields without freshness evaluation

### 4.2 Subtitles / Dub / Compose

Hot Follow needs these distinctions to stay explicit:

- subtitle artifact truth is not the same as subtitle currentness
- dub artifact truth is not the same as dub currentness
- compose success is not the same as final freshness

That is why:

- `dub_status=done` may still coexist with `audio_ready=false`
- final video existence may still coexist with `final_fresh=false`
- board/workbench must prefer derived currentness over stale step status when showing main completion

## 5. Hard Prohibitions

Skills Runtime must not directly write:

- repo truth
- deliverable truth
- asset sink truth
- final status / ready gate truth

Worker Gateway must not directly write:

- repo truth
- final deliverable truth
- publish truth

Frontend must not directly author:

- any persisted truth field
- ready gate fields
- currentness truth

## 6. Why This Matrix Matters For `tasks.py` Decomposition

`tasks.py` currently mixes:

- HTTP transport
- orchestration
- truth writes
- derived currentness compatibility updates
- view-facing projection

This matrix freezes the intended separation before code moves:

- state write path owns operational truth
- service/deliverable write path owns artifact truth
- status policy owns derived readiness/currentness
- presenters own display-only projection

## Recovery Clarification

For the tag-derived Hot Follow recovery branch:

- stale `no_dub` skip markers are historical operational truth only until the
  current subtitle/audio reducer confirms they still apply
- top-level `errors` are L4 projection-only outputs and must clear when L2/L3
  truth is recovered
- helper provider failure is side-channel evidence unless helper output absence
  is the live blocking subtitle truth
