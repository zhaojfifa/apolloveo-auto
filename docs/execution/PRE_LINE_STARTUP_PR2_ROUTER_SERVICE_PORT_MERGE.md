# Pre-Line Startup PR-2: Router / Service Port Merge

Date: 2026-04-20

## Gate Citation

This PR is governed by:

- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md`
- `docs/reviews/appendix_code_inventory.md`
- `docs/reviews/appendix_router_service_state_dependency_map.md`
- `docs/reviews/appendix_four_layer_state_map.md`

## Fix

- Replaced hidden lazy imports in `gateway/app/services/task_router_actions.py` with explicit registered action ports.
- Registered the current task-router action implementations from `gateway/app/routers/tasks.py` without adding new route behavior.
- Removed the direct `apollo_avatar.py` import from `gateway.app.routers.tasks` by moving operator key validation into `gateway/app/services/op_auth.py`.
- Added focused tests proving the task action bridge no longer lazy-imports `gateway.app.routers.tasks` and dispatches through registered ports.

## Not Fix

- No second/new production line work.
- No OpenClaw work.
- No broad platform abstraction.
- No compose ownership change.
- No move of the large dub/pipeline implementations yet; this PR only removes hidden router import masking and direct router-to-router auth coupling.

## Follow-Up

- Continue extracting the large task-router-owned dub and pipeline execution paths into service-owned implementations.
- PR-3 should keep compose ownership hardening separate from this port merge.
- PR-4 should continue state boundary tightening after router coupling is reduced.

## Validation

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/task_router_actions.py gateway/app/services/op_auth.py gateway/app/routers/tasks.py gateway/app/routers/hot_follow_api.py gateway/app/routers/apollo_avatar.py gateway/app/services/tests/test_task_router_actions.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/tests/test_task_router_actions.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`

Result: 29 passed.
