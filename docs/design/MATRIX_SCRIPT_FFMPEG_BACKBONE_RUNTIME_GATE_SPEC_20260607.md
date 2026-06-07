# Matrix Script — ffmpeg Backbone Runtime Gate Spec (2026-06-07)

Status: **ACCEPTED-PENDING-SIGNOFF GATE SPEC — docs-only. The FIRST runtime-integration
gate spec for the proven ffmpeg backbone. Implements nothing itself. The implementation
gate is CLOSED until §12 signoff merges to `main`.**

This gate spec freezes the **first runtime integration scope** for the
offline-proven **ffmpeg compose/qc + Ken-Burns image_to_video proxy backbone**. It is a
*runtime* gate spec (its future PRs would touch Matrix-Script runtime services), but it
**authorizes no code** — code begins only after §12 signoff merges, one slice at a time,
each slice its own Owner-gated S5→S6 (L3) decision.

Source authority (consumed, not superseded):
- Offline trial evidence: `docs/execution/MATRIX_SCRIPT_CAPABILITY_OFFLINE_TRIAL_REPORT_20260607.md`
- Capability review + trial plan: `docs/reviews/MATRIX_SCRIPT_VIDEO_CAPABILITY_UPGRADE_REVIEW_20260607.md`,
  `docs/design/MATRIX_SCRIPT_CAPABILITY_TRIAL_PLAN_20260607.md`
- Bucket A: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`
- Process: `docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md`, `…AUTOPILOT_EXECUTION_POLICY_20260607.md`

When this gate spec conflicts with Bucket A, `ENGINEERING_RULES.md`, or
`CURRENT_ENGINEERING_FOCUS.md`, the underlying authority wins.

---

## 1. Source Evidence

The offline trial (`…OFFLINE_TRIAL_REPORT_20260607.md`) measured, on the real
tomato-beach stills, with local secret-free ffmpeg 8.1.1 + ffprobe:

- **image_to_video (Ken-Burns proxy):** ~0.9–1.0s per 3–4s 1080×1920 h264 clip, $0,
  valid output — **a motion proxy, not generative animation**.
- **compose (ffmpeg concat):** delivery-spec **10.0s** 1080×1920 h264 cut in **0.09s**,
  $0, deterministic; **strongest result**.
- **qc (ffprobe):** verified resolution / duration / codec / fps / bitrate / frame count.
- **subtitle_style:** **blocked** in the tested build (no drawtext/libfreetype, no libass).
- generative providers / voiceover / broll / avatar / bgm: **not run** (no credentials).

This gate spec scopes exactly the proven, free, deterministic, secret-free part.

## 2. Problem / Scope

Matrix Script today has one real production lever (visual material in/out) and a
slow/single-path generation. The proven backbone can immediately add a **fast,
deterministic, zero-cost preview + assembly + QC path** without any provider or secret.
Scope of this first integration:

- **Ken-Burns proxy clip generation** from a still image (pan/zoom → short h264 clip).
- **ffmpeg concat compose** of per-shot clips → a single delivery-spec cut.
- **ffprobe QC** producing a structured quality/spec report.
- **Deterministic 1080×1920 h264 preview outputs** (fixed encode params).
- A **Fast Preview Path** (cheap, instant iteration) distinct from any future final/
  generative render.
- **Artifact output + manifest/evidence projection expectations** (see §5), within the
  existing four-layer boundary (no four-layer change).
- **Fallback-tier semantics** (see §8): the proxy is the fallback below a future
  generative route.
- **No credential dependency. No vendor UI exposure.**

## 3. First Integration Boundary

The implementation, when later authorized, may touch only:

- a new Matrix-Script-scoped backbone service module
  (e.g. `gateway/app/services/matrix_script/ffmpeg_backbone.py`) that shells out to the
  already-installed local `ffmpeg`/`ffprobe`;
- the Matrix Script test suites under `gateway/app/services/tests/`.

It is a **local, deterministic, secret-free** integration: it invokes the system
`ffmpeg`/`ffprobe` on operator-supplied stills/clips, writes outputs to the existing
Matrix-Script `local_workspace` artifact area, and projects results through existing
L2 artifact-fact / L3 attempt / L4 operator-summary surfaces. It introduces **no
provider, no network egress, no secret, no new endpoint behavior, no vendor field.**

## 4. Explicit Non-Goals

Stated explicitly (binding):

- **Ken-Burns proxy is NOT generative animation.** It pans/zooms a still; it does not
  synthesize motion or new content.
- **It is a fallback / preview backbone, not the final quality fix.** It raises speed
  and assembly/QC determinism, not generative output quality.
- **Generative `image_to_video` provider remains PENDING a credentialed offline trial**
  (`…CREDENTIALED_PROVIDER_TRIAL_PLAN_20260607.md`) and a separate future gate spec; it
  is **not** in this scope.
- **`subtitle_style` is BLOCKED** unless a suitable freetype/libass-enabled ffmpeg build
  **or** a pre-rendered-PNG → `overlay` adapter is separately proven and gated. Not in
  this scope.
- **`voiceover` / `bgm_select` / `broll_retrieval` / `avatar_segment` are OUT OF SCOPE.**
- No provider routing decision; no `official_publish_ready=true`; no Slot Workflow v2
  PR-1; no §13 (Slot Workflow v2) signoff touched.

## 5. Artifact Contract Expectations

The backbone produces three artifact kinds, represented **within existing structures**;
any *new closed field / schema / contract* requires **separate contract approval** before
the PR that needs it (per the Owner's "no schemas/contracts changes unless separately
approved"). Expectations:

- **proxy clip artifact** — per-shot h264 mp4, 1080×1920, 30fps, fixed duration window;
  recorded as an L2 artifact fact in the Matrix-Script `local_workspace` area with
  `bytes_resolvable=true` semantics consistent with the #211/#212 material path.
- **composed cut artifact** — single h264 mp4 (delivery-spec), the concat of confirmed
  per-shot clips; recorded as an L2 artifact fact.
- **qc report** — structured, operator-safe fields only (width/height/fps/duration/
  codec/bitrate/frame-count/pass-fail per §7); projected to L4 operator summary; raw
  ffprobe JSON belongs to J-zone diagnostics, never primary copy.
- **No vendor / model / provider / engine / credential** field anywhere; **no
  `local_path`, raw manifest, or provider URL** in operator-facing copy. `final.mp4`
  remains a preview candidate; `official_publish_ready` stays `false`.

If representing any of the above requires a new closed field, the PR is **blocked** until
a separate contract amendment is approved — the gate spec does not pre-authorize it.

## 6. Fast Preview Path

- The backbone is the **Fast Preview Path**: regenerate a single shot's proxy clip in
  ~1s and re-compose in ~0.1s, so the operator iterates per-shot without a long render.
- **Targeted regenerate:** re-run only the changed shot's proxy (per the Slot Workflow
  v2 Assignment set), reuse unchanged shot clips, then re-compose.
- The Fast Preview Path is explicitly distinct from any future **final/generative
  render** (out of scope here); it never claims final quality and never sets
  `official_publish_ready=true`.
- Determinism: fixed encode params (1080×1920, 30fps, h264, yuv420p, fixed CRF/preset)
  so the same input yields the same output — testable.

## 7. QC Requirements

The `qc` step (ffprobe-based) MUST verify, per clip and per composed cut:

- **resolution** = 1080×1920 (reject otherwise).
- **codec** = h264, pixel format yuv420p.
- **fps** = 30.
- **duration fit** — within the shot/cut target window (exact-match expected for proxy/
  concat; tolerance documented).
- **frame count** consistent with duration × fps.
- **bitrate / size** present and within sane bounds.
- **pass/fail verdict** per artifact, surfaced as operator-safe L4 summary; a fail routes
  the shot back to regenerate or to the §8 fallback. `official_publish_ready` stays
  `false` regardless of QC pass (delivery-readiness is gated elsewhere).

## 8. Fallback Semantics

- The Ken-Burns proxy is the **fallback tier** for `image_to_video`: when no generative
  route is available/authorized (the current state), the proxy provides motion; below
  the proxy is a **static still** (no motion).
- A QC failure on a proxy clip falls back to the static still for that shot; compose
  still proceeds with the remaining shots.
- The fallback is **honest**: operator copy states it is a preview/proxy, never claims
  generative or final quality. When a future generative route lands, the proxy becomes
  the explicit fallback beneath it (no behavior removed).

## 9. Forbidden Paths

Any appearance in a slice's `git diff --name-only` is an automatic fail:

```
gateway/app/services/hot_follow*     gateway/app/services/digital_anchor/
gateway/app/services/asset/          **/artifact_storage.py
schemas/                             docs/contracts/
routers/ (no route behavior change)  CURRENT_ENGINEERING_FOCUS.md
gateway/app/templates/**             (no UI change in this backbone scope)
any *_GATE_SPEC_*.md                 any Slot Workflow v2 surface change
```

Allowed implementation paths only: a new
`gateway/app/services/matrix_script/ffmpeg_backbone.py` (or similarly-scoped
matrix_script service module) and Matrix Script test suites under
`gateway/app/services/tests/`. No secret file, no env-key requirement, no network.

## 10. Acceptance Rows

The future Closeout records PASS/FAIL against every row:

| # | Acceptance criterion | Slice |
|---|----------------------|-------|
| FB-1 | Ken-Burns proxy generates a valid h264 1080×1920 30fps clip from a still, deterministically (same input → same output). | PR-1 |
| FB-2 | Proxy generation requires **no credential, no network, no secret**; uses only local ffmpeg. | PR-1 |
| FB-3 | Operator copy states the proxy is a **preview/proxy, not generative**, never claims final quality. | PR-1 |
| FB-4 | ffmpeg concat composes confirmed per-shot clips into a single delivery-spec h264 cut; duration = sum of shot durations. | PR-2 |
| FB-5 | Targeted regenerate re-runs only the changed shot and reuses unchanged clips before compose. | PR-2 |
| FB-6 | ffprobe QC verifies resolution/codec/fps/duration/frame-count/bitrate and emits a pass/fail verdict (operator-safe fields only). | PR-3 |
| FB-7 | QC failure falls back to static still for that shot; compose still proceeds. | PR-3 |
| FB-8 | No leakage: no `local_path` / raw manifest / provider URL / vendor / model / credential in operator-facing copy (raw ffprobe JSON → J-zone only). | every PR |
| FB-9 | `official_publish_ready` remains `false`; the backbone output is a preview candidate only. | every PR |
| FB-10 | No new closed field / schema / contract introduced without a separate approved amendment (PR blocked otherwise). | every PR |
| FB-11 | No `gateway/**` template/UI change, no provider, no `schemas/`/`docs/contracts/`, no Hot Follow / Digital Anchor / asset / artifact_storage touch (forbidden-path scan clean per §9). | every PR |
| FB-12 | Matrix Script suite stays green; new dedicated tests cover proxy/compose/qc happy + failure paths. | every PR |

## 11. PR Slicing

Small PRs, gate-spec-first; each opens only after its predecessor merges + reviews; each
slice's S5→S6 is its own Owner-gated (L3) decision. No bundling.

| PR | Scope | Touches | Risk |
|----|-------|---------|------|
| **PR-1** | Ken-Burns proxy generator (still → deterministic h264 clip) + honest preview/proxy semantics. | new `ffmpeg_backbone.py` + tests | Medium |
| **PR-2** | ffmpeg concat compose + targeted-regenerate (reuse unchanged clips). | `ffmpeg_backbone.py` + tests | Medium |
| **PR-3** | ffprobe QC (verdict + operator-safe projection) + static-still fallback. | `ffmpeg_backbone.py` + tests | Medium |
| **PR-4** | Closeout docs — acceptance audit (§10), no-leak / forbidden-path audit, signoff. | docs only | Docs-only |

> Reviewer-fail / new-defect corrections are separate narrow follow-up PRs, never folded
> into a merged slice. Any UI surfacing of the backbone (Slot Workflow v2) is a
> **separate** gate (the Slot Workflow v2 Gate Spec), not opened by this one.

## 12. Owner Signoff Block (gate opens on merge)

| Role | Name | Date | Verdict |
|------|------|------|---------|
| Architect | Owner-authorized (Harness X) | 2026-06-07 | APPROVED — gate-opening for PR-1 only (subject to a separate S5→S6 go) |
| Reviewer | Harness X Code Review (S6→S7) | 2026-06-07 | READY TO MERGE (gate spec) |
| Operations Coordinator | `<fill>` | `<fill>` | binds Closeout (PR-4) |
| Product Manager | `<fill>` | `<fill>` | binds Closeout (PR-4) |

Architect + Reviewer signoff merged to `main` **opens the implementation gate for PR-1
only**. Coordinator + PM bind the Closeout audit (§10, PR-4). This spec authorizes no
code; the first allowed action after signoff is PR-1 per §11. Opening each subsequent
slice is its own Owner-gated S5→S6 (L3) decision.

### §12 signoff reconciliation (2026-06-07, docs-only)

The Owner authorized this gate-opening signoff PR (Architect + Reviewer rows filled
above). Binding facts of record:

- The **Owner authorized the gate-opening §12 signoff** for the ffmpeg backbone gate —
  the Architect + Reviewer rows record that Harness X authorization, mirroring the Guided
  Operator Workflow §10 precedent committed in #221.
- **Per the Owner's explicit stricter posture, merging this signoff does NOT auto-start
  PR-1.** Even with the gate "open," **ffmpeg backbone PR-1 may begin only after a
  separate, explicit Owner S5→S6 (L3) approval.** This signoff prepares the gate-opening
  paperwork; it does not itself start runtime.
- **Coordinator + Product Manager rows remain `<fill>`** because they bind the future
  Closeout (PR-4), not gate opening.
- This reconciliation is **docs-only**: it changes no runtime, no `gateway/**`, no
  services / templates / tests, no provider adapter, no generative provider integration,
  no credentialed call, no schemas / contracts, no vendor UI, and authorizes no
  implementation slice. The first allowed runtime action remains PR-1, gated on a
  separate Owner S5→S6 go.

---

## Authority Boundary

- Docs-only; authorizes no code; opens no wave; supersedes no authority.
- Does **not** authorize runtime implementation, provider integration, generative
  `image_to_video` adapter, Slot Workflow v2 PR-1, or any §13 (Slot Workflow v2) signoff.
- Does **not** change `gateway/**`, services, templates, tests, `schemas/**`,
  `docs/contracts/**`, providers, Akool, Hot Follow, Digital Anchor, or the four-layer
  state model; no secrets; no vendor in UI; no provider routing decision.
- Code begins only after §12 signoff merges, one slice at a time, under the standard
  discipline.

*This is an accepted-pending-signoff runtime gate spec for the proven ffmpeg backbone.
It implements nothing. The generative-quality lever stays pending a credentialed trial +
its own future gate.*
