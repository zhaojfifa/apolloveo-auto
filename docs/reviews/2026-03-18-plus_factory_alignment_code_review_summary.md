# Factory Alignment Code Review Summary

Date: 2026-04-20

## Verdict

**Only after prerequisites. Do not add a new production line yet.**

ApolloVeo now has real factory primitives, but the current runtime is still too Hot-Follow-shaped and router-heavy to safely onboard a second production line.

## What Already Matches The Intended Architecture

- `gateway/app/lines/base.py` and `gateway/app/lines/hot_follow.py` provide a real runtime `ProductionLine` registry.
- `gateway/app/services/line_binding_service.py` resolves line binding from `task.kind`.
- `docs/contracts/hot_follow_ready_gate.yaml` is consumed by `gateway/app/services/ready_gate/hot_follow_rules.py`.
- `gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state()` is a real derived-state entrypoint.
- `gateway/app/services/compose_service.py::CompositionService` is a real compose service boundary.
- Worker Gateway exists and compose FFmpeg execution goes through `gateway/app/services/workers/internal_subprocess_worker.py`.
- `skills/hot_follow` is a real read-only advisory bundle loaded by `gateway/app/services/skills_runtime.py`.

## Main Mismatches

- `tasks.py` is still a God router: 3,480 lines, 87 functions, 47 route handlers, 37 `_policy_upsert` references.
- `hot_follow_api.py` is still a large Hot Follow transaction script: 2,325 lines, 71 functions, 18 `_policy_upsert` references.
- `task_view.py::build_hot_follow_workbench_hub()` is 492 lines and mixes object facts, attempt facts, derived state, projection, advisory, line metadata, and compatibility repair.
- Deliverable profile, asset sink profile, SOP profile, worker profile, and confirmation policy are not fully runtime-enforced.
- The four-layer state model is real but not yet protected by a single write-owner or versioned response schema.

## Highest-Risk Evidence

- Largest functions:
  - `tasks.py::_run_dub_job()` 673 lines
  - `task_view.py::build_hot_follow_workbench_hub()` 492 lines
  - `steps_v1.py::run_dub_step()` 472 lines
  - `steps_v1.py::run_post_generate_pipeline()` 443 lines
- Direct write/filter points:
  - `tasks.py`: 37 `_policy_upsert`, 8 `_repo_upsert`
  - `hot_follow_api.py`: 18 `_policy_upsert`
  - `steps_v1.py`: 18 `_update_task`
- Direct subprocess remains outside compose Worker Gateway:
  - `tasks.py`: 2 `subprocess.run`
  - `steps_v1.py`: 7 `subprocess.run`

## Current Hot Follow Status

- Business completion: high.
- Operator completion: medium-high.
- Contract completion: medium.
- State-model completion: medium.
- Service-boundary completion: medium.
- Skills extraction completion: early MVP.
- Safe as reusable engineering template: **not yet**.

## No-Go Zones

- No new production line route stack.
- No copying Hot Follow workbench payload assembly.
- No new business logic in `tasks.py`.
- No skills writes to repo/deliverables/ready gate/status.
- No worker direct writes to accepted deliverable truth.
- No publish readiness outside ready gate/status policy.

## Ordered Prerequisites

1. Freeze new-line onboarding.
2. Centralize task truth and deliverable truth writes.
3. Split Hot Follow workbench assembly into four explicit layers.
4. Add versioned response models for workbench/publish hub.
5. Make deliverable profile runtime-readable.
6. Make ready-gate/status-policy selection truly line-driven.
7. Move remaining subprocess execution behind Worker Gateway or explicit service adapters.
8. Replace lazy router action bridges with service calls.
9. Add line contract conformance tests.
10. Only then start new-line onboarding.
