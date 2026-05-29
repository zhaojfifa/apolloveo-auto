# Matrix Script · Script-to-Video · Contract Alignment v1

Date: 2026-05-29
Status: **Architecture alignment document only.** No generic contract change. Any line-packet additions described here are *additive* and reserved for a future Phase 3 wave. No code, no schema, no packet, no closed-enum change is made by this document. UI cannot infer readiness. Scene Pack remains non-blocking. Final video is the primary result. No vendor / model / provider / engine controls.

Authority: user mission `[SYSTEM OVERRIDE]` 2026-05-29 (Script-to-Video Presenter / Contract Alignment Architect, Deliverable 2). Companion to [docs/design/matrix_script_script_to_video_presenter_alignment_v1.md](../design/matrix_script_script_to_video_presenter_alignment_v1.md).

---

## 1. Purpose

Map the approved script-to-video Phase 1 mock to the existing factory-generic contract layer so that Phase 2B (presenter mapping) and Phase 3 (line-packet additions) have an explicit contract substrate to consume. **No generic contract is modified by this document.** Where the mock surface needs data not present in any current generic contract, the gap is recorded as a Phase-3 *line-packet additive binding* — not as a generic contract change.

---

## 2. Mapping the Phase 1 mock to factory-generic contracts

### 2.1 Entry → `factory_input_contract_v1`

| Mock entry-page field | Generic contract field | Generic-contract owner |
|---|---|---|
| Script paste / upload / select | `factory_input.source_asset_references` (script-as-asset) | `factory_input_contract_v1` §"Required Inputs" |
| Product / material upload | `factory_input.source_asset_references` (operator-uploaded materials) | same |
| Target platform | `factory_input.operator-supplied business metadata` | same |
| Aspect ratio | (none — **operator intent only**; not in any generic contract today) | line-specific intent (see §3.1) |
| Target language | `factory_input.source language hints` (target side) | same; consumed by `factory_language_plan_contract_v1` |
| Audience | `factory_input.operator-supplied business metadata` | same |
| Role / voice / subtitle / B-Roll preference | (none — **operator intent only**; consumed by line packet bindings) | line-specific intent (see §3.2 / §3.4 / §3.5) |
| Variant strategy | (none — **operator intent only**; consumed by Matrix Script's `variation_plan`) | line packet |

**Discipline:** the entry page must NOT widen `factory_input` to absorb the new operator-intent fields. Those fields live in the Matrix Script line packet's `operator_intent_map` (presenter-only until Phase 3 formalises them as additive line-specific bindings).

### 2.2 §B 脚本理解 → `factory_content_structure_contract_v1`

| Mock §B field | Generic contract field |
|---|---|
| Hook / Body / CTA | `factory_content_structure.structural segment references` + line-specific Matrix Script Hook/Body/CTA section interpretation. |
| 卖点 (selling points) | (none — **placeholder** until generic content-structure adds selling-points segment vocabulary; presenter-only for now). |
| 关键词 / 禁用词 | `factory_content_structure.taxonomy` (line-specific). |
| 目标平台 + 时长 | Echoes `factory_input.operator-supplied business metadata` + line-specific length hint. |
| 目标语言 | Echoes `factory_input.source language hints` (target side). |

### 2.3 §C 视频生成计划 → `factory_scene_plan_contract_v1`

| Mock §C field | Generic contract field |
|---|---|
| `scene_count` | `factory_scene_plan.ordered scene-plan object` (length). |
| `scenes[*].script_segment_zh` | `factory_scene_plan.scene-level references must remain traceable to structure/input evidence` (operator-language projection of the structure segment for this scene). |
| `scenes[*].visual_intent_zh` | `factory_scene_plan.scene execution prerequisites` (operator-language). |
| `scenes[*].background_suggestion_zh` / `broll_suggestion_zh` | `factory_scene_plan.optional scene-pack expectations` + line-specific visual binding (see §3.4). |
| `scenes[*].product_material_slot_label_zh` | `factory_input.source_asset_references` (per-scene slot). |
| `scenes[*].role_assignment_zh` | Line-specific role binding to Digital Anchor role asset (see §3.5). |
| `scenes[*].voiceover_line_zh` / `subtitle_line_zh` | `factory_audio_plan` per-scene line + `factory_language_plan` per-scene subtitle. |
| `scenes[*].music_mood_zh` | `factory_audio_plan.optional audio artifacts` (BGM legality declaration). |
| `scenes[*].aspect_ratio` | (none — **operator intent only**; not in any generic contract today). |

**Validation rule (Phase 3, when line-packet `scene_plan_binding` lands):** scene-plan absence must not by itself demote the line — already enforced by `factory_scene_plan.Validation Rules`.

### 2.4 §D 画面与素材 → `factory_input.reference_assets` + Asset Supply Matrix

| Mock §D field | Generic contract field |
|---|---|
| `bg_candidates[]` | `factory_input.source_asset_references` (operator-uploaded) + future Asset Supply stock bridge. |
| `broll_candidates[]` | same. |
| `uploaded_materials[]` | `factory_input.source_asset_references` (operator-uploaded). |
| `commercial_status_zh` per candidate | Line-specific asset metadata (per `docs/product/asset_supply_matrix_v1.md`). |

### 2.5 §E 角色与声音 → `factory_audio_plan_contract_v1` + Digital Anchor role binding

| Mock §E field | Generic contract field |
|---|---|
| `role_choice` | Line-specific consumer of Digital Anchor's `role_profile` (per `docs/product/digital_anchor_product_flow_v1.md`). Matrix Script does NOT author roles; only consumes. |
| `role_persona_zh` | Line-specific operator-language label. |
| `gender_zh` / `voice_style_zh` / `target_language_zh` / `speed_label` | `factory_audio_plan.audio plan object` (intended route) + `factory_language_plan.language plan object` (target side). |
| `voice_preview_status_code = voice_preview_pending_voicetrans` | `factory_audio_plan.audio plan must declare intended route separately from current audio outcome` — current outcome is "pending VoiceTrans bridge". |

**Discipline:** no generic contract field references VoiceTrans by name. VoiceTrans is the *line-runtime provider* bound at the runtime layer (per `factory_audio_plan.Relation To Line Runtime`).

### 2.6 §F 字幕与音乐 → `factory_language_plan_contract_v1` + `factory_audio_plan_contract_v1`

| Mock §F field | Generic contract field |
|---|---|
| `subtitle_language_zh` | `factory_language_plan.authoritative subtitle expectations`. |
| `subtitle_font_label_zh` / `subtitle_size_label_zh` / `subtitle_color_label_zh` / `subtitle_position_label_zh` | (none — **placeholder** until compose worker exposes a subtitle-style projection; presenter-only for now). |
| `keyword_highlights[]` | (none — **placeholder** until subtitle-style projection lands). |
| `bgm_mood_zh` | `factory_audio_plan.no-TTS / preserve-source / BGM legality declaration` (BGM allowed under operator-chosen mood). |
| `bgm_volume_default_pct` | (presenter-only). |

### 2.7 §G 视频变体 → Matrix Script line packet `variation_plan`

| Mock §G field | Line-packet field |
|---|---|
| `versions[]` | `variation_plan.variant_candidates[]` (operator-language projection). |
| `versions[*].headline_zh` / `differentiator_zh` / `why_test_zh` / `is_recommended` | Operator-language projection on top of existing variant fields (presenter-layer rewrite of `readable_variant_view` output). |

**No change** to the Matrix Script line packet variation_plan schema is implied. The change is at the presenter layer.

### 2.8 §H 校对与微调 → existing closure path

| Mock §H field | Existing contract path |
|---|---|
| `zones[*]` | `matrix_script_publish_feedback_closure` four-zone review path (already wired). |
| `zones[*].status_code` | Closure-derived per-zone status (presenter projection of existing closure events). |

### 2.9 §I 交付入口 → `publish_readiness_contract_v1`

| Mock §I field | Generic contract field |
|---|---|
| `publishable` | `publish_readiness.publishable` (single unified producer; already wired by PR-A Section 4). |
| `line1_zh` / `line2_zh` / `cta_href` | Operator-language wrapper around the existing publish_readiness output. |

### 2.10 §J 技术诊断 → architect quarantine (no contract mapping)

The fold's content is the home for everything that does not have an operator-visible mapping. It carries the retired PR-3 / PR-A markers and the engineering identifiers (`publish_readiness` / `head_reason` / `artifact_lookup` / `final_video` / `RC-R8` / `event_kind` / `closure` / `slot_pack` / `provenance` / `variation_axis`). No new contract is involved.

### 2.11 Delivery Center → `factory_delivery_contract_v1` (unchanged)

PR-B Delivery Center mapping holds. §3 of the Delivery Center already exposes the five required deliverables; §4 already exposes optional deliverables; §6 already exposes publish backfill. **No contract change.** Scene Pack remains non-blocking (per `factory_delivery_contract_v1.Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)`).

---

## 3. Future line-packet additive bindings (Phase 3; recorded only)

These are **future additive bindings** to the Matrix Script line packet. None is authored by this document. None changes any factory-generic contract. Each is **additive** — existing packet instances continue to validate without these new fields.

### 3.1 `aspect_ratio_intent` (line-packet additive)

- Type: closed enum `{"9:16","16:9","1:1"}`.
- Owner: Matrix Script line packet (line-specific operator intent).
- Generic reference: none (operator intent only).
- Default: `9:16`.

### 3.2 `operator_intent_map` (line-packet additive)

- Type: `Mapping[str, Any]` covering the entry-page operator-intent fields not yet in any generic contract (role / voice / subtitle / B-Roll preference; variant strategy).
- Owner: Matrix Script line packet.
- Generic reference: none (line-specific).
- Default: `{}` (empty map — entry page silently falls back to current behaviour).
- Discipline: each key inside the map MUST be a closed enum or operator-language free-text; no vendor / model / engine name.

### 3.3 `scene_plan_binding` (line-packet additive)

- Type: `Mapping[str, Any]` with the shape declared by `factory_scene_plan_contract_v1` plus line-specific Matrix Script fields (per-scene `script_segment_ref`, `visual_intent_zh`, etc.).
- Owner: Matrix Script line packet.
- Generic reference: `factory_scene_plan_contract_v1` (binding, not copy).
- Default: absent (presenter falls back to `plan_pending_upstream` placeholder).
- Discipline: scene-pack non-blocking rule (Plan C) applies; `scene_plan_binding.scenes[*].kind = scene_pack` rows must carry `required=false && blocking_publish=false`.

### 3.4 `visual_materials_binding` (line-packet additive)

- Type: `Mapping[str, Any]` referencing `factory_input.source_asset_references` + Asset Supply bridge metadata.
- Owner: Matrix Script line packet.
- Generic reference: `factory_input_contract_v1` (binding, not copy).
- Default: absent (presenter falls back to `broll_pending_upstream` placeholder).
- Discipline: every asset row MUST carry `commercial_status_code ∈ {commercial_ok, commercial_review, operator_upload}` (closed); the runtime never invents commercial status.

### 3.5 `audio_plan_binding` (line-packet additive)

- Type: `Mapping[str, Any]` with the shape declared by `factory_audio_plan_contract_v1` plus line-specific Matrix Script fields (per-scene voiceover line, BGM mood, volume).
- Owner: Matrix Script line packet.
- Generic reference: `factory_audio_plan_contract_v1` (binding, not copy).
- Default: absent (presenter falls back to `voice_preview_pending_voicetrans` + `bgm_pending_upstream` placeholders).
- Discipline: voice route binding is line-runtime concern; the line packet declares intended route only, not vendor.

### 3.6 `language_plan_binding` (line-packet additive)

- Type: `Mapping[str, Any]` with the shape declared by `factory_language_plan_contract_v1`.
- Owner: Matrix Script line packet.
- Generic reference: `factory_language_plan_contract_v1` (binding, not copy).
- Default: absent (presenter falls back to existing Matrix Script subtitle authority — already wired).
- Discipline: single-owned authoritative subtitle expectation rule applies (per `factory_language_plan.Validation Rules`).

### 3.7 `video_versions_binding` (line-packet additive)

- Type: `Mapping[str, Any]` with the shape declared by Matrix Script's existing `variation_plan` plus per-version `headline_zh` / `why_test_zh` / `is_recommended` operator-language projections.
- Owner: Matrix Script line packet.
- Generic reference: existing Matrix Script line packet (no new generic reference).
- Default: existing `variation_plan` continues to validate without these fields (additive).
- Discipline: per-version label MUST be operator-language; no axis-tuple raw label in the version `headline_zh`.

---

## 4. Discipline guards (binding rules for Phase 2B + Phase 3)

These rules MUST hold in every Phase 2B / Phase 3 wave that follows:

| # | Rule |
|---|---|
| 4.1 | **No generic contract change in Phase 2 / 3.** The six factory-generic contracts (`factory_input` / `factory_content_structure` / `factory_scene_plan` / `factory_audio_plan` / `factory_language_plan` / `factory_delivery`) remain bytewise stable. |
| 4.2 | **Any line packet additions must be additive.** Existing Matrix Script line-packet instances must continue to validate without the new bindings (§3.1–§3.7). |
| 4.3 | **UI cannot infer readiness.** Every readiness label (`未生成` / `生成中` / `待审核` / `可交付` / `已就位` / `缺失` etc.) flows from `publish_readiness_contract_v1` or a presenter projection of an L2 artifact fact. The UI never invents truth. |
| 4.4 | **Scene Pack remains non-blocking.** Per `factory_delivery_contract_v1` Plan C amendment. Any per-scene `kind = scene_pack` row inside `scene_plan_binding` carries `required=false && blocking_publish=false`. |
| 4.5 | **Final video is the primary result.** `factory_delivery_contract_v1.primary delivery truth must dominate optional derivative state` continues to apply. Variant videos are *optional derivatives* (visible in §G + DC §4); the *primary* deliverable remains the main video. |
| 4.6 | **No vendor / model / provider / engine controls.** Validator R3 stays binding. Role / voice / subtitle / B-Roll preference UI captures operator intent only; the runtime layer binds the intent to providers (VoiceTrans / Digital Anchor / Asset Supply / compose worker / generation worker). |
| 4.7 | **No fake `final_video` / `publish_url` / thumbnail.** Section 1 preview hero + Section 2 preview hero + Section 6 publish-URL column either render real artifacts via helper-supplied data or render the honest empty-state copy. |

---

## 5. Closed status-code register (for Phase 2B presenter use)

Phase 2B presenters will emit these closed status codes against the §7 placeholder policy. **No closed enum is registered in any generic contract by this document.** Phase 3 may promote a subset of these codes to a contract-level closed enum if the scope warrants — for now they are presenter-layer constants.

| Status code | Surface | Operator-language label |
|---|---|---|
| `plan_pending_upstream` | §C 视频生成计划 | "当前尚未生成视频方案。" |
| `plan_resolved_placeholder` | §C | "视频方案为占位演示版。" |
| `plan_resolved_real` | §C | "视频方案已就绪。" |
| `broll_pending_upstream` | §D 画面与素材 | "素材匹配能力尚未接入。" |
| `voice_preview_pending_voicetrans` | §E 角色与声音 | "VoiceTrans 桥接尚未接入；语音预览暂为占位。" |
| `subtitle_style_pending_compose` | §F 字幕与音乐 | "字幕样式接入后，可在此处实时预览。" |
| `bgm_pending_upstream` | §F | "替换 / 上传背景音乐的能力尚未接入。" |
| `main_video_pending_capability` | §A 主视频结果 | (= existing `not_generated`; carry the PR-A copy) |
| `variants_pending_capability` | §G 视频变体 | "追加或同时生成视频版本的能力尚未接入。" |
| `commercial_ok` | §D candidate row | "商用可" |
| `commercial_review` | §D candidate row | "需审核" |
| `operator_upload` | §D candidate row | "运营上传" |

---

## 6. Architecture alignment summary

The script-to-video product target maps cleanly onto the existing factory-generic contract layer. The corrective work to land Phase 2B (presenter mapping) and Phase 3 (line-packet additive bindings) does NOT require any generic contract change:

| Mock section | Generic contract consumed | Line-packet additive required (Phase 3) |
|---|---|---|
| Entry · script | `factory_input` | — (existing entry fields preserved) |
| Entry · operator intent | — | `aspect_ratio_intent` + `operator_intent_map` |
| §A 主视频结果 | `factory_delivery` + `publish_readiness` | — |
| §B 脚本理解 | `factory_content_structure` | — |
| §C 视频生成计划 | `factory_scene_plan` | `scene_plan_binding` |
| §D 画面与素材 | `factory_input.reference_assets` | `visual_materials_binding` |
| §E 角色与声音 | `factory_audio_plan` + `factory_language_plan` + Digital Anchor consumer | `audio_plan_binding` (subset) |
| §F 字幕与音乐 | `factory_language_plan` + `factory_audio_plan` | `language_plan_binding` + `audio_plan_binding` (BGM subset) |
| §G 视频变体 | (line-specific `variation_plan`) | `video_versions_binding` |
| §H 校对与微调 | (existing closure path) | — |
| §I 交付入口 | `factory_delivery` + `publish_readiness` | — |
| §J 技术诊断 | (architect view; no contract mapping) | — |
| DC §1–§7 | `factory_delivery` (PR-B mapping) | — |

L1 / L2 / L3 / L4 state discipline is preserved throughout. Section C "video generation plan" is an L3 plan object (intended route), distinct from L2 artifact facts (the actual video) and from L4 surface summaries (Workbench / Delivery Center).

---

## 7. Final position

This document is the **architecture alignment spec** that defines:

- which generic contracts each script-to-video mock section consumes (§2),
- which future line-packet additive bindings are needed and what their shapes are (§3),
- the seven discipline rules that bind Phase 2B + Phase 3 (§4),
- the closed status-code register for Phase 2B presenter placeholder copy (§5),
- the architecture alignment summary (§6).

No generic contract change is made. No line packet is modified. No code is touched. Phase 2B opens only after both this contract alignment and the companion presenter alignment (`docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`) are reviewed and accepted.
