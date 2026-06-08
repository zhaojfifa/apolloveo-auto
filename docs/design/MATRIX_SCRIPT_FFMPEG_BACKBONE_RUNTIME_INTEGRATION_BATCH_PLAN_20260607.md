# Matrix Script — ffmpeg Backbone Runtime Integration Batch Plan (2026-06-07)

Status: **PLANNING — docs-only. Not implementation authority. Not a Gate Spec. Authorizes
no code.** Defines a medium-sized runtime integration batch that connects the merged,
proven `ffmpeg_backbone` module to the Matrix Script fast-preview / minimal-result path.
Implementation requires a separate Owner S5→S6 (or Fast Lane) grant.

Source authority (consumed, not superseded):
- Gate Spec: `docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`
  (§12 signoff merged #238; PR-1 #239 / PR-2 #240 merged).
- Backbone module: `gateway/app/services/matrix_script/ffmpeg_backbone.py`.
- Bucket A: `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`.

When this plan conflicts with Bucket A, `ENGINEERING_RULES.md`, or
`CURRENT_ENGINEERING_FOCUS.md`, the underlying authority wins.

---

## 0. Why a batch (not another tiny PR)

PR-1 (proxy + compose + qc + fallback) and PR-2 (targeted-regenerate) landed the backbone
as a **standalone, well-tested module** — but **nothing consumes it yet**. The remaining
value is the *wiring*: making the Matrix Script fast-preview path actually render with the
backbone. That wiring is one cohesive, medium-sized batch (a real preview path), not a
sequence of 1-function PRs. This plan scopes that batch.

## 1. What existing Matrix Script service / result path should consume `ffmpeg_backbone`?

**`gateway/app/services/matrix_script/minimal_result_loop.py::run_minimal_result_loop`** —
the existing fast-preview / minimal-result entry that today renders a REAL local
`final.mp4` via `simple_scene_renderer` (solid-color `lavfi` scene cards → silent audio →
`assemble_final_video`) over a `MatrixScriptShotPlan`.

The batch routes this path through the **proven `ffmpeg_backbone`** so each shot's preview
is a **Ken-Burns proxy of its real still** (instead of a color card), composed by the
backbone, and **QC'd by ffprobe** — with targeted regenerate available for the operator
edit loop. The seam is well-bounded: `run_minimal_result_loop` already isolates rendering
behind `simple_scene_renderer` calls; the batch swaps/extends that renderer seam.

Adjacent consumers that ride the same path (read-only awareness, not all touched):
`minimal_result_service.py`, `minimal_result_command.py`, `real_trial_orchestrator.py`.

## 2. What input object should be used?

Primary input: the existing **`MatrixScriptShotPlan`** (`shot_plan.py`,
`shot_plan_builder.build_shot_plan`) whose `MatrixScriptShotSpec` shots carry
`shot_id` + per-shot image / `generation_mode = image_to_video` + duration. Mapping into
the backbone:

- **shot plan** → ordered `ffmpeg_backbone.ShotSpec(shot_id, image_path, duration, zoom)`.
- **still image assets** → each shot's bound still (the canonical input for the Ken-Burns
  proxy); for the tomato-beach case these are the `assets/matrix_script_assets/...` stills.
- **uploaded material assignments** → when a shot has an operator upload
  (`shot_material_storage` `msmaterial://`, `bytes_resolvable=true`), the resolved local
  bytes are the proxy input (reusing the #211/#212 resolution, **read-only** — no change to
  storage or the consumption contract).
- **existing task artifact paths** → the per-shot proxy clips from a prior run feed
  `targeted_regenerate`'s `existing_clips` so unchanged shots are reused.

No new input contract is invented; the batch consumes the existing shot plan + material
resolution and adapts it to `ShotSpec`.

## 3. What output should be produced?

- **proxy scene clips** — one Ken-Burns proxy mp4 per shot (1080×1920 h264), written to the
  existing minimal-result `local_workspace` output dir (caller-supplied, as today).
- **composed preview `final.mp4`** — backbone `compose_concat` cut (delivery-spec), the
  fast-preview result the path already promises.
- **manifest** — the existing minimal-result manifest (`scene_manifest` / `build_manifest_dict`),
  extended with backbone evidence via the **operator-safe** `BackboneManifest.operator_summary()`
  / `TargetedRegenResult.operator_summary()` (no `local_path` / raw probe JSON / vendor).
- **QC evidence** — `ffprobe` QC verdict per clip + composed cut (`qc_probe`), surfaced as
  operator-safe fields (resolution / fps / duration / pass-fail); raw probe JSON stays
  diagnostics-only.
- **operator-safe summary** — the L4 projection consumed by the existing fast-preview
  surface, honest about proxy/non-generative tier; `official_publish_ready` stays `False`.

## 4. Which existing artifact / delivery truth must remain unchanged?

- The minimal-result **manifest shape** + its `_assert_no_forbidden_tokens` guard — the
  backbone evidence is *added* through operator-safe projections, not by mutating the
  manifest contract.
- The **delivery candidate semantics** — delivery follows the confirmed main only; the
  preview `final.mp4` is a *candidate*, never auto-promoted.
- **`official_publish_ready = false`** everywhere — unchanged.
- The **four-layer boundary** — backbone outputs are L2 artifact facts behind the existing
  boundary; no L1/L3/L4 truth producer is redefined; no second source of truth.
- The **#211/#212 material resolution + consumption honesty** — reused read-only; no
  change to `shot_material_storage` or `material_bytes_consumed` semantics.
- **`simple_scene_renderer`** stays available (color-card fallback when a shot has no
  usable still) — the batch adds the backbone path, it does not delete the existing one.
- **Hot Follow / Digital Anchor / `artifact_storage.py` / schemas / contracts / routes /
  templates** — untouched.

## 5. Which files would likely be touched?

| File | Change | Note |
|------|--------|------|
| `gateway/app/services/matrix_script/minimal_result_loop.py` | wire the backbone renderer seam (shot still → `ShotSpec` → proxy/compose/qc) + operator-safe evidence | the integration core; keep the `simple_scene_renderer` fallback |
| `gateway/app/services/matrix_script/ffmpeg_backbone.py` | (only if a thin adapter helper `shot_plan → ShotSpec` is wanted) | optional, additive; may instead live in the loop |
| `gateway/app/services/tests/test_matrix_script_minimal_result_loop.py` | extend for the backbone path + reuse + QC evidence | |
| `gateway/app/services/tests/test_matrix_script_ffmpeg_backbone.py` | extend if an adapter helper is added | |
| `docs/execution/owner_summaries/...` + an execution note under `docs/execution/` | batch owner summary + execution evidence | docs |

Explicitly **not** touched: `simple_scene_renderer.py` behavior (kept as fallback),
`shot_material_storage.py`, `artifact_storage.py`, routers, templates, schemas, contracts.

## 6. Which tests are required?

- shot plan with stills → backbone proxy clips produced (per-shot), composed `final.mp4`
  is delivery-spec (ffprobe-verified) — real-ffmpeg integration (skips when ffmpeg absent).
- uploaded material assignment → that shot's proxy uses the resolved upload bytes
  (read-only; no consumption-contract change).
- targeted regenerate across a second run → only changed shots re-rendered, others reused.
- manifest + operator-safe summary carry backbone QC evidence with **no leakage**
  (`local_path` / raw JSON / provider / vendor absent) and `official_publish_ready=false`.
- color-card **fallback** path still works when a shot lacks a usable still.
- `_assert_no_forbidden_tokens` still passes on the extended manifest.
- adjacent minimal-result / orchestrator tests stay green (behavior preservation).

## 7. Which parts remain out of scope?

- **Generative `image_to_video` provider** (Kling/Runway/Veo) — pending the credentialed
  trial + a future gate; the batch uses the **proxy** only.
- **`subtitle_style` runtime, `voiceover`, `bgm_select`, `broll_retrieval`,
  `avatar_segment`, `face_swap`** — out of scope.
- **Provider / credential / network / secret / Akool** — none.
- **Schema / contract change** — none, unless a specific need is **explicitly marked as a
  future gated amendment** and approved separately (this batch assumes none).
- **Routes / new endpoints / UI templates / vendor exposure** — none.
- **Delivery-truth / `official_publish_ready` change** — none.
- **Slot Workflow v2 runtime** — none (UI convergence is its own gate).
- **PR-3 of the backbone gate spec slicing** — superseded in spirit (compose/qc/fallback
  already landed); this batch is the integration step, gated separately.

## 8. Boundary

- **docs-only** — this plan adds one design doc; no code.
- runtime implemented in this step: **none**.
- provider integration / credentialed calls / generative adapter: **none**.
- subtitle/voiceover/bgm/broll/avatar runtime: **none**.
- schemas/contracts: **no change** (any future need is a separately-gated amendment).
- vendor UI: **none** · delivery truth: **unchanged** · `official_publish_ready`:
  **unchanged (False)** · Slot Workflow v2 runtime: **none**.
- Does **not** authorize the batch; implementation requires a separate Owner S5→S6 grant.

## 9. Owner Decision Needed

Recommend one:
- **approve S5→S6 for the integration batch** — implement the `minimal_result_loop` ⇆
  `ffmpeg_backbone` wiring per §1–§7 (one medium batch, tests included, no provider, no
  delivery-truth change);
- **revise the plan**;
- **hold**.

**Recommendation:** **approve S5→S6 for the integration batch** — it converts the proven
backbone from a standalone module into a real operator-facing fast-preview improvement,
at the well-bounded `minimal_result_loop` seam, with zero provider/secret/contract risk.

---

*This is a docs-only integration plan. It wires nothing, integrates no provider, changes
no contract/schema/route/UI or delivery truth, and authorizes no code. Implementation is a
separate, Owner-gated batch.*
