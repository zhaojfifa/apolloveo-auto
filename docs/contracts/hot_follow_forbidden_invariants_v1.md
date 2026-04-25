# Hot Follow Forbidden Invariants v1

Date: 2026-04-25
Status: Frozen docs-only authority packet

## Purpose

This document freezes contradictory Hot Follow state shapes that must never
exist.

These invariants are derived from observed regression classes already discussed
on the `VeoBase02-clean-tag-verify` baseline:

- clean success / closure shape
- early `no_tts` premature terminalization shape
- translation waiting retryable shape
- helper warning-only successful shape
- contradictory split shape

## Global Rule

If any invariant below is violated, the shape is contract-invalid even if one
surface still appears usable.

## Forbidden Invariants

### HF-FI-01 Subtitle Done Without Subtitle Ready

Forbidden shape:

- `subtitles.status=done`
- `subtitle_ready=false`

unless the state is explicitly a post-step stale/currentness mismatch under a
named non-ready state such as `translation_waiting_retryable`.

Required interpretation:

- step completion alone is insufficient
- L4 must not present subtitle success when L3 says subtitle currentness is
  false

### HF-FI-02 Subtitle Authority Split Against Missing-Authority Surface

Forbidden shape:

- `target_subtitle_current=true`
- `target_subtitle_authoritative_source=true`
- any surface still reports missing authority, missing current subtitle, or
  equivalent subtitle-not-ready authority wording

Required interpretation:

- once authority and currentness are both true, all surfaces must clear the
  missing-authority projection

### HF-FI-03 Audio Done While Audio Error Persists

Forbidden shape:

- `audio.status=done`
- `audio_ready=true`
- top-level audio error remains populated

Required interpretation:

- when current audio truth is recovered, stale top-level audio error projection
  must clear

### HF-FI-04 Compose Route Split Across Truth Owners

Forbidden shape:

- `artifact_facts.selected_compose_route` disagrees with
  `current_attempt.selected_compose_route`
- or either disagrees with the route assumed by `ready_gate`

Required interpretation:

- selected compose route is one current-attempt decision path
- artifact facts, current attempt, and ready gate may reflect it in different
  shapes, but they must not disagree

### HF-FI-05 Helper Failure Overrides Mainline Success

Forbidden shape:

- helper side-channel failure is present
- authoritative target subtitle, current audio, or current final is already
  ready
- helper failure still downgrades mainline route, ready gate, or publish truth

Required interpretation:

- helper failure becomes warning/advisory only after mainline success exists

### HF-FI-06 History Residue Drives Current Truth

Forbidden shape:

- stale historical events such as `target_subtitle_empty` or `dub_input_empty`
  remain in history
- current subtitle/audio/final truth is already recovered
- historical residue still drives current `no_dub`, terminal-route, or
  readiness projection

Required interpretation:

- event history may remain visible
- it may not remain the source of current truth

### HF-FI-07 Subtitle Waiting Projected As Terminal No-Dub / No-TTS

Forbidden shape:

- current state is subtitle waiting, translation incomplete, or helper
  retryable failure
- route is still expected to continue through subtitle or TTS completion
- any surface projects terminal `no_tts` / `no_dub` route truth

Required interpretation:

- waiting/retryable subtitle shapes stay on the mainline route family unless
  explicit no-dub/no-TTS contract facts are satisfied

### HF-FI-08 Helper Null-State Ambiguity

Forbidden shape:

- helper path is relevant to the current task shape
- helper state is represented as implicit null/unknown/no-field ambiguity

Required interpretation:

- helper path must be one explicit state family:
  - waiting
  - retryable warning
  - resolved with warning
  - irrelevant to current mainline truth

### HF-FI-09 Final Ready With Stale Historical Substitution

Forbidden shape:

- `final_ready` or `publish_ready` is projected
- only historical final exists, or current final is stale

Required interpretation:

- historical final may be shown
- it must not satisfy current-ready truth

### HF-FI-10 Publish Ready Downgraded By Scene-Pack Residue

Forbidden shape:

- current final is fresh
- current attempt is ready
- publish-ready conditions are satisfied
- scene-pack pending or failed residue downgrades publish readiness

Required interpretation:

- scene-pack residue is advisory only once current publish truth is satisfied

### HF-FI-11 No-Dub / No-TTS Without Explicit Boundary Facts

Forbidden shape:

- route is projected as `preserve_source_route`, `bgm_only_route`, or
  `no_tts_compose_route`
- explicit no-dub/no-TTS allowance facts are absent from the current L2/L3
  shape

Required interpretation:

- preserve policy alone is insufficient
- translation-incomplete or helper-failed voice-led shapes do not silently
  convert into legal no-dub terminal states

### HF-FI-12 Terminal Failure And Retryable Warning At The Same Time

Forbidden shape:

- a state is presented as terminal failed
- the same current path is also presented as retryable warning-only

Required interpretation:

- current path must resolve to one of:
  - retryable non-terminal
  - manual-intervention non-terminal
  - terminal failed

## Invariant Families By Observed Regression Class

| Observed class | Frozen invariant family |
| --- | --- |
| clean success / closure shape | HF-FI-02, HF-FI-03, HF-FI-09, HF-FI-10 |
| early `no_tts` premature terminalization shape | HF-FI-07, HF-FI-11 |
| translation waiting retryable shape | HF-FI-01, HF-FI-07, HF-FI-12 |
| helper warning-only successful shape | HF-FI-05, HF-FI-08 |
| contradictory split shape | HF-FI-02, HF-FI-03, HF-FI-04, HF-FI-06 |

## Review Outcome

After this freeze:

- contradictory Hot Follow shapes are explicitly named
- helper, history, route, subtitle, audio, and final contradictions are
  separated
- the next runtime-enforcement pass has a frozen forbidden-invariants set to
  implement against
