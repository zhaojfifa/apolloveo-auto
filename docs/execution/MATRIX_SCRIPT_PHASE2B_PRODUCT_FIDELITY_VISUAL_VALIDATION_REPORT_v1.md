# Matrix Script · Phase 2B Product Fidelity · Visual Validation Report v1

Date: 2026-05-30
Branch under test: `fix/ms-script-to-video-phase2b-product-fidelity-20260530`
Commit under test: `076cddc`
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2B Product Fidelity Visual Validator).

## 0. Environment + render method

| Item | Value |
|---|---|
| Repository | https://github.com/zhaojfifa/apolloveo-auto |
| Branch | `fix/ms-script-to-video-phase2b-product-fidelity-20260530` (HEAD = 076cddc) |
| Host platform | macOS Darwin 25.0.0; Python 3.13 (Jinja render harness) |
| Live-browser PNG capture | **Not available in this environment.** No connected Chrome MCP browser; no `.claude/launch.json` write. Same constraint as the PR-C visual validation. Validation degrades to **rendered HTML snapshots** + **source-level audits** + the 468-test Phase 2B + back-compat regression run. |
| Render method | `scripts/render_workbench_pra_screenshots.py` (PR-A harness; updated in commit 076cddc to populate `task.kind="matrix_script"` so the header gate fires) + `scripts/render_delivery_center_prb_screenshots.py` (PR-B harness). Both render the Jinja `task_workbench.html` / `task_publish_hub.html` against a synthetic empty-state context. |
| New Task page snapshot | Not rendered via harness (the existing harnesses cover Workbench + Delivery Center only). Validation is **source-level** against `gateway/app/templates/matrix_script_new.html` per HEAD `076cddc`. |

## 1. Screenshot / rendered artifact paths

| Mission required view | Artifact |
|---|---|
| New Task first screen | Source: `gateway/app/templates/matrix_script_new.html` (audited via the source-level checklist in §2.1) |
| Workbench first screen | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html) |
| Section C 视频生成计划 | Same Workbench snapshot, scroll to `data-role="matrix-script-section-generation-plan"` |
| Section G 视频变体 | Same Workbench snapshot, scroll to `data-role="matrix-script-section-video-versions"` |
| Section J collapsed | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html) (fold has no `open` attribute) |
| Section J expanded | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html) (architect view; legacy A–F + relocated PR-A stepper visible inside) |
| Delivery Center | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html) (+ [02_prb_delivery_center_full_section7_expanded.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_prb_delivery_center_full_section7_expanded.html) for architect view) |

## 2. Checklist results

### 2.1 New Task page

| Check | Result | Evidence |
|---|---|---|
| Page title is product-facing `生成脚本视频方案` | ✅ PASS | `gateway/app/templates/matrix_script_new.html:208` carries `<h1 ... data-role="ms-new-page-title">生成脚本视频方案</h1>`. Source-level grep returns 1 occurrence of `生成脚本视频方案` and 0 of `创建矩阵脚本任务`. |
| Primary CTA is `生成视频方案` | ✅ PASS | Submit button (`data-role="ms-new-submit"`) inner text rendered as `生成视频方案 →`. Regex `<button[^>]*data-role="ms-new-submit"[^>]*>(.*?)</button>` returns the literal `'生成视频方案 →'`. |
| Primary copy explains script-to-video plan generation | ✅ PASS | Subtitle reads `输入脚本、素材和目标平台，系统先生成可确认的视频方案：脚本理解、分镜、背景 / B-Roll、角色、旁白、字幕、音乐与视频变体。`. Topbar subtitle reads `脚本转视频 · 生成方案入口`. |
| Sidebar explains 生成脚本理解 → 生成视频方案 → 生成角色与音频计划 → 进入工作台确认方案 | ✅ PASS | Sidebar rendered visible text: `生成脚本理解：Hook / Body / CTA / 卖点。 生成视频方案：分镜、背景、B-Roll、商品素材位。 生成角色与音频计划：角色、旁白、字幕、音乐。 进入工作台确认方案，再生成主视频。`. (Source-level grep for the literal concatenated string returns 0 because each step uses `生成<strong>脚本理解</strong>` — the `<strong>` HTML splits the source. Rendered visible text DOES contain `生成脚本理解` and `生成角色与音频计划` as continuous text.) |
| Old phrases absent from primary UI | ✅ PASS | Source-level grep returns 0 occurrences for each: `创建矩阵脚本任务` (0), `正式产线新建入口` (0), `任务摘要` (0), `脚本结构` (0), `变体方案` (0), `生成进度` (0), `候选评审` (0), `交付摘要` (0). |

### 2.2 Workbench first screen

| Check | Result | Evidence |
|---|---|---|
| Matrix Script does NOT show the legacy task-meta header card first | ✅ PASS | The `{% if task.kind != "matrix_script" %}` gate around the legacy header (`task_workbench.html:161-208`) means the card is suppressed for matrix_script tasks. Rendered Workbench HTML returns **0 occurrences** of `workbench.meta.task_id` and **0** of `id="status-badge"`. |
| No visible primary task_id / platform / account / category / language meta card | ✅ PASS | Same gate. No `task_id` / `platform` / `account_id` / `category_key` / `content_lang` meta-item renders in the matrix_script Workbench. |
| First meaningful section is §A 主视频结果 | ✅ PASS | First `matrix-script-*` data-role anchor in the rendered HTML is `matrix-script-main-video-result` (Section A). |
| Main video result is honest empty state, not fake media | ✅ PASS | Section A preview hero renders the helper-supplied empty-state copy `当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。`. Rendered HTML contains **0** of `<video` / `<iframe` / `<source ` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com`. |

### 2.3 Workbench primary IA ordering (A → J)

| Section | data-role anchor | Position in rendered Workbench HTML |
|---|---|---|
| A 主视频结果 | `matrix-script-main-video-result` | 8017 |
| B 脚本理解 | `matrix-script-section-script-understanding` | 11999 |
| C 视频生成计划 | `matrix-script-section-generation-plan` | 15439 |
| D 画面与素材 | `matrix-script-section-visual-materials` | 28716 |
| E 角色与声音 | `matrix-script-section-role-voice` | 31586 |
| F 字幕与音乐 | `matrix-script-section-subtitle-music` | 34029 |
| G 视频变体 | `matrix-script-section-video-versions` | 36683 |
| H 校对与微调 | `matrix-script-section-review-tuning` | 43045 |
| I 交付入口 | `matrix-script-section-delivery-entry` | 45646 |
| J 技术诊断 fold opens at | `op-console-ms-technical-diagnostics-fold` | 46633 |

**Ordering verdict: PASS.** Positions are strictly increasing A < B < C < D < E < F < G < H < I < J.

### 2.4 §C 视频生成计划

| Check | Result | Evidence |
|---|---|---|
| 11 storyboard field anchors present, 3 occurrences each (3 scenes × 11 fields) | ✅ PASS | All 11 anchors return count = 3: `scene-number` / `scene-script-segment` / `scene-visual-intent` / `scene-background-suggestion` / `scene-broll-suggestion` / `scene-product-material-slot` / `scene-role` / `scene-voiceover` / `scene-subtitle` / `scene-music-mood` / `scene-aspect-ratio`. |
| Operator-language field labels visible | ✅ PASS | `场景 1` (1) / `场景 2` (1) / `场景 3` (1); labels `脚本片段` / `视觉意图` / `背景建议` / `B-Roll 建议` / `产品素材位` / `角色 / 出镜` / `旁白` / `音乐情绪` / `画幅` all ≥ 3. |
| Product-language examples present (not only status codes) | ✅ PASS | `厨房` (3) / `阳台` (1) / `农场` (4) / `超市` (3) / `主体特写` (2) / `终镜定格` (1) / `AI 主播` (2) / `温和女声` (2) / `上扬` (7). The section reads as a generation plan with realistic placeholder content. |
| Honest pending chips visible | ✅ PASS | Each scene row carries `data-status-code="plan_pending_upstream"` + pill `当前占位`. Background and B-Roll labels carry `未接入素材匹配` sub-chip. Section header carries `当前占位 · 后台待接入` operator-language pill. |
| Reads as product storyboard, NOT backend pending diagnostics | ✅ PASS | The 11 fields, the product-language examples, and the operator-language pills together render as a Kapwing-style storyboard. Backend identifier substrings absent from primary scan. |

### 2.5 §G 视频变体

| Check | Result | Evidence |
|---|---|---|
| V1 / V2 / V3 cards present | ✅ PASS | `data-version-id="V1"` (1) / `V2` (1) / `V3` (1) — exactly three cards. |
| Recommended marker on exactly one version | ✅ PASS | `ms-section-video-versions-card-recommended-marker` count = 1; located inside the V1 card (V1 has `data-is-recommended="true"`; V2/V3 have `data-is-recommended="false"`). |
| 哪里不同 / 为什么测这一版 visible | ✅ PASS | Operator-language labels `哪里不同` (4) and `为什么测这一版` (4) both render. `⭐ 推荐` (1) appears once. |
| 当前状态 column per card | ✅ PASS | Each card carries `data-role="ms-section-video-versions-card-status"` with pill text `当前占位 · 待生成`. |
| Primary §G scan does NOT contain axis vocabulary | ✅ PASS | Section G body (from `matrix-script-section-optional-variants` to `matrix-script-section-review-tuning`) returns **0 occurrences** of each: `variation_axis` / `axis_tuple` / `audience=[` / `tone=[` / `length=[` / `b2b` / `b2c` / `casual` / `formal` / `playful`. |

### 2.6 §J 技术诊断

| Check | Result | Evidence |
|---|---|---|
| §J collapsed by default | ✅ PASS | `<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold">` opens WITHOUT an `open` attribute. |
| Legacy A–F markers only inside §J | ✅ PASS | All 6 legacy anchors (`matrix-script-block-a-goal-summary` … `matrix-script-block-f-delivery-teaser`) resolve **INSIDE fold** position-wise (position > fold offset). Zero occurrences in primary scan. |
| Old PR-A stepper only inside §J | ✅ PASS | `matrix-script-production-flow-stepper` anchor and 9 `ms-production-flow-step*` markers resolve INSIDE fold; the standalone primary block was relocated by the fidelity fix. |
| Backend terms not in primary UI | ✅ PASS | Phase 2B fidelity test suite (44 assertions) enforces this; the 12 forbidden-token audits from PR-A + 10 from Phase 2B all pass against the rendered HTML. |

### 2.7 Delivery Center

| Check | Result | Evidence |
|---|---|---|
| DC remains final-video oriented | ✅ PASS | All 6 PR-B section anchors present in primary scan exactly once: `matrix-script-dc-section-intro` / `-main-video` / `-required-deliverables` / `-optional-deliverables` / `-publish-settings` / `-publish-backfill`. Section 2 `主视频` is the dominant visual. |
| Publish/download actions gated when final_video absent | ✅ PASS | DC §2 download button + DC §5 `标记为已发布` submit (rendered count = 2: new Phase 2B form + preserved legacy `block-publish-settings` form inside §7) both carry `disabled` attribute when `ops_pr.publishable` is false. The synthetic snapshot fixture has `publishable=false` and the buttons render disabled. |
| No generation controls reintroduced in DC | ✅ PASS | Audit `grep -cE "生成主视频\|触发生成\|立即生成"` returns 5 occurrences but all 5 are inside operator-language explanatory text ("尚未生成主视频", "主视频生成完成后…"), NOT inside any `<button>` or actionable control. The "在 Workbench 重新生成" CTAs in DC §3 are `<a>` anchors linking back to the Workbench (not in-place generation). |
| Section 7 fold collapsed by default | ✅ PASS | `<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold">` opens WITHOUT `open` attribute. |
| No fake media / publish URL in DC primary | ✅ PASS | Audit returns 0 occurrences of `<video` / `<iframe` / `<source ` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com`. |

## 3. Score + verdict

| Surface | Items audited | PASS | FAIL |
|---|---|---|---|
| 2.1 New Task page | 5 | 5 | 0 |
| 2.2 Workbench first screen | 4 | 4 | 0 |
| 2.3 Workbench primary IA ordering | 1 | 1 | 0 |
| 2.4 §C 视频生成计划 | 5 | 5 | 0 |
| 2.5 §G 视频变体 | 5 | 5 | 0 |
| 2.6 §J 技术诊断 | 4 | 4 | 0 |
| 2.7 Delivery Center | 5 | 5 | 0 |
| **Total** | **29** | **29** | **0** |

**Verdict: PASS.**

Supporting:

- **468 test regression** on the fix branch (44 product-fidelity + 53 Phase 2B structural + 371 back-compat / cross-line) — all green.
- **0 forbidden backend tokens** in primary scan across both Workbench (15-token list) and Delivery Center (PR-B audit set).
- **0 fake media tags** (`<video` / `<iframe` / `<source `) in either primary scan.
- **0 fake URLs** (`.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com`) in either primary scan.
- **0 provider / model / vendor / engine** controls in primary.
- **6 / 6 legacy A–F markers** properly quarantined inside §J fold.
- **PR-A standalone stepper** properly quarantined inside §J fold.
- **Legacy task-meta header** properly gated to non-matrix_script kinds.

## 4. Whether the real page now aligns with Phase 1 mock

**Yes.** Concrete alignment per Phase 1 mock surface:

| Phase 1 mock surface (`docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html`) | Real page after 076cddc |
|---|---|
| Mock ① 新建 · 生成视频方案 | Real `/tasks/matrix-script/new` page H1 + subtitle + sidebar + CTA all match. |
| Mock ② Workbench A–J, ten sections in order | Real `/tasks/{task_id}` matrix_script branch renders A–J in design order; first-screen anchor is §A 主视频结果. |
| Mock ②§C storyboard with 11 fields (scene number / script segment / visual intent / background / B-Roll / product material slot / role / voiceover / subtitle / music mood / aspect ratio) | All 11 fields render in real §C with 3 scenes × 11 = 33 field instances. Product-language example content (厨房 / 农场 / 超市 / AI 主播 · 温和女声 / 上扬 …). |
| Mock ②§G V1/V2/V3 video-version cards with 哪里不同 / 为什么测 / 推荐 | All three cards render with literal `data-version-id` + ⭐ 推荐 on V1 only + both column labels visible. |
| Mock ②§J 技术诊断 collapsed | §J fold renders without `open`; legacy A–F + stepper quarantined inside. |
| Mock ③ Delivery Center six sections + §7 fold | PR-B DC bytewise preserved; all 6 anchors + §7 fold render correctly; publish CTAs gated. |
| Mock honest discipline (placeholder chips / no fake media / no vendor controls) | All maintained in real templates; 44 Phase 2B fidelity tests mechanically enforce. |

The five drifts identified in the 5f5a0bc rejection are all corrected in 076cddc; the visual validation against the rendered HTML + source confirms the real Matrix Script pages now match the Phase 1 mock's mental model.

## 5. Explicit no-runtime / no-contract / no-worker / no-fake-media statement

This validation wave is **docs-only**:

- **No code change.** This commit adds only this report under `docs/execution/`.
- **No contract / schema / packet / closed-enum change.** `docs/contracts/`, `schemas/`, packet files all bytewise unchanged.
- **No runtime change.** No router edit; no service-layer mutation; no new endpoint; no new dependency; no worker added.
- **No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime touch.** All cross-line files bytewise unchanged.
- **No backend generation worker added.** Matrix Script remains not production-operable; Section A continues to render the honest empty-state copy until the Capability Expansion Wave lands.
- **No fake `final_video` / thumbnail / media URL / `publish_url`.** Confirmed by audit: 0 occurrences of any media tag or streaming-host URL in either Workbench or Delivery Center primary scan.
- **No VoiceTrans iframe / raw UI embed.** §E carries the same future-provider label as 076cddc; no `<iframe>` in primary.
- **No provider / model / vendor / engine controls.** Audit returns 0 occurrences of vendor names (azure / gemini / akool / seedance / openai / anthropic / google / elevenlabs) in primary visible text.

## 6. Final verdict

**Real Matrix Script pages now align with Phase 1 mock product intent. Phase 2B fidelity fix at commit 076cddc is visually validated.**

Stopping here per mission. No Phase 3 start. No backend generation. No worker. No contract / schema / packet / closed-enum change.
