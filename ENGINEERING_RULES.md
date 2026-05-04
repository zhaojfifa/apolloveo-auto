# Engineering Rules

## 1. File Size Rules

- router file target: `< 1200` lines
- service file target: `< 900` lines
- oversized threshold:
  - router: `> 1800` lines
  - service: `> 1400` lines
- if a file crosses the oversized threshold, the PR must state a thinning plan or a follow-up thinning path

## 2. Function Size Rules

- normal function target: `< 40` lines
- orchestration function target: `< 80` lines
- decomposition threshold:
  - normal function: `> 60` lines
  - orchestration function: `> 120` lines

## 3. Router Rules

Router may only own:

- request parsing
- auth / permission entry
- response mapping
- thin compatibility wrapper

Router must not own:

- business orchestration
- media flow control
- line-specific state logic
- artifact truth derivation

## 4. Service Rules

- service owns business / runtime flow
- service must not become a dumping ground
- unrelated orchestration must be split instead of appended

## 5. Import / Dependency Rules

- no router-to-router coupling
- no circular imports
- no lazy import used to hide architecture problems
- cross-boundary interaction should go through service / contract / registry boundaries

## 6. Contract-First Rules

- if runtime semantics change, the related contract / runbook / execution doc must be updated in the same PR
- do not let docs lag behind behavior changes

## 7. Compatibility Rules

- compatibility helpers must be explicitly temporary
- new compatibility helpers require a stated removal path
- compatibility code must not absorb new business logic

## 8. Truth-Source Rules

- presentation must derive from artifact / runtime facts
- legacy status must not override fact-based truth
- no UI patching to hide source-of-truth problems

## 9. Factory Alignment Gate Rules

- No second/new production line work may enter `main` until the active factory alignment review prerequisites are cleared.
- `tasks.py` must not receive new line-specific logic, scenario-specific orchestration, state semantics, or production-line onboarding logic.
- `hot_follow_api.py` must not grow new business orchestration or new line-extension logic.
- Do not add new mixed L1/L2/L3/L4 state projection logic into `task_view.py` or workbench builders.
- Line contract, deliverable profile, asset sink profile, worker profile, SOP profile, and confirmation policy must not be presented as runtime-bound if they remain metadata-only or ceremonial.
- Any PR touching workbench or publish payload shape must update the related contract/docs in the same PR.
- Any PR touching new-line onboarding, router restructuring, four-layer state, ready gate, deliverables SSOT, Skills, Worker Gateway, line runtime binding, or publish/workbench contracts must cite `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` and the relevant appendices.

## 10. Validation Rules

- no merge without required regression
- interpreter / environment must be stated
- distinguish code regressions from environment limitations

## 11. Scope Control Rules

Every PR must state:

- what it fixes
- what it does not fix
- what remains follow-up

## 12. Default Project Entry Map

Before starting any engineering PR, after the root indexes and the docs indexes, consume `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` to confirm the current wave, the affected line, the surface position, and the frozen next engineering sequence. The map is a navigation document; it does not replace contracts, reviews, architecture docs, wave 指挥单, execution logs, or the master plan — when its wording conflicts with any of those, the underlying authority wins.

## 13. Product-Flow Module Presence Rule

When a line is under operator workflow convergence (Operator Workflow Convergence Wave / OWC, or any successor wave with the same convergence intent), every PR claiming operator-ready or trial-ready scope on that line MUST extend the line's operator surface block on `gateway/app/templates/tasks.html`, `gateway/app/templates/task_workbench.html`, and/or `gateway/app/templates/task_publish_hub.html` to expose the product-flow module the PR delivers. Service / projection / contract additive landings without surface convergence are by definition incomplete for an operator-ready claim and must be returned for surface convergence before merge.

Authority surfaces that bind the module-presence check (consume the line-specific authority for the touched line; not all are cited per PR):

- factory-wide abstract flow: `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- operator-visible surfaces: `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- design handoff: `docs/handoffs/apolloveo_2_0_design_handoff_v1.md`
- Matrix Script line-specific execution authority: `docs/product/matrix_script_product_flow_v1.md`
- Digital Anchor line-specific execution authority: `docs/product/digital_anchor_product_flow_v1.md`

Reviewer obligation: for every PR claiming convergence on one of those lines, the reviewer MUST open the relevant template branches and verify each module enumerated in the PR's scope is operator-visible. A PR that lands a service module + a wiring seam + a contract addendum but does not also extend the line's `tasks.html` / `task_workbench.html` / `task_publish_hub.html` operator block to expose the module is by definition incomplete and must be returned. This rule complements §6 (Contract-First) and §8 (Truth-Source); it does not relax either.
