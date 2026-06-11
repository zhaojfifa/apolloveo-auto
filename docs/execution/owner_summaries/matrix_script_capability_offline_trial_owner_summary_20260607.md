# Owner Summary — Matrix Script Capability Offline Trial (2026-06-07)

Docs-only. One-page summary for the Owner. Not authority; evidence only.

Full report: `docs/execution/MATRIX_SCRIPT_CAPABILITY_OFFLINE_TRIAL_REPORT_20260607.md`

## What was run

Real, offline, **secret-free** trials with **ffmpeg 8.1.1 + ffprobe** on the four local
tomato-beach stills (`assets/matrix_script_assets/MS-TOMATO-BEACH-001/*.png`). All
credentialed-provider routes were **honestly skipped** (no keys / offline) — no provider
output or metric was fabricated. Trial binaries live in `/tmp` (not committed).

## Headline results (real metrics)

- **image_to_video (ffmpeg Ken-Burns proxy):** ~0.9–1.0s per 3–4s 1080×1920 h264 clip,
  $0. Valid clips — but a **motion proxy, not generative animation** (fallback tier, not
  the quality fix).
- **compose (ffmpeg concat) + qc (ffprobe):** **strongest result** — composed a
  delivery-spec **10.0s** 1080×1920 h264 cut in **0.09s**, $0, deterministic,
  secret-free; ffprobe verified resolution/duration/codec/fps/bitrate/frames.
- **subtitle_style:** **BLOCKED** in this ffmpeg build (no `drawtext`/libfreetype, no
  libass). Needs a freetype/libass build or a pre-rendered-PNG → `overlay` adapter; CJK
  needs a CJK font.
- **text_to_video / broll_retrieval / avatar_segment / voiceover / bgm_select:**
  **SKIPPED** (provider/library + credentials needed) — unmeasured.

## Quality / speed / cost / risk

- fastest: compose (0.09s) + proxy (~1s) — well under targets. cheapest: ffmpeg ($0).
- best-quality route: **unknown** — the generative providers that lift quality were not
  trialled (no credentials).
- duration fit exact; product visibility preserved by the proxy; audio/subtitle not
  testable (routes not run / blocked).
- safe: ffmpeg (proxy/compose/qc). needs-review: all providers (ToS, content rights,
  credit, secret handling), broll/bgm licensing. blocked: subtitle burn-in (this build);
  face_swap remains unsuitable for first integration.

## Recommended first runtime integration

**image_to_video provider + ffmpeg compose/qc**, scoped so the **proven ffmpeg
compose/qc + Ken-Burns proxy backbone** (free, deterministic, secret-free) is specified
first, with the **generative image_to_video provider added as a pluggable adapter
pending its own credentialed offline trial**.

## Boundary confirmations

- runtime changed: No · repo code changed: No (docs-only) · secrets committed: No
- provider adapter added: No · UI changed: No · four-layer state changed: No
- no `gateway/**`/services/templates/tests/schemas/contracts · no vendor in UI
- no Slot Workflow v2 PR-1 · no Gate Spec §13 signoff · no automatic routing decision

## Owner decision needed (report §9)

- **proceed to Runtime Gate Spec for first integration** (ffmpeg compose/qc + proxy
  backbone; generative provider as pluggable adapter pending credentialed trial) — *recommended*;
- **run more offline trials** (credentialed providers + voiceover + a working
  subtitle_style path);
- **hold**;
- **block**.

Recommendation: **proceed to a Runtime Gate Spec for the proven ffmpeg backbone**, and
**in parallel authorize a credentialed offline provider trial** (still no runtime) to
settle the generative image_to_video / subtitle / voiceover gaps on real data before
they enter the integration.
