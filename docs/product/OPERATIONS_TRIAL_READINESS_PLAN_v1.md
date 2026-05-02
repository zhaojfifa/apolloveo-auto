# Operations Trial Readiness Plan v1 (Plan A)

Date: 2026-05-02
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave")
Status: Plan A — operator-facing trial scope freeze. **Documentation only. No code, no UI, no runtime change.**
Authority:
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) (gap review v1; §11 Plan A is the source of this document's structure)
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) (active wave authority)
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) (Plan B / C / D contract freeze; final gate PASS)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)
- Newly frozen contracts:
  - Plan B: `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md`, `docs/contracts/digital_anchor/new_task_route_contract_v1.md`, `docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md`, `docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md`
  - Plan C: `docs/contracts/asset_library_object_contract_v1.md`, `docs/contracts/promote_request_contract_v1.md`, `docs/contracts/promote_feedback_closure_contract_v1.md`, plus amendments to `docs/contracts/factory_delivery_contract_v1.md` (`required` / `blocking_publish` / `scene_pack_blocking_allowed: false`) and `docs/contracts/hot_follow_projection_rules_v1.md` (explicit scene-pack non-blocking)
  - Plan D: `docs/contracts/publish_readiness_contract_v1.md`, `docs/contracts/workbench_panel_dispatch_contract_v1.md`, `docs/contracts/l4_advisory_producer_output_contract_v1.md`, plus amendment to `docs/contracts/hot_follow_current_attempt_contract_v1.md` (`final_provenance` L3 field)

## 1. Reading Declaration

This document was authored after Plan B / C / D contract freeze landed (per the execution log §8 final gate). Every statement below is backed either by an existing on-spec engineering progress row in the gap review §4, by the wave authority, or by a frozen contract. Where a contract is frozen but its implementation is gated to Plan E, the trial-eligibility statement is explicit about the difference.

There is no top-level `CLAUDE.md` in this repository. The reading order followed mirrors the Plan B/C/D log: engineering rules → current engineering focus → wave authority → gap review → frozen contracts.

## 2. Current Phase Restatement

Phase = **Operator-Visible Surface Validation Wave**. The phase is **not**:

- Platform Runtime Assembly (BLOCKED — admission requires this wave green and Plan A executed).
- Capability Expansion Gate W2.2 / W2.3 (BLOCKED).
- New-line / third-line runtime loading (BLOCKED).

Plans B / C / D contract freeze is complete. Plan A is this document. Plan E (next operator-visible implementation gate) waits on Plan A trial execution and write-up.

## 3. Operator-Safe Trial Scope (what operators MAY use now)

### 3.1 Trial-eligible lines

| Line            | Trial scope                                                                                                                                                                | Truth backing                                                                                                                                              |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hot Follow** | End-to-end (intake → publish), as today.                                                                                                                                    | Frozen runtime boundary reference (gap review §7.1; `factory_runtime_boundary_design_v1.md:4`); no commits since `ca20c60` (2026-02-17).                  |
| **Matrix Script** | End-to-end **except Delivery Center binding**: submit, inspect Workbench Phase B variation surface, exercise publish-feedback closure.                                  | Phases A–D contracts frozen; create-entry shipped (`4896f7c`); workbench panel render shipped (`b370e46`, #77).                                            |
| **Digital Anchor** | **Inspection-only.** Operators may open the New-Tasks card to confirm the line exists; they MUST NOT submit a task.                                                    | Phase D.1 write-back not implemented; formal `/tasks/digital-anchor/new` route not implemented (gap review §7.3). Plan B contracts now exist; code does not. |

### 3.2 Trial-eligible surfaces

| Surface                                                            | Eligibility           | Authority                                                                                                                                |
| ------------------------------------------------------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `/tasks` Board (Hot Follow + Matrix Script rows)                   | Production-eligible   | `derive_board_publishable` over `ready_gate`; tested. (Note: surface still re-derives publishable until Plan D `publish_readiness_contract_v1` lands in code at Plan E.) |
| `/tasks/matrix-script/new` create-entry form                       | Production-eligible   | Closed packet payload builder per `task_entry_contract_v1`; alignment doc `matrix_script_formal_create_entry_alignment_v1.md`.            |
| Workbench panel — Hot Follow                                       | Production-eligible   | L3 `current_attempt` consumed via packet refs (per `hot_follow_current_attempt_contract_v1.md`).                                          |
| Workbench panel — Matrix Script (Phase B variation surface, read-only) | Production-eligible (read-only) | Read-only projection of `line_specific_refs[matrix_script_variation_matrix/slot_pack].delta`; merge note `matrix_script_operator_visible_slice_merge_note_v1.md`. |
| Delivery Center — Hot Follow                                       | Production-eligible   | Existing read-only projection over `ready_gate` + L2 facts.                                                                              |
| Delivery Center — Matrix Script                                    | **Inspect-only**      | `result_packet_binding.artifact_lookup` still emits `not_implemented_phase_c` placeholders at `gateway/app/services/matrix_script/delivery_binding.py:93-125`. The Plan B B4 contract pins the resolution shape; the code change waits on Plan E. |
| Cross-line `/tasks` Board inspection                               | Production-eligible   | Three lines listed; only Hot Follow + Matrix Script rows accept new tasks.                                                               |

### 3.3 Surfaces operators may inspect but not operate

- Digital Anchor New-Tasks card — visible, label-only; submit MUST be hidden or disabled.
- Digital Anchor Workbench panel placeholder — not rendered for trial; if the placeholder branch is reachable, label as "preview" (gap review §6 discovery-only classification).
- Matrix Script Delivery Center rows — visible with `not_implemented_phase_c` placeholder rendered as "unresolved"; operators may inspect but MUST NOT treat as truth for ops 跑量.

## 4. Forbidden / Preview-Only Scope (what operators MUST NOT use)

### 4.1 Hidden or "preview" labeled

- **Digital Anchor end-to-end runs.** Phase D.1 write-back is contract-frozen (Plan B B3) but not implemented. Create-entry payload builder is contract-frozen (Plan B B1) but not implemented. The formal `/tasks/digital-anchor/new` route is contract-frozen (Plan B B2) but not implemented; the generic temp `/tasks/connect/digital_anchor/new` is discovery-only and MUST NOT be used.
- **Asset Supply / B-roll page.** Contracts now exist (Plan C C1/C2/C3) but no asset-library service, no promote intent service, no closure service exists. Page is contract-frozen, not operational.
- **Promote intent submission.** Contract-frozen (C2) but not implemented. Hide the submit affordance during trial.
- **Any vendor / model / provider / engine selector.** Forbidden by `asset_supply_matrix_v1.md` §"Decoupling rules" item 7 and validator R3 — at all phases, on all surfaces.
- **Any "third line" entry.** Out of scope for this wave.
- **Workbench mutations beyond closure contracts.** Workbench remains read-only; only the publish-feedback closure paths (where implemented) are mutable.

### 4.2 Contract-frozen but not operational (Plan E gate)

These items have contract truth but no implementation. They MUST NOT be presented to operators as features:

- Digital Anchor create-entry payload builder (B1).
- Digital Anchor formal new-task route (B2).
- Digital Anchor Phase D.1 publish-feedback write-back (B3).
- Matrix Script `result_packet_binding` artifact lookup (B4) — the `not_implemented_phase_c` string is the visible signal that this item is gated.
- Asset Library object service / UI (C1).
- Promote intent service / UI (C2).
- Promote closure service / admin review UI (C3).
- Unified `publish_readiness` producer (D1) — Board / Workbench / Delivery still re-derive locally until Plan E.
- L3 `final_provenance` field producer (D2) — UI still infers current-vs-historical from `final_fresh` + timestamps until Plan E.
- Workbench panel dispatch as contract-driven object (D3) — today still in-code dict at `gateway/app/services/operator_visible_surfaces/projections.py:239-246`.
- L4 advisory producer / emitter (D4) — taxonomy frozen; no service emits.

## 5. Operator Explanation Model (口径)

The trial coordinator MUST use these phrasings verbatim or close to verbatim. Operators see three primary surfaces; each gets one short explanation.

### 5.1 Task Area (`/tasks`, `/tasks/<line>/new`)

> **What you see:** three lines listed — Hot Follow, Matrix Script, Digital Anchor.
> **What you may do:** submit Hot Follow tasks; submit Matrix Script tasks via the line's create-entry form.
> **What you may not do:** submit Digital Anchor tasks. The Digital Anchor card is preview only; its create form has not yet landed.
> **What's hidden:** vendor, model, provider, engine, route — these are runtime concerns and never appear here.

### 5.2 Workbench (`/tasks/{task_id}`)

> **What you see:** a read-only projection of the current attempt and accepted artifacts.
> **What is current vs historical:** "Current attempt" rows describe what the line is doing right now. "Historical" rows are previously accepted outputs that may be replaced as new attempts complete; they are timestamped and labeled but they are **not** current truth.
> **What you may do:** inspect; for Matrix Script, exercise publish-feedback closure on each variation.
> **What you may not do:** edit anything outside the closure paths. Workbench does not own task or packet truth.

Note for trial coordinator: until Plan D D2 lands in code, the "current vs historical" distinction is UI inference from `final_fresh` + timestamps. Treat the inference as accurate for trial purposes; do not create test cases that race the inference (e.g. rapid resubmits) — those edge cases are why D2 promotes the field to L3 truth.

### 5.3 Delivery Center (`/tasks/{task_id}/publish`)

> **What you see:** the deliverables for this task — final video, required deliverables, and optional items.
> **What is required vs optional:** required deliverables block publish; optional items (e.g., scene pack) **never block publish**. If you see an optional item missing, that is expected and not an error.
> **What you may do:** for Hot Follow, publish end-to-end. For Matrix Script, inspect — Delivery Center is not yet truth for this line; operate via Workbench publish-feedback closure instead.
> **What you may not do:** rely on a deliverable row labeled "unresolved" for Matrix Script. That label means the artifact lookup has not yet been wired through to L2 truth.

Note for trial coordinator: the `required` / `blocking_publish` field shape is contract-frozen (Plan C C4 amendment to `factory_delivery_contract_v1.md`); the per-row UI rendering will arrive at Plan E. Until then, scene_pack-style derivatives MUST be presented as "optional, never blocks publish" verbatim. Scene-pack non-blocking is now explicit contract truth (`scene_pack_blocking_allowed: false`); this is binding for all lines.

## 6. Line-by-Line Trial Guidance

### 6.1 Hot Follow

- **Trial scope:** end-to-end (intake → subtitle → dub → compose → publish).
- **Sample profile:** short clip with a known-good source, full TTS-replace route, full publish.
- **Confidence:** high. Hot Follow is the runtime boundary reference and has not moved since `ca20c60`. The advisory taxonomy at `hot_follow_projection_rules_v1.md:272-335` is fully authored — but the **producer** that emits these advisories does not yet exist (D4 contract-frozen, implementation gated). Operators may see Workbench/Publish surfaces without advisory rows; this is expected during trial.
- **Operator misuse to avoid:** treating helper translation history as a current error after target subtitle is authoritative — per `hot_follow_projection_rules_v1.md` §"Helper retryable provider warning". Coordinator should brief operators on this distinction.

### 6.2 Matrix Script

- **Trial scope:** end-to-end **except Delivery Center binding**. Submit via `/tasks/matrix-script/new`; inspect the Workbench Phase B variation surface; exercise publish-feedback closure on variation rows.
- **Sample profile:** 2–3 axis × 4–6 slot variation plan against a fixed topic; target language `mm` or `vi` (current allowed set per `gateway/app/services/matrix_script/create_entry.py:39`).
- **Confidence:** medium for shape inspection; **low for end-to-end Delivery** — the `result_packet_binding.artifact_lookup` placeholder (`not_implemented_phase_c` at five rows) means deliverable-side artifact resolution does not yet read packet truth. Operators MUST treat Delivery Center for this line as inspect-only.
- **Operator misuse to avoid:** treating a Matrix Script Delivery Center row as confirmed delivery. Treating publish-feedback closure as a substitute for unimplemented Delivery binding.

### 6.3 Digital Anchor

- **Trial scope:** **inspection only.** Operators may open the New-Tasks landing page and confirm the Digital Anchor card exists. They MUST NOT click through to submit.
- **Sample profile:** none. No trial sample is authorized for Digital Anchor in this wave.
- **Confidence:** none for runs; high for the contract layer (Phases A–D.0 frozen + Plan B B1/B2/B3 contracts now frozen). The visible gap is implementation, not contract.
- **Operator misuse to avoid:** submitting via the generic temp route `/tasks/connect/digital_anchor/new` — that route is discovery-only and MUST be removed once the formal route lands at Plan E. Coordinator should hide or disable both the New-Tasks card click target and the temp URL during trial.

## 7. Suggested Trial Samples

### 7.1 First-wave samples (in order)

1. **Hot Follow — short clip golden path.** A 30–90 second source video with clean audio and a known-good language pair. Full TTS-replace route with subtitle + dub + compose + publish. Goal: confirm the runtime baseline is unchanged and Board / Workbench / Delivery surfaces present a coherent operator narrative.
2. **Hot Follow — preserve-source route.** Same clip, preserve-source compose. Goal: confirm `dub_not_required_for_route` flow renders as expected and scene-pack absence does NOT block publish (validates the explicit `scene_pack_blocking_allowed: false` rule from the operator perspective).
3. **Matrix Script — small variation plan.** 2 axes × 4 slots against a fixed topic. Submit via `/tasks/matrix-script/new`. Goal: confirm the create-entry form accepts only the closed entry set; confirm the Workbench Phase B variation surface renders read-only; confirm publish-feedback closure mutates rows correctly.
4. **Matrix Script — multi-language target.** Same plan with `target_language=vi`. Goal: confirm `target_language` enum is enforced (`mm` / `vi` only).
5. **Cross-line `/tasks` Board inspection.** Open the Board with at least one task per eligible line in flight. Goal: confirm three lines render side-by-side; confirm Digital Anchor row is preview-labeled and not actionable.

### 7.2 Samples to avoid in the first trial wave

- Any Digital Anchor task submission (from any route).
- Any promote intent or B-roll page interaction.
- Any Matrix Script task whose success criterion is Delivery Center end-to-end (publish via Workbench feedback closure instead).
- Any rapid-fire resubmit / race-condition test against the "current vs historical" distinction (D2 promotion to L3 lands at Plan E).
- Any task that requires a vendor / model / provider selector (none should be available; if one appears, file as a regression).
- Any third-line task — none exists.

## 8. Risks and Misuse Prevention

| Risk                                                                                                                | Mitigation                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Operator submits a Digital Anchor task via New-Tasks card or the generic temp route.                                | Hide or disable the New-Tasks Digital Anchor card click target during trial; remove `/tasks/connect/digital_anchor/new` from operator-facing navigation.    |
| Operator treats Matrix Script Delivery Center row as confirmed delivery.                                             | Coordinator briefs explicitly: Matrix Script Delivery Center is inspect-only this wave. Use Workbench publish-feedback closure for the Matrix Script flow. |
| Operator interprets `not_implemented_phase_c` as a system error.                                                     | Coordinator explains the placeholder is an explicit "unresolved" indication — by design — until Plan E lands the artifact lookup.                          |
| Operator interprets a missing scene-pack row as a publish blocker.                                                   | Brief: scene-pack is non-blocking by contract (`scene_pack_blocking_allowed: false`). Missing scene-pack is expected; it never blocks publish.              |
| Operator opens an Asset Supply / B-roll page expecting working filters or promote.                                   | Hide the page from operator navigation. Page is contract-frozen, not implemented.                                                                          |
| Operator looks for a vendor / model / route selector to "fix" a stale dub.                                          | Brief: vendor / model / provider / engine controls are forbidden at all phases. Retry / inspect dub via Workbench advisory once advisories land at Plan E. |
| Operator confuses "Current attempt" with "Historical" rows on Workbench.                                            | Coordinator briefs §5.2 explanation verbatim; coordinator avoids race-y resubmit test cases until D2 lands.                                                |
| Operator submits a publish action that races a publish-feedback callback.                                           | Plan B B3 freezes monotonic-per-`(row_scope, row_id)` timestamp discipline; producer code lands at Plan E. During trial, brief operators to wait for closure record before re-issuing. |
| Operator triggers "third line" entry by exploring URLs.                                                             | None should exist; if any URL pattern resolves, file as a regression and stop the trial.                                                                  |

## 9. Next Gate Conditions (Plan E pre-conditions)

The next operator-visible implementation wave (Plan E per gap review §11) MUST NOT start until:

1. **Plan A executed.** This document used to coordinate at least one full trial wave covering the §7.1 sample set; trial write-up filed under `docs/execution/` documenting what landed, what blocked, and what surfaces drifted.
2. **Plan B contract freeze remains binding.** Digital Anchor B1 / B2 / B3 and Matrix Script B4 contracts un-amended (or amendments only additive).
3. **Plan C contract freeze remains binding.** Asset Library / promote contracts un-amended; `scene_pack_blocking_allowed: false` un-amended.
4. **Plan D contract freeze remains binding.** Unified `publish_readiness_contract_v1`, `final_provenance` L3 amendment, panel dispatch contract, and advisory producer output contract un-amended.
5. **No regression observed in the trial wave** that requires re-opening Hot Follow business behavior, Matrix Script frozen contracts, or Digital Anchor frozen Phase A–D.0 contracts.
6. **No premature implementation** of any Plan E item began during this wave — the freeze is the deliverable; implementation is gated.

When all six conditions hold, Plan E may be authored and the next wave's command file may be issued.

### Permitted Plan E scope when the gate opens

Mirrors gap review §11 Plan E:

- Asset Library page (read-only) backed by `asset_library_object_contract_v1`.
- Promote intent UI backed by `promote_request_contract_v1`.
- Delivery Center per-deliverable zoning rendered from `required` + `blocking_publish`.
- Workbench `final_provenance` strip rendered from L3.
- Board / Workbench / Delivery converging on `publish_readiness_contract_v1` (single source).
- L4 advisory producer emitting; surfaces consuming.
- Digital Anchor formal create-entry route + payload builder + Phase D.1 write-back implementation.
- Matrix Script `result_packet_binding` artifact-lookup wired (replacing `not_implemented_phase_c` placeholders).

### Forbidden until the gate opens

- New line implementation.
- W2.2 / W2.3 capability work.
- Platform Runtime Assembly.
- Provider / model / vendor consoles.
- Workbench writeback beyond closure contracts.
- Donor namespace import.

## 10. Validation

This is a documentation freeze; validation is documentary.

1. **Authority alignment.** Every trial-eligibility statement traces to the gap review §4 row, the wave authority, or a frozen contract. Cross-checked: §3.1 to gap review §4 + §7; §3.2 to existing engineering progress; §4 to frozen contracts and Plan E gate.
2. **No operational promise exceeds gate status.** Every "Production-eligible" or "Plan E gate" row is explicit; no surface is promised end-to-end without the contract-and-code combination required.
3. **Preview-only vs trial-safe scope explicit.** §3 vs §4 split is binding; §6 line-by-line guidance restates the split per line.
4. **No vendor / model / provider drift.** §4.1, §5, §6, §8 all reassert that vendor / model / provider / engine controls are forbidden at all phases.
5. **No new contract authored.** This document does not author packet, schema, or contract truth; it consumes the Plan B / C / D freeze and the existing wave authority verbatim.
6. **No scope expansion.** No statement here permits work that the gap review §13 final gate decision marked BLOCKED.

## 11. Execution Log Update

This Plan A document is itself the execution artifact for the Plan A step. The Plan B / C / D execution log at [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) §8 marked Plan A readiness = YES on 2026-05-02; this document is the realization of that readiness.

- Plan A document created: `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (this file).
- Authority read: gap review v1, wave authority, Plan B/C/D execution log, all newly frozen contracts (12 files), engineering rules, current engineering focus.
- Trial-safe scope: §3.
- Preview-only / contract-frozen-not-operational scope: §4.
- Final readiness judgment: §12.

A trial-execution write-up (post-trial) MUST be filed separately under `docs/execution/` once §7.1 sample wave completes; that file is the Plan E pre-condition #1.

## 12. Final Readiness Conclusion

- **Ops trial readiness:** **CONDITIONAL**
  - Conditions for the trial to proceed safely:
    1. Trial coordinator briefs operators on §5 explanation 口径 verbatim.
    2. Digital Anchor New-Tasks card and `/tasks/connect/digital_anchor/new` are hidden or disabled for the trial duration.
    3. Asset Supply / B-roll page is hidden from operator navigation for the trial duration.
    4. Trial scope is restricted to §7.1 samples; samples in §7.2 are not attempted.
    5. Coordinator monitors for the §8 risk list and pauses the trial if any forbidden surface activates.
- **Next operator-visible implementation wave (Plan E):** **BLOCKED — READY WITH CONDITIONS** (the six pre-conditions in §9 must all hold; today only Plan B/C/D freeze is satisfied — Plan A trial execution remains).
- **Runtime Assembly:** **BLOCKED**
- **Capability Expansion:** **BLOCKED**
- **Frontend patching:** **BLOCKED**

End of Plan A.
