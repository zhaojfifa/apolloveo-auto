# Plan A · Operations Trial Coordination Write-up v1

Date: 2026-05-02
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave")
Status: Plan A trial-coordination & static verification write-up. **Documentation only. No code, no UI, no runtime change.**
Authority:
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (frozen operator trial brief; this report exercises §7.1 sample plan and §8 risk list)
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) (gap review v1)
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) (Plan B/C/D contract freeze, gate PASS)
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md)
- Newly frozen contract set landed in PR #79 / commit `54ede3b`; Plan A brief landed in PR #80 / commit `6052014`.

## 0. Scope Disclaimer (binding)

This is a **coordinator-side trial-coordination write-up**: it documents the trial brief, the runbook the coordinator must follow with operators, and a **static verification pass** confirming that the system surfaces visible to operators today match the contract truth that the trial brief promises. It is **not** a record of live operator runs — those happen in the operations environment, with real operators, against the deployed branch. Live-run results (dated logs, sample task ids, captured surfaces) MUST be appended to this document as §10 once the operations team executes §3 of the trial brief.

This report does not implement anything, does not patch UI, does not change runtime behavior. Per the brief §10 validation rule: every statement here traces to a frozen contract, to existing engineering progress, or to a static surface inspection. No operational promise exceeds the current gate status.

## 1. Inputs Read

- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) — the frozen brief.
- All twelve Plan B / C / D contracts and the three amended files (per the freeze log).
- Read-only code surface checks against the deployed branch (no edits):
  - `gateway/app/routers/tasks.py` — entry routes; `_TEMP_CONNECTED_LINES`.
  - `gateway/app/services/matrix_script/create_entry.py` — closed entry + `ALLOWED_TARGET_LANGUAGES = ("mm", "vi")`.
  - `gateway/app/services/matrix_script/delivery_binding.py:93-125` — five `not_implemented_phase_c` placeholders.
  - `gateway/app/services/operator_visible_surfaces/projections.py` — `FORBIDDEN_OPERATOR_KEYS`, `PANEL_REF_DISPATCH`, `derive_board_publishable`, `derive_delivery_publish_gate`.
  - `gateway/app/templates/tasks_newtasks.html` — Digital Anchor card target (`/tasks/connect/digital_anchor/new`); Matrix Script card target (`/tasks/matrix-script/new`).

## 2. Coordinator Runbook (operator-facing)

Trial coordinator MUST execute the following in order before any operator session begins. Each step is a contract-aligned guard from the brief §8 (risks) and §12 (conditions).

### 2.1 Pre-trial guards (must hold before any operator submits anything)

1. **Hide Digital Anchor entry surfaces.** New-Tasks card click target for Digital Anchor and the temp route `/tasks/connect/digital_anchor/new` MUST be hidden or disabled in the trial environment (per brief §6.3 + §8 row 1). If the trial environment cannot hide them, post a top-of-page operator notice that Digital Anchor is preview-only; do not rely on operator memory to enforce this.
2. **Hide Asset Supply / B-roll page.** Per brief §4.1 + §8 row 5. The page is contract-frozen, not implemented; any operator interaction is unsafe.
3. **Brief the §5 explanation 口径.** Coordinator reads the Task Area / Workbench / Delivery Center explanations verbatim to operators, including the "current vs historical" rule and the "scene-pack never blocks publish" rule.
4. **Restrict trial sample set to brief §7.1.** Brief §7.2 samples are explicitly excluded; coordinator stops the trial if any §7.2 pattern is observed.
5. **Confirm coordinator has the abort criteria.** If any §8 risk activates (operator submits Digital Anchor; vendor selector appears; third-line URL resolves; Matrix Script Delivery row treated as confirmed), pause trial and file a regression note before continuing.

### 2.2 Operator-facing scope (paraphrased one-liner per surface)

- **Task Area:** "Three lines listed; Hot Follow and Matrix Script accept new tasks; Digital Anchor card is preview only."
- **Workbench:** "Read-only projection of current attempt and accepted artifacts; historical artifacts are timestamped — they are not current truth."
- **Delivery Center:** "Lists final / required / optional deliverables. Optional items (e.g., scene pack) never block publish. For Matrix Script, Delivery Center is inspect-only this wave; use Workbench publish-feedback closure."

### 2.3 Per-line runbook

| Line           | Allowed actions                                                                                          | Forbidden actions                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Hot Follow     | Submit short-clip golden-path; submit preserve-source variant; publish.                                  | Rapid resubmit / race tests against current-vs-historical (D2 not yet in code).                                |
| Matrix Script  | Submit via `/tasks/matrix-script/new` (target `mm` or `vi` only); inspect Workbench Phase B variation surface; exercise publish-feedback closure per variation row. | Treating Matrix Script Delivery Center row as confirmed delivery; submitting target language outside `{mm, vi}`. |
| Digital Anchor | **Inspect-only.** Open New-Tasks landing; confirm card is labeled preview.                                | Any submission via any route (formal `/tasks/digital-anchor/new` is contract-frozen, not implemented; temp `/tasks/connect/digital_anchor/new` is discovery-only). |

## 3. Static Verification Pass (coordinator-side, against deployed branch)

This pass confirms the system, as deployed, supports the brief's promises and forbidden-list constraints. Each row corresponds to a brief promise; the evidence column points at a current-branch file/line.

### 3.1 Trial-eligibility evidence

| Brief promise                                                                  | Static evidence on deployed branch                                                                                                | Result |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Hot Follow end-to-end is unchanged.                                            | No commits to `gateway/app/services/hot_follow_*`, `tasks.py` Hot Follow paths, or `hot_follow_api.py` business logic since `ca20c60` (per gap review §4 + §7.1). | PASS   |
| Matrix Script `/tasks/matrix-script/new` accepts a closed entry set.           | `gateway/app/services/matrix_script/create_entry.py:22-37` enumerates `MATRIX_SCRIPT_REQUIRED_FIELDS` + `_OPTIONAL_FIELDS`; unknown fields rejected via `_require()`. | PASS   |
| Matrix Script target language restricted to `{mm, vi}`.                        | `create_entry.py:39` `ALLOWED_TARGET_LANGUAGES = ("mm", "vi")`; enforced at line 97.                                              | PASS   |
| Workbench Phase B variation surface renders read-only.                          | `gateway/app/services/matrix_script/workbench_variation_surface.py` is projection-only (no packet mutation); merge note `matrix_script_operator_visible_slice_merge_note_v1.md` fences scope. | PASS   |
| Forbidden vendor/model/provider/engine keys are stripped at the operator boundary. | `gateway/app/services/operator_visible_surfaces/projections.py:24-33` `FORBIDDEN_OPERATOR_KEYS` enforced by `sanitize_operator_payload` at line 36. | PASS   |
| Workbench panel dispatch is closed-by-default.                                 | `projections.py:239-246` `PANEL_REF_DISPATCH` exactly matches the closed map in [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md); `projections.py:268-270` rejects unknown ref_ids. | PASS   |

### 3.2 Forbidden / preview-only evidence

| Brief constraint                                                                  | Static evidence on deployed branch                                                                                                | Result |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Digital Anchor Phase D.1 write-back is not implemented.                            | `gateway/app/services/digital_anchor/publish_feedback_closure.py` exists (Phase D.0 closure shape) with no write-back code path.   | PASS — must be hidden from trial |
| Digital Anchor formal `/tasks/digital-anchor/new` route is not implemented.        | `gateway/app/routers/tasks.py` has no `/tasks/digital-anchor/new` handler; only the generic temp route `/tasks/connect/digital_anchor/new` is reachable via `_TEMP_CONNECTED_LINES["digital_anchor"]` at `tasks.py:541-546`. | PASS — must be hidden from trial |
| Matrix Script Delivery binding artifact lookup is not implemented.                 | `gateway/app/services/matrix_script/delivery_binding.py:93,101,109,117,125` emits `"artifact_lookup": "not_implemented_phase_c"` on all five rows. | PASS — operator must treat as inspect-only |
| Asset Supply / B-roll page is not implemented.                                    | No `gateway/app/services/asset_library/` module; no asset-library route under `tasks.py`. Page is contract-frozen only.            | PASS — must be hidden from trial |
| Promote intent submission is not implemented.                                      | No promote service module on the deployed branch.                                                                                  | PASS — must be hidden from trial |
| Unified `publish_readiness_contract_v1` producer is not yet in code.               | `projections.py:51-79` `derive_board_publishable` and `:95-131` `derive_delivery_publish_gate` remain independent re-derivations (gap review §10.6). | PASS — surfaces still drift acceptably during trial; brief §5 explanation accounts for this |
| L3 `final_provenance` is not yet emitted.                                          | `gateway/app/services/contract_runtime/` and `gateway/app/services/status_policy/hot_follow_state.py` have no `final_provenance` field; today UI infers from `final_fresh` + timestamps. | PASS — brief §5.2 trial-coordinator note accounts for this |
| L4 advisory producer is not yet emitting.                                          | No `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` module exists; advisory taxonomy is contract-only.         | PASS — brief §6.1 accounts for empty advisory rows during trial |

### 3.3 Coordinator-side hide/disable items (gating before trial begins)

The following are deployed-branch surfaces the trial coordinator MUST hide or disable before the trial sample wave (brief §12 conditions 2 and 3):

- The Digital Anchor New-Tasks card click target at `gateway/app/templates/tasks_newtasks.html:47` (the `<a href="/tasks/connect/digital_anchor/new...">` element).
- Any operator-facing navigation entry to an Asset Supply / B-roll page (none currently authored on this branch — verified by the absence of an asset-library template/route).

## 4. Sample-Plan Dry Run (against contract truth + deployed code)

For each §7.1 sample, the coordinator dry-runs the trial pre-conditions, the runtime path operator will exercise, and the success/abort criteria.

### Sample 1 — Hot Follow short-clip golden path

- **Path:** `/tasks/newtasks` → Hot Follow card → existing Hot Follow create surface → Workbench → Delivery Center → publish.
- **Pre-conditions:** Hot Follow business behavior unchanged (verified §3.1 row 1).
- **Success criteria:** task reaches `final_ready=true`; Delivery Center `publish_gate=true` per `derive_delivery_publish_gate`; publish completes; Workbench shows current-attempt + accepted artifact rows.
- **Abort criteria:** advisory produces unknown code outside the frozen taxonomy (would indicate a producer landed prematurely); Workbench shows a vendor/model selector (validator R3 regression); Board re-derivation diverges from Workbench re-derivation (drift before D1 unifies).
- **Coordinator note:** advisory rows will likely be empty (D4 not in code); operators MUST be briefed not to interpret an empty advisory row as "all clear" beyond what `ready_gate` says.

### Sample 2 — Hot Follow preserve-source route

- **Path:** same as Sample 1, with preserve-source compose.
- **Pre-conditions:** preserve-source legality unchanged per `hot_follow_current_attempt_contract_v1.md` §"Allowed Compose States".
- **Success criteria:** `dub_not_required_for_route` flow visible; scene-pack absence does NOT show as a publish blocker on Delivery Center (validates the Plan C `scene_pack_blocking_allowed: false` rule from the operator perspective).
- **Abort criteria:** scene-pack appears in `ready_gate.blocking[]` (would violate the explicit Plan C amendment); Delivery rejects publish for an optional-only reason.

### Sample 3 — Matrix Script small variation plan

- **Path:** `/tasks/newtasks` → Matrix Script card (`tasks_newtasks.html:107`) → `/tasks/matrix-script/new` → submit (2 axes × 4 slots, `target_language=mm`) → `/tasks/{task_id}` Workbench → exercise publish-feedback closure per variation row.
- **Pre-conditions:** create-entry rejects unknown fields (verified §3.1 row 2); target-language enforced (verified row 3).
- **Success criteria:** payload created via `build_matrix_script_task_payload`; packet seeded with `line_specific_refs[matrix_script_variation_matrix]` + `[matrix_script_slot_pack]`; Workbench panel mounts via `PANEL_REF_DISPATCH`; closure rows accept publish-feedback events per the existing Phase D closure module.
- **Abort criteria:** Delivery Center rows shown as resolved (would indicate `not_implemented_phase_c` regressed prematurely); a vendor/model field appears; the panel mount fails (would indicate `PANEL_REF_DISPATCH` drifted from the contract).
- **Coordinator note:** explicitly do NOT treat Matrix Script Delivery Center as the success surface; the artifact-lookup contract (Plan B B4) is the resolution path and lands at Plan E.

### Sample 4 — Matrix Script multi-language target

- **Path:** same as Sample 3 with `target_language=vi`.
- **Pre-conditions:** `vi` is in `ALLOWED_TARGET_LANGUAGES`.
- **Success criteria:** as Sample 3.
- **Abort criteria:** any third language accepted (would indicate the closed enum drifted).

### Sample 5 — Cross-line `/tasks` Board inspection

- **Path:** `/tasks` Board with at least one task per eligible line in flight.
- **Pre-conditions:** Hot Follow + Matrix Script tasks active; no Digital Anchor task submitted.
- **Success criteria:** three lines render side-by-side; Digital Anchor row contains no operator-actionable submit affordance; sanitization at `projections.py:36` strips any leaked vendor key.
- **Abort criteria:** Digital Anchor row exposes a submit; a vendor key reaches an operator-visible payload (sanitization regression).

## 5. Risk Watch (live monitoring during trial)

Coordinator monitors for the brief §8 risk list during operator sessions. The watch surface is grouped by trigger:

| Trigger                                                                              | Action                                                                                       |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Operator clicks Digital Anchor card and reaches a create form (any).                 | **Pause trial.** File regression note. The hide/disable guard from §2.1 step 1 failed.       |
| `not_implemented_phase_c` rendered on Matrix Script Delivery row appears as a system error to operator. | Coordinator restates brief §6.2 explanation; this is by-design until Plan E.                 |
| Optional row (scene-pack, archive, pack_zip) presented as a publish blocker.         | **Pause trial.** Validate against Plan C `scene_pack_blocking_allowed: false`; file regression. |
| Vendor / model / provider / engine selector appears anywhere.                        | **Pause trial immediately.** R3 regression; do not resume until root cause identified.       |
| Asset Supply / B-roll page reached by URL.                                           | Hide via deployed-environment guard or coordinator-enforced URL block; warn operator off.    |
| Advisory row shows an unknown code outside the Hot Follow taxonomy.                  | **Pause trial.** Producer drift; D4 contract pins the closed taxonomy.                       |
| Workbench panel mount fails for a known ref_id.                                      | **Pause trial.** Verify `PANEL_REF_DISPATCH` matches the contract object (D3).               |
| Board / Workbench / Delivery disagree on `publishable` for the same task.            | Note the divergence; expected variability until D1 lands. Do not abort unless divergence is operator-confusing. |

## 6. Surfaces Confirmed Drift-Free vs Drift-Tolerated

### 6.1 Drift-free (must remain stable through trial)

- Hot Follow runtime boundary (no commits since `ca20c60`).
- Matrix Script Phase A entry contract; Phase B workbench projection; Phase C delivery binding (read-only); Phase D.1 publish-feedback closure shape.
- Validator R3 forbidden-key sanitization at the operator boundary.
- Closed `ALLOWED_TARGET_LANGUAGES` enum.
- `PANEL_REF_DISPATCH` map.
- `scene_pack` non-blocking discipline (now explicit per Plan C).

### 6.2 Drift-tolerated during trial (acknowledged in brief; resolved at Plan E)

- Three independent re-derivations of `publishable` (Board / Workbench / Delivery). Brief §5 explanation accounts for the variability.
- Inferred current-vs-historical distinction (until D2 lands `final_provenance` in code). Brief §5.2 coordinator note caps the test surface to non-racey samples.
- Empty advisory strip (until D4 emitter lands). Brief §6.1 calls it out.
- `not_implemented_phase_c` placeholder rendered on Matrix Script Delivery rows. Brief §6.2 explicitly explains the placeholder.
- Generic temp `/tasks/connect/digital_anchor/new` reachable via `_TEMP_CONNECTED_LINES`. Coordinator MUST hide via §2.1 step 1.

## 7. Findings (static pass; pre-live)

1. The deployed branch matches every Plan A trial-safe promise. No surface promises end-to-end on a feature whose contract is frozen but whose code is gated.
2. The deployed branch matches every Plan A forbidden / preview-only constraint via the absence of the corresponding implementation modules. The brief's "must be hidden" items are real surfaces that the coordinator MUST hide.
3. The Plan C amendment to `factory_delivery_contract_v1.md` (`scene_pack_blocking_allowed: false`) is contract truth on this branch but not yet enforced by a runtime validator (Plan E gate). During trial, coordinator MUST manually verify Sample 2's success criterion.
4. The Plan D D3 `PANEL_REF_DISPATCH` map matches the contract verbatim — closed-by-default rule observed at `projections.py:268-270`.
5. The R3 forbidden-key sanitization is in place at `projections.py:36` and is the load-bearing guard for the operator boundary; coordinator should not relax it.

## 8. Live-Run Section (placeholder for ops team)

The operations team appends live-run results below once §3 of the brief is executed. Each entry should record:

```
- date / window:
- coordinator:
- operators:
- samples run (with task ids):
- abort triggers fired (none / list):
- regressions filed (none / list):
- per-surface notes (Task Area / Workbench / Delivery Center):
- gate-condition deltas:
```

This section is intentionally empty in this static pass.

## 9. Final Coordinator Judgment (post-static-pass)

- **Trial-safe scope (per brief §3):** confirmed deployable. Hot Follow end-to-end, Matrix Script except Delivery Center binding, Digital Anchor inspect-only.
- **Preview-only scope (per brief §4):** confirmed must-be-hidden. Digital Anchor end-to-end runs, Asset Supply, promote intent — none are reachable as a feature on the deployed branch; hide the surfaces that exist as discovery-only entries.
- **Coordinator pre-conditions (per brief §12):** the five conditions are achievable on the deployed branch with §2.1 / §2.3 / §5 enforcement — no code change required.
- **Operational promise vs gate status:** in alignment. No statement here promises an unimplemented feature as operator-eligible.

## 10. Final Statement

- **Plan A document created:** done (this report; brief at [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)).
- **Authority read:** brief, gap review, Plan B/C/D execution log, frozen contracts, deployed-branch surfaces.
- **Trial-safe scope confirmed:** Hot Follow end-to-end; Matrix Script except Delivery binding; Digital Anchor inspect-only.
- **Preview-only scope confirmed:** Digital Anchor end-to-end runs; Asset Supply; promote intent; vendor/model/provider/engine controls; third-line entry.
- **Final readiness judgment:**
  - **Static verification pass:** PASS.
  - **Live-trial readiness:** **CONDITIONAL** — gated on coordinator executing §2.1 hide/disable guards, §2.2 explanation 口径, and §2.3 per-line runbook before any operator session. Live-run results appended in §8.
  - **Plan E pre-condition #1 (Plan A executed + write-up filed):** PARTIAL — write-up filed (this document); live-trial execution by operations team remains. Plan E gate cannot open until §8 carries at least one full sample-wave entry.
- **Runtime Assembly:** **BLOCKED**
- **Capability Expansion:** **BLOCKED**
- **Frontend patching:** **BLOCKED**

End of Plan A trial-coordination write-up.
