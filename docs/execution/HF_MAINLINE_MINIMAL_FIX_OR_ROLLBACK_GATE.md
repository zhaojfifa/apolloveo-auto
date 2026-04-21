# HF Mainline Minimal Fix Or Rollback Gate

Date: 2026-04-22

## Scope

This branch is a clean minimal-fix branch from current `main`:

- branch: `fix/hf-source-lane-target-write-mainline`
- base: current `main` at `22f528a`

This work repairs only the mainline Hot Follow business break:

`source subtitle lane -> target subtitle main object -> canonical target SRT -> downstream dub enablement`

Out of scope:

- ready_gate changes
- advisory changes
- operator_summary changes
- `task_view.py` or `task_view_workbench_contract.py`
- `compose_service.py`
- PR-4 / PR-5 work
- architecture cleanup

## Mainline Break

Current mainline symptom:

1. parse/source subtitle exists
2. target subtitle main object stays empty
3. subtitle step surfaces `subtitle_missing`
4. dub is skipped with `target_subtitle_empty`

The active break is before authoritative target subtitle write.

## Minimal Fix Contract

Minimal repair rules:

1. If stored normalized source SRT exists, use it.
2. Else if stored origin source SRT exists, use it.
3. Else accept the same visible source text the UI already treats as valid source lane input.
4. Translate that source text.
5. Normalize plain source text into authoritative target SRT when needed.
6. Write target subtitle truth through `_hf_save_authoritative_target_subtitle(...)`.
7. Regenerate canonical `vi.srt`.
8. Preserve downstream empty-dub recovery so rerun dub becomes available again.

Must remain preserved:

- helper-only translation remains helper-only and non-authoritative
- semantically empty target subtitles remain rejected
- valid saved target subtitle still re-enables downstream dub

## Allowed Surfaces

Primary code surfaces for this branch:

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/static/js/hot_follow_workbench.js` only if the request payload is otherwise insufficient
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`

## Regression Gate

Required regression coverage:

1. source-lane persists target SRT from normalized source SRT
2. source-lane persists target SRT from origin SRT
3. source-lane persists target SRT from visible plain source text when storage lane is missing
4. helper-only translation remains non-authoritative
5. semantically empty target subtitles are still rejected
6. valid saved target subtitle regenerates canonical `vi.srt` and re-enables downstream dub

## Validation Gate

Required before merge:

- compile changed Python files
- syntax check changed JS file
- focused pytest for source-lane translation, authoritative write, and dub recovery
- real Hot Follow live validation proving:
  - source subtitle exists
  - translate to target language writes non-empty target subtitle main object
  - `vi.srt` exists
  - rerun dub works

## Rollback Gate

Stop rule:

If this minimal mainline fix branch still cannot restore the business line quickly and cleanly,
stop and recommend rollback to:

- tag `compose-heavy-input-stability-20260419`
- commit `1f02f2a`

Then rebuild PR-1 / PR-2 / PR-3 / PR-4 from that baseline.

## Validation Record

Code-level validation completed on this branch:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `node --check gateway/app/static/js/hot_follow_workbench.js`
- focused pytest:
  - `gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle`
  - `gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt`
  - `gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty`
  - `gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_plain_source_text_when_storage_lane_missing`
  - `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_rejects_semantically_empty_srt_without_replacing_truth`
  - `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt`
  - `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_successful_redub_persists_current_subtitle_snapshot`

Observed result:

- focused regression set passed: `7 passed`

Live validation status:

- still required before merge
- not yet satisfied in this session

Conclusion:

- minimal code fix is present on this mainline branch
- merge remains blocked until real Hot Follow live validation succeeds
