# Hot Follow Business Flow Freeze v1

Date: 2026-04-30
Branch: `VeoBase02`
Status: flow definition freeze before further implementation

## Purpose

This document freezes the operator-understandable Hot Follow first-line flows before any further route/state implementation work. Code changes are frozen until these flows are reviewed and accepted.

## Flow A: URL Main Flow

Formal business flow:

```text
raw -> origin.srt -> target subtitle -> dub -> compose
```

Meaning:

- `raw` is the captured source video.
- `origin.srt` is the source subtitle artifact.
- `target subtitle` is the formal translated/current target subtitle artifact.
- `dub` consumes the current target subtitle.
- `compose` consumes formal current target subtitle plus current dub audio.

Business rules:

- `origin.srt` alone is not target subtitle closure.
- Dub cannot be current before target subtitle is authoritative/current.
- Compose cannot be ready before target subtitle and audio are both current.
- Helper translation may assist target subtitle creation, but helper state is not business truth.

## Flow B: Local Upload Operator Test Flow

Formal business flow:

```text
raw -> preserve_source_route -> compose
```

Meaning:

- This is an operator testing path for local uploads.
- It intentionally preserves source audio and skips the target-subtitle/dub dependency chain.
- It must remain visible as `preserve_source_route`, not disguised as failed or pending dubbing.

Business rules:

- Preserve-source route is valid when explicitly selected for local-upload testing.
- Preserve-source route does not imply target subtitle readiness.
- Preserve-source route does not imply dub readiness.
- Compose readiness in this path is based on the preserved-source route contract, not helper translation status.

## Flow C: Explicit Transition Action

Formal transition:

```text
local preserve-source test flow -> dubbing main flow
```

Target business flow after transition:

```text
raw -> origin.srt -> target subtitle -> dub -> compose
```

Required rule:

- The transition must be a formal operator action.
- Helper failure must not be the hidden owner or trigger for route switching.
- The action should make the operator intent explicit: leave preserve-source testing and enter subtitle/dub flow.

## Helper Rule

Helper translation is auxiliary only.

Allowed:

- provide draft translation
- show pending/unavailable/exhausted telemetry
- support manual target subtitle editing

Forbidden:

- own route switching
- own target subtitle truth
- block manual continuation by being failed/unavailable
- create readiness or closure facts

## Freeze Rule

Do not change Hot Follow state policy, route reducers, ready-gate behavior, advisory behavior, or surface projection again until this business-flow definition is accepted.
