# VEOBASE01 Contract Runtime Expansion Pass 2

Date: 2026-04-23
Branch: `VeoBase01-contract-runtime-expansion-pass2`
Base SHA: `e8ef8cb2f562dbc6b39c3ecb99b272f84be4042f`

## Purpose

Expand the Hot Follow contract-runtime path beyond the first minimal slice while
preserving current business behavior and publish/workbench alignment.

## Reading Declaration

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
   - This pass only expands Hot Follow contract-runtime coverage and ownership
     reduction for the selected ready-gate/projection/blocking subset. Broader
     scenario, product, review, and new-line docs were not required.

5. Missing-authority handling:
   - none

## Runtime Subset Expanded

- compose-input terminal mode handling now uses contract-loaded route/reason
  data instead of local literals only
- no-dub / no-tts compose route reason derivation now uses contract-loaded route
  maps
- compose-allowed reason derivation is centralized in projection runtime and
  consumed by workbench projection
- final-vs-historical surface selection now uses projection runtime precedence
  rules
- scene-pack pending reason fallback now resolves through one runtime helper
- blocking reasons now support contract-loaded priority ordering in addition to
  canonicalization and publish-ready suppression

## Contract Sources Used

- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

## Modules Changed

- `docs/contracts/hot_follow_projection_rules_v1.md`
- `gateway/app/services/contract_runtime/__init__.py`
- `gateway/app/services/contract_runtime/blocking_reason_runtime.py`
- `gateway/app/services/contract_runtime/projection_rules_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py`
- `gateway/app/services/tests/test_contract_runtime_projection_rules.py`
- `docs/execution/VEOBASE01_CONTRACT_RUNTIME_EXPANSION_PASS2.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`

## Ownership Removed

`gateway/app/services/task_view_helpers.py`

- removed local scene-pack pending fallback branching from `publish_hub_payload`
- helper now calls `scene_pack_pending_reason_for_task(...)` in
  `contract_runtime`

`gateway/app/services/task_view_presenters.py`

- final/current-vs-historical presentation selection now calls
  `select_presentation_final(...)` in `contract_runtime`

`gateway/app/services/task_view_workbench_contract.py`

- compose-allowed reason no longer hardcodes the no-dub/default reason branch
- contract adapter now consumes the already-derived runtime reason from
  `ready_gate`

`gateway/app/services/contract_runtime/ready_gate_runtime.py`

- route terminal mode, no-tts route reason, compose exec failed statuses, and
  compose-allowed reason derivation now use loaded projection-rule contract data

`gateway/app/services/contract_runtime/projection_rules_runtime.py`

- now owns selected final precedence, compose-allowed reason, scene-pack pending
  reason resolution, and publish/workbench selected field adaptation

`gateway/app/routers/hot_follow_api.py`

- not touched; no selected rule subset leaked there in this pass

`gateway/app/routers/tasks.py`

- not touched; no selected rule subset leaked there in this pass

`gateway/app/services/status_policy/hot_follow_state.py`

- not touched; pass-1 already routed ready-gate evaluation through
  `contract_runtime`

## Validation

- `git diff --check`: passed
- `PYTHONPYCACHEPREFIX=/tmp/apolloveo-pycache python3 -m py_compile gateway/app/services/contract_runtime/__init__.py gateway/app/services/contract_runtime/runtime_loader.py gateway/app/services/contract_runtime/ready_gate_runtime.py gateway/app/services/contract_runtime/projection_rules_runtime.py gateway/app/services/contract_runtime/blocking_reason_runtime.py gateway/app/services/task_view_helpers.py gateway/app/services/task_view_presenters.py gateway/app/services/task_view_workbench_contract.py gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py`: passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/tests/test_contract_runtime_projection_rules.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py`: `47 passed`

## Regression Classes Covered

- local upload + preserved source audio + final done
- URL/reference + TTS-only + final done
- final-ready + scene-pack pending but publishable
- final absent / compose genuinely in progress
- no-dub / no-tts compose-route gating via preserved-source, bgm-only, and empty
  subtitle compose tests

Live exact-task replay was not executed in this workspace. Evidence is
fixture/in-process coverage only.

## Risks

- Runtime rule data still lives in Markdown fenced YAML blocks. Future edits
  must preserve parseable YAML.
- The selected subset is broader but still not a full state-engine replacement.
- Some current-attempt summary logic remains in `hot_follow_route_state.py` and
  can be reduced in a later narrow pass.

## Rollback Path

- Revert the pass-2 commit on `VeoBase01-contract-runtime-expansion-pass2`.

## Acceptance Judgment

Accepted:

- more selected Hot Follow rule coverage is genuinely loaded from contract
  runtime
- helper/presenter/contract-adapter files lost real rule ownership for this
  subset
- publish/workbench alignment tests remained green
- no Hot Follow business behavior or execution semantics were intentionally
  changed
