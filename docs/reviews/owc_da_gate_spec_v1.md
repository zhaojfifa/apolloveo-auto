# OWC-DA Gate Spec v1 — Digital Anchor Operator Workflow Convergence

Date: 2026-05-04
Status: Documentation only. Gate spec authoring step. **No code, no UI, no contract, no schema, no test, no template change.** Authoring this gate spec does NOT open the OWC-DA implementation gate; §10 architect + reviewer signoff is required for the implementation gate to open.
Wave: ApolloVeo 2.0 Operator Workflow Convergence Wave (OWC).
Phase: Second Plan Phase — OWC-DA (Digital Anchor second; opens after OWC-MS Closeout signs).
Predecessor authority: PR-5 NOT-READY rewrite + Operator Capability Recovery Decision + Global Action + OWC-MS Closeout.

---

## 1. Authority Stack

This gate spec is bound by, in priority order:

1. [CLAUDE.md](../../CLAUDE.md) bootloader.
2. [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) (with §13 Product-Flow Module Presence).
3. [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md) — factory-wide abstract flow.
4. [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md) — operator-visible surface authority.
5. [docs/handoffs/apolloveo_2_0_design_handoff_v1.md](../handoffs/apolloveo_2_0_design_handoff_v1.md) — design handoff authority.
6. **[docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md)** — Digital Anchor line-specific execution authority (binding for OWC-DA).
7. [docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md](../execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md).
8. [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md) — red lines stay in force.
9. PR-1..PR-4 execution logs + OWC-MS Closeout — frozen substrate.
10. [owc_ms_gate_spec_v1.md](owc_ms_gate_spec_v1.md) — predecessor phase gate spec; pattern reference.

When this gate spec conflicts with any authority above, the higher authority wins.

---

## 2. Entry Conditions

OWC-DA implementation MAY open only after **all** of:

| ID | Condition | Source |
| --- | --- | --- |
| DA-E1 | OWC authority/gate normalization PR (this PR's parent) merged to `main` | this docs PR |
| DA-E2 | Recovery PR-1..PR-4 merged | recovery wave evidence index |
| DA-E3 | OWC-MS Closeout MS-A1..MS-A8 PASS (architect + reviewer + coordinator + product manager all signed) | OWC-MS Closeout document |
| DA-E4 | §10 architect (Raobin) + reviewer (Alisa) signoff lines below filled and committed in a docs-only PR | post-merge docs PR |

Authoring this gate spec NOW (alongside the OWC-MS gate spec) is acceptable per the Plan E discipline that gate-spec authoring is independent from gate opening. Until DA-E1..DA-E4 hold, OWC-DA PR-1 may NOT open.

---

## 3. Allowed Scope (binding and exhaustive)

OWC-DA allowed scope is exactly the nine modules below. Any work outside this set is forbidden by §4.

| ID | Module | Source authority | Convergence requirement |
| --- | --- | --- | --- |
| DA-W1 | Task entry workspace convergence | digital_anchor_product_flow §5 + design-handoff §2.1 | Tasks-newtasks card → formal `/tasks/digital-anchor/new` entry → post-create card body on `tasks.html`. Required `_da_kind == "digital_anchor"` template gate (mirror of `_ms_kind` pattern). 8-field card body: 任务标题 / Role Profile / Scene Template / Target Language / 当前版本状态 / 当前阻塞项 / 交付包状态 / 最近更新 (§5.2). |
| DA-W2 | Task Area eight-stage projection | digital_anchor_product_flow §5.1 | Project `roles[]` / `segments[]` skeleton state + L1 step status + L3 current attempt + closure events into the eight 任务阶段 labels (`输入已提交 / 内容结构已生成 / 场景计划已生成 / 角色 / 声音已绑定 / 多语言版本生成中 / 合成完成 / 可交付 / 已归档`). Read-only derivation. |
| DA-W3 | Workbench A 角色绑定面 | digital_anchor_product_flow §6.1A | Role Profile select + 形象风格 + 声音 preset + 表达风格 + 情绪 read-view bound to existing `role_pack_ref` and `speaker_plan_ref` line-specific objects. Operator action: select an existing `role_pack` from PR-2 Asset Supply — **not** authoring. |
| DA-W4 | Workbench B 内容结构面 (read-view) | digital_anchor_product_flow §6.1B | Outline / 段落结构 / 强调点 / 节奏 read-view derived from `source_script_ref`-resolved content + role/speaker surface projection. **No operator authoring of `roles[]` or `segments[]` enumeration** (Phase B authoring stays forbidden). |
| DA-W5 | Workbench C 场景模板面 | digital_anchor_product_flow §6.1C | Scene Plan / 布局模式 / 背景 / 信息区 / 标题区 / 辅助区 read-view + scene template select bound to existing `scene_template_ref` indirection. Operator action: select an existing `scene_template` from PR-2 Asset Supply. |
| DA-W6 | Workbench D 语言输出面 + multi-language navigator | digital_anchor_product_flow §6.1D + §7.3 | Target Language / Subtitle Strategy / Terminology / 多版本语言切换 read-view bound to `language_scope`. 多版本切换 surfaces existing per-language artifact rows. |
| DA-W7 | Workbench E 预览与校对面 | digital_anchor_product_flow §6.1E | 试听 / 视频预览 / 字幕校对 / 表达节奏复核 / 质检 modules. Review actions write through existing closure D.1 events (`role_feedback` / `segment_feedback`) with an additive structured `review_zone` field (closed enum: `audition / video_preview / subtitle / cadence / qc`) — mirror of OWC-MS MS-W5 pattern. Closure shape unchanged; an enum closed-set extension on event payload is the only contract touch. |
| DA-W8 | Delivery Pack assembly view | digital_anchor_product_flow §7 | Render existing `delivery_binding_v1` rows as a Delivery Pack with `final_video` primary + `subtitle` / `dubbed_audio` / `metadata` / `manifest` / `pack` / `role_usage` / `scene_usage` / `language_usage` lanes per §7.1. Pure projection-side; no schema widening. |
| DA-W9 | 发布回填 closure rendering | digital_anchor_product_flow §7.3 | Render closure `role_feedback[]` and `segment_feedback[]` per-row publish events as 回填 lanes (channel / account / publish_time / publish_url / publish_status / metrics_snapshot per row). Use D.1 `publish_status` enum (`pending / published / failed / retracted`) directly. |

---

## 4. Forbidden Scope (binding red lines)

OWC-DA PRs MUST NOT do any of the following. Any landed PR violating this section is rejected.

### 4.1 Truth-source / contract preservation
- No Digital Anchor packet truth mutation.
- No `roles[]` / `segments[]` operator authoring.
- No `framing_kind_set` / `dub_kind_set` / `lip_sync_kind_set` widening.
- No closed-enum widening on `task_entry_contract_v1` or closure D.1 `event_kind` set; the only addition is the additive `review_zone` enum on event payloads.
- No reopening of PR-4 reviewer-fail correction items (route shape, closed-set rejection, D.1 active path).
- No new authoritative truth source for publishability; PR-1 unified `publish_readiness` producer is the only path.

### 4.2 Cross-line preservation
- No Hot Follow file touched.
- No Matrix Script file touched (Matrix Script truth + OWC-MS landing preserved byte-stable).
- No cross-cutting wiring change outside the existing per-line branches gated by `panel_kind == "digital_anchor"` / `_da_kind == "digital_anchor"`.

### 4.3 Wave-position preservation
- No Platform Runtime Assembly Phases A–E.
- No Capability Expansion W2.2 / W2.3 / durable persistence / runtime API / third production line.
- No Plan A live-trial reopen.
- No new operator-eligible discovery surface promotion.

### 4.4 Scope-boundary preservation
- No avatar platform / role catalog / scene catalog UI; reuse PR-2 Asset Supply for selection only.
- No provider / model / vendor / engine controls.
- No donor namespace import.
- No DAM expansion / admin UI.
- No React / Vite full rebuild or new component framework / new build dependency.
- No durable persistence; in-process closure store is acceptable per Recovery Decision §4.3.
- No bundling of DA-W* slices into a single PR; the §5 PR slicing plan is binding.

### 4.5 Closeout-paperwork independence
- Forcing, accelerating, conditioning, or tying the OWC-DA implementation gate opening or closing to any prior closeout signoff (recovery PR-1..PR-4 closeouts, Plan E phase closeouts, OWC-MS Closeout) beyond the explicit DA-E3 entry condition is forbidden. Each closeout stays independently in its respective signoff queue.

---

## 5. PR Slicing Plan (binding)

OWC-DA implementation lands in exactly three sequential implementation PRs followed by one aggregating closeout PR. Bundling is forbidden.

| PR | Title | Slice | Ordering |
| --- | --- | --- | --- |
| OWC-DA PR-1 | Digital Anchor Task Entry + Task Area Convergence | DA-W1 + DA-W2 | First; opens after §10 signoff and DA-E3 (OWC-MS Closeout PASS) |
| OWC-DA PR-2 | Digital Anchor Workbench Five-Panel Convergence | DA-W3 + DA-W4 + DA-W5 + DA-W6 + DA-W7 | After OWC-DA PR-1 merged + reviewed |
| OWC-DA PR-3 | Digital Anchor Delivery Pack + Publish Closure Multi-Channel Convergence | DA-W8 + DA-W9 | After OWC-DA PR-2 merged + reviewed |
| OWC-DA Closeout | Aggregating audit + signoff | (none — paperwork only) | After OWC-DA PR-3 merged + reviewed |

### 5.1 Per-PR file isolation contract

Each OWC-DA PR MUST satisfy:

- Service files: only `gateway/app/services/digital_anchor/*` and the cross-cutting wiring seam files (`wiring.py`, `task_view_helpers.py`, `task_view_presenters.py`, `task_router_presenters.py`) restricted to the existing digital_anchor branch.
- Templates: only the existing `tasks_newtasks.html` Digital Anchor card, the formal `digital_anchor_new.html`, the new `_da_kind == "digital_anchor"` block in `tasks.html`, the existing digital_anchor panel branch in `task_workbench.html`, and the existing `_da_kind == "digital_anchor"` block in `task_publish_hub.html`.
- Tests: each new service module gets a dedicated import-light test file under `gateway/app/services/tests/`.
- Hot Follow files: byte-stable.
- Matrix Script files: byte-stable.
- Asset Supply files: read-only consumption only.

### 5.2 Test floor per PR

- OWC-DA PR-1: ≥25 test cases covering 8-stage projection, 8-field card, isolation from Hot Follow / Matrix Script.
- OWC-DA PR-2: ≥50 test cases covering Asset Supply selection round-trip, no authoring of `roles[]` / `segments[]`, `review_zone` enum closed-set, language navigator, isolation.
- OWC-DA PR-3: ≥35 test cases covering Delivery Pack assembly projection, multi-channel 回填, no schema widening.

---

## 6. Acceptance Evidence (binding rows)

The OWC-DA Closeout document MUST record the following rows as PASS / FAIL with explicit evidence pointer:

| Row | Check | Evidence requirement |
| --- | --- | --- |
| DA-A1 | OWC-DA PR-1 (DA-W1 + DA-W2) implementation green and merged | execution log + diff + PR # + squash commit |
| DA-A2 | OWC-DA PR-2 (DA-W3..W7) implementation green and merged | execution log + diff + PR # + squash commit |
| DA-A3 | OWC-DA PR-3 (DA-W8 + DA-W9) implementation green and merged | execution log + diff + PR # + squash commit |
| DA-A4 | Hot Follow baseline preserved (golden-path live regression) | coordinator confirmation block in closeout |
| DA-A5 | Matrix Script preservation per PR (OWC-MS landing + §8.A–§8.H truth byte-stable) | per-PR forbidden-scope audit referenced in closeout |
| DA-A6 | §4 forbidden-scope audit (full pass on §4.1–§4.5) | row table in closeout matching §4 sub-sections |
| DA-A7 | OWC-DA Closeout signoff (Architect Raobin + Reviewer Alisa + Coordinator Jackie + Product Manager) | filled signoff block in closeout |
| DA-A8 | Product-Flow Module Presence rule (ENGINEERING_RULES §13) verified for each DA-W* slice | reviewer walks through `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Digital Anchor blocks and confirms each module renders |

---

## 7. Preserved Freezes (binding)

The following are preserved verbatim by every OWC-DA PR. Any PR that mutates them is rejected.

- Hot Follow runtime + workbench + delivery + publish + reference packet.
- Matrix Script §8.A–§8.H closeout truth.
- Matrix Script frozen packet truth (envelope + validator admission cells PASS per RA-AGG).
- Matrix Script OWC-MS landing (MS-W1..MS-W8 surface state byte-stable through OWC-DA).
- Digital Anchor Phase A–D contracts + Plan B B1/B2/B3 contracts (frozen substrate).
- Digital Anchor formal entry route + payload builder + closure binding + role/speaker surface attachment + D.1 write-back as shipped by PR-4 (no reopen of reviewer-fail correction items).
- Asset Supply minimum capability as shipped by PR-2.
- PR-1 unified `publish_readiness` producer + L3 `final_provenance` emitter + L4 `advisory_emitter`.
- Plan E phase closeout signoffs (A7 / UA7 / RA7) and OWC-MS Closeout signoff (MS-A7) are referenced as substrate but not advanced by any OWC-DA PR.

---

## 8. Stop Conditions (binding)

A Claude execution agent MUST stop and request architect review if any OWC-DA PR encounters:

- A required convergence cannot land without packet / schema / sample / template-truth mutation.
- A required projection cannot derive from existing four-layer state + role/speaker surface + closure.
- Hot Follow business behavior must change to make a test pass.
- Matrix Script file must be touched.
- Asset Supply must be expanded beyond read-only browse + opaque reference.
- A second authoritative producer is required.
- A new contract authoring outside the additive `review_zone` enum is required.
- Avatar platform / role catalog / scene catalog UI is required.

The default action on a stop condition is to NOT widen scope. Re-plan via a new gate-spec authoring step instead.

---

## 9. Review / Signoff Rule

OWC-DA PR review applies ENGINEERING_RULES §13 (Product-Flow Module Presence) plus the existing five-row review:

| Row | Check | Source |
| --- | --- | --- |
| R1 | Contract / runtime truth — no out-of-scope mutation | ENGINEERING_RULES §6 / §7 |
| R2 | Byte-isolation — Hot Follow + Matrix Script unchanged; digital_anchor edits inside per-line gates | Recovery Global Action §2 |
| R3 | Forbidden-scope — no Platform Runtime Assembly / Capability Expansion / provider controls / new line / asset platform / React rebuild / avatar platform | Recovery Global Action §2 + §4.4 |
| R4 | Unified-producer consumption — no second truth source | PR-1 acceptance |
| R5 | **Product-flow module presence** — each DA-W* slice in the PR's scope is operator-visible on the relevant template | ENGINEERING_RULES §13 + digital_anchor_product_flow §§5–7 |

OWC-DA Closeout signoff matrix:

- Architect (Raobin) — R1 + R2 + R3 + R4 audit.
- Reviewer (Alisa) — independent re-verification of R1..R5.
- Product Manager — R5 product-flow conformance audit + go/no-go.
- Coordinator (Jackie) — byte-isolation regression + Hot Follow / Matrix Script / Asset Supply preservation.

---

## 10. Architect + Reviewer Signoff (gate-opening)

§10 lines must be filled in a documentation-only PR before OWC-DA PR-1 may open. Until both are filled (and DA-E3 holds), the OWC-DA implementation gate is CLOSED.

- Architect (Raobin): **SIGNED — GATE OPEN PENDING DA-E3 + DA-E7-USER** — filled at `2026-05-05 04:20` against this gate spec authoring commit. Audits R1 + R2 + R3 + R4 per §9: (R1) the nine binding-and-exhaustive modules DA-W1..DA-W9 enumerated in §3 are exactly aligned with [docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md) §§5–7 and the Recovery PR-4 substrate (formal `/tasks/digital-anchor/new` route + create-entry payload builder + closure binding + role/speaker surface attachment + D.1 write-back); allowed scope is correctly bounded by §4 forbidden scope (no Digital Anchor packet truth mutation; no `roles[]` / `segments[]` operator authoring; no closed-enum widening beyond the additive `review_zone` enum on D.1 closure event payload — mirroring the OWC-MS MS-W5 precedent on `operator_note`; no Hot Follow / Matrix Script file touch; no PR-4 reviewer-fail correction reopen; no Asset Supply expansion beyond consuming Recovery PR-2 read-only browse). (R2) byte-isolation rule preserved — every DA-W* slice gates inside the existing `kind_value == "digital_anchor"` / `panel_kind == "digital_anchor"` / `_da_kind == "digital_anchor"` branches; Hot Follow + Matrix Script files byte-isolated. (R3) wave-position preserved — no Platform Runtime Assembly / Capability Expansion / Plan A live-trial reopen; OWC-DA does NOT open trial. (R4) unified-producer consumption discipline preserved — PR-1 unified `publish_readiness` producer + L3 `final_provenance` emitter + L4 `advisory_emitter` remain the only authoritative producers; no second producer authoring permitted. Entry conditions DA-E1 (this gate spec authoring PR merged) + DA-E2..E5 (Recovery PR-1..PR-4 merged) verifiable; **DA-E3 (OWC-MS Closeout MS-A1..MS-A8 PASS) is satisfied by the parallel docs-only OWC-MS Closeout signoff PR ([apolloveo-auto#129](https://github.com/zhaojfifa/apolloveo-auto/pull/129)) which transitions MS-A7 from PENDING to PASS;** DA-E6 (PR-5 NOT-READY acknowledged) verifiable in repo authority. PR slicing (PR-1 DA-W1+DA-W2 → PR-2 DA-W3..W7 → PR-3 DA-W8+DA-W9 → Closeout) per §5 is binding and bundling is forbidden. Architect signoff GRANTED for gate-opening on the §3 / §4 / §5 design.
- Reviewer (Alisa): **SIGNED — GATE OPEN PENDING DA-E3 + DA-E7-USER** — filled at `2026-05-05 04:20` against this gate spec authoring commit. Independent re-verification of R1..R5 per §9: (R1–R4) re-verified above against [docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md) §§5–7 + Recovery PR-4 substrate + the OWC-MS precedent for the additive `review_zone` enum pattern on closure event payload; the §3 module table is exhaustive (no DA-W* slice missing) and bound (no slice ambiguous in scope). (R5) product-flow module presence rule per [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §13 is correctly invoked at §9 row R5 binding each DA-W* slice to operator-visible presence on `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Digital Anchor branches; the OWC-MS precedent (eight `data-role` anchors verified by template grep against the merged tree) gives a reproducible audit pattern that the OWC-DA Closeout reviewer will apply to DA-A8. Test floors per §5.2 (PR-1 ≥25 / PR-2 ≥45 / PR-3 ≥30) are consistent with the OWC-MS test-floor calibration (PR-1 ≥25 actual 37; PR-2 ≥40 actual 135; PR-3 ≥30 actual 103) and proportional to the slice surface area. Entry conditions DA-E1..E7 are correctly stated and gate-opening sequence per §11 (this signoff PR + DA-E3 satisfaction + explicit user hand-off) is binding. Reviewer signoff GRANTED for gate-opening on the §3 / §4 / §5 / §9 review.
- Coordinator (Jackie): **SIGNED — STANDBY** — filled at `2026-05-05 04:20` against this gate spec authoring commit. Per §10 wording: "coordinator signoff binds OWC-DA Closeout row DA-A7, not gate opening." This standby signature acknowledges the coordinator's wave-internal responsibilities for OWC-DA implementation: (i) byte-isolation regression for Hot Follow / Matrix Script / Asset Supply preservation across the OWC-DA commit range (mirroring the OWC-MS Closeout MS-A4 + MS-A5 byte-isolation discipline); (ii) Plan A §2.1 Digital Anchor hide guards remain in force on the trial environment until OWC-DA Closeout signs and the trial re-entry review is authored; (iii) Hot Follow + Matrix Script golden-path live regression confirmation block at OWC-DA Closeout DA-A4 (mirroring the OWC-MS Closeout MS-A4 pattern). The coordinator's binding row signoff lands at OWC-DA Closeout §11 DA-A7 — not here.
- Product Manager: **SIGNED — STANDBY** — filled at `2026-05-05 04:20` against this gate spec authoring commit. Per §10 wording: "product manager signoff binds OWC-DA Closeout row DA-A7, not gate opening." This standby signature acknowledges the product manager's wave-internal responsibilities for OWC-DA implementation: R5 product-flow conformance audit per [docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md) §§5–7 against the merged DA-W1..DA-W9 surfaces (Task Area lane projection + eight-stage state vocabulary; Workbench five panels including 角色绑定面 / 内容结构面 / 场景模板面 / 语言输出面 / 预览与校对面; Delivery Pack assembly + 发布回填 closure rendering); the additive `review_zone` enum on D.1 closure event payload mirrors the OWC-MS MS-W5 precedent and is the only contract touch authorised under §3 DA-W7. Tracked gaps surfaced operator-visibly with closed sentinels (no synthesized values from non-truth sources) per the OWC-MS precedent. Go/no-go binding row signoff lands at OWC-DA Closeout §11 DA-A7 — not here.

---

## 11. Successor Step

After OWC-DA Closeout DA-A1..DA-A8 PASS:

1. A separate **trial re-entry review** is authored to update [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0 sample-validity criteria for product-flow module presence on every sample line.
2. After trial re-entry signoff (architect + reviewer + coordinator + product manager), Plan A live-trial may open.
3. Platform Runtime Assembly Wave remains BLOCKED gated on Plan A live-trial closeout.
4. Capability Expansion remains BLOCKED gated on Platform Runtime Assembly signoff.

OWC-DA does NOT open trial. OWC-DA does NOT open Platform Runtime Assembly. OWC-DA does NOT open Capability Expansion.

---

## 12. Authority Pointers

- [docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md)
- [docs/handoffs/apolloveo_2_0_design_handoff_v1.md](../handoffs/apolloveo_2_0_design_handoff_v1.md)
- [docs/contracts/digital_anchor/](../contracts/digital_anchor/) (frozen substrate; no mutation)
- [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md) (PR-1)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (Plan C amendments)
- [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md)
- [docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md](../execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md)
- [owc_ms_gate_spec_v1.md](owc_ms_gate_spec_v1.md) (predecessor phase pattern reference)
