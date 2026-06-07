# Owner Summary — Matrix Script Video Capability Upgrade Review (2026-06-07)

Docs-only. One-page summary for the Owner. Not authority; the review governs its own
scope and is itself only a diagnosis.

Review: `docs/reviews/MATRIX_SCRIPT_VIDEO_CAPABILITY_UPGRADE_REVIEW_20260607.md`

## The shift

Harness X process works and Slot Workflow v2 (UI/flow) is useful — but the **real
bottleneck is now production capability**, not process or UI: generation is slow, the
path is complex, output quality is weak, only the **visual material** slot is truly
actionable, and voice/subtitle/BGM are not yet real production slots. UI re-arrangement
cannot fix this; the slots are honest *because* the capability is missing.

## What the review proposes (capability layer, not vendor UI)

- **Capability kinds** (not vendors): `image_to_video`, `text_to_video`,
  `avatar_segment`, `face_swap`, `broll_retrieval`, `voiceover`, `subtitle_burn`,
  `subtitle_style`, `bgm_select`, `compose`, `qc` — each behind a stable internal
  contract; vendors are swappable adapters, never exposed in the UI.
- **Intake model** for GitHub/skill/donor tools: scored on kind, I/O contract, license,
  dependency, speed, quality, cost, adapter difficulty → classified donor / reference /
  runtime-candidate / future / not-suitable.
- **Provisional candidate map** (offline-verified later, none integrated): Akool /
  Veo / Kling / Runway / Azure Speech as active candidates; Gemini + local media
  helpers as donor/reference; **ffmpeg** as the local foundation for compose/qc.
- **Shot-level routing** (backend decision): product close-up / lifestyle / hook /
  avatar / CTA / replacement / B-roll → preferred capability + fallback.
- **Fast preview vs targeted regenerate vs final render** tiering — iterate cheap,
  regenerate only changed shots, pay full render once at the end → less operator waiting.
- **Quality gate** (`qc`): visual relevance, product visibility, motion, subtitle
  readability, audio sync, duration fit, delivery readiness.
- **Benchmark plan**: 5 tomato-beach shots (product close-up / lifestyle / hook /
  narration-CTA / final compose) with desired result, capability, success criteria,
  fallback, speed target.
- **Upgrade path**: Phase A capability inventory + Tool Registry docs → Phase B offline
  provider/donor trials → Phase C choose default routing → Phase D Gate Spec for first
  runtime integration (Owner-gated S5→S6) → Phase E operator trial with real clips.

## Boundary confirmations

- docs-only (2 files); no runtime, no `gateway/**`, no services/templates/tests.
- no provider integration; Akool/Veo/Kling/Runway/Azure/Gemini **not wired**; map is
  provisional + offline-verified later.
- no schema/contracts change (unless a later, separately-approved Gate Spec authorizes).
- no Harness X skill installed inside this review (skill adoption is the separate
  Tyler-local policy track, PR #231).
- no vendor exposure in UI; no change to the four-layer state model.
- does not authorize Slot Workflow v2 PR-1; does not fill the Gate Spec §13 signoff;
  Hot Follow / Digital Anchor untouched.

## Owner decision needed

Recommend one (review §13):
- **proceed to Capability Trial Plan (Phase A/B, docs + offline)** — *recommended*;
- **revise review**;
- **hold**.

Recommendation: **proceed to Capability Trial Plan** — author the Tool Registry doc +
the offline benchmark trial plan so decision-grade speed/quality/cost/license data can
inform a future Phase D runtime-integration Gate Spec. Still docs-only + offline; no
runtime.
