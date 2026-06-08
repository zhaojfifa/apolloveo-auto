# Owner Summary — Matrix Script Akool Real Capability Batch (2026-06-08)

Docs companion (Heavy Fast Lane S5→S8). Not authority; the report governs.

Report: `docs/execution/MATRIX_SCRIPT_AKOOL_REAL_CAPABILITY_BATCH_20260608.md`

## Headline

- **Real Azure voiceover SUCCEEDED** end-to-end — the operator final.mp4 now carries real
  narration (`audio_mode=azure_tts`, mean_volume −20.8 dB, 旁白已生成). Voiceover is no longer
  blocked: the credentials in `~/.apolloveo/apolloveo-auto.env` made it real.
- **Akool image_to_video capability wired + VALIDATED against the live API** — a real
  `create_task(IMAGE_TO_VIDEO,{image_url,prompt})` returned a provider task id, **status QUEUED**.
  Credential valid, endpoint + transport + auth correct.
- **Full local Akool clip not produced** — the one-shot on an arbitrary public test image hit a
  real provider processing **FAILED** (`provider_status_failed`), and the orchestrator's real
  still could not be hosted locally because `artifact_storage` fails to import on **Python 3.9.6**
  (`config.py:43` PEP-604) — the same env limit affecting route tests all along. On Python 3.10+
  (deploy/CI) hosting works and the real still feeds Akool.
- **STOPPED BEFORE MERGE** per the Owner stop condition "Akool call fails with real provider
  error." PR opened, merge-ready. **USD ~1** (one Akool job), well under any cap.

## What this batch adds (real capability, allowed files only)

- New `gateway/app/services/matrix_script/akool_image_to_video_capability.py`: live HTTP
  transport → `AkoolClient` create → bounded poll → download → normalize to 1080×1920/30fps;
  gated behind `MATRIX_SCRIPT_AKOOL_REAL` + key presence; honest per-shot status
  (provider_success / provider_failed / credential_missing / policy_blocked / timeout). No
  env-name resolver needed (the canonical mapping already matches `AKOOL_API_KEY` /
  `AKOOL_API_BASE_URL`). Vendor-agnostic render token `provider_image_to_video` (no brand leak).
- Orchestrator: one designated shot (`shot02`) attempts real Akool when enabled; any failure →
  honest backbone-proxy fallback + per-shot status. `providers/akool`, `capability/adapters`,
  `workers/*` are imported, not modified.

## Credential handling

Loaded from `~/.apolloveo/apolloveo-auto.env` into the process only; presence-only probe (no
values printed); api key only on the outgoing `x-api-key` header; redacted diagnostics (class
only); no secret in repo/log/manifest/operator payload. no-secret scan clean.

## Capability scorecard (live smoke)

P0 final.mp4 ✅ playable 1080×1920 · voiceover ✅ **real Azure (生成)** · subtitles ✅ burned ·
image_to_video ⚠️ **live create validated (QUEUED); full clip blocked by test-image processing
failure + 3.9.6 hosting limit** · material/V1-V2 ✅ preserved · BGM ➖ honest 配乐未选择 ·
publish_ready ✅ false.

## Validation

Akool 7 + voiceover 7 + akool_real_gate pass · adjacent **104 passed** (4 = pre-existing PEP-604
route limit) · py_compile OK · diff-check / forbidden-path / no-secret clean. No
routes/schemas/contracts/providers modified.

## Boundary

provider calls: **Yes** (Akool create validated; one bounded job) · credentials: env-only, never
committed/printed · secrets committed: **No** · schemas/contracts/routes: **No** · vendor UI:
**No** · delivery truth: **unchanged** · official_publish_ready: **false** · Slot v2: **not
started** · merged: **No**.

## 给 Claude 的指令

- **current Owner decision:** S5→S9 Akool real capability; stop only on a hard boundary — a real
  Akool provider error occurred → stopped before merge.
- **allowed next actions:** on Owner go → merge (capability is sound + live-create-validated;
  runs on 3.10+ deploy) + run a deploy/CI smoke hosting the real still; or run the smoke on a
  Python 3.10+ runtime first, then merge.
- **forbidden actions:** no secrets anywhere; no faked provider/voice/BGM; no vendor selector in
  primary UI; no schema/contracts; no route change; no delivery-truth change;
  no `official_publish_ready=true`; no Slot v2 runtime; no merge without Owner go.
- **required outputs (delivered):** rollback tag; capability + wiring; tests; live smoke; report;
  this summary.
- **validation checks:** tests + py_compile + diff-check + forbidden-path + no-secret + live
  credentialed smoke — all run.
- **stop point:** stopped before merge (PR opened, merge-ready).
- **Owner Decision Needed:** below.

## Owner Decision Needed

`final.mp4` is playable with **real voiceover**; the Akool capability is wired and **live-create
validated** (QUEUED), but the full local clip hit a real provider processing failure (test image)
+ the Python 3.9.6 hosting limit. Choose:
- **APPROVE merge** (capability runs on the 3.10+ deploy with the real hosted still), then a
  deploy smoke captures a real Akool clip; or
- **Run the smoke on a Python 3.10+ runtime first** (real still hosted → correct product image to
  Akool) before merging; or
- **Revise / hold.**

Stop before merge.
