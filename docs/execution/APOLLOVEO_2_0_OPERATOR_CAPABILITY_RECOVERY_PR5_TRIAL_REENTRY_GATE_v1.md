# ApolloVeo 2.0 · Operator Capability Recovery · PR-5 · Real Operator Trial Re-Entry Gate v1

Date: 2026-05-04 (rewritten from a GO gate to a NOT-READY decision +
Product-Flow Enforcement Order on 2026-05-04 per the rewrite mission)
Status: **Trial re-entry gate document — NOT READY decision.** This
document does **NOT** authorize real operator trial. It records the
recovery wave's contract-backed minimum capability as restored, and
explicitly declares operator workflow convergence as not yet
sufficient for real trial.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery — Re-entry
**evaluation** (the re-entry itself is BLOCKED by this document's
verdict).
Decision authority:
[`docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md).
Action authority:
[`docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md) §8 (PR-5).
Predecessors (all MERGED to `main` 2026-05-04):
- PR-1 ([#114](https://github.com/zhaojfifa/apolloveo-auto/pull/114), squash `4c317c4`) — Unified Publish Readiness Runtime Recovery.
- PR-2 ([#116](https://github.com/zhaojfifa/apolloveo-auto/pull/116), squash `4343bec`) — B-roll / Asset Supply minimum operator capability.
- PR-3 ([#118](https://github.com/zhaojfifa/apolloveo-auto/pull/118), squash `d53da0f`) — Matrix Script Operator Workspace Promotion.
- PR-4 ([#119](https://github.com/zhaojfifa/apolloveo-auto/pull/119), squash `0549ee0`) — Digital Anchor Operator Workspace Recovery.

## 0. Verdict

**Real operator trial is NOT READY.**

The minimum **contract-backed** operator capability is restored
(PR-1 / PR-2 / PR-3 / PR-4 all merged to `main` 2026-05-04). What
remains missing is **operator workflow convergence**: the per-line
operator-visible surfaces (Task Area card fields, Workbench modules,
Delivery Center sections) are not yet mapped to the line-specific
product-flow authority documents
[`docs/product/matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
and
[`docs/product/digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md).
Consequently an operator opening a Matrix Script or Digital Anchor task
today does not see the workflow that the product-flow design specifies
— they see only the contract-truth projection.

Real operator trial therefore remains **blocked**. The next mandatory
wave is the **Operator Workflow Convergence Wave** (Matrix Script
first, Digital Anchor second), defined in §4 below.

## 1. Why this document was rewritten (2026-05-04)

The first revision of this gate document declared real operator trial
**GO subject to coordinator G5..G9**. That conclusion was wrong: it
treated "contract-backed minimum operator capability is present" as a
sufficient condition for real trial, when the binding condition is
"operator workflow as specified by the line-specific product-flow
documents is present on operator-visible surfaces". The two are not
the same. The recovery wave restored the former; the latter remains
unmet.

This rewrite:

1. Flips the gate verdict from **GO** to **NOT READY**.
2. Adds the **Product-Flow Enforcement Order** (§3) elevating the two
   product-flow design documents to binding line-specific execution
   authority.
3. Names the **Operator Workflow Convergence Wave** (§4) as the next
   mandatory wave, with Matrix Script first and Digital Anchor second.
4. Rewrites §2's checklist from G1..G16 (acceptance) to W1..W12
   (workflow-convergence preconditions for real trial).
5. Preserves §1 of the prior revision's evidence map (renamed §6 here)
   verbatim — the recovery wave's contract-backed acceptance is
   intact; this document simply states that contract-backed
   acceptance is necessary but not sufficient.
6. Preserves the §"Stop conditions during real trial" list (renamed
   §10 here) verbatim — those stop conditions remain binding for any
   future trial.

The pre-rewrite revision is preserved in git history; no documentation
on `main` claims real operator trial is GO.

## 2. Real-Trial Re-Entry Workflow-Convergence Preconditions (W1..W12)

These are the binding preconditions for real operator trial. Until
**all** are satisfied, real operator trial remains BLOCKED.

### 2.1 Contract-backed minimum capability (already met by recovery)

- [x] **W1.** PR-1 (Unified Publish Readiness Runtime Recovery)
  merged to `main`. See §6 row 1 evidence.
- [x] **W2.** PR-2 (B-roll / Asset Supply minimum) merged to `main`.
  See §6 row 2 evidence.
- [x] **W3.** PR-3 (Matrix Script Operator Workspace Promotion)
  merged to `main`. See §6 row 3 evidence.
- [x] **W4.** PR-4 (Digital Anchor Operator Workspace Recovery)
  merged to `main` after the §9.1 reviewer-fail correction pass.
  See §6 row 4 evidence.

### 2.2 Product-flow authority elevated (this PR-5)

- [x] **W5.** [`docs/product/matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
  is in `main` with the line-specific-execution-authority preamble
  (PR-5).
- [x] **W6.** [`docs/product/digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md)
  is in `main` with the line-specific-execution-authority preamble
  (PR-5).

### 2.3 Operator workflow convergence (NOT YET MET — blocks real trial)

- [ ] **W7.** Matrix Script Task Area card carries the §5.3 fields
  from `matrix_script_product_flow_v1.md` (主题 / 目标; 核心脚本名称;
  当前变体数; 可发布版本数; 已发布账号数; 当前最佳版本; 最近一次生
  成时间; 当前阻塞项).
- [ ] **W8.** Matrix Script Workbench renders the §6.1 modules from
  `matrix_script_product_flow_v1.md` (A 脚本结构区, B 变体配置区,
  C 预览对比区, D 校对区, E 质检与诊断区) — not only the Phase B
  variation-surface projection that PR-3 wired.
- [ ] **W9.** Matrix Script Delivery Center renders the §7.1 standard
  deliverable set (final.mp4, subtitles, audio, copy_bundle, metadata
  / manifest, scene_pack 可选, publish_status) and enforces §7.2
  publish rules (成片完成 + 发布必需项就绪 = 可发布; Scene Pack 非
  阻塞; 历史成功 vs 当前尝试分开解释; publish 只消费 authoritative
  projection).
- [ ] **W10.** Digital Anchor Task Area card carries the §5.2 fields
  from `digital_anchor_product_flow_v1.md` (任务标题; Role Profile;
  Scene Template; Target Language; 当前版本状态; 当前阻塞项; 交付
  包状态; 最近更新).
- [ ] **W11.** Digital Anchor Workbench renders the §6.1 modules
  from `digital_anchor_product_flow_v1.md` (A 角色绑定面, B 内容结
  构面, C 场景模板面, D 语言输出面, E 预览与校对面) — not only the
  Phase B role/speaker-surface projection that PR-4 wired.
- [ ] **W12.** Digital Anchor Delivery Center renders the §7.1
  standard deliverable set (final_video, subtitle, dubbed_audio,
  metadata, manifest, pack, role_usage, scene_usage, language_usage)
  and enforces §7.2 delivery rules (主交付物是成片; 附属交付物可追
  溯; manifest 是交付证据; pack 是协作接口; 历史成功 vs 当前尝试分
  开解释).

W7..W12 will be delivered by the **Operator Workflow Convergence
Wave** (§4). Until they are all checked, real operator trial cannot
be authorized.

### 2.4 Re-entry decision

| Condition | State | Implication |
|---|---|---|
| W1 .. W4 (recovery contract-backed) | MET | Necessary, not sufficient. |
| W5 .. W6 (product-flow authority elevated) | MET | This PR-5 lands them. |
| W7 .. W12 (operator workflow convergence) | NOT MET | **Real trial BLOCKED.** |

**Verdict: NOT READY.** Real operator trial does not start until
W7..W12 are met by the Operator Workflow Convergence Wave.

## 3. Product-Flow Enforcement Order (binding)

The two product-flow design documents
[`docs/product/matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
and
[`docs/product/digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md)
are hereby elevated from "design notes" to **binding line-specific
execution authority** for their respective lines. The ordering rule:

1. **Top-level flow remains valid as the factory-wide abstract flow.**
   [`docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
   continues to define the factory-wide abstract chain
   (task → line → workbench → delivery → publish → archive). It is
   the cross-line authority for what a "task" is, what a "deliverable"
   is, and what "publishability" is.
2. **Line-specific product-flow documents are binding inside their
   line.** For Matrix Script surfaces, the Matrix Script product-flow
   document is the line-specific authority for Task Area card fields,
   Workbench modules, Delivery Center sections, and the line's
   §"运营目标" (跑量测试 / 内容配方验证 / 账号矩阵分发 / 快速复盘).
   Same for Digital Anchor on Digital Anchor surfaces.
3. **Future Task Area / Workbench / Delivery implementations MUST map
   to the product-flow modules.** Mapping to the packet / contract /
   runtime truth alone is **not sufficient** for operator-ready. A
   workbench page that consumes the Phase B variation surface
   projection but does not render §6.1 A / B / C / D / E modules is
   not operator-ready under this rule.
4. **Operator-ready cannot be claimed unless product-flow modules are
   actually present.** The PR-5 NOT-READY verdict is the first
   instance of this rule. Future PRs that claim "operator-ready" or
   "real trial GO" MUST cite the specific product-flow modules they
   render.
5. **Conflict-resolution.** Where the line-specific document and the
   top-level document diverge for a line-specific concern, the
   line-specific document wins on that line's surfaces. Where the
   line-specific document and a frozen contract diverge, the contract
   wins (validators / packet rules / Plan B/C/D contracts are not
   re-opened by product-flow elevation).
6. **Re-versioning discipline.** Either document may be re-versioned
   (`_v2`) only via a separate authored PR; this PR-5 does not modify
   their substantive content beyond adding the authority preamble.

## 4. Operator Workflow Convergence Wave (next mandatory wave)

The next mandatory wave after PR-5 is the **Operator Workflow
Convergence Wave**. Its scope is exactly W7..W12 (§2.3 above).

### 4.1 Wave goal

Land operator workflow convergence on the two recovered lines so that
W7..W12 can be checked. The wave is **operator-surface only**: it
maps existing recovered runtime + contract truth into the modules
specified by the product-flow documents. It does NOT add new runtime
features, new contracts, new packet truth, or new Plan E phases.

### 4.2 Wave ordering (mandatory)

1. **Phase OWC-MS — Matrix Script first.** Lands W7 + W8 + W9.
2. **Phase OWC-DA — Digital Anchor second.** Lands W10 + W11 + W12.

Matrix Script is sequenced first because it is the more mature line
(8 §8.A..§8.H corrections complete; Phase B authoring already
populates real axes / cells / slots) and because the task-area /
workbench / delivery surfaces all already have the contract-backed
projections wired by PR-1 / PR-3. Digital Anchor's Phase B authoring
is not yet implemented (it is contract-deferred per the PR-4 residual
risks); the Digital Anchor convergence step therefore renders empty
panels by design until Phase B authoring lands separately.

### 4.3 Wave hard boundaries

This wave MUST NOT:

- Add new runtime features outside what is needed to map existing
  truth into the product-flow modules.
- Reopen Platform Runtime Assembly.
- Reopen Capability Expansion (W2.2 / W2.3 / durable persistence /
  runtime API / third production line).
- Modify the Matrix Script or Digital Anchor packet schema, sample,
  or any frozen contract.
- Modify Hot Follow business behavior.
- Add provider / model / vendor / engine controls.
- Re-version either product-flow document.

### 4.4 Wave acceptance

The Operator Workflow Convergence Wave is acceptable only when:

- W7 .. W9 are all checked for Matrix Script (Phase OWC-MS).
- W10 .. W12 are all checked for Digital Anchor (Phase OWC-DA).
- The repository ships a follow-up gate document that records each
  W-item as PASS with a file/line citation into the operator surface.
- That follow-up gate document re-runs the §10 stop-condition list
  against the post-convergence state.

After OWC-MS + OWC-DA close, a separate "Trial Re-Entry Gate v2"
document may be authored to reopen the real-trial decision. PR-5
does NOT pre-decide that gate.

## 5. Post-recovery Stage Definition

The repository's stage transitions from the pre-recovery
**"Operator-Visible Surface Validation Wave (authority-only trial
freeze)"** to the post-recovery **"Operator Workflow Convergence Wave
— Matrix Script First, Digital Anchor Second"**.

This is **not** the start of:

- Real operator trial (BLOCKED — gated on §2.3 W7..W12).
- Platform Runtime Assembly (still BLOCKED).
- Capability Expansion (still BLOCKED).
- New production lines (still BLOCKED).
- Provider / model / vendor consoles (forbidden at every phase).

It IS the start of: mapping the recovered operator surfaces onto the
two product-flow design documents, line-by-line, in the ordering of
§4.2.

## 6. Recovery Wave Acceptance — Evidence Map (W1..W4)

Each row maps a Recovery Decision §4 mandatory capability onto the
merged PR that delivered it, the execution log, and the operator-
visible surface(s) that exercise it. **This evidence is sufficient
for W1..W4 of §2 only — not sufficient for real-trial re-entry.**

| § | Capability | Status | Merged commit | Execution log | Operator-visible surface |
|---|---|---|---|---|---|
| 4.1 | Asset Supply / B-roll minimum usable operator capability | **PASS** | [`4343bec`](https://github.com/zhaojfifa/apolloveo-auto/commit/4343bec) (PR #116) | [`PR2_ASSET_SUPPLY`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md) | `/assets`, `/api/assets`, `POST /api/assets/promote` |
| 4.2 | Unified `publish_readiness` runtime producer | **PASS** | [`4c317c4`](https://github.com/zhaojfifa/apolloveo-auto/commit/4c317c4) (PR #114) | [`PR1_PUBLISH_READINESS`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md) | Board / Workbench / Delivery converge on the same producer |
| 4.3 | Matrix Script operator workspace promotion (variation → workbench → delivery → feedback loop) | **PASS** | [`d53da0f`](https://github.com/zhaojfifa/apolloveo-auto/commit/d53da0f) (PR #118) | [`PR3_MATRIX_SCRIPT_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md) | `/api/matrix-script/closures/{task_id}` (GET / POST events / peek), publish-hub `_ms_kind == "matrix_script"` block |
| 4.3 | Digital Anchor operator workspace recovery (formal create-entry + Phase D.1 write-back) | **PASS** | [`0549ee0`](https://github.com/zhaojfifa/apolloveo-auto/commit/0549ee0) (PR #119) | [`PR4_DIGITAL_ANCHOR_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md) (with §9.1 reviewer-fail correction pass) | `/tasks/digital-anchor/new`, `/api/digital-anchor/closures/{task_id}` (GET / POST events / peek), publish-hub `_da_kind == "digital_anchor"` block |
| 4.4 | Trial re-entry preparation | **PASS (this document) — verdict NOT READY** | (PR-5) | [`PR5_EXECUTION_LOG`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md) | n/a — gate document only |

The recovery wave's mandatory ordering (Global Action §3) is satisfied;
the recovery sequence PR-1 → PR-2 → PR-3 → PR-4 → PR-5 is complete.
Real operator trial is a separate condition (§2.3 W7..W12), not
satisfied by §6 alone.

## 7. Operator Surface Inventory (post-recovery, pre-convergence)

What the recovered surfaces actually present today, line-by-line. This
is the baseline the Operator Workflow Convergence Wave starts from.

### 7.1 Hot Follow

End-to-end (intake → publish), unchanged. Per
[`docs/architecture/hot_follow_business_flow_v1.md`](../architecture/hot_follow_business_flow_v1.md)
the Hot Follow operator workflow is already convergent at the line
level — no Hot Follow product-flow document is required by this
gate. Hot Follow remains the runtime reference line and is **not**
in scope for the Operator Workflow Convergence Wave.

### 7.2 Matrix Script

- Task Area card today: line-id, kind, status, formal-entry next-
  surfaces. **Does not yet carry §5.3 fields** (主题 / 核心脚本名称
  / 当前变体数 / 可发布版本数 / 已发布账号数 / 当前最佳版本 / 最近
  一次生成时间 / 当前阻塞项).
- Workbench today: Phase B variation panel (axes / cells / slots),
  comprehension panel (PR-U2). **Does not yet render §6.1 modules**
  (A 脚本结构区 / B 变体配置区 / C 预览对比区 / D 校对区 / E 质检
  与诊断区).
- Delivery Center today: the five contract-frozen rows
  (variation_manifest / slot_bundle / subtitle_bundle / audio_preview
  / scene_pack), per-row `required` / `blocking_publish` zoning,
  delivery comprehension lanes, the variation_feedback table from
  PR-3. **Does not yet render §7.1 standard deliverable set as the
  product-flow expects** (final.mp4 primacy is partly there via
  comprehension; copy_bundle / publish_status / metadata / manifest
  rows are not yet first-class).

### 7.3 Digital Anchor

- Task Area card today: line-id, kind, formal-entry next-surfaces.
  **Does not yet carry §5.2 fields** (Role Profile / Scene Template
  / Target Language / 当前版本状态 / 当前阻塞项 / 交付包状态 / 最
  近更新).
- Workbench today: empty-on-create role/speaker projection (Phase B
  authoring deferred). **Does not yet render §6.1 modules** (A 角色
  绑定面 / B 内容结构面 / C 场景模板面 / D 语言输出面 / E 预览与
  校对面).
- Delivery Center today: contract-frozen rows from
  `digital_anchor_delivery_binding_v1`. **Does not yet render §7.1
  standard deliverable set** (final_video / subtitle / dubbed_audio
  / metadata / manifest / pack / role_usage / scene_usage /
  language_usage).

### 7.4 Asset Supply

`/assets` page renders contract-backed assets with closed-facet
filters; promote-intent submit accepted; `requested → withdrawn /
rejected` closure visible. Asset Supply is a cross-line resource
surface, not a per-line workflow; it is not subject to the Operator
Workflow Convergence Wave's per-line W-checks but remains an enabler
for Matrix Script reference-into-task and Digital Anchor role/scene
asset discovery.

### 7.5 Cross-line Board

`/tasks` Board renders Hot Follow + Matrix Script + Digital Anchor
rows. The unified `publish_readiness` from PR-1 is the truth; Board
/ Workbench / Delivery agree on the same publishable state per task.

## 8. What operators MAY do during the Convergence Wave (interim)

The Convergence Wave is operator-surface engineering, not operator
trial. The operations team SHOULD NOT execute live operator trial
samples against the post-recovery / pre-convergence state. Two
exceptions are permitted:

1. **Hot Follow golden-path samples** — Hot Follow is unchanged by
   the recovery wave and unchanged by the Convergence Wave. Hot
   Follow trial samples remain valid as factory-baseline evidence
   per the pre-recovery Plan A §7.1 wave 1 / wave 2.
2. **Static surface inspection by the trial coordinator** — the
   coordinator MAY inspect the post-recovery surfaces, file
   convergence-gap notes against §7.2 / §7.3, and use those notes as
   input to the Convergence Wave. This is documentation work, not
   operator trial.

All other operator actions remain blocked by §2.4's NOT-READY verdict.

## 9. Cross-cutting Forbidden List (carried forward)

These remain forbidden at every phase, including during the
Convergence Wave:

- **Vendor / model / provider / engine / avatar-engine / TTS-provider
  / lip-sync-engine selectors / consoles** anywhere on operator-
  visible surfaces (validator R3 + `asset_supply_matrix_v1.md`
  decoupling rules item 7).
- **Donor (SwiftCraft) namespace import** anywhere.
- **State-shape fields** (`status`, `ready`, `done`, `phase`,
  `current_attempt`, `delivery_ready`, `final_ready`, `publishable`)
  outside the scoped Phase D `publish_status` enum (validator R5).
- **Closed kind-set widening** (`framing_kind_set`,
  `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`,
  Matrix Script axis kinds, asset-library closed enums).
- **Workbench writes outside closure paths.**
- **Phase B authoring at entry-time** for Digital Anchor `roles[]`
  / `segments[]`.
- **Operator-driven Matrix Script Phase B axis authoring** in this
  wave.
- **B-roll / Asset Supply admin review UI, fingerprinting platform,
  full DAM, upload-heavy admin tooling.**
- **Platform Runtime Assembly entry / phases A–E.**
- **Capability Expansion** (W2.2 / W2.3 / durable persistence /
  runtime API).
- **Third production line.**
- **Re-versioning either product-flow document under cover of the
  Convergence Wave.**

## 10. Stop conditions (carried forward; binding for any future trial)

If the operations team or the Convergence Wave engineering team
observes any of the following, the wave MUST pause and a regression
note MUST be filed:

- A vendor / model / provider / engine selector appears on any
  operator surface.
- A `/tasks/connect/{matrix_script,digital_anchor}/...` route resolves
  with a non-404.
- A Matrix Script Phase B variation panel renders empty-fallback
  messages or the bound-method repr — those samples were created
  before §8.A / §8.G and are pre-recovery.
- A Digital Anchor formal-entry POST silently accepts a flat
  `source_language` / `target_language` form key without rejection
  (PR-4 reviewer-fail correction §9.1.1 closed this).
- A Digital Anchor `/api/digital-anchor/closures/{task_id}/publish-closure`
  endpoint is reachable (PR-4 reviewer-fail correction §9.1.3 retired
  it).
- The publish-feedback closure mirrors the legacy D.0 closure-wide
  `publish_status` enum on operator-visible surfaces (PR-4 reviewer-
  fail correction §9.1.3 made D.1 per-row the active truth path).
- Either product-flow document is silently re-versioned without an
  authored re-version PR.

## 11. Signoff

The trial coordinator MUST NOT obtain real-trial signoff from this
document. This document records the **NOT-READY** verdict for real
operator trial. Real-trial signoff is the responsibility of a future
"Trial Re-Entry Gate v2" document authored after the Operator
Workflow Convergence Wave closes.

What this document's signoff block records is the **acceptance of the
recovery wave + the elevation of the two product-flow documents to
binding line-specific execution authority + the NOT-READY verdict
itself**:

- [ ] **Architect (codex):** confirms §6 evidence map is intact;
  confirms §3 product-flow enforcement order is binding; confirms §0
  NOT-READY verdict reflects the §2.3 W7..W12 gap.
- [ ] **Reviewer / Merge owner:** confirms `main` HEAD includes
  squash commits `4c317c4`, `4343bec`, `d53da0f`, `0549ee0`, and the
  PR-5 squash commit (filled at merge time); confirms no later commit
  has silently re-introduced a Recovery Decision §5 forbidden item;
  confirms no later commit has silently flipped the §0 verdict to GO
  without an authored "Trial Re-Entry Gate v2" PR.
- [ ] **Trial coordinator (operations):** acknowledges that real
  operator trial is BLOCKED until the Convergence Wave closes; commits
  to using only the §8 interim allowances during the wave.

## 12. References

- Decision: [`ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md)
- Action: [`APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md)
- **Matrix Script line-specific execution authority (elevated by this PR-5):**
  [`docs/product/matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
- **Digital Anchor line-specific execution authority (elevated by this PR-5):**
  [`docs/product/digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md)
- Top-level abstract flow (factory-wide; remains valid):
  [`docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- Predecessor execution logs (all merged):
  - [`PR1_PUBLISH_READINESS`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md)
  - [`PR2_ASSET_SUPPLY`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md)
  - [`PR3_MATRIX_SCRIPT_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md)
  - [`PR4_DIGITAL_ANCHOR_WORKSPACE`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md) (with §9.1 reviewer-fail correction pass)
- Pre-recovery trial brief (re-anchored by Plan A §13 in this PR — to be re-rewritten to NOT-READY by this PR's edit):
  [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- Pre-recovery coordinator write-up (live-run section appended in this PR — to be re-rewritten to NOT-READY by this PR's edit):
  [`PLAN_A_OPS_TRIAL_WRITEUP_v1.md`](PLAN_A_OPS_TRIAL_WRITEUP_v1.md)
- Cross-line contracts pinned by the gate (unchanged):
  [`publish_readiness_contract_v1.md`](../contracts/publish_readiness_contract_v1.md),
  [`factory_delivery_contract_v1.md`](../contracts/factory_delivery_contract_v1.md),
  [`workbench_panel_dispatch_contract_v1.md`](../contracts/workbench_panel_dispatch_contract_v1.md)
