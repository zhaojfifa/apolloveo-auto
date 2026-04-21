# Hot Follow Source Subtitle Translation Binding Fix

Date: 2026-04-21

## Scope

This is a narrow Hot Follow fix after subtitle-truth recovery. It does not start PR-4, does not refactor the four-layer state architecture, does not roll back PR-1, and does not touch Avatar or second-line work.

## Exact Remaining Root Cause

The translation action had been split into explicit input sources, but the source-subtitle path still read too narrowly:

- `gateway/app/static/js/hot_follow_workbench.js::translateMmBtn` was bound to the normal `翻译为越南语/翻译为缅语` button and sent `input_source: "source_subtitle_lane"`.
- `gateway/app/routers/hot_follow_api.py::translate_hot_follow_subtitles` received the request and delegated to `_hf_translate_source_subtitle_lane`.
- `_hf_translate_source_subtitle_lane` only loaded `_hf_load_origin_subtitles_text(task)`, which reads the `origin_srt_path` storage object.

That missed tasks where the parsed/full source subtitle lane is present through the normalized source subtitle path (`origin_normalized.srt` / `normalized_source_text`) while `origin_srt_path` is empty or unavailable.

## Proof From Current vs Previous Task Shape

- Current task `7c94a1f15582` has full Chinese source subtitles visible to the operator but empty target subtitle fields. That matches the missed `normalized_source_text` / source-lane binding path.
- Previous task `bc58e3a013bd` produced target subtitle/audio from helper input only (`"cái này"`). That proves helper-only translation and target write-back can work, but it also proves the full source-subtitle workflow was not the path being used.

The bug is therefore not helper translation itself. It is the normal source-subtitle translation action failing to bind to the full parsed source subtitle lane.

## Files Changed

- `gateway/app/static/js/hot_follow_workbench.js`
  - The normal target-language translation button now treats `normalized_source_text`, `raw_source_text`, `origin_text`, or `parse_source_text` as evidence that a source lane exists before calling the backend.
  - It still sends `input_source: "source_subtitle_lane"` and does not fall back to helper input.

- `gateway/app/routers/hot_follow_api.py`
  - `_hf_translate_source_subtitle_lane` now prefers normalized source SRT when available, then falls back to origin source SRT.
  - It still requires SRT so cue/timecodes are preserved.
  - The translated target SRT still writes through the authoritative target subtitle save path.

- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
  - Added regression coverage for normalized-source-only tasks.
  - Existing helper-only and origin-source-lane tests remain in place.

## Why No Rollback Is Needed

The recovered subtitle truth model is correct: helper input must not become authoritative target subtitle truth unless explicitly saved, and target subtitle currentness must derive from the authoritative target subtitle artifact.

This fix reconnects the missing source-lane input to that same truth path. No pre-PR1 rollback is needed because the bug is a narrow translation input binding gap, not a state/projection architecture regression.

## Preserved Behavior

- Helper-only translation remains available and non-authoritative unless the operator saves it.
- Normal subtitle workflow uses `source_subtitle_lane`, not helper text.
- Cue/timecodes are preserved by requiring SRT input.
- Target subtitle save-contract, subtitle currentness, no-dub/advisory fixes, and valid dub recovery remain unchanged.

## Remaining Before PR-4

PR-4 should still tighten broader four-layer state boundaries. This fix only resolves the source-subtitle translation binding path needed before that work resumes.
