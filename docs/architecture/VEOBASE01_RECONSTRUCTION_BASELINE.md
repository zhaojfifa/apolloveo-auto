# VeoBase01 Reconstruction Baseline

## Purpose

VeoBase01 is the reconstruction baseline branch for ApolloVeo v1.9 stabilization toward the 2.0 factory architecture.

This branch aligns code and docs around explicit production-line, state, contract, and skill boundaries while preserving the current Hot Follow business line.

From PR-4 onward, every VeoBase01 PR must read both required entry files before implementation:

- `ENGINEERING_CONSTRAINTS_INDEX.md`: root-level engineering authority for how engineering work must be done.
- `docs/ENGINEERING_INDEX.md`: docs-level business/runtime/contract navigation for how line, state, contract, skill, and architecture work must be understood.

For documentation placement and structure, read `docs/README.md`. For shared file logic and architecture-sharing logic, read `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`.

Root governance remains the highest authority, and this baseline document must be read through the task-oriented paths defined in the docs-level index.

## Baseline Evidence

The branch starts from `main` at:

- `6a2caa764245cd722a6519320a93c9f04573cb14`

Current business evidence:

- URL task `c084b276e819`: parse, subtitles, dub, compose, final, compose-ready, and publish-ready are working.
- Local task `8501fc94c1c8`: parse, subtitles, dub, and `tts_voiceover_plus_source_audio` path are working.

## Design Target

ApolloVeo moves toward:

```text
Production Line =
  Line Contract
  + SOP Profile
  + Skills Bundle
  + Worker Profile
  + Deliverable Profile
  + Asset Sink Profile
```

The state model is explicitly four-layer:

- L1 pipeline step status
- L2 artifact facts
- L3 current attempt / runtime resolution
- L4 ready gate / presenter / advisory

## Top-Level Architecture Surfaces

### Production Line Contract

The production line contract defines line identity, task kind, input contract, SOP profile, skills bundle, worker profile, deliverable profile, asset sink profile, status policy, and ready gate reference.

VeoBase01 freezes Hot Follow as the first reconstruction line. It does not introduce a second line.

### Ready Gate / State Contract

Ready gate is derived state. It consumes L1/L2/L3 facts and returns readiness, blocking reasons, and publish/compose eligibility. It does not write business truth.

### Skills Bundle Boundary

Skills consume line facts and produce advisory or routing suggestions. They do not write repository truth, deliverable truth, ready gate truth, or asset sink truth.

PR-4 freezes the Hot Follow skills bundle as a runtime-consumed reference. The line binding path loads `skills/hot_follow` through the skills runtime loader and exposes the consumed bundle under `line.runtime_refs.skills_bundle`.

### Worker Profile Boundary

Worker profile selects execution resources and providers. Worker execution can return artifacts and structured results, but persisted truth is accepted by the owning service/controller.

PR-4 exposes `worker_profile_ref` as a runtime-bound reference so the active line payload can prove which worker profile contract is in force without changing worker execution behavior.

### Deliverable Profile Boundary

Deliverable profile defines primary, secondary, and optional deliverables. For Hot Follow, final video is primary; target subtitle and audio are secondary; packs are optional.

PR-4 consumes `deliverable_profile_ref` by reading the Hot Follow line contract YAML and exposing primary and secondary deliverable kinds as read-only runtime metadata.

### Asset Sink Boundary

Asset sink is downstream of accepted deliverable truth. Workers and presenters must not directly promote artifacts into canonical asset truth.

PR-4 exposes `asset_sink_profile_ref` and the line sink policy flag as runtime-bound metadata. This does not authorize skills, workers, or presenters to promote sink truth.

## Reconstruction Priorities

P0:

- four-layer state contract
- workbench response contract
- status ownership matrix
- line contract runtime consumption path

PR-4 completes the next narrow runtime consumption step for Hot Follow by resolving and exposing:

- line registry binding
- skills bundle reference
- worker profile reference
- deliverable profile reference
- asset sink profile reference

These references are consumed through `gateway/app/services/line_binding_service.py` and surfaced as `line.runtime_refs`. They remain read-only contract metadata and do not change translation, dub, compose, helper translation, or ready gate semantics.

PR-2 freezes the first executable typed workbench response model:

- `gateway/app/services/contracts/hot_follow_workbench.py`

The model is Hot Follow-first. It validates the current wire payload without renaming fields so the existing business path and UI contract remain stable.

## Sequential Phase Order

VeoBase01 now follows a frozen sequential strategy:

1. Phase 1: architecture closure
2. Phase 2: code-debt cleanup
3. Phase 3: new-line loading

These three phases must not run in parallel.

Reference decision note:

- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

## Phase Plan

### Phase 1 — Architecture Closure

Goal:

- finish VeoBase01 structural closure
- keep business baseline stable
- do not start new-line implementation

Focus:

1. line contract/runtime ref closure
2. skills / worker / deliverable / asset sink boundary freeze
3. four-layer state enforcement
4. workbench contract vs implementation alignment
5. task semantic convergence where still needed
6. docs/index/ADR/contract alignment

Acceptance:

- contracts no longer drift
- state layers are stable
- runtime refs are real, not ceremonial
- business baseline still passes

### Phase 2 — Code-Debt Cleanup

This phase may start only after Phase 1 passes.

Priority order:

1. `tasks.py`
2. `hot_follow_api.py`
3. `task_view.py`
4. `task_view_workbench_contract.py`

Goal:

- router thinning
- single-write ownership
- remove god-file behavior
- reduce compatibility residue
- no business behavior change

### Phase 3 — New-Line Loading

This phase may start only after Phase 1 and Phase 2 are both validated.

Allowed only then:

- new-line design continuation
- new-line minimum implementation
- multi-role harness introduction

P1 architecture closure slices:

- service extraction for router burden reduction
- skills boundary loader/stub
- deliverable profile / worker profile explicit references

P2 code-debt cleanup and post-closure structural thinning:

- router thinning after architecture closure passes
- compatibility residue reduction after architecture closure passes

P3 new-line loading:

- new-line onboarding preparation is already frozen by PR-5
- implementation remains blocked until architecture closure and code-debt
  cleanup are both stable

## Non-Goals

- Do not implement a second production line.
- Do not restart PR-4 / PR-5 as previously scoped branches.
- Do not redesign business features first.
- Do not alter working translation, dub, or compose behavior unless required for structural extraction.
- Do not merge back to `main` until validation is complete.
- Do not run architecture closure, code-debt cleanup, and new-line loading in parallel.

## Shared Preparation Freeze

PR-5 adds the minimum preparation surfaces required before any future line
onboarding can be reviewed:

- `docs/contracts/veobase01_glossary.md`
- `docs/contracts/new_line_onboarding_template.md`
- `docs/contracts/line_job_state_machine.md`
- `docs/contracts/skills_bundle_boundary.md`
- `docs/contracts/line_contract.example.yaml`
- `docs/contracts/worker_profile.example.yaml`
- `docs/contracts/deliverable_profile.example.yaml`
- `docs/contracts/asset_sink_profile.example.yaml`

These docs freeze vocabulary, lifecycle, and example profile shapes for future
design work only. They do not authorize second-line runtime implementation, do
not change workbench wire semantics, and do not rewrite ready-gate meaning.

Current gate result after PR-5:

- new-line design may continue
- new-line implementation remains blocked
- multi-role harness remains blocked

## Unified Glossary

The active shared terminology now lives in:

- `docs/contracts/veobase01_glossary.md`

That glossary supersedes the older inline glossary block here so VeoBase01 docs
and future onboarding packets use one vocabulary source.
