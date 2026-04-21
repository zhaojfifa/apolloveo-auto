# Hot Follow Helper Translation Only Fix

Date: 2026-04-22

## Baseline

- Baseline tag: `hot-follow-business-baseline-20260421`
- Baseline commit: `22f528a412ce3b14ea44b533848ddfc6235f251a`
- Branch: `fix/hf-helper-translation-only`

This branch starts from the frozen Hot Follow business baseline where the main subtitle -> dub -> compose path was recovered and live-validated.

## Scope

This is a helper-translation-only fix.

Helper translation is auxiliary side-channel state. It must never:

- overwrite the target subtitle main object
- alter authoritative target subtitle truth
- break rerun dub
- affect compose readiness
- affect final output availability

PR-4 and PR-5 remain paused until the helper-only fix is verified.

## Files Changed

- `gateway/app/services/hot_follow_helper_translation.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/HF_HELPER_TRANSLATION_ONLY_FIX.md`

No source subtitle lane normal translation path, target subtitle authoritative save path, `vi.srt` generation, dub execution, compose execution, ready gate, advisory, operator summary, PR-4, PR-5, second-line, or Avatar code was changed.

## What Is Fixed

Helper translation success and failure now persist explicit helper-layer metadata only:

- helper input text
- helper translated text on success
- helper target language
- helper provider
- helper status
- sanitized helper error fields on failure

The workbench subtitle projection exposes this metadata under the helper translation projection. It remains separate from authoritative target subtitle truth.

Provider failures such as Gemini `429` / `RESOURCE_EXHAUSTED` remain sanitized and operator-readable.

## What Is Explicitly Not Fixed

This does not change the recovered main business line.

Explicitly not changed:

- normal source subtitle -> target subtitle translation
- target subtitle main object save contract
- semantic-empty target SRT rejection
- canonical `vi.srt` generation
- dub input generation
- dub execution
- compose execution
- ready gate
- operator summary
- advisory routing

This does not claim provider capacity is fixed. If Gemini returns `429`, the failure remains provider exhaustion, but it is kept helper-scoped.

## Regression Validation

Compile validation:

```bash
python3.11 -m py_compile \
  gateway/app/services/hot_follow_helper_translation.py \
  gateway/app/routers/hot_follow_api.py \
  gateway/app/services/subtitle_helpers.py \
  gateway/app/services/task_view_workbench_contract.py \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py
```

Result: passed.

Focused pytest:

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure \
  -q
```

Result: `7 passed`.

Additional advisory regression:

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_voice_led_does_not_recommend_no_tts_compose \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_with_saved_target_subtitle_stays_helper_scoped \
  -q
```

Result: `2 passed`.

Coverage from this validation:

1. Helper translation success writes helper layer only.
2. Helper translation failure remains helper-scoped.
3. Helper translation failure does not clear or replace target subtitle main object.
4. Helper translation failure does not affect preserved dub readiness fields when target subtitle is already valid.
5. Helper translation failure does not affect preserved compose/final readiness fields when mainline outputs already exist.
6. Normal target source-lane translation regression still passes.

## Live Validation

Required before merge:

1. Verify the main line still works on a real Hot Follow task:
   - source subtitle exists
   - target translation writes target subtitle main object
   - `vi.srt` exists
   - rerun dub works
   - compose works
   - final exists
2. Verify helper failure does not poison the main line:
   - helper failure remains in helper state only
   - target subtitle truth remains valid
   - dub remains current when already valid
   - compose readiness and final availability remain intact

Live validation has not been completed in this code-edit session. The branch must not be treated as merge-ready until this real-task validation is recorded.

Local workspace note:

- The local `shortvideo.db` was checked for task `b1bf7348a7f3`.
- No row for that task was present locally, so the real-task validation could not be completed from this workspace.

## Next Step

Run the real Hot Follow live validation against this branch. If any change threatens the recovered main business line, stop immediately and revert that change from this branch.
