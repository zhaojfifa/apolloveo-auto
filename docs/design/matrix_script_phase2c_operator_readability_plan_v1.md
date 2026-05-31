# Matrix Script · Phase 2C · Operator Readability Plan v1

Date: 2026-05-30
Status: **Planning document only.** No code, no template edits, no presenter edits, no contract / schema / packet / closed-enum / runtime / route change. No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans touch. No `final_video` / `publish_url` / media URL fabrication. No provider / model / vendor / engine controls. No merge to `main`.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2C Planning Archivist).

Predecessor authorities:

- `docs/execution/VEOMATRIXVOICE04_MANUAL_VALIDATION_AND_PHASE2C_INTAKE_v1.md` — CONDITIONAL PASS WITH P1 / P2 ISSUES (no P0; five P1 product-mindset issues; eight P2 readability / copy issues).
- `docs/product/matrix_script_product_flow_v2_delta.md` — v2 framing: Matrix Script = 面向账号矩阵运营的脚本转视频批量生产线.
- `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md` — presenter mapping target.
- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` — contract-layer boundary.
- `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` — Phase 1 mock.

Base branch: `VeoMatrixVoice04` (commit `63bc709`).
Planning branch: `design/ms-phase2c-operator-readability-planning-20260530`.

---

## 1. Scope and hard boundaries

### 1.1 Scope (what Phase 2C is)

Phase 2C is **operator-readability + product-mindset polish only**. Its job is to repair the five P1 product-mindset issues and the eight P2 readability / copy issues recorded in the VeoMatrixVoice04 intake without claiming any new system capability.

Only the following surface areas may be touched by a later Phase 2C implementation PR:

- Operator-visible copy (Chinese-language strings rendered to operators).
- Per-section layout density inside already-existing Workbench sections A–J + Delivery Center sections 1–6 + New Task Cards 1–5.
- Presenter-layer projections that pass already-existing packet / closure / publish_readiness truth to those templates.

### 1.2 Hard boundaries (what Phase 2C is NOT)

Phase 2C **MUST NOT** do any of the following (binding for the future implementation PR as well as for this planning PR):

- No new backend capability, worker, generator, compose service, BGM service, subtitle worker, video worker, B-Roll retrieval, Asset Supply runtime, VoiceTrans bridge, or any other runtime component.
- No new endpoint, no new router, no router edit that changes URL surface.
- No `factory_*` contract / schema / packet / closed-enum mutation.
- No widening of any closed status-code set; existing `data-status-code` anchors remain bytewise stable.
- No new line packet field, no `scene_plan_binding`, no operator preference persistence into truth.
- No fake `final_video` / thumbnail / media URL / `publish_url` / generated media.
- No raw VoiceTrans iframe / embed inside Matrix Script branches.
- No provider / model / vendor / engine controls anywhere in operator-visible copy.
- No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans / generic factory readiness file touched.
- No merge to `main`. Implementation lands on a `fix/ms-script-to-video-phase2c-operator-readability-…` branch and is validated in a separate `VeoMatrixVoice05` joint validation branch before any main consideration.
- **Honest placeholder discipline remains.** `当前占位` chips, `data-status-code` anchors, and `disabled` buttons stay; Phase 2C only changes their density and surrounding copy. No pretend capability.

### 1.3 IA preservation

- Workbench IA stays at exactly 10 sections (A 主视频结果 / B 脚本理解 / C 视频生成计划 / D 画面与素材 / E 角色与声音 / F 字幕与音乐 / G 视频变体 / H 校对与微调 / I 交付入口 / J 技术诊断 collapsed).
- Delivery Center IA stays at exactly 6 numbered sections + the §7 `<details>` fold.
- New Task IA stays at exactly 5 cards (脚本 / 产品 / 素材 / 目标·画幅·语言 / 角色·声音·字幕 / 变体策略).
- V1 / V2 / V3 video-version framing stays; no axis-row regression.

---

## 2. Section-by-section readability plan

The B/C/D/E/F/G readability fixes below are stated as design targets for a later Phase 2C implementation PR. **No file is touched by this planning PR.**

### 2.1 §B 脚本理解 — remove contract / backend vocabulary; use operator language

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Selling-points row (P2-1) | `卖点项尚未由 content_structure 投射；可在 J 节查看占位字段。` | `卖点项接入后会在这里展开。当前阶段以脚本主旨为准。` | Pure copy. No new selling-points field; that needs a generic content-structure contract amendment which is deferred (§7). |
| Platform / length / language echo | Currently scattered | Single line `平台 · 时长 · 语言` summary with dot separators; wording 1:1 with New Task Card 3 | Pure template / presenter rewording. |
| Keywords / forbidden words | Already OK | Keep; empty-state copy `运营在 New Task Card 3 未声明关键词。` when absent | Pure copy. |

### 2.2 §C 视频生成计划 — keep storyboard; rewrite backend / pending language as product-facing draft / replacement language

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Disclaimer (P2-2) | `上述分镜为占位草案；正式方案需由后端方案生成能力产出，当前不声明任何镜头已就绪。` | `当前展示的是占位草案；方案生成能力接入后会替换为真实分镜，每个镜头单独可编辑。` | Drops `后端`. Pure copy. |
| 11-field storyboard table | Already OK | Keep; ensure operator-language column labels (e.g. `script_segment` → `脚本片段`) render; render empty cells as `—` instead of `null` | Pure template. |
| Single-scene edit | Currently read-only | **Not implemented in Phase 2C.** Disclaimer states the future capability; no fake edit affordance is added. | No fake interaction. |

### 2.3 §D 画面与素材 — consolidate repeated pending slots into one upload / material selection panel

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Three identical pending slots (P1-1) | 背景 / B-Roll / 产品素材 three rows each carrying `当前占位` + `data-status-code="broll_pending_upstream"` | **One consolidated upload area + one explanatory line**: `素材匹配能力接入后会在这里出现背景 / B-Roll / 产品素材候选；当前可直接上传素材占位。` Upload reuses the New Task Card 2 path already in `source_asset_references`; presenter-only reuse, no new endpoint. | Upload routes already exist (entry-cards path); no B-Roll worker invocation. |
| Three identical disabled tooltips (P2-3) | Same sentence repeated three times | Differentiate per button: `背景候选接入后开放替换` / `B-Roll 候选接入后开放替换` / `素材匹配能力接入后开放重新生成建议` | Pure copy. |
| `data-status-code="broll_pending_upstream"` anchor | Present | Kept (architect / test consumption preserved) | Closed status-code set untouched. |

### 2.4 §E 角色与声音 — promote role / voice preference selectors; demote voice-preview placeholder

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Four preference selectors (P1-2) | Dominated visually by voice-preview placeholder | Promoted to section top: 角色 / 气质 / 性别 + 语气 / 目标语言 / 语速; horizontal 2-column grid; mirrors New Task Card 4 | Template + presenter projection; no form submit. |
| Voice-preview placeholder (P2-4) | Large placeholder + architect-style disclaimer | Reduced to a small top-right chip `🔊 试听能力接入后开放`; small print rewritten to `语音预览能力接入后会在这里实时试听；当前阶段以偏好选择为准。` | Removes self-disclosing wording (`本节不嵌入 VoiceTrans 页面` etc.). |
| Architect notes about Digital Anchor / role asset | Currently inline | Move into §J fold | Migration only; not deleted. |

### 2.5 §F 字幕与音乐 — make subtitle / music controls carry operator intent

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Subtitle style / position / BGM mood / volume selectors (P1-3) | Static; all carry `当前占位` chip | **Selectable; selection persisted client-side / presenter session only (hidden field acceptable).** Section reads as a choice panel, not a result panel. | Pure presenter; no packet write; no contract change; no backend submission. |
| Chip wording | `当前占位 · subtitle_style_pending_compose` / `bgm_pending_upstream` | Anchors preserved; visible chip text rewritten to operator language (`预览生成后生效` etc.) | `data-status-code` set untouched. |
| Relationship to New Task Card 4 | Currently duplicates Card 4 without saying so | Section-top sentence: `已沿用 New Task 中你选择的 …；可在此处调整。` | Pure copy. |

### 2.6 §G 视频变体 — add 适合哪些账号 / 场景 column; split recommendation / state pills

| Issue | Current | Phase 2C target | Boundary |
|---|---|---|---|
| Card columns (P1-4) | `哪里不同` + `为什么测这一版` only | Add third column `适合哪些账号 / 场景` (operator-language one-liner; default placeholder `主视频生成后会基于指标投射建议适配账号` when no metrics projection exists) | New presenter field `recommended_audience_zh`; no packet / closed-enum change. |
| Status pill (P2-5) | Single `当前占位 · 待生成` pill | **Two pills**: recommendation pill (`推荐` / `备选`) + state pill (`待生成` / `已生成` / `待审核`, default `待生成`) | State pill values **not** added to any closed enum; pure presenter. |
| ⭐ recommendation marker | On V1 only | Keep single marker; recommendation pill on the same row reads from the same source | No change. |

---

## 3. Backend-pending language reduction strategy

Three structural levers, in priority order:

### 3.1 Top-level capability banner

Replace the per-section pending pill density (currently §D + §E + §F + §H each show one or more `当前占位` chips at section top) with a single Workbench-level capability banner above section A:

> 成片生成与素材匹配能力接入后，本工作台标记为"可生成"。当前阶段以方案与偏好为准。

Per-section `当前占位` chips are not deleted; they are **collapsed** into one indicator per section or moved into a hover / fold so the operator's first scroll is dominated by product copy, not status pills.

### 3.2 Forbidden vocabulary list

A small operator-copy forbidden-vocabulary list, enforced by grep tests during the Phase 2C implementation acceptance gate (§8). The following terms MUST NOT appear in operator-visible copy in the Matrix Script branches (they remain permissible inside the §J / §7 architect folds and inside `data-*` anchors):

- `content_structure`
- `后端`
- `compose`
- `producer`
- `bridge`
- `provider`
- `vendor`
- `engine`
- `model`
- Vendor names: `azure`, `akool`, `seedance`, `openai`, `anthropic`, `elevenlabs`, `gemini`

### 3.3 Narrative empty-state wording

Rewrite "待 X 接入" framing into "X 接入后会出现 Y" framing. The operator reads not "what is missing" but "what will appear next". Worked examples:

- `指标投射尚未上线 · 暂不展示数值。` → `指标投射上线后会展示首发完播率 / 点赞 / 评论 / 留资数据。` (P2-7)
- `待主视频生成。` (repeated four times in §H) → one consolidated banner `主视频生成后，按 4 个分区开放校对入口` + compact zone labels (P2-6).
- `素材匹配能力尚未接入。` (repeated three times in §D) → three differentiated tooltips per §2.3 above (P2-3).

---

## 4. D / E / F operator choice-panel mental model

**Workbench D / E / F are screens for expressing operator intent, not windows for waiting on backend results.**

| Section | Mental model | Operator action available today | Operator action deferred |
|---|---|---|---|
| §D 画面与素材 | "Operator uploads or earmarks material the future generation pass will use." | Upload via consolidated single area | Real B-Roll candidate retrieval / Asset Supply browse (Phase 3+) |
| §E 角色与声音 | "Operator expresses role / voice / language / speed preference." | Pick 4 preference selectors | Real voice audition (VoiceTrans bridge — Phase 4) |
| §F 字幕与音乐 | "Operator expresses subtitle / BGM preference; adjusts what was already chosen in New Task Card 4." | Adjust subtitle style / position / BGM mood / volume selectors | Real subtitle compose / BGM mixing (Phase 3+ compose worker) |

When future runtime capability lands, these expressed intents become inputs to the generation pass without UI rework.

---

## 5. Video-version enhancement — stable three-question model

After Phase 2C lands, each V1 / V2 / V3 card answers exactly three operator questions:

| Question | Source field | Default wording when source absent |
|---|---|---|
| 哪里不同 | `differentiator_zh` (existing) | (already shipped) |
| 为什么测这一版 | `why_test_zh` (existing) | (already shipped) |
| 适合哪些账号 / 场景 | `recommended_audience_zh` (new presenter field; Phase 2C) | `主视频生成后会基于指标投射建议适配账号` |

Combined with the two-pill split (recommended / 备选 + state), the operator's scan path on §G becomes:

```
which versions exist → which is recommended → what each is suited for → what state each is in
```

instead of four visually identical placeholder cards.

---

## 6. Implementation scope candidate list

The following files **may** be touched by a future Phase 2C implementation PR. **This planning PR does NOT touch them.**

| Candidate file | Expected change kind | Driven by |
|---|---|---|
| `gateway/app/templates/task_workbench.html` (matrix_script branch only) | Copy + localized layout (§D consolidation, §E selector promotion, §F selectable controls, §G third column + dual pill, top-level capability banner) | P1-1 / P1-2 / P1-3 / P1-4 / P1-5 / P2-1 / P2-2 / P2-3 / P2-4 / P2-5 / P2-6 |
| `gateway/app/templates/task_publish_hub.html` (matrix_script §6 metrics card) | Copy rewrite | P2-7 |
| `gateway/app/templates/matrix_script_new.html` (Card 4 options) | Option-label usage hints | P2-8 |
| `gateway/app/services/matrix_script/*` (presenter helper modules only) | Add `recommended_audience_zh` default value; §E selector projection; §F preference echo projection — **presenter layer only, not packet** | P1-2 / P1-3 / P1-4 |
| `gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py` (and adjacent scoped tests) | Extend: forbidden-vocabulary grep; new chip / pill assertions; `recommended_audience_zh` default placeholder assertion; §D single upload-area assertion; §E selector-order assertion | All P1 / P2 |

**Explicitly out of scope (future implementation PR may not touch):** any `gateway/app/services/hot_follow*`, `gateway/app/services/digital_anchor*`, `gateway/app/services/asset*`, `gateway/app/services/voice_tool*`, `gateway/app/routers/*`, `gateway/app/main.py`, any `docs/contracts/`, any `schemas/`, any `samples/`.

---

## 7. Deferred Phase 3+ list (binding non-scope for Phase 2C)

The following items are explicitly **NOT** in Phase 2C and remain gated to Phase 3 or later wave authorities:

- `scene_plan_binding` line-packet additive binding / single-scene edit.
- Real B-Roll retrieval / Asset Supply runtime / Asset Library bridge.
- VoiceTrans bridge (Phase 4 contract bridge; never raw embed).
- Subtitle / BGM compose worker.
- Backend video generation worker (`生成主视频` / `重新生成` / `接受为主版本` real triggers).
- Publish metrics-based recommendation projection (`recommended_audience_zh` real-data computation).
- Real review-zone activation in §H (requires actual primary video result).
- Packet persistence of new §E / §F operator preferences into line-packet truth.
- Delivery Center §2 real primary-video download / §5 real publish submit.
- Any closed enum addition (e.g. new `data-status-code`).

---

## 8. Acceptance gates for future Phase 2C implementation

A future Phase 2C implementation PR closes only when all of the following gates hold:

1. **Forbidden vocabulary grep**: `content_structure` / `后端` / `compose` / `producer` / `provider` / `vendor` / `engine` / `model` / `azure` / `akool` / `seedance` count = 0 in operator-visible Matrix Script branches (§J fold + `data-*` anchors permitted).
2. **§D single upload area**: one consolidated upload area + one explanatory line; repeated pending slot count = 0.
3. **§E selector order**: the four preference selectors render **above** the voice-preview placeholder in DOM order.
4. **§F selectable controls**: the four subtitle / BGM controls are `<select>` / `<input>` (or equivalent interactive elements), not static text.
5. **§G V1 / V2 / V3 fields and pill structure**: each card carries exactly one `differentiator_zh` + one `why_test_zh` + one `recommended_audience_zh` + two pills (recommendation pill + state pill).
6. **Capability banner density**: the top-level capability banner appears exactly once; per-section `当前占位` chip count in §D / §E / §F / §H drops from ≥ 4 to ≤ 1.
7. **New Task Card 4 usage hints**: the three role / voice / 语气 option labels include `（推荐：…）` suffixes per P2-8.
8. **Delivery §6 future-metrics wording**: rewritten per §3.3 with the narrative form (`首发完播率 / 点赞 / 评论 / 留资`).
9. **Zero contract / schema / packet / runtime / worker changes**: `git diff --stat` shows zero changes under `docs/contracts/`, `schemas/`, `samples/`, `gateway/app/routers/`, `gateway/app/main.py`, `gateway/app/services/hot_follow*`, `gateway/app/services/digital_anchor*`, `gateway/app/services/asset*`, `gateway/app/services/voice_tool*`.
10. **Scoped test pass**: existing 143-test Matrix Script suite passes; new forbidden-vocabulary + structural assertions pass.
11. **No `main` merge**: implementation lands on a `fix/ms-script-to-video-phase2c-operator-readability-…` branch and is validated through a fresh `VeoMatrixVoice05` joint validation branch before any further consideration.
12. **No surface regression**: Hot Follow / Digital Anchor / Asset Supply / VoiceTrans pages render bytewise unchanged; smoke check confirms.

---

## 9. Final boundary statement

This document authorizes **planning only**.

Implementation of Phase 2C requires a separate裁决. Specifically:

- A separate user hand-off must explicitly open the Phase 2C implementation branch (`fix/ms-script-to-video-phase2c-operator-readability-…`).
- No template, presenter, or test file may be edited under the authority of this document.
- No backend capability or runtime change may be invoked under the authority of this document.
- No `main` merge of either this planning document or any subsequent implementation PR may proceed without explicit, separate裁决.

Until that separate裁决 lands, the Phase 2C scope remains documented and frozen at this plan; the Matrix Script line continues to operate at the VeoMatrixVoice04 baseline (CONDITIONAL PASS WITH P1 / P2 ISSUES).
