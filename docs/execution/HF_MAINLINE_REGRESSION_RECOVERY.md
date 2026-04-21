# HF Mainline Regression Recovery

Date: 2026-04-21

Branch: `recovery/hf-mainline-regression-20260421`

## Last Known-Good Commit / Tag

- Last known-good tagged baseline used for this recovery investigation:
  - `compose-heavy-input-stability-20260419`
  - commit `1f02f2a`

Reason for choosing this baseline:

- it is the last tagged Hot Follow baseline on the mainline before the target-subtitle save / source-lane translation merge sequence landed
- the regression range that changed the normal translate flow begins after this tag

## First Known-Bad Commit / Range

- First known-bad range on the mainline path:
  - `a589c99..11aace7`
- First bad mainline merge containing that range:
  - `22f528a`

Exact judgment:

- `a589c99` introduced the contract break by changing the normal translate flow from explicit client text translation into a strict `source_subtitle_lane` backend path plus immediate authoritative target-subtitle save
- `11aace7` widened the visible mismatch by letting the frontend enable the normal translate action from more visible source-lane fields while the backend still only accepted storage-backed source subtitle inputs

## Exact Root Cause

The regression was introduced at the source-subtitle translation contract boundary.

After `a589c99` / `11aace7`:

- `gateway/app/static/js/hot_follow_workbench.js` switched the main translate action to:
  - send `input_source: "source_subtitle_lane"`
  - stop relying on explicit user-provided source text as the primary input contract
  - immediately persist the translated result as the authoritative target subtitle object

- `gateway/app/routers/hot_follow_api.py::_hf_translate_source_subtitle_lane`
  - only loaded source input from `_hf_load_normalized_source_text()` or `_hf_load_origin_subtitles_text()`
  - required SRT when using that path
  - did not reliably fall back to request-carried source text when the visible source lane was present in the UI but not backed by stored normalized/origin SRT

That created a split contract:

- frontend: source lane is visible, so translate is allowed
- backend: no persisted source-lane SRT available, so translate does not produce the authoritative target subtitle object

Downstream results then matched the live failure:

- target subtitle main object remains empty
- `subtitle_ready=false` / `subtitle_missing`
- dubbing remains skipped with `target_subtitle_empty`
- advisory and ready-gate consume the empty target truth and surface a no-TTS / no-dub route even though the intended translation step never successfully wrote target subtitle truth

## Exact Files Involved

Primary root-cause files:

- `gateway/app/static/js/hot_follow_workbench.js`
- `gateway/app/routers/hot_follow_api.py`

Related downstream consumers inspected during recovery:

- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/hot_follow_route_state.py`
- `skills/hot_follow/input_skill.py`
- `skills/hot_follow/routing_skill.py`

Judgment on downstream files:

- they were not the write-path root cause
- they correctly consumed the empty target subtitle truth after the translation contract failed

## Recovery Action Taken

Recovery was done surgically on the recovery branch, not on `main`.

Applied recovery action:

1. restored request-carried source text as a valid recovery input for `source_subtitle_lane`
2. kept storage-backed normalized/origin SRT as the preferred source when available
3. when only plain source text is available, translated it and normalized it into a valid authoritative target subtitle SRT before save
4. kept helper-only translation behavior separate
5. kept authoritative target subtitle save semantics intact

Code surfaces changed on the recovery branch:

- `gateway/app/static/js/hot_follow_workbench.js`
  - main translate action now sends the visible source text with `input_source: "source_subtitle_lane"`

- `gateway/app/routers/hot_follow_api.py`
  - `_hf_translate_source_subtitle_lane()` now:
    - prefers stored normalized/origin SRT when present
    - falls back to request-carried source text when storage-backed source lane is missing
    - supports plain source text by translating and normalizing it into authoritative target SRT before save

- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
  - added focused regression coverage for source-lane translation with plain source text and no stored source-lane SRT

## Validation Evidence

Direct reproduction against current `main` before the recovery patch:

- with `input_source="source_subtitle_lane"` and no stored normalized/origin source SRT, the backend returned:
  - `reason=source_subtitle_lane_empty`

That reproduces the broken contract: source lane can be visible to the operator while the authoritative target subtitle write path still fails to produce target truth.

Focused validation run on the recovery branch:

```bash
python3.11 -m py_compile \
  gateway/app/routers/hot_follow_api.py \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py
```

Focused regression set:

```bash
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_plain_source_text_when_storage_lane_missing \
  gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_voice_led_does_not_recommend_no_tts_compose \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_helper_translate_failure_with_saved_target_subtitle_stays_helper_scoped \
  -q
```

Observed result:

- `8 passed`

Additional note:

- a wider suite including `test_hot_follow_subtitle_binding.py` surfaced two unrelated subtitle-render baseline assertions and one sandbox-sensitive workspace-path test under `/opt/render/...`
- those failures were not introduced by this recovery patch and are outside the source-translation write-path regression

## Live Validation

Required but not yet complete in this session:

- validate the recovery branch against at least one real Hot Follow task
- confirm:
  1. source subtitle exists
  2. translate to target language writes target subtitle main object
  3. `vi.srt` is produced when expected
  4. rerun dub works
  5. compose works
  6. final exists when expected

Until that live validation succeeds, this recovery must not be treated as mainline-ready.

## Status

PR-4 and PR-5 remain paused until recovery succeeds.
