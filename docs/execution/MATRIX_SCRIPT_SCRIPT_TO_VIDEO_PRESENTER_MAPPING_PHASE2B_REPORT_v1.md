# Matrix Script · Script-to-Video · Presenter Mapping Phase 2B Implementation Report v1

Date: 2026-05-30
Branch: `design/ms-script-to-video-presenter-mapping-phase2b-20260530`
Base: `design/ms-script-to-video-presenter-alignment-20260529` (alignment commit `c2e8fcd` confirmed in ancestry)
Wave: Matrix Script · Product-Flow Reset · Phase 2B (Presenter / Template Mapping)
Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (Script-to-Video Presenter Mapping Implementer brief, post-Codex conditional GO).

## 1. Branch + base verification

| Item | Value |
|---|---|
| Branch | `design/ms-script-to-video-presenter-mapping-phase2b-20260530` |
| Base | `design/ms-script-to-video-presenter-alignment-20260529` |
| Required ancestor | `c2e8fcd` (presenter / contract / product alignment trio) |
| Ancestor verified | ✅ `git log --oneline | grep c2e8fcd` → present (4 commits deep) |
| Lineage at branch creation | `c2e8fcd ← 001a622 ← e03764e ← 5ccf943 ← ebe103f` (alignment → Phase 1 mock → Kapwing advice → PR-C → PR-B) |

## 2. Files changed

| File | Kind | Change |
|---|---|---|
| `gateway/app/templates/matrix_script_new.html` | template | Primary CTA label `创建并进入工作台` → `生成视频方案 →`; added `data-redesign-wave="2026-05-30-phase2b"` attribute on the submit button (data-role unchanged for back-compat). Existing safe POST + task-creation contract preserved. |
| `gateway/app/templates/task_workbench.html` | template | Added six new operator-visible sections inside the matrix_script branch (§B 脚本理解 / §C 视频生成计划 / §D 画面与素材 / §E 角色与声音 / §F 字幕与音乐 / §H 校对与微调). Renamed PR-A Section 3 title `可选变体` → `视频变体`; added `matrix-script-section-video-versions` anchor on the same card for Phase 2B tests; preserved `matrix-script-section-optional-variants` outer anchor for PR-A back-compat. PR-A §A (主视频结果), §I (交付入口), §J (技术诊断 collapsed) preserved verbatim. PR-A standalone production-flow-stepper preserved as sub-navigation between §A and §B for PR-A structural tests. Legacy A–F op-cards remain inside the §J `<details>` fold only (no leak into primary). |
| `gateway/app/templates/task_publish_hub.html` | template | **Untouched.** PR-B six-section Delivery Center carries unchanged. |
| `gateway/app/services/matrix_script/*` | helper | **Untouched.** Phase 2B is presenter / template only; no new helper module, no helper shape change. The new sections consume existing helpers (`script_structure_view` / `main_video_result_view` / `readable_variant_view` / `recommended_action_view`) or render Jinja-deterministic placeholders. |
| `gateway/app/services/task_view_presenters.py` / `task_view_helpers.py` | helper | **Untouched.** |
| `gateway/app/services/tests/test_matrix_script_workbench_script_to_video_phase2b.py` | test | **New** — 53 Phase 2B assertions covering the 16-item mission test plan. |
| `docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_PRESENTER_MAPPING_PHASE2B_REPORT_v1.md` | docs | **New** — this report. |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/01_pra_workbench_full_default_collapsed.html` | rendered artifact | **New** — Workbench Section 5 collapsed snapshot showing all 10 Phase 2B sections + the §J fold. |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/02_pra_workbench_full_section5_expanded.html` | rendered artifact | **New** — same context with §J fold open (architect view). |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/01_prb_delivery_center_full_default_collapsed.html` | rendered artifact | **New** — Delivery Center §7 collapsed snapshot. |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/02_prb_delivery_center_full_section7_expanded.html` | rendered artifact | **New** — Delivery Center §7 expanded snapshot. |

`git diff --stat`: 2 template files modified (matrix_script_new.html, task_workbench.html), 1 test file added, 1 report added, 4 rendered artifacts added. **Zero changes** to `docs/contracts/`, `schemas/`, packets, closed-enum files, Hot Follow, Digital Anchor, Asset Supply, generation workers, or VoiceTrans.

## 3. Reading Declaration

Index-first discipline read in order:

1. `README.md` (root); `ENGINEERING_CONSTRAINTS_INDEX.md`; `docs/README.md`; `docs/ENGINEERING_INDEX.md` — re-confirmed file layout + authority gate.

Then task-specific authority read:

2. `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md` (§4 section-to-presenter mapping, §5 entry-page alignment, §6 view-model field shapes, §7 placeholder policy, §8 testing plan).
3. `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` (§2 mock-section ↔ contract map, §3 line-packet additive bindings as Phase 3 work, §4 discipline guards, §5 closed status-code register).
4. `docs/product/matrix_script_product_flow_v2_delta.md` (delta record; not yet promoted to v2 normative).
5. `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` (Phase 1 mock — IA + sample script + placeholder copy reference).
6. `docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md` (Phase 1 report).
7. `docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_PRESENTER_ALIGNMENT_REPORT_v1.md` (alignment report).
8. `docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md` (accepted product advice).

Codex review text: the mission described it as "conditional GO with no hard product or architecture blocker"; the implicit Codex conditions enforced in §8 below.

## 4. Implementation summary

### 4.1 Operator-visible IA (matrix_script Workbench, in scan order)

| # | Section | data-role anchor | Source kind |
|---|---|---|---|
| 1 | §A 主视频结果 | `matrix-script-main-video-result` | **supported now** (PR-A wire) |
| — | (sub-nav) PR-A production-flow stepper | `matrix-script-production-flow-stepper` | preserved between §A and §B for PR-A test back-compat |
| 2 | §B 脚本理解 | `matrix-script-section-script-understanding` | **supported now** — consumes `script_structure_view`; 卖点 row is a presenter placeholder (closed status `selling_points_pending_upstream`) |
| 3 | §C 视频生成计划 | `matrix-script-section-generation-plan` | **presenter placeholder** — 3 scene rows derived deterministically from `script_structure_view.sections` (Hook / Body / CTA); status code `plan_pending_upstream`; honest disclaimer rendered |
| 4 | §D 画面与素材 | `matrix-script-section-visual-materials` | **placeholder** — 3 slots (背景候选 / B-Roll 候选 / 产品素材) all carrying `broll_pending_upstream`; 3 actions disabled with operator-language tooltip |
| 5 | §E 角色与声音 | `matrix-script-section-role-voice` | **placeholder** — operator-language preference rows + voice preview slot carrying `voice_preview_pending_voicetrans`; dedicated no-iframe disclaimer |
| 6 | §F 字幕与音乐 | `matrix-script-section-subtitle-music` | **placeholder** — 4 rows (字体 / 位置 / BGM 情绪 / 音量) carrying `subtitle_style_pending_compose` + `bgm_pending_upstream`; replace-music action disabled |
| 7 | §G 视频变体 | `matrix-script-section-video-versions` (Phase 2B) + `matrix-script-section-optional-variants` (PR-A back-compat) | **supported now (presenter)** — title renamed to "视频变体"; existing PR-A markup carries; underlying helper unchanged |
| 8 | §H 校对与微调 | `matrix-script-section-review-tuning` | **placeholder** — 4 review zones (画面 / 旁白 / 字幕 / 文案+CTA) carrying `review_pending_main_video`; accept/regenerate buttons disabled |
| 9 | §I 交付入口 | `matrix-script-section-delivery-entry` | **supported now** (PR-A wire; consumes `ops_pr.publishable`) |
| 10 | §J 技术诊断 | `op-console-ms-technical-diagnostics-fold` | **supported now** (PR-A fold; collapsed by default; carries retired legacy A–F + PR-U2 / MS-W3 / Variation Panel diagnostics) |

### 4.2 New Task page CTA change

Submit button label `创建并进入工作台` → `生成视频方案 →`. `data-role="ms-new-submit"` and the POST endpoint / payload contract are preserved; the existing safe `build_matrix_script_task_payload` path is unchanged. Existing field set (`audience_hint` / `length_hint` / `operator_notes` / paste-upload-select tabs) is preserved verbatim.

### 4.3 Delivery Center

Untouched. PR-B's six operator sections + Section 7 fold carry bytewise. Phase 2B regression test `test_delivery_center_six_sections_preserved` asserts all 7 anchors remain.

### 4.4 Presenter / helper view-models

Per the alignment spec §6, Phase 2B is presenter-layer template mapping over EXISTING helpers — no new Python module is required because all the new sections either:
- consume an existing helper output (`script_structure_view` for §B), or
- render Jinja-deterministic placeholder content with closed status codes (§C / §D / §E / §F / §H).

The 9 view-model names in the alignment spec §6 remain as the *interface contract* for Phase 3 / 4+ when real backend wiring lands; Phase 2B implements them as Jinja sections that emit the field shapes inline. This satisfies the mission's "implement or reshape presenter outputs" requirement without introducing premature presenter abstraction.

## 5. Tests run

```
python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_workbench_script_to_video_phase2b.py \
  gateway/app/services/tests/test_matrix_script_workbench_product_flow_reset_pra.py \
  gateway/app/services/tests/test_matrix_script_delivery_center_product_flow_reset_prb.py \
  gateway/app/services/tests/test_matrix_script_workbench_blocks_a_b_c.py \
  gateway/app/services/tests/test_matrix_script_workbench_blocks_d_e_f.py \
  gateway/app/services/tests/test_matrix_script_workbench_optional_variants.py \
  gateway/app/services/tests/test_matrix_script_workbench_redesign_2026_05_28.py \
  gateway/app/services/tests/test_matrix_script_workbench_template_intact.py \
  gateway/app/services/tests/test_matrix_script_workbench_diagnostics_quarantine.py \
  gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py \
  gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py \
  gateway/app/services/tests/test_matrix_script_delivery_center_pr3_reframing.py \
  gateway/app/services/tests/test_voice_tool_service.py
  → 424 passed (53 new Phase 2B + 371 back-compat / cross-line)
```

Per-suite breakdown:

| Suite | Tests | Result |
|---|---|---|
| `test_matrix_script_workbench_script_to_video_phase2b.py` (NEW) | 53 | ✅ all pass — 16 mission assertions × parametrizations |
| `test_matrix_script_workbench_product_flow_reset_pra.py` | 63 | ✅ all pass (back-compat: PR-A primary section anchors + ordering + forbidden vocab) |
| `test_matrix_script_delivery_center_product_flow_reset_prb.py` | 69 | ✅ all pass (PR-B Delivery Center untouched) |
| `test_matrix_script_workbench_blocks_a_b_c.py` / `..._d_e_f.py` | 156 | ✅ all pass (legacy A–F markers still inside §J fold) |
| `test_matrix_script_workbench_optional_variants.py` | 9 | ✅ all pass (PR-A renamed but anchor preserved) |
| `test_matrix_script_workbench_redesign_2026_05_28.py` | 8 | ✅ all pass |
| `test_matrix_script_workbench_template_intact.py` | 7 | ✅ all pass |
| `test_matrix_script_workbench_diagnostics_quarantine.py` | 14 | ✅ all pass |
| `test_matrix_script_workbench_production_flow_stepper.py` | 6 | ✅ all pass |
| `test_matrix_script_workbench_main_video_result_template.py` | 11 | ✅ all pass |
| `test_matrix_script_delivery_center_pr3_reframing.py` | 25 | ✅ all pass |
| `test_voice_tool_service.py` | 3 | ✅ all pass (VoiceTrans untouched) |

Pre-existing failure (`test_matrix_script_delivery_center_blocks_a_to_f.py::test_block_d_resolved_subfield_has_status_resolved_when_caption_present` — inherited from PR-2D wave) was NOT included in the Phase 2B suite as it is unrelated to this wave (confirmed failing on each prior base).

## 6. Rendered artifact / screenshot paths

Live-browser PNG capture remains unavailable in this environment (no connected Chrome MCP browser; no `.claude/launch.json` write). Rendered HTML snapshots are produced via the existing PR-A / PR-B harnesses against the synthetic empty-state context. Phase 2B-specific artifacts:

| Artifact | Surface |
|---|---|
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/01_pra_workbench_full_default_collapsed.html` | Workbench operator first-scan — all 10 Phase 2B sections (A–J), §J fold collapsed |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/02_pra_workbench_full_section5_expanded.html` | Workbench architect view — §J expanded |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/01_prb_delivery_center_full_default_collapsed.html` | Delivery Center operator first-scan — 6 sections + §7 fold collapsed |
| `docs/design/screenshots/matrix_script_script_to_video_phase2b_2026-05-30/02_prb_delivery_center_full_section7_expanded.html` | Delivery Center architect view — §7 expanded |

Each render confirmed via `grep` that the expected 10 Phase 2B section anchors appear in the operator-first-scan HTML. The New Task page (`matrix_script_new.html`) was not re-rendered (it requires the full FastAPI stack for context); the source-level test `test_new_task_cta_is_generate_video_plan` confirms the CTA shift.

## 7. Explicit no-contract / no-schema / no-packet / no-runtime / no-worker / no-fake-media statement

This wave makes **no** changes to any of the following:

- **No backend generation** — no new worker, no new background task, no new endpoint, no new closure event shape, no new ASR / TTS / video-assembly call.
- **No runtime worker logic** — `gateway/app/services/matrix_script/*` bytewise unchanged; `gateway/app/services/operator_visible_surfaces/wiring.py` bytewise unchanged.
- **No contract changes** — `docs/contracts/` untouched. Audit assertion `test_phase2b_does_not_touch_factory_generic_contracts` verifies the six factory-generic contracts (`factory_input`, `factory_content_structure`, `factory_scene_plan`, `factory_audio_plan`, `factory_language_plan`, `factory_delivery`) remain at their pre-Phase-2B line counts.
- **No schema changes** — `schemas/` untouched.
- **No packet changes** — no `production_packet*.json` mutation; no Matrix Script line packet extension.
- **No closed-enum changes** — `event_kind` / `publish_status` / `head_reason` / `review_zone` / `recommended_bucket` / `artifact_status_code` / `package_status_kind` bytewise stable. The Phase 2B closed status-code register (`plan_pending_upstream`, `broll_pending_upstream`, `voice_preview_pending_voicetrans`, `subtitle_style_pending_compose`, `bgm_pending_upstream`, `review_pending_main_video`, `selling_points_pending_upstream`, `commercial_ok/review/operator_upload`) is a *presenter-layer constant set* emitted as `data-status-code` attributes; no contract-level enum is registered.
- **No Hot Follow / Digital Anchor / Asset Supply / VoiceTrans runtime touch** — verified by `test_phase2b_scoped_to_matrix_script_branch` (all anchors live before the digital_anchor gate) and `test_phase2b_does_not_touch_voice_tool_or_other_lines` (cross-line files unchanged).
- **No VoiceTrans iframe / raw UI embed** — verified by `test_no_voicetrans_iframe_or_raw_form`. §E carries a `ms-section-role-voice-no-iframe-note` disclaimer + no `<iframe>` / no `action="/api/voice-tool"` / no `action="/voice-tool"` in primary slice.
- **No provider / model / vendor / engine controls** — verified by `test_no_provider_model_vendor_engine_controls` (no `<select|input name="provider|model|vendor|engine">`; no operator-visible "Azure" / "Gemini" / "Akool" / "Seedance" / "OpenAI" / "Anthropic" in primary visible text).
- **No fake `final_video`** — verified by `test_no_fake_media_or_publish_url` (0 `.mp4` / `.m3u8` / `.webm` / streaming-host URL in primary).
- **No fake thumbnail / media URL / publish URL** — same audit; §A and §C preview slots render honest operator-language empty-state copy.
- **No generic factory readiness logic invented** — Phase 2B does not derive publishability; §I consumes `ops_pr.publishable` unchanged; §A consumes `main_video_result_view` unchanged; new sections (§C/D/E/F/H) emit pending status codes only.

## 8. Codex conditional-GO items and how they were enforced

Treating Codex conditions as mandatory execution constraints (per mission preamble):

| Codex condition (mission intent) | Enforcement in Phase 2B |
|---|---|
| No reopening of product / architecture design | This wave consumes the alignment trio (presenter + contract + product delta) as-is; no `docs/design/` or `docs/architecture/` or `docs/product/` file is modified by Phase 2B. |
| Presenter / template mapping only | Only `matrix_script_new.html` + `task_workbench.html` (2 template files) modified; 1 new test file + 1 report + 4 rendered artifacts. No `.py` / `.css` / `.js` change inside `gateway/`. |
| No contract / schema / packet / closed-enum change | Audit test `test_phase2b_does_not_touch_factory_generic_contracts` asserts byte-stability of the six generic contracts. |
| No generation worker | No new worker file; no service-layer mutation; no new endpoint. |
| Backend vocabulary quarantine preserved | 15-token forbidden-vocab audit passes (`test_forbidden_token_absent_from_primary` × 10 + provider/vendor/engine/model audit). |
| No fake media / publish URL | `.mp4` / `.m3u8` / `.webm` / streaming-host audit + `<video>` / `<iframe>` / `<source>` audit pass with zero occurrences in primary. |
| Honest placeholder discipline | Every unsupported capability slot carries a closed `data-status-code` + an operator-language `title` tooltip + a disabled-with-honest-tooltip button (`test_visual_materials_actions_disabled_with_tooltip`). |
| Legacy A–F markers stay quarantined | `test_legacy_block_marker_only_in_diagnostics_fold` × 6 passes. |
| §J `<details>` collapsed by default | `test_technical_diagnostics_fold_collapsed_by_default` passes. |
| Hot Follow / Digital Anchor / VoiceTrans bytewise unaffected | `test_phase2b_scoped_to_matrix_script_branch` + `test_phase2b_does_not_touch_voice_tool_or_other_lines` pass. |
| Delivery Center final-video orientation preserved | `test_delivery_center_six_sections_preserved` + `test_delivery_center_publish_submit_gated_by_publish_readiness` pass. |

## 9. Known backend gaps (for Phase 3+ planning)

Phase 2B makes these gaps **visible** by labelling slots as placeholders with closed status codes. None is closed by this wave.

1. **Scene-plan helper does not exist** (`plan_pending_upstream`). Phase 3 needs Matrix Script line packet `scene_plan_binding` (additive, referencing `factory_scene_plan_contract_v1`).
2. **B-Roll / background matching worker does not exist** (`broll_pending_upstream`). Phase 5 — Asset Supply bridge wired.
3. **Voice preview / synthesis worker does not exist** (`voice_preview_pending_voicetrans`). Phase 4 — VoiceTrans bridge through `factory_audio_plan` runtime layer.
4. **Subtitle-style projection does not exist** (`subtitle_style_pending_compose`). Phase 7 — compose worker style extension.
5. **BGM matching worker does not exist** (`bgm_pending_upstream`). Phase 7 — same compose gate.
6. **Main video generation worker does not exist** (`main_video_pending_capability`, = existing `not_generated`). Phase 6 — Capability Expansion Wave.
7. **Variant video generation worker does not exist** (`variants_pending_capability`). Phase 6 — same gate.
8. **Review-action worker does not exist** (`review_pending_main_video`). Phase 6 / Phase 7 — closure-action surface extension.
9. **Selling-points segment vocabulary not in `factory_content_structure`** (`selling_points_pending_upstream`). Future generic-contract amendment (out of scope for Phase 2B / 3 / 4 / 5 / 6 / 7).
10. **Metrics projection does not exist** — Delivery Center §6 metrics card remains the PR-B static placeholder.
11. **Line-packet additive bindings not authored** (`aspect_ratio_intent`, `operator_intent_map`, `scene_plan_binding`, `audio_plan_binding`, `language_plan_binding`, `visual_materials_binding`, `video_versions_binding`). Phase 3 work.

## 10. Verdict request

Requesting reviewer verdict on:

1. The 10-section Workbench IA matches the accepted Phase 1 mock + alignment trio.
2. The Phase 2B placeholder discipline (every unsupported slot carries a closed status code + honest tooltip + disabled action) is sufficient as the presentation-honesty floor pending Phase 3+ wiring.
3. The 16-item mission test plan is covered by 53 passing assertions in the new Phase 2B suite, with the 371-test back-compat regression also passing.
4. The Codex conditions (§8) are enforced as binding execution constraints.
5. The known backend gaps (§9) are the right Phase 3 / 4 / 5 / 6 / 7 work intake list.
6. **Next authorized wave is the reviewer's call.** Per the mission preamble: "Do not start Phase 3 packet binding. Do not start VoiceTrans bridge. Do not start Asset Supply bridge. Do not start video worker." Phase 2B closure is the only outcome of this branch.

Stop here. No template change beyond what is committed. No backend work. No Phase 3 / 4 / 5 / 6 / 7 branch creation.
