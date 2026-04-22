# Contract-Driven Four-Layer State Baseline v1

Date: 2026-04-23
Status: Rules-first baseline

## Purpose

This document freezes the contract-driven state baseline for future work.

It defines four state layers with explicit precedence so publish/workbench drift
cannot re-enter through compatibility fields or local surface logic.

## State Layers

### S1 — Step Execution State

S1 records what execution steps ran and how they ended.

Examples:

- parse status
- subtitles status
- dub status
- compose status
- pack status
- publish status

S1 answers what execution happened. It does not, by itself, answer whether the
current business output is fresh or publishable.

### S2 — Artifact Fact State

S2 records factual existence and factual metadata of artifacts.

Examples:

- final exists / fresh
- subtitle exists
- audio exists
- compose input exists / ready as factual input evidence
- pack / scenes / manifest existence

S2 is factual state. It must not be backfilled from surface wording.

### S3 — Current Attempt State

S3 interprets currentness and attempt readiness from S1 + S2.

Examples:

- `compose_status`
- `compose_reason`
- `audio_ready`
- `dub_current`
- `requires_recompose`
- `requires_redub`
- `current_subtitle_source`

S3 may interpret currentness, but it may not rewrite artifact truth.

### S4 — Presentation / Interpretation State

S4 exposes surface-safe derived outputs.

Examples:

- `ready_gate`
- `advisory`
- `operator_summary`
- publish presentation
- workbench presentation

S4 may consume S2/S3 but may not override them.

## Hard Rules

1. S4 may consume S2/S3 but may not override them.
2. S3 may interpret currentness but may not rewrite artifact truth.
3. S2 may not be backfilled from surface text.
4. Compatibility fields must not override S2/S3.
5. Scene-pack pending may be non-blocking when final-ready publish truth is
   already established.
6. `final_exists + current_attempt ready` must dominate publish presentation
   truth.

## Precedence Table

| Question | Winning layer | Losing layer if conflict exists |
| --- | --- | --- |
| Did the compose step run? | S1 | S4 presentation shorthand |
| Does the current final artifact exist? | S2 | S4 labels or missing legacy aliases |
| Is the current audio/subtitle/final path ready now? | S3 | S1 done-like step status alone |
| Should publish/workbench show ready? | S4 derived from S2/S3 | compatibility-only surface fields |
| Can historical final satisfy current-ready truth? | S2/S3 freshness logic | S4 convenience fallback |

## Blocking vs Non-Blocking Table

| Condition | Class | Reason |
| --- | --- | --- |
| final absent while compose still in progress | blocking | current output not ready |
| audio route requires TTS but `audio_ready=false` | blocking | current attempt not ready |
| compose input derivation failed | blocking | current attempt terminally blocked |
| final exists but is stale against current inputs | blocking | current output not current |
| scene-pack pending while current final is fresh and publishable | non-blocking | advisory only |
| helper translation failure after authoritative target subtitle is valid | non-blocking | support lane failure must not override main subtitle truth |

## Known Contradiction Class Example

Hot Follow regression class:

- workbench showed `final.exists=true`, `compose_status=done`,
  `audio_ready=true`, `publish_ready=true`
- publish simultaneously showed `final.exists=true` but
  `composed_ready=false`, `compose_status=pending`, and false blockers such as
  `voiceover_missing` and `audio_not_ready`

What caused it:

- S4 publish presentation was reading a stale compatibility path instead of the
  same S2/S3-derived projection path used by workbench

What rule prevents it now:

- S4 must consume the shared authoritative projection path
- compatibility fields may not override S2/S3 truth
- `final_exists + current_attempt ready` dominates publish presentation truth

## Minimal Interpretation Sequence

1. Read S1 execution state.
2. Read S2 artifact facts.
3. Derive S3 current-attempt readiness/currentness.
4. Build S4 ready gate, advisory, and surface presentation from S2/S3 only.

## How This Reduces Silicon-Parallel Drift

- It gives state work a fixed precedence model instead of letting each surface
  invent its own fallback ordering.
- It separates factual artifact state from current-attempt interpretation, which
  makes stale/current contradictions easier to detect and harder to reintroduce.
- It gives future scenario onboarding a stable rule baseline before any new line
  or scenario logic is discussed.
