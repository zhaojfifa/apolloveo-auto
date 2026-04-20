# Appendix: Router / Service / State Dependency Map

Date: 2026-04-20

## Runtime Entrypoint

`gateway/app/main.py` creates the FastAPI app and includes:

- `tasks_router.pages_router`
- `tasks_router.api_router`
- `hot_follow_api_router`
- auth/tools/publish/admin routers
- `v1_actions.router` mounted at `/v1`
- `v17_pack_router`

Startup side effects:

- database table creation and schema patching
- provider config table creation
- storage service initialization
- workspace directory creation
- Whisper warmup
- route table logging

Implication: runtime boot is not line-isolated. It initializes global storage/model/provider infrastructure before any line-level execution.

## Primary Request Paths

### Generic task compose path

```text
POST /api/tasks/{task_id}/compose
  -> gateway/app/routers/tasks.py::compose_task
  -> tasks.py::_execute_compose_task_contract
  -> CompositionService.prepare_hot_follow_compose_task
  -> CompositionService.resolve_fresh_final_key
  -> CompositionService.compose
  -> CompositionService._prepare_workspace
  -> CompositionService._run_ffmpeg
  -> WorkerGateway.execute
  -> InternalSubprocessWorkerAdapter.execute
  -> subprocess.run
  -> CompositionService._upload_and_verify
  -> policy_upsert via router wrapper
  -> hub_loader
```

Risk: generic task compose path is Hot-Follow-shaped and uses Hot Follow compose service contract.

### Hot Follow compose path

```text
POST /api/hot_follow/tasks/{task_id}/compose
  -> gateway/app/routers/hot_follow_api.py::compose_hot_follow_final_video
  -> hot_follow_api.py::_execute_hot_follow_compose_contract
  -> CompositionService.prepare_hot_follow_compose_task
  -> CompositionService.resolve_fresh_final_key
  -> CompositionService.compose
  -> Worker Gateway-backed FFmpeg execution
  -> policy_upsert via hot_follow_api.py::_policy_upsert
  -> _service_build_hot_follow_workbench_hub
```

Risk: two compose HTTP paths still exist and must stay behaviorally aligned.

### Hot Follow workbench path

```text
GET /api/hot_follow/tasks/{task_id}/workbench_hub
  -> hot_follow_api.py::get_hot_follow_workbench_hub
  -> hot_follow_api.py::_service_build_hot_follow_workbench_hub
  -> task_view.py::build_hot_follow_workbench_hub
  -> subtitle lane loader
  -> composed state loader
  -> pipeline state loaders
  -> route/content/audio helpers
  -> deliverables loader
  -> presentation aggregate builders
  -> compute_hot_follow_state
  -> ready gate engine
  -> advisory builder
```

Risk: this path crosses routers, service view assembly, status policy, ready gate, skills, storage object checks, and compatibility defaults.

### Hot Follow dub path

```text
POST /api/hot_follow/tasks/{task_id}/dub
  -> hot_follow_api.py::rerun_hot_follow_dub
  -> task_router_actions.py::rerun_dub_entry
  -> lazy import gateway.app.routers.tasks::rerun_dub
  -> tasks.py::_run_dub_job
  -> provider/TTS/subtitle/audio fit logic
  -> policy_upsert
```

Risk: `task_router_actions.py` is a service-looking bridge that still imports router functions. New lines must not copy this pattern.

### Pipeline background path

```text
POST /api/tasks/{task_id}/run
  -> tasks.py::run_task_pipeline
  -> BackgroundTasks
  -> tasks.py::_run_pipeline_background
  -> parse/subtitles/dub/pack/compose paths
  -> policy_upsert / asyncio.run step functions
```

Risk: background orchestration is router-owned.

## Import Dependency Notes

### `tasks.py` imports

`tasks.py` has 64 imports, including:

- FastAPI, Pydantic, responses/security
- config/settings/storage
- schemas
- repository/deps
- `steps_v1`
- status policy service and Hot Follow state
- parse, Xiongmao provider, TTS policy
- Hot Follow language profiles, dub text guard, subtitle providers
- artifact storage, scenes service, publish service, task state service
- cleanup, pipeline config, subtitle probe, task semantics
- media validation, workspace, compose helpers, media helpers, task view helpers, presenters, voice state, artifact helpers, Hot Follow runtime bridge, line binding, compose service

Conclusion: `tasks.py` still knows too much about runtime internals.

### `hot_follow_api.py` imports

`hot_follow_api.py` has 49 imports, including:

- config/schemas/deps/storage/repository
- status policy service and Hot Follow state
- source audio policy, TTS policy, dub guard
- subtitle providers/helpers
- artifact storage, media validation, scenes service
- `steps_v1`
- workspace/constants/compose/media helpers
- task router actions
- compose service
- Hot Follow language/currentness/skills/voice/workbench presenter
- line binding and task view

Conclusion: the file is a Hot Follow runtime hub, not just HTTP transport.

### Known import cycle

AST import scan found one concrete cycle:

```text
gateway.app.adapters.repo_sql
gateway.app.db
gateway.app.models
```

Router coupling risk is mostly lazy/directional rather than an AST cycle:

- `task_router_actions.py` lazily imports router functions from `gateway.app.routers.tasks`.
- `hot_follow_runtime_bridge.py` exposes compatibility surfaces for helpers that moved to services.

## State Write Dependency Map

### Main write facade

```text
routers/tasks.py::_policy_upsert
routers/hot_follow_api.py::_policy_upsert
  -> gateway/app/services/status_policy/service.py::policy_upsert
  -> status_policy.registry.get_status_policy
  -> StatusPolicy.reconcile_after_step
  -> coerce_final_status
  -> repo.upsert
```

The facade filters writes, but callers still construct update dicts.

### Other write surfaces

- `steps_v1.py::_update_task` call sites
- `TaskStateService.update_fields()`
- file/storage uploads in routers/services
- direct repo helper paths in task repository adapters

## Execution Boundary Map

### Worker Gateway-backed

```text
CompositionService._run_ffmpeg
  -> WorkerRequest(line_id="hot_follow_line", step_id="compose", worker_capability="ffmpeg")
  -> get_worker_gateway().execute
  -> WorkerGatewayRegistry.resolve
  -> InternalSubprocessWorkerAdapter.execute
```

Implemented timeout/error envelope:

- success/failed/timeout result
- returncode in `output_facts`
- stderr/stdout in `raw_output`
- retry hint

### Direct subprocess still present

- `tasks.py::_ensure_mp3_audio`
- `tasks.py::_detect_subtitle_streams`
- multiple `steps_v1.py` media/provider helper paths

Rule: future subprocess execution should use Worker Gateway or an explicit service adapter with equivalent timeout/error contract.

## Projection Dependency Map

```text
task_view.py::build_hot_follow_workbench_hub
  -> object_exists and storage-derived URLs
  -> subtitle lane state
  -> voice state
  -> composed state
  -> pipeline state
  -> deliverables list
  -> artifact_facts/current_attempt/operator_summary
  -> compute_hot_follow_state
  -> ready_gate
  -> advisory
  -> UI defaults
```

This is the current projection choke point. It must not become the pattern for a second line.

## Dependency Risk Summary

| Risk | Evidence | Impact |
| --- | --- | --- |
| Router-owned orchestration | `tasks.py::_run_pipeline_background`, `_run_dub_job`, `_execute_compose_task_contract` | New lines would add branches to a God router |
| Hot Follow-specific generic paths | Generic `/api/tasks/{id}/compose` calls Hot Follow compose service | New line would need awkward branching or duplicate route |
| Lazy router service bridge | `task_router_actions.py` imports `tasks.py` functions | Service layer is not cleanly below routers |
| Workbench God function | `task_view.py::build_hot_follow_workbench_hub` 492 lines | Response shape and truth layers are hard to reason about |
| Multi-write state | 37 `_policy_upsert` in `tasks.py`, 18 in `hot_follow_api.py` | SSOT depends on convention and tests |
| Mixed execution envelopes | Worker Gateway for compose, direct subprocess elsewhere | Timeout/retry/error consistency is incomplete |
