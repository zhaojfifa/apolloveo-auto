# Hot Follow Rebuild Baseline Closeout

Status: Accepted baseline
Branch: `VeoReBuild01`
Baseline commit: `bae5939`
Suggested tag: `HotFollow-Rebuild-Baseline`

## Decision

Hot Follow rebuild on `VeoReBuild01` is accepted as the new baseline.

Hot Follow is now treated as a rebuilt baseline line, not a rescue line.

## Validated Business Paths

- URL main flow is validated: `raw -> origin.srt -> target subtitle -> dub -> compose`.
- Local preserve flow is validated: `raw -> preserve_source_route -> compose`.
- Preserve re-entry is validated: `preserve_source_route -> explicit route event -> subtitle/dub main flow`.

## Helper Translation

Helper translation is confirmed as backend capability testing and advisory support, not a blocker for the rebuilt line.

Helper input can materialize target subtitle and correctly force stale-final/recompose when subtitle truth changes.

## Scope Boundary

Remaining pack/scenes/BGM pending states are outside the current rebuild acceptance scope.

## Merge-To-Main Recommendation

Recommend merging `VeoReBuild01` to `main` as the Hot Follow rebuilt baseline.

The merge should preserve the Wave 0 contract docs, Wave 1 CurrentAttempt producer, Wave 2 L4 consumption alignment, and Wave 3 router shrink plus operational validation samples.

## Execution Reset

After merge/tag, resume parallel progress across the three production lines:

- Hot Follow: rebuilt baseline line.
- Matrix Script: production-line progress continues in parallel.
- Digital Anchor: production-line progress continues in parallel.
