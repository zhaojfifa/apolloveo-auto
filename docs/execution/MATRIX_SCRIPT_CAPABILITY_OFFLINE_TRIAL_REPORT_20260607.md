# Matrix Script — Capability Offline Trial Report (2026-06-07)

Status: **OFFLINE TRIAL REPORT — docs-only. No runtime, no provider integration, no
adapter code, no secrets, no UI change, no four-layer state change.** Executes the
offline trials defined in `docs/design/MATRIX_SCRIPT_CAPABILITY_TRIAL_PLAN_20260607.md`
against the tomato-beach benchmark stills, using only locally-available, secret-free
tooling. Provider routes that require credentials/network were **not run** and are
honestly marked SKIPPED — no provider output or metric is fabricated.

Authority: this is evidence only (Design Authority Index Anti-Sprawl rule 1). It does
not authorize runtime, does not select a production route, and does not supersede Bucket
A or any Gate Spec.

---

## 1. Trial Context

- **baseline main:** `76a1951f` (after #232 review + #233 trial plan merged).
- **trial branch:** `docs/matrix-script-capability-offline-trial-20260607` (docs-only;
  this report + owner summary).
- **benchmark shots:** the four real local stills in
  `assets/matrix_script_assets/MS-TOMATO-BEACH-001/` —
  `01_beach_hook.png`, `02_tomato_bowl.png`, `03_pick_tomato.png`,
  `04_eat_tomato.png` (all 941×1672 portrait PNG).
- **tools/providers tested (run for real, offline, local):** **ffmpeg 8.1.1** +
  **ffprobe** — `image_to_video` (Ken-Burns pan/zoom proxy), `compose` (concat),
  `qc` (ffprobe probe).
- **tools/providers skipped (not runnable in this offline, secret-free environment):**
  Akool, Veo, Kling, Runway, Gemini, Azure Speech (no credentials / network egress;
  using secrets is out of scope). `subtitle_style` text burn-in was **attempted** but
  is **blocked in this ffmpeg build** (no `drawtext`/libfreetype, no libass `subtitles`
  filter present). `broll_retrieval`, `avatar_segment`, `voiceover`, `bgm_select`
  require a provider/library and were not run.
- **trial outputs:** written to `/tmp/ms_trials/` (clips + ffprobe logs); **not
  committed** (binaries excluded from the repo by design).

## 2. Per-Shot Results

### BM-1 — Product close-up (`02_tomato_bowl.png`)
- desired result: crisp product detail with gentle motion.
- capability route: `image_to_video` → `qc`.
- candidate tool/provider: **ffmpeg Ken-Burns proxy** (zoom-in). (Generative providers
  Kling/Runway/Veo: SKIPPED — no credentials.)
- input: 941×1672 still + zoom-in spec.
- output artifact: `/tmp/ms_trials/bm1.mp4` — h264, 1080×1920, 30fps, 3.0s, 90 frames, 884,746 B.
- generation time: **0.90s** (`/usr/bin/time -p real`).
- cost estimate: **$0** (local ffmpeg).
- quality verdict: **proxy-acceptable, not generative.** Product stays legible (it is
  the original still); motion is a believable pan/zoom but **not true animation** — a
  fast-preview / fallback tier, not the generative-quality answer.
- failure mode: none (clip valid); the *limitation* is "no real motion."
- fallback result: this **is** the fallback tier; below it is a static still.

### BM-2 — Lifestyle / beach (`01_beach_hook.png`)
- desired result: believable beach ambiance.
- capability route: `image_to_video` (proxy) / would prefer `broll_retrieval` or
  `text_to_video` → `compose` → `qc`.
- candidate tool/provider: **ffmpeg Ken-Burns proxy** (zoom-out). (broll_retrieval /
  text_to_video providers: SKIPPED.)
- input: 941×1672 still + zoom-out spec.
- output artifact: `/tmp/ms_trials/bm2.mp4` — h264, 1080×1920, 30fps, 4.0s, 120 frames, 819,810 B.
- generation time: **1.00s**.
- cost estimate: **$0** (local).
- quality verdict: **proxy-acceptable**; true ambiance/scene synthesis needs a provider
  (not trialled).
- failure mode: none; limitation = static scene (no synthesized motion/scene).
- fallback result: proxy is the fallback; true scene gen deferred.

### BM-3 — Hook shot (`04_eat_tomato.png`)
- desired result: attention-grabbing first 2s, "tasting" feel.
- capability route: `image_to_video` (punch-in) → `qc`.
- candidate tool/provider: **ffmpeg Ken-Burns proxy** (zoom-in). (Generative: SKIPPED.)
- input: 941×1672 still.
- output artifact: `/tmp/ms_trials/bm3.mp4` — h264, 1080×1920, 30fps, 3.0s, 90 frames, 833,698 B.
- generation time: **0.87s**.
- cost estimate: **$0** (local).
- quality verdict: **proxy-acceptable**; real "tasting" motion needs a generative
  provider (not trialled).
- failure mode: none; limitation = no real motion.
- fallback result: proxy is the fallback tier.

### BM-4 — Narration / CTA (`subtitle_style` + `voiceover`)
- desired result: readable CTA card + spoken line.
- capability route: `voiceover` + `compose` + `subtitle_style`.
- candidate tool/provider: ffmpeg `drawtext` (subtitle/CTA text) **attempted**; Azure
  Speech voiceover SKIPPED.
- input: text "Fresh Tomatoes / Order Now" + a subtitle line on BM-3.
- output artifact: **none produced** — both `drawtext` runs failed at ~0.02–0.04s.
- generation time: n/a (immediate filter-init failure).
- cost estimate: n/a.
- quality verdict: **BLOCKED — capability unavailable in this build.** This ffmpeg has
  **no `drawtext` filter** (no libfreetype) and **no libass `subtitles`/`ass` filter**;
  only `overlay`/`colorize` are present.
- failure mode: filter not compiled in → text burn-in cannot run.
- fallback result: subtitle/CTA would require either a **freetype/libass-enabled ffmpeg
  build** or a **pre-rendered PNG → `overlay`** adapter (text rendered upstream). CJK
  (Chinese) subtitles additionally need a CJK font. Voiceover needs a TTS provider.

### BM-5 — Final compose (10-shot proxy: BM-1+BM-2+BM-3)
- desired result: consistent, delivery-ready cut.
- capability route: `compose` + `qc`.
- candidate tool/provider: **ffmpeg concat + ffprobe**.
- input: bm1.mp4 + bm2.mp4 + bm3.mp4 (concat list).
- output artifact: `/tmp/ms_trials/final_cut.mp4` — h264, 1080×1920, 30fps, **10.0s**,
  300 frames, 2,536,686 B, ~2.03 Mbps.
- generation time: **0.09s** (stream copy).
- cost estimate: **$0** (local).
- quality verdict: **PASS** — single delivery-spec cut, exact expected duration
  (3+4+3=10s), consistent resolution/codec/fps across shots; ffprobe confirms all
  fields.
- failure mode: none.
- fallback result: per-shot fallbacks (proxies) flowed into compose without issue;
  audio/subtitle/bgm not present (those routes not run).

## 3. Cross-Tool Comparison

- **image_to_video:** only the **ffmpeg Ken-Burns proxy** was runnable offline (~0.9–1.0s,
  $0, valid h264). It is a **motion proxy, not generative animation** — the right
  fast-preview/fallback tier, but it does **not** answer the "weak output quality" need
  on its own. Generative providers (Kling/Runway/Veo) were **not** trialled (no
  credentials) → their quality/speed/cost remain **unmeasured**.
- **text_to_video:** SKIPPED (provider-only) — unmeasured.
- **broll_retrieval:** SKIPPED (provider/library + license screen) — unmeasured.
- **avatar_segment:** SKIPPED (Akool, future/gated) — unmeasured.
- **voiceover:** SKIPPED (Azure Speech; needs key) — unmeasured.
- **compose / qc:** **ffmpeg + ffprobe = proven, fast (0.09s), free, deterministic,
  secret-free.** Produced and verified a delivery-spec 10s cut. **Strongest result of
  the trial.** (`subtitle_style` burn-in BLOCKED in this build — needs freetype/libass
  or a PNG-overlay adapter.)

## 4. Quality Findings

- **product visibility:** preserved by the proxy (it renders the original still); good.
- **motion quality:** proxy pan/zoom only — believable but **not generative**; real
  motion quality is unmeasured (providers not run).
- **visual relevance:** inherits the input still's relevance; no synthesis tested.
- **subtitle / readability:** **not achievable in this build** (no drawtext/libass);
  blocked finding.
- **audio sync:** not testable — no voiceover/bgm route run (no clips have audio).
- **duration fit:** **exact** — per-shot durations and the 10s composed total matched
  the spec precisely (ffprobe-verified).
- **operator usability:** the proxy+compose path is instant and deterministic; an
  operator could iterate per-shot proxies and compose in ~1s each — but the *output
  quality ceiling* of proxies is low, so this is a backbone, not the quality fix.

## 5. Speed / Cost Findings

- **fastest route:** `compose` (ffmpeg concat, **0.09s**) and `image_to_video` proxy
  (~0.9–1.0s) — both far under the trial-plan fast-preview targets (≤30–60s).
- **best quality route:** **unknown / unmeasured** — the generative providers that would
  raise quality were not trialled offline (no credentials).
- **cheapest route:** ffmpeg (proxy + compose + qc) at **$0**, no secrets, local.
- **unacceptable route:** `subtitle_style` via this ffmpeg build (no drawtext/libass) —
  unusable as-is; needs a different build or a PNG-overlay adapter.

## 6. License / Operational Risk

- **safe:** ffmpeg (`image_to_video` proxy, `compose`, `qc`) — LGPL/GPL local tooling,
  no content-rights issue (inputs are the operator's own stills), no secret, no network.
- **needs review:** generative providers (Akool/Veo/Kling/Runway) — API ToS +
  generated-content rights + credit cost + secret handling; `broll_retrieval` library
  content licensing; `bgm_select` music licensing; Azure Speech voice licensing + key
  handling. All **unverified** (not trialled).
- **blocked:** `subtitle_style` text burn-in in the current ffmpeg build; `face_swap`
  remains **unsuitable** for first integration (ethics/identity), per the review.

## 7. Recommended First Runtime Integration

**image_to_video provider + ffmpeg compose/qc** — *with a scoping qualification.*

The **proven, evidence-backed backbone** from this trial is **ffmpeg `compose` + `qc`
(+ the Ken-Burns `image_to_video` proxy as the deterministic fallback tier)**: fast
(0.09s compose), free, secret-free, delivery-spec-correct. That backbone is ready to be
specified for a first integration now.

The **generative `image_to_video` provider** (the part that actually lifts output
quality) was **not measurable offline** here (no credentials), so the provider choice
must be settled by a **follow-on credentialed offline trial** before it enters the same
Gate Spec. Recommended framing for Phase D: integrate the **ffmpeg compose/qc + proxy
backbone first**, with the generative provider as a pluggable `image_to_video` adapter
slotted in once its credentialed trial passes §4 decision criteria.

## 8. Boundary

- **runtime changed:** No.
- **repo code changed:** No (docs-only: this report + owner summary).
- **secrets committed:** No (no provider keys used or stored; provider routes not run).
- **provider adapter added:** No.
- **UI changed:** No.
- Also: no `gateway/**` / services / templates / tests / `schemas/**` / `docs/contracts/**`
  change; no four-layer state change; no vendor exposure; no Slot Workflow v2 PR-1; no
  Gate Spec §13 signoff; no automatic production routing decision. Trial binaries live
  in `/tmp` and are not committed.

## 9. Owner Decision Needed

Recommend exactly one:

- **proceed to Runtime Gate Spec for first integration** *(recommended)* — scope it to
  the **proven ffmpeg compose/qc + Ken-Burns image_to_video proxy backbone** (free,
  deterministic, secret-free), with the generative `image_to_video` provider added as a
  pluggable adapter pending its own credentialed offline trial;
- **run more offline trials** — specifically a **credentialed** trial of the generative
  providers (Kling/Runway/Veo) + Azure voiceover + a freetype/libass `subtitle_style`
  path, before any integration;
- **hold**;
- **block.**

**Recommendation:** **proceed to a Runtime Gate Spec for the ffmpeg compose/qc + proxy
backbone**, *and* in parallel authorize a **credentialed offline provider trial** (still
no runtime) to settle the generative `image_to_video` choice and the
subtitle/voiceover gaps before they enter the integration. This banks the proven,
zero-risk backbone now while the quality-lifting provider decision is made on real data.

---

*This is a docs-only offline trial report. It ran only local, secret-free ffmpeg/ffprobe
trials; all credentialed-provider routes were honestly skipped. It authorizes no code,
integrates no provider, exposes no vendor, and changes no contract/schema or the
four-layer state model.*
