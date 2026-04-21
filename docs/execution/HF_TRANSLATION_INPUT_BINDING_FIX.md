# Hot Follow Translation Input Binding Fix

Date: 2026-04-21

## Scope

This is a narrow Hot Follow follow-up after the target-subtitle truth recovery. It does not start PR-4, does not roll back PR-1, and does not add second-line or platform work.

## Root Cause

The operator-facing `翻译为越南语/翻译为缅语` button was bound to helper-input semantics instead of the parsed source subtitle lane.

Code evidence:

- `gateway/app/static/js/hot_follow_workbench.js::translateMmBtn` read `assistedInputTextEl` first, then `subtitlesTextEl`, and posted only `{text, target_lang}`.
- `gateway/app/static/js/hot_follow_workbench.js::assistedTranslateBtn` reused the same `translateCurrentSubtitles(text)` helper.
- `gateway/app/routers/hot_follow_api.py::translate_hot_follow_subtitles` chose the translation source exclusively from `HotFollowTranslateRequest.text`.

That made the main subtitle workflow translate helper-only text such as `this`, returning plain translated text such as `cai nay`, instead of translating the parsed/full source subtitle SRT into a target-language SRT.

## Why No Rollback Is Needed

PR-1 exposed the SRT-first editor contract, but this failure is not caused by the recovered subtitle truth model. The remaining bug is an action binding bug: the frontend and endpoint did not distinguish helper-only candidate translation from full source-subtitle-lane translation.

The existing recovered truth remains valid:

- helper/candidate input is not authoritative target subtitle truth;
- authoritative target subtitle truth must be saved through the target subtitle owner path;
- target subtitle currentness and dub readiness derive from that authoritative artifact.

## Changed Files

- `gateway/app/static/js/hot_follow_workbench.js`
  - main translate button now sends `input_source: "source_subtitle_lane"`;
  - assisted translation now sends `input_source: "helper_only_text"`;
  - the main source-lane translation reloads the hub after the backend writes the target subtitle main object.

- `gateway/app/routers/hot_follow_api.py`
  - `HotFollowTranslateRequest` now carries explicit `input_source`;
  - helper-only translation remains non-persistent and returns helper text only;
  - source-subtitle-lane translation loads the parsed source SRT from the task, preserves cue/timecodes, translates every segment, and writes the result through the authoritative target subtitle save path.

- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
  - added focused coverage for helper-only translation staying helper-only;
  - added focused coverage for full source-lane translation producing and persisting target SRT.

## Preserved Boundaries

- Helper-only translation does not pretend to be full subtitle translation.
- Source-lane translation does not fall back to helper text.
- Translation provider failures still remain helper/provider-scoped.
- The target subtitle save-contract fix remains the authoritative write path.
- Valid translated target subtitles continue to re-enable the dub path through existing subtitle currentness and empty-dub recovery logic.

## Remaining Before PR-4

PR-4 should still address broader four-layer boundary tightening. This fix only makes the translation action input source explicit and restores the correct full-subtitle workflow.
