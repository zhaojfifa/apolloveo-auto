# Hot Follow Target Subtitle Split-Brain Follow-Up

Date: 2026-04-21

Branch: `hotfix/hf-target-subtitle-save-contract`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_line_contract_skill_readiness.md`

## Exact Remaining Root Cause

PR #56 fixed the authoritative save admission path, but existing invalid target subtitle artifacts could still split presentation truth after the fact.

Remaining breakpoints:

- `gateway/app/services/subtitle_helpers.py::hf_subtitle_lane_state` and router compatibility `_hf_subtitle_lane_state` marked `subtitle_artifact_exists=false` for timing-only target SRT, but still exposed the timing-only file body through `edited_text`, `srt_text`, and `primary_editable_text`.
- `gateway/app/services/task_view_workbench_contract.py::_subtitles_section` used the independently loaded `subtitles_text` fallback for `edited_text` / `srt_text` / `primary_editable_text`, bypassing lane-authoritative subtitle truth.
- `gateway/app/services/task_view.py::hf_deliverables` and router compatibility `_hf_deliverables` projected `deliverables[kind=subtitle]` from physical `mm_srt_path` existence and `subtitles_status`, so an invalid timing-only target artifact could show `done` while `artifact_facts.subtitle_exists=false`.
- `gateway/app/services/hot_follow_route_state.py::build_hot_follow_artifact_facts` could expose a subtitle URL even when `subtitle_exists=false`.

That left editor hydration, deliverables, artifact facts, and currentness reading different versions of target subtitle truth.

## Files / Symbols Changed

- `gateway/app/services/subtitle_helpers.py::hf_subtitle_lane_state`
  - hides semantically-empty target artifact text from authoritative editor fields.
- `gateway/app/routers/hot_follow_api.py::_hf_subtitle_lane_state`
  - keeps router compatibility behavior aligned with service truth.
- `gateway/app/services/task_view_workbench_contract.py::_subtitles_section`
  - hydrates editor fields from lane-authoritative `primary_editable_text`, not raw loaded subtitle text.
- `gateway/app/services/task_view.py::hf_deliverables`
  - marks subtitle deliverable done only when semantic target subtitle artifact truth exists.
- `gateway/app/routers/hot_follow_api.py::_hf_deliverables`
  - keeps router compatibility deliverable projection aligned.
- `gateway/app/services/hot_follow_route_state.py::build_hot_follow_artifact_facts`
  - only exposes `subtitle_url` when `subtitle_exists=true`.
- Focused tests in:
  - `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
  - `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`

## Why Revert Is Not Needed

PR-1's SRT-first target editor remains the correct main-object design. The bug was not the SRT-first design; it was that legacy/raw physical subtitle text could bypass lane-authoritative semantic truth during workbench projection and deliverable projection.

The fix keeps the SRT-first contract and makes the projection surfaces consume the corrected owner truth.

## What Was Fixed

- Timing-only blank SRT no longer hydrates as the current authoritative editable subtitle.
- `deliverables[kind=subtitle]` no longer reports `done` for semantically invalid target subtitle artifacts.
- `artifact_facts.subtitle_exists=false` now aligns with `artifact_facts.subtitle_url=null`.
- `subtitles.primary_editable_text`, `subtitles.srt_text`, `subtitles.edited_text`, `subtitle_ready`, and `target_subtitle_current` now align for timing-only invalid artifacts.
- Helper translate 429 remains helper-scoped.
- Valid saved target subtitle still re-enables dub.
- Genuine intended no-dub/no-TTS flow remains covered by existing regression.

## What Remains For PR-4

PR-4 still needs the broader state-boundary tightening:

- remove remaining duplicated router compatibility projections
- reduce mixed L1/L2/L3/L4 logic in workbench assembly
- make deliverable projection contract-first instead of helper-specific
- keep ready gate and artifact facts as explicit typed state snapshots rather than hidden dict coupling

## Validation

Focused validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/hot_follow_route_state.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_subtitles_keep_srt_as_primary_editable_object gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_does_not_hydrate_timing_only_target_artifact gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_subtitle_lane_keeps_target_editor_empty_when_only_origin_exists gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_subtitle_lane_does_not_treat_timing_only_target_artifact_as_existing_truth gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_sync_saved_target_subtitle_artifact_refuses_semantically_empty_srt gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_rejects_semantically_empty_srt_without_replacing_truth gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_hot_follow_live_muted_no_tts_route_recommends_compose_no_tts -q`

Result: `25 passed`.

