# Hot Follow Pre-Merge Known-Good Anchor

Date: 2026-04-22

## Decision

Use the exact pre-merge head of `hotfix/hf-target-subtitle-save-contract` as the new known-good repair anchor.

Do not use:

- current `main` as the repair anchor
- tag `compose-heavy-input-stability-20260419` as the repair anchor
- a scratch rebuild or new minimal line

Do not patch yet. The immediate work is anchor confirmation, diff mapping, and replay planning.

PR-4 and PR-5 remain paused.

## Exact Pre-Merge Known-Good SHA

Known-good anchor:

- `11aace75c3bf658d2e409731a607bf3ce9e2e77e`
- Branch head: `hotfix/hf-target-subtitle-save-contract`
- Remote branch head: `origin/hotfix/hf-target-subtitle-save-contract`
- Commit subject: `fix(hot-follow): bind source subtitle translation lane`

Merge into current `main`:

- Merge commit: `22f528a412ce3b14ea44b533848ddfc6235f251a`
- First parent: `a2ee63a1adbe1f4eb5d8e3109601416cbc1d3f98`
- Second parent: `11aace75c3bf658d2e409731a607bf3ce9e2e77e`

The known-good anchor is the second parent of the merge commit. That is the exact hotfix branch head immediately before it was merged into `main`.

New repair motherline created from the anchor:

- `repair/hf-premerge-known-good-anchor`

## Why This Replaces The Old Tag As Recovery Baseline

The old tag `compose-heavy-input-stability-20260419` / `1f02f2a` is no longer the right recovery baseline for this investigation because it predates the target-subtitle save-contract work and risks discarding business details accumulated after that point.

The pre-merge hotfix head is a better anchor because:

1. It was live-validated as fixed before merge.
2. It includes the recovered target subtitle save contract.
3. It includes the split-brain projection alignment.
4. It includes source-subtitle translation lane binding.
5. It preserves current Hot Follow business shape more closely than the old tag.

Therefore this anchor replaces both the old tag and scratch-rebuild strategy for the next repair pass.

## Diff Scope: Anchor To Current Main

Compared:

- Anchor: `11aace75c3bf658d2e409731a607bf3ce9e2e77e`
- Current `main`: `22f528a412ce3b14ea44b533848ddfc6235f251a`

Result:

- `git diff --stat 11aace75c3bf658d2e409731a607bf3ce9e2e77e..main` is empty.
- `git diff --name-status 11aace75c3bf658d2e409731a607bf3ce9e2e77e..main` is empty.
- Anchor tree, merge tree, and current `main` tree are identical:
  - `bea0284ad0da8315d07924a6a61cc0ce5dcc7bf1`

Commit range after the anchor on current `main`:

- `22f528a412ce3b14ea44b533848ddfc6235f251a` only.

Important conclusion:

There are no post-anchor content changes on current `main`. The merge commit records the integration of the hotfix branch, but the final tree of current `main` is the same as the pre-merge hotfix head.

This changes the investigation shape. If the hotfix head was truly live-validated as fixed and current `main` has the same tree, then a later mainline code commit did not re-break the line. The remaining suspect classes are:

- merge/deploy/runtime environment drift after the same tree was deployed
- task data or artifact state from before the hotfix
- a validation gap where the pre-merge live validation did not cover one of the two failure shapes
- post-main branches or recovery variants, not current `main`

## Suspect Commit Chain After The Anchor

### Current mainline chain

After the anchor, current `main` contains only:

- `22f528a` merge commit `Merge branch 'hotfix/hf-target-subtitle-save-contract'`

There is no file diff from the anchor to current `main`, so this commit cannot be blamed for a code-level re-break unless the issue is merge/deployment metadata outside the tree.

### Target subtitle main object write

No post-anchor current-main code commit re-breaks this path.

Relevant pre-anchor chain already included in the known-good anchor:

- `a589c99` introduced explicit `source_subtitle_lane` translation and authoritative target write.
- `11aace7` broadened source-lane binding.

Because `11aace7` is now the known-good anchor, do not treat `a589c99` / `11aace7` as post-anchor suspects unless live validation is disproven or narrowed to a shape not covered by the pre-merge validation.

### Semantic-empty target SRT admission

No post-anchor current-main code commit re-breaks this path.

Relevant pre-anchor repairs already included in the known-good anchor:

- `dfdfa0c` rejects semantically-empty target subtitle saves and artifact syncs.
- `6d3a346` aligns projection surfaces so timing-only target artifacts do not hydrate or project as authoritative target truth.

If semantic-empty target SRT can still become authoritative from current `main`, the next audit should look for bypass writers that do not use the guarded save/sync path, or for stale task artifacts created before the hotfix.

### `no_dub` / `no_tts` presentation drift

No post-anchor current-main code commit re-breaks this path.

Relevant pre-anchor behavior already included in the known-good anchor:

- `cfc50a0` adds terminal no-dub/no-TTS advisory projection.
- `385f2c1` propagates route-local no-TTS/no-dub terminal state through route state, task view, and skills routing.
- `b4f13e0` mitigates helper-translation failures so they do not collapse into no-TTS route guidance.

If current behavior still presents target-write failure as a no-TTS route, the next audit should determine whether the source failure is:

- a real upstream missing/empty target subtitle caused by stale task state,
- a helper-translation failure path,
- or a live data shape not covered by the pre-merge validation.

## Replay Map From Old Baseline To New Anchor

The anchor already includes the target-subtitle repair chain that was previously under review:

1. `dfdfa0c` - enforce target subtitle save semantics.
2. `6d3a346` - align subtitle projection truth.
3. `a589c99` - bind target translation to source subtitle lane.
4. `11aace7` - bind source subtitle translation lane.

The old replay question changes from "which post-anchor commit re-broke main?" to "what changed after the same tree was live-validated?"

Because anchor and current `main` have identical trees, the replay map should start from this anchor and then inspect:

1. deployment revision / runtime wrapper used for live validation vs current runtime
2. task data created before vs after the hotfix
3. stale artifacts already present in storage
4. any branch deployed that is not `main` or `hotfix/hf-target-subtitle-save-contract`
5. recovery branches that diverged from this anchor

## Recommended Selective Replay / Revert Path

Do not patch code until the anchor SHA and identical-tree result are accepted.

Recommended path:

1. Keep `repair/hf-premerge-known-good-anchor` as the repair motherline.
2. Reproduce the business guardrails on this branch using the same task shape that was live-validated before merge.
3. Reproduce the current failing task shape against the same branch.
4. If the known-good task passes and the current failing task fails on the same tree, classify the issue as data-shape or stale-artifact drift before code changes.
5. If both fail, the pre-merge validation was incomplete and the repair should be narrowed inside the anchor tree.
6. If the anchor passes but current deployed `main` fails, inspect deployment/runtime configuration rather than reverting source commits.
7. Only after reproduction identifies a code path should a selective replay or revert be proposed.

Selective revert guidance:

- Do not revert PR-1, PR-2, or PR-3 broadly.
- Do not revert `dfdfa0c` or `6d3a346`.
- Do not remove helper translation isolation from `b4f13e0` / `9d60d73`.
- Do not weaken semantic-empty target subtitle rejection.
- If a code change is required, prefer a narrow guard or bypass-writer fix around the exact subtitle write or projection path proven by reproduction.

Business guardrails for any later patch:

1. Source subtitle exists.
2. Translate writes a non-empty target subtitle main object.
3. Canonical `vi.srt` exists.
4. Semantically-empty target SRT cannot become authoritative.
5. Rerun dub works.
6. Compose works.
7. Final artifact exists.
8. State/advisory does not present write failure as a valid no-TTS route.

## Pause Statement

PR-4 and PR-5 remain paused completely.

This anchor update does not restart architecture work, does not authorize a scratch rebuild, and does not authorize broad refactor. The next step is validation and drift identification from the known-good pre-merge hotfix head.
