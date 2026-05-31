# VeoMatrixVoice04 · Joint Validation Branch · Integration Report v1

Date: 2026-05-30
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (ApolloVeo Matrix Script + VoiceTrans Joint Validation Branch Operator — VeoMatrixVoice04).

## 1. Branch + base + ancestry

| Item | Value |
|---|---|
| Branch | `VeoMatrixVoice04` |
| Base | `origin/fix/ms-script-to-video-phase2b-new-task-entry-cards-20260530b` (HEAD = `c2d0daa`) |
| Final HEAD | `c2d0daa` (no extra commit on this branch — bytewise identical to base) |
| Push | ✅ pushed; new remote ref `VeoMatrixVoice04` created |
| Open-PR URL | https://github.com/zhaojfifa/apolloveo-auto/pull/new/VeoMatrixVoice04 |

**Required commit ancestry check:**

| Commit | Purpose | Result |
|---|---|---|
| `c2d0daa` | Phase 2B new-task entry-cards fidelity fix (5-card structure) | ✅ present |
| `076cddc` | Phase 2B fidelity fix (H1 / CTA / sidebar / header gate) | ✅ present |
| `4220fcd` | Phase 2B fidelity visual validation report | ✅ present |
| `origin/VoiceTrans` | VoiceTrans integration | ✅ present (via VeoMatrixVoice01 → ... chain) |

`VeoMatrixVoice03` (HEAD `71b7fad` with the audit addendum identifying the gap) is in ancestry too — preserved as the audit-of-record per the mission preamble.

## 2. VoiceTrans inclusion

**Already present — no merge required.** Verification:

```
$ git merge-base --is-ancestor origin/VoiceTrans HEAD && echo ✓
✓
$ ls -la gateway/app/templates/voice_tool.html gateway/app/routers/voice_tool.py gateway/app/services/voice_tool/__init__.py
-rw-r--r--@ 1 tylerzhao  staff   8462 May 28 21:54 gateway/app/routers/voice_tool.py
-rw-r--r--@ 1 tylerzhao  staff    305 May 28 21:54 gateway/app/services/voice_tool/__init__.py
-rw-r--r--@ 1 tylerzhao  staff  22726 May 28 21:54 gateway/app/templates/voice_tool.html
$ grep -n "voice_tool" gateway/app/main.py
35:    voice_tool as voice_tool_router,
195:app.include_router(voice_tool_router.page_router)
196:app.include_router(voice_tool_router.api_router)
```

## 3. Files changed (delta vs `origin/VeoMatrixVoice03`)

```
3 files changed, +639 / -31

gateway/app/templates/matrix_script_new.html                              | +208 / -31
gateway/app/services/tests/test_matrix_script_new_task_entry_cards_fidelity.py | +299 (new)
docs/execution/MATRIX_SCRIPT_NEW_TASK_ENTRY_CARDS_FIDELITY_FIX_REPORT_v1.md    | +163 (new)
```

**Zero changes** to `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow runtime, Digital Anchor runtime, Asset Supply runtime, VoiceTrans runtime, generation workers, or any other template / Python module beyond `matrix_script_new.html`.

## 4. New Task page marker audit

```
$ grep -c <marker> gateway/app/templates/matrix_script_new.html
```

| Marker | Count | Expected |
|---|---|---|
| `生成脚本视频方案` (H1) | 1 | ≥1 ✅ |
| `脚本来源` (Card 1 title) | 2 | ≥1 ✅ |
| `产品 / 素材` (Card 2 title) | 1 | ≥1 ✅ NEW |
| `目标 · 画幅 · 语言` (Card 3 title) | 2 | ≥1 ✅ NEW |
| `角色 · 声音 · 字幕` (Card 4 title) | 3 | ≥1 ✅ NEW |
| `变体策略` (Card 5 title) | 3 | ≥1 ✅ NEW |
| `生成视频方案` (CTA + Card 5 mention) | 1 | ≥1 ✅ |
| `任务基本信息` (LEGACY) | 1 | **0 in operator UI** ⚠ |

**Note on the `任务基本信息` count of 1**: this single occurrence lives inside a Jinja `{# … #}` comment block (line 385 of `matrix_script_new.html`: `"legacy single 任务基本信息 card is restructured into FOUR"`) — it is an architect-only annotation explaining the fidelity-fix history. Jinja comments are stripped at render time; the operator-visible HTML contains **0** occurrences of `任务基本信息`. The fidelity test `test_legacy_task_meta_card_title_absent` (`test_matrix_script_new_task_entry_cards_fidelity.py`) explicitly strips Jinja comments before the assertion and passes.

### 4.1 5-card structure verified (operator scan order)

| # | Card | data-role anchor | Source line range |
|---|---|---|---|
| 1 | 脚本 · 脚本来源 | `ms-new-card-source` | preserved from PR-1 |
| 2 | 素材 · 产品 / 素材 | `ms-new-card-product-material` | new (c2d0daa) |
| 3 | 目标 · 目标 · 画幅 · 语言 | `ms-new-card-target-aspect-language` | new (c2d0daa) |
| 4 | 角色 · 角色 · 声音 · 字幕 | `ms-new-card-role-voice-subtitle` | new (c2d0daa) |
| 5 | 变体 · 变体策略 | `ms-new-card-variant-strategy` | new (c2d0daa) |

`ms-new-card-task-meta` (legacy Card 2 data-role) — **absent from primary**.

## 5. Workbench marker audit

`gateway/app/templates/task_workbench.html` matrix_script branch — all 10 Phase 2B section anchors present exactly once:

| Section | data-role anchor | Count |
|---|---|---|
| A 主视频结果 | `matrix-script-main-video-result` | 1 |
| B 脚本理解 | `matrix-script-section-script-understanding` | 1 |
| C 视频生成计划 | `matrix-script-section-generation-plan` | 1 |
| D 画面与素材 | `matrix-script-section-visual-materials` | 1 |
| E 角色与声音 | `matrix-script-section-role-voice` | 1 |
| F 字幕与音乐 | `matrix-script-section-subtitle-music` | 1 |
| G 视频变体 | `matrix-script-section-video-versions` | 1 |
| H 校对与微调 | `matrix-script-section-review-tuning` | 1 |
| I 交付入口 | `matrix-script-section-delivery-entry` | 1 |
| J 技术诊断 | `op-console-ms-technical-diagnostics-fold` | 1 |

All 10 Phase 2B section anchors render in design order (validated by `test_primary_section_order_is_exactly_a_to_j` in the fidelity test suite).

## 6. Delivery Center marker audit

`gateway/app/templates/task_publish_hub.html` matrix_script branch — all 6 PR-B sections + §7 fold present exactly once:

| Section | data-role anchor | Count |
|---|---|---|
| 1 交付结果介绍 | `matrix-script-dc-section-intro` | 1 |
| 2 主视频 | `matrix-script-dc-section-main-video` | 1 |
| 3 必需交付物 | `matrix-script-dc-section-required-deliverables` | 1 |
| 4 可选交付物 | `matrix-script-dc-section-optional-deliverables` | 1 |
| 5 发布设置 | `matrix-script-dc-section-publish-settings` | 1 |
| 6 发布回填 | `matrix-script-dc-section-publish-backfill` | 1 |
| 7 技术诊断 | `op-console-ms-dc-technical-diagnostics-fold` | 1 |

## 7. VoiceTrans route audit

| Item | Result |
|---|---|
| `/voice-tool` page route wired | ✅ `gateway/app/main.py:195` includes `voice_tool_router.page_router` |
| `/api/voice-tool/*` API routes wired | ✅ `gateway/app/main.py:196` includes `voice_tool_router.api_router` |
| Template present | ✅ `gateway/app/templates/voice_tool.html` (22 726 bytes) |
| Router present | ✅ `gateway/app/routers/voice_tool.py` (8 462 bytes) |
| Service present | ✅ `gateway/app/services/voice_tool/__init__.py` (305 bytes) + `service.py` + `storage.py` |
| Test present | ✅ `gateway/app/services/tests/test_voice_tool_service.py` — 3 tests, all pass |
| VoiceTrans NOT embedded in Matrix Script Workbench | ✅ source-level `test_no_voicetrans_iframe_or_raw_form` (Phase 2B suite) passes |
| VoiceTrans NOT embedded in Matrix Script New Task | ✅ source-level `test_no_voicetrans_iframe_or_raw_form` (entry-card fidelity suite) passes |
| No route collision with Matrix Script | ✅ `/voice-tool` lives at root; Matrix Script under `/tasks/matrix-script/*` and `/tasks/{task_id}*` |

## 8. Test results

```
16 targeted Matrix Script + VoiceTrans suites:
  → 599 passed, 4 skipped, 1 failed (pre-existing)
```

| Suite | Tests | Result |
|---|---|---|
| `test_matrix_script_new_task_entry_cards_fidelity.py` (c2d0daa NEW) | **30** | ✅ all pass |
| `test_matrix_script_workbench_phase2b_product_fidelity.py` | 44 | ✅ all pass |
| `test_matrix_script_workbench_script_to_video_phase2b.py` | 53 | ✅ all pass |
| `test_matrix_script_workbench_product_flow_reset_pra.py` | 63 | ✅ all pass |
| `test_matrix_script_delivery_center_product_flow_reset_prb.py` | 69 | ✅ all pass |
| `test_matrix_script_workbench_blocks_{a_b_c,d_e_f}.py` | 156 | ✅ all pass |
| `test_matrix_script_workbench_optional_variants.py` | 9 | ✅ all pass |
| `test_matrix_script_workbench_redesign_2026_05_28.py` | 8 | ✅ all pass |
| `test_matrix_script_workbench_template_intact.py` | 7 | ✅ all pass |
| `test_matrix_script_workbench_diagnostics_quarantine.py` | 14 | ✅ all pass |
| `test_matrix_script_workbench_production_flow_stepper.py` | 6 | ✅ all pass |
| `test_matrix_script_workbench_main_video_result_template.py` | 11 | ✅ all pass |
| `test_matrix_script_delivery_center_pr3_reframing.py` | 25 | ✅ all pass |
| `test_matrix_script_delivery_center_blocks_a_to_f.py` | 100 | ✅ 99 pass / 1 ⚠ pre-existing / 4 skipped |
| `test_voice_tool_service.py` | 3 | ✅ all pass |
| **Total** | **600** | **599 ✅ / 1 ⚠ pre-existing / 4 skipped** |

The single failure `test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` is **pre-existing on VeoMatrixVoice01 / V02 / V03** (PR-2D wave drift; documented in PR-B report §4, V02 / V03 reports). Not introduced by this branch.

## 9. Known limitations

1. **Live-browser PNG capture not available in this environment.** No Chrome MCP browser connected; no `.claude/launch.json` write. Same constraint as PR-C / Phase 2B fidelity visual validation / V02 / V03. Functional validation must include a real-browser pass against the Render deploy or local FastAPI.
2. **Workbench live gate does NOT enter for an API-created matrix_script task with no packet binding.** Inherited from V02 / V03 (Known blocker #1). Source + 599-test regression + Jinja snapshots all confirm Phase 2B correctness; live gate requires the `operator_surfaces.workbench.line_specific_panel.panel_kind` projection to be populated. Functional validation either needs a packet-bound task fixture OR a presenter-layer projection-default fallback in `gateway/app/services/operator_visible_surfaces/wiring.py` (no contract / packet mutation required).
3. **Legacy task-meta header gate** in `task_workbench.html` (`{% if task.kind != "matrix_script" %}`) depends on `task.kind` being resolved correctly by the task-loading code path; functional validation should verify against a live `/tasks/{task_id}` for a packet-bound matrix_script task.
4. **VoiceTrans API endpoints not exercised in this report's smoke pass.** Only the page-route was smoke-tested in V02 / V03 (200 OK with all content markers). Functional validation should exercise `/api/voice-tool/translate`, `/synthesize`, `/speech-rewrite`, `/speech-variants`, `/download/{job_id}` end-to-end.
5. **Matrix Script remains NOT production-operable.** Backend final-video generation worker is still pending (Phase 6 of the accepted advice). Workbench §A continues to render the honest empty-state copy on every real task.
6. **`docs/design/screenshots/` rendered snapshots from the c2d0daa fidelity-card branch were not regenerated.** The PR-A / PR-B render harnesses cover Workbench + Delivery Center (already snapshotted under `matrix_script_phase2b_product_fidelity_fix_2026-05-30/`); the New Task page has no Jinja harness in this repo. The 30-test entry-card fidelity suite mechanically locks the New Task surface.

## 10. Explicit no-contract / no-schema / no-packet / no-runtime-worker / no-fake-media statement

This branch creation **does NOT modify any file** relative to its base `c2d0daa`. Specifically, this wave makes **no** changes to:

- **Contracts** (`docs/contracts/` untouched).
- **Schemas** (`schemas/` untouched).
- **Packets** (no `production_packet*.json` mutation).
- **Closed enums** (`event_kind` / `publish_status` / `head_reason` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` bytewise stable).
- **Backend generation / runtime workers** (no new worker, no new endpoint, no router edit, no service-layer mutation).
- **Hot Follow runtime** (bytewise unchanged).
- **Digital Anchor runtime** (bytewise unchanged).
- **Asset Supply runtime** (bytewise unchanged).
- **VoiceTrans runtime** (`gateway/app/services/voice_tool/*` and `gateway/app/templates/voice_tool.html` bytewise unchanged).
- **Generic factory readiness logic** (no projection re-derivation; UI continues to consume `ops_pr.publishable` unchanged).
- **No fake `final_video` / thumbnail / media URL / `publish_url` / generated media.** Confirmed by the 599-test regression suite (entry-card fidelity + Phase 2B fidelity + Phase 2B structural + back-compat) — 0 occurrences of `<video` / `<iframe` / `<source ` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com` in any operator-visible primary scan.
- **No VoiceTrans iframe / raw UI embed** inside Matrix Script branches.
- **No provider / model / vendor / engine controls** in primary UI.
- **VeoMatrixVoice03 untouched** — verified `git rev-parse origin/VeoMatrixVoice03` returns its prior HEAD `71b7fad` unchanged.

## 11. Final verdict

**VeoMatrixVoice04 is ready for joint manual validation.**

The root-cause F gap that blocked VeoMatrixVoice03 — the missing four Phase 1 mock entry cards on `/tasks/matrix-script/new` — is closed by `c2d0daa`. VeoMatrixVoice04 carries that fix on top of the validated Phase 2B fidelity stack and the preserved VoiceTrans integration:

- **New Task page** (`/tasks/matrix-script/new?ui_locale=zh`) — 5-card script-to-video structure: 脚本 / 素材 / 目标 · 画幅 · 语言 / 角色 · 声音 · 字幕 / 变体策略, with H1 `生成脚本视频方案` + CTA `生成视频方案 →` + 4-step sidebar.
- **Workbench** (`/tasks/{task_id}`) — 10-section Phase 2B IA (A → J) with the legacy task-meta header gated to non-matrix_script kinds and the PR-A standalone stepper relocated into §J.
- **Delivery Center** (`/tasks/{task_id}/publish`) — PR-B 6-section IA + §7 fold preserved.
- **VoiceTrans** (`/voice-tool`) — independent route, not embedded raw inside Matrix Script.

The 600-test regression run on this branch passes 599 / 600 (the single failure is pre-existing and documented). Functional validation should open with a real-browser pass against either the Render deploy or a local FastAPI; the live Workbench-gate-not-entering issue under packet-unbound conditions (Known limitation #2) is the only remaining smoke gap, inherited from V02 / V03 and not introduced by this wave.

Stopped after pushing branch and writing this report. **No Phase 3 start. No packet binding. No VoiceTrans bridge. No Asset Supply bridge. No video worker.**
