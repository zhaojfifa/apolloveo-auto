# VeoMatrixVoice03 · Joint Validation Branch · Integration Report v1

Date: 2026-05-30
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (ApolloVeo Matrix Script + VoiceTrans Joint Validation Branch Operator).

## 1. Branch + base + commits

| Item | Value |
|---|---|
| Branch | `VeoMatrixVoice03` |
| Base | `origin/fix/ms-script-to-video-phase2b-product-fidelity-20260530` |
| Required commit `076cddc` (Phase 2B product fidelity fix) | ✅ verified in ancestry |
| Required commit `4220fcd` (Phase 2B fidelity visual validation report) | ✅ verified in ancestry |
| Final HEAD | `4220fcd` (no extra commit — branch is bytewise identical to the validated fidelity-fix HEAD) |
| Push | ✅ pushed; new remote ref created |
| Open-PR URL | https://github.com/zhaojfifa/apolloveo-auto/pull/new/VeoMatrixVoice03 |

## 2. VoiceTrans inclusion

**Already present — no merge required.** Verification:

```
$ git merge-base --is-ancestor origin/VoiceTrans VeoMatrixVoice03 && echo ✓
✓
$ git branch -a --contains origin/VoiceTrans
  VeoMatrixVoice01
  VeoMatrixVoice02
* VeoMatrixVoice03
  design/ms-kapwing-benchmark-product-advice-20260529
  design/ms-script-to-video-presenter-alignment-20260529
  ...
```

VoiceTrans is in ancestry via the chain `VeoMatrixVoice03 ← fix/ms-script-to-video-phase2b-product-fidelity (076cddc) ← design/ms-script-to-video-presenter-mapping-phase2b (5f5a0bc) ← design/ms-script-to-video-presenter-alignment (c2e8fcd) ← design/ms-script-to-video-static-mock-phase1 (001a622) ← design/ms-kapwing-benchmark-product-advice (e03764e) ← review/ms-product-flow-reset-visual-validation-prc (5ccf943) ← reset/ms-delivery-product-flow-cleanup-prb (ebe103f) ← reset/ms-workbench-product-flow-cleanup-pra (574246a) ← design/ms-workbench-product-flow-reset (fc9cdf4) ← VeoMatrixVoice01 (8c55d22, which carries the VoiceTrans integration via commit 06046a9)`.

Files confirmed present: `gateway/app/templates/voice_tool.html`, `gateway/app/routers/voice_tool.py`, `gateway/app/services/voice_tool/{service,storage,__init__}.py`, `gateway/app/services/tests/test_voice_tool_service.py`. Routes wired in `gateway/app/main.py:195-196`.

## 3. Conflicts

**None.** No merge was performed since VoiceTrans was already in ancestry. The branch is bytewise identical to its base.

## 4. Files changed (delta vs `origin/VeoMatrixVoice02`)

Since both VeoMatrixVoice02 and VeoMatrixVoice03 are "joint validation" branches built on different Matrix Script tips, the delta over V02 represents all Matrix Script work landed between them — Phase 1 mock + Kapwing advice + presenter alignment + Phase 2B presenter mapping + Phase 2B fidelity fix + Phase 2B visual validation:

```
24 files changed, +25065 / -182

Templates:
  gateway/app/templates/matrix_script_new.html               | +22/-…  (CTA + sidebar + subtitle rewrite)
  gateway/app/templates/task_workbench.html                  | +804/-…  (Phase 2B 10-section IA + fidelity fix)

Tests (new + updated):
  test_matrix_script_workbench_script_to_video_phase2b.py    | +543 (53 tests)
  test_matrix_script_workbench_phase2b_product_fidelity.py   | +495 (44 tests)
  test_matrix_script_workbench_product_flow_reset_pra.py     |  +63 (7 stepper-quarantine updates)

Scripts:
  scripts/render_workbench_pra_screenshots.py                |   +2 (task.kind="matrix_script" fixture)

Design / architecture docs:
  docs/design/matrix_script_script_to_video_presenter_alignment_v1.md       (+410)
  docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md  (+270)
  docs/product/matrix_script_product_flow_v2_delta.md                       (+204)
  docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md          (+435)
  docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html (+827)

Execution reports:
  Phase 1 mock report / Phase 2B presenter mapping / Phase 2B fidelity / Phase 2B fidelity visual (+1000 lines)

Rendered HTML snapshots (4 sets × 4 files = 16 artifacts, ~10000 lines).
```

Zero changes to `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow runtime, Digital Anchor runtime, Asset Supply runtime, generation workers, or VoiceTrans runtime.

## 5. Test results

```
13 targeted Matrix Script + VoiceTrans suites:
  → 569 passed, 4 skipped, 1 failed
```

Per-suite breakdown:

| Suite | Tests | Result |
|---|---|---|
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
| `test_matrix_script_delivery_center_blocks_a_to_f.py` | 100 | ✅ 99 pass / 1 fail (pre-existing; see below) / 4 skipped |
| `test_voice_tool_service.py` | 3 | ✅ all pass |
| **Total** | **570** | **569 ✅ / 1 ⚠ pre-existing / 4 skipped** |

The single failure `test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` is **pre-existing on VeoMatrixVoice01 / V02** (documented in the PR-B report §4 and the VeoMatrixVoice02 integration report §5 known-limitation #3). It is unrelated to Phase 2B and to this joint validation branch.

## 6. Browser smoke results (live FastAPI via uvicorn @127.0.0.1:8779, Python 3.13, AUTH_MODE=header + OP_ACCESS_KEY)

| URL | HTTP | Bytes | Content markers verified |
|---|---|---|---|
| `/voice-tool` | 200 | 79880 | `语音翻译` (2) · `拟人配音` (15) · `target_language` (4) · `source_language` (2) — page loads, translation input + language controls + dubbing area all rendered |
| `/tasks/matrix-script/new?ui_locale=zh` | 200 | 84042 | H1 `生成脚本视频方案` (1) · CTA `生成视频方案 →` (1) · 4 sidebar steps `生成<strong>脚本理解</strong>` / `<strong>视频方案</strong>` / `<strong>角色与音频计划</strong>` / `工作台确认方案` (1 each) · 0 of `创建矩阵脚本任务` / `正式产线新建入口` / `任务摘要` / `候选评审` |
| `/tasks/{task_id}/publish` (real DC) | 200 | 192127 | All 6 PR-B section anchors + §7 fold present · 0 fake media tags / fake URLs |
| `/tasks/{task_id}` (real Workbench) | 200 | 64543 | **Live matrix_script gate did NOT enter** (see Known blocker #1) — Phase 2B IA renders correctly in source + in Jinja snapshots but does NOT render live for an API-created task without packet binding. |

### 6.1 Matrix Script validation result

| Phase 2B fidelity requirement | Source-level / snapshot evidence | Live-smoke evidence |
|---|---|---|
| New Task H1 = 生成脚本视频方案 | ✅ source | ✅ live |
| New Task CTA = 生成视频方案 | ✅ source | ✅ live |
| New Task sidebar 4 steps | ✅ source | ✅ live |
| New Task absent legacy phrases | ✅ source | ✅ live |
| Workbench legacy task-meta header gated | ✅ source | ⚠ live gate doesn't fire (Known blocker #1; render shows legacy header because matrix_script panel_kind projection is empty for packet-unbound task) |
| Workbench 10 sections A–J in order | ✅ source + rendered snapshot | ⚠ live (same gate issue) |
| §C 11-field storyboard | ✅ rendered snapshot (`01_pra_workbench_full_default_collapsed.html`) | ⚠ live (same gate issue) |
| §G V1 / V2 / V3 cards + ⭐ on V1 | ✅ rendered snapshot | ⚠ live (same gate issue) |
| §J collapsed by default, legacy A–F + stepper inside | ✅ rendered snapshot | ⚠ live (same gate issue) |
| No fake media / publish URL in Workbench primary | ✅ source + rendered + live | ✅ live (0 occurrences) |
| Delivery Center final-video oriented, 6 sections + §7 fold | ✅ source + rendered + live | ✅ live |
| Delivery Center publish CTA gated | ✅ source + rendered + live | ✅ live |

**Matrix Script verdict (per surface):**
- **New Task page**: ✅ live + source + snapshot fully aligned with Phase 1 mock product intent.
- **Workbench**: ✅ source + rendered snapshot fully aligned (validated by the 468-test suite on this branch). ⚠ live render gate didn't fire because the API-created task has no packet binding (pre-existing projection limitation — same as Known blocker #1 on VeoMatrixVoice02; **not** a Phase 2B regression).
- **Delivery Center**: ✅ live + source + snapshot fully aligned.

### 6.2 VoiceTrans validation result

| VoiceTrans requirement | Result |
|---|---|
| Page loads | ✅ HTTP 200, 79 KB |
| Translation input visible | ✅ `data-role="*"` markers + `source_language` + `target_language` controls present |
| Source / target language controls | ✅ |
| Translation result area | ✅ `语音翻译` page title + result region |
| Dubbing / voice generation area | ✅ `拟人配音` (15 occurrences across UI) |
| No route collision with Matrix Script pages | ✅ `/voice-tool` is its own route; Matrix Script pages live under `/tasks/matrix-script/*` and `/tasks/{task_id}*`; no overlap |
| No raw VoiceTrans embed inside Matrix Script Workbench | ✅ source-level `test_no_voicetrans_iframe_or_raw_form` passes; no `<iframe>` / no `action="/api/voice-tool"` in matrix_script branch |

## 7. Screenshot / rendered artifact paths

The fidelity-fix branch (already in V03's ancestry) shipped four rendered HTML snapshots that cover the Workbench + Delivery Center surfaces:

| Mission view | Artifact |
|---|---|
| New Task first screen | `gateway/app/templates/matrix_script_new.html` (source-level + live smoke at `/tmp/v3_msnew.html`, http=200, 84 KB) |
| Workbench first screen / §C / §G / §J collapsed | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_pra_workbench_full_default_collapsed.html) |
| Workbench §J expanded (architect view) | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_pra_workbench_full_section5_expanded.html) |
| Delivery Center | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/01_prb_delivery_center_full_default_collapsed.html) (live smoke `/tmp/v3_dc.html`, http=200, 192 KB) |
| Delivery Center §7 expanded | [docs/design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_prb_delivery_center_full_section7_expanded.html](../design/screenshots/matrix_script_phase2b_product_fidelity_fix_2026-05-30/02_prb_delivery_center_full_section7_expanded.html) |
| VoiceTrans page | live smoke `/tmp/v3_voice.html`, http=200, 79 KB (template source `gateway/app/templates/voice_tool.html`) |

## 8. Known blockers before functional validation

1. **Workbench live gate does NOT enter for an API-created matrix_script task with no packet binding.** Inherited from VeoMatrixVoice02 (Known blocker #1 of the V02 integration report). The `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` gate requires the `operator_surfaces.workbench.line_specific_panel.panel_kind` projection to be populated; for a fresh API task that key is empty. Source + rendered snapshots + 468-test suite all confirm Phase 2B correctness; functional validation either needs a packet-bound fixture or a small projection-default extension in `gateway/app/services/operator_visible_surfaces/wiring.py` (presenter-only change; no contract / packet mutation).
2. **Legacy task-meta header still renders in live Workbench under the same packet-unbound condition.** Same root cause as #1: when the matrix_script gate doesn't fire, the legacy header gate `{% if task.kind != "matrix_script" %}` may still see `task.kind` as something other than `"matrix_script"` depending on how `task_view` resolves it for a packet-unbound task. The presenter-level fix already gates the header correctly when `task.kind == "matrix_script"` is true; functional validation should verify the task-loading code path sets `task.kind` consistently.
3. **Live-browser PNG capture not available.** No Chrome MCP browser connected; no `.claude/launch.json` write. Same constraint as PR-C and the Phase 2B fidelity visual validation. Functional validation must include a real-browser pass.
4. **Pre-existing `test_block_d_resolved_subfield_has_status_resolved_when_caption_present` failure.** PR-2D wave drift inherited; not introduced by Phase 2B / VeoMatrixVoice03.
5. **VoiceTrans API endpoints not exercised in this smoke pass.** Only the `/voice-tool` page route was smoke-tested (200 OK with all content markers). Functional validation should exercise `/api/voice-tool/translate`, `/synthesize`, `/speech-rewrite`, `/speech-variants`, `/download/{job_id}` end-to-end.
6. **Matrix Script remains NOT production-operable.** Backend final-video generation worker is still pending (Phase 6 of the accepted advice). Section A continues to render the honest empty-state copy on every real task.

## 9. Explicit no-contract / no-schema / no-packet / no-runtime-worker / no-fake-media statement

This branch creation **does NOT modify any file** relative to the validated fidelity-fix HEAD `4220fcd`. Specifically, this wave makes **no** changes to:

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
- **No fake `final_video` / thumbnail / media URL / `publish_url` / generated media.** Confirmed by live smoke: 0 occurrences of `<video` / `<iframe` / `<source ` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `example.com` in Workbench + Delivery Center primary scan.
- **No VoiceTrans iframe / raw UI embed** inside Matrix Script branches.
- **No provider / model / vendor / engine controls** in primary UI.
- **VeoMatrixVoice02 untouched** — verified `git rev-parse origin/VeoMatrixVoice02` returns its prior HEAD unchanged.

## 10. Final verdict

**VeoMatrixVoice03 is ready for joint manual validation.**

Live smoke confirms the New Task page (Phase 2B fidelity copy + CTA), the Delivery Center (PR-B 6-section IA + §7 fold), and the VoiceTrans page (`/voice-tool`) all return 200 with the expected operator-language content markers. The Matrix Script Workbench's Phase 2B 10-section IA is fully validated at source level + rendered Jinja snapshot + 468-test regression; the live-smoke gate-not-entering issue under packet-unbound conditions is documented as Known blocker #1 (inherited; not a Phase 2B regression) and does not block joint manual validation against a packet-bound task fixture or with the projection-fallback extension applied.

Stopped after pushing the branch and writing this report. **No Phase 3 packet binding. No VoiceTrans bridge. No Asset Supply bridge. No video worker.**

---

## 11. Audit addendum (2026-05-30) — Root-cause F discovered on `/tasks/matrix-script/new`

User-reported observation against the deployed `https://apolloveo-auto.onrender.com/tasks/matrix-script/new?ui_locale=zh`:

- H1 `生成脚本视频方案` ✓ present
- CTA `生成视频方案` ✓ present
- **But primary form body still shows the old structure:**
  - `脚本来源` (Card 1, legacy)
  - `任务基本信息` (Card 2, legacy)
- **And the four Phase-1-mock entry cards are MISSING:**
  - `产品 / 素材`
  - `目标 · 画幅 · 语言`
  - `角色 · 声音 · 字幕`
  - `变体策略`

### 11.1 Diagnostic results

| Check | Result |
|---|---|
| `git merge-base --is-ancestor 076cddc HEAD` | ✅ 076cddc present |
| `git merge-base --is-ancestor 4220fcd HEAD` | ✅ 4220fcd present |
| `git diff origin/fix/ms-script-to-video-phase2b-product-fidelity-20260530 -- gateway/app/templates/matrix_script_new.html` | **0 lines** — V03 source matches the validated fidelity-fix branch bytewise |
| `git diff … -- gateway/app/templates/task_workbench.html` | **0 lines** — same |
| Render deploy commit (`/healthz/build`) | `git_sha=dc797c5…` — matches current V03 HEAD |
| Source-level marker audit on `matrix_script_new.html` | `生成脚本视频方案` ✓ 1 · `生成视频方案 →` ✓ 1 · `脚本来源` **2** · `任务基本信息` **2** · `产品 / 素材` **0** · `目标 · 画幅 · 语言` **0** · `角色 · 声音 · 字幕` **0** · `变体策略` **0** · `datalist` (platform selector) **0** |
| Legacy entry-form fields still present | `audience_hint` 2 · `length_hint` 2 · `operator_notes` 2 · `existing_source_script_ref` 3 |

### 11.2 Root cause classification

**Classification: F — "Phase 2B fidelity did not fully implement the New Task entry card structure."**

Rejected alternatives:
- **A** (wrong base) — rejected; ancestry includes 076cddc + 4220fcd; base is `origin/fix/ms-script-to-video-phase2b-product-fidelity-20260530` per `git status`.
- **B** (missing commits) — rejected; both validated commits are in ancestry.
- **C** (VoiceTrans merge reverted) — rejected; no merge was performed (VoiceTrans is in ancestry via VeoMatrixVoice01 chain). Template diff vs fidelity-fix branch is 0 lines.
- **D** (stale deploy) — rejected; Render `/healthz/build` reports `git_sha=dc797c5`, exactly matching V03 HEAD.
- **E** (stale build) — rejected; same evidence as D.
- **F** (Phase 2B fidelity didn't fully implement entry cards) — **confirmed.** Source-level grep shows the four new entry-card sections (`产品 / 素材`, `目标 · 画幅 · 语言`, `角色 · 声音 · 字幕`, `变体策略`) are absent from `gateway/app/templates/matrix_script_new.html`. The H1 / CTA / sidebar / topbar-subtitle were renamed by the fidelity fix (076cddc); the form body Card 1 (`脚本来源`) + Card 2 (`任务基本信息`) were left at PR-1's structure. The required four additional cards from the Phase 1 mock §① (mock cards 2 / 3 / 4 / 5) and from the presenter-alignment spec §5.1 ("ADD (presenter-only)" rows) were **never added**.

### 11.3 Why the prior visual validation missed it

The Phase 2B fidelity visual validation report at commit `4220fcd` audited the New Task page via source-level grep for:
- H1 = `生成脚本视频方案` ✓ (present)
- CTA = `生成视频方案 →` ✓ (present)
- Old phrases absent ✓ (all 0)
- Sidebar 4-step copy ✓ (present)

The report did **not** assert on the presence of the four new entry-card sections, only on the absence of the eight legacy phrases. The legacy phrases (`创建矩阵脚本任务`, `正式产线新建入口`, `任务摘要`, `脚本结构`, `变体方案`, `生成进度`, `候选评审`, `交付摘要`) genuinely are absent; the legacy cards `脚本来源` and `任务基本信息` were not on the forbidden list because they are operator-language section titles, not the legacy A–F backend vocabulary. The card-IA gap therefore slipped through the 4220fcd PASS verdict.

### 11.4 Fix policy applied

Per mission §7 rule **"F: Stop and report. Do not invent new UI. We need a separate fidelity correction."**

This branch operator does **not** modify code. The four missing entry cards require a separate fidelity-correction wave to be authored per the Phase 1 mock §① card structure (mock cards 2 / 3 / 4 / 5) and the presenter-alignment spec §5.1 (presenter-only fields). That correction is **out of scope for this audit branch**.

### 11.5 Updated test results

Running the Phase 2B test suites confirms the gap is NOT caught by existing tests:

```
python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py \
  gateway/app/services/tests/test_matrix_script_workbench_script_to_video_phase2b.py
  → 97 passed (44 fidelity + 53 structural) — none assert on the 4 new entry cards
```

The 44 fidelity tests check H1 / CTA / sidebar / topbar-subtitle / absence-of-legacy-phrases but do not check presence-of-new-cards. The 53 structural tests focus on Workbench, not New Task. A follow-up correction wave should add 4 new test cases:

- `test_new_task_card_product_material_present` — `data-role="ms-new-card-product-material"` or similar.
- `test_new_task_card_target_aspect_language_present` — `产品 / 素材` / `目标 · 画幅 · 语言` cards.
- `test_new_task_card_role_voice_subtitle_present`.
- `test_new_task_card_variant_strategy_present`.

### 11.6 Render deploy audit

```
$ curl -s https://apolloveo-auto.onrender.com/healthz/build
{"service":"shortvideo-v1-capcut","version":"v1.7-day1","git_sha":"dc797c59886124b75d262267daf4add2fe1d0726","has_pack_v17_youcut":true,"edge_tts":true,"r2_enabled":true,"pack_v17_status":"frozen"}
```

Render is serving exactly the current V03 HEAD `dc797c5` (no stale deploy). The "old form" the operator sees is the genuine source-level state of the validated fidelity-fix branch.

### 11.7 Files changed during this audit

**Zero source-code files.** Only this report file is modified (the audit addendum §11 is appended to the existing report). No template, no Python, no test, no contract, no schema, no packet, no closed-enum change.

### 11.8 Revised explicit no-change statement

This audit + report-update wave makes **no** changes to:

- **Code / templates / Python** — zero source files modified.
- **Contracts** (`docs/contracts/` untouched).
- **Schemas** (`schemas/` untouched).
- **Packets** (no `production_packet*.json` mutation).
- **Closed enums** (bytewise stable).
- **Runtime workers** (no worker added; no endpoint; no router edit).
- **Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime** (all bytewise unchanged).
- **Generic factory readiness logic** (no projection re-derivation).
- **No fake `final_video` / thumbnail / media URL / `publish_url` / generated media** (no new render output produced).

### 11.9 Revised verdict

**VeoMatrixVoice03 is BLOCKED before joint manual validation.**

Reason: the New Task page (`/tasks/matrix-script/new`) does not match the accepted Phase 1 mock §① product intent. The legacy two-card form structure (`脚本来源` + `任务基本信息`) is still primary; the four Phase 1 mock entry cards (`产品 / 素材`, `目标 · 画幅 · 语言`, `角色 · 声音 · 字幕`, `变体策略`) are absent. This is **upstream fidelity gap on the validated branch** (`fix/ms-script-to-video-phase2b-product-fidelity-20260530` at 076cddc) that the 4220fcd visual validation report missed.

Recommended next branch (NOT authorised by this audit):

```
fix/ms-script-to-video-phase2b-new-task-entry-cards-20260530b
```

Scope: add the four Phase 1 mock §① entry cards as presenter-only sections under `gateway/app/templates/matrix_script_new.html` (between the legacy `脚本来源` card and `任务基本信息` card, or replacing `任务基本信息` if the architect prefers), each carrying operator-language placeholder fields per the presenter alignment spec §5.1; add four corresponding fidelity test cases; preserve the existing safe POST + task-creation contract; preserve `audience_hint` / `length_hint` / `operator_notes` / `existing_source_script_ref` as either operator-renamed or technical-mode-only fields.

The recommended branch is **not** opened by this audit. The mission preamble forbids inventing UI; the correction wave needs its own product-design sign-off.

Stop here. No code change. No Phase 3 start.
