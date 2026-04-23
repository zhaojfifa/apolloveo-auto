# VEOBASE01 Minimal Contract Runtime Skeleton

Date: 2026-04-23
Branch: `VeoBase01-minimal-contract-runtime`
Base SHA: `11ec2c192ef74e89cdc0e98f39e8ad8a3208e003`

## Purpose

Turn the frozen ready-gate / projection / blocking-reason rules into a minimal
runtime skeleton so the selected Hot Follow state/projection subset stops being
owned implicitly by helper/router branches.

## Reading Declaration

Authority files read before code changes:

- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`
- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/execution/VEOBASE01_CODE_DEPOWERING_PLAN_V1.md`

Current phase authority:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_SEQUENTIAL_EXECUTION_DECISION.md`

State truth authority:

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
- `docs/contracts/status_ownership_matrix.md`

Ready-gate / projection / ownership authority:

- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`

## Runtime Subset Implemented

1. Ready-gate rule loading:
   - `gateway/app/services/contract_runtime/ready_gate_runtime.py`
   - `compute_hot_follow_state(...)` now consumes `evaluate_contract_ready_gate(...)`
     instead of evaluating the bound gate spec directly inside
     `hot_follow_state.py`.
2. Projection-rule loading:
   - `gateway/app/services/contract_runtime/projection_rules_runtime.py`
   - publish/workbench now apply loaded dominance and non-blocking rules from
     `docs/contracts/hot_follow_projection_rules_v1.md`.
3. Blocking-reason mapping loading:
   - `gateway/app/services/contract_runtime/blocking_reason_runtime.py`
   - canonicalization, non-blocking classification, and publish-ready
     suppression are now centralized.
4. Runtime reference loading:
   - `gateway/app/services/contract_runtime/runtime_loader.py`
   - line binding now exposes `projection_rules_ref`, and runtime loaders
     resolve the active refs from the bound line.

## Exact Contract Sources Used

- Ready gate: `docs/contracts/hot_follow_ready_gate.yaml`
- Projection rules: `docs/contracts/hot_follow_projection_rules_v1.md`
- Line runtime binding: `docs/architecture/line_contracts/hot_follow_line.yaml`
- State baseline and ownership semantics:
  - `docs/contracts/four_layer_state_contract.md`
  - `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/contracts/workbench_hub_response.contract.md`
  - `docs/contracts/production_line_runtime_assembly_rules_v1.md`

## Scope

- add the minimal `contract_runtime` module set
- route Hot Follow ready-gate evaluation through that runtime bridge
- route publish/workbench selected projection behavior through the projection
  runtime
- load blocking-reason normalization from contract data
- remove only the selected rule ownership now replaced by the runtime bridge

## Non-Goals

- no new line implementation
- no multi-role harness
- no contract editor UI
- no full state-engine replacement
- no full router/service rewrite
- no Hot Follow business-flow change
- no translation / helper translation / subtitle save semantic change
- no dub / compose / ffmpeg / worker runtime behavior change

## Files Changed

- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
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

## Ownership Removed

`gateway/app/services/task_view_helpers.py`

- publish-hub scene-pack pending reason no longer lives only in local helper
  branching when a projection contract ref is available
- helper fallback now consumes the contract-loaded blocking runtime for that
  reason subset

`gateway/app/routers/hot_follow_api.py`

- router no longer passes publish final-URL resolution into the workbench
  builder for the selected projection subset
- projection/runtime application remains inside service/presenter space

`gateway/app/routers/tasks.py`

- removed unused imports for selected helper-state/projection helpers:
  `compute_composed_state`, `resolve_hub_final_url`, `scene_pack_info`
- the generic fallback publish builder remains, but the selected publish
  scene-pack reason path now defers to contract runtime when the line is bound

`gateway/app/services/status_policy/hot_follow_state.py`

- removed local ready-gate ownership for selected route/compose blocking logic
- selected ready-gate enrichment now flows through
  `contract_runtime.ready_gate_runtime`

`gateway/app/services/task_view_presenters.py`

- removed local publish scene-pack pending-rule ownership
- publish/workbench selected projection dominance and non-blocking handling now
  flow through the projection runtime

`gateway/app/services/steps_v1.py`

- not touched in this pass

## Validation

Static / structural:

- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/task_view_presenters.py gateway/app/services/task_view_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/runtime_loader.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/blocking_reason_runtime.py gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py`
- `git diff --check`

Targeted pytest:

- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`

Result:

- `31 passed`

## Regression Evidence

Live exact-task replay was not executed in this workspace. The strongest
in-process evidence used in this pass was targeted regression coverage.

Contradiction-class coverage:

1. Local upload + preserved source audio + final done:
   - `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py::test_publish_hub_uses_authoritative_final_ready_state_for_local_upload_preserve`
2. URL/reference + TTS-only + final done:
   - `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py::test_publish_hub_uses_authoritative_final_ready_state_for_url_tts_only`
3. Scene-pack pending but final publishable:
   - `gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py::test_publish_hub_keeps_scene_pack_pending_non_blocking_when_final_ready`
   - `gateway/app/services/tests/test_contract_runtime_projection_rules.py::test_projection_runtime_final_ready_dominates_publish_truth`
4. Final absent / compose genuinely in progress:
   - `gateway/app/services/tests/test_contract_runtime_projection_rules.py::test_projection_runtime_preserves_in_progress_truth_without_final_dominance`

Additional runtime-binding evidence:

- line binding exposes `projection_rules_ref`
- status-policy entry now consumes `evaluate_contract_ready_gate(...)`
- blocking-reason alias/canonicalization is covered directly

## Risks

- projection rules are loaded from YAML code blocks inside a Markdown contract
  document, so future contract editing must preserve valid fenced YAML
- this pass covers only the selected ready-gate/projection/blocking subset; the
  broader state engine is still mixed between legacy helpers and newer policy
  paths
- `publish_hub_payload(...)` remains a fallback path and is only partially
  de-powered in this pass

## Rollback Path

- `git revert` the runtime skeleton commit on
  `VeoBase01-minimal-contract-runtime`, or reset the branch to
  `11ec2c192ef74e89cdc0e98f39e8ad8a3208e003` before this pass if the branch has
  not been published

## Acceptance Judgment

- selected ready-gate loading is now routed through contract runtime
- selected projection dominance and scene-pack non-blocking behavior are now
  loaded from contract-backed runtime data
- blocking-reason normalization for the selected subset is centralized
- publish/workbench contradiction coverage remained green
- Hot Follow business behavior was intentionally preserved
