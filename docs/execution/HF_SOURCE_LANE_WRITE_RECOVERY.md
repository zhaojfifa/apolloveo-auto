# HF Source-Lane Write Recovery

Date: 2026-04-21

## Scope

This note records the minimum recovery for the Hot Follow business-line break identified by
`docs/reviews/HF_PR1_PR2_PR3_DRIFT_REVIEW.md`.

This is not PR-4 or PR-5 work.

Out of scope:

- ready-gate cleanup
- advisory cleanup
- operator summary cleanup
- compose ownership changes
- four-layer architecture cleanup

## Root Cause

The active break was before authoritative target subtitle write.

The main translate flow declared `input_source: "source_subtitle_lane"`, but the backend
source-lane resolver only trusted stored normalized/origin subtitle lanes. When the UI showed
visible source subtitle text but no stored normalized/origin SRT was available, the translation
request did not reach `_hf_save_authoritative_target_subtitle(...)`.

That produced the live failure chain:

1. source subtitle visible in workbench
2. target subtitle main object remains empty
3. `subtitle_ready=false` / `subtitle_missing`
4. dub remains skipped with `target_subtitle_empty`

## Minimum Recovery Applied

Primary recovery surface:

- `gateway/app/routers/hot_follow_api.py`

Supporting request-carrier surface:

- `gateway/app/static/js/hot_follow_workbench.js`

Focused regression coverage:

- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`

## Contract After Recovery

Recovered source-lane resolution contract:

1. If stored normalized source SRT exists, use it first.
2. Else if stored origin source SRT exists, use it.
3. Else accept the same visible source text the UI already treats as a valid source lane.
4. If the recovered source text is SRT, preserve cue/timecodes and translate per segment.
5. If the recovered source text is plain text, translate it and normalize it into authoritative target SRT.
6. Persist the result through `_hf_save_authoritative_target_subtitle(...)`.
7. Regenerate canonical target subtitle artifact (`vi.srt` for Vietnamese).
8. Preserve downstream empty-dub recovery so valid saved target subtitle re-enables dubbing.

Preserved boundaries:

- helper-only translation remains helper-only and non-authoritative
- semantically empty target subtitles remain rejected at the save owner boundary
- downstream ready-gate/advisory/compose consumers remain unchanged

## Code Surfaces

### `gateway/app/routers/hot_follow_api.py`

Recovered `_hf_translate_source_subtitle_lane(...)`:

- prefers stored normalized/origin subtitle lanes when present
- accepts `source_text_hint` from the request when storage-backed source lane is missing
- supports both SRT and plain visible source text
- writes translated target subtitle through `_hf_save_authoritative_target_subtitle(...)`

### `gateway/app/static/js/hot_follow_workbench.js`

Recovered main translate action:

- sends the visible source-lane text along with `input_source: "source_subtitle_lane"`
- keeps helper translate on `input_source: "helper_only_text"`

### `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`

Focused regression coverage includes:

1. source-lane persists target SRT from normalized source SRT
2. source-lane persists target SRT from origin SRT
3. source-lane persists target SRT from visible plain source text when storage lane is missing
4. helper-only translation remains non-authoritative

Additional preserved owner-boundary and dub-recovery coverage remains in:

- `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py`

## Validation Gate

Required validation for this recovery:

- `py_compile` on changed files
- focused pytest on source-lane translation, authoritative write, and dub recovery
- real Hot Follow task validation showing:
  - non-empty target subtitle main object
  - `vi.srt` exists
  - rerun dub works

## Current Status

Compile and focused regression validation are required for this branch.

Real task validation remains the final merge gate. This recovery must not be treated as complete
until a real Hot Follow task confirms:

1. non-empty target subtitle main object
2. `vi.srt` exists
3. rerun dub works

## Validation Record

Completed in this session:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `node --check gateway/app/static/js/hot_follow_workbench.js`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_only_does_not_persist_target_subtitle gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_uses_normalized_source_srt_when_origin_key_empty gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_plain_source_text_when_storage_lane_missing gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_rejects_semantically_empty_srt_without_replacing_truth gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_successful_redub_persists_current_subtitle_snapshot -q`

Observed result:

- focused regression set passed: `7 passed`

Live validation status in this session:

- local workspace does not contain a populated Hot Follow task DB or task artifact set
- the reachable deployed Render host at `https://ai-service-leob.onrender.com` is not serving the Hot Follow API contract; its live OpenAPI is a poster-generation service, so it cannot validate `/api/hot_follow/tasks/{task_id}/...`

Conclusion:

- code-level recovery is validated
- real Hot Follow task validation is still pending and remains the final gate before reporting business-path success
