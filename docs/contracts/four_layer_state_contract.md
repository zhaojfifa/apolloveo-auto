# Four-Layer State Contract

Date: 2026-04-22
Status: Canonical authority

## Purpose

This document is the canonical four-layer state authority for VeoBase01.

It freezes the layer meanings used by Hot Follow and by future line work so
state/projection/runtime changes do not collapse artifact truth, attempt truth,
and presentation truth back into one compatibility layer.

This contract is complemented by:

- `docs/contracts/status_ownership_matrix.md`
  - ownership and write-path authority
- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
  - reusable template/fallback reference for future line or schema drafting

The template is not the primary authority when this contract exists.

## Canonical Layer Model

- L1 = Pipeline Step Status
- L2 = Artifact Facts
- L3 = Current Attempt
- L4 = Ready Gate / Operator Summary / Advisory / Presentation

## Layer Definitions

### L1 Pipeline Step Status

L1 records execution status only.

Examples:

- `parse_status`
- `subtitles_status`
- `dub_status`
- `compose_status`
- `pack_status`
- `publish_status`
- `last_step`

L1 does not prove business correctness by itself.

### L2 Artifact Facts

L2 records what artifacts currently exist and the factual metadata used to judge
freshness.

Examples:

- raw/source artifact existence
- target subtitle artifact existence
- current audio artifact existence
- current final artifact existence
- scene-pack artifact existence
- content hashes, `updated_at`, `sha256`, asset version

L2 answers what exists, not whether it is the current valid business outcome.

### L3 Current Attempt

L3 interprets whether the current subtitle/audio/final path is current and
actionable.

Examples:

- `audio_ready`
- `audio_ready_reason`
- `dub_current`
- `dub_current_reason`
- `compose_input_ready`
- `compose_execute_allowed`
- selected compose route
- `requires_redub`
- `requires_recompose`
- `final_stale_reason`

L3 is derived from L1 + L2 facts and runtime resolution logic.

### L4 Ready Gate / Operator Summary / Advisory / Presentation

L4 exposes presentation-safe outputs derived from L2/L3.

Examples:

- `ready_gate`
- `operator_summary`
- `advisory`
- workbench surface payload
- publish surface payload
- task-detail presentation

L4 must consume L2/L3 truth and must not create or override it.

## Hard Rules

1. Surfaces consume L2/L3-derived truth.
2. Presenters must not invent truth.
3. Compatibility fallback must not override valid final, subtitle, or audio
   artifact truth.
4. Contract adapters must not mutate authoritative projection after ready-gate
   computation.
5. `final.exists` is not equivalent to `final.fresh`.
6. Historical output must not satisfy current-ready truth when current freshness
   is false.

## Hot Follow-Specific Dominance Rules

For Hot Follow:

- current fresh final + current-attempt readiness dominates publish/workbench
  truth
- helper translation may support subtitle generation but must not override valid
  authoritative target subtitle truth
- scene-pack pending may remain visible but is non-blocking once the final is
  fresh and publishable

## Canonical Interpretation By Layer

| Layer | Authority question | Owned by |
| --- | --- | --- |
| L1 | What step ran and what was its execution status? | execution/controller path |
| L2 | What artifacts and freshness inputs exist? | artifact/service truth path |
| L3 | Is the current attempt ready/current/stale/blocked? | status policy / route resolution / freshness evaluation |
| L4 | What should operators or surfaces see? | presenter / contract adapter / UI-safe aggregation |

## Required Reading Pairing

When work touches state, projection, or readiness:

1. read this contract
2. read `docs/contracts/status_ownership_matrix.md`
3. read the active line/runtime contracts

Use `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md` only as a drafting
template or fallback reference when creating future generalized schema work.
