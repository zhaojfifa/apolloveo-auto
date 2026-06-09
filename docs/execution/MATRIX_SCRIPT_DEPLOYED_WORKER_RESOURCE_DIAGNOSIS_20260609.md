# Matrix Script Deployed Worker Resource Diagnosis

Date: 2026-06-09
Type: **Diagnostic + low-load batch.** Added env-driven load knobs + redacted phase-timing logs +
partial-trace-before-compose logging. Local characterization done; **deployed low-load runs are the
next step (require the knobs deployed).** No schema/contract change, no UI, no PR-5. **Stops before
merge** (code changes were needed).

> **Headline finding:** A **single ffmpeg `zoompan` (Ken-Burns) process peaks at ~1.57 GB RAM** at
> 1080×1920 (clean local measurement, max-concurrent = 1). That is a **strong OOM candidate on any
> instance < ~2 GB**, and it runs once per non-provider (backbone) shot. Separately, the observed
> deployed **502 at ~180–200 s falls during the Akool-polling/normalize phase** (before the
> render-loop zoompan), pointing to a **long-blocking-job worker timeout** as the *first* crash. So
> two distinct resource pressures are implicated: (a) a worker-lifecycle/blocking issue from the
> ~215 s synchronous in-process job, and (b) a ~1.6 GB ffmpeg memory spike at render. **Strict
> classification: INCONCLUSIVE** (deployed 1/2/3-shot + Render OOM logs not yet available) — but the
> local evidence strongly implicates RESOURCE (ffmpeg memory) and/or WEB_DYNO_UNSUITABLE.

## 1. Hypothesis
- **Why a resource issue is suspected:** the heavy step (ffmpeg `zoompan` Ken-Burns, 1080×1920) peaks
  at **~1.57 GB** for a single process (measured locally, below); generation runs **in-process** on
  the web dyno (FastAPI `BackgroundTasks` → `auto_preview_generation` → `run_tomato_real_result`),
  and the deployed run 502s mid-generation then finalizes `retry_required`.
- **Why it is not proven yet:** I have **no Render dashboard/log access** (cannot see `OOMKilled` /
  worker-restart), and the **deployed low-load runs require the new knobs deployed** (this batch adds
  them but stops before merge). So neither the Owner's `RESOURCE_CONFIRMED` trigger (1/2 pass, 3
  crashes) nor an OOM log is in hand yet.

## 2. Render Log Evidence
- **OOM/killed/restart:** **NOT AVAILABLE** to this agent (no Render dashboard access). The Owner
  should check `apolloveo-auto2` logs around the crash for `OOMKilled` / `Worker timeout` / `SIGKILL`.
- **502 timing (from my deployed HTTP probes, prior turn):** controlled run `81d1eb65bb42` —
  `running` t+1s→t+165s, **HTTP 502 at t+182s & t+199s**, recovered t+215s→t+297s, `retry_required`
  at t+313s. Reproduced on a second task (`121caedd5a05`).
- **process lifecycle:** the 502 then recovery indicates a **worker crash/restart at ~180–200 s**;
  the in-process background job is lost on restart, so the projection's stale guard
  (`RUNNING_STALE_SECONDS=300`) finalizes `retry_required`.

## 3. Low-load Runs
- **deployed 1-shot / 2-shot / 3-shot:** **NOT RUN this batch** — the knobs
  (`MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` etc.) are newly added and not yet deployed; per instruction I
  stop before merge. These are the immediate next step once the knobs are deployed.
- **local validation (this batch):** the knobs + phase logs were exercised locally (mocked provider,
  no cost). Log confirms knob application: `ms_phase phase=provider_knobs target_shots=3 attempt_cap=5
  gemini_retry=True`; all phase logs emit (`generation_start` → `provider_batch_start` →
  `gemini_refine_done` → `akool_*` → `shot_done` → `provider_trace_presummary` → `compose_start/done`
  → `upload_done total_generation_ms=…`). 3/3 mock shots consumed; result correct.
- **NOTE — knob caveat:** `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` reduces **Akool/provider** load
  (fewer real calls) but NOT the **ffmpeg `zoompan`** load — non-provider shots still render via the
  ~1.57 GB Ken-Burns backbone. So a deployed `TARGET_SHOTS=1` run that **still crashes (at the render
  zoompan)** ⇒ ffmpeg/RESOURCE; one that **completes** ⇒ the crash was provider-polling/worker-timeout.
  To directly throttle ffmpeg memory, a resolution/motion lever is needed (see §6) — NOT added here
  (the resolution constant is woven through the backbone + QC; not an "already-safe" knob).

## 4. Phase Timing
- **Gemini:** ~0–2 s/shot (deterministic fallback is instant; live refine ≈1–2 s). Falls back to
  deterministic on any error (no crash contribution).
- **Akool (per shot, real — from the PR-254 live smoke):** **~62–90 s/shot** (host + create + poll
  dominated). **3 shots sequential ≈ 215 s** — this is the bulk of wall-clock and the phase the
  deployed ~180 s 502 lands in.
- **download:** ~5 s/shot. **normalize:** ~3 s/shot (scale/crop re-encode; moderate memory).
- **compose (final concat):** **~5 s** (measured locally) — fast, and it runs *after* the ~215 s
  provider phase (i.e., after the observed 180 s crash point).
- **zoompan / Ken-Burns (backbone shots, render loop):** **~1.57 GB peak RAM, single process**
  (`ffmpeg_backbone.py:132` `zoompan`); runs once per non-provider shot in the render loop (after the
  provider phase).
- **upload/staging:** ~0–1 s (local sink); R2 staging adds network time on deploy.

## 5. Root Cause
**INCONCLUSIVE (deployed)** — pending deployed 1/2/3-shot runs (knobs) + Render OOM logs, which the
Owner's own criteria require for `RESOURCE_CONFIRMED`. Local evidence narrows it strongly to **two
concurrent pressures**, both arguing the heavy multi-shot generation does not belong in-process on a
small web dyno:
- **WEB_DYNO_UNSUITABLE (first-observed crash):** the ~180 s 502 is during the long synchronous
  Akool-polling phase — consistent with a worker/lifecycle timeout from a ~215 s blocking in-process
  `BackgroundTask`, not an ffmpeg memory spike (polling is low-memory).
- **RESOURCE (ffmpeg, latent at render):** the ~1.57 GB `zoompan` spike would additionally OOM the
  render phase on any instance < ~2 GB.
(Not `PROVIDER_BLOCKED`: no Akool/Gemini/R2 error surfaced before the crash; `r2_enabled:true`. Not a
clean `TRACE_GAP` only — the new partial-trace presummary log now mitigates that going forward.)

## 6. Recommendation
**Primary — move generation off the web dyno (Render background worker, or Cloud Run Job / external
worker).** This resolves BOTH pressures: the long (~215 s) job no longer blocks/kills the web worker,
and it gets dedicated memory for the ~1.6 GB ffmpeg. (Also avoids future request-lifecycle limits.)
- **Interim quick unblock:** a **temporary Pro / larger instance (≥ 4 GB headroom)** to absorb the
  ~1.6 GB ffmpeg + the blocking job, to confirm completion end-to-end on deploy.
- **Code-side mitigation (separate, gated):** lower the compose/Ken-Burns resolution (e.g.
  720×1280) or replace `zoompan` with a lighter motion filter to cut the ffmpeg memory peak — this is
  the real lever for the ffmpeg-OOM half and is NOT done here (touches backbone constants + QC).
- **Confirm-the-cause step (cheap, before spending on Pro):** deploy the knobs + run a deployed
  `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS=1` task and read Render logs at the crash — `OOMKilled` ⇒
  RESOURCE; `Worker timeout`/SIGTERM during polling ⇒ WEB_DYNO_UNSUITABLE. The phase logs added here
  will show exactly which `ms_phase` preceded the kill.

---
### Changes in this batch (code, NOT merged — stop before merge)
- `provider_orchestrator.py`: `enable_retry` knob + redacted phase logs (`gemini_refine_done`,
  `akool_*` lifecycle with elapsed, `shot_done`, `provider_batch_start`).
- `tomato_real_result_orchestrator.py`: env knobs `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS` /
  `MATRIX_SCRIPT_PROVIDER_ATTEMPT_CAP` / `MATRIX_SCRIPT_PROVIDER_ENABLE_GEMINI_RETRY`; phase logs
  (`generation_start`, `provider_knobs`, `provider_trace_presummary` **before** compose,
  `compose_start/done`, `upload_start/done total_generation_ms`).
- `test_matrix_script_provider_orchestrator.py`: +2 tests (retry-toggle, env-knob helpers).
- **Boundary:** no schema/contract change; no provider selector; no delivery-truth change;
  `official_publish_ready=false`; redacted logs only (shot_id / status / elapsed — no key/URL/task-id);
  `MATRIX_SCRIPT_COMPOSE_RESOLUTION` intentionally NOT added (not an "already-safe" knob).
- **Validation:** offline orchestrator/refiner **21 passed**; multi-shot akool **7 passed**; focused
  matrix_script suite **2 failed / 2064 passed** (both failures pre-existing block-title tests,
  stash-confirmed in prior batches — NOT new regressions); py_compile clean.

## Owner Decision Needed
1. **Merge + deploy these diagnostic knobs/logs**, set `MATRIX_SCRIPT_PROVIDER_TARGET_SHOTS=1`, run a
   deployed task, and read the Render logs at the crash (confirm OOM vs worker-timeout) — then I
   re-run the deployed 1/2/3-shot acceptance and classify definitively; **or**
2. **Go straight to the off-dyno worker / larger-instance** decision based on the ~1.57 GB ffmpeg +
   long-blocking-job evidence above.

Stopping before merge.
