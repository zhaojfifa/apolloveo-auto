# VeoBase01 Execution Log

## Branch Setup

- Branch: `VeoBase01`
- Source branch: `main`
- Source commit: `6a2caa764245cd722a6519320a93c9f04573cb14`
- Baseline purpose: reconstruction baseline for ApolloVeo v1.9 stabilization toward the 2.0 factory architecture.

VeoBase01 must not be merged back to `main` until reconstruction baseline validation is complete.

## 2026-04-22 Reading Contract Freeze And Publish Hotfix Start

- Branch: `VeoBase01-reading-contract-publish-hotfix`
- Base branch: `VeoBase01`
- Base SHA: `6931530953933cd4720cae804e48f91c9f628449`
- Execution note: `docs/execution/VEOBASE01_READING_CONTRACT_AND_HOTFIX_PLAN.md`

Purpose:

- freeze authority-file reading as a mandatory engineering precondition
- repair the Hot Follow publish final-ready regression through the authoritative
  projection path
- document flow/state/projection contract drafts after the regression fix is
  clear

Stage 0 acceptance:

- `docs/contracts/engineering_reading_contract_v1.md` added
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`,
  `docs/ENGINEERING_INDEX.md`, and
  `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md` wired to it
- execution note includes a Reading Declaration and authority conflict record

Authority-path mismatch frozen for this slice:

- requested but missing: `docs/contracts/four_layer_state_contract.md`
- requested but missing: `docs/contracts/workbench_hub_response.contract.md`
- requested but missing: `apolloveo_current_architecture_and_state_baseline.md`

Active fallback references actually read:

- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

## 2026-04-22 Publish Final-Ready Regression Hotfix

- Branch: `VeoBase01-reading-contract-publish-hotfix`
- Base SHA: `7485464`
- Execution note: `docs/execution/VEOBASE01_HOTFIX_PUBLISH_FINAL_READY_REGRESSION_V2.md`

Root cause:

- publish still evaluated final/audio/compose readiness from the old
  `publish_hub_payload(task)` compatibility path instead of starting from the
  authoritative workbench projection path

Stale source path identified:

- `gateway/app/routers/hot_follow_api.py:1467`
- `gateway/app/services/task_view_presenters.py` previous
  `build_hot_follow_publish_hub(...)`
- `gateway/app/services/task_view_helpers.py:834`
  `publish_hub_payload(task)`
- `gateway/app/services/task_view_helpers.py:487`
  `compute_composed_state(task, task_id)`

Authoritative source path used after fix:

- `gateway/app/services/task_view_projection.py:351`
  `build_hot_follow_workbench_projection(...)`
- `gateway/app/services/task_view_presenters.py:407`
  `_build_hot_follow_authoritative_state(...)`
- `gateway/app/services/status_policy/hot_follow_state.py`
  `compute_hot_follow_state(...)`

Files changed:

- `gateway/app/services/task_view_presenters.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`

Validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
  - result: passed
- `git diff --check`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q`
  - result: `24 passed`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `1 passed`

Regression evidence note:

- live replay for task ids `7852ffeefdf9` and `01f530caabf5` was not available
  in this workspace
- local in-process regression coverage now explicitly covers:
  - local upload + preserved source audio + final done
  - URL/reference + TTS-only + final done
  - scene-pack pending but final publishable
  - final absent / compose in progress

Acceptance:

- publish now consumes the shared authoritative projection path before
  ready-gate evaluation
- false publish blockers from the stale compatibility path are removed for this
  contradiction class

## 2026-04-22 Hot Follow Flow / State / Projection Design Packet

- Branch: `VeoBase01-reading-contract-publish-hotfix`
- Follows hotfix note: `docs/execution/VEOBASE01_HOTFIX_PUBLISH_FINAL_READY_REGRESSION_V2.md`

Created documents:

- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/architecture/contract_editor_preparation_notes_v1.md`

Purpose:

- make Hot Follow business flow explicit
- freeze the first state-machine and projection-rule drafts
- define the future contract-editor object model without starting UI or runtime
  replacement work

Non-scope preserved:

- no new-line implementation
- no multi-role harness
- no Hot Follow business-flow change
- no compose / dub / translation runtime rewrite

Design acceptance:

- business flow now explicitly covers local upload, URL/reference,
  source-audio-preserved lanes, TTS-only lanes, authoritative subtitle truth,
  helper-translation support, compose success, publish-ready, scene-pack
  pending non-blocking, and current-attempt vs historical-final separation
- state-machine draft now freezes blocking vs non-blocking distinctions and the
  dominance rule for current fresh final truth
- projection-rules draft now defines publish/workbench projection objects as
  contract surfaces instead of router-local logic

## 2026-04-22 Merge Into VeoBase01

- Merge branch: `VeoBase01-reading-contract-publish-hotfix`
- Source base SHA: `6931530953933cd4720cae804e48f91c9f628449`
- Source final SHA: `f0a0deb0b138e6785e35372d068bed7ab4c076d6`
- Merge commit SHA: `8908df79aa5ea8013e2ae92b9575b7469ebe8341`
- Merge style: regular merge commit

Why:

- preserve the reading-contract, hotfix, and Stage 2 design lineage explicitly
  in VeoBase01 history

Post-merge validation:

- merged-file presence check: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
  - result: passed
- `git diff --check`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `25 passed`

Acceptance:

- VeoBase01 contains the publish regression fix and Stage 0/Stage 2 documents
- publish/workbench authoritative alignment remains intact after merge
- no unrelated code changes were introduced in the merge step

## 2026-04-22 Authority Refresh And Documentation Supplement

- Execution note: `docs/execution/VEOBASE01_AUTHORITY_REFRESH_AND_DOC_SUPPLEMENT.md`

Missing before refresh:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

Decision:

- reconstructed as canonical authority docs

Reconstructed files:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `apolloveo_current_architecture_and_state_baseline.md`

Index / reading-contract files updated:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

Authority refresh acceptance:

- the active reading contract now names canonical files that exist in the repo
- `STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md` remains an explicit drafting/fallback
  template, not the primary state authority
- `status_ownership_matrix.md` remains the ownership/write-path companion
  authority

## 2026-04-23 Authority Baseline Tag And Rule-Freeze Start

- Tag name: `VeoBase01-AuthorityBaseline-PreRuleFreeze`
- Tag target SHA: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`
- Tag type: annotated

Reason:

- mark the authority-aligned, publish-regression-fixed VeoBase01 baseline as a
  rollback-safe point before the rules-first foundation pass

Tag push:

- pushed to `origin`

## 2026-04-23 Main / VeoBase01 Alignment

- Pre-alignment main SHA: `6a2caa764245cd722a6519320a93c9f04573cb14`
- Pre-alignment VeoBase01 SHA: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`
- Alignment method: fast-forward `main` to `VeoBase01`

Why:

- `main` was an ancestor of `VeoBase01`
- the accepted VeoBase01 lineage already contained the stable authority/hotfix
  baseline
- fast-forward preserved lineage without rewriting or weakening the accepted
  branch history

Post-alignment SHAs:

- `main`: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`
- `VeoBase01`: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`

Remote update:

- `origin/main` fast-forwarded to `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`

## 2026-04-23 Rules-First Foundation Pass

Created baseline documents:

- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`

Purpose:

- freeze factory architecture layers
- freeze contract-driven four-layer state precedence
- freeze runtime assembly rules for production lines
- define how oversized files lose rule power without starting the refactor here

Scope preserved:

- no new scenario runtime work
- no new line implementation
- no multi-role harness
- no UI/editor implementation

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

## Minimal Contract Runtime Skeleton

Branch: `VeoBase01-minimal-contract-runtime`
Base SHA: `11ec2c192ef74e89cdc0e98f39e8ad8a3208e003`

Why:

- the rules-first baseline had been frozen in docs, but the selected
  ready-gate / projection / blocking subset still lived in Python helper and
  presenter branches instead of a dedicated runtime bridge.

Scope:

- add the minimal `gateway/app/services/contract_runtime/` package
- route Hot Follow ready-gate evaluation through the contract runtime bridge
- route publish/workbench selected projection dominance through the projection
  runtime
- load selected blocking-reason mapping from contract data
- remove only the matching rule ownership replaced by the new runtime subset

Reading Declaration:

- current phase: `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`,
  `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- state truth: `docs/contracts/four_layer_state_contract.md`,
  `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`,
  `docs/contracts/status_ownership_matrix.md`
- ready-gate semantics: `docs/contracts/hot_follow_ready_gate.yaml`
- projection semantics: `docs/contracts/hot_follow_projection_rules_v1.md`,
  `docs/contracts/hot_follow_state_machine_contract_v1.md`
- ownership semantics: `docs/contracts/production_line_runtime_assembly_rules_v1.md`,
  `docs/architecture/factory_four_layer_architecture_baseline_v1.md`,
  `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`

Files changed:

- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_MINIMAL_CONTRACT_RUNTIME_SKELETON.md`
- `gateway/app/lines/base.py`
- `gateway/app/lines/hot_follow.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/contract_runtime/__init__.py`
- `gateway/app/services/contract_runtime/blocking_reason_runtime.py`
- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/contract_runtime/runtime_loader.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py`
- `gateway/app/services/status_policy/tests/test_line_runtime_binding.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/tests/test_contract_runtime_projection_rules.py`
- `gateway/app/services/tests/test_line_binding_service.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/task_view_presenters.py gateway/app/services/task_view_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/runtime_loader.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/blocking_reason_runtime.py gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py`: passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`: `31 passed`

Regression evidence:

- exact live task replay was not run in this workspace
- in-process contradiction-class coverage passed for:
  - local upload + preserved source audio + final done
  - URL/reference + TTS-only + final done
  - scene-pack pending but final publishable
  - final absent / compose genuinely in progress

Acceptance:

- selected ready-gate evaluation now flows through
  `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- publish/workbench selected projection dominance now flows through
  `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- blocking-reason mapping is centralized in
  `gateway/app/services/contract_runtime/blocking_reason_runtime.py`
- `task_view_presenters.py`, `task_view_helpers.py`, `tasks.py`, and
  `hot_follow_api.py` each lost a narrow piece of selected rule ownership
- Hot Follow business behavior was intentionally preserved

## Index-First Reading Discipline Correction

Branch: `VeoBase01-index-first-reading-discipline`
Base SHA: `2a825cdfd260850ef75700ea84f6315e878bf1a2`

Why:

- the prior reading contract still encouraged broad raw authority lists for
  every engineering task
- future contract-runtime work needs a repeatable index-first pattern:
  root indexes, docs indexes, task classification, then minimum authority files

Reading Declaration:

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from the indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/execution/VEOBASE01_EXECUTION_LOG.md`
4. Sufficiency note:
   - This was documentation-governance work only. It did not touch runtime,
     state, projection, ready-gate, line contract, or business behavior.
5. Missing-authority handling:
   - none

Files changed:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_INDEX_FIRST_READING_DISCIPLINE.md`

Validation:

- `git diff --check`: passed
- `ls README.md ENGINEERING_CONSTRAINTS_INDEX.md docs/README.md docs/ENGINEERING_INDEX.md docs/contracts/engineering_reading_contract_v1.md docs/execution/VEOBASE01_EXECUTION_LOG.md docs/execution/VEOBASE01_INDEX_FIRST_READING_DISCIPLINE.md docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md docs/contracts/four_layer_state_contract.md docs/contracts/status_ownership_matrix.md docs/contracts/workbench_hub_response.contract.md docs/contracts/hot_follow_ready_gate.yaml docs/contracts/hot_follow_projection_rules_v1.md docs/contracts/production_line_runtime_assembly_rules_v1.md docs/architecture/line_contracts/hot_follow_line.yaml docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md docs/architecture/factory_four_layer_architecture_baseline_v1.md docs/contracts/contract_driven_four_layer_state_baseline_v1.md`: passed

Acceptance:

- active reading rules now require index-first routing
- Reading Declaration shape now records root indexes, docs indexes, minimum
  task-specific authorities, sufficiency, and missing-authority handling
- no runtime behavior was intentionally changed

## Contract Runtime Expansion Pass 2

Branch: `VeoBase01-contract-runtime-expansion-pass2`
Base SHA: `e8ef8cb2f562dbc6b39c3ecb99b272f84be4042f`

Why:

- operator validation confirmed the first runtime slice preserved publish-center
  final-ready behavior, so the next safe step was to expand contract-loaded
  rule ownership for a still-narrow Hot Follow subset.

Reading Declaration:

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from indexes:
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/production_line_runtime_assembly_rules_v1.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
   - `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`
4. Sufficiency note:
   - This pass only expanded Hot Follow contract-runtime coverage and ownership
     reduction for the selected rule subset. Broader scenario/product docs were
     not required.
5. Missing-authority handling:
   - none

Runtime subset expanded:

- compose-input terminal mode handling
- no-dub / no-tts route reason derivation
- compose-allowed reason derivation
- final-vs-historical surface precedence
- scene-pack pending non-blocking reason resolution
- blocking reason canonicalization plus priority ordering

Files changed:

- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/execution/VEOBASE01_CONTRACT_RUNTIME_EXPANSION_PASS2.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `gateway/app/services/contract_runtime/__init__.py`
- `gateway/app/services/contract_runtime/blocking_reason_runtime.py`
- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/tests/test_contract_runtime_projection_rules.py`

Validation:

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/runtime_loader.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/blocking_reason_runtime.py gateway/app/services/task_view_helpers.py gateway/app/services/task_view_presenters.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py`: passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py`: `47 passed`

Acceptance:

- expanded subset is contract-loaded at runtime
- helper/presenter/contract-adapter paths lost rule ownership for the selected
  subset
- publish/workbench alignment coverage remained green
- no scenario onboarding, new-line runtime, or multi-role harness work was
  started

## Contract Runtime Expansion Pass 3

Branch: `VeoBase01`
Base SHA: `3e6dc57a7c780886359035a90e99c0cc9130fc81`

Why:

- a real Hot Follow task exposed that a first TTS/dub failure with a ready
  target subtitle could be misclassified as terminal no-TTS/no-dub route truth
- pass 3 narrows the fix to current-attempt route-summary, advisory selection,
  and retriable-vs-terminal route classification

Reading Declaration:

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Reading contract read:
   - `docs/contracts/engineering_reading_contract_v1.md`
4. Minimum task-specific authority files selected from indexes:
   - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
   - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
   - `docs/contracts/four_layer_state_contract.md`
   - `docs/contracts/status_ownership_matrix.md`
   - `docs/contracts/production_line_runtime_assembly_rules_v1.md`
   - `docs/contracts/hot_follow_ready_gate.yaml`
   - `docs/contracts/hot_follow_projection_rules_v1.md`
   - `docs/contracts/hot_follow_state_machine_contract_v1.md`
   - `docs/architecture/line_contracts/hot_follow_line.yaml`
   - `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`
5. Sufficiency note:
   - This pass targets current-attempt/advisory/route-summary
     contractization for Hot Follow and does not require broader scenario docs.
6. Missing-authority handling:
   - none

Runtime subset expanded:

- intended route vs fallback route precedence
- subtitle-ready/TTS-expected current-attempt route summary
- retriable TTS/provider/audio generation failure classification
- terminal no-dub/no-TTS route classification
- selected-subset `compose_allowed_reason` and `subtitle_terminal_state`
- advisory selection for final-ready, retriable dub failure, and true no-TTS
  terminal paths

Files changed:

- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/execution/VEOBASE01_CONTRACT_RUNTIME_EXPANSION_PASS3.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `gateway/app/services/contract_runtime/__init__.py`
- `gateway/app/services/contract_runtime/advisory_runtime.py`
- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/hot_follow_route_state.py`
- `gateway/app/services/hot_follow_skills_advisory.py`
- `gateway/app/services/ready_gate/hot_follow_rules.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/tests/test_hot_follow_artifact_facts.py`
- `gateway/app/services/tests/test_hot_follow_skills_advisory.py`

Ownership removed:

- `hot_follow_route_state.py` lost selected current-attempt route-summary rule
  ownership for the selected subset; it now delegates to
  `contract_runtime/current_attempt_runtime.py`
- `hot_follow_skills_advisory.py` lost advisory selection ownership for the
  selected final-ready / retriable-dub-failure / terminal-no-TTS subset
- ready-gate code now imports selected-route runtime from
  `contract_runtime/current_attempt_runtime.py`
- presenters/helpers remained output shapers and did not receive new rule power

Validation:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/contract_runtime/advisory_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/hot_follow_route_state.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/services/ready_gate/hot_follow_rules.py gateway/app/services/status_policy/hot_follow_state.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_contract_runtime_projection_rules.py -q`: `37 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py -q`: `77 passed`
- `git diff --check`: passed

Regression evidence:

- voice-led / subtitle-ready / first TTS failure stays `tts_replace_route`,
  classifies as `retriable_dub_failure`, and does not recommend
  `compose_no_tts`
- voice-led retry success resolves to `tts_replace_route`, `audio_ready=true`,
  `compose_status=done`, and final-ready advisory
- true no-dub/no-TTS terminal path remains legal when explicit route facts and
  no-dub/no-TTS allowance apply
- final-ready / scene-pack pending remains non-blocking through existing
  publish/workbench ready-gate coverage

Live replay:

- exact live task replay for `a71bb3fd679e` was not run
- evidence is fixture/in-process coverage only

Acceptance:

- first-dub-failure misclassification fixed for the selected contract-runtime
  subset
- current-attempt/advisory logic for the selected subset is now genuinely
  contract-runtime loaded
- no scenario onboarding, new-line implementation, UI/editor work, or
  multi-role harness work was introduced

## 2026-04-23 - VeoBase01 Subtitle Authority Repair

Branch:

- `VeoBase01-subtitle-authority-repair`

Base:

- `7e2e56b873f59537bf6d33a51b854343631bca63`

Reading declaration:

- root indexes: `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes: `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- authority files:
  - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
  - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/architecture/line_contracts/hot_follow_line.yaml`
- missing authority: none

Exact bug class addressed:

- subtitle-authority chain failure on source-subtitle translation/provider
  failure
- helper/provider failure not entering authoritative subtitle state
- downstream projection falling back to `subtitle_missing` and `no_dub`/`no_tts`
  symptoms instead of exposing the upstream failure truth

Exact root cause:

- source-subtitle translation raised sanitized helper/provider errors without
  persisting authoritative subtitle failure state when no current target
  subtitle existed
- duplicated subtitle-lane projection in `hot_follow_api.py` did not surface
  helper failure metadata/reasons for the same shape

Modules changed:

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_REPAIR.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Exact ownership changed:

- `hot_follow_api.py`: source-subtitle lane now owns authoritative persistence
  of helper/provider failure for missing-target-subtitle cases; duplicate lane
  projection now reflects helper failure truth
- `subtitle_helpers.py`: subtitle readiness/currentness projection now owns
  helper-failure-first reason mapping for missing-target-subtitle cases
- `task_view_presenters.py`: no longer allows helper-failure-with-missing-target
  shapes to collapse into no-dub UI state

Validation:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_presenters.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `git diff --check`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_persists_subtitle_authority_failure gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_preserves_current_target_subtitle gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_persists_full_target_srt gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs -q`: `4 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py::test_publish_hub_keeps_scene_pack_pending_non_blocking_when_final_ready -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_skills_advisory.py::test_voice_led_retry_success_resolves_tts_replace_and_final_ready -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_contract_runtime_projection_rules.py::test_projection_runtime_final_ready_dominates_publish_truth -q`: `1 passed`

Representative task verification:

- live replay not available in this workspace
- searched repo/workspace and local `shortvideo.db` for `6b40d86589da`,
  `944e2e8e6f0d`, `91990da2b72f`; no local artifacts/rows found
- evidence is in-process/runtime coverage only

Acceptance:

- Gate 1 target subtitle authority: repaired for the selected source-subtitle
  helper/provider failure subset
- Gate 2 helper failure propagation: repaired for the selected subset
- Gate 3 downstream classification honesty: repaired for the selected subset
- `VeoBase01` is usable as the repair base for the next subtitle-authority
  tightening round

## 2026-04-23 - VEOBASE01 Subtitle Authority Review

Branch:

- `VeoBase01-subtitle-authority-repair`

Head reviewed:

- `bc75f8ae8b74146bef113f16b8593d75eb7d7f59`

Pass type:

- review-only

Authority set checked:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/contracts/engineering_reading_contract_v1.md`

Evidence availability:

- requested real-task ids `6b40d86589da`, `944e2e8e6f0d`, `91990da2b72f`,
  `796bf811a43b` were not present in the local repo/workspace or local
  `shortvideo.db`
- review therefore used authority docs, implementation trace, the existing
  repair note, and the user-provided bad-shape/repair-lessons summary

Review judgment:

- the repeated subtitle-authority collapse is primarily a contract problem
- the root failure class is a combination of:
  - split authoritative target-subtitle write ownership
  - helper side-channel leakage into subtitle-step success truth
  - semantic-empty subtitle acceptance on the subtitles-step path
  - downstream L4 masking after upstream truth is already inconsistent

Primary ownership leak found:

- `run_subtitles_step()` can persist `subtitles_status=\"ready\"` even when the
  target subtitle is non-authoritative or absent from the canonical target
  subtitle artifact path

Required next pass:

- `VeoBase01-subtitle-authority-contract-correction`

Validation:

- authority path existence check: passed
- `git diff --check`: passed
- runtime/code changes: none in this review pass

## 2026-04-24 - VEOBASE01 Subtitle Authority Contract Correction

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `a1a6837eaf11e55a806db487ca7120a32ba3fd4e`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/engineering_reading_contract_v1.md`
  - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
  - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/architecture/line_contracts/hot_follow_line.yaml`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
- missing authority: none

Execution scope:

- single-owner authoritative target subtitle write
- subtitle-step success gate bound to authoritative truth
- helper side-channel isolation from subtitle-step success
- empty-body subtitle rejection before authoritative success

Exact single owner chosen:

- `gateway/app/services/hot_follow_subtitle_authority.py`

Exact ownership correction:

- `steps_v1.py` no longer writes authoritative subtitle success truth directly
- `hot_follow_api.py` no longer writes authoritative subtitle success truth
  directly
- both delegate to the subtitle-authority service

Exact success gate introduced:

- `subtitles_status=\"ready\"` now requires:
  - authoritative target subtitle
  - semantic target subtitle body
  - canonical target subtitle artifact
  - `target_subtitle_current=true`

Exact helper boundary correction:

- helper/non-authoritative subtitle outcomes can no longer persist subtitle-step
  success truth
- helper remains side-channel only for the corrected boundary

Exact empty-body rejection rule:

- timing-only or semantic-empty subtitle content cannot become authoritative
  subtitle success
- physical file existence alone is insufficient

Files changed:

- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/services/steps_v1.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/tests/test_steps_v1_subtitles_step.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Validation:

- `python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_authority.py gateway/app/services/steps_v1.py gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_consumes_result_contract_for_myanmar gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_marks_vi_translation_incomplete_without_step_error gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_marks_myanmar_translation_incomplete_without_step_error gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_treats_preserved_source_audio_as_helper_only gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_delegates_authoritative_truth_to_service gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_rejects_timing_only_target_subtitle_before_success gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_save_authoritative_target_subtitle_delegates_to_single_owner gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_save_authoritative_target_subtitle_rejects_source_copy_before_success gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_persists_subtitle_authority_failure gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_source_lane_failure_preserves_current_target_subtitle gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs -q`: `11 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_helper_translate_429_persists_sanitized_helper_failure -q`: `1 passed`
- `git diff --check`: passed

Limitations:

- live representative task replay was unavailable in this workspace
- broader `test_hot_follow_subtitle_binding.py` still has two unrelated
  subtitle-render expectation failures already present on this branch

Acceptance:

- subtitle authority has a single owner
- subtitle-step success is bound to authoritative truth
- helper is restored to side-channel status for the corrected boundary
- empty-body subtitle success is impossible on the corrected paths
- `VeoBase01` is safe for later resumed contract tightening on this boundary

## 2026-04-24 - VEOBASE01 Subtitle Authority Closure Continuation

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `c8389b29b605cd36e37e853fb216486315bd0006`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/engineering_reading_contract_v1.md`
  - `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
  - `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
  - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- missing authority: none

Exact remaining gap repaired:

- projection still depended too heavily on storage-backed subtitle artifacts
- authoritative local target subtitle text could exist while
  `edited_text` / `srt_text` / `primary_editable_text` / `dub_input_text`
  stayed empty
- persisted upstream formation failure reasons such as
  `target_subtitle_translation_incomplete` could still collapse to generic
  `subtitle_missing`

Exact modules changed:

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Exact formation path repaired:

- subtitle text load path now falls back from override -> storage artifact ->
  local workspace authoritative subtitle artifact
- subtitle artifact physical existence now accepts the local workspace target
  subtitle file as evidence for currentness/binding projection

Helper/provider failure propagation before / after:

- before: explicit helper/provider or translation-incomplete failure truth could
  still be downgraded to `subtitle_missing` when no target text loaded
- after: explicit persisted failure reasons survive subtitle-lane projection and
  remain visible as the primary target-formation failure class

Dub-input binding before / after:

- before: `dub_input_text` could remain empty when the authoritative subtitle
  existed only in the local/current artifact path
- after: `dub_input_text` is restored from authoritative/current target
  subtitle truth when that truth exists in override, storage, or local
  workspace artifact form

Validation:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -k "local_authoritative_target or translation_incomplete_reason or source_lane_failure_persists_subtitle_authority_failure or source_lane_persists_full_target_srt or helper_failure_preserves_authoritative_outputs or does_not_treat_timing_only_target_artifact_as_existing_truth"`: `6 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -k "vi_currentness_blocks_false_done_states or myanmar_currentness_blocks_false_done_states or helper_translate_429_persists_sanitized_helper_failure"`: `3 passed`
- `git diff --check`: passed

Validation note:

- `test_manual_subtitle_save_clears_helper_translate_failure` currently returns
  `422` in this workspace; that endpoint issue was not introduced by this pass
  and was left out of scope

Real representative task verification:

- not available locally
- `2825a683c861`, `6b40d86589da`, `944e2e8e6f0d`, `91990da2b72f`, and
  `796bf811a43b` were not available in local repo artifacts or local
  `shortvideo.db`
- acceptance is therefore based on focused in-process/runtime coverage only

Acceptance:

- target subtitle formation closure is repaired for the storage-missing /
  local-authoritative-artifact shape
- helper/provider and translation-incomplete failure truth no longer disappears
  into generic `subtitle_missing`
- authoritative target subtitle to dub-input binding is restored
- `VeoBase01-subtitle-authority-contract-correction` is now a safer merge
  candidate for subtitle-authority completion

## 2026-04-24 - VEOBASE01 Subtitle-Step Terminal Resolution

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `d328c6f39134b308bcdb7555cfd667b44251ed8e`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
  - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- missing authority: none

Exact issue addressed:

- subtitles step could remain `failed` or `running` even after authoritative
  target subtitle truth was fully current
- helper 429 remained visible correctly, but still polluted subtitle-step
  terminal resolution
- stale `target_subtitle_empty` / no-dub skip-state could linger after current
  subtitle/audio truth already existed

Exact modules changed:

- `gateway/app/services/subtitle_helpers.py`
- `gateway/app/services/task_view_projection.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Exact correction:

- added a narrow subtitle terminal-success predicate based on authoritative
  current subtitle truth
- workbench/projection now resolves subtitle-step state to terminal success
  when authoritative/current subtitle truth is already established
- source-subtitle-lane helper failure updates now keep helper failure visible
  while restoring `subtitles_status=ready` and clearing stale subtitle-step
  errors when current authoritative subtitle already exists
- stale no-dub skip-state is cleared through the existing empty-dub recovery
  path when current subtitle truth is present

Validation:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_projection.py gateway/app/services/task_view_presenters.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -k "source_lane_failure_preserves_current_target_subtitle"`: `1 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -k "subtitles_terminal_success or helper_translate_429_persists_sanitized_helper_failure or does_not_hydrate_timing_only_target_artifact"`: `3 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -k "does_not_keep_no_dub_when_audio_is_current or successful_redub_persists_current_subtitle_snapshot"`: `2 passed`
- `git diff --check`: passed

Real representative task verification:

- direct local replay of `42c51c62581b` was not available
- repo/workspace search returned no local artifact for that id
- local `shortvideo.db` schema does not expose the newer subtitle-currentness
  columns needed for direct comparison
- acceptance is therefore based on focused in-process/runtime coverage only

Acceptance:

- subtitle-authority formation remains intact
- subtitle-step terminal success now resolves correctly from current
  authoritative subtitle truth
- helper 429 remains visible but side-channel only
- stale skip-state no longer outranks current subtitle/audio truth
- branch is safer for later compose/final acceptance work

## 2026-04-24 - VEOBASE01 subtitle-authority continuation: URL recovery surface + preserve-source route

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `d8dd55673c5034ac01d644110afe3539c054d947`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
  - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- missing authority: none

Pass A - exact correction:

- recovered current-audio truth now overrides stale raw `dub_status=failed` in
  pipeline projection
- stale dub error display is suppressed once `audio_ready=true`
- audio preview URL now falls back to `/v1/tasks/{task_id}/audio_mm` when
  current audio is ready/deliverable even if the raw `voiceover_url` field is
  missing

Pass B - exact correction:

- preserve-source helper-only subtitle extraction is no longer treated as
  `target_subtitle_not_authoritative` mainline failure
- subtitles step now resolves to accepted completion for that route with:
  - `subtitles_status=ready`
  - `subtitles_error=None`
  - `target_subtitle_current=false`
  - `target_subtitle_current_reason=preserve_source_route_no_target_subtitle_required`
- helper-only preserve-source output no longer sets mainline
  `translation_incomplete=true`

Exact modules changed:

- `gateway/app/services/voice_service.py`
- `gateway/app/services/task_view_projection.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/services/steps_v1.py`
- `gateway/app/services/tests/test_steps_v1_subtitles_step.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Validation:

- `python3.11 -m py_compile gateway/app/services/voice_service.py gateway/app/services/task_view_projection.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_subtitle_authority.py gateway/app/services/steps_v1.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py::test_run_subtitles_step_treats_preserved_source_audio_as_helper_only -q`: `1 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -k "recovers_current_audio_preview_and_clears_stale_failed_residue or preserve_source_route_does_not_project_target_subtitle_authority_failure or resolves_subtitles_terminal_success_when_authoritative_truth_is_current" -q`: `3 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/tests/test_hot_follow_artifact_facts.py -q`: `20 passed`
- `git diff --check`: passed

Real representative task verification:

- direct local replay of `42c51c62581b` and `7fe6dc8b4e95` was not available
- repo/workspace search returned no local artifacts for those ids
- local `shortvideo.db` did not contain those rows
- acceptance is therefore based on focused in-process/runtime coverage only

Acceptance:

- Pass A URL helper-recovery / preview issue: corrected for the tested current
  truth shape
- Pass B local preserve-source contract: corrected for the tested helper-only
  preserve-source shape
- URL mainline remains healthy
- preserve-source route no longer inherits a misleading target-subtitle
  authority failure at the subtitles-step boundary

## 2026-04-24 - VEOBASE01 runtime rule-freeze for business-boundary stabilization

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `e42fbb7f0776886e619130e521a1c82352187e23`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
  - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- missing authority: none

Exact top-level rules frozen:

- URL voice-led standard dubbing:
  - authoritative/current target subtitle truth keeps the task on
    `tts_replace_route`
  - helper failure history and translation-incomplete history are diagnostic
    only after current authoritative subtitle truth exists
- local preserve-source route separation:
  - preserve-policy tasks now distinguish explicit
    `preserve_source_route_no_target_subtitle_required` exceptions from
    preserve-policy tasks that still require the normal TTS route
- helper side-channel coexistence:
  - helper/provider failure is side-channel only once current subtitle/audio/
    final truth exists, unless an explicit rule says it blocks mainline
- historical event isolation:
  - stale `target_subtitle_empty` / `dub_input_empty` skip history does not
    override current authoritative truth for the frozen rule subset

Exact runtime modules changed:

- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/tests/test_contract_runtime_projection_rules.py`
- `gateway/app/services/tests/test_hot_follow_artifact_facts.py`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Validation:

- `python3.11 -m py_compile gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py`: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_contract_runtime_projection_rules.py -q`: `42 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -k "preserve_source_route_does_not_project_target_subtitle_authority_failure or resolves_subtitles_terminal_success_when_authoritative_truth_is_current or recovers_current_audio_preview_and_clears_stale_failed_residue" -q`: `3 passed`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q`: `7 passed`
- `git diff --check`: passed

Representative task verification:

- direct replay of the successful URL closure case, failed URL
  translation-incomplete case, and local preserve-source first/recovered cases
  was not available locally
- acceptance is therefore based on focused in-process/runtime coverage only

Acceptance:

- URL same-class route resolution is now constrained by explicit top-level
  rules instead of drifting through scattered current-attempt branching
- local preserve-source route handling is now rule-separated from the normal
  voice-led TTS route
- helper failure no longer pollutes recovered current truth once authoritative
  subtitle/audio/final truth exists
- historical skip/failure events no longer override current truth for the
  frozen boundary subset
- this line is in a better state for final acceptance and merge consideration

## 2026-04-24 - Hot Follow current-branch final acceptance freeze

Branch:

- `VeoBase01-subtitle-authority-contract-correction`

Base:

- `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`

Starting SHA:

- `0d804fd149a5dc4aec1143ea684e1b12d940a1f8`

Reading declaration:

- root indexes:
  - `README.md`
  - `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes:
  - `docs/README.md`
  - `docs/ENGINEERING_INDEX.md`
- task-specific authority:
  - `docs/contracts/engineering_reading_contract_v1.md`
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/hot_follow_projection_rules_v1.md`
  - `docs/contracts/hot_follow_state_machine_contract_v1.md`
  - `docs/reviews/VEOBASE01_SUBTITLE_AUTHORITY_REVIEW.md`
  - `docs/execution/VEOBASE01_SUBTITLE_AUTHORITY_CONTRACT_CORRECTION.md`
  - `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- missing authority:
  - none

Scope:

- acceptance verification only
- baseline-freeze judgment only
- one minimal same-branch correction only because acceptance evidence forced it

Acceptance-evidence correction forced by this pass:

- manual subtitle save after helper failure still returned `422`
- root cause was strict currentness matching between canonical Myanmar
  `mm.srt` and legacy Myanmar `my.srt`
- narrow correction accepted `my.srt` as a Myanmar-only authoritative alias for
  currentness/source matching

Exact modules changed:

- `gateway/app/services/hot_follow_subtitle_currentness.py`
- `gateway/app/services/tests/test_hot_follow_subtitle_currentness.py`
- `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Validation:

- `python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_currentness.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py`
  - result: passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
  - result: `7 passed`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q`
  - result: `61 passed`
- `git diff --check`
  - result: passed

Representative task verification:

- direct live replay of `791a826f4e11`, `c0dac743a540`, and `e7c248b90ef4`
  was not available in this workspace
- repo/workspace search and local `shortvideo.db` lookup did not find those
  rows
- acceptance therefore relies on contract/runtime inspection plus focused
  in-process validation

Freeze judgment:

- four-layer architecture acceptance: accepted
- contract-driven status acceptance: accepted
- business-flow acceptance: accepted
- boundary stability acceptance: accepted
- final freeze judgment: `A. Freeze accepted`

Next action:

- move upward into factory-level contract objects and line-template design
- do not reopen Hot Follow internals unless a new acceptance regression is
  found against this frozen baseline

## 2026-04-24 - Hot Follow baseline freeze tag, VeoBase01 alignment, and factory-layer lift

Source-of-truth docs used:

- `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

Part 1 - frozen baseline tag:

- source branch: `VeoBase01-subtitle-authority-contract-correction`
- frozen baseline commit SHA: `2bfef16053c5f97b85b044de3a28a367eca26fbc`
- tag name: `HotFollow-ContractDriven-Baseline-Freeze01`
- tag SHA: `4d271022cef1bfe94b3e0a33cb4a429a6ab25d36`
- tag target commit SHA: `2bfef16053c5f97b85b044de3a28a367eca26fbc`
- tag type: annotated
- remote push:
  - `origin` updated with the new tag

Part 2 - VeoBase01 alignment:

- local `VeoBase01` SHA before alignment: `7e2e56b873f59537bf6d33a51b854343631bca63`
- remote `origin/VeoBase01` SHA before alignment: `7e2e56b873f59537bf6d33a51b854343631bca63`
- alignment method used: `git checkout VeoBase01` + `git merge --ff-only VeoBase01-subtitle-authority-contract-correction`
- accepted lineage preserved: yes
- history rewrite used: no
- local `VeoBase01` SHA after alignment: `2bfef16053c5f97b85b044de3a28a367eca26fbc`
- remote `origin/VeoBase01` updated: yes
- remote `origin/VeoBase01` SHA after alignment: `2bfef16053c5f97b85b044de3a28a367eca26fbc`
- `main` touched in this pass: no

Part 3 - Hot Follow freeze write-back:

- Hot Follow is now recorded as the first frozen contract-driven
  production-line baseline
- further Hot Follow internal work is paused unless a new acceptance regression
  appears
- next work is explicitly routed upward into factory-level contract objects and
  line-template design

Part 4 - factory-layer docs created on `VeoBase01`:

- `docs/execution/HOT_FOLLOW_BASELINE_FREEZE_AND_VEOBASE01_ALIGNMENT.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/architecture/factory_line_template_design_v1.md`

Index update:

- `docs/ENGINEERING_INDEX.md`
  - added factory contract-object baseline authority entries
  - added a task-oriented reading path for factory-level contract object design
  - updated the new-line gate to keep work at the factory-contract/template
    layer while Hot Follow stays frozen

Validation:

- `git diff --check`
  - result: passed
- authority path existence checks:
  - `test -f docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
  - `test -f docs/execution/HOT_FOLLOW_BASELINE_FREEZE_AND_VEOBASE01_ALIGNMENT.md`
  - `test -f docs/contracts/factory_input_contract_v1.md`
  - `test -f docs/contracts/factory_content_structure_contract_v1.md`
  - `test -f docs/contracts/factory_scene_plan_contract_v1.md`
  - `test -f docs/contracts/factory_audio_plan_contract_v1.md`
  - `test -f docs/contracts/factory_language_plan_contract_v1.md`
  - `test -f docs/contracts/factory_delivery_contract_v1.md`
  - `test -f docs/architecture/factory_line_template_design_v1.md`
  - result: passed

Conflict-resolution note:

- no code/doc conflict resolution was required during VeoBase01 alignment
- alignment was a pure fast-forward to the accepted frozen baseline

Acceptance:

- annotated freeze tag created and pushed
- `VeoBase01` now contains the accepted frozen Hot Follow baseline
- accepted lineage was preserved by fast-forward only
- Hot Follow is now frozen as the first production-line sample
- next work has moved upward one layer into factory-level contract objects and
  line-template design only

## 2026-04-24 - main alignment to accepted VeoBase01 baseline and factory discussion branch start

Source-of-truth docs used:

- `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
- this execution log

Before-state:

- current branch before alignment: `VeoBase01`
- local `main` SHA before alignment: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`
- remote `origin/main` SHA before alignment: `7687ba9aaeaae3ac5f55d37c3d511aff37cabc9f`
- local `VeoBase01` SHA before alignment: `093a6e2dfb5abeb1bfd1600eebfd75a00359873d`
- remote `origin/VeoBase01` SHA before alignment: `093a6e2dfb5abeb1bfd1600eebfd75a00359873d`
- accepted tag name: `HotFollow-ContractDriven-Baseline-Freeze01`
- accepted tag SHA: `4d271022cef1bfe94b3e0a33cb4a429a6ab25d36`
- accepted tag target SHA: `2bfef16053c5f97b85b044de3a28a367eca26fbc`

Part 2 - main alignment:

- alignment source: `VeoBase01`
- alignment method used: `git checkout main` + `git merge --ff-only VeoBase01`
- history rewrite used: no
- `main` SHA after alignment: `093a6e2dfb5abeb1bfd1600eebfd75a00359873d`
- remote `origin/main` updated: yes
- remote `origin/main` SHA after alignment: `093a6e2dfb5abeb1bfd1600eebfd75a00359873d`
- freeze tag changed: no
- `VeoBase01` contents changed for alignment: no

Part 3 - fresh discussion branch:

- branch name: `factory-contract-objects-discussion-v1`
- branch base: updated `main`
- branch created from SHA: `093a6e2dfb5abeb1bfd1600eebfd75a00359873d`
- remote branch pushed: yes

Part 4 - write-back:

- execution note created:
  - `docs/execution/MAIN_ALIGNMENT_AND_FACTORY_DISCUSSION_BRANCH_START.md`
- execution log updated
- `docs/ENGINEERING_INDEX.md` did not require a further discoverability update
  because the factory-level contract-object design path was already added in
  the prior baseline pass

Current active scope:

- accepted Hot Follow freeze tag remains unchanged
- `main` is aligned to the accepted `VeoBase01` baseline
- next active branch is `factory-contract-objects-discussion-v1`
- next work is factory-level contract discussion only
- runtime onboarding for the next line remains blocked

Validation:

- `git diff --check`
  - result: passed
- branch/commit/tag verification:
  - `git rev-parse main`
  - `git rev-parse origin/main`
  - `git rev-parse VeoBase01`
  - `git rev-parse origin/VeoBase01`
  - `git rev-parse HotFollow-ContractDriven-Baseline-Freeze01`
  - `git rev-parse HotFollow-ContractDriven-Baseline-Freeze01^{}`
  - result: verified
- authority path existence checks:
  - `test -f docs/execution/MAIN_ALIGNMENT_AND_FACTORY_DISCUSSION_BRANCH_START.md`
  - `test -f docs/execution/VEOBASE01_EXECUTION_LOG.md`
  - result: passed

Acceptance:

- lineage preserved
- branch drift reduced by aligning `main` to accepted `VeoBase01`
- discussion moved upward into factory-level contract scope
- frozen Hot Follow internals remain closed in this pass

## 2026-04-24 - product-driven factory alignment pass for Matrix Script, Digital Anchor, and frozen Hot Follow

Branch:

- `factory-contract-objects-discussion-v1`

Reading Declaration:

1. Root indexes read first:
   - `README.md`
   - `ENGINEERING_CONSTRAINTS_INDEX.md`
2. Docs indexes read second:
   - `docs/README.md`
   - `docs/ENGINEERING_INDEX.md`
3. Minimum task-specific authority files selected from indexes:
   - `docs/contracts/engineering_reading_contract_v1.md`
   - `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
   - `docs/contracts/production_line_runtime_assembly_rules_v1.md`
   - `docs/contracts/factory_input_contract_v1.md`
   - `docs/contracts/factory_content_structure_contract_v1.md`
   - `docs/contracts/factory_scene_plan_contract_v1.md`
   - `docs/contracts/factory_audio_plan_contract_v1.md`
   - `docs/contracts/factory_language_plan_contract_v1.md`
   - `docs/contracts/factory_delivery_contract_v1.md`
   - `docs/architecture/factory_line_template_design_v1.md`
   - `docs/contracts/script_video_planning_contract.md`
   - `docs/contracts/action_replica_planning_assets_contract.md`
   - `docs/reviews/review_jellyfish_importability_for_factory.md`
   - `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
   - `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
4. Why these files were sufficient:
   - this pass is a product-driven factory alignment pass above the frozen Hot
     Follow sample
   - Matrix Script line truth is represented by the script-video planning
     contract and the script-driven planning review path
   - Digital Anchor line truth is represented by the action-replica planning
     asset contract and the digital-human planning review path
   - Hot Follow is used only as the frozen production-line reference sample
5. Missing-authority handling:
   - no indexed authority file was missing
   - no new product doc was created in this pass; write-back stays in the
     execution log only

Execution scope:

- raise contract architecture one level higher without starting runtime
  onboarding
- map product flow to architecture layers, UI surfaces, and backend domains
- define tool integration as backend capability supply rather than front-end
  model selection
- define the Broll asset-library vs tool-backend boundary
- produce one implementation backlog split by:
  - factory-generic
  - line-specific
  - runtime-policy
  - tool-supply
  - asset-supply
  - platform capabilities

Scenario alignment baseline:

- Matrix Script Line:
  - treated as a script-driven, result-oriented matrix production line
  - authoritative upstream truth is the script planning chain:
    script -> segment -> shot -> candidate asset -> linked asset -> delivery
  - `docs/contracts/script_video_planning_contract.md` is the current product
    truth proxy
- Digital Anchor Line:
  - treated as a script-driven personal-anchor production line
  - authoritative upstream truth is the role/scene binding chain:
    script/plan -> identity -> role binding -> shot binding -> language/audio
    plan -> delivery
  - `docs/contracts/action_replica_planning_assets_contract.md` is the current
    product truth proxy
- Hot Follow:
  - remains the frozen reference line
  - contributes the accepted four-layer runtime sample, delivery precedence,
    and workbench/publish truth-path discipline
  - no Hot Follow internal reopening is allowed in this pass

### Execution Alignment Summary

Contract architecture must now be raised one level above the current
factory-object set.

The next abstraction layer is not “another line contract” and not “runtime
onboarding”. It is the factory product packet that binds:

- input contract
- content structure contract
- scene plan contract
- audio plan contract
- language plan contract
- delivery contract
- line template bindings

into one product-facing packet that a line must provide before runtime work is
allowed.

Debt-reduction path:

1. keep Hot Follow frozen as the runtime reference line
2. stop treating front-end workbench payloads as the place where line product
   concepts are discovered
3. lift Matrix Script and Digital Anchor product logic into contract-object
   packets first
4. define backend domains that can consume those packets without putting tool
   choice, asset browsing, or route policy into routers/UI
5. only after those packet and domain boundaries are explicit, allow line
   runtime onboarding discussion

Product flow to architecture-layer mapping:

- Layer 1 production-line contract:
  - declares which line is active and which packet bindings it requires
- Layer 2 state/projection:
  - interprets artifact truth, route truth, language/audio currentness, and
    delivery readiness from packet-driven rules
- Layer 3 surface/execution:
  - exposes workbench and delivery center surfaces and dispatches services that
    consume packet-driven rules

Product flow to UI-surface mapping:

- intake/create surface:
  - factory input contract
- planning/workbench surface:
  - content structure, scene plan, language plan, audio plan
- candidate confirmation/editor surface:
  - Matrix Script candidate/link flow
  - Digital Anchor identity/role/shot binding flow
- delivery center:
  - factory delivery contract
- operator-facing publish/final review:
  - ready-gate and delivery outputs derived from authoritative state, not
    planning drafts

Backend integration rule:

- tool registry -> capability adapters -> routing policy -> worker execution
- front end must not select raw model/provider as product runtime logic
- front end may select product intent, quality tier, or line options
- backend resolves that into tools/capabilities and execution routing

Broll and tool boundary:

- Broll asset library is asset supply:
  - reusable references, candidate assets, linked assets, file-usage indexes,
    asset availability, licensing/usage metadata
- tool backend is capability supply:
  - text analysis, script planning, image generation, speech, dubbing, motion,
    composition, retrieval, ranking
- neither Broll nor tool backend should own task/workbench business truth
- line runtime consumes both through contracts and supply adapters

Additional platform capabilities required for a true video factory:

- factory packet validator before runtime onboarding
- capability registry and adapter governance
- asset-supply index and usage tracing
- product-intent to capability-routing policy layer
- versioned workbench/delivery response models
- line conformance and packet completeness checks
- execution/provenance tracing across planning, asset linking, and delivery

### Implementation Backlog

A. factory-generic

- define one factory packet envelope that groups the six contract objects as
  one pre-runtime onboarding requirement
- add packet completeness and contract cross-reference validation
- define factory-level product flow vocabulary shared by Matrix Script and
  Digital Anchor without copying Hot Follow runtime residue
- define versioned surface response contracts for intake, planning, and
  delivery center

B. line-specific

- Matrix Script line:
  - bind script planning draft, shot candidate flow, and result-oriented
    delivery profile into one line packet
- Digital Anchor line:
  - bind identity/role/shot planning, speaker/language/audio expectations, and
    personal-anchor delivery profile into one line packet
- Hot Follow:
  - no new internal work; retain only as frozen reference sample

C. runtime-policy

- formalize packet-to-line-template binding rules
- formalize which packet fields become L2 facts, which become L3 route
  decisions, and which remain L4-only planning/presentation inputs
- define runtime onboarding gate checks that prove a new line is packet-complete
  before any router/service runtime work starts
- define ready-gate selection and delivery precedence rules as line policy, not
  UI or router heuristics

D. tool-supply

- create/strengthen backend domains for:
  - capability registry
  - capability adapters
  - routing policy
  - worker execution envelope
  - provider/model/settings governance
- remove product dependence on front-end model selection
- expose product-level intent knobs only, with backend resolution to tools

E. asset-supply

- create/strengthen backend domains for:
  - Broll/reference asset library
  - candidate vs linked asset confirmation
  - file-usage / scope indexing
  - asset availability / provenance / usage metadata
- keep asset supply distinct from task/workbench truth and from tool capability
  supply

F. platform capabilities

- packet validation service
- line conformance tests
- versioned response schemas for workbench and delivery center
- provenance tracing from planning draft to linked assets to accepted delivery
- operator confirmation hooks that remain contract-driven
- cross-line policy observability and execution audit views

Validation:

- `git diff --check`
  - result: passed

Acceptance:

- contract architecture is now aligned one layer higher than the current
  factory object set
- Matrix Script and Digital Anchor are both mapped as script-driven planning
  lines without starting runtime onboarding
- tool integration is aligned to backend capability supply
- Broll is aligned to asset supply
- Hot Follow remains frozen and unopened in this pass

## 2026-04-24 Hot Follow First-Attempt Subtitle-Authority Stabilization

Context:

- Current branch only narrow stabilization pass for representative failure class
  `0b4ad74b6244`
- Scope held to first-attempt subtitle-authority stabilization only

Fix:

- separated unresolved translation from terminal empty-target handling for
  first-attempt voice-led tasks by blocking dub-step empty-target skip when
  `target_subtitle_translation_incomplete` still has parse-source evidence
- stopped premature `no_dub=true` and `post.dub.skip(target_subtitle_empty)`
  projection for voice-led unresolved translation lanes
- moved `artifact_facts.selected_compose_route` onto the same runtime-policy
  route derivation used by current-attempt and ready-gate
- kept stale `target_subtitle_empty` / `no_dub` residue out of current truth
  surfaces once current subtitle/audio truth recovers

Validation:

- `python3.11 -m py_compile gateway/app/services/task_view_helpers.py gateway/app/services/task_view_presenters.py gateway/app/services/task_view_projection.py gateway/app/services/hot_follow_route_state.py gateway/app/services/steps_v1.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q`
- `git diff --check`

Acceptance result:

- unresolved translation first-attempt no longer collapses into
  `target_subtitle_empty`
- selected compose route is consistent across artifact facts, current attempt,
  and ready gate
- `no_dub` emission is now terminal-only for this boundary
- retry/current-truth recovery keeps stale empty-target residue out of current
  surfaces

## 2026-04-24 Hot Follow Translation-Lane State-Machine Stabilization

Context:

- Current branch only narrow follow-up pass for representative failure class
  `d215fbcb5d5e`
- Scope held to translation-lane non-terminal state modeling only

Fix:

- converted first unresolved target-subtitle translation from terminal
  `subtitles_status=failed` into non-terminal pending/waiting state when
  voice-led parse-source evidence exists and no terminal contract evidence is
  present
- converted dub first unresolved translation from hard failure into blocked
  pending state with `waiting_for_target_subtitle_translation`
- preserved contract-precise authority reason
  `target_subtitle_translation_incomplete` while projecting retryable waiting
  wording through `subtitle_ready_reason`, `audio_ready_reason`, current
  attempt, ready gate, advisory, and operator summary
- added helper-lane visibility classification so unresolved translation now
  exposes one of:
  - pending provider work
  - temporary provider issue
  - terminal provider failure
  - no helper used
- kept prior no-dub suppression, single-source route selection, and stale
  residue cleanup behavior intact

Validation:

- `python3.11 -m py_compile gateway/app/services/hot_follow_helper_translation.py gateway/app/services/subtitle_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_subtitle_authority.py gateway/app/services/voice_state.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/hot_follow_workbench_presenter.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/steps_v1.py gateway/app/services/contract_runtime/advisory_runtime.py gateway/app/services/tests/test_hot_follow_helper_translation.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_helper_translation.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_artifact_facts.py -q`
- `git diff --check`

Acceptance result:

- subtitles first unresolved translation is now non-terminal
- dub is blocked/pending instead of hard-failed when subtitle translation is
  the only blocker
- helper/provider visibility is explicit on the subtitle lane
- ready gate, advisory, and operator summary now use waiting/retryable wording
  for unresolved translation lanes

## 2026-04-24 Hot Follow Four-Layer Projection Drift Repair

Context:

- Current branch only narrow projection repair for representative waiting-state
  class `d215fbcb5d5e`
- Scope held to L4 projection derivation only

Fix:

- froze `translation_waiting_retryable` as a strict non-terminal contract state
  spanning L2 truth and L3 gate/current-attempt derivation
- patched L4 deliverable projection so subtitle/audio rows derive from current
  waiting truth instead of stale failed residue
- isolated historical `post.dub.fail(target_subtitle_translation_incomplete)`
  to events only; it no longer drives deliverables when the current contract
  state is waiting/retryable
- updated state-machine and projection-rule docs so L4 surfaces must derive
  strictly from L2 facts plus L3 gate state for this boundary

Validation:

- `python3.11 -m py_compile gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/tests/test_hot_follow_skills_advisory.py gateway/app/services/tests/test_hot_follow_helper_translation.py -q`
- `git diff --check`

Acceptance result:

- translation waiting now projects consistently across pipeline, deliverables,
  current attempt, ready gate, advisory, and operator summary
- deliverable failed residue is removed for subtitle/audio while helper
  translation remains pending/retryable
- historical dub-fail events remain diagnostic-only and do not override current
  truth

## 2026-04-24 Hot Follow Helper-Translation Side-Channel Repair

Context:

- Current branch only narrow helper-translation repair pass for representative
  mainline-success class `fad8c8c4d050`
- Scope held to helper classification, projection, and messaging only
- No subtitle-authority, no-dub, route-selection, compose, or publish policy
  changes

Fix:

- froze helper lane public state to one explicit contract state set:
  `helper_unavailable`, `helper_pending`, `helper_resolved`,
  `helper_retryable_failure`, `helper_terminal_failure`
- kept helper input/output helper-scoped and left authoritative target subtitle
  ownership unchanged
- carried explicit helper status/retryable/terminal facts through subtitle
  lane, artifact facts, and current attempt so the helper side-channel is no
  longer half-represented across layers
- preserved existing current-truth dominance: when authoritative target
  subtitle, dub, and final are already current, helper retryable failure stays
  helper warning/history only and does not become the current mainline failure
  surface
- kept the resolved helper path valid for helper-only input samples and manual
  authoritative subtitle save flow

Validation:

- `python3.11 -m py_compile gateway/app/services/hot_follow_helper_translation.py gateway/app/services/hot_follow_route_state.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/tests/test_hot_follow_helper_translation.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_helper_translation.py::test_helper_translate_lane_state_distinguishes_pending_temporary_terminal_and_not_involved gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only gateway/app/services/tests/test_hot_follow_artifact_facts.py::test_helper_failure_does_not_override_mainline_success -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_subtitle_lane_preserves_translation_incomplete_reason_over_generic_missing gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_translation_incomplete_does_not_project_stale_empty_no_dub gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_recovers_current_audio_preview_and_clears_stale_failed_residue gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
- `git diff --check`

Acceptance result:

- helper retryable failure is non-blocking once mainline authoritative truth is
  ready
- helper retryable failure no longer overrides current mainline success
  surfaces
- helper resolved path remains valid
- Hot Follow contract freeze remains stable after this narrow helper-only fix

## 2026-04-24 Hot Follow Helper Dual-State Warning Repair

Context:

- Current branch only ultra-narrow helper-lane repair pass for representative
  success class `fad8c8c4d050`
- Scope held to helper-side classification, projection, and messaging only
- No subtitle authority, route, no-dub, dub, compose, or publish policy
  changes

Fix:

- split helper state into two contract dimensions:
  - output state:
    `helper_output_unavailable`, `helper_output_pending`,
    `helper_output_resolved`
  - provider health:
    `provider_ok`, `provider_retryable_failure`,
    `provider_terminal_failure`
- added explicit composite contract state
  `helper_resolved_with_retryable_provider_warning` for the shape where helper
  output already exists and is already consumed, but the provider currently
  reports a retryable warning such as quota/429 exhaustion
- helper output consumed into authoritative/current target subtitle truth no
  longer projects as helper failure
- provider retryable warning remains preserved in helper facts/history, but
  current-attempt and presentation surfaces stay clean and success-led
- helper manual input/resolved path remains valid

Validation:

- `python3.11 -m py_compile gateway/app/services/hot_follow_helper_translation.py gateway/app/services/subtitle_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_route_state.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/tests/test_hot_follow_helper_translation.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hot_follow_artifact_facts.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_helper_translation.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_helper_translation_projection_stays_helper_layer_only gateway/app/services/tests/test_hot_follow_artifact_facts.py::test_helper_failure_does_not_override_mainline_success gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_resolves_subtitles_terminal_success_when_authoritative_truth_is_current gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_translation_incomplete_does_not_project_stale_empty_no_dub gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_manual_subtitle_save_clears_helper_translate_failure -q`
- `git diff --check`

Acceptance result:

- helper output resolved plus provider retryable warning is now representable as
  a dual-state contract shape
- `helper_resolved_with_retryable_provider_warning` is projected explicitly
- provider retryable issues remain warning/history only once mainline truth is
  already successful
- mainline success surfaces remain clean

## 2026-04-24 Hot Follow Helper Translate Idempotency And Single-Flight Repair

Context:

- Current branch only final ultra-narrow helper interaction repair pass
- Scope held to helper translate API idempotency, same-request single-flight,
  and resolved-with-warning success-led projection only
- No subtitle authority, route, no-dub, dub, compose, or publish policy
  changes

Fix:

- added stable helper request fingerprinting from `task_id`, helper input text,
  target language, and input source
- added same-fingerprint single-flight guard at the helper translate endpoint
- repeated helper-only translate requests on an already-current authoritative
  task now return idempotent success/no-op responses instead of conflict-style
  provider failure
- when helper output is already resolved/consumed and provider health remains
  retryable-warning only, API/result projection stays success-led as
  `resolved_with_warning`
- repeated helper calls no longer mutate current mainline status/error truth
  for already-current tasks

Validation:

- `python3.11 -m py_compile gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/hot_follow_helper_translation.py gateway/app/services/contract_runtime/current_attempt_runtime.py gateway/app/services/hot_follow_route_state.py gateway/app/services/subtitle_helpers.py gateway/app/services/task_view_workbench_contract.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_repeat_on_already_current_task_is_idempotent_success gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_repeat_dedupes_same_in_flight_request gateway/app/services/tests/test_hot_follow_subtitle_binding.py::test_translate_subtitles_helper_failure_preserves_authoritative_outputs gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py::test_hot_follow_workbench_resolves_subtitles_terminal_success_when_authoritative_truth_is_current gateway/app/services/tests/test_hot_follow_artifact_facts.py::test_helper_failure_does_not_override_mainline_success -q`
- `git diff --check`

Acceptance result:

- repeated helper translate on already-current authoritative tasks is now
  idempotent and non-destructive
- same-request helper calls are single-flight
- resolved-with-warning remains success-led and warning-only
- current mainline truth stays clean for the `33c0b9a82024`-class success shape
