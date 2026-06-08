# Owner Summary / Smoke Report — Matrix Script Fast Preview Production Smoke (2026-06-07)

Docs companion to the Production Smoke Batch (Fast Lane S5→S8). Not authority.

Scope authority: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`,
`…INTEGRATION_BATCH_PLAN_20260607.md`; integration landed in #242.

## What this batch is

A **runtime acceptance / production smoke** for the merged ffmpeg-backbone fast-preview
path — proving it produces **operator-consumable** results, using only **existing public
service/projection functions read-only**. **No runtime was modified** (a new acceptance
test + this doc). **Not merged.**

## What was verified (real, on the tomato fixture)

Chain exercised end-to-end (real ffmpeg; skips when absent):
`run_minimal_result_loop(shot_images=tomato stills)` → `MatrixScriptMinimalResultSummary`
→ `minimal_result_summary_to_record` → operator + delivery projections → closed UI/delivery
-safe dicts.

- backbone engaged (`scene_strategy = ffmpeg_backbone_proxy`); shots with stills → proxy,
  a shot without → **color-card fallback** (preserved).
- real artifacts produced: `final.mp4` (non-empty) + `manifest.json` + `subtitles.srt` +
  `narration.wav`.
- ffprobe **QC** on the composed cut: passed, 1080×1920; `backbone` evidence
  `is_generative=false`, `official_publish_ready=false`.
- the **existing operator + delivery projections consume the produced artifacts**:
  `has_final_video` / `final_video_path` / `has_manifest` / `manifest_path` /
  `has_subtitles` / `has_audio` / `shot_count` / `publish_ready_candidate=true` /
  `official_publish_ready=false`; forbidden-token guard passes (no provider/vendor leak).
- the backbone strategy + QC fact is **operator-referenceable via the surfaced
  `manifest_path`** (the manifest carries `scene_strategy` / `qc` / `backbone` / `per_shot_render`).
- legacy color-card path (no `shot_images`) still operator-consumable; manifest byte-stable.

## Findings (two flagged scope-expansion items — reported, NOT implemented)

1. **Operator projection does not expose `scene_strategy` / `qc` as first-class fields.**
   The projection's *closed key set* surfaces the artifact paths + publish-readiness, but
   not the backbone strategy/QC verdict directly — those are only referenceable by reading
   the surfaced `manifest_path`. Promoting them to projection fields would edit
   `minimal_result_projection.py` (+ the record), **outside the preferred allowed files** →
   reported as a scope-expansion decision, not done.
2. **Operator service entry does not thread `shot_images`.**
   `run_matrix_script_minimal_result` (the live operator service entry) calls the loop
   **without** `shot_images`, so the backbone does not auto-engage in the live service
   flow (color-card is produced). Making the backbone operator-triggerable via the service
   would edit `minimal_result_service.py` (+ its request object, + resolving uploaded
   material), **outside the preferred allowed files** → reported as a scope-expansion
   decision, not done.

Neither finding is a defect in the merged backbone or integration; both are **input/
presentation wiring** that the Owner explicitly fenced (allowed files prefer
loop/backbone/workbench-view/template/tests/docs). The artifact path itself is proven
operator-consumable.

## Validation evidence

- Production smoke acceptance test: **2 passed** (backbone-consumable + legacy-consumable;
  real ffmpeg, self-skips when absent).
- Focused: backbone (35) + minimal_result_loop (13) + smoke (2) = **50 passed**.
- Adjacent: minimal-result orchestrator + projection + record = **39 passed**.
- `py_compile gateway/app/main.py` → OK.
- `git diff --check` clean; **no runtime file changed** (only a new test + this doc);
  forbidden-path clean; no-secret clean.

## Boundary

runtime changed: **No** (acceptance test + docs only) · provider integration: **No** ·
credentialed calls: **No** · generative adapter: **No** · subtitle/voiceover/bgm/broll/
avatar: **No** · schemas/contracts: **No** · routes: **No** · vendor UI: **No** ·
delivery truth: **unchanged** · official_publish_ready: **unchanged (False)** · Slot v2
runtime: **none** · merged: **No**.

---

## 给 Claude 的指令

- **current Owner decision:** Fast Lane S5→S8 Production Smoke Batch executed; **acceptance
  PASS** with two flagged scope-expansion findings; **NOT merged**. Credentialed trial =
  HOLD. §13 = untouched. Slot v2 = CLOSED. PR-3 = not started.
- **allowed next actions (on Owner go):** (a) **APPROVE S8→S9 merge** for this acceptance
  batch (test + docs); and/or (b) authorize a **scope-expansion batch** to surface
  `scene_strategy`/`qc` on the operator projection and/or thread `shot_images` through the
  operator service entry (touches `minimal_result_service.py` / `minimal_result_projection.py`).
- **forbidden actions:** no merge without Owner S8→S9; no editing `minimal_result_service.py`
  / `minimal_result_projection.py` / schema / contracts / routes / provider without an
  explicit scope-expansion grant; no provider calls/credentials; no generative adapter; no
  subtitle/voiceover/bgm/broll/avatar; no vendor UI; no delivery-truth/`official_publish_ready`
  change; no Slot v2 runtime; no §13 fill.
- **required outputs (delivered):** acceptance smoke test; this Smoke Report / Owner Summary.
- **validation checks:** smoke (2) + focused (50) + adjacent (39) tests, py_compile,
  diff-check, forbidden-path, no-secret — all clean; runtime unchanged.
- **stop point:** stop before merge; request S8→S9 (and surface the two scope-expansion findings).
- **Owner Decision Needed:** (1) APPROVE S8→S9 merge for the acceptance batch? and (2) do
  you authorize a scope-expansion batch for the two findings, or hold?
