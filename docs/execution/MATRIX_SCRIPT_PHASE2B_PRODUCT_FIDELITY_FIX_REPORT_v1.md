# Matrix Script · Phase 2B Product Fidelity Fix · Implementation Report v1

Date: 2026-05-30
Branch: `fix/ms-script-to-video-phase2b-product-fidelity-20260530`
Base commit: `5f5a0bc` (Phase 2B presenter mapping; conditionally rejected for product validation)
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script Phase 2B Product Fidelity Fixer).

## 0. What this PR delivers

The Phase 2B implementation at `5f5a0bc` passed structural tests but drifted back toward the legacy task / status Workbench because:

- The legacy task-meta header card (status pill + `task_id` / `platform` / `account_id` / `category_key` / `language` meta-grid) sat ABOVE §A 主视频结果 for matrix_script tasks, beating the script-to-video product to first-screen attention.
- The PR-A standalone production-flow stepper sat between §A and §B, advertising backend status as a top-level visual.
- §C 视频生成计划 rendered only 4 status rows (脚本片段 / 视觉意图 / 音乐情绪 / 画幅) — not a storyboard.
- §G 视频变体 rendered only the legacy "main + others-fold" structure without the V1 / V2 / V3 video-version cards the Phase 1 mock + alignment spec defined.
- The New Task page still announced "创建矩阵脚本任务" and "正式产线新建入口" with a sidebar that named the legacy A–F blocks ("任务摘要 / 脚本结构 / 变体方案 / 生成进度 / 候选评审 / 交付摘要").

This fix corrects all five drifts. The real `task_workbench.html` + `matrix_script_new.html` now match the Phase 1 mock's mental model.

## 1. Branch + commit

| Item | Value |
|---|---|
| Branch | `fix/ms-script-to-video-phase2b-product-fidelity-20260530` |
| Base | `design/ms-script-to-video-presenter-mapping-phase2b-20260530` (5f5a0bc) |
| HEAD commit | to be reported on push. |
| Push | to be reported on push. |

## 2. Files changed

| File | Change |
|---|---|
| `gateway/app/templates/task_workbench.html` | (a) Wrapped the legacy task-meta header card (status pill + 9 task-meta rows) in `{% if task.kind != "matrix_script" %}` so matrix_script tasks open directly at §A 主视频结果. Hot Follow / Digital Anchor / baseline tasks keep their header bytewise unchanged. (b) Relocated the PR-A standalone production-flow stepper (181 lines) from the operator primary scan INTO the §J 技术诊断 collapsed fold (architect view). (c) Enriched §C 视频生成计划 with all 11 storyboard fields (场景编号 / 脚本片段 / 视觉意图 / 背景建议 / B-Roll 建议 / 产品素材位 / 角色 / 出镜 / 旁白 / 字幕 / 音乐情绪 / 画幅) with product-language placeholder content. (d) Added explicit V1 / V2 / V3 video-version cards in §G with `headline_zh` / `differentiator_zh` / `why_test_zh` / `is_recommended` / `current state` columns; legacy PR-A empty-state + main/others-fold preserved BELOW for back-compat. |
| `gateway/app/templates/matrix_script_new.html` | Topbar subtitle `"正式产线新建入口"` → `"脚本转视频 · 生成方案入口"`; page H1 `创建矩阵脚本任务` → `生成脚本视频方案`; subtitle expanded to the script-to-video promise; sidebar steps reframed away from legacy A–F vocabulary into the four script-to-video stages. |
| `gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py` | **New** — 44 product-fidelity assertions covering the 13-item mission checklist + the 14th matrix_script header-gate audit. |
| `gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py` | Updated 7 PR-A tests that previously asserted the standalone stepper anchor was in `primary_slice` to now assert against `matrix_branch` (full gate) — the stepper is legitimately quarantined inside §J fold per the Phase 2B fidelity fix. |
| `scripts/render_workbench_pra_screenshots.py` | Fixture context: added `task.kind = "matrix_script"` (+ category_key / platform / status) so the legacy header gate fires correctly in the snapshot render. |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html` | **New** rendered snapshot — Workbench operator first-scan; legacy task-meta header gated out; PR-A stepper gone from primary; §C 11-field storyboard visible; §G V1/V2/V3 cards visible. |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html` | **New** — Workbench architect view (§J expanded). |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html` | **New** — Delivery Center operator first-scan (PR-B bytewise untouched). |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_prb_delivery_center_full_section7_expanded.html` | **New** — Delivery Center architect view (§7 expanded). |
| `docs/execution/MATRIX_SCRIPT_PHASE2B_PRODUCT_FIDELITY_FIX_REPORT_v1.md` | This report. |

Zero changes to `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow runtime, Digital Anchor runtime, Asset Supply runtime, VoiceTrans runtime, generation workers, or generic factory readiness logic.

## 3. What drift was corrected

| Phase 2B drift | Fix |
|---|---|
| Legacy task-meta header card was visible at top of every matrix_script task page, looking like a project-management surface | Wrapped in `{% if task.kind != "matrix_script" %}`. Hot Follow / Digital Anchor / baseline tasks bytewise unchanged; matrix_script tasks now open at §A 主视频结果 directly. |
| PR-A standalone production-flow stepper sat between §A and §B in primary scan | Physically moved into §J 技术诊断 fold. The `matrix-script-production-flow-stepper` anchor + nine `ms-production-flow-step*` markers preserved bytewise inside the architect view for PR-A test back-compat. Seven PR-A tests updated to assert against `matrix_branch` rather than `primary_slice`. |
| §C 视频生成计划 rendered only 4 status rows, looking like backend pending diagnostics rather than a storyboard | Enriched to 11 storyboard fields per Phase 1 mock §C: 场景编号 / 脚本片段 / 视觉意图 / 背景建议 / B-Roll 建议 / 产品素材位 / 角色 / 出镜 / 旁白 / 字幕 / 音乐情绪 / 画幅. Deterministic placeholder content (厨房 / 阳台 / 农场 backgrounds; 主体特写 / 终镜定格 B-Roll; AI 主播 · 温和女声 roles; 上扬 / 上扬 sting music moods). All unsupported items carry honest pending chips but the section reads as a product plan. |
| §G 视频变体 rendered only the legacy "main + others-fold" structure | Added explicit V1 / V2 / V3 cards with `headline_zh` / 哪里不同 / 为什么测这一版 / current state columns; V1 carries ⭐ 推荐 marker. Legacy PR-A empty-state + main/others-fold preserved BELOW for back-compat with the PR-A optional-variants test suite. |
| New Task page H1 = 创建矩阵脚本任务; subtitle = 创建后…工作台评审; topbar subtitle = 正式产线新建入口; sidebar mentioned legacy A–F blocks | H1 → 生成脚本视频方案; subtitle → 输入脚本、素材和目标平台，系统先生成可确认的视频方案：脚本理解、分镜、背景 / B-Roll、角色、旁白、字幕、音乐与视频变体; topbar subtitle → 脚本转视频 · 生成方案入口; sidebar four-step copy = 生成脚本理解 → 生成视频方案 → 生成角色与音频计划 → 进入工作台确认方案，再生成主视频. |

## 4. Tests

| Suite | Tests | Result |
|---|---|---|
| `test_matrix_script_workbench_phase2b_product_fidelity.py` (NEW) | **44** | ✅ all pass — covers 13-item mission checklist + matrix_script header-gate audit (14th) |
| `test_matrix_script_workbench_script_to_video_phase2b.py` (Phase 2B) | 53 | ✅ all pass (unchanged) |
| `test_matrix_script_workbench_product_flow_reset_pra.py` (PR-A, updated) | 63 | ✅ all pass — 7 tests updated from `primary_slice` to `matrix_branch` for stepper-quarantined anchors |
| `test_matrix_script_delivery_center_product_flow_reset_prb.py` (PR-B) | 69 | ✅ all pass (DC bytewise unchanged) |
| `test_matrix_script_workbench_blocks_a_b_c.py` / `..._d_e_f.py` | 156 | ✅ all pass |
| `test_matrix_script_workbench_optional_variants.py` | 9 | ✅ all pass |
| `test_matrix_script_workbench_redesign_2026_05_28.py` | 8 | ✅ all pass |
| `test_matrix_script_workbench_template_intact.py` | 7 | ✅ all pass |
| `test_matrix_script_workbench_diagnostics_quarantine.py` | 14 | ✅ all pass |
| `test_matrix_script_workbench_production_flow_stepper.py` | 6 | ✅ all pass |
| `test_matrix_script_workbench_main_video_result_template.py` | 11 | ✅ all pass |
| `test_matrix_script_delivery_center_pr3_reframing.py` | 25 | ✅ all pass |
| `test_voice_tool_service.py` (VoiceTrans bytewise unchanged) | 3 | ✅ all pass |
| **Total** | **468** | **✅ all pass** |

## 5. Rendered artifact paths

Live-browser PNG capture remains unavailable in this environment (no connected Chrome MCP browser; no `.claude/launch.json` write). Rendered HTML snapshots via the existing Jinja harnesses:

| Artifact | Verified content |
|---|---|
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html` | All 7 new Phase 2B anchors render; legacy `workbench.meta.task_id` rows = **0 occurrences** (header gate fires); ⭐ 推荐 marker visible on V1; §C 11-field storyboard visible |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html` | §J fold open shows the relocated PR-A stepper + the retired legacy A–F op-cards |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html` | PR-B Delivery Center bytewise unchanged |
| `docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_prb_delivery_center_full_section7_expanded.html` | PR-B Section 7 fold expanded; bytewise unchanged from PR-B |

The New Task page snapshot is not re-rendered here (the existing harness only covers Workbench + Delivery Center); the source-level fidelity tests (`test_new_task_page_uses_script_to_video_title`, `test_new_task_subtitle_uses_script_to_video_promise`, `test_new_task_topbar_subtitle_is_script_to_video`, the 6 sidebar-omission parametrizations, `test_new_task_sidebar_has_four_script_to_video_steps`) verify the copy is correct.

## 6. Explicit no-contract / no-schema / no-packet / no-runtime / no-worker / no-fake-media statement

This fix wave makes **no** changes to any of the following:

- **No backend generation.** No worker added, no endpoint added, no router edit, no service-layer mutation.
- **No runtime worker logic.** `gateway/app/services/matrix_script/*` bytewise unchanged.
- **No contract changes.** `docs/contracts/` untouched.
- **No schema changes.** `schemas/` untouched.
- **No packet changes.** No `production_packet*.json` mutation.
- **No closed-enum changes.** `event_kind` / `publish_status` / `head_reason` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` bytewise stable.
- **No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime touch.** Hot Follow's task-meta header behavior is bytewise preserved (the `{% if task.kind != "matrix_script" %}` gate is true for Hot Follow tasks). Digital Anchor branch isolated. VoiceTrans (`gateway/app/services/voice_tool/`, `gateway/app/templates/voice_tool.html`) bytewise unchanged.
- **No VoiceTrans iframe / raw UI embed.** §E carries the same future-provider label as Phase 2B; no `<iframe>` in primary.
- **No provider / model / vendor / engine controls.** Audit assertion in §13 + §13.5 (fidelity test `test_no_vendor_name_in_primary_visible_text` covers azure / gemini / akool / seedance / openai / anthropic / google / elevenlabs).
- **No fake `final_video`.** Section A preview hero + Section 2 (DC) preview hero render the honest empty-state copy.
- **No fake thumbnail / media URL.** Audit returns 0 occurrences of `.mp4` / `.m3u8` / `.webm` / `youtu.be` / `tiktok.com` / `example.com` / streaming-host URLs in primary scan.
- **No fake `publish_url`.** DC §6 publish-URL column renders `—` for empty rows; submit button disabled until main video generated.
- **No generic factory readiness logic invented.** §I consumes `ops_pr.publishable` unchanged.

## 7. Does the real page now match Phase 1 mock product intent?

**Yes.** Concrete evidence:

| Phase 1 mock intent | Real page after fidelity fix |
|---|---|
| Workbench opens at 主视频结果 as the first-screen dominant section | ✅ Legacy task-meta header gated to non-matrix_script kinds; §A is the first visible card |
| §C reads as a generation plan with 11 storyboard fields | ✅ Each scene row renders the 11 fields (场景编号 + 10 op-meta-items) with product-language placeholders |
| §G renders V1 / V2 / V3 video-version cards with 哪里不同 / 为什么测 / 推荐 | ✅ Three explicit cards with literal `data-version-id="V1/V2/V3"`; ⭐ 推荐 on V1; legacy markers preserved below for back-compat |
| Backend status surfaces (stepper / task-meta) live only in architect view | ✅ Stepper relocated into §J fold; task-meta header gated out |
| Honest "当前占位 / 后台待接入 / 未接入素材匹配" chips on every unsupported slot | ✅ Closed status codes (`plan_pending_upstream`, `broll_pending_upstream`, `voice_preview_pending_voicetrans`, `subtitle_style_pending_compose`, `bgm_pending_upstream`, `review_pending_main_video`, `variants_pending_capability`) emitted on every placeholder slot |
| New Task page reads as script-to-video entry, not task form | ✅ H1 / subtitle / topbar subtitle / sidebar four-step copy all rewritten per Phase 1 mock ① 新建 |
| Legacy A–F op-cards quarantined inside §J | ✅ All 6 legacy markers asserted absent from primary scan and present in §J fold |

The 44 fidelity tests in `test_matrix_script_workbench_phase2b_product_fidelity.py` mechanically enforce these intent matches; the 468-test combined regression confirms no back-compat regression.

## 8. Verdict request

Requesting reviewer verdict on:

1. The five Phase 2B drifts (§3) are corrected — the real Workbench + New Task page match Phase 1 mock product intent.
2. The 14-assertion fidelity test suite (44 tests including parametrizations) is sufficient to lock the fix and prevent re-drift.
3. The Codex-conditioned no-contract / no-schema / no-packet / no-runtime / no-worker / no-fake-media discipline is preserved (§6).
4. The next authorized wave (Phase 3 line-packet additive bindings) opens only after a separate裁决 sign-off — the mission preamble explicitly forbids starting Phase 3 from this branch.

Stop here. No Phase 3. No backend generation. No worker. No contract / schema / packet / closed-enum change. No fake media.
