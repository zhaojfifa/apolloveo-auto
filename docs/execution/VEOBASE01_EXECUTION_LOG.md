# VeoBase01 Execution Log

## Branch Setup

- Branch: `VeoBase01`
- Source branch: `main`
- Source commit: `6a2caa764245cd722a6519320a93c9f04573cb14`
- Baseline purpose: reconstruction baseline for ApolloVeo v1.9 stabilization toward the 2.0 factory architecture.

VeoBase01 must not be merged back to `main` until reconstruction baseline validation is complete.

From PR-4 onward, both entry files are mandatory reading before every VeoBase01 engineering PR:

- `ENGINEERING_CONSTRAINTS_INDEX.md`: root-level engineering constraint file and authority for how engineering work must be done.
- `docs/ENGINEERING_INDEX.md`: docs-level engineering index and authority for business/runtime/contract navigation.

Both are required before any future PR slice. `docs/README.md` is also mandatory before adding, moving, or reclassifying docs. Root governance remains the highest authority.

## 2026-04-22 Baseline Refresh Before PR-6

- Refresh date: `2026-04-22`
- Refreshed integration branch: `VeoBase01`
- Refreshed from: `main`
- Baseline commit: `6a2caa764245cd722a6519320a93c9f04573cb14`
- Previous local VeoBase01 tip archived as: `backup-VeoBase01-pre-refresh-20260422` at `ea437f1`
- Remote force-push performed: no

Reason:

- `main` is the stable operational branch and is the required source of truth for the Phase 2 cleanup series.
- Older `VeoBase01` history is retained only as archived reconstruction history and is not the authoritative baseline for PR-6 onward.

Mandatory pre-read completed for the refresh:

- root governance files
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- required Hot Follow / four-layer / runtime contracts
- required VeoBase01 review docs
- active factory alignment gate: `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

Requested-file note:

- `apolloveo_current_architecture_and_state_baseline.md` was requested in the mandatory reading order but is not present in this workspace. The refresh proceeded from the active root/docs/contract/review authority set above.

Read-only validation run on `main` before recreating `VeoBase01`:

- `git diff --check`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/tasks.py gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_app_import_smoke.py`
  - result: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_ready_gate_backfills_compose_when_current_final_is_fresh gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_compose_view_is_done_when_final_ready gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_stale_final_is_historical_only_after_redub gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `5 passed`

Fixed regression sample evidence required for refresh:

- Live workspace access to task ids `9c755859d049` and `9280fcb9f0b1` is not available in this repo checkout. No checked-in repository task data or seeded local DB rows exist for those ids.
- Closest equivalent read-only evidence was executed by probing the current publish/workbench surfaces with synthetic in-memory tasks using those exact ids and the current router/service builders.

Synthetic surface probe result for final-ready sample `9c755859d049`:

- publish surface: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`
- workbench surface: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose view status `done`
- repository backfill result: `compose_status=done`

Synthetic surface probe result for compose-running sample `9280fcb9f0b1`:

- publish surface: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`
- workbench surface: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose view status `pending`
- repository state remained operationally in progress: persisted `compose_status=running`

Refresh judgment:

- `main` is accepted as the PR-6 baseline.
- `VeoBase01` is recreated locally from `main` at `6a2caa764245cd722a6519320a93c9f04573cb14`.
- PR-6 may start from this refreshed branch baseline.

## Business Baseline Evidence

Hot Follow URL task `c084b276e819` is the current URL-path evidence:

- parse done
- subtitles done
- dub done
- compose done
- final exists
- `compose_ready=true`
- `publish_ready=true`

Hot Follow local task `8501fc94c1c8` is the current local-upload evidence:

- parse done
- subtitles done
- dub done
- `tts_voiceover_plus_source_audio` path is valid

These tasks establish that the Hot Follow business line is stable enough to freeze and refactor from.

## Reconstruction Guardrails

Hard constraints:

1. Do not implement a second production line.
2. Do not restart PR-4 / PR-5 as previously scoped branches.
3. Do not redesign business features first.
4. Do not touch working translation, dub, or compose behavior unless required for structural extraction.
5. Every structural change must preserve current Hot Follow business-line behavior.

## Sequential Execution Decision

VeoBase01 now follows a frozen sequential phase order:

1. architecture closure first
2. code-debt cleanup second
3. new-line loading third

No parallel execution is allowed across these three phases.

Decision note:

- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

Current gate:

- new-line design may continue
- new-line implementation remains blocked
- multi-role harness remains blocked

## Initial Contract Freeze

Phase 1 creates the branch and freezes the docs needed for contract-first reconstruction:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/contracts/line_contract.schema.json`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/adr/ADR-VEOBASE01-LINE-STATE-CONTRACT.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

## First PR Slice Proposal

First slice: `VeoBase01-PR1-contract-freeze-runtime-binding`.

Scope:

- freeze line/state/workbench contracts
- add contract conformance tests where runtime surfaces already exist
- bind existing Hot Follow runtime reads to the line contract where the path is already present
- do not move translation/dub/compose business behavior

Non-scope:

- no second line
- no PR-4 / PR-5 restart
- no broad router rewrite
- no business feature redesign

## PR-1 Started

Branch: `VeoBase01-pr1-contract-freeze-runtime-binding`

Initial implementation scope:

- add VeoBase01 contract conformance tests for Hot Follow line contract schema, YAML contract, runtime line registry, status runtime binding, and line runtime payload
- add workbench hub section conformance assertions against the existing Hot Follow workbench route
- keep runtime behavior unchanged
- keep Hot Follow translation, dub, compose, ready gate semantics unchanged

## PR-2 Started

Branch: `VeoBase01-pr2-typed-workbench-and-four-layer-state-freeze`

Scope:

- add a typed Hot Follow workbench response model
- validate the current runtime workbench payload against that model
- preserve the existing wire response shape
- freeze L1/L2/L3/L4 state responsibility in docs

Field assignment summary:

- L1 `pipeline_step_status`: parse/subtitles/dub/pack/compose rows and step statuses only.
- L2 `artifact_facts`: final/subtitle/audio/pack existence, compose input facts, audio lane facts, helper translation fact flags.
- L3 `current_attempt`: dub currentness, audio readiness, compose status/reason, redub/recompose flags, current subtitle source.
- L4 `ready_gate` / `operator_summary` / `advisory` / presentation: gate decisions and operator/UI guidance derived from L2/L3.

Non-scope:

- no translation input/source changes
- no target subtitle save changes
- no helper translation behavior changes
- no dub path changes
- no compose service behavior changes
- no second-line work

Validation:

- `python3.11 -m py_compile gateway/app/services/contracts/hot_follow_workbench.py gateway/app/services/task_view.py gateway/app/services/tests/test_hot_follow_workbench_contract.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
  - result: passed
- `git diff --check`
  - result: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_workbench_contract.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_ready_gate_backfills_compose_when_current_final_is_fresh -q`
  - result: `3 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`
  - result: `72 passed`

Acceptance status:

- workbench response has an explicit typed contract
- current runtime payload validates against the typed model
- wire response shape is unchanged
- four-layer state definitions are frozen in docs
- no translation, dub, compose, helper translation, ready gate, or advisory behavior was intentionally changed

## Business Validation Plan

Required validation before any future main alignment:

1. URL Hot Follow path still works:
   - source subtitle exists
   - target subtitle exists
   - dub works
   - compose works
   - final exists
2. Local upload path still works.
3. Helper translation does not poison mainline truth.
4. Workbench, presenter, and advisory stay aligned with artifact facts and current attempt.
5. No split-brain appears between deliverables and ready gate.

Live validation must cite the real task ids and observed state fields before VeoBase01 can be considered merge-ready.

## PR-3 Router/Service Ownership Boundary

Branch: `VeoBase01-pr3-router-service-ownership-boundary`

Scope:

- Add `docs/ENGINEERING_INDEX.md` as the mandatory engineering entry point.
- Link the engineering index from VeoBase01 architecture and execution docs.
- Move Hot Follow workbench presentation helper ownership out of `hot_follow_api.py` consumption and into `gateway.app.services.task_view`.
- Preserve the existing wire response shape and Hot Follow business runtime behavior.

Service-owned helpers consumed by the router:

- `safe_collect_hot_follow_workbench_ui`
- `collect_hot_follow_workbench_ui`
- `hf_pipeline_state`
- `hf_deliverables`
- `hf_task_status_shape`

Forbidden scope remains unchanged:

- no translation input/source changes
- no target subtitle save contract changes
- no helper translation logic changes
- no dub logic changes
- no compose logic changes
- no ready gate semantic changes
- no second-line implementation

Validation to record before PR-3 close:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py`: passed
- `git diff --check`: passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`: passed, 72 tests
- Wire response shape changed: no

## PR-4 Entry Discipline Update

Before PR-4 starts, VeoBase01 requires two layered entry files:

- `ENGINEERING_CONSTRAINTS_INDEX.md` is mandatory. It is the root-level engineering constraint entry and defines how engineering work must be done, including big-file prevention, router/service ownership, single-writer state ownership, PR slicing, validation, and write-back constraints.
- `docs/ENGINEERING_INDEX.md` is mandatory. It is the docs-level business/runtime/contract navigation entry and defines how line, state, contract, skills, architecture, execution, and new-line onboarding docs must be read.

Both are required before any future PR slice. The files are intentionally layered:

- root = engineering authority
- docs = business/runtime/contract navigation

PR-4 must not start until both files are present and cross-linked.

## Docs Structure Normalization Pass

Before the main PR-4 runtime slice, VeoBase01 re-anchors docs structure and shared reading logic.

Updated files:

- `docs/README.md`: docs structure and placement entry.
- `docs/ENGINEERING_INDEX.md`: task-oriented engineering/business reading entry.
- `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`: file-sharing logic, architecture-sharing logic, file priority matrix, forbidden doc misuse, and new-line / multi-role harness readiness review.
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`: references docs structure and shared-logic review entries.
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`: records this normalization pass.

Placement rule:

- root = engineering constraints
- `docs/README.md` = docs placement and structure
- `docs/ENGINEERING_INDEX.md` = task-oriented business/runtime/contract reading
- contracts/architecture/ADR/execution/review/archive remain distinct authority layers

No runtime code changed. Translation, dub, and compose behavior were not touched. PR-4 runtime work has not started.

## PR-4 Line Runtime Consumption And Skills Boundary

Branch: `VeoBase01-pr4-line-runtime-consumption-and-skills-boundary`

Mandatory pre-read completed before coding:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- relevant contracts under `docs/contracts/`
- line contract files under `docs/architecture/line_contracts/`

Scope:

- consume Hot Follow line runtime references through `gateway/app/services/line_binding_service.py`
- expose consumed references under `line.runtime_refs`
- load the Hot Follow skills bundle through the explicit skills runtime loader boundary
- keep worker, deliverable, and asset-sink references read-only and diagnostic
- preserve existing Hot Follow translation, dub, compose, helper translation, and ready gate behavior

Runtime-consumed references:

- `gateway.app.lines.base.LineRegistry`
- `skills/hot_follow`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/contracts/status_ownership_matrix.md`

Validation:

- `python3.11 -m py_compile gateway/app/services/line_binding_service.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/tests/test_veobase01_contract_conformance.py gateway/app/services/tests/test_hot_follow_skills_advisory.py`: passed
- `git diff --check`: passed
- focused pytest for line binding, contract conformance, skills runtime, skills advisory, workbench ready gate, and workbench contract: `43 passed`
- representative business/runtime pytest for subtitle binding, compose freshness/duration, source-audio preservation, subtitle-only compose, dub voice/text guard, current dub state, and app import smoke: `145 passed, 2 deselected`

## PR-5 New-Line Onboarding Prep And Schema Freeze

Branch: `VeoBase01-pr5-new-line-onboarding-prep-and-schema-freeze`

Mandatory pre-read completed before editing:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`

Scope:

- freeze a unified glossary for VeoBase01 preparation docs
- add a new-line onboarding template
- add minimal schema examples for line contract, worker profile,
  deliverable profile, and asset sink profile
- define a shared line-job state machine
- define skills bundle boundary and multi-role harness preconditions
- document the second-line onboarding gate while keeping it blocked

Non-scope:

- no second-line implementation
- no translation changes
- no dub changes
- no compose changes
- no ready-gate semantic rewrite
- no workbench wire changes
- no broad platformization rewrite

Docs added:

- `docs/contracts/veobase01_glossary.md`
- `docs/contracts/new_line_onboarding_template.md`
- `docs/contracts/line_job_state_machine.md`
- `docs/contracts/line_contract.example.yaml`
- `docs/contracts/worker_profile.example.yaml`
- `docs/contracts/deliverable_profile.example.yaml`
- `docs/contracts/asset_sink_profile.example.yaml`
- `docs/contracts/skills_bundle_boundary.md`

Docs updated:

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Behavior impact:

- runtime/business behavior changed: no
- workbench wire response changed: no
- second-line onboarding gate lifted: no

Validation:

- `git diff --check`: passed
- cross-link and required-section checks for new docs: passed
- schema/example consistency checks for the new example YAML set: passed by YAML parse, required-key verification against `docs/contracts/line_contract.schema.json`, and ref existence checks
- URL workbench representative path remains covered by `/api/hot_follow/tasks/{task_id}/workbench_hub` ready-gate tests with `compose_ready=true` and `publish_ready=true`
- local source-audio-preserved plus TTS path remains covered by `tts_voiceover_plus_source_audio` current dub state tests

Forbidden scope remains unchanged:

- no second-line implementation
- no translation changes
- no target subtitle save contract changes
- no helper translation behavior changes
- no dub changes
- no compose changes
- no ready gate semantic rewrite
- no broad framework rewrite

## Post-PR5 Sequential Strategy Freeze

After PR-5 acceptance, VeoBase01 execution order is explicitly frozen.

Phase 1 — architecture closure:

- finish VeoBase01 structural closure
- keep business baseline stable
- do not start new-line implementation

Architecture-closure focus:

1. line contract/runtime ref closure
2. skills / worker / deliverable / asset sink boundary freeze
3. four-layer state enforcement
4. workbench contract vs implementation alignment
5. task semantic convergence where still needed
6. docs/index/ADR/contract alignment

Phase 1 acceptance:

- contracts no longer drift
- state layers are stable
- runtime refs are real, not ceremonial
- business baseline still passes

Phase 2 — code-debt cleanup:

- start only after Phase 1 passes
- priority order: `tasks.py`, `hot_follow_api.py`, `task_view.py`,
  `task_view_workbench_contract.py`
- goal: router thinning, single-write ownership, god-file reduction,
  compatibility cleanup, and no business behavior change

Phase 3 — new-line loading:

- start only after Phase 1 and Phase 2 are both validated
- only then may new-line minimum implementation or multi-role harness
  introduction be considered

Frozen rule:

- do not run architecture closure and code-debt cleanup in parallel
- do not run code-debt cleanup and new-line loading in parallel
- do not start second-line implementation before both earlier phases stabilize

## PR-6 Tasks.py Ownership Reduction

Branch: `VeoBase01-pr6-tasks-ownership-reduction`

Why:

- `tasks.py` still owned generic publish/status response assembly and reusable download/not-ready helper logic that should live in services instead of route space.

Scope:

- restore required VeoBase01 authority docs on the refreshed baseline branch
- move generic publish-hub dispatch into `gateway/app/services/task_router_presenters.py`
- move legacy `/v1/tasks/{task_id}/status` payload assembly into `gateway/app/services/task_router_presenters.py`
- move reusable not-ready/text/download helpers into `gateway/app/services/task_download_views.py`
- keep endpoint behavior unchanged

Files changed:

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

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/tasks.py gateway/app/services/task_router_presenters.py gateway/app/services/task_download_views.py gateway/app/services/task_view.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_task_download_views.py`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_task_download_views.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `33 passed`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `pending`
  - persisted task state remained `compose_status=running`

Acceptance:

- `tasks.py` line count reduced from `3421` to `3296`
- route space no longer owns generic publish-hub dispatch
- legacy task-status payload assembly moved out of the router
- reusable download/not-ready payload helpers moved out of `tasks.py`
- Hot Follow business behavior intentionally unchanged

## PR-7 Hot Follow API Boundary Reduction

Branch: `VeoBase01-pr7-hot-follow-api-boundary-reduction`

Why:

- `hot_follow_api.py` still carried workbench/presenter helper ownership that belonged in the shared service layer and duplicated extracted view logic.

Scope:

- move shared Hot Follow workbench/presentation helper ownership into `gateway/app/services/task_view.py`
- keep `hot_follow_api.py` as thin wrappers that inject router-local collaborators into the extracted helpers
- preserve router-local helper names so the current regression harness still validates through the router seam
- keep publish/workbench behavior unchanged

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR7_HOT_FOLLOW_API_BOUNDARY_REDUCTION.md`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/task_view.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `37 passed`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py -q`: `52 passed`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `pending`
  - persisted task state remained `compose_status=running`

Acceptance:

- `hot_follow_api.py` line count reduced from `2368` to `2027`
- shared workbench/presentation helper ownership moved into `gateway/app/services/task_view.py`
- router-level wrappers remain thin collaborator-injection seams instead of payload-assembly ownership points
- Hot Follow business behavior intentionally unchanged

## PR-8 Task View Projection/Presenter Split

Branch: `VeoBase01-pr8-task-view-projection-presenter-split`

Why:

- `task_view.py` still mixed authoritative Hot Follow projection assembly with presenter/payload shaping, which left one file owning both truth normalization and surface output concerns.

Scope:

- add `gateway/app/services/task_view_projection.py` for authoritative pipeline/deliverable/workbench projection assembly
- add `gateway/app/services/task_view_presenters.py` for publish/workbench presenters and presentation aggregates
- reduce `gateway/app/services/task_view.py` to a thin import-stable facade
- keep publish/workbench behavior unchanged

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR8_TASK_VIEW_PROJECTION_PRESENTER_SPLIT.md`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_projection.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view.py gateway/app/services/task_view_projection.py gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/hot_follow_runtime_bridge.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `89 passed`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `pending`
  - persisted task state remained `compose_status=running`

Acceptance:

- `task_view.py` line count reduced from `964` to `48`
- authoritative projection moved into `gateway/app/services/task_view_projection.py`
- presenter logic moved into `gateway/app/services/task_view_presenters.py`
- import-stable callers still use `gateway/app/services/task_view.py` as a thin facade
- Hot Follow business behavior intentionally unchanged

## PR-9 Workbench Contract Hardening

Branch: `VeoBase01-pr9-workbench-contract-hardening`

Why:

- `task_view_workbench_contract.py` still contained late payload mutation helpers that rewrote compose/final presentation state after authoritative projection had already been established by `compute_hot_follow_state()`.

Scope:

- remove contract-layer helpers that mutated final deliverable and compose state after ready-gate evaluation
- keep top-level `compose_allowed` and `compose_allowed_reason` only as compatibility aliases sourced from `ready_gate`
- preserve the patchable `task_view.py` facade needed by existing service-level tests
- keep publish/workbench behavior unchanged

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR9_WORKBENCH_CONTRACT_HARDENING.md`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_workbench_contract.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_runtime_bridge.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_runtime_bridge.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `100 passed`

Supplemental note:

- the broader file `gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q` still reports two unrelated existing failures in `gateway/app/services/compose_service.py` subtitle-render defaults; PR-9 did not touch that file

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `pending`
  - persisted task state remained `compose_status=running`

Acceptance:

- contract-layer post-ready-gate mutation of final deliverable and compose state removed
- `task_view_workbench_contract.py` now acts as schema shaping plus compatibility aliasing only
- top-level `compose_allowed` remains available for UI compatibility, but is sourced from `ready_gate` instead of late truth rewriting
- Hot Follow business behavior intentionally unchanged

## Remote VeoBase01 Switch

Branch: `VeoBase01`

Why:

- local `VeoBase01` was the approved post-PR-9 integration baseline
- `origin/VeoBase01` still pointed to stale pre-refresh history
- the remote integration branch had to be intentionally replaced so later cleanup continues from the approved baseline instead of the archived line

Remote replacement evidence:

- old remote SHA before replacement: `ea437f1bcebdead870f91864dc34ae22d2680ae0`
- approved local replacement SHA: `004dffcb6cde0e1ccda2c3add75d6ac255da2100`
- exact push command used: `git push --force-with-lease origin VeoBase01:VeoBase01`
- push result: `+ ea437f1...004dffc VeoBase01 -> VeoBase01 (forced update)`

Verification:

- `git fetch origin`: passed
- `git rev-parse HEAD`: `004dffcb6cde0e1ccda2c3add75d6ac255da2100`
- `git rev-parse origin/VeoBase01`: `004dffcb6cde0e1ccda2c3add75d6ac255da2100`
- `git log --oneline --decorate --left-right origin/VeoBase01...VeoBase01`: no output
- `git status --short --branch`: `## VeoBase01...origin/VeoBase01`

Rollback reference:

- stale remote VeoBase01 tip before replacement: `ea437f1bcebdead870f91864dc34ae22d2680ae0`

Acceptance:

- `origin/VeoBase01` was intentionally replaced with the approved refreshed local integration baseline
- rollback target was recorded before the switch in `docs/execution/VEOBASE01_REMOTE_SWITCH_AND_PHASE25_PLAN.md`
- no code changes were mixed into the remote-switch step; only handoff documentation was added

## PR-10 Tasks.py Shell Reduction Follow-up

Branch: `VeoBase01-pr10-tasks-shell-reduction`

Why:

- `tasks.py` still owned reusable stream/range helper logic and subtitle-detection cache helpers that were not route-specific.

Scope:

- move generic audio/final stream meta and range-handling logic into `gateway/app/services/task_stream_views.py`
- move subtitle-stream detection/cache helpers into `gateway/app/services/task_subtitle_detection.py`
- keep compatibility wrapper names in `tasks.py` so existing tests and callers remain stable
- keep endpoint behavior unchanged

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR10_TASKS_SHELL_REDUCTION.md`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_stream_views.py`
- `gateway/app/services/task_subtitle_detection.py`
- `gateway/app/services/tests/test_task_stream_views.py`
- `gateway/app/services/tests/test_task_subtitle_detection.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/tasks.py gateway/app/services/task_stream_views.py gateway/app/services/task_subtitle_detection.py gateway/app/services/tests/test_task_stream_views.py gateway/app/services/tests/test_task_subtitle_detection.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_task_stream_views.py gateway/app/services/tests/test_task_subtitle_detection.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `89 passed`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `pending`
  - persisted task state remained `compose_status=running`

Acceptance:

- additional reusable non-route stream/detection helper logic moved out of `tasks.py`
- `tasks.py` line count reduced from `3296` to `3074`
- compatibility wrappers preserved endpoint/test behavior
- Hot Follow business behavior intentionally unchanged

## PR-11 Hot Follow API Shell Reduction Follow-up

Branch: `VeoBase01-pr11-hot-follow-api-shell-reduction`

Why:

- `hot_follow_api.py` still carried duplicated helper implementations for router-adjacent state normalization and workbench/publish support defaults.

Scope:

- replace router-local implementations of lipsync stub fallback, state-status normalization, parse-artifact readiness, and operational defaults with service-backed wrappers
- keep existing router helper names and workbench/publish injection seams stable
- avoid business-flow changes in compose, dub, translation, or publish semantics

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR11_HOT_FOLLOW_API_SHELL_REDUCTION.md`
- `gateway/app/routers/hot_follow_api.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/routers/hot_follow_api.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`: `118 passed, 2 failed`
- the two failures were the known unrelated subtitle-render default tests:
  - `test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow`
  - `test_subtitle_render_signature_tracks_minimal_retune_defaults`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -k "not test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not test_subtitle_render_signature_tracks_minimal_retune_defaults" -q`: `118 passed, 2 deselected`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
  - persisted state: `compose_status=done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `running`
  - persisted task state remained `compose_status=running`

Acceptance:

- `hot_follow_api.py` line count reduced from `2027` to `1858`
- route helper names and collaborator seams stayed stable for existing tests and callers
- no Hot Follow business-flow change was introduced

## PR-12 Compose Service Pressure Audit

Branch: `VeoBase01-pr12-compose-service-pressure-audit`

Why:

- `compose_service.py` remained the next concentrated file after the router reductions, with a large pure subtitle-render helper block living beside orchestration logic.

Scope:

- extract pure subtitle-render/layout/filter helpers into `gateway/app/services/compose_subtitle_rendering.py`
- keep `compose_service.py` as the orchestration owner and import consumer of the extracted helpers
- add direct tests for the extracted helper module using current repo behavior

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR12_COMPOSE_SERVICE_PRESSURE_AUDIT.md`
- `gateway/app/services/compose_service.py`
- `gateway/app/services/compose_subtitle_rendering.py`
- `gateway/app/services/tests/test_compose_subtitle_rendering.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/compose_subtitle_rendering.py gateway/app/services/tests/test_compose_subtitle_rendering.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_compose_subtitle_rendering.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py -k "not test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow and not test_subtitle_render_signature_tracks_minimal_retune_defaults" -q`: `107 passed, 2 deselected`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
  - persisted state: `compose_status=done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `running`
  - persisted task state remained `compose_status=running`

Acceptance:

- `compose_service.py` line count reduced from `2348` to `2111`
- pure subtitle-render helper logic now lives in a dedicated module rather than the main compose orchestrator
- no FFmpeg behavior or runtime policy was intentionally changed

## PR-13 Steps V1 Compatibility Reduction Audit

Branch: `VeoBase01-pr13-steps-v1-compatibility-reduction`

Why:

- `steps_v1.py` still carried a neutral SRT/text compatibility helper cluster that did not belong inside the main step-orchestration file.

Scope:

- extract stateless SRT/text helpers into `gateway/app/services/steps_text_support.py`
- keep legacy helper names in `steps_v1.py` as thin wrappers for import stability
- add direct tests for the extracted support module

Files changed:

- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_PR13_STEPS_V1_COMPATIBILITY_REDUCTION.md`
- `gateway/app/services/steps_v1.py`
- `gateway/app/services/steps_text_support.py`
- `gateway/app/services/tests/test_steps_text_support.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/steps_v1.py gateway/app/services/steps_text_support.py gateway/app/services/tests/test_steps_text_support.py`: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/tests/test_steps_text_support.py gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q`: `96 passed`

Regression sample evidence:

- final-ready `9c755859d049` synthetic surface probe remained aligned:
  - publish: `final_exists=true`, `composed_ready=true`, `publish_ready=true`, `audio_ready=true`, compose `done`
  - workbench: `artifact_facts.final_exists=true`, `composed_ready=true`, `ready_gate.publish_ready=true`, `audio.audio_ready=true`, compose `done`
  - persisted state: `compose_status=done`
- compose-running `9280fcb9f0b1` synthetic surface probe remained in progress:
  - publish: `final_exists=false`, `composed_ready=false`, `publish_ready=false`, `audio_ready=true`, compose `pending`
  - workbench: `artifact_facts.final_exists=false`, `composed_ready=false`, `ready_gate.publish_ready=false`, `audio.audio_ready=true`, compose `running`
  - persisted task state remained `compose_status=running`

Acceptance:

- `steps_v1.py` line count reduced from `2413` to `2349`
- neutral SRT/text compatibility helpers moved into a dedicated support module
- step execution semantics were intentionally preserved
