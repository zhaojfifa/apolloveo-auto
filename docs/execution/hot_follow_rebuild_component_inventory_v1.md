# Hot Follow Rebuild Component Inventory v1

Status: Wave 0 frozen
Branch: `VeoReBuild01`

## Governing Sources

- `ENGINEERING_STATUS.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `ENGINEERING_RULES.md`
- `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/architecture/factory_runtime_boundary_design_v1.md`
- `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`

## Preserve Inventory

Preserve as stable backend service layer unless a later wave explicitly
versions this inventory:

| Component family | Preserve rule | Governing source |
| --- | --- | --- |
| L1 execution steps | Preserve step execution modules and provider/worker execution behavior. | `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`, `docs/architecture/factory_runtime_boundary_design_v1.md` |
| Parse/source artifact producers | Preserve source/raw artifact production and parse evidence production. | `docs/runbooks/hot_follow_sop.md`, `docs/architecture/factory_runtime_boundary_design_v1.md` |
| Subtitle authority anchors | Preserve target subtitle authority/currentness anchors; rebuild aggregation around them, not inside them. | `docs/contracts/hot_follow_state_commit_contract_v1.md`, `docs/contracts/status_ownership_matrix.md` |
| Artifact-fact producers | Preserve L2 artifact fact producers as factual inputs. | `docs/contracts/four_layer_state_contract.md`, `docs/contracts/status_ownership_matrix.md` |
| Voice/audio fact producers | Preserve voice state and audio artifact fact producers as inputs to L3. | `docs/contracts/status_ownership_matrix.md`, `docs/architecture/factory_runtime_boundary_design_v1.md` |
| Compose service | Preserve artifact-producing compose execution; do not expand compose/post optimization in Wave 0/1. | `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`, `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md` |
| Ready-gate engine and YAML | Preserve engine/YAML contract; Wave 2 may adapt extractors to consume L3. | `docs/contracts/hot_follow_line_contract.md`, `docs/contracts/hot_follow_ready_gate.yaml` |
| Skills bundle | Preserve as advisory/strategy reader only. | `docs/contracts/hot_follow_line_contract.md`, `docs/contracts/status_ownership_matrix.md` |
| Line registry and line contract metadata | Preserve line identity and runtime refs. | `docs/contracts/hot_follow_line_contract.md`, `docs/architecture/line_contracts/hot_follow_line.yaml` |
| Existing contract-aligned tests | Preserve and update only when contract changes require it. | `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/runbooks/VERIFICATION_BASELINE.md` |

## Rebuild Inventory

Rebuild or replace in waves:

| Component family | Rebuild rule | Wave |
| --- | --- | --- |
| Route truth ownership | Replace read-time route inference with explicit route command/event truth. | Wave 1 |
| L3 CurrentAttempt aggregation | Create one typed L3 producer for route/currentness/compose legality. | Wave 1 |
| Ready-gate signal extraction | Consume CurrentAttempt and L2 facts only; remove competing extraction truth. | Wave 2 |
| Operator summary/advisory | Consume CurrentAttempt/ready gate only; helper remains advisory. | Wave 2 |
| Workbench/publish/task-detail projection | Rebuild as L4 consumers of shared authoritative projection. | Wave 2 |
| Frontend consumption | Consume surface contract fields and explicit route commands only. | Wave 2 |
| Router orchestration shape | Shrink transport/router logic after L3/L4 contract path is stable. | Wave 3 or parallel shrink workstream |
| Compatibility aliases | Convert to read-only adapters or remove with documented migration. | Waves 2-3 |

## Explicitly Out Of Scope For Wave 0

- runtime behavior changes
- provider strategy redesign
- compose/post optimization
- platform-wide runtime generalization
- UI redesign
- second production line work
- broad router refactor

## Wave 1 Admission Condition

Wave 1 may start only after this inventory, engineering rule index, business
rule index, route event contract, CurrentAttempt contract, surface consumption
contract, and Wave 0 freeze note are all frozen.
