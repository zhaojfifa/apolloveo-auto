# Matrix Script · Kapwing-Benchmark Product Advice v1

Date: 2026-05-29
Status: **Design advice only.** No code, no template edits, no contract / schema / packet / closed-enum / runtime change. No Hot Follow / Digital Anchor / Asset Supply touch. No backend generation implied. No fabricated `final_video` / media URL / `publish_url`. This document does NOT open any implementation gate; it is a product-direction recommendation.

Authoring authority: user-issued mission `[SYSTEM OVERRIDE]` 2026-05-29 (Matrix Script Product Design Advisor / Competitive Benchmark Reviewer). The recommendation supersedes — for design-direction purposes only — any earlier interpretation that Matrix Script's first product target is a "task / status / result surface" rather than a "script-to-video generation surface".

Branch: `design/ms-kapwing-benchmark-product-advice-20260529` (created from `VeoMatrixVoice02`, which is bytewise identical to `review/ms-product-flow-reset-visual-validation-prc-20260529` HEAD `5ccf943`).

---

## 1. Reading Declaration

### 1.1 Authority files read (17 / 17 from the mission required-reading list)

1. `docs/product/matrix_script_product_flow_v1.md` (347 lines) — Matrix Script product definition, content structure, variant dimensions, task area / Workbench / Delivery Center spec, capability embedding strategy, contract object plan (Input / Outline / Variant / Tool-Routing / Deliverable / Publish-Feedback).
2. `docs/product/digital_anchor_product_flow_v1.md` (380 lines) — Digital Anchor as a separate production line: role / scene / language / speaker / delivery binding. Cross-reference for §11.
3. `docs/design/matrix_script_workbench_product_flow_reset_v1.md` (346 lines) — PR-A / PR-B / PR-C reset design, four primary Workbench sections + five-section Delivery Center, §5 forbidden vocabulary list, §6 Delivery Center boundary rules, §9 acceptance bar.
4. `docs/design/matrix_script_result_oriented_ui_plan_v1.md` (381 lines) — Result-oriented UI implementation plan; operator-visible block mapping (S001 / S002 / S003 anchor); six-block primary path.
5. `docs/design/matrix_script_workbench_wireframe_v1.md` (437 lines) — Operator six-question framing (subject / variants / blocker / next action / recommended / publishable); legacy A–F block-by-block field shape.
6. `docs/handoffs/apolloveo_2_0_product_handoff_v1.md` (161 lines) — Product handoff: Matrix Script line packet schema requirements; six factory-generic contracts to consume; explicit "no vendor / no model name" rule; required packet fields (`script` / `outline` / `variation_plan` / `copy_bundle` / `publish_feedback` / `result_packet_binding`).
7. `docs/handoffs/apolloveo_2_0_design_handoff_v1.md` (191 lines) — Design handoff: five-face IA (任务区 / 工作台 / 交付中心 / 素材供给区 / 工具后台), three-surface low-fi requirements, line-specific differentiation modules.
8. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` (171 lines) — Top-level business flow (factory → line → result).
9. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` (552 lines) — Current wave, three-line status, B-roll position, five-bucket review classification.
10. `docs/contracts/factory_input_contract_v1.md` (74 lines) — `goal` / `audience` / `topic` / `script_text` / `target_language` / `reference_assets` / `forbidden_rules` input shape; factory-generic vs line-specific separation.
11. `docs/contracts/factory_content_structure_contract_v1.md` (72 lines) — Structural understanding object (Hook / Body / CTA semantics through generic vocabulary; risk flags; planner input bundle for scene / audio / language).
12. `docs/contracts/factory_scene_plan_contract_v1.md` (72 lines) — Scene-plan object: required scenes vs optional scene-pack derivatives; scene-pack non-blocking discipline.
13. `docs/contracts/factory_audio_plan_contract_v1.md` (76 lines) — Audio plan: intended route vs current truth; no-TTS / preserve-source / BGM legality; voice provider abstraction layer.
14. `docs/contracts/factory_language_plan_contract_v1.md` (75 lines) — Language plan: single-owned authoritative subtitle expectation; helper translation side channel.
15. `docs/contracts/factory_delivery_contract_v1.md` (126 lines) — Delivery contract: primary vs secondary; `required` / `blocking_publish` zoning (Plan D); scene-pack non-blocking rule (Plan C).
16. `docs/contracts/workbench_panel_dispatch_contract_v1.md` (163 lines) — Workbench panel dispatch contract (shell neutrality; panel_kind dispatch).
17. `docs/ENGINEERING_INDEX.md` (220 lines) — Engineering authority index (read-first map).

No file was missing. All 17 files are present at the listed paths in this branch.

### 1.2 Benchmark surfaces inspected (Kapwing public product surface, accessed via prior product-research notes — no live network fetch performed in this run, so the surface description below is paraphrased from publicly documented product behaviour, not screenshot-anchored quotes)

| Kapwing surface | Inspected concept | What it teaches us |
|---|---|---|
| Kapwing AI / KAI chat | Conversational creative-prompt entry that turns one operator sentence into a multi-step generation plan. | The first interaction is a prompt, not a task form. The user types an intent ("make a 30-second TikTok promoting our 7-day gym trial"); the product surfaces a generation plan before any heavy worker fires. |
| Script-to-Video studio | Editor canvas + side panel that compiles a written script into a scene list with auto-matched stock B-Roll, an AI voiceover, captions, and BGM. | The product treats the *plan* as the first-class object: scene list, per-scene script line, per-scene visual, per-scene voiceover, per-scene caption. The user reviews and edits the plan before pressing "Generate". |
| Storyboard / Shot-list view | Numbered scene rows with thumbnail / B-Roll picker / script segment / per-scene audio. | The user can swap a B-Roll clip, regenerate a thumbnail, or edit a single scene without re-running the whole task. |
| B-Roll / visual matching | Stock-library + custom-upload matching; the editor proposes clips per scene, the user replaces any clip with one click. | Asset supply is a *substrate* the user mixes; commercial-rights / source labelling is visible per clip. |
| AI character / presenter | Avatar gallery + voice picker per persona; per-scene presenter assignment. | Character is a per-project choice, then a per-scene assignment, not a model selector. |
| Voiceover / dubbing | Voice pick → preview → per-line regenerate; multi-language tab; dubbing into target language reuses the same script. | Voice is *previewable* before commit; the user picks by listening, not by reading provider names. |
| Subtitles / caption styling | Font / size / colour / position / keyword-highlight / animation; preview live on the canvas. | Subtitles are a *style-able layer* on top of the script — language ≠ visual style ≠ position. |
| Background music | Mood-tagged BGM library + upload; per-project track choice with volume slider. | BGM is selected by mood ("upbeat" / "calm") not by file name; volume sliders cap loudness against voiceover. |
| Editable timeline / generated video | Generated video lands on a timeline; every scene / overlay / caption / track remains editable. | "Generation" is not terminal — the output is opened for human polish before export. |
| Export / publishing workflow | Export → choose aspect ratio + platform + watermark choices → download or post; publish back-fill is the user's manual link. | The product never claims to have published — it hands the operator the file and the publish form. |
| Collaboration / brand kit | Brand kit (colours, logo, fonts) is set once, applied across all generations. | Brand consistency is a per-workspace asset, not a per-task field. |

### 1.3 Repository wave context inspected

- Current branch tip: `5ccf943` (PR-C visual-validation report). Workbench reset (PR-A) + Delivery Center reset (PR-B) are landed. Live smoke (per the VeoMatrixVoice02 integration report) confirms the Delivery Center renders the six new sections, but the Workbench still depends on a packet-bound task to enter the `panel_kind == "matrix_script"` gate.
- Six factory-generic contracts (`factory_input` / `factory_content_structure` / `factory_scene_plan` / `factory_audio_plan` / `factory_language_plan` / `factory_delivery`) are stable and form the substrate this recommendation maps to in §12.

---

## 2. Executive verdict

The PR-A / PR-B / PR-C cleanup is a **useful foundation** — it removes the additive-A/B/C/D/E/F clutter, retires backend vocabulary from the operator surface, and gives the operator a four-section Workbench + a six-section Delivery Center that no longer reads like six backend projections. As a *cleanup pass*, the wave succeeds.

But the wave is **not enough** as a market-facing script-to-video product. The reset produced a *honest empty-state result surface*; it did not produce a *result-generation surface*. The operator who lands on the Workbench today sees:

- a state pill that says "未生成",
- a banner that explains "the generation backend is pending",
- a stepper with three collapsed details that show some structural / variant facts.

The operator does **not** see:

- the generation plan (storyboard, shot-list, per-scene visual, voiceover line, subtitle line, music mood),
- the visual / B-Roll matching surface,
- the product-material slot,
- the role / presenter / voice surface,
- a single "生成视频方案" CTA they can press.

In Kapwing's mental model, the operator types an intent and gets a plan to confirm. In our current Matrix Script Workbench, the operator types task metadata into a New Task form, opens a Workbench that explains the task's metadata, and waits for a generation worker that does not exist. The mental model is still **task → status → result**, not **script → plan → result**.

**Stance**: useful cleanup foundation; not enough as a market-facing script-to-video product; must shift from a status / result surface to a *result-generation surface* — with the generation plan as a first-class product object, before the generation worker lands.

---

## 3. Kapwing benchmark analysis

The features below are the columns of Kapwing's mental model. Each row explains the *user value*, not just the feature.

| # | Feature | What it actually does for the user |
|---|---|---|
| 3.1 | **Prompt / script-first entry** | The user expresses creative intent in natural language at the door — "make me a 30-sec TikTok for our 7-day gym trial". The product immediately decomposes that intent into a structured plan the user can argue with. The user never types `task_id`, `category_key`, `kind`, `platform`, `account_id`, `source_url` to start. **Value:** the first interaction matches how creators actually think. |
| 3.2 | **Plan before generation** | After the prompt, the user gets a *visible plan*: scene list, per-scene script, per-scene visual intent, voice, subtitle, music. The user confirms, edits, or rewrites the plan. Only then does the heavy generation worker fire. **Value:** the user spends ~30 seconds editing a plan instead of ~30 minutes regenerating videos until one works. Saves cost, saves time, makes the system explainable. |
| 3.3 | **Storyboard / shot list** | The plan is shown as numbered scenes; each scene has a thumbnail, script segment, visual intent, suggested B-Roll, suggested voiceover. Scenes can be re-ordered, edited, or regenerated individually. **Value:** narrative pacing becomes a direct manipulation; the user can fix a bad hook in one click without re-running the rest of the video. |
| 3.4 | **B-Roll / visual matching** | Per-scene B-Roll picker. The system proposes 2–3 stock clips per scene; the user replaces any clip with one from the library or an upload. Commercial-rights chip is visible per clip. **Value:** visual variety without manual editing; commercial-risk is visible before publish, not after takedown. |
| 3.5 | **AI character / presenter** | Per-project (or per-scene) avatar / role / presenter assignment. The user picks by avatar preview, not by model name. **Value:** the user expresses "I want a warm female narrator" — they don't pick `gemini-tts-zh-female-warm-v3`. |
| 3.6 | **Voiceover / dubbing** | Voice picked from a preview gallery; multi-language tab regenerates the same script into N languages. Per-line regenerate if a single line sounds off. **Value:** the audio is *previewable* and *line-granular*; the user doesn't have to regenerate the full video to fix one line. |
| 3.7 | **Subtitles + style** | Subtitles are auto-generated from the script; font / size / colour / position / keyword-highlight / animation are styleable. Live preview on the canvas. **Value:** captions become a brand expression layer (font + colour + keyword highlight = brand voice), not just an accessibility deliverable. |
| 3.8 | **Background music** | Mood-tagged BGM library plus upload; per-project track; volume slider with auto-duck against voiceover. **Value:** the user picks by mood ("upbeat", "calm", "tense"), not by filename. The mix avoids drowning the narration. |
| 3.9 | **Editable timeline** | The generated video lands on a timeline editor. Every scene, overlay, caption, audio track is still editable after generation. **Value:** generation is not terminal — the user polishes. This is the difference between a "video generator" and a "video product". |
| 3.10 | **Export / publish** | Export menu with aspect ratio + platform + watermark + caption-burn-in choices. Publish flow hands the user the file and the publish form (or, on some plans, a direct platform integration). The product never claims to have published — it surfaces evidence and asks for confirmation. **Value:** honest publish state. No fake `publish_url`. |
| 3.11 | **Collaboration / brand kit** | Workspace-level brand kit (colours, logo, fonts, default voice, default music) auto-applied across all generations. **Value:** consistency across an account matrix without per-task re-input. This is directly aligned with our matrix-operations target. |

The product pattern that emerges: **(a) prompt / script in → (b) visible plan → (c) confirm → (d) generation → (e) editable output → (f) export / publish**. Six stages, every stage has direct manipulation, every stage is honest about what the system has versus what the user must provide.

---

## 4. ApolloVeo Matrix Script product gap

Concrete gaps measured against §3 and against our own `docs/product/matrix_script_product_flow_v1.md` §6 / §7 spec.

| # | Gap | Where it shows up today | Why it matters |
|---|---|---|---|
| 4.1 | **No generation plan as a first-class product object.** | The Workbench shows a state pill, a banner, and a stepper. There is no scene list, no per-scene script line, no per-scene visual intent. The "stepper" is a navigation strip, not a plan. | The user cannot confirm before generation; cannot edit the plan; cannot answer "what video will be generated?". |
| 4.2 | **No storyboard / shot-list surface.** | Block B (脚本结构) shows Hook / Body / CTA as one big block. There is no scene decomposition. | Pacing edits are impossible at scene granularity; the user must regenerate the whole video to fix one beat. |
| 4.3 | **No background / B-Roll matching surface.** | Asset supply is referenced only in `docs/product/asset_supply_matrix_v1.md` as a planned input. The Workbench has no B-Roll picker. | Visual variety is not operatable from the Workbench; commercial risk is not surfaced. |
| 4.4 | **No product material replacement flow.** | Uploads happen on the New Task page (paste / upload / select), then disappear from the Workbench. | Once a task is open, the user cannot swap product clips; matrix testing is hobbled. |
| 4.5 | **No role / character input.** | The Workbench has no presenter / role surface. Digital Anchor's role concept is line-separated. | The user cannot say "use our brand spokesperson" without leaving Matrix Script. |
| 4.6 | **No voiceover editing surface.** | The Workbench mentions voice only as part of the variant table's "字幕 / 配音" cell. No preview, no per-line regenerate. | Audio is not previewable; voice errors are only catchable after full generation. |
| 4.7 | **No subtitle style editing surface.** | Subtitles are a deliverable row in the Delivery Center. No font / colour / position / keyword-highlight controls. | Captions are an accessibility deliverable, not a brand expression layer. |
| 4.8 | **No background music replacement.** | BGM is not surfaced anywhere on the Workbench or Delivery Center. | BGM is silently chosen by the generator (if any) without operator input or override. |
| 4.9 | **Variants are still too close to config rows, not video versions.** | Workbench Section 3 (`可选变体`) and the legacy Block E candidate cards show variants as axis rows (`语气 / 时长 / 受众 / 开头方式 / 画面方向`). No per-variant preview, no per-variant scene swap. | The user picks by reading axis values, not by watching previews. This is the inverse of how creators choose. |
| 4.10 | **Delivery Center still partly carries old 1.85 pack / SOP logic.** | Section 7 (技术诊断) contains the retired Block A–F + the Recovery PR-3 closure block + the JS-hydrated diagnostic shells. The 1.85 pack-SOP language survives there. | Architects can still read those panels, but the operator's mental model can leak in low-signal moments (e.g. when a tooltip text references "pack" / "SOP" / "scene_pack"). |
| 4.11 | **VoiceTrans is separate but not yet productised as an audio / language provider.** | VoiceTrans lives at `/voice-tool`. Matrix Script does not call it. The two surfaces share users but not data. | The brand voice from VoiceTrans cannot flow into Matrix Script as a voiceover preset; the language pair from VoiceTrans cannot pre-fill Matrix Script's language plan. |
| 4.12 | **UI still allows task / status mental model to dominate.** | The Workbench page header still references "Stage" / "Status" / "task_id"; the operator hand-off from PR-A reads like a project-management surface, not a creative-production surface. | The product never declares "we make videos" — it declares "we track task state". |

---

## 5. Revised product target

**Proposed product target wording (Chinese — recommended; English provided for reviewer clarity):**

> **Matrix Script = 面向账号矩阵运营的脚本转视频批量生产线。**
>
> **主承诺：输入脚本 → 生成视频方案 / 故事板 → 匹配画面与 B-Roll → 配置角色、旁白、字幕、音乐 → 生成主视频与多版本 → 校对微调 → 交付发布。**

In English (for non-Chinese reviewer reference; the Chinese wording is normative):

> Matrix Script is a script-to-video batch production line for matrix-account operations. The promise: paste / upload a script → see a video plan / storyboard → match visuals and B-Roll → configure the presenter, voice, subtitles, and music → generate the main video and its variants → review and fine-tune → deliver and publish.

The shift from the prior product wording (`docs/product/matrix_script_product_flow_v1.md` §2 / §11 "面向矩阵运营与快速试错的脚本驱动成片产线") is small but operationally decisive: we move the verb from *driving generation* to **producing a visible plan before generation**, and we name the editable layers (画面 / B-Roll / 角色 / 旁白 / 字幕 / 音乐 / 多版本 / 校对) as first-class product objects, not as variant-axis rows.

---

## 6. Minimal viable correction (NOT a full rebuild)

We do not propose a Kapwing clone. We propose the smallest correction set that makes Matrix Script behave like a result-oriented script-to-video product in operator perception. Six discipline rules:

| # | Discipline | Honest target |
|---|---|---|
| 6.1 | **Result first.** | The first card the operator sees is "what video will be generated" (main video result hero with preview slot or honest empty state). Already partially achieved by PR-A Section 1 — extend to a richer plan preview. |
| 6.2 | **Visible generation plan.** | The operator sees a storyboard / shot-list / scene-by-scene plan BEFORE pressing "generate", even when the plan is auto-suggested. The plan is editable per scene. |
| 6.3 | **One clear generate action.** | A single "生成视频方案" / "生成主视频" CTA, state-dependent enablement, no model picker, no provider picker. Disabled-with-honest-tooltip while the backend worker is pending. |
| 6.4 | **Honest unsupported-capability labels.** | Every editable slot that is not yet wired (B-Roll picker, voice preview, BGM picker, subtitle style) renders the slot with an operator-language "尚未接入" pill rather than fabricating a working control. |
| 6.5 | **Backend diagnostics hidden.** | The §5 forbidden vocabulary list (already enforced by PR-A / PR-B) stays out of primary copy. Technical diagnostics remain collapsed in the architect fold. |
| 6.6 | **No fake output.** | The Workbench / Delivery Center never fabricate a `final_video` URL, a `publish_url`, or a thumbnail. Section 2 of Delivery Center renders the helper-supplied empty-state copy. |

These six rules are the floor. The IA in §7 is what the rules buy us when applied as primary content.

---

## 7. Proposed Matrix Script Workbench IA (ten sections; J collapsed)

This is a *design proposal*, not an implementation target. Sections are listed in operator scan order. Every section maps to one or more factory-generic contract objects so the UI never invents truth.

### A · 主视频结果 (result hero, dominant first screen)
- video preview slot with four states (`未生成` / `生成中` / `待审核` / `可交付`)
- four actions: 生成主视频 / 重新生成 / 接受为主版本 / 前往交付
- honest empty-state copy when no `current_fresh` media exists (carry the PR-A copy)
- one-line blocker + one-line next-action banner

This section is essentially the PR-A Section 1 made richer (richer preview slot when media exists; same honest empty state when it does not).

### B · 脚本理解 (script understanding, replaces stepper step 1)
- Hook · Body · CTA (carries from `factory_content_structure`)
- 卖点 (selling points) — new slot
- 风险词 / 禁用词 (risk / forbidden terms)
- 目标平台 (target platform) + 时长 (target duration)

This section consumes `factory_content_structure_contract_v1` directly. No engineering field name reaches the operator.

### C · 视频生成计划 (the core product section — NEW)
The product centre. A scene-by-scene plan:

| 字段 | Per-scene content |
|---|---|
| 镜头编号 | 1, 2, 3, … |
| 脚本片段 | the script line for that scene |
| 视觉意图 | "口播 + 实拍学员对比" / "教练正面镜头" / etc. |
| 背景建议 | "健身房环境" / "白底人像" / etc. |
| B-Roll 建议 | "stock 跑步机镜头 ×2, 上传素材 #2" |
| 产品素材位 | upload slot or reference to uploaded materials |
| 角色 / 出镜 | "AI 主播 (warm female zh-CN)" / "本地主持人 #2" / "none" |
| 旁白 | the voiceover line for that scene (= 脚本片段 default; editable) |
| 字幕 | subtitle line + keyword highlights |
| 音乐情绪 | "上扬" / "舒缓" / "紧张" |
| 画幅 | 9:16 / 16:9 / 1:1 |

The plan is editable per scene. The plan is the **artifact** the operator confirms before "生成主视频" fires. This is the single biggest gap closure.

Backend mapping: `factory_scene_plan_contract_v1` already declares scene-plan object shape; the line packet's `variation_plan` already covers per-axis variation. This section asks the contract layer to **expose the scene-plan object** through the Matrix Script line packet's `scene_plan_binding` (new line-specific binding, generic-ref to `factory_scene_plan`).

### D · 画面与素材 (visuals + materials, NEW)
- matched background (operator-language, one card per matched candidate; chip carries commercial-rights hint)
- matched B-Roll (similar shape)
- uploaded product materials (gallery of operator-uploaded clips with replace / remove / preview)
- replace background / replace product clip / regenerate visual suggestion CTAs (disabled-with-honest-tooltip while the visual-matching worker is pending)
- asset source / commercial risk note per clip

Backend mapping: consumes `factory_input.reference_assets` + future B-Roll asset-supply bridge (per `docs/product/asset_supply_matrix_v1.md`).

### E · 角色与声音 (role + voice, NEW)
- role choice: 无 / AI 主播 / 本地主持人 / 自定义角色 (per Digital Anchor's role concept, but consumed-only — no role authoring here)
- role persona: warm / authoritative / playful / professional (operator-language tags)
- gender / voice style / target language / speed / emotion (operator-language)
- voice preview placeholder (clearly labelled `尚未接入` until VoiceTrans bridge lands)
- relation note: "角色资产由数字人口播线供应；语音由 VoiceTrans 桥接 (尚未接入)"

Backend mapping: `factory_audio_plan_contract_v1` intended-route + `factory_language_plan_contract_v1` source / target. Per §11, role assets come from Digital Anchor; voice generation comes from VoiceTrans. Neither integration is implemented today — the section is a *presenter placeholder* until §11 and §10 bridges land.

### F · 字幕与音乐 (subtitles + music, NEW)
- subtitle language (read-only from §B `factory_language_plan`)
- font / colour / size / position (operator-language style controls)
- keyword highlight rules
- BGM recommendation (mood-tagged: 上扬 / 舒缓 / 紧张 / 推介)
- replace / upload music
- volume slider with operator-language guidance ("自动避让旁白音量")

Backend mapping: subtitle style fields are presenter-only until the compose worker exposes a style projection; BGM consumes `factory_audio_plan.optional_audio_artifacts` (BGM legality already in the contract).

### G · 视频变体 (variants as video versions, REPLACES the current axis-row variants)
Each variant is a **video version**, not an axis tuple. Per variant the surface answers three questions:

- 哪里不同？ (what is different — operator-language one-liner)
- 为什么测这一版？ (why test this — recommendation from `recommended_action_view`)
- 推荐版本？ (which version is recommended — single ⭐ marker)

Variant kinds (operator-language; no axis vocabulary):

- background variant
- B-Roll variant
- product-material variant
- voiceover variant
- subtitle-style variant
- music variant
- role variant
- pacing / aspect-ratio variant

Backend mapping: `variation_plan` already in the Matrix Script line packet; the change is **operator-language labelling** — `variation_axis` rows like `audience=[b2b,b2c]` become "受众侧重新会员 vs 续费用户". This is the gap PR-A surfaced but did not close.

### H · 校对与微调 (review + fine-tune, NEW operator-flow section)
- 画面匹配检查 (visual match check)
- 旁白校对 (voiceover check)
- 字幕校对 (subtitle check)
- 文案 / CTA 校对 (copy / CTA check)
- 接受 / 重新生成 (accept / regenerate) — per-variant or whole-task

Backend mapping: consumes the existing `review_zone_view` closure path (already wired for the four review zones: 字幕 / 配音 / 文案 / CTA). The new framing is the visible flow, not new wiring.

### I · 交付入口 (delivery entry, lightweight CTA — carries from PR-A Section 4)
Already correct in PR-A. Two-line + single CTA pointing to Delivery Center. Keep as-is.

### J · 技术诊断 (collapsed `<details>`, architect view — carries from PR-A Section 5)
Already correct in PR-A. All retired legacy markup + engineering identifiers live here. Keep as-is.

---

## 8. Proposed New Task page adjustment

The current New Task page (`/tasks/matrix-script/new`) already passes operator boundary polish (paste / upload / select script primary tabs; `?technical=1` reveals the mint button). PR-1 closed the immediate "operator pastes script in opaque-ref slot" complaint. But the page still reads as a **task form**, not as a **script-to-video entry**. Proposed adjustment:

Recommended fields (operator-visible; no engineering field name reaches the operator):

1. **脚本** — paste / upload / select existing (already present; keep PR-1 wording).
2. **产品 / 素材** — upload product clips / reference images; preview chips.
3. **目标平台** — TikTok / YouTube Shorts / Instagram Reels / 抖音 / 视频号 / 小红书 / 快手 (free-text allowed; matches Delivery Center §5 free-text discipline).
4. **画幅** — 9:16 / 16:9 / 1:1 (radio).
5. **目标语言** — multi-select; default zh-CN.
6. **受众** — operator-language brief description; not closed enum.
7. **角色偏好** — 无 / AI 主播 / 本地主持人 / 自定义 (read-only chip; redirects to "在工作台配置" once §11 bridge lands).
8. **声音偏好** — warm / authoritative / playful / professional (operator-language tags; redirects similarly).
9. **字幕风格** — pick a brand style (read-only chip; redirects).
10. **背景 / B-Roll 偏好** — 优先使用上传素材 / 优先使用 stock 库 / 混合 (operator-language radio).
11. **变体策略** — 单版本 / 同时生成 N 个变体 (operator-language; default N=3).

**Primary CTA — replaces "创建任务":**

> **生成视频方案** (operator-language; triggers the plan worker, which lands the operator on the Workbench with §C plan populated — *not* "create task" which lands on an empty state).

The CTA wording shift is the most important change here. "创建任务" is a project-management verb; "生成视频方案" is a creative-production verb. The post-CTA landing remains the same Workbench page; what differs is that the operator expects to see a plan, not a state pill.

---

## 9. Proposed Delivery Center adjustment

PR-B already gives us the six operator sections. The remaining adjustment is to make the Delivery Center *final-video oriented* in copy and to push the 1.85 pack / SOP carry-over deeper:

| # | Section (current PR-B name) | Suggested adjustment |
|---|---|---|
| 1 | 交付结果介绍 | Carry as-is. |
| 2 | 主视频 | Add download CTA (operator-language "下载主视频", disabled-with-tooltip until backend lands). Add aspect-ratio chip (9:16 / 16:9 / 1:1). |
| 3 | 必需交付物 | Carry as-is (字幕 / 音频 / 文案包 / manifest / 交付包 rows). |
| 4 | 可选交付物 | Add 其他视频版本 (other variant videos) as a third sub-group above 场景包 / 补充素材. |
| 5 | 发布设置 | Carry as-is. |
| 6 | 发布回填 | Add metrics placeholder rows that explicitly read "指标投射尚未上线" (already implemented as a single placeholder; expand to per-variant lanes when the metrics worker lands). |
| 7 | 技术诊断 (collapsed) | Quarantine the retired 1.85 SOP / pack tooltips deeper; replace tooltips that mention "pack" / "SOP" with operator-language equivalents before they're folded. |

No new section is required; the proposal is to *carry PR-B and tighten copy* rather than restructure.

---

## 10. VoiceTrans role

VoiceTrans is a useful, working independent tool today. Recommended trajectory:

| Stage | What VoiceTrans is |
|---|---|
| Now | An **independent operator tool** at `/voice-tool`. Operators use it stand-alone for translation / dubbing / voiceover preview. No coupling with Matrix Script. |
| Phase 4 (per §14) | A **language / audio provider** behind a contract bridge. VoiceTrans exposes voice presets + translation results through a stable interface that Matrix Script's audio_plan + language_plan consume. |
| Future | The default audio / language fulfilment path. VoiceTrans renders inside Matrix Script's §E "角色与声音" as a voice-pick preview gallery (the operator hears samples, does not pick provider names). |

**Strict discipline:** the VoiceTrans UI itself is NEVER embedded raw inside Matrix Script's Workbench. What flows is the *audio plan* and the *language plan* — not the VoiceTrans page. The user-visible voice / dubbing controls inside Matrix Script render against the audio_plan / language_plan contracts, with VoiceTrans bound at the runtime layer (per `factory_audio_plan_contract_v1` "line runtime binds the generic audio plan to line-specific providers, voices, preserve-source rules").

---

## 11. Digital Anchor role

Digital Anchor is a separate production line today (per `docs/product/digital_anchor_product_flow_v1.md`). For Matrix Script's purpose, Digital Anchor becomes the **role / character / presenter asset provider**:

| Aspect | Direction |
|---|---|
| Role / character / presenter assets | Authored inside Digital Anchor; *consumed* inside Matrix Script's §E. |
| Role persona / local host / custom character | Operator-language chips. The selector reads "选择角色" — never "选择 avatar 模型 / vendor". |
| Asset registration | Happens once per workspace inside Digital Anchor; reusable across Matrix Script tasks. |
| Cross-line ownership | Digital Anchor owns the role lifecycle; Matrix Script owns the per-task role *assignment*. No state mutation crosses the line boundary. |

**Strict discipline:** Matrix Script's §E never exposes a model / vendor / provider control. The role choice is operator-language: "AI 主播 (温和女声)" / "本地主持人 #2 (内部录制)" / "自定义角色 — 在数字人口播线注册". If the operator wants to author a new role, they leave Matrix Script and enter Digital Anchor — the link is a navigation, not an in-place form.

---

## 12. Architecture alignment

The proposed Workbench IA maps to the existing factory-generic contracts. Nothing in §7 / §8 / §9 contradicts the contract layer; the recommendation can be implemented as presenter-layer + line-packet-binding work without touching the generic contracts.

| Section | Consumes | Notes |
|---|---|---|
| §A 主视频结果 | `factory_delivery_contract_v1` primary-deliverable truth + `publish_readiness_contract_v1` | Already wired by PR-A; carry. |
| §B 脚本理解 | `factory_content_structure_contract_v1` | Already wired by PR-A Section 2 step 1; promote to a full section. |
| §C 视频生成计划 | `factory_scene_plan_contract_v1` (scene-plan object) + Matrix Script line packet's `scene_plan_binding` (new line-specific binding) | Requires line-packet extension; contract layer untouched. |
| §D 画面与素材 | `factory_input.reference_assets` + Asset Supply bridge | Requires Asset Supply Phase 5 wire (per §14). |
| §E 角色与声音 | `factory_audio_plan_contract_v1` intended-route + `factory_language_plan_contract_v1` + Digital Anchor role binding (consumed-only) | Requires VoiceTrans bridge + Digital Anchor consumer wire (presenter-only until then). |
| §F 字幕与音乐 | `factory_language_plan_contract_v1` (subtitle authority) + `factory_audio_plan_contract_v1` (BGM legality) | Subtitle style is presenter-only until compose worker exposes style projection. |
| §G 视频变体 | Matrix Script line packet's `variation_plan` (existing) | Operator-language labelling only; no contract change. |
| §H 校对与微调 | Existing review_zone closure path | Already wired; visible-flow change only. |
| §I 交付入口 | `factory_delivery_contract_v1` publishability declaration | Carry from PR-A. |
| §J 技术诊断 | (architect view) | Carry from PR-A. |

L1 / L2 / L3 / L4 state discipline is preserved throughout: §C "video generation plan" is an L3 plan object (intended route), distinct from L2 artifact facts and from L4 surface summaries. The UI never invents readiness truth — every "已就位" / "尚未具备" / "待审核" label comes from a contract projection.

---

## 13. Capability support matrix

Every module is marked with one of five states:

- **supported now** — already wired and rendering live.
- **presenter placeholder** — UI slot exists with operator-language "尚未接入" copy; no backend.
- **requires contract update** — additive amendment to a generic or line contract; no breaking change.
- **requires backend worker** — needs a runtime worker landing (Capability Expansion Wave or later).
- **future phase** — out of P2 / P3 scope; recorded for completeness.

| Module | Current state | Notes |
|---|---|---|
| Script understanding (Hook / Body / CTA / 卖点 / 风险词) | **supported now** | PR-A Section 2 step 1 + helper `script_structure_view` already projects this. Need slot for 卖点 + 风险词 (presenter-only fields on the helper). |
| Storyboard / scene plan | **presenter placeholder** + **requires contract update** | UI can render placeholder slots immediately. To fill them with real data, `factory_scene_plan_contract_v1` is already there; the Matrix Script line packet needs a `scene_plan_binding` (additive). |
| B-Roll / background matching | **presenter placeholder** + **requires backend worker** | UI can render placeholder picker; matching worker is future phase. |
| Product material replacement | **presenter placeholder** + **requires backend worker** | UI can render upload + swap controls (presenter-only). Worker is future. |
| Character / presenter | **presenter placeholder** + **requires backend worker** | Depends on Digital Anchor role-asset bridge. |
| Voiceover | **presenter placeholder** + **requires backend worker** | Depends on VoiceTrans bridge. |
| Subtitles / style | **presenter placeholder** + **requires backend worker** | Subtitle authority is already covered by `factory_language_plan_contract_v1`; style projection requires a compose-worker extension. |
| BGM | **presenter placeholder** + **requires backend worker** | `factory_audio_plan_contract_v1` already allows BGM legality declaration; matching worker is future. |
| Main video generation | **requires backend worker** | The Capability Expansion Wave is the binding gate. Section 1 stays in honest empty state until it lands. |
| Variant video generation | **requires backend worker** | Same gate; relabelling axis-row UI to video-version UI is presenter-only and can ship first. |
| Delivery package | **supported now** | PR-B Section 3 already projects from `delivery_comprehension`. |
| Publish feedback (backfill) | **supported now (partial)** | PR-B Section 6 renders the 4 closure-driven columns; metrics column is placeholder, recorded as Known limitation in PR-B. |

---

## 14. Implementation recommendation (staged; NOT to start now)

Phase 0 is the only phase this advice document concludes; everything else is recommendation for future-wave authoring. Do **not** open any of Phases 1+ without an explicit裁决 sign-off.

| Phase | Scope | Authority gate |
|---|---|---|
| **Phase 0 · Product design freeze** | This document. The裁决 either accepts the §5 product target wording + §7 Workbench IA + §8 New Task adjustment + §9 Delivery Center adjustment, or rejects with redirection. | Architect / Coordinator sign-off on this document. |
| **Phase 1 · Static clickable product mock / preview route** | A non-Jinja static route (or a separate `/_design-preview/matrix-script` page) that demonstrates the §7 IA with hand-authored content. No backend wiring; no contract change; no test fixture. Purpose: alignment review against real visual. | Phase 0 closed. |
| **Phase 2 · Presenter mapping with honest placeholders** | Wire the existing helpers (`script_structure_view`, `recommended_action_view`, `delivery_ready_package_view`, etc.) into the §7 sections in `task_workbench.html`. Sections C–F render presenter placeholders for the unsupported capabilities. No new helper; no contract change. | Phase 1 closed; static mock signed off. |
| **Phase 3 · Packet / contract update for scene_plan + audio_plan + language_plan bindings** | Matrix Script line packet gains `scene_plan_binding`, `audio_plan_binding`, `language_plan_binding` (additive; reference the existing factory-generic contracts). Packet validator extended; no breaking change to any generic contract. | Phase 2 closed; presenter mapping reviewed. |
| **Phase 4 · VoiceTrans bridge** | Define a thin VoiceTrans adapter at the runtime layer that satisfies `factory_audio_plan` voice-route + `factory_language_plan` translation-route. VoiceTrans UI stays untouched; Matrix Script's §E renders against the audio_plan / language_plan contracts. | Phase 3 packet update merged. |
| **Phase 5 · B-Roll / asset supply bridge** | `docs/product/asset_supply_matrix_v1.md` operationalised: B-Roll / product-material assets registered through Asset Supply; Matrix Script's §D consumes them through `factory_input.reference_assets`. | Phase 4 closed. |
| **Phase 6 · Video assembly worker** | The Capability Expansion Wave's video-generation worker lands. Sections A and G become alive. | Phase 5 closed. |
| **Phase 7 · Delivery / publish-feedback hardening** | Metrics column in Section 6 wired to a real metrics projection; archive flow promoted from `operator_note` to a closed `record_kind == archive_action` (PG-4 schema extension). | Phase 6 closed. |

The phases are stop-or-go; each phase opens only after the prior wave is reviewed. None of Phases 1+ are authorised by this document.

---

## 15. Risks and non-goals

Explicit no-build / no-cross discipline:

| # | Risk / non-goal |
|---|---|
| 15.1 | **Do not clone Kapwing fully.** The benchmark is a mental-model reference, not a UI clone target. ApolloVeo's architecture (four-layer state, factory contracts, line packets, asset supply) is the source of truth — Kapwing's brand-kit / collaboration / editing-timeline UI is out of scope for the corrective wave. |
| 15.2 | **Do not expose model / vendor / provider controls.** Validator R3 remains binding. Voice / role / B-Roll / BGM choices read in operator language; provider selection happens at the runtime layer. |
| 15.3 | **Do not fake generated media.** No fabricated `final_video` URL; no placeholder media player; no synthetic thumbnail. Sections A / D / E / F render presenter placeholders with operator-language "尚未接入" copy until the workers land. |
| 15.4 | **Do not let UI invent status truth.** Every state pill, every readiness label, every blocker reason flows through a contract projection. No surface re-derives publishability. |
| 15.5 | **Do not bypass existing production-line architecture.** Matrix Script remains one of three production lines; the four-face IA (任务区 / 工作台 / 交付中心 / 素材供给区 / 工具后台) is preserved. No new top-level surface. |
| 15.6 | **Do not embed VoiceTrans raw UI inside Matrix Script.** VoiceTrans is consumed as an audio / language provider through a contract bridge, never as an embedded iframe / panel. |
| 15.7 | **Do not reopen Hot Follow behaviour.** Hot Follow is frozen. The recommendation touches Matrix Script only; cross-line copy-paste is forbidden. |
| 15.8 | **Do not skip Phase 0 sign-off.** Phases 1+ require sign-off; opening Phase 1 without裁决 would re-create the additive-on-top problem PR-A had to subtract. |

---

## 16. Final recommendation

**Recommended product direction ready for裁决.**

The corrective shift this document proposes is structurally small but operationally decisive:

1. Promote the **generation plan** (storyboard / scene-by-scene / per-scene visual + voice + subtitle + music) from "nonexistent in UI" to **first-class product object** (§C of the proposed Workbench IA).
2. Rename the operator's mental anchor from **task** to **script-to-video**, surfaced as the New Task CTA shift "创建任务" → "生成视频方案" (§8).
3. Reframe the variants from **axis-tuple rows** to **video versions** (§G), each carrying "what is different / why test / which is recommended".
4. Hold the §5 / §6 / §15 discipline: no model / vendor / provider controls; no fake media; no UI-invented status; presenter placeholders for everything not yet wired.

If the裁决 accepts this direction, Phase 1 (static clickable mock) is the next authorised wave. If the裁决 redirects, this document is the artifact to redirect against.

Stopping here. No code, no template edits, no contract / schema / packet / closed-enum / runtime change introduced by this document.
