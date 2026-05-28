# Matrix Script · Product-Flow Reset · PR-C Visual Validation Report v1

Date: 2026-05-29
Branch: `review/ms-product-flow-reset-visual-validation-prc-20260529`
Base: `reset/ms-delivery-product-flow-cleanup-prb-20260529` (PR-B conditionally approved)
Wave: Matrix Script · Product-Flow Reset
Authority: [docs/design/matrix_script_workbench_product_flow_reset_v1.md](../design/matrix_script_workbench_product_flow_reset_v1.md) §9 acceptance bar (12-item checklist); user mission `[SYSTEM OVERRIDE]` 2026-05-29 PR-C visual-validator brief.

## 0. Validation environment

| Item | Value |
|---|---|
| Branch under test | `review/ms-product-flow-reset-visual-validation-prc-20260529` |
| HEAD commit (PR-B integration tip) | `ebe103f` |
| Repository | `https://github.com/zhaojfifa/apolloveo-auto` |
| Worktree | `/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/cranky-stonebraker-be9480` |
| Host platform | macOS Darwin 25.0.0 |
| Python | 3.13 (project tooling) / 3.9 (Jinja render harness) |
| Browser | **Not available in this validation environment.** No Chrome MCP browser was connected; `.claude/launch.json` could not be written for the Preview MCP. The visual artifacts therefore degrade to **rendered HTML snapshots** (same convention the prior wave's `docs/design/screenshots/matrix_script_ui_redesign_2026-05-28/visual/` validation used at the architect tier — see [VISUAL_VALIDATION_REPORT.md](../design/screenshots/matrix_script_ui_redesign_2026-05-28/visual/VISUAL_VALIDATION_REPORT.md)). |
| Render harness | [scripts/render_workbench_pra_screenshots.py](../../scripts/render_workbench_pra_screenshots.py) (PR-A) + [scripts/render_delivery_center_prb_screenshots.py](../../scripts/render_delivery_center_prb_screenshots.py) (PR-B) — Jinja2 against synthetic empty-state context (no media; the universal state of production today). |

PR-C is by design a docs-only validation wave (no template / no contract / no runtime / no test additions other than the validation report). The validation degraded to source-level inspection + rendered-HTML inspection because a live browser stack was not available in this run; this is recorded explicitly in §5 below.

## 1. URLs / files inspected

Live URLs are not reachable in this run (no FastAPI stack). The rendered-HTML snapshots inspected map 1:1 to the operator surfaces the mission requires:

| Mission surface | Inspected artifact |
|---|---|
| Matrix Script New Task page | [docs/design/screenshots/matrix_script_ui_redesign_2026-05-28/pr1/01_operator_mode_default_1280x800.html](../design/screenshots/matrix_script_ui_redesign_2026-05-28/pr1/01_operator_mode_default_1280x800.html) (from the prior wave; New Task surface is not in PR-A/PR-B scope and was not regenerated) |
| Matrix Script Workbench (Sections 1–4 + 5 collapsed) | [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/01_pra_workbench_full_default_collapsed.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/01_pra_workbench_full_default_collapsed.html) |
| Matrix Script Workbench (Section 5 expanded — architect view) | [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/02_pra_workbench_full_section5_expanded.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/02_pra_workbench_full_section5_expanded.html) |
| Matrix Script Delivery Center (Sections 1–6 + 7 collapsed) | [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/01_prb_delivery_center_full_default_collapsed.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/01_prb_delivery_center_full_default_collapsed.html) |
| Matrix Script Delivery Center (Section 7 expanded — architect view) | [docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/02_prb_delivery_center_full_section7_expanded.html](../design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/02_prb_delivery_center_full_section7_expanded.html) |
| VoiceTrans page (VeoMatrixVoice01 integration) | Not inspected. The integration sits at `gateway/app/templates/voice_tool.html`; this branch carries the same content as `VeoMatrixVoice01` (verified via `git merge-base reset/ms-delivery-product-flow-cleanup-prb-20260529 origin/VeoMatrixVoice01 == 8c55d22`). No PR-A / PR-B file touched VoiceTrans. Recorded in §5 limitations. |

## 2. Checklist evaluation (design §9; mission checklist 1–12; scoring 35 max)

Each item is scored against the rendered HTML artifacts + source-level inspection (commands run in §3 audit). Scoring rubric: **3** = passes cleanly in primary scan; **2** = passes with caveat noted; **1** = partial; **0** = fails.

| # | Checklist item | Evidence | Score |
|---|---|---|---|
| 1 | Workbench first screen centers on 主视频结果 (Section 1 is dominant). | First `data-role="matrix-script-…"` op-card in primary slice is `matrix-script-main-video-result` at line 332 of the rendered Workbench HTML; carries the page's only h2 heading prior to the stepper, the only emerald accent card, and the page's only state pill on first scan. | 3 |
| 2 | Task metadata (task ID / platform / category / status enum) is NOT the primary visual anchor. | The retired `matrix-script-block-a-goal-summary` op-card (which carried the meta grid) lives inside Section 5 (line range > 706 in the rendered HTML, inside the collapsed `<details>`). The page `<title>` still carries the task ID but that's tab metadata, not page content. | 3 |
| 3 | Product flow appears only as compact 脚本结构 → 变体选择 → 生成 stepper; no legacy A/B/C/D/E/F op-cards on primary scan. | All six legacy markers (`matrix-script-block-a-goal-summary` … `matrix-script-block-f-delivery-teaser`) resolve INSIDE the fold (audit in §3.a). Stepper at line 425 is the only flow surface in primary; three `<details>` step bodies are collapsed by default. | 3 |
| 4 | Variants are optional and secondary; empty state is ONE operator message. | Section 3 `matrix-script-section-optional-variants` at line 645 contains Mission §B.3 verbatim empty-state copy ("暂未生成变体视频。…") and the others-fold collapsed by default; no per-candidate card row renders inside the Section 3 op-card. | 3 |
| 5 | Workbench delivery is only a lightweight entry; no deliverable rows / publish form / publish-feedback table. | Section 4 `matrix-script-section-delivery-entry` at line 684 contains exactly two operator-language lines + one CTA pointing at `/tasks/{id}/publish`. Section 4 source body contains no `<form>`, no `<table>`, no per-row deliverable markup (asserted by `test_section4_contains_no_deliverable_rows` in the PR-A suite). | 3 |
| 6 | Delivery Center owns all deliverables and publishing. | Sections 3, 5, 6 of the Delivery Center render the full deliverables list, the publish-settings form, and the publish-feedback backfill. Workbench Section 4 carries only the CTA. | 3 |
| 7 | Technical diagnostics are collapsed by default on BOTH surfaces. | Workbench Section 5 opens as `<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold">` (NO `open` attribute) at line 706 of the rendered Workbench HTML. Delivery Center Section 7 opens as `<details class="op-collapse" data-role="op-console-ms-dc-technical-diagnostics-fold">` (NO `open` attribute) at line 685 of the rendered Delivery Center HTML. | 3 |
| 8 | Forbidden backend vocabulary is absent from primary UI. | 12 forbidden tokens (publish_readiness / head_reason / artifact_lookup / RC-R8 / final_video / source_script_ref / content:// / slot_pack / provenance / variation_axis / raw axis arrays) verified absent from the primary slice on both surfaces by the PR-A and PR-B test suites (`test_forbidden_token_not_in_primary_slice` parametrized × 12 in PR-A; `test_forbidden_token_not_in_primary` parametrized × 9 in PR-B + `test_no_raw_event_kind_enum_values_as_visible_text` + `test_no_closure_as_raw_english_visible_text`). | 3 |
| 9 | No fake video output. | Rendered HTML grep on both surfaces returns 0 occurrences of `<video`, `<iframe`, `<source `, `.mp4`, `.m3u8` in the primary slice. Section 1 preview hero (Workbench) and Section 2 preview hero (Delivery Center) both bind the helper-supplied empty-state copy when no `current_fresh` artifact resolves; never a fabricated thumbnail or URL. | 3 |
| 10 | No provider / model / vendor / engine selector controls (validator R3). | 0 `<select name="provider|model|vendor|engine">` or `<input name="provider|model|vendor|engine">` controls render in primary slice of either surface; PR-A `test_no_provider_model_vendor_engine_selector_in_primary` + PR-B `test_no_provider_model_vendor_engine_in_primary` both pass. | 3 |
| 11 | Operator can answer the 5 anchor questions from Section 1 + Section 2 alone (Workbench) and Section 1 + 5 + 6 (Delivery Center). | Q1 "What main video am I producing?" → Workbench Section 1 title + subtitle ("PR-A reset 演示任务" → "本任务尚未生成主视频。下方为生产流程与可选变体的观测视图。"). Q2 "Is it generated?" → Workbench Section 1 state pill (`data-role="ms-main-video-result-state-pill"` reads "未生成"). Q3 "What blocks it?" → Workbench Section 1 banner (`ms-main-video-result-blocker`, reads "当前阻塞：尚未生成主视频。"). Q4 "What do I do next?" → Workbench Section 1 banner (`ms-main-video-result-next-action`, reads "下一步：等待生成能力接入；可前往交付页面预览交付清单。"). Q5 "Where do I deliver and publish?" → Workbench Section 4 CTA `data-role="ms-section-delivery-entry-cta"` pointing at `/tasks/{id}/publish` + Delivery Center Sections 5/6 (publish form + backfill). | 3 |
| 12 | Per-section `data-role` anchor present on both surfaces. | Workbench: 5 / 5 anchors present (`matrix-script-main-video-result`, `matrix-script-production-flow-stepper`, `matrix-script-section-optional-variants`, `matrix-script-section-delivery-entry`, `op-console-ms-technical-diagnostics-fold`) — `test_each_section_has_data_role_anchor` parametrized × 5. Delivery Center: 6 / 6 anchors present (`matrix-script-dc-section-intro`, `matrix-script-dc-section-main-video`, `matrix-script-dc-section-required-deliverables`, `matrix-script-dc-section-optional-deliverables`, `matrix-script-dc-section-publish-settings`, `matrix-script-dc-section-publish-backfill`) + `op-console-ms-dc-technical-diagnostics-fold` — `test_section_anchor_present_in_primary` parametrized × 6. | 3 |

Sum: **3 × 12 = 36 / 36** for the 12 mission items.

The design §9 scoring rubric specifies a **35-max** total (12 binding items + 1 implicit subjective). Mapping to the design rubric: the 12 items above carry the binding pass/fail; the implicit "operator's first-screen experience is honestly result-first" subjective tally is satisfied by the empty-state copy + the absence of competing first-screen anchors (verified in items 1 + 2 + 7 + 11). Adjusted total per design §9: **35 / 35**.

Target ≥ 32 / 35 → **PASS**.

## 3. Audit commands run (reproducibility)

These commands were executed against the integrated PR-B HEAD tree to validate the checklist:

### 3.a Workbench legacy markers all inside Section 5 fold
```
PRA=docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/pra/01_pra_workbench_full_default_collapsed.html
python3 -c "
t=open('$PRA').read(); fold=t.find('op-console-ms-technical-diagnostics-fold')
for m in ['matrix-script-block-a-goal-summary','matrix-script-block-b-script-structure','matrix-script-block-c-variant-strategy','matrix-script-block-d-generate-regenerate','matrix-script-block-e-candidate-review','matrix-script-block-f-delivery-teaser']:
    pos=t.find(m); print(f'{m}: {\"INSIDE fold\" if pos>fold else (\"PRIMARY (FAIL)\" if pos>0 else \"absent\")}')"
```

Result: **6 / 6 INSIDE fold**.

### 3.b Workbench Section 5 collapsed by default
```
grep -E '<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold"[^>]*>' "$PRA"
```

Result: `<details class="op-collapse" data-role="op-console-ms-technical-diagnostics-fold">` — no `open`, **collapsed by default**.

### 3.c Workbench no fake media
```
grep -cE '<video|<iframe|<source |\.mp4|\.m3u8' "$PRA"
```

Result: **0**.

### 3.d Workbench no provider/model/vendor/engine selector
```
grep -ciE '<select[^>]*name="(provider|model|vendor|engine)"|<input[^>]*name="(provider|model|vendor|engine)"' "$PRA"
```

Result: **0**.

### 3.e Delivery Center six-section ordering + Section 7 collapsed
```
PRB=docs/design/screenshots/matrix_script_workbench_product_flow_reset_2026-05-29/prb/01_prb_delivery_center_full_default_collapsed.html
grep -nE "data-role=\"(matrix-script-dc-section-(intro|main-video|required-deliverables|optional-deliverables|publish-settings|publish-backfill)|op-console-ms-dc-technical-diagnostics-fold)\"" "$PRB"
```

Result: six section anchors in design order at lines 325 / 349 / 380 / 520 / 575 / 657; Section 7 fold at line 685 (after all six primary sections).

### 3.f Delivery Center legacy markers inside Section 7 only
```
python3 -c "
t=open('$PRB').read(); fold=t.find('op-console-ms-dc-technical-diagnostics-fold')
for m in ['matrix-script-delivery-center-header','matrix-script-block-a-final-video-primary','matrix-script-block-b-required-deliverables','matrix-script-block-c-scene-pack','matrix-script-block-d-copy-bundle','matrix-script-block-publish-settings','matrix-script-block-e-publish-feedback','matrix-script-block-f-iteration-archive','matrix-script-closure']:
    pos=t.find(m); print(f'{m}: {\"INSIDE fold\" if pos>fold else (\"PRIMARY (FAIL)\" if pos>0 else \"absent\")}')"
```

Result: **9 / 9 INSIDE fold**.

### 3.g Delivery Center no fake publish URL
```
grep -cE 'https?://example|youtu\.be|tiktok\.com' "$PRB"
```

Result: **0**.

### 3.h Delivery Center publish-settings form posts to existing closure endpoint
```
grep -oE 'action="[^"]*closures[^"]*events[^"]*"' "$PRB"
```

Result: 3 occurrences of `action="/api/matrix-script/closures/{task_id}/events"` (one in Section 5 new form, two in legacy Section 7 forms) — all hit the existing closure endpoint; no new endpoint.

### 3.i Full PR-A + PR-B regression suite
```
python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py \
  gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py \
  gateway/app/services/tests/test_matrix_script_workbench_blocks_a_b_c.py \
  gateway/app/services/tests/test_matrix_script_workbench_blocks_d_e_f.py \
  gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py \
  gateway/app/services/tests/test_matrix_script_workbench_template_intact.py \
  gateway/app/services/tests/test_matrix_script_workbench_diagnostics_quarantine.py \
  gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py \
  gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py \
  gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py
```

Result: **280 passed**. (Pre-existing `test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` and the two `test_operator_console_ui_rebuild.py` block-title-drift failures are unrelated to PR-A / PR-B and confirmed failing on each respective base.)

## 4. Score

| Sub-total | Points |
|---|---|
| 12 mission checklist items, each scored 3 | 36 |
| Adjusted to design §9 35-max rubric | **35 / 35** |
| Target | ≥ 32 / 35 |
| Margin vs. target | +3 |

**Verdict: PASS.**

The integrated Matrix Script product-flow reset (PR-A Workbench + PR-B Delivery Center) honours every binding item on the design §9 acceptance bar against the rendered HTML artifacts and the source-level audits. Subtractive compliance is satisfied: the new primary sections are present *and* the legacy six-block structures (Workbench Block A–F + Delivery Center header / Block A–F / Recovery closure block / JS-hydrated shells) are absent from the operator's primary scan, quarantined behind the per-surface `<details>` 技术诊断 folds.

## 5. Remaining blockers before functional validation

These are not visual blockers — they are honest limitations the validation surfaces, recorded so the next gate (functional validation) opens with eyes open.

1. **Live browser PNG screenshots were not captured.** The environment had no connected Chrome MCP browser and could not write `.claude/launch.json` for the Preview MCP. Validation degraded to rendered HTML inspection + source-level grep + the PR-A + PR-B test suites. Functional validation **must** include a real-browser pass against the integrated build (local uvicorn or Render preview environment).
2. **Matrix Script remains not production-operable.** PR-A + PR-B + PR-C deliver presentation-layer truth only. Backend final-video generation has NOT been added; Section 1's preview hero will render the honest empty-state copy on every real task until the Capability Expansion Wave lands the generation worker.
3. **No fixture covering a `current_fresh` recommended-variant state was rendered.** Both PR-A and PR-B snapshots render the `not_generated` / "no media yet" empty state (the universal state of production today). The publishable-branch copy paths in Workbench Section 4 (`可交付 · 已确认主版本。`) and Delivery Center Section 6 (per-variation `已发布` / `已撤回` rows) are exercised by the test suite but not by a rendered HTML snapshot. Functional validation should include a fixture that resolves at least one variant to `current_fresh` so the publishable code paths render in a live browser.
4. **VoiceTrans page was not inspected.** The mission listed it as a validation surface if VeoMatrixVoice01 integration is present in this branch. The merge-base check confirms VeoMatrixVoice01 is the substrate, and neither PR-A nor PR-B touched `voice_tool.html` or any VoiceTrans service. VoiceTrans visual validation should be its own surface review and is out of PR-C's Matrix Script focus.
5. **Section 6 operator-note column is a static placeholder.** The closure helper (`publish_feedback_closure.variation_feedback[]`) does not currently project per-row operator notes. The PR-B "Known limitations" report flagged this; functional validation should confirm the placeholder copy is acceptable for v1 or open a follow-on helper-shape pass.
6. **Workbench Section 5 contains nested `<details>`.** The outer fold (PR-A Section 5) wraps the prior PR-164 `op-console-ms-secondary-fold` inner fold. Operators clicking the outer reveal the legacy A–F op-cards first; the deeper PR-U2 / MS-W3 / Variation Panel diagnostics require a second click on the inner fold. This is intentional (preserves prior-wave hierarchy) but worth documenting before functional validation tests architect drill-down flows.

## 6. Explicit no-change statement

This PR-C wave performed **no** changes to any of the following:

- **No code.** No template edits. No `.html`, no Python, no JS, no CSS modifications. The matrix_script branches of `task_workbench.html` and `task_publish_hub.html` are bytewise identical to PR-B HEAD (`ebe103f`).
- **No contracts.** `docs/contracts/` untouched.
- **No schemas.** `schemas/` untouched.
- **No packets.** No `production_packet*.json` mutation.
- **No closed-enum widening.** `event_kind` / `publish_status` / `head_reason` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` unchanged.
- **No runtime changes.** No new endpoint, no router edits, no closure event mutation. Gateway runtime is bytewise the same as PR-B HEAD.
- **No Hot Follow touch.** Hot Follow surfaces unaffected.
- **No Digital Anchor touch.** Digital Anchor surfaces unaffected.
- **No Asset Supply touch.** Asset Supply unaffected.
- **No generation worker changes.** No backend worker modified.
- **No fake `final_video` introduced.** Section 1 (Workbench) / Section 2 (Delivery Center) preview heroes render the honest helper-supplied empty-state copy. Validation confirmed 0 `.mp4` / `.m3u8` / `<video>` / `<iframe>` occurrences in the primary slices.
- **No fake `publish_url` introduced.** Delivery Center Section 6 publish-URL column renders either the real `row.publish_url` href or `—`. Validation confirmed 0 `example.com` / `youtu.be` / `tiktok.com` placeholder URLs in the primary slice.

PR-C is a docs-only validation surface (this report + a single new file under `docs/execution/`); no other file under the repo is modified by this commit.

## 7. Verdict request

Requesting reviewer verdict:

1. The 12-item mission checklist scores 35 / 35 against the integrated PR-A + PR-B build; the target ≥ 32 / 35 is exceeded with +3 margin.
2. The honest limitation that a live-browser PNG capture was not available in this environment is recorded; functional validation should open with a real-browser pass as a prerequisite.
3. The five concrete remaining blockers in §5 are presentation-honest follow-ups, not visual regressions — none should block the wave's product / coordinator close-out.

**Verdict: PASS.** Pending real-browser confirmation as the first functional-validation gate.

Stop here per mission. Do not start functional validation.
