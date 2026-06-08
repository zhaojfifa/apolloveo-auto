# Matrix Script Operator-Visible Backbone Integration Report

Status: **Fast Lane S5→S8 executed. Implemented + tested + operator-smoked. NOT merged
(stop before merge).** Owner-approved narrow scope expansion (Decision A): connect the
proven ffmpeg backbone + ffprobe QC into the operator-visible Path A.

## 1. PR / Tag
- rollback tag: `matrix-script-before-capability-integration-20260607` → `32338539` (pushed)
- PR: none opened (stop-before-merge; no PR without Owner approval)
- branch: `feat/matrix-script-production-capability-integration-20260607`
- commit: backbone-integration commit on the branch (runtime + tests + this report); not pushed, not merged

## 2. Reading / Rule Declaration
- root rules: `CLAUDE.md`, `README.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`,
  `CURRENT_ENGINEERING_FOCUS.md`.
- indexes: `docs/README.md`, `docs/ENGINEERING_INDEX.md`,
  `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`.
- Gate Specs: ffmpeg backbone runtime gate spec
  (`docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`); Operator
  Value Gap Review (`docs/reviews/MATRIX_SCRIPT_OPERATOR_VALUE_GAP_REVIEW_20260607.md`);
  Material-to-V2 Visible Closure Gate Spec.
- Owner summaries: the Production Capability Integration pilot
  (`docs/execution/MATRIX_SCRIPT_PRODUCTION_CAPABILITY_INTEGRATION_PILOT_20260607.md`) +
  its owner summary; #239/#240/#242/#243/#244.

## 3. Scope Expansion
- approved scope: Owner Decision **A** — render the operator-visible tomato video through the
  ffmpeg backbone + produce ffprobe QC evidence on the operator final.mp4.
- files changed (runtime): **`gateway/app/services/matrix_script/tomato_real_result_orchestrator.py`** only
  (+ its test `test_matrix_script_tomato_real_result.py`). `auto_preview_generation.py` needed
  **no change** (it calls the orchestrator, so the backbone engages automatically for both the
  initial preview and V2 regeneration). `ffmpeg_backbone.py` needed **no change** (all
  primitives already present).
- why `tomato_real_result_orchestrator` was required: it is the operator-visible generator
  (New Task → auto preview → Workbench `<video>`). The backbone (#239–#244) previously lived
  only in the internal `minimal_result_loop` path; the only way to put it on the operator
  video is here. This is exactly the file the Owner authorized.
- why this is not provider integration: the backbone is **local ffmpeg only** — a
  deterministic Ken-Burns proxy + ffprobe QC. No provider call, no credential, no network, no
  vendor/model/engine, no Akool/Kling/Runway/Veo/Azure. `official_publish_ready` stays false.

## 4. Runtime Integration
- operator path: `auto_preview_generation.trigger_*` → `build_matrix_script_tomato_preview_payload`
  / `build_matrix_script_regeneration_payload` → `run_tomato_real_result` (unchanged callers).
- ffmpeg backbone usage: each shot now renders via the new `_render_shot_via_backbone` →
  `backbone.generate_with_fallback` (deterministic **1080×1920 / 30fps** Ken-Burns proxy;
  static-still fallback on render failure). Replaces the prior 720×1280 `render_shot_clip`
  motion engine.
- scene clips: 5/5 rendered through the backbone (`render_mode=ffmpeg_backbone_proxy`, or
  `…_static_still` on fallback), recorded per-shot in the manifest.
- final.mp4: composed via the existing `assemble_final_video`; **1080×1920 h264 30fps**,
  ~5.3 MB, 20.0s on the tomato pack.
- ffprobe QC: `backbone.qc_probe` on the composed final → `qc` verdict in the manifest +
  operator-safe scalars (`qc_passed` / `qc_resolution`) on the result + payload. QC is
  best-effort evidence (try/except → `qc=None`), never a publish gate.
- material trace: unchanged + preserved — `material_overrides` (#212) feed the backbone via
  `_resolve_shot_render_source`; consumed shots reported in `consumed_material_shot_ids`
  (verified: an uploaded/replacement image is consumed through the backbone).
- V1/V2 difference: unchanged — V1 staged candidate vs V2 version path preserved; the
  backbone renders both; `operator_workbench_view` projection untouched.
- captions: **preserved (burned-in)** — the existing Pillow caption PNG is overlaid on the
  backbone clip at 1080×1920 (this build has no drawtext/libass). When no CJK font exists the
  motion clip is promoted and the .srt sidecar remains (honest fallback, unchanged).
- audio fallback: **preserved** — Azure TTS only if env present, else honest silent fallback.
- manifest: additive operator-safe keys — `scene_engine`, `per_shot_render`, `qc`, `backbone`;
  legacy keys unchanged; no `local_path`/provider/publish leak.

## 5. Browser / Operator Smoke
- URL: `GET /tasks/{task_id}` (Workbench `<video data-role="ms-main-video-result-video">`) +
  `GET /api/matrix-script/{task_id}/preview-version/{V}/final.mp4` (existing serving route,
  unchanged).
- task id: `bb-smoke-001` (service smoke) + `bb-override` (material-override smoke).
- final.mp4: produced, **5.3 MB**, exists, non-empty.
- playable: yes — `ffprobe` → `h264, 1080, 1920, 30/1`.
- QC visible: yes — manifest `qc.passed=true` (resolution/codec/fps/duration_fit all pass) +
  payload `backbone_qc_passed=true`, `backbone_qc_resolution=1080x1920`.
- material trace visible: yes — `consumed_material_shot_ids=('shot04',)` on the override run;
  operator view consumed-materials projection unchanged.
- V1/V2 visible: yes — version projection unchanged (both rendered via backbone).
- delivery candidate: `delivery_candidate=true` (follows confirmed main only; unchanged).
- official_publish_ready: **false**.
- leakage check: payload + manifest forbidden-token guards pass; no `local_path`/provider/
  vendor/publish token; `_assert_clean`/delivery-view guards unchanged.

## 6. Code Review
- verdict: **PASS** (self-review).
- scope compliance: only the Owner-authorized orchestrator file + its test changed.
- allowed files: `tomato_real_result_orchestrator.py` ✅ + Matrix Script test ✅ + docs ✅.
- forbidden paths: none — `git diff --name-only` shows no routes / schemas / `docs/contracts/`
  / providers / `auto_preview_generation.py` / `ffmpeg_backbone.py`.
- provider / credential check: none — local ffmpeg only; no network/credential/secret.
- schema / contract check: no change (manifest/payload additions are operator-safe, additive,
  not a published schema/contract).
- route check: no change (existing preview-serving routes reused unchanged).
- delivery truth check: unchanged (`staged_record_to_delivery_block`, provider="none").
- official_publish_ready check: stays false everywhere (orchestrator, manifest, payload, QC).
- test adequacy: updated the resolution assertion; added 2 dedicated backbone tests (manifest
  QC + per-shot render evidence; replacement-material consumed through the backbone) +
  payload QC assertions.

## 7. Operator Trial
- verdict: **PASS WITH ISSUES BUT PLAYABLE**.
- result quality: **improved** — operator video is now **1080×1920** (was 720×1280) with a
  passing ffprobe QC verdict; captions still burned-in.
- operator-visible improvement: higher-resolution deterministic video on the real Workbench
  path + a QC verdict + per-shot render-mode evidence in the manifest — the backbone value is
  now ON the operator path, not internal-only.
- acceptable issues: Ken-Burns proxy is non-generative (a motion proxy, not a generated
  scene); shot04/shot05 remain semantic-reuse in the default plan (3/5 real_visual); the
  backbone crop is centered (the per-shot focus-framing of the old renderer is not applied).
- blockers: none — final.mp4 exists, plays, page shows it, publish stays false, delivery
  truth unchanged, no leakage.

## 8. Validation
- focused tests: `test_matrix_script_tomato_real_result.py` → **13 passed** (incl. 2 new
  backbone tests + updated resolution/QC assertions); 4 route tests fail at import on the
  pre-existing PEP-604 env limit (below).
- adjacent Matrix Script tests: backbone (35) + minimal_result loop/service/staging +
  operator workbench flow alignment = **93 passed**; workbench blocks A–F + minimal-result
  workbench block/action = **160 passed** (1 route-import failure = same PEP-604 limit).
- py_compile: `tomato_real_result_orchestrator.py` → OK.
- diff check: `git diff --check` clean.
- forbidden-path scan: clean (no routes/schemas/contracts/providers).
- no-secret scan: clean (only a test's forbidden-token assertion list mentions "akool").
- worktree: branch as above; runtime change limited to the orchestrator + its test.
- **Pre-existing env limit (not a regression):** route/config-importing tests fail at
  `gateway/app/config.py:43` (`str | None` needs Python 3.10+; local is 3.9.6) — verified
  identical on the clean stash before my change; documented in `ENGINEERING_RULES.md` §10;
  CI runs Python 3.10+.

## 9. Boundary
- runtime changed: **Yes — `tomato_real_result_orchestrator.py` only**
- provider integration: **No**
- credentialed calls: **No**
- generative adapter: **No**
- schemas/contracts: **No**
- routes: **No**
- vendor UI: **No**
- delivery truth: **unchanged**
- official_publish_ready: **unchanged (False)**
- Slot Workflow v2: **not started**

## 10. Verdict

**PASS WITH ISSUES BUT PLAYABLE.** The ffmpeg backbone + ffprobe QC are now on the
operator-visible Path A: the Workbench video is a playable 1080×1920 h264 cut rendered through
the backbone, with a passing QC verdict, burned-in captions, honest silent-audio fallback,
material trace + V1/V2 preserved, delivery truth unchanged, and `official_publish_ready=false`.

## 给 Claude 的指令
- **current Owner decision:** Decision A approved — backbone integrated into the operator
  video; Fast Lane S5→S8; stop before merge; no follow-up PR without approval.
- **allowed next actions:** on Owner S8→S9 → merge + sync main + post-merge validation +
  merge report. Any further capability (generative provider, subtitle/voice/BGM, Slot v2)
  needs its own gate + Owner grant.
- **forbidden actions:** no merge without Owner S8→S9; no provider/credential/Akool/Kling/
  Runway/Veo/Azure runtime; no generative adapter; no vendor UI; no schema/contracts; no
  route change; no delivery-truth change; no `official_publish_ready=true`; no fake
  subtitle/voice/BGM controls; no Slot v2 runtime; no unrelated refactor; no follow-up PR
  without approval.
- **required outputs (delivered):** rollback tag; the runtime integration; tests; this report;
  the Owner Summary.
- **validation checks:** focused + adjacent tests, py_compile, diff-check, forbidden-path
  scan, no-secret scan, behavior preservation, operator smoke — all clean (pre-existing
  PEP-604 env skips aside).
- **stop point:** stopped before merge; no PR opened; no push.
- **Owner Decision Needed:** below.

## 11. Owner Decision Needed

The operator video is playable and safe with the backbone + QC integrated.

**APPROVE S8→S9 merge** for the Matrix Script Operator-Visible Backbone Integration? (or
request revision / hold). Stop before merge; no follow-up PR will be opened without approval.
