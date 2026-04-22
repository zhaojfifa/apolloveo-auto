# VEOBASE01 PR-7: hot_follow_api.py service boundary reduction

- Branch name: `VeoBase01-pr7-hot-follow-api-boundary-reduction`
- Base branch: `VeoBase01`
- Base commit: `9f94cd2701b20d50f05eb00c2c3c0aac033bc242`

## Why this PR exists

`gateway/app/routers/hot_follow_api.py` still carried a large workbench/presentation helper block that duplicated service-layer logic. That kept the router as a payload assembler instead of a route/auth/dispatch entry layer and preserved split-brain risk between router-local workbench assembly and the shared view path.

This PR moves that logic behind `gateway/app/services/task_view.py` while preserving the existing router-level monkeypatch seams used by the validation harness.

## Scope

- move Hot Follow workbench/presentation helper ownership into `gateway/app/services/task_view.py`
- keep `hot_follow_api.py` as thin wrappers that inject router-local collaborators into the extracted service helpers
- preserve existing router-local helper names so route-level tests and compatibility seams still target the router surface
- keep publish/workbench endpoint behavior unchanged

## Non-goals

- no endpoint redesign
- no Hot Follow business-logic rewrite
- no translation changes
- no helper translation changes
- no subtitle save contract changes
- no dub changes
- no compose runtime changes
- no workbench contract rewrite
- no new-line abstraction work

## Files changed

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR7_HOT_FOLLOW_API_BOUNDARY_REDUCTION.md`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/task_view.py`

## Exact validations run

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `37 passed`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py -q`
  - result: `52 passed`
- synthetic exact-id surface probe on `9c755859d049` and `9280fcb9f0b1`
  - result: publish/workbench semantics remained aligned after the router-to-service extraction

## Regression sample results

Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not present in this workspace, so PR-7 reran the read-only synthetic surface probe with those exact task ids against the current publish/workbench surfaces.

Final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`

Compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status `pending`
- persisted repository state remains operationally in progress: `compose_status=running`

## Risks

- `task_view.py` now owns more of the shared Hot Follow workbench/presenter assembly, so mistakes there can affect both router and service callers
- the router still exposes wrapper helpers for testability and compatibility; if those wrappers drift from their injected collaborator set, coverage could become misleading
- line-count reduction in `hot_follow_api.py` is structural only; truth ownership still depends on keeping router wrappers thin

## Rollback path

- revert this branch/commit sequence
- or reset `VeoBase01` back to `9f94cd2701b20d50f05eb00c2c3c0aac033bc242` if PR-7 must be abandoned wholesale

## Acceptance judgment

- `hot_follow_api.py` no longer owns the main workbench/presentation helper implementations
- extracted helper logic now lives in `gateway/app/services/task_view.py`
- router wrappers preserve existing route-space collaborator seams without reabsorbing business truth ownership
- `hot_follow_api.py` line count reduced from `2368` to `2027`
- Hot Follow final-ready and compose-running guard semantics remained aligned in the regression probe
- accepted for PR-7 scope
