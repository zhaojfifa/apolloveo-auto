# Hot Follow Restart From Known-Good Tag

## Decision

Stop patching the current mainline and recovery branches. Both current variants are abandoned for Hot Follow continuation work.

Restart from the last known-good business baseline:

- Tag: `compose-heavy-input-stability-20260419`
- Baseline commit: `1f02f2a3a339e193ed4039cf20aad13b30a30536`
- Tag object observed locally: `e6c1716b2b85b635b95377d43be5697fe31a74f6`

The active restart branch is created from that tag. Current mainline architecture work is frozen and must not be used as the base for PR-1, PR-2, PR-3, or PR-4 replay.

## Why Mainline And Recovery Are Abandoned

The current line has two independent unacceptable business regressions:

1. The target subtitle main object can fail to be written at all.
2. The target subtitle artifact can be written as a semantically empty SRT.

Either failure breaks the Hot Follow business path. Continuing to patch on top of either variant risks preserving unstable behavior and obscuring the actual regression source.

## Pause Statement For PR-4 / PR-5

PR-4 and PR-5 are paused completely until the business baseline is restored and PR-1, PR-2, and PR-3 have been replayed one by one with business guardrails passing after each replay.

When PR-4 restarts, its scope must stay state/presenter only. PR-4 must not touch translation input, target subtitle writing, helper translation, or the dub business path.

## Restart Sequence

### Phase 0: Restore Business Baseline Only

1. Check out `compose-heavy-input-stability-20260419`.
2. Create a fresh restart branch from that tag.
3. Do not apply current mainline or recovery architecture patches.
4. Do not resume PR-4 or PR-5.

### Phase 1: Verify Business Path End-To-End

Before any architecture work, verify the Hot Follow business path end to end:

1. Source subtitle exists.
2. Translate writes a non-empty target subtitle main object.
3. Canonical `vi.srt` exists.
4. Rerun dub works.
5. Compose works.
6. Final artifact exists.

No architecture replay may begin until all six checks pass on the restored baseline.

### Phase 2: Replay PR-1 / PR-2 / PR-3

Replay PR-1, PR-2, and PR-3 one by one from the restored baseline.

After each PR replay, rerun the full Phase 1 business guardrail checklist. Do not proceed to the next PR if any regression appears.

### Phase 3: Restart PR-4

Only after PR-1, PR-2, and PR-3 have been replayed successfully and the business guardrails pass after each step, restart PR-4.

PR-4 scope is limited to state/presenter work. It must not modify translation input, target subtitle write behavior, helper translation behavior, or dub business path behavior.

## Business Guardrail Checklist

Every PR that touches any of the following files must pass business guardrails, not just unit tests:

- `hot_follow_workbench.js`
- `hot_follow_api.py`
- `subtitle_helpers.py`
- `task_view.py`
- `task_view_workbench_contract.py`
- `input_skill.py`
- `routing_skill.py`

Required guardrails:

1. Source subtitle exists.
2. Translate writes a non-empty target subtitle main object.
3. Canonical `vi.srt` exists.
4. Rerun dub works.
5. Compose works.
6. Final artifact exists.

The guardrail result must be recorded before merging or proceeding to the next replay step.
