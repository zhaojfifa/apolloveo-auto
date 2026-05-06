# ApolloVeo 2.0 · Operations Trial Readiness — Post-OWC Addendum v1

Date: 2026-05-06
Status: **Documentation only. No code, no UI, no contract, no schema, no template change.**
Authority: Produced from the OWC operations-readiness alignment review (2026-05-06) using the authority stack listed in §0.
Wave position: Post-OWC-MS + OWC-DA closeout. Pre-trial re-entry review. Pre-Plan A live-trial reopen.
Relation to Plan A: This file is an **addendum** to `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`. It does NOT replace Plan A. It updates the operational trial baseline to reflect the OWC-MS and OWC-DA surface convergence landings, and must be read alongside Plan A before any trial re-entry review is authored or any live-trial session is coordinated.

---

## 0. Authority Read for This Addendum

This addendum was authored after reading the following authority stack in full:

- `CLAUDE.md` (bootloader)
- `ENGINEERING_RULES.md` (engineering governance)
- `CURRENT_ENGINEERING_FOCUS.md` (active wave + forbidden work)
- `ENGINEERING_STATUS.md` (stage / gate / completion log)
- `docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md` (OWC-MS engineering verdict + tracked gaps §8)
- `docs/execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md` (OWC-DA engineering verdict + tracked gaps §8)
- `docs/reviews/owc_ms_gate_spec_v1.md` (OWC-MS allowed + forbidden scope)
- `docs/reviews/owc_da_gate_spec_v1.md` (OWC-DA allowed + forbidden scope)
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/product/matrix_script_product_flow_v1.md`
- `docs/product/digital_anchor_product_flow_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/handoffs/apolloveo_2_0_design_handoff_v1.md`
- `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (Plan A)
- OWC-MS PR-1 / PR-2 / PR-3 execution logs (under `docs/execution/APOLLOVEO_2_0_OWC_MS_PR*`)
- OWC-DA PR-1 / PR-2 / PR-3 execution logs (under `docs/execution/APOLLOVEO_2_0_OWC_DA_PR*`)
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- The OWC operations-readiness alignment review produced 2026-05-06 (conversation artifact)

No code was written. No trial re-entry review is started by this file. No OWC implementation is reopened.

---

## 1. Status Statement

### 1.1 Engineering / product-flow closeout verdicts

| Phase | Engineering verdict | Signoff state |
|---|---|---|
| OWC-MS (MS-W1..MS-W8) | **PASS** | All four signatories (Raobin + Alisa + Jackie + PM) SIGNED — commit `b1160b3`, PR #127 |
| OWC-DA (DA-W1..DA-W9) | **PASS** | All four signatories (Raobin 2026-05-06 21:10 + Alisa 21:18 + Jackie 21:25 + PM "sunny" 21:30) SIGNED — per OWC-DA Closeout §11 |

All 17 OWC surface modules (MS-W1..W8 + DA-W1..W9) are on `main`. Both phase closeouts carry complete four-party engineering + product-flow + coordination + PM signoffs.

### 1.2 What engineering closeout PASS means

Engineering PASS on an OWC phase means:

- Every contracted product-flow module has an operator-visible `data-role` anchor in the correct template branch.
- Every field derives from authoritative projections — no invented state, no second truth sources.
- Byte-isolation, forbidden-scope, and preserved-freeze audits are all clean.
- The gate spec's binding-and-exhaustive module list is 100% on `main`.
- Test evidence meets or exceeds the per-PR floor stated in the gate spec.

Engineering PASS does **not** mean:

- Every surface field contains resolved, non-placeholder content for a given task.
- Backend artifacts are accessible to operators via every surface that names them.
- Persistence is durable across process restart.
- Interactive asset selection is wired from the workbench.
- Phase B content authoring is available from the workbench.

### 1.3 Current state: pre-trial, contract/projection constrained

**As of 2026-05-06, the system is in the following state:**

- OWC-MS and OWC-DA are engineering-closeout PASS. The surfaces exist; their content is contract/projection-aligned only.
- **Real operator trial has NOT re-opened.** The PR-5 NOT-READY verdict remains in force.
- The trial re-entry review has NOT been authored. It may begin only after PR #141 (this addendum) merges to `main` AND after explicit user hand-off; see §7.2 + §7.4 for the binding sequencing rule.
- Plan A live-trial remains BLOCKED until: (a) trial re-entry review authored; (b) signed by architect + reviewer + coordinator + PM.
- Platform Runtime Assembly Wave and Capability Expansion Gate Wave remain BLOCKED.

**Operations posture is stricter than engineering posture in this wave.** Surface-visible does not imply operationally usable. Engineering closeout PASS does not imply trial-capable. This addendum carries the operations verdict, which is more restrictive than the four-party engineering signoffs would suggest if read in isolation.

This addendum updates the operational trial baseline that the trial re-entry review must evaluate against. It does NOT open live-trial.

### 1.4 Headline operations verdict

| Line | Operations verdict |
|---|---|
| Hot Follow | **Benchmark end-to-end line.** Operationally trial-capable; reference / control line for any trial. |
| Matrix Script | **Limited / constrained trial candidate.** Partially operable — Task Area + Workbench C/D/E + 回填; Workbench A and Delivery Center copy_bundle are inspect-only / display-only. Trial scope must be explicitly narrowed and operator-briefed. |
| Digital Anchor | **NOT a trial candidate in current state.** Contract/projection-aligned only. Surface-visible but not operationally usable. Not eligible for real operator trial in this wave even though OWC-DA engineering closeout is PASS. See §2.3 for the five findings that anchor this verdict. |

---

## 2. Line-by-Line Trial Scope (Post-OWC Baseline)

### 2.1 Hot Follow — Benchmark End-to-End Line

**Role:** Benchmark end-to-end line. Operational control / reference line. Hot Follow is the only line in the system with an unqualified end-to-end operational capability this wave.

**Trial scope:** End-to-end. Intake → subtitle → dub → compose → publish → Delivery Center. No inspection-only restrictions apply to the core workflow.

**What changed from Plan A §6.1:** Nothing. The OWC wave was forbidden from touching any Hot Follow file. Zero Hot Follow files were modified across OWC-MS PR-1/2/3 and OWC-DA PR-1/2/3 (confirmed by git log isolation tests in all six PRs). Hot Follow runtime, workbench, publish hub, and reference packet are bytewise unchanged from the Plan A baseline.

**What to confirm in trial:** Advisory taxonomy (D4) is now live via Recovery PR-1. Operators may see advisory rows where they previously saw nothing. Coordinator should brief operators: advisory rows are now real output from the L4 advisory emitter, not placeholders.

**Operational classification:** OPERABLE END-TO-END. Reference benchmark for all comparative trial assessment.

---

### 2.2 Matrix Script — Limited / Constrained Trial Candidate

**Role:** Limited / constrained trial candidate. Surface-converged, partially operable production line. Operators can run the Task Area + Workbench C/D/E core workflow with a narrowed scope. Delivery Center surfaces exist but carry significant content gaps and are not delivery-truth in this wave.

**What OWC-MS added since Plan A:**

- Task Area: full three-tier projection (MS-W1) + eight-stage state + 8-field card (MS-W2) — both new since Plan A.
- Workbench: five panels now exist (MS-W3..W6). Previously, no workbench panels existed at this level of convergence.
- Delivery Center: copy_bundle layout (MS-W7) + multi-channel 回填 layout (MS-W8) — both new since Plan A.

**Operable surfaces:**

| Surface | Module | Classification | Notes |
|---|---|---|---|
| Task Area three-tier projection | MS-W1 | **OPERABLE** | 脚本任务 → 变体任务 → 发布任务 truth-backed from packet |
| Task Area eight-stage state + 8-field card | MS-W2 | **OPERABLE** | Eight-stage badge + 可发布版本数 + 当前阻塞项 all consume PR-1 unified `publish_readiness` producer; no invented state |
| Workbench C 预览对比区 | MS-W4 | **OPERABLE (read-view)** | Per-variation preview + recommended marker from B4 `artifact_lookup` + PR-1 unified producer |
| Workbench D 校对区 | MS-W5 | **OPERABLE** | Per-(variation, zone) `<form class="matrix-script-review-form">` writes through existing Recovery PR-3 closure endpoint; closed `REVIEW_ZONE_VALUES = {"subtitle","dub","copy","cta"}` enum is real |
| Workbench E 质检与诊断区 | MS-W6 | **OPERABLE (read-view)** | Risk items mirror `publish_readiness.blocking_advisories[]` verbatim; advisory emitter (Recovery PR-1) is live |

**Inspect-only / display-only surfaces:**

| Surface | Module | Classification | Gap |
|---|---|---|---|
| Workbench A 脚本结构区 | MS-W3 | **DISPLAY-ONLY with gaps** | Outline Contract for Hook / Body / CTA / 关键词 / 禁用词 not landed. All content fields show `STATUS_UNRESOLVED` sentinels with operator-language gating explanation. Operators can see the panel; no readable script content is present. |
| Delivery Center copy_bundle | MS-W7 | **DISPLAY-ONLY** | copy_bundle projection contract (caption / hashtags / CTA / comment_keywords derivation from `variation_manifest`) not landed. All MS-W7 subfields render as `STATUS_UNRESOLVED` sentinels. Panel exists with correct layout; all content is empty. Operators may NOT treat this as delivery-ready copy. |
| Delivery Center 回填 | MS-W8 | **PARTIALLY OPERABLE** | Multi-channel 回填 reads from closure `variation_feedback[]` correctly. `account_id` is always `STATUS_UNSOURCED` (the closure schema does not carry `account_id`). Channel + publish time + publish URL + publish status are readable if closure events exist. |

**Explicitly tracked limits for operator briefing:**

1. **`source_script_ref` product meaning (unchanged from Plan A §0.2):** A source-script asset identity handle. NOT a body-input field. NOT a publisher-URL ingestion field. NOT currently dereferenced. Submit using the operator transitional convention `content://matrix-script/source/<token>` or another `task://` / `asset://` / `ref://` opaque shape. External web URLs (`https://` / `http://`) and bucket schemes (`s3://` / `gs://`) are rejected at HTTP 400 by the §8.F guard — that is the guard working, not a defect.

2. **Workbench A unresolved structure fields:** On any Matrix Script task in this wave, the Workbench A 脚本结构区 panel renders the panel shell but all Hook / Body / CTA content subfields are `STATUS_UNRESOLVED`. This is correct behavior per the OWC-MS Closeout §8 tracked gap table. Operators MUST NOT report unresolved structure fields as defects — they are the expected sentinel state until Outline Contract lands.

3. **Delivery Center copy_bundle unresolved state:** The MS-W7 panel is a layout-only surface in this wave. All copy content (标题 / hashtags / CTA / 评论关键词) is `STATUS_UNRESOLVED`. Operators seeking to extract copy for publishing must use the publish-feedback closure path (MS-W5 / MS-W8), not the Delivery Center copy_bundle display.

4. **account_id capture gap:** MS-W8 `account_id` is always shown as `STATUS_UNSOURCED` (labeled with `ACCOUNT_TRACKED_GAP_EXPLANATION_ZH`). Operators will not see account identity in the 回填 table. This is a contract gap (closure schema lacks `account_id`), not a display defect.

5. **Closure store volatility (see §4):** All Matrix Script closure data (variation feedback, review-zone submissions, publish events) is in-process and non-durable. Gateway restart destroys all closure history.

**Pre-OWC Plan A scope that no longer applies:**

- Plan A §6.2 classified Matrix Script as "end-to-end except Delivery Center binding." OWC-MS has now delivered five Workbench panels and Delivery Center layout panels. The updated scope above supersedes Plan A §6.2 for these surfaces.
- Plan A §3.2 showed no Task Area card body or Workbench panels for Matrix Script. Both now exist (MS-W1..W6).
- Plan A §3.3 classified "Matrix Script Workbench Phase B variation panel — now mounts and renders real inspectable axes / cells / slots." This is preserved; in addition, the five OWC-MS panels now surround it.

**Operator scope for trial re-entry review:**

> Matrix Script trial scope post-OWC: Task Area (fully operable) + Workbench C / D / E (operable) + Workbench A (inspect-only, content unresolved) + Delivery Center 回填 (operable with account gap) + Delivery Center copy_bundle (display-only). Delivery Center remains NOT suitable for actual copy extraction or delivery-truth reliance this wave.

---

### 2.3 Digital Anchor — NOT a Trial Candidate in Current State

**Role:** **Contract/projection-aligned only. Surface-visible but not operationally usable. NOT eligible for real operator trial in this wave**, even though OWC-DA engineering closeout is PASS and all nine DA-W* modules are merged with four-party signoffs.

This is a deliberate operations correction. An earlier draft of this addendum described Digital Anchor as a "constrained smoke-trial line." That framing overclaimed operator capability and is rejected here. The corrected verdict is:

> **Digital Anchor is NOT trial-capable in the current wave. The line is engineering-closeout PASS but operations-NOT-READY. The trial re-entry review must NOT plan or admit any Digital Anchor operator trial sample.**

#### 2.3.1 Five operations findings that anchor the not-trial-capable verdict

These findings are the operational reading of the OWC-DA Closeout §8 tracked gaps + the structural absences in the DA pipeline as of 2026-05-06. Each is independently sufficient to disqualify Digital Anchor from real operator trial; together they are conclusive.

1. **Script generation / source path is not operationally closed.** A real DA operator workflow per [digital_anchor_product_flow_v1.md §4.1](digital_anchor_product_flow_v1.md) requires that script / 文案 input is converted into 讲解提纲 / 段落逻辑 / 节奏 / 强调点 — i.e. a closed source-to-content-structure path. In the current wave there is no operationally closed path: Phase B content structure authoring is not landed (DA-W4 fields show `STATUS_UNRESOLVED` for most tasks); `roles[]` / `segments[]` operator authoring is forbidden; `source_script_ref` resolution to readable content body does not exist (the same product-meaning constraint that applies to Matrix Script `source_script_ref` per Plan A §0.2 — handle, not body). An operator who creates a DA task today cannot drive script-to-structure conversion through the platform. The line cannot deliver its first product-flow stage.

2. **Workbench panels are partitioned but not truly operable.** The DA Workbench is correctly partitioned into five panels per gate spec §3 (DA-W3 角色绑定 / DA-W4 内容结构 / DA-W5 场景模板 / DA-W6 语言输出 / DA-W7 预览与校对). Surface convergence is real. **But operability is not the same as visibility.** DA-W3 and DA-W5 surface only an Asset Supply browse pointer — not an interactive selector — so role and scene cannot be configured from the workbench. DA-W4 is display-only with mostly unresolved content. DA-W6 is a read-view of language_scope with no operator authoring affordance. Only DA-W7 carries a real write-through path (review-zone forms posting to the Recovery PR-4 closure endpoint), but DA-W7 alone is a closure-feedback surface, not a content-creation surface. The five-panel partition is correct as a contract projection; it is insufficient as an operator workbench.

3. **Interactive capability is insufficient for an operator session.** A real DA operator session requires the operator to: select a role; select a scene template; review or correct content structure; review/adjust language output; submit review feedback. Of these five, only the last (DA-W7 review submission) is interactive in this wave. Role and scene are fixed at task creation time and cannot be corrected from any DA Workbench surface. Content structure cannot be authored. Language output is read-view. The interactive surface area is too narrow to constitute an operator-driven workflow — the operator's role would be limited to inspecting projections of decisions made elsewhere and submitting closure feedback after the fact.

4. **No practically usable generation result is available for operators.** The DA Delivery Center surface (DA-W8) is the canonical place an operator would expect to obtain the final DA artifact. In the current wave the `final_video` lane renders as primacy-label-only with tracked-gap explanation — the Phase C delivery binding does not enumerate a row for the composed final asset. The actual artifact is reachable only via `media.final_video_url` on the publish hub payload, which is not exposed as an operator-visible action in the DA Delivery Pack. DA artifact_lookup remains `not_implemented_phase_c`. DA-W9 回填 carries `account` and `channel` tracked-gaps. There is no operator-accessible path through the standard DA surface that delivers a usable final result. An operator cannot complete a "produce → review → deliver" loop through the visible surface.

5. **Therefore: Digital Anchor is NOT trial-capable in the current state, even though engineering closeout PASS exists.** Findings 1–4 each point at a different stage of the line where operability is missing: the source-to-structure conversion (1), the workbench-driven configuration (2 + 3), and the delivery of the produced artifact (4). The OWC-DA engineering closeout PASS verdict is correct on its own terms — every contracted surface module is on `main` with a `data-role` anchor, every projection is truth-source-clean, every byte-isolation audit holds. But surface convergence is what OWC was chartered to deliver; it is not what an operator trial requires. Operations must read the closeout PASS as "the projections are correct" — not as "operators can run a workflow." The two are different verdicts on different questions.

#### 2.3.2 Consequence: trial scope for Digital Anchor in this wave

| Aspect | Verdict |
|---|---|
| Real operator trial sample | **NOT PERMITTED.** No DA task may be submitted as a trial sample in this wave. |
| Operator-visible inspection (no submission) | Permitted with explicit "surface-inspection only — not a trial sample" labeling. Operators may open `tasks.html` and confirm the DA card renders post-OWC, may navigate to Workbench / Delivery Center and confirm the surfaces render, but MUST NOT submit, configure, or interact for trial-evidence purposes. |
| New-Tasks DA card click target during trial | Hidden or disabled by coordinator (mirrors the Plan A §6.3 disposition). The OWC formal route `/tasks/digital-anchor/new` exists in the codebase but is not opened to operators in this trial wave. |
| DA-W7 review forms during trial | NOT exercised. Closure submissions on DA tasks are not produced as trial evidence. |
| DA Delivery Pack inspection during trial | NOT exercised as trial evidence. Even surface-inspection should not include the Delivery Pack because the `final_video` access path is not operationally closed for trial purposes. |
| Coordinator briefing | Must explicitly state: "Digital Anchor is engineering-closeout PASS but operations-NOT-READY. Do not submit. Do not configure. Do not consume any DA surface as trial evidence." |

#### 2.3.3 What would unblock Digital Anchor trial readiness (out of this addendum's scope)

The following items are NOT delivered by this addendum and are NOT preconditions for the trial re-entry review of Matrix Script + Hot Follow. They are recorded as the named structural prerequisites for any future operations posture in which Digital Anchor becomes trial-capable:

1. An operationally closed script-to-content-structure path: either upstream content-structure authoring lands (Phase B authoring for `roles[]` / `segments[]` / Outline / cadence) or a deterministic Phase B authoring step (parallel to Matrix Script §8.C) is added for DA.
2. Interactive role and scene selection wired from DA-W3 / DA-W5 (replacing the read-only browse pointer with a selector backed by the Asset Library object service).
3. A `final_video` access path enumerated in the DA Delivery Pack (or a documented, supported alternative operator path that is briefed in operator-language UI, not buried in a payload field).
4. DA artifact_lookup wired (DA equivalent of Matrix Script Plan E B4) so DA delivery lanes resolve to real artifacts, not `not_implemented_phase_c`.
5. Durable closure persistence (in-process closure store retired in favor of durable backing) — same constraint as Matrix Script but applies more sharply to DA because DA's only interactive surface (DA-W7) writes to the volatile store.

These items together constitute a future wave; none of them is a single-PR scope. The trial re-entry review must not attempt to relax any of them by widening trial scope; it must classify Digital Anchor as not-trial-capable and proceed with Matrix Script + Hot Follow only.

#### 2.3.4 Surface-by-surface state (informational, not trial scope)

The DA surface state is recorded here for completeness so future addenda or trial re-entry reviews have a documented baseline. These rows describe what each DA surface DOES if an operator inspects it (in non-trial inspection mode). They do NOT define trial scope; the only DA trial scope in this wave is "no DA trial samples."

| Surface | Module | What the surface displays | Trial-relevance |
|---|---|---|---|
| Task Area 8-field card | DA-W1 | 任务标题 / Role Profile / Scene Template / Target Language / 当前版本状态 / 当前阻塞项 / 交付包状态 / 最近更新 — fields read from packet + PR-1 unified producer | NOT TRIAL SCOPE |
| Task Area eight-stage projection | DA-W2 | Eight-stage badge from `board_bucket` | NOT TRIAL SCOPE |
| Workbench A 角色绑定面 | DA-W3 | Read-view of `role_pack_ref + speaker_plan_ref`; Asset Supply browse pointer only (NOT interactive) | NOT TRIAL SCOPE |
| Workbench B 内容结构面 | DA-W4 | Display-only; STATUS_UNRESOLVED for most fields; no Phase B authoring | NOT TRIAL SCOPE |
| Workbench C 场景模板面 | DA-W5 | Display-only scene five-zone view; `scene_binding_writeback` is `not_implemented_phase_b`; Asset Supply browse pointer only | NOT TRIAL SCOPE |
| Workbench D 语言输出面 | DA-W6 | Read-view of language_scope + delivery_binding | NOT TRIAL SCOPE |
| Workbench E 预览与校对面 | DA-W7 | Real per-(role, segment) write-through forms posting to Recovery PR-4 closure endpoint; closed `REVIEW_ZONE_VALUES` enum | NOT TRIAL SCOPE — surface exists but trial samples MUST NOT exercise it |
| Delivery Pack | DA-W8 | Nine-lane Delivery Pack view with `final_video` primacy-label-only; lanes carry `STATUS_TRACKED_GAP*` sentinels | NOT TRIAL SCOPE |
| 发布回填 | DA-W9 | Read-view of closure D.1 events with `account` / `channel` tracked-gaps | NOT TRIAL SCOPE |

**Operator scope for trial re-entry review:**

> Digital Anchor scope: **NOT a trial candidate.** No DA tasks submitted, no DA closure events produced, no DA delivery surfaces consumed as trial evidence. The DA New-Tasks card click target should be hidden or disabled during trial. Engineering closeout PASS does not translate to trial readiness for this line in this wave; the trial re-entry review must explicitly carry this verdict and must NOT author DA sample-validity criteria, since no DA samples are valid trial evidence.

---

## 3. Visible / Usable / Operable Matrix

For each line and surface area, the classification is:
- **Operable:** operator can take real action with real data; result is meaningful AND surface is in trial scope.
- **Usable:** operator can interact but results may be partially incomplete / sentinel-filled; surface is in trial scope.
- **Inspect-only / display-only:** operator can see the surface; cannot take meaningful action; content may be unresolved; surface MAY be in trial scope as a read-only reference.
- **Not present / blocked:** surface does not exist for this line in this wave.
- **Not trial scope (DA):** Digital Anchor surfaces all carry this classification. The DA column entries describe what each surface DOES if rendered (informational only). Per §2.3, Digital Anchor is NOT a trial candidate in the current wave; the DA column is included for surface-state documentation, NOT trial scoping. Read every DA cell as "this surface technically renders X, but the operator MUST NOT consume it as trial evidence in this wave."

### 3.1 Task Area

| Surface | Hot Follow | Matrix Script | Digital Anchor (NOT TRIAL SCOPE) |
|---|---|---|---|
| Task list + line filter | **Operable** | **Operable** | Surface renders; not trial scope |
| Three-tier / eight-stage state projection | **Operable** | **Operable** (MS-W1 + MS-W2) | Surface renders (DA-W1 + DA-W2); not trial scope |
| 8-field operator-language card body | **Operable** | **Operable** (MS-W2) | Surface renders (DA-W1); not trial scope |
| Blocked / ready / publishable tri-state | **Operable** | **Operable** | Surface renders; not trial scope |
| Entry: new task creation | **Operable** | **Operable** (formal `/tasks/matrix-script/new` POST only) | Route exists (`/tasks/digital-anchor/new`); **MUST be hidden / disabled during trial** |
| Quick actions (进入工作台 / 跳交付中心) | **Operable** | **Operable** | Surface renders; not trial scope |

### 3.2 Workbench

| Panel | Hot Follow | Matrix Script | Digital Anchor (NOT TRIAL SCOPE) |
|---|---|---|---|
| A — content structure / 脚本结构区 / 角色绑定面 | **Operable** | **Inspect-only** (STATUS_UNRESOLVED, Outline Contract gap) | Read-view; Asset Supply browse pointer only; not interactive; not trial scope |
| B — scene plan / variation panel / 内容结构面 | **Operable** | **Operable** (Phase B variation panel — real axes/cells/slots) | Display-only; STATUS_UNRESOLVED; no Phase B authoring; not trial scope |
| C — audio / preview compare / 场景模板面 | **Operable** | **Usable** (MS-W4 read-view, recommended marker live) | Display-only; `scene_binding_writeback` is `not_implemented_phase_b`; not trial scope |
| D — language / 校对区 / 语言输出面 | **Operable** | **Operable** (MS-W5 real write-through forms) | Read-view of language_scope; not trial scope |
| E — QC / diagnostics / 预览与校对面 | **Operable** | **Usable** (MS-W6 advisory-backed read-view) | Real write-through forms exist (DA-W7); **MUST NOT be exercised in trial** |
| Variation panel (Matrix Script specific) | Not present | **Operable** (Plan A §3.2 baseline, real axes/cells/slots per §8.A–§8.H) | Not present |

### 3.3 Delivery Center

| Panel | Hot Follow | Matrix Script | Digital Anchor (NOT TRIAL SCOPE) |
|---|---|---|---|
| Final video primary lane | **Operable** | **Inspect-only** (artifact_lookup still `not_implemented_phase_c`) | `final_video` primacy-label-only; actual artifact at `media.final_video_url`; not trial scope |
| Required deliverables | **Operable** | **Inspect-only** (STATUS_UNRESOLVED) | STATUS_TRACKED_GAP* sentinels; not trial scope |
| Optional / non-blocking deliverables (scene_pack etc.) | **Operable** | **Inspect-only** | Surface renders; not trial scope |
| copy_bundle / delivery pack layout | Not applicable | **Display-only** (all subfields STATUS_UNRESOLVED) | Nine-lane layout with tracked-gap sentinels; not trial scope |
| 回填 / publish feedback multi-channel | **Operable** | **Usable** (MS-W8 reads closure; account always STATUS_UNSOURCED) | DA-W9 reads closure; account / channel tracked-gap; not trial scope |
| Publish action button | **Operable** | **Usable** (consumes authoritative projection; no copy delivery) | Surface renders; **MUST NOT be exercised in trial** |

### 3.4 Asset Supply Dependency Surfaces

| Concern | Classification | Notes |
|---|---|---|
| Asset Supply browse (`/assets`) | **Inspect-only** | Recovery PR-2 shipped minimum capability: browse + opaque `asset://` reference. No interactive selection wired from Workbench panels yet. |
| Promote intent submission | **Not operable** | Approval path is restricted to `requested → rejected` only (Recovery PR-2 §9.1.6). No approval path exists until Asset Library write path lands in a later wave. |
| Role/scene select from Workbench A / C | **Not operable; reinforces DA not-trial-capable verdict** | DA-W3 and DA-W5 surface browse pointer only; interactive selector is a future operator-driven authoring wave item. The absence of this capability is one of the five findings (§2.3.1 finding 3) anchoring the DA not-trial-capable verdict. |
| Matrix Script Asset Supply reference | **Not applicable** | MS creates `content://` opaque handles via Plan E F2 minting flow; no direct Asset Supply dependency in the MS workbench panels. |

---

## 4. Trial Protocol Constraints

These constraints are **binding** for any trial session coordinated after this addendum is published. Violating them may produce misleading trial evidence or unexplained data loss.

### 4.1 No planned gateway restarts during trial sessions

**Constraint:** Trial sessions for Matrix Script and Digital Anchor MUST NOT plan or permit gateway process restarts.

**Why:** Both MS and DA use `InMemoryClosureStore` — a process-local, in-memory closure store. This is acknowledged as a tracked gap in both OWC closeouts (OWC-MS Closeout §8; OWC-DA Closeout §8), deferred to the Platform Runtime Assembly Wave (durable persistence). On gateway restart, ALL closure records are lost: variation feedback rows, review-zone submissions, publish events, DA role_feedback, segment_feedback, feedback_closure_records. This data loss would look like a system defect to operators if they are not briefed.

**Mitigation:**
- Coordinate trial timing to avoid scheduled maintenance windows.
- Brief operators: "Closure history (your review notes and feedback submissions) is stored for the duration of the current running session. If the system restarts, closure data resets. This is by design in this wave; durable persistence is a future wave item."
- Single-session trial runs preferred. Avoid multi-day sessions for the same closure state.
- If coordinator needs to test closure persistence: capture screenshots / export closure state before any planned restart.

### 4.2 Operators must be briefed on tracked-gap sentinel fields

**Constraint:** Before operators begin any session, coordinator MUST brief them on the sentinel fields they will encounter. Operators who have not been briefed will interpret sentinel labels as system errors.

**Required briefing items (minimum):**

| Sentinel | Surface | Briefing text |
|---|---|---|
| `STATUS_UNRESOLVED` | MS-W3 Workbench A, MS-W7 Delivery Center | "This field is awaiting the Outline/copy projection contract which lands in a future wave. It is displaying the correct sentinel state, not an error." |
| `STATUS_TRACKED_GAP` / `STATUS_TRACKED_GAP_*` | DA-W8 Delivery Pack lanes | "These lanes are intentionally labeled as deferred items. They are not missing — they are correctly marked as future-wave scope." |
| `STATUS_UNSOURCED` (account_id) | MS-W8 回填, DA-W9 回填 | "Account identity is not yet captured in the closure schema. This is a known gap, not a defect." |
| `not_implemented_phase_b` (DA-W5) | DA Workbench C 场景模板面 | "Scene template writeback is a Phase B future item. The scene is bound at task creation; it cannot be changed from the workbench in this wave." |

### 4.3 DA final_video access path (informational only — DA is not trial scope)

**Status correction:** An earlier draft of this addendum framed the DA `final_video` access path as a coordinator briefing item required for DA Delivery Center trial sessions. That framing implied DA Delivery Center inspection was a trial activity. **It is not** — per §2.3, Digital Anchor is NOT a trial candidate in the current wave, and DA Delivery Center is not consumed as trial evidence.

**The underlying surface state (informational, for future-wave reference):**
- DA-W8 Delivery Pack renders `final_video` as a primacy-label-only lane with a tracked-gap explanation.
- The Phase C delivery binding does not enumerate a composed final asset row.
- The actual final video URL is available via `media.final_video_url` on the publish hub payload.
- This is finding 4 in §2.3.1: there is no operator-accessible path through the standard DA surface that delivers a usable final result. This is one of the five reasons DA is not trial-capable in this wave.

**No trial coordinator action required this wave.** No DA trial session is planned. The `media.final_video_url` access path is documented here only for future reference once DA becomes trial-capable in a later wave (per §2.3.3, this requires an enumerated `final_video` lane in the Delivery Pack or a documented operator-language alternative path — not just a payload field name).

### 4.4 All trial samples must be fresh, valid, and correctly configured

**Constraint:** No pre-OWC Matrix Script samples and no pre-§8.A / pre-§8.F Matrix Script samples may be used as trial evidence. See §5 for sample validity criteria.

**Why:** Pre-OWC Matrix Script samples do not carry the OWC-MS-converged surface rendering. Pre-§8.A / pre-§8.F Matrix Script samples carry invalid `source_script_ref` shapes. (Digital Anchor sample validity is a non-question in this wave because no DA samples are valid trial evidence — see §2.3.2.)

### 4.5 Forbidden-token scrub substring match risk

**Constraint:** If any trial workflow runs real operator-authored copy through MS-W5 or DA-W7 review-zone submission forms, coordinator should be aware that the forbidden-token scrub uses substring matching. Legitimate captions containing the scrubbed English nouns may be silently altered in the closure payload.

**Mitigation:** For the first trial wave, use controlled sample content that does not contain the scrubbed token strings. Report any silent alteration as a tracked defect, not an operator error.

---

## 5. Trial Sample Validity — Post-OWC Update

### 5.1 Hot Follow sample validity (unchanged from Plan A §0.1)

Plan A §0.1 / §7.1 sample 1 and 2 remain valid. No change required.

### 5.2 Matrix Script sample validity (updated from Plan A §0.1)

Plan A §0.1 defined seven acceptance criteria for a valid Matrix Script trial sample. All seven remain in force. The following additions apply post-OWC:

**Additional acceptance criterion 8 (post-OWC):**
A Matrix Script task is valid post-OWC trial evidence iff the following ALSO holds:
- **OWC surface rendering present.** `GET /tasks/{task_id}` for `kind=matrix_script` renders the Task Area card with `data-role="ms-three-tier-lanes"` + `data-role="ms-eight-stage"` + `data-role="ms-field-row"` visible. The Workbench renders five panels with `data-role="matrix-script-script-structure-panel"` / `data-role="matrix-script-preview-compare-panel"` / `data-role="matrix-script-review-zone-panel"` / `data-role="matrix-script-qc-diagnostics-panel"` visible. The Delivery Center renders with `data-role="matrix-script-delivery-copy-bundle"` and `data-role="matrix-script-delivery-backfill"` visible.
- If these anchors are absent, the task was rendered against a pre-OWC build state — refresh or recreate.

**What remains inspect-only for MS trial samples:**
- Workbench A 脚本结构区 content fields (`STATUS_UNRESOLVED`) — inspect only; MUST NOT be reported as defects.
- Delivery Center copy_bundle subfields (`STATUS_UNRESOLVED`) — inspect only; operators MUST NOT use this as copy delivery.
- account_id on 回填 rows (`STATUS_UNSOURCED`) — labeled expected state; MUST NOT be reported as a defect.

### 5.3 Digital Anchor sample validity — NO valid DA trial samples exist in this wave

**Status correction:** An earlier draft of this addendum authored seven DA sample-validity criteria parallel to the Matrix Script criteria, plus a ten-step suggested DA trial workflow. That framing implied DA had a defined trial sample shape. **It does not** — per §2.3, Digital Anchor is NOT a trial candidate in the current wave. There is no valid DA trial sample.

**The corrected statement:**

> **No Digital Anchor task is a valid trial sample in this wave.** The trial re-entry review must NOT author DA sample-validity criteria. Any document or runbook that defines a DA trial sample profile is rejected as inconsistent with this addendum's operations verdict.

This is not a temporary classification awaiting clarification. It is the operations verdict for the OWC-MS + OWC-DA closeout state, anchored on the five findings in §2.3.1. The line is engineering-closeout PASS but operations-NOT-READY; trial samples require operations-READY, not engineering-PASS.

**Consequences:**

| Concern | Disposition |
|---|---|
| DA task creation during trial | NOT PERMITTED. New-Tasks DA card click target hidden / disabled by coordinator. |
| Pre-existing DA tasks in trial environment | NOT consumed as trial evidence. May exist in the system; trial coordinator does not include them in the §7.1 sample roster. |
| DA-W7 review-zone form submissions | NOT exercised. No closure events produced as trial evidence. |
| DA Delivery Center inspection | NOT exercised as trial evidence. The `final_video` access path question (§4.3) does not arise this wave because no DA Delivery Center trial inspection happens. |
| DA surface rendering verification | Permitted as a non-trial smoke check ONLY (engineering-team verification that OWC-DA `data-role` anchors render correctly post-deploy). Coordinator labels this explicitly as "engineering verification, not trial evidence." |

**What unblocks DA sample validity authoring in a future wave:** see §2.3.3. Until those five structural prerequisites are addressed, no DA sample-validity criteria may be authored, and any draft attempting to author them is to be rejected.

---

## 6. Non-Blocking-for-Closeout but Blocking-for-Ops Gaps

These gaps are documented in both OWC closeouts as non-blocking tracked items. They are **not blocking** for engineering closeout. They ARE operationally significant for any real operator trial. Each gap is classified by its trial impact.

### 6.1 Critical (would block end-to-end workflow for the named scenario)

**DA-aggregating finding (overrides per-DA-gap classifications):** OPS-GAP-1 + OPS-GAP-5 + OPS-GAP-6 + OPS-GAP-8, taken together with the absence of an operationally closed script-to-content-structure path (§2.3.1 finding 1) and the insufficient interactive surface area (§2.3.1 finding 3), classify Digital Anchor as NOT trial-capable in this wave. The DA-specific gaps below are NOT gaps to be mitigated for trial coordination — they are evidence that DA does not meet the operations bar for trial entry. No coordinator briefing or trial protocol can compensate for these gaps within this wave.

| Gap ID | Gap | Lines affected | What it blocks |
|---|---|---|---|
| OPS-GAP-1 | **DA `final_video` not accessible through Delivery Pack** | Digital Anchor only | Operators cannot complete "deliver and download final video" through the standard Delivery Center surface. The actual artifact is at `media.final_video_url` — a non-obvious path. **Operations classification: contributes to the DA not-trial-capable verdict (§2.3.1 finding 4).** |
| OPS-GAP-2 | **`InMemoryClosureStore` volatile across gateway restart** | Matrix Script + Digital Anchor | All MS and DA closure history lost on gateway restart. For Matrix Script: managed by the §4.1 trial protocol constraint. For Digital Anchor: amplifies the not-trial-capable verdict because DA's only interactive surface (DA-W7) writes to the volatile store. |
| OPS-GAP-3 | **MS copy_bundle all fields `STATUS_UNRESOLVED`** | Matrix Script only | Operators cannot extract actual copy (title / hashtags / CTA / comment_keywords) from the Delivery Center. The surface exists but delivers no content. Any MS trial workflow requiring actual copy delivery is blocked. |

### 6.2 Significant (degrades trial quality; does not block the core loop but will confuse operators)

| Gap ID | Gap | Lines affected | What it degrades |
|---|---|---|---|
| OPS-GAP-4 | **MS-W3 script structure fields `STATUS_UNRESOLVED`** | Matrix Script only | Operators expecting to review the Hook / Body / CTA / 关键词 / 禁用词 content structure in the Workbench see empty panels. Core MS readability without the Outline Contract is limited to the variation panel + review forms. |
| OPS-GAP-5 | **DA-W4 content structure fields `STATUS_UNRESOLVED`** | Digital Anchor only | Workbench B is display-only with mostly unresolved content. **Operations classification: contributes to the DA not-trial-capable verdict (§2.3.1 finding 1 + finding 2). Not a coordinator briefing item; not mitigable for trial coordination this wave.** |
| OPS-GAP-6 | **DA-W3 / DA-W5 asset selection not interactive** | Digital Anchor only | Workbench A and C surface only an Asset Supply browse pointer; no interactive selector. **Operations classification: contributes to the DA not-trial-capable verdict (§2.3.1 finding 2 + finding 3). Not a coordinator briefing item; not mitigable for trial coordination this wave.** |
| OPS-GAP-7 | **account_id always `STATUS_UNSOURCED` / tracked-gap (MS + DA 回填)** | Matrix Script + Digital Anchor | Operators cannot identify which account published the content from the 回填 tables. For Matrix Script: a tracked sentinel-state to brief. For Digital Anchor: not in trial scope this wave. |
| OPS-GAP-8 | **DA artifact_lookup `not_implemented_phase_c` on DA delivery lanes** | Digital Anchor only | DA delivery binding lanes that depend on artifact lookup show tracked-gap sentinels. **Operations classification: contributes to the DA not-trial-capable verdict (§2.3.1 finding 4). Not a coordinator briefing item; not mitigable for trial coordination this wave.** |

### 6.3 Low impact (known regression risk; unlikely to affect first-wave trial if coordinator manages content)

| Gap ID | Gap | Lines affected | What it risks |
|---|---|---|---|
| OPS-GAP-9 | **Forbidden-token scrub uses substring match** | Matrix Script + Digital Anchor | Legitimate captions containing scrubbed English nouns may be silently altered in closure payloads. Risk is per-payload; manageable via controlled sample content. |
| OPS-GAP-10 | **Per-variation `final_provenance` granularity (manifest-level only)** | Matrix Script only | MS-W4 preview compare shows a per-variation `per_cell_artifact_granularity_note_zh` note. Multi-variation provenance is at manifest level, not variation level. Low impact unless trial specifically tests provenance tracing. |

---

## 7. Recommendation for Next Step

### 7.1 What this addendum establishes

This addendum establishes the **post-OWC operational trial baseline** with a stricter operations posture than the engineering closeout PASS verdicts on their own would suggest:

- **Hot Follow:** benchmark end-to-end line. Trial-capable. Reference / control line for trial.
- **Matrix Script:** limited / constrained trial candidate. Partially operable; trial scope must be explicitly narrowed (Task Area + Workbench C/D/E + 回填 only; Workbench A and Delivery Center copy_bundle inspect-only / display-only) and operator-briefed on closure store volatility, sentinel fields, and unresolved-content disposition.
- **Digital Anchor:** **NOT a trial candidate in current state.** Engineering closeout PASS, operations NOT-READY. Surface-visible but not operationally usable. The five findings in §2.3.1 anchor this verdict; OPS-GAP-1 / 5 / 6 / 8 are evidence of, not mitigations for, the not-trial-capable state.

This addendum supersedes Plan A §6.2 (Matrix Script — narrows scope), Plan A §6.3 (Digital Anchor — supersedes the prior "inspection-only" framing with the "NOT a trial candidate" framing now grounded in OWC tracked gaps), and Plan A §7.1 (trial samples). Plan A's §0.1 / §0.2 (Matrix Script sample validity and `source_script_ref` product meaning), §6.1 (Hot Follow), §8 (risks and mitigations), and §9 (next gate conditions) remain in force unchanged.

### 7.2 What the trial re-entry review must do

**Sequencing (binding):** The trial re-entry review may begin only after PR #141 (this addendum) merges to `main` AND after explicit user hand-off. Both preconditions must hold; either alone is insufficient. While PR #141 is open, no trial re-entry review work may begin, even if the hand-off has been issued.

When both preconditions hold, the formal trial re-entry review (the next docs-only step) must:

1. **Evaluate against this updated baseline.** The trial re-entry review must cite this addendum as the operational baseline and confirm which ops gaps are acceptable for trial vs which require further mitigation before trial begins.
2. **Carry the DA not-trial-capable verdict explicitly.** The trial re-entry review must NOT widen DA scope, MUST NOT author DA sample-validity criteria, and MUST NOT plan or admit any DA trial sample. Any DA-related content in the trial re-entry review must be limited to (a) restating §2.3 verdict; (b) confirming the §4.3 informational-only treatment of `media.final_video_url`; (c) noting the §2.3.3 future-wave prerequisites without authoring them.
3. **Define the Matrix Script trial scope precisely.** Operating on the Hot Follow + Matrix Script line set only. Brief coordinator briefing scripts (Plan A §5 口径 update) covering MS Task Area, MS Workbench A inspect-only, MS Workbench C/D/E operability, MS Delivery Center copy_bundle display-only state, MS Delivery Center 回填 with account gap.
4. **Confirm the trial protocol constraints (§4) are satisfiable in the planned trial environment.** Specifically: confirm gateway restart risk is manageable for the trial window for Matrix Script. Confirm DA card click target is hidden / disabled.
5. **Update Plan A §12 readiness conclusion.** The trial re-entry review must update the Plan A §12 final readiness conclusion to reflect the post-OWC, post-addendum operational posture, including the explicit "DA NOT trial-capable" verdict.

### 7.3 What this addendum does NOT unlock

This addendum is documentation only. It does NOT:

- Open Plan A live-trial. Live-trial requires the trial re-entry review to be authored and signed by architect + reviewer + coordinator + PM.
- Reopen OWC-MS or OWC-DA implementation.
- Advance Platform Runtime Assembly Wave.
- Advance Capability Expansion Gate Wave.
- Close OPS-GAP-1..OPS-GAP-10 — those gaps remain open and are correctly classified as future-wave scope.

### 7.4 Precondition summary for trial re-entry review to open

| Precondition | Status |
|---|---|
| OWC-MS Closeout MS-A1..MS-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; MS-A7 signed commit `b1160b3` |
| OWC-DA Closeout DA-A1..DA-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; DA-A7 signed per §11 (2026-05-06) |
| OWC-DA Closeout merged to `main` | **SATISFIED** — PR #139 squash `f5e86a5`; docs-only housekeeping PR #140 also merged |
| Pre-trial ops-readiness review produced | **SATISFIED** — OWC operations-readiness alignment review 2026-05-06 |
| Pre-trial ops addendum (this document) authored | **SATISFIED** — authored 2026-05-06 in PR #141 |
| Pre-trial ops addendum (this document) merged to `main` (PR #141) | **PENDING** — PR #141 is currently OPEN; sequencing requires PR #141 to merge before any trial re-entry review work may begin |
| Explicit user hand-off for trial re-entry review | PENDING — the next explicit user instruction; must be issued AFTER PR #141 merges |

**Sequencing rule (binding):** the trial re-entry review may begin only after PR #141 merges to `main` AND after explicit user hand-off. Both preconditions must hold concurrently. Issuing a hand-off while PR #141 is still open does not unblock the trial re-entry review; the merge precondition is independent of the hand-off precondition and neither substitutes for the other.

---

## 8. References

- Plan A authority: [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- OWC-MS Closeout (tracked gaps §8): [docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md)
- OWC-DA Closeout (tracked gaps §8): [docs/execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_DA_PHASE_CLOSEOUT_v1.md)
- OWC-MS gate spec: [docs/reviews/owc_ms_gate_spec_v1.md](../reviews/owc_ms_gate_spec_v1.md)
- OWC-DA gate spec: [docs/reviews/owc_da_gate_spec_v1.md](../reviews/owc_da_gate_spec_v1.md)
- Matrix Script product flow: [docs/product/matrix_script_product_flow_v1.md](matrix_script_product_flow_v1.md)
- Digital Anchor product flow: [docs/product/digital_anchor_product_flow_v1.md](digital_anchor_product_flow_v1.md)
- Operator-visible surfaces: [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md)
- Top-level business flow: [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- Evidence index: [docs/execution/apolloveo_2_0_evidence_index_v1.md](../execution/apolloveo_2_0_evidence_index_v1.md)
