# Matrix Script · Script-to-Video · Presenter Alignment v1

Date: 2026-05-29
Status: **Design / interface-alignment document only.** No code, no template edits, no contract / schema / packet / closed-enum / runtime change. No Hot Follow / Digital Anchor / Asset Supply touch. No fake `final_video` / `publish_url` / media URL. No VoiceTrans raw embed. No provider / model / vendor / engine controls.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-29 (Script-to-Video Presenter / Contract Alignment Architect). This document does NOT open Phase 2B implementation; it is the alignment artifact that Phase 2B will consume.

Branch: `design/ms-script-to-video-presenter-alignment-20260529` (created from `design/ms-script-to-video-static-mock-phase1-20260529`, commit 001a622).

---

## 1. Reading Declaration

### 1.1 Authority + spec files read (15 / 15 from the mission required-reading list)

1. `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` — the approved Phase 1 mock (827 lines, three-tab clickable).
2. `docs/execution/MATRIX_SCRIPT_SCRIPT_TO_VIDEO_STATIC_MOCK_PHASE1_REPORT_v1.md` — Phase 1 implementation report.
3. `docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md` — accepted Kapwing-benchmark product advice (commit e03764e).
4. `docs/product/matrix_script_product_flow_v1.md` — current normative Matrix Script product spec.
5. `docs/design/matrix_script_workbench_product_flow_reset_v1.md` — PR-A / PR-B / PR-C reset design.
6. `docs/contracts/factory_input_contract_v1.md` — factory-generic input shape.
7. `docs/contracts/factory_content_structure_contract_v1.md` — content-structure object.
8. `docs/contracts/factory_scene_plan_contract_v1.md` — scene-plan object (required vs optional scenes; scene-pack non-blocking).
9. `docs/contracts/factory_audio_plan_contract_v1.md` — audio plan (intended route vs current truth).
10. `docs/contracts/factory_language_plan_contract_v1.md` — language plan (authoritative subtitle ownership).
11. `docs/contracts/factory_delivery_contract_v1.md` — delivery contract (primary vs optional; scene-pack non-blocking).
12. `docs/contracts/workbench_panel_dispatch_contract_v1.md` — Workbench panel dispatch.
13. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` — top-level business flow.
14. `docs/ENGINEERING_INDEX.md` — engineering authority index.
15. Matrix Script presenter / helper / template inventory:
    - `gateway/app/templates/matrix_script_new.html` — 27 unique `data-role` markers; fields `audience_hint`, `existing_source_script_ref`, `length_hint`, `operator_notes` plus paste / upload / select tabs.
    - `gateway/app/templates/task_workbench.html` — matrix_script branch (PR-A reset); five primary section anchors + Section 5 fold.
    - `gateway/app/templates/task_publish_hub.html` — matrix_script branch (PR-B reset); six primary section anchors + Section 7 fold.
    - `gateway/app/services/task_view_presenters.py` — generic task-view presenter layer.
    - `gateway/app/services/task_view_helpers.py` — generic task-view helpers.
    - `gateway/app/services/matrix_script/` — 27 helper modules (full list in §3.2).
    - `gateway/app/services/tests/test_matrix_script_*.py` — 46 test files in scope.

No file was missing.

### 1.2 Repository state inspected

- Branch tip: `001a622` (Phase 1 mock).
- Matrix Script line: PR-A + PR-B + PR-C landed; presenter wave (this document) opens against that integrated tip.

---

## 2. Approved product surface summary

The Phase 1 static mock at `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` defines the operator-visible target surface for this alignment work. Three pages:

### Page ① 新建 · 生成视频方案
Five cards on operator scan order:
1. **脚本** — paste / upload / select (sample script preloaded).
2. **产品 / 素材** — upload product clips / reference images / reference videos.
3. **目标 · 画幅 · 语言** — platform datalist + aspect-ratio radio + language multi-select + 受众 free-text.
4. **角色 · 声音 · 字幕** — operator-language preference selectors.
5. **变体策略** — variant count + 差异维度.

Primary CTA: **「生成视频方案」** (replaces "创建任务").

### Page ② 工作台 · 矩阵脚本 · 脚本转视频
Ten sections (A–J):

A. 主视频结果 (result hero, dominant first screen)
B. 脚本理解
C. **视频生成计划 (core product object — storyboard)**
D. 画面与素材
E. 角色与声音
F. 字幕与音乐
G. 视频变体 (video-level, not axis rows)
H. 校对与微调
I. 交付入口
J. 技术诊断 (`<details>` collapsed by default)

### Page ③ 交付中心
Seven sections (1–7):

1. 交付结果介绍
2. 主视频
3. 必需交付物 (字幕 / 音频 / 文案包 / manifest / 交付包)
4. 可选交付物 (其他视频版本 / scene pack / supporting material)
5. 发布设置
6. 发布回填
7. 技术诊断 (`<details>` collapsed; legacy quarantine)

---

## 3. Existing implementation inventory

### 3.1 New Task page (`gateway/app/templates/matrix_script_new.html`)

Operator-visible fields (form `name` attributes on the matrix_script create form):

| Field | Purpose | Source |
|---|---|---|
| `existing_source_script_ref` | Select existing source-script reference | hidden in operator mode (PR-1 gating) |
| `audience_hint` | Free-text audience description | operator |
| `length_hint` | Target length hint (operator language) | operator |
| `operator_notes` | Operator notes for the new task | operator |
| paste / upload / select tabs | Choose script entry mode (PR-1) | operator |

Submit handler: `gateway/app/routers/tasks.py:649 create_matrix_script_task` → `build_matrix_script_entry()` → `build_matrix_script_task_payload()` (both in `gateway/app/services/matrix_script/create_entry.py`).

### 3.2 Matrix Script presenter helpers (27 modules in `gateway/app/services/matrix_script/`)

| Module | Returns (top-level dict shape) | Currently feeds |
|---|---|---|
| `closure_binding.py` | closure binding for publish-feedback writes | publish hub closure block |
| `create_entry.py` | entry / task payload construction | new task route |
| `delivery_backfill_view.py` | publish backfill rows | DC §6 |
| `delivery_binding.py` | Matrix Script delivery contract binding | DC §3 + §4 |
| `delivery_comprehension.py` | required / optional lane projection | DC §3 (legacy Block B/C) |
| `delivery_copy_bundle_view.py` | copy-bundle subfields | DC §3 row 3 (legacy Block D) |
| `delivery_ready_package_view.py` | per-variation package readiness rows | WB Section 1 + DC §3 |
| `main_video_result_view.py` | main video state pill + 4 actions + preview slot | **WB Section 1 (PR-A)** |
| `phase_b_authoring.py` | Phase B authored truth from packet | content_structure source |
| `preview_compare_view.py` | per-variation preview status | WB Section 3 (PR-A) + DC §4 |
| `publish_backfill_readiness_view.py` | per-variation readiness rows | DC §6 (legacy Block F) |
| `publish_feedback_closure.py` | closure event projection | DC §6 + closure block |
| `publish_hub_pr3_attach.py` | PR-3 hub attach wire | DC bootstrap |
| `publish_hub_render_data.py` | DC render-data orchestration | DC top-level seam |
| `qc_diagnostics_view.py` | QC diagnostics items | WB Section 5 fold |
| `readable_variant_view.py` | operator-readable variant candidates | WB Section 2 step 2 (PR-A) + Section 3 |
| `recommended_action_view.py` | recommended variant + next-action | WB Section 1 banner + WB Section 3 |
| `result_status_view.py` | task result status pill | WB Section 5 fold + DC §1 |
| `review_zone_view.py` | per-zone review forms | WB Section 5 fold |
| `script_structure_view.py` | Hook / Body / CTA / taxonomy projection | **WB Section 2 step 1 (PR-A)** |
| `source_script_body_store.py` | source script body storage | new task path |
| `source_script_ref_minting.py` | source-script ref minting (technical-mode only) | new task path |
| `task_area_convergence.py` | task area card convergence | task area + DC §1 |
| `task_card_summary.py` | task card summary | task area |
| `workbench_comprehension.py` | PR-U2 comprehension shell | WB Section 5 fold |
| `workbench_variation_surface.py` | variation surface (axes / cells / slots) | WB Section 5 fold |

### 3.3 Generic presenter scaffolding (`gateway/app/services/task_view_*.py`)

- `task_view.py` — base task view object.
- `task_view_presenters.py` — per-line presenter dispatcher.
- `task_view_helpers.py` — shared helpers.
- `task_view_projection.py` — projection layer.
- `task_view_workbench_contract.py` — workbench contract glue.
- `operator_visible_surfaces/` directory — surface wiring.

### 3.4 Test inventory

46 `test_matrix_script_*.py` files in `gateway/app/services/tests/`. The relevant Phase-2B regression set:

- PR-A: `test_matrix_script_workbench_product_flow_reset_pra.py` (63 tests).
- PR-B: `test_matrix_script_delivery_center_product_flow_reset_prb.py` (69 tests).
- PR-C: source-level audits + 280-test combined regression (no new test file).
- Helper-level: per-presenter `test_matrix_script_*_view.py` (already cover the existing helpers in §3.2).

---

## 4. Section-to-presenter mapping

Each table row defines the mapping for one mock section. **Phase 2B does not implement these mappings — it consumes this document as the alignment spec.**

### A · 主视频结果

| Field | Value |
|---|---|
| **Product purpose** | Show "is the main video generated? what's blocking? what's next?" as the dominant first-screen anchor. |
| **Current data source** | `main_video_result_view.derive_matrix_script_main_video_result` (already wired by PR-A). |
| **Proposed presenter field** | `main_video_result_view` (existing — no rename). |
| **Capability state** | **supported now** (presenter wired); main-video generation worker **backend pending**. |
| **Forbidden in primary** | `final_video` raw, `publish_readiness` raw, `head_reason` raw, `RC-R8`, `provider`/`model`/`vendor`/`engine`. |
| **Phase 2B test assertion** | `assert "matrix-script-main-video-result" in primary_slice and first_op_card == that anchor` (already in PR-A suite — extend with operator-language pill copy assertion). |

### B · 脚本理解

| Field | Value |
|---|---|
| **Product purpose** | Operator-language script understanding: Hook / Body / CTA / 卖点 / 关键词 / 禁用词 / 目标平台 + 时长 / 目标语言. |
| **Current data source** | `script_structure_view.derive_matrix_script_script_structure_view` (already wired by PR-A Section 2 step 1). |
| **Proposed presenter field** | `script_understanding_view` (alias of existing; consider promoting to a top-level name for Phase 2B clarity). |
| **Capability state** | **supported now** for Hook / Body / CTA / 关键词 / 禁用词; **placeholder now** for 卖点 (no helper field yet — presenter can stub). |
| **Forbidden in primary** | `variation_axis`, raw axis arrays (`audience=[…]` etc.), `source_script_ref`. |
| **Phase 2B test assertion** | `assert all-section-fields-present(primary, ['Hook','Body','CTA','关键词','禁用词','目标平台'])` + `assert "audience=[" not in primary`. |

### C · 视频生成计划 (CORE)

| Field | Value |
|---|---|
| **Product purpose** | Visible storyboard / shot-list / scene-by-scene plan BEFORE generation fires. THE central product object. |
| **Current data source** | **None.** No helper produces scene-plan output today. `factory_scene_plan_contract_v1` defines the object shape but no Matrix Script line packet binding exists. |
| **Proposed presenter field** | `generation_plan_view` (NEW presenter for Phase 2B; reads from a Matrix Script line packet `scene_plan_binding` additive field that does not exist yet). |
| **Capability state** | **placeholder now** (presenter renders hand-authored scene list from packet metadata + hardcoded fallback fields) + **requires contract update** (`scene_plan_binding` line-packet additive, no generic contract change) + **backend pending** (scene-plan generation worker). |
| **Forbidden in primary** | `cell_id`, `slot_id`, `script_slot_ref`, `slot_pack`, `content://`, raw axis tuples. |
| **Phase 2B test assertion** | `assert "matrix-script-generation-plan" in primary_slice and primary_slice.find("generation-plan") < primary_slice.find("section-optional-variants")`. |

### D · 画面与素材

| Field | Value |
|---|---|
| **Product purpose** | Per-scene background + B-Roll candidates + product material slot + commercial-rights chip. |
| **Current data source** | **None.** No helper produces visual-material candidates today. Asset Supply matrix (`docs/product/asset_supply_matrix_v1.md`) is the future authority. |
| **Proposed presenter field** | `visual_materials_view` (NEW for Phase 2B; placeholder candidate list until Asset Supply bridge wires). |
| **Capability state** | **placeholder now** + **backend pending** (B-Roll matching worker, Asset Supply bridge — Phase 5). |
| **Forbidden in primary** | `artifact_lookup`, raw asset URLs, `content://`, vendor names. |
| **Phase 2B test assertion** | `assert all-three-subgroups-present(['ms-visual-bg-candidates','ms-visual-broll-candidates','ms-visual-uploaded-materials'])` + `assert all-disabled-buttons-carry-honest-tooltip()`. |

### E · 角色与声音

| Field | Value |
|---|---|
| **Product purpose** | Role / voice / language / speed preferences in operator language. No vendor names. |
| **Current data source** | Partial: `factory_audio_plan` intended-route (no presenter yet) + `factory_language_plan` (no presenter yet) + Digital Anchor role-asset registry (consumed-only; line-separated). |
| **Proposed presenter field** | `role_voice_view` (NEW for Phase 2B; placeholder selectors until VoiceTrans bridge + Digital Anchor role consumer wire — Phase 4 / §11). |
| **Capability state** | **placeholder now** + **backend pending** (VoiceTrans bridge for voice; Digital Anchor consumer for role). |
| **Forbidden in primary** | All vendor / model / engine names; raw role / speaker IDs. |
| **Phase 2B test assertion** | `assert no-vendor-words-in-primary(['azure','gemini','akool','seedance'])` + `assert voicetrans-iframe-absent()` + `assert role-selector-is-text-not-id()`. |

### F · 字幕与音乐

| Field | Value |
|---|---|
| **Product purpose** | Subtitle font / size / color / position / keyword highlight + BGM mood + volume. |
| **Current data source** | Partial: `factory_language_plan` (subtitle authority — wired); subtitle-style projection does not exist; BGM legality declared in `factory_audio_plan` but no presenter. |
| **Proposed presenter field** | `subtitle_music_view` (NEW for Phase 2B; style controls render as presenter-only until compose worker exposes a style projection). |
| **Capability state** | **placeholder now** (style controls) + **backend pending** (subtitle-style projection + BGM matching worker — Phase 7). |
| **Forbidden in primary** | Raw font filenames, raw color hex (use named tokens), `provider`/`engine`. |
| **Phase 2B test assertion** | `assert subtitle-controls-are-presenter-only()` + `assert no-bgm-file-name-in-primary()`. |

### G · 视频变体

| Field | Value |
|---|---|
| **Product purpose** | Variants are VIDEO VERSIONS with "what is different / why test / which is recommended" — not axis tuples. |
| **Current data source** | `readable_variant_view.derive_matrix_script_readable_variants` (already wired; produces per-variant differentiator + axis_summary). |
| **Proposed presenter field** | `video_versions_view` (renamed from `readable_variant_view` at the surface level; underlying helper unchanged). Field shape: `variant_id`, `headline_zh` ("V1 厨房·上扬"), `differentiator_zh`, `why_test_zh`, `is_recommended`. |
| **Capability state** | **supported now** (presenter wired; operator-language labels need extension for "why test" line) + **backend pending** (variant video generation). |
| **Forbidden in primary** | `cell_id`, `axis_tuple`, raw axis array, `slot_id`. |
| **Phase 2B test assertion** | `assert variant-rows-show(['哪里不同','为什么测','推荐'])` + `assert "axis=[" not in primary`. |

### H · 校对与微调

| Field | Value |
|---|---|
| **Product purpose** | Four review zones (画面 / 旁白 / 字幕 / 文案+CTA) for human polish post-generation. |
| **Current data source** | `review_zone_view.derive_matrix_script_review_zone_view` (already wired in PR-A Section 5 fold for closure forms). |
| **Proposed presenter field** | `review_tuning_view` (NEW front-facing alias; underlying helper unchanged — preserves closure-write contract). |
| **Capability state** | **supported now** (closure path wired); **backend pending** review-actions worker for accept/regenerate. |
| **Forbidden in primary** | `event_kind` raw, `closure` raw English, `record_kind`. |
| **Phase 2B test assertion** | `assert review-zones-rendered-in-operator-language(['画面','旁白','字幕','文案','CTA'])` + `assert no-event_kind-literal-in-primary()`. |

### I · 交付入口

| Field | Value |
|---|---|
| **Product purpose** | Lightweight 2-line + CTA → Delivery Center. |
| **Current data source** | `ops_pr.publishable` (already wired by PR-A Section 4). |
| **Proposed presenter field** | `delivery_entry_view` (alias of existing PR-A Section 4 wire). |
| **Capability state** | **supported now**. |
| **Forbidden in primary** | `publish_readiness`. |
| **Phase 2B test assertion** | `assert section-i-has(['line1','line2','cta'])` + `assert cta-href == "/tasks/{task_id}/publish"`. |

### J · 技术诊断

| Field | Value |
|---|---|
| **Product purpose** | `<details>` collapsed by default; architect view; quarantines retired legacy markers + engineering identifiers. |
| **Current data source** | All retired PR-3 / PR-A helpers' outputs (Workbench Section 5; DC Section 7). |
| **Proposed presenter field** | `technical_diagnostics_view` (alias for both surfaces). |
| **Capability state** | **supported now**. |
| **Forbidden in primary** | (N/A — this IS the home for everything otherwise forbidden.) |
| **Phase 2B test assertion** | `assert fold-collapsed-by-default()` + `assert legacy-markers-inside-fold(['matrix-script-block-a-…',…])`. |

---

## 5. Entry page alignment

### 5.1 Field evolution

| Current field | Phase 2B treatment |
|---|---|
| paste / upload / select script tabs | **Keep** — PR-1 wording stable. |
| `audience_hint` | **Keep** under operator-language label "受众". |
| `length_hint` | **Keep** under "目标时长". |
| `operator_notes` | **Keep** under "运营备注". |
| `existing_source_script_ref` | **Keep hidden** in operator mode (PR-1 gating). |
| `?technical=1` mint button gate | **Keep** — architect drill-down only. |
| — | **ADD (presenter-only):** product / material upload references (slot label + chips; no real upload yet). |
| — | **ADD (presenter-only):** target platform datalist (carries from Delivery Center §5 — 7 closed suggestions + free text). |
| — | **ADD (presenter-only):** aspect ratio radio (9:16 / 16:9 / 1:1). |
| — | **ADD (presenter-only):** role / voice / subtitle / B-Roll preference selectors (operator intent only; NO vendor config). |
| — | **ADD (presenter-only):** variant strategy selector. |

### 5.2 CTA shift

| Current CTA | Phase 2B CTA |
|---|---|
| `创建任务` (ms-new-submit) | `生成视频方案` (rename label; data-role unchanged for back-compat; submit still creates a task safely). |

### 5.3 Post-submit routing

- Submit handler unchanged: `create_matrix_script_task` continues to call `build_matrix_script_task_payload`.
- **Phase 2B:** post-submit redirect target is the Workbench page with Section C (`generation_plan_view`) rendering a **placeholder generation plan** (hand-authored fallback fields from script + entry preferences). No backend planning worker fires.

### 5.4 Discipline

- All new entry-page fields are **operator-intent capture**; they do not change task payload shape or contract truth.
- New fields are stored in `operator_notes` extension (JSON-encoded operator intent map) until the contract layer formalises them in Phase 3. This avoids any closed-enum widening at the contract level.
- Submit MUST remain safe: if the new fields are absent or unreadable, fall back to the existing payload shape. Backward-compatible by default.

---

## 6. Interface boundary (view-model names)

These names ARE the Phase 2B presenter-layer contract. **No presenter implementation in this phase.** Phase 2B will create modules under `gateway/app/services/matrix_script/script_to_video/` (or extend existing modules — choice deferred to Phase 2B authoring).

### 6.1 `script_understanding_view`

Minimal fields (`Mapping[str, Any]`):

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate for surface. |
| `hook_text` | str | Operator-language Hook line. |
| `body_text` | str | Operator-language Body line. |
| `cta_text` | str | Operator-language CTA line. |
| `selling_points` | list[str] | Operator-language selling-points list (placeholder allowed). |
| `keywords` | list[str] | Operator-language keywords. |
| `banwords` | list[str] | Operator-language forbidden terms. |
| `target_platform` | str | Operator-language target platform name. |
| `length_hint_zh` | str | Operator-language duration hint. |
| `target_languages` | list[str] | Operator-readable language codes. |

Source: extends `script_structure_view` (existing).

### 6.2 `generation_plan_view`

Minimal fields:

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `plan_status_code` | str | `plan_pending_upstream` / `plan_resolved_placeholder` / `plan_resolved_real` (closed). |
| `plan_status_label_zh` | str | Operator-language. |
| `scene_count` | int | Number of scenes. |
| `scenes` | list[dict] | Per-scene plan rows (see below). |
| `confirm_action_enabled` | bool | False until scene-plan worker lands. |

Per-scene row shape:

| Field | Type | Meaning |
|---|---|---|
| `scene_index` | int | 1-based. |
| `script_segment_zh` | str | The script line for this scene. |
| `visual_intent_zh` | str | Operator-language visual intent. |
| `background_suggestion_zh` | str | Operator-language. |
| `broll_suggestion_zh` | str | Operator-language. |
| `product_material_slot_label_zh` | str | "空 · 可上传" / "已绑定" etc. |
| `role_assignment_zh` | str | "AI 主播 (温和女声)" etc. |
| `voiceover_line_zh` | str | The voiceover line. |
| `subtitle_line_zh` | str | The subtitle line. |
| `music_mood_zh` | str | "上扬" / "舒缓" etc. |
| `aspect_ratio` | str | "9:16" / "16:9" / "1:1". |

### 6.3 `visual_materials_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `bg_candidates` | list[dict] | Background candidates (`name_zh`, `source_zh`, `commercial_status_zh` ∈ {"商用可","需审核","运营上传"}). |
| `broll_candidates` | list[dict] | B-Roll candidates (same shape). |
| `uploaded_materials` | list[dict] | Operator-uploaded materials. |
| `regenerate_action_enabled` | bool | False until matching worker lands. |

### 6.4 `role_voice_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `role_choice` | str | "AI 主播 · 温和女声 (默认)" / "无角色 · 仅画面" / etc. |
| `role_persona_zh` | str | "温和 / 真诚" / etc. |
| `gender_zh` | str | "女" / "男" / "不限". |
| `voice_style_zh` | str | "自然亲切" / etc. |
| `target_language_zh` | str | "zh-CN". |
| `speed_label` | str | "1.0x" etc. |
| `voice_preview_status_code` | str | `voice_preview_pending_voicetrans` (closed). |
| `voice_preview_status_label_zh` | str | "VoiceTrans 桥接尚未接入". |

### 6.5 `subtitle_music_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `subtitle_language_zh` | str | "zh-CN". |
| `subtitle_font_label_zh` | str | "思源黑 Bold (默认)" / etc. |
| `subtitle_size_label_zh` | str | "大" / "中" / "小". |
| `subtitle_color_label_zh` | str | "白色 + 黑色描边". |
| `subtitle_position_label_zh` | str | "底部居中" / etc. |
| `keyword_highlights` | list[str] | Operator-language. |
| `bgm_mood_zh` | str | "上扬 / 轻快". |
| `bgm_volume_default_pct` | int | 35. |
| `bgm_action_enabled` | bool | False until BGM worker lands. |

### 6.6 `video_versions_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `versions` | list[dict] | Per-video-version rows. |
| `add_version_action_enabled` | bool | False until generation worker lands. |
| `generate_all_action_enabled` | bool | False until generation worker lands. |

Per-version row shape:

| Field | Type | Meaning |
|---|---|---|
| `version_id` | str | "V1" / "V2" / etc. |
| `headline_zh` | str | "V1 · 厨房 · 上扬". |
| `differentiator_zh` | str | "背景：温馨厨房 · BGM：上扬 · 字幕：大字高亮". |
| `why_test_zh` | str | "主流情绪基线版，覆盖大多数账号 / 时段。". |
| `is_recommended` | bool | At most one row carries `True`. |

Source: extends `readable_variant_view` + `recommended_action_view`.

### 6.7 `review_tuning_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `zones` | list[dict] | One row per review zone. |

Per-zone row shape:

| Field | Type | Meaning |
|---|---|---|
| `zone_id` | str | `visual_match` / `voiceover` / `subtitle` / `copy_cta` (closed). |
| `zone_label_zh` | str | "画面匹配检查" / etc. |
| `status_code` | str | `pending_main_video` / `ready_for_review` / `accepted`. |
| `status_label_zh` | str | Operator-language. |

Source: extends `review_zone_view` (existing — preserves closure-write contract).

### 6.8 `delivery_entry_view`

| Field | Type | Meaning |
|---|---|---|
| `is_matrix_script` | bool | Gate. |
| `publishable` | bool | From `ops_pr.publishable`. |
| `line1_zh` | str | "当前不能交付：尚未生成主视频。" / "可交付 · 已确认主版本。". |
| `line2_zh` | str | "生成完成后…" / "前往交付页面填写发布设置…". |
| `cta_href` | str | "/tasks/{task_id}/publish". |

### 6.9 `technical_diagnostics_view`

| Field | Type | Meaning |
|---|---|---|
| `fold_label_zh` | str | "矩阵脚本 · 技术诊断（架构师视图，默认收起）". |
| `fold_hint_zh` | str | One-line hint. |
| `legacy_markers_preserved` | list[str] | Asserts which legacy `data-role`s are quarantined. |
| `engineering_identifiers_visible` | list[str] | The engineering identifiers permitted only inside this fold. |

---

## 7. Placeholder policy

Exact copy for unsupported capabilities. Phase 2B presenters must emit these strings literally.

| Capability | Placeholder copy (operator-language only) | Closed status code |
|---|---|---|
| Scene plan not generated yet | "当前尚未生成视频方案。已完成脚本理解；接入方案生成后将在这里展开故事板。" | `plan_pending_upstream` |
| B-Roll matching not connected | "素材匹配能力尚未接入；展示的为占位候选与运营可上传的素材槽。" | `broll_pending_upstream` |
| VoiceTrans bridge not connected | "VoiceTrans 桥接尚未接入；语音预览暂为占位。" | `voice_preview_pending_voicetrans` |
| Subtitle style projection not connected | "字幕样式接入后，可在此处实时预览。" | `subtitle_style_pending_compose` |
| BGM worker not connected | "替换 / 上传背景音乐的能力尚未接入。" | `bgm_pending_upstream` |
| Final video worker not connected | "当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。" | `main_video_pending_capability` (= existing `not_generated`) |
| Variant video generation not connected | "追加或同时生成视频版本的能力尚未接入。" | `variants_pending_capability` |

Behavioural rules:
- Every disabled button MUST carry a `title` attribute whose text is the operator-language placeholder copy for the relevant capability.
- Every placeholder slot MUST carry a `data-status-code` attribute whose value is the closed status code (so tests can assert against the code, not the copy).
- Phase 2B presenter MUST return `False` for any `*_action_enabled` field whose underlying worker is not wired.

---

## 8. Testing plan (Phase 2B targets)

The Phase 2B test suite will add these assertions. All run against the rendered HTML of `/tasks/{task_id}` and `/tasks/{task_id}/publish` for a matrix_script task with the standard packet binding.

| # | Test | Rule |
|---|---|---|
| 8.1 | `test_primary_has_no_backend_vocabulary` | The 15 forbidden tokens (publish_readiness / head_reason / artifact_lookup / final_video / RC-R8 / provider / vendor / engine / source_script_ref / content:// / slot_pack / provenance / variation_axis / event_kind / closure) absent from primary slice. |
| 8.2 | `test_generation_plan_section_before_variant_section` | `primary.find("generation-plan") < primary.find("section-optional-variants")` AND `primary.find("video-versions")`. |
| 8.3 | `test_variants_are_video_versions_not_axis_rows` | Each row in §G carries `data-version-id` (not `data-axis-tuple`); each row has `differentiator_zh` + `why_test_zh` columns. |
| 8.4 | `test_voicetrans_not_embedded` | No `<iframe[^>]*voice-tool`; no `<form action="/api/voice-tool`; no VoiceTrans page DOM shape in matrix_script branch. |
| 8.5 | `test_no_provider_model_vendor_engine_controls` | No `<select name="provider|model|vendor|engine">`, no `<input name="…">` with those names, no Chinese-language provider names ("Azure" / "Gemini" / "Akool" / "Seedance" etc.) in primary. |
| 8.6 | `test_no_fake_video_media_publish_url` | 0 `<video>` / `<iframe src>` / `<source src>` / `.mp4` / `.m3u8` / `youtu.be` / `tiktok.com` / `douyin.com` / `example.com` in primary. |
| 8.7 | `test_unsupported_capabilities_render_honest_placeholder_chips` | For each `data-status-code in {plan_pending_upstream, broll_pending_upstream, voice_preview_pending_voicetrans, subtitle_style_pending_compose, bgm_pending_upstream, variants_pending_capability}` the operator-language label appears AND the relevant action button is disabled with a `title` attribute. |
| 8.8 | `test_delivery_center_remains_final_video_oriented` | DC §1 = `交付结果介绍` paragraph; DC §2 = `主视频` preview hero; no production-flow controls in DC; no generation buttons in DC primary; DC §7 `<details>` collapsed by default. |
| 8.9 | `test_entry_cta_is_generate_video_plan` | New Task page CTA text is `生成视频方案` (or includes that string), not `创建任务`. |
| 8.10 | `test_post_submit_routes_to_workbench_with_plan_placeholder` | After creating a matrix_script task, the workbench page renders §C with `data-status-code="plan_pending_upstream"` and the operator-language placeholder copy. |

All assertions are source-level + rendered-HTML inspection. No new helper test required for Phase 2B beyond extending the PR-A suite (`test_matrix_script_workbench_product_flow_reset_pra.py`) and PR-B suite (`test_matrix_script_delivery_center_product_flow_reset_prb.py`) with the above 10 cases.

---

## 9. Out-of-scope (explicit non-goals for Phase 2B)

- No template implementation in this document (Phase 2B authoring opens later).
- No backend worker.
- No generic contract change.
- No closed-enum widening.
- No new endpoint.
- No VoiceTrans coupling.
- No Digital Anchor coupling (consumer-only stub; role-asset registry remains line-separated).
- No real B-Roll matching.
- No real BGM matching.
- No real video generation.
- No metrics projection.
- No fake media URL / publish URL anywhere.

---

## 10. Final position

This document is the **interface alignment spec** that Phase 2B (presenter mapping with honest placeholders) consumes. It defines:

- the operator-visible surface (per Phase 1 mock §2),
- the helper inventory (per §3),
- the section-to-presenter map (§4),
- the entry-page evolution (§5),
- the view-model field shapes (§6),
- the placeholder copy + status-code closed set (§7),
- the test plan for Phase 2B (§8).

Phase 2B opens only after this alignment is reviewed and accepted. No template, contract, schema, packet, runtime, or worker change is made by this document.
