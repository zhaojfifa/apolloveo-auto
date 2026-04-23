# VeoBase01 Subtitle Authority Rollback 1

Date: 2026-04-23
Rollback branch: `VeoBase01-subtitle-authority-rollback1`

## Current Broken Tip

- Branch observed before rollback: `VeoBase01`
- Broken-tip SHA: `7e2e56b873f59537bf6d33a51b854343631bca63`
- Broken-tip commit: `Expand Hot Follow contract runtime pass 3`

## Rollback Safety Tag

- Tag name: `VeoBase01-PreSubtitleAuthorityRollback`
- Tag type: annotated
- Tag target SHA: `7e2e56b873f59537bf6d33a51b854343631bca63`
- Purpose: preserve the broken pass-3 tip for later comparison without
  continuing work on top of it.

## Rollback Target

- Rollback target SHA: `3e6dc57a7c780886359035a90e99c0cc9130fc81`
- Target commit: `Merge VeoBase01 contract runtime expansion pass 2`
- Reason selected: it is the immediate parent before pass 3. This matches the
  one-version rollback requirement and preserves the last baseline where the
  known smaller current-attempt/advisory misclassification bug could still be
  retried through the mainline.

## Rollback Method

Commands used:

- `git tag -a VeoBase01-PreSubtitleAuthorityRollback 7e2e56b873f59537bf6d33a51b854343631bca63 -m "Safety tag before subtitle authority rollback"`
- `git checkout -B VeoBase01-subtitle-authority-rollback1 3e6dc57a7c780886359035a90e99c0cc9130fc81`

No patch was applied to the broken tip. No destructive reset of
`origin/VeoBase01` was performed. The broken tip remains reachable by tag and
by `origin/VeoBase01` until an explicit branch update decision is made.

## Why Rollback One, Not Two

Rollback one was chosen because the immediately previous baseline is the
documented "small-bug-but-mainline-works" target:

- it predates pass 3 subtitle-authority breakage
- it preserves pass-2 contract-runtime work
- it keeps the known smaller first-dub-failure interpretation bug available as
  the next controlled redo problem

Rollback two is not selected unless this rollback-one branch fails the
subtitle-authority gates below.

## Gate 1 — Target Subtitle Authority

Result: passed by fixture/in-process evidence.

Evidence:

- subtitle generation/currentness tests passed
- source-lane target subtitle persistence test passed
- helper-only preserved-source path does not overwrite target subtitle truth
- workbench subtitle-currentness and ready-gate tests passed in the broader
  suite

Expected good behavior covered:

- target subtitle can be persisted as authoritative target subtitle
- `target_subtitle_current=true` is produced for valid target subtitle output
- `subtitle_ready=true` and non-empty `dub_input_text` are available from the
  subtitle lane when target subtitle truth is valid
- invalid/source-copy/translation-incomplete target subtitle remains blocked
  instead of silently becoming current

Gate-specific command:

- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_generate_subtitles_keeps_preserved_source_audio_helper_out_of_target_truth gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
- Result: `6 passed`

## Gate 2 — Helper Translation Failure Propagation

Result: passed by fixture/in-process evidence.

Evidence:

- helper translation provider failure persists sanitized authoritative helper
  failure fields
- helper failure preserves authoritative target subtitle outputs
- manual subtitle save clears helper failure state
- helper translation projection remains helper-layer only and does not become
  target subtitle truth

Expected good behavior covered:

- provider failure is explicitly represented through helper error reason/message
- helper translation failure does not silently disappear as clean no-dub truth
- helper output does not overwrite target subtitle authority

## Validation Commands

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_projection.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/task_view_presenters.py gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/hot_follow_route_state.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/services/steps_v1.py`
  - Result: passed
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
  - Result: `46 passed`, `2 failed`
  - Failure note: the two failures were subtitle-rendering microtune assertions
    for `FontSize` / render signature, not subtitle-authority or helper
    failure propagation gates.
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -k 'not compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not subtitle_render_signature_tracks_minimal_retune_defaults' -q`
  - Result: `46 passed`, `2 deselected`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`
  - Result: `60 passed`

The first attempted gate-specific command referenced two stale test names and
returned pytest collection errors. It was corrected with the explicit six-test
gate command listed above.

`git diff --check` will be run after this documentation update.

## Live Replay

No live representative Hot Follow replay was run in this workspace. The
validation evidence is fixture/in-process coverage only.

## Mainline Usability

Judgment: usable as rollback baseline.

The rollback-one branch restores the last baseline where subtitle authority and
helper-failure propagation pass the required gates. The older smaller bug is
still expected to remain: first-dub-failure current-attempt/advisory
misclassification can still occur and should be redone from this baseline in a
fresh, narrower subtitle-authority-aware branch.

## Rollback Two Decision

Rollback two is not needed now.

Reason:

- Gate 1 passed
- Gate 2 passed
- broader publish/workbench/ready-gate fixture coverage passed
- the remaining observed failures are unrelated subtitle-rendering microtune
  expectations, not subtitle-authority failures

## Rollback / Compare Path

- Broken tip comparison: `git diff 3e6dc57a7c780886359035a90e99c0cc9130fc81..VeoBase01-PreSubtitleAuthorityRollback`
- Return to broken tip for investigation only:
  `git checkout VeoBase01-PreSubtitleAuthorityRollback`
- Continue safe redo work from:
  `VeoBase01-subtitle-authority-rollback1`
