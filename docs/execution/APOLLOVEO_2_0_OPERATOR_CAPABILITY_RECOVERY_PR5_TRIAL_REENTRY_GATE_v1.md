# ApolloVeo 2.0 · Operator Capability Recovery · PR-5 · Real Operator Trial Re-Entry Gate v1

Date: 2026-05-04
Status: **Trial re-entry gate document.** This is the binding gate for
real operator trial re-entry after the Minimal Operator Capability
Recovery wave (PR-1 / PR-2 / PR-3 / PR-4) has all merged to `main`.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery — Re-entry.
Decision authority:
[`docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md).
Action authority:
[`docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md) §8 (PR-5).
Predecessors (all MERGED to `main` 2026-05-04):
- PR-1 ([#114](https://github.com/zhaojfifa/apolloveo-auto/pull/114), squash `4c317c4`)
- PR-2 ([#116](https://github.com/zhaojfifa/apolloveo-auto/pull/116), squash `4343bec`)
- PR-3 ([#118](https://github.com/zhaojfifa/apolloveo-auto/pull/118), squash `d53da0f`)
- PR-4 ([#119](https://github.com/zhaojfifa/apolloveo-auto/pull/119), squash `0549ee0`)

## 0. Why this document exists

The pre-recovery Plan A trial brief
[`docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
froze a trial that was, by the recovery decision §1.1, an
"authority-only" trial — operators could not actually exercise an
end-to-end production loop because the publish-readiness producer was
not unified, the Asset Supply surface was hidden, the Matrix Script
publish-feedback closure was never reachable, and Digital Anchor was
inspection-only. The Recovery Decision §0 demoted that trial.

PR-1 through PR-4 have now landed the **minimum operator capability**
that the decision required as a precondition for real operator trial.
This document is the explicit go/no-go gate that re-opens trial as
**real operator trial** rather than authority-only trial. It does NOT
author new contracts, new runtime, or new product features. It is the
gate artifact whose purpose is exactly:

1. Tie each recovered capability to a concrete merged PR + execution log;
2. State precisely what operators MAY now do that they could not before;
3. State precisely what remains blocked even after re-entry;
4. Provide a coordinator/architect/reviewer signoff block that, when
   filled, authorizes the operations team to proceed with a real
   trial wave.

## 1. Recovery Wave Acceptance — Evidence Map

Each row maps a Recovery Decision §4 mandatory capability onto the
merged PR that delivered it, the execution log, and the operator-
visible surface(s) that exercise it.

| § | Capability | Status | Merged commit | Execution log | Operator-visible surface |
|---|---|---|---|---|---|
| 4.1 | Asset Supply / B-roll minimum usable operator capability | **PASS** | [`4343bec`](https://github.com/zhaojfifa/apolloveo-auto/commit/4343bec) (PR #116) | [`PR2_ASSET_SUPPLY`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md) | `/assets`, `/api/assets`, `POST /api/assets/promote` |
| 4.2 | Unified `publish_readiness` runtime producer | **PASS** | [`4c317c4`](https://github.com/zhaojfifa/apolloveo-auto/commit/4c317c4) (PR #114) | [`PR1_PUBLISH_READINESS`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md) | Board / Workbench / Delivery — same `publish_readiness` truth across surfaces |
| 4.3 | Matrix Script operator workspace promotion (variation → workbench → delivery → feedback loop) | **PASS** | [`d53da0f`](https://github.com/zhaojfifa/apolloveo-auto/commit/d53da0f) (PR #118) | [`PR3_MATRIX_SCRIPT_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md) | `/api/matrix-script/closures/{task_id}` (GET / POST events / peek), publish-hub `_ms_kind == "matrix_script"` block |
| 4.3 | Digital Anchor operator workspace recovery (formal create-entry + Phase D.1 write-back) | **PASS** | [`0549ee0`](https://github.com/zhaojfifa/apolloveo-auto/commit/0549ee0) (PR #119) | [`PR4_DIGITAL_ANCHOR_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md) (with §9.1 reviewer-fail correction pass) | `/tasks/digital-anchor/new`, `/api/digital-anchor/closures/{task_id}` (GET / POST events / peek), publish-hub `_da_kind == "digital_anchor"` block |
| 4.4 | Trial re-entry preparation | **PASS (this document)** | (PR-5) | [`PR5_EXECUTION_LOG`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md) | n/a — gate document only |

All four predecessor PRs merged before PR-5 was authored. The recovery
wave's required ordering (Global Action §3) is therefore satisfied.

## 2. Real-Trial Re-Entry Go/No-Go Checklist

Each item below is binding. The trial coordinator MUST verify every
row before authorizing the first real-trial sample.

### 2.1 Engineering preconditions (PR-1 .. PR-4 acceptance)

- [x] **G1.** Recovery PR-1 (Unified Publish Readiness Runtime
  Recovery) merged to `main`. Evidence: §1 row 4.2;
  `gateway/app/services/operator_visible_surfaces/publish_readiness.py`
  exists and is the producer; Board / Workbench / Delivery consume it
  via `compute_publish_readiness`. Tests:
  `test_publish_readiness_unified_producer.py` (30/30 PASS),
  `test_final_provenance_emission.py` (5/5),
  `test_publish_readiness_surface_alignment.py` (18/18).
- [x] **G2.** Recovery PR-2 (B-roll / Asset Supply Minimum Usable
  Operator Capability) merged to `main`. Evidence: §1 row 4.1;
  `gateway/app/routers/assets.py` registered; `/assets` page renders
  contract-backed assets; `POST /api/assets/promote` accepts
  contract-shaped intent and rejects `license_metadata.source !=
  task_artifact_promote`. Tests: `test_asset_library_read_only.py`
  (18/18), `test_asset_promote_lifecycle.py` (24/24),
  `test_asset_surface_boundary.py` (8/8),
  `test_asset_surface_submit_end_to_end.py` (5/5).
- [x] **G3.** Recovery PR-3 (Matrix Script Operator Workspace
  Promotion) merged to `main`. Evidence: §1 row 4.3 (Matrix Script);
  `gateway/app/services/matrix_script/closure_binding.py` exposes
  `apply_event_for_task`; `/api/matrix-script/closures/{task_id}/events`
  is the active operator path; publish-hub renders the
  variation_feedback table inside the matrix_script gate. Tests:
  `test_matrix_script_closure_binding.py` (11/11),
  `test_matrix_script_closure_publish_hub_wiring.py` (4/4),
  `test_matrix_script_closure_surface_boundary.py` (6/6),
  `test_matrix_script_closure_api.py` (HTTP end-to-end).
- [x] **G4.** Recovery PR-4 (Digital Anchor Operator Workspace
  Recovery) merged to `main`. Evidence: §1 row 4.3 (Digital Anchor);
  `/tasks/digital-anchor/new` formal route accepts the contract-shaped
  `language_scope` mapping and rejects unknown form/JSON keys at HTTP
  400; `/api/digital-anchor/closures/{task_id}/events` is the active
  D.1 write-back operator path with closed event_kind set
  `{publish_attempted, publish_accepted, publish_rejected,
  publish_retracted, metrics_snapshot, operator_note}` and per-row
  `publish_status` ∈ `{pending, published, failed, retracted}`. Tests:
  `test_digital_anchor_create_entry.py` (16/16),
  `test_digital_anchor_closure_binding.py` (16/16),
  `test_digital_anchor_workspace_wiring.py` (4/4),
  `test_digital_anchor_surface_boundary.py` (9/9),
  `test_digital_anchor_new_task_route_shape.py` (route shape +
  closed-set rejection),
  `test_digital_anchor_closure_api.py` (HTTP end-to-end).

### 2.2 Trial-environment preconditions (coordinator-side)

- [ ] **G5.** Trial environment is on a `main`-tracking deploy whose
  HEAD includes squash commit `0549ee0` or later.
- [ ] **G6.** Coordinator has read this PR-5 gate document, the
  Recovery Decision, and the four predecessor execution logs end-to-end.
- [ ] **G7.** Coordinator has briefed the operations team on §4
  (post-recovery operator-eligible scope) and §5 (post-recovery
  operator-blocked scope) of this document, including the verbatim
  口径 wording in §6.
- [ ] **G8.** Coordinator confirms there is no remaining
  pre-§8.A / pre-§8.F Matrix Script sample being treated as live trial
  evidence (the PR-3 promotion did not retrofit historical samples).
- [ ] **G9.** Coordinator confirms no provider / model / vendor /
  engine / avatar-engine / TTS-provider / lip-sync-engine selector is
  visible on any operator surface (regression-only check; the recovery
  PRs do not add any).

### 2.3 Out-of-scope confirmation (no stealth scope expansion)

- [x] **G10.** No Platform Runtime Assembly work landed under cover of
  PR-5. Evidence: this document; PR-5 file diff.
- [x] **G11.** No Capability Expansion (W2.2 / W2.3 / durable
  persistence / runtime API) landed under cover of PR-5.
- [x] **G12.** No new production line landed.
- [x] **G13.** No Hot Follow business behavior change in PR-5.
- [x] **G14.** No Matrix Script / Digital Anchor packet, schema, or
  closed-truth contract redesign in PR-5.
- [x] **G15.** No provider / model / vendor / engine controls in PR-5.
- [x] **G16.** No generalized digital-human platform expansion in
  PR-5.

### 2.4 Re-entry decision

If G1 .. G4 are checked (engineering preconditions; this document's
state) AND G10 .. G16 are checked (out-of-scope confirmation; this
document's state) AND G5 .. G9 are checked by the trial coordinator
before the first sample, the gate is **GO** for real operator trial.
If any G item is unchecked, the gate is **NO-GO** and the coordinator
MUST not authorize the first sample.

## 3. Post-recovery Stage Definition

The repository's stage transitions from the pre-recovery
**"Operator-Visible Surface Validation Wave (authority-only trial
freeze)"** to the post-recovery **"Real Operator Trial Re-Entry —
Minimum Operator Capability Recovered"**.

This is **not** the start of:
- Platform Runtime Assembly (still BLOCKED — gated on this real trial
  closing successfully and a separate wave-start authority).
- Capability Expansion (still BLOCKED — gated on Platform Runtime
  Assembly signoff).
- New production lines (still BLOCKED — gated on the same).
- Provider / model / vendor consoles (forbidden at every phase).

It IS the start of: real operators submitting real tasks, completing
real workspace flows, exercising real publish-feedback closures, and
producing real trial evidence under a coordinator runbook tied to the
recovered capabilities.

## 4. Post-Recovery Operator-Eligible Scope

What operators MAY now do, by line and surface. Each row supersedes
the corresponding row in Plan A §3 / §3.1 / §3.2 / §3.3.

### 4.1 Hot Follow

End-to-end (intake → publish), unchanged. The unified
`publish_readiness` from PR-1 is the truth; Board / Workbench /
Delivery converge.

### 4.2 Matrix Script

End-to-end **including** the publish-feedback closure loop, no longer
inspect-only on the closure surface. Operators may:

- Submit a task via `/tasks/matrix-script/new` (formal Matrix Script
  entry; closed eleven-field set).
- Inspect the Workbench Phase B variation panel (real authored axes /
  cells / slots, §8.A–§8.H corrections active).
- Open the Delivery Center; the per-row `required` /
  `blocking_publish` zoning + delivery comprehension lanes are real,
  consuming the unified `publish_readiness` from PR-1.
- Lazily create the Phase D.1 closure for the task and write per-
  variation events
  (`operator_publish` / `operator_retract` / `operator_note`)
  through `POST /api/matrix-script/closures/{task_id}/events`.
- See `publish_status_mirror` aggregate per-variation status on the
  Delivery surface.

### 4.3 Digital Anchor

End-to-end **promoted from inspection-only**, with explicit Phase B
authoring deferred. Operators may:

- Submit a task via `/tasks/digital-anchor/new` (formal entry; closed
  eleven-field set; `language_scope` is a structured object;
  bracket-notation form keys or JSON body accepted; unknown keys
  rejected at HTTP 400).
- Inspect the Workbench role/speaker panel (read-only projection of
  packet truth; empty `roles[]` / `segments[]` until Phase B authoring
  lands in a future wave).
- Open the Delivery Center; rows render from the contract-frozen
  Phase C delivery binding.
- Lazily create the Phase D.1 closure for the task and write per-row
  D.1 events
  (`publish_attempted` / `publish_accepted` / `publish_rejected` /
  `publish_retracted` / `metrics_snapshot` / `operator_note`)
  scoped to a role or segment row through
  `POST /api/digital-anchor/closures/{task_id}/events`.
- See `publish_status_mirror` aggregate per-row status on the
  Delivery surface.

### 4.4 Asset Supply

Browse + filter + reference + promote-intent submit.

- `/assets` page renders contract-backed assets with closed-facet
  filters.
- `POST /api/assets/promote` accepts contract-shaped intent (artifact-
  backed source only).
- Operators see promote-closure status transition (`requested` →
  `rejected` / `withdrawn`); approval is intentionally disabled until
  a future wave lands the asset-library write path.

### 4.5 Cross-line Board

`/tasks` Board renders Hot Follow + Matrix Script + Digital Anchor
rows; all three accept new tasks under their formal create-entry
routes.

## 5. Post-Recovery Operator-Blocked Scope

What operators MUST NOT do, even after re-entry.

### 5.1 Out of recovery scope

- **Platform Runtime Assembly entry / phases A–E.** Still BLOCKED. The
  recovery wave was scoped to operator-visible capability, not runtime
  assembly.
- **Capability Expansion (W2.2 / W2.3 / durable persistence / runtime
  API).** Still BLOCKED.
- **Third production line.** Still BLOCKED. The trial covers Hot
  Follow + Matrix Script + Digital Anchor only.
- **Asset platform expansion beyond PR-2.** Asset library
  write/admin/upload paths remain forbidden; PR-2 shipped read +
  promote-intent only. The asset-library write path lands in a
  separate wave; until then, `approve_request()` raises
  `AssetLibraryWriteUnavailable`.

### 5.2 Forbidden at every phase (validator + asset-supply red lines)

- **Vendor / model / provider / engine / avatar-engine / TTS-provider
  / lip-sync-engine selectors / consoles** anywhere on operator-
  visible surfaces (validator R3 + `asset_supply_matrix_v1.md`
  decoupling rules item 7).
- **Donor (SwiftCraft) namespace import** anywhere.
- **State-shape fields** (`status`, `ready`, `done`, `phase`,
  `current_attempt`, `delivery_ready`, `final_ready`, `publishable`)
  outside the scoped Phase D `publish_status` enum (validator R5).
- **Closed kind-set widening** (`framing_kind_set`,
  `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`,
  Matrix Script axis kinds, asset-library closed enums).
- **Workbench writes outside closure paths.** Workbench remains
  read-only except where the closure contracts authorize per-row
  write-back.

### 5.3 Out of scope for this trial wave

- Phase B authoring of Digital Anchor `roles[]` / `segments[]` (the
  Phase B contract is frozen; entry-time authoring is forbidden;
  workbench-time authoring is a separate future wave).
- Operator-driven Matrix Script Phase B authoring (axes / cells /
  slots are deterministic per §8.C; operator-driven authoring is
  forbidden in this wave).
- B-roll / Asset Supply admin review UI, fingerprinting platform,
  full DAM, upload-heavy admin tooling.
- Digital Anchor `platform_callback` / `metrics_snapshot` event
  surfaces beyond the operator-side D.1 write-back UI (the service
  API supports these events; the operator UI exposes only the operator
  events).

## 6. Coordinator 口径 — Verbatim Briefing Lines

These lines supersede the pre-recovery Plan A §5 wording where the
two conflict. Pre-recovery wording that remains accurate (e.g. the
"current vs historical" rule on Workbench) is preserved.

### 6.1 Task Area
> **What you see:** three lines listed — Hot Follow, Matrix Script,
> Digital Anchor. All three accept new tasks; all three have a formal
> create-entry route.
> **What you may do:** submit a task on any of the three lines.
> **What's hidden:** vendor, model, provider, engine, route — these
> are runtime concerns and never appear here.

### 6.2 Workbench
> **What you see:** a read-only projection of the current attempt and
> accepted artifacts. Matrix Script tasks render the Phase B variation
> panel; Digital Anchor tasks render the role/speaker panel.
> **What you may do:** inspect; trigger publish-feedback closure
> events on the variation row (Matrix Script) or per role/segment
> (Digital Anchor).
> **What you may not do:** edit anything outside the closure paths;
> author `roles[]` / `segments[]` or widen any closed kind-set; expect
> the system to fetch external URLs.

### 6.3 Delivery Center
> **What you see:** the deliverables for this task, with required vs
> optional zoning. The publish-readiness gate is unified across Board,
> Workbench, and Delivery — they will agree on the same task state.
> **What you may do:** publish (Hot Follow); for Matrix Script and
> Digital Anchor, exercise the publish-feedback closure events on the
> per-row scope.
> **What you may not do:** rely on a deliverable row labeled
> "unresolved" as truth (it means the artifact lookup has not yet
> resolved); rely on closure-wide `publish_status` (the active truth
> path is per-row D.1 publish_status).

### 6.4 Asset Supply
> **What you see:** read-only Asset Library with closed-facet filters
> and promote-intent action.
> **What you may do:** browse / filter; reference an asset opaquely;
> submit a promote intent against a task artifact; see the closure
> status (`requested` → `rejected` / `withdrawn`).
> **What you may not do:** upload / approve / mark canonical /
> mark reusable / edit metadata.

## 7. Suggested Real-Trial Sample Wave (overrides Plan A §7.1 / §7.2)

The pre-recovery §7.1 sample plan covered Hot Follow + Matrix Script
inspect-first samples. The post-recovery sample wave extends that with
Digital Anchor and Asset Supply samples. Coordinator runs the
following in order; samples are **real** trial evidence (not authority
trial evidence).

1. **Hot Follow golden path** (unchanged from §7.1 sample 1).
2. **Hot Follow preserve-source route** (unchanged from §7.1 sample 2).
3. **Matrix Script — fresh contract-clean small variation plan** with
   `variation_target_count=4`, `target_language=mm`, opaque
   `source_script_ref=content://matrix-script/source/<token>`. Goal:
   exercise the full variation → workbench → delivery → feedback loop
   via at least one `operator_publish` event per cell.
4. **Digital Anchor — formal create-entry submission** via
   `/tasks/digital-anchor/new`. Provide `topic`, opaque
   `source_script_ref`, structured `language_scope`, opaque
   `role_profile_ref`, `role_framing_hint=half_body`, `output_intent`,
   `speaker_segment_count_hint=2`. Goal: confirm the formal entry
   route accepts the contract-shaped body, persists the task, and
   directs the operator to the workbench. Then open
   `POST /api/digital-anchor/closures/{task_id}/events` and write at
   least one `publish_attempted` event on a role row and one
   `publish_accepted` event simulated as a platform callback.
5. **Asset Supply — promote intent** on a Hot Follow artifact created
   in sample 1. Goal: confirm `POST /api/assets/promote` accepts the
   contract-shaped JSON, the closure renders `requested` state, and
   `withdraw_request()` transitions to `rejected` cleanly.
6. **Cross-line `/tasks` Board** inspection with at least one task per
   line in flight. Goal: confirm Board's `publishable` matches
   Workbench's and Delivery's for each task (PR-1 unified producer
   agreement).

## 8. Forbidden in this Trial Wave (re-asserts §5)

- Any task submitted through a temp `/tasks/connect/...` URL (those
  routes are retired for matrix_script and digital_anchor).
- Any vendor / model / provider / engine selector — none should
  exist; if any appears, file a regression and pause the trial.
- Any Phase B authoring action against Digital Anchor or operator-
  driven Matrix Script axis authoring.
- Any approve / mark-canonical / mark-reusable action against the
  asset library (the write path is intentionally absent).
- Any third-line or new-line probe.

## 9. Validation

The validation script at
[`scripts/recovery_pr5_trial_reentry_check.py`](../../scripts/recovery_pr5_trial_reentry_check.py)
re-asserts the documentation invariants this gate depends on:

- All four predecessor PR execution logs exist and carry "MERGED"
  status with the four squash commits named.
- This PR-5 gate document exists.
- The PR-5 execution log exists.
- Plan A's pre-recovery §12 readiness conclusion has been re-anchored
  by a §13 trial re-entry section.
- `CURRENT_ENGINEERING_FOCUS.md` carries the post-recovery stage line.

The same invariants are pinned by
`gateway/app/services/tests/test_recovery_pr5_trial_reentry_gate.py`
so CI catches regression of the gate documentation.

## 10. Signoff

The trial coordinator MUST obtain the three signoffs below before
authorizing the first real-trial sample.

- [ ] **Trial coordinator:** confirms G5 .. G9 (this document §2.2)
  are satisfied in the trial environment.
- [ ] **Architect (codex):** confirms the recovery wave acceptance
  in §1 is intact and PR-5 introduces no stealth scope (G10 .. G16
  green by file diff).
- [ ] **Reviewer / Merge owner:** confirms `main` HEAD includes squash
  commits `4c317c4`, `4343bec`, `d53da0f`, `0549ee0`, and the PR-5
  squash commit (filled at merge time) — and that no later commit has
  silently re-introduced a Recovery Decision §5 forbidden item.

## 11. Stop conditions during real trial

The coordinator MUST pause the trial if any of the following is
observed:

- A vendor / model / provider / engine selector appears on any
  operator surface.
- A `/tasks/connect/{matrix_script,digital_anchor}/...` route resolves
  with a non-404.
- A Matrix Script Phase B variation panel renders empty-fallback
  messages or the bound-method repr — those samples were created
  before §8.A / §8.G and are pre-recovery; not real-trial evidence.
- A Digital Anchor formal-entry POST silently accepts a flat
  `source_language` / `target_language` form key without rejection
  (PR-4 reviewer-fail correction §9.1.1 closed this).
- A Digital Anchor `/api/digital-anchor/closures/{task_id}/publish-closure`
  endpoint is reachable (PR-4 reviewer-fail correction §9.1.3 retired
  it).
- The publish-feedback closure mirrors the legacy D.0 closure-wide
  `publish_status` enum on operator-visible surfaces (PR-4 reviewer-
  fail correction §9.1.3 made D.1 per-row the active truth path).

## 12. References

- Decision: [`ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md)
- Action: [`APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md)
- Predecessor execution logs (all merged):
  - [`PR1_PUBLISH_READINESS`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md)
  - [`PR2_ASSET_SUPPLY`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md)
  - [`PR3_MATRIX_SCRIPT_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md)
  - [`PR4_DIGITAL_ANCHOR_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md) (with §9.1 reviewer-fail correction pass)
- Pre-recovery trial brief (re-anchored by Plan A §13 in this PR):
  [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- Pre-recovery coordinator write-up (live-run section appended in this
  PR): [`PLAN_A_OPS_TRIAL_WRITEUP_v1.md`](PLAN_A_OPS_TRIAL_WRITEUP_v1.md)
- Cross-line contracts pinned by the gate:
  [`publish_readiness_contract_v1.md`](../contracts/publish_readiness_contract_v1.md),
  [`factory_delivery_contract_v1.md`](../contracts/factory_delivery_contract_v1.md),
  [`workbench_panel_dispatch_contract_v1.md`](../contracts/workbench_panel_dispatch_contract_v1.md)
