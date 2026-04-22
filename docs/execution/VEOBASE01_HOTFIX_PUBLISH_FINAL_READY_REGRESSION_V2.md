# VeoBase01 Hotfix Publish Final-Ready Regression v2

Date: 2026-04-22
Branch: `VeoBase01-reading-contract-publish-hotfix`
Base branch: `VeoBase01`
Base SHA: `7485464`

## Purpose

Repair the Hot Follow publish final-ready regression by removing publish-side
re-derivation from the stale compatibility path and making publish consume the
same authoritative projection path already used by workbench.

## Reading Declaration

Authority files read before this code change:

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `PROJECT_RULES.md`
- `ENGINEERING_RULES.md`
- `ENGINEERING_STATUS.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- requested path missing: `docs/contracts/four_layer_state_contract.md`
- requested path missing: `docs/contracts/workbench_hub_response.contract.md`
- active fallback used: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- requested path missing: `apolloveo_current_architecture_and_state_baseline.md`
- `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`
- `docs/reviews/VEOBASE01_POST_PR5_GATE_REVIEW.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

Current phase defined by:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

State truth defined by:

- active fallback: `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/status_ownership_matrix.md`

Line / runtime / ready-gate ownership defined by:

- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_runtime_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Root Cause

Publish and workbench were not consuming the same state path.

Stale publish-side source path before the fix:

- `gateway/app/routers/hot_follow_api.py:1467`
  - `_service_build_hot_follow_publish_hub(...)`
- `gateway/app/services/task_view_presenters.py`
  - previous `build_hot_follow_publish_hub(...)`
  - called `compute_hot_follow_state(task, publish_hub_payload(task))`
- `gateway/app/services/task_view_helpers.py:834`
  - `publish_hub_payload(task)`
- `gateway/app/services/task_view_helpers.py:487`
  - `compute_composed_state(task, task_id)`

Why that path drifted:

- publish assembled its own base payload from compatibility-heavy helper logic
- that helper recomputed final/audio/compose readiness from older publish-side
  facts instead of starting from the shared projection used by workbench
- `compute_hot_follow_state(...)` then evaluated ready-gate truth against that
  stale publish payload, which allowed false blockers such as
  `missing_voiceover`, `audio_not_ready`, and `compose_not_done` even when the
  workbench projection already showed a valid fresh final and ready current
  attempt

Authoritative path already used by workbench:

- `gateway/app/services/task_view_projection.py:351`
  - `build_hot_follow_workbench_projection(...)`
- `gateway/app/services/task_view_presenters.py:407`
  - `_build_hot_follow_authoritative_state(...)`
- `gateway/app/services/task_view_workbench_contract.py`
  - workbench payload shaping only after authoritative inputs are assembled
- `gateway/app/services/status_policy/hot_follow_state.py`
  - `compute_hot_follow_state(...)` applied to the projection-derived payload

## Fix Implemented

Implemented change:

- extracted a shared `_build_hot_follow_authoritative_state(...)` helper in
  `gateway/app/services/task_view_presenters.py`
- that helper starts from `build_hot_follow_workbench_projection(...)`, builds
  the authoritative pre-surface payload, attaches L2/L3 presentation inputs, and
  only then runs `compute_hot_follow_state(...)`
- `build_hot_follow_publish_hub(...)` now adapts the publish surface from that
  authoritative state instead of calling `publish_hub_payload(task)`
- `hot_follow_api.py` no longer passes the old `publish_payload_builder` seam
  into the publish service

What was intentionally not changed:

- no Hot Follow business-flow change
- no translation or helper-translation change
- no subtitle-save semantic change
- no dub / compose / ffmpeg / worker runtime change
- no line-contract semantic change
- no new publish one-off such as `if final exists then publish_ready=true`

## Scope

- publish final-ready regression repair
- publish/workbench path convergence at the presenter/service layer
- focused regression coverage for the contradiction classes called out in the
  task

## Non-Goals

- no new-line implementation
- no multi-role harness
- no redesign of external publish/workbench contracts
- no broad router or compose refactor in this slice

## Files Changed

- `gateway/app/services/task_view_presenters.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`

## Exact Validations Run

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m py_compile gateway/app/services/task_view_presenters.py gateway/app/routers/hot_follow_api.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py`
  - result: passed
- `git diff --check`
  - result: passed
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q`
  - result: `24 passed`
- `WORKSPACE_ROOT=/tmp/apolloveo-workspace PYTHONPYCACHEPREFIX=/tmp/apolloveo_pycache python3.11 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`
  - result: `1 passed`

## Regression Evidence

Live replay against repository task ids was not possible in this workspace.
No live task-row replay is claimed here.

Strongest local evidence used:

1. Local upload + preserved source audio + final done:
   - regression id mirrored: `7852ffeefdf9`
   - publish resolves `final.exists=true`, `composed_ready=true`,
     `compose_status=done`, `ready_gate.audio_ready=true`,
     `ready_gate.publish_ready=true`
   - route recorded as `preserve_source_route`
   - scene-pack pending remained non-blocking

2. URL/reference + TTS-only + final done:
   - regression id mirrored: `01f530caabf5`
   - publish resolves `final.exists=true`, `composed_ready=true`,
     `compose_status=done`, `ready_gate.publish_ready=true`
   - false blockers `missing_voiceover`, `audio_not_ready`, and
     `compose_not_done` are absent

3. Scene-pack pending but final publishable:
   - publish keeps `ready_gate.publish_ready=true`
   - `scene_pack_pending_reason` stays present without downgrading final-ready

4. Final absent / compose genuinely in progress:
   - publish keeps `final.exists=false`, `composed_ready=false`,
     `compose_status=pending`, `ready_gate.publish_ready=false`

Additional contract-safety result:

- publish now starts from the same authoritative projection path as workbench
- the contract layer is not used here to rewrite authoritative truth after
  ready-gate computation

## Risks

- publish deliverable adaptation still has a surface-specific mapping layer,
  though it now consumes authoritative state instead of recomputing truth
- the workspace still has missing authority paths that should be restored or
  explicitly superseded in a later authority-doc refresh

## Rollback Path

- revert the publish-hub service changes in
  `gateway/app/services/task_view_presenters.py`
- restore the previous router call in `gateway/app/routers/hot_follow_api.py`
- revert the regression test file to the prior baseline if the shared-state
  adapter proves incompatible

## Acceptance Judgment

Accepted for this slice.

Reason:

- publish no longer re-derives final-ready truth from the stale compatibility
  helper path
- publish and workbench now share the same authoritative projection inputs
  before ready-gate evaluation
- contradiction-class regressions are covered locally without claiming a live
  replay that did not happen
