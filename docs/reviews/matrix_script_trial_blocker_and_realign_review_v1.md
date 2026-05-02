# Matrix Script Trial Blocker and Realign Review v1

Status: BLOCKING — Plan A live-run evidence collection on the current Matrix
Script sample is suspended pending the correction items in §8.

Authority: ApolloVeo 2.0 Chief Architect, under
`CURRENT_ENGINEERING_FOCUS.md` (Factory Alignment Review Gate active) and
`docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (Operator-Visible Surface
Validation Wave).

Date: 2026-05-02.

---

## 1. Executive Conclusion

The current Matrix Script task is **invalid trial evidence**. The default
judgment ("invalid until proven otherwise") is confirmed.

The framing "the formal Matrix Script entry path was bypassed and script body
was smuggled through `source_url`" is **partially wrong**. The formal entry
path was used. The deterministic mapping inside the formal payload-builder
placed `source_script_ref` into the legacy task-table column `source_url`
exactly as written in `gateway/app/services/matrix_script/create_entry.py:144`
— that column is the contract-correct destination for the opaque ref handle.
The reason the resulting task is unusable as trial evidence is *not* path
bypass. It is two distinct gaps:

1. **Entry-form discipline gap.** The form accepts a free `<textarea>` for
   `source_script_ref` with no ref-shape validation, so an operator can paste
   raw script body where the contract requires an opaque reference. The
   payload-builder then carries that body verbatim into `source_url` and into
   `packet.config.entry.source_script_ref`, violating
   `task_entry_contract_v1` semantics and the no-body-embedding rule of
   `slot_pack_contract_v1`.
2. **Empty packet truth.** The payload-builder seeds
   `packet.line_specific_refs[]` only with **pointers to the contract docs**
   for `matrix_script_variation_matrix` and `matrix_script_slot_pack`. There
   is no Phase B authoring/planning capability in this wave that converts the
   `source_script_ref` into populated `axes[] / cells[] / slots[]` deltas.
   The Phase B render surface has nothing to render, so axes / cells / slots
   present as empty by construction — this is exactly the integrity-warning
   branch that `workbench_variation_surface_contract_v1` permits.

Two of the seven observed facts are **by design for this wave** and were
mis-labelled as defects in the trigger brief: Delivery Center is
inspect-only per Plan A §3.2, and Phase D publish-feedback closure write-back
is contract-only per `publish_feedback_closure_contract_v1` (Phase D.0 freeze,
no implementation in this wave).

Trial: **BLOCKED**. Current sample: **DO NOT continue**. Fresh sample:
**YES**, but only after §8.A and §8.C land and §8.B is confirmed.

## 2. Reading Declaration

Standard repo-entry discipline followed.

Authority surface consulted:

- Stage / focus
  - [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — Factory Alignment Review Gate active; broad shell import, generic platform build, second-line onboarding, and provider/model/vendor controls forbidden in current scope.
- Plan A trial scope (current wave authority)
  - [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- Latest gap review and ops plan
  - [docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md](operations_upgrade_gap_review_and_ops_plan_v1.md)
  - [docs/reviews/operator_visible_surface_wiring_feasibility_v1.md](operator_visible_surface_wiring_feasibility_v1.md)
- Matrix Script frozen contracts (Phase A–D)
  - [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md)
  - [docs/contracts/matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md)
  - [docs/contracts/matrix_script/variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md)
  - [docs/contracts/matrix_script/slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md)
  - [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md)
  - [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md)
  - [docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md](../contracts/matrix_script/publish_feedback_closure_contract_v1.md)
  - [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md)
- Cross-line dispatch authority
  - [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- Implementation surface inspected (read-only)
  - [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py)
  - [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html)
  - [gateway/app/routers/tasks.py:614](../../gateway/app/routers/tasks.py:614)
  - [gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py)
  - [gateway/app/services/matrix_script/delivery_binding.py:93](../../gateway/app/services/matrix_script/delivery_binding.py:93)
  - [gateway/app/services/matrix_script/publish_feedback_closure.py](../../gateway/app/services/matrix_script/publish_feedback_closure.py)

Recent commits considered: `8c5130d` (Plan A trial coordination write-up v1),
`6052014` (worktree wave merge), `54ede3b` (Plan B/C/D contract freeze),
`05830ae` (Operations Upgrade gap review), `b370e46` (Phase B variation
surface render in workbench panel), `4896f7c` (formal `/tasks/matrix-script/new`
create-entry — referenced by gap review §4).

## 3. Observed Invalid Trial Sample

The trigger brief reports the following observed facts. Each is now
classified by true cause:

| # | Observed fact | True cause class |
|---|---|---|
| 1 | Script body was passed through `source_url` | (II) Form-discipline failure — operator pasted body into a textarea with no ref-shape validator; builder mapped it deterministically per `create_entry.py:144` |
| 2 | Workbench is still the generic engineering shell | (III) Panel-dispatch failure pending route confirmation — Phase B render code exists at `workbench_variation_surface.py` (`b370e46`); needs verification that `/tasks/{id}` for `kind=matrix_script` reaches it |
| 3 | `variation_matrix` did not resolve | (II) Form/wave-item gap — packet seeds only a contract-doc pointer; no LS1 delta payload was authored |
| 4 | `slot_pack` did not resolve | (II) Form/wave-item gap — packet seeds only a contract-doc pointer; no LS2 delta payload was authored |
| 5 | axes / cells / slots are empty | (II) Direct consequence of #3/#4; `workbench_variation_surface_contract_v1` integrity-warning branch is the contractually correct render |
| 6 | Publish feedback is placeholder-level | (I) **By design this wave** — `publish_feedback_closure_contract_v1` is a Phase D.0 contract-only freeze; write-back implementation is explicitly NOT in this wave |
| 7 | Delivery is not operator-usable | (I) **By design this wave** — Plan A §3.2 declares Matrix Script Delivery Center inspect-only; `delivery_binding.py:93` still emits the contract-pinned `not_implemented_phase_c` placeholder rows |

Class (I) findings are **not defects against the wave**; they signal an
operator-brief defect (see §8.D). Class (II) and (III) findings are the real
blockers.

## 4. Entry-Path Trace

### Expected formal path

operator opens `/tasks/matrix-script/new`
→ HTML form (`matrix_script_new.html`) collects the closed required field set
  (`topic`, `source_script_ref`, `language_scope`, `target_platform`,
  `variation_target_count`) per `task_entry_contract_v1`
→ POST handler at `gateway/app/routers/tasks.py:614` parses the form
→ calls `create_entry.build_matrix_script_task_payload(...)`
→ payload normalised by `normalize_task_payload(...)`
→ task row persisted with `kind = "matrix_script"`; `packet.line_id =
  "matrix_script"`; `packet.line_specific_refs[]` carries
  `matrix_script_variation_matrix` and `matrix_script_slot_pack`
→ operator navigates to `/tasks/{task_id}`
→ workbench panel-dispatch (`workbench_panel_dispatch_contract_v1`)
  routes `kind=matrix_script` to the line-specific Phase B variation panel
  (`workbench_variation_surface.py`, projection
  `matrix_script_workbench_variation_surface_v1`)
→ operator inspects axes/cells/slots and exercises Phase D closure surface
  (closure surface render only — write-back is contract-only this wave)
→ Delivery Center is inspect-only; rows are `not_implemented_phase_c`
  placeholders by Plan B contract.

### Actual path used

The same path. There is **no evidence of a payload-builder bypass**. The
formal handler at `tasks.py:614` was invoked, the formal builder at
`create_entry.py:114-202` ran, and the packet was seeded with the line_id and
the two `line_specific_refs[]` pointers.

What actually happened to the script body:

- the operator typed/pasted body text into the `<textarea
  name="source_script_ref">` at `matrix_script_new.html:161-162`
- the handler accepted it as `source_script_ref: str = Form(...)` with no
  shape check
- `create_entry.py:144` mapped it deterministically to `payload["source_url"]`
  (the legacy task-table column) and `create_entry.py:155` mirrored it into
  `packet.config.entry.source_script_ref`
- `packet.line_specific_refs[]` was seeded only with contract-doc pointers
  (lines 172–185 and 187–200) — no `axes[] / cells[] / slots[]` deltas were
  produced because no capability in this wave produces them.

### Divergence point

Three concrete loci:

a. **`matrix_script_new.html:161-162`** — `<textarea>` with prose
   placeholder "粘贴脚本文本、文档链接或内容引用编号" (paste script text, doc
   link, or content ref ID) explicitly invites body content into a field that
   the contract defines as an opaque ref. There is no `pattern`, no
   `maxlength`, no inline help that distinguishes ref vs body.
b. **`create_entry.py` `_normalise_entry`** — there is no
   `_validate_ref_shape(...)` or equivalent guard that refuses
   `source_script_ref` values that look like prose body (multi-line, no
   scheme, exceeds a sane ref length). `_require(...)` only checks
   non-emptiness.
c. **Packet authoring gap** — `build_matrix_script_task_payload` stops at
   pointer skeletons. There is no Phase B planning/authoring capability that
   converts `source_script_ref` into populated `matrix_script_variation_matrix`
   and `matrix_script_slot_pack` deltas. The render surface therefore renders
   empty/integrity-warning by construction.

## 5. Product-Line Requirement Mismatch

### Task creation

Contract: `task_entry_contract_v1` requires `source_script_ref` as an opaque
ref handle; absence MUST block creation; provider/model/vendor and
status-shape fields forbidden.

Runtime: closed required-set check, language enum, `variation_target_count`
all enforced (`create_entry.py:96-98, 22-29, 31-37`). **However**, no
ref-shape check on `source_script_ref` — operator-supplied prose body is
accepted as if it were a ref.

Verdict: **MISMATCH on ref semantics; aligned on field set.**

### Workbench model

Contract: line-specific Phase B variation surface
(`workbench_variation_surface_contract_v1`) is the projection an operator
sees for `kind=matrix_script`; generic engineering shell is not the workbench
truth for this line. Panel routing is governed by
`workbench_panel_dispatch_contract_v1`.

Runtime: Phase B render code exists (`workbench_variation_surface.py`, commit
`b370e46`). The trigger brief reports the operator landed on the generic
shell. Either the panel-dispatch did not route `kind=matrix_script` to the
Phase B panel for this task, or it did and the operator misidentified the
panel because empty axes/cells/slots made it look generic.

Verdict: **MISMATCH pending route trace** (§8.B).

### Variation model

Contract: `variation_matrix_contract_v1` requires `axes[] / cells[]` with
round-trip resolution into `slot_pack_contract_v1.slots[]`; `body_ref` MUST
be opaque and MUST NOT embed body text.

Runtime: LS1/LS2 are pointer skeletons only; no axes/cells/slots ever
existed for this task; if body text is parked in `source_script_ref`, it is
also pointed at by `body_ref` semantics in any future authoring step, which
would be a `slot_pack_contract_v1:44` violation if not corrected upstream.

Verdict: **RUNTIME MISMATCH; CONTRACT ALIGNED.** The wave-item to populate
LS1/LS2 is missing or has not yet been exercised on this sample.

### Delivery model

Contract: `delivery_binding_contract_v1` is five projection rows; the rows
"do not prove artifact existence, freshness, publishability, or final
delivery readiness"; state-shape fields like `delivery_ready` /
`publishable` / `final_ready` are forbidden.
`result_packet_binding_artifact_lookup_contract_v1` resolves the
`not_implemented_phase_c` placeholder at the spec surface only — code change
is gated to Plan E.

Runtime: `delivery_binding.py:93-125` still emits the five
`not_implemented_phase_c` placeholder rows. This is exactly what Plan A §3.2
declared "inspect-only" for Matrix Script trial.

Verdict: **NOT a mismatch.** Treating it as a defect is an operator-brief
miscalibration.

## 6. Contract Alignment Check

### Respected contracts

- `task_entry_contract_v1` — closed required field set, language enum
  restriction (`mm`, `vi`), forbidden fields not introduced.
- `packet_v1` — `line_id`, `packet_version`, `line_specific_refs[]`
  scaffolding seeded.
- `workbench_variation_surface_contract_v1` — render code exists, projection
  name `matrix_script_workbench_variation_surface_v1` (commit `b370e46`).
  Contract permits inline integrity warnings on unresolved refs without
  mutating `evidence.ready_state` — and that is exactly what the empty
  axes/cells/slots condition would render.
- `delivery_binding_contract_v1` — five-row placeholder shape preserved; no
  state-shape fields introduced.
- `publish_feedback_closure_contract_v1` — Phase D.0 contract-only posture
  observed; no packet/entry/workbench/delivery mutation in the wave.
- `result_packet_binding_artifact_lookup_contract_v1` — Plan B contract-only
  posture observed; `not_implemented_phase_c` placeholder unchanged at the
  code level.

### Bypassed / violated contracts

- `task_entry_contract_v1` semantic on `source_script_ref` — opaque-ref
  requirement bypassed at the form/handler layer (no ref-shape guard); body
  text accepted as a ref value.
- `slot_pack_contract_v1:44` ("`body_ref` MUST be opaque … pack does not
  embed body text") — bypassed transitively: any later authoring step on this
  sample would carry the body text into `body_ref`. The violation is staged,
  not yet realised, because the authoring step did not run.

### Missing runtime reflection

- Phase B *authoring/planning* of LS1/LS2 deltas. The contracts for
  `matrix_script_variation_matrix` and `matrix_script_slot_pack` are frozen,
  the Phase B *render* surface is landed, but **no capability in this wave
  produces the deltas from `source_script_ref`**. Without that capability or
  an explicit fixture-LS-delta policy (§8.C), the Phase B render surface has
  nothing to render and Plan A trial cannot produce evidence.

## 7. Why This Task Is Not Valid Trial Evidence

1. **`source_script_ref` carries body, not a ref.** This violates entry
   semantics; any downstream authoring against this packet would compound the
   violation. A trial sample cannot validate operator-visible surfaces while
   the seed value is contract-invalid.
2. **Packet truth is empty.** LS1/LS2 hold contract-doc pointers, not deltas.
   Axes / cells / slots cannot resolve because they were never produced.
3. **Workbench surface had nothing to render.** Whether or not panel-dispatch
   reached the Phase B panel, the render result is indistinguishable from "no
   panel" without populated deltas. The sample cannot demonstrate the
   operator path.
4. **Generic-shell observation is unconfirmed but plausible.** If
   panel-dispatch did not route `kind=matrix_script`, the operator-visible
   surface contract is broken in code; if it did, the operator could not
   tell, which is itself a defect. Either way the sample is not evidence.
5. **Delivery and closure observations are scope-misread.** Operator marked
   them as defects; they are wave-scoped inspect-only / contract-only by Plan
   A §3.2 and `publish_feedback_closure_contract_v1`. The sample's apparent
   "broken delivery" is a brief calibration issue, not a runtime failure —
   but until §8.D corrects the brief, every future sample will reproduce this
   noise.

The conclusion is unambiguous: this task cannot serve as Plan A live-run
evidence for Matrix Script.

## 8. Required Correction Path

These items are the precondition for creating a fresh corrected Matrix
Script trial sample. They are specs, not implementation work in this turn.

### §8.A — Entry-form ref-shape guard

- **Server side:** add `_validate_ref_shape(value: str) -> None` in
  `gateway/app/services/matrix_script/create_entry.py`, called from
  `_normalise_entry` before `_require(...)` returns. Reject:
  - multi-line strings;
  - strings exceeding a sane ref length (e.g. 512 chars);
  - strings without a recognisable ref scheme/prefix (`content://`,
    `task://`, an absolute URL, or a token ID matching a documented pattern).
  - On rejection, raise the existing entry-validation error type so the form
    re-renders with a localised message.
- **Client side:** change
  `gateway/app/templates/matrix_script_new.html:161-162` from
  `<textarea>` to `<input type="text">` with `pattern=` and `maxlength=`
  matching the server guard, replace the prose placeholder with a ref-only
  example, and add helper text that explicitly forbids pasting body text.
- **Contract addendum:** if the contract does not already enumerate the
  accepted ref schemes for `source_script_ref`, add a one-line clarification
  to `task_entry_contract_v1` stating the closed scheme set used by the
  guard.

### §8.B — Confirm workbench panel dispatch

- Open the trial task id in the running gateway. Verify that `/tasks/{id}`
  for `kind=matrix_script` renders
  `matrix_script_workbench_variation_surface_v1` (the Phase B variation
  panel), not the generic engineering shell.
- If dispatch is correct, document the confirmation in this review's §3
  table (close row #2).
- If dispatch is wrong, file a separate blocker against
  `workbench_panel_dispatch_contract_v1` describing the mis-route.

### §8.C — Phase B authoring capability or explicit fixture policy

Pick exactly one:

- **Option C1 — land Phase B planning capability.** Implement the capability
  that, given a valid `source_script_ref`, produces populated
  `matrix_script_variation_matrix.axes[] / cells[]` and
  `matrix_script_slot_pack.slots[]` deltas, attached as packet line-specific
  delta payloads (not pointers). Honour `slot_pack_contract_v1:44` —
  `slots[].body_ref` stays opaque; no body embedding.
- **Option C2 — freeze fixture-LS-delta policy.** Add a contract-addendum
  document stating that Plan A trial uses pre-seeded fixture LS1/LS2
  deltas, define their shape, and write the seeding step as part of the
  trial-task creation flow (clearly marked as fixture, not authoring).

Without C1 or C2, the Phase B render surface has nothing to render and
Plan A trial cannot produce evidence regardless of §8.A and §8.B.

### §8.D — Operator brief correction

- Update `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` operator brief
  language to make explicit that, for Matrix Script in this wave:
  - Delivery Center renders inspect-only `not_implemented_phase_c`
    placeholder rows by design;
  - Phase D.1 publish-feedback closure write-back is not yet implemented and
    closure surface is read-only;
  - Operators must NOT report these as defects in trial evidence.
- This change must be a brief-only change; it must not modify Plan A scope.

## 9. Gate Recommendation

- **Matrix Script trial: BLOCKED.**
- **Continue current sample: NO.** Do not record any further observation
  against this task as Plan A evidence.
- **Create fresh corrected sample: YES**, only after §8.A and §8.C have
  landed and §8.B has been confirmed. §8.D should land in the same wave so
  the next operator brief is accurate.

### Hard red lines (re-stated)

While correcting:

- do not reopen Hot Follow scope;
- do not enter Platform Runtime Assembly;
- do not enter Capability Expansion;
- do not introduce provider / model / vendor / engine controls as a
  workaround;
- do not patch the workbench UI to fake populated axes/cells/slots;
- do not weaken the `source_script_ref` contract to accept body text;
- do not promote Delivery Center beyond inspect-only for Matrix Script in
  this wave;
- do not add state-shape fields (`delivery_ready`, `publishable`,
  `final_ready`, etc.) to any surface;
- do not onboard a second production line until the Matrix Script
  correction items above are gated through.

End of v1.
