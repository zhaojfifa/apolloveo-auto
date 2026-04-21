# Hot Follow Translation Baseline Promotion To Main

Date: 2026-04-22

## Why This Branch Is The New Baseline

`fix/hf-helper-translation-only` is promoted to the Hot Follow translation baseline because both translation lines are now recovered:

1. Normal target-subtitle translation line.
2. Helper-only translation line.

The previous recovered business baseline already proved the main subtitle -> dub -> compose line:

- target subtitle main object works
- `vi.srt` works
- dub works
- final compose works

This promotion adds the helper-only translation recovery while preserving the recovered main business line. Helper translation remains auxiliary side-channel state and must not become authoritative target subtitle truth.

## Merge

- Merged branch: `fix/hf-helper-translation-only`
- Merge target: `main`
- Merge method: `git merge --no-ff fix/hf-helper-translation-only`
- Merge commit: `f64a165b44a9fe15739fafc0b6270c5c9abaaac5`

## Tag

- Tag name: `hot-follow-translation-baseline-20260421`
- Tagged commit: `f64a165b44a9fe15739fafc0b6270c5c9abaaac5`

This tag freezes the version where the normal target-subtitle translation line and helper-only translation line are both recovered.

## Validation Evidence Used

Recovered real-task validation sample:

- Task: `b1bf7348a7f3`

Validation evidence cited for the recovered business line:

- target subtitle main object valid
- `vi.srt` valid
- audio ready
- dub current
- helper translation failure no longer poisons mainline truth
- `helper_translation.failed=false`
- no helper failure poisoning of target subtitle, dub, compose, or final truth

Pre-merge local validation on `fix/hf-helper-translation-only`:

```bash
python3.11 -m py_compile \
  gateway/app/services/hot_follow_helper_translation.py \
  gateway/app/routers/hot_follow_api.py \
  gateway/app/services/subtitle_helpers.py \
  gateway/app/services/task_view_workbench_contract.py \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py
```

Result: passed.

```bash
git diff --check hot-follow-business-baseline-20260421..HEAD
```

Result: passed.

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_voice_led_does_not_recommend_no_tts_compose \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_with_saved_target_subtitle_stays_helper_scoped \
  -q
```

Result: `9 passed`.

## Scope

Included:

- helper translation request path metadata
- helper translation provider error metadata
- helper translation workbench projection
- helper-only and source-lane regression tests
- helper-translation execution note

Excluded:

- target subtitle authoritative write path
- source subtitle lane normal translation behavior beyond regression validation
- target subtitle save contract
- `vi.srt` generation
- dub input generation
- dub execution
- compose execution
- ready gate
- operator summary
- advisory routing
- PR-4 / PR-5 work
- second-line / Avatar work

## Pause Statement

PR-4 and PR-5 remain paused until post-merge verification is complete.

This baseline promotion does not restart architecture PR planning. Architecture work can resume only after one more mainline live verification passes.

## Next Step

Run one more Hot Follow live verification on `main` after the merge and tag push.

Required post-merge live checks:

1. Normal translation path works.
2. Helper translation path works.
3. Target subtitle main object stays valid.
4. `vi.srt` stays valid.
5. Dub works.
6. Final output availability is not poisoned.

Only after this mainline live verification is recorded should architecture PR planning resume.
