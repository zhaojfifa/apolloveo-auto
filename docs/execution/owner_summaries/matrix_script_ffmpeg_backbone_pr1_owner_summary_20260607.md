# Owner Summary — Matrix Script ffmpeg Backbone PR-1 (2026-06-07)

Docs companion to the first runtime slice. Not authority; the Gate Spec governs.

Gate Spec: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`
(§12 Architect + Reviewer signoff merged via #238; Owner granted S5→S6 for PR-1 only)

## What this PR is

The **first authorized runtime slice** — the secret-free ffmpeg backbone module.
**Implementation PR; NOT merged.** Per the Owner's S5→S6 grant for PR-1, this implements
the backbone capability the offline trial proved.

> **Scope reconciliation (transparent):** the Owner's "Allowed scope" for PR-1 explicitly
> enumerated proxy generation **+** compose **+** ffprobe QC **+** artifact/manifest/QC
> evidence **+** Fast Preview Path / fallback semantics. The Gate Spec §11 had tentatively
> split these across PR-1/PR-2/PR-3; this slice follows the **Owner's explicit PR-1 scope
> definition** (one cohesive backbone module). The Gate Spec's no-bundling note yields to
> the Owner's explicit instruction for this run; acceptance rows FB-1..FB-12 are all
> satisfied within this single module.

## Files

- `gateway/app/services/matrix_script/ffmpeg_backbone.py` (new module, +374)
- `gateway/app/services/tests/test_matrix_script_ffmpeg_backbone.py` (new tests, +226)
- this Owner Summary.

**No existing file modified** — additions only → behavior preserved by construction.

## What it implements (Gate Spec §3 allowed scope)

- **Ken-Burns proxy** clip generation from a still (deterministic 1080×1920 / 30fps /
  h264 / yuv420p / fixed preset+crf), explicitly a **motion proxy, not generative** —
  honest semantics (`is_generative=False`, operator label `预览代理（非生成式）`).
- **ffmpeg concat compose** of per-shot clips into one delivery-spec cut.
- **ffprobe QC** with a pass/fail verdict (resolution / codec / fps / duration-fit /
  has-duration), operator-safe (no `local_path` / raw JSON in the verdict).
- **Fast Preview Path / fallback semantics:** proxy first, then static-still fallback on
  render failure (`generate_with_fallback`); compose still proceeds.
- **Artifact / manifest / QC evidence:** `ClipArtifact` + `BackboneManifest` with
  `operator_summary()` projections that exclude `local_path` and any raw/vendor field;
  `official_publish_ready` stays `False` (preview candidate only).

## Hard boundary honored (Gate Spec §4 / §9)

- No credential, no network, no provider/vendor/model/engine, no Akool, no generative
  `image_to_video` adapter, no `subtitle_style` runtime, no voiceover/bgm/broll/avatar.
- No `artifact_storage` / R2 write (caller passes the output dir); no schema/contract
  change; no UI/template; no route change; no Hot Follow / Digital Anchor / asset touch.
- No delivery-truth change; `official_publish_ready` unchanged (`False`). No vendor in UI.
- No Slot Workflow v2 PR-1; no §13 fill; no provider routing decision.

## Validation evidence

- `py_compile gateway/app/services/matrix_script/ffmpeg_backbone.py gateway/app/main.py` → OK.
- Focused backbone tests: **24 passed** (incl. a real ffmpeg/ffprobe end-to-end
  integration test that runs because ffmpeg is locally available; it self-skips where
  ffmpeg is absent).
- Targeted adjacent Matrix Script tests: **76 passed** (closure binding, task card
  summary, PR-1 A-state narration, backbone).
- `git diff --check` clean; forbidden-path scan clean (only the two allowed paths);
  no-secret scan clean (the only `secret` hits are a test leakage *fixture* asserting
  non-leakage, not a credential).
- Pre-existing PEP-604 collection errors on Python 3.9.6 in unrelated files are an
  environment limitation per `ENGINEERING_RULES.md` §10, not a regression (confirmed
  they error independently of this change).
- Behavior preservation: additions only; no existing file modified.

## Post-Code-Review fix (composed-cut duration accuracy)

Operator Trial (S7→S8) found one minor non-blocking nit: the `composed_cut` descriptor's
`operator_summary()` reported `duration_seconds: 0.0` while the authoritative ffprobe QC
correctly reported the real duration. Owner chose **fix-then-merge (option A)**. Narrow
correction (PR-1 module + tests only):

- `compose_concat` now accepts an optional `clip_durations` (per-input seconds) and sets
  the composed cut's `duration_seconds` to their **sum**, so the descriptor / manifest
  evidence matches the QC. A length-mismatch raises `BackboneRenderError`.
- The authoritative QC (`qc_probe`) is **unchanged**; operator summary + manifest are now
  consistent with it. Verified live: descriptor `4.0` == QC `4.0`.
- Added 3 dedicated tests (duration populated from sum; defaults `0.0` without durations;
  length-mismatch rejected) + 2 asserts in the real-ffmpeg integration test. Focused suite
  now **27 passed** (was 24); leak scan still NONE; `official_publish_ready` still `False`.

## Boundary

runtime changed: **Yes (new module only, authorized PR-1)** · existing runtime modified:
**No** · provider integration: **No** · credentialed calls: **No** · schemas/contracts:
**No** · vendor in UI: **No** · delivery truth: **unchanged** · official_publish_ready:
**unchanged (False)** · Slot Workflow v2 PR-1: **No** · §13: **untouched** · merged: **No**.

## Owner decision needed

After review/trial evidence, decide per Harness X whether to proceed to **Code Review →
Operator Trial → merge** (S6→S7→S8→S9), or send back. **Not merged** by this step.

---

## 给 Claude 的指令

- **current Owner decision:** Owner granted **S5→S6 for ffmpeg backbone PR-1 only**.
  This Implementation PR is authored but **NOT merged**. Credentialed provider trial =
  HOLD. Slot Workflow v2 runtime = CLOSED. §13 = untouched.
- **allowed next actions (only on explicit Owner instruction):** (a) on Owner go →
  proceed through Harness X **Code Review (S6→S7)** then **Operator Trial (S7→S8)** then
  **Owner merge (S8→S9)** for this PR-1; (b) **PR-2 is NOT authorized** — opening it is a
  separate Owner S5→S6 decision; (c) credentialed provider trial runs only on explicit
  Owner approval + credentials.
- **forbidden actions:** do not merge this PR without Owner approval; do not start PR-2;
  do not run credentialed provider calls; no credentials/secrets; no generative provider
  adapter; no subtitle_style/voiceover/bgm/broll/avatar; no schemas/contracts; no vendor
  in UI; no delivery-truth or `official_publish_ready` change; no Slot Workflow v2 PR-1;
  no §13 fill; no provider routing decision; no edits to existing runtime files beyond the
  new backbone module.
- **required outputs (this round, delivered):** Implementation PR; Implementation PR
  Report (chat); this Owner Summary.
- **validation checks:** focused backbone tests; relevant Matrix Script tests;
  `py_compile gateway/app/main.py`; `git diff --check`; forbidden-path scan; no-secret
  scan; behavior-preservation (additions-only) — all run and clean.
- **stop point:** stop after the Developer / PR report. Do not merge; do not start PR-2;
  do not run provider calls.
- **Owner Decision Needed:** after this report, do you approve proceeding to **Code
  Review / Operator Trial / merge** for ffmpeg backbone PR-1 per Harness X — or send back?
