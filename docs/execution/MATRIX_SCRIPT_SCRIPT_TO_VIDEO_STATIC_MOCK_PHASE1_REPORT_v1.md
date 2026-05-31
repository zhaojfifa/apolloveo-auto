# Matrix Script · Script-to-Video · Phase 1 Static Mock Implementation Report v1

Date: 2026-05-29
Branch: `design/ms-script-to-video-static-mock-phase1-20260529`
Base: `design/ms-kapwing-benchmark-product-advice-20260529` (commit e03764e — accepted product advice)
Wave: Matrix Script · Product-Flow Reset · Phase 1 (Static Clickable Mock)
Authority: [docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md](../design/matrix_script_kapwing_benchmark_product_advice_v1.md) §6 / §7 / §8 / §9 / §14 Phase 1; user mission `[SYSTEM OVERRIDE]` 2026-05-29 (Script-to-Video Static Mock Designer brief).

## 0. What this PR delivers

A single self-contained static HTML mock (no FastAPI route, no template includes, no XHR) that demonstrates the **script-to-video** product target accepted in the Kapwing-benchmark advice document. The mock is a clickable three-tab artifact (① 新建 → ② 工作台 → ③ 交付中心) using the sample script "美女十分开心地吃西红柿，说，西红柿亚克西。" to populate every section with realistic placeholder content.

Files added:

| File | Purpose |
|---|---|
| [docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html](../design/previews/matrix_script_script_to_video_workbench_v1/index.html) | The static clickable mock — 827 lines, all inline CSS + minimal vanilla-JS tab switcher. No network, no runtime, no embedded media. |
| [docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md](MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md) | This report. |

No FastAPI route was added. The mission allows either route or static artifact; static artifact was chosen because adding a route would touch `gateway/app/main.py` (runtime) which the mission forbids.

## 1. Branch + commit

- **Branch:** `design/ms-script-to-video-static-mock-phase1-20260529`
- **Base:** `design/ms-kapwing-benchmark-product-advice-20260529` (e03764e)
- **HEAD:** to be reported on push.
- **Push:** to be reported.
- **Open PR URL:** to be reported on push.

## 2. Files changed

```
docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html   | +827  (new — static mock)
docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md | +~280 (new — this report)
                                                                       2 files added
```

Zero changes to `gateway/`, `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow, Digital Anchor, Asset Supply, generation workers, or any existing template.

## 3. Preview URL / static path

The mock is a static HTML file that runs offline:

- **Repository path:** [docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html](../design/previews/matrix_script_script_to_video_workbench_v1/index.html)
- **Open instructions:** double-click the file in Finder / Explorer to open in your default browser, or `open docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` from the repo root on macOS.
- **No FastAPI route was added** to keep `gateway/app/main.py` byte-untouched (mission boundary).
- The file is fully self-contained (inline CSS + inline JS + no external assets) so it loads identically whether served via `file://`, `python -m http.server`, or as a GitHub-rendered preview.

## 4. Mock pages / states delivered (all three required surfaces)

The mock contains three pages, switchable via the sticky top navigation. The accepted product target IA from `matrix_script_kapwing_benchmark_product_advice_v1.md` §7 / §8 / §9 is reflected as follows:

### 4.1 Page ① — 新建 · 生成视频方案 (`#entry`)

Replaces the legacy "create task" form with a script-to-video entry. Five cards on operator scan order:

| Card | data-role | Content |
|---|---|---|
| 1 · 脚本 | `mock-entry-script-card` | paste textarea (pre-filled with the sample script) + upload + select-existing CTAs. |
| 2 · 产品 / 素材 | `mock-entry-materials-card` | upload product clips / reference images / reference videos (placeholders). |
| 3 · 目标 · 画幅 · 语言 | `mock-entry-targets-card` | platform datalist (7 closed suggestions + free text) + 9:16/16:9/1:1 aspect ratio + target language multi-select + 受众. |
| 4 · 角色 · 声音 · 字幕 | `mock-entry-style-card` | role preference / voice preference / subtitle style / B-Roll preference (operator-language only). |
| 5 · 变体策略 | `mock-entry-variant-card` | 1 / 3 / 6 variant count + 差异维度 free-text. |
| → 提交 | `mock-entry-cta-card` | **Primary CTA: 「生成视频方案」** (NOT "创建任务"). Navigates to Page ② Workbench. |

### 4.2 Page ② — 工作台 · 矩阵脚本 · 脚本转视频 (`#workbench`)

Ten sections per the accepted product advice §7, in scan order:

| Section | data-role | Coverage |
|---|---|---|
| A · 主视频结果 | `mock-section-a-main-video-result` | preview hero in honest empty state · `未生成` pill · four buttons (生成主视频 disabled with honest tooltip; 重新生成 disabled; 接受为主版本 disabled; 前往交付页面 active anchor) · banner with blocker + next-action. |
| B · 脚本理解 | `mock-section-b-script-understanding` | Hook / Body / CTA / 卖点 / 关键词 / 禁用词 / 目标平台 + 时长 / 目标语言 — all populated from the sample script. |
| **C · 视频生成计划 (核心)** | `mock-section-c-generation-plan` | **3 scenes** decomposed from the sample script. Each scene shows: 脚本片段 / 视觉意图 / 背景建议 / B-Roll 建议 / 产品素材位 / 角色 / 出镜 / 旁白 / 字幕 / 音乐情绪 / 画幅. Per-scene fields are operator-language; B-Roll matching is marked `placeholder · 未接入素材匹配`. |
| D · 画面与素材 | `mock-section-d-visuals` | 4 background candidates (Scene 1) + 4 B-Roll candidates (Scene 2) + upload slot. Each card carries commercial-rights chip (`商用可` / `需审核` / `运营上传`). |
| E · 角色与声音 | `mock-section-e-role-voice` | role / 气质 / 性别 / 语气 / 目标语言 / 语速 selectors (operator-language) + 语音预览 placeholder explicitly tagged "VoiceTrans 桥接尚未接入"; no embedded VoiceTrans UI. |
| F · 字幕与音乐 | `mock-section-f-subtitle-music` | subtitle font / size / color / position / keyword-highlight + BGM mood / 音量 / 替换上传 (placeholder). |
| G · 视频变体 | `mock-section-g-variants` | 3 video-level variants (V1 厨房·上扬 ⭐推荐 / V2 农场·真情实感 / V3 超市·快节奏) each with "哪里不同 / 为什么测 / 推荐". NOT axis rows. |
| H · 校对与微调 | `mock-section-h-review` | 4 review zones (画面 / 旁白 / 字幕 / 文案·CTA) all in `待生成` placeholder state. |
| I · 交付入口 | `mock-section-i-delivery-entry` | 2-line + CTA → Page ③. |
| J · 技术诊断 | `mock-section-j-technical-diagnostics` | `<details>` collapsed by default; lists the retired primary markers (`matrix-script-block-a-goal-summary` … `matrix-script-block-f-delivery-teaser`) and the engineering identifiers that are quarantined here. |

### 4.3 Page ③ — 交付中心 · 主视频 + 发布 (`#delivery`)

Seven sections per the accepted advice §9 (carries PR-B's six sections + tightens copy + quarantines 1.85 SOP / pack legacy):

| Section | data-role | Content |
|---|---|---|
| 1 · 介绍 | `mock-dc-section-intro` | operator-language paragraph: "本任务当前不能交付：尚未生成主视频" + next-action line. |
| 2 · 主视频 | `mock-dc-section-main-video` | preview hero in honest empty state + `9:16 · 抖音` chip + disabled-with-tooltip download button. |
| 3 · 必需 | `mock-dc-section-required` | 5 required-deliverable rows (字幕 / 音频 / 文案包 / manifest / 交付包); missing rows link back to Workbench via "在 Workbench 重新生成" CTA (no inline regen). |
| 4 · 可选 | `mock-dc-section-optional` | 其他视频版本 (V2 / V3) collapsed fold + 场景包 + 补充素材. |
| 5 · 发布 | `mock-dc-section-publish-settings` | 6-field publish form (platform / account / title / copy / hashtags / scheduled time); submit disabled until main video generated. |
| 6 · 回填 | `mock-dc-section-backfill` | publish URL / status / operator note / metrics placeholder (explicitly "指标投射尚未上线"). |
| 7 · 技术诊断 | `mock-dc-section-technical` | `<details>` collapsed by default; quarantines `matrix-script-delivery-center-header` / Block A–F / Recovery PR-3 closure block / 1.85 pack-SOP legacy. |

## 5. Sample-content coverage

The mock uses the mission-required sample script **"美女十分开心地吃西红柿，说，西红柿亚克西。"** and demonstrates that the storyboard infers:

| Inference dimension | Mock content |
|---|---|
| Background candidates | 温馨厨房 / 清晨阳台 / 农场摘菜 / 超市果蔬区 (4 candidates in Section D) |
| B-Roll candidates | 西红柿特写 / 新鲜蔬菜组合 / 人物试吃慢动作 (3 candidates + 上传槽 in Section D) |
| Role / presenter options | AI 主播·温和女声 / 无角色·仅画面 / 本地主持人 #1 / 本地主持人 #2 / 自定义角色 (5 choices in Section E) |
| Voice | 温和女声 (operator-language only; no vendor name) |
| Subtitles | 大字 + 关键词高亮：开心 / 新鲜 / 亚克西 (Section F) |
| Music mood | 上扬 / 轻快 (Section F + per-scene C) |
| Video-level variants | V1 厨房·上扬 ⭐推荐 / V2 农场·真情实感 / V3 超市·快节奏 (Section G) |

## 6. Validation against accepted product direction

The mock satisfies every binding requirement from the accepted advice document and from the Phase 1 mission brief:

| Requirement | Mock evidence |
|---|---|
| Script-to-video entry, not task form (advice §8) | Page ① replaces "创建任务" CTA with "生成视频方案". |
| Visible generation plan before generation (advice §6.2) | Page ②, Section C renders the 3-scene storyboard with per-scene editable slots. |
| One clear generate action (advice §6.3) | Section A's "生成主视频" is the only generate CTA; disabled with honest tooltip. |
| Honest unsupported-capability labels (advice §6.4) | Every placeholder slot carries a `placeholder` / `future` flag chip; every disabled button has an operator-language `title` tooltip. |
| Backend diagnostics hidden (advice §6.5) | Section J + Section 7 are `<details>` collapsed by default; engineering identifiers (publish_readiness / head_reason / artifact_lookup / final_video / RC-R8 / event_kind / closure / 1.85 pack-SOP) appear ONLY inside those folds. |
| No fake output (advice §6.6) | 0 `<video>` / `<iframe>` / `.mp4` / `.m3u8` / fabricated URL in mock. Every preview hero renders the operator-language empty-state copy. |
| Variants are video versions, not axis tuples (advice §7.G) | Section G table is "V1 / V2 / V3" with "哪里不同 / 为什么测 / 推荐" columns. |
| No model / vendor / provider / engine controls (advice §15.2) | Audit-stripped primary scan: `provider` 0 / `vendor` 0 / `engine` 0 occurrences. |
| VoiceTrans not embedded raw (advice §15.6) | Section E renders a voice preview placeholder explicitly labelled "VoiceTrans 桥接尚未接入"; no iframe / no VoiceTrans UI. |
| Digital Anchor consumed-only (advice §11) | Section E references "数字人口播线" as a future provider; no in-place role-authoring form. |
| 1.85 pack / SOP legacy quarantined (mission §3) | Page ③ Section 7 lists the legacy identifiers inside the collapsed fold; primary scan reads operator-language only. |

### Forbidden-vocabulary primary-scan audit

Audit command (Section J + Section 7 + footer + scripts stripped; attribute values stripped; word-boundary match):

```
python3 -c "
import re
t=open('docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html').read()
t=re.sub(r'<details class=\"section7\".*?</details>','',t,flags=re.S)
t=re.sub(r'<footer class=\"mock-footer\".*?</footer>','',t,flags=re.S)
t=re.sub(r'<script.*?</script>','',t,flags=re.S)
t=re.sub(r'<style.*?</style>','',t,flags=re.S)
t=re.sub(r'<!--.*?-->','',t,flags=re.S)
t=re.sub(r'=\"[^\"]*\"','=\"\"',t)
for tok in ['publish_readiness','head_reason','artifact_lookup','final_video','RC-R8','provider','vendor','engine','source_script_ref','content://','slot_pack','provenance','variation_axis','event_kind','closure']:
    n=len(re.findall(rf'\\b{re.escape(tok)}\\b', t)); print(f'  {tok}: {n}')
"
```

Result: **VERDICT: CLEAN** — 0 occurrences of every audited forbidden token in the operator-primary scan.

## 7. Screenshots

Live-browser PNG capture is not available in this validation environment (no connected Chrome MCP browser; `.claude/launch.json` write was denied in PR-C). The mock itself IS the visual artifact: the file at [docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html](../design/previews/matrix_script_script_to_video_workbench_v1/index.html) renders identically in any modern browser (Chrome / Safari / Firefox / Edge), and the three tabs ① / ② / ③ map 1:1 to the mission's eight required screenshot views as follows:

| Mission screenshot view | Where in the mock |
|---|---|
| Entry page | Page ① (`#entry`), full scroll |
| Workbench first screen | Page ② (`#workbench`), top |
| Storyboard / generation plan | Page ② Section C (`mock-section-c-generation-plan`) |
| Visual materials section | Page ② Section D (`mock-section-d-visuals`) |
| Role and voice section | Page ② Section E (`mock-section-e-role-voice`) |
| Subtitle and music section | Page ② Section F (`mock-section-f-subtitle-music`) |
| Video variants section | Page ② Section G (`mock-section-g-variants`) |
| Delivery Center mock | Page ③ (`#delivery`) |

Architect-tier validation: open the file in a browser and click the three tabs. Functional validation (real-browser PNG capture) is recommended as the first gate after this Phase 1 sign-off, captured against either a local browser or via the Render preview environment when Phase 2 presenter mapping lands.

## 8. Explicit no-code / no-runtime / no-contract / no-fake-media statement

This PR makes **no** changes to any of the following:

- **No code.** Zero `.py` / `.js` (gateway) / `.css` (gateway) modifications. The mock's inline JS is a 14-line tab switcher with no network calls.
- **No template edits.** `gateway/app/templates/task_workbench.html`, `task_publish_hub.html`, `matrix_script_new.html`, `voice_tool.html` all bytewise unchanged.
- **No backend runtime.** `gateway/app/main.py`, `gateway/app/routers/`, `gateway/app/services/` bytewise unchanged. No new endpoint. No new dependency. No worker. No background task. No closure event.
- **No contract changes.** `docs/contracts/` untouched.
- **No schema changes.** `schemas/` untouched.
- **No packet changes.** No `production_packet*.json` mutation.
- **No closed-enum changes.** `event_kind` / `publish_status` / `head_reason` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` unchanged.
- **No Hot Follow / Digital Anchor / Asset Supply touch.**
- **No generation worker changes.**
- **No VoiceTrans raw UI embed.** Section E references VoiceTrans as a future provider via text label; no iframe / no embedded form.
- **No fake media.** 0 `<video>` / `<iframe>` / `<source>` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com` / `https://...placeholder` in the mock.
- **No fake `publish_url`.** Delivery Center §6 publish-URL column shows `—` for empty rows; the submit button in §5 is disabled until main video generated.
- **No fake `final_video`.** Every preview hero renders the helper-supplied empty-state copy.
- **No `provider` / `model` / `vendor` / `engine` controls.** Validator R3 compliant — primary-scan audit returns 0 occurrences of each token.

## 9. Does the mock satisfy the accepted product direction?

**Yes.** The mock realises every binding section from the accepted product advice document:

- §5 product target: the mock's three pages collectively express "脚本 → 视频方案 / 故事板 → 画面与 B-Roll → 角色 / 旁白 / 字幕 / 音乐 → 主视频与多版本 → 校对微调 → 交付发布".
- §6 minimal correction discipline: all six rules satisfied (result first / visible plan / one CTA / honest labels / hidden diagnostics / no fake output).
- §7 ten-section Workbench IA: all ten sections rendered (A–J).
- §8 New Task adjustment: CTA shifted to "生成视频方案"; all 11 recommended fields rendered.
- §9 Delivery Center adjustment: seven sections rendered with download CTA + aspect-ratio chip + 其他视频版本 fold + legacy quarantine.
- §10 / §11 VoiceTrans + Digital Anchor: referenced as future providers via label; never embedded.
- §15 risks / non-goals: every non-goal verified absent.

## 10. Known backend gaps (recorded for Phase 2+ planning)

The mock makes these gaps visible by labelling slots as `placeholder` / `future`:

1. **Scene-plan helper does not exist.** Section C scenes are hand-authored from the sample script. Phase 3 needs the Matrix Script line packet to gain a `scene_plan_binding` (additive to `factory_scene_plan_contract_v1`).
2. **B-Roll / background matching worker does not exist.** Section D candidates are hand-authored. Phase 5 needs the Asset Supply bridge wired.
3. **Voice preview / synthesis worker does not exist.** Section E preview slot is a text placeholder. Phase 4 needs the VoiceTrans bridge defined and wired through `factory_audio_plan_contract_v1`.
4. **Subtitle-style projection does not exist.** Section F style controls are inactive selectors. The compose worker must expose a subtitle-style projection (Phase 7 hardening) for them to flow.
5. **BGM matching worker does not exist.** Section F BGM-mood selector is inactive. Same gate as #4.
6. **Main video generation worker does not exist.** Section A "生成主视频" is permanently disabled until the Capability Expansion Wave lands.
7. **Variant video generation worker does not exist.** Section G "追加视频版本" / "同时生成所有版本" disabled until #6.
8. **Metrics projection does not exist.** Delivery §6 metrics placeholder is static text. Phase 7 hardening covers this.
9. **`scene_plan_binding` / `audio_plan_binding` / `language_plan_binding` line-packet extensions not authored.** Phase 3 work. The mock's primary-scan correctness does NOT depend on these extensions; the placeholders are honest about them.

## 11. Verdict request

Requesting reviewer verdict on:

1. The static mock at `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` is an acceptable Phase 1 artifact for product-direction sign-off.
2. The three-page IA (① 新建 / ② 工作台 with 10 sections / ③ 交付中心 with 7 sections) matches the accepted product advice document section-for-section.
3. The forbidden-vocabulary primary-scan audit (§6 of this report) is sufficient as a presentation-layer guardrail at this phase, with the understanding that the same audit must be re-run against rendered output in Phase 2.
4. The known backend gaps in §10 are the right Phase-2 / Phase-3 work intake list — none should be opened before this Phase 1 review closes.
5. The next authorised wave (per advice §14) is **Phase 2 — Presenter mapping with honest placeholders** in `task_workbench.html` and `task_publish_hub.html`, opened only after this Phase 1 mock is reviewed.

Stop here. Do not start presenter mapping or backend work until this Phase 1 mock is reviewed.
