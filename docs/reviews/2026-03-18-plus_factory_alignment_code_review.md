# 2026-03-18+ Factory Alignment Code Review

Date: 2026-04-20

Scope: read-only architecture and code review of the current ApolloVeo runtime after the Hot Follow heavy-input stability merge. Code is treated as truth when docs and code diverge.

Reviewed evidence:

- Runtime entrypoint: `gateway/app/main.py`
- Primary routers: `gateway/app/routers/tasks.py`, `gateway/app/routers/hot_follow_api.py`
- Core services: `gateway/app/services/compose_service.py`, `gateway/app/services/task_view.py`, `gateway/app/services/status_policy/hot_follow_state.py`, `gateway/app/services/hot_follow_route_state.py`, `gateway/app/services/ready_gate/*`, `gateway/app/services/skills_runtime.py`, `gateway/app/services/worker_gateway*`
- Line code: `gateway/app/lines/base.py`, `gateway/app/lines/hot_follow.py`, `gateway/app/services/line_binding_service.py`
- Contracts/docs: `docs/baseline/ARCHITECTURE_BASELINE.md`, `docs/contracts/status_ownership_matrix.md`, `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`, `docs/contracts/hot_follow_line_contract.md`, `docs/contracts/hot_follow_ready_gate.yaml`, `docs/contracts/skills_runtime_contract.md`, `docs/contracts/worker_gateway_runtime_contract.md`, `docs/adr/ADR-task-router-decomposition.md`, `docs/adr/ADR-phase2-skills-worker-planning.md`
- Tests: Hot Follow state/status/workbench, compose, ready gate, skills, line binding, worker gateway tests under `gateway/app/services/**/tests`

Related appendices:

- `docs/reviews/appendix_code_inventory.md`
- `docs/reviews/appendix_router_service_state_dependency_map.md`
- `docs/reviews/appendix_four_layer_state_map.md`
- `docs/reviews/appendix_line_contract_skill_readiness.md`

## Executive Judgment

ApolloVeo is partially aligned with the intended production-factory architecture, but it is not yet safe to add a new production line as a normal engineering act.

The current code has real factory primitives:

- `ProductionLine` and `LineRegistry` exist and Hot Follow is runtime-registered in `gateway/app/lines/hot_follow.py`.
- Hot Follow ready gate is YAML-backed through `docs/contracts/hot_follow_ready_gate.yaml` and loaded by `gateway/app/services/ready_gate/hot_follow_rules.py::load_hot_follow_gate_spec`.
- `compute_hot_follow_state()` is a real status-policy entrypoint.
- `CompositionService` is a real service boundary for compose, with Worker Gateway-backed FFmpeg execution.
- `skills/hot_follow` is a real read-only advisory bundle loaded through `gateway/app/services/skills_runtime.py`.

But the foundation is still Hot-Follow-shaped rather than line-general:

- `tasks.py` is 3,480 lines, 87 functions, 47 route handlers, and still has 37 `_policy_upsert` call sites, 10 `asyncio.run` calls, and the largest function is `_run_dub_job()` at 673 lines.
- `hot_follow_api.py` is 2,325 lines, 71 functions, 15 route handlers, and still has 18 `_policy_upsert` call sites.
- `task_view.py::build_hot_follow_workbench_hub()` is 492 lines and still performs state assembly, ready-gate projection repair, line metadata attachment, advisory attachment, and compatibility status overrides in one function.
- Hot Follow line declarations are runtime-bound for metadata/gate/skills, but worker profile, deliverable profile, asset sink profile, and confirmation policy remain mostly metadata or docs, not generic execution controls.
- The four-layer state model exists, but write/read/derive/projection are still split across routers, services, status policy, task view, and compatibility wrappers.

Hard gate: **Only after prerequisites**. Do not add a new production line until router write ownership, workbench response shape, per-line status policy/gate/skills loading, and deliverable SSOT contracts are made enforceable.

## Section 1: Current Real Architecture

### Actual Runtime Boundaries

`gateway/app/main.py` is the true FastAPI runtime entrypoint. It creates `app = FastAPI(title="ShortVideo Gateway", version="v1")`, mounts static/audio paths, runs startup DB/storage initialization, and includes these important routers:

- `tasks_router.pages_router`
- `tasks_router.api_router`
- `hot_follow_api_router`
- auth/tools/publish/admin/v17 pack routers
- `v1_actions.router` under `/v1`

The live runtime is therefore not a pure line runtime. It is a mixed FastAPI app where generic task APIs, Hot Follow APIs, legacy `/v1` routes, publish/admin routes, and static UI routes all share one process and repository shape.

The older RFC language is now split across concrete docs rather than literal RFC files in the live tree: RFC-0001 production line contract is represented by `gateway/app/lines/base.py`, `gateway/app/lines/hot_follow.py`, and `docs/contracts/hot_follow_line_contract.md`; RFC-0002 skills runtime is represented by `docs/contracts/skills_runtime_contract.md`, `gateway/app/services/skills_runtime.py`, and `skills/hot_follow`; RFC-0003/OpenClaw remains intentionally non-runtime in this repo and appears as future-facing control protocol language in earlier reviews, not as current implementation.

### Router-Level Transaction Scripts

`gateway/app/routers/tasks.py` remains a transaction-script hub:

- 3,480 lines
- 64 imports
- 87 functions
- 47 route handlers
- 37 `_policy_upsert` references
- 81 `HTTPException` references
- 10 `asyncio.run` references
- 8 `BackgroundTasks` references
- direct `subprocess.run` usage in `_ensure_mp3_audio()` and `_detect_subtitle_streams()`

Largest functions:

- `_run_dub_job()` lines 2545-3217, 673 lines
- `_run_pipeline_background()` lines 1550-1717, 168 lines
- `create_task_local_upload()` lines 1919-2028, 110 lines
- `_execute_compose_task_contract()` lines 2240-2339, 100 lines
- `build_parse()` lines 2399-2469, 71 lines
- `auto_run_pipeline()` lines 1478-1548, 71 lines

`gateway/app/routers/hot_follow_api.py` is smaller but still router-heavy:

- 2,325 lines
- 49 imports
- 71 functions
- 15 route handlers
- 18 `_policy_upsert` references
- 27 `HTTPException` references
- 6 `BackgroundTasks` references

Largest functions:

- `create_hot_follow_task_local_upload()` lines 1745-1866, 122 lines
- `_execute_hot_follow_compose_contract()` lines 241-350, 110 lines
- `_hf_deliverables()` lines 1157-1261, 105 lines
- `patch_hot_follow_audio_config()` lines 1942-2013, 72 lines
- `_hf_pipeline_state()` lines 1075-1146, 72 lines
- `_collect_hot_follow_workbench_ui()` lines 1390-1455, 66 lines

The intended architecture says routers should be transport and compatibility boundaries. The current code still has router-owned orchestration, state writes, background execution, and presentation assembly.

### Responsibilities Already Serviceized

The following are real service boundaries:

- Compose execution: `gateway/app/services/compose_service.py::CompositionService`
- Worker execution envelope: `gateway/app/services/worker_gateway.py`, `gateway/app/services/worker_gateway_registry.py`, `gateway/app/services/workers/internal_subprocess_worker.py`
- Ready gate engine: `gateway/app/services/ready_gate/engine.py::evaluate_ready_gate`
- Hot Follow gate spec loader: `gateway/app/services/ready_gate/hot_follow_rules.py::load_hot_follow_gate_spec`
- Status policy calculation: `gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state`
- Line binding: `gateway/app/services/line_binding_service.py::get_line_runtime_binding`
- Skills runtime loader: `gateway/app/services/skills_runtime.py::load_line_skills_bundle`
- Hot Follow advisory: `gateway/app/services/hot_follow_skills_advisory.py::maybe_build_hot_follow_advisory`
- Workbench/publish assembly partially moved to `gateway/app/services/task_view.py`

These are not just docs. They are runtime-called.

### Layering Violations Still Present

Major remaining violations:

- Routers still write truth directly through `_policy_upsert` wrappers.
- `task_view.py::build_hot_follow_workbench_hub()` mutates presentation fields after `compute_hot_follow_state()` and can override compose pipeline/deliverable presentation based on `compose_ready`. This is projection logic reasserting state semantics.
- `gateway/app/services/task_router_actions.py` lazily imports router functions from `gateway/app/routers/tasks.py`. It avoids direct router-to-router imports, but it is still a service wrapper around router functions, not a clean service boundary.
- `gateway/app/services/hot_follow_runtime_bridge.py` is explicitly compatibility-only, but it still exports compose/workbench/subtitle/dub compatibility surfaces that downstream callers can treat as runtime APIs.
- `status_policy/service.py::policy_upsert()` is the main write filter, but the callers still decide many truth fields and call it from many places.

## Section 2: Current Line Architecture Maturity

### Is Hot Follow Runtime-Bound As A Line?

Yes, partially.

Runtime evidence:

- `gateway/app/lines/base.py::ProductionLine` defines `line_id`, `task_kind`, contract refs, deliverable refs, SOP refs, skills refs, worker refs, ready gate refs, status policy refs, and confirmation policy.
- `gateway/app/lines/hot_follow.py::HOT_FOLLOW_LINE` registers `line_id="hot_follow_line"` and `task_kind="hot_follow"`.
- `gateway/app/main.py` imports `gateway.app.lines.hot_follow` at startup so the line registers.
- `gateway/app/services/line_binding_service.py::get_line_runtime_binding()` resolves by `task.kind`.
- `gateway/app/services/status_policy/registry.py::get_status_runtime_binding()` resolves the line and ready gate spec.
- `gateway/app/services/ready_gate/registry.py` maps `docs/contracts/hot_follow_ready_gate.yaml` to `HOT_FOLLOW_GATE_SPEC`.
- `gateway/app/services/hot_follow_skills_advisory.py` uses line binding to resolve `skills/hot_follow`.

So Hot Follow is no longer document-only.

### Where Contracts Are Declared

- Human-readable line contract: `docs/contracts/hot_follow_line_contract.md`
- YAML line contract: `docs/architecture/line_contracts/hot_follow_line.yaml`
- Runtime mirror: `gateway/app/lines/hot_follow.py`
- Ready gate contract: `docs/contracts/hot_follow_ready_gate.yaml`
- Runtime ready gate loader: `gateway/app/services/ready_gate/hot_follow_rules.py`
- Skills runtime contract: `docs/contracts/skills_runtime_contract.md`
- Worker runtime contract: `docs/contracts/worker_gateway_runtime_contract.md`
- State ownership: `docs/contracts/status_ownership_matrix.md`
- Four-layer schema: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`

### Where Contracts Are Consumed

Actually consumed:

- `ready_gate_ref` is consumed through `ready_gate/registry.py`.
- `status_policy_ref` exists in `ProductionLine.contract_metadata()` and line payload, but status policy selection is still by kind through `status_policy/registry.py`, not by dynamically importing the ref.
- `skills_bundle_ref` is consumed by `skills_runtime.py`.
- `worker_profile_ref` is passed into `WorkerRequest` in `compose_service.py::_run_ffmpeg()`.
- `line.contract_metadata()` is exposed in compose response, workbench payload, and publish/workbench service paths.

Mostly ceremonial:

- `deliverable_profile_ref` is metadata. Runtime deliverables are assembled by `task_view.py::hf_deliverables()` and router helpers, not loaded from the YAML deliverable profile.
- `asset_sink_profile_ref` points at `docs/contracts/status_ownership_matrix.md`; there is no generic asset sink runtime.
- `confirmation_policy` exists in `ProductionLine`, but publish/execute/retry confirmation is not driven by a generic line confirmation engine.
- SOP steps in `docs/architecture/line_contracts/hot_follow_line.yaml` are not the runtime step graph.
- Worker profile is a reference in `WorkerRequest`, but Worker Gateway default registration is hard-coded to `hot_follow_line/compose/ffmpeg/internal`.

## Section 3: Four-Layer State Architecture

The docs define four layers in `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`; the code implements them unevenly.

### L1 Pipeline Step Status / Attempt Status

Source of truth:

- Persisted task fields such as `status`, `last_step`, `subtitles_status`, `dub_status`, `compose_status`, `pack_status`, `publish_status`, errors, timestamps.

Write points:

- `tasks.py` has 37 `_policy_upsert` references.
- `hot_follow_api.py` has 18 `_policy_upsert` references.
- `steps_v1.py` has 18 `_update_task` references.
- `task_state_service.py::TaskStateService.update_fields()` calls `policy_upsert`.
- Compose failure/success updates are produced by `CompositionService.build_compose_failure_updates()` and `_upload_and_verify()`, then persisted by router compose contracts.

Read points:

- `task_view.py::hf_pipeline_state()`
- `hot_follow_api.py::_hf_pipeline_state()`
- `task_view.py::build_hot_follow_workbench_hub()`
- `status_policy/hot_follow_state.py` side effects
- Board/task presenters

Risks:

- Step status still competes with artifact truth. Example: `compose_status=done` does not prove final freshness, and docs explicitly say this in `status_ownership_matrix.md`.
- Many write points mean status regressions are filtered, not prevented at source.
- Router background jobs still set coarse status and last_step.

### L2 Artifact Existence

Source of truth:

- Storage keys and object existence: `raw_path`, `mute_video_key`, `origin_srt_path`, target subtitle keys, `mm_audio_key`, `final_video_key`, `pack_key`, etc.
- Artifact validation helpers in `media_validation.py`, `artifact_storage.py`, object heads/existence.

Write points:

- Upload and artifact sync in routers and services.
- `CompositionService._upload_and_verify()` writes final video keys and final source snapshots.
- Subtitle save paths include `_hf_sync_saved_target_subtitle_artifact()` in `hot_follow_api.py`.
- Pack/publish paths still write keys from router/service paths.

Read points:

- `task_view.py::hf_deliverables()`
- `task_view.py::build_hot_follow_workbench_hub()`
- `status_policy/hot_follow_state.py::_resolve_artifacts()`
- download routes in `tasks.py`

Risks:

- Artifact existence is not fully centralized in a deliverables index writer.
- `task_view.py` calls `object_exists` 22 times, making presentation layer partially responsible for checking artifact truth.
- Optional pack/scenes still appear in the same workbench payload as primary final deliverable state.

### L3 Currentness / Resolution

Source of truth:

- Derived from L1/L2 plus revision snapshots:
  - `subtitles_content_hash`
  - `subtitles_override_updated_at`
  - `dub_source_subtitles_content_hash`
  - `dub_source_subtitle_updated_at`
  - `audio_sha256`
  - final source snapshots
  - render signature

Derivation points:

- `compute_composed_state()` via `gateway/app/services/status_policy/service.py` and task view loaders
- `compose_service.py::_current_final_is_fresh()`
- `hot_follow_subtitle_currentness.py`
- `voice_state.py::collect_voice_execution_state()`
- `hot_follow_route_state.py::build_hot_follow_current_attempt_summary()`

Read points:

- `compute_hot_follow_state()`
- workbench/publish hub assembly
- skills input via `skills/hot_follow/input_skill.py`

Risks:

- Derived fields may be cached on task for compatibility.
- `task_view.py::build_hot_follow_workbench_hub()` computes, passes through, and then adjusts presentation fields after state computation.
- Hot Follow currentness is service-backed, but not yet enforced by a generic per-line state schema.

### L4 Ready Gate / Projection

Source of truth:

- `docs/contracts/hot_follow_ready_gate.yaml` runtime rules.
- `gateway/app/services/ready_gate/engine.py::evaluate_ready_gate()`.
- `gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state()`.

Write/derive points:

- Ready gate is computed, not persisted as canonical truth.
- `compute_hot_follow_state()` applies side effects into payload compatibility fields.

Read points:

- workbench hub
- publish hub
- task presenters
- skills advisory input

Risks:

- `task_view.py::build_hot_follow_workbench_hub()` still writes `compose_allowed`, `compose_allowed_reason`, and mutates `ready_gate["compose_allowed_reason"]` after state computation.
- Later in the same function, if `compose_ready` is false, it resets compose pipeline/legacy/deliverable display to `pending`. That can hide terminal failed/blocked display unless guarded by prior fixes.
- Advisory consumes a presentation payload, not a formally versioned response model.

## Section 4: `tasks.py` / `hot_follow_api.py` Risk Profile

### File Lengths And Function Concentration

High-risk files:

- `gateway/app/routers/tasks.py`: 3,480 lines
- `gateway/app/routers/hot_follow_api.py`: 2,325 lines
- `gateway/app/services/compose_service.py`: 2,137 lines
- `gateway/app/services/steps_v1.py`: 2,413 lines
- `gateway/app/services/task_view.py`: 1,123 lines

Largest functions across reviewed files:

- `tasks.py::_run_dub_job()` 673 lines
- `task_view.py::build_hot_follow_workbench_hub()` 492 lines
- `steps_v1.py::run_dub_step()` 472 lines
- `steps_v1.py::run_post_generate_pipeline()` 443 lines
- `steps_v1.py::run_subtitles_step()` 217 lines
- `compose_service.py::_prepare_workspace()` 187 lines
- `tasks.py::_run_pipeline_background()` 168 lines
- `steps_v1.py::run_pack_step()` 161 lines

### Import Graph And Cycles

Direct module parse found one import cycle among `gateway.app.adapters.repo_sql`, `gateway.app.db`, and `gateway.app.models`.

Router/service coupling risks:

- `tasks.py` imports many services and providers directly, including status policy, parse, Xiongmao provider, TTS policy, subtitle/dub helpers, scene service, publish service, task cleanup, compose helpers, runtime bridge, line binding, and compose service.
- `hot_follow_api.py` imports task view, status policy, compose service, voice service, skills advisory, subtitle helpers, and action bridges.
- `task_router_actions.py` imports `gateway.app.routers.tasks` lazily inside service functions. This is better than a direct import cycle but not a clean dependency boundary.

### Subprocess, Timeout, Temp Cleanup

Subprocess execution:

- `tasks.py` has two direct `subprocess.run` call sites.
- `steps_v1.py` has seven `subprocess.run` references.
- `compose_service.py` imports subprocess but routes compose execution through Worker Gateway in `_run_ffmpeg()`.
- `workers/internal_subprocess_worker.py` uses `subprocess.run(..., timeout=timeout)` and returns structured timeout results.

Temp cleanup:

- `tasks.py` uses `TemporaryDirectory` for publish bundle assembly.
- `compose_service.py` uses `tempfile.TemporaryDirectory()` around compose.
- `steps_v1.py` uses temporary workspaces.
- Avatar asset helpers use `NamedTemporaryFile(delete=False)` and therefore require explicit cleanup discipline.

Timeout handling:

- Compose has explicit `ComposeTimeouts` and Worker Gateway timeout handling.
- Direct router/service subprocess paths outside Worker Gateway are less standardized.

### Workbench Payload Complexity

`task_view.py::build_hot_follow_workbench_hub()` is the primary complexity hotspot:

- It accepts 23 injectable loader parameters.
- It assembles input, media, pipeline, subtitles, audio, scenes, scene_pack, deliverables, target language profile, events, compose, errors, artifact facts, current attempt, operator summary, presentation, line metadata, advisory, and UI defaults.
- It computes state through `state_computer`, then further adjusts compose/deliverable display.

This function is already a service, but it is still a God function. Adding a new line by copying this structure would duplicate collapse risk.

### State Write Points

Direct count evidence:

- `tasks.py`: 37 `_policy_upsert`, 8 `_repo_upsert`
- `hot_follow_api.py`: 18 `_policy_upsert`
- `steps_v1.py`: 18 `_update_task`
- `TaskStateService` exists but does not dominate writes.

The write path is filtered by status policy, not centralized by ownership.

### Would New Line Logic Worsen Risk?

Yes. Adding a new line now would likely copy or branch inside:

- `tasks.py` route handlers and background paths
- `task_view.py` workbench payload assembly
- status/deliverable projection fields
- skills/advisory payload assumptions
- Worker Gateway registration patterns

That would multiply already-large transaction scripts and make line-specific truth split-brain harder to detect.

## Section 5: Hot Follow Completion Level

Business completion: **High but not complete as a standard template.**

- Hot Follow can ingest, subtitle, dub/no-dub, compose, present workbench/publish surfaces, and recover from several known failure modes.
- Recent compose-input terminalization is covered by focused tests.

Operator completion: **Medium-high.**

- Workbench/publish hubs exist.
- Advisory exists.
- Presentation has many compatibility repairs, indicating the operator UX depends on a large assembled payload rather than a formal response model.

Contract completion: **Medium.**

- Line, ready gate, skills, worker, state ownership docs exist.
- Runtime consumes line/ready-gate/skills partially.
- Deliverable profile, asset sink profile, worker profile, SOP, and confirmation policy are not fully runtime-enforced.

State-model completion: **Medium.**

- Four-layer language is present and partly implemented.
- Currentness and ready gate are real.
- Split-brain risks remain in projection and multi-write status fields.

Service-boundary completion: **Medium.**

- Compose is serviceized.
- Ready gate/status are serviceized.
- Skills and Worker Gateway exist.
- Dub/subtitles/parse and workbench assembly remain too router/transaction-script shaped.

Skills extraction completion: **Early MVP.**

- `skills/hot_follow` is real and read-only.
- It is advisory-focused, not execution-routing ownership.

Safe to treat Hot Follow as first standard engineering line? **Not yet.**

It is a reference implementation for business behavior and several state repairs. It is not yet a reusable line engineering template.

## Section 6: Current Skills Reality

### Actual Skills Runtime

Implemented:

- `skills_runtime.py` loads a bundle from `line.skills_bundle_ref`.
- `skills/hot_follow/config/defaults.yaml` defines stage order and advisories.
- Stage files exist:
  - `input_skill.py`
  - `routing_skill.py`
  - `quality_skill.py`
  - `recovery_skill.py`
- `hot_follow_skills_advisory.py` builds read-only advisory input from `ready_gate`, `pipeline`, `deliverables`, `media`, `artifact_facts`, `current_attempt`, and `operator_summary`.

### Implicit Skill Logic Still In Code

Routing decisions:

- `hot_follow_route_state.py::_selected_compose_route()`
- `hot_follow_route_state.py::_route_allowance()`
- `subtitle_helpers.py` and Hot Follow subtitle/dub route helpers
- `task_view.py` no-dub decision assembly

Quality decisions:

- `dub_text_guard.py::clean_and_analyze_dub_text()`
- target language gate helpers in `hot_follow_api.py`
- subtitle currentness checks

Recovery decisions:

- `CompositionService.recover_stale_running_compose()`
- `CompositionService.build_compose_failure_updates()`
- `skills/hot_follow/routing_skill.py` and `quality_skill.py` map facts to advisory keys

Reference understanding:

- `hot_follow_subtitle_currentness.py`
- target subtitle source and content hash logic in `hot_follow_api.py`

TTS/provider decisions:

- `tts_policy.py`
- `voice_state.py`
- `voice_service.py`
- large `tasks.py::_run_dub_job()`

Content mode split:

- `subtitle_helpers.py` and `task_view.py` carry no-dub / subtitle-led / silent candidate / voice-led semantics.

### What Should Be Extracted First

First extraction candidates:

1. Content mode and compose route interpretation, but only as read-only recommendations until status truth is stable.
2. Provider/TTS selection hints, not audio deliverable writes.
3. Recovery/advisory ranking, because it already has a safe read-only path.
4. Quality warnings around subtitle/dub/compose input, not readiness truth.

Must remain outside skills:

- status truth
- deliverable truth
- asset sink truth
- ready-gate truth
- final publish truth
- repo writes

## Section 7: Contract Reality

Implemented:

- Runtime `ProductionLine` class and registry.
- Hot Follow runtime line registration.
- Ready gate YAML contract and runtime loader.
- Status policy entrypoint for Hot Follow.
- Skills bundle loader and Hot Follow read-only advisory bundle.
- Worker Gateway request/result classes and internal subprocess adapter.
- Compose service contract by code, with tests.

Partially implemented:

- Line contract: runtime-bound for metadata/gate/skills, not a full runtime backbone.
- Deliverable profile: docs exist, but runtime deliverables are hand-assembled.
- Workbench response contract: real payload exists, but no strict response model/schema.
- Manifest/schema: planning contracts exist for script/action planning; Hot Follow deliverables are not manifest-driven.
- Worker profile: passed as ref; adapter registry is hard-coded for Hot Follow compose.
- Confirmation policy: metadata only for most runtime purposes.
- Asset sink profile: documented ownership, not a runtime sink engine.

Only documented or ceremonial:

- SOP profile as executable step graph.
- Generic line onboarding manifest.
- Generic per-line workbench schema.
- Generic asset sink profile.
- Generic worker profile loader.
- Generic confirmation policy executor.

Missing:

- Single write-owner service for task truth.
- DeliverablesIndexWriter or equivalent.
- Per-line response model versioning.
- Generic line runtime loader that wires input contract, deliverable profile, SOP, skills, worker profile, asset sink, confirmation, status policy, and ready gate.

## Section 8: Can We Safely Add A New Line Now?

Hard judgment: **Only after prerequisites.**

Do not add a new production line yet.

Exact prerequisites, in order:

1. Freeze a no-new-line rule until `tasks.py`, `hot_follow_api.py`, and `task_view.py` stop being the place where new line semantics are added.
2. Create a single write boundary for task operational truth and deliverable truth. Existing `_policy_upsert` wrappers can remain temporarily, but new writes must go through a service with ownership categories.
3. Extract a versioned Hot Follow workbench response builder/model from `task_view.py::build_hot_follow_workbench_hub()` so L1/L2/L3/L4 blocks are explicit and testable.
4. Make ready-gate/status-policy selection line-driven by runtime binding, not just kind-based special cases.
5. Make deliverable profile runtime-readable and use it to assemble deliverables.
6. Make Worker Gateway registration profile-driven enough that adding a line does not require hard-coded registry edits.
7. Keep skills read-only, but define a per-line advisory input schema and stage output schema.
8. Define a new-line onboarding checklist that requires contract, deliverable profile, ready gate, state map, response model, tests, and owner boundaries before code.

## Section 9: Next-Step Engineering Rules

Enforce these immediately:

1. No new Hot Follow or new-line business logic may be added to `tasks.py`.
2. No new line-specific workbench payload assembly may be added to `task_view.py::build_hot_follow_workbench_hub()`.
3. Any new state write must declare whether it writes L1 artifact truth, L2 attempt truth, L3 derived cache, or L4 projection. L3/L4 must not be persisted as independent truth.
4. No skills stage may call `repo.upsert`, `policy_upsert`, storage upload, publish, or asset sink.
5. No worker adapter may write repo truth or accepted deliverable truth.
6. Every new route that mutates a task must call a service boundary; router code may parse HTTP and return response only.
7. Every new deliverable must be represented in a deliverable profile before implementation.
8. Every new line must provide a four-layer state map before any route is added.
9. Every new line must provide a ready-gate contract before any publish/compose-ready UI is added.
10. Every workbench/publish response must have an explicit response model or documented schema before new fields are added.
11. `compose_status`, `dub_status`, `subtitles_status`, and `pack_status` cannot be used alone to decide business readiness.
12. Optional artifacts such as pack/scenes cannot downgrade primary final deliverable readiness.
13. Compatibility bridges may be used for migration only; they may not become extension points for new lines.
14. Any new subprocess execution must go through Worker Gateway or a service with explicit timeout/error envelope.
15. Any PR that touches state derivation must update or cite the four-layer state appendix and include focused regression tests.

## No-Go Zones

No-go until prerequisites are met:

- Adding a second production line route stack.
- Copying Hot Follow workbench assembly for another line.
- Adding new route-specific status fields without ownership declaration.
- Letting skills decide final task status.
- Letting worker results write accepted deliverable keys directly.
- Adding publish readiness outside ready gate/status policy.
- Treating line docs as runtime truth without a loader/consumer.

## Strict Ordered Action List

1. Freeze new-line onboarding.
2. Inventory all task write fields by owner and convert write points to one `TaskTruthWriter`/`DeliverablesWriter` facade.
3. Split `build_hot_follow_workbench_hub()` into four blocks: object facts, attempt facts, derived state, projection.
4. Add response models for Hot Follow workbench and publish hub.
5. Make deliverable profile runtime-readable and use it in Hot Follow deliverable assembly.
6. Move remaining direct subprocess paths behind Worker Gateway or explicit service adapters.
7. Convert `task_router_actions.py` lazy router imports into service calls.
8. Convert line refs that are currently metadata-only into runtime-resolved profiles, one at a time.
9. Expand tests from Hot Follow-specific regressions to line contract conformance tests.
10. Only then begin new-line contract onboarding.
