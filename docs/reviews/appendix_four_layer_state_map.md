# Appendix: Four-Layer State Map

Date: 2026-04-20

This appendix maps the documented four-layer state model to current runtime code.

Reference docs:

- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/status_ownership_matrix.md`

## Layer Mapping Summary

| Layer | Document language | Current code surface | Status |
| --- | --- | --- | --- |
| L1 | Object / source facts and artifact metadata | task fields, storage keys, object heads, `artifact_facts`, final/historical final | Partially centralized |
| L2 | Attempt / runtime operation state | step statuses, `compose.last`, `current_attempt`, errors/timestamps | Widely written |
| L3 | Derived / interpreted state | freshness, currentness, ready gate, composed/publish readiness | Real but mixed with compatibility fields |
| L4 | Projection / presentation state | workbench/publish payloads, deliverables block, advisory, pipeline cards | Serviceized but God-function shaped |

## L1: Object / Source Facts

### Source of truth

Persisted task fields and storage objects:

- source/raw video: `raw_path`, `raw_video_key`, `mute_video_key`, `mute_video_path`
- subtitles: `origin_srt_path`, `mm_srt_path`, language-specific subtitle keys, subtitle hashes
- audio: `mm_audio_key`, `mm_audio_path`, `audio_sha256`
- final: `final_video_key`, `final_video_path`, final metadata fields
- pack/scenes: `pack_key`, `scenes_key`
- compose input: `compose_input_policy`

### Write points

- `hot_follow_api.py::_hf_sync_saved_target_subtitle_artifact`
- `compose_service.py::_upload_and_verify`
- upload/local ingest routes in `tasks.py` and `hot_follow_api.py`
- pack/publish handlers
- `steps_v1.py` step implementations

### Read points

- `task_view.py::hf_deliverables`
- `task_view.py::build_hot_follow_workbench_hub`
- `status_policy/hot_follow_state.py::_resolve_artifacts`
- download endpoints in `tasks.py`
- `hot_follow_route_state.py::build_hot_follow_artifact_facts`

### Current violations / mismatch risks

- Presentation calls `object_exists` directly in `task_view.py`.
- Deliverable profile is not the runtime source for deliverable assembly.
- Artifact truth exists both as raw task fields and as derived `artifact_facts`.
- Optional pack/scenes fields are close to primary final state in workbench payload.

## L2: Attempt / Runtime Operation State

### Source of truth

Persisted operational fields:

- `status`
- `last_step`
- `parse_status`, `subtitles_status`, `dub_status`, `compose_status`, `pack_status`, `publish_status`
- `*_error`, `*_error_reason`
- `compose_last_status`, `compose_last_started_at`, `compose_last_finished_at`

Runtime attempt projections:

- `current_attempt`
- `compose.last`
- pipeline row states

### Write points

- `tasks.py`: 37 `_policy_upsert` references
- `hot_follow_api.py`: 18 `_policy_upsert` references
- `steps_v1.py`: 18 `_update_task` references
- `CompositionService.build_compose_running_updates`
- `CompositionService.build_compose_failure_updates`
- `CompositionService._upload_and_verify`

### Read points

- `task_view.py::hf_pipeline_state`
- `hot_follow_api.py::_hf_pipeline_state`
- `hot_follow_route_state.py::build_hot_follow_current_attempt_summary`
- `skills/hot_follow/input_skill.py`
- task list/presenter helpers

### Current violations / mismatch risks

- Step statuses can lag behind artifact truth.
- `compose_status=done` is insufficient for `final_fresh`.
- `dub_status=done` is insufficient for `audio_ready`.
- Multi-write paths mean terminal state can be overwritten or reinterpreted unless protected by policy and tests.

## L3: Derived / Interpreted State

### Source of truth

L3 is computed, not authored directly.

Primary code:

- `gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state`
- `gateway/app/services/ready_gate/engine.py::evaluate_ready_gate`
- `gateway/app/services/status_policy/service.py::compute_composed_state` via task view loaders
- `gateway/app/services/voice_state.py::collect_voice_execution_state`
- `gateway/app/services/hot_follow_subtitle_currentness.py`
- `gateway/app/services/hot_follow_route_state.py`

### Derived fields

- `target_subtitle_current`
- `target_subtitle_current_reason`
- `dub_current`
- `dub_current_reason`
- `audio_ready`
- `audio_ready_reason`
- `final_fresh`
- `final_stale_reason`
- `composed_ready`
- `ready_gate`
- `compose_route_allowed`
- `compose_input_ready`
- `compose_execute_allowed`

### Read points

- workbench and publish hubs
- task board presenters
- skills advisory input
- compose freshness decisions

### Current violations / mismatch risks

- Some derived fields are cached or mirrored into payload compatibility fields.
- `task_view.py::build_hot_follow_workbench_hub` modifies compose presentation after calling `compute_hot_follow_state`.
- Ready gate is line-bound for Hot Follow, but not yet generic across lines.
- `status_policy_ref` exists as metadata but is not dynamically imported as the policy implementation.

## L4: Projection / Presentation State

### Source of truth

Projection consumes L1-L3 and should not create truth.

Primary code:

- `task_view.py::build_hot_follow_workbench_hub`
- `task_view.py::build_hot_follow_publish_hub`
- `hot_follow_workbench_presenter.py`
- `task_router_presenters.py`
- `hot_follow_skills_advisory.py`
- frontend JS consumers under `gateway/app/static/js`

### Projection fields

- `pipeline`
- `pipeline_legacy`
- `deliverables`
- `media`
- `source_video`
- `artifact_facts`
- `current_attempt`
- `operator_summary`
- `advisory`
- button/card state fields

### Current violations / mismatch risks

- Projection sometimes patches fields that look like state truth, for example `compose_allowed`, `compose_allowed_reason`, pipeline row statuses, and final deliverable status.
- Workbench response lacks an explicit response model.
- Advisory consumes projection payloads rather than a versioned state snapshot contract.

## Split-Brain Risk Register

| Risk | Code evidence | Why it matters |
| --- | --- | --- |
| Step status vs final currentness | `compose_status` written by routers/service; `final_fresh` computed by status policy | A successful compose can become stale after subtitle/dub changes |
| Artifact exists vs readiness | `object_exists` checks in task view and routes; ready gate in status policy | Physical file presence can be mistaken for current-ready |
| Current final vs historical final | `hot_follow_state.py::_pick_current_final`, `_pick_historical_final` | Old final must not be exposed as current final |
| Route allowed vs execute allowed | `hot_follow_route_state.py`, `hot_follow_state.py` compose-input split | Legal no-TTS/BGM/preserve route does not imply encoder-safe compose input |
| Advisory vs truth | `hot_follow_skills_advisory.py` read-only inputs | Skills must not become another truth writer |
| Projection override | `task_view.py::build_hot_follow_workbench_hub` post-state mutation | UI cards can diverge from ready-gate terminal reasons |

## Required State Safety Rules

1. L1 artifact truth must be written by artifact/deliverable owners only.
2. L2 attempt truth must be written by a single controller/service boundary per step.
3. L3 must be derived from L1/L2 and must not be directly authored by skills, workers, or frontend.
4. L4 must be presentation-only and must not be fed back as task truth.
5. Any persisted compatibility field must name its owner and derivation source.
6. Ready gate must remain the authority for readiness; task status is not enough.
7. Deliverables must remain the authority for physical artifact exposure; pipeline status is not enough.
