# Hot Follow Compose Guard Rollback Review

Date: 2026-04-19

## Rollback Point

- Last known good compose baseline: `c730c0c` (`fix(subtitles): reduce hot follow default subtitle font size slightly`).
- Guard commit rolled back: `0f657ae` (`fix(compose): guard hot follow large input compose`).
- Rollback branch: `fix/hf-compose-guard-rollback-first`.
- Runtime result: the Hot Follow compose runtime files are byte-identical to `c730c0c` after the revert.

## Focused Findings

### 1. Original 196MB Incident

The original incident was a resource-control failure in the compose path. A large source video could enter final compose directly, so the app relied on the full ffmpeg compose command to survive large input size, video decode, subtitle burn, audio mix, output encode, temporary files, and upstream request lifetime. Production evidence showed `502 Bad Gateway` on compose and follow-up task/workbench requests, which is consistent with the instance becoming unavailable or resource-exhausted during heavy compose work.

The baseline did not have a preflight/adaptation boundary for large media. That gap is real, but it should be closed with a narrow policy model that preserves normal Hot Follow shortvideo shapes.

### 2. Regression Introduced By PR #39 / #40

PR #39/#40 added a hard height rule:

- `MAX_HEIGHT = 1080`
- `if profile.height and profile.height > MAX_HEIGHT: blocked/resolution_too_high`

That rule is not orientation-aware. A normal portrait shortvideo `720x1280` has height `1280`, so it is blocked even though its pixel count, duration, file size, and bitrate are safe. This is the direct cause of the reported `resolution_too_high` regression for a small portrait input.

The patch also raised blocked preflight through `compose_fail(...)`, whose default HTTP status is `409`. Because the router writes `compose_lock_until` and `compose_status=running` before invoking `svc.compose(...)`, a preflight block happened inside the locked/running execution section. The final state was eventually written as failed/blocked, but the request surface still behaved like a conflict-style compose failure. That blurred two distinct states:

- real concurrent compose, where `409 compose_in_progress` is appropriate
- deterministic input block, where the request should fast-fail without looking like another compose is running

### 3. Rules That Belong In Configurable Policy/Skill Config

The reverted patch hardcoded guard policy inside `compose_service.py`. The following should not be embedded as isolated service constants without a contract/policy layer:

- file-size thresholds for direct/adapt/block
- duration limits
- bitrate limits
- resolution or pixel-budget limits
- adaptation target profile
- disk-reserve threshold
- block/adapt reason mapping shown to operators

These rules belong in a small configurable compose policy, ideally line-aware for Hot Follow. The service should execute the decision, not own all product policy. The policy must model portrait shortvideo as a first-class safe input, not as an incidental exception.

### 4. SSOT / Presenter Divergence

PR #39/#40 added `compose_preflight_*` fields in workbench payloads and task projection, but it did not update the ready-gate contract or advisory model as the SSOT for operator readiness.

Observed divergence risk:

- Workbench `compose_allowed` could be forced false by `compose_preflight_status`.
- Ready-gate/advisory could still reason from existing audio/subtitle/final signals and produce compose-ready or recompose messaging.
- Task card/presenter logic could continue using ready-gate output without understanding blocked compose policy.

The correct model is one SSOT path for compose eligibility. If input policy says compose is blocked, task card, advisory, operator summary, and compose action should all report the same blocked reason and no compose-ready/recompose prompt.

## Explicit Comparison

### Baseline-Safe Portrait Input

- Example: `720x1280`, approximately `2.7MB`, approximately `24s`, low bitrate.
- Baseline behavior at `c730c0c`: no resolution guard exists, so the normal compose path proceeds.
- Required future behavior: direct allowed, not blocked.

### Large-Input Incident

- Example: approximately `196MB`.
- Baseline behavior at `c730c0c`: enters direct compose with no preflight/adaptation.
- Incident behavior: heavy ffmpeg compose can destabilize the instance and surface `502` on compose and follow-up workbench/task requests.
- Required future behavior: adapt first or block before heavy compose, depending on policy and available resources.

### PR #39 / #40 Blocked Behavior

- `720x1280` is incorrectly blocked as `resolution_too_high` because height alone is compared to `1080`.
- Blocked state is introduced after the router has already acquired compose execution and written running state.
- Blocked failures use the same `409` default path as conflict-style compose errors.

### Lock / Conflict Behavior

- Baseline: `409` is used for active compose lock or in-process lock acquisition conflict.
- PR #39/#40: deterministic preflight block also surfaces through `409`, even though it is not concurrent compose.
- Required future behavior: blocked fast-fail must not hold or refresh compose lock, and repeated blocked attempts must return the same blocked result rather than `compose_in_progress`.

### Ready-Gate / Advisory / Presenter Behavior

- Baseline: ready-gate and presenter reason from final freshness, raw, subtitles, audio, and no-dub allowance.
- PR #39/#40: blocked state is partly projected in workbench payloads, but ready-gate/advisory SSOT is not aligned.
- Required future behavior: `compose_allowed=false` with a stable blocked reason must drive task card, advisory, operator summary, and compose action state together.

## Required Findings Confirmed

- `720x1280` portrait shortvideo must be baseline-safe and must not be blocked by a height-only rule.
- Blocked preflight must not behave like compose-in-progress conflict.
- Presenter/advisory must not say compose-ready when `compose_allowed=false`.
- Compose guard thresholds need a narrower, policy-owned model using orientation-aware or pixel-budget-aware logic.

## Narrow Rework Plan

### A. Preflight Classification

- Add a policy object for compose guard thresholds instead of scattered service constants.
- Replace height-only blocking with pixel-budget and orientation-aware checks.
- Treat normal shortvideo portrait shapes, including `720x1280`, as direct-safe when size, duration, bitrate, and disk reserve are safe.
- Adapt large-but-allowed inputs before final compose.
- Block only truly unsafe inputs or insufficient local resources.

### B. Blocked Fast-Fail Semantics

- Run lightweight preflight before writing `compose_status=running` or `compose_lock_until`.
- Reserve `409 compose_in_progress` only for active lock or in-memory lock conflict.
- Persist blocked state with a stable code/message, but return a non-conflict blocked response shape.
- Repeated blocked attempts must remain deterministic and must not create a stale running state.

### C. Presenter / Ready-Gate Alignment

- Add compose input policy result as an explicit ready-gate signal or equivalent SSOT input.
- Ensure `compose_allowed=false` drives task card, advisory, operator summary, and compose button/action messaging.
- Suppress compose-ready/recompose advisory when the current blocker is input/resource policy.

### Non-Scope For Rework

- No subtitle visual tuning.
- No dubbing redesign.
- No new task type or scenario split.
- No broad router or presenter refactor beyond the minimum SSOT alignment.
- No incremental patching on top of the reverted PR #39/#40 implementation.

## Verification Completed For Rollback

- Runtime files touched by PR #39/#40 compare clean against `c730c0c`.
- No repository video fixtures are available for a local real-media `720x1280` compose run.
- Targeted baseline checks passed with `/opt/homebrew/bin/python3.11`:
  - `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/task_view_helpers.py gateway/app/services/task_view.py gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_compose_service_contract.py`
  - `python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py gateway/app/services/tests/test_task_router_presenters.py -q` -> 97 passed.

## Remaining Risks

- The local environment does not include a representative `720x1280` video fixture, so live-media compose recovery still needs confirmation in an environment with representative Hot Follow media and ffmpeg/provider setup.
- The original 196MB incident root cause is inferred from production symptoms and code path shape; exact process-level memory/disk/timeout telemetry was not available in this repo.
