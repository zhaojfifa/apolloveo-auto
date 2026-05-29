# Matrix Script · Phase 2C Operator Readability Validation · Report v1

Date: 2026-05-30
Status: **Validation-only report. No code, no template, no runtime, no contract, no worker, no fake-media change.** No Phase 3. No VeoMatrixVoice05 created by this report.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2C Manual Readability Validator).

---

## 1. Subject under validation

| Item | Value |
|---|---|
| Branch | `fix/ms-script-to-video-phase2c-operator-readability-20260530` |
| Commit | `e09ad6f` (`fix(matrix-script): improve phase2c operator readability`) |
| Base | `de38192` (planning archive) |
| Validation surfaces | New Task page · Workbench · Delivery Center · VoiceTrans route smoke |

---

## 2. Validation method & limitation (READ FIRST)

**Live browser screenshots were NOT available in this environment.** Two independent blockers were confirmed:

1. The runtime app cannot be imported under the available Python 3.9.6 interpreter: `gateway/app/config.py` uses PEP-604 `str | None` annotations at class scope, which raise `TypeError: unsupported operand type(s) for |` on 3.9 (no `from __future__ import annotations` in that module). This is a pre-existing environment/runtime characteristic, **not** introduced by Phase 2C.
2. The available Python 3.11.15 interpreter does not have the app dependency set installed (`jinja2`, etc.), so it cannot render the templates either.

A `TestClient`-based render harness was prepared (modeled on `test_matrix_script_workbench_dispatch.py::_post_fresh_sample`) to produce real rendered HTML snapshots, but it could not execute for the reasons above. **No rendered HTML snapshot or PNG artifact was produced.**

**Method actually used:** source-level audit of the committed templates plus the automated structural test suite. Every checklist line below is backed by a concrete file:line grep against commit `e09ad6f`, and by the 242-passing Matrix-Script-scoped test suite (including the 20-assertion Phase 2C readability test). This is the strongest evidence obtainable in this environment; the operator-perceived "first impression" items (B) are inferred from DOM order + copy, not from a pixel render.

### 2.1 Render artifacts

| Artifact | Path | Status |
|---|---|---|
| New Task rendered HTML | (intended) `/tmp/ms_phase2c_snapshots/01_new_task.html` | NOT PRODUCED — env blocked |
| Workbench rendered HTML | (intended) `/tmp/ms_phase2c_snapshots/02_workbench.html` | NOT PRODUCED — env blocked |
| Delivery Center rendered HTML | (intended) `/tmp/ms_phase2c_snapshots/03_delivery.html` | NOT PRODUCED — env blocked |
| Source audit (this report) | grep/read against `e09ad6f` | ✅ complete |
| Automated structural suite | `pytest` (242 passed) | ✅ complete |

---

## 3. Checklist results

Legend: ✅ verified by source audit + tests · ⚠️ verified by source only (no live render) · ❌ fail.

### A. New Task page

| Check | Result | Evidence |
|---|---|---|
| Five-card structure (脚本来源 / 产品·素材 / 目标·画幅·语言 / 角色·声音·字幕 / 变体策略) | ✅ | anchors `ms-new-card-source`(230), `-product-material`(400), `-target-aspect-language`(445), `-role-voice-subtitle`(514), `-variant-strategy`(564); titles match |
| Card 4 option labels carry usage hints (推荐：…) | ✅ | lines 528–530, 537–538, 547 (`推荐：纯 B-Roll + 字幕` / `讲解型短视频` / `本地化投放` / `生活种草` / `测评说明` / `短视频首屏`) |
| No provider/model/vendor/engine controls | ✅ | zero `<select|input name="(provider|model|vendor|engine)">` |
| No VoiceTrans iframe / raw embed | ✅ | `<iframe>` count = 0; no `action="…voice…"`; future-provider note reworded, anchor preserved |
| CTA remains 生成视频方案 | ✅ | `ms-new-submit` (604) → `生成视频方案 →` |

### B. Workbench first impression

| Check | Result | Evidence |
|---|---|---|
| Reads as script-to-video workspace, not backend/status page | ⚠️ | DOM order + copy support this; no live render |
| Top-level capability banner visible once, explains capability state | ✅ | `matrix-script-capability-banner` count = 1 (line 295), body explains generation/material steps open as capability lands |
| 主视频结果 remains first meaningful operator section | ✅ | order: banner(295) → `matrix-script-main-video-result`(326) → B(445) … |
| Task metadata/status does not dominate | ⚠️ | legacy A–F blocks relocated into §J fold (line 1098+); first scan is banner+主视频; not pixel-confirmed |

### C. §B 脚本理解

| Check | Result | Evidence |
|---|---|---|
| Operator labels 目标受众 / 语气 / 时长 / 卖点 / 关键词 / 禁用词 appear | ✅ | static labels 卖点(449)/目标受众/语气/时长 added; 关键词·禁用词 rendered by `ms-section-script-understanding-taxonomy` loop + named in subtitle (454) |
| No primary `content_structure` / `audience=[` / `tone=[` / `length=[` / provider/vendor/engine/model | ✅ | none in primary slice (273–1097); the only `audience=[…]`/`tone=[…]` occurrences are inside the §J fold documentation `{# … #}` comment (~1090) |

### D. §C 视频生成计划

| Check | Result | Evidence |
|---|---|---|
| 11 storyboard fields remain visible | ✅ | scene fields: number/script-segment/visual-intent/background-suggestion/broll-suggestion/product-material-slot/role/voiceover/subtitle/music-mood/aspect-ratio (= 11) |
| Wording reads 占位草案 / 可替换 / 待选择, not backend diagnostics | ✅ | pill `占位草案`(525); subtitle "分镜草案…会替换为可逐镜编辑的真实分镜"; disclaimer de-`后端`'d, honesty kept |
| No fake edit controls | ✅ | fields are read-only spans; no enabled edit inputs |
| No fake generated scene truth | ✅ | rows carry `data-status-code="plan_pending_upstream"`; "当前未声明任何镜头已就绪" |

### E. §D 画面与素材

| Check | Result | Evidence |
|---|---|---|
| Repeated pending slots consolidated | ✅ | one `ms-section-visual-materials-intent-panel`(line ~634); three legacy slots demoted into `…-slots-fold` `<details>` |
| Reads as material-intent / selection panel | ⚠️ | 素材意图 panel copy supports this; no live render |
| Background / B-Roll / product-material intent understandable | ✅ | slot anchors preserved (bg/broll/product); panel copy describes each |
| No upload endpoint / real file POST implied | ✅ | zero `type="file"` / `<form>` / `enctype` in §D; buttons disabled with differentiated tooltips |

### F. §E 角色与声音

| Check | Result | Evidence |
|---|---|---|
| Role and voice choices visually primary | ⚠️ | choice meta-items precede preview; no live render |
| Voice-preview placeholder demoted to small chip | ✅ | `ms-section-role-voice-preview-label` → chip `🔊 试听能力接入后开放` |
| No VoiceTrans bridge/iframe/raw form in primary UI | ✅ | §E (687–733): `<iframe>`/`<form>` = 0; no `VoiceTrans`/`供应方`/`桥接` in primary visible §E text |
| No architect-style disclosure dominates | ✅ | no-iframe note reworded to operator language |

### G. §F 字幕与音乐

| Check | Result | Evidence |
|---|---|---|
| Subtitle / BGM controls read as operator preferences | ✅ | 4 `<select>` (font/position/bgm-mood/bgm-volume) at 756/765/774/784 |
| No new submitted fields | ✅ | zero `<select name=…>` in entire workbench |
| No fake persistence | ✅ | UI-only selects; no route POST / packet / storage write |
| "预览生成后生效" understandable | ✅ | `ms-section-subtitle-music-preview-chip` present |

### H. §G 视频变体

| Check | Result | Evidence |
|---|---|---|
| V1/V2/V3 cards remain | ✅ | 3 `…-card-headline` |
| Each shows 哪里不同 / 为什么测这一版 / 适合哪些账号·场景 / 推荐·备选 / 待生成 | ✅ | differentiator×3, why-test×3, audience×3, recommended-marker×1 (V1), alt-marker×2 (V2/V3), status×3 all `待生成` |
| Reads as video-version testing, not config rows | ⚠️ | card framing + subtitle support this; no live render |

### I. Delivery Center

| Check | Result | Evidence |
|---|---|---|
| Remains final-video oriented | ✅ | §2 主视频 card with preview/empty-state; publish gated by `ms_pub_readiness.publishable`(328) |
| Metrics placeholder explains future metrics (完播率/点赞/评论/留资) | ✅ | `ms-dc-section-publish-backfill-metrics-placeholder`(634) rewritten with all four |
| No fake metrics | ✅ | placeholder is descriptive future copy, no numeric values |
| Publish/download gated when no final_video | ✅ | empty-state when no recommended variation; `ms-dc-section-main-video-no-fake-note` "只有真实写入的成片才会出现下载入口" |

### J. VoiceTrans

| Check | Result | Evidence |
|---|---|---|
| /voice-tool still loads | ⚠️ | route registered `voice_tool.py:76 GET /voice-tool` → `voice_tool.html`; live GET not executable (env); no source change to this route in Phase 2C |
| No Matrix Script page embeds VoiceTrans raw UI | ✅ | `<iframe>` = 0 across `task_workbench.html` / `matrix_script_new.html` / `task_publish_hub.html` |

---

## 4. Issue list

### P0 (blocking) — NONE
- No route-unavailable defect attributable to Phase 2C, no page crash in changed templates, no fake media/publish URL introduced, VoiceTrans route present and untouched, no contract/runtime/worker change (diff allowlist clean), no Hot Follow / Digital Anchor regression (those templates untouched by the diff).

### P1 (readability defects) — NONE
- Workbench first-scan order is banner → 主视频结果 → B…J; §D/§E/§F read as operator choice panels; §G reads as video-version testing; next action is surfaced by the main-video banner + delivery entry. No P1 found at source level.

### P2 (polish / coverage)
- **P2-1 (validation coverage):** No live browser / rendered-HTML artifact could be produced in this environment (Python 3.9 cannot import the app due to pre-existing `config.py` PEP-604 annotations; Python 3.11 lacks installed deps). Items B / E-primary-ordering / G-feel / J-route-load are verified by source + DOM order only, not by pixels. Recommend a one-time live operator render smoke once an app-capable interpreter is available — this is a coverage caveat, not a defect in Phase 2C.
- **P2-2 (§B labels):** 关键词 / 禁用词 appear as labels only when the `taxonomy` projection has values (rendered by the `ms-section-script-understanding-taxonomy` loop); on an empty taxonomy they are named in the subtitle but not shown as standalone rows. Acceptable (honest), but a future presenter could surface them as explicit empty-state rows for symmetry with 目标受众/语气/时长.
- **P2-3 (density):** §C still renders 11 fields × 3 scenes; dense on a narrow viewport. Not a regression (pre-existing), but worth a future density pass.

---

## 5. Explicit no-change statement

This validation produced **no** code, template, presenter, contract, schema, packet, closed-enum, runtime, worker, router, endpoint, or sample change. No `final_video`, thumbnail, media URL, `publish_url`, generated media, metric, or publish-success value was faked or introduced. No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime or generic factory-readiness file was touched. The diff `de38192..e09ad6f` contains only: 3 Matrix-Script templates, 1 Matrix-Script-scoped test, 1 execution report (`git diff --name-only` confirmed zero out-of-scope paths). No VeoMatrixVoice05 was created. No Phase 3 work was started.

---

## 6. Final verdict

**CONDITIONAL PASS WITH P2 ISSUES.**

Phase 2C at commit `e09ad6f` measurably improves Matrix Script Workbench operator readability across all required surfaces at the source/DOM level, with zero P0 and zero P1 issues and a clean diff allowlist. The single material caveat is validation **coverage**, not implementation quality: live browser / rendered-HTML evidence was not obtainable in this environment.

---

## 7. Recommendation

**Proceed to create VeoMatrixVoice05** on this basis, with the following non-blocking conditions:

1. Capture a one-time live operator render smoke of the three surfaces (New Task / Workbench / Delivery Center) on an app-capable interpreter, attaching screenshots, to close P2-1. This can run in parallel with VeoMatrixVoice05 scoping and does not gate it.
2. Track P2-2 / P2-3 as future copy/presenter polish; neither blocks promotion.

Creating VeoMatrixVoice05, fixing P2 items, and starting Phase 3 each require a separate explicit裁决. This report performs none of them.
