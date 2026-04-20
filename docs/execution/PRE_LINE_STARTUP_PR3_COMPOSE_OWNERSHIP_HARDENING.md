# PR-3 Compose Ownership Hardening

Date: 2026-04-20

Branch: `pr/compose-ownership-hardening`

Active gate citations:
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/appendix_router_service_state_dependency_map.md`
- `docs/reviews/appendix_four_layer_state_map.md`

## Fix

PR-3 narrows Hot Follow compose execution to a single compose-owned lifecycle path:

- `CompositionService.execute_hot_follow_compose_contract(...)` is now the compose startup/finalize owner.
- `CompositionService._write_compose_state(...)` is now the single compose state write entry for compose-owned transitions.
- Generic `/api/tasks/{task_id}/compose` and Hot Follow `/api/hot_follow/tasks/{task_id}/compose` keep their response behavior but delegate lifecycle ownership to the compose service.

The compose owner now owns:

- stale-running recovery
- compose lock conflict projection
- per-task mutex acquire/release
- `compose_lock_until` acquire/release writes
- request compose-plan preparation writes
- `pending/running -> done`
- `running -> failed`
- compose-input derive failure terminalization through existing failure update shaping
- final artifact write-back through the existing compose result update path

## Previous Ownership Split

Before this PR, both `gateway/app/routers/tasks.py` and `gateway/app/routers/hot_follow_api.py` carried duplicated compose transaction scripts. Router code directly:

- checked/recovered stale-running compose state
- acquired compose locks
- wrote `compose_lock_until`
- wrote running state
- wrote lipsync warnings
- wrote success/failure finalization
- released locks and cleared `compose_lock_until`

That made routers secondary compose owners and left two places where future line work could accidentally add compose state semantics.

## New Single-Owner Path

Current compose startup path:

1. Router validates task existence and maps the request payload.
2. Router calls `CompositionService.execute_hot_follow_compose_contract(...)`.
3. The compose service owns lock, stale recovery, running state, compose execution, success/failure finalize, and lock release.
4. Router maps the returned contract to the existing JSON response.

State writes inside the compose lifecycle go through:

- `CompositionService._write_compose_state(...)`
- `status_policy.service.policy_upsert(...)`

Router-side compose lifecycle writes were removed from both compose entry helpers.

## Not Fix

This PR does not change:

- task view/workbench contract shape
- router/service port merge boundaries outside compose delegation
- subtitle visual tuning
- dubbing route selection
- no-TTS/BGM/preserve route semantics
- UI copy or login behavior
- second-line onboarding or OpenClaw work

## Preserved Live Invariants

The implementation preserves existing compose behavior for:

- normal TTS compose
- legal no-TTS/subtitle-only compose route behavior
- heavy-input derived compose and derive-failure retry behavior
- stale-running recovery before false 409
- existing workbench response projection after compose

## Validation

Focused validation run:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/routers/tasks.py gateway/app/routers/hot_follow_api.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py -q`
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache /opt/homebrew/bin/python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q`

Reverse ownership scans:

- router compose lifecycle helpers now delegate to `CompositionService.execute_hot_follow_compose_contract(...)`
- no reverse imports from `gateway.app.routers.tasks` remain under `gateway/app`
- `task_compose_lock`, stale recovery, running/failure update builders, and `compose_lock_until` lifecycle are now used by the compose service owner, not router lifecycle scripts

## Follow-Up

PR-4 should continue with four-layer state boundary tightening. It should not reinterpret this PR as permission to add a second production line or broaden compose into a generic platform abstraction.
