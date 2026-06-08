# Owner Summary — Matrix Script Storyboard-to-Video Architecture Alignment

Date: 2026-06-08
Type: **Docs-only alignment pass.** No code / template / router / schema / contract / test / runtime change. No implementation opened.
Full document: `docs/design/MATRIX_SCRIPT_STORYBOARD_TO_VIDEO_ARCHITECTURE_ALIGNMENT_20260608.md`

---

## Decision

- **v1 stays the business spine** (`matrix_script_product_flow_v1.md`).
- **v2 delta is ACCEPTED as the current Script-to-Video product amendment direction** (generation plan as first-class object; A–J ten-section Workbench; video-level variants; VoiceTrans/Digital Anchor as future provider bridges).
- **Akool / Azure / ffmpeg / R2 are capability substrate, not the final product flow.**
- **The next heavy wave builds Generation Plan + Storyboard Control + Current Shot Workbench**, driven by product flow v2 — converging the already-specified Slot Workflow v2 (Shot Queue + Current Shot Panel) and `generation_plan_view`, plus the **genuinely new** piece: **script-directed generation** (Prompt Builder + material-role binding + per-shot script-derived Akool regeneration). It is **gate-spec-first**; this document authorizes no runtime.

## Source files read (representative; full list in alignment doc §0)
- Root/rules: `ENGINEERING_RULES.md` (§1–§13), `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`, `MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`, unified alignment map.
- Product: `matrix_script_product_flow_v1.md`, `..._v2_delta.md`, `asset_supply_matrix_v1.md`.
- Design/benchmark: `matrix_script_kapwing_benchmark_product_advice_v1.md`, `..._presenter_alignment_v1.md`, `MATRIX_SCRIPT_SLOT_WORKFLOW_V2_PRODUCT_PLAN/GATE_SPEC_20260607.md`, ffmpeg backbone gate spec.
- Architecture/contract: `matrix_script_script_to_video_contract_alignment_v1.md`.
- Execution/review: real-video batch (#245), Akool real capability (#247), Akool provider-mode smoke + merge (#248), guided-workflow closeout, video-capability-upgrade review, slot-workflow-v2 operator review, + the requested owner summaries.
- Runtime/code: `matrix_script/` services (`shot_plan.py`, `tomato_real_result_orchestrator.py`, `akool_image_to_video_capability.py`, `akool_real_gate.py`, `voiceover_capability.py`, `ffmpeg_backbone.py`, `operator_workbench_view.py`), `providers/akool/client.py`, `task_workbench.html`.
- **Honestly missing (named in the brief, do not exist):** `docs/product/hot_follow_product_flow_v1.md`; `docs/design/MATRIX_SCRIPT_MATERIAL_TO_V2_VISIBLE_CLOSURE_GATE_SPEC_20260607.md`; `docs/reviews/MATRIX_SCRIPT_OPERATOR_VALUE_GAP_REVIEW_20260607.md`; the smoke file is `..._SMOKE_20260608.md` (no `_REPORT`). Nearest-equivalent authorities were read instead.

## Current baseline (2026-06-08)
- **Akool image_to_video:** proven **locally** (real clip → consumed into `final.mp4` as shot02, 1080×1920, playable); deployed smoke **queued, not opened**. Prompt is hardcoded (`DEFAULT_PROMPT`), single shot, gated by `MATRIX_SCRIPT_AKOOL_REAL`.
- **Azure voiceover:** proven real (`audio_mode=azure_tts`, −20.8 dB, 旁白已生成); honest fallback chain.
- **ffmpeg compose/QC/subtitle-burn/fallback:** proven; QC always `official_publish_ready=false`.
- **R2/artifact:** input still hosted via presigned R2 URL; Akool result downloaded + normalized + composed, then discarded — never a delivery source, never operator-visible.
- **V1/V2 + delivery:** preserved; `official_publish_ready=false`.
- **Governance note:** root governance files (`CURRENT_ENGINEERING_FOCUS`, unified map) are stale vs the June work; the June batches are governed by the June gate specs, not yet folded into root governance.

## Gap
1. Generation is **image-motion, not script-directed** (hardcoded prompt; script doesn't shape the picture).
2. UI exposes **material cards, not storyboard / shot intent**.
3. Material replacement is **not role-bound** (intent only; no product/scene/character/style role).
4. **BGM/subtitle/voice are honest status, not real operator controls.**
5. Operator **cannot edit the generation requirement before spending a provider call.**
6. The workbench is **`task→status→result`, not `script→plan→confirm→generate→edit`.** Slot Workflow v2 fixes navigation but is presentation-only; the capability-upgrade review confirms "no amount of queue/panel re-arrangement fixes this."

## Target architecture
`Script → Script Understanding → Generation Plan/Storyboard → Shot Control → Material Role Binding → Provider Fulfillment → Compose/QC → V1/V2 Review → Delivery.` Per-stage owner layer / source of truth / current impl / gap / next step are in alignment doc §5. The plan, role, and prompt are **projection-only first** (no schema/contract change); the only forced backend touch is the Prompt Builder + wiring it into the Akool call (replacing `DEFAULT_PROMPT`) + one per-shot script-directed regeneration.

## Provider mapping (backend fulfillers, never UI selectors)
- **Gemini** → understanding / storyboard / prompt + language rewrite.
- **Akool** → primary `image_to_video` (video_gen).
- **Azure** → voiceover (dub).
- **ffmpeg** → compose / QC / fallback / subtitle burn / normalize (post_production).
- **R2/artifact** → input hosting + result persistence.
- **VoiceTrans** (future) → audio/language bridge; **Digital Anchor** (future) → role/presenter provider (consumer-only).
- No provider selector in primary UI; provider failure = per-shot fallback evidence in operator language; Akool result URL downloaded/transferred, never a delivery source.

## Heavy batch scope
**Name:** Matrix Script Storyboard Control + Shot Workbench Batch. **Gate-spec-first.**
Scope: `generation_plan_view` projection · prompt builder (pure function, 3 outputs, no secret) · Current Shot Work Panel extension (镜头目标 / 画面动作 / 素材角色 / AI 生成要求 / 负面约束) inside §B/§C · material-role binding (presenter-first) · one controlled script-directed Akool regeneration into `final.mp4` · V1/V2 shot-change explanation.
Non-goals: no provider selector; no `official_publish_ready=true`; no delivery-truth change; no full timeline editor; no Digital Anchor authoring; no VoiceTrans embedded form; no broad schema/contract unless forced (then separate gated step); no Hot Follow / DA / `artifact_storage.py` / `schemas/` / `docs/contracts/` touch.

## Acceptance criteria (summary; full in §12)
Fresh task shows storyboard queue (1) + current shot panel (2); operator sees visual goal / motion / material role / AI generation prompt (3); one shot generated by Akool from a script-derived prompt + hosted material (4) consumed into `final.mp4` (5); Azure voiceover audible (6); subtitles visible (7); V1/V2 preserved (8); `official_publish_ready=false` (9); no vendor/secret/raw-URL leak (10); regenerate-this-shot works or the exact route is documented (11 — today regeneration is whole-task and provider runs only for shot02; gate spec must add a per-shot route or bind the active shot to the existing whole-task regen).

## Owner decision needed
- **APPROVE** → authorize authoring the heavy-wave gate spec (docs-only, §10-signoff-gated). *(Recommended — substrate is proven; remaining gap is exactly script-directed generation + storyboard control.)*
- **REVISE** → redirect the framing before any gate spec.
- **HOLD** → keep substrate as-is; do not open the wave.

Stop point honored: alignment doc + this Owner Summary + validation report only. **No runtime implemented. No heavy engineering PR opened.**
