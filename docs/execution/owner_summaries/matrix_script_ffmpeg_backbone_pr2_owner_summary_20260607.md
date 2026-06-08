# Owner Summary — Matrix Script ffmpeg Backbone PR-2 (2026-06-07)

Docs companion to the ffmpeg backbone PR-2 slice (Fast Lane S5→S8). Not authority; the
Gate Spec governs.

Gate Spec: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`
(Owner granted **S5→S8 Fast Lane for PR-2 only**; PR-1 merged at S9 via #239)

## What this PR is

The PR-2 slice: **targeted-regenerate orchestration** over the merged PR-1 backbone.
**Implementation PR; NOT merged** (stops before S8→S9 per Fast Lane). Compose / QC /
fallback already landed in PR-1 (the Owner's PR-1 scope absorbed them), so PR-2's
residual scope is exactly the targeted-regenerate helper.

## What it implements (authorized PR-2 scope)

- `ShotSpec` (ordered shot: still + proxy params), `ShotClipResult` (per-shot
  `regenerated`/`reused` + clip), `TargetedRegenResult` (per-shot actions + recomposed cut).
- `targeted_regenerate(...)`: regenerates a proxy **only** for changed shots (or shots
  with no existing clip) via `generate_with_fallback` (fallback-tier preserved); **reuses**
  unchanged shots' existing clips; re-composes the cut from changed + reused clips with
  correct per-shot durations (uses the PR-1 `compose_concat` duration fix).
- QC is **preserved and unchanged** — callers run `qc_probe` on `composed_cut`
  (authoritative duration source untouched).
- Operator-safe manifest/evidence: `TargetedRegenResult.operator_summary()` excludes
  `local_path` and any raw/vendor field; `official_publish_ready` stays `False`.

## Validation evidence

- `py_compile gateway/app/services/matrix_script/ffmpeg_backbone.py gateway/app/main.py` → OK.
- Focused backbone tests: **35 passed** (was 27; +8 targeted-regen, incl. a real-ffmpeg
  round-1→round-2 reuse integration test; self-skips when ffmpeg absent).
- Adjacent Matrix Script tests: **52 passed**.
- Live Operator Trial on real stills: baseline (all regenerated) → change only `shot02`
  → `shot02` regenerated, `shot01`/`shot03` **reused with bytes untouched on disk** →
  composed preview updated → QC passed (1080×1920 h264, dur 6.0 = sum) → descriptor ==
  QC → leak tokens NONE → `official_publish_ready` False.
- `git diff --check` clean; forbidden-path scan clean (only the module + tests + this
  summary); no-secret scan clean (only the test leakage *fixture*).
- Behavior preservation: only the backbone module + its tests changed (PR-2's own files);
  no other existing runtime file touched.

## Boundary

runtime changed: **backbone module only (authorized PR-2)** · existing runtime (outside
the module): **unmodified** · provider integration: **No** · credentialed calls: **No** ·
generative adapter: **No** · subtitle/voiceover/bgm/broll/avatar: **No** ·
schemas/contracts: **No** · routes: **No** · vendor UI: **No** · delivery truth:
**unchanged** · official_publish_ready: **unchanged (False)** · PR-3: **not started** ·
merged: **No**.

---

## 给 Claude 的指令

- **current Owner decision:** Owner granted **S5→S8 Fast Lane for ffmpeg backbone PR-2
  only**. PR-2 implemented + reviewed + trialled; **NOT merged**. PR-3 = not authorized.
  Credentialed trial = HOLD. §13 = untouched. Slot v2 runtime = CLOSED.
- **allowed next actions (on Owner go):** **APPROVE S8→S9 merge** for PR-2 → then merge +
  sync main + post-merge validation + merge report. PR-3 needs a separate Owner S5→S6 (or
  Fast Lane) grant.
- **forbidden actions:** no merge without explicit Owner S8→S9; no PR-3; no provider
  calls/credentials/secrets; no network/API integration; no generative adapter; no
  subtitle/voiceover/bgm/broll/avatar; no schemas/contracts; no route change; no vendor in
  UI; no delivery-truth/`official_publish_ready` change; no Slot v2 runtime; no edits
  outside the backbone module + its tests + this summary.
- **required outputs (delivered):** Implementation (PR-2); Fast Lane report; this Owner Summary.
- **validation checks:** focused (35) + adjacent (52) tests, py_compile, diff-check,
  forbidden-path, no-secret, behavior-preservation, live Operator Trial — all clean.
- **stop point:** stop before merge; request S8→S9.
- **Owner Decision Needed:** APPROVE S8→S9 merge for ffmpeg backbone PR-2?
