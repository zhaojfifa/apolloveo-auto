# VEOBASE01 PR-9: task_view_workbench_contract.py contract hardening

- Branch name: `VeoBase01-pr9-workbench-contract-hardening`
- Base branch: `VeoBase01`
- Base commit: `0ffe60ed8486f5a2388bcfc5b9196a27cb633d43`

## Why this PR exists

`gateway/app/services/task_view_workbench_contract.py` still contained late post-ready-gate payload mutation helpers that rewrote compose/final presentation state after authoritative projection had already been established by `compute_hot_follow_state()`. That kept the contract layer acting as a silent truth patcher instead of a schema/normalization adapter.

This PR removes those late mutations and leaves only shape builders plus compatibility aliases that do not rewrite L1/L2/L3 truth.

## Scope

- remove contract-layer helpers that mutated final deliverable and compose state after ready-gate evaluation
- keep top-level `compose_allowed` / `compose_allowed_reason` as compatibility aliases sourced from `ready_gate`
- keep `task_view.py` facade patchable for existing service-level tests without moving ownership back into the facade
- keep Hot Follow publish/workbench behavior unchanged

## Non-goals

- no endpoint redesign
- no Hot Follow business-logic rewrite
- no translation changes
- no helper translation changes
- no subtitle save contract changes
- no dub changes
- no compose runtime changes
- no render-default retune work
- no new-line abstraction work

## Files changed

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR9_WORKBENCH_CONTRACT_HARDENING.md`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_workbench_contract.py`

## Exact validations run

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_runtime_bridge.py`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `100 passed`
- synthetic exact-id surface probe on `9c755859d049` and `9280fcb9f0b1`
  - result: publish/workbench semantics remained aligned after removing post-ready-gate contract mutation

## Supplemental validation note

The broader file `gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q` still reports two existing failures in `compose_service.py` subtitle-render defaults:

- `test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow`
- `test_subtitle_render_signature_tracks_minimal_retune_defaults`

This PR did not modify `gateway/app/services/compose_service.py`, so those failures were treated as unrelated existing drift rather than PR-9 regressions. The directly affected contract-layer test from that file was run and passed.

## Regression sample results

Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not present in this workspace, so PR-9 reran the read-only synthetic surface probe with those exact task ids against the current publish/workbench surfaces.

Final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`

Compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status `pending`
- persisted repository state remains operationally in progress: `compose_status=running`

## Risks

- top-level `compose_allowed` and `compose_allowed_reason` are still compatibility aliases, so downstream consumers that rely on them must eventually move to `ready_gate`
- the `task_view.py` facade remains patchable for compatibility, which is useful for tests but still a surface that can be misused if new ownership is pushed back into it
- broader subtitle-render default drift still exists in `compose_service.py`, outside the scope of this PR

## Rollback path

- revert this branch/commit sequence
- or reset `VeoBase01` back to `0ffe60ed8486f5a2388bcfc5b9196a27cb633d43` if PR-9 must be abandoned wholesale

## Acceptance judgment

- contract-layer post-ready-gate mutation of final deliverable and compose state has been removed
- `task_view_workbench_contract.py` now keeps schema shaping and compatibility aliasing only
- authoritative final/compose truth stays owned by upstream projection plus `compute_hot_follow_state()`
- Hot Follow final-ready and compose-running guard semantics remained aligned in the regression probe
- accepted for PR-9 scope
