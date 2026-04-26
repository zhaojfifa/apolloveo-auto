# Hot Follow State Commit Contract v1

Date: 2026-04-26
Status: active repair contract for URL state instability

## Purpose

This contract freezes the minimum state-commit order for the Hot Follow URL
instability class. It does not introduce a new line, provider behavior, UI
model, or factory abstraction.

The required order is:

1. authoritative subtitle commit
2. route reducer
3. recovered-error scrub
4. projection / presentation

No route, ready-gate, or presentation consumer may treat a visible intermediate
target subtitle text as complete authoritative subtitle truth before the commit
phase has finished.

## A. Authoritative Subtitle Commit Phase

Authoritative target subtitle truth may become externally visible only after all
of the following are true:

- target subtitle text is persisted
- target subtitle artifact is persisted
- currentness and source match are validated
- `target_subtitle_current=true`
- `target_subtitle_authoritative_source=true`

`edited_text` / `srt_text` presence alone is not authoritative subtitle truth.
Those fields may expose candidate or editable text, but L2 subtitle truth still
requires the artifact/source/currentness checks above.

## B. Route Reducer Phase

`selected_compose_route` may only be reduced from post-commit L2 truth.

Old `no_dub` / `no_tts` residue from `target_subtitle_empty` or
`dub_input_empty` may not override recovered subtitle truth. If candidate target
subtitle text is visible but authoritative subtitle commit is not complete yet,
the route must remain waiting/intermediate and must not project
`no_tts_compose_route` or `no_dub_route_terminal` unless explicit non-stale
contract facts still require that terminal route.

## C. Recovered-Error Scrub Phase

When L2/L3 has recovered, stale subtitle/helper residue must be cleared before
projection. Recovery is established when:

- subtitle status is done/ready
- `subtitle_ready=true`
- `target_subtitle_current=true`
- `target_subtitle_authoritative_source=true`

The scrub must clear visible stale residue for:

- `subtitles_error`
- `subtitles.error`
- helper failure alias
- stale `no_dub` / `no_tts` terminal residue
- recovered top-level residue derived from `subtitle_missing`

Historical events may remain in event history, but they may not shape current
route, ready-gate, or L4 presentation after recovery.

## D. Projection Phase

L4 workbench, publish, operator summary, advisory, and compatibility aliases may
only consume post-commit, post-scrub truth. L4 may explain current truth; it may
not recreate stale helper/subtitle failures once L2/L3 has recovered.

