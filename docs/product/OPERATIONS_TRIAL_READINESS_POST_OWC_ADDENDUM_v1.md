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

- OWC-MS and OWC-DA are engineering-closeout PASS. The surfaces exist.
- **Real operator trial has NOT re-opened.** The PR-5 NOT-READY verdict remains in force.
- The trial re-entry review has NOT been authored. It is the next docs-only step.
- Plan A live-trial remains BLOCKED until: (a) trial re-entry review authored; (b) signed by architect + reviewer + coordinator + PM.
- Platform Runtime Assembly Wave and Capability Expansion Gate Wave remain BLOCKED.

This addendum updates the operational trial baseline that the trial re-entry review must evaluate against. It does NOT open live-trial.

---

## 2. Line-by-Line Trial Scope (Post-OWC Baseline)

### 2.1 Hot Follow — Benchmark End-to-End Line

**Role:** Operational control line. Hot Follow is the only line in the system with an unqualified end-to-end operational capability this wave.

**Trial scope:** End-to-end. Intake → subtitle → dub → compose → publish → Delivery Center. No inspection-only restrictions apply to the core workflow.

**What changed from Plan A §6.1:** Nothing. The OWC wave was forbidden from touching any Hot Follow file. Zero Hot Follow files were modified across OWC-MS PR-1/2/3 and OWC-DA PR-1/2/3 (confirmed by git log isolation tests in all six PRs). Hot Follow runtime, workbench, publish hub, and reference packet are bytewise unchanged from the Plan A baseline.

**What to confirm in trial:** Advisory taxonomy (D4) is now live via Recovery PR-1. Operators may see advisory rows where they previously saw nothing. Coordinator should brief operators: advisory rows are now real output from the L4 advisory emitter, not placeholders.

**Operational classification:** OPERABLE END-TO-END. Reference benchmark for all comparative trial assessment.

---

### 2.2 Matrix Script — Constrained Operator Trial

**Role:** Surface-converged, partially operable production line. Operators can run the Task Area + Workbench core workflow. Delivery Center surfaces exist but carry significant content gaps.

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

### 2.3 Digital Anchor — Surface-Readiness / Constrained Smoke-Trial Line

**Role:** Surface-convergence confirmed line. All nine OWC-DA modules exist. This is NOT a full end-to-end operational line in this wave. Operators may run a smoke trial that exercises Task Area, Workbench E review forms, and Delivery Center inspection — but significant authoring and artifact-resolution capabilities are absent.

**What OWC-DA added since Plan A:**

Plan A §6.3 classified Digital Anchor as "**inspection only. Operators may open the New-Tasks landing page and confirm the Digital Anchor card exists. They MUST NOT click through to submit.**" This is fundamentally superseded by OWC-DA. The following capabilities now exist:

- Task Area: 8-field card (DA-W1) + eight-stage projection (DA-W2).
- Workbench: five panels (DA-W3..W7), including the DA-W7 review forms that write through the Recovery PR-4 closure endpoint.
- Delivery Center: Delivery Pack assembly view (DA-W8) + 发布回填 multi-channel view (DA-W9).
- Formal task creation route (`/tasks/digital-anchor/new`) shipped by Recovery PR-4 — operators may now create and submit DA tasks.

**Operable surfaces:**

| Surface | Module | Classification | Notes |
|---|---|---|---|
| Task Area 8-field card | DA-W1 | **OPERABLE** | 任务标题 / Role Profile / Scene Template / Target Language / 当前版本状态 / 当前阻塞项 / 最近更新 truth-backed. 当前版本状态 reads `board_bucket` from PR-1 unified producer. 交付包状态 now shows real DA-W8 delivery pack state (sentinel upgraded by PR-3 landing). |
| Task Area eight-stage projection | DA-W2 | **OPERABLE** | Eight-stage badge reads `board_bucket` from PR-1 unified producer. Correct mapping to `输入已提交 / 内容结构已生成 / 场景计划已生成 / 角色/声音已绑定 / 多语言版本生成中 / 合成完成 / 可交付 / 已归档`. |
| Workbench A 角色绑定面 | DA-W3 | **OPERABLE (read-view, subject to data availability)** | Reads from existing `role_pack_ref + speaker_plan_ref`. If these are populated on the task, the panel renders Role Profile / 形象风格 / 声音 preset / 表达风格 / 情绪 correctly. If not populated, status sentinels appear. |
| Workbench D 语言输出面 | DA-W6 | **OPERABLE (read-view)** | Target Language / Subtitle Strategy / Terminology / multi-language navigator surface from `language_scope` + delivery_binding rows. Subtitle-Strategy enum derives from `capability_plan` closed set (`SUBTITLE_STRATEGY_REQUIRED / OPTIONAL / DISABLED / UNKNOWN`). |
| Workbench E 预览与校对面 | DA-W7 | **OPERABLE** | Per-(role, segment) `<form class="digital-anchor-review-form">` writes through the existing Recovery PR-4 `POST /api/digital-anchor/closures/{task_id}/events` endpoint. Five review zones (试听 / 视频预览 / 字幕校对 / 表达节奏复核 / 质检) are real forms. This is the **primary operator-interaction surface** for DA workflow in this wave. |
| 发布回填 | DA-W9 | **PARTIALLY OPERABLE** | Renders per-row closure data from `role_feedback[]` / `segment_feedback[]` / `feedback_closure_records[]` D.1 events. `account` always tracked-gap (closure schema lacks `account_id`). `channel` tracked-gap when no `metrics_snapshot.channel_id` present. Channel + publish time + publish URL + publish status readable if closure events exist. |

**Read-only / display-only / inspect-only surfaces:**

| Surface | Module | Classification | Gap |
|---|---|---|---|
| Workbench A 角色绑定面 — Asset Supply select | DA-W3 | **READ-VIEW (no interactive selection)** | Asset Supply selection beyond read-only browse is not landed. The Asset Supply browse pointer is present but is NOT an interactive selector. Operators can see the role binding hint but cannot select or change the role from within the Workbench A panel. Role binding is fixed at task creation time for this wave. |
| Workbench B 内容结构面 | DA-W4 | **DISPLAY-ONLY with structural gaps** | Phase B authoring for Outline / 段落结构 / 强调点 / 节奏 bodies is not landed. Fields show `STATUS_RESOLVED / STATUS_UNRESOLVED / STATUS_OPAQUE_REF` per section depending on what is bound. No operator authoring of `roles[]` / `segments[]` is available from this panel — explicitly forbidden in OWC scope. `roles[]` / `segments[]` are read-only surfaces only. |
| Workbench C 场景模板面 | DA-W5 | **DISPLAY-ONLY (browse pointer only)** | Scene five-zone read-view (布局 / 背景 / 信息区 / 标题区 / 辅助区) bound to `scene_template_ref` indirection. Status shows `STATUS_TEMPLATE_BOUND / STATUS_GENERIC_REF_ONLY / STATUS_TEMPLATE_PENDING` depending on `entry.scene_binding_hint`. The Asset Supply browse pointer is present but is NOT an interactive selector. `scene_binding_writeback` shows `not_implemented_phase_b`. Scene is fixed at task creation time for this wave. |
| Delivery Center Delivery Pack | DA-W8 | **DISPLAY-ONLY — see §4 for final_video access** | Nine-lane Delivery Pack view (final_video / subtitle / dubbed_audio / metadata / manifest / pack / role_usage / scene_usage / language_usage) renders with `STATUS_RESOLVED / STATUS_TRACKED_GAP / STATUS_TRACKED_GAP_SCENE / STATUS_TRACKED_GAP_LANGUAGE / STATUS_TRACKED_GAP_ROLES` per lane. **`final_video` is primacy-label-only with tracked-gap explanation — the actual final video artifact is NOT accessible through this surface.** See §4.4 for the correct operator access path. Operators may NOT treat this as a download / delivery surface for the final video in this wave. |

**Explicitly tracked limits for operator briefing:**

1. **Non-interactive role/scene selection:** Role binding (DA-W3) and scene template (DA-W5) are read-only views of what was bound at task creation. Operators cannot select a different role or scene from the workbench. If a task has an incorrect role or scene binding, it cannot be corrected in-session — the operator must create a new task with the correct configuration.

2. **Unresolved Workbench B content structure fields:** DA-W4 shows Outline / cadence / emphasis fields as `STATUS_UNRESOLVED` unless upstream content structure has been resolved by the production pipeline. Most DA tasks in the trial environment will show unresolved content structure fields. This is correct sentinel behavior; operators MUST NOT report these as defects.

3. **DA-W8 final_video access path — critical operator briefing item:** The Delivery Pack (DA-W8) renders `final_video` as a primacy lane label with tracked-gap explanation. It does NOT expose the final video URL. The actual final video artifact is accessible via `media.final_video_url` on the publish hub payload — this is the correct path for operators who need to access the final DA video. Coordinator MUST brief operators on this access path before any DA trial session. An operator navigating to the Delivery Center and seeing only the label will otherwise conclude the final video is missing; it is not missing — it is accessible through a different surface path.

4. **account / channel capture gaps:** Both DA-W9 `account` (always tracked-gap) and `channel` (tracked-gap when no `metrics_snapshot.channel_id`) are correctly labeled sentinel states. Operators will not see account identity in the 回填 table. This is a contract-layer gap (closure schema lacks `account_id`; `CHANNEL_METRICS_KEYS` excludes `channel_id`), not a display defect.

5. **DA artifact_lookup is `not_implemented_phase_c`:** Per OWC-DA Closeout §8: "The Digital Anchor side keeps `artifact_lookup='not_implemented_phase_c'` because OWC-DA scope is read-only consumption." DA delivery lanes that depend on artifact lookup show tracked-gap sentinels. Future Plan E equivalent phase for DA B4 is required; out of this wave's scope.

6. **Closure store volatility (see §4):** All DA closure data (role_feedback, segment_feedback, feedback_closure_records, DA-W7 review-zone submissions) is in-process and non-durable. Gateway restart destroys all closure history.

**Operator scope for trial re-entry review:**

> Digital Anchor trial scope post-OWC: Task Area (fully operable) + Workbench E (real write-through, primary DA interaction surface) + Workbench D (operable read-view) + Workbench A/C (read-view, browse pointer only, not interactive) + Workbench B (display-only, content unresolved) + Delivery Center 回填 (operable with account gap) + Delivery Center Delivery Pack (display-only, final_video via `media.final_video_url` path only). Digital Anchor is a **constrained smoke-trial line**, not a full end-to-end operator line in this wave.

---

## 3. Visible / Usable / Operable Matrix

For each line and surface area, the classification is:
- **Operable:** operator can take real action with real data; result is meaningful.
- **Usable:** operator can interact but results may be partially incomplete / sentinel-filled.
- **Inspect-only / display-only:** operator can see the surface; cannot take meaningful action; content may be unresolved.
- **Not present / blocked:** surface does not exist for this line in this wave.

### 3.1 Task Area

| Surface | Hot Follow | Matrix Script | Digital Anchor |
|---|---|---|---|
| Task list + line filter | **Operable** | **Operable** | **Operable** |
| Three-tier / eight-stage state projection | **Operable** | **Operable** (MS-W1 + MS-W2) | **Operable** (DA-W1 + DA-W2) |
| 8-field operator-language card body | **Operable** | **Operable** (MS-W2) | **Operable** (DA-W1) |
| Blocked / ready / publishable tri-state | **Operable** | **Operable** | **Operable** |
| Entry: new task creation | **Operable** | **Operable** (formal `/tasks/matrix-script/new` POST only) | **Operable** (formal `/tasks/digital-anchor/new` POST only) |
| Quick actions (进入工作台 / 跳交付中心) | **Operable** | **Operable** | **Operable** |

### 3.2 Workbench

| Panel | Hot Follow | Matrix Script | Digital Anchor |
|---|---|---|---|
| A — content structure / 脚本结构区 / 角色绑定面 | **Operable** | **Inspect-only** (STATUS_UNRESOLVED, Outline Contract gap) | **Usable** (read-view if data present; no interactive role selection) |
| B — scene plan / variation panel / 内容结构面 | **Operable** | **Operable** (Phase B variation panel — real axes/cells/slots) | **Display-only** (STATUS_UNRESOLVED, no Phase B authoring) |
| C — audio / preview compare / 场景模板面 | **Operable** | **Usable** (MS-W4 read-view, recommended marker live) | **Display-only** (browse pointer only, no interactive scene selection) |
| D — language / 校对区 / 语言输出面 | **Operable** | **Operable** (MS-W5 real write-through forms) | **Usable** (DA-W6 read-view, language rows from delivery_binding) |
| E — QC / diagnostics / 预览与校对面 | **Operable** | **Usable** (MS-W6 advisory-backed read-view) | **Operable** (DA-W7 real write-through forms — primary DA interaction surface) |
| Variation panel (Matrix Script specific) | Not present | **Operable** (Plan A §3.2 baseline, real axes/cells/slots per §8.A–§8.H) | Not present |

### 3.3 Delivery Center

| Panel | Hot Follow | Matrix Script | Digital Anchor |
|---|---|---|---|
| Final video primary lane | **Operable** | **Inspect-only** (artifact_lookup still `not_implemented_phase_c`) | **Display-only** (`final_video` is primacy-label-only; actual artifact at `media.final_video_url`) |
| Required deliverables | **Operable** | **Inspect-only** (STATUS_UNRESOLVED) | **Inspect-only** (STATUS_TRACKED_GAP* sentinels) |
| Optional / non-blocking deliverables (scene_pack etc.) | **Operable** | **Inspect-only** | **Inspect-only** |
| copy_bundle / delivery pack layout | Not applicable | **Display-only** (all subfields STATUS_UNRESOLVED) | **Inspect-only** (nine-lane layout with tracked-gap sentinels) |
| 回填 / publish feedback multi-channel | **Operable** | **Usable** (MS-W8 reads closure; account always STATUS_UNSOURCED) | **Usable** (DA-W9 reads closure; account always tracked-gap) |
| Publish action button | **Operable** | **Usable** (consumes authoritative projection; no copy delivery) | **Usable** (consumes authoritative projection) |

### 3.4 Asset Supply Dependency Surfaces

| Concern | Classification | Notes |
|---|---|---|
| Asset Supply browse (`/assets`) | **Inspect-only** | Recovery PR-2 shipped minimum capability: browse + opaque `asset://` reference. No interactive selection wired from Workbench panels yet. |
| Promote intent submission | **Not operable** | Approval path is restricted to `requested → rejected` only (Recovery PR-2 §9.1.6). No approval path exists until Asset Library write path lands in a later wave. |
| Role/scene select from Workbench A / C | **Not operable** | DA-W3 and DA-W5 surface browse pointer only; interactive selector is a future operator-driven authoring wave item. |
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

### 4.3 DA final_video actual access path

**Constraint:** Operators accessing DA tasks in the Delivery Center MUST be briefed on the correct access path for the final video artifact.

**The gap:** DA-W8 Delivery Pack renders `final_video` as a primacy-label-only lane with a tracked-gap explanation. The surface correctly identifies this as a gap — the Phase C delivery binding does not enumerate a composed final asset row. The actual final video URL is available via `media.final_video_url` on the publish hub payload.

**Required coordinator action before any DA Delivery Center trial session:**
1. Confirm the `media.final_video_url` field is populated for the trial task before beginning.
2. Brief operators: "The Delivery Pack 'Final Video' row shows a label, not a link — this is expected in this wave. To access the actual final video, use [the alternative access path at `media.final_video_url`]."
3. Document the access path explicitly in the trial sample profile (see §5).

**Note for trial re-entry review:** The trial re-entry review must confirm and document the exact UI path or API call that exposes `media.final_video_url` to operators. This addendum names the field; the trial re-entry review must verify the operator-accessible path.

### 4.4 All trial samples must be fresh, valid, and correctly configured

**Constraint:** No pre-OWC samples, no pre-§8.A / pre-§8.F Matrix Script samples, no incorrectly-configured DA tasks may be used as trial evidence. See §5 for sample validity criteria.

**Why:** Pre-OWC samples do not carry the OWC-converged surface rendering. Pre-§8.A / pre-§8.F Matrix Script samples carry invalid `source_script_ref` shapes. DA tasks with incorrectly-bound role or scene cannot be corrected in-session (role/scene are fixed at creation in this wave).

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

### 5.3 Digital Anchor sample validity (new — Plan A had none)

A Digital Anchor task counts as a valid post-OWC trial evidence task iff ALL of the following hold:

**At task creation time:**

1. **Formal create-entry route.** Created via the formal `/tasks/digital-anchor/new` POST (Recovery PR-4 formal route). Never via the legacy temp `/tasks/connect/digital_anchor/new` or any other path.

2. **Role binding configured at creation.** The task `config.entry.role_profile_ref` is populated with a valid `role_pack_ref` value at creation time. This binding CANNOT be changed from the Workbench A panel in this wave. If it is missing or incorrect, the Workbench A panel will render without meaningful role binding data — create a new task.

3. **Scene binding configured at creation.** The task `config.entry.scene_binding_hint` is populated at creation time. This binding CANNOT be changed from the Workbench C panel in this wave. If it is missing or incorrect, Workbench C renders `STATUS_TEMPLATE_PENDING` — create a new task.

4. **Target language(s) configured at creation.** The task `language_scope.target_languages` is populated at creation time. DA-W6 Workbench D and DA-W8 `language_usage` depend on this.

**At trial time:**

5. **OWC surface rendering present.** `GET /tasks/{task_id}` for `kind=digital_anchor` renders the Task Area card with `data-role="da-eight-stage"` + `data-role="da-*"` per-field anchors visible. The Workbench renders five panels with `data-role="digital-anchor-role-binding-panel"` / `data-role="digital-anchor-content-structure-panel"` / `data-role="digital-anchor-scene-template-panel"` / `data-role="digital-anchor-language-output-panel"` / `data-role="digital-anchor-review-zone-panel"` visible. The Delivery Center renders with `data-role="digital-anchor-delivery-pack"` and `data-role="digital-anchor-delivery-backfill"` visible.

6. **final_video access path confirmed before Delivery Center trial.** Before any DA Delivery Center trial session, coordinator must confirm that `media.final_video_url` is accessible for the trial task. The DA-W8 Delivery Pack will NOT expose this URL — that is expected; the alternative access path must be briefed and confirmed.

7. **Closure store not restarted.** No gateway restart between task creation and trial session. See §4.1.

**What is NOT expected to be corrected in-session:**

- Role binding (Workbench A) — fixed at task creation.
- Scene template (Workbench C) — fixed at task creation.
- Content structure (Workbench B Outline / 段落逻辑 / 强调点 / 节奏) — unresolved in most cases; cannot be authored from the workbench in this wave.
- `final_video` URL in Delivery Pack — not surfaced through Delivery Pack; access via `media.final_video_url`.
- Account identity in 回填 rows — always tracked-gap; cannot be captured in this wave.

**DA trial sample suggested workflow (for first-wave samples):**

| Step | Surface | Expected result |
|---|---|---|
| 1. Create DA task via formal route | `/tasks/digital-anchor/new` POST | Task created; 任务区 row appears |
| 2. Inspect Task Area 8-field card | `tasks.html` DA branch | Eight fields visible; 当前版本状态 reads from PR-1 unified producer |
| 3. Enter Workbench | `task_workbench.html` DA branch | Five panels visible with correct `data-role` anchors |
| 4. Inspect DA-W3 角色绑定面 | Workbench A panel | Role Profile / 形象风格 / 声音 preset / 表达风格 / 情绪 visible if role configured |
| 5. Inspect DA-W6 语言输出面 | Workbench D panel | Target Language / Subtitle Strategy / multi-language navigator visible |
| 6. Submit DA-W7 review via form | Workbench E form → `POST /api/digital-anchor/closures/{task_id}/events` | Closure event recorded; review zone submission confirmed |
| 7. Navigate to Delivery Center | `task_publish_hub.html` DA branch | DA-W8 nine-lane layout + DA-W9 backfill layout visible |
| 8. Inspect DA-W8 Delivery Pack | Delivery Center DA branch | `final_video` primacy lane labeled (expected); other lanes show tracked-gap or resolved status |
| 9. Access final video via publish hub payload | `media.final_video_url` field | Actual final video URL accessible via this path (verify pre-trial) |
| 10. Inspect DA-W9 回填 | Delivery Center DA branch | Post-closure events visible; account tracked-gap (expected) |

---

## 6. Non-Blocking-for-Closeout but Blocking-for-Ops Gaps

These gaps are documented in both OWC closeouts as non-blocking tracked items. They are **not blocking** for engineering closeout. They ARE operationally significant for any real operator trial. Each gap is classified by its trial impact.

### 6.1 Critical (would block end-to-end workflow for the named scenario)

| Gap ID | Gap | Lines affected | What it blocks |
|---|---|---|---|
| OPS-GAP-1 | **DA `final_video` not accessible through Delivery Pack** | Digital Anchor only | Operators cannot complete "deliver and download final video" through the standard Delivery Center surface. The actual artifact is at `media.final_video_url` — a non-obvious path that requires coordinator briefing. |
| OPS-GAP-2 | **`InMemoryClosureStore` volatile across gateway restart** | Matrix Script + Digital Anchor | All MS and DA closure history lost on gateway restart. Review-zone submissions, publish events, feedback records — all non-durable. Affects any multi-session trial workflow. |
| OPS-GAP-3 | **MS copy_bundle all fields `STATUS_UNRESOLVED`** | Matrix Script only | Operators cannot extract actual copy (title / hashtags / CTA / comment_keywords) from the Delivery Center. The surface exists but delivers no content. Any MS trial workflow requiring actual copy delivery is blocked. |

### 6.2 Significant (degrades trial quality; does not block the core loop but will confuse operators)

| Gap ID | Gap | Lines affected | What it degrades |
|---|---|---|---|
| OPS-GAP-4 | **MS-W3 script structure fields `STATUS_UNRESOLVED`** | Matrix Script only | Operators expecting to review the Hook / Body / CTA / 关键词 / 禁用词 content structure in the Workbench see empty panels. Core MS readability without the Outline Contract is limited to the variation panel + review forms. |
| OPS-GAP-5 | **DA-W4 content structure fields `STATUS_UNRESOLVED`** | Digital Anchor only | Operators expecting to review Outline / 段落结构 / 强调点 / 节奏 in the Workbench see empty or `STATUS_UNRESOLVED` fields. DA content structure comprehension is limited in this wave. |
| OPS-GAP-6 | **DA-W3 / DA-W5 asset selection not interactive** | Digital Anchor only | Operators expecting to select or change a role or scene template from the Workbench find browse pointers only. Role/scene correction is not possible in-session; must be done by creating a new task. |
| OPS-GAP-7 | **account_id always `STATUS_UNSOURCED` / tracked-gap (MS + DA 回填)** | Matrix Script + Digital Anchor | Operators cannot identify which account published the content from the 回填 tables. Account-level publishing analytics are unavailable this wave. |
| OPS-GAP-8 | **DA artifact_lookup `not_implemented_phase_c` on DA delivery lanes** | Digital Anchor only | DA delivery binding lanes that depend on artifact lookup show tracked-gap sentinels. Artifact resolution for DA is not yet wired (Plan E equivalent for DA B4 is out of scope). |

### 6.3 Low impact (known regression risk; unlikely to affect first-wave trial if coordinator manages content)

| Gap ID | Gap | Lines affected | What it risks |
|---|---|---|---|
| OPS-GAP-9 | **Forbidden-token scrub uses substring match** | Matrix Script + Digital Anchor | Legitimate captions containing scrubbed English nouns may be silently altered in closure payloads. Risk is per-payload; manageable via controlled sample content. |
| OPS-GAP-10 | **Per-variation `final_provenance` granularity (manifest-level only)** | Matrix Script only | MS-W4 preview compare shows a per-variation `per_cell_artifact_granularity_note_zh` note. Multi-variation provenance is at manifest level, not variation level. Low impact unless trial specifically tests provenance tracing. |

---

## 7. Recommendation for Next Step

### 7.1 What this addendum establishes

This addendum establishes the **post-OWC operational trial baseline**. It supersedes Plan A §6.2 (Matrix Script), Plan A §6.3 (Digital Anchor), and Plan A §7.1 (trial samples) for the OWC-converged surfaces. Plan A's §0.1 / §0.2 (Matrix Script sample validity and `source_script_ref` product meaning), §6.1 (Hot Follow), §7.1 samples 1–5, §8 (risks and mitigations), and §9 (next gate conditions) remain in force unchanged.

### 7.2 What the trial re-entry review must do

The formal trial re-entry review (the next docs-only step, opened by explicit user hand-off) must:

1. **Evaluate against this updated baseline.** The trial re-entry review must cite this addendum as the operational baseline and confirm which ops gaps are acceptable for trial vs which require further mitigation before trial begins.
2. **Resolve the `media.final_video_url` access path for DA trial.** The trial re-entry review must confirm and document the exact operator-accessible path (UI route or API call) for `media.final_video_url` so the DA trial coordinator can brief operators with a precise instruction, not just a field name.
3. **Author the DA equivalent of Plan A §5 口径.** The trial re-entry review must produce coordinator briefing scripts for DA that parallel the Plan A §5.1 / §5.2 / §5.3 口径 — covering Task Area, Workbench (emphasizing DA-W7 as primary interaction surface), and Delivery Center (emphasizing the final_video access path).
4. **Confirm the trial protocol constraints (§4) are satisfiable in the planned trial environment.** Specifically: confirm gateway restart risk is manageable for the trial window; confirm `media.final_video_url` is populated for the trial DA task set.
5. **Update Plan A §12 readiness conclusion.** The trial re-entry review must update the Plan A §12 final readiness conclusion to reflect the post-OWC, post-addendum operational posture.

### 7.3 What this addendum does NOT unlock

This addendum is documentation only. It does NOT:

- Open Plan A live-trial. Live-trial requires the trial re-entry review to be authored and signed by architect + reviewer + coordinator + PM.
- Reopen OWC-MS or OWC-DA implementation.
- Advance Platform Runtime Assembly Wave.
- Advance Capability Expansion Gate Wave.
- Close OPS-GAP-1..OPS-GAP-10 — those gaps remain open and are correctly classified as future-wave scope.

### 7.4 Precondition summary for trial re-entry review to open

The following preconditions are ALL satisfied as of 2026-05-06:

| Precondition | Status |
|---|---|
| OWC-MS Closeout MS-A1..MS-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; MS-A7 signed commit `b1160b3` |
| OWC-DA Closeout DA-A1..DA-A8 PASS | **SATISFIED** — all eight acceptance rows PASS; DA-A7 signed per §11 (2026-05-06) |
| OWC-DA Closeout merged to `main` | **SATISFIED** — PR #139 squash `f5e86a5`; docs-only housekeeping PR #140 also merged |
| Pre-trial ops-readiness review produced | **SATISFIED** — OWC operations-readiness alignment review 2026-05-06 |
| Pre-trial ops addendum authored | **SATISFIED** — this document |
| Explicit user hand-off for trial re-entry review | PENDING — the next explicit user instruction |

After the explicit user hand-off lands, the trial re-entry review may open as the next docs-only step.

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
