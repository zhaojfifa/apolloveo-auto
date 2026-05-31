# Matrix Script Workbench · Product-Flow Reset Design v1

Date: 2026-05-29
Status: **Design package only.** No code, no template edits, no contract / schema / packet / closed-enum / runtime change. No Hot Follow / Digital Anchor / Asset Supply touch. No backend generation implied. No fake `final_video` / `publish_url`. This document does NOT open any implementation gate; it is the design anchor for a future implementation wave.

Authoring authority of this reset: user-issued mission `[SYSTEM OVERRIDE]` on 2026-05-29 acknowledging that the prior wave (PR-1 → PR-4 on `VeoMatrix01` + `VeoMatrixVoice01`) drifted from the result-oriented IA target. This document supersedes — for design purposes only — any implementation pattern from the prior wave that contradicts the product flow doc.

Branch: `design/ms-workbench-product-flow-reset-20260529` (created from `origin/VeoMatrixVoice01`).

---

## 1. Reading Declaration

Read before authoring this document:

- [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md) §§1–7 (business definition, content structure, variant dimensions, task area, workbench module spec, delivery center)
- [docs/design/matrix_script_result_oriented_ui_plan_v1.md](matrix_script_result_oriented_ui_plan_v1.md) §1 (declarative intent + non-scope) + sections on operator-visible block mapping
- [docs/design/matrix_script_workbench_wireframe_v1.md](matrix_script_workbench_wireframe_v1.md) §1 (page goal — the operator's six 10-second questions)
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](ApolloVeo_Operator_Visible_Surfaces_v1.md) (five operator-visible surfaces; validator R3 red lines)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) (panel_kind dispatch; shell neutrality)
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (`required` / `blocking_publish` zoning; scene_pack non-blocking)
- [docs/product/digital_anchor_product_flow_v1.md](../product/digital_anchor_product_flow_v1.md) (cross-reference for alignment-rule note in §7)
- [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md) (to locate active authority files)

Wave evidence read:

- The prior wave's 7 PRs and their reports under `docs/design/screenshots/matrix_script_ui_redesign_2026-05-28/{pr1,pr2a,pr2b,pr2c,pr2d,pr3,pr4}/PR*_REPORT.md`
- Live deployment verification report (this conversation, 2026-05-28): `apolloveo.com` currently serves `git_sha=da5d7ec` (on `main`), confirming the wave's content is on `VeoMatrixVoice01` but never deployed; the "Workbench still wrong" observation reflects the wave's content as merged on `VeoMatrixVoice01`, not a stale build

---

## 2. Context Summary

### 2.1 What was attempted on `VeoMatrix01` / `VeoMatrixVoice01`

Seven branches, 147 new tests, 14 HTML snapshots:

- **PR-1**: New Task page operator boundary — hide opaque `source_script_ref` + mint button behind `?technical=1`; render paste / upload / select primary tabs.
- **PR-2A**: New "主视频结果" anchor block at the TOP of the matrix_script Workbench branch with state pill (未生成 / 生成中 / 待审核 / 可交付), preview hero (honest empty state when no media), 4-action bar (生成主视频 / 重新生成 / 确认为主版本 / 前往交付页面), operator-language blocker + next-action banner.
- **PR-2B**: Compact horizontal stepper 脚本结构 → 变体选择 → 生成 inserted between the new main-video block and the legacy Block A.
- **PR-2C**: Block E renamed 候选评审 → 可选变体 with Mission §B.3 verbatim empty-state copy.
- **PR-2D**: Quarantine sweep — moved `publish_readiness` / `head_reason` / `final_video` / `RC-R8` out of Block D banner / Block E + F tech notes; simplified Block F "待补齐" to mission baseline.
- **PR-3**: Delivery Center reframed to 6 mission sections (① 介绍 / ② 主视频 / ③ 必需 / ④ 可选 / ⑤ 发布设置 / ⑥ 发布回填); added publish-settings form using the existing closure event endpoint.
- **PR-4**: Unified visual validation report — claimed 35/35 PASS.

Integration branches `VeoMatrix01` (Matrix Script only) and `VeoMatrixVoice01` (Matrix Script + VoiceTrans) were pushed to origin. Source-level grep confirms PR-1 gating works (`technical_mode` is consumed; hidden input present in operator mode; mint button gated). The page's first screen on the New Task surface is correctly result-oriented at the input layer.

### 2.2 What improved

- **New Task page**: paste / upload / select primary tabs; opaque `source_script_ref` is a hidden input in operator mode; mint button only revealed under `?technical=1`. The first complaint ("operator pastes script in opaque-ref slot") is resolved.
- **Workbench dominance**: a 主视频结果 anchor block is present at the TOP of the matrix_script branch (above the legacy Block A) — the first visual element is no longer task-meta.
- **Block E empty state**: a single mission-mandated operator-language message replaces N empty per-candidate cards.
- **Block F simplified**: a 2-line 已具备 / 待补齐 summary + CTA to Delivery Center; per-row deliverable tables removed from the Workbench.
- **Delivery Center 6 sections** numbered ① → ⑥; new ⑤ 发布设置 form added.
- **Diagnostics fold** is operationally complete: F · 诊断 collapsed-by-default carrying all engineering identifiers.

### 2.3 What still failed (operator validation 2026-05-29)

Despite the 35/35 PR-4 self-report, manual operator validation observed:

1. **Workbench still starts with a large task-meta card**. The 主视频结果 anchor was added ABOVE the existing Block A 任务摘要 — but Block A itself still renders, large, immediately below. Operators see two redundant first-screen anchors competing for attention.
2. **Task ID / platform / category / status are still visually prominent** elsewhere on the page (the page `<title>`, the workbench shell header strip, Block A meta fields).
3. **The old A / B / C / D / E / F block structure survived in full**. The redesign added new blocks ABOVE the old ones; it never replaced them. The page now has *more* blocks than before, not fewer.
4. **Old labelled blocks remain present and labelled**: 任务摘要 (Block A), 脚本结构 (Block B), 变体方案 (Block C), 生成进度 (Block D), 可选变体 (Block E, post-rename), 交付摘要 (Block F). Per the user feedback, this still reads like "six backend projections" to the operator, not a result-first journey.
5. **Backend vocabulary still leaks** in places the quarantine missed (per the live validation grep — these were in helpers that PR-2D's sweep partially covered but did not eliminate):
   - `publish_readiness` (in helper data-attrs + a small number of helper-emitted operator-visible strings)
   - `closure` (in event-log explanations on review-zone surfaces)
   - `final_video` (in some tech-notes still on the surface, not just collapsed)
   - `RC-R8` (in self-referential "no-fake-output" disclaimers)
   - `audience=[b2b, b2c]`, `tone=[casual, formal, playful]`, `length=[30, 45, 60, 75]` (raw Phase-B axis arrays in Block B Body card AND Block C variant table 差异点 column — this is Visual Issue #4 from the PR-4 report, deferred at the time)
   - `provider` / `model` / `vendor` / `engine` (only as red-line "禁用词" chip list — legitimate, but still operator-confusing without context)
   - 任务 ID as a heading-tier element in places
6. **Operators still cannot answer the 5 anchor questions clearly** even on the integrated build:
   - Q1 "What main video am I producing?" — partially answered by 主视频结果 subtitle, but the task title is buried under Block A.
   - Q2 "Is the main video generated?" — answered by the state pill if the operator looks at the right block; but the same answer is restated in 4 places (主视频结果 pill + 生产流程 step 3 pill + Block D pill + Block F pill) with subtly different wording.
   - Q3 "What is blocking it?" — answered, but the answer appears in 3 places (主视频结果 banner + Block D banner + Block F banner), in 3 different copy styles.
   - Q4 "What do I do next?" — same multi-locality problem.
   - Q5 "Where do I deliver and publish?" — there's a CTA in 主视频结果 + Block F + the stepper; operators report uncertainty about which one is canonical.

### 2.4 Why the current Workbench is not operator-centered

The wave delivered an **additive** redesign on top of the legacy structure rather than a **replacement** redesign. The 主视频结果 block was added, but Block A was preserved. The compact stepper was added, but Blocks B/C/D were preserved. The 可选变体 rename happened, but the candidate-card structure stayed intact. The operator now sees:

```
[NEW] 主视频结果 (PR-2A)
[NEW] 生产流程可观测 stepper (PR-2B)
[OLD] Block A 任务摘要              ← redundant with 主视频结果 meta
[OLD] Block B 脚本结构              ← redundant with stepper Step 1 detail
[OLD] Block C 变体方案              ← redundant with stepper Step 2 detail
[OLD] Block D 生成进度              ← redundant with 主视频结果 + stepper Step 3
[OLD/RENAMED] Block E 可选变体     ← variants now optional but still dominant
[OLD/SIMPLIFIED] Block F 交付摘要   ← redundant with 主视频结果 "前往交付页面" CTA
[COLLAPSED] F · 诊断                ← architect view
```

The visible result on a real task is ~8 sections of content, not 5. The operator's journey has more anchors after the wave, not fewer. The wave optimised for *additive* compatibility (preserve every `data-role` marker for test back-compat) instead of *subtractive* clarity (delete what the operator does not need to see).

---

## 3. Product-Flow Diagnosis

Four root causes:

1. **Patches instead of replacement.** Each PR added a new block above or beside the legacy structure. None of the PRs *removed* a legacy block. PR-2C renamed Block E in place; PR-2D simplified Block F in place; PR-3 reordered Delivery Center headings in place. The implementation pattern was "add new, demote old" — but in HTML, demotion still leaves the old block visible.

2. **Backend projection language leaked back into primary UI.** PR-2D's quarantine sweep was string-level (find/replace on a handful of helper constants) rather than structural (refactor the helper output shape). Strings outside the sweep — Block B Body card axis arrays, Block C 差异点 raw values, review-zone helper subtitles, advisory tech notes — kept their engineering vocabulary. The Visual Validation Report #4 acknowledged this as deferred but the wave closed without fixing it.

3. **Old A/B/C/D/E/F structure survived.** The OWC-MS gate spec + MS-RO design package both define a six-block structure as the operator-visible substrate. PR-1..PR-3 honoured that by ADDING the new result-first blocks alongside the existing six. The wave needed authority to *retire* the legacy six-block structure in favour of a 4-section IA — that authority was never authored, and the wave proceeded without it.

4. **Result-first design was added on top of old blocks, not as their replacement.** The PR-2A 主视频结果 block sits above Block A but does not replace it. The PR-2B stepper sits above Blocks B/C/D but does not replace them. The PR-2D simplification of Block F sits above the F · 诊断 fold but does not remove the redundant 交付状态摘要 pill from elsewhere on the page.

Workbench and Delivery Center boundary is also still fuzzy:
- 主视频结果 actions include "确认为主版本" — that's a per-variant write-through that arguably belongs in Delivery Center's main-video confirmation flow.
- Block F 交付摘要 has its own state pill that re-derives publishability — Delivery Center's ① 交付结果介绍 should be the single source for this.
- The closure event-log on Workbench (review-zone forms) is a backend-feedback affordance; operator's mental model wants this in Delivery Center / Publish Feedback, not on the workbench.

---

## 4. Target Workbench IA (final, four primary sections)

This section defines the **only** primary content that should render on the matrix_script Workbench branch after the reset. The legacy A/B/C/D/E/F structure must be RETIRED from primary view (their data-role markers may be preserved inside the 技术诊断 collapsed fold for back-compat with existing structural tests, but they MUST NOT render as visible operator content).

### Section 1 · 主视频结果 (PRIMARY, dominant first screen)

This is the first and dominant section. It is the page's identity.

It answers:
- 是否已经生成主视频？
- 当前能不能交付？
- 当前阻塞是什么？
- 下一步该做什么？

**State pill** (closed 4-value enum, operator-language only):
- 未生成
- 生成中
- 待审核
- 可交付

**No-video state copy** (verbatim):

> "当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。"

**Actions** (state-dependent enablement; same 4-action contract as PR-2A):
- 生成主视频 (disabled-with-tooltip until generation backend lands)
- 重新生成 (same)
- 确认为主版本 (enabled only when at least one variation has `current_fresh` media + no confirmation yet; writes the existing `[main-version-confirmed]` operator_note via existing closure endpoint)
- 前往交付页面 (always enabled; canonical CTA to Delivery Center)

**Operator-language blocker + next-action one-liner** below the action bar. Engineering enum values NEVER appear in this copy.

### Section 2 · 生产流程可观测 (SECONDARY, compact, collapsed-detail by default)

A compact 3-step horizontal stepper. Navigation aid only. Not dominant. Total collapsed height ≤120px.

Flow: **脚本结构 → 变体选择 → 生成**

Each step is *collapsed by default* — clicking expands inline detail. The expanded detail content is:

- **脚本结构**: Hook (前 3 秒) / Body (中段) / CTA (结尾) / 关键词 / 禁用词 (rendered as operator-readable cards; ALL raw axis arrays + bracketed English tuples REMOVED)
- **变体选择**: 主推版本 marker / 变体数量 / 变体差异维度 in operator language (**语气 / 时长 / 受众 / 开头方式 / 画面方向**; the last two are stubbed with `STATUS_UNRESOLVED` operator-language sentinels until Outline Contract lands — same pattern as PR-2A)
- **生成**: 主视频状态 (mirrors Section 1's pill) / 当前阻塞 / 下一步 (read-only; actions live in Section 1)

The expanded detail content for Step 1 (脚本结构) is the ONLY place Block B's content survives. Step 2 detail is the ONLY place Block C's content survives. Step 3 detail is the ONLY place Block D's content survives. **The standalone Block B / Block C / Block D op-cards are RETIRED from primary view.** Their `data-role` markers may be preserved inside the 技术诊断 fold for test back-compat.

### Section 3 · 可选变体 (TERTIARY)

Variants are not the center of the Workbench. The center is Section 1's main video result.

Show:
- 当前主推版本 (one card; same variant referenced by Section 1's preview)
- 其他变体 (folded list of N − 1 cards; expand on click)
- 追加生成变体 (action button; disabled-with-tooltip until generation backend)
- 同时生成多个变体 (action button; same)

If no media exists on any variation (the universal state today), render a single operator-language message:

> "暂未生成变体视频。你可以先生成主视频，或选择同时生成多个变体。"

**Do not render four empty candidate cards. Do not render large backend-like variation tables.** This is the same wording PR-2C landed; the difference here is that the empty-state IS the entire Section 3 content, not an empty-state branch sitting next to a large Block E op-card.

The per-variant review-zone write-through forms (PR-2C / MS-W5 substrate) move INSIDE the expanded variant detail under "当前主推版本" / "其他变体" — preserving the closure-write contract without surfacing the review-zone as an autonomous panel.

### Section 4 · 交付入口 (LIGHTWEIGHT)

Workbench shows a **2-line lightweight delivery entry only**:

> "当前不能交付：尚未生成主视频。"
> "生成完成后，可前往交付页面查看成片、字幕、音频、文案包与发布设置。"

Plus a single CTA: **前往交付页面 →**

When the task is publishable, the copy switches to:

> "可交付 · 已确认主版本。"
> "前往交付页面填写发布设置或回填发布状态。"

No full delivery rows in Workbench. No publish form. No publish-feedback backfill table. No state pill restating Section 1's pill. Those all live in Delivery Center only.

### Section 5 · 技术诊断 (COLLAPSED by default — architect view only)

`<details>` collapsed by default. Operator never sees it on the primary scan. Architects expand for audit.

All retired-from-primary content lives here:
- The full legacy A / B / C / D / E / F op-card markup (preserved for `data-role` back-compat with prior wave's structural tests)
- All engineering identifiers (`publish_readiness`, `head_reason`, `artifact_lookup`, `final_video` raw field references, `RC-R8` audit notes, `closure` event-log explanations, `slot_pack`, `provenance`, `variation_axis`, raw axis arrays)
- The PR-U2 / MS-W3 / RC PR-1..4 secondary diagnostics
- Task ID (visible as a code-styled label, not as a heading)
- All packet ref handles

---

## 5. Forbidden Primary UI Vocabulary

This is the binding list. Any token below appearing in any operator-visible primary section (Sections 1–4) on the matrix_script Workbench branch is a reviewer-fail blocker. They are permitted inside the collapsed Section 5 fold only.

| Forbidden in primary UI | Reason |
|---|---|
| `source_script_ref` | engineering field name; operator sees 脚本来源 if anything |
| `content://`, `task://`, `asset://`, `ref://` | opaque handle vocabulary |
| `publish_readiness` | engineering producer name; operator sees 发布门禁 |
| `head_reason` | engineering enum field; operator sees the language label only |
| `artifact_lookup` | engineering field; operator sees 产物状态 |
| `final_video` (as a raw field name) | engineering field; operator sees 主视频 / 成片 |
| `RC-R8` (audit reference) | engineering audit reference |
| `closure` (raw English) | engineering noun; operator sees 反馈回填 / 操作记录 |
| `slot_pack`, `script_slot_ref`, `cell_id` | engineering identifiers |
| `provenance`, `final_provenance` | engineering field |
| `variation_axis`, `axis_id` | engineering field |
| `audience=[b2b, b2c]` | raw axis array |
| `tone=[casual, formal, playful]` | raw axis array |
| `length=[30, 45, 60, 75]` | raw axis array |
| `provider`, `model`, `vendor`, `engine` (as labels or selectors) | validator R3 red line |
| 任务 ID as a heading (`<h1>` / `<h2>` / `op-section-title`) | task ID is metadata, not content |

These tokens may appear inside Section 5 (技术诊断), inside `<title>` tags, inside JS string literals that aren't rendered as visible text, and inside HTML comments — none of which are operator-visible.

---

## 6. Delivery Center reset

Delivery Center keeps the PR-3 six-section structure, with one tightening: **NO generation controls anywhere**, and **NO production-flow panels anywhere**.

| # | Section | Content |
|---|---|---|
| ① | 交付结果介绍 | 1–2 paragraph operator-language summary: which main video, current delivery status, what's missing if not ready. No tables. Single state pill (re-uses Workbench Section 1's enum so the operator sees the same word in both places). |
| ② | 主视频 | Preview if available (real artifact only — RC-R8 honesty preserved). Download if available. Operator-language empty state if unavailable. NO "生成主视频" button (that's Workbench-only). |
| ③ | 必需交付物 | 5 fixed operator-language rows: 字幕 / 音频 / 文案包 / manifest / 交付包. Each row: 名称 + 状态 (resolved / 缺失 / 历史版本) + 下载 (when resolved) + "在 Workbench 重新生成" CTA (when missing — link back to Workbench, never inline regen here). |
| ④ | 可选交付物 | 其他变体 (folded list with download per variant) / scene_pack (with non-blocking tag) / supporting material (operator-language label, hidden when absent — never an empty row). |
| ⑤ | 发布设置 | Form: platform (datalist with TikTok / YouTube Shorts / Instagram Reels / 抖音 / 视频号 / 小红书 / 快手; free-text allowed per product decision #3) / account / title / copy / hashtags / scheduled time. Submit writes `operator_publish` via existing closure endpoint. Honesty note: "本表单不直接对外发布". |
| ⑥ | 发布回填 | publish URL / publish status / operator note / metrics placeholder. Timeline of closure publish events (rendered as operator-language rows, NEVER showing `event_kind` enum literals). |

Boundary rule: Delivery Center MUST NOT show any production-flow editing controls (no script structure editor, no variant axis selector, no "生成" button). Operators who need to change production state click "在 Workbench 重新生成" to return to the Workbench surface.

---

## 7. Digital Anchor alignment note (NOT redesigned here)

Do NOT redesign Digital Anchor in this wave. Recorded alignment rule for whenever DA's redesign opens:

> Digital Anchor should also be **result-first**: main anchor video result → content / role / scene / language observability → delivery pack → publish / feedback.
> Do NOT dump raw `role_pack` / `speaker_plan` / `scene_template` contract objects into primary UI. Mirror the Matrix Script reset: one dominant main-video-result anchor, a compact observability stepper for content / role / scene / language, secondary asset binding controls, lightweight delivery entry, collapsed technical diagnostics.

Digital Anchor's standing operations verdict (per the post-OWC addendum §2.3) — **NOT a trial candidate** — is unchanged by this reset. The alignment rule applies the day DA's operations verdict moves to trial-capable.

---

## 8. Implementation Plan (after this design signs)

Three implementation PRs + one validation PR. Each is single-purpose, single-branch, independently committed + pushed + reported.

### PR-A · Workbench product-flow cleanup *(LARGE — heart of the reset)*

**Scope** (`gateway/app/templates/task_workbench.html` matrix_script branch + helper output shape only):

- **Retire** the standalone Block A / B / C / D / E / F op-cards from primary view. Their `data-role` markers + content move into a single ARCHITECT-ONLY wrapper inside Section 5 (`<details>` collapsed by default), preserving back-compat for structural tests.
- **Implement** the 4 primary sections from §4 above:
  - Section 1: 主视频结果 (re-use PR-2A `main_video_result_view.py` helper; promote it to the sole first-screen anchor)
  - Section 2: 生产流程可观测 (compact stepper, with inline expandable detail that consumes the helpers behind today's Blocks B / C / D)
  - Section 3: 可选变体 (compact; 1 main + N folded other; empty-state when no media)
  - Section 4: 交付入口 (2-line lightweight; CTA only)
- **Quarantine sweep — structural this time** (not string-level). Rewrite helper output to drop raw axis arrays, replace contract `kind_label_zh` overlays with operator-language baselines, push all engineering identifiers into Section 5 only.

**Forbidden in PR-A** (binding): contract / schema / closed-enum / packet truth / Hot Follow / Digital Anchor / Asset Supply touch; new endpoint; new helper module (re-use the 7 existing matrix_script presenter helpers); provider/model/vendor/engine selector; fake `final_video` / `publish_url`; backend generation.

**Tests**: at least 30 new tests covering 4-section IA presence, Section 5 quarantine, no-forbidden-vocab in Sections 1–4 source, no-fake-URL audit, redundant-block-removal audit.

**Estimated PR size**: large (Workbench template + ~5 helper shape adjustments + ~30 tests).

### PR-B · Delivery Center product-flow cleanup *(medium)*

**Scope** (`gateway/app/templates/task_publish_hub.html` matrix_script branch + 1 helper for the ① introduction paragraph):

- Tighten the PR-3 6-section structure: ensure ① 交付结果介绍 is a real operator-language paragraph (not just a relabelled header). 
- Confirm sections ② → ⑥ render Mission §C content with NO production-flow controls.
- Apply the Section 5-style technical quarantine to publish-hub helpers that still leak `closure` / `publish_url` / `event_kind` etc.

**Forbidden in PR-B**: same standing list; no new endpoint (publish settings + backfill use the existing closure endpoint as PR-3 already does).

**Tests**: ~12 new tests covering section ordering, ① paragraph content, no-generation-controls audit, no-production-flow-panels audit, publish-settings form preserved.

### PR-C · Manual visual validation *(docs-only)*

**Scope**: run real browser screenshots against the integrated PR-A + PR-B build (locally, or via Render preview environment if available). Score against the 12-item checklist below. Target score ≥ 32/35. Write a visual validation report.

If the score falls below 32/35, the report MUST identify the gap concretely (which checklist item, where in the rendered HTML the gap appears, what helper / template fragment owns it). PR-C is a stop-or-go gate: ≥ 32/35 → wave closes; < 32/35 → wave re-opens for a follow-up patch PR.

### Sequencing

- PR-A may open immediately after this design signs.
- PR-B opens only after PR-A merges.
- PR-C opens only after PR-B merges.

---

## 9. Acceptance Criteria

The reset wave (PR-A + PR-B + PR-C) is acceptable **only if** all 12 items below pass on a real browser screenshot of the integrated build.

1. Workbench first screen (no scroll, 1280×900) centers on 主视频结果 as the dominant section.
2. Task metadata (task ID, platform, category, kind, status enum) is NOT the primary visual anchor anywhere in Sections 1–4.
3. Product flow appears only as the compact 脚本结构 → 变体选择 → 生成 stepper (Section 2), collapsed by default. No legacy A/B/C/D/E/F op-cards visible on primary scan.
4. Variants (Section 3) are optional and secondary; empty state when no media is ONE operator-language message, not N empty cards.
5. Workbench Section 4 contains a 2-line summary + CTA only — NO per-row deliverable lists, NO publish form, NO publish-feedback table.
6. Delivery Center owns deliverables and publishing — all per-row deliverable detail, publish-settings form, and publish-feedback backfill live ONLY in Delivery Center.
7. Backend vocabulary is quarantined: a source-level grep against Sections 1–4 rendered HTML returns 0 occurrences of the §5 forbidden list.
8. Technical diagnostics (Section 5) `<details>` is collapsed by default on both Workbench and Delivery Center.
9. No fake video output anywhere — no fabricated URL, no placeholder media player, no synthesized `final_video` reference.
10. No provider / model / vendor / engine selector control on any operator surface (validator R3).
11. The operator can answer the 5 anchor questions (Q1–Q5 from §2.3) by looking at Section 1 + Section 2 collapsed view alone — without scrolling, without opening Section 5.
12. Per-PR product-flow module presence audit (ENGINEERING_RULES §13) — every claimed Section has a `data-role` anchor in the matrix_script branch of `task_workbench.html` / `task_publish_hub.html`.

The PR-4-style baseline score (35/35 self-reported in the prior wave) was achieved by *additive* compliance — every prior item was technically present in source. The reset wave requires *subtractive* compliance — items must be present AND legacy items must be absent from primary view. A claim of "35/35" with the legacy six-block structure still visible is by definition false.

---

## 10. Final verdict

**Design ready for implementation.**

The design plan is self-contained, scoped within standing wave-gate constraints, and proposes a clean per-PR implementation sequence (PR-A → PR-B → PR-C) that can be reviewed and merged independently. No contract / packet / closed-enum / runtime / Hot Follow / Digital Anchor / Asset Supply / backend-generation work is required or implied. The honest target verdict after PR-C closes remains:

> *"UI visually verifiable; backend final-video generation remains pending."*

Matrix Script is NOT production-operable. The reset wave does not change that — it makes the operator surface honestly reflect that fact.

Awaiting product / reviewer / coordinator signoff on this design document before opening PR-A.
