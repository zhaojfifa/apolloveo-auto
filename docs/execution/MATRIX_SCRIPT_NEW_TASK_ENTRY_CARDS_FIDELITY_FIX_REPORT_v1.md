# Matrix Script · New Task Entry Cards · Fidelity Fix Implementation Report v1

Date: 2026-05-30
Branch: `fix/ms-script-to-video-phase2b-new-task-entry-cards-20260530b`
Base: `VeoMatrixVoice03` (HEAD = 71b7fad; audit addendum identified root cause F)
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Matrix Script New Task Entry Card Fidelity Fixer).

## 1. Root cause fixed

Per the VeoMatrixVoice03 audit addendum (§11 of `docs/execution/VEOMATRIXVOICE03_JOINT_VALIDATION_REPORT_v1.md`): the Phase 2B fidelity fix at 076cddc renamed the New Task page H1 / CTA / sidebar / topbar subtitle but **never added** the four product-language entry cards from the Phase 1 mock §① and the presenter-alignment spec §5.1. The deployed page still showed the legacy two-card form (`脚本来源` + `任务基本信息`); the four cards (`产品 / 素材`, `目标 · 画幅 · 语言`, `角色 · 声音 · 字幕`, `变体策略`) were absent.

This branch closes that gap **template-only**, preserving the existing safe POST + `build_matrix_script_task_payload` contract bytewise.

## 2. Files changed

| File | Change |
|---|---|
| [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) | Replaced the legacy single `Card 2 · 任务基本信息` (data-role `ms-new-card-task-meta`) with FOUR new product-language cards: `Card 2 · 素材` (`ms-new-card-product-material`) · `Card 3 · 目标 · 画幅 · 语言` (`ms-new-card-target-aspect-language`) · `Card 4 · 角色 · 声音 · 字幕` (`ms-new-card-role-voice-subtitle`) · `Card 5 · 变体策略` (`ms-new-card-variant-strategy`). Every POST-required `name=` attribute preserved (topic / source_language / target_language / target_platform / variation_target_count / audience_hint / tone_hint / length_hint / product_ref / operator_notes / source_script_ref / existing_source_script_ref / script_body). Card 1 (`脚本来源`) preserved verbatim. Page H1 / CTA / sidebar / topbar subtitle preserved per 076cddc. |
| [gateway/app/services/tests/test_matrix_script_new_task_entry_cards_fidelity.py](../../gateway/app/services/tests/test_matrix_script_new_task_entry_cards_fidelity.py) | **New** — 30 fidelity assertions covering the 12-item mission test plan + 4 bonus per-card sub-field assertions. |
| [docs/execution/MATRIX_SCRIPT_NEW_TASK_ENTRY_CARDS_FIDELITY_FIX_REPORT_v1.md](MATRIX_SCRIPT_NEW_TASK_ENTRY_CARDS_FIDELITY_FIX_REPORT_v1.md) | This report. |

`git diff --stat` summary: 1 template modified (+~200 lines, –~70 lines), 1 new test file (+~280 lines), 1 new report.

Zero changes to `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow runtime, Digital Anchor runtime, Asset Supply runtime, VoiceTrans runtime, generation workers, or any other template / Python module.

## 3. Card structure before / after

### Before (076cddc / 4220fcd / V03)

```
Page H1:      生成脚本视频方案                                 ✓ Phase 2B fidelity (076cddc)
Topbar sub:   脚本转视频 · 生成方案入口                        ✓ Phase 2B fidelity
Subtitle:     输入脚本、素材和目标平台…                        ✓ Phase 2B fidelity
Card 1:       1 · 脚本   脚本来源     (paste / upload / select) ✓
Card 2:       2 · 任务   任务基本信息  (LEGACY single big form: ✗ mismatched product intent
                                       topic / source_lang /
                                       target_lang / target_platform /
                                       variation_target_count /
                                       audience / tone / length /
                                       product_ref / operator_notes)
[NO 产品 / 素材 card]                                          ✗ MISSING
[NO 目标 · 画幅 · 语言 card]                                   ✗ MISSING
[NO 角色 · 声音 · 字幕 card]                                   ✗ MISSING
[NO 变体策略 card]                                             ✗ MISSING
CTA:          生成视频方案 →                                   ✓ Phase 2B fidelity
Sidebar:      4 script-to-video steps                          ✓ Phase 2B fidelity
```

### After (this branch)

```
Page H1:      生成脚本视频方案                                 ✓ preserved
Topbar sub:   脚本转视频 · 生成方案入口                        ✓ preserved
Subtitle:     输入脚本、素材和目标平台…                        ✓ preserved
Card 1:       1 · 脚本   脚本来源     (paste / upload / select) ✓ preserved
Card 2:       2 · 素材   产品 / 素材   (NEW per mock §①.2)
              · product_ref (renamed label "产品名称 / SKU / 资料链接")
              · upload slot placeholder (status code materials_pending_upstream)
              · material description textarea
              · B-Roll preference select
Card 3:       3 · 目标   目标 · 画幅 · 语言   (NEW per mock §①.3)
              · topic (renamed label "视频主题")
              · target_platform + datalist (7 platform suggestions + free text)
              · aspect ratio radio (9:16 / 16:9 / 1:1) — operator intent only
              · source_language / target_language selects
              · length_hint (renamed "视频时长")
              · audience_hint (renamed "目标受众")
Card 4:       4 · 角色   角色 · 声音 · 字幕   (NEW per mock §①.4)
              · role preference select (无角色 / AI 主播 / 本地主播 / 自定义)
              · voice preference select (女声自然 / 男声专业 / 轻松直接 / 无旁白)
              · subtitle style select (大字高亮 / 品牌色 / 常规 / 极简)
              · tone_hint (renamed "目标语言旁白说明")
              · VoiceTrans future-provider tech-note (label only, no iframe)
Card 5:       5 · 变体   变体策略   (NEW per mock §①.5)
              · variation_target_count (renamed "测试版本数量", default 3)
              · 8 variant-axis checkboxes (operator intent; not in POST payload)
              · operator_notes textarea (footer)
CTA:          生成视频方案 →                                   ✓ preserved
Sidebar:      4 script-to-video steps                          ✓ preserved
```

**Removed from primary UI**: `Card 2 · 任务基本信息` title + `ms-new-card-task-meta` data-role. The underlying 10 form fields are redistributed across Cards 2–5 with operator-language labels; every `name=` attribute is preserved.

## 4. Tests

```
python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_new_task_entry_cards_fidelity.py    [30 new tests]
  gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py [44]
  gateway/app/services/tests/test_matrix_script_workbench_script_to_video_phase2b.py  [53]
  gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py   [63]
  gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py [69]
  gateway/app/services/tests/test_matrix_script_workbench_blocks_a_b_c.py             [82]
  gateway/app/services/tests/test_matrix_script_workbench_blocks_d_e_f.py             [74]
  gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py        [9]
  gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py      [8]
  gateway/app/services/tests/test_matrix_script_workbench_template_intact.py          [7]
  gateway/app/services/tests/test_matrix_script_workbench_diagnostics_quarantine.py   [14]
  gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py  [6]
  gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py [11]
  gateway/app/services/tests/test_matrix_script_delivery_center_pr3_reframing.py      [25]
  gateway/app/services/tests/test_voice_tool_service.py                                [3]
  → 498 passed
```

The 30 new fidelity tests cover the 12 mission assertions (1-4 four-card presence + ordering, 5 legacy-title-absent, 6 CTA-preserved, 7 source_script_ref hidden, 8 technical-mode controls preserved, 9 no VoiceTrans iframe / raw form, 10 no provider/model/vendor/engine controls, 11 no fake media / publish URL, 12 13 POST-required name= attributes preserved) + 4 bonus per-card sub-field audits.

**Pre-existing failures NOT introduced by this branch** (confirmed on the V03 base via `git stash`):

- `test_matrix_script_new_page_redesign_2026_05_28.py::test_mission_mandated_operator_copy_present` (PR-1 asserted old subtitle copy, superseded by 076cddc)
- `test_matrix_script_new_page_redesign_2026_05_28.py::test_page_title_is_chinese_operator_language` (PR-1 asserted old H1 `创建矩阵脚本任务`, superseded by 076cddc)
- `test_matrix_script_source_script_ref_shape.py::test_template_helper_text_forbids_pasting_body` / `test_template_helper_text_documents_transitional_convention` (PR-1 asserted helper-text wording removed during operator boundary polish)
- `test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` (PR-2D drift; documented since PR-B report §4)

All five are inherited from prior waves and predate this fidelity-card fix.

## 5. Rendered artifact paths

Live-browser PNG capture remains unavailable in this environment (no Chrome MCP browser connected; no `.claude/launch.json` write — same constraint as PR-C / Phase 2B fidelity visual validation / V02 / V03 reports). Validation degrades to **source-level audits** + the **30-test fidelity suite** + the **498-test combined regression**.

The New Task page is not covered by the existing Workbench / Delivery Center Jinja render harness (the harness renders `task_workbench.html` and `task_publish_hub.html` only). Rendering the New Task page requires the full FastAPI app stack (or a fresh Jinja harness fixture for `matrix_script_new.html`) which is beyond the template-only scope of this fix. The source-level fidelity tests in `test_matrix_script_new_task_entry_cards_fidelity.py` mechanically verify every required marker.

Recommended next-step screenshot path (NOT produced by this branch): render against the live FastAPI app on VeoMatrixVoice04 (the next joint validation branch after this fix lands).

## 6. Explicit no-contract / no-schema / no-packet / no-runtime / no-worker / no-fake-media statement

This fix wave makes **no** changes to any of the following:

- **No code beyond two files.** Modified: `gateway/app/templates/matrix_script_new.html` (template only). Added: `gateway/app/services/tests/test_matrix_script_new_task_entry_cards_fidelity.py` (test only).
- **No backend generation.** No worker added, no endpoint added, no router edit, no service-layer mutation.
- **No contract changes.** `docs/contracts/` untouched.
- **No schema changes.** `schemas/` untouched.
- **No packet changes.** No `production_packet*.json` mutation.
- **No closed-enum changes.** All seven closed enums bytewise stable.
- **No new payload field.** The four new cards' presenter-only fields (`aspect ratio radio` / `role / voice / subtitle / B-Roll preference selectors` / `variant-axis checkboxes` / `material upload slot` / `material description textarea`) do NOT carry `name=` attributes that would land in the form POST. Only the existing 13 POST-required fields submit.
- **No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime touch.** `gateway/app/services/voice_tool/*`, `gateway/app/templates/voice_tool.html`, `gateway/app/services/hot_follow/*`, `gateway/app/services/digital_anchor/*` all bytewise unchanged.
- **No VoiceTrans iframe / raw UI embed.** Card 4 carries the `ms-new-voicetrans-future-provider-note` disclaimer (label-only); audit asserts 0 `<iframe>` / 0 `action="/api/voice-tool"` / 0 `action="/voice-tool"` in the New Task source.
- **No provider / model / vendor / engine controls.** Audit asserts 0 form controls with those names; 0 vendor names (azure / akool / seedance / openai / anthropic / elevenlabs) in operator copy outside Jinja statements.
- **No fake `final_video` / thumbnail / media URL / `publish_url` / generated media.** Audit asserts 0 occurrences of `.mp4` / `.m3u8` / `.webm` / streaming-host URL in the New Task source.
- **No backend payload contract change.** The form action remains the existing `/tasks/matrix-script/new` POST path; the four new cards expose only presenter-only operator-intent capture; `build_matrix_script_task_payload` continues to receive the bytewise-identical 13-field payload it has consumed since PR-1.

## 7. Whether VeoMatrixVoice03 can be repaired from this branch

**Yes.** VeoMatrixVoice03 can be repaired by:

1. Fast-forwarding `VeoMatrixVoice03` to include this branch's HEAD (when this fix merges), or
2. Creating `VeoMatrixVoice04` from this fix branch's HEAD (recommended — V03 stays as the audit-of-record).

Either path puts the four missing entry cards into the joint validation surface. Render and live-browser smoke against `https://apolloveo-auto.onrender.com/tasks/matrix-script/new` should then show:

- H1 `生成脚本视频方案` (preserved)
- Card 1 `脚本来源` (preserved)
- Card 2 `产品 / 素材` (NEW — fixed by this branch)
- Card 3 `目标 · 画幅 · 语言` (NEW — fixed by this branch)
- Card 4 `角色 · 声音 · 字幕` (NEW — fixed by this branch)
- Card 5 `变体策略` (NEW — fixed by this branch)
- CTA `生成视频方案 →` (preserved)
- Sidebar 4 script-to-video steps (preserved)
- Legacy `任务基本信息` title — gone

The audit addendum §11 of `VEOMATRIXVOICE03_JOINT_VALIDATION_REPORT_v1.md` should be cross-referenced; a follow-up V04 report should record the verdict shift from BLOCKED to READY.

Stop here. No Phase 3 start. No backend generation. No worker. No contract / schema / packet / closed-enum change.
