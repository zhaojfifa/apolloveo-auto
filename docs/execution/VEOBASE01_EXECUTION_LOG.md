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
