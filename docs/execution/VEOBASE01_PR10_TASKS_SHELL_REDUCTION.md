# VEOBASE01 PR-10: tasks.py shell reduction follow-up

- Branch name: `VeoBase01-pr10-tasks-shell-reduction`
- Base branch: `VeoBase01`
- Base commit: `0b50635d86dfd6e86f095d0ce7d65972077c7d38`

## Purpose

Continue pushing `gateway/app/routers/tasks.py` toward a thinner route/auth/dispatch shell by removing additional reusable non-route helper ownership that still lived in the router.

## Scope

- move generic audio/final stream meta and range-handling logic into `gateway/app/services/task_stream_views.py`
- move subtitle-stream detection/cache helpers into `gateway/app/services/task_subtitle_detection.py`
- keep compatibility wrapper names in `tasks.py` for existing tests and call sites
- keep endpoint behavior unchanged

## Non-goals

- no route topology rewrite
- no task business-logic rewrite
- no translation changes
- no helper-translation changes
- no subtitle save contract changes
- no dub / compose / ffmpeg / worker runtime changes
- no Hot Follow state/projection contract changes

## Files changed

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR10_TASKS_SHELL_REDUCTION.md`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_stream_views.py`
- `gateway/app/services/task_subtitle_detection.py`
- `gateway/app/services/tests/test_task_stream_views.py`
- `gateway/app/services/tests/test_task_subtitle_detection.py`

## Exact validation commands run

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/tasks.py gateway/app/services/task_stream_views.py gateway/app/services/task_subtitle_detection.py gateway/app/services/tests/test_task_stream_views.py gateway/app/services/tests/test_task_subtitle_detection.py`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_task_stream_views.py gateway/app/services/tests/test_task_subtitle_detection.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `89 passed`

## Regression evidence

Exact live replay is not available in this workspace, so PR-10 reran the in-process synthetic publish/workbench probe with the fixed task ids.

Final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, `compose_status=done`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose status `done`

Compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, `compose_status=pending`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose status `pending`
- persisted repository state remains operationally in progress: `compose_status=running`

Additional checks:

- contract layer still does not mutate authoritative truth after projection; PR-10 does not touch task-view contract or state-policy modules
- publish/workbench alignment remained unchanged in the synthetic probe

## Risks

- `tasks.py` still keeps compatibility wrappers for `_resolve_audio_meta`, `_resolve_final_meta`, `_parse_http_range`, and subtitle-detection helpers, so ownership is reduced but not eliminated
- stream error/416 behavior is sensitive to header details; the extraction preserved existing response semantics but still touches low-level download paths
- `tasks.py` remains large after this PR, so additional shell reduction is still required

## Rollback path

- revert this branch/commit sequence
- or reset `VeoBase01` back to `0b50635d86dfd6e86f095d0ce7d65972077c7d38` if PR-10 must be abandoned wholesale

## Acceptance judgment

- additional reusable non-route stream/detection helper logic moved out of `tasks.py`
- `tasks.py` line count reduced from `3296` to `3074`
- compatibility wrappers preserved endpoint/test behavior
- Hot Follow publish/workbench semantics remained aligned
- accepted for PR-10 scope
