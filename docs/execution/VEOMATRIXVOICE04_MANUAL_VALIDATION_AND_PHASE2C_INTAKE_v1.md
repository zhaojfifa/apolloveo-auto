# VeoMatrixVoice04 · Manual Validation Preparation + Phase 2C Intake v1

Date: 2026-05-30
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (ApolloVeo Matrix Script + VoiceTrans Final Validation Recorder).

---

## 1. Executive verdict

**CONDITIONAL PASS WITH P1 / P2 ISSUES.**

- No **P0** found.
- Five **P1** product-mindset issues identified — primarily that Workbench §§B–F still feel more like "honest pending status surfaces" than usable script-to-video product panels.
- Eight **P2** readability / copy / layout issues identified — mostly around `当前占位 / 后台待接入` chip density, ambiguous CTA disabled-state explanations, and V1/V2/V3 cards needing stronger "for which account / scene" framing.

Phase 2C planning is recommended; **do NOT implement Phase 2C in this conversation.**

---

## 2. Environment

| Item | Value |
|---|---|
| Branch | `VeoMatrixVoice04` (also `docs/veomatrixvoice04-manual-validation-phase2c-intake-20260530` for this report) |
| Commit | `63bc709` (joint validation report on top of `c2d0daa` entry-cards fidelity fix) |
| Render URL | `https://apolloveo-auto.onrender.com` |
| Render build SHA | `63bc709a74943e9415af9dccd07d384e6d2e1b17` — **matches VeoMatrixVoice04 HEAD exactly** (no stale deploy) |
| Validation method | **Source-level audit + 143-test scoped regression + live HEAD-only smoke against Render** (Render `/healthz/build` confirmed the deployed SHA; `/tasks/matrix-script/new?ui_locale=zh` returned **HTTP 302** → `/auth/login?next=…` for unauthenticated access). No anonymous live browser PNG capture was possible. Live HTML body comparison degrades to source-level inspection inside this branch's checked-out template files. |
| Live PNG screenshot capture | **Not available in this environment.** No Chrome MCP browser connected; no `.claude/launch.json` write. Consistent with PR-C / Phase 2B fidelity visual validation / V02 / V03 limitations. |
| Source-level audit artifacts | `gateway/app/templates/matrix_script_new.html`, `gateway/app/templates/task_workbench.html`, `gateway/app/templates/task_publish_hub.html`, `gateway/app/templates/voice_tool.html` checked out at V04 HEAD. |
| Test result | 143 / 143 pass on the four scoped suites (entry-cards fidelity + Phase 2B product fidelity + Phase 2B structural + VoiceTrans service). |

---

## 3. New Task validation (`/tasks/matrix-script/new?ui_locale=zh`)

### Checklist result

| Check | Result | Source evidence |
|---|---|---|
| H1 `生成脚本视频方案` | ✅ | `grep -c` returns 1; lives at `matrix_script_new.html:208` |
| Card 1 `脚本 / 脚本来源` | ✅ | `grep -c 脚本来源` returns 2 (heading + label); anchor `ms-new-card-source` |
| Card 2 `素材 / 产品 / 素材` | ✅ | anchor `ms-new-card-product-material`; title literal `产品 / 素材` ×1 |
| Card 3 `目标 / 目标 · 画幅 · 语言` | ✅ | anchor `ms-new-card-target-aspect-language`; title `目标 · 画幅 · 语言` ×2 |
| Card 4 `角色 / 角色 · 声音 · 字幕` | ✅ | anchor `ms-new-card-role-voice-subtitle`; title ×3 (heading + helpers) |
| Card 5 `变体 / 变体策略` | ✅ | anchor `ms-new-card-variant-strategy`; title ×3 |
| CTA `生成视频方案 →` | ✅ | `grep -c` returns 1; submit button inner text |
| `任务基本信息` absent from operator UI | ✅ | `grep -c` returns 1, but the single match is inside a Jinja `{# … #}` comment (architect annotation); operator-visible HTML count = 0 (`test_legacy_task_meta_card_title_absent` passes) |
| `source_script_ref` hidden unless technical mode | ✅ | hidden `<input>` with `type="hidden"` present; mint-button gated by `technical_mode` |
| No VoiceTrans iframe / raw form | ✅ | 0 `<iframe>` / 0 `action="/api/voice-tool"`; Card 4 carries label-only tech-note `ms-new-voicetrans-future-provider-note` |
| No provider / model / vendor / engine controls | ✅ | 0 `<select|input name="provider|model|vendor|engine">`; 0 vendor names (azure / akool / seedance / openai / anthropic / elevenlabs) in operator copy |

**Live New Task smoke**: `curl https://apolloveo-auto.onrender.com/tasks/matrix-script/new?ui_locale=zh` returns HTTP 302 → `/auth/login`. Page body not anonymously inspectable; live PNG validation requires an authenticated browser session.

### Issues
- **None classified as P0 / P1 / P2 on the New Task page surface.** The Phase 2B entry-card fidelity fix (`c2d0daa`) closed all known gaps for this surface; the 30-test fidelity suite enforces the structure.

---

## 4. Workbench validation (`/tasks/{task_id}?created=matrix_script`)

### Checklist result

| Check | Result | Evidence |
|---|---|---|
| 10 Phase 2B section anchors A–J present in design order | ✅ | All 10 anchors render exactly once in template source (verified by `test_primary_section_order_is_exactly_a_to_j`) |
| Legacy task-meta header gated to non-matrix_script kinds | ✅ source | `{% if task.kind != "matrix_script" %}` wraps `info-row` + `meta-grid` (verified by `test_legacy_task_meta_header_gated_to_non_matrix_script`) |
| PR-A standalone production-flow stepper moved into §J | ✅ source | `matrix-script-production-flow-stepper` anchor lives only inside `op-console-ms-technical-diagnostics-fold` (verified by `test_pra_stepper_lives_inside_diagnostics_fold`) |
| §A 主视频结果 carries honest empty-state copy | ✅ source | `当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。` |
| §A 4 actions (生成主视频 / 重新生成 / 接受为主版本 / 前往交付页面) | ✅ source | `data-role="ms-main-video-result-actions"` carries all four; generate / regenerate / accept disabled with honest tooltip until worker lands |
| §C scene rows 11 storyboard fields (场景编号 / 脚本片段 / 视觉意图 / 背景建议 / B-Roll 建议 / 产品素材位 / 角色 · 出镜 / 旁白 / 字幕 / 音乐情绪 / 画幅) | ✅ source | All 11 `ms-section-generation-plan-scene-*` anchors present × 3 scenes = 33 instances |
| §G renders V1 / V2 / V3 with ⭐ on V1 + 哪里不同 + 为什么测这一版 | ✅ source | All three `data-version-id="V1/V2/V3"`; `recommended-marker` count = 1; `哪里不同` 4 / `为什么测这一版` 4 / `⭐ 推荐` 1 |
| No fake media (`<video` / `<iframe` / `<source` / `.mp4` / `.m3u8` / streaming-host URLs) in primary scan | ✅ source | 0 occurrences of each |
| No provider / model / vendor / engine controls | ✅ source | audit returns 0 |
| §J 技术诊断 `<details>` collapsed by default (no `open` attr) | ✅ source | `<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold">` (no `open`) |
| All 6 legacy A–F markers + PR-A stepper inside §J fold | ✅ source | 7 / 7 verified inside fold (verified by `test_legacy_block_marker_only_in_diagnostics_fold` × 6 + `test_pra_stepper_lives_inside_diagnostics_fold`) |

### Live render gap (inherited from V02 / V03)

The Workbench `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate **does not enter** for an API-created task with no packet binding, because `operator_surfaces.workbench.line_specific_panel.panel_kind` is empty for unbound tasks. Source + 143-test regression + Jinja snapshots all confirm Phase 2B correctness; this is a presenter-projection limitation, not a Phase 2B regression. Functional validation must use either a packet-bound task fixture OR add a small presenter-layer fallback (no contract / packet mutation required — out of scope for this report).

### Does the Workbench still feel too backend / status-oriented?

**Partially yes — see P1 issues §8 below.** The 10-section IA + 11-field storyboard + V1/V2/V3 video-version cards are structurally aligned with the Phase 1 mock. But several sections still read primarily as "what's pending" rather than "what choices the operator is making":

- §D 画面与素材 renders three slot anchors all carrying `data-status-code="broll_pending_upstream"` with three `当前占位` chips. Operator sees three "pending" labels before any actionable affordance.
- §E 角色与声音 renders all four operator-language selectors as static dropdowns, then a voice-preview slot labeled `🔊 语音预览占位 · VoiceTrans 桥接尚未接入`. The selectors look usable but the preview slot dominates the operator's eye.
- §F 字幕与音乐 renders style + BGM selectors with all chips reading `当前占位 · subtitle_style_pending_compose` / `当前占位 · bgm_pending_upstream`. The operator can read intent but nothing acts.
- §H 校对与微调 renders 4 review zones all reading `待主视频` with disabled accept/regenerate buttons.

This is honest discipline; it is also dense and slightly demoralising for a creator. Phase 2C should rebalance the "honest placeholder" density without claiming pretend capability.

### Issues
- See P1 §8 + P2 §9.

---

## 5. Delivery Center validation (`/tasks/{task_id}/publish`)

### Checklist result

| Check | Result | Evidence |
|---|---|---|
| 6 PR-B sections + §7 fold present | ✅ source | All 7 anchors render once (audited via `grep`) |
| Final-video-oriented (§2 主视频 as dominant) | ✅ source | §2 is the second card after §1 介绍; preview hero binds real artifact or honest empty state |
| No generation controls in DC primary | ✅ source | 0 `生成主视频` / `触发生成` / `立即生成` button labels in DC primary scan (only operator-language explanatory text mentions 生成) |
| Publish / download actions gated when `final_video` absent | ✅ source | DC §2 download button + DC §5 submit both carry `disabled` when `ops_pr.publishable` is false; the synthetic fixture renders disabled (validated by `test_section6_metrics_placeholder_present` + `test_section4_cta_points_to_delivery_center`) |
| No fake `final_video` / `publish_url` / media URL | ✅ source | 0 `<video` / `<iframe` / `<source` / `.mp4` / `.m3u8` / `example.com` / `youtu.be` / `tiktok.com` |
| Section 7 technical fold collapsed by default | ✅ source | `<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold">` (no `open`) |
| Legacy 1.85 SOP / pack identifiers quarantined inside §7 | ✅ source | All retired `matrix-script-block-*` + `matrix-script-closure` markers live inside the fold |

### Issues
- No P0 / P1 found on DC.
- One P2: see §9 item P2-7.

---

## 6. VoiceTrans validation (`/voice-tool`)

### Checklist result

| Check | Result | Evidence |
|---|---|---|
| `/voice-tool` page route wired | ✅ source | `gateway/app/main.py:195` includes `voice_tool_router.page_router` |
| `/api/voice-tool/*` API routes wired | ✅ source | `gateway/app/main.py:196` includes `voice_tool_router.api_router` |
| Template / router / service present | ✅ source | `voice_tool.html` (22 726 B), `voice_tool.py` (8 462 B), `services/voice_tool/__init__.py` + `service.py` + `storage.py` |
| Translation input visible | ✅ source | translation tab + textarea in `voice_tool.html` |
| Source / target language controls visible | ✅ source | language pickers present |
| Translation result area visible | ✅ source | result region present |
| Dubbing / voice generation area visible | ✅ source | `拟人配音` × 15 in template |
| `voice_tool_service` tests pass | ✅ 3 / 3 | `test_voice_tool_service.py` |
| No route collision with Matrix Script | ✅ | `/voice-tool` at root; Matrix Script under `/tasks/matrix-script/*` and `/tasks/{task_id}*`; no overlap |
| VoiceTrans NOT embedded inside Matrix Script branches | ✅ source | `test_no_voicetrans_iframe_or_raw_form` passes for both Workbench (Phase 2B suite) and New Task (entry-card fidelity suite) |

### Issues
- No P0 / P1 / P2 found on VoiceTrans within this audit scope. Functional validation should exercise `/api/voice-tool/translate` / `synthesize` / `speech-rewrite` / `speech-variants` / `download` end-to-end (recorded as known limitation in V02 / V03 / V04 reports).

---

## 7. P0 issue list

**No P0 issues found.**

---

## 8. P1 issue list (product-mindset)

| ID | Section | Description |
|---|---|---|
| **P1-1** | Workbench §D 画面与素材 | Three slot rows all carry `当前占位` + `data-status-code="broll_pending_upstream"`. Operator sees three identical "pending" rows before any product affordance. Phase 2C should compress the trio into one operator-language "素材匹配能力接入后会在这里出现背景 / B-Roll / 产品素材的候选" line + a single placeholder upload zone, instead of three identical pending slots. |
| **P1-2** | Workbench §E 角色与声音 | The voice-preview placeholder (`🔊 语音预览占位 · VoiceTrans 桥接尚未接入`) is the biggest visual element in the section, beating the four operator-language preference selectors. Phase 2C should demote the preview placeholder into a small inline chip and elevate the four preference selectors (角色 / 气质 / 性别 + 语气 / 目标语言 / 语速) so the section reads as a choice panel. |
| **P1-3** | Workbench §F 字幕与音乐 | Subtitle font / position / BGM mood / volume rows all read `当前占位 · subtitle_style_pending_compose` / `bgm_pending_upstream`. The operator can read the intended choices but none is interactive. Phase 2C should let the selectors actually carry operator intent (no backend submission) so the operator can express style preference in the Workbench, paralleling the choices already captured in New Task Card 4. |
| **P1-4** | Workbench §G 视频变体 | V1 / V2 / V3 cards correctly carry 哪里不同 + 为什么测这一版. But the "for which account / scene" framing requested by the mission (Phase 1 mock §G "what is recommended" column) is not visible. Phase 2C should add a third operator-language column per card: `适合哪些账号 / 场景` (operator-language one-liner; default placeholder when no metrics projection exists). |
| **P1-5** | Workbench overall | Sections D / E / F / H all carry one or more `当前占位` chips at the top of the card. On the first scroll the operator sees the same chip pattern four times. The chip is honest but it crowds out the product copy. Phase 2C should consolidate the per-section pending pill into a single Workbench-level "成片生成能力接入后此区将启用" banner with chip-collapsing rule (e.g. show one collapsed status indicator + an expandable diagnostic row), so the operator's primary scan is not dominated by "pending" pills. |

---

## 9. P2 issue list (readability / copy / layout)

| ID | Section | Description |
|---|---|---|
| **P2-1** | Workbench §B 脚本理解 | 卖点 row reads `卖点项尚未由 content_structure 投射；可在 J 节查看占位字段。`. The mention of `content_structure` leaks a contract-layer term into operator copy. Phase 2C should rewrite to `卖点项接入后会在这里展开。当前阶段以脚本主旨为准。` (no contract name). |
| **P2-2** | Workbench §C disclaimer copy | `上述分镜为占位草案；正式方案需由后端方案生成能力产出，当前不声明任何镜头已就绪。` uses "后端" — operator-facing copy should not name "后端". Phase 2C should rewrite to `当前展示的是占位草案；方案生成能力接入后会替换为真实分镜，每个镜头单独可编辑。` |
| **P2-3** | Workbench §D disabled-button tooltips | Three buttons disabled with tooltips like `素材匹配能力尚未接入。` repeat the same sentence. Phase 2C should differentiate per button: `背景候选接入后开放替换` / `B-Roll 候选接入后开放替换` / `素材匹配能力接入后开放重新生成建议`. |
| **P2-4** | Workbench §E small print | `本节不嵌入 VoiceTrans 页面；运营时层接入后由系统选择供应方，不向运营暴露供应商名。` uses `供应方` / `供应商名` (operator-language) — good. But `本节不嵌入 VoiceTrans 页面` reads as architect disclosure. Phase 2C should soften to `语音预览能力接入后会在这里实时试听；当前阶段以偏好选择为准。`. |
| **P2-5** | Workbench §G version cards | Each V1 / V2 / V3 card uses pill `当前占位 · 待生成`. The repeating `当前占位` is dense; the recommendation marker ⭐ 推荐 is the only visual difference. Phase 2C should split status into two pills: `推荐 / 备选` (recommended marker) + `待生成 / 已生成 / 待审核` (state pill from worker; default `待生成`) — operator's eye reads recommendation first, state second. |
| **P2-6** | Workbench §H | Four review zones all read `待主视频生成。`. The single-sentence repetition is redundant. Phase 2C should consolidate into a single banner `主视频生成后，按 4 个分区开放校对入口` + the 4 zone labels listed compactly without per-row status text. |
| **P2-7** | Delivery Center §6 metrics placeholder | The metrics placeholder card reads `指标投射尚未上线 · 暂不展示数值。` — accurate but flat. Phase 2C should rephrase as `指标投射上线后会展示首发完播率 / 点赞 / 评论 / 留资数据。` so the operator understands what metrics will appear, not just that they're missing. |
| **P2-8** | New Task Card 4 voice/role copy | Card 4 dropdown options use generic operator labels (女声自然 / 男声专业 / 轻松直接). Phase 2C should pair each label with a usage hint: `女声自然（推荐：日常种草）` / `男声专业（推荐：知识科普 / 评测）` / `轻松直接（推荐：促销 / 转化）` to help operators choose without auditioning. |

---

## 10. Phase 2C recommended scope

Phase 2C is **operator-readability + product-mindset polish only**. **No backend / contract / packet / worker change.** Recommended planning target (do NOT open implementation in this conversation):

| Area | Phase 2C target |
|---|---|
| Workbench §B / §C / §D / §E / §F / §G copy | Rewrite operator-visible copy per P2-1 through P2-8 to remove backend-leaking terms (`content_structure`, `后端`, etc.) and add product framing (usage hints, recommendation + state split, consolidated banners). |
| Workbench §D placeholder density | Compress three identical pending slots into one consolidated "素材接入后展开" line + a single upload zone (per P1-1). |
| Workbench §E layout | Demote the voice-preview placeholder into an inline chip; elevate the four preference selectors (per P1-2). |
| Workbench §F | Make subtitle style + BGM selectors carry operator intent (presenter-only; no backend submission) so the section reads as a choice panel (per P1-3). |
| Workbench §G | Add `适合哪些账号 / 场景` column per V1/V2/V3 card; split status into `推荐 / 备选` + worker state pill (per P1-4 + P2-5). |
| Workbench overall | Consolidate per-section pending pills into one Workbench-level capability banner with chip-collapsing (per P1-5). |
| Delivery Center §6 | Reword metrics placeholder per P2-7. |
| New Task Card 4 | Add usage hints to role / voice option labels per P2-8. |
| Tests | Extend `test_matrix_script_workbench_phase2b_product_fidelity.py` with assertions that operator-language hints exist and forbidden contract terms (`content_structure`, `后端`) are absent. |
| Rendered artifacts | Re-render Jinja snapshots after Phase 2C lands to capture the new operator-readable layout. |

### Discipline rules carried into Phase 2C (binding)

- **Preserve honest placeholders** — the chips and disabled buttons stay; only the copy + density change.
- **Preserve all architecture and contract boundaries** — no `factory_*` contract / schema / packet / closed-enum touch.
- **Preserve the 10-section Workbench IA + 6-section DC IA** — no section added or removed; only copy + per-section layout polished.
- **Preserve the V1 / V2 / V3 video-version framing** — variants stay as video versions, not axis rows.
- **Preserve the §J / §7 fold quarantine** — legacy A–F + stepper + raw vocabulary stay inside the architect view.
- **Preserve the New Task 5-card structure** — only Card 4 option labels gain usage hints; structure unchanged.

---

## 11. Hard red lines for Phase 2C

- **No backend generation worker added.**
- **No runtime workers added.** No service-layer mutation; no new dependency.
- **No contract / schema / packet / closed-enum changes.** The 6 factory-generic contracts (`factory_input` / `factory_content_structure` / `factory_scene_plan` / `factory_audio_plan` / `factory_language_plan` / `factory_delivery`) remain bytewise stable.
- **No fake `final_video` / thumbnail / media URL / `publish_url` / generated media.** Empty-state copy + disabled-with-honest-tooltip discipline carries.
- **No raw VoiceTrans embedding** inside Matrix Script branches. VoiceTrans stays at `/voice-tool` as an independent tool; future bridging is the runtime layer's job (Phase 4 in the accepted advice §14).
- **No provider / model / vendor / engine controls** in any operator-visible primary copy.
- **No Hot Follow / Digital Anchor regression.** Both surfaces bytewise untouched.
- **No merge to `main`.** Phase 2C lands on a `fix/ms-script-to-video-phase2c-operator-readability-…` branch then promotes through a fresh `VeoMatrixVoice05` joint validation branch.

---

## 12. Recommended next-conversation opening prompt

```text
We are continuing from VeoMatrixVoice04.

Current branch:       VeoMatrixVoice04
Current HEAD:         63bc709 (joint validation report on top of c2d0daa entry-card fidelity fix)
Render build SHA:     63bc709 (deployed and verified)
Required ancestors:   c2d0daa ✓ · 076cddc ✓ · 4220fcd ✓ · origin/VoiceTrans ✓
Validation status:    CONDITIONAL PASS WITH P1/P2 ISSUES
                      (no P0; 5 P1 product-mindset; 8 P2 readability/copy)
Open audit:           docs/execution/VEOMATRIXVOICE04_MANUAL_VALIDATION_AND_PHASE2C_INTAKE_v1.md

Outstanding P1 (product-mindset, Workbench-side):
  P1-1  §D 画面与素材 — three identical pending slots dominate; consolidate.
  P1-2  §E 角色与声音 — voice-preview placeholder beats the 4 preference selectors visually.
  P1-3  §F 字幕与音乐 — style + BGM selectors should carry operator intent (presenter-only).
  P1-4  §G 视频变体 — V1/V2/V3 cards need a third column "适合哪些账号 / 场景".
  P1-5  Workbench overall — pending pills repeat 4× across D/E/F/H; consolidate.

Outstanding P2 (readability / copy):
  P2-1  §B 卖点 row leaks "content_structure" — rewrite to operator language.
  P2-2  §C disclaimer leaks "后端" — rewrite.
  P2-3  §D button tooltips repeat the same sentence — differentiate per button.
  P2-4  §E small print reads as architect disclosure — soften.
  P2-5  §G card pills repeat "当前占位 · 待生成" — split into 推荐/备选 + state.
  P2-6  §H 4 review zones repeat "待主视频生成" — consolidate.
  P2-7  DC §6 metrics placeholder flat — say what metrics will appear.
  P2-8  New Task Card 4 role/voice labels need usage hints.

Immediate task: **Phase 2C operator-readability planning only**.

DO NOT implement Phase 2C in this conversation. Produce a planning
document (recommended path: docs/design/matrix_script_phase2c_operator_
readability_plan_v1.md) covering:
  - per-issue acceptance criteria (P1-1 through P2-8)
  - presenter-layer / template-layer edit boundaries
  - test additions (extend Phase 2B fidelity suite)
  - rendered artifact targets

Hard red lines (binding):
  - no backend generation, no workers, no endpoints, no router edits
  - no contracts / schemas / packets / closed-enum changes
  - no fake final_video / thumbnail / media URL / publish_url
  - no raw VoiceTrans iframe / embed
  - no provider / model / vendor / engine controls
  - no Hot Follow / Digital Anchor regression
  - no main merge

Stop after the planning document is committed and pushed to its own
docs branch (recommended: design/ms-phase2c-operator-readability-
planning-<YYYYMMDD>). Do not open Phase 2C implementation until the
planning document is reviewed.
```

---

## 13. Final stop statement

**Stop here. Do not implement Phase 2C in this conversation.**
