# Operations Trial Readiness · Matrix Script Result-Capability Recovery Amendment v1

Date: 2026-05-06
Status: **Authoritative governance amendment. Docs-only.** Re-scopes Plan A live-trial execution: Hot Follow benchmark may proceed; Matrix Script live-trial is paused; Digital Anchor remains excluded.
Wave position: Post-OWC-MS + OWC-DA closeout. Post-pre-trial ops addendum (PR #141 squash `27a5b6d`). Post-trial-re-entry-review SIGNED (PR #143 squash `d6619cf` + direct-to-main signoff `7e2ad59`). Pre-Plan A live-trial Hot Follow execution. Pre-Matrix Script Result-Capability Recovery Wave gate spec authoring.
Authority: Produced after reading the authority stack listed in §0 in full.
Relation to Plan A: This amendment supersedes specific sections of Plan A and of the trial re-entry review for Matrix Script trial scope only. Hot Follow scope is unchanged. Digital Anchor scope is unchanged.

---

## 0. Authority Read for This Amendment

Consulted in order per `CLAUDE.md` §2 boot sequence, before any authoring:

1. `CLAUDE.md` (bootloader)
2. `ENGINEERING_RULES.md` (engineering governance)
3. `CURRENT_ENGINEERING_FOCUS.md` (active wave + forbidden work; user-edited `7e2ad59` post-signoff state)
4. `ENGINEERING_STATUS.md` (stage / gate / completion log)
5. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` §7 (frozen next engineering sequence)
6. `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (Plan A — including §13 post-OWC addendum + §14 trial re-entry review reference)
7. `docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md` (post-OWC operational trial baseline; PR #141)
8. `docs/reviews/trial_reentry_review_v1.md` (SIGNED trial re-entry review; per-line verdicts in §7)
9. `docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md` (OWC-MS engineering verdict + tracked gaps §8)

No code files were read. No contract or schema files were read. No implementation work is opened by this amendment.

---

## 1. Status Statement

The trial re-entry review (PR [#143](https://github.com/zhaojfifa/apolloveo-auto/pull/143) authored, `7e2ad59` signed) classified Matrix Script as a **LIMITED / CONSTRAINED TRIAL CANDIDATE** based on surface convergence: Task Area + Workbench C/D/E + 回填 are operable; Workbench A and Delivery Center copy_bundle are inspect-only / display-only. The four-party §8 signoff was issued on that classification.

A subsequent product/operations review of the Matrix Script line concluded that surface convergence — fields, panels, cells, slots, and diagnostics — does **not** constitute a trial-capable line. The line presents structural projection of contract data; it does not yet present an operator-understandable, result-oriented deliverable path. An operator who creates a Matrix Script task today cannot identify, on the existing surfaces alone:

1. **What is usable now** — which variation / version is currently a deliverable artifact, not just a populated cell.
2. **What is blocked** — which variation is gated by a missing input vs by a closed advisory vs by a sentinel-state field.
3. **Which version is recommended** — the per-task "recommended variation marker" exists in the Workbench C projection but is not framed as an actionable result decision.
4. **What next action is required** — the surfaces show diagnostic state (`STATUS_UNRESOLVED`, advisory rows, blocking advisories) but do not present an operator-language "do X next."

This is **not** an engineering defect against the OWC-MS gate spec. The OWC-MS gate spec was scoped to surface convergence per `docs/product/matrix_script_product_flow_v1.md` §§5.1 / 5.2 / 5.3 / 6.1A / 6.1C / 6.1D / 6.1E / 7.1 / 7.3, and the eight modules MS-W1..MS-W8 deliver exactly that. The OWC-MS engineering verdict PASS stands; the eight already-merged modules remain on `main` as substrate. **This amendment is at the operations layer, not the engineering layer.** It corrects the operational classification of Matrix Script without re-litigating any merged engineering scope.

Hot Follow is unchanged: the benchmark end-to-end line is operationally trial-capable. The Plan A live-trial Hot Follow scope (§7.1 samples 1–2 — golden + preserve-source) may proceed.

Digital Anchor is unchanged: NOT a trial candidate, anchored on the five operations findings in the post-OWC addendum §2.3.1.

---

## 2. Six Binding Statements

The amendment declares the following six statements as binding. They take effect on this amendment's merge to `main`.

### 2.1 Plan A live-trial execution is paused for Matrix Script.

Plan A live-trial execution per alignment map §7.1 is **paused** for the Matrix Script line. Operations team coordinator MUST NOT execute Plan A §7.1 samples 3–6 (Matrix Script `mm` / `vi` boundary check + cross-line Board inspection insofar as they require Matrix Script samples) against the live system. The PR-5 NOT-READY verdict (commit `da55a52` on the recovery branch) is **re-instated for Matrix Script only** until the result-capability recovery wave closes.

### 2.2 Hot Follow may continue as benchmark line.

Plan A live-trial Hot Follow execution may proceed per alignment map §7.1, scoped to:
- Plan A §7.1 sample 1 — Hot Follow golden-path
- Plan A §7.1 sample 2 — Hot Follow preserve-source
- Plan A §7.1 cross-line Board inspection insofar as it does not require Matrix Script samples
- Coordinator §5.1 / §5.2 / §5.3 口径 briefings for Hot Follow scope only
- Coordinator §2.1 hide guards (Digital Anchor card + temp route + Asset Supply / B-roll + promote intent submit) and additionally hides Matrix Script New-Tasks card click target during the Hot-Follow-only trial run

The four post-OWC trial protocol constraints from the trial re-entry review §6 (no gateway restarts; sentinel briefing; fresh samples; forbidden-token scrub) remain in force for Hot Follow scope; sentinel briefing applies only to Hot Follow advisory rows in the Hot-Follow-only window.

### 2.3 Matrix Script is downgraded from limited trial candidate to result-capability recovery required.

The post-OWC addendum §1.4 / §2.2 classification of Matrix Script as **LIMITED / CONSTRAINED TRIAL CANDIDATE** is **superseded** for the period from this amendment's merge until the Matrix Script Result-Capability Recovery Wave closes. The new classification is:

> **Matrix Script — RESULT-CAPABILITY RECOVERY REQUIRED.** Engineering closeout PASS, operations NOT-READY for trial. The line presents contract-projection surfaces but not a result-oriented operator deliverable path. Not eligible for real operator trial in this state. Becomes eligible only after the Matrix Script Result-Capability Recovery Wave closes and a follow-on trial re-entry review signs.

The trial re-entry review §4 (Matrix Script trial scope), §7 (per-line verdict for MS), and §7's MS-related conditions (conditions 6, 9, 10, 11, 12) are **superseded** for live-trial purposes by this classification. The §8 signoff itself remains a binding audit record — it represents the four parties' verdict on the trial re-entry review **as authored**. This amendment does not re-open or unsign §8; it changes the operational classification going forward.

### 2.4 Digital Anchor remains not a trial candidate.

The post-OWC addendum §2.3 / §2.3.1 verdict on Digital Anchor is unchanged. Five operations findings still anchor the not-trial-capable verdict. No DA samples are valid trial evidence. DA New-Tasks card and `/tasks/digital-anchor/new` route remain hidden / disabled during any trial run.

### 2.5 The next allowed Matrix Script engineering wave is limited to result-capability recovery.

The next Matrix Script engineering wave authorised by this amendment is the **Matrix Script Result-Capability Recovery Wave**, scoped exclusively to:

> Reorganize the existing Matrix Script operator surfaces to present an operator-understandable, result-oriented deliverable path: the operator must be able to identify what is usable now, what is blocked, which version is recommended, and what next action is required, using existing data sources from the OWC-MS modules and the Recovery PR-1..PR-4 substrate.

**Scope explicitly bounded by:**

- No new contract authoring. The recovery wave consumes existing contracts (matrix_script packet truth; closure shape envelope; `publish_readiness` producer; L3 `final_provenance`; L4 advisory emitter; `REVIEW_ZONE_VALUES`).
- No new structural surface modules. The recovery wave reorganizes / re-frames the existing MS-W1..MS-W8 surfaces; it does not author MS-W9 or wider.
- No closed-enum widening (`task_entry_contract_v1`, `D1_EVENT_KINDS`, `REVIEW_ZONE_VALUES`, `target_language` axis, canonical Phase B axes, `source_script_ref` accepted-scheme set all remain frozen).
- No Hot Follow file touch.
- No Digital Anchor file touch.
- No Asset Supply expansion beyond minimum capability.
- Hot Follow benchmark posture (end-to-end result-first, actionable next step, clear deliverables, clear publish readiness, clear operator decision points) is the operational reference; the recovery wave delivers the Hot Follow operator outcome lens applied to Matrix Script's existing data.

**Authority sequence for the recovery wave** (binding):

1. This amendment merges to `main`.
2. A separate **Matrix Script Result-Capability Recovery Wave gate spec** is authored at `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md` as a docs-only step. The gate spec MUST define: pre-conditions / forbidden scope (mirroring §2.5 above) / permitted scope / acceptance criteria / preserved freezes / signoff block. It MUST cite this amendment as authority.
3. The gate spec §10 architect (Raobin) + reviewer (Alisa) signoff lands in a follow-on docs-only PR.
4. Implementation PRs open under the gate spec only after step 3 merges. Implementation slicing is gate-spec-defined; this amendment does not pre-decide.

This amendment **does not** author the gate spec. It authorises the next docs-only step (gate spec authoring) and bounds its scope.

### 2.6 This amendment does not open Platform Runtime Assembly or Capability Expansion.

Platform Runtime Assembly Wave remains BLOCKED gated on Plan A live-trial closeout (Hot Follow live-trial closeout AND post-recovery Matrix Script live-trial closeout, both required). Capability Expansion Gate Wave remains BLOCKED gated on Platform Runtime Assembly signoff. Plan E phase closeout signoffs (A7 / UA7 / RA7) remain independently pending in Raobin / Alisa / Jackie / PM queue and are NOT advanced by this amendment.

---

## 3. What This Amendment Does NOT Do

To prevent scope drift on the merge of this amendment:

| Item | Disposition |
|---|---|
| OWC-MS re-litigation | NOT done. The OWC-MS engineering verdict PASS stands. MS-W1..MS-W8 modules remain merged substrate. Reviewer-fail or new-defect corrections must still be authored as separate narrow follow-up PRs citing the merged PR-1/PR-2/PR-3 commits per existing forbidden-scope discipline. |
| OWC-MS surface deletion / removal | NOT done. The eight already-merged operator-visible modules stay rendered on `tasks.html`, `task_workbench.html`, `task_publish_hub.html`. The recovery wave reframes them; it does not delete them. |
| Hot Follow runtime touch | NOT done. Hot Follow remains benchmark; the recovery wave is bounded to MS files only. |
| Digital Anchor scope widening | NOT done. DA remains NOT a trial candidate. The five operations findings (post-OWC addendum §2.3.1) remain in force unchanged. |
| Platform Runtime Assembly opening | NOT done. Remains BLOCKED. |
| Capability Expansion opening | NOT done. Remains BLOCKED. |
| Trial re-entry review §8 signoff unsigning | NOT done. The §8 four-party signoff is a binding audit record on the trial re-entry review as authored. This amendment changes the forward operational classification of MS; it does not retract any signature. |
| Plan A core sections (§0.1 / §0.2 / §6.1 Hot Follow / §7.2 / §8 / §9) modification | NOT done. Those sections remain in force unchanged. |
| New contract authoring | NOT done. No contract / schema / packet / closure-shape / closed-enum changes. |
| Forced advancement of Plan E A7 / UA7 / RA7 closeout signoffs | NOT done. These remain independently pending. |

---

## 4. Per-Line Updated Posture (Post-Amendment, Binding)

| Production Line | Pre-amendment classification | Post-amendment classification |
|---|---|---|
| Hot Follow | Benchmark end-to-end line. Operationally trial-capable. | **Unchanged.** Benchmark end-to-end line. Operationally trial-capable. Plan A live-trial Hot Follow scope MAY proceed. |
| Matrix Script | LIMITED / CONSTRAINED trial candidate (post-OWC addendum §1.4 / §2.2). | **RESULT-CAPABILITY RECOVERY REQUIRED.** Not a trial candidate until the Matrix Script Result-Capability Recovery Wave closes and a follow-on trial re-entry review signs. |
| Digital Anchor | NOT a trial candidate (post-OWC addendum §2.3). | **Unchanged.** NOT a trial candidate. Five operations findings remain in force. |

---

## 5. Updated Plan A Live-Trial Scope (Hot-Follow-Only Window)

For the Hot-Follow-only trial window that this amendment authorises, the coordinator runs:

| Plan A authority element | Scope this window |
|---|---|
| §7.1 sample 1 — Hot Follow golden-path | **In scope** |
| §7.1 sample 2 — Hot Follow preserve-source | **In scope** |
| §7.1 sample 3 — Matrix Script `mm` boundary check | **OUT OF SCOPE** until MS recovery wave closes |
| §7.1 sample 4 — Matrix Script `vi` boundary check | **OUT OF SCOPE** until MS recovery wave closes |
| §7.1 sample 5 — Matrix Script post-§8.F sample | **OUT OF SCOPE** until MS recovery wave closes |
| §7.1 sample 6 — cross-line Board inspection | **In scope only for Hot Follow rows.** Matrix Script and Digital Anchor rows are inspected as visible Task Area state but no Matrix Script or Digital Anchor task is submitted as a trial sample. |
| §5.1 / §5.2 / §5.3 coordinator briefing | **In scope** for Hot Follow surfaces only. Matrix Script-specific paragraphs of §5.1 / §5.2 / §5.3 (and the post-OWC updated §5.1 / §5.2 / §5.3 from the trial re-entry review §4.4) are NOT briefed in this window — operators are told only that "Matrix Script is in a result-capability recovery wave; do not submit Matrix Script tasks." |
| §2.1 hide guards | **In scope** + additionally hide Matrix Script New-Tasks card click target during this window |
| §0.1 sample-validity rule | **In scope** for Hot Follow samples (Hot Follow has no §0.1 — that rule is Matrix Script-specific; for Hot Follow, the Plan A §6.1 baseline applies) |
| §0.2 product-meaning of `source_script_ref` | **Out of scope** for this window — `source_script_ref` is Matrix Script-only |

Coordinator write-up §8 should record this window as a **Hot-Follow-only live-run cycle**, distinct from any future Matrix Script live-run cycle that follows the recovery wave. The four-party signoff on this window's findings (architect + reviewer + coordinator + product manager) is independent of any future Matrix Script signoff.

---

## 6. Updated Frozen Next Engineering Sequence

Per CLAUDE.md §6 ("If a future change to repo authority makes any line in this file stale, the underlying authority wins"), this amendment carries the updated sequence and the alignment map §7.1 is updated in the same docs-only PR.

After this amendment merges, **two tracks proceed in parallel** with separate ownership and separate signoff cycles. They converge only before Platform Runtime Assembly Wave entry.

```
... → Trial re-entry review SIGNED (`7e2ad59`)
    → Matrix Script Result-Capability Recovery Amendment (THIS DOCUMENT)

         ┌── TRACK A (operations team) ──────────────────────────────┐
         │  A1. Hot-Follow-only Plan A live-trial window (per §5)    │
         │  A2. Hot Follow live-trial findings                       │
         │  A3. Four-party signoff on Hot-Follow-only cycle          │
         └────────────────────────────────────────────────────────────┘

         ┌── TRACK B (engineering — Matrix Script Recovery Wave) ────┐
         │  B1. Recovery Wave gate spec authoring (docs-only)        │
         │      ← NEXT ALLOWED ENGINEERING STEP                       │
         │  B2. Gate spec §10 architect (Raobin) + reviewer (Alisa)  │
         │      signoff (docs-only)                                   │
         │      ← IMPLEMENTATION GATE: B4 cannot open until B2 merges│
         │  B3. (no step — separator)                                │
         │  B4. Recovery Wave implementation PRs                     │
         │  B5. Recovery Wave Closeout                               │
         │  B6. Follow-on trial re-entry review for Matrix Script    │
         │  B7. Plan A live-trial Matrix Script execution            │
         │  B8. Four-party signoff on Matrix Script live-trial cycle │
         └────────────────────────────────────────────────────────────┘

    → Both tracks must close: A3 AND B8 signed
    → Platform Runtime Assembly Wave (BLOCKED until A3 ∧ B8)
    → Capability Expansion Gate Wave (BLOCKED until Platform Runtime Assembly signoff)
```

**Track A and Track B parallelism rules (binding):**

- Track A (operations) and Track B (engineering) may run in parallel from the moment this amendment merges. There is no strict-serial ordering between the two tracks.
- Hot Follow live-trial findings (Track A) are **informational input** to the recovery gate spec (Track B step B1) — not a hard predecessor gate on gate spec authoring or on §10 signoff. The gate spec author may incorporate findings as they land; the gate spec authoring does not have to wait for A3.
- Matrix Script implementation PRs (Track B step B4) are gated on **Track B step B2** (recovery gate spec §10 architect + reviewer signoff merging to `main`), **not on Track A signoff**.
- Track A's signoff cycle (A3) is independent of Track B's gate spec §10 signoff cycle (B2). The two signoff cycles produce separate audit records.
- Plan A live-trial Matrix Script execution (B7) requires B5 closeout AND B6 follow-on trial re-entry review signed; it does not require A3 (although in practice A3 will land first).

---

## 7. Hard Boundaries for the Follow-On Engineering Plan

These boundaries apply to the Matrix Script Result-Capability Recovery Wave gate spec (which this amendment authorises but does NOT author) and to its implementation PRs. They are binding on any follow-on engineering work in this thread of work.

1. **Do not widen Digital Anchor.** No DA file touch. No DA scope re-evaluation. The five operations findings remain in force.
2. **Do not reopen Hot Follow runtime.** No Hot Follow file touch. Hot Follow stays benchmark.
3. **Do not start Platform Runtime Assembly.** Wave remains BLOCKED.
4. **Do not start Capability Expansion.** Wave remains BLOCKED.
5. **Do not re-litigate OWC-MS as a contract-projection wave.** OWC-MS PR-1/PR-2/PR-3 substrate stays merged. Reviewer-fail / new-defect corrections must still be narrow follow-up PRs.
6. **Do not author new contracts or schemas.** The recovery wave consumes existing data; it does not produce new packet truth, new closure shape, new producers, or new closed enums.
7. **Do not add new structural surface modules.** No MS-W9. No new operator-visible panel beyond reorganization of existing eight modules.
8. **Stay inside Matrix Script operator surface and workflow reframe.** Result-oriented deliverable path delivered as a re-presentation of existing data on existing surfaces; no expansion.

---

## 8. Sequencing Rule (Binding) for the Next Step

After this amendment merges to `main`, the following posture is binding:

**Allowed (Track B engineering — single next docs-only step):**

- Author the Matrix Script Result-Capability Recovery Wave gate spec at `docs/reviews/matrix_script_result_capability_recovery_gate_spec_v1.md`. The gate spec must cite this amendment as authority and observe the §7 hard boundaries.

**Allowed (Track A operations — in parallel with Track B):**

- Plan A live-trial Hot-Follow-only window per §5 above. Operations team may run Track A regardless of Track B's progress; the two tracks do not block each other.

**Forbidden:**

- Opening Matrix Script Result-Capability Recovery Wave implementation PRs before the recovery-wave gate spec §10 architect + reviewer signoff merges to `main`. **The implementation gate is gate spec §10 signoff** — not Hot Follow live-trial signoff. Track A's signoff is not a precondition for Track B implementation.
- Re-opening any merged OWC-MS module (MS-W1..MS-W8) for re-litigation; the recovery wave operates by reorganization, not re-litigation.
- Plan E A7 / UA7 / RA7 closeout signoff advancement under cover of this amendment, the recovery-wave gate spec, the recovery-wave implementation PRs, or any housekeeping PR. Plan E closeout signoffs remain independently pending.
- Platform Runtime Assembly Wave entry. Remains BLOCKED until BOTH Track A's Hot Follow live-trial signoff AND Track B's Matrix Script live-trial signoff (Track B step B8) land. The recovery wave's gate spec, implementation, and closeout are all internal to Track B; they do not unblock Platform Runtime Assembly on their own.
- Capability Expansion Gate Wave entry. Remains BLOCKED until Platform Runtime Assembly signoff.
- Digital Anchor scope widening. The five operations findings (post-OWC addendum §2.3.1) remain in force. No DA file touch is permitted in the recovery-wave gate spec or its implementation PRs.

This amendment does **not** author the gate spec. It authorises and bounds the next docs-only step (gate spec authoring) without making the recovery wave's progress conditional on Track A.

---

## 9. References

- Plan A authority: [`docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (including §13 post-OWC addendum + §14 trial re-entry review reference + §15 this amendment reference)
- Post-OWC addendum: [`docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md`](OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md) (PR [#141](https://github.com/zhaojfifa/apolloveo-auto/pull/141) squash `27a5b6d`)
- Trial re-entry review (SIGNED): [`docs/reviews/trial_reentry_review_v1.md`](../reviews/trial_reentry_review_v1.md) (PR [#143](https://github.com/zhaojfifa/apolloveo-auto/pull/143) squash `d6619cf` + signoff `7e2ad59`)
- Unified alignment map (§7 frozen sequence updated by this amendment's PR): [`docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`](../architecture/apolloveo_2_0_unified_alignment_map_v1.md)
- OWC-MS Closeout: [`docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md`](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md) (engineering verdict PASS — preserved unchanged)
- Evidence index: [`docs/execution/apolloveo_2_0_evidence_index_v1.md`](../execution/apolloveo_2_0_evidence_index_v1.md)
