# Hot Follow Rebuild Engineering Rule Index v1

Status: Wave 0 frozen
Branch: `VeoReBuild01`

## Reading Declaration

Engineering-rule entrypoints read first:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `ENGINEERING_RULES.md`
- `ENGINEERING_STATUS.md`
- `PROJECT_RULES.md`

Business/document index entrypoints read second:

- `docs/ENGINEERING_INDEX.md`
- `docs/README.md`
- `docs/contracts/`
- `docs/architecture/`
- `docs/product/`
- `docs/design/`
- `docs/runbooks/`
- `docs/sop/hot_follow/`

Minimum task-specific authority files selected through the indexes:

- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_state_commit_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`
- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/architecture/factory_runtime_boundary_design_v1.md`
- `docs/architecture/factory_line_template_design_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/README.md`
- `docs/design/surface_workbench_lowfi_v1.md`
- `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
- `docs/runbooks/VERIFICATION_BASELINE.md`
- `docs/runbooks/hot_follow_sop.md`
- `docs/runbooks/ops/hot_follow_delivery_sop.md`
- `docs/runbooks/ops/hot_follow_publish_sop.md`
- `docs/sop/hot_follow/hot_follow_v_1_9_operations_manual.md`

This set is sufficient for Wave 0 because the task is docs/contract freeze for
Hot Follow rebuild on the stable backend layer, not runtime implementation.

## Frozen Engineering Rules

1. Rebuild work must be index-first.
   Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/ENGINEERING_INDEX.md`, `docs/contracts/engineering_reading_contract_v1.md`.

2. Wave 0 is docs and contracts only; no runtime behavior may change before the
   rule and contract baseline is frozen.
   Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/engineering_reading_contract_v1.md`, `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`.

3. Routers may parse requests, resolve dependencies, dispatch to services, and
   shape HTTP responses; routers must not own Hot Follow route truth, current
   attempt truth, artifact truth, ready-gate truth, or projection rules.
   Governing sources: `ENGINEERING_RULES.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`, `docs/contracts/production_line_runtime_assembly_rules_v1.md`.

4. Services own reusable business/runtime concerns and must expose explicit
   collaborator boundaries; service modules must not become new dumping grounds.
   Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `ENGINEERING_RULES.md`, `docs/contracts/production_line_runtime_assembly_rules_v1.md`.

5. Four-layer discipline is mandatory:
   L1 step execution only, L2 artifact facts only, L3 current attempt only,
   L4 ready gate/operator summary/advisory/presentation only.
   Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/four_layer_state_contract.md`, `docs/contracts/contract_driven_four_layer_state_baseline_v1.md`.

6. Every business truth field must have one writer or documented derived owner.
   Presenters, frontend, skills, and workers must not write repo truth,
   deliverable truth, ready-gate truth, or currentness truth.
   Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/status_ownership_matrix.md`, `docs/contracts/hot_follow_line_contract.md`.

7. L4 surfaces consume L2/L3 truth only and may not recompute route,
   currentness, compose readiness, publish readiness, or artifact truth.
   Governing sources: `docs/contracts/workbench_hub_response.contract.md`, `docs/contracts/hot_follow_projection_rules_v1.md`, `docs/design/README.md`.

8. Helper translation is auxiliary. Helper output or failure may be advisory,
   but it must not become authoritative target subtitle truth, route truth, or
   publish/compose blocking truth once mainline truth is valid.
   Governing sources: `docs/contracts/four_layer_state_contract.md`, `docs/contracts/hot_follow_state_machine_contract_v1.md`, `docs/architecture/hot_follow_business_flow_v1.md`.

9. Target subtitle truth requires authoritative commit: persisted text,
   persisted target artifact, source/currentness validation,
   `target_subtitle_current=true`, and
   `target_subtitle_authoritative_source=true`.
   Governing sources: `docs/contracts/hot_follow_state_commit_contract_v1.md`, `docs/contracts/status_ownership_matrix.md`, `docs/architecture/hot_follow_business_flow_v1.md`.

10. Compatibility wrappers may remain temporarily, but they must not absorb new
    business logic and must have a removal or replacement direction.
    Governing sources: `ENGINEERING_RULES.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`.

11. God-file growth is blocked. Wave 1+ must not expand `tasks.py`,
    `hot_follow_api.py`, or mixed `task_view.py` projection logic with new
    business orchestration.
    Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `ENGINEERING_RULES.md`, `ENGINEERING_STATUS.md`, `PROJECT_RULES.md`.

12. Hot Follow rebuild must preserve stable backend execution and artifact
    producers unless a later wave explicitly documents and approves an
    exception.
    Governing sources: `ENGINEERING_STATUS.md`, `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`, `docs/architecture/factory_runtime_boundary_design_v1.md`.

13. Validation must be proportional to blast radius, record interpreter,
    distinguish code regressions from environment limits, and include Hot
    Follow business regression when runtime behavior changes.
    Governing sources: `ENGINEERING_CONSTRAINTS_INDEX.md`, `ENGINEERING_RULES.md`, `PROJECT_RULES.md`, `docs/runbooks/VERIFICATION_BASELINE.md`, `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`.

## Wave 0 Constraint

Wave 0 is accepted only when this engineering rule index, the business rule
index, route event contract, CurrentAttempt contract, surface consumption
contract, component inventory, and freeze note are all committed as docs. Runtime
implementation starts no earlier than Wave 1.
