# OWC-MS Gate Spec v1 — Matrix Script Operator Workflow Convergence

Date: 2026-05-04
Status: Documentation only. Gate spec authoring step. **No code, no UI, no contract, no schema, no test, no template change.** Authoring this gate spec does NOT open the OWC-MS implementation gate; §10 architect + reviewer signoff is required for the implementation gate to open.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC).
Phase: First Plan Phase — OWC-MS (Matrix Script first).
Predecessor authority: PR-5 NOT-READY rewrite + Operator Capability Recovery Decision + Global Action.

---

## 1. Authority Stack

This gate spec is bound by, in priority order:

1. [CLAUDE.md](../../CLAUDE.md) bootloader.
2. [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) (with §13 Product-Flow Module Presence).
3. [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md) — factory-wide abstract flow.
4. [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md) — operator-visible surface authority.
5. [docs/handoffs/apolloveo_2_0_design_handoff_v1.md](../handoffs/apolloveo_2_0_design_handoff_v1.md) — design handoff authority.
6. **[docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md)** — Matrix Script line-specific execution authority (binding for OWC-MS).
7. [docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md](../execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md).
8. [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md) — red lines stay in force.
9. PR-1..PR-4 execution logs — frozen substrate.

When this gate spec conflicts with any authority above, the higher authority wins.

---

## 2. Entry Conditions

OWC-MS implementation MAY open only after **all** of:

| ID | Condition | Source |
| --- | --- | --- |
| MS-E1 | OWC authority/gate normalization PR (this PR's parent) merged to `main` | this docs PR |
| MS-E2 | Recovery PR-1 merged | PR #114 / commit `4c317c4` |
| MS-E3 | Recovery PR-2 merged | PR #116 / commit `4343bec` |
| MS-E4 | Recovery PR-3 merged | PR #118 / commit `d53da0f` |
| MS-E5 | Recovery PR-4 merged | PR #119 / commit `0549ee0` |
| MS-E6 | PR-5 NOT-READY verdict acknowledged in repo authority | this docs PR + ENGINEERING_STATUS.md |
| MS-E7 | §10 architect (Raobin) + reviewer (Alisa) signoff lines below filled and committed in a docs-only PR | post-merge docs PR |

Until MS-E1..MS-E7 hold, OWC-MS PR-1 may NOT open.

---

## 3. Allowed Scope (binding and exhaustive)

OWC-MS allowed scope is exactly the eight modules below. Any work outside this set is forbidden by §4.

| ID | Module | Source authority | Convergence requirement |
| --- | --- | --- | --- |
| MS-W1 | Task Area three-tier projection | matrix_script_product_flow §5.1 | Render the existing Matrix Script packet + variation_cells + closure publish events as a logical 脚本任务 → 变体任务 → 发布任务 lane view inside the existing single-card model on `gateway/app/templates/tasks.html`. Pure projection over existing truth; no schema change; no packet mutation. |
| MS-W2 | Task Area state vocabulary + 8-field card | matrix_script_product_flow §5.2 + §5.3 | Project existing four-layer state (L1 step status / L2 artifact facts / L3 current attempt / L4 ready gate) into the eight operator-language stages (`已创建 / 待配置 / 生成中 / 待校对 / 成片完成 / 可发布 / 已回填 / 已归档`); render the eight task-card fields (主题 / 核心脚本名称 / 当前变体数 / 可发布版本数 / 已发布账号数 / 当前最佳版本 / 最近一次生成时间 / 当前阻塞项). Read-only derivation; no L5 invented. |
| MS-W3 | Workbench A 脚本结构区 (read-view) | matrix_script_product_flow §6.1A | Surface Hook / Body / CTA / 关键词 / 禁用词 read-view derived from existing `source_script_ref`-resolved content. **No operator authoring of `source_script`** (Phase B authoring stays forbidden per gate spec §4). |
| MS-W4 | Workbench C 预览对比区 | matrix_script_product_flow §6.1C | Side-by-side multi-variation preview using B4 `artifact_lookup` rows now backed by PR-1 `final_provenance`. 差异项提示 derived from existing axis-tuple comparator. 推荐版本标识 derived from PR-1 unified `publish_readiness` producer + closure 操作历史. |
| MS-W5 | Workbench D 校对区 | matrix_script_product_flow §6.1D | Four review affordances (字幕 / 配音 / 文案 / CTA) writing through existing closure `operator_note` event with an additive structured `review_zone` field (closed enum: `subtitle / dub / copy / cta`). Closure shape unchanged; an enum closed-set extension on event payload is the only contract touch. |
| MS-W6 | Workbench E 质检与诊断区 | matrix_script_product_flow §6.1E | Render PR-1 L4 `advisory_emitter` output in the Matrix Script branch of `gateway/app/templates/task_workbench.html`. 风险提示 / 合规提示 / 时长 / 清晰度 / 字幕可读性 / 产物状态 / ready gate 解释 mapped from existing advisory taxonomy. Pure presentation; no advisory rule change. |
| MS-W7 | Delivery Center copy_bundle exposure | matrix_script_product_flow §7.1 | Render `copy_bundle` (标题 / hashtags / CTA / 评论关键词) as a Delivery Center row backed by existing `variation_manifest.copy` projection. If the field is not projection-ready, mark as a tracked gap; do NOT add packet truth in this wave. |
| MS-W8 | Delivery 回填 multi-channel rendering | matrix_script_product_flow §7.3 | Render closure `variation_feedback` per-row publish events as a multi-channel 回填 lane (channel / account / publish_time / publish_url / publish_status / metrics_snapshot). Entirely projection-side; no closure schema widening. |

---

## 4. Forbidden Scope (binding red lines)

OWC-MS PRs MUST NOT do any of the following. Any landed PR violating this section is rejected.

### 4.1 Truth-source / contract preservation
- No Matrix Script packet truth mutation.
- No reopen of §8.A–§8.H correction chain.
- No widening of `target_language`, canonical axes set `{tone, audience, length}`, or `source_script_ref` accepted-scheme set `{content, task, asset, ref}`.
- No operator-driven Phase B authoring (variation cells stay deterministically derived).
- No `source_script_ref` repurposing as body-input or URL-ingestion or dereferenced content address.
- No new authoritative truth source for publishability; PR-1 unified `publish_readiness` producer is the only path.
- No second producer for `final_provenance` (L3) or L4 advisory.

### 4.2 Cross-line preservation
- No Hot Follow file touched (Hot Follow source files byte-isolated; structural debt deferred to Platform Runtime Assembly Wave).
- No Digital Anchor file touched (Digital Anchor freeze preserved; OWC-DA is a strictly-later phase).
- No cross-cutting wiring change outside the existing per-line branches gated by `panel_kind == "matrix_script"` / `_ms_kind == "matrix_script"`.

### 4.3 Wave-position preservation
- No Platform Runtime Assembly Phases A–E.
- No Capability Expansion W2.2 / W2.3 / durable persistence / runtime API / third production line.
- No Plan A live-trial reopen.
- No new operator-eligible discovery surface promotion.

### 4.4 Scope-boundary preservation
- No provider / model / vendor / engine controls or operator selector.
- No donor namespace import (`from swiftcraft.*`).
- No Asset Supply page / promote service / DAM expansion beyond consuming PR-2 read-only browse.
- No React / Vite full rebuild or new component framework / new build dependency.
- No durable persistence backend swap; in-process closure store is acceptable per Recovery Decision §4.3.
- No bundling of MS-W* slices into a single PR; the §5 PR slicing plan is binding.

### 4.5 Closeout-paperwork independence
- Forcing, accelerating, conditioning, or tying the OWC-MS implementation gate opening or closing to any prior closeout signoff (recovery PR-1..PR-4 closeouts, Plan E phase closeouts) is forbidden. Each closeout stays independently pending in Raobin / Alisa / Jackie / product-manager queues.

---

## 5. PR Slicing Plan (binding)

OWC-MS implementation lands in exactly three sequential implementation PRs followed by one aggregating closeout PR. Bundling is forbidden.

| PR | Title | Slice | Ordering |
| --- | --- | --- | --- |
| OWC-MS PR-1 | Matrix Script Task Area Workflow Convergence | MS-W1 + MS-W2 | First; opens after §10 signoff |
| OWC-MS PR-2 | Matrix Script Workbench Five-Panel Convergence | MS-W3 + MS-W4 + MS-W5 + MS-W6 | After OWC-MS PR-1 merged + reviewed |
| OWC-MS PR-3 | Matrix Script Delivery Convergence + 回填 Multi-Channel | MS-W7 + MS-W8 | After OWC-MS PR-2 merged + reviewed |
| OWC-MS Closeout | Aggregating audit + signoff | (none — paperwork only) | After OWC-MS PR-3 merged + reviewed |

### 5.1 Per-PR file isolation contract

Each OWC-MS PR MUST satisfy:

- Service files: only `gateway/app/services/matrix_script/*` and the cross-cutting wiring seam files (`wiring.py`, `task_view_helpers.py`, `task_view_presenters.py`, `task_router_presenters.py`) restricted to the existing matrix_script branch.
- Templates: only the existing `{% if line_id == "matrix_script" %}` block in `tasks.html`, the existing matrix_script panel branch in `task_workbench.html`, and the existing `_ms_kind == "matrix_script"` block in `task_publish_hub.html`.
- Tests: each new service module gets a dedicated import-light test file under `gateway/app/services/tests/`.
- Hot Follow files: byte-stable.
- Digital Anchor files: byte-stable.
- Asset Supply files: read-only consumption only.

### 5.2 Test floor per PR

- OWC-MS PR-1: ≥25 test cases covering lane view projection, 8-stage state derivation, 8-field card rendering, isolation from Hot Follow / Digital Anchor.
- OWC-MS PR-2: ≥40 test cases covering per-panel projection, advisory emitter wiring, `review_zone` enum closed-set, isolation, no operator authoring of `source_script`.
- OWC-MS PR-3: ≥30 test cases covering copy_bundle row, multi-channel 回填, no schema widening.

---

## 6. Acceptance Evidence (binding rows)

The OWC-MS Closeout document MUST record the following rows as PASS / FAIL with explicit evidence pointer:

| Row | Check | Evidence requirement |
| --- | --- | --- |
| MS-A1 | OWC-MS PR-1 (MS-W1 + MS-W2) implementation green and merged | execution log + diff + PR # + squash commit |
| MS-A2 | OWC-MS PR-2 (MS-W3..W6) implementation green and merged | execution log + diff + PR # + squash commit |
| MS-A3 | OWC-MS PR-3 (MS-W7 + MS-W8) implementation green and merged | execution log + diff + PR # + squash commit |
| MS-A4 | Hot Follow baseline preserved (golden-path live regression) | coordinator confirmation block in closeout |
| MS-A5 | Digital Anchor freeze preserved per PR | per-PR forbidden-scope audit referenced in closeout |
| MS-A6 | §4 forbidden-scope audit (full pass on §4.1–§4.5) | row table in closeout matching §4 sub-sections |
| MS-A7 | OWC-MS Closeout signoff (Architect Raobin + Reviewer Alisa + Coordinator Jackie + Product Manager) | filled signoff block in closeout |
| MS-A8 | Product-Flow Module Presence rule (ENGINEERING_RULES §13) verified for each MS-W* slice | reviewer walks through `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Matrix Script blocks and confirms each module renders |

---

## 7. Preserved Freezes (binding)

The following are preserved verbatim by every OWC-MS PR. Any PR that mutates them is rejected.

- Hot Follow runtime + workbench + delivery + publish + reference packet.
- Matrix Script §8.A–§8.H closeout truth (correction chain CLOSED).
- Matrix Script frozen packet truth (envelope E1–E5 + validator R1–R5 admission cells PASS per RA-AGG).
- Digital Anchor formal entry route + payload builder + closure binding + role/speaker surface attachment + D.1 write-back as shipped by PR-4.
- Asset Supply minimum capability as shipped by PR-2.
- PR-1 unified `publish_readiness` producer + L3 `final_provenance` emitter + L4 `advisory_emitter`.
- Plan E phase closeout signoffs (A7 / UA7 / RA7) remain independently pending in Raobin / Alisa / Jackie's queue and are NOT advanced by any OWC-MS PR.

---

## 8. Stop Conditions (binding)

A Claude execution agent MUST stop and request architect review if any OWC-MS PR encounters:

- A required convergence cannot land without packet / schema / sample / template-truth mutation.
- A required projection cannot derive from existing four-layer state.
- Hot Follow business behavior must change to make a test pass.
- Digital Anchor file must be touched.
- A second authoritative producer is required.
- A new contract authoring outside the additive `review_zone` enum is required.

The default action on a stop condition is to NOT widen scope. Re-plan via a new gate-spec authoring step instead.

---

## 9. Review / Signoff Rule

OWC-MS PR review applies ENGINEERING_RULES §13 (Product-Flow Module Presence) plus the existing five-row review:

| Row | Check | Source |
| --- | --- | --- |
| R1 | Contract / runtime truth — no out-of-scope mutation | ENGINEERING_RULES §6 / §7 |
| R2 | Byte-isolation — Hot Follow + Digital Anchor unchanged; matrix_script edits inside per-line gates | Recovery Global Action §2 |
| R3 | Forbidden-scope — no Platform Runtime Assembly / Capability Expansion / provider controls / new line / asset platform / React rebuild | Recovery Global Action §2 |
| R4 | Unified-producer consumption — no second truth source | PR-1 acceptance |
| R5 | **Product-flow module presence** — each MS-W* slice in the PR's scope is operator-visible on the relevant template | ENGINEERING_RULES §13 + matrix_script_product_flow §§5–7 |

OWC-MS Closeout signoff matrix:

- Architect (Raobin) — R1 + R2 + R3 + R4 audit.
- Reviewer (Alisa) — independent re-verification of R1..R5.
- Product Manager — R5 product-flow conformance audit + go/no-go.
- Coordinator (Jackie) — byte-isolation regression + Hot Follow / Digital Anchor / Asset Supply preservation.

---

## 10. Architect + Reviewer Signoff (gate-opening)

§10 lines must be filled in a documentation-only PR before OWC-MS PR-1 may open. Until both are filled, the OWC-MS implementation gate is CLOSED.

- Architect (Raobin): `<fill>` — filled at `<YYYY-MM-DD HH:MM>` against this gate spec authoring commit.
- Reviewer (Alisa): `<fill>` — filled at `<YYYY-MM-DD HH:MM>` against this gate spec authoring commit.
- Coordinator (Jackie): `<fill>` — coordinator signoff binds OWC-MS Closeout row MS-A7, not gate opening.
- Product Manager: `<fill>` — product manager signoff binds OWC-MS Closeout row MS-A7, not gate opening.

---

## 11. Successor Phase

Successor Plan Phase: OWC-DA (see [owc_da_gate_spec_v1.md](owc_da_gate_spec_v1.md)).
OWC-DA implementation MAY NOT open until OWC-MS Closeout MS-A1..MS-A8 are PASS.

After OWC-DA Closeout completes, the next step is a separate trial re-entry review (re-anchoring [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0 sample-validity criteria for product-flow module presence). After trial re-entry signoff, Plan A live-trial may open. Platform Runtime Assembly Wave remains BLOCKED gated on Plan A live-trial closeout. Capability Expansion remains BLOCKED gated on Platform Runtime Assembly signoff.

---

## 12. Authority Pointers

- [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md)
- [docs/handoffs/apolloveo_2_0_design_handoff_v1.md](../handoffs/apolloveo_2_0_design_handoff_v1.md)
- [docs/contracts/matrix_script/](../contracts/matrix_script/) (frozen substrate; no mutation)
- [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md) (PR-1)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (Plan C amendments)
- [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md)
- [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md)
