# State Schema Four-Layer Template

## Purpose

Provide a reusable, production-line-agnostic state model for building reliable operator workflows (Save Subtitle, Re-dub, Re-compose, Publish, etc.) while preventing “existence-based correctness” and avoiding ambiguity between current output and historical outputs.

This document is a platform skill: it defines how to model, persist, derive, and project state across services and UIs.

## Scope

Applies to any production line that:

- Has authoritative inputs that can be edited over time (subtitle, script, prompt, source link, scene plan, avatar config, localization glossary, etc.).
- Runs multi-step attempts (dub, compose, render, pack, QC, publish).
- Exposes “ready” gates to operators and automation.
- Needs repeatable cycles (2nd, 3rd, Nth edits and re-runs) without confusing old outputs for current ones.

## Core Principles

- Authoritative inputs are explicitly defined and versioned; everything else is derived or cached.
- Execution facts (a file exists, a job ran) are never equal to business readiness.
- “Current output” is a semantic object: it must be proven fresh against current authoritative inputs.
- Historical outputs are reference-only unless explicitly selected as fallback.
- Gates/UI must bind to derived/projection state, not to raw artifact existence.
- Every successful output must persist the exact input snapshot it used (lineage), so freshness is auditable and computable.

## Four-Layer State Model

This is the canonical decomposition:

### 1) Object State (Authority Layer)

The persistent, authoritative objects and configs for the task/asset.

Typical examples:

- Authoritative input artifacts: `mm.srt` (saved target subtitle), script JSON, scene plan YAML.
- Operator editable metadata: `source_url`, `title`, `notes`.
- Long-lived configs: voice config, compose config, render config, publish config.

Rules:

- Only explicitly defined artifacts are authoritative.
- Authority must not be inferred from “latest modified file in storage”.
- Authority must have a stable identifier and revision semantics.

Recommended fields (examples, not exhaustive):

- `subtitles_content_hash`
- `subtitles_override_updated_at` (timestamp of the saved authoritative override)
- `audio_sha256` (for current dub output)
- `dub_generated_at`
- `source_url` (editable metadata; does not affect freshness)

### 2) Attempt State (Execution Layer)

The mutable record of what the system is currently trying to do or recently attempted.

Typical examples:

- `current_attempt` (compose attempt, dub attempt, publish attempt)
- `last_attempt` history
- per-step statuses and errors

Rules:

- Attempt state is about execution, not correctness.
- Attempt success does not imply the output is current; it only implies it succeeded for the inputs it used.
- Attempt records must capture input snapshot identity at start or at completion (see Freshness Model).

Recommended fields (examples):

- `compose_status` (`pending|running|done|failed`)
- `compose_last_started_at`
- `compose_last_finished_at`
- `compose_error`

### 3) Derived State (Business Semantics Layer)

Pure, deterministic computations over Object State + Attempt State + persisted snapshots. This layer answers:

- Is the current output fresh for the current authoritative inputs?
- If not, why is it stale?
- What actions are required next?

Rules:

- Derived state must be recomputable from stored facts.
- Derived state must be monotonic with respect to authority changes: when authoritative inputs change, freshness must invalidate immediately.
- Derived state must be stable across API endpoints and UI surfaces.

Recommended derived fields:

- `final_fresh` (boolean)
- `final_stale_reason` (enum/string)
- `requires_recompose` (boolean)
- `compose_ready` (boolean, meaning “compose can be run now”)
- `publish_ready` (boolean, meaning “safe to publish now”)

### 4) Projection State (API/Hub/Workbench Layer)

The user-facing and integration-facing representation. This layer shapes derived state into:

- deliverables (`final`, `pack`, etc.)
- UI cards (“Final Video”, “Compose Needed”)
- hub summary lists and task detail payloads

Rules:

- Projections must not silently re-interpret semantics.
- Projections must not downgrade freshness semantics into existence semantics.
- Projections may include convenience booleans, but they must be derived from Layer 3, not invented.

## Standard State Propagation Chain

A reliable production line follows this chain:

1. Operator updates authoritative inputs (Layer 1).
2. System persists updated authority revision identity (hash + timestamp).
3. Derived state invalidates any dependent outputs immediately (Layer 3).
4. Operator triggers a new attempt (Layer 2).
5. Execution reads only authoritative inputs and current configs (Layer 1).
6. On success, execution persists an output plus an input snapshot (lineage) (Layer 2/1).
7. Derived state recomputes freshness using snapshot identity (Layer 3).
8. Projection exposes “current output” only when freshness is true; otherwise it exposes “historical output” only for reference/fallback (Layer 4).

## Current Output vs Historical Output

Define two distinct concepts:

- **Current output**: the effective output for “what the task means right now”. It is only valid when `final_fresh=true`.
- **Historical output**: any prior successful output, useful for fallback, auditing, or comparison. It is not current by default.

Rules:

- Current and historical must not default to pointing to the same artifact object.
- If a backward-compat field must exist, it should not mirror current output unless it is truly distinct.
- File existence is a storage fact; it is not a semantic indicator of “current output”.

Projection guidelines:

- `final`: only current effective output (fresh).
- `historical_final`: only distinct previous outputs, or fallback output when current is unavailable/failed/stale.

## Freshness Model

Freshness is a lineage check: compare the current authoritative input revision identity to the snapshot identity used to produce the current output.

### Snapshot Fields (Lineage)

Each successful compose/publish must persist the snapshot of inputs it used, at minimum:

- `final_source_audio_sha256`
- `final_source_dub_generated_at` (or dub revision id)
- `final_source_subtitles_content_hash`
- `final_source_subtitle_updated_at`
- `final_updated_at` (output production time)

For other lines, analogous fields apply (script hash, scene plan hash, avatar config hash, localization glossary hash, etc.).

### Stale Rules (Generic)

Mark current output stale if any of the following is true:

- `audio_sha256 != final_source_audio_sha256`
- `subtitles_content_hash != final_source_subtitles_content_hash`
- `dub_generated_at > compose_last_finished_at` (when timestamps are reliable)
- `subtitles_override_updated_at > compose_last_finished_at`

Notes:

- Prefer content hashes for correctness; timestamps are often useful secondary checks.
- “Authority update invalidates output” must apply repeatedly (Nth cycles) without special-case logic.
- Never treat “compose_status=done” as “fresh”; it is only “done for that attempt”.

## Gate Model (Compose/Publish/UI)

Gates should be derived, not inferred:

- `compose_ready`: prerequisites satisfied (authoritative subtitle exists, current dub exists, configs valid).
- `requires_recompose`: authoritative inputs changed since last compose snapshot.
- `composed_ready`: current final exists and is fresh (a stronger condition than “final exists”).
- `publish_ready`: only true when the current output is fresh and any additional publish constraints pass.

UI binding rules:

- Button enablement must bind to `compose_ready` + `requires_recompose`, not to `final.exists`.
- Any view that shows a “final video” must prefer current output; historical output should be clearly labeled as fallback/reference.

## Naming Suggestions

Prefer consistent prefixes to reduce ambiguity:

- `*_content_hash` for authoritative content identity
- `*_updated_at` for authoritative revision time
- `*_sha256` for binary artifacts
- `*_generated_at` for outputs created by a step
- `*_source_*` for snapshot fields captured at output time
- `current_*` for the effective revision used for future steps
- `historical_*` for prior outputs

Avoid names that blur semantics:

- Avoid treating `*_exists` as a readiness signal.
- Avoid using a single `final` object for both “current” and “historical fallback”.

## Cross-Line Applicability

This template generalizes directly to:

- Localization: glossary/script/subtitle authority, dubbing attempts, localization compose, publish gates.
- Avatar / Swap: avatar config authority, render attempts, compositing, output freshness.
- Scene Pack: scene plan authority, pack build attempts, pack deliverables, freshness against scene plan.
- Publish Hub: publish config authority, publish attempts, publish-ready gates, current vs historical publication artifacts.

Any line with operator edits and re-runs benefits from:

- explicit authority definitions
- persisted input snapshots
- derived freshness semantics
- projection discipline

## Architectural Implications

This schema supports platform refactors and multi-service evolution:

- Ports/Adapters: keep Layer 3 derivations in a stable domain module; adapters fetch/persist Layer 1/2 facts.
- Lineage-first design: snapshots make outputs auditable and enable reliable caching.
- Aggregation stability: hub/task detail endpoints should be thin projections over a single derivation source-of-truth.
- Testing discipline: state transitions become testable without UI coupling.

## Usage Checklist

Use this checklist when designing or reviewing a new line or workflow:

- Define authoritative inputs explicitly and store revision identity (hash + updated_at).
- Ensure each attempt reads only authoritative inputs and configs.
- Persist snapshot identity on each successful output (source hashes, source updated_at).
- Implement freshness as lineage comparison, not as file existence.
- Derive `requires_*` and gate booleans from freshness and prerequisites.
- Ensure projections expose current output only when fresh; historical output only when distinct or fallback.
- Bind UI enablement and readiness labels to derived/projection state, not raw artifacts.
- Add repeated-cycle tests (2nd/3rd/Nth edit + re-run) to prevent regression.

## One-Sentence Summary

Model production workflows with authoritative object revisions, attempt execution facts, derived freshness semantics, and disciplined projections so operators always act on the current output, not merely on existing artifacts.

