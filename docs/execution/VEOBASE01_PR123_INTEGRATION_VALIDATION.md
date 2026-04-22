# VeoBase01 PR-1/PR-2/PR-3 Integration Validation

Date: 2026-04-22

Branch: `VeoBase01`

## Purpose

This note records the internal VeoBase01 integration of the first three reconstruction slices before PR-4 starts.

Main is not updated by this step. This is VeoBase01-only integration.

## Exact Merge Order

1. PR-1 branch: `VeoBase01-pr1-contract-freeze-runtime-binding`
   - Result: merge commit `53c33ba`
   - Scope: contract/runtime binding conformance tests and workbench section conformance assertions.
2. PR-2 branch: `VeoBase01-pr2-typed-workbench-and-four-layer-state-freeze`
   - Result: merge commit `945b85f`
   - Conflict resolution: kept both PR-1 section conformance assertions and PR-2 typed `HotFollowWorkbenchResponse` validation in the ready-gate test.
   - Scope: typed Hot Follow workbench response model and four-layer state contract freeze.
3. PR-3 branch: `VeoBase01-pr3-router-service-ownership-boundary`
   - Result: merge commit `731a296`
   - Scope: engineering index discipline and router/service presentation ownership boundary.

Follow-up integration fix:

- Service-owned Hot Follow presentation helpers now resolve default collaborators at call time instead of binding function objects at import time. This preserves service ownership while keeping tests and router compatibility wrappers able to inject patched collaborators.
- Hot Follow deliverable presentation now falls back when optional subtitle-lane inspection fails because of unavailable workspace paths. This keeps deliverable projection presentation-safe and does not change translation, dub, compose, or authoritative artifact truth.

## Files And Doc Surfaces Verified

Verified present and cross-linked:

- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- root governance files: `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

Engineering index discipline verified:

- document priority is explicit and keeps root governance highest
- task-oriented reading paths are present
- VeoBase01-specific entry docs are linked
- forbidden doc misuse is documented
- PR pre-read and write-back checklists exist
- new-line onboarding gate exists

## Contract/Runtime Integration

Line contract/runtime integration:

- `docs/contracts/line_contract.schema.json` is covered by `gateway/app/services/tests/test_veobase01_contract_conformance.py`
- Hot Follow runtime line binding is covered by `get_line_runtime_binding`
- status runtime binding consumes line contract refs through `get_status_runtime_binding`
- workbench payload includes line metadata and hook refs

Typed workbench integration:

- `gateway/app/services/contracts/hot_follow_workbench.py::HotFollowWorkbenchResponse` validates representative runtime payloads.
- Runtime workbench hub validation is covered in the ready-gate test.
- Wire response shape remains unchanged.

Four-layer state assignment:

- L1 `pipeline_step_status`: parse/subtitles/dub/pack/compose step rows and status only.
- L2 `artifact_facts`: artifact existence, freshness, audio lane facts, compose input facts, helper translation fact flags.
- L3 `current_attempt`: dub currentness, audio readiness, compose status/reason, redub/recompose flags, current subtitle source.
- L4 `ready_gate` / `operator_summary` / `advisory` / presentation: gate decisions and operator/UI projection derived from L2/L3.

## Integrated Validation Run

Required validation:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/contracts/__init__.py gateway/app/services/contracts/hot_follow_workbench.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/task_view.py gateway/app/services/tests/test_hot_follow_workbench_contract.py gateway/app/services/tests/test_veobase01_contract_conformance.py`
  - Result: passed
- `git diff --check`
  - Result: passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_workbench_contract.py gateway/app/services/tests/test_veobase01_contract_conformance.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py::test_service_workbench_projects_empty_dub_reason gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py::test_hot_follow_api_deliverables_use_dry_key_not_source_audio_key -q`
  - Result: passed, `79 passed`

Representative business/runtime validation:

- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_source_audio_policy_persistence.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q -k 'not compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not subtitle_render_signature_tracks_minimal_retune_defaults'`
  - Result: passed, `145 passed, 2 deselected`
  - The two deselected tests assert compose subtitle styling constants unrelated to PR-1/PR-2/PR-3 integration. Compose runtime behavior was not changed in this integration step.

Real external live-task replay was not run in this workspace. The current live evidence remains:

- URL Hot Follow task `c084b276e819`: parse done, subtitles done, dub done, compose done, final exists, `compose_ready=true`, `publish_ready=true`.
- Local Hot Follow task `8501fc94c1c8`: parse done, subtitles done, dub done, `tts_voiceover_plus_source_audio` path valid.

## URL Path Result

Representative URL-path validation passed through the Hot Follow workbench route tests:

- workbench hub returns HTTP 200
- parse/subtitle/audio/compose/final-ready projections remain aligned
- `HotFollowWorkbenchResponse` validates the runtime payload
- ready gate `compose_ready` and `publish_ready` stay true when current final output is fresh

This preserves the current URL task baseline evidence from `c084b276e819`.

## Local Path Result

Representative local-path validation passed through source audio policy, current dub state, subtitle binding, and dry voiceover deliverable tests:

- subtitle binding remains guarded
- source-audio-preserved plus TTS voiceover path remains represented by `tts_voiceover_plus_source_audio`
- dry TTS voiceover deliverable is preferred over preserved source audio where appropriate
- app import smoke passes

This preserves the current local task baseline evidence from `8501fc94c1c8`.

## State Consistency Result

No split-brain was found across:

- `artifact_facts`
- `current_attempt`
- `ready_gate`
- `operator_summary`
- `advisory`
- `deliverables`

The integrated tests validate that L4 presentation consumes service-derived L2/L3 facts and that typed workbench validation does not change the wire response shape.

## PR-4 Readiness

VeoBase01 is ready to start PR-4 after this integration.

Expected next branch:

- `VeoBase01-pr4-line-runtime-consumption-and-skills-boundary`

PR-4 must remain scoped to:

- runtime consumption of line registry refs
- skills bundle boundary / loader stub
- worker profile references
- deliverable profile references
- asset sink profile references

PR-4 must not implement a second line and must not change translation, dub, or compose business behavior.

