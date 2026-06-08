# Matrix Script Storyboard-to-Video Architecture Alignment

Date: 2026-06-08
Status: **Architecture / product alignment document only. Docs-only.** No code, no template, no router, no schema, no contract, no test, no runtime change is made by this document. It authorizes no implementation, opens no wave, and supersedes no authority. It is an Owner-requested deep alignment pass that **consumes** the binding authorities (Bucket A + the 2026-06-07 gate specs + the merged Akool/Azure/ffmpeg substrate) and proposes — gate-spec-first — the next heavy engineering wave. Where this document conflicts with Bucket A (`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`), `ENGINEERING_RULES.md`, or `CURRENT_ENGINEERING_FOCUS.md`, the underlying authority wins and this document is corrected in a docs-only follow-up.

Anti-Sprawl posture (Design Authority Index rules 1–6): this is **not** a new Matrix Script IA / mock / reset, and it does **not** supersede Bucket A. Every operator-value item it proposes re-homes into the **existing A–J Workbench** and the **Slot Workflow v2 Current Shot Work Panel** — never a parallel flow. Execution logs are cited as evidence only, not as authority.

Authoring authority: Owner correction received 2026-06-08 ("perform a serious product/architecture/provider alignment pass before any heavy implementation").

---

## 0. Reading Declaration

Files actually read in full or in decision-relevant part for this alignment, grouped per the mandatory-reading list. Honest notes on what was missing are included.

### 0.1 Root / engineering rules
- `CLAUDE.md` — bootloader / router (in context).
- `README.md` — **not re-opened this pass** (consumed via the unified map §1 + `docs/README.md` index; declared honestly, not re-read line-by-line).
- `PROJECT_RULES.md` — **not re-opened this pass** (root governance consumed via the unified map §6.1 baseline list; declared honestly).
- `ENGINEERING_RULES.md` §1–§13 (file/function size, router/service ownership, import discipline, contract-first §6, truth-source §8, factory-alignment gate §9, validation §10, scope control §11, default entry map §12, **Product-Flow Module Presence §13**).
- `CURRENT_ENGINEERING_FOCUS.md` (full, 126 lines) — current stage, allowed/forbidden work, merge gates, structural-risk reminders, cross-cutting cognition map.
- `ENGINEERING_STATUS.md` (lines 1–114; tail paged) — current completion log, Plan E phase state, recovery-wave state.
- `docs/README.md`, `docs/ENGINEERING_INDEX.md` — **consumed as index pointers** (not re-read line-by-line this pass; declared honestly).
- `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md` (BINDING, 2026-06-01) — Bucket A authority list, A–J binding reading, Anti-Sprawl rules, accepted Guided/Slot-v2 gate specs.

### 0.2 Product
- `docs/product/matrix_script_product_flow_v1.md` (full) — normative business spine.
- `docs/product/matrix_script_product_flow_v2_delta.md` (full) — v2 delta (generation plan, 10-section IA, video-level variants, VoiceTrans/Digital Anchor bridges).
- `docs/product/asset_supply_matrix_v1.md` (full) — closed input/deliverable kind sets, supply-vs-donor decoupling.
- `docs/product/digital_anchor_product_flow_v1.md` — **consumed via Kapwing §11 + presenter §E + contract-alignment §2.5/§3.5** (role-as-provider relationship); not re-read in full this pass (declared honestly).
- `docs/product/hot_follow_product_flow_v1.md` — **MISSING.** No such file exists. The Hot Follow business flow lives at `docs/architecture/hot_follow_business_flow_v1.md` + `docs/contracts/hot_follow_*`; not load-bearing for this Matrix Script alignment.
- VoiceTrans / voice product docs — **no dedicated `docs/product/` VoiceTrans flow exists.** VoiceTrans is referenced inside v2-delta §6, the Kapwing advice §10, the contract alignment §2.5, and `docs/execution/VOICE_TRANSLATION_TOOL_*`. Treated as a future provider bridge only.

### 0.3 Design / benchmark
- `docs/design/matrix_script_kapwing_benchmark_product_advice_v1.md` (full) — Kapwing mental-model benchmark, §7 ten-section Workbench IA, §C generation plan, §G video versions, §13 capability support matrix.
- `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md` (full) — §6.2 `generation_plan_view` field shape, §7 placeholder policy, closed status codes.
- `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_PRODUCT_PLAN_20260607.md` (full, #228 merged) — scalable queue + single active panel; Shot/Slot/Assignment object model; honest slot classification.
- `docs/design/MATRIX_SCRIPT_SLOT_WORKFLOW_V2_GATE_SPEC_20260607.md` (full, ACCEPTED-PENDING-SIGNOFF) — binding B区 zone rules, slot capability classification, acceptance rows A-V2-1..18, forbidden paths.
- `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md` — read via faithful sub-agent digest (local deterministic ffmpeg/ffprobe preview/proxy/QC; no provider/secret; `official_publish_ready=false`).
- `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html` — **present; not opened as raw HTML this pass.** Its operator-target surface is fully described by the presenter alignment §2 and the Kapwing advice §7 (both read in full); declared honestly.
- `docs/design/MATRIX_SCRIPT_MATERIAL_TO_V2_VISIBLE_CLOSURE_GATE_SPEC_20260607.md` — **MISSING.** No such file. The nearest landed authorities are the Guided Operator Workflow gate spec/closeout and the Slot Workflow v2 gate spec (both read).

### 0.4 Architecture / contract
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` (full) — wave/line/surface position, frozen next sequence (note: dated 2026-05-03, wave-stale vs the June work — see §2.5).
- `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md` (full) — §2 mock→generic-contract mapping, §3 future additive line-packet bindings, §4 discipline guards, §5 closed status-code register.
- No `docs/contracts/**` file was opened, edited, or relied on as a mutation target (this pass is contract-read-only via the alignment docs above).

### 0.5 Execution / review
- `docs/execution/MATRIX_SCRIPT_REAL_VIDEO_PRODUCTION_CAPABILITY_BATCH_20260607.md` — real Azure voiceover chain + capability status strip (NOT merged; #245).
- `docs/execution/MATRIX_SCRIPT_AKOOL_REAL_CAPABILITY_BATCH_20260608.md` — Akool image_to_video wired + Azure real (MERGED #247, `134b551f`).
- `docs/execution/MATRIX_SCRIPT_AKOOL_PROVIDER_MODE_PRODUCTION_SMOKE_20260608.md` — real Akool clip E2E proven locally (python3.11), consumed into final.mp4 (shot02).
- `docs/execution/MATRIX_SCRIPT_AKOOL_PROVIDER_MODE_MERGE_REPORT_20260608.md` — provider-mode contract fix `video_url`→`video` (MERGED #248, `824181b3`).
- `docs/execution/MATRIX_SCRIPT_AKOOL_REAL_CAPABILITY_MERGE_REPORT_20260608.md` — post-merge validation (88 tests pass).
- `docs/execution/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_CLOSEOUT_20260607.md` — Guided workflow engineering-closed (presentation over frozen truth).
- `docs/execution/MATRIX_SCRIPT_OPERATOR_VISIBLE_BACKBONE_INTEGRATION_20260607.md` — backbone+QC into operator path (NOT merged).
- `docs/execution/owner_summaries/` — `matrix_script_real_video_production_capability_owner_summary_20260607.md`, `matrix_script_akool_real_capability_owner_summary_20260608.md`, `matrix_script_akool_provider_mode_production_smoke_owner_summary_20260608.md`, `matrix_script_akool_real_capability_merge_owner_summary_20260608.md` (the requested "PR #245–#248 owner summaries").
- `docs/execution/MATRIX_SCRIPT_AKOOL_PROVIDER_MODE_PRODUCTION_SMOKE_REPORT_20260608.md` — **MISSING** as named; the real file is `..._SMOKE_20260608.md` (no `_REPORT`), read above.
- `docs/reviews/MATRIX_SCRIPT_VIDEO_CAPABILITY_UPGRADE_REVIEW_20260607.md` — capability-supply gap diagnosis; "no amount of queue/panel re-arrangement fixes this".
- `docs/reviews/matrix_script_slot_workflow_v2_operator_review.md` — operator-seat Round 2 PASS; C-1 V1/V2 wording fix, C-2 no-dead-control fix.
- `docs/reviews/MATRIX_SCRIPT_OPERATOR_VALUE_GAP_REVIEW_20260607.md` — **MISSING.** No such file. The nearest landed authorities are the video-capability-upgrade review and the slot-workflow-v2 operator review (both read).

### 0.6 Runtime / code / tests
Read via `rg` + three structured code-baseline sweeps (file:line cited where load-bearing in §2/§3/§5):
- `gateway/app/services/matrix_script/` — full module inventory (54 files). Read in depth: `shot_plan.py`, `shot_plan_builder.py`, `scene_artifacts.py`, `scene_manifest.py`, `tomato_real_result_orchestrator.py`, `tomato_real_result_plan.py`, `akool_image_to_video_capability.py`, `akool_real_gate.py`, `voiceover_capability.py`, `ffmpeg_backbone.py`, `real_asset_scene_renderer.py`, `simple_scene_renderer.py`, `operator_workbench_view.py`, the `minimal_result_*` family, `real_trial_orchestrator.py`.
- `gateway/app/services/providers/akool/client.py` — create/read endpoints + result field.
- `gateway/app/templates/task_workbench.html` — matrix_script A–E primary blocks + per-shot cards + V1/V2 compare.
- Tests sighted: `gateway/app/services/tests/test_matrix_script_akool_image_to_video_capability.py`, `..._voiceover_capability.py`, `..._ffmpeg_backbone.py`, `..._minimal_result_loop.py`, `..._minimal_result_service.py` (existence + role confirmed; not exhaustively read).

---

## 1. Executive Decision

1. **v1 remains the business spine.** `docs/product/matrix_script_product_flow_v1.md` (主题/目标 → 脚本结构化 → 变体配置 → 生成任务 → 校对与筛选 → 成片交付 → 发布回填 → 复盘沉淀) is the normative product authority. The primary deliverable stays `final_video`; Scene Pack stays optional / non-blocking; publish stays `final_ready + required_deliverables`; no vendor/model/provider in operator UI.

2. **The v2 delta is ACCEPTED as the current Matrix Script Script-to-Video product amendment direction.** `docs/product/matrix_script_product_flow_v2_delta.md` (Option B "carry as amendment") + its companions (Kapwing benchmark advice, presenter alignment, contract alignment) are Bucket A binding authority per `MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`. The first-class product object is the **generation plan / storyboard**; the operator reviews the plan **before** heavy generation fires; variants are **video versions**, not axis tuples; the Workbench is the **A–J ten-section** IA.

3. **Akool / Azure / ffmpeg / R2 are capability substrate, not the final product flow.** As of 2026-06-08 the provider/compose/host substrate is proven (see §2). But proving that a clip can be generated, narrated, composed, and hosted is **not** the same as a script-directed Script-to-Video product. Today's generation is **image-motion** (a hardcoded camera-motion prompt over a still), not **script-directed**; the operator surface is a per-shot **material-card queue**, not a storyboard whose generation intent is visible and editable.

4. **The next heavy engineering wave must build Generation Plan + Storyboard Control + Current Shot Workbench — driven by product flow v2, not by isolated provider fixes.** Concretely, the wave converges three accepted lines plus one genuinely new capability:
   - **Storyboard Control + Current Shot Workbench** = the already-specified **Slot Workflow v2** (compact Shot Queue + single Current Shot Work Panel + Slot Editor + Assignment) — pending §13 signoff;
   - **Generation Plan surface** = the already-specified **`generation_plan_view`** (presenter alignment §6.2) — projection-only;
   - **NEW (beyond every current gate):** **script-directed generation** — a Prompt Builder that turns the script + shot intent + material role into the provider prompt (replacing the hardcoded `DEFAULT_PROMPT`), **material-role binding**, and a **per-shot script-derived Akool regeneration** consumed into `final.mp4`.
   This wave is **gate-spec-first**: this document is an architect/product alignment artifact (Harness X S1/S2 class), not a gate spec; runtime cannot start until a dedicated gate spec is authored and §10-signed (see §11, §14).

---

## 2. Current Capability Baseline

Evidence as of 2026-06-08. Each capability is classified across four lenses: **proven locally**, **proven deployed**, **operator-visible**, **still weak**.

### 2.1 Akool provider mode (image_to_video)
- **Proven locally:** YES. A real Akool `image2Video` clip was generated from the tomato-beach still (`02_tomato_bowl.png`), `video_status==3` SUCCESS, downloaded, normalized to 1080×1920/30fps h264, and **consumed into `final.mp4`** as `shot02` with `render_mode=provider_image_to_video` (`MATRIX_SCRIPT_AKOOL_PROVIDER_MODE_PRODUCTION_SMOKE_20260608.md`; on python3.11 to clear the local 3.9.6 import limit). Final video: ~5.96 MB, 1080×1920, 20.0s, playable, QC passed.
- **Proven deployed:** NOT YET. The Deploy/CI smoke on the deployed Python 3.10+ runtime is **queued, not opened** (`..._MERGE_REPORT_20260608.md`).
- **Operator-visible:** PARTIAL / honest. The operator sees a capability-status chip `AI 视频生成已生成此镜头` per shot; no vendor name, no raw URL.
- **Still weak:** prompt is hardcoded (`akool_image_to_video_capability.py:80` `DEFAULT_PROMPT = "subtle natural camera motion, gentle parallax, realistic lighting"`) — **not script-directed**; only **one designated shot** (`AKOOL_SHOT_ID = shot02`) runs the provider per task to bound cost; production hardening (poll/timeout tuning, error taxonomy, concurrency, credit/cost guard) deferred. Gated by `MATRIX_SCRIPT_AKOOL_REAL` + `AKOOL_API_KEY` presence (`akool_real_gate.py`).

### 2.2 Azure voiceover
- **Proven locally + deployed-credentialed:** YES. With Azure credentials present, `voiceover_capability.synthesize_narration(...)` produced real narration (`audio_mode=azure_tts`, mean_volume −20.8 dB, `旁白已生成`) composed into `final.mp4` (`..._AKOOL_REAL_CAPABILITY_BATCH_20260608.md`). Fallback chain is honest: Azure → keyless `edge_tts` → silent fallback (never faked).
- **Operator-visible:** YES (status chip 旁白已生成 / 旁白未生成 · 缺少语音凭证).
- **Still weak:** narration text is the concatenation of per-shot `voiceover_zh`; there is no per-shot voice selection, no per-line re-synthesis, no operator-visible voice preview.

### 2.3 ffmpeg compose / QC / fallback / subtitle burn
- **Proven locally:** YES. `ffmpeg_backbone.py` provides Ken-Burns proxy (`generate_with_fallback` → static-still on failure), `compose_concat` (stream-copy concat + audio mux), and `qc_probe`/`qc_report` (resolution/codec/fps/duration_fit). Subtitles are **burned** via Pillow PNG overlay (`real_asset_scene_renderer.render_caption_png` + `overlay_caption`) **and** a sidecar `.srt` is always written. QC verdict on the composed final passed (1080×1920 / h264 / 30fps / duration_fit).
- **Operator-visible:** YES (字幕已烧录; QC reflected as operator-safe scalars).
- **Still weak:** ffmpeg is a **proxy/assembly/QC** tier, never the generative tier; `qc_report` always emits `official_publish_ready: false` (QC pass ≠ publish-ready).

### 2.4 R2 / artifact input hosting + result persistence
- **Proven locally:** YES. The input still is hosted via the existing ApolloVeo artifact path (`create_storage_service()` R2/s3 mode → `artifact_storage.upload_artifact` → `get_download_url` → presigned R2 URL the provider fetches). No new uploader; no local path sent to the provider.
- **Result-URL discipline:** the Akool result URL is **downloaded + normalized to backbone spec + composed**, then the raw temp file is deleted; the provider URL is **never** persisted as a delivery source and **never** surfaced to the operator. (This matches the Owner's "Akool result URL must be downloaded/transferred; not long-term delivery source.")
- **Still weak:** long-term result persistence of the provider clip to R2 (vs in-workspace) is deferred to a later wave.

### 2.5 V1/V2 and delivery truth + governance note
- **V1/V2:** preserved. V1 is current main; V2 is always a candidate until explicit confirm; delivery follows the confirmed main only; `official_publish_ready` remains `false` at every checkpoint (`tomato_real_result_orchestrator.py:120`).
- **Operator-visible:** the Guided Operator Workflow (#220–#227, engineering-closed) renders 看 V1 → 判断 Shot → 上传素材 → 再次生成 V2 → 对比 V1/V2 → 确认主版本 → 交付 as **presentation/projection over frozen truth**.
- **Governance honesty (load-bearing):** `CURRENT_ENGINEERING_FOCUS.md` and the unified alignment map (dated 2026-05-03) top out at the May Recovery Wave + Plan E phases; the June 2026-06-07/08 work (#245 not-merged; #247/#248 merged; Guided/Slot-v2/backbone gate specs) is **not yet folded into the root governance files** — it is governed by the June gate specs + the Harness X heavy-fast-lane execution discipline. This document does not modify those root files (forbidden by the Slot-v2 forbidden-path scan); it records the lag so the heavy-wave gate spec can re-anchor them in a separate docs-only PR.

---

## 3. Product Gap Diagnosis

Why the current result is not yet a Script-to-Video product:

1. **Generation is image-motion, not script-directed.** The Akool clip exists, but the prompt is the fixed `DEFAULT_PROMPT` camera-motion string; the script's narration / visual goal / motion intent do **not** shape the provider payload. The narration and subtitles are script-derived; the *picture generation* is not. (`akool_image_to_video_capability.py:80,233`.)

2. **The UI does not expose shot intent or storyboard control.** The Workbench renders §A 主视频预览 + §B per-shot **material cards** keyed by `shot_id`, but there is no visible storyboard whose *generation intent* (visual goal, motion instruction, AI generation requirement) is shown or editable. The video-capability-upgrade review (2026-06-07) states it plainly: the line "has exactly one real production lever (visual material in/out)"; "no amount of queue/panel re-arrangement (Slot Workflow v2) fixes this."

3. **Material replacement is not role-bound.** Material is stored as a flat `shot_id → {material_ref, material_name, material_kind, intent}` map (`operator_workbench_view.py`, `matrix_script_material_replacement_intents`); intent is `keep / replace / supplement`. There is **no semantic role** (product / scene / character / style), so the system cannot use "this is the product reference" vs "this is the scene background" to shape generation.

4. **BGM / subtitle / voice controls are not real operator controls.** They are honest status today: BGM = `配乐未选择`; subtitle style + voice are display/future slots with no operator-effective backend action (slot-v2 classification; capability-upgrade review §2). They label capability honestly but are not levers.

5. **The operator cannot edit the generation requirement before spending a provider call.** There is no "AI 生成要求" the operator can read/rewrite before regenerating; regeneration today is whole-task with a fixed single-shot provider call. The Kapwing benchmark's core value — *plan before generation* — is absent (Kapwing advice §3.2, §4.1).

6. **The current workbench is not a Kapwing-like Script-to-Video flow.** It is `task → status → result` (material cards + stitched clips), not `script → plan → confirm → generation → editable output → export` (Kapwing advice §2 verdict). Slot Workflow v2 fixes the *navigation* (queue + single active panel) but is explicitly **presentation-only** and does not make generation script-directed.

---

## 4. Product Flow v2 Interpretation

Translating `matrix_script_product_flow_v2_delta.md` (+ Kapwing advice + presenter/contract alignment) into implementation terms:

- **First product object = generation plan.** The plan (storyboard / scene-by-scene) is the artifact the operator confirms before heavy generation. Surfaced as Workbench **§C 视频生成计划**; view-model = `generation_plan_view` (presenter alignment §6.2).
- **Plan review before heavy generation.** The operator edits the plan per scene; the system fires the heavy worker once with the confirmed plan; a wrong scene is fixed by editing that scene and re-running that scene — not the whole video (v2-delta §4).
- **Scene-by-scene editable storyboard.** Per-scene fields: script segment / visual intent / background / B-Roll / product material slot / role / voiceover line / subtitle line / music mood / aspect ratio (presenter §6.2 per-scene row).
- **Video-level variants, not axis tuples.** Each variant is a video version answering 哪里不同？ / 为什么测？ / 推荐？ (`differentiator_zh` / `why_test_zh` / `is_recommended`); axis tuples move to the architect-only J fold (v2-delta §5).
- **Workbench 10-section IA (A–J).** A 主视频结果 / B 脚本理解 / C 视频生成计划 / D 画面与素材 / E 角色与声音 / F 字幕与音乐 / G 视频变体 / H 校对与微调 / I 交付入口 / J 技术诊断. **New value merges into these sections — never a parallel flow** (Anti-Sprawl rule 4).
- **J diagnostics collapsed.** Engineering identifiers, raw enums, raw handles, raw manifest/JSON live only in J, collapsed by default (Design Authority Index rule 5; slot-v2 §7).
- **No vendor/model/provider in operator UI.** Validator R3 + v2-delta §9 + slot-v2 §7. Operator picks intent in operator language; the runtime binds providers.
- **VoiceTrans and Digital Anchor remain consumer/provider bridges, not embedded forms.** VoiceTrans = future audio/language provider behind a contract bridge (v2-delta §6); Digital Anchor = future role/presenter asset provider, consumed-only inside §E (v2-delta §7). Neither is embedded as an iframe/raw form; role authoring happens in Digital Anchor, voice fulfilment at the runtime layer.

---

## 5. Target Architecture

The target chain and, per stage: **owner layer**, **source of truth**, **current implementation**, **gap**, **next implementation step**.

```
Script
 → Script Understanding
 → Generation Plan / Storyboard
 → Shot Control
 → Material Role Binding
 → Provider Fulfillment
 → Compose / QC
 → V1 / V2 Review
 → Delivery
```

### 5.1 Script
- **Owner layer:** Layer 1 input (`factory_input`); entry route.
- **Source of truth:** `factory_input` `source_asset_references` (script-as-asset) + `source_script_ref` (opaque handle; `matrix_script` requires `source_script` per asset-supply matrix).
- **Current impl:** `/tasks/matrix-script/new` create-entry; opaque-ref discipline (4-scheme set; F2 minting flow landed).
- **Gap:** entry CTA still reads `创建任务` not `生成视频方案`; product/material/preference fields are presenter-only (not captured).
- **Next step:** entry-page evolution per presenter alignment §5 (CTA rename, presenter-only preference fields stored in `operator_intent_map`) — **not** in the first heavy slice; recorded.

### 5.2 Script Understanding
- **Owner layer:** Layer 2/3 projection (`factory_content_structure`).
- **Source of truth:** `script_structure_view` (Hook/Body/CTA/taxonomy).
- **Current impl:** **supported now** — Workbench §B step 1 renders Hook/Body/CTA.
- **Gap:** 卖点 (selling points) has no helper field; presenter stub only.
- **Next step:** promote to full §B section; stub 卖点 (presenter-only). Low risk; can ride the heavy slice or precede it.

### 5.3 Generation Plan / Storyboard
- **Owner layer:** Layer 3 plan object (`factory_scene_plan`).
- **Source of truth:** `generation_plan_view` (presenter alignment §6.2), reading the line packet's **additive** `scene_plan_binding` (contract alignment §3.3) once it lands; **projection-only placeholder** (`plan_pending_upstream` / `plan_resolved_placeholder`) until then.
- **Current impl:** **none as an operator surface.** The closest internal object is the deterministic shot plan: `MatrixScriptShotPlan` + `MatrixScriptShotSpec{shot_id, order, duration_seconds, role?, visual_intent, action, scene_context, asset_need, audio_text, subtitle_text, generation_mode, blocking}` (`shot_plan.py`), `GENERATION_MODES = {static_asset, image_to_video, avatar_segment, broll, title_card, cta_card}`. The tomato path uses fixed `TomatoShot{shot_id, order, title_zh, visual_intent_zh, voiceover_zh, subtitle_zh, asset_filename, source, focus, zoom, real_visual, semantic_match}`.
- **Gap:** the internal shot plan is **not projected** to an operator storyboard; no `generation_plan_view`; no `scene_plan_binding`.
- **Next step:** implement `generation_plan_view` as a **projection** over the existing shot plan + entry intent (no contract change first — see §7). This is the heart of the heavy wave's §C surface.

### 5.4 Shot Control
- **Owner layer:** Layer 3 surface (Workbench §B / §C).
- **Source of truth:** Slot Workflow v2 model — Shot (read-only structure) / Slot (typed fill-point) / Assignment (only operator-mutable object), over #211–#215 projection truth.
- **Current impl:** **specified, not implemented.** Slot Workflow v2 gate spec is ACCEPTED-PENDING-SIGNOFF (§13). Guided Workflow per-shot cards are the v1 substrate.
- **Gap:** the scalable Shot Queue + single Current Shot Work Panel is not built; §13 signoff not merged.
- **Next step:** Slot Workflow v2 PR-1..PR-3 (presentation-only) is the prerequisite navigation skeleton. The heavy wave **adds the generation-intent fields** (visual goal / motion / AI 生成要求 / negative) into the Current Shot Work Panel — but those fields are new operator value and require their own gate (see §8, §11).

### 5.5 Material Role Binding
- **Owner layer:** Layer 1 input + line-specific binding.
- **Source of truth:** asset-supply matrix closed kinds + commercial-status codes (`commercial_ok / commercial_review / operator_upload`, contract alignment §3.4); proposed `material_role` (see §9).
- **Current impl:** flat `shot_id → {material_ref, material_name, material_kind, intent}` (`operator_workbench_view.py`); **no role semantics.**
- **Gap:** no product/scene/character/style role; role does not shape generation.
- **Next step:** add a `material_role` projection (presenter-first; see §9), bound per shot, that the Prompt Builder consumes.

### 5.6 Provider Fulfillment
- **Owner layer:** Layer 3 runtime worker (capability adapters / routing).
- **Source of truth:** capability kinds (`understanding / video_gen / dub / post_production / pack / variation`), never vendor names (validator R3).
- **Current impl:** Akool `image_to_video` for one shot (`akool_image_to_video_capability.py`); Azure TTS (`voiceover_capability.py`); gated by `MATRIX_SCRIPT_AKOOL_REAL`.
- **Gap:** prompt is hardcoded, not script-derived; single-shot only; no per-shot regenerate route.
- **Next step:** wire the Prompt Builder output (script-derived) into the provider payload (replacing `DEFAULT_PROMPT`); add one controlled per-shot script-directed regeneration (see §10, §11).

### 5.7 Compose / QC
- **Owner layer:** Layer 3 post-production (`post_production`).
- **Source of truth:** `ffmpeg_backbone.compose_concat` + `qc_probe`/`qc_report`.
- **Current impl:** **proven.** Concat + audio mux + subtitle burn + QC (resolution/codec/fps/duration_fit); honest fallback (proxy → static still).
- **Gap:** none structural; QC always `official_publish_ready=false` (correct).
- **Next step:** no change required by the heavy wave beyond consuming the script-directed clip; preserve QC + fallback evidence.

### 5.8 V1 / V2 Review
- **Owner layer:** Layer 3/4 (review + readiness).
- **Source of truth:** preview-version compare (V1 current_main / V2 candidate); review-zone closure path.
- **Current impl:** **supported** (Guided Workflow C区 + Slot-v2 C区 batch entry; `data-preview-version="V1|V2"`).
- **Gap:** the per-shot **change explanation** ("哪些镜头变了，为什么") is present in the Guided/v2 substrate but must be extended to explain *script-directed* regenerations.
- **Next step:** extend the V1/V2 compare to attribute each changed shot to its Assignment + generation requirement (presenter-only).

### 5.9 Delivery
- **Owner layer:** Layer 1/4 (`factory_delivery` + `publish_readiness`).
- **Source of truth:** `publish_readiness` single producer; `delivery_comprehension` lanes (必交付·阻塞 / 必交付·不阻塞 / 可选·不阻塞).
- **Current impl:** **supported.** Delivery follows confirmed main; `正式交付就绪：否`; `official_publish_ready=false`.
- **Gap:** none for this wave.
- **Next step:** no change; the heavy wave MUST preserve delivery truth exactly.

---

## 6. Provider Capability Mapping

Providers are **backend capability fulfillers**, mapped to capability **kinds**, never to operator-facing selectors.

| Provider | Capability kind(s) | Role |
|---|---|---|
| **Gemini** | `understanding`, (`variation` assist) | script understanding, storyboard/plan generation, prompt rewrite, language rewrite. (Product flow v1 §8.1: "参考视频理解、内容标签、脚本结构辅助、风险提示".) **Not yet wired for storyboard/prompt in Matrix Script runtime.** |
| **Akool** | `video_gen` (`image_to_video`), future `avatar` / `face_swap` | primary video / image-to-video provider. Proven for one shot (§2.1). |
| **Azure** | `dub` | voiceover / TTS. Proven real (§2.2). |
| **ffmpeg** | `post_production` | compose, QC, fallback, subtitle burn, normalization. Proven (§2.3). Local, secret-free. |
| **R2 / artifact** | (storage substrate) | input hosting (presigned URL the provider fetches) + result persistence in workspace. Proven (§2.4). |
| **VoiceTrans** (future) | `dub` / `language` bridge | future audio / language provider via contract bridge (Phase 4, v2-delta §6). Never embedded raw. |
| **Digital Anchor** (future) | `avatar` / role provider | future role / presenter asset provider, consumed-only inside §E (Phase 4+, v2-delta §7). Role authoring stays in Digital Anchor. |

**Binding provider discipline (restated for the heavy wave):**
- **No provider selector in the primary UI.** Operator expresses intent in operator language; `capability_routing_policy` (runtime) selects the realization. (Validator R3; asset-supply decoupling rule 4 "mode is descriptive, not selective"; slot-v2 §7.)
- **Provider failure is per-shot fallback evidence**, surfaced in operator language (e.g. `AI 视频生成已生成此镜头` vs an honest fallback label), never as a vendor error or a broken clip. Fallback tier (ffmpeg proxy → static still) is automatic and honest.
- **Akool result URL must be downloaded / transferred — not a long-term delivery source.** The provider URL is consumed into `final.mp4` and discarded; it never persists as delivery truth and never surfaces to the operator.

---

## 7. Generation Plan Object

The object the wave needs. Field classification: **[S]** system-generated · **[O]** operator-editable · **[R]** runtime-only · **[D]** diagnostics-only.

| Field | Class | Meaning / source |
|---|---|---|
| `plan_id` | [S] | deterministic plan identity (mirrors `MatrixScriptShotPlan.plan_id`). |
| `shot_id` | [S] | per-shot identity (mirrors `MatrixScriptShotSpec.shot_id`). |
| `shot_order` | [S] | 1-based order (mirrors `order`). |
| `shot_title` | [S→O] | operator-language title (tomato path has `title_zh`; general path derives from `action`+`scene_context`). |
| `script_segment` | [S] | the script line for this shot (projection of structure segment). |
| `narration_line` | [S→O] | voiceover line (`audio_text` / `voiceover_zh`); operator may tune copy in a later gated phase. |
| `visual_goal` | [S→O] | operator-language visual intent (`visual_intent` / `visual_intent_zh`). |
| `subject` | [S→O] | the focal subject of the shot (e.g. 产品 / 人物 / 场景). **New presenter field; no code equivalent today.** |
| `scene_context` | [S→O] | scene/background context (mirrors `scene_context`). |
| `motion_instruction` | [S→O] | desired motion (push-in / pan / handheld follow). **New presenter field**; today motion is implicit in `generation_mode` / Ken-Burns zoom. |
| `material_requirements` | [S] | what material this shot needs (kind + role). |
| `material_role` | [S→O] | semantic role (see §9). **New**; today material is role-less (`intent` only). |
| `selected_material_ref` | [O] | the bound material (friendly label only; never raw `msmaterial://` / `asset://`). |
| `provider_capability_kind` | [R] | capability kind (`image_to_video` etc.); **never a vendor name** in operator copy. |
| `provider_prompt` | [R] | the prompt sent to the provider, built by the Prompt Builder (§10). **Runtime-transient — NOT stored on the shot plan** (`shot_plan.py:71–81` forbids a `provider_prompt` field by design; it appears operator-side only as the operator-safe "AI 生成要求" summary). |
| `negative_prompt` | [R] | provider negative constraints; runtime-transient, operator-side as a readable summary. |
| `duration_seconds` | [S→O] | shot duration (mirrors `duration_seconds`). |
| `aspect_ratio` | [S→O] | 9:16 / 16:9 / 1:1 (plan-level `aspect_ratio`; per-shot is operator intent only). |
| `generation_status` | [R→D] | per-shot status (`provider_success` / `fallback_proxy` / `credential_missing` …); operator sees an operator-language chip, raw enum in J. |
| `fallback_reason` | [D] | why a fallback tier was used; diagnostics fold only. |
| `accepted_state` | [O] | operator acceptance of the shot (maps to Assignment + V1/V2 confirm). |

**Projection-only-first verdict (answering the Owner's §7 question):** **YES — the generation plan can be projection-only first, without any schema/contract change.**
- The plan view (`generation_plan_view`) is a **pure projection** over the already-existing shot plan + entry intent; the contract alignment (§3.3) reserves `scene_plan_binding` as an **additive** line-packet field for a later Phase 3 — until then the presenter renders a `plan_resolved_placeholder` from existing fields.
- New operator-intent fields (`subject`, `motion_instruction`, `material_role`, edited copy) ride in the additive `operator_intent_map` (contract alignment §3.2; presenter-only; empty-map fallback preserves current behavior) — **no closed-enum widening, no generic-contract change.**
- `provider_prompt` / `negative_prompt` are **runtime-transient** (built per call, never stored on the plan, never operator-facing as raw text) — so no contract field is added and `shot_plan.py`'s forbidden-token discipline is preserved.

The **only forced backend touch** is: (a) the Prompt Builder function, and (b) wiring its output into the Akool capability call in place of `DEFAULT_PROMPT`, and (c) one per-shot script-directed regeneration path. Everything else is projection.

---

## 8. Current Shot Workbench Product Design

This converges the **Slot Workflow v2** Current Shot Work Panel (already gated, pending §13 signoff) with the **generation-intent** fields the heavy wave adds. All of it re-homes into Workbench **§B/§C** of the A–J IA — no parallel flow.

### A. Storyboard Queue (= Slot Workflow v2 Compact Shot Queue, §3.B.1)
- compact row per shot — one short scannable row, readable at 10+ shots; exactly one active shot.
- **status chip** — closed operator-language set (`待处理 / 已上传素材 / 已跳过 / 已进入 V2 / 无需处理`), mapped from existing per-shot truth.
- **role / material chip** — friendly material label + (new) material-role chip (§9); never a raw handle.
- **provider / fallback chip in operator language** — `AI 视频生成已生成此镜头` vs honest fallback (`本镜头使用基础合成` etc.); never a vendor name or URL.
- per-shot **R-SHOT-REASON** one-liner only when flagged.

### B. Current Shot Panel (= Slot Workflow v2 Current Shot Work Panel, §3.B.2–§3.B.4, EXTENDED)
Operator-language fields:
- **镜头目标** (visual goal) — `[S→O]`
- **画面动作** (motion instruction) — `[S→O]` (new)
- **旁白** (narration line) — `[S]` display; copy-edit gated to a later phase
- **字幕重点** (subtitle focus / keyword highlights) — `[S]` display
- **素材角色** (material role, §9) — `[S→O]` (new)
- **AI 生成要求** (operator-safe generation requirement = the Prompt Builder's operator summary, §10) — `[S→O]` **(new; the central new operator value)**
- **负面约束** (negative constraints, operator-safe summary) — `[S→O]` (new)
- **当前生成结果** (current shot result: provider/fallback chip + clip status) — `[R→display]`
- operation buttons:
  - **改写生成要求** (rewrite the generation requirement) — opens the operator-safe AI 生成要求 / 负面约束 for editing; recorded as Assignment intent.
  - **替换素材** (replace material) — the Slot Workflow v2 `visual_material_slot` Assignment (use / supplement / replace + upload primary; advanced binding folded). This is the **only actionable material slot** (slot-v2 §6).
  - **重新生成这个镜头** (regenerate this shot) — see §11 / §12.11 for the route decision.
  - **接受这个镜头** (accept this shot) — records `accepted_state` on the Assignment.

Honesty discipline carried verbatim from Slot Workflow v2 §6/§7: `text_copy_slot` / `subtitle_slot` are **display-only** (no edit control); `voiceover_slot` / `bgm_slot` are **future workflow** (status line only, **no button, not even disabled**). The new **AI 生成要求** field is actionable **only** because it drives the one real generation lever (the visual/`image_to_video` slot). If it is not yet wired for a given shot, it renders an honest `尚未接入` status, never a dead control.

### C. V1/V2 Compare (inherits Slot Workflow v2 §3.C + §4/§5)
- **show what changed by shot** — list the shots that entered V2 and attribute each to its Assignment + (new) generation-requirement change.
- **current main stays V1 until confirm** — explicit V1/V2 dual-state copy (slot-v2 C-1 fix): an existing V2 candidate is updated by batch regenerate (not a new parallel version); V1 + delivery unchanged before an explicit `确认 V2 为主版本`.
- **delivery follows confirmed main only** — unconfirmed V2 is never the delivery candidate; `正式交付就绪：否`; `official_publish_ready=false`.

---

## 9. Material Role Binding

Define material **roles** (the semantic binding the Prompt Builder consumes). Today material is role-less (`intent` only); roles are a **new presenter projection** (additive `operator_intent_map`, no schema change first).

| Role | Meaning | Drives prompt as |
|---|---|---|
| `product_reference` | the product to feature faithfully | "preserve product shape/color/label; feature prominently" |
| `character_reference` | a person / presenter appearance | "keep the person's appearance consistent; natural skin/hands" |
| `scene_reference` | background / environment | "place in / match this scene; environment continuity" |
| `style_reference` | look-and-feel / palette / mood | "match this visual style / palette / lighting mood" |
| `replacement_image` | a direct still to animate for this shot | "animate this still; honor its framing" |
| `broll_candidate` | supplemental cutaway footage | "cutaway B-Roll; not the hero subject" |

Each role carries a closed **commercial-status** code (`commercial_ok / commercial_review / operator_upload`, contract alignment §3.4); roles map to the asset-supply matrix closed input kinds (`source_video / source_script / business_metadata` …) and never name a donor (asset-supply decoupling rule 1).

**Tomato pilot binding:**
- tomato bowl (`02_tomato_bowl.png`) = **`product_reference`** → "preserve the cherry tomatoes' shape, color, glossy surface; feature prominently."
- beach = **`scene_reference`** (scene_context) → "seaside / warm afternoon light environment continuity."
- eating / lifestyle image = **`character_reference` + `product_reference` (mixed)** where applicable → "person tasting the product; keep both the product and the natural human action faithful."

**How role drives the prompt:** the Prompt Builder (§10) reads `material_role` + `selected_material_ref` and emits the corresponding preservation/placement clause + the matching negative constraints (e.g. `product_reference` ⇒ negative "distortion, warping, label change"; `character_reference` ⇒ negative "face distortion, extra fingers"). Role is the bridge from "what this material *is*" to "how the picture must be generated."

---

## 10. Prompt Builder Design

How the script becomes a provider prompt. The Prompt Builder is a **pure, deterministic backend function** (no network, no secret, no clock) that composes three outputs from script-derived shot fields + material role.

**Inputs:** `script_segment`, `narration_line`, `visual_goal`, `motion_instruction`, `material_role`, `selected_material` (label + role + commercial status), product-preservation constraints (derived from role), `negative_prompt` (derived from role + global rules), `aspect_ratio`, `duration_seconds`.

**Outputs (three, separated by audience):**
1. **operator-safe prompt** — the "AI 生成要求" the operator reads/rewrites in §8.B; operator language; **no vendor name, no raw URL, no secret**.
2. **provider payload** — the actual provider prompt string + negative prompt + image_url (the presigned R2 URL), assembled at call time and **never surfaced to the operator**; replaces `akool_image_to_video_capability.py:80` `DEFAULT_PROMPT`.
3. **diagnostic summary** — operator-language one-liner for the queue/diagnostics (e.g. "镜头2 · 产品特写 · 使用产品素材 · 推近运动"); raw payload only in J.

**Example A — product close-up tomato bowl**
- Inputs: `visual_goal=产品特写 · 突出果实饱满与光泽`; `narration_line=颗颗饱满，海边阳光下的圣女果`; `motion_instruction=缓慢推近 + 轻微视差`; `material_role=product_reference` (tomato bowl).
- Operator-safe prompt (AI 生成要求): *"小番茄产品特写，海边暖色阳光，缓慢推近 + 轻微视差；保持果实形状、颜色与光泽真实；竖屏 9:16。"*
- Provider payload prompt (runtime-only): `"Close-up of a bowl of cherry tomatoes by the seaside in warm afternoon light; slow push-in with gentle parallax; keep the tomatoes' shape, color and glossy surface faithful; cinematic, realistic lighting, vertical 9:16."`
- Negative prompt (runtime-only): `"distortion, warping, label change, extra hands, text, watermark, logo, oversaturation"`.

**Example B — lifestyle eating tomato**
- Inputs: `visual_goal=生活化品尝 · 真实人物`; `narration_line=一口咬下，汁水四溢`; `motion_instruction=手部递近 + 轻微跟随`; `material_role=character_reference + product_reference`.
- Operator-safe prompt (AI 生成要求): *"生活化品尝小番茄的真实瞬间，海边自然光，手部递近 + 轻微跟随；保持人物自然、产品真实；竖屏 9:16。"*
- Provider payload prompt (runtime-only): `"A person tasting a juicy cherry tomato at the beach, candid natural moment, gentle handheld follow motion, realistic skin and food texture, warm light, vertical 9:16."`
- Negative prompt (runtime-only): `"face distortion, extra fingers, product warping, text, watermark, unnatural color"`.

No secrets, no provider raw result URL, and no API key appear in any of the three outputs. The operator-safe prompt and diagnostic summary are the only operator-visible artifacts.

---

## 11. Heavy Engineering Batch Plan

**Name:** **Matrix Script Storyboard Control + Shot Workbench Batch.**

This is the convergence wave. It is **gate-spec-first**: this document is an alignment artifact (Harness X S1/S2 class); the batch opens only after (a) Slot Workflow v2 §13 signoff merges (the presentation skeleton), and (b) a **dedicated heavy-wave gate spec** for the script-directed-generation pieces is authored and §10-signed (the parts that cross the presentation-only boundary). The capability-upgrade review (2026-06-07) already points at this path: "Author a Gate Spec for the first capability kind to integrate (likely the upgraded `image_to_video` … + `compose`/`qc`), behind the internal contract, no vendor in UI, four-layer boundary preserved. Owner-gated S5→S6."

**Scope:**
- **generation plan projection / service** — `generation_plan_view` over the existing shot plan + entry intent (projection-only first; §7).
- **prompt builder** — pure deterministic function (§10); operator-safe prompt + runtime payload + diagnostic summary.
- **current shot workbench UI** — extend the Slot Workflow v2 Current Shot Work Panel with 镜头目标 / 画面动作 / 素材角色 / AI 生成要求 / 负面约束 (§8.B), inside §B/§C of the A–J IA.
- **material role binding** — `material_role` projection (§9), presenter-first via `operator_intent_map`.
- **one controlled Akool regeneration** — a single per-shot, script-derived provider call (Prompt Builder output → Akool payload, replacing `DEFAULT_PROMPT`), consumed into `final.mp4`, gated by `MATRIX_SCRIPT_AKOOL_REAL`.
- **V1/V2 shot-change explanation** — attribute each changed shot to its Assignment + generation requirement (presenter-only).

**Allowed files (expected):**
- `gateway/app/services/matrix_script/operator_workbench_view.py` (presentation projection: plan view, role chip, AI 生成要求 summary).
- a new Matrix-Script-scoped `gateway/app/services/matrix_script/generation_plan_view.py` (projection) and a new `gateway/app/services/matrix_script/prompt_builder.py` (pure function).
- `gateway/app/services/matrix_script/akool_image_to_video_capability.py` (consume the built prompt instead of `DEFAULT_PROMPT`; honest status unchanged).
- `gateway/app/services/matrix_script/tomato_real_result_orchestrator.py` (wire the Prompt Builder + per-shot regeneration; preserve fallback/QC/`official_publish_ready=false`).
- `gateway/app/templates/task_workbench.html` (matrix_script §B/§C extension only; A–J preserved; J holds raw).
- Matrix Script tests under `gateway/app/services/tests/` (prompt-builder unit tests, projection tests, no-leak tests, role-binding tests, one provider-mode smoke).
- one route only **if** per-shot regenerate is chosen over the documented existing whole-task route (see §12.11) — to be decided in the gate spec.

**Expected tests:** prompt-builder determinism + operator-safe/no-secret assertions; `generation_plan_view` projection shape; material-role projection; no-leak (`_assert_clean`) on the new fields; V1/V2 preservation; one controlled Akool script-directed smoke producing a consumed clip; `official_publish_ready=false` at every checkpoint.

**Explicit non-goals (forbidden):**
- no provider selector in UI;
- no `official_publish_ready=true`;
- no delivery-truth change;
- no full timeline editor;
- no Digital Anchor authoring (consumer-only stub at most);
- no VoiceTrans embedded form;
- no broad schema / contract change unless **forced** (and any forced additive change is a separate, gated, contract-first step — not bundled);
- no Hot Follow / Digital Anchor / `artifact_storage.py` / `schemas/` / `docs/contracts/` touch beyond what a separately-gated additive step authorizes;
- no second source of truth; no new readiness producer.

---

## 12. Acceptance Criteria

The heavy batch (and its gate spec) MUST satisfy:

1. A fresh Matrix Script task has a **storyboard queue** (compact, scannable, one row per shot).
2. A **current shot panel** is visible (single active shot).
3. The operator sees the shot's **visual goal, motion instruction, material role, and AI generation prompt** (operator-safe "AI 生成要求").
4. One shot is **generated by Akool from a script-derived prompt + hosted material** (not the hardcoded `DEFAULT_PROMPT`).
5. That clip is **consumed into `final.mp4`**.
6. **Azure voiceover is audible** in `final.mp4`.
7. **Subtitles are visible** (burned + sidecar).
8. **V1/V2 semantics are preserved** (V1 main until explicit confirm; delivery follows confirmed main).
9. **`official_publish_ready=false`.**
10. **No vendor / secret / raw provider URL leak** (operator surface passes `_assert_clean` + dedicated no-secret test).
11. **Operator can trigger regenerate-this-shot**, OR the batch documents the exact route. *Route note (documented now):* today regeneration is whole-task (`POST /api/matrix-script/{task_id}/tomato-real-result` and `/regenerate-preview`), and the provider runs only for `AKOOL_SHOT_ID = shot02`. There is **no per-shot regenerate route today.** The gate spec must either (a) add a per-shot script-directed regenerate route, or (b) bind the single active shot's Assignment to the existing whole-task regenerate with the active shot as the designated provider shot — and state which, with tests.

---

## 13. Risk / Boundary

| Risk | Classification | Mitigation |
|---|---|---|
| New additive line-packet fields tempt a schema/contract change | **schema/contract boundary** | projection-first (§7); any forced additive change is a separate contract-first gated step, never bundled. |
| Per-shot regenerate may need a new route | **route boundary** | gate spec decides (a) new route vs (b) reuse whole-task regen (§12.11); router stays thin (`ENGINEERING_RULES` §3). |
| Real provider calls cost money / are slow | **provider cost/latency** | one controlled shot per task (keep `AKOOL_SHOT_ID` bounding); add credit/cost guard + poll/timeout tuning (capability-upgrade review §1); fast-preview proxy tier remains the cheap iteration path. |
| Adding §B/§C fields could regress the A–J / Slot-v2 surface | **UI complexity** | extend, do not restructure (Anti-Sprawl rule 4); honest slot classification preserved; J holds raw. |
| Prompt / payload / result URL could leak | **secret leakage** | three-output separation (§10); operator sees only the operator-safe summary; `_assert_clean` + no-secret test; result URL downloaded + discarded. |
| Old manifest / stale task could mislead | **stale task / old manifest** | preserve the #203 async/stale-guard baseline; projection reads current truth only. |
| Local-only proof ≠ deployed proof | **deploy parity** | Akool full clip is proven local (python3.11); the Deploy/CI smoke on Python 3.10+ is queued and is a precondition for any deployed-trial claim. |
| Root governance lag (§2.5) | **governance** | heavy-wave gate spec re-anchors `CURRENT_ENGINEERING_FOCUS` / unified map in a separate docs-only PR; this document does not touch them. |

---

## 14. Owner Decision Needed

Choose one:

- **APPROVE heavy engineering batch** — authorize authoring the **Matrix Script Storyboard Control + Shot Workbench Batch gate spec** (docs-only, §10-signoff-gated), which on signoff opens RC-style sliced implementation per §11. (This does **not** itself start runtime; it starts the gate-spec authoring.)
- **REVISE alignment** — redirect the product/architecture/provider framing in §1–§10 before any gate spec is authored.
- **HOLD** — keep the proven capability substrate (Akool/Azure/ffmpeg/R2) as-is; do not open the storyboard-control wave yet.

Recommended: **APPROVE** (author the gate spec), because the substrate is proven and the remaining gap is precisely the script-directed generation + storyboard control this document scopes. But the Owner裁决 is the gate.

---

## 给 Claude 的指令 (next-step command block — DO NOT IMPLEMENT YET)

```
IF Owner = APPROVE:

  Step 1 (docs-only, gate-spec-first):
    Author docs/design/MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_<date>.md
      - cite Bucket A + Slot Workflow v2 gate spec + ffmpeg backbone gate spec
        + the capability-upgrade review as authority; do NOT supersede Bucket A.
      - freeze: §C generation_plan_view projection (projection-only first, no schema change),
        prompt_builder (pure function, three outputs, no secret), material_role binding
        (operator_intent_map, additive), one controlled script-directed Akool regen,
        per-shot regenerate route decision (§12.11), V1/V2 shot-change explanation.
      - honest slot classification preserved; A区/C区/D区/E区 inherit; new fields in §B/§C only.
      - acceptance rows = §12 (1..11) + no-leak + no-second-truth + official_publish_ready=false.
      - PR slicing (recommended): PR-1 generation_plan_view projection + storyboard queue fields;
        PR-2 prompt_builder + AI 生成要求 panel (operator-safe) ; PR-3 material_role binding;
        PR-4 one controlled script-directed Akool regen + V1/V2 change explanation; PR-5 closeout.
      - §10 architect + reviewer signoff block = <fill>; coordinator + PM bind closeout.
    Then STOP. Do not open PR-1 until §10 signoff merges.

  Step 2 (only after §10 signoff merges, Owner-gated S5->S6 per slice):
    Open PR-1 only. Each subsequent slice is its own Owner-gated decision.

  Forbidden in every slice: provider selector in UI; official_publish_ready=true;
  delivery-truth change; full timeline editor; Digital Anchor authoring;
  VoiceTrans embedded form; Hot Follow / Digital Anchor / artifact_storage.py /
  schemas/ / docs/contracts/ touch (beyond a separately-gated additive step);
  second source of truth; vendor/secret/raw provider URL in operator surface.

IF Owner = REVISE: redirect §1–§10 here; re-issue this alignment.
IF Owner = HOLD: stop; substrate stays as-is.
```

---

*This is a docs-only architecture/product alignment. It implements nothing, opens no wave, supersedes no authority, and advances no signoff. Runtime begins only after a dedicated gate spec is authored and §10-signed, one slice at a time, under the standard discipline.*
