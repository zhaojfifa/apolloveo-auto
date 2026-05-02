# Matrix Script §8.D Operator Brief Correction — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, item §8.D)
Status: documentation correction green; ready for signoff
Authority:
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) §8.D
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (operator-facing trial brief; this change corrects it)
- [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) (trial coordination write-up; this change adds the §11 §8.D addendum)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed; PASS)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed; PASS)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed; PASS)
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with §8.A and §8.C addenda already landed; not modified by §8.D)
- [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md) (Plan B B4; explains the inspect-only Delivery Center boundary that §8.D preserves)
- [docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md](../contracts/matrix_script/publish_feedback_closure_contract_v1.md) (Phase D.0 freeze + Phase D.1 minimal write-back; preserved by §8.D)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation, §11 Scope Control
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the standing
execution discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
[PROJECT_RULES.md](../../PROJECT_RULES.md), and
[docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this work is:

- engineering rules / current focus / status / constraints index;
- docs index;
- the §8.A / §8.B / §8.C landed logs (so §8.D's correction reflects
  exactly the accepted post-correction state — entry-form ref-shape
  guard in force, panel dispatch confirmed, deterministic Phase B
  authoring in force);
- the trial readiness plan (current operator brief authority — this
  change's primary subject);
- the Plan A trial coordination write-up (static-pass coordinator
  runbook authority — this change adds an §11 §8.D addendum);
- the matrix_script frozen contracts (the Plan B B4 `result_packet_binding`
  contract pinning the inspect-only Delivery Center boundary, the
  Phase D.0 publish-feedback closure contract pinning the closure-shape
  boundary, the §8.A / §8.C addenda on `task_entry_contract_v1`);
- the blocker review §8.D requirements and §9 hard red lines.

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

This change implements **only** §8.D from the Matrix Script trial blocker
review: a documentation correction to the operator-facing trial brief so
that Matrix Script trial scope, valid-sample rules, inspect-only
boundaries, and the status of the old broken sample are all explained
accurately and aligned with the accepted §8.A / §8.B / §8.C results.
Items §8.A (entry-form ref-shape guard — landed), §8.B (panel-dispatch
confirmation — confirmed, no narrow fix required), and §8.C (Phase B
deterministic authoring — landed) are out of scope and remain as already
accepted.

### 2.1 What this change adds

- A binding §0.1 "Matrix Script Trial Sample Validity (post-§8.A / §8.B / §8.C)"
  section at the top of [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
  enumerating: the old broken sample is invalid evidence; what counts as
  a fresh corrected sample (formal POST + opaque ref + populated Phase B
  deltas + correct workbench mount); the workbench is now inspectable for
  real packet truth; Delivery Center remains inspect-only; Phase D.1
  closure surface is unchanged; operators MUST NOT report inspect-only /
  contract-only surfaces as defects.
- Corrected §3.1 "Trial-eligible lines" Matrix Script row that now cites
  §8.A / §8.B / §8.C explicitly and points operators at the formal
  `/tasks/matrix-script/new` POST as the only acceptable sample-creation
  path.
- Corrected §3.2 "Trial-eligible surfaces" rows for the create-entry form
  (now mentions the §8.A guard), the Workbench panel (now mentions §8.B
  dispatch confirmation and §8.C populated deltas), and the Delivery
  Center (now explicitly notes §8.A / §8.B / §8.C did not promote it
  beyond inspect-only).
- Corrected §3.3 "Surfaces operators may inspect but not operate" with
  the Phase B variation panel inspection boundary and the Delivery
  Center inspect-only restatement.
- Corrected §5.2 Workbench operator explanation 口径 with the Matrix
  Script panel mount details and a coordinator note explaining the
  empty-fallback message as a "prior invalid sample" indicator.
- Corrected §6.2 Matrix Script line-by-line guidance: trial scope refined
  to the fresh contract-clean sample only; sample profile now explicitly
  enumerates the §8.A guard's accepted ref shapes, the §8.C deterministic
  axes, and the round-trip rule; confidence raised to "high for entry-shape,
  panel-mount, and Phase B inspection" while keeping "low for end-to-end
  Delivery"; operator-misuse list expanded to cover old-sample reuse,
  legacy-path submission, deterministic-axes misreporting, and Delivery
  Center placeholder misreporting.
- Corrected §7.1 first-wave samples: sample 3 rewritten to the fresh
  contract-clean profile with explicit goals (a)–(d); samples 4 and 5
  retained / refined; new sample 5 added for variation-count boundary
  check at k=1 and k=12 (the validated `_variation_count` bounds per
  `create_entry.py`).
- Corrected §7.2 samples-to-avoid list: added bans on pre-§8.A reuse,
  legacy `/tasks/connect/matrix_script/new` path, and operator-authoring
  expectation on the Phase B panel.
- Expanded §8 risk list with five new rows specific to §8.A / §8.B / §8.C
  consequences (body-text paste, old-sample reuse, empty-fallback
  observation, deterministic-axes misreport, legacy-path submission,
  panel-authoring expectation).
- Added §11.1 "Matrix Script Plan A trial corrections — landed updates"
  history block in the operator brief.
- Updated §12 Final Readiness Conclusion with the §8.A / §8.B / §8.C / §8.D
  PASS gate row and an additional condition #6 binding Matrix Script
  trial samples to the §0.1 sample-validity rule.
- Added §11 "Matrix Script Plan A Trial Corrections — Addendum (2026-05-03)"
  to [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md)
  with the why-the-original-sample-was-invalid restatement, the trial
  corrections landed-status table, the static-pass overlay for the
  Matrix Script rows, the coordinator action items added by §8.D, and
  the final corrected coordinator judgment.
- This execution log.
- Standing repo guidance writeback.

### 2.2 What this change does NOT add

- no runtime behavior change (no `.py`, no `.html`, no `.json` schema /
  sample / packet edit);
- no contract change (no edits to any `docs/contracts/**` file —
  including the §8.A and §8.C addenda on `task_entry_contract_v1`);
- no router / service / template / projector / wiring code change;
- no widening of `PANEL_REF_DISPATCH`;
- no schema / sample / packet re-version;
- no test additions or modifications;
- no §8.A / §8.B / §8.C reopening;
- no workbench redesign;
- no contract-truth alteration unless wording-alignment-only;
- no Hot Follow / Digital Anchor scope reopening;
- no Runtime Assembly / Capability Expansion entry;
- no provider / model / vendor / engine controls;
- no Plan B B4 (`result_packet_binding`), Plan D D1 (`publish_readiness`),
  D2 (`final_provenance`), D3 (panel-dispatch-as-contract-object), or
  D4 (advisory producer) implementation — all remain Plan E gated;
- no second production line onboarding;
- no Asset Library / promote (Plan C C1–C3) work;
- no live-trial execution (operations team appends live-run results to
  PLAN_A_OPS_TRIAL_WRITEUP_v1.md §8 separately).

## 3. Doc Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| Add §0.1 binding sample-validity rule; refresh authority list with §8.A / §8.B / §8.C / §8.D logs and the trial blocker review; correct §3.1 Matrix Script row; correct §3.2 create-entry / Workbench / Delivery rows; correct §3.3 inspect-only list; correct §5.2 Workbench explanation 口径 with empty-fallback coordinator note; correct §6.2 Matrix Script line-by-line guidance; correct §7.1 first-wave samples; correct §7.2 samples-to-avoid; expand §8 risk list with five new Matrix Script-specific rows; add §11.1 trial-corrections landed-history block; correct §12 Final Readiness Conclusion. | [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) | EDIT |
| Update front-matter date / status / authority list to cite the §8.A / §8.B / §8.C / §8.D landed execution logs and the blocker review; append §11 "Matrix Script Plan A Trial Corrections — Addendum (2026-05-03)" with §11.1 why-original-was-invalid, §11.2 trial-corrections landed-status table, §11.3 static-pass overlay, §11.4 coordinator action items, §11.5 final corrected coordinator judgment. | [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) | EDIT |
| This execution log. | [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback (Current Completion row added; Allowed Next Work row referencing §8.D landed; Recommended Next Direction left intact). | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) | EDIT |
| Standing repo guidance writeback (Current Main Line row updated to reflect §8.D landed; CLAUDE.md absence reaffirmed by reference to ENGINEERING_RULES.md and this focus file). | [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) | EDIT |
| Append §"Plan A Trial Correction §8.D — Operator Brief Correction" row mirroring the §8.A / §8.B / §8.C row style; cite the §8.D execution log + the operator brief / coordinator write-up edits; restate hard-red-lines observance. | [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md) | EDIT |
| Add Plan A Trial Correction §8.D rows pointing at the new execution log and the corrected operator brief / coordinator write-up. | [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

No `.py`, no `.html`, no schema, no sample, no contract, no test file
was modified. No router / service / template / projector / wiring code
edit. No new line-specific logic anywhere. The change is documentation-
only, as the §8.D blocker-review brief explicitly requires.

## 4. Validation Evidence

This is a documentation-only change; validation is documentary. Per
`ENGINEERING_RULES.md` §10, the validation discipline is "no merge
without required regression" — documentation-only changes have no
runtime regression to run. The §8.A / §8.B / §8.C suites remain green
on baseline `9f25b89` and are not affected by this change (no code
edited). Runtime behavior is byte-for-byte identical to the §8.C
baseline.

### 4.1 Required validation per §8.D brief — mapped to evidence

| Required validation | Evidence |
| ------------------- | -------- |
| Operator brief now matches the accepted §8.A / §8.B / §8.C conclusions. | [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 enumerates the post-correction state explicitly: §8.A guard in force on `source_script_ref`; §8.B panel-dispatch confirmed; §8.C populated `variation_matrix.delta` (3 canonical axes — `tone` / `audience` / `length` — and `variation_target_count` cells) and `slot_pack.delta` (one slot per cell) author-time; round-trip resolves; rendered HTML carries real axes / cells / slots. §3.1 / §3.2 / §3.3 / §5.2 / §6.2 / §7.1 / §7.2 / §8 / §11.1 / §12 rows each cite the relevant §8.A / §8.B / §8.C execution log or the contract addenda those changes added. |
| Valid vs invalid Matrix Script trial sample criteria are explicit. | §0.1 enumerates the four conditions a sample must satisfy to qualify (formal POST path; opaque `source_script_ref` per §8.A's accepted scheme set; populated Phase B deltas per §8.C; mounted Matrix Script Phase B variation panel rendering real axes / cells / slots per §8.B + §8.C). The "old broken sample remains invalid" rule is restated in §0.1, §6.2 operator-misuse list, §7.2 samples-to-avoid list, and §8 risk list. |
| No operational promise exceeds current gate status. | §3.2 row "Delivery Center — Matrix Script" stays "Inspect-only"; §6.2 confidence row stays "low for end-to-end Delivery"; §3.3 keeps the inspect-only enumeration; §4.2 (untouched) keeps the Plan E gate enumeration; §0.1 explicitly states Phase D.1 closure surface boundary is unchanged; §12 keeps Plan E "BLOCKED — READY WITH CONDITIONS"; Runtime Assembly / Capability Expansion / Frontend patching all stay "BLOCKED". The only status promotions are the §8.A / §8.B / §8.C / §8.D PASS rows in §12 — and those are landed gates, not promises. |
| No stale wording remains that still describes Matrix Script as empty-shell / no-Phase-B-truth. | The original "create-entry shipped (`4896f7c`); workbench panel render shipped (`b370e46`)" framing in §3.1 was replaced with explicit §8.A / §8.B / §8.C citations and the "fresh samples now carry populated `variation_matrix.delta` and `slot_pack.delta`" statement. The original "Read-only projection of `line_specific_refs[matrix_script_variation_matrix/slot_pack].delta`" phrasing in §3.2 was preserved (still factually correct) **and** extended with §8.B dispatch + §8.C populated-delta language. The §6.2 sample profile "2–3 axis × 4–6 slot" phrasing was replaced with the §8.C deterministic-authoring shape (3 canonical axes + `variation_target_count` cells). The §7.1 sample 3 "2 axes × 4 slots" shorthand was rewritten to the fresh contract-clean profile. The Plan A coordination write-up §4 sample 3 entry's stale shorthand is acknowledged in the §11.3 overlay and superseded by the trial brief's §6.2 / §7.1. |
| No repo guidance / status file is left stale. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), and [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) are all updated by this change to reference the §8.D landed status. The `CLAUDE.md` absence and the standing-rule fallback are reaffirmed in §1 of this log and in the §8.A / §8.B / §8.C logs (unchanged). |

### 4.2 Cross-checks performed

- **Operator brief vs §8.A execution log §3 "Closed Accepted Shape":** the brief's §3.2 / §6.2 ref-shape enumeration matches the closed scheme set (`content`, `task`, `asset`, `ref`, `s3`, `gs`, `https`, `http`) and envelope rules (single line, no whitespace, ≤512 chars) verbatim.
- **Operator brief vs §8.B execution log §3.2 / §3.3:** the brief's §3.2 / §0.1 dispatch markers (`panel_kind="matrix_script"`, `data-role="matrix-script-variation-panel"`, `data-panel-kind="matrix_script"`, projection name `matrix_script_workbench_variation_surface_v1`) match the captured render markers in §5.3 of the §8.B log verbatim.
- **Operator brief vs §8.C execution log §4.5 "Live end-to-end render evidence":** the brief's §6.2 sample profile lists 3 canonical axes (`tone` / `audience` / `length`), `variation_target_count` cells, one slot per cell, and the opaque `body_ref` template `content://matrix-script/{task_id}/slot/{slot_id}` — all consistent with the §8.C planner output and the live captured evidence.
- **Operator brief vs §8.C contract addendum on `task_entry_contract_v1`:** the brief's §6.2 deterministic-axes warning ("operators MUST NOT report `tone` / `audience` / `length` as a defect — they are the authored canonical axes per §8.C's contract addendum") matches the addendum's pinned canonical-axes table.
- **Operator brief vs Plan B B4 contract:** the brief's §3.2 / §3.3 / §6.2 / §0.1 Delivery Center inspect-only rows preserve the Plan B B4 / `result_packet_binding_artifact_lookup_contract_v1` boundary (`not_implemented_phase_c` placeholders; code change gated to Plan E).
- **Operator brief vs Phase D.1 publish-feedback closure boundary:** the brief's §0.1 Phase D.1 statement preserves the existing closure-shape boundary per `publish_feedback_closure_contract_v1` and the Phase D.1 minimal write-back already shipped (per `MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md` §"Phase D.1"). §8.D does not promote, mutate, or expand this boundary.
- **Coordinator write-up §11 addendum vs the operator brief:** the §11.3 static-pass overlay is consistent with the brief's §0.1 / §3.2 / §6.2; the §11.4 coordinator action items reference the brief's §0.1 / §6.2 verbatim; the §11.5 final corrected coordinator judgment matches the brief's §12 final readiness conclusion.

### 4.3 Pre-existing environment limitation

`gateway/app/services/tests/test_task_repository_file.py::test_op_download_proxy_uses_attachment_redirect_for_final_video`
was recorded as an environment limitation in the §8.A / §8.B / §8.C
execution logs per `ENGINEERING_RULES.md` §10. §8.D adds no code; it
neither introduces nor affects this failure. No test run is required for
a documentation-only change.

## 5. Contract Alignment Check

- `task_entry_contract_v1` (with §8.A and §8.C addenda): respected. §8.D
  does not modify the contract; it only ensures the operator-facing
  brief consumes the contract truth correctly.
- `result_packet_binding_artifact_lookup_contract_v1` (Plan B B4):
  respected. The brief preserves the inspect-only / `not_implemented_phase_c`
  boundary that this contract pins.
- `publish_feedback_closure_contract_v1` (Phase D.0 freeze): respected.
  The brief preserves the closure-shape boundary; §8.D does not promote
  Phase D.1 beyond the existing minimal write-back.
- `workbench_variation_surface_contract_v1`: respected. The brief
  preserves the read-only boundary on the Phase B panel; the §3.3 /
  §6.2 statements explicitly note the panel does not author or mutate
  axes / cells / slots on operator command.
- `workbench_panel_dispatch_contract_v1`: respected. The brief consumes
  the dispatch truth confirmed by §8.B (`panel_kind="matrix_script"`)
  without proposing any change to `PANEL_REF_DISPATCH`.
- `slot_pack_contract_v1` §"Forbidden": respected. The brief reaffirms
  the opaque `body_ref` rule — operators are explicitly told `body_ref`
  is opaque and is not the operator-supplied `source_script_ref`.
- `tasks.py` / `task_view.py` / `hot_follow_api.py`: untouched. No code
  change anywhere.
- No new vendor / model / provider / engine identifier introduced.
- No second source of task or state truth introduced. The brief remains
  consumer-side documentation only.

## 6. Final Gate

- **§8.D: PASS.** Operator brief at [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) and trial coordination write-up at [docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) corrected; valid vs invalid Matrix Script trial sample criteria explicit (§0.1); inspect-only / contract-only boundaries preserved; stale empty-shell / no-Phase-B-truth language removed; repo guidance / status writeback complete.
- **Plan A Matrix Script brief corrected: YES.**
- **Old invalid sample remains invalid: YES** (per blocker review §9 and §8.A's PASS gate; §8.D codifies the rule in the operator brief §0.1, §6.2, §7.2, §8).
- **Fresh corrected Matrix Script retry sample fully briefed: YES** (per the operator brief §0.1 sample-validity criteria, §3.1 / §3.2 row backing, §6.2 sample profile, and §7.1 sample 3 explicit goals (a)–(d)).
- **Ready for Matrix Script retry sample creation: YES** (operations team may proceed with §7.1 sample 3 / 4 / 5 / 6 once the §11.4 coordinator action items in the trial coordination write-up are completed; live-run results append to `PLAN_A_OPS_TRIAL_WRITEUP_v1.md` §8 by the operations team, separately).

## 7. Hard Red Lines (re-stated, observed)

This change observes every red line restated by the blocker review §9
and the wave authority:

- Hot Follow scope: not reopened.
- Platform Runtime Assembly / Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake populated axes / cells / slots — the
  brief consumes §8.C's real authored deltas as truth, not as a UI
  mock.
- Workbench redesign: no.
- Per-line workbench template: not added.
- `source_script_ref` contract: unchanged (§8.A's addendum stands as-is;
  §8.C's addendum stands as-is; §8.D adds no contract addendum).
- Delivery Center for Matrix Script: still inspect-only; brief preserves
  the boundary.
- Phase D.1 publish-feedback closure: unchanged from existing minimal
  write-back; brief preserves the boundary.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.
- `tasks.py` / `task_view.py` / `hot_follow_api.py`: untouched.
- Old invalid sample: not promoted; remains invalid evidence per §0.1.
- Asset Library / promote (Plan C C1–C3): not entered.
- Plan E gated items (B4 `result_packet_binding`, D1 `publish_readiness`,
  D2 `final_provenance`, D3 panel-dispatch-as-contract-object,
  D4 advisory producer, Digital Anchor B1 / B2 / B3 implementation):
  not implemented.
- `g_lang` token alphabet: not pinned in this PR (separate review).
- `.py`, `.html`, schema, sample, contract: all untouched per the
  documentation-only scope.
- Repo read/write discipline: unchanged. The standing instruction lives
  in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md` /
  `ENGINEERING_STATUS.md` / `ENGINEERING_CONSTRAINTS_INDEX.md` /
  `docs/ENGINEERING_INDEX.md`; this change does not modify those files'
  reading-order or status-trail discipline rules — it only updates the
  status / focus rows that §8.D landing implies.

End of v1.
