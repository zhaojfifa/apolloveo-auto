# VEOBASE01 Remote Switch And Phase 2.5 Plan

- Branch name: `VeoBase01`
- Intended remote target: `origin/VeoBase01`
- Local approved baseline SHA: `f4a19681f7b0ea60f8115d7a198841bf9c4e86b7`
- Current stale remote SHA before replacement: `ea437f1bcebdead870f91864dc34ae22d2680ae0`

## Why remote replacement is required

Local `VeoBase01` is now the approved post-PR-9 integration baseline:

- it was rebuilt from updated `main`
- PR-6 through PR-9 were applied sequentially on top of that refreshed baseline
- final-ready and compose-running regression probes remained aligned through the cleanup series

`origin/VeoBase01` still points to the older pre-refresh VeoBase01 history, so the remote integration branch no longer matches the accepted local integration truth.

## Approved baseline statement

The approved integration baseline for continued VeoBase01 work is the local `VeoBase01` tip at:

- `f4a19681f7b0ea60f8115d7a198841bf9c4e86b7`

That commit is the post-PR-9 baseline intended to replace `origin/VeoBase01`.

## Evidence of stale remote history

Fresh divergence after `git fetch origin`:

- local-only approved integration commits:
  - `f4a1968` `refactor(workbench): remove post-gate contract truth mutation`
  - `0ffe60e` `refactor(task-view): split projection from presenters`
  - `d25d592` `refactor(hot-follow): move router view helpers into task view services`
  - `9f94cd2` `refactor(tasks): move route-owned view builders into services`
- remote-only stale VeoBase01 tip:
  - `ea437f1` `hotfix: align hot follow publish and workbench state projection`

The remote branch is therefore stale relative to the accepted local integration line.

## Rollback reference

If the remote replacement must be rolled back, the pre-replacement remote VeoBase01 tip is:

- `ea437f1bcebdead870f91864dc34ae22d2680ae0`

## Remote switch intent

The remote update is intentionally a branch replacement, not a merge:

- replace `origin/VeoBase01` with the approved refreshed local `VeoBase01`
- use explicit `--force-with-lease`
- verify the remote ref after push

## Phase 2.5 scope after remote switch

This phase remains cleanup only. It does not start Phase 3 and does not start new-line implementation.

Priority order:

1. `gateway/app/routers/tasks.py` shell reduction follow-up
2. `gateway/app/routers/hot_follow_api.py` shell reduction follow-up
3. `gateway/app/services/compose_service.py` pressure audit and safe extraction
4. `gateway/app/services/steps_v1.py` compatibility-pressure audit and safe extraction

## Non-goals

- no Hot Follow business behavior change
- no translation or helper-translation behavior change
- no subtitle save semantic change
- no dub / compose / ffmpeg / worker runtime behavior change except strictly structural extraction with preserved behavior
- no new-line implementation
- no multi-role harness
- no API contract redesign
