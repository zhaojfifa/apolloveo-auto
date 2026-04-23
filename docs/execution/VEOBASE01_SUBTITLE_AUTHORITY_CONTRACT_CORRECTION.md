# VEOBASE01 Subtitle Authority Contract Correction

Date: 2026-04-24
Branch: `VeoBase01-subtitle-authority-contract-correction`
Base SHA: `a1a6837eaf11e55a806db487ca7120a32ba3fd4e`

## Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from the indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/workbench_hub_response.contract.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
   - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
4. Sufficiency note:
   - this pass only corrects subtitle-authority ownership and acceptance rules
   - no broader scenario, advisory, or compose redesign was required
5. Missing-authority handling:
   - no indexed authority docs were missing

## Exact Ownership Correction

Authoritative target-subtitle success truth is now owned by:

- `gateway/app/services/hot_follow_subtitle_authority.py`

The previous split was:

- `run_subtitles_step()` in `gateway/app/services/steps_v1.py`
- `_hf_save_authoritative_target_subtitle()` in
  `gateway/app/routers/hot_follow_api.py`

After this pass:

- `steps_v1.py` no longer writes authoritative subtitle success truth directly
- `hot_follow_api.py` no longer writes authoritative subtitle success truth
  directly
- both call the new subtitle-authority service

## Exact Single Owner Chosen

Single owner:

- `persist_hot_follow_authoritative_target_subtitle(...)`
- `finalize_hot_follow_subtitles_step(...)`

Both functions live in:

- `gateway/app/services/hot_follow_subtitle_authority.py`

This module now owns:

- authoritative target subtitle acceptance
- authoritative target subtitle success persistence
- subtitle-step success/failure gating against authoritative truth

## Exact Success Gate Introduced

L1 subtitle success now requires L2 authoritative target subtitle truth.

`subtitles_status="ready"` is accepted only when all are true:

- target subtitle is explicitly authoritative
- semantic target subtitle body exists
- canonical target subtitle artifact exists
- `target_subtitle_current=true`
- `target_subtitle_current_reason="ready"`

This pass blocks subtitle-step success when:

- target subtitle is absent
- target subtitle is non-authoritative
- target subtitle is semantically empty
- translation is incomplete
- target subtitle is a source-copy / otherwise not current

## Exact Helper Boundary Correction

Helper side-channel was restored by preventing helper/non-authoritative subtitle
outcomes from satisfying subtitle-step success.

Concrete changes:

- helper-only / non-authoritative subtitle outcomes now persist
  `subtitles_status="failed"` instead of `ready`
- helper-side outcomes no longer stand in for authoritative target subtitle
  truth
- existing source-subtitle-lane helper failure persistence remains intact

This pass did not redesign advisory or no-dub/no-TTS logic. It corrected the
upstream truth boundary first.

## Exact Empty-Body Rejection Rule

Authoritative subtitle success now requires semantic subtitle content.

Rule:

- physical file existence alone is insufficient
- timing-only / empty-body SRT cannot become authoritative subtitle success

Step-path effect:

- subtitles step no longer uploads/accepts target subtitle artifact as success
  when the generated target subtitle body is semantically empty

API-path effect:

- manual/save authoritative target subtitle path now rejects non-current or
  invalid authoritative target subtitle writes before success persistence

## Modules Changed

- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/services/steps_v1.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/tests/test_steps_v1_subtitles_step.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

## Validations Run

- `python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_authority.py gateway/app/services/steps_v1.py gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_consumes_result_contract_for_myanmar gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_marks_vi_translation_incomplete_without_step_error gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_marks_myanmar_translation_incomplete_without_step_error gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_treats_preserved_source_audio_as_helper_only gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_delegates_authoritative_truth_to_service gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_rejects_timing_only_target_subtitle_before_success gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_save_authoritative_target_subtitle_delegates_to_single_owner gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_save_authoritative_target_subtitle_rejects_source_copy_before_success gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_persists_subtitle_authority_failure gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_preserves_current_target_subtitle gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs -q`: `11 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure -q`: `1 passed`
- `git diff --check`: passed

Validation note:

- broader `test_hot_follow_subtitle_binding.py` still contains two unrelated
  subtitle-render expectation failures already present on this branch
- those failures are outside the subtitle-authority contract boundary changed
  here

## Live Representative Task Replay

Live representative task replay was not available in this workspace.

- exact real-task replay for `6b40d86589da`, `944e2e8e6f0d`, `91990da2b72f`,
  `796bf811a43b` was not run
- evidence for this pass is focused in-process coverage only

## Rollback Path

- compare against the review head:
  - `git diff a1a6837eaf11e55a806db487ca7120a32ba3fd4e..VeoBase01-subtitle-authority-contract-correction`
- return to the review head:
  - `git checkout VeoBase01-subtitle-authority-repair`
- discard this branch locally if needed after comparison:
  - `git branch -D VeoBase01-subtitle-authority-contract-correction`

## Acceptance Judgment

Accepted for the narrow subtitle-authority contract scope.

- subtitle authority now has a single owner
- subtitle-step success is now bound to authoritative/current target subtitle
  truth
- helper-only/non-authoritative subtitle outcomes no longer contaminate mainline
  subtitle success truth
- empty-body subtitle success is now impossible on the corrected paths
- `VeoBase01` is safer for the later resumed contract-tightening pass

## Closure Continuation - 2026-04-24

### Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from the indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/workbench_hub_response.contract.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
   - this execution note
4. Missing-authority handling:
   - no indexed authority docs were missing

### Exact Remaining Gap From The Prior Correction Pass

The previous contract correction prevented fake subtitle success, but closure
was still incomplete for two shapes:

- authoritative target subtitle could exist locally while projection still
  returned empty `edited_text` / `srt_text` / `primary_editable_text` /
  `dub_input_text` because only storage-backed keys were consulted
- persisted upstream target-formation failure truth such as
  `target_subtitle_translation_incomplete` could still collapse back to generic
  `subtitle_missing` when no current target artifact text was loaded

That left the contract gate correct, but the formation/binding projection still
open.

### Exact Formation Path Repaired

The repaired path is:

1. authoritative target subtitle is created in the single-owner subtitle
   authority flow
2. projection now reloads target subtitle text from:
   - override file first
   - storage artifact second
   - local workspace target subtitle artifact third
3. subtitle artifact physical existence now treats the local workspace target
   subtitle artifact as valid evidence when the storage copy is not yet
   available
4. once authoritative/current target subtitle truth is present, projection now
   restores:
   - `edited_text`
   - `srt_text`
   - `primary_editable_text`
   - `dub_input_text`

### Exact Helper Failure Propagation Before / After

Before:

- helper/provider failure could be persisted upstream
- but when target subtitle text stayed empty, projection could still degrade the
  state to generic `subtitle_missing`
- the true blocking reason was therefore partially lost in the subtitle lane

After:

- helper/provider failure remains side-channel only
- but when it explains why target subtitle formation did not complete, the
  explicit persisted failure reason survives projection
- non-helper authoritative failure reasons such as
  `target_subtitle_translation_incomplete` also survive projection instead of
  being rewritten to `subtitle_missing`

### Exact Dub-Input Binding Before / After

Before:

- `dub_input_text` depended on successful storage-backed target subtitle reload
- if the authoritative subtitle existed only in the local workspace/current
  artifact path, dub input stayed empty and downstream still saw
  `target_subtitle_empty`

After:

- `dub_input_text` derives from authoritative/current target subtitle truth
  loaded from override, storage, or local workspace artifact
- when target subtitle truth is current and semantically valid,
  `dub_input_text` is non-empty and bound to `target_subtitle`

### Modules Changed In The Closure Continuation

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

### Validations Run

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -k "local_authoritative_target or translation_incomplete_reason or source_lane_failure_persists_subtitle_authority_failure or source_lane_persists_full_target_srt or helper_failure_preserves_authoritative_outputs or does_not_treat_timing_only_target_artifact_as_existing_truth"`: `6 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -k "vi_currentness_blocks_false_done_states or myanmar_currentness_blocks_false_done_states or helper_translate_429_persists_sanitized_helper_failure"`: `3 passed`
- `git diff --check`: passed

Validation note:

- `test_manual_subtitle_save_clears_helper_translate_failure` currently returns
  `422` in this workspace; that endpoint issue was not introduced by this pass
  and is outside the subtitle-authority closure scope addressed here

### Real Representative Task Verification

Live representative task replay was still unavailable in this workspace.

- exact local replay for `2825a683c861`, `6b40d86589da`, `944e2e8e6f0d`,
  `91990da2b72f`, and `796bf811a43b` was not possible
- those ids were not present in the local repo artifacts or local
  `shortvideo.db`
- acceptance for this continuation therefore relies on focused in-process
  coverage only

### Acceptance Judgment

Accepted for the remaining subtitle-authority closure scope.

- the corrected contract base remains intact
- target subtitle formation projection is now closed for the storage-missing /
  local-authoritative-artifact shape
- helper/provider and translation-incomplete failure truth no longer disappears
  into generic `subtitle_missing`
- authoritative target subtitle to `dub_input_text` binding is restored
- this branch is now a safer merge candidate for subtitle-authority repair
  completion before later contract tightening resumes
