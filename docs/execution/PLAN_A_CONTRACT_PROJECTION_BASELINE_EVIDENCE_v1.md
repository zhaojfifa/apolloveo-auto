# Plan A · Contract / Projection Baseline Evidence v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave
Status: Baseline evidence note. **Documentation only. No code, no UI, no contract, no schema, no template, no test changes.** This note records a single deployed-environment observation strictly as **contract / projection baseline evidence** for the 2.0 architecture/state alignment of the Matrix Script production line. It is **not** a Plan A live-trial completion record, **not** a usability judgment, **not** an operator-workspace completion claim, and **not** a delivery-loop completion claim. Plan A live-trial obligations remain unchanged; this note is one narrow input toward the eventual minimal gate-closing trial.

## 0. Scope (binding)

This evidence note is scoped exactly to the three baseline questions named by user instruction (2026-05-03):

- Does the 2.0 formal entry path **work** end-to-end against the deployed branch?
- Is the contract / projection slice **aligned** (panel dispatch, line-specific refs, projection name, §8.* render correctness)?
- Is the architecture / state framework **not drifting** in the deployed environment?

It is **not** scoped to:

- Operator-workspace usability conclusions.
- Delivery-loop end-to-end completion (Delivery Center inspect-only this wave).
- UI patching decisions (no UI patch authored or proposed).
- §7.1 sample-wave completion (Sample 1 Hot Follow golden / Sample 2 Hot Follow preserve-source / Sample 4 / Sample 5 / Sample 6 are not in scope of this note).
- §12 trial pre-condition closure (the eight conditions are owned by the coordinator; this note does not assert them).
- Plan A "complete" / Plan E "unblock" verdicts (those require live-run §8 fill-in + coordinator/architect/reviewer signoff per [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7.1).

If a future reader interprets this note as anything beyond contract / projection baseline evidence, the scope above wins.

## 1. Authority

- Trial brief: [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) — §0.1 sample-validity rule (criterion 1, 2, 4, 5 are the baseline-evidence criteria); §0.2 product-meaning of `source_script_ref`; §3.2 Workbench Phase B variation surface; §6.2 Matrix Script line guidance; §11.1 trial corrections history.
- Trial coordination write-up: [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) — §3 static evidence rows; §11 / §12 §8.A→§8.H addenda.
- Pre-trial authority audit: [docs/execution/PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md](PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md) — confirms HEAD `b0c61c0` anchors hold.
- Contracts cited (read-only consumption):
  - [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) — §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)"; §"Phase B deterministic authoring (addendum, 2026-05-03)".
  - [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md).
  - [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) — §"Shared shell neutrality (addendum, 2026-05-03)".

## 2. Observation source

- Deployed environment: `apolloveo.com` (operator-visible domain).
- Observation provided to the AI agent on 2026-05-03 by the project owner as a set of UI screenshots covering:
  - `/tasks/matrix-script/new?ui_locale=zh` — formal Matrix Script create-entry form.
  - `/tasks/newtasks` — task-scenario picker (cross-line entry surface).
  - `/tasks/{task_id}?created=matrix_script` — Matrix Script workbench for the freshly-created task.
  - `/tasks` — task board.
- Real `task_id` observed: `7a407e8d00a9`.
- Real persisted `source_script_ref`: `content://matrix-script/source/vn-ai-money-001` (operator-chosen `<token>`, opaque to the product per §0.2).
- Real `target_language`: `vi` (`Tiếng Việt`).
- Real `variation_target_count`: `4`.
- Task creation timestamp shown on workbench: `2026-05-03 10:34:07+00:00`.

This note treats those screenshots as a single deployed-environment observation provided by the project owner. It does **not** elevate them to coordinator-monitored §7.1 sample evidence; that remains the human ops team's deliverable per the brief and the live-run capture template's §0 binding rule.

## 3. Baseline evidence — what this observation establishes

### 3.1 The 2.0 formal entry path works

| Baseline check | Deployed-environment observation | Authority |
| -------------- | -------------------------------- | --------- |
| Formal POST `/tasks/matrix-script/new` is reachable and accepts a closed entry-set submission. | Form rendered; submission produced a real `task_id=7a407e8d00a9` with `kind=matrix_script` and redirected to `/tasks/{task_id}?created=matrix_script`. | Brief §3.2 row "Matrix Script `/tasks/matrix-script/new` accepts a closed entry set"; write-up §3.1. |
| §8.A + §8.F opaque-ref shape accepted. | `source_script_ref=content://matrix-script/source/vn-ai-money-001` accepted (single line, no whitespace, opaque-by-construction `content://` scheme). | Brief §0.1 criterion 2 + 3; §6.2 sample profile; [task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §8.A/§8.F addendum. |
| `target_language` ∈ `{mm, vi}` enforced. | `target_language=vi` accepted; persisted on packet (visible as `language_scope.target=vi` per slot in workbench). | Brief §3.2; [create_entry.py:44](../../gateway/app/services/matrix_script/create_entry.py) `ALLOWED_TARGET_LANGUAGES`. |

This baseline is the answer to "does the 2.0 formal entry path work end-to-end on deployed?" — answer: yes, in this single observation.

### 3.2 The contract / projection slice is aligned

| Baseline check | Deployed-environment observation | Authority |
| -------------- | -------------------------------- | --------- |
| `panel_kind` resolves to `matrix_script`. | Workbench shows `Panel kind: matrix_script`. | [workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md); [projections.py:239 PANEL_REF_DISPATCH](../../gateway/app/services/operator_visible_surfaces/projections.py). |
| `line_specific_refs[]` carries the two Matrix Script Phase B refs. | Workbench renders `matrix_script_variation_matrix` + `matrix_script_slot_pack` under Line-specific panel. | Brief §0.1 criterion 4; §3.2; [packet_v1.md](../contracts/matrix_script/packet_v1.md). |
| Projection identity. | Header reads "Read-only projection of `matrix_script_workbench_variation_surface_v1`. Source: `line_specific_refs[].delta`. No vendor / model / provider controls." | [workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md). |
| §8.C deterministic Phase B truth. | Three canonical axes (`tone` / `audience` / `length`); `variation_target_count=4` cells; one slot per cell; `cells[i].script_slot_ref ↔ slots[i].slot_id` round-trip visible (`cell_001 ↔ slot_001` … `cell_004 ↔ slot_004`); `body_ref="content://matrix-script/7a407e8d00a9/slot/slot_NNN"` opaque-by-construction. | [task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §"Phase B deterministic authoring (addendum, 2026-05-03)"; [phase_b_authoring.py](../../gateway/app/services/matrix_script/phase_b_authoring.py). |
| §8.G Axes table render correctness. | `tone: formal · casual · playful`, `audience: b2b · b2c · internal`, `length: min=30 · max=120 · step=15`. No bound-method repr. | Brief §0.1 criterion 5; [task_workbench.html:298](../../gateway/app/templates/task_workbench.html). |
| §8.E shared-shell suppression. | The `kind=matrix_script` workbench surface visible in the screenshot is the header card + operator surface strip + line-specific panel slot + Matrix Script panel block. Hot Follow stage cards / pipeline summary / dub-engine selectors / Burmese deliverable strip / publish-hub CTA / debug-logs panel are not visible on this surface. | Brief §0.1 criterion 6; [workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) §"Shared shell neutrality (addendum, 2026-05-03)"; four whitelist gates at [task_workbench.html](../../gateway/app/templates/task_workbench.html) lines 176, 479, 554, 713. |

This baseline is the answer to "is the contract / projection slice aligned on deployed?" — answer: yes, in this single observation.

### 3.3 The architecture / state framework is not drifting

| Baseline check | Deployed-environment observation | Authority |
| -------------- | -------------------------------- | --------- |
| L3 publish gate semantics intact (final not yet ready). | Workbench shows `L3 PUBLISH GATE: blocked · final_missing` — i.e. the L3 publish gate correctly reports the absence of final video; this is the expected state for a freshly-created Matrix Script task that has not yet completed production. | [docs/architecture/factory_four_layer_architecture_baseline_v1.md](../architecture/factory_four_layer_architecture_baseline_v1.md) Layer 2 ready gate; [hot_follow_ready_gate.yaml](../contracts/hot_follow_ready_gate.yaml) (analogous reference). |
| Board bucket projection consistent with publish gate. | Workbench shows `BOARD BUCKET: ready` (the Matrix Script-specific board projection separate from publish gate); board view shows the task in `处理中` (processing) which is the expected pre-final state. | [projections.py:51 derive_board_publishable](../../gateway/app/services/operator_visible_surfaces/projections.py). |
| Delivery feedback projection inspect-only as expected. | Workbench "Publish feedback projection" panel shows `feedback_writeback: not_implemented_phase_b` for the delivery side; `reference_line` / `validator_report` / `ready_state` show `—` placeholders — exactly the inspect-only Delivery Center stance for Matrix Script this wave. | Brief §3.2 row "Matrix Script Delivery Center"; brief §3.3; [result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md) (Plan B B4, gated to Plan E). |
| No vendor / model / provider / engine leak on operator surface. | None visible on the workbench projection ("No vendor / model / provider controls" footer label); attribution-refs row shows `WORKER_PROFILE_REF: —` and `CAPABILITY_PLAN: —` (no donor / runtime identity exposed). | Validator R3; [projections.py:24 FORBIDDEN_OPERATOR_KEYS](../../gateway/app/services/operator_visible_surfaces/projections.py); [projections.py:36 sanitize_operator_payload](../../gateway/app/services/operator_visible_surfaces/projections.py). |
| Cross-line board renders three lines side-by-side without re-deriving Matrix Script publishability via Hot Follow paths. | Board shows the Matrix Script task `7a407e8d00a9` ("越南已经有人用AI赚钱了") in `处理中` alongside other lines' tasks; the Bucket filter (`All` / `Blocked` / `Ready` / `Publishable`) is intact. | Brief §3.2 row "Cross-line `/tasks` Board inspection"; alignment map §4.1–§4.3. |

This baseline is the answer to "is the architecture / state framework drifting on deployed?" — answer: no drift visible in this single observation.

## 4. What this evidence does NOT claim (binding)

- **Does NOT claim Plan A live-trial complete.** §7.1 Samples 1 / 2 / 4 / 5 / 6 are out of scope of this note. Plan A live-trial closure remains the human ops team's deliverable per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §0 and [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) §0.
- **Does NOT claim §12 conditions all hold.** This note does not certify the eight pre-conditions in brief §12; coordinator owns that certification.
- **Does NOT claim operator-workspace completion.** Operator usability, end-to-end operator workflow legibility, and trial-environment hygiene are explicitly out of scope per the user instruction grounding this note.
- **Does NOT claim delivery-loop completion.** Delivery Center for Matrix Script remains inspect-only this wave; `feedback_writeback: not_implemented_phase_b` is by design and is gated to Plan E by [result_packet_binding_artifact_lookup_contract_v1](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md).
- **Does NOT propose a UI patch.** The user instruction explicitly forbids reopening UI patching from current observations. No file under `gateway/app/templates/` or `gateway/app/static/` is modified or recommended for modification by this note.
- **Does NOT unblock Plan E.** Plan E pre-condition #1 (per brief §9.1) is still gated on the live-run §8 entries plus coordinator/architect/reviewer signoff. This note is one input, not a substitute.
- **Does NOT modify [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), or [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).** Wave-state truth stays where it is.

## 5. Net role in the gate-closing minimal trial

Per the user instruction, Plan A continues only as a **minimal gate-closing trial** to prove 2.0 architecture / state alignment so the project can move to the next gate cleanly. Within that minimal scope:

- This note records the contract / projection baseline observed at HEAD `b0c61c0` on the deployed environment for one Matrix Script task `7a407e8d00a9` on 2026-05-03.
- The remaining minimal-trial obligations (per brief §7.1 + §12 + alignment map §7.1 deliverable) are unchanged:
  1. Coordinator confirms the eight §12 conditions in the trial environment.
  2. Operations team executes the §7.1 sample wave in order in the deployed environment.
  3. Coordinator fills [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) with real metadata + per-sample observations + signoff.
  4. Filled live-run entries are appended to [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 placeholder.
  5. Architect + reviewer sign off after coordinator signoff.
  6. Plan E gate spec is then authored as a separate review document.

This baseline-evidence note can be cited by the coordinator at step 3 / 4 as supporting material for the Matrix Script Sample 3 row, but it does not pre-fill the §8 placeholder and does not substitute for the coordinator's structured fill-in.

## 6. Validation

Per [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 and §11:

1. **Authority alignment.** Every baseline-evidence row in §3 traces to a frozen contract, the trial brief by section, the trial coordination write-up by section, or a deployed-branch anchor verified by [PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md](PLAN_A_PRE_TRIAL_AUTHORITY_AUDIT_v1.md). No new contract / schema / packet / runtime semantics are authored.
2. **No scope expansion.** The note remains inside the three baseline questions named in §0. It does not author a UI patch decision, an operator-workspace verdict, a delivery-loop verdict, a §7.1 wave-completion verdict, a §12 condition certification, or a Plan E gate decision.
3. **No truth-source overwrite.** The note does not modify the brief, the write-up, or any contract / engineering-status file. It is additive evidence only.
4. **No private memory / parallel state.** The file lives under `docs/execution/`, the native execution-evidence directory; no off-index cognition file is created.
5. **No reopening of §8.A → §8.H.** The note cites those corrections as authority and as the basis for the baseline checks; it does not propose modification to any of them.

## 7. What the AI agent did NOT do for this note (binding)

- Did **not** patch UI; did **not** propose a UI patch.
- Did **not** fill [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md); did **not** synthesize per-sample fields; did **not** invent coordinator / operator names or signoff.
- Did **not** modify [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md); did **not** append to its §8 placeholder.
- Did **not** author a `PLAN_A_POST_TRIAL_GATE_REVIEW_v1.md` or any review-tier document.
- Did **not** modify [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), or any wave-state file.
- Did **not** open Plan E preparation; did **not** advance the wave gate.
- Did **not** reopen any §8.A → §8.H correction.
- Did **not** reopen Hot Follow business behavior, Matrix Script frozen contracts, or Digital Anchor frozen Phase A–D.0 contracts.
- Did read the project owner's screenshots and recorded only the contract / projection baseline observations narrowly framed by §0.

## 8. Final state

- **Contract / projection baseline aligned in deployed environment as of 2026-05-03 (HEAD `b0c61c0`):** YES (one observation, narrow scope per §0).
- **Plan A live-trial completion:** UNCHANGED — still gated on coordinator-monitored §7.1 wave + signoff per brief / write-up / capture template.
- **Plan E gate spec authoring:** UNCHANGED — still gated on Plan A live-trial completion.
- **Runtime Assembly:** BLOCKED.
- **Capability Expansion:** BLOCKED.
- **Frontend patching:** BLOCKED (and explicitly not reopened by this note).

End of Plan A contract / projection baseline evidence note.
