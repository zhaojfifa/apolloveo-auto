# Operations Trial Readiness Plan v1 (Plan A)

Date: 2026-05-02 (initial freeze); 2026-05-03 (Matrix Script §8.D operator brief correction landed)
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (a.k.a. "Operations Upgrade Alignment Wave")
Status: Plan A — operator-facing trial scope freeze. **Documentation only. No code, no UI, no runtime change.** Matrix Script trial brief now reflects the accepted §8.A / §8.B / §8.C corrections (see §0.1).
Authority:
- [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](../reviews/operations_upgrade_gap_review_and_ops_plan_v1.md) (gap review v1; §11 Plan A is the source of this document's structure)
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) (Matrix Script Plan A trial blocker + realign review; §8.A / §8.B / §8.C accepted; §8.D operator brief correction realised in this document)
- [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md) (active wave authority)
- [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) (Plan B / C / D contract freeze; final gate PASS)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed; PASS)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed; PASS)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed; PASS)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) (§8.D — this document's correction)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)
- Newly frozen contracts:
  - Plan B: `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md`, `docs/contracts/digital_anchor/new_task_route_contract_v1.md`, `docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md`, `docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md`
  - Plan C: `docs/contracts/asset_library_object_contract_v1.md`, `docs/contracts/promote_request_contract_v1.md`, `docs/contracts/promote_feedback_closure_contract_v1.md`, plus amendments to `docs/contracts/factory_delivery_contract_v1.md` (`required` / `blocking_publish` / `scene_pack_blocking_allowed: false`) and `docs/contracts/hot_follow_projection_rules_v1.md` (explicit scene-pack non-blocking)
  - Plan D: `docs/contracts/publish_readiness_contract_v1.md`, `docs/contracts/workbench_panel_dispatch_contract_v1.md`, `docs/contracts/l4_advisory_producer_output_contract_v1.md`, plus amendment to `docs/contracts/hot_follow_current_attempt_contract_v1.md` (`final_provenance` L3 field)
  - Matrix Script Plan A trial corrections (additive): `docs/contracts/matrix_script/task_entry_contract_v1.md` §"Source script ref shape (addendum, 2026-05-02)" (§8.A) and §"Phase B deterministic authoring (addendum, 2026-05-03)" (§8.C)

## 0.1 Matrix Script Trial Sample Validity (binding, post-§8.A / §8.B / §8.C)

This section is the operator-facing rule on which Matrix Script samples count as trial evidence. It overrides any older §3 / §6 / §7 wording that was authored before the §8.A / §8.B / §8.C corrections landed; the §3, §6, and §7 sub-sections below have been corrected to match.

- **Old broken Matrix Script sample (pre-§8.A): INVALID.** Any Matrix Script task created before the §8.A `source_script_ref` ref-shape guard landed is **invalid trial evidence** and MUST NOT be reused. The blocker review §9 ruling stands; §8.A's PASS gate explicitly does not retrofit existing rows. If an operator session encounters a task whose `source_url` carries pasted script body text (multi-line, prose, or any non-opaque-ref payload), it is the prior invalid sample — discard it from trial evidence and create a fresh sample via the formal route.
- **Fresh corrected Matrix Script sample (post-§8.A / §8.B / §8.C): the only acceptable trial sample type.** A sample qualifies as trial evidence iff:
  1. it was created via the formal `/tasks/matrix-script/new` POST (the formal Matrix Script entry path) — never the generic `/tasks/connect/...` path;
  2. its persisted `source_url` (and `packet.config.entry.source_script_ref`) is an opaque ref handle accepted by the §8.A guard (closed schemes `content` / `task` / `asset` / `ref` / `s3` / `gs` / `https` / `http`, or a bare token id matching the documented pattern; single line; no whitespace; ≤512 chars);
  3. its packet carries populated `line_specific_refs[matrix_script_variation_matrix].delta` (3 canonical axes — `tone` / `audience` / `length` — and `variation_target_count` cells) and `line_specific_refs[matrix_script_slot_pack].delta` (one slot per cell) authored deterministically at task creation per §8.C; `cells[i].script_slot_ref ↔ slots[i].slot_id` round-trips for every i;
  4. its workbench mounts the Matrix Script Phase B variation panel (`panel_kind="matrix_script"`, `data-role="matrix-script-variation-panel"`, projection `matrix_script_workbench_variation_surface_v1`) with real resolvable axes / cells / slots — not the empty-fallback messages (`"No axes resolved on this packet"`, `"No cells resolved on this packet"`, `"No slots resolved on this packet"`, `"No `line_specific_refs[]` on this packet"`).
- **Matrix Script workbench is now inspectable for real packet truth.** Per §8.B the dispatch is correct end-to-end on a fresh contract-clean sample (`/tasks/{task_id}` for `kind=matrix_script` lands the Phase B variation panel inside the shared shell — per-line dispatch is via `panel_kind` mounting, not a per-line template). Per §8.C the panel renders real axes / cells / slots — the empty-shell / no-Phase-B-truth state described in the original blocker observation is no longer the live state for fresh samples. Operators may inspect the panel's authored axes / cells / slots and exercise publish-feedback closure on each variation row.
- **Matrix Script Delivery Center remains inspect-only.** This boundary is unchanged by §8.A / §8.B / §8.C. `delivery_binding.py:93-125` still emits the five `not_implemented_phase_c` placeholder rows by Plan A §3.2 and `result_packet_binding_artifact_lookup_contract_v1` (Plan B B4 — code change gated to Plan E). Operators MUST treat Delivery Center for Matrix Script as inspect-only this wave; use Workbench publish-feedback closure for the Matrix Script flow.
- **Matrix Script Phase D.1 publish-feedback closure surface remains as already shipped.** The closure shape / write-back boundary is per `publish_feedback_closure_contract_v1` (Phase D.0 freeze) and the Phase D.1 minimal write-back already landed (see [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](../execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md) §"Phase D.1"); §8.D does not promote, mutate, or expand this boundary. The Plan B B3 (Digital Anchor) write-back stays gated to Plan E.
- **Operators MUST NOT report inspect-only / contract-only surfaces as defects.** Specifically: Matrix Script Delivery Center placeholder rows are by design; Matrix Script Phase B variation panel rendering authored deterministic axes (`tone` / `audience` / `length`) is by design (per §8.C addendum); Matrix Script Delivery Center will not become operator-truth in this wave even after §8.D lands.

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
| **Matrix Script** | End-to-end **except Delivery Center binding**: submit a fresh contract-clean sample via the formal `/tasks/matrix-script/new` POST (under §8.A's `source_script_ref` ref-shape guard), inspect the Workbench Phase B variation panel (now rendering real authored axes / cells / slots per §8.C), exercise publish-feedback closure per variation row. **Old pre-§8.A samples are invalid trial evidence — see §0.1.** | Phases A–D contracts frozen; create-entry shipped (`4896f7c`); workbench panel render shipped (`b370e46`, #77); Plan A trial corrections §8.A (`f6125aa`, source_script_ref ref-shape guard), §8.B (`970b4dc`, panel-dispatch confirmation), §8.C (`9f25b89`, deterministic Phase B authoring) all PASS — fresh samples now carry populated `variation_matrix.delta` (3 canonical axes — `tone`/`audience`/`length` — and `variation_target_count` cells) and `slot_pack.delta` (one slot per cell), and the Phase B variation panel mounts and renders real inspectable truth. |
| **Digital Anchor** | **Inspection-only.** Operators may open the New-Tasks card to confirm the line exists; they MUST NOT submit a task.                                                    | Phase D.1 write-back not implemented; formal `/tasks/digital-anchor/new` route not implemented (gap review §7.3). Plan B contracts now exist; code does not. |

### 3.2 Trial-eligible surfaces

| Surface                                                            | Eligibility           | Authority                                                                                                                                |
| ------------------------------------------------------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `/tasks` Board (Hot Follow + Matrix Script rows)                   | Production-eligible   | `derive_board_publishable` over `ready_gate`; tested. (Note: surface still re-derives publishable until Plan D `publish_readiness_contract_v1` lands in code at Plan E.) |
| `/tasks/matrix-script/new` create-entry form                       | Production-eligible   | Closed packet payload builder per `task_entry_contract_v1`; alignment doc `matrix_script_formal_create_entry_alignment_v1.md`. **Per §8.A:** the form input for `source_script_ref` is now a constrained text input (`pattern` + `maxlength=512`) and the server-side `_validate_source_script_ref_shape` guard rejects pasted body text (multi-line, whitespace-bearing, overlong, or unrecognised-scheme values) with `HTTP 400` before the payload-builder runs. The contract addendum at `task_entry_contract_v1.md` §"Source script ref shape (addendum, 2026-05-02)" pins the closed accepted scheme set as exhaustive at v1. |
| Workbench panel — Hot Follow                                       | Production-eligible   | L3 `current_attempt` consumed via packet refs (per `hot_follow_current_attempt_contract_v1.md`).                                          |
| Workbench panel — Matrix Script (Phase B variation surface, read-only) | Production-eligible (read-only) | Read-only projection of `line_specific_refs[matrix_script_variation_matrix/slot_pack].delta`; merge note `matrix_script_operator_visible_slice_merge_note_v1.md`. **Per §8.B:** dispatch is confirmed end-to-end on a fresh contract-clean sample — `GET /tasks/{task_id}` for `kind=matrix_script` lands `task_workbench.html` (the shared shell), `resolve_line_specific_panel(packet)` returns `panel_kind="matrix_script"`, `wiring.py` attaches the formal `matrix_script_workbench_variation_surface_v1` projection, and the rendered HTML carries `data-role="matrix-script-variation-panel"`, `data-panel-kind="matrix_script"`, the projection name, and both seeded `ref_id`s. **Per §8.C:** the panel now renders real authored axes (`tone` / `audience` / `length`), `variation_target_count` cells, and one slot per cell — empty-fallback messages are absent on fresh samples. |
| Delivery Center — Hot Follow                                       | Production-eligible   | Existing read-only projection over `ready_gate` + L2 facts.                                                                              |
| Delivery Center — Matrix Script                                    | **Inspect-only**      | `result_packet_binding.artifact_lookup` still emits `not_implemented_phase_c` placeholders at `gateway/app/services/matrix_script/delivery_binding.py:93-125`. The Plan B B4 contract pins the resolution shape; the code change waits on Plan E. **Unchanged by §8.A / §8.B / §8.C:** these corrections covered task entry, panel dispatch, and Phase B authoring — none of them promote Matrix Script Delivery Center beyond inspect-only this wave. |
| Cross-line `/tasks` Board inspection                               | Production-eligible   | Three lines listed; only Hot Follow + Matrix Script rows accept new tasks.                                                               |

### 3.3 Surfaces operators may inspect but not operate

- Digital Anchor New-Tasks card — visible, label-only; submit MUST be hidden or disabled.
- Digital Anchor Workbench panel placeholder — not rendered for trial; if the placeholder branch is reachable, label as "preview" (gap review §6 discovery-only classification).
- Matrix Script Delivery Center rows — visible with `not_implemented_phase_c` placeholder rendered as "unresolved"; operators may inspect but MUST NOT treat as truth for ops 跑量. (Unchanged by §8.A / §8.B / §8.C — the Delivery Center boundary stays inspect-only this wave.)
- Matrix Script Workbench Phase B variation panel — now mounts and renders **real** inspectable axes / cells / slots on a fresh contract-clean (post-§8.A / §8.B / §8.C) sample. The panel itself is read-only by `workbench_variation_surface_contract_v1`; operator interaction is limited to inspecting the authored axes (`tone` / `audience` / `length`), `variation_target_count` cells, and per-cell slots, plus exercising publish-feedback closure on each variation row. The panel does NOT yet author or mutate axes / cells / slots on operator command — the §8.C deterministic authoring step runs once at task creation only.

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

> **What you see:** a read-only projection of the current attempt and accepted artifacts. For Matrix Script (`kind=matrix_script`), the shared workbench shell mounts the Phase B variation panel on top — labelled "Matrix Script — Variation Panel" with the contract projection name `matrix_script_workbench_variation_surface_v1`. On a fresh contract-clean sample (created via the formal `/tasks/matrix-script/new` POST after §8.A / §8.B / §8.C landed), this panel renders real authored axes (`tone` / `audience` / `length`), `variation_target_count` cells, and one slot per cell — not the empty-fallback messages.
> **What is current vs historical:** "Current attempt" rows describe what the line is doing right now. "Historical" rows are previously accepted outputs that may be replaced as new attempts complete; they are timestamped and labeled but they are **not** current truth.
> **What you may do:** inspect; for Matrix Script, inspect the Phase B variation panel's authored axes / cells / slots and exercise publish-feedback closure on each variation row.
> **What you may not do:** edit anything outside the closure paths. Workbench does not own task or packet truth. The Phase B variation panel is read-only — it does not author or mutate axes / cells / slots on operator command (§8.C runs once at task creation only).

Note for trial coordinator: until Plan D D2 lands in code, the "current vs historical" distinction is UI inference from `final_fresh` + timestamps. Treat the inference as accurate for trial purposes; do not create test cases that race the inference (e.g. rapid resubmits) — those edge cases are why D2 promotes the field to L3 truth.

Note for trial coordinator (Matrix Script panel): if a Matrix Script task workbench shows the empty-slot fallback ("No axes resolved on this packet" / "No cells resolved on this packet" / "No slots resolved on this packet" / "No `line_specific_refs[]` on this packet"), that task is the **prior invalid sample** (created before §8.A / §8.B / §8.C) — discard from trial evidence and create a fresh sample. Per §8.A's PASS gate, the corrections do not retrofit existing rows; only fresh samples carry populated deltas.

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

- **Trial scope:** end-to-end **except Delivery Center binding**. Submit a fresh contract-clean sample via the formal `/tasks/matrix-script/new` POST (only — never via `/tasks/connect/...`); inspect the Workbench Phase B variation panel rendering real authored axes / cells / slots; exercise publish-feedback closure on variation rows.
- **Sample profile:**
  - **Source script ref (`source_script_ref`):** opaque ref handle only. Accepted: a URI with one of the closed schemes (`content://...`, `task://...`, `asset://...`, `ref://...`, `s3://...`, `gs://...`, `https://...`, `http://...`) or a bare token id matching `^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$`. Single line, no whitespace, ≤512 chars. **Pasting raw script body is rejected with `HTTP 400` by §8.A's guard.**
  - **Topic / target / variation count:** the closed entry-field set per `task_entry_contract_v1` is enforced; `target_language` ∈ `{mm, vi}` (current allowed set per `ALLOWED_TARGET_LANGUAGES` at `gateway/app/services/matrix_script/create_entry.py:44`); `variation_target_count` ∈ `[1, 12]`.
  - **Authored Phase B truth:** §8.C's deterministic planner runs once at task creation and emits 3 canonical axes (`tone` categorical / `audience` enum / `length` range with `{min: 30, max: 120, step: 15}`) and `variation_target_count` cells, each paired with one slot via index-aligned `cells[i].script_slot_ref ↔ slots[i].slot_id`. `body_ref = "content://matrix-script/{task_id}/slot/{slot_id}"` is opaque by construction. Operators inspect these axes / cells / slots; they do not author them.
- **Confidence:** **high** for entry-shape, panel-mount, and Phase B inspection — §8.A's guard, §8.B's dispatch confirmation, and §8.C's deterministic authoring make a fresh contract-clean sample render real resolvable truth in the Phase B variation panel. **Low for end-to-end Delivery** — the `result_packet_binding.artifact_lookup` placeholder (`not_implemented_phase_c` at five rows) means deliverable-side artifact resolution does not yet read packet truth. Operators MUST treat Delivery Center for this line as inspect-only.
- **Operator misuse to avoid:**
  - Treating a Matrix Script Delivery Center row as confirmed delivery (it is inspect-only this wave).
  - Treating publish-feedback closure as a substitute for unimplemented Delivery binding.
  - Reusing an old pre-§8.A Matrix Script sample (any task whose `source_url` carries pasted script body text) — those are invalid evidence per §0.1; create a fresh sample instead.
  - Submitting Matrix Script via the generic `/tasks/connect/...` path or any non-formal route — the formal `/tasks/matrix-script/new` POST is the only acceptable trial-sample creation path.
  - Reporting the Phase B variation panel's deterministic axes (`tone` / `audience` / `length`) as a defect — they are the authored canonical axes per §8.C's contract addendum, not operator-supplied custom axes (Plan E may extend this; in this wave, the canonical set is binding).
  - Reporting the Delivery Center `not_implemented_phase_c` placeholder rows as defects — they are inspect-only by `result_packet_binding_artifact_lookup_contract_v1` (Plan B B4) until Plan E.

### 6.3 Digital Anchor

- **Trial scope:** **inspection only.** Operators may open the New-Tasks landing page and confirm the Digital Anchor card exists. They MUST NOT click through to submit.
- **Sample profile:** none. No trial sample is authorized for Digital Anchor in this wave.
- **Confidence:** none for runs; high for the contract layer (Phases A–D.0 frozen + Plan B B1/B2/B3 contracts now frozen). The visible gap is implementation, not contract.
- **Operator misuse to avoid:** submitting via the generic temp route `/tasks/connect/digital_anchor/new` — that route is discovery-only and MUST be removed once the formal route lands at Plan E. Coordinator should hide or disable both the New-Tasks card click target and the temp URL during trial.

## 7. Suggested Trial Samples

### 7.1 First-wave samples (in order)

1. **Hot Follow — short clip golden path.** A 30–90 second source video with clean audio and a known-good language pair. Full TTS-replace route with subtitle + dub + compose + publish. Goal: confirm the runtime baseline is unchanged and Board / Workbench / Delivery surfaces present a coherent operator narrative.
2. **Hot Follow — preserve-source route.** Same clip, preserve-source compose. Goal: confirm `dub_not_required_for_route` flow renders as expected and scene-pack absence does NOT block publish (validates the explicit `scene_pack_blocking_allowed: false` rule from the operator perspective).
3. **Matrix Script — fresh contract-clean small variation plan.** Submit via the formal `/tasks/matrix-script/new` POST with `variation_target_count=4`, `target_language=mm`, a fixed `topic`, and an opaque `source_script_ref` (e.g. `content://matrix-script/source/<your-id>`). **Do not paste raw script body — §8.A's guard rejects it with HTTP 400.** Goals: (a) confirm the create-entry form rejects body-text input and accepts the opaque ref; (b) confirm `GET /tasks/{task_id}` for `kind=matrix_script` mounts the Matrix Script Phase B variation panel (`data-role="matrix-script-variation-panel"`, projection `matrix_script_workbench_variation_surface_v1`) with the empty-fallback messages absent; (c) confirm the panel renders 3 canonical axes (`tone` / `audience` / `length`), 4 cells (`cell_001..cell_004`), and 4 slots (`slot_001..slot_004`) with `cells[i].script_slot_ref ↔ slots[i].slot_id` resolving end-to-end; (d) confirm publish-feedback closure mutates rows correctly per `cell_id ↔ variation_id`.
4. **Matrix Script — multi-language target.** Same plan with `target_language=vi`. Goals: (a) confirm `target_language` enum is enforced (`mm` / `vi` only); (b) confirm slot `language_scope.target_language` carries `vi` end-to-end on the persisted packet.
5. **Matrix Script — variation count boundary check.** Submit one fresh sample with `variation_target_count=1` and another with `variation_target_count=12`. Goal: confirm cardinality matches at both boundaries and the panel still renders real axes (cardinality of `axes[]` is fixed at 3 by the §8.C addendum regardless of `variation_target_count`).
6. **Cross-line `/tasks` Board inspection.** Open the Board with at least one task per eligible line in flight. Goal: confirm three lines render side-by-side; confirm Digital Anchor row is preview-labeled and not actionable.

### 7.2 Samples to avoid in the first trial wave

- Any Digital Anchor task submission (from any route).
- Any promote intent or B-roll page interaction.
- Any Matrix Script task whose success criterion is Delivery Center end-to-end (publish via Workbench feedback closure instead).
- Any rapid-fire resubmit / race-condition test against the "current vs historical" distinction (D2 promotion to L3 lands at Plan E).
- Any task that requires a vendor / model / provider selector (none should be available; if one appears, file as a regression).
- Any third-line task — none exists.
- **Any reuse of a pre-§8.A Matrix Script sample.** If an operator session encounters a Matrix Script task whose `source_url` / `packet.config.entry.source_script_ref` carries pasted body text (multi-line, prose, or any non-opaque-ref payload), or whose Phase B panel renders the empty-fallback messages, that task is the **prior invalid sample** — discard from trial evidence and create a fresh sample via the formal POST. §8.A's PASS gate explicitly does not retrofit existing rows.
- **Any Matrix Script task created via `/tasks/connect/matrix_script/new`** — this generic temp path was removed from the primary route by the formal create-entry alignment wave; if it is still reachable, file a regression and use the formal `/tasks/matrix-script/new` POST instead.
- **Any expectation that the Phase B variation panel is operator-authoring** — the panel is read-only; §8.C's deterministic authoring runs once at task creation, not on operator command. Operator-driven Phase B authoring is permitted Plan E future work per the §8.C contract addendum.

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
| Operator pastes raw script body text into Matrix Script `source_script_ref`.                                        | §8.A's server-side guard rejects with `HTTP 400` and the form re-renders with a localised error message; coordinator briefs §6.2 sample profile (opaque ref only) and the `/tasks/matrix-script/new` form's helper text already forbids body paste. If the rejection is observed, that is the guard working — not a defect. |
| Operator reuses a pre-§8.A Matrix Script sample (any task whose `source_url` carries pasted body text).             | Coordinator briefs §0.1 and §6.2: the old sample is invalid evidence per the blocker review §9 and §8.A's PASS gate. Discard from trial evidence and create a fresh sample via the formal POST. §8.A does not retrofit existing rows. |
| Operator opens a Matrix Script task and observes empty-fallback messages on the Phase B panel ("No axes resolved on this packet" / "No cells resolved on this packet" / "No slots resolved on this packet" / "No `line_specific_refs[]` on this packet"). | That task is the prior invalid sample (created before §8.A / §8.B / §8.C). Discard from trial evidence; create a fresh sample. On a fresh contract-clean sample, §8.C's deterministic authoring populates the deltas at task creation and the empty-fallback messages are absent. |
| Operator reports the Phase B panel's deterministic axes (`tone` / `audience` / `length`) as a defect or "wrong" axis set. | Coordinator briefs §6.2: §8.C's contract addendum at `task_entry_contract_v1.md` §"Phase B deterministic authoring (addendum, 2026-05-03)" pins the canonical axes. Operator-driven custom axes are Plan E future work, not in this wave. |
| Operator submits Matrix Script via `/tasks/connect/matrix_script/new` (legacy generic path).                         | The formal create-entry alignment wave removed Matrix Script from `_TEMP_CONNECTED_LINES`; if the legacy path is still reachable, file a regression. Use the formal `/tasks/matrix-script/new` POST. |
| Operator expects to author or mutate axes / cells / slots from the Phase B panel.                                    | Brief: the Phase B variation panel is read-only by `workbench_variation_surface_contract_v1`. §8.C's deterministic authoring runs once at task creation only; operator-driven Phase B authoring is Plan E future work per the §8.C addendum. |

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
5. **No new contract authored.** This document does not author packet, schema, or contract truth; it consumes the Plan B / C / D freeze and the existing wave authority verbatim. The §8.D correction adds no contract addendum either — §0.1 / §3 / §6 / §7 / §8 / §11.1 / §12 cite the §8.A and §8.C contract addenda already on `task_entry_contract_v1` without modifying them.
6. **No scope expansion.** No statement here permits work that the gap review §13 final gate decision marked BLOCKED.
7. **§8.D correction — Matrix Script trial brief alignment.** Cross-checked against the §8.A / §8.B / §8.C execution logs: §0.1 / §3.2 / §6.2 ref-shape rule mirrors §8.A's closed accepted scheme set verbatim; §0.1 / §3.2 / §5.2 panel-mount markers mirror §8.B's captured render markers verbatim; §0.1 / §3.2 / §5.2 / §6.2 / §7.1 axes / cells / slots / `body_ref` template mirror §8.C's deterministic-authoring output verbatim; §3.2 / §3.3 / §6.2 / §0.1 Delivery Center inspect-only language preserves Plan B B4 / `result_packet_binding_artifact_lookup_contract_v1`; §0.1 Phase D.1 closure-surface language preserves `publish_feedback_closure_contract_v1` and the existing minimal write-back. No stale empty-shell / no-Phase-B-truth language remains for Matrix Script. See [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) §4.1 / §4.2 for the row-by-row evidence map.

## 11. Execution Log Update

This Plan A document is itself the execution artifact for the Plan A step. The Plan B / C / D execution log at [docs/execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md](../execution/PLAN_BCD_CONTRACT_FREEZE_EXECUTION_LOG_v1.md) §8 marked Plan A readiness = YES on 2026-05-02; this document is the realization of that readiness.

- Plan A document created: `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (this file).
- Authority read: gap review v1, wave authority, Plan B/C/D execution log, all newly frozen contracts (12 files), engineering rules, current engineering focus.
- Trial-safe scope: §3.
- Preview-only / contract-frozen-not-operational scope: §4.
- Final readiness judgment: §12.

A trial-execution write-up (post-trial) MUST be filed separately under `docs/execution/` once §7.1 sample wave completes; that file is the Plan E pre-condition #1.

### 11.1 Matrix Script Plan A trial corrections — landed updates (additive history)

- 2026-05-02 — Plan A trial coordination write-up filed at [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](../execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md) (static pass; live-run §8 placeholder).
- 2026-05-02 — Matrix Script trial blocker / realign review v1 filed at [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md). Blocker conclusion: prior Matrix Script sample is invalid trial evidence (entry-form discipline gap on `source_script_ref`; empty Phase B packet truth). Correction items §8.A / §8.B / §8.C / §8.D enumerated.
- 2026-05-02 — §8.A landed (`f6125aa`); execution log [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md). Server-side ref-shape guard, client-side input shape, contract addendum, validation tests all green.
- 2026-05-03 — §8.B confirmed (`970b4dc`); execution log [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md). No narrow fix required — `panel_kind="matrix_script"` resolves and the Phase B variation panel mounts on a fresh contract-clean sample.
- 2026-05-03 — §8.C landed (`9f25b89`); execution log [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md). Option C1 (deterministic Phase B authoring) chosen; populated `variation_matrix.delta` and `slot_pack.delta` ship at task creation; round-trip resolves; rendered HTML carries real axes / cells / slots.
- 2026-05-03 — §8.D landed (this document update); execution log [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md). Operator brief (this file) corrected so that valid vs invalid Matrix Script trial sample criteria are explicit, no operational promise exceeds current gate status, and no stale wording still describes Matrix Script as empty-shell / no-Phase-B-truth.

## 12. Final Readiness Conclusion

- **Ops trial readiness:** **CONDITIONAL**
  - Conditions for the trial to proceed safely:
    1. Trial coordinator briefs operators on §5 explanation 口径 verbatim.
    2. Digital Anchor New-Tasks card and `/tasks/connect/digital_anchor/new` are hidden or disabled for the trial duration.
    3. Asset Supply / B-roll page is hidden from operator navigation for the trial duration.
    4. Trial scope is restricted to §7.1 samples; samples in §7.2 are not attempted.
    5. Coordinator monitors for the §8 risk list and pauses the trial if any forbidden surface activates.
    6. Matrix Script trial samples MUST be fresh contract-clean samples per §0.1 (post-§8.A / §8.B / §8.C, formal `/tasks/matrix-script/new` POST only). Pre-§8.A samples MUST NOT be reused as trial evidence.
- **Matrix Script Plan A trial corrections:**
  - §8.A (source_script_ref ref-shape guard): **PASS** (landed `f6125aa`, 2026-05-02).
  - §8.B (workbench panel dispatch confirmation): **PASS** (confirmed `970b4dc`, 2026-05-03; no narrow fix required).
  - §8.C (Phase B deterministic authoring): **PASS** (landed `9f25b89`, 2026-05-03; Option C1).
  - §8.D (operator brief correction): **PASS** (this document update, 2026-05-03).
  - **Matrix Script retry sample creation: READY** — Plan A Matrix Script brief now reflects the accepted §8.A / §8.B / §8.C results; valid vs invalid trial sample criteria are explicit (§0.1); fresh corrected sample is fully briefed (§6.2 + §7.1 sample 3); old invalid sample remains invalid (§0.1, §7.2).
- **Next operator-visible implementation wave (Plan E):** **BLOCKED — READY WITH CONDITIONS** (the six pre-conditions in §9 must all hold; today Plan B/C/D freeze is satisfied and the Matrix Script Plan A trial corrections §8.A / §8.B / §8.C / §8.D are all PASS — Plan A live-trial execution against the §7.1 sample wave still remains).
- **Runtime Assembly:** **BLOCKED**
- **Capability Expansion:** **BLOCKED**
- **Frontend patching:** **BLOCKED**

End of Plan A.
