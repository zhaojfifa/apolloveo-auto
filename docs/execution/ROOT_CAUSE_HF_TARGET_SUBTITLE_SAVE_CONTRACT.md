# Root Cause: Hot Follow Target Subtitle Save Contract

Date: 2026-04-20

Branch: `hotfix/hf-target-subtitle-save-contract`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_line_contract_skill_readiness.md`

## Exact Root Cause

The regression was admitted at the authoritative target-subtitle write contract.

After PR-1, the Hot Follow workbench target subtitle editor became SRT-first:

- `gateway/app/services/subtitle_helpers.py::hf_subtitle_lane_state` exposes `primary_editable_text` from the saved target subtitle text and sets `primary_editable_format="srt"`.
- `gateway/app/services/task_view_workbench_contract.py::_subtitles_section` projects that value as `subtitles.primary_editable_text` / `subtitles.primary_editable_format`.
- `gateway/app/static/js/hot_follow_workbench.js::renderSubtitles` loads `primary_editable_text || srt_text || edited_text` into the target editor.
- `gateway/app/static/js/hot_follow_workbench.js::patchSubtitles` saves the editor body as JSON `{ "srt_text": ... }`.

The backend save endpoint still treated parseable SRT structure as valid target-subtitle truth even when cue bodies were empty:

- `gateway/app/routers/hot_follow_api.py::_hf_is_srt_text` returned true for timing-only SRT because `gateway/app/steps/subtitles.py::_parse_srt_to_segments` returns segments for blocks with valid time ranges even when `text_lines` is empty.
- `gateway/app/routers/hot_follow_api.py::patch_hot_follow_subtitles` wrote the normalized text to the override file before any semantic validation.
- `gateway/app/routers/hot_follow_api.py::_hf_sync_saved_target_subtitle_artifact` uploaded the same timing-only SRT as the canonical target artifact.

That let physical artifact truth and semantic readiness diverge: `mm.srt` could exist while the subtitle body was semantically empty. Downstream currentness then correctly reported `target_subtitle_empty`, but artifact presence and presentation could still see a target artifact, creating split-brain state across artifact existence, readiness, no-dub routing, and operator summary.

## Why PR-1 Exposed It

PR-1 split workbench projection and made the target subtitle main object explicit and SRT-first in `task_view_workbench_contract.py`. That was the correct product direction, but it exposed an older backend contract weakness: the save path did not distinguish "valid SRT container" from "valid target subtitle content".

Before PR-1, plain edited text and legacy fallback surfaces made the issue easier to miss. After PR-1, the main target editor could preserve SRT timing with empty cue bodies and submit it as the authoritative target subtitle object.

## PR-2 / PR-3 Contribution

PR-2 (`adc72300d564e2506adabeabf2ead24926640415`) did not introduce the subtitle save regression. Its relevant changes were router/service port merge and action bridge cleanup; it did not change `/api/hot_follow/tasks/{task_id}/subtitles` save ownership or target subtitle semantic validation.

PR-3 (`0435c15`) did not cause the subtitle save/truth regression directly. It hardened compose ownership and moved compose lifecycle responsibility into `CompositionService`; it did not change the target subtitle PATCH save contract.

## Why Helper Translate 429 Was Not The Main Root Cause

The helper translate 429 path exposed a symptom: helper translation could fail and leave target subtitle empty. PR #54 and PR #55 correctly scoped helper/provider failure so it does not become fake subtitle success or misleading no-dub guidance.

The deeper bug was independent of provider exhaustion: any semantically-empty SRT body submitted to the authoritative save endpoint could be accepted as target artifact truth. That is why the fix belongs at target-subtitle save validation and lane derivation, not only helper UI/error handling.

## What Changed

The fix adds a narrow semantic target-subtitle check at the owner boundary:

- `gateway/app/services/hot_follow_subtitle_currentness.py`
  - exposes `normalize_subtitle_semantic_text`
  - exposes `has_semantic_target_subtitle_text`
  - uses semantic text presence for target currentness
- `gateway/app/routers/hot_follow_api.py::patch_hot_follow_subtitles`
  - rejects semantically-empty target subtitle submissions with `422 target_subtitle_semantically_empty`
  - does this before override file write, artifact upload, helper failure clearing, no-dub recovery, or task truth updates
- `gateway/app/routers/hot_follow_api.py::_hf_sync_saved_target_subtitle_artifact`
  - refuses to upload semantically-empty target subtitle artifacts
- `gateway/app/services/subtitle_helpers.py::hf_sync_saved_target_subtitle_artifact`
  - mirrors the same artifact-write guard for service callers
- `gateway/app/services/subtitle_helpers.py::hf_subtitle_lane_state`
  - treats a physical timing-only target artifact as not existing target subtitle truth
- `gateway/app/services/subtitle_helpers.py::hf_dub_input_text`
  - refuses timing-only SRT as dub input
- `gateway/app/routers/hot_follow_api.py::_hf_subtitle_lane_state`
  - keeps the router compatibility lane aligned with the service lane
- `gateway/app/routers/hot_follow_api.py::_hf_dub_input_text`
  - keeps the router compatibility dub input helper aligned with service truth

## Answers To Review Questions

1. Source of `primary_editable_text` / `primary_editable_format`:
   `hf_subtitle_lane_state` loads target subtitle text from the override file or canonical target subtitle object, then exposes `primary_editable_text=edited_text` and `primary_editable_format="srt"`. `_subtitles_section` projects those into the workbench payload.

2. Frontend save payload:
   `hot_follow_workbench.js::patchSubtitles` sends `{ "srt_text": srtText || "" }` to `/api/hot_follow/tasks/{task_id}/subtitles`.

3. Backend landing point:
   `gateway/app/routers/hot_follow_api.py::patch_hot_follow_subtitles`.

4. Authoritative target artifact write:
   `patch_hot_follow_subtitles` normalizes text, writes the override file, then `_hf_sync_saved_target_subtitle_artifact` uploads canonical `mm.srt` / language-specific target subtitle artifact and updates `mm_srt_path`.

5. Can timing-only SRT be saved before this fix:
   Yes. `_hf_is_srt_text` accepted SRT with valid timing and empty cue bodies because `_parse_srt_to_segments` still returned a segment.

6. Downstream derivation:
   - `subtitle_exists` came from `subtitle_artifact_exists`.
   - `subtitle_ready` came from target currentness.
   - `target_subtitle_current` came from `compute_hot_follow_target_subtitle_currentness`.
   - `dub_input_text` was set only when `subtitle_ready` was true.
   - `no_dub / target_subtitle_empty` could be derived from empty target readiness while a physical target artifact still existed.

7. Bug classification:
   Primary cause: backend save contract admitted invalid authoritative target subtitle truth.
   Secondary propagation: subtitle lane derivation treated physical artifact presence as target artifact truth even when cue bodies were semantic-empty.
   Not primary: PR-3 compose ownership, helper translate 429, or UI-only editor behavior.

## Not Fix

This is not PR-4 and does not refactor the four-layer state platform.

No changes were made to:

- second-line onboarding
- OpenClaw
- compose ownership
- subtitle visual tuning
- router-service port merge architecture
- generic subtitle platform design
- UI redesign

## Validation

Focused validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_currentness.py gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_subtitle_lane_keeps_target_editor_empty_when_only_origin_exists gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_subtitle_lane_does_not_treat_timing_only_target_artifact_as_existing_truth gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_sync_saved_target_subtitle_artifact_refuses_semantically_empty_srt gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_rejects_semantically_empty_srt_without_replacing_truth gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_hot_follow_live_muted_no_tts_route_recommends_compose_no_tts -q`

Result: `23 passed`.

Observed unrelated failure:

- Running all of `gateway/app/services/tests/test_hot_follow_subtitle_binding.py` also executes subtitle visual tuning expectations for old `FontSize=14.0/13.2` defaults. Current main returns `16/15`. This PR did not change subtitle visual tuning, and that area is explicitly out of scope.
