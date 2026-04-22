# Four-Layer State Contract

## Purpose

VeoBase01 freezes the ApolloVeo state model into four explicit layers. The same model applies to Hot Follow first and must be reused for later production lines only after the Hot Follow baseline remains stable.

## L1: Pipeline Step Status

L1 records operational step status.

Examples:

- `subtitles_status`
- `dub_status`
- `compose_status`
- `publish_status`
- `last_step`
- coarse task `status`

Owners:

- controller/service write paths after step execution

Not owners:

- frontend
- skills
- presenters
- workers writing directly to repository truth

## L2: Artifact Facts

L2 records accepted physical artifact truth.

Examples:

- raw video key/path
- origin/source subtitle key
- target subtitle key such as `vi.srt`
- audio key such as `audio_vi.mp3`
- final video key/path/url
- object existence and object metadata

Owners:

- artifact/deliverable service write path
- storage-aware acceptance path after validation

Not owners:

- presenter
- ready gate
- skills

## L3: Current Attempt / Runtime Resolution

L3 derives whether current outputs are fresh for current authoritative inputs.

Examples:

- `target_subtitle_current`
- `dub_current`
- `audio_ready`
- `final_fresh`
- `requires_redub`
- `requires_recompose`
- selected compose route
- stale reason fields

Owners:

- status policy
- freshness/currentness evaluators
- runtime state assembly services

Rule:

L3 can be cached for compatibility but must remain derivable from L1/L2 and input snapshots.

## L4: Ready Gate / Presenter / Advisory

L4 is derived readiness and presentation.

Examples:

- `ready_gate.compose_ready`
- `ready_gate.publish_ready`
- ready gate blocking reasons
- deliverable rows
- operator summary
- advisory
- UI CTA enablement

Owners:

- ready gate engine
- presenter/view services
- skills advisory runtime for read-only guidance

Rule:

L4 must not write L1/L2/L3 truth.

## Cross-Layer Rules

1. A lower layer does not read from a higher layer as authority.
2. Presenters may consume all layers but write none.
3. Ready gate is derived, not persisted business truth.
4. Workers produce outputs; owning services accept or reject outputs.
5. Helper translation is auxiliary helper state, not target subtitle truth.
6. Semantic target subtitle validity must beat physical SRT existence.
7. Final availability must distinguish historical final from current fresh final.

## VeoBase01 Validation Rule

Any structural PR that changes one layer must include focused validation proving no split-brain with adjacent layers.
