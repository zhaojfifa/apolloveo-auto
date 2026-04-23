# VEOBASE01 Subtitle Authority Repair

Date: 2026-04-23
Branch: `VeoBase01-subtitle-authority-repair`
Base SHA: `7e2e56b873f59537bf6d33a51b854343631bca63`

## Reading Declaration

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from indexes:
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/workbench_hub_response.contract.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
4. Missing-authority handling:
   - none

## Exact Root Cause

The source-subtitle translation lane raised sanitized `GeminiSubtitlesError`
responses without persisting the failure into authoritative subtitle state.
That left the task with no current target subtitle artifact or text, but without
truthful subtitle failure state. Downstream projection then saw empty target
subtitle fields and could collapse into `subtitle_missing` and `no_dub`/`no_tts`
symptoms instead of surfacing the upstream helper/provider failure.

There was also duplicated subtitle-lane projection in `hot_follow_api.py` that
did not project helper failure metadata or helper-derived readiness reasons,
which kept API/runtime views out of sync with the authoritative failure shape.

## Exact Modules Changed

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_REPAIR.md`

## Exact Subtitle-Authority Chain Repaired

1. Source-subtitle lane provider/helper failures now persist:
   - helper failure status/reason/message/provider
   - authoritative subtitle failure state when no current target subtitle exists
   - `target_subtitle_current=false`
   - subtitle/publish/compose readiness reset for the failed-no-target shape
2. Subtitle-lane projection now prefers the upstream helper failure reason over
   generic `subtitle_missing` when target subtitle truth is absent because the
   helper/provider failed.
3. Subtitle-to-dub binding remains strict:
   - `dub_input_text` stays empty until authoritative target subtitle is current
   - existing current target subtitles remain authoritative and are preserved on
     later helper/provider failure
4. Workbench no-dub projection no longer hides upstream subtitle-authority
   failure when helper translation failed and subtitle readiness is false.

## Helper Failure Propagation Before / After

Before:

- source-subtitle lane provider failure returned HTTP 409
- helper failure fields were not reliably written for this lane
- subtitle state could stay `running` or other non-authoritative values
- effective target subtitle remained empty
- downstream saw `subtitle_missing` or `target_subtitle_empty`

After:

- source-subtitle lane provider failure writes helper failure fields
- if no authoritative target subtitle is current, subtitle state becomes failed
- reason/message/provider are visible in authoritative task state
- subtitle projection reports helper/provider failure as the blocking truth

## Subtitle -> Dub Input Binding Before / After

Before:

- target subtitle could be missing while subtitle state looked clean or partial
- `dub_input_text` became empty with weak failure attribution
- downstream no-dub/no-TTS classification could hide the upstream failure class

After:

- `dub_input_text` remains bound only to current authoritative target subtitle
- missing target subtitle because of helper/provider failure projects as that
  failure, not a fake clean-success subtitle state
- no-dub suppression now keeps the upstream subtitle-authority failure visible

## Validation Results

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_presenters.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `git diff --check`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_persists_subtitle_authority_failure gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_preserves_current_target_subtitle gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs -q`: `4 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py::test_publish_hub_keeps_scene_pack_pending_non_blocking_when_final_ready -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_voice_led_retry_success_resolves_tts_replace_and_final_ready -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_contract_runtime_projection_rules.py::test_projection_runtime_final_ready_dominates_publish_truth -q`: `1 passed`

## Real Representative Task Verification

Exact live replay was not possible in this workspace.

- searched repo/workspace for `6b40d86589da`, `944e2e8e6f0d`, `91990da2b72f`: no local artifacts found
- queried local `shortvideo.db` `tasks` table for those ids: no rows found

The acceptance evidence here is in-process/runtime coverage only.

## Rollback Path

- compare pre-repair base to repair branch:
  - `git diff VeoBase01..VeoBase01-subtitle-authority-repair`
- return to pre-repair base:
  - `git checkout VeoBase01`
- preserve reference to the previously recorded broken-tip safety tag:
  - `VeoBase01-PreSubtitleAuthorityRollback`

## Acceptance Judgment

Accepted for the narrow repair scope.

- subtitle authority is repaired for the source-subtitle helper/provider failure
  shape on `VeoBase01`
- helper/provider failure is no longer silently swallowed for that lane
- target subtitle missing no longer projects as a fake clean-success subtitle
  state for the repaired shape
- downstream no-dub/no-TTS projection no longer hides the upstream
  subtitle-authority failure for that shape
- this branch is a safe base for the next subtitle-authority-focused tightening
  round
