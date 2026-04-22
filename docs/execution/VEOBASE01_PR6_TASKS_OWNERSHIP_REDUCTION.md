# VEOBASE01 PR-6: tasks.py ownership reduction

- Branch name: `VeoBase01-pr6-tasks-ownership-reduction`
- Base branch: `VeoBase01`
- Base commit: `6a2caa764245cd722a6519320a93c9f04573cb14`

## Why this PR exists

`gateway/app/routers/tasks.py` still owned response assembly that did not belong in route space:

- generic publish-hub dispatch was still selecting and building the publish surface in the router
- the legacy `/v1/tasks/{task_id}/status` response was still assembled inline in the router
- reusable download/not-ready response helpers were still defined inside `tasks.py`

This PR moves those responsibilities into service modules so `tasks.py` is closer to route/auth/dispatch shell behavior without changing Hot Follow business semantics.

## Scope

- restore the VeoBase01 authority docs that were absent after refreshing `VeoBase01` from `main`
- move generic publish-hub dispatch into `gateway/app/services/task_router_presenters.py`
- move legacy `/v1/tasks/{task_id}/status` payload assembly into `gateway/app/services/task_router_presenters.py`
- move reusable not-ready/text/download helper logic into `gateway/app/services/task_download_views.py`
- rewire `tasks.py` routes to call service builders instead of assembling those payloads inline

## Non-goals

- no endpoint redesign
- no Hot Follow business-logic rewrite
- no translation changes
- no helper translation changes
- no subtitle save contract changes
- no dub changes
- no compose runtime changes
- no workbench contract change
- no new-line abstraction work

## Files changed

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR6_TASKS_OWNERSHIP_REDUCTION.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`
- `docs/reviews/VEOBASE01_POST_PR5_GATE_REVIEW.md`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_router_presenters.py`
- `gateway/app/services/task_download_views.py`
- `gateway/app/services/tests/test_task_router_presenters.py`
- `gateway/app/services/tests/test_task_download_views.py`

## Exact validations run

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/tasks.py gateway/app/services/task_router_presenters.py gateway/app/services/task_download_views.py gateway/app/services/task_view.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_task_download_views.py`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_task_download_views.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `33 passed`

## Regression sample results

Exact live task data for `9c755859d049` and `9280fcb9f0b1` is not present in this workspace, so the PR used the same read-only synthetic surface probe as the baseline refresh.

Final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`

Compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status `pending`
- persisted repository state remains operationally in progress: `compose_status=running`

## Risks

- restored VeoBase01 authority docs now ride in the same branch as PR-6 because refreshed `main` did not contain them
- generic task publish-hub dispatch now routes Hot Follow tasks through the service-level Hot Follow publish builder instead of the direct helper call
- download helper extraction is internal-only but touches multiple v1 deliverable endpoints

## Rollback path

- revert this branch/commit sequence
- or move `VeoBase01` back to `backup-VeoBase01-pre-refresh-20260422` if the refreshed baseline itself must be abandoned

## Acceptance judgment

- `tasks.py` no longer assembles generic publish-hub dispatch in route space
- legacy task-status payload assembly moved out of the router
- reusable download/not-ready payload helpers moved to services
- `tasks.py` line count dropped from `3421` to `3296`
- Hot Follow final-ready and compose-running guard semantics remained aligned in the read-only regression probe
- accepted for PR-6 scope
