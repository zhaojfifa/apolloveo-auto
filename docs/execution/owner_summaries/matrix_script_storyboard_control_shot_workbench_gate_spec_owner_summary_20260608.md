# Owner Summary — Matrix Script Storyboard Control + Shot Workbench Gate Spec

Date: 2026-06-08
Type: **Docs-only gate spec authoring (Harness X S5).** No code / template / router / schema / contract / test / runtime change. No implementation opened.
Gate Spec: `docs/design/MATRIX_SCRIPT_STORYBOARD_CONTROL_SHOT_WORKBENCH_GATE_SPEC_20260608.md`
Authority: Owner decision 2026-06-08 — "APPROVE S5 … author the Gate Spec only."

---

## What was authored
A binding-pending-signoff gate spec that freezes the accepted Storyboard-to-Video alignment into enforceable rules for the **first script-directed generation wave**. It is the first gate spec authorized to cross into the generation path (Prompt Builder → Akool), a boundary Slot Workflow v2 and the ffmpeg backbone gate spec deliberately left closed. It does **not** supersede Bucket A and authors **no** new IA.

## Coverage of the 13 required content points
1. **Source authority** — §2 (Bucket A, v1 spine, v2 delta, Slot Workflow v2 gate spec, ffmpeg backbone gate spec, Akool smoke + merge reports, capability-upgrade review, the alignment doc).
2. **Frozen target** — §4 (Script → Generation Plan → Storyboard Queue → Current Shot Workbench → Material Role Binding → Prompt Builder → Akool Provider Fulfillment → Compose/QC → V1/V2 Review → Delivery).
3. **Projection-first rule** — §5 (`generation_plan_view` projection-only first; `material_role` + intent via additive `operator_intent_map`; `provider_prompt`/`negative_prompt` runtime-transient — operator sees only AI 生成要求 / 负面约束).
4. **Workbench scope** — §6 (re-home in A–J; Slot Workflow v2 compact Shot Queue + single Current Shot Work Panel; no new IA, no parallel flow).
5. **Required operator fields** — §7 (镜头目标 / 画面动作 / 旁白 / 字幕重点 / 素材角色 / AI 生成要求 / 负面约束 / 当前生成状态 + buttons 改写生成要求 / 替换素材 / 重新生成这个镜头 / 接受这个镜头).
6. **Prompt Builder** — §8 (pure deterministic fn; inputs script_segment/narration_line/visual_goal/motion_instruction/material_role/selected_material/duration/aspect_ratio; outputs a operator-safe AI 生成要求, b provider payload, c diagnostic summary; replaces `DEFAULT_PROMPT`; no secret/raw-URL/vendor name).
7. **Material roles** — §9 (product_reference / character_reference / scene_reference / style_reference / replacement_image / broll_candidate; tomato bowl bound as product_reference).
8. **Controlled Akool regeneration** — §10 (≥1 shot from script-derived prompt + hosted URL; clip downloaded/normalized/consumed into final.mp4; others may fall back; Azure voiceover + subtitles remain; `official_publish_ready=false`).
9. **Route decision** — §11 (**Option A chosen**: reuse existing `POST /api/matrix-script/{task_id}/tomato-real-result` + generalize `run_tomato_real_result` so the active shot is the provider-target and the built prompt replaces `DEFAULT_PROMPT`; router stays thin — request-parsing only; **no new route**; Option B per-shot route deferred and forbidden this wave).
10. **Acceptance rows** — §14 (A-SC-1..A-SC-16, covering all 12 Owner minimums + determinism, role binding, no-second-truth, inherited-behavior preservation).
11. **Slicing proposal** — §15 (PR-1 plan/queue → PR-2 Prompt Builder/panel → PR-3 material role → PR-4 controlled Akool regen + V1/V2 explanation → PR-5 closeout). **Recommendation: do NOT combine PR-1~PR-4** — justified by cost/risk isolation (only PR-4 spends a real provider call), repo discipline (per-slice S5→S6), and that operator-result coherence is still proven at PR-4.
12. **Forbidden scope** — §16 + forbidden paths §17 (no provider selector; no `official_publish_ready=true`; no delivery-truth change; no full timeline editor; no Digital Anchor authoring; no VoiceTrans embedded form; no Hot Follow touch; no `artifact_storage.py` touch unless separately approved; no schemas/contracts change unless contract-first scope expansion explicitly approved; no raw URL/key/token/handle leak; no second source of truth).
13. **Signoff block** — §19 (Architect + Reviewer + **Owner** placeholders gate-opening; Coordinator + PM bind closeout; runtime CLOSED until merge + Owner S5→S6 grant).

## Key engineering decisions made in the spec
- **Route: Option A** (no new route; thin request-parse + service generalization). Chosen for router-thin discipline and lowest route-boundary risk; precise pins: route `matrix_script_tomato_real_result.py:65`, hardcoded `AKOOL_SHOT_ID = "shot02"` (`tomato_real_result_orchestrator.py:85`) generalized to the active shot, prompt enters at `akool_image_to_video_capability.py:198`.
- **Five slices, not one PR.** PR-1..PR-3 are projection/presentation (zero provider cost, independently testable); PR-4 is the only generation-path / real-provider-call slice and carries the end-to-end smoke.
- **Projection-first, no contract change.** Plan/role/intent ride as projection + additive `operator_intent_map`; prompt is runtime-transient.

## Validation
- `git diff --check`: clean (tracked); my two new files have 0 conflict markers / 0 trailing-whitespace.
- docs-only scan: PASS (both `docs/*.md`).
- forbidden-path scan: PASS (no `gateway/`, `schemas/`, `docs/contracts/`, `.py`, tests, routes in my change set).
- no-secret scan: PASS (no URLs; no secret values; only env-var **names** as identifiers; no raw handle/endpoint leak).

## Owner decision needed
Review the gate spec, then fill §19 (Architect + Reviewer + **Owner**) to open the implementation gate for **PR-1 only**. Runtime remains CLOSED until that signoff merges and the Owner explicitly grants S5→S6. **PR-1 will not be opened until the Owner approves after gate-spec review.**

Stop point honored: Gate Spec + this Owner Summary + validation report only. No runtime implemented. No PR opened.
