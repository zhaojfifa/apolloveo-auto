# ADR: VeoBase01 Line And State Contract Reconstruction

## Status

Accepted for `VeoBase01`.

## Context

Hot Follow is now stable enough to become the reconstruction baseline:

- URL task `c084b276e819` validates parse, subtitles, dub, compose, final, compose readiness, and publish readiness.
- Local task `8501fc94c1c8` validates parse, subtitles, dub, and `tts_voiceover_plus_source_audio`.

The system still carries architecture risk:

- routers carry too much orchestration burden
- status ownership is mixed with presentation and compatibility fields
- line contract metadata exists but is not yet the full runtime backbone
- workbench response shape is not sufficiently typed
- service boundaries need extraction without business regression

## Decision

Use `VeoBase01` as the reconstruction baseline branch.

The reconstruction target is:

```text
Production Line =
  Line Contract
  + SOP Profile
  + Skills Bundle
  + Worker Profile
  + Deliverable Profile
  + Asset Sink Profile
```

State boundaries are frozen as:

- L1 pipeline step status
- L2 artifact facts
- L3 current attempt / runtime resolution
- L4 ready gate / presenter / advisory

## Constraints

- Do not implement a second production line.
- Do not restart PR-4 / PR-5 as previously scoped branches.
- Do not redesign business features first.
- Do not touch working translation, dub, or compose behavior unless required for structural extraction.
- Every structural change must preserve the Hot Follow business line.

## Consequences

VeoBase01 PRs must update code and docs together.

Structural extraction order:

1. freeze contracts
2. bind existing runtime reads to explicit contracts
3. reduce router burden
4. extract service ownership
5. validate URL and local-upload business paths

No merge back to `main` is allowed until live business validation is complete.
