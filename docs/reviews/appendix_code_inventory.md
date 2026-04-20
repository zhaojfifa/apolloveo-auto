# Appendix: Code Inventory

Date: 2026-04-20

This appendix records concrete code metrics used by `2026-03-18-plus_factory_alignment_code_review.md`.

## Oversized Runtime Files

| File | Lines | Imports | Functions | Classes | Route handlers | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `gateway/app/routers/tasks.py` | 3,480 | 64 | 87 | 9 | 47 | Generic task router plus Hot Follow residual orchestration and background steps |
| `gateway/app/routers/hot_follow_api.py` | 2,325 | 49 | 71 | 6 | 15 | Hot Follow HTTP, compatibility helpers, workbench/publish/compose wrappers |
| `gateway/app/services/steps_v1.py` | 2,413 | 41 | 42 | 1 | 0 | Parse/subtitles/dub/pack/post-generate step logic |
| `gateway/app/services/compose_service.py` | 2,137 | 25 | 69 | 9 | 0 | Compose service, FFmpeg command construction, workspace, final upload |
| `gateway/app/services/task_view.py` | 1,123 | 19 | 16 | 0 | 0 | Hot Follow workbench/publish assembly and projection |
| `gateway/app/services/status_policy/hot_follow_state.py` | 346 | 5 | 10 | 0 | 0 | Hot Follow derived state and ready-gate side effects |
| `gateway/app/services/hot_follow_route_state.py` | 452 | 4 | 9 | 1 | 0 | Compose-input, audio-lane, selected route and current attempt projection |
| `gateway/app/services/ready_gate/engine.py` | 206 | 3 | 1 | 5 | 0 | Declarative ready gate evaluator |
| `gateway/app/services/ready_gate/hot_follow_rules.py` | 360 | 7 | 23 | 0 | 0 | Hot Follow YAML gate loader and signal extractors |

## Largest Functions

| File | Function | Lines | Location |
| --- | --- | ---: | --- |
| `tasks.py` | `_run_dub_job` | 673 | 2545-3217 |
| `task_view.py` | `build_hot_follow_workbench_hub` | 492 | 632-1123 |
| `steps_v1.py` | `run_dub_step` | 472 | 1031-1502 |
| `steps_v1.py` | `run_post_generate_pipeline` | 443 | 1908-2350 |
| `steps_v1.py` | `run_subtitles_step` | 217 | 812-1028 |
| `compose_service.py` | `_prepare_workspace` | 187 | 1115-1301 |
| `tasks.py` | `_run_pipeline_background` | 168 | 1550-1717 |
| `steps_v1.py` | `run_pack_step` | 161 | 1505-1665 |
| `hot_follow_route_state.py` | `build_hot_follow_current_attempt_summary` | 142 | 311-452 |
| `hot_follow_api.py` | `create_hot_follow_task_local_upload` | 122 | 1745-1866 |
| `hot_follow_api.py` | `_execute_hot_follow_compose_contract` | 110 | 241-350 |
| `tasks.py` | `create_task_local_upload` | 110 | 1919-2028 |
| `hot_follow_api.py` | `_hf_deliverables` | 105 | 1157-1261 |
| `tasks.py` | `_execute_compose_task_contract` | 100 | 2240-2339 |
| `compose_service.py` | `_upload_and_verify` | 98 | 2040-2137 |
| `compose_service.py` | `_derive_safe_compose_input` | 97 | 1483-1579 |

## Router Endpoints

### `gateway/app/routers/tasks.py`

47 route handlers:

- Pages/static/download/status:
  - `/favicon.ico`
  - `/tasks`
  - `/tasks/new`
  - `/tasks/baseline/new`
  - `/tasks/newtasks`
  - `/tasks/apollo-avatar/new`
  - `/tasks/avatar/new`
  - `/ui`
  - `/tools/hub`
  - `/tools/{tool_id}`
  - `/v1/tasks/{task_id}/raw`
  - `/v1/tasks/{task_id}/subs_origin`
  - `/v1/tasks/{task_id}/subs_mm`
  - `/v1/tasks/{task_id}/mm_txt`
  - `/v1/tasks/{task_id}/audio_mm` HEAD/GET
  - `/v1/tasks/{task_id}/final` HEAD/GET
  - `/v1/tasks/{task_id}/pack`
  - `/v1/tasks/{task_id}/scenes`
  - `/v1/tasks/{task_id}/publish_bundle`
  - `/v1/tasks/{task_id}/publish_hub`
  - `/v1/tasks/{task_id}/status`
  - `/tasks/{task_id}`
  - `/tasks/{task_id}/publish`
  - `/op/dl/{task_id}`
  - `/d/{code}`
- API:
  - `POST /tasks/probe`
  - `POST /tasks`
  - `POST /tasks/local_upload`
  - `POST /tasks/{task_id}/bgm`
  - `PATCH /tasks/{task_id}`
  - `GET /tasks`
  - `GET /tasks/{task_id}/text`
  - `POST /tasks/{task_id}/mm_edited`
  - `GET /tasks/{task_id}`
  - `GET /tasks/{task_id}/events`
  - `GET /tasks/{task_id}/publish_hub`
  - `POST /tasks/{task_id}/compose`
  - `POST /tasks/{task_id}/run`
  - `POST /tasks/{task_id}/parse`
  - `POST /tasks/{task_id}/scenes`
  - `POST /tasks/{task_id}/pack`
  - `POST /tasks/{task_id}/dub`
  - `POST /tasks/{task_id}/publish`
  - `POST /tasks/{task_id}/subtitles`
  - `DELETE /tasks/{task_id}`

### `gateway/app/routers/hot_follow_api.py`

15 route handlers:

- `POST /hot_follow/tasks`
- `POST /hot_follow/tasks/local_upload`
- `POST /hot_follow/tasks/{task_id}/bgm`
- `GET /hot_follow/tasks/{task_id}/publish_hub`
- `GET /hot_follow/tasks/{task_id}/workbench_hub`
- `PATCH /hot_follow/tasks/{task_id}/audio_config`
- `PATCH /hot_follow/tasks/{task_id}/compose_plan`
- `PATCH /hot_follow/tasks/{task_id}/source_url`
- `PATCH /hot_follow/tasks/{task_id}/subtitles`
- `POST /hot_follow/tasks/{task_id}/translate_subtitles`
- `POST /hot_follow/tasks/{task_id}/compose`
- `POST /hot_follow/tasks/{task_id}/dub`
- `POST /hot_follow/tasks/{task_id}/probe`
- `POST /hot_follow/tasks/{task_id}/run`
- `POST /hot_follow/tasks/{task_id}/scene_pack` deprecated

## Write / Execution Hotspots

| File | `_policy_upsert` | `_repo_upsert` | `_update_task` | `subprocess.run` | `TemporaryDirectory` | `BackgroundTasks` | `asyncio.run` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `tasks.py` | 37 | 8 | 0 | 2 | 1 | 8 | 10 |
| `hot_follow_api.py` | 18 | 0 | 0 | 0 | 0 | 6 | 0 |
| `steps_v1.py` | 0 | 0 | 18 | 7 | 1 | 0 | 0 |
| `compose_service.py` | 0 | 0 | 0 | 1 import / Worker Gateway execution | 1 | 0 | 0 |
| `task_view.py` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Service Boundary Inventory

| Area | Runtime file | Status |
| --- | --- | --- |
| Line registry | `gateway/app/lines/base.py`, `gateway/app/lines/hot_follow.py` | Implemented for Hot Follow |
| Line binding | `gateway/app/services/line_binding_service.py` | Implemented minimal resolver |
| Status policy registry | `gateway/app/services/status_policy/registry.py` | Kind-based; partially line-aware through ready-gate binding |
| Hot Follow state | `gateway/app/services/status_policy/hot_follow_state.py` | Implemented |
| Ready gate engine | `gateway/app/services/ready_gate/engine.py` | Implemented |
| Hot Follow ready gate loader | `gateway/app/services/ready_gate/hot_follow_rules.py` | Implemented YAML-backed |
| Compose service | `gateway/app/services/compose_service.py` | Implemented but large |
| Worker Gateway | `gateway/app/services/worker_gateway.py`, `worker_gateway_registry.py` | Implemented MVP; Hot Follow compose registration hard-coded |
| Skills runtime | `gateway/app/services/skills_runtime.py` | Implemented MVP |
| Hot Follow skills advisory | `gateway/app/services/hot_follow_skills_advisory.py` | Implemented read-only advisory |
| Workbench/publish assembly | `gateway/app/services/task_view.py` | Serviceized but God-function risk remains |
| State write service | `gateway/app/services/task_state_service.py` | Exists but not dominant write path |

## Test Inventory

Total test lines under `gateway/app`: 10,380.

High-signal coverage areas:

- Ready gate line binding: `gateway/app/services/ready_gate/tests/test_line_binding.py`
- Status/ready gate/workbench: `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py` (1,198 lines)
- Current dub/subtitle state: `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py` (1,421 lines)
- Compose service contract: `gateway/app/services/tests/test_compose_service_contract.py`
- Compose freshness: `gateway/app/services/tests/test_hf_compose_freshness.py`
- Compose duration: `gateway/app/services/tests/test_compose_video_master_duration.py`
- Artifact facts and route projection: `gateway/app/services/tests/test_hot_follow_artifact_facts.py`
- Skills advisory/runtime: `gateway/app/services/tests/test_hot_follow_skills_advisory.py`, `test_skills_runtime.py`
- Worker Gateway: `gateway/app/services/tests/test_worker_gateway.py`
- Task router presenters: `gateway/app/services/tests/test_task_router_presenters.py`

Coverage gaps:

- No generic line onboarding conformance suite.
- No versioned workbench response-model conformance suite.
- No generic deliverable profile loader tests because the loader does not exist yet.
- No generic asset sink profile runtime tests.
- Worker Gateway coverage is MVP-level, not end-to-end for all parse/subtitle/dub execution paths.
