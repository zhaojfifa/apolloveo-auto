# Matrix Script · Product Flow v2 Delta

Date: 2026-05-29
Status: **Delta document for review only.** Does NOT overwrite [docs/product/matrix_script_product_flow_v1.md](matrix_script_product_flow_v1.md). The v1 spec remains the normative product authority until this delta is reviewed and either accepted as a v2 replacement or merged back into v1 as an amendment.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-29 (Script-to-Video Presenter / Contract Alignment Architect, Deliverable 3). Companion to:
- [docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md](../design/matrix_script_kapwing_benchmark_product_advice_v1.md) — Kapwing-benchmark advice (accepted commit e03764e).
- [docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html](../design/previews/matrix_script_script_to_video_workbench_v1/index.html) — Phase 1 mock (accepted).
- [docs/design/matrix_script_script_to_video_presenter_alignment_v1.md](../design/matrix_script_script_to_video_presenter_alignment_v1.md) — presenter alignment (this branch, Deliverable 1).
- [docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md](../architecture/matrix_script_script_to_video_contract_alignment_v1.md) — contract alignment (this branch, Deliverable 2).

---

## 1. Delta summary

| Aspect | v1 (current normative) | v2 (proposed, after Phase 2B + Phase 3) |
|---|---|---|
| **Product framing** | 面向矩阵运营与快速试错的 **脚本驱动成片** 产线。<br/>(`task / status / result surface`) | 面向账号矩阵运营的 **脚本转视频批量生产线**。<br/>(`script-to-video generation surface`) |
| **Main promise** | 将一个内容主题转化为多条可发布短视频版本。 | 输入脚本 → 生成视频方案 / 故事板 → 匹配画面与 B-Roll → 配置角色、旁白、字幕、音乐 → 生成主视频与多版本 → 校对微调 → 交付发布。 |
| **First product object** | task (with `kind=matrix_script`) | **generation plan** (storyboard / scene-by-scene; the new first-class product object) |
| **Variants** | axis-tuple rows (`audience × tone × length …`) | **video versions** (V1 / V2 / V3 with `headline_zh` / `differentiator_zh` / `why_test_zh` / `is_recommended`) |
| **Entry CTA** | 创建任务 | 生成视频方案 |
| **Workbench IA** | 6 blocks (A 任务摘要 / B 脚本结构 / C 变体方案 / D 生成 / E 候选评审 / F 交付摘要) | **10 sections** (A 主视频结果 / B 脚本理解 / **C 视频生成计划** / D 画面与素材 / E 角色与声音 / F 字幕与音乐 / G 视频变体 / H 校对与微调 / I 交付入口 / J 技术诊断 collapsed) |
| **Delivery Center IA** | 6 numbered sections (PR-B reset) | carried; 7th `<details>` fold quarantines 1.85 SOP / pack legacy more deeply |
| **VoiceTrans relation** | none | **future audio / language provider via contract bridge** (Phase 4); never raw-embedded |
| **Digital Anchor relation** | line-separated | **future character / presenter / role asset provider** (consumer-only inside Matrix Script §E) |
| **Capability honesty** | partial (some "已就绪" labels render before backend wired) | **every unsupported slot carries an operator-language placeholder chip + status code** (§5 of the contract alignment closed status-code register) |

The delta is *additive operator-facing surface* + *renamed operator-facing CTA / variant framing*. It does NOT change the v1 contract object plan (§9 of v1); it consumes that plan unchanged.

---

## 2. Revised product target

(v2 target wording — to replace v1 §2 / §11 when this delta is accepted)

**Matrix Script = 面向账号矩阵运营的脚本转视频批量生产线。**

它的核心目标是：

- 把一段脚本转成 **可直接发布的短视频**；
- 在生成之前先产出一个 **可审阅、可编辑的视频生成方案**（故事板 / 分镜）；
- 围绕主视频提供 **画面与素材匹配、角色与声音、字幕与音乐** 的可调控层；
- 一次任务产出 **多个视频版本**（不是配置组合）；
- 支撑账号矩阵的批量测试、分发、回填、复盘。

主结果（v1 §2.1 carried unchanged）：`final_video`。

附属结果（v1 §2.2 carried unchanged）：`subtitle` / `audio` / `copy_bundle` / `scene_pack` (optional, non-blocking) / `metadata` / `manifest` / `publish_status` / `variation_config`.

---

## 3. Revised operator journey

(v2 operator journey — to replace v1 §4 "核心业务逻辑" when this delta is accepted)

```
1. 入口 · 生成视频方案
   ├─ 粘贴 / 上传 / 选择脚本
   ├─ 上传产品 / 参考素材
   ├─ 表达目标平台 / 画幅 / 语言 / 受众
   ├─ 表达角色 / 声音 / 字幕 / B-Roll 偏好
   ├─ 选择变体策略
   └─ CTA: 生成视频方案  →  进入工作台（视频生成计划占位）

2. 工作台 · 审阅方案 + 配置 + 生成
   A 主视频结果         · 第一屏识别身份
   B 脚本理解           · 系统读懂的脚本
   C 视频生成计划[核心] · 故事板 / 分镜 / 可编辑
   D 画面与素材         · 背景 / B-Roll / 产品素材
   E 角色与声音         · 偏好选择（不暴露 vendor）
   F 字幕与音乐         · 样式 / 高亮 / BGM mood
   G 视频变体           · 视频级版本，不是配置行
   H 校对与微调         · 4 个分区 (画面 / 旁白 / 字幕 / 文案+CTA)
   I 交付入口           · 2 行 + CTA → 交付页面
   J 技术诊断           · 默认收起（架构师视图）

3. 交付中心 · 主视频 + 发布
   1 介绍 / 2 主视频 / 3 必需 / 4 可选 / 5 发布设置 / 6 发布回填 / 7 技术诊断
```

The flow `主题/目标 → 脚本结构化 → 变体配置 → 生成任务 → 校对与筛选 → 成片交付 → 发布回填 → 复盘沉淀` from v1 §4 remains the *business-flow* spine. v2 adds an explicit **plan审阅** stage between *脚本结构化* and *生成任务*, surfaced as Workbench §C.

---

## 4. New first-class product object: generation plan

The single biggest delta. Defined in detail at [docs/design/matrix_script_script_to_video_presenter_alignment_v1.md](../design/matrix_script_script_to_video_presenter_alignment_v1.md) §6.2 (`generation_plan_view`) and [docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md](../architecture/matrix_script_script_to_video_contract_alignment_v1.md) §2.3 + §3.3 (`scene_plan_binding`).

Operator value:

- The operator sees **what video will be generated** before pressing generate.
- The plan is **editable per scene** (script segment / visual intent / B-Roll / product material / role / voiceover line / subtitle line / music mood / aspect ratio).
- The operator confirms the plan once; the system fires the heavy workers exactly once with the confirmed plan.
- If a single scene is wrong, the operator edits that scene and re-runs that scene — not the whole video.

Architecture position:

- `factory_scene_plan_contract_v1` already declares the scene-plan object shape (no generic change).
- Matrix Script line packet gains an **additive** `scene_plan_binding` (Phase 3).
- Until Phase 3, Workbench §C renders a `plan_pending_upstream` placeholder with operator-language copy.

---

## 5. New video-level variants

(replaces v1 §4.2 "变体维度" framing for operator-visible surface; the line-packet `variation_plan` object itself stays the same)

Variants are **video versions**, not axis tuples. Each version answers three operator questions:

| Question | Source field |
|---|---|
| 哪里不同？ | `differentiator_zh` (one-liner: "背景：温馨厨房 · BGM：上扬 · 字幕：大字高亮") |
| 为什么测这一版？ | `why_test_zh` (one-liner: "主流情绪基线版，覆盖大多数账号 / 时段") |
| 推荐版本？ | `is_recommended` (boolean; at most one ⭐) |

The axis-tuple display (v1 §4.2 "Hook 变体 / 背景画面变体 / 配音变体 / 字幕语言变体 / 视觉风格变体 / 节奏快慢变体") moves into the architect-only Section J fold; primary scan reads as "V1 / V2 / V3 with one-line operator framing".

---

## 6. VoiceTrans role (future audio / language provider)

Defined at [docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md](../design/matrix_script_kapwing_benchmark_product_advice_v1.md) §10. Summary for the product delta:

- **Now**: VoiceTrans is an independent operator tool at `/voice-tool`. Matrix Script does not consume it.
- **Phase 4**: VoiceTrans becomes the runtime-layer fulfilment provider for `factory_audio_plan_contract_v1` (voice route) and `factory_language_plan_contract_v1` (translation route). The binding is at the runtime layer, not at the UI layer.
- **Phase 4+**: Matrix Script Workbench §E renders against `factory_audio_plan` / `factory_language_plan` outputs. Operator picks role / voice preferences in operator language; the runtime selects VoiceTrans (or any future provider) without exposing the provider name.

Discipline: VoiceTrans is **never** embedded as an iframe or raw form inside Matrix Script's Workbench / Delivery Center / New Task page.

---

## 7. Digital Anchor role (future character / presenter provider)

Defined at [docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md](../design/matrix_script_kapwing_benchmark_product_advice_v1.md) §11. Summary for the product delta:

- **Now**: Digital Anchor is a separate production line (`docs/product/digital_anchor_product_flow_v1.md`).
- **Phase 4+**: Digital Anchor is the **role asset provider** for Matrix Script. The role assets (AI 主播 / 本地主持人 / 自定义角色) are authored in Digital Anchor; Matrix Script consumes them via a line-packet binding.
- **Phase 4+**: Matrix Script Workbench §E renders role choices as operator-language chips, not as model / vendor IDs.

Discipline: Role authoring is **never** done inside Matrix Script. If the operator wants a new role, they leave Matrix Script and enter Digital Anchor — the link is a navigation, not an in-place form.

---

## 8. What remains pending (recorded honestly)

These are the gaps the v2 delta makes visible but does NOT close. They are Phase 2B / Phase 3 / Phase 4 / Phase 5 / Phase 6 / Phase 7 intake per the accepted advice §14.

| Gap | Phase that closes it |
|---|---|
| Scene-plan helper does not exist; Workbench §C renders `plan_pending_upstream` placeholder | Phase 3 (`scene_plan_binding` additive) |
| B-Roll / background matching worker does not exist; Workbench §D renders `broll_pending_upstream` candidate placeholder | Phase 5 (Asset Supply bridge) |
| Voice preview / synthesis worker does not exist; Workbench §E renders `voice_preview_pending_voicetrans` placeholder | Phase 4 (VoiceTrans bridge) |
| Subtitle-style projection does not exist; Workbench §F renders `subtitle_style_pending_compose` placeholder | Phase 7 (compose worker subtitle-style projection) |
| BGM matching worker does not exist; Workbench §F renders `bgm_pending_upstream` placeholder | Phase 7 |
| Main video generation worker does not exist; Workbench §A renders `main_video_pending_capability` (= existing `not_generated`) | Phase 6 (Capability Expansion Wave) |
| Variant video generation worker does not exist; Workbench §G "追加" / "同时生成" disabled with honest tooltip | Phase 6 |
| Metrics projection does not exist; Delivery Center §6 metrics card is static placeholder | Phase 7 |
| `aspect_ratio_intent` / `operator_intent_map` / `scene_plan_binding` / `audio_plan_binding` / `language_plan_binding` / `visual_materials_binding` / `video_versions_binding` line-packet additive bindings not authored | Phase 3 |
| Selling-points segment vocabulary not in `factory_content_structure_contract_v1`; Workbench §B 卖点 row renders placeholder | future generic-contract amendment (NOT in scope of Phase 2B / 3) |
| Closure event `record_kind == archive_action` (PG-4 schema extension) | Phase 7 |

---

## 9. Discipline carry-over (binding from v1)

All discipline statements in v1 carry unchanged into v2:

- 主结果 = `final_video` (v1 §2.1).
- Scene Pack = optional non-blocking (v1 §3.2 + `factory_delivery_contract_v1` Plan C amendment).
- Publish = `final_ready + required_deliverables` (v1 §7.2).
- No vendor / model / provider / engine in operator UI (v1 §8 + validator R3).
- Helper translation = side-channel (v1 §8.4 + `factory_language_plan` validation rules).
- Tool routing = backend assembly, not UI selector (v1 §9.4 + Validator R3).

No discipline relaxation by v2.

---

## 10. Acceptance pathway

If this delta is accepted:

1. **Option A** — Promote to v2 normative: overwrite `docs/product/matrix_script_product_flow_v1.md` with a v2 file that merges this delta. (Out of scope for the current branch.)
2. **Option B** — Carry as amendment: keep v1 as the spine; reference this delta as the v2 amendment authority. (Recommended for least disruption.)

Either way, the next authorised wave is **Phase 2B** (presenter mapping in `task_workbench.html` and `task_publish_hub.html` consuming the presenter / contract alignment specs), opened only after this delta + the presenter alignment + the contract alignment are reviewed and accepted as a trio.

---

## 11. Final position

This document records the product delta from v1 (task / status / result surface) to v2 (script-to-video generation surface), without overwriting v1. The delta consists of:

- a revised product target wording (§2),
- a revised operator journey (§3) that introduces the **plan审阅** stage as Workbench §C,
- a **new first-class product object** (generation plan, §4),
- a **new video-level variant framing** (§5),
- VoiceTrans / Digital Anchor consumer-only consumption rules (§6 / §7),
- an honest pending-gap register (§8),
- a discipline carry-over statement (§9),
- two acceptance options (§10).

No file under `docs/product/` is overwritten. No code, contract, schema, packet, runtime, or worker is modified.
