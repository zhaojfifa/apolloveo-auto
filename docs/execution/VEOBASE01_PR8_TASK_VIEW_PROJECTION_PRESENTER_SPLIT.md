# VEOBASE01 PR-8: task_view.py projection/presenter split

- Branch name: `VeoBase01-pr8-task-view-projection-presenter-split`
- Base branch: `VeoBase01`
- Base commit: `d25d592d7d92a4da1b841149c75024890c16c87b`

## Why this PR exists

`gateway/app/services/task_view.py` still mixed authoritative Hot Follow workbench input assembly with surface/presenter shaping. That kept projection and presentation logic interleaved inside one file and made it harder to prove that workbench-facing payload shaping was consuming a single normalized truth path.

This PR splits the module into an authoritative projection layer and a presenter layer, while leaving `task_view.py` as an import-stable facade for existing callers.

## Scope

- add `gateway/app/services/task_view_projection.py` for authoritative pipeline/deliverable/workbench projection assembly
- add `gateway/app/services/task_view_presenters.py` for publish/workbench presenters and presentation aggregates
- reduce `gateway/app/services/task_view.py` to a thin re-export facade
- keep Hot Follow publish/workbench behavior unchanged

## Non-goals

- no endpoint redesign
- no Hot Follow business-logic rewrite
- no translation changes
- no helper translation changes
- no subtitle save contract changes
- no dub changes
- no compose runtime changes
- no workbench contract hardening beyond structural split
- no new-line abstraction work

## Files changed

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR8_TASK_VIEW_PROJECTION_PRESENTER_SPLIT.md`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_projection.py`

## Exact validations run

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view.py gateway/app/services/task_view_projection.py gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/hot_follow_runtime_bridge.py`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `89 passed`
- synthetic exact-id surface probe on `9c755859d049` and `9280fcb9f0b1`
  - result: publish/workbench semantics remained aligned after the projection/presenter split

## Regression sample results

Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not present in this workspace, so PR-8 reran the read-only synthetic surface probe with those exact task ids against the current publish/workbench surfaces.

Final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`

Compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status `pending`
- persisted repository state remains operationally in progress: `compose_status=running`

## Risks

- `task_view.py` is now only a facade, so callers that previously relied on implementation-local imports must continue to use exported symbols only
- the projection/presenter split relies on keeping `task_view_projection.py` authoritative and `task_view_presenters.py` presentation-only; future drift between those modules would recreate the same ownership problem under new filenames
- `task_view_presenters.py` is materially smaller than the old file but still substantial, so PR-9 remains necessary to reduce post-projection contract mutation

## Rollback path

- revert this branch/commit sequence
- or reset `VeoBase01` back to `d25d592d7d92a4da1b841149c75024890c16c87b` if PR-8 must be abandoned wholesale

## Acceptance judgment

- `task_view.py` is reduced from `964` lines to a `48` line facade
- authoritative projection logic now lives in `gateway/app/services/task_view_projection.py`
- presenter/payload shaping now lives in `gateway/app/services/task_view_presenters.py`
- Hot Follow final-ready and compose-running guard semantics remained aligned in the regression probe
- accepted for PR-8 scope
