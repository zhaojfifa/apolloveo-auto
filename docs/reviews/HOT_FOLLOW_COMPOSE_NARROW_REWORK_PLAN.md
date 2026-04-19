# Hot Follow Compose Narrow Rework Plan

Date: 2026-04-19

## Source Of Truth

- Rollback review: `docs/reviews/HOT_FOLLOW_COMPOSE_GUARD_ROLLBACK_REVIEW.md`
- Live service: `https://apolloveo.com`
- Live regression task: `fc45e93f83c3`

## Phase 1 Validation Summary

The live task proves that the reverted guard model was unsafe:

- `compose.preflight_status = blocked`
- `compose.preflight_reason = resolution_too_high`
- input probe: `720x1280`, approximately `2.7MB`, approximately `23.85s`, video bitrate approximately `778928`, sufficient free disk

This is a normal portrait shortvideo input. It must be baseline-safe and direct-allowed. The regression came from a height-only resolution rule, not from a real large-input resource risk.

The same task also proves presenter/SSOT divergence:

- `compose_allowed = false`
- `compose_allowed_reason = resolution_too_high`
- task/presenter state still carried compose-not-done / recompose-style messaging

## Rework Goals

1. Preserve baseline-safe portrait compose behavior.
2. Add only narrow large-input guardrails.
3. Ensure blocked inputs fast-fail before compose lock/running state.
4. Align presenter, ready-gate, advisory, task card, current attempt, and operator summary around the same blocked truth.

## Allowed Scope

### A. Preflight Classification

- Use orientation-aware or pixel-budget-aware input classification.
- Direct-allow normal portrait shortvideo inputs such as `720x1280` when size, duration, bitrate, and disk are safe.
- Do not block based on portrait height alone.
- Classify true heavy inputs by a combined constraint model:
  - file size
  - duration
  - pixel count / effective long-edge policy
  - bitrate
  - available disk
- Adapt large-but-allowed inputs only when the combined model says direct compose is risky.
- Block only inputs that exceed hard safety limits or cannot be processed with available local resources.

### B. Pre-Lock Blocked Fast-Fail

- Run the blocking portion of preflight before acquiring compose lock or writing `compose_status=running`.
- Blocked result must not create, refresh, or retain `compose_lock_until`.
- Repeated blocked compose clicks must return the same stable blocked state and must not return `409`.
- Reserve `409 compose_in_progress` only for real concurrent compose:
  - active persisted compose lock
  - in-memory compose lock acquisition conflict

### C. Presenter / Ready-Gate / Advisory Alignment

- Add compose input policy truth as one shared SSOT signal consumed by the workbench/presenter path.
- When blocked, propagate:
  - `compose_allowed=false`
  - stable blocked reason
  - human-readable blocked message
  - current attempt blocked state
- Suppress compose-ready or recompose advisory when the current blocker is compose input policy.
- Ensure task card, advisory, current attempt, operator summary, and compose action state agree.

## Required Tests

1. `720x1280` portrait, small file, short duration, low bitrate => direct allowed.
2. Genuinely heavy input => classified by combined rule, not by naive height.
3. Blocked preflight => no compose lock retained and retry is not `409`.
4. Presenter/advisory => no compose-ready or recompose wording when blocked.
5. Real concurrent compose => still returns `409 compose_in_progress`.

## Non-Goals

- No subtitle visual tuning.
- No dubbing redesign.
- No new scenario or task type.
- No broad architecture refactor.
- No speculative cleanup outside the compose guardrail fix.
- No resurrection of PR #39/#40 code paths without redesigning the faulty semantics above.

## Acceptance

- Baseline-safe portrait compose works again.
- `720x1280` portrait input is direct-allowed.
- Blocked fast-fail is stable and conflict-free.
- Presenter truth is aligned.
- Real concurrent compose still returns `409`.
- No reintroduction of PR #39/#40 regression behavior.

## Post-Fix Validation Pending

- Rerun the live task `fc45e93f83c3` after the rework to confirm portrait compose succeeds.
- Validate a true heavy input routes to adapt or blocked according to the new combined policy.
- Confirm workbench/task detail remain readable before and after both successful and blocked compose attempts.
