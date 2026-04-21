# HF Line Recovery From Baseline

Date: 2026-04-21

Branch: `recovery/hf-mainline-regression-20260421`

## Baseline Commit / Tag Used

- Baseline tag: `compose-heavy-input-stability-20260419`
- Baseline commit: `1f02f2a`

This baseline is the truth reference for Hot Follow business-path recovery in this branch.

## Exact Bad Range

- Known-bad range: `a589c99..11aace7`
- First bad mainline merge: `22f528a`

## Root Cause

The mainline regression was introduced at the source-subtitle to target-subtitle authoritative write boundary.

The frontend changed the main translate flow to use `input_source: "source_subtitle_lane"` while the backend source-lane translation path only trusted storage-backed normalized/origin subtitle inputs. When the operator-visible source subtitle existed in the UI but no storage-backed normalized/origin SRT was available, the translation action did not write the target subtitle main object.

That broke the business path in this sequence:

1. source subtitle is visible
2. translate is allowed from the workbench
3. target subtitle main object stays empty
4. subtitle step reports `subtitle_missing`
5. dub is skipped with `target_subtitle_empty`
6. compose/final downstream behavior is blocked by missing target subtitle truth

Helper translation failures such as `429` were observed but are not the primary regression. The primary regression is the broken authoritative target-subtitle write path.

## Exact Files Changed

Recovery branch code changes:

- `gateway/app/static/js/hot_follow_workbench.js`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`

Recovery branch execution note:

- `docs/execution/HF_LINE_RECOVERY_FROM_BASELINE.md`

Files reviewed against the baseline as part of the recovery scope:

- `gateway/app/services/subtitle_helpers.py`

`subtitle_helpers.py` was reviewed during the baseline diff because helper-only behavior must remain helper-only, but it is not part of the applied recovery patch.

## Recovery Action

The recovery branch reconstructs the baseline business-path behavior without touching ready-gate, advisory, operator-summary, or other architecture cleanup work.

Applied recovery action:

1. restore visible source text as a valid recovery input for the normal `source_subtitle_lane` translate path
2. keep stored normalized/origin subtitle content as the preferred source-lane truth when present
3. when only plain source text is available, translate it and normalize it into authoritative target SRT before save
4. preserve helper-only translation as helper-only
5. preserve downstream dub/compose enablement semantics by fixing the target subtitle write path instead of changing dub/compose logic

## Validation Evidence

### Compile Check

```bash
python3.11 -m py_compile \
  gateway/app/routers/hot_follow_api.py \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py
```

### Focused Pytest

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_plain_source_text_when_storage_lane_missing \
  gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt \
  -q
```

Expected business-path confirmation from the focused regression set:

1. helper-only translation does not persist authoritative target subtitle truth
2. source-lane translation persists full target SRT
3. normalized source SRT remains authoritative when present
4. plain source text fallback persists authoritative target subtitle truth when storage lane is missing
5. canonical target subtitle synchronization continues to support downstream dub enablement

### Real Hot Follow Live Validation

Required before any merge to `main`:

1. source subtitle exists
2. clicking translate writes target subtitle main object
3. `vi.srt` is produced
4. rerun dub works
5. compose works
6. final exists when expected

This live validation is still required and remains the merge gate for recovery.

## Status

- PR-4 remains paused
- PR-5 remains paused
- this branch is business-path recovery only
- do not merge to `main` until real Hot Follow live validation passes
