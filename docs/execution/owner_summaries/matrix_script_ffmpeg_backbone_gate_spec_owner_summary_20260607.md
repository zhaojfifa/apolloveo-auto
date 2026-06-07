# Owner Summary — Matrix Script ffmpeg Backbone Runtime Gate Spec (2026-06-07)

Docs-only. One-page summary for the Owner. Not authority; the Gate Spec governs.

Gate Spec: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`

## What this is

The **first runtime-integration gate spec**, scoping the offline-proven **ffmpeg
compose/qc + Ken-Burns image_to_video proxy backbone**. It freezes scope into enforceable
rules but **implements nothing** — the implementation gate is **CLOSED until §12 signoff
merges**.

## Scope it freezes

- Ken-Burns proxy clip generation from stills; ffmpeg concat compose; ffprobe QC;
  deterministic 1080×1920 h264 preview outputs; a Fast Preview Path (per-shot ~1s,
  compose ~0.1s, targeted regenerate); artifact + manifest/evidence projection
  expectations within the existing four-layer boundary; honest fallback-tier semantics.
- **No credential dependency. No vendor UI. No secret. No network.**

## What it explicitly is NOT (binding non-goals)

- Ken-Burns proxy is **not generative animation** — a fallback/preview backbone, not the
  final quality fix.
- Generative `image_to_video` provider stays **pending a credentialed offline trial** +
  a separate future gate.
- `subtitle_style` is **blocked** unless a freetype/libass build or PNG-overlay adapter
  is separately proven; `voiceover` / `bgm` / `broll` / `avatar` are **out of scope**.
- No provider routing decision; no Slot Workflow v2 PR-1; no §13 signoff; no
  `official_publish_ready=true`.

## Acceptance / slicing

- Acceptance rows **FB-1..FB-12** (deterministic proxy, no-credential, honest copy,
  compose, targeted regenerate, QC verdict + fallback, no-leak, publish-ready-false,
  no-contract-without-approval, forbidden-path clean, tests green).
- Slices **PR-1** (proxy) → **PR-2** (compose + targeted regenerate) → **PR-3** (QC +
  static-still fallback) → **PR-4** (closeout). Allowed path: a new
  `gateway/app/services/matrix_script/ffmpeg_backbone.py` + Matrix Script tests only.
- `<fill>` §12 signoff; gate opens for PR-1 only after Architect + Reviewer merge; each
  later slice is its own Owner-gated S5→S6.

## Boundary

docs-only · no runtime · no `gateway/**`/services/templates/tests change · no provider
adapter code · no schemas/contracts (unless separately approved) · no secrets · no
vendor in UI · no four-layer state change · no Slot Workflow v2 PR-1 · no provider
routing decision · no §13 signoff filled.

## Owner decision needed

- **Approve merge** of this Gate Spec (docs-only), then a **separate** §12 signoff PR
  would open PR-1; or
- **Request revision**; or
- **Hold**.

Approving the merge does **not** authorize implementation — filling §12 (a separate
docs-only signoff PR) is the gate-opening step, and even then only PR-1 opens.
