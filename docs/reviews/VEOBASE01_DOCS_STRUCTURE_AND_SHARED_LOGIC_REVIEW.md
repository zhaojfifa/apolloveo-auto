# VeoBase01 Docs Structure And Shared Logic Review

Date: 2026-04-22

Branch: `VeoBase01`

## Purpose

This review re-anchors documentation placement, shared reading logic, and shared architecture logic before the main PR-4 runtime slice starts.

It does not start PR-4 runtime work, does not implement a second line, and does not change translation, dub, or compose behavior.

## File-Sharing Logic

### Who Reads Which Files First

All engineering roles start with:

1. Root governance: `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`
2. Root engineering constraints: `ENGINEERING_CONSTRAINTS_INDEX.md`
3. Docs structure entry: `docs/README.md`
4. Docs task-oriented entry: `docs/ENGINEERING_INDEX.md`

Business-line implementers then read:

- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- relevant contracts in `docs/contracts/`
- relevant architecture docs in `docs/architecture/`
- latest execution note in `docs/execution/`

Architecture reviewers then read:

- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/adr/ADR-VEOBASE01-LINE-STATE-CONTRACT.md`
- relevant review evidence in `docs/reviews/`

Runtime contract implementers then read:

- `docs/contracts/line_contract.schema.json`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/status_ownership_matrix.md`

Skill and advisory implementers then read:

- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/SKILLS_MVP_ADVISORY_CONTRACT.md`
- `docs/contracts/status_ownership_matrix.md`
- line-specific architecture and execution notes selected through `docs/ENGINEERING_INDEX.md`

### Authoritative Docs By Purpose

| Purpose | Authority |
| --- | --- |
| How engineering work is done | `ENGINEERING_CONSTRAINTS_INDEX.md` |
| Where docs belong | `docs/README.md` |
| What to read for a task | `docs/ENGINEERING_INDEX.md` |
| Current project baseline | `docs/baseline/PROJECT_BASELINE_INDEX.md` |
| Runtime boundary | `docs/contracts/*` |
| Structural architecture | `docs/architecture/*` |
| Accepted decision | `docs/adr/*` |
| Execution evidence | `docs/execution/*` |
| Diagnostic evidence | `docs/reviews/*` |
| Historical reference | `docs/archive/*` |

### Docs That Cannot Substitute For Others

- Reviews cannot substitute for runtime contracts.
- Execution logs cannot substitute for permanent architecture rules.
- Archive docs cannot substitute for active implementation sources.
- Runbooks cannot substitute for ownership contracts.
- ADRs cannot substitute for validation evidence.
- `docs/README.md` cannot substitute for task-oriented reading paths in `docs/ENGINEERING_INDEX.md`.
- `docs/ENGINEERING_INDEX.md` cannot substitute for root engineering constraints in `ENGINEERING_CONSTRAINTS_INDEX.md`.

## Architecture-Sharing Logic

### Shared Object Model

Production Line:

- A business execution line under an explicit line contract.
- Shared through line contract refs, SOP profile refs, skills bundle refs, worker profile refs, deliverable profile refs, and asset sink profile refs.
- New lines must not copy Hot Follow router orchestration.

Four-layer State:

- L1: pipeline step status only.
- L2: artifact facts only.
- L3: current attempt/runtime resolution only.
- L4: ready gate, operator summary, advisory, and presentation only.
- L4 consumes L2/L3 and must not create new business truth.

Workbench Contract:

- The workbench response is a typed runtime payload.
- It must preserve wire compatibility unless a PR explicitly changes the contract and validates the UI/runtime impact.
- Workbench presentation cannot invent artifact or current-attempt truth.

Skills Boundary:

- Skills read line facts and current state.
- Skills return advisory or routing suggestions.
- Skills cannot write repository truth, artifact truth, ready-gate truth, or deliverable truth.

Worker Profile:

- Worker profile declares execution resources and provider policy.
- Workers can return artifacts and structured results.
- Accepted persisted truth is written by the owning service/controller, not by the worker profile itself.

Deliverable Profile:

- Deliverable profile declares primary, secondary, and optional outputs and acceptance rules.
- Deliverable profile does not make a presenter the owner of artifact truth.

Asset Sink Profile:

- Asset sink profile is downstream of accepted deliverable truth.
- Asset sinks cannot promote unaccepted artifacts into canonical truth.

## File Priority Matrix

| Priority | File Class | Role |
| --- | --- | --- |
| 1 | Root governance | highest project and engineering authority |
| 2 | Root engineering constraints | engineering method and constraint authority |
| 3 | Baseline/gate docs | current project/business baseline and gate authority |
| 4 | Contracts | runtime boundary authority |
| 5 | Architecture docs | structural design authority |
| 6 | ADRs | accepted decision authority |
| 7 | Execution logs | branch/phase evidence |
| 8 | Reviews | diagnostic evidence and analysis |
| 9 | Archive | historical reference only |

## Forbidden Doc Misuse

- Archive is not an active implementation source.
- Execution logs are not permanent architecture rules.
- Review docs are not runtime contracts.
- Presenter code cannot redefine truth.
- Skills cannot write truth.
- Runtime contracts cannot be bypassed by citing a future-state review.
- Historical SOP docs cannot override current line/state/contract authority.

## New-Line And Multi-Role Harness Readiness

Before starting a new production line, these must exist:

- frozen four-layer state contract
- typed workbench response contract
- explicit line contract runtime consumption
- skills boundary and loader contract
- worker profile refs
- deliverable profile refs
- asset sink profile refs
- business regression validation for existing Hot Follow behavior
- docs placement and reading-path discipline from `docs/README.md` and `docs/ENGINEERING_INDEX.md`

Before introducing multi-role harness work, these must exist:

- role-specific reading paths in `docs/ENGINEERING_INDEX.md`
- root engineering constraints in `ENGINEERING_CONSTRAINTS_INDEX.md`
- runtime ownership matrix in `docs/contracts/status_ownership_matrix.md`
- explicit contract for which role reads, derives, presents, or writes state
- validation proving roles do not create multiple write owners for the same truth
- archive/review/execution docs separated from active runtime contracts

## Current Structure Assessment

The target top-level docs layout is present:

- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/baseline/`
- `docs/reviews/`
- `docs/execution/`
- `docs/contracts/`
- `docs/architecture/`
- `docs/architecture/line_contracts/`
- `docs/runbooks/`
- `docs/skills/`
- `docs/adr/`
- `docs/archive/`

Legacy exceptions remain and are intentionally not moved in this pass:

- `docs/scenarios/`
- `docs/sop/`
- `docs/hot_follow_workbench_closure.md`

Future changes should not add new docs to those legacy exception paths unless the PR explicitly justifies preserving a legacy reference.

## PR-4 Readiness

After this docs-structure normalization pass, PR-4 runtime work may begin only if the implementer first reads:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
- relevant contracts selected by the task-oriented reading path

