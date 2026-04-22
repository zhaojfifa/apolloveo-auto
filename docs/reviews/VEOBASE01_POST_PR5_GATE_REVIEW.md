# VeoBase01 Post-PR5 Gate Review

Date: 2026-04-22

Branch reviewed: `VeoBase01-pr5-new-line-onboarding-prep-and-schema-freeze`

Review scope:

- Hot Follow current product definition and architecture alignment
- task/router/workbench large-file diagnosis
- docs/contracts/architecture/code readiness before any new line

Business baseline evidence preserved in this review:

- URL sample `c084b276e819`
- local sample `8501fc94c1c8`

Mandatory pre-read completed:

1. `ENGINEERING_CONSTRAINTS_INDEX.md`
2. `PROJECT_RULES.md`
3. `ENGINEERING_RULES.md`
4. `ENGINEERING_STATUS.md`
5. `docs/README.md`
6. `docs/ENGINEERING_INDEX.md`
7. `docs/architecture/VEOBASE01_RECONSTRUCTION_BASELINE.md`
8. `docs/execution/VEOBASE01_EXECUTION_LOG.md`
9. `docs/contracts/four_layer_state_contract.md`
10. `docs/contracts/workbench_hub_response.contract.md`
11. `docs/contracts/hot_follow_line_contract.md`
12. `docs/contracts/skills_runtime_contract.md`
13. `docs/contracts/new_line_onboarding_template.md`
14. `docs/contracts/line_job_state_machine.md`
15. `docs/reviews/VEOBASE01_DOCS_STRUCTURE_AND_SHARED_LOGIC_REVIEW.md`

Additional active gate references also reviewed because root rules require them:

- `CURRENT_ENGINEERING_FOCUS.md`
- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`

## A. Executive Conclusion

### Gate Decision

- Next-line design readiness: `DESIGN READY`
- Next-line implementation readiness: `NOT IMPLEMENTATION READY`
- Multi-role harness introduction readiness: `NOT HARNESS READY`

### Executive Judgment

VeoBase01 is now structurally ready for future new-line design work in the
documentation and contract sense, but it is still not ready for second-line
runtime implementation.

Hot Follow is no longer just a pile of runtime patches. It is now explicitly
defined as a production line in docs and in runtime registration:

- line registry exists and Hot Follow is registered in
  `gateway/app/lines/hot_follow.py`
- workbench payload now exposes `line.runtime_refs`
- ready gate and skills bundle are real runtime-consumed references

However, the implementation surface around that line remains too heavy and too
compatibility-shaped to safely start a second production line:

- `gateway/app/routers/tasks.py` is 3,421 lines and still owns major
  orchestration and truth writes
- `gateway/app/routers/hot_follow_api.py` is 2,077 lines and still exceeds the
  router oversized threshold
- `gateway/app/services/task_view.py` is 1,018 lines and still concentrates
  workbench assembly, deliverable projection, and presentation aggregation
- the workbench contract is frozen, but the runtime payload still carries a
  large compatibility surface and post-build projection mutation
- line refs are only partially enforceable in runtime; worker/deliverable/asset
  sink/confirmation policy are still mostly metadata-bound rather than
  generic execution controls

### What Remains Blocked

Blocked for implementation:

- second production line implementation
- multi-role harness introduction into runtime
- any claim that Hot Follow router/service ownership is fully standardized

Not blocked:

- second production line design packet preparation
- new-line contract drafting against the PR-5 onboarding template
- further review-first thinning plans for routers, workbench, and state
  ownership

## B. Hot Follow Alignment

### Product Definition

Hot Follow is now correctly defined as a production line in the VeoBase01
baseline, not merely as a temporary runtime branch.

Evidence:

- `docs/contracts/hot_follow_line_contract.md` freezes line identity,
  input contract, deliverable profile reference, SOP profile reference,
  skills bundle reference, worker profile reference, asset sink profile
  reference, status policy reference, and ready gate reference
- `gateway/app/lines/hot_follow.py:9-35` registers `HOT_FOLLOW_LINE`
  with explicit contract metadata
- `gateway/app/services/line_binding_service.py:187-200` exposes that
  contract metadata plus `runtime_refs` into payloads

Conclusion:

- product-definition alignment is materially improved and now coherent enough
  for new-line design work
- Hot Follow should be treated as the first production line baseline

### Contract Reference Coherence

The current reference chain is coherent, but not equally runtime-enforced.

Coherently referenced and materially runtime-consumed:

- line identity and task kind
- ready gate reference
- skills bundle reference
- line registry binding

Coherently referenced but still mostly metadata or narrow introspection:

- worker profile reference
- deliverable profile reference
- asset sink profile reference
- confirmation policy
- status policy reference

Evidence:

- `gateway/app/services/line_binding_service.py:84-100` consumes
  `skills_bundle_ref`
- `gateway/app/services/line_binding_service.py:103-115` confirms
  `worker_profile_ref` existence
- `gateway/app/services/line_binding_service.py:118-149` parses the Hot Follow
  YAML to expose deliverable kinds, but does not drive runtime acceptance from
  that profile
- `gateway/app/services/line_binding_service.py:152-165` confirms
  `asset_sink_profile_ref` and reports `auto_sink_enabled`, but no generic
  asset sink engine exists
- `gateway/app/services/status_policy/registry.py:16-18` only registers
  `apollo_avatar`; Hot Follow still falls through the default policy path

Judgment:

- coherent reference graph: yes
- fully enforceable line-general runtime control: no

### Runtime Behavior Alignment

The current runtime behavior still matches the preserved business baseline
evidence:

- URL sample `c084b276e819`: parse, subtitles, dub, compose, final,
  `compose_ready=true`, `publish_ready=true`
- local sample `8501fc94c1c8`: parse, subtitles, dub, and
  `tts_voiceover_plus_source_audio` path valid

Representative validation references recorded in VeoBase01 execution history:

- PR-2 workbench/state freeze: `72 passed`
- PR-3 router/service ownership boundary: `72 passed`
- PR-4 line binding and skills boundary: `43 passed`
- PR-4 representative runtime/business pytest set: `145 passed, 2 deselected`
- PR-5 docs/schema freeze: `git diff --check` passed, cross-link checks passed,
  schema/example checks passed

### Operator-Facing Logic

Operator-facing logic is more disciplined than before, but still concentrated in
one workbench assembly surface.

Good:

- operator summary and advisory are explicitly L4 concepts in the workbench
  contract
- advisory remains read-only and is attached after the main payload assembly

Risks:

- `gateway/app/services/task_view.py:769-1018` still combines
  workbench assembly, deliverable projection syncing, ready-gate projection
  repair, compatibility aliasing, line metadata attachment, and advisory
  attachment in one function
- the workbench remains Hot-Follow-shaped, not yet safely line-general

### Current Limitations

Hot Follow is aligned enough to serve as the baseline line, but not yet as a
copy-safe template for implementing a second line.

Current limitations:

- router-owned orchestration remains too large
- workbench compatibility residue remains large
- line refs are not yet full runtime controls
- `/api` and `/v1` semantics are still meaningfully split

## C. Architecture Readiness

### Four-Layer State Review

#### L1 `pipeline_step_status`

The current implementation respects the idea that L1 is operational step state,
but write ownership remains too distributed.

Evidence:

- routers still call `policy_upsert()` directly through wrappers in
  `gateway/app/routers/tasks.py:88-89` and
  `gateway/app/routers/hot_follow_api.py:166-168`
- `tasks.py` still contains 27 `_policy_upsert(...)` call sites
- `hot_follow_api.py` still contains 9 `_policy_upsert(...)` helper call sites,
  plus direct `policy_upsert(...)`

Assessment:

- semantic model: mostly aligned
- write-boundary discipline: still weak

#### L2 `artifact_facts`

L2 is conceptually correct, but artifact fact assembly is still partially owned
by presenter/service code rather than a thinner accepted-deliverable boundary.

Evidence:

- `gateway/app/services/task_view.py:377-518` builds deliverable rows by mixing
  storage checks, fallback status fields, and endpoint URL generation
- `gateway/app/services/task_view.py:630-649` builds artifact facts in service
  space
- `gateway/app/services/task_view_workbench_contract.py:414-439` and
  `470-511` later mutate final deliverable projection based on higher-layer
  readiness

Assessment:

- artifact fact concepts: aligned
- clean single accepted-deliverable boundary: not yet

#### L3 `current_attempt`

L3 derivation is materially present and clearer than before.

Evidence:

- `gateway/app/services/task_view.py:652-674` builds current attempt summary
- `gateway/app/services/contracts/hot_follow_workbench.py:38-47` freezes L3
  fields in the typed model
- Hot Follow currentness and ready-gate tests are referenced in the VeoBase01
  execution log

Assessment:

- L3 semantics: aligned
- L3 isolation from L4 patching: improved, but not fully clean because
  workbench post-processing still rewrites downstream projections

#### L4 `ready_gate` / `operator_summary` / `advisory` / presentation

L4 is explicitly modeled and mostly respected, but the presentation layer still
performs corrective mutation after state computation.

Evidence:

- `gateway/app/services/task_view.py:994-1011` applies ready-gate compose
  projection after `compute_hot_follow_state(...)`
- `gateway/app/services/task_view_workbench_contract.py:442-467` rewrites
  compose readiness aliases and pipeline status
- `gateway/app/services/task_view_workbench_contract.py:470-511` rewrites final
  deliverable rows after ready-gate interpretation

Assessment:

- L4 existence and contracts: aligned
- semantic leakage into projection repair: still present

### Remaining Split-Brain / Semantic Leakage

Remaining risks:

1. `deliverables` are still a projection, then further mutated by ready-gate
   helpers, so they are not a pristine readout of accepted truth.
2. compose pipeline rows can still be rewritten after state computation.
3. workbench compatibility aliases mean multiple surfaces can describe the same
   underlying fact.

Overall four-layer judgment:

- frozen enough for design: yes
- clean enough for new-line implementation: no

### SSOT / Write-Boundary Review

#### Deliverables As Truth Source

Deliverables are not and should not be the single source of truth. The current
contracts correctly define them as a projection from L2/L4, not the underlying
accepted truth.

The real issue is different:

- accepted artifact truth is still not owned through one thin deliverable
  acceptance boundary
- deliverable projection is still being patched after the main state compute

#### Repo/State Write Unification

Repo/state writes are still not sufficiently unified.

Evidence:

- router-owned `_policy_upsert(...)` remains common in `tasks.py`
- `tasks.py:2463-3135` performs a long dub execution transaction with multiple
  writebacks inside the router
- `tasks.py:2298-2313` still queues pipeline background execution directly from
  the router
- `hot_follow_api.py:1483-1604` still creates and persists local-upload tasks in
  router space

Judgment:

- write filtering exists through `policy_upsert()`
- write ownership is still too router-heavy for a second-line implementation

#### `/api` And `/v1` Split

`/api` and `/v1` semantics are still split in a meaningful way.

Evidence:

- `gateway/app/main.py:171-180` includes both task routers and `v1_actions`
- `gateway/app/routers/tasks.py` exposes many `/v1/tasks/...` artifact and hub
  pages/download endpoints
- `gateway/app/routers/hot_follow_api.py` exposes `/api/hot_follow/...`
  operational endpoints

Judgment:

- split still exists
- not an immediate design blocker
- still a structural blocker for claiming clean runtime unification

#### Presentation Derived From Truth

Presentation is much closer to truth-derived than before, but it still performs
repair logic that compensates for legacy fields and compatibility needs.

Evidence:

- `gateway/app/services/task_view_workbench_contract.py:389-403` attaches
  compatibility aliases
- `gateway/app/services/contracts/hot_follow_workbench.py:8-9` and `97-125`
  intentionally allow extra fields

Judgment:

- presentation is no longer obviously hiding truth bugs
- presentation is still patching over compatibility debt

### Line-Contract / Runtime-Binding Review

Hot Follow line binding is real enough to support design gating, but not yet
strong enough to support second-line runtime implementation.

Strong runtime binding:

- line registration
- line lookup by task kind
- workbench `line.runtime_refs`
- ready gate spec lookup
- skills bundle loading

Partial or metadata-only binding:

- status policy reference
- deliverable profile runtime control
- asset sink runtime control
- confirmation policy runtime control

Evidence:

- `gateway/app/lines/hot_follow.py:9-35`
- `gateway/app/services/line_binding_service.py:168-220`
- `gateway/app/services/status_policy/registry.py:16-18`

### Skills Boundary Review

Skills boundary is coherent and frozen enough for future design work.

Positive signals:

- skills runtime contract is explicit
- skills bundle boundary is explicit
- advisory remains read-only
- line binding consumes the skills bundle reference through runtime refs

Remaining limitation:

- skills are still Hot-Follow-first rather than proven line-general
- this is acceptable for design readiness, but not enough to clear the
  implementation or harness gates

## D. Code Structure Diagnosis

### Summary Classification

| File | Role | Line Count | Rule Status | Current Classification |
| --- | --- | ---: | --- | --- |
| `gateway/app/routers/tasks.py` | mixed pages/download/api router plus pipeline and dub orchestration | 3421 | router oversized threshold exceeded (`> 1800`) | blocking |
| `gateway/app/routers/hot_follow_api.py` | Hot Follow API router plus workbench adapters and task creation/update flows | 2077 | router oversized threshold exceeded (`> 1800`) | blocking |
| `gateway/app/services/task_view.py` | workbench/publish presenter service and projection assembly | 1018 | above service target (`> 900`), below oversized threshold (`< 1400`) | transitional, not final |
| `gateway/app/services/task_view_workbench_contract.py` | workbench payload builder and compatibility projection helpers | 516 | acceptable on size | transitional due semantic coupling |
| `gateway/app/services/contracts/hot_follow_workbench.py` | typed workbench contract model | 126 | acceptable | acceptable |

### `gateway/app/routers/tasks.py`

Current role:

- generic task router
- page/download router for `/v1/tasks/...`
- API router under `/api`
- background pipeline runner
- dub orchestration surface
- compose entry bridge

Measured hotspots:

- 47 route handlers
- `_run_dub_job()` at line 2463, 673 lines
- `_run_pipeline_background()` at line 1544, 168 lines
- `create_task_local_upload()` at line 1913, 110 lines

Rule violations or near-violations:

- file size violation: 3421 lines exceeds router oversized threshold 1800
- severe function-size violation: 673-line orchestration function exceeds the
  120-line decomposition threshold
- router still owns orchestration and many state writes
- compatibility bridge usage remains embedded in a generic router:
  `tasks.py:2271-2291`

Current judgment: `blocking`

Required thinning path:

1. move dub transaction execution out of router space first
2. move pipeline background orchestration out of router space second
3. remove remaining Hot Follow compatibility entrypoints from this router
4. leave `tasks.py` as transport, download/page handling, and minimal delegation

### `gateway/app/routers/hot_follow_api.py`

Current role:

- Hot Follow-specific API router
- local-upload task creation/update surface
- workbench/publish route surface
- compatibility adapter layer for service-owned helpers

Measured hotspots:

- 16 route handlers
- `create_hot_follow_task_local_upload()` at line 1483, 122 lines
- `translate_hot_follow_subtitles()` at line 1837, 85 lines
- `patch_hot_follow_audio_config()` at line 1680, 72 lines

Rule violations or near-violations:

- file size violation: 2077 lines exceeds router oversized threshold 1800
- local-upload creation still performs repo create, artifact upload, and
  `policy_upsert()` in router space: `1483-1604`
- router still carries duplicate workbench presentation helpers:
  `_hf_artifact_facts()` at `1229`, `_hf_current_attempt_summary()` at `1251`,
  `_hf_safe_presentation_aggregates()` at `1291`
- router still passes a large adapter bundle into the service workbench builder:
  `1635-1660`

Current judgment: `blocking`

Required thinning path:

1. remove duplicate presentation aggregate helpers from the router
2. move local-upload task construction/persistence into a service/controller
3. keep only route parsing and service entry delegation here

### `gateway/app/services/task_view.py`

Current role:

- service-owned workbench and publish payload assembly
- deliverable projection
- artifact facts and current attempt summary assembly
- presentation fallback/defaults aggregation

Measured hotspots:

- `build_hot_follow_workbench_hub()` at line 769, 250 lines
- `hf_deliverables()` at line 377, 142 lines
- `collect_hot_follow_workbench_ui()` at line 121, 103 lines

Rule violations or near-violations:

- file size near violation: 1018 lines is above the 900-line service target
- `build_hot_follow_workbench_hub()` exceeds the 120-line orchestration
  decomposition threshold
- `hf_deliverables()` exceeds the 120-line decomposition threshold
- service is now the right ownership direction, but it still aggregates too much
  workbench logic into one module

Current judgment: `transitional`

Required thinning path:

1. split deliverable projection from workbench assembly
2. split L2/L3 aggregate computation from final payload composition
3. leave `task_view.py` with orchestration of smaller service helpers only

### `gateway/app/services/task_view_workbench_contract.py`

Current role:

- presentation-only payload builder
- compatibility alias attachment
- ready-gate-based projection updates

Measured hotspots:

- `build_hot_follow_workbench_payload()` at line 111, 90 lines
- `_set_compose_pipeline_status()` at line 470, 47 lines
- `_subtitles_section()` at line 234, 46 lines

Rule status:

- size is acceptable
- function sizes are mostly acceptable or near-target

Remaining concern:

- semantic coupling remains high
- the builder still emits compatibility-heavy fields such as `pipeline_legacy`,
  `final`, `historical_final`, `task`, `source_video`, `audio_config`, `title`,
  and `platform`
- the helper layer mutates deliverables and pipeline after ready-gate decisions

Current judgment: `transitional`

Required thinning path:

1. separate frozen contract fields from compatibility aliases
2. stop mutating deliverables/pipeline after the main state compute where
   possible
3. define a removal path for legacy aliases before multi-line extension

### `gateway/app/services/contracts/hot_follow_workbench.py`

Current role:

- typed contract model for workbench payload validation

Strength:

- small and clear
- enforces required L1/L2/L3/L4 sections

Remaining concern:

- `_CompatModel` uses `extra="allow"` at `8-9`
- this is acceptable during reconstruction, but it means the typed contract is
  still compatibility-tolerant rather than fully closed

Current judgment: `acceptable but intentionally open`

## E. Docs Structure Readiness

### Root Engineering Constraints

Ready and coherent:

- root governance files and engineering constraints are now clearly layered
- file-size, function-size, router/service, and truth-source rules are explicit

### Docs README + Engineering Index

Ready and coherent:

- `docs/README.md` now clearly separates placement authority
- `docs/ENGINEERING_INDEX.md` now clearly separates reading paths and gate rules
- PR-5 added the glossary, onboarding template, line-job state machine, and
  skills bundle boundary in the correct contract bucket

### Contract Placement

Current placement is good:

- contracts are in `docs/contracts/`
- structure baseline lives in `docs/architecture/`
- execution evidence lives in `docs/execution/`
- reviews stay in `docs/reviews/`

### Archive / Review / Execution Misuse Risk

Current risk level: `low to moderate`

Why it is lower now:

- the docs explicitly define the authority order
- PR-5 preparation docs do not pretend to be runtime implementation

What still needs discipline:

- execution logs must not become hidden contract policy
- the active gate review must still be promoted into future contract or
  architecture docs if implementation rules change
- legacy docs exceptions still exist:
  - `docs/scenarios/`
  - `docs/sop/`
  - `docs/hot_follow_workbench_closure.md`

Docs readiness judgment:

- docs structure is not the blocker now
- runtime/code structure remains the blocker

## F. New-Line / Harness Gate

### DESIGN READY

`YES`

Reason:

- product line vocabulary is frozen
- new-line onboarding template exists
- line-job state machine exists
- skills bundle boundary exists
- minimal example profiles exist
- Hot Follow is documented and runtime-bound enough to serve as the reference
  line for design work

Allowed under this gate:

- second-line design packet drafting
- second-line contract design
- multi-role harness design/spec work on paper

### IMPLEMENTATION READY

`NO`

Reason:

- `tasks.py` is still structurally unsafe for new-line onboarding
- `hot_follow_api.py` is still oversized and still owns too much logic
- `task_view.py` is still too heavy and still workbench-centric
- workbench contract is not yet compatibility-thin
- line refs are only partially runtime-enforced
- write ownership is not yet thin enough to prevent copying router drift into a
  second line

### HARNESS READY

`NO`

Reason:

- PR-5 documents multi-role harness prerequisites, but runtime ownership is not
  yet thin enough to enforce them
- harness states must be derivable from L1-L4 facts, but current workbench and
  router surfaces still contain compatibility repair logic
- role handoff validation would currently inherit too much router/task-view
  coupling

## G. Remaining Gaps Before New Line

### Docs Gaps

No major blocking docs gap remains for design work.

Minor remaining docs gap:

- future implementation PRs will need a more explicit runtime-consumption story
  for status policy, deliverable acceptance, asset sink control, and
  confirmation policy

### Contract Gaps

- status policy reference is documented, but not yet line-general in runtime
- deliverable profile is referenced, but runtime still derives deliverables from
  service logic rather than a generic accepted-deliverable engine
- asset sink profile is referenced, but not enforced by a generic runtime sink
  boundary
- confirmation policy exists in line metadata, but not through a generic
  confirmation gate engine

### Runtime Gaps

- router-owned orchestration remains too large
- `/api` and `/v1` task semantics remain split
- compatibility bridges remain active and still part of normal runtime paths

### State-Model Gaps

- L2 accepted artifact truth is still checked in presenter-oriented service code
- L4 projection still mutates deliverables and pipeline after state compute
- write ownership is filtered by policy, but not sufficiently centralized at the
  source

### File-Structure / Ownership Gaps

- `tasks.py`: blocking
- `hot_follow_api.py`: blocking
- `task_view.py`: transitional but too heavy for line scaling
- router duplicate helper residue remains in Hot Follow API

## Ordered Next Actions

Strict order, not parallel:

1. Thin `gateway/app/services/task_view.py` and
   `gateway/app/services/task_view_workbench_contract.py` so the workbench
   contract path separates frozen contract fields from compatibility alias
   projection and no longer rewrites deliverable state as heavily.
2. Thin `gateway/app/routers/hot_follow_api.py` so router-local duplicate
   presentation helpers disappear and local-upload task creation/update logic is
   moved behind a service/controller boundary.
3. Thin `gateway/app/routers/tasks.py` by extracting dub transaction ownership
   and pipeline background orchestration out of router space.
4. Unify or explicitly deprecate the remaining `/v1/tasks/...` versus `/api/...`
   split so new lines do not inherit mixed runtime semantics.
5. Make line-bound runtime controls stronger for status policy, deliverable
   acceptance, asset sink policy, and confirmation policy.
6. Only after steps 1-5 pass review and regression validation should a second
   production line implementation PR be considered.
7. Multi-role harness introduction must remain blocked until the same thinning
   work proves role handoffs can be asserted from L1-L4 evidence without
   compatibility repair logic.

Second-line implementation remains blocked at the end of this review.

## Validation And Evidence

This review used:

- file-size checks with `wc -l`
- function-size checks with AST-based line counting
- route-handler counts via AST
- targeted code inspection with line-numbered reads for:
  - `gateway/app/routers/tasks.py`
  - `gateway/app/routers/hot_follow_api.py`
  - `gateway/app/services/task_view.py`
  - `gateway/app/services/task_view_workbench_contract.py`
  - `gateway/app/services/contracts/hot_follow_workbench.py`
  - `gateway/app/services/line_binding_service.py`
  - `gateway/app/services/status_policy/registry.py`
  - `gateway/app/services/hot_follow_runtime_bridge.py`
  - `gateway/app/services/task_router_actions.py`
  - `gateway/app/main.py`

Representative validation references reused from VeoBase01 execution history:

- PR-2 typed workbench and four-layer freeze: `72 passed`
- PR-3 router/service ownership boundary: `72 passed`
- PR-4 line runtime consumption and skills boundary: `43 passed`
- PR-4 representative business/runtime pytest set: `145 passed, 2 deselected`
- PR-5 docs/schema freeze: `git diff --check` passed, cross-link checks passed,
  schema/example consistency checks passed
