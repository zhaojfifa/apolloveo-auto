# Matrix Script Phase 3 — PR-A Tomato Real Result Path (Execution Note + Validation Report)

Date: 2026-06-01
Branch: `phase3/pr-a-matrix-script-tomato-real-result`
Base: `origin/main` @ `3ecff9e0d61ffc677bd22015dc143c2db5c01540`
Status: First operator-usable Matrix Script result. Controlled real-asset path for the fixed case
《海边与圣女果的盛夏约定》. `official_publish_ready=false`. Awaiting human operator validation.

This implements PR-A from the Real Result Baseline (`docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md`)
and follows the launch instruction's order: read & align → confirm four-layer → align mock/surface →
define controlled path → run the tomato case → produce one result record → hand to human validation.

---

## 1. Branch / Commit / PR

- branch: `phase3/pr-a-matrix-script-tomato-real-result`
- commit: see PR head (this note lands in the same PR)
- PR: PR-A (see GitHub)

## 2. Reading Declaration

- root indexes: `CLAUDE.md`, `README.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`
- docs indexes: `docs/README.md`, `docs/ENGINEERING_INDEX.md`, `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- authority files: `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md`, `docs/product/matrix_script_product_flow_v1.md`, `docs/design/matrix_script_workbench_product_flow_reset_v1.md`, `docs/execution/MATRIX_SCRIPT_PHASE3_P0_R2_PREVIEW_STAGING.md`, `docs/execution/MATRIX_SCRIPT_PHASE3_PR17R_REAL_OPERATOR_TRIAL.md`, `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`
- missing authority: none (the baseline + product-flow + reset + P0R2 + PR-17R set was sufficient; no invented authority)

## 3. Mock / UI Alignment

- Workbench fields (new "运营可用预览" action, rendered live from the route response):
  `operator_usable` / `technical_preview` / `visual_semantic_match` / `shot_match_count` (`/ shot_count`) /
  `real_visual_count` / `delivery_candidate` / `official_publish_ready` / `blocked_reason` / 打开视频 (`preview_url`).
- Delivery fields (staged-candidate block, shown when present): the same acceptance fields plus the existing
  `storage_scope=artifact_staged` / `delivery_candidate` / `official_publish_ready=false` / `打开视频（暂存预览）`.
- four-layer mapping:
  - L1 step status — asset ingestion → shot assembly → audio → subtitle → final assembly → artifact staging (recorded on the manifest `pipeline_steps`).
  - L2 artifact facts — shot clips / final.mp4 / subtitles / audio / manifest exist; `preview_url` resolves (real files).
  - L3 readiness — the operator acceptance gate (`tomato_acceptance_gate.py`): `technical_preview` / `operator_usable` / `visual_semantic_match` / `shot_match_count` / `real_visual_count` / `delivery_candidate` / `blocked_reason`.
  - L4 UI — Workbench + Delivery render only these derived facts; a fallback-only result can never become a delivery candidate.
- what was added: 4 new services + 1 new route + 2 minimal surface additions + 1 main.py registration (+2 lines).
- what was NOT changed: no schema / packet / contract / closed-enum change; `artifact_storage.py` untouched; `simple_scene_renderer.py` color-card path untouched (kept as honest fallback); no Hot Follow / Digital Anchor touch; `minimal_result_loop.py` / `real_trial_orchestrator.py` unchanged.

## 4. Controlled Engineering Path

- service / route / command: `POST /api/matrix-script/{task_id}/tomato-real-result` (+ `GET …/preview/final.mp4`) → `run_tomato_real_result(...)`.
- asset ingestion: fixed pack `assets/matrix_script_assets/MS-TOMATO-BEACH-001/` (3 real 941×1672 photos).
- shot mapping (fixed, no drift): 01→`01_beach_hook.png` (local_real_asset) · 02→`02_tomato_bowl.png` (local_real_asset) · 03→`03_pick_tomato.png` (local_real_asset) · 04→reuse `03_pick_tomato.png` crop/zoom (fallback_semantic_reuse) · 05→reuse `02_tomato_bowl.png` crop/zoom (fallback_semantic_reuse).
- TTS: Azure (`AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION`) used only when env present; otherwise honest silent fallback. This run: **silent fallback** (no Azure env) — burned captions + `.srt` carry the script.
- subtitles: operator-language captions burned per shot via a Pillow-rendered caption PNG composited with ffmpeg `overlay` (this ffmpeg build has no `drawtext`/`subtitles`); `.srt` sidecar also produced. If Pillow is absent the renderer degrades to the `.srt` sidecar only.
- ffmpeg assembly: image→motion via `zoompan` (Ken-Burns, per-shot focus/zoom) → caption overlay → `assemble_final_video` (reused).
- artifact staging: `stage_minimal_result` (reused) → opaque `artifact://` refs; `staged_record_to_delivery_block` (reused).
- preview_url: dedicated gateway endpoint streaming the staged local `final.mp4` — browser-openable regardless of storage backend; NOT a publish/provider/download URL.

## 5. Tomato Case Run

- task_id: `MS-TOMATO-BEACH-001-run1`
- run path: registered app route via FastAPI TestClient (`POST` → orchestrator → render → stage → delivery block → acceptance → `GET` preview). Not a temporary script.
- final.mp4: `.local_workspace/artifacts/matrix_script_tomato_real_result/MS-TOMATO-BEACH-001-run1/final/final.mp4` (2,331,263 bytes)
- duration: 20.0s (ffprobe)
- resolution: 720×1280 (9:16), video h264 + audio aac
- preview_url: `/api/matrix-script/MS-TOMATO-BEACH-001-run1/tomato-real-result/preview/final.mp4`
- browser playable: YES — `GET preview` → HTTP 200, `Content-Type: video/mp4`, 2,331,263 bytes

## 6. Shot Result

| Shot | Expected | Asset | Source | Pass |
|---|---|---|---|---|
| 01 | 海边 Hook | 01_beach_hook.png | local_real_asset | ✅ real + match |
| 02 | 小番茄特写 | 02_tomato_bowl.png | local_real_asset | ✅ real + match |
| 03 | 拿起小番茄 | 03_pick_tomato.png | local_real_asset | ✅ real + match |
| 04 | 品尝爆汁 | 03_pick_tomato.png (crop/zoom) | fallback_semantic_reuse | ◐ semantic reuse |
| 05 | 递向镜头 CTA | 02_tomato_bowl.png (crop/zoom) | fallback_semantic_reuse | ◐ semantic reuse |

Frame inspection of the assembled `final.mp4` confirmed real photographic pixels + legible burned Chinese captions per shot (beach woman / cherry-tomato bowl / picking hand / reused close-ups). Not a color card.

## 7. Operator Acceptance

- technical_preview: **false**
- operator_usable: **true**
- delivery_candidate: **true**
- official_publish_ready: **false**
- visual_semantic_match: **partial_pass**
- shot_count: 5
- shot_match_count: 3
- real_visual_count: 3
- blocked_reason: null

## 8. Boundary Check

- no provider_url: ✅ (payload forbidden-token scan = none)
- no publish_url/status: ✅
- no Akool task/model/credit: ✅
- no schema/contract changes: ✅
- no Hot Follow/Digital Anchor changes: ✅
- artifact_storage.py untouched: ✅
- `official_publish_ready` never true: ✅
- fallback-only result fails operator acceptance (gate unit-tested): ✅

## 9. Verdict

- **PASS WITH LIMITATIONS**
- Limitations (honest):
  1. Audio was the silent fallback (no Azure env in this dev environment). Burned captions + `.srt` carry the script; set `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` to get real voiceover via the same path.
  2. The production storage-staging sink needs a configured R2/local backend (not present in this dev env); the run used the in-memory staging sink (CI parity). The `final.mp4` + `preview_url` are real and persisted locally; the `artifact://` refs are opaque records. This mirrors the PR-17R / P0R2 validation posture.
  3. Shots 04 / 05 are semantic reuses of real photos (crop/zoom), not distinct captures — counted honestly as `fallback_semantic_reuse`, not toward `real_visual_count`.
- next action: human operator validation of the preview against the 5-shot checklist; optionally provide Azure creds and/or two more distinct photos (真实 04 品尝 / 05 递镜) to lift `partial_pass` → `pass`.

## 10. Validation Commands

- `.venv/bin/python -m pytest gateway/app/services/tests/test_matrix_script_tomato_real_result.py` → 16 passed
- adjacent regression (real_trial route + orchestrator + tomato) → 31 passed
- `py_compile` on all changed Python files → OK; `git diff --check` → clean
- Jinja parse of `task_workbench.html` + `task_publish_hub.html` → OK
- Interpreter: `.venv` Python 3.13.5 (the repo's 3.9.6 system Python hits the pre-existing PEP-604 `config.py` limitation; environment limitation, not a code regression). ffmpeg 8.1.1 (no libfreetype/libass → captions via Pillow overlay).

## 11. Scope (fix / not-fix / follow-up)

- fixes: produces the first operator-usable Matrix Script result from the fixed tomato script + local asset pack, with an L3 acceptance gate and operator-visible surfaces; replaces "color-card success" with an honest operator-usable verdict.
- does not fix: real per-shot generation (Akool live remains gated/out of scope); production storage staging requires backend config; Delivery server-side population of `matrix_script_staged_candidate` from a run (the Workbench action is the reliable live path today, per P0R2 §5).
- follow-up: Azure voiceover when creds exist; distinct 04/05 captures for `pass`; wiring the staged candidate into `task.config` for the Delivery server-render path (PR-185 territory).
