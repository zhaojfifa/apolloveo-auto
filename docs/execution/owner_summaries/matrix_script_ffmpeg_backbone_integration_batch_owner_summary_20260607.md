# Owner Summary — Matrix Script ffmpeg Backbone Runtime Integration Batch (2026-06-07)

Docs companion to the integration batch (Fast Lane S5→S8). Not authority; the Gate Spec
+ Integration Batch Plan govern.

Plan: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_INTEGRATION_BATCH_PLAN_20260607.md` (#241)
Backbone module: `gateway/app/services/matrix_script/ffmpeg_backbone.py` (PR-1 #239 + PR-2 #240)

## What this PR is

The integration batch: it **wires the proven `ffmpeg_backbone` into the Matrix Script
fast-preview / minimal-result path** (`minimal_result_loop.run_minimal_result_loop`).
**Implementation PR; NOT merged** (stops before S8→S9 per Fast Lane).

> **No new helper file was needed** — the shot-plan→`ShotSpec` adapter is a small inline
> mapping in the loop; `ffmpeg_backbone.py` was **not modified** this batch. So there is
> no scope expansion to report.

## What it implements (authorized seam)

- New optional `shot_images` param on `run_minimal_result_loop` (shot_id → local still /
  caller-resolved material path). **Backbone engages only when ≥1 shot has a usable still.**
- In backbone mode every clip renders at the backbone's deterministic **1080×1920 / 30fps**
  (uniform so proxy + color-card clips compose): a shot with a still → Ken-Burns **proxy**
  via `generate_with_fallback` (static-still on failure); a shot without → the existing
  **color-card** path (preserved).
- After `assemble_final_video`, the composed `final.mp4` is **QC'd via `ffprobe`**
  (`qc_probe`); operator-safe `qc` + `per_shot_render` + `backbone` evidence is added to
  the manifest (additive keys; legacy manifest shape preserved when omitted).
- `official_publish_ready` stays **false**; delivery truth unchanged; no provider /
  credential / vendor / schema / route / UI change.

## Truth preserved (Plan §4)

- Legacy color-card path **byte-stable** when `shot_images` is absent (10 legacy tests
  pass; `scene_strategy` stays `ffmpeg_color_card`, no qc/per_shot/backbone keys).
- Manifest shape + `_assert_no_forbidden_tokens` guard preserved (backbone keys additive,
  forbidden-token-clean).
- `simple_scene_renderer` color-card path kept as fallback; `shot_material_storage` /
  `artifact_storage` / schemas / contracts / routes / templates untouched.
- Four-layer boundary: backbone output is L2 artifact facts behind the existing boundary;
  no new producer / second source of truth.

## Validation evidence

- `py_compile gateway/app/main.py` (+ touched modules) → OK.
- Focused: backbone (35) + minimal_result_loop (13, +3 integration incl. real-ffmpeg) = **48 passed**.
- Adjacent: minimal-result orchestrator + closure binding + task card summary = **47 passed**.
- Live Operator Trial on real tomato stills: backbone engaged; shots with stills → proxy,
  shots without → color-card fallback; composed `final.mp4`; ffprobe QC passed (1080×1920
  h264 30fps, dur 8.0, `official_publish_ready=false`); manifest leak tokens **NONE**.
- `git diff --check` clean; allowed-files-only; forbidden-path clean; no provider/
  credential/network added; no-secret clean.
- Behavior preservation: only `minimal_result_loop.py` + its test changed; the backbone
  module and all other runtime files untouched.

## Boundary

runtime changed: **minimal_result_loop seam only (authorized)** · provider integration:
**No** · credentialed calls: **No** · generative adapter: **No** ·
subtitle/voiceover/bgm/broll/avatar: **No** · schemas/contracts: **No** · routes: **No** ·
vendor UI: **No** · delivery truth: **unchanged** · official_publish_ready: **unchanged
(False)** · PR-3: **not started** · merged: **No**.

---

## 给 Claude 的指令

- **current Owner decision:** Owner granted **S5→S8 Fast Lane for the Integration Batch
  only** (after #241 merged). Batch implemented + reviewed + trialled; **NOT merged**.
  Credentialed trial = HOLD. §13 = untouched. Slot v2 runtime = CLOSED. PR-3 = not started.
- **allowed next actions (on Owner go):** **APPROVE S8→S9 merge** for this batch PR → then
  merge + sync main + post-merge validation + merge report. Any further runtime
  (generative provider, etc.) needs its own gate + Owner grant.
- **forbidden actions:** no merge without explicit Owner S8→S9; no provider
  calls/credentials/secrets; no network/API integration; no generative adapter; no
  subtitle/voiceover/bgm/broll/avatar; no schemas/contracts; no route change; no vendor in
  UI; no delivery-truth/`official_publish_ready` change; no Slot v2 runtime; no §13 fill;
  no edits outside the seam + tests + this summary.
- **required outputs (delivered):** Implementation (batch PR); Fast Lane report; this Owner Summary.
- **validation checks:** focused (48) + adjacent (47) tests, py_compile, diff-check,
  forbidden-path, no-secret, behavior-preservation, live Operator Trial — all clean.
- **stop point:** stop before merge; request S8→S9.
- **Owner Decision Needed:** APPROVE S8→S9 merge for the ffmpeg Backbone Runtime Integration Batch?
