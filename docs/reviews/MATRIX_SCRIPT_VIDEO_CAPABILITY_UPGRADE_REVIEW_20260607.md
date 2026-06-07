# Matrix Script — Video Capability Upgrade Review (2026-06-07)

Status: **REVIEW — docs-only. Not implementation authority. Not a Gate Spec. Not a
provider integration. Not a Bucket A change.** A diagnosis of how to improve **actual
video generation capability** (the production backend), distinct from the UI/flow work
that the Slot Workflow v2 track already covers.

Author posture: ApolloVeo 2.0 Architect, capability-supply lens.
Branch baseline: `main` after #229 (preview merged).

This review proposes capability **kinds** and an intake/benchmark model — it does
**not** select a vendor, wire a provider, change schemas/contracts, expose a vendor in
the UI, or touch the four-layer state model. When it conflicts with Bucket A
(`docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`), `ENGINEERING_RULES.md`, or
`CURRENT_ENGINEERING_FOCUS.md`, the underlying authority wins.

---

## 1. Problem Statement

The bottleneck has shifted. Harness X process is working (Product Plan → Preview →
Operator Review → Gate Spec all landed cleanly for Slot Workflow v2), and the UI/flow
re-planning is useful. **But the larger constraint is now production capability, not
process and not UI.** Concretely:

- **Generation is slow** — the operator waits a long time for a single V1/V2.
- **The production path is overly complex** — many steps to get one main video.
- **Output quality is weak** — generated clips are not reliably broadcast-usable.
- **Only visual material is really actionable** — upload/replace of the visual slot is
  the one path that genuinely changes output (#211/#212).
- **Voice / subtitle / BGM are not yet real production slots** — they are status /
  display / future, because no real backend action produces them on this line.

No amount of queue/panel re-arrangement (Slot Workflow v2) fixes this; the slots are
honest precisely *because* the underlying capability is missing. This review diagnoses
the **capability supply** problem and proposes a docs-first upgrade path. It does not
start runtime.

## 2. Current Matrix Script Capability Baseline

What the line can actually do today (from the #202–#215 substrate + Guided/Slot v2 docs):

| Capability | State today |
|------------|-------------|
| **V1 generation** | script → shot-plan → `final.mp4` → artifact_staged → preview_url; works, but slow and quality-variable. |
| **Shot cards** | per-shot decision surface (keep/supplement/replace) + #215 trace; Slot v2 converges to a queue. |
| **Material upload / replacement** | real: `msmaterial://`, `bytes_resolvable=true`, `local_workspace` scope (#211). The one truly-actionable production input. |
| **Regenerate V2** | V2 candidate consumes uploaded bytes (image direct; video first-frame when extraction succeeds) (#212); off-thread, V1 protected. |
| **V1/V2 confirmation** | explicit confirm promotes V2 → main; discard keeps V1; delivery follows confirmed main. |
| **Delivery candidate** | follows confirmed main only; `official_publish_ready=false`. |
| **Subtitle / audio / BGM status** | **status / display only** — no operator-effective backend action on this line. |
| **Active vs display-only vs future slots** | visual_material = **active**; text_copy / subtitle = **display-only**; voiceover / bgm = **future** (Slot v2 Gate Spec §6). |

**Reading:** the line has exactly one real production lever (visual material in/out) and
a confirm/deliver spine around it. Everything audio/text is honest placeholder. The
upgrade target is to turn one-lever-slow-weak into several-levers-fast-good — at the
**capability** layer, behind the existing four-layer boundary.

## 3. Capability Gaps

Where production quality/speed actually falls short:

- **Image-to-video quality** — uploaded stills animate weakly (limited/again motion,
  artifacts); product detail not preserved.
- **Text-to-video / scene generation** — no real generative scene synthesis for shots
  lacking material; falls back to reuse/placeholder.
- **B-roll retrieval** — no retrieval of relevant stock/library clips to fill generic
  shots (lifestyle, ambiance), forcing manual upload.
- **Avatar / person-segment generation** — no narrator/spokesperson segment capability.
- **Voiceover generation** — none (voiceover slot is future).
- **Subtitle styling** — subtitles are derived/status only; no burn-in or styled
  rendering control.
- **BGM selection** — none (bgm slot is future); no music bed selection/ducking.
- **Final render quality** — composite/encode quality and consistency across shots is
  not gated.
- **Speed / cost** — single-path generation is slow and not tiered (no cheap fast
  preview vs expensive final).

## 4. Tool Registry Direction

Define capability **kinds**, not vendor UIs. A Tool Registry maps each kind to one or
more interchangeable backends behind a stable internal contract; the operator and the
four-layer state never see the vendor. Capability kinds:

```
image_to_video     still / product image → short animated clip
text_to_video      prompt / scene description → generated clip
avatar_segment     script line → talking-presenter segment
face_swap          identity-swap on an existing segment (gated; license/ethics risk)
broll_retrieval    query → relevant stock / library clip(s)
voiceover          text → spoken audio track
subtitle_burn      text + timing → burned-in subtitle render
subtitle_style     subtitle appearance / layout styling
bgm_select         mood / duration → background music bed (with ducking)
compose            assemble shots + audio + subtitle + bgm → final render
qc                 automated quality checks on a clip / final (see §9)
```

Registry principle: each kind has an **input/output contract** (§5); a vendor is an
**adapter** behind that contract, swappable without UI/state change. No vendor name,
model id, credit, or engine ever enters an operator payload (red line, §12).

## 5. GitHub / Skill / Donor Intake Model

How any GitHub project, skill, or external tool is evaluated before it is even
considered a candidate. Each intake is scored on:

| Dimension | What to record |
|-----------|----------------|
| **capability kind** | which §4 kind(s) it serves |
| **input/output contract** | accepted inputs, produced outputs, formats, resolution/codec |
| **license risk** | OSS license / commercial terms / model weights license / content rights |
| **runtime dependency** | GPU? external service? heavy install? network egress? |
| **speed** | latency for preview vs final; batch behavior |
| **quality** | measured against §9 quality gate on benchmark shots (§10) |
| **cost** | per-clip / per-minute / subscription; free tier limits |
| **adapter difficulty** | effort to wrap behind the §5 internal contract |
| **classification** | **donor / reference / runtime candidate** |

Classification meanings:
- **runtime candidate** — could become a real adapter behind a kind, pending its own
  Gate Spec.
- **donor / reference** — borrow patterns/code/approach; not wired as-is.
- **future** — promising but not now (cost/quality/license/maturity).
- **not suitable** — fails license/safety/quality/dependency screening.

Intake is **docs-only**; nothing is installed into runtime by this review. Skill intake
additionally obeys the Harness X Skill Adoption Policy (Tyler-local, read-only-first).

## 6. Candidate Provider / Donor Map

Backend **supply** candidates only — **no UI, no vendor exposure, no integration here.**
This is a first-pass map to be validated offline in Phase B (§11); classifications are
provisional pending benchmark data (§10).

| Candidate | Likely kind(s) | Provisional class | Notes (to verify offline) |
|-----------|----------------|-------------------|----------------------------|
| **Akool** | avatar_segment, face_swap, image_to_video | active candidate (already referenced in repo lore) | gated; license/ethics for face_swap; keep behind contract; never in UI |
| **Veo (Google)** | text_to_video, image_to_video | active candidate | quality high; cost/quota + access to verify |
| **Kling** | text_to_video, image_to_video | active candidate | strong motion; access/region + terms to verify |
| **Runway (or equivalent)** | text_to_video, image_to_video | active candidate | mature API; cost to verify |
| **Azure Speech** | voiceover, (subtitle timing) | active candidate | TTS quality + multilingual; secret handling out of scope until Gate Spec |
| **Gemini** | text_to_video (Veo-backed), prompt/scene drafting, qc-assist | donor / reference + future | useful for prompt/scene structuring + QC heuristics |
| **ffmpeg** | compose, subtitle_burn, basic image_to_video (Ken Burns), qc (probe) | active candidate (local) | already local-friendly; no external cost; foundation for compose/qc |
| **local media helpers** | broll_retrieval (local library), subtitle_style, compose helpers | donor / reference | extend existing `shot_material_storage` patterns; local-only |
| **GitHub video/media tools** (vetted, safe) | broll_retrieval, subtitle_style, qc | donor / reference | evaluate per §5 intake; license/dependency screen first |

> No candidate is selected, integrated, or installed by this review. Akool / providers
> remain **not integrated**; Hot Follow / Digital Anchor untouched.

## 7. Shot-Level Routing Model

Different shot intents need different capability kinds. A routing model picks the kind
per shot (the operator sees a result, never the route):

| Shot intent | Preferred capability route | Fallback |
|-------------|----------------------------|----------|
| **product close-up** | uploaded material → image_to_video (preserve product detail) | reuse existing material / placeholder |
| **lifestyle scene** | broll_retrieval → compose; or text_to_video | reuse material |
| **hook shot** | text_to_video / strong image_to_video (attention-grabbing) | best available reuse |
| **avatar / narration shot** | avatar_segment + voiceover | static title + voiceover; or text card |
| **CTA card** | compose (text card) + bgm_select | static card |
| **uploaded material replacement** | image_to_video on the uploaded bytes (current #212 path, upgraded) | image-direct (no motion) |
| **B-roll filler** | broll_retrieval | placeholder / reuse |

Routing is a **backend decision** mapped from existing shot-plan signals; it adds no
operator control surface and no vendor exposure. It is the future home of "this shot is
a product close-up → use image_to_video adapter X."

## 8. Fast Preview vs Final Render

Tier generation to cut operator waiting:

- **Fast preview path** — cheap, low-res / short / low-step generation (or even a
  representative still + motion proxy) for the operator to judge composition quickly.
  Goal: seconds-to-low-minutes, not a long single render.
- **Targeted regenerate path** — regenerate only the shots that changed (the Slot v2
  Assignment set), not the whole video; reuse unchanged shots.
- **Final render path** — full-quality compose/encode, run only after the operator
  confirms the composition is right.

Why this reduces waiting: the operator iterates on **fast preview + per-shot targeted
regenerate**, and pays the expensive **final render** cost once, at the end — instead of
paying full cost on every iteration of the whole video.

## 9. Quality Gate

Minimum automated quality checks (a `qc` capability kind) before a clip/final is
offered as a candidate:

- **visual relevance** — the clip matches the shot intent / script beat.
- **product visibility** — for product shots, the product is present and legible.
- **motion quality** — no severe artifacts / warping / flicker; motion is plausible.
- **subtitle readability** — contrast, size, safe-area, no overrun, correct timing.
- **audio sync** — voiceover/BGM aligned; no clipping; levels balanced (ducking works).
- **duration fit** — shot/final duration within the target window.
- **delivery readiness** — codec/resolution/container meet delivery spec;
  `official_publish_ready` still gated by the delivery contract (stays `false` until an
  approved gate says otherwise).

QC failures route a shot back to regenerate (or to a fallback per §7) rather than
surfacing a broken clip to the operator.

## 10. Benchmark Plan

Use benchmark shots from the **tomato beach** case (MS-TOMATO-BEACH-001). For each:
desired result, required capability, success criteria, acceptable fallback, speed
target. (These are evaluation targets for Phase B offline trials — not a build order.)

| # | Benchmark shot | Desired visual result | Required capability | Success criteria | Acceptable fallback | Speed target (preview) |
|---|----------------|------------------------|---------------------|------------------|---------------------|------------------------|
| B1 | **Product close-up (切开番茄)** | crisp product detail, gentle motion, appetite appeal | image_to_video (on uploaded still) | product legible, no warping, ≤ motion artifacts | image-direct (static) | ≤ ~30s preview |
| B2 | **Lifestyle scene (沙滩远景)** | believable beach ambiance | broll_retrieval or text_to_video | relevant, license-clean, coherent | reuse uploaded material | ≤ ~60s preview |
| B3 | **Hook shot (吃番茄特写)** | attention-grabbing first 2s, real "tasting" feel | image_to_video / text_to_video | strong first frame, plausible motion | best reuse still | ≤ ~30s preview |
| B4 | **Narration / CTA (行动号召)** | clear spoken CTA + readable card | voiceover + compose + subtitle_burn | audio sync, subtitle readable, duration fit | static card + text | ≤ ~30s preview |
| B5 | **Final compose (10-shot cut)** | consistent, delivery-ready cut | compose + qc | passes §9 gate end-to-end | per-shot fallbacks applied | final render, run once |

Benchmarks are measured offline (Phase B); no runtime integration is implied.

## 11. Recommended Upgrade Path

Docs-first, gate-spec-first, Owner-gated at each runtime boundary:

- **Phase A — Capability inventory + Tool Registry docs.** Author the capability-kind
  registry (§4) + the §5 intake template as docs; no runtime. (This review is the seed.)
- **Phase B — Offline provider / donor trials.** Evaluate §6 candidates against the §10
  benchmarks offline (Tyler-local / sandbox), recording speed/quality/cost/license per
  §5. No repo runtime change; no secrets in repo.
- **Phase C — Choose default Matrix Script routing.** From Phase B data, pick the
  default capability per shot intent (§7) and the fast/final tiering (§8) — as a docs
  decision.
- **Phase D — Gate Spec for first runtime integration.** Author a Gate Spec for the
  **first** capability kind to integrate (likely the upgraded `image_to_video` on the
  already-actionable visual slot, + `compose`/`qc` via local ffmpeg), behind the
  internal contract, no vendor in UI, four-layer boundary preserved. Owner-gated S5→S6.
- **Phase E — Operator trial with real generated clips.** Run the Slot Workflow v2
  operator loop against real upgraded output; validate speed + quality against §9/§10.

Each phase is its own Harness X artifact; only Phase D's signed Gate Spec opens runtime.

## 12. Boundary

- **docs-only** — this review adds two docs (this file + owner summary); no code.
- **no runtime** — no `gateway/**`, services, templates, tests touched.
- **no provider integration** — no Akool/Veo/Kling/Runway/Azure/Gemini wiring; the §6
  map is provisional and offline-verified later.
- **no schema/contracts change** unless a later, separately-approved Gate Spec authorizes
  it (`schemas/**`, `docs/contracts/**` frozen here).
- **no Harness X skill installation inside this review** — skill adoption is the
  separate Tyler-local policy track (PR #231); this review installs nothing.
- **no vendor exposure in UI** — capability kinds only; no vendor/model/credit/engine in
  any operator payload (inherited red line).
- **no change to the four-layer state model** — L1 step status / L2 artifact facts / L3
  attempt resolution / L4 operator summary boundaries are preserved; new capability
  produces L2 artifact facts behind the existing boundary, it does not redefine it.
- Does **not** authorize Slot Workflow v2 PR-1, does **not** fill the §13 Gate Spec
  signoff, does **not** touch Hot Follow / Digital Anchor.

## 13. Owner Decision Needed

Recommend exactly one:

- **proceed to Capability Trial Plan** *(recommended)* — author Phase A/B as the next
  docs track: the Tool Registry doc + the offline benchmark trial plan against §10, so
  real speed/quality/cost/license data can inform a Phase D Gate Spec. Still docs-only +
  offline; no runtime.
- **revise review** — adjust capability kinds, candidate map, benchmarks, or phasing.
- **hold** — keep capability upgrade parked; continue Slot Workflow v2 docs closure only.

**Recommendation:** **proceed to Capability Trial Plan (Phase A/B, docs + offline)**.
The production-capability bottleneck is the real blocker; a docs Tool Registry +
offline benchmark trial is the cheapest way to get decision-grade data before any
runtime integration Gate Spec.

---

*This is a docs-only capability review. It authorizes no code, integrates no provider,
opens no wave, exposes no vendor, and changes no contract/schema or the four-layer
state model. Runtime integration requires a separate, Owner-gated Gate Spec (Phase D).*
