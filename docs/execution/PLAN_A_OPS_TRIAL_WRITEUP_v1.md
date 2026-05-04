# Plan A · Operations Trial Coordination Write-up v1

Date: 2026-05-02 (initial static pass); 2026-05-03 (Matrix Script Plan A trial corrections §8.A / §8.B / §8.C / §8.D landed — see §11 addendum)
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave")
Status: Plan A trial-coordination & static verification write-up. **Documentation only. No code, no UI, no runtime change.** The static-pass body (§1–§10) reflects the deployed branch as of 2026-05-02. A §11 addendum captures the Matrix Script Plan A trial corrections that landed 2026-05-02 → 2026-05-03 (§8.A / §8.B / §8.C / §8.D); coordinators MUST read both the static-pass body and the §11 addendum before briefing operators on Matrix Script samples.
Authority:
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (frozen operator trial brief; this report exercises §7.1 sample plan and §8 risk list — note: the brief was extended on 2026-05-03 with §0.1 Matrix Script Trial Sample Validity and §11.1 trial-correction history; this write-up's §11 addendum mirrors that extension)
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) (gap review v1)
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) (Matrix Script Plan A trial blocker + realign review; §8.A / §8.B / §8.C / §8.D items now all PASS)
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) (Plan B/C/D contract freeze, gate PASS)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed; PASS)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed; PASS)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed; PASS)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) (§8.D — operator brief correction landed; PASS)
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md)
- Newly frozen contract set landed in PR #79 / commit `54ede3b`; Plan A brief landed in PR #80 / commit `6052014`. Matrix Script trial blocker landed in PR #82 / commit `2ec6198`. §8.A landed in PR #83 / commit `f6125aa`. §8.B confirmed in PR #84 / commit `970b4dc`. §8.C landed at commit `9f25b89`. §8.D landed at this update.

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

## 8. Live-Run Section (live evidence appended / partial closeout state for ops team)

The operations team appends live-run results below as §3 of the brief is executed against the deployed branch. §8 currently carries the partial Matrix Script Sample 3 baseline slice only; the broader sample wave (1, 2, 4, 5a, 5b, 6) is captured in [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) §2.1–§2.6 awaiting §6 coordinator / architect / reviewer signoff before formal append into §8 per that template's §7 handoff rule. Each appended entry records:

```
### 8.x Partial live evidence — Matrix Script Sample 3 contract/projection baseline slice only

- date / window:
  2026-05-03 10:00–10:11

- coordinator:
  Jackie

- operators:
  sunny

- sample covered:
  Sample 3 — Matrix Script fresh contract-clean small variation plan (partial slice only)

- task_id:
  7a407e8d00a9

- entry path used:
  /tasks/newtasks → Matrix Script card → /tasks/matrix-script/new → create and enter workbench

- entry parameters observed:
  target_language: vi
  variation_target_count: 4
  topic: 越南已经有人用AI赚钱了
  source_script_ref: content://matrix-script/source/vn-ai-money-001
  target_platform: tiktok

- evidence observed:
  [x] formal /tasks/matrix-script/new entry path usable on deployed environment
  [x] opaque-ref transitional convention accepted
  [x] target_language enum accepted with vi
  [x] task created successfully and real task_id issued
  [x] Matrix Script line-specific workbench panel mounted
  [x] projection name aligned to matrix_script_workbench_variation_surface_v1
  [x] axes rendered human-readably (tone / audience / length)
  [x] 4 cells rendered (cell_001..cell_004)
  [x] 4 slots rendered (slot_001..slot_004)
  [x] slot detail rendered and cell↔slot binding visible
  [x] no Hot Follow stage cards / pipeline summary / Burmese strip visible on the Matrix Script workbench
  [x] task visible on /tasks board
  [x] board card shows matrix_script task in processing state and board bucket ready
  [x] workbench operator surface shows L3 publish gate blocked · final_missing
  [x] Matrix Script delivery / publish-feedback area remains inspect-only this wave

- per-surface notes:
  Task Area:
    Matrix Script entry surface is reachable from /tasks/newtasks and create-entry succeeds with a formal opaque ref.

  Workbench:
    Matrix Script variation panel is mounted and readable.
    This observation proves contract/projection alignment only; it does not prove operator-workspace completion.

  Delivery Center:
    No final deliverable observed in this sample.
    Publish gate remained blocked · final_missing.
    Delivery/publish-feedback remains inspect-only / placeholder-level for this wave.

- gate-condition deltas:
  Digital Anchor card was still visibly present on /tasks/newtasks during this observation.
  Therefore this observation MUST NOT be treated as full valid Plan A completion evidence unless the coordinator confirms the §12 hide/disable condition and records that decision explicitly.

- regressions / observations:
  Observation only:
  Board-level "ready" wording may be operator-confusing when the Matrix Script workbench still shows blocked · final_missing.

- limitation statement:
  This entry records only a partial live slice for Matrix Script Sample 3.
  It does NOT claim:
  - full Sample 3 completion
  - full Plan A completion
  - §12 condition certification
  - operator-workspace completion
  - delivery-loop completion
  - Plan E unblock

- coordinator initials + timestamp:
  Jackie / 2026-05-03 10:11

This Matrix Script Sample 3 partial baseline slice is the only wave entry currently appended to §8. Samples 1, 2, 4, 5a, 5b, 6 baseline evidence remains in [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) §2.1–§2.6 and is not formally appended here pending §6 capture-template signoff. The wave verdict therefore remains **PARTIAL**, Plan E pre-condition #1 (per §10) remains **not satisfied**, and Plan E remains **BLOCKED**.

## 9. Final Coordinator Judgment (post-static-pass)

- **Trial-safe scope (per brief §3):** confirmed deployable. Hot Follow end-to-end, Matrix Script except Delivery Center binding, Digital Anchor inspect-only.
- **Preview-only scope (per brief §4):** confirmed must-be-hidden. Digital Anchor end-to-end runs, Asset Supply, promote intent — none are reachable as a feature on the deployed branch; hide the surfaces that exist as discovery-only entries.
- **Coordinator pre-conditions (per brief §12):** the five conditions are achievable on the deployed branch with §2.1 / §2.3 / §5 enforcement — no code change required.
- **Operational promise vs gate status:** in alignment. No statement here promises an unimplemented feature as operator-eligible.

## 10. Final Statement

At the current state of Plan A evidence:

- Hot Follow is the operational baseline line for ApolloVeo 2.0.
- Matrix Script has established contract/projection/state baseline evidence in deployed environment and becomes the next line to be pushed toward operator-facing implementation.
- Digital Anchor remains inspect-only and contract-aligned in this wave; no operator submission is authorized.

This means the project is advancing exactly in the intended 2.0 sequence:
line-first, platform-later.
The current record is therefore sufficient to support the next implementation planning step,
but not yet to declare full Plan A completion or to unblock Plan E.
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

End of Plan A trial-coordination write-up (initial static pass, 2026-05-02).

## 11. Matrix Script Plan A Trial Corrections — Addendum (2026-05-03)

This addendum captures the Matrix Script Plan A trial corrections that landed after the initial static pass above. The §1–§10 body is unchanged on its own terms; this addendum is the post-correction overlay coordinators MUST apply when briefing operators on Matrix Script samples.

### 11.1 Why the original Matrix Script trial sample was invalid

Per [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) §1, the prior Matrix Script trial sample was **invalid trial evidence** for two distinct reasons:

1. **Entry-form discipline gap (now closed by §8.A).** The form accepted a free `<textarea>` for `source_script_ref` with no ref-shape validation; an operator could paste raw script body text where the contract requires an opaque ref. The payload-builder then carried that body verbatim into `source_url` and `packet.config.entry.source_script_ref`, violating `task_entry_contract_v1` semantics and the no-body-embedding rule of `slot_pack_contract_v1`.
2. **Empty packet truth (now closed by §8.C).** The payload-builder seeded `packet.line_specific_refs[]` only with **pointers to the contract docs**; no Phase B authoring/planning capability existed to convert `source_script_ref` into populated `axes[] / cells[] / slots[]` deltas. The Phase B render surface had nothing to render.

### 11.2 Trial corrections — landed status

| Item | Status | Authority | Evidence |
| ---- | ------ | --------- | -------- |
| §8.A — Entry-form ref-shape guard | **PASS** (landed `f6125aa`, 2026-05-02) | Blocker review §8.A | `MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md` |
| §8.B — Workbench panel dispatch confirmation | **PASS** (confirmed `970b4dc`, 2026-05-03; no narrow fix required) | Blocker review §8.B | `MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md` |
| §8.C — Phase B deterministic authoring (Option C1) | **PASS** (landed `9f25b89`, 2026-05-03) | Blocker review §8.C | `MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md` |
| §8.D — Operator brief correction | **PASS** (landed this update, 2026-05-03) | Blocker review §8.D | `MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md` |

### 11.3 Static-pass overlay — what changed for Matrix Script

The §3 / §4 / §5 / §6 / §9 rows in this write-up that mention Matrix Script remain factually correct on the deployed-branch surfaces they describe. The following additions overlay them:

- **§3.1 row "Matrix Script `/tasks/matrix-script/new` accepts a closed entry set"** is still PASS, **and** §8.A's `_validate_source_script_ref_shape` guard now additionally rejects body-text input on `source_script_ref` (multi-line, whitespace-bearing, overlong, or unrecognised-scheme values) with `HTTP 400` before the payload-builder runs. Coordinator can verify by attempting a body-text POST in a non-operator environment — expect 400.
- **§3.1 row "Workbench Phase B variation surface renders read-only"** is still PASS as a contract claim, **and** §8.B confirms the dispatch end-to-end on a fresh contract-clean sample (`panel_kind="matrix_script"`, projection `matrix_script_workbench_variation_surface_v1` attached, `data-role="matrix-script-variation-panel"` rendered, empty-fallback messages absent). §8.C populates real authored axes / cells / slots so the panel renders real inspectable truth instead of empty fallback. The "read-only" boundary is unchanged.
- **§3.2 row "Matrix Script Delivery binding artifact lookup is not implemented"** is still PASS — the five `not_implemented_phase_c` placeholder rows remain. §8.A / §8.B / §8.C did not promote, mutate, or expand the Delivery Center boundary; it stays inspect-only this wave.
- **§4 Sample 3 (Matrix Script — small variation plan)** is now refined: the operator-facing brief at §6.2 of [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) and §7.1 sample 3 are the binding operator instructions. The `2 axes × 4 slots` shorthand from this write-up's original §4 has been superseded by §8.C's deterministic authoring (3 canonical axes — `tone` / `audience` / `length` — and `variation_target_count` cells with one slot per cell).
- **§5 Risk watch — operator empty-panel observation:** if a Matrix Script task workbench shows the empty-fallback messages, the operator is looking at a pre-§8.A invalid sample. **Pause that observation as evidence**, brief operator on §6.2 / §0.1 of the trial brief, and create a fresh sample. Do not file a bug — §8.A's PASS gate explicitly does not retrofit existing rows.
- **§5 Risk watch — Matrix Script via legacy connect path:** the formal create-entry alignment wave removed Matrix Script from `_TEMP_CONNECTED_LINES`. If a task is still reachable via `/tasks/connect/matrix_script/new`, file as a regression and use the formal `/tasks/matrix-script/new` POST.

### 11.4 Coordinator action items added by §8.D

- Brief operators on §0.1 of the trial brief (binding sample-validity rule) before any Matrix Script session.
- Confirm samples queued for the trial wave were created via the formal `/tasks/matrix-script/new` POST (under §8.A's guard) and carry populated Phase B deltas (3 canonical axes, `variation_target_count` cells, one slot per cell).
- For any task created before 2026-05-02 (§8.A's land date), assume invalid until proven otherwise — verify `packet.config.entry.source_script_ref` is opaque and `line_specific_refs[*].delta` is populated; if either fails, discard from trial evidence.
- Continue to enforce the §2.1 hide/disable guards, §2.2 explanation 口径, and §2.3 per-line runbook from the original static pass; §8.D does not relax any of those.

### 11.5 Final corrected coordinator judgment

- **Plan A Matrix Script brief corrected:** YES (this addendum + the Plan A brief's §0.1 / §3 / §6 / §7 / §8 / §11.1 / §12 updates).
- **Old invalid Matrix Script sample remains invalid:** YES — §8.A does not retrofit; §0.1 of the trial brief and §11.1 above codify the rule.
- **Fresh corrected Matrix Script retry sample fully briefed:** YES — §6.2 sample profile, §7.1 sample 3, and §0.1 sample-validity criteria together specify exactly what counts as a fresh contract-clean sample.
- **Ready for Matrix Script retry sample creation:** YES — operations team may proceed with §7.1 sample 3 / 4 / 5 once §11.4 action items are completed.
- **Live-trial readiness for Matrix Script:** **CONDITIONAL** (unchanged) — coordinator executes §2.1 / §2.2 / §2.3 of this write-up plus §11.4 of this addendum, then operations team appends live-run results in §8.

End of §8.D operator brief correction addendum (2026-05-03).

## 12. Matrix Script Plan A Trial Follow-up Corrections — Addendum (2026-05-03)

This addendum captures the Matrix Script Plan A follow-up corrections that landed after the §11 §8.D addendum above. The §1–§10 body and §11 addendum are unchanged on their own terms; this §12 addendum is the post-correction overlay coordinators MUST apply when briefing operators on Matrix Script samples after 2026-05-03.

### 12.1 Why §11 alone was insufficient

Per [docs/reviews/matrix_script_followup_blocker_review_v1.md](../reviews/matrix_script_followup_blocker_review_v1.md) §1 / §3, live operator observations on a fresh post-§8.A / §8.B / §8.C / §8.D sample (`task_id=415ea379ebc6`) demonstrated three additional defects that the §11 §8.D addendum did not catch:

1. **§8.E — Workbench shell contamination.** The shared `task_workbench.html` was rendering Hot Follow stage cards / pipeline summary / dub-engine selectors / Burmese deliverable strip on top of the matrix_script panel. The operator-visible page was a Hot Follow workbench *plus* a Matrix Script panel, not a Matrix Script workbench. §8.B's "PASS — no narrow fix required" verdict was correct on its own terms (dispatch is correct) but understated the visible operator surface.
2. **§8.F — Source-ref discipline semantically loose.** The §8.A guard accepted `https://` / `http://` URIs, so an ordinary publisher article URL passed (operator submitted `https://news.qq.com/rain/a/...`). The contract intent ("opaque ref handle") was unenforceable while the accepted set included general web schemes.
3. **§8.G — Phase B panel rendering bug.** The `axes[].values` column rendered as `<built-in method values of dict object at 0x…>` for `tone`, `audience`, and `length`. Root cause: a Jinja attribute-vs-item access bug (`axis.values` resolved to `dict.values` bound method before falling back to the `"values"` key). The §8.C planner output was correct; only the template-level access pattern was wrong.

### 12.2 Trial corrections — landed status (extension of §11.2)

| Item | Status | Authority | Evidence |
| ---- | ------ | --------- | -------- |
| §8.G — Phase B panel render correctness | **PASS** (landed PR #88, 2026-05-03; narrow Jinja item-access fix) | Follow-up review §7 | `MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md` |
| §8.E — Workbench shell suppression | **PASS** (landed PR #89, 2026-05-03; pure shell-suppression execution step) | Follow-up review §5 | `MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md` |
| §8.F — Opaque-ref discipline tightening | **PASS** (landed PR #90, 2026-05-03; Option F1 only — Options F2 / F3 explicitly rejected in this wave) | Follow-up review §6 | `MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md` |
| §8.H — Operator brief re-correction | **PASS** (landed this update, 2026-05-03; documentation-only) | Follow-up review §8 (natural successor) | `MATRIX_SCRIPT_H_OPERATOR_BRIEF_RECORRECTION_EXECUTION_LOG_v1.md` |

### 12.3 Static-pass overlay — what changed for Matrix Script (post-§8.E / §8.F / §8.G / §8.H)

The §3 / §4 / §5 / §6 / §9 rows in this write-up that mention Matrix Script remain factually correct on the deployed-branch surfaces they describe **as they describe them**. The following extensions overlay the §11 addendum:

- **§3.1 row "Workbench Phase B variation surface renders read-only" (extending §11.3):** still PASS, **and** §8.G's narrow Jinja item-access fix replaces the broken `axis.values` attribute access with `axis["values"]` item access; the Axes table now renders human-readable values (`tone: formal · casual · playful`, `audience: b2b · b2c · internal`, `length: min=30 · max=120 · step=15`) instead of the dict bound-method repr. Coordinator can verify by GETting `/tasks/{task_id}` on a fresh contract-clean sample and grepping for `<built-in method values` (must be absent from the rendered HTML). **And** §8.E's whitelist `{% if task.kind == "hot_follow" %}` gates around four contiguous Hot Follow-only template regions in `task_workbench.html` mean the visible workbench HTML for `kind=matrix_script` is now the header card + operator surface strip + line-specific panel slot + the Matrix Script panel block — and nothing else (no Hot Follow stage cards / pipeline summary / dub-engine selectors / Burmese deliverable strip / publish-hub CTA / debug-logs panel). Coordinator can verify by GETting the same workbench and grepping for the closed list of 28 forbidden Hot Follow control tokens (must all be absent in the visible HTML; the inlined global `window.__I18N__` translation payload necessarily contains Hot Follow string keys, so coordinator must strip `<script>` blocks before grepping — see `MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md` §3 / §4).
- **§3.1 row "Matrix Script `/tasks/matrix-script/new` accepts a closed entry set" (extending §11.3):** still PASS with §8.A's body-text rejection, **and** §8.F's tightening replaces the eight-scheme accepted set `{content, task, asset, ref, s3, gs, https, http}` with the four-scheme opaque-by-construction set `{content, task, asset, ref}`. External web schemes (`https` / `http`) and bucket schemes (`s3` / `gs`) are now rejected at HTTP 400 with `"scheme is not recognised"`. The HTML pattern on `matrix_script_new.html` and the helper text mirror the tightened set; the helper text additionally pins the operator transitional convention `content://matrix-script/source/<token>` for the Plan A trial wave. The §8.A contract addendum's heading is renamed to `Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)` and gains four new sub-sections (opaque-by-construction discipline; operator transitional convention; why this is contract-tightening AND a usability adjustment; out of scope for §8.F). Coordinator can verify by attempting a publisher-URL POST in a non-operator environment — expect HTTP 400 with the error branch.
- **§4 Sample 3 (Matrix Script — small variation plan) (extending §11.3):** the operator-facing brief at §6.2 of the trial brief and §7.1 sample 3 are the binding instructions. Fresh sample creation now uses the operator transitional convention `content://matrix-script/source/<token>` (e.g. `content://matrix-script/source/op-token-001`); other `task://` / `asset://` / `ref://` opaque shapes are also accepted. The §11.3 reminder about §8.C's deterministic axes (3 canonical axes, `variation_target_count` cells, one slot per cell) stands; §8.G additionally requires that the Axes table render human-readable values — coordinator-side spot-check via grep for `formal · casual · playful` etc.
- **§5 Risk watch — operator empty-panel observation (existing from §11.3):** unchanged — empty-fallback is a pre-§8.A invalid sample.
- **§5 Risk watch — operator observes the dict bound-method repr in the Axes table:** that page was rendered before §8.G landed. Refresh the page (template-only fix, no task migration needed). On a §8.G-correct render the Axes table shows `formal · casual · playful` / `b2b · b2c · internal` / `min=30 · max=120 · step=15`. If the bound-method repr persists after refresh, file a regression.
- **§5 Risk watch — operator observes Hot Follow stage cards on a Matrix Script workbench:** that page was rendered before §8.E landed. Refresh the page (template-only fix, no task migration needed). On a §8.E-correct render the visible HTML is the header card + operator surface strip + line-specific panel slot + the Matrix Script panel block. If the Hot Follow controls persist after refresh, file a regression.
- **§5 Risk watch — operator submits a publisher article URL or bucket URI as `source_script_ref`:** the §8.F-tightened guard rejects with HTTP 400 / `"scheme is not recognised"`. Coordinator briefs §0.2 (product-meaning of `source_script_ref` — asset identity handle, not body input, not URL ingestion, not currently dereferenced) and §6.2 (operator transitional convention `content://matrix-script/source/<token>`). The rejection is the guard working — not a defect.
- **§5 Risk watch — operator reuses a pre-§8.F Matrix Script sample (any task whose `source_url` is `https://` / `http://` / `s3://` / `gs://`, including the live-trigger sample `task_id=415ea379ebc6`):** discard from trial evidence and create a fresh sample using the operator transitional convention. §8.F does not retrofit existing rows; the live-trigger sample stays invalid.
- **§5 Risk watch — operator confuses `source_script_ref` with a body-input field, publisher-URL ingestion field, or currently dereferenced content address:** brief §0.2 of the trial brief verbatim. `source_script_ref` is a source-script asset identity handle. It is not where script body text goes (§8.A rejects); it is not where article URLs go (§8.F rejects); the product does not currently dereference any handle to body content (Plan B B4 contract-only / Plan E gated). The operator's mapping between `<token>` and source location lives in operator's own working notes — not in this field.

### 12.4 Coordinator action items added by §8.E / §8.F / §8.G / §8.H

In addition to the §11.4 action items (which remain in force):

- Brief operators on §0.2 of the trial brief (product-meaning of `source_script_ref`) verbatim before any Matrix Script sample-creation session — the four-bullet structure (what it IS / what it IS NOT × 3) is load-bearing.
- Confirm samples queued for the trial wave use the operator transitional convention `content://matrix-script/source/<token>` (or another `task://` / `asset://` / `ref://` opaque shape); flag any task whose `source_url` is an `https://` / `http://` / `s3://` / `gs://` URI as a pre-§8.F invalid sample.
- For any Matrix Script task workbench observation that includes Hot Follow stage cards, pipeline summary, dub-engine selectors, Burmese deliverable strip, publish-hub CTA, or debug-logs panel: refresh the page; if it persists, file a regression against §8.E's shell-suppression gates.
- For any Matrix Script Axes table observation that shows the `<built-in method values of dict object at 0x…>` repr: refresh the page; if it persists, file a regression against §8.G's Jinja item-access fix.
- Continue to enforce the §2.1 hide/disable guards, §2.2 explanation 口径, §2.3 per-line runbook, and §11.4 action items from the prior addenda; §8.E / §8.F / §8.G / §8.H do not relax any of those.

### 12.5 Final corrected coordinator judgment (post-§8.H)

- **Plan A Matrix Script brief re-corrected:** YES (this §12 addendum + the trial brief's §0.1 / §0.2 / §3 / §5 / §6 / §7 / §8 / §11.1 / §12 updates).
- **Old invalid Matrix Script samples remain invalid:** YES — pre-§8.A samples (pasted-body) AND pre-§8.F samples (`https://` / `http://` / `s3://` / `gs://`, including the live-trigger sample `task_id=415ea379ebc6`) are both invalid evidence; §0.1, §7.2, and §12.3 above codify the rule.
- **Fresh corrected Matrix Script retry sample fully briefed:** YES — §6.2 sample profile (with the operator transitional convention `content://matrix-script/source/<token>`), §7.1 sample 3 (with the §8.E / §8.F / §8.G acceptance criteria), §0.1 sample-validity (seven new criteria), and §0.2 product-meaning together specify exactly what counts as a fresh contract-clean sample.
- **Ready for Matrix Script retry sample creation:** YES — operations team may proceed with §7.1 sample 3 / 4 / 5 once §11.4 + §12.4 action items are completed.
- **Live-trial readiness for Matrix Script:** **CONDITIONAL** — coordinator executes §2.1 / §2.2 / §2.3 of this write-up plus §11.4 of the prior addendum and §12.4 of this addendum; operations team appends live-run results in §8 of the write-up (the §8 placeholder remains empty in this static pass).

End of §8.E / §8.F / §8.G / §8.H operator brief follow-up correction addendum (2026-05-03).

Coordinator note:
This observation is retained as deployed-environment baseline evidence for Matrix Script Sample 3 only.
It is valid as contract/projection baseline evidence, but not yet sufficient as full Plan A wave-completion evidence.

---

## 13. Real Operator Trial Re-Entry — NOT READY (Recovery Wave PR-5, 2026-05-04)

This section closes the **static-only / authority-only era** of this
write-up. It does **NOT** open the real operator trial era. The
PR-5 gate verdict is **NOT READY**: contract-backed minimum operator
capability is restored (PR-1..PR-4 merged) but operator workflow
convergence to the line-specific product-flow authority documents
is missing. Real operator trial therefore remains BLOCKED until the
**Operator Workflow Convergence Wave** closes.

### 13.1 What changed under recovery

The Operator Capability Recovery wave (decision authority:
[`docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md))
demoted the pre-recovery Plan A from "current main action" to
"validation action after PR-1 .. PR-4 restore minimum operator
capability". Recovery PR-1 / PR-2 / PR-3 / PR-4 have all merged to
`main` 2026-05-04:

- PR-1 ([#114](https://github.com/zhaojfifa/apolloveo-auto/pull/114),
  squash `4c317c4`) — Unified Publish Readiness Runtime Recovery.
- PR-2 ([#116](https://github.com/zhaojfifa/apolloveo-auto/pull/116),
  squash `4343bec`) — B-roll / Asset Supply minimum operator capability.
- PR-3 ([#118](https://github.com/zhaojfifa/apolloveo-auto/pull/118),
  squash `d53da0f`) — Matrix Script Operator Workspace Promotion.
- PR-4 ([#119](https://github.com/zhaojfifa/apolloveo-auto/pull/119),
  squash `0549ee0`) — Digital Anchor Operator Workspace Recovery.

### 13.2 Authority pointer (binding)

The binding gate document for real operator trial re-entry is
[`APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md).
It supersedes:

- §2.1 / §2.2 / §2.3 of this write-up (pre-recovery coordinator
  runbook).
- §11.4 / §12.4 of this write-up (pre-recovery action items).
- §12 of [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
  (pre-recovery readiness conclusion); the trial brief now carries
  §13 with the post-recovery readiness conclusion.

### 13.3 §8 live-run placeholder — closed for the static-only era

The §8 live-run placeholder in this write-up's body was authored when
Plan A was authority-only. With recovery PR-1 .. PR-4 merged and the
PR-5 NOT-READY gate authored, real-trial live-run results are not yet
captured anywhere — because real-trial is BLOCKED until the Operator
Workflow Convergence Wave closes. When the Convergence Wave closes
and a separate "Trial Re-Entry Gate v2" PR re-opens the real-trial
decision, real-trial live-run results will be captured in:

- The signoff block of the future "Trial Re-Entry Gate v2" document
  (coordinator, architect, reviewer).
- Per-sample live-run logs filed under `docs/execution/` by the
  operations team after each real-trial sample. Naming convention:
  `OPERATOR_TRIAL_SAMPLE_<n>_<line>_<yyyymmdd>_v1.md` — re-numbered
  from a v2 trial gate, not from PR-5.

### 13.4 Coordinator instruction during the Convergence Wave

Coordinators MUST NOT authorize a real-trial sample on Matrix Script
or Digital Anchor surfaces during the Convergence Wave. Two
allowances apply (verbatim from PR-5 gate §8):

1. **Hot Follow golden-path samples** remain valid as factory-baseline
   evidence per the pre-recovery Plan A §7.1 wave 1 / wave 2.
2. **Static surface inspection** by the trial coordinator MAY produce
   convergence-gap notes used as input to the Convergence Wave.

When the Convergence Wave closes and a "Trial Re-Entry Gate v2"
document is authored, that document — not PR-5 — is the authoritative
record of real-trial readiness.

### 13.5 Operator Workflow Convergence Wave

The next mandatory wave is the **Operator Workflow Convergence Wave**.
Its scope is the W7..W12 preconditions in the PR-5 gate document §2.3,
ordered Matrix Script first (Phase OWC-MS) then Digital Anchor
second (Phase OWC-DA). The two product-flow authority documents
elevated by PR-5 are:

- [`docs/product/matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
- [`docs/product/digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md)

Future Task Area / Workbench / Delivery Center implementations on
those two lines MUST map to the product-flow modules, not only to
the packet / contract / runtime truth.

End of §13 — Real Operator Trial Re-Entry section.