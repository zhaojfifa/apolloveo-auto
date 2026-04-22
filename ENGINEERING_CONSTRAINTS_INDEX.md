# Engineering Constraints Index

This file is the root-level engineering constraint entry for all future engineering work.

Root governance files remain the highest authority:

1. `PROJECT_RULES.md`
2. `ENGINEERING_RULES.md`
3. `CURRENT_ENGINEERING_FOCUS.md`
4. `ENGINEERING_STATUS.md`

This file defines how engineering work must be done. It does not replace the docs-level business/runtime/contract navigation entry in `docs/ENGINEERING_INDEX.md`. Before any future PR slice, read both:

- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Authority lists in these entry files must only name docs that actually exist,
unless the entry explicitly says one file is replaced by another.

## Engineering-Only Constraints

Engineering changes must be scoped, testable, and owned by the correct module boundary.

- A PR must have one primary engineering purpose.
- Runtime behavior changes must be declared before implementation.
- Structural extraction must preserve existing business behavior unless the PR explicitly says otherwise.
- Compatibility wrappers may exist temporarily, but new ownership must live in the target service/module.
- Generated or advisory output must not become persisted business truth.

## Big-File Prevention Rules

God-file growth is forbidden.

- Do not add new orchestration branches to `tasks.py` or `hot_follow_api.py` when a service can own the logic.
- Do not add presentation aggregation, policy evaluation, artifact truth checks, or contract interpretation to routers.
- Do not place new line-specific runtime contracts in general router files.
- If a touched file is already a hotspot, prefer extracting a cohesive helper or service over adding another conditional branch.
- Any PR adding substantial logic to an existing large file must explain why extraction is not the safer change.

The following drift patterns are explicitly blocked:

- god-file growth
- cross-router business logic accumulation
- hidden runtime coupling through router imports
- duplicated state evaluation in presenter and service layers

## Router/Service Ownership Rules

Routers own HTTP concerns only:

- request parsing
- dependency injection
- response status selection
- calling service entry points
- thin compatibility wrappers during staged extraction

Services own reusable business/runtime concerns:

- state assembly
- artifact fact evaluation
- current attempt resolution
- ready-gate evaluation
- presenter-safe aggregation
- line/runtime contract consumption
- skill/advisory orchestration

Routers must not become the source of business truth. Services must expose explicit collaborator injection points when tests or compatibility paths need controlled dependencies.

## Single-Writer And State Ownership Constraints

Every state field must have a single write owner or a documented derived owner.

- L1 step status is written by step execution.
- L2 artifact facts are derived from artifact truth.
- L3 current attempt is derived from runtime resolution.
- L4 ready gate, operator summary, advisory, and presentation consume L2/L3 and do not create truth.
- Repository writes must be owned by the service/controller responsible for that state.
- Presenter and advisory code may explain truth, but may not replace it.

Multiple write owners for the same business truth are forbidden unless an explicit contract names the owner split and validation coverage exists.

Rules-first foundation work must freeze architecture/state/runtime rules before
scenario onboarding. Scenario concepts must not enter runtime code before the
rule baseline is explicit in contracts/architecture docs.

## PR Slicing Rules

Each PR slice must be small enough to review for ownership and behavior.

- One PR should change one boundary or one contract surface.
- Do not mix architecture extraction with feature redesign.
- Do not combine helper translation, normal translation, dub, compose, and presenter changes unless the PR is explicitly a recovery fix requiring all of them.
- Do not start second-line implementation inside a boundary-hardening PR.
- When a PR changes a constraint, contract, or architecture surface, update the relevant docs in the same PR.
- If validation fails, stop the next slice and repair the current baseline first.

## Mandatory Validation Rules

Every engineering PR must run validation proportional to its blast radius.

Minimum validation:

- `py_compile` on changed Python files.
- `git diff --check`.
- focused pytest for the touched ownership boundary.
- contract/conformance tests when contracts or runtime bindings are touched.

Hot Follow business-path validation is required for changes touching:

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/task_view.py`
- `gateway/app/services/task_view_workbench_contract.py`
- `gateway/app/services/subtitle_helpers.py`
- `skills/hot_follow/input_skill.py`
- `skills/hot_follow/routing_skill.py`

Business validation must verify the relevant path does not regress:

- target subtitle main object truth
- canonical subtitle availability
- dub currentness
- compose readiness
- final output availability
- helper translation isolation when helper behavior is involved

## Write-Back And Update Rules

Before closing a PR:

- Update docs when ownership, constraints, contracts, or runtime paths change.
- Record exact validation commands and results.
- Record whether wire response shape changed.
- Record whether business behavior changed.
- Record any known validation gap instead of implying live coverage that was not run.
- Leave unrelated architecture or feature work for the next PR slice.

Execution logs are acceptable for run evidence. Permanent rules belong in root governance, this file, docs-level indexes, contracts, architecture docs, or ADRs according to their authority layer.

## Required Future Pre-Read

From PR-4 onward, every engineering PR must begin by reading:

1. Root governance files.
2. `ENGINEERING_CONSTRAINTS_INDEX.md`.
3. `docs/ENGINEERING_INDEX.md`.
4. `docs/contracts/engineering_reading_contract_v1.md`.
5. Task-specific contracts, architecture docs, ADRs, and execution logs selected through `docs/ENGINEERING_INDEX.md` and the reading contract.
