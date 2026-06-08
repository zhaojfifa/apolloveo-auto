# Owner Summary — Matrix Script Operator-Visible Backbone Integration (2026-06-07)

Docs companion to the integration (Fast Lane S5→S8). Not authority; the report governs.

Report: `docs/execution/MATRIX_SCRIPT_OPERATOR_VISIBLE_BACKBONE_INTEGRATION_20260607.md`

## What this is

The Owner-approved (Decision A) narrow integration that **puts the proven ffmpeg backbone +
ffprobe QC onto the operator-visible video path** (Path A), so the backbone is no longer
internal-only. **Implementation PR; NOT merged** (stops before S8→S9).

- rollback tag: `matrix-script-before-capability-integration-20260607` → `32338539`
- branch: `feat/matrix-script-production-capability-integration-20260607`

## What changed (one runtime file)

- **`tomato_real_result_orchestrator.py`** — each operator shot now renders through
  `ffmpeg_backbone.generate_with_fallback` (deterministic **1080×1920 / 30fps** Ken-Burns
  proxy; static-still fallback), with the existing Pillow caption overlay preserved on top;
  the composed final.mp4 is QC'd via `ffmpeg_backbone.qc_probe`; the manifest gains additive
  operator-safe evidence (`scene_engine` / `per_shot_render` / `qc` / `backbone`) and the
  payload gains `backbone_qc_passed` / `backbone_qc_resolution`.
- **No change needed** to `auto_preview_generation.py` (it calls the orchestrator, so the
  backbone engages automatically for the initial preview *and* V2 regeneration) or to
  `ffmpeg_backbone.py` (all primitives already existed).

## Live operator smoke (real tomato pack)

- final.mp4 produced, **1080×1920 h264 30fps**, ~5.3 MB, 20.0s, playable.
- **ffprobe QC passed** (resolution / codec / fps / duration_fit all pass).
- captions burned-in preserved; silent-audio fallback preserved.
- material trace preserved — a replacement image is consumed through the backbone
  (`consumed_material_shot_ids=('shot04',)`).
- V1/V2 preserved; delivery_candidate=true; **official_publish_ready=false**; no leakage.

## Goal scorecard (all 8 authorized runtime goals met)

1 scene clips via backbone ✅ · 2 final.mp4 playable in Workbench ✅ · 3 ffprobe QC evidence
✅ · 4 operator flow preserved (final exists / video plays / material trace / V1-V2 / burned
captions / silent fallback) ✅ · 5 publish-ready false ✅ · 6 delivery truth unchanged ✅ ·
7 default + uploaded/replacement materials used ✅ · 8 fallback preserved (static-still /
no-asset skip) ✅.

## Validation

focused tomato tests **13 passed** (incl. 2 new backbone tests) · adjacent **93 + 160
passed** · py_compile OK · diff-check clean · forbidden-path clean (no routes/schemas/
contracts/providers) · no-secret clean. The only failures are the **pre-existing PEP-604 env
limit** (`config.py:43`, Python 3.9.6) on route/config-importing tests — identical on the
clean baseline, not a regression; CI runs 3.10+.

## Boundary

runtime changed: **`tomato_real_result_orchestrator.py` only** · provider: **No** ·
credentials: **No** · generative adapter: **No** · schemas/contracts: **No** · routes:
**No** · vendor UI: **No** · delivery truth: **unchanged** · official_publish_ready:
**unchanged (False)** · Slot v2: **not started** · merged: **No**.

## Is implementation authorized / merged?

Implemented under the approved Fast Lane; **NOT merged**. Merge needs an explicit Owner
S8→S9.

## 给 Claude 的指令

- **current Owner decision:** Decision A approved; backbone on the operator path; stop before
  merge; no follow-up PR without approval.
- **allowed next actions:** on Owner S8→S9 → merge + sync main + post-merge validation +
  merge report.
- **forbidden actions:** no merge without S8→S9; no provider/credential/Akool/Kling/Runway/
  Veo/Azure runtime; no generative adapter; no vendor UI; no schema/contracts; no route
  change; no delivery-truth change; no `official_publish_ready=true`; no fake subtitle/voice/
  BGM controls; no Slot v2 runtime; no unrelated refactor; no follow-up PR without approval.
- **required outputs (delivered):** rollback tag; runtime integration; tests; report; this summary.
- **validation checks:** tests + py_compile + diff-check + forbidden-path + no-secret +
  operator smoke — all clean (pre-existing PEP-604 env aside).
- **stop point:** stopped before merge; no PR; no push.
- **Owner Decision Needed:** APPROVE S8→S9 merge for the Operator-Visible Backbone
  Integration? (or revise / hold).

## Owner Decision Needed

**APPROVE S8→S9 merge?** The operator video is playable and safe (1080×1920 + passing QC +
captions + material trace + publish-ready false). Stop before merge until you decide.
