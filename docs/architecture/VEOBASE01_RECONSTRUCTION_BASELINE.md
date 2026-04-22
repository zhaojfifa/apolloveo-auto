# VeoBase01 Reconstruction Baseline

## Purpose

VeoBase01 is the reconstruction baseline branch for ApolloVeo v1.9 stabilization toward the 2.0 factory architecture.

This branch aligns code and docs around explicit production-line, state, contract, and skill boundaries while preserving the current Hot Follow business line.

`docs/ENGINEERING_INDEX.md` is the mandatory engineering entry point for every VeoBase01 PR. Root governance remains the highest authority, and this baseline document must be read through the task-oriented paths defined in the index.

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

### Worker Profile Boundary

Worker profile selects execution resources and providers. Worker execution can return artifacts and structured results, but persisted truth is accepted by the owning service/controller.

### Deliverable Profile Boundary

Deliverable profile defines primary, secondary, and optional deliverables. For Hot Follow, final video is primary; target subtitle and audio are secondary; packs are optional.

### Asset Sink Boundary

Asset sink is downstream of accepted deliverable truth. Workers and presenters must not directly promote artifacts into canonical asset truth.

## Reconstruction Priorities

P0:

- four-layer state contract
- workbench response contract
- status ownership matrix
- line contract runtime consumption path

PR-2 freezes the first executable typed workbench response model:

- `gateway/app/services/contracts/hot_follow_workbench.py`

The model is Hot Follow-first. It validates the current wire payload without renaming fields so the existing business path and UI contract remain stable.

P1:

- service extraction for router burden reduction
- skills boundary loader/stub
- deliverable profile / worker profile explicit references

P2:

- new-line onboarding preparation only after VeoBase01 baseline is stable

## Non-Goals

- Do not implement a second production line.
- Do not restart PR-4 / PR-5 as previously scoped branches.
- Do not redesign business features first.
- Do not alter working translation, dub, or compose behavior unless required for structural extraction.
- Do not merge back to `main` until validation is complete.

## Minimal Glossary

| Term | Frozen VeoBase01 Meaning |
| --- | --- |
| Production Line | A business execution line that produces a target result under an explicit line contract. |
| Production Agent | Runtime assembly of line contract, SOP, skills, worker profile, deliverable profile, and asset sink policy for a line job. |
| SOP Profile | The standard operating procedure for a line: ordered stages, retry rules, operator checkpoints, and publish confirmation rules. |
| Skills Bundle | A line-scoped bundle of advisory/routing/content skills that reads facts and returns suggestions, not truth writes. |
| Worker Profile | Execution-provider policy for model/API/local workers used by the line. |
| Deliverable Profile | Declaration of primary, secondary, and optional outputs and their acceptance rules. |
| Asset Sink Profile | Policy for downstream asset-library sinking after deliverables are accepted. |
| Smart Pack | A structured package of accepted line artifacts plus metadata for reuse, review, or delivery. |
| Job | A submitted unit of production work. |
| Task | The persisted execution record backing a job in the current runtime. |
| Line Job | A task interpreted through a specific production line contract. |
