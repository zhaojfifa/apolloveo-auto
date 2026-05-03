# Plan A Signoff Checklist v1

Date: 2026-05-03
Status: **Documentation only. No code, no UI, no contract, no schema, no test, no template change.** Coordinator-facing closeout checklist for Plan A live-trial. Distilled from the actual gap state of [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) and [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) on commit `a3e2f38`. Authority of creation: documentation re-anchoring under [unified map §3.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [unified map §7.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [MATRIX_SCRIPT_NEXT_WAVE_START_NOTE_v1.md §4](MATRIX_SCRIPT_NEXT_WAVE_START_NOTE_v1.md).

---

## 0. Purpose and binding scope

This is the closeout checklist Jackie (operations team coordinator), Raobin (architect), and Alisa (reviewer) use to bring Plan A from the current **PARTIAL** state to a clean closeout. It enumerates every remaining human confirmation, every outstanding evidence box, and every signoff field still unsigned.

This checklist:

- Does **not** open Plan E gate-spec authoring. Plan E gate spec authoring is gated on the completion of this checklist plus formal append per [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md §7](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md). See §6 below.
- Does **not** start any operator-facing implementation. Plan E implementation remains BLOCKED until Plan E gate spec is authored, reviewed, and approved.
- Does **not** start Platform Runtime Assembly. Platform Runtime Assembly remains gated on Plan E green per [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).
- Does **not** weaken the Plan A wave verdict. Wave verdict remains **PARTIAL** until §6 conditions are all satisfied.
- Does **not** mutate any contract, schema, runtime, template, or test.

If wording in this checklist ever conflicts with [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md), or [unified map](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), the underlying authority wins and this checklist is updated.

---

## 1. Audit summary (state on commit `a3e2f38`)

### 1.1 Capture template — already-recorded evidence (do not re-confirm)

The following is already filled in [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) and is treated as recorded evidence:

| Section | Already recorded |
| --- | --- |
| §1 Trial-window header | date / window, deployed branch / SHA, trial environment URL, coordinator (Jackie), operator (sunny), architect observer (Raobin), reviewer observer (Alisa); §12 conditions **3 / 6 / 8** confirmed `[x] yes`; coordinator note recording partial-only nature |
| §2.1 Sample 1 (Hot Follow golden) | task_id `c03ab0b46118`, entry path, 3 of 4 success criteria, per-surface notes, coordinator initials + timestamp |
| §2.2 Sample 2 (Hot Follow preserve-source) | task_id `e857ea46be1d`, entry path, **2 of 2** success criteria (complete), per-surface notes, coordinator initials + timestamp |
| §2.3 Sample 3 (Matrix Script fresh contract-clean) | task_id `7a407e8d00a9`, entry parameters, 8 of 12 success criteria checked (positive-path acceptance + (b) panel mount + (c) 3 axes / 4 cells / 4 slots / round-trip + (d) human-readable axes + (e) shell suppression), per-surface notes, coordinator initials + timestamp |
| §2.4 Sample 4 (Matrix Script multi-language `mm`) | task_id `9f3b7b0d3d07`, entry parameters, **2 of 2** success criteria (complete), per-surface notes, coordinator initials + timestamp |
| §2.5a Sample 5a (variation_target_count=1) | task_id `e46557070bdd`, **4 of 4** success criteria (complete), per-surface notes |
| §2.5b Sample 5b (variation_target_count=12) | task_id `8cf9ed1d810a`, **4 of 4** success criteria (complete), per-surface notes |
| §2.6 Sample 6 (cross-line board inspection) | tasks observed (Hot Follow `c03ab0b46118` + Matrix Script `7a407e8d00a9` + Digital Anchor n/a), 2 of 3 success criteria, per-surface notes, coordinator initials + timestamp |
| §3 Cross-cutting observations | all six rows answered (pre-trial guards retained, no forbidden sample attempted, no vendor/model/provider/engine selector observed, no third-line URL resolved, board-vs-workbench publishable divergence flagged, no drift from §3.1 / §3.2 static evidence) + free-text coordinator narrative |
| §4 Regression / blocker capture | empty (zero regressions filed; appropriate) |
| §5 Final live-run judgment | total sample evidence captured, formal start conditions partial, samples aborted (none), samples skipped (none), regressions (0), net trial verdict **PARTIAL**, reason articulated, Plan E pre-condition #1 marked `[x] not satisfied` |
| §6 Statements | three signoff statements filled (Jackie / Raobin / Alisa) |

### 1.2 Capture template — human confirmations still required (operator-action gaps)

The following are still missing or pending operator action. Each row names the file, section, and exact confirmation owed.

| Item | File / section | What is still owed |
| --- | --- | --- |
| §12 condition 1 — §5 explanation 口径 briefed to operators verbatim | capture template §1 | Coordinator brief operators verbatim from [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §5](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) and the trial brief §5; flip `[ ] yes / [x] no` → `[x] yes / [ ] no` and re-record. |
| §12 condition 2 — Digital Anchor card + temp connect route hidden / disabled | capture template §1 | Apply hide/disable guard per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §2.1](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) on (a) `<a href="/tasks/connect/digital_anchor/new ...">` element in [gateway/app/templates/tasks_newtasks.html:47](../../gateway/app/templates/tasks_newtasks.html) and (b) the temp `/tasks/connect/digital_anchor/new` route. **This is load-bearing** — every other observation that records "Digital Anchor card was still visibly present" depends on this guard being applied first. Flip the box and re-record. |
| §12 condition 4 — Trial scope restricted to §7.1 samples (1..6) | capture template §1 | Coordinator confirms (in coordinator note) that no operator session strayed into §7.2 forbidden samples; flip the box. |
| §12 condition 5 — Coordinator has §8 risk list in front of them | capture template §1 | Coordinator prints / displays the §8 risk list from [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §5 / §6.2](PLAN_A_OPS_TRIAL_WRITEUP_v1.md); flip the box. |
| §12 condition 7 — §0.2 product-meaning of `source_script_ref` briefed | capture template §1 | Coordinator briefs operators verbatim from [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md §0.2](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md); flip the box. |
| Sample 1 success criterion — `publish completed` | capture template §2.1 | Coordinator confirms whether publish was actually completed for `task_id=c03ab0b46118`. If yes, flip the box and add a one-line note. If publish was not completed during this observation window, leave unchecked, add a one-line `not run / not applicable in partial slice` note, and document in §3 / §5 that Sample 1 is partial. |
| Sample 3 success criterion (a) — form rejected body-text input (HTTP 400) | capture template §2.3 | Coordinator runs the negative-path test in a non-operator environment per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §11.3](PLAN_A_OPS_TRIAL_WRITEUP_v1.md): POST a body-text payload to `/tasks/matrix-script/new`; expect HTTP 400 from `_validate_source_script_ref_shape`. Flip the box. |
| Sample 3 success criterion (a) — form rejected publisher-URL input (HTTP 400 "scheme is not recognised") | capture template §2.3 | Coordinator POSTs `https://news.qq.com/...` (or any `https://` / `http://` value) per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §12.3](PLAN_A_OPS_TRIAL_WRITEUP_v1.md); expect HTTP 400 with `"scheme is not recognised"`. Flip the box. |
| Sample 3 success criterion (a) — form rejected bucket-URI input (HTTP 400 "scheme is not recognised") | capture template §2.3 | Coordinator POSTs `s3://...` or `gs://...` per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §12.3](PLAN_A_OPS_TRIAL_WRITEUP_v1.md); expect HTTP 400. Flip the box. |
| Sample 3 success criterion (f) — publish-feedback closure mutated rows correctly | capture template §2.3 | **N/A this wave — Plan E gated.** Per [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §3.1 / §6.2](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), Matrix Script Delivery Center is inspect-only this wave; the artifact-lookup contract (Plan B B4) and publish-feedback resolution are gated to Plan E. Coordinator should annotate the box with `N/A — Plan E gated` rather than attempt the test. This does not block Plan A closeout. |
| Sample 6 success criterion — Digital Anchor row contains no operator-actionable submit affordance | capture template §2.6 | After §12 condition 2 hide/disable guard is applied above, coordinator re-inspects the `/tasks` board card and confirms the Digital Anchor row carries no submit affordance. Flip the box. |

### 1.3 Capture template — signoff-only fields (after §1.2 is complete)

The §6 signoff block has three subsections; each has two `<fill>` placeholders that only the named human can fill. Statements are already drafted.

| Role | File / section | Fields owed |
| --- | --- | --- |
| Operations team coordinator — Jackie | capture template §6 (first block) | `Date / time:` `<fill>`; `Signature / handle:` `<fill>` |
| Architect — Raobin | capture template §6 (second block) | `Date / time:` `<fill>`; `Signature / handle:` `<fill>` |
| Reviewer — Alisa | capture template §6 (third block) | `Date / time:` `<fill>`; `Signature / handle:` `<fill>` |

### 1.4 Writeup consistency audit

Verified rows in [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md):

| Row | Verdict |
| --- | --- |
| §8 introduction (post-`8f1fcba`) | consistent — partial Sample 3 slice acknowledged; samples 1, 2, 4, 5a, 5b, 6 evidence pointed at capture template; §6 signoff dependency named |
| §8 trailing line (post-`8f1fcba`) | consistent — PARTIAL / not satisfied / BLOCKED reaffirmed |
| §10 Final Statement | consistent — line 282 `"but not yet to declare full Plan A completion or to unblock Plan E"`; lines 290-293 PARTIAL / BLOCKED |
| §11.5 Final corrected coordinator judgment | consistent — line 396 `"Live-trial readiness for Matrix Script: CONDITIONAL"`; retry-sample-creation readiness only |
| §12.5 Final corrected coordinator judgment (post-§8.H) | consistent on verdict; **minor surface-staleness** — line 396 contains the parenthetical `"(the §8 placeholder remains empty in this static pass)"` which was true when §12.5 was authored earlier on 2026-05-03 but is no longer true after the partial Sample 3 slice was appended later that day in `992b24b`. Temporal scope `"in this static pass"` makes the phrase semi-defensible (it refers to the §11/§12 static-pass authoring moment), but a cold reader could be confused. **No verdict overclaim**, so this is logged here as a documentation drift to address in a future evidence write-back, not a blocker for Plan A closeout. |
| Coordinator note line 400-402 | consistent — `"not yet sufficient as full Plan A wave-completion evidence"` |

**Conclusion:** appended partial evidence and verdict wording remain internally consistent. No sentence overclaims Plan A completion or Plan E unblock.

---

## 2. Outstanding closeout work (canonical list)

The work remaining to bring Plan A from PARTIAL to closeout, grouped by gate.

### 2.1 Coordinator-action confirmations (§1.2 above; flip boxes after action)

5 of 8 §12 conditions remain `[ ] yes / [x] no`:

- §12 condition 1 — verbatim §5 brief
- §12 condition 2 — Digital Anchor hide/disable guard **(load-bearing — apply first)**
- §12 condition 4 — trial-scope restriction confirmation
- §12 condition 5 — §8 risk list in coordinator's hand
- §12 condition 7 — §0.2 product-meaning brief

Sample-level boxes still unchecked:

- Sample 1 `publish completed` — confirm or annotate `not run`
- Sample 3 (a) — three negative-path tests (body-text, publisher-URL, bucket-URI rejections)
- Sample 3 (f) — annotate `N/A — Plan E gated` (Plan B B4 / publish-feedback resolution lands at Plan E)
- Sample 6 Digital Anchor row — re-inspect after §12 condition 2 guard applied

### 2.2 Signoff fields (§1.3 above)

Three signoff blocks in capture template §6 need date/time + signature/handle from Jackie, Raobin, Alisa respectively.

### 2.3 Formal append from capture template into writeup §8

After §2.1 + §2.2 above are complete, the operations team coordinator (or designate) executes the §7 handoff rule of the capture template:

> *Append the contents of §1 (header) and §2.1–§2.6 (per-sample capture) and §3–§5 (cross-cutting + regression + verdict) and §6 (signoff) to [PLAN_A_OPS_TRIAL_WRITEUP_v1.md] §8 placeholder, preserving the field-name shape from that §8 placeholder. Do not mutate any other section of the write-up. Do not mutate the brief.*

Append rules:

- Preserve verdict semantics. Wave verdict in capture template §5 is **PARTIAL**; this verdict is what is appended into writeup §8.
- The Sample 3 slice already in writeup §8 (commit `992b24b` / refined in `8f1fcba`) is preserved — the formal append adds samples 1, 2, 4, 5a, 5b, 6 and the §3 / §4 / §5 / §6 blocks alongside it.
- Do not modify §10 Final Statement during this append.
- Do not promote any wording from PARTIAL to PASS during this append. The PARTIAL → PASS transition (if any) is a separate signoff event recorded in §6 of the capture template, not in writeup §10.

### 2.4 Verdict-transition decision (post-append)

After §2.3 append lands, the coordinator + architect + reviewer determine the closeout verdict by comparing the appended evidence against [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) "Final readiness judgment":

- If every §12 condition is `[x] yes` AND every sample has at least one positive criterion checked AND no abort trigger fired AND no regression filed AND §6 is fully signed: closeout **PASS** is admissible.
- If any §12 condition remains `[ ] no`, or any positive criterion remains unchecked without an N/A annotation, or any abort trigger fired, or any regression remains open: closeout verdict remains **PARTIAL**.
- Closeout **FAIL** only if a §8 risk-list trigger from the brief activated and was not resolved.

This checklist does not pre-decide the verdict; it only enumerates the gating evidence.

---

## 3. Definition: when Plan E pre-condition #1 becomes satisfied

Plan E pre-condition #1 is named in [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10 line 290](PLAN_A_OPS_TRIAL_WRITEUP_v1.md):

> *"Plan E pre-condition #1 (Plan A executed + write-up filed): PARTIAL — write-up filed (this document); live-trial execution by operations team remains. Plan E gate cannot open until §8 carries at least one full sample-wave entry."*

For this checklist, "at least one full sample-wave entry" is operationalized as **all** of the following holding:

1. Capture template §1 carries `[x] yes` on **all eight** §12 conditions (currently 3 of 8 satisfied).
2. Capture template §2.1–§2.6 carries either `[x]` or an explicit `N/A — Plan E gated` annotation on **every** success criterion box (currently 17 boxes need attention per §1.2 above).
3. Capture template §6 carries date/time + signature/handle for **all three** signoff blocks (currently 0 of 3 signed).
4. The handoff per [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md §7](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) has been executed: contents of §1, §2.1–§2.6, §3, §4, §5, §6 from the capture template are appended into [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §8](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) preserving field-name shape.
5. The closeout verdict (per §2.4 of this checklist) has been recorded as **PASS** or **PARTIAL with explicit residual gaps documented**. A FAIL outcome blocks Plan E pre-condition #1; PARTIAL with documented residual gaps may be admissible only at architect + reviewer concurrence.

When **all five** of the above hold, Plan E pre-condition #1 is satisfied.

Until **all five** hold, Plan E pre-condition #1 is **not satisfied**, the wave verdict remains **PARTIAL**, and Plan E gate spec authoring is **not authorized**.

---

## 4. Plan E gate-spec authoring authorization

**Plan E gate spec may only start after this checklist is fully completed and §3 above is satisfied.**

Per [unified map §7.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), Plan E gate spec is Step 2 in the frozen engineering sequence. Per [unified map §7.6 hard red line](../architecture/apolloveo_2_0_unified_alignment_map_v1.md):

> *"Do not skip Step 1 by running Plan E preparation in parallel — the Plan E gate spec depends on Plan A live-run findings."*

Concretely, Plan E gate-spec authoring becomes authorized only when:

- §3 of this checklist is satisfied (all five conditions hold), **and**
- A separate review document is opened to author the gate spec (Plan E gate spec is owned by a review document, not by the writeup or capture template), **and**
- The author of the gate spec re-reads [unified map §6.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) eight root files and the closed-out Plan A artifacts above before beginning.

This checklist does not authorize Plan E gate-spec authoring. Authorization is a separate signoff event after §3 is satisfied.

Plan E **implementation** remains BLOCKED until Plan E gate spec is authored, reviewed, and approved per its own acceptance criteria. Platform Runtime Assembly remains BLOCKED until Plan E green per [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). Capability Expansion remains BLOCKED until Platform Runtime Assembly green per [unified map §7.5](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).

---

## 5. Posture preserved by this checklist

| Posture element | State after checklist completion | Authority pointer |
| --- | --- | --- |
| Hot Follow = operational baseline line | preserved — no behavior reopened | [unified map §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Matrix Script = next operator-facing line | preserved — gate-spec authoring still upstream of implementation | [unified map §4.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Digital Anchor = inspect-only / contract-aligned, no operator submission this wave | preserved — §12 condition 2 guard explicit; no operator submission authorized | [unified map §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Plan A wave verdict | remains **PARTIAL** until §3 satisfied | [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) |
| Plan E gate spec authoring | not authorized; gated on §3 satisfaction | [unified map §7.2 / §7.6](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Plan E implementation | BLOCKED | [unified map §3.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Platform Runtime Assembly | BLOCKED | [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Capability Expansion | BLOCKED | [unified map §7.5](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Frontend patching beyond shipped | BLOCKED | [unified map §3.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Provider / model / vendor / engine controls | forbidden | [unified map §2.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), validator R3 |

---

## 6. Closeout signoff (this checklist)

This section is filled when this checklist itself is closed (i.e. when §3 is satisfied and Plan A is signed off).

```
Operations team coordinator — Jackie
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm §1.2 / §1.3 of this checklist have been executed, the
                      capture template §1 §12 conditions are all `[x] yes`, every sample
                      criterion is `[x]` or annotated `N/A — Plan E gated`, and the §7
                      handoff into writeup §8 has been performed.

Architect — Raobin
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm the appended evidence remains inside the Operator-Visible
                      Surface Validation Wave. No Plan E implementation, Platform Runtime
                      Assembly, or Capability Expansion work is implied by this closeout.

Reviewer — Alisa
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm Plan E pre-condition #1 is satisfied per §3 of this
                      checklist. Plan E gate-spec authoring may now be opened in a
                      separate review document; Plan E implementation remains BLOCKED.
```

End of Plan A Signoff Checklist v1.
