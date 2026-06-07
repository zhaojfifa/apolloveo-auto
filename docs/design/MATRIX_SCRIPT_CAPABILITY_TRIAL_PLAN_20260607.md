# Matrix Script — Capability Trial Plan (2026-06-07)

Status: **TRIAL PLAN — docs-only. Not implementation authority. Not a Gate Spec. Not a
provider integration. Not a Bucket A change.** Designs **offline** capability trials to
improve actual video output quality, so that decision-grade speed / quality / cost /
license data exists before any runtime-integration Gate Spec (Phase D of the upgrade
review).

Derivation:
- `docs/reviews/MATRIX_SCRIPT_VIDEO_CAPABILITY_UPGRADE_REVIEW_20260607.md` (capability
  kinds, candidate map, benchmark seed, Phase A–E path) — this plan is **Phase A/B**.
- Substrate: the merged #211/#212 visual-material path (the one actionable lever today).

This plan proposes **offline** trials only. It selects no vendor for runtime, wires no
provider, changes no schema/contract, exposes no vendor in the UI, and does not touch
the four-layer state model. When it conflicts with Bucket A
(`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`), `ENGINEERING_RULES.md`, or
`CURRENT_ENGINEERING_FOCUS.md`, the underlying authority wins.

---

## 0. How to read this plan

Each benchmark shot below is an **offline evaluation target**, not a build step. Trials
run Tyler-local / sandbox (no repo runtime, no secrets in repo, no production
generation wired into the line). Results feed a Phase C routing decision and a Phase D
Gate Spec. "candidate class" uses the review's taxonomy: **active / donor-reference /
future / unsuitable**.

Capability kinds in scope (review §4): `image_to_video`, `text_to_video`,
`broll_retrieval`, `avatar_segment`, `voiceover`, `subtitle_style`, `bgm_select`,
`compose`, `qc`.

Backend supply in scope (review §6): Akool · Veo · Kling · Runway (or equiv) · Gemini ·
Azure Speech · ffmpeg · safe GitHub donor tools (license/security-screened first).

---

## 1. Benchmark shots (tomato beach case, MS-TOMATO-BEACH-001)

Five benchmark shots spanning the line's real shot intents. Each is specified with:
required capability, candidates, I/O expectations, success criteria, fallback, speed
target, cost estimate, license/operational risk, adapter difficulty, and per-candidate
classification.

### BM-1 — Product close-up (切开番茄)

- **Required capability:** `image_to_video` (animate an uploaded product still while
  preserving product detail) → `qc`.
- **Candidate tools/providers/donors:**
  - Kling — *active* (strong motion on stills).
  - Runway (or equiv) — *active* (mature image-to-video API).
  - Veo — *active* (high quality; quota/access to verify).
  - ffmpeg Ken-Burns (pan/zoom) — *donor-reference* (cheap motion proxy / fallback).
  - Akool — *future* for this kind (stronger fit for avatar/face; see BM-4).
- **Input/output expectations:** in = uploaded still (the #211 `msmaterial://` bytes) +
  short motion prompt; out = 3–5s clip, ≥720p, h.264/mp4, product centered & legible.
- **Success criteria (qc, review §9):** product visible & legible; no warping/flicker on
  the product; motion plausible; duration within shot window.
- **Fallback path:** ffmpeg Ken-Burns on the still (motion proxy) → static still.
- **Speed target:** ≤ ~30s for a fast-preview-tier clip.
- **Cost estimate:** per-clip API cost (Kling/Runway/Veo) — record actual in trial;
  ffmpeg fallback ≈ free/local.
- **License / operational risk:** API ToS + generated-content rights; product likeness
  is the operator's own asset (low). GPU/credit dependency for the API path.
- **Adapter difficulty:** medium — wrap as `image_to_video` adapter behind the internal
  contract; reuse the existing uploaded-bytes path.
- **Classification:** Kling / Runway / Veo = **active**; ffmpeg = **donor-reference
  (fallback)**; Akool = **future** for this kind.

### BM-2 — Lifestyle scene (沙滩远景)

- **Required capability:** `broll_retrieval` (relevant beach ambiance) OR
  `text_to_video` (synthesize scene) → `compose` → `qc`.
- **Candidate tools/providers/donors:**
  - Stock/library `broll_retrieval` via a safe GitHub/media tool — *donor-reference*
    (license screen mandatory).
  - Veo / Kling / Runway `text_to_video` — *active* (synthesize a beach scene).
  - Gemini — *donor-reference* (scene-prompt drafting / query expansion for retrieval).
- **Input/output expectations:** in = scene description / query + duration; out = 3–6s
  ambiance clip, ≥720p, license-clean.
- **Success criteria:** scene relevant & coherent; license-clean; blends with adjacent
  shots in `compose`.
- **Fallback path:** reuse an operator-uploaded clip → placeholder.
- **Speed target:** ≤ ~60s fast-preview.
- **Cost estimate:** retrieval ≈ low/free (library) vs text_to_video per-clip API cost.
- **License / operational risk:** **highest here** — stock/library content licensing +
  generated-scene rights; the screen must reject any tool with unclear content rights.
- **Adapter difficulty:** medium (retrieval) / medium-high (text_to_video).
- **Classification:** text_to_video providers = **active**; retrieval donor tools =
  **donor-reference (pending license screen)**; Gemini = **donor-reference**.

### BM-3 — Hook shot (吃番茄特写)

- **Required capability:** `image_to_video` / `text_to_video` (attention-grabbing first
  2s, real "tasting" feel) → `qc`.
- **Candidate tools/providers/donors:** Kling / Runway / Veo — *active*; ffmpeg
  punch-in proxy — *donor-reference (fallback)*.
- **Input/output expectations:** in = uploaded "tasting" still or prompt; out = 2–4s
  high-impact clip; strong first frame.
- **Success criteria:** compelling first frame; plausible motion; no artifacts on the
  face/food; duration fit.
- **Fallback path:** best uploaded still + ffmpeg punch-in → static.
- **Speed target:** ≤ ~30s fast-preview.
- **Cost estimate:** per-clip API cost; fallback ≈ free.
- **License / operational risk:** generated-content rights; food/face plausibility
  (no identity claims). Moderate.
- **Adapter difficulty:** medium (shares the BM-1 `image_to_video` adapter).
- **Classification:** Kling / Runway / Veo = **active**; ffmpeg = **donor-reference**.

### BM-4 — Narration / CTA (行动号召)

- **Required capability:** `voiceover` + `compose` + `subtitle_style` (readable CTA card
  with spoken line); optional `avatar_segment` → `qc`.
- **Candidate tools/providers/donors:**
  - Azure Speech — *active* (multilingual TTS; secret handling deferred to Gate Spec).
  - Akool — *active* for `avatar_segment` (talking presenter), *gated* for face_swap.
  - ffmpeg — *active* for `compose` + `subtitle_style` (burn-in / styling).
  - Gemini — *donor-reference* (CTA copy drafting / SSML hints).
- **Input/output expectations:** in = CTA text (+ optional presenter); out = spoken
  audio track + styled subtitle + composed card, audio synced.
- **Success criteria (qc):** audio sync; subtitle readable (contrast/size/safe-area);
  levels balanced (ducking); duration fit.
- **Fallback path:** static CTA card + styled subtitle (no voiceover) → text card only.
- **Speed target:** ≤ ~30s fast-preview (TTS + compose).
- **Cost estimate:** TTS per-character cost (Azure); avatar per-segment cost (Akool);
  ffmpeg ≈ free.
- **License / operational risk:** TTS voice licensing; **avatar/face_swap = highest
  ethics/identity risk** — gated, not in the first integration. Secret handling for
  Azure deferred to Gate Spec (no secrets in repo).
- **Adapter difficulty:** voiceover = medium; subtitle_style/compose = low (ffmpeg);
  avatar_segment = high (gated).
- **Classification:** Azure Speech = **active (voiceover)**; ffmpeg = **active
  (compose/subtitle_style)**; Akool avatar = **future/gated**; face_swap = **unsuitable
  for first integration (ethics/identity)**.

### BM-5 — Final compose (10-shot cut)

- **Required capability:** `compose` + `qc` (assemble all shots + audio + subtitle + bgm
  into a delivery-ready cut).
- **Candidate tools/providers/donors:** ffmpeg — *active* (compose + probe-based qc);
  `bgm_select` via a safe library/GitHub tool — *donor-reference* (license screen);
  Gemini — *donor-reference* (qc heuristic assist).
- **Input/output expectations:** in = ordered shot clips + audio + subtitle + bgm; out =
  single delivery-spec mp4 (resolution/codec/container), consistent across shots.
- **Success criteria (qc, full §9 gate):** end-to-end relevance/visibility/motion/
  subtitle/audio-sync/duration/delivery-readiness pass; `official_publish_ready` stays
  `false` until the delivery contract gate says otherwise.
- **Fallback path:** per-shot fallbacks applied (BM-1..BM-4), compose still proceeds.
- **Speed target:** final render run **once** (not per-iteration); minutes acceptable.
- **Cost estimate:** ffmpeg ≈ free/local; bgm library cost low.
- **License / operational risk:** BGM licensing (screen mandatory); encode settings
  must meet delivery spec. Low-moderate.
- **Adapter difficulty:** low-medium (ffmpeg compose/qc are local-friendly).
- **Classification:** ffmpeg = **active**; bgm/qc donor tools = **donor-reference
  (pending license/security screen)**.

---

## 2. Candidate summary (classification roll-up)

| Capability kind | Active candidate(s) | Donor / reference | Future | Unsuitable |
|-----------------|---------------------|-------------------|--------|------------|
| `image_to_video` | Kling, Runway, Veo | ffmpeg (motion proxy) | Akool | — |
| `text_to_video` | Veo, Kling, Runway | Gemini (prompt drafting) | — | — |
| `broll_retrieval` | — | safe GitHub/library tool (license-screened), Gemini (query) | provider-backed retrieval | unlicensed scrapers |
| `avatar_segment` | — | — | Akool | — |
| `face_swap` | — | — | — | **unsuitable (first integration; ethics/identity)** |
| `voiceover` | Azure Speech | Gemini (SSML/copy) | — | — |
| `subtitle_style` | ffmpeg | — | — | — |
| `bgm_select` | — | safe library/GitHub tool (license-screened) | provider-backed | unlicensed music |
| `compose` | ffmpeg | local media helpers | — | — |
| `qc` | ffmpeg (probe) | Gemini (heuristic assist) | learned-QC model | — |

**First-integration shortlist (for the eventual Phase D Gate Spec, not authorized here):**
the **already-actionable visual lever** — `image_to_video` (one active provider, picked
from BM-1/BM-3 trial data) + `compose` + `qc` via **ffmpeg** (local, free, low-risk).
Audio/avatar/bgm follow in later gated phases.

## 3. Trial execution model (offline, Tyler-local)

- **Environment:** Tyler-local / sandbox; no repo runtime; no secrets committed to the
  repo; provider keys (if a trial needs one) stay in Tyler's local env, never in repo.
- **Method per benchmark:** run the candidate offline on the BM input, capture the
  output clip, score it against the success criteria (§9 of the review), and record
  speed + cost + license notes in the trial log.
- **Recorded per candidate (review §5 intake):** capability kind, I/O contract, license
  risk, runtime dependency, speed, quality (vs qc), cost, adapter difficulty,
  classification.
- **Output of trials:** a comparison table per capability kind → feeds Phase C (choose
  default routing) → feeds Phase D (first-integration Gate Spec).
- **GitHub donor tools:** pass a **license + security screen** before any trial (no
  unvetted code execution; no network egress of secrets; reject unclear content rights).

## 4. Decision criteria (how a candidate becomes "active for Phase D")

A candidate advances toward a Phase D Gate Spec only if, on the benchmarks:
1. it passes the §9 quality gate on its target shot(s);
2. its fast-preview speed meets the BM target (or a documented near-miss);
3. its cost is acceptable and recorded;
4. its license/operational risk is clear and acceptable (no unsuitable flags);
5. its adapter fits the internal capability-kind contract without UI/state change.

A candidate failing any of (1)–(5) is reclassified donor-reference / future /
unsuitable with the reason logged.

## 5. Boundary

- **docs-only** — this plan adds one design doc; no code.
- **no runtime integration** — no `gateway/**`, services, templates, tests touched.
- **no provider integration** — Akool/Veo/Kling/Runway/Gemini/Azure not wired; trials
  are offline; the candidate map is provisional until trial data exists.
- **no schema/contract change** unless a later, separately-approved Gate Spec authorizes
  it (`schemas/**`, `docs/contracts/**` frozen here).
- **no vendor exposure in UI** — capability kinds only; no vendor/model/credit/engine in
  any operator payload.
- **no four-layer state change** — new capability would produce L2 artifact facts behind
  the existing boundary; this plan does not redefine the boundary.
- **no secrets in repo** — any provider key used in an offline trial stays Tyler-local.
- Does **not** authorize Slot Workflow v2 PR-1, does **not** fill the Gate Spec §13
  signoff, does **not** touch Hot Follow / Digital Anchor.

## 6. Owner Decision Needed

Recommend exactly one:
- **proceed to run the offline trials** (execute §1 benchmarks Tyler-local, record §3
  data) → then Phase C routing decision (docs) → then Phase D Gate Spec authoring;
- **revise the trial plan** (adjust benchmarks, candidates, criteria, or shortlist);
- **hold.**

**Recommendation:** **proceed to run the offline trials**, starting with the
first-integration shortlist (`image_to_video` provider trial on BM-1/BM-3 + ffmpeg
`compose`/`qc`), because that is the already-actionable lever and the cheapest path to
real quality/speed/cost data for a Phase D Gate Spec. All trials remain offline +
Tyler-local; no runtime, no provider wiring, no secrets in repo.

---

*This is a docs-only trial plan. It runs no trials by itself, integrates no provider,
opens no wave, exposes no vendor, and changes no contract/schema or the four-layer state
model. Runtime integration requires a separate, Owner-gated Gate Spec (review Phase D).*
