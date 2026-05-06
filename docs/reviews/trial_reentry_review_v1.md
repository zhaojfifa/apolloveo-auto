# ApolloVeo 2.0 · Trial Re-Entry Review v1

Date: 2026-05-06 (authored); 2026-05-06 (§8 signed by all four parties — see §8)
Status: **SIGNED — §8 signoff block filled by Architect Raobin (2026-05-06 21:10), Reviewer Alisa (2026-05-06 21:18), Operations Coordinator Jackie (2026-05-06 21:25), Product Manager sunny (2026-05-06 21:30). Plan A live-trial reopen AUTHORIZED.**
Wave position: Post-OWC-MS + OWC-DA closeout. Post-pre-trial ops addendum. Pre-Plan A live-trial reopen.
Authority: Produced after reading the authority stack listed in §0 in full.
Relation to Plan A: This review is the gate document for Plan A live-trial reopen. It evaluates against the post-OWC addendum as the binding operational baseline and updates Plan A §12 readiness conclusion (§7 below). It does NOT reopen OWC-MS or OWC-DA implementation, does NOT start Platform Runtime Assembly, does NOT start Capability Expansion, and does NOT author Digital Anchor sample-validity criteria.

---

## 0. Authority Read and Preconditions

### 0.1 Authority files read

Consulted in order per `CLAUDE.md` §2 boot sequence, before any authoring:

1. `CLAUDE.md` (bootloader)
2. `ENGINEERING_RULES.md` (engineering governance)
3. `CURRENT_ENGINEERING_FOCUS.md` (active wave + forbidden work)
4. `ENGINEERING_STATUS.md` (stage / gate / completion log)
5. `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (Plan A — including §13 post-OWC addendum reference)
6. `docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md` (**binding operational baseline for this review**)
7. `docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md` (OWC-MS engineering verdict + tracked gaps §8)
8. `docs/execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md` (OWC-DA engineering verdict + tracked gaps §8)
9. `docs/reviews/owc_ms_gate_spec_v1.md` (OWC-MS allowed + forbidden scope)
10. `docs/reviews/owc_da_gate_spec_v1.md` (OWC-DA allowed + forbidden scope)
11. `docs/execution/apolloveo_2_0_evidence_index_v1.md` (evidence index — trial re-entry review row)

No code files were read. No contract or schema files were read. No trial re-entry review work was started before both preconditions below were verified as satisfied.

### 0.2 Preconditions satisfied

Per `docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md` §7.4 (binding sequencing rule):

| Precondition | Status |
|---|---|
| OWC-MS Closeout MS-A1..MS-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; MS-A7 signed commit `b1160b3` |
| OWC-DA Closeout DA-A1..DA-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; DA-A7 signed per §11 (Raobin 2026-05-06 21:10; Alisa 2026-05-06 21:18; Jackie 2026-05-06 21:25; PM sunny 2026-05-06 21:30) |
| OWC-DA Closeout merged to `main` | **SATISFIED** — PR [#139](https://github.com/zhaojfifa/apolloveo-auto/pull/139) squash `f5e86a5`; housekeeping PR [#140](https://github.com/zhaojfifa/apolloveo-auto/pull/140) also merged |
| Pre-trial ops-readiness review produced | **SATISFIED** — OWC operations-readiness alignment review 2026-05-06 (conversation artifact) |
| Pre-trial ops addendum authored | **SATISFIED** — authored 2026-05-06 in PR [#141](https://github.com/zhaojfifa/apolloveo-auto/pull/141) |
| Pre-trial ops addendum (PR #141) merged to `main` | **SATISFIED** — MERGED 2026-05-06T02:34:45Z, squash commit `27a5b6d` |
| Explicit user hand-off for trial re-entry review | **SATISFIED** — user hand-off issued 2026-05-06 |

**All preconditions satisfied. Trial re-entry review is authorized.**

No code, no UI, no contract, no schema, no template change is introduced by this document or by this PR.

---

## 1. Binding Operational Baseline

The binding operational baseline for this review is:

> **[`docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md`](../product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md)** — PR [#141](https://github.com/zhaojfifa/apolloveo-auto/pull/141), squash commit `27a5b6d`, merged 2026-05-06T02:34:45Z.

This addendum supersedes Plan A §6.2 (Matrix Script — narrowed scope), Plan A §6.3 (Digital Anchor — superseded from "inspection-only" to "NOT a trial candidate"), and Plan A §7.1 (trial samples). All other Plan A sections (§0.1 / §0.2 `source_script_ref` discipline, §6.1 Hot Follow, §7.2 samples to avoid, §8 risks, §9 next gate conditions) remain in force unchanged.

The addendum headline operations verdict is the starting point for this review:

| Line | Addendum operations verdict |
|---|---|
| Hot Follow | **Benchmark end-to-end line.** Operationally trial-capable. Reference / control line for any trial. |
| Matrix Script | **Limited / constrained trial candidate.** Task Area + Workbench C/D/E + 回填 operable; Workbench A and Delivery Center copy_bundle inspect-only / display-only. |
| Digital Anchor | **NOT a trial candidate in current state.** Engineering closeout PASS, operations NOT-READY. Not eligible for real operator trial in this wave. |

This review evaluates against this baseline and confirms which OPS gaps are acceptable for trial, which are not applicable, and that none require further mitigation before trial begins.

---

## 2. OPS-GAP Acceptability Assessment

The addendum §6 registers OPS-GAP-1..OPS-GAP-10. This section classifies each gap as: **acceptable for trial** (manageable via protocol or coordinator briefing), **not applicable** (DA scope — DA is not a trial candidate), or **requires further mitigation before trial begins**.

| Gap ID | Gap | Classification | Disposition |
|---|---|---|---|
| OPS-GAP-1 | DA `final_video` not accessible through Delivery Pack | **Not applicable** | DA is NOT trial scope. The `media.final_video_url` informational note (addendum §4.3) is documented in §5 of this review for completeness. No mitigation needed for trial. |
| OPS-GAP-2 | `InMemoryClosureStore` volatile across gateway restart | **Acceptable for trial (MS portion) / Not applicable (DA portion)** | Matrix Script: managed by §6.1 no-restart constraint below. DA: not trial scope; OPS-GAP-2 amplifies the DA not-trial-capable verdict but does not create a mitigation action for trial. |
| OPS-GAP-3 | MS copy_bundle all fields `STATUS_UNRESOLVED` | **Acceptable for trial** | Coordinator briefs operators: Delivery Center copy_bundle is display-only this wave; use MS-W5 / MS-W8 closure path instead. Not a defect. No trial evidence should rely on copy_bundle content. |
| OPS-GAP-4 | MS-W3 script structure fields `STATUS_UNRESOLVED` | **Acceptable for trial** | Coordinator briefs operators: Workbench A 脚本结构区 is inspect-only; no readable Hook / Body / CTA content is expected in this wave. Not a defect — correct sentinel state. |
| OPS-GAP-5 | DA-W4 content structure `STATUS_UNRESOLVED` | **Not applicable** | DA is NOT trial scope. This gap is one of the five findings that anchor the DA not-trial-capable verdict (addendum §2.3.1 finding 1 + 2). |
| OPS-GAP-6 | DA-W3 / DA-W5 asset selection not interactive | **Not applicable** | DA is NOT trial scope. This gap is one of the five findings (addendum §2.3.1 finding 2 + 3). |
| OPS-GAP-7 | `account_id` always `STATUS_UNSOURCED` / tracked-gap (MS + DA 回填) | **Acceptable for trial (MS portion) / Not applicable (DA portion)** | Matrix Script MS-W8: coordinator briefs operators that account identity is not captured in the closure schema; expected sentinel state, not a defect. DA: not trial scope. |
| OPS-GAP-8 | DA artifact_lookup `not_implemented_phase_c` on DA delivery lanes | **Not applicable** | DA is NOT trial scope. This gap is one of the five findings (addendum §2.3.1 finding 4). |
| OPS-GAP-9 | Forbidden-token scrub uses substring match | **Acceptable for trial** | Manageable via controlled sample content per §6.4 below. Coordinator uses content that does not contain the scrubbed English nouns in first-wave samples. Any silent alteration reported as a tracked defect. |
| OPS-GAP-10 | Per-variation `final_provenance` granularity (manifest-level only) | **Acceptable for trial** | Low impact; provenance tracing is not a first-wave trial goal. No mitigation needed. |

**Conclusion:** No OPS-GAP requires further mitigation before trial begins, beyond the named protocol constraints in §6. All DA-scope gaps (OPS-GAP-1 / 5 / 6 / 8) are not applicable because Digital Anchor is not a trial candidate. The remaining Matrix Script gaps (OPS-GAP-2 / 3 / 4 / 7 / 9 / 10) are all acceptable with coordinator briefing and the §6 protocol constraints in place.

---

## 3. Hot Follow — Trial Scope (Benchmark End-to-End)

**Unchanged from addendum §2.1 and Plan A §6.1.**

Hot Follow is the benchmark end-to-end line. No restrictions apply to the core Hot Follow operator workflow. The OWC wave was forbidden from touching any Hot Follow file; zero Hot Follow files were modified across OWC-MS PR-1/2/3 and OWC-DA PR-1/2/3 (confirmed by git log isolation tests in all six PRs). Hot Follow runtime, workbench, publish hub, and reference packet are bytewise unchanged from the Plan A baseline.

**One capability addition since Plan A:** Advisory rows (D4 L4 advisory emitter) are now live via Recovery PR-1. Operators may see advisory rows where they previously saw nothing. Coordinator briefs: "Advisory rows are now real output from the L4 advisory emitter. This is a capability addition, not a defect."

**Classification:** OPERABLE END-TO-END. Reference benchmark for all comparative trial assessment.

Trial sample profiles per Plan A §7.1 samples 1 and 2 remain valid (golden-path + preserve-source). No change to Hot Follow sample validity criteria.

---

## 4. Matrix Script — Trial Scope (Limited / Constrained)

### 4.1 Operable surfaces (post-OWC update)

The following surfaces are operable for Matrix Script trial. These supersede the Plan A §3.2 "trial-eligible surfaces" table for the Matrix Script row.

| Surface | Module | Classification | Notes |
|---|---|---|---|
| Task Area three-tier projection | MS-W1 | **OPERABLE** | 脚本任务 → 变体任务 → 发布任务 truth-backed from packet. New since Plan A. |
| Task Area eight-stage state + 8-field card | MS-W2 | **OPERABLE** | Eight-stage badge + 可发布版本数 + 当前阻塞项 consume PR-1 unified `publish_readiness` producer; no invented state. New since Plan A. |
| Workbench C 预览对比区 | MS-W4 | **OPERABLE (read-view)** | Per-variation preview + recommended marker from B4 `artifact_lookup` + PR-1 unified producer. New since Plan A. |
| Workbench D 校对区 | MS-W5 | **OPERABLE** | Per-(variation, zone) `<form class="matrix-script-review-form">` writes through existing Recovery PR-3 closure endpoint; closed `REVIEW_ZONE_VALUES = {"subtitle","dub","copy","cta"}` enum is real. New since Plan A. |
| Workbench E 质检与诊断区 | MS-W6 | **OPERABLE (read-view)** | Risk items mirror `publish_readiness.blocking_advisories[]` verbatim; L4 advisory emitter (Recovery PR-1) is live. New since Plan A. |
| Delivery Center 回填 | MS-W8 | **PARTIALLY OPERABLE** | Multi-channel 回填 reads from closure `variation_feedback[]` correctly. `account_id` is always `STATUS_UNSOURCED` — see OPS-GAP-7 briefing in §6.2. Channel + publish time + URL + publish_status are readable if closure events exist. New since Plan A. |
| Phase B variation panel | Plan A §3.2 baseline | **OPERABLE** | Real axes / cells / slots per §8.A–§8.H; all seven Plan A §0.1 acceptance criteria remain in force. Unchanged by OWC. |

### 4.2 Inspect-only / display-only surfaces (post-OWC)

| Surface | Module | Classification | Gap |
|---|---|---|---|
| Workbench A 脚本结构区 | MS-W3 | **INSPECT-ONLY (STATUS_UNRESOLVED)** | Hook / Body / CTA / 关键词 / 禁用词 all render `STATUS_UNRESOLVED` sentinels. Outline Contract not landed. Operators may see the panel shell; no readable content is present. Coordinator MUST brief: this is correct sentinel state, not a defect — see §6.2 briefing table. |
| Delivery Center copy_bundle | MS-W7 | **DISPLAY-ONLY (STATUS_UNRESOLVED)** | All copy content (标题 / hashtags / CTA / 评论关键词) is `STATUS_UNRESOLVED`. Layout exists; all content is empty. Operators MUST NOT use this for copy extraction or treat it as delivery-ready copy. |

### 4.3 Matrix Script sample validity (post-OWC)

All seven Plan A §0.1 acceptance criteria remain in force verbatim:
1. Formal create-entry route (`/tasks/matrix-script/new` POST only).
2. §8.A + §8.F opaque-ref shape (four opaque-by-construction closed schemes only; `https://`, `http://`, `s3://`, `gs://` rejected at HTTP 400).
3. §8.F operator transitional convention recommended (`content://matrix-script/source/<token>`).
4. §8.C populated Phase B truth (3 canonical axes + `variation_target_count` cells + one slot per cell).
5. §8.B + §8.G mounted readable Phase B panel (real axes / cells / slots; human-readable Axes table).
6. §8.E shared-shell suppression intact (no Hot Follow stage cards / pipeline summary / Burmese deliverable strip on `kind=matrix_script`).
7. §8.D + §8.H operator brief in force.

**Eighth criterion (post-OWC, per addendum §5.2):**

A Matrix Script task is valid post-OWC trial evidence iff the following ALSO holds:
- **OWC surface rendering present.** `GET /tasks/{task_id}` for `kind=matrix_script` renders the Task Area card with `data-role="ms-three-tier-lanes"` + `data-role="ms-eight-stage"` + `data-role="ms-field-row"` visible. The Workbench renders with `data-role="matrix-script-script-structure-panel"` / `data-role="matrix-script-preview-compare-panel"` / `data-role="matrix-script-review-zone-panel"` / `data-role="matrix-script-qc-diagnostics-panel"` visible. The Delivery Center renders with `data-role="matrix-script-delivery-copy-bundle"` and `data-role="matrix-script-delivery-backfill"` visible.
- If these anchors are absent, the task was rendered against a pre-OWC build state — refresh or recreate.

**What remains inspect-only (per addendum §5.2):**
- Workbench A content fields (`STATUS_UNRESOLVED`) — inspect only; MUST NOT be reported as defects.
- Delivery Center copy_bundle subfields (`STATUS_UNRESOLVED`) — inspect only; MUST NOT be used for copy delivery.
- `account_id` on 回填 rows (`STATUS_UNSOURCED`) — labeled expected state; MUST NOT be reported as a defect.

### 4.4 Updated coordinator 口径 (Plan A §5 update for post-OWC surfaces)

The following coordinator briefing scripts supersede the relevant Plan A §5 paragraphs for surfaces that changed since the Plan A wave. Plan A §5.1 (Task Area) and §5.3 (Delivery Center) are updated; Plan A §5.2 (Workbench) is updated to cover the five OWC-MS panels.

**§5.1 Task Area (updated):**

> **What you see:** three lines listed — Hot Follow, Matrix Script, Digital Anchor.
> **What you may do:** submit Hot Follow tasks (end-to-end); submit Matrix Script tasks via the formal `/tasks/matrix-script/new` POST only.
> **What you may not do:** submit Digital Anchor tasks. The Digital Anchor card click target is hidden or disabled during trial; Digital Anchor is engineering-closeout PASS but operations-NOT-READY in this wave.
> **What has changed since the last trial wave:** Matrix Script tasks now show a full operator-language Task Area card (脚本任务 → 变体任务 → 发布任务 three-tier + 八阶段状态 + 八字段卡体). Advisory rows are now live for Hot Follow (L4 advisory emitter is active).
> **What's hidden:** vendor, model, provider, engine, route — these are runtime concerns and never appear here.

**§5.2 Workbench (updated — post-OWC five panels):**

> **What you see for Matrix Script:** five Workbench panels — Workbench A 脚本结构区 / Workbench C 预览对比区 / Workbench D 校对区 / Workbench E 质检与诊断区 / Phase B variation panel.
> **What you may do:** inspect all five panels. For Workbench C, view per-variation previews and the recommended variation marker. For Workbench D 校对区, submit review-zone feedback per (variation, zone) — this writes to the closure endpoint. For Workbench E 质检与诊断区, inspect quality advisory output (L4 advisory emitter is live).
> **What is inspect-only:** Workbench A 脚本结构区 — this panel exists but all Hook / Body / CTA / 关键词 / 禁用词 content fields show "STATUS_UNRESOLVED" labels. This is correct behavior, not an error — the content projection contract has not yet landed. MUST NOT be reported as a defect.
> **What you may not do:** expect Workbench A to show readable script content — it will not in this wave.
> **Note on account_id:** In the Delivery Center 回填 table (MS-W8), the account_id column shows a sentinel label. This is expected — account identity is not captured in the closure schema this wave.

**§5.3 Delivery Center (updated — post-OWC MS-W7 + MS-W8):**

> **What you see for Matrix Script:** two Delivery Center sections — a copy_bundle layout (MS-W7) and a multi-channel 回填 table (MS-W8).
> **copy_bundle (MS-W7):** all fields show "STATUS_UNRESOLVED". This panel exists with the correct layout; the copy projection contract has not yet landed. MUST NOT be used for copy extraction or treated as delivery-ready copy. This is correct sentinel state, not a defect.
> **回填 (MS-W8):** multi-channel publish event table. Readable if closure events exist. `account_id` column is always "STATUS_UNSOURCED" — known gap, not a defect.
> **What you may do:** inspect the 回填 table to confirm publish events are recorded correctly after MS-W5 / closure submissions.
> **What you may not do:** rely on the copy_bundle panel for any deliverable copy (display-only this wave); extract copy from the Delivery Center.

---

## 5. Digital Anchor — NOT a Trial Candidate

**The Digital Anchor verdict from the addendum is restated verbatim and is binding for this review.**

Per addendum §2.3:

> **Digital Anchor is NOT trial-capable in the current wave. The line is engineering-closeout PASS but operations-NOT-READY. The trial re-entry review must NOT plan or admit any Digital Anchor operator trial sample.**

**This review carries that verdict explicitly and without qualification.**

This is not a temporary classification awaiting clarification. It is the operations verdict for the OWC-MS + OWC-DA closeout state, anchored on the five findings in addendum §2.3.1:
1. Script generation / source path is not operationally closed.
2. Workbench panels are partitioned but not truly operable.
3. Interactive capability is insufficient for an operator session.
4. No practically usable generation result is available for operators.
5. Therefore: Digital Anchor is NOT trial-capable in the current state even though engineering closeout PASS exists.

### 5.1 Consequences for this review

| Aspect | Disposition |
|---|---|
| Real operator trial sample | NOT PERMITTED. No DA task may be submitted as a trial sample in this wave. |
| DA sample-validity criteria | NOT AUTHORED in this review. Any document defining DA trial sample profiles is rejected per addendum §5.3. |
| DA New-Tasks card click target during trial | Hidden or disabled by coordinator. The formal route `/tasks/digital-anchor/new` exists in the codebase but is not opened to operators in this trial wave. |
| DA-W7 review-zone forms during trial | NOT exercised. No DA closure events produced as trial evidence. |
| DA Delivery Center inspection | NOT exercised as trial evidence. |
| DA `media.final_video_url` path (addendum §4.3 informational) | Informational only. The actual final video URL is available via `media.final_video_url` on the publish hub payload — not an operator-visible action, and not a trial coordinator action item. Documented for future-wave reference only. |
| Future-wave prerequisites (addendum §2.3.3) | Noted but NOT authored here. The five structural prerequisites (operationally closed script-to-content-structure path; interactive role/scene selection; enumerated `final_video` Delivery Pack lane; DA artifact_lookup wired; durable closure persistence) constitute a future wave; this review does not attempt to relax or plan them. |

**Coordinator briefing (binding):**

> "Digital Anchor is engineering-closeout PASS but operations-NOT-READY. Do not submit. Do not configure. Do not consume any DA surface as trial evidence."

---

## 6. Trial Protocol Constraints — Satisfiability Confirmation

The addendum §4 protocol constraints are reproduced here with satisfiability confirmation for each.

### 6.1 No planned gateway restarts during trial sessions (addendum §4.1)

**Constraint:** Trial sessions for Matrix Script MUST NOT plan or permit gateway process restarts. Both MS and DA use `InMemoryClosureStore`; on restart, all closure records (variation feedback, review-zone submissions, publish events) are lost.

**Satisfiability:** Manageable for the planned trial window.

**Required coordinator actions:**
- Coordinate trial timing to avoid scheduled maintenance windows.
- Brief operators before session start: "Closure history (review notes and feedback submissions) is stored for the duration of the current running session. If the system restarts, closure data resets. This is by design in this wave; durable persistence is a future wave item."
- Prefer single-session trial runs. Avoid multi-day sessions for the same closure state.
- Capture screenshots / export closure state before any planned restart.

**Verdict: SATISFIABLE.** OPS-GAP-2 (MS portion) is acceptable for trial with this protocol in place.

### 6.2 Sentinel field briefing required (addendum §4.2)

**Constraint:** Coordinator MUST brief operators on the sentinel fields they will encounter before any session begins.

**Required briefings (minimum):**

| Sentinel | Surface | Required briefing |
|---|---|---|
| `STATUS_UNRESOLVED` | MS-W3 Workbench A 脚本结构区 | "This field is awaiting the Outline/copy projection contract which lands in a future wave. It is displaying the correct sentinel state, not an error." |
| `STATUS_UNRESOLVED` | MS-W7 Delivery Center copy_bundle | "The copy_bundle layout exists but all copy content fields are awaiting the copy projection contract. Do not use for copy extraction. This is correct sentinel state, not an error." |
| `STATUS_UNSOURCED` (account_id) | MS-W8 Delivery Center 回填 | "Account identity is not yet captured in the closure schema. The account_id field always shows a sentinel label. This is a known gap, not a defect." |

**Verdict: SATISFIABLE.** These are coordinator-executable briefings with no engineering prerequisites.

### 6.3 All trial samples must be fresh, valid, and correctly configured (addendum §4.4)

**Constraint:** No pre-OWC Matrix Script samples (lacking OWC surface anchors) and no pre-§8.A / pre-§8.F Matrix Script samples (invalid `source_script_ref` shapes) may be used as trial evidence.

**Satisfiability:** Satisfied by creating fresh samples via the formal `/tasks/matrix-script/new` POST after OWC-MS has merged. Samples must satisfy all eight acceptance criteria (§4.3 above): the seven Plan A §0.1 criteria plus the eighth OWC surface rendering criterion (addendum §5.2).

**Verdict: SATISFIABLE.**

### 6.4 Forbidden-token scrub substring match risk (addendum §4.5)

**Constraint:** If any trial workflow runs real operator-authored copy through MS-W5 review-zone submission forms, the forbidden-token scrub uses substring matching. Legitimate captions containing the scrubbed English nouns may be silently altered in the closure payload.

**Satisfiability:** Manageable for the first-wave trial via controlled sample content. Coordinator instructs operators to use content that does not contain the scrubbed token strings. Any silent alteration is reported as a tracked defect, not an operator error.

**Verdict: SATISFIABLE** with controlled sample content in the first-wave trial.

---

## 7. Updated Plan A §12 Readiness Conclusion (Post-OWC, Post-Addendum)

**This section updates Plan A §12 to the post-OWC, post-addendum operational posture. It is binding and supersedes the original §12 conditional verdict for the OWC-converged surfaces.**

The original Plan A §12 verdict ("CONDITIONAL — eight conditions") was authored before OWC-MS and OWC-DA landed. The eight conditions remain in force. Four additional conditions apply post-OWC (conditions 9–12 below). The updated verdicts per line are:

| Line | Final readiness verdict (post-OWC, post-addendum) |
|---|---|
| Hot Follow | **OPERABLE END-TO-END. Trial-capable.** Reference benchmark. Advisory rows (D4) now live. No restrictions on the core operator workflow. |
| Matrix Script | **LIMITED / CONSTRAINED TRIAL CANDIDATE.** Task Area (MS-W1 + MS-W2) + Workbench C/D/E (MS-W4 + MS-W5 + MS-W6) + Phase B variation panel + Delivery Center 回填 (MS-W8) all operable. Workbench A (MS-W3) and Delivery Center copy_bundle (MS-W7) are inspect-only / display-only. 12 conditions must hold for live-trial. |
| Digital Anchor | **NOT A TRIAL CANDIDATE.** Engineering closeout PASS, operations NOT-READY. No DA trial samples authorized. No DA sample-validity criteria. Five operations findings (addendum §2.3.1) anchor this verdict; it is not a temporary classification. |

**Conditions for Plan A live-trial to proceed (12 conditions — all must hold):**

*Original Plan A §12 conditions (all remain in force, some text updated for post-OWC context):*

1. **Trial coordinator briefs operators on §5 口径 verbatim** — using the post-OWC updated §5.1 / §5.2 / §5.3 wording from §4.4 of this review (supersedes Plan A §5.1–§5.3 for post-OWC surfaces).
2. **Digital Anchor New-Tasks card and `/tasks/connect/digital_anchor/new` are hidden or disabled** for the trial duration. The formal `/tasks/digital-anchor/new` route is also NOT opened to operators in this trial wave.
3. **Asset Supply / B-roll page is hidden** from operator navigation for the trial duration (unchanged from Plan A).
4. **Trial scope restricted to Hot Follow + Matrix Script only.** No Digital Anchor task creation; no DA trial samples. §7.1 samples may be adapted for post-OWC scope; §7.2 samples to avoid remain binding.
5. **Coordinator monitors for the §8 risk list** and pauses the trial if any forbidden surface activates (unchanged from Plan A).
6. **Matrix Script trial samples are fresh contract-clean samples per all eight acceptance criteria** (§4.3 of this review): seven Plan A §0.1 criteria plus the eighth OWC surface rendering criterion (addendum §5.2). Pre-§8.A, pre-§8.F, and pre-OWC samples MUST NOT be reused as trial evidence.
7. **Coordinator briefs operators on §0.2 product-meaning of `source_script_ref`** verbatim before any sample-creation session (unchanged from Plan A — `source_script_ref` is a source-script asset identity handle, not a body-input field, not a publisher-URL ingestion field, and not a currently dereferenced content address).
8. **Coordinator confirms the operator transitional convention `content://matrix-script/source/<token>`** is in use for new Matrix Script samples (unchanged from Plan A).

*Post-OWC additions:*

9. **Gateway restart constraint satisfied:** trial coordinator has confirmed no planned gateway restarts during trial sessions; operators briefed on `InMemoryClosureStore` volatility per §6.1 of this review.
10. **Sentinel field briefing completed:** coordinator has briefed operators on `STATUS_UNRESOLVED` (MS-W3 / MS-W7) and `STATUS_UNSOURCED` (MS-W8 account_id) sentinel fields before session begins, per §6.2 of this review.
11. **Workbench A inspect-only briefing completed:** coordinator has briefed operators that Workbench A 脚本结构区 content fields are `STATUS_UNRESOLVED` and MUST NOT be reported as defects. Operators understand no readable script content is available in this wave.
12. **Delivery Center copy_bundle display-only briefing completed:** coordinator has briefed operators that MS-W7 copy_bundle is display-only (layout with no content); operators MUST NOT use it for copy extraction and MUST NOT report its `STATUS_UNRESOLVED` state as a defect.

**Gate verdict: READY FOR PLAN A LIVE-TRIAL REOPEN** — pending the §8 signoff block below being filled by all four parties in the follow-on docs-only signoff PR.

Plan A live-trial MUST NOT reopen until all four §8 signoff lines are filled and committed to `main`. The follow-on docs-only signoff PR is the standard pattern (parallel to OWC-MS Closeout §11 signoff commit `b1160b3` and OWC-DA gate spec §10 signoff commit `6825005`).

---

## 8. Signoff Block

This block was filled by all four parties in the follow-on docs-only signoff PR. **Plan A live-trial reopen is now AUTHORIZED upon merge of this signoff PR to `main`.**

| Role | Name | Date | Signature / handle |
|---|---|---|---|
| Architect | Raobin | 2026-05-06 21:10 | raobin |
| Reviewer | Alisa | 2026-05-06 21:18 | alisa |
| Operations Coordinator | Jackie | 2026-05-06 21:25 | jackie |
| Product Manager | sunny | 2026-05-06 21:30 | sunny |

**What the follow-on signoff PR must do:**

1. Fill all four lines above with date and signature / handle.
2. Annotate the evidence index trial re-entry review row as SIGNED.
3. Update `CURRENT_ENGINEERING_FOCUS.md` to reflect Plan A live-trial reopen authorized.
4. Update `ENGINEERING_STATUS.md` completion log accordingly.
5. Record that Platform Runtime Assembly Wave and Capability Expansion Gate Wave remain BLOCKED pending Plan A live-trial closeout.

**What the follow-on signoff PR must NOT do:**

- Advance any OWC-MS or OWC-DA implementation item.
- Author Digital Anchor sample-validity criteria.
- Open any new implementation wave.
- Fill Plan E phase closeout signoffs A7 / UA7 / RA7 (those remain independently pending in Raobin / Alisa / Jackie / PM queue and are NOT advanced by the signoff PR).

---

## 9. References

- Plan A authority: [`docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) (including §13 post-OWC addendum reference and §14 trial re-entry review reference)
- **Binding operational baseline: [`docs/product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md`](../product/OPERATIONS_TRIAL_READINESS_POST_OWC_ADDENDUM_v1.md)**
- OWC-MS Closeout: [`docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md`](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md)
- OWC-DA Closeout: [`docs/execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md`](../execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md)
- OWC-MS gate spec: [`docs/reviews/owc_ms_gate_spec_v1.md`](owc_ms_gate_spec_v1.md)
- OWC-DA gate spec: [`docs/reviews/owc_da_gate_spec_v1.md`](owc_da_gate_spec_v1.md)
- Evidence index: [`docs/execution/apolloveo_2_0_evidence_index_v1.md`](../execution/apolloveo_2_0_evidence_index_v1.md)
