# Matrix Script Phase 3 — PR-5R Minimal Result Service Bridge (Execution Note)

Date: 2026-05-31
Branch: `phase3/pr5r-matrix-script-minimal-result-service`
Base: `main` @ `a084bd90ea659f27c794271757ccc72c45800797`
Status: Promotes the PR-4R standalone result loop into a **callable Matrix Script internal service capability**. Still NOT UI, NOT Delivery Center, NOT Akool live.

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5 (first real controlled route)
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR4R_MINIMAL_RESULT_LOOP.md`, `…PR3…`, `…PR2…`
- `gateway/app/services/matrix_script/`: `minimal_result_loop.py`, `simple_scene_renderer.py`, `shot_plan.py`, `shot_plan_builder.py`, `scene_artifacts.py`, `scene_manifest.py`, `create_entry.py` (entry field shape), `phase_b_authoring.py`, `main_video_result_view.py`

### Why sufficient
PR-5R is a thin internal-service bridge over already-merged PR-2/PR-3/PR-4R capability. `create_entry.py` fixes the task-entry field set used by the deterministic outline derivation. No contract/schema change is needed.

### Missing-authority handling
None.

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/minimal_result_service.py` | `MatrixScriptMinimalResultRequest` / `MatrixScriptMinimalResultSummary` + `run_matrix_script_minimal_result()` + `MatrixScriptMinimalResultService` + `derive_outline_from_task()`. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_service.py` | Service tests (logic always-run; real-render gated on ffmpeg). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR5R_MINIMAL_RESULT_SERVICE.md` | This note. |

Optional `minimal_result_types.py` was **not** needed — types live in the service module. `gateway/app/services/matrix_script/__init__.py` was **not** touched.

### Flow
```
Matrix Script task-like fixture OR explicit outline
  → derive_outline_from_task (deterministic placeholder; NOT real understanding)
  → build_shot_plan (PR-2)
  → build_scene_manifest_skeleton (PR-3)        [via the loop]
  → run_minimal_result_loop (PR-4R)             → local result pack + manifest
  → verify final.mp4 exists & non-empty
  → MatrixScriptMinimalResultSummary (local paths + shot_count + duration +
     generation_provider="none" + scene/audio strategy)
```

The service **does not own artifact truth** — it returns local result-pack paths for service-layer validation only. `generation_provider` stays `"none"`. The task→outline derivation is a deterministic placeholder, not real script understanding (gated behind Capability Expansion W2.3).

---

## Validation

Environment: ffmpeg 8.1.1 / ffprobe present. Without ffmpeg the real-render tests **skip** with a clear reason — a fake `final.mp4` is never produced.

- `pytest test_matrix_script_minimal_result_service.py` → all pass (logic + real-render).
- `pytest test_matrix_script_minimal_result_loop.py` → pass (PR-4R regression).
- `pytest test_matrix_script_shot_plan.py` / `test_matrix_script_scene_artifacts.py` → pass (PR-2/PR-3 regression).
- `py_compile minimal_result_service.py` → OK; `git diff --check` → clean; forbidden-path guard → none.

---

## What was explicitly NOT added (PR-5R forbidden scope)

No Akool live API / adapter import; no webhook / polling; no `artifact_storage` / R2 write (output only to the caller's temp dir); no publish logic; no route / template / Delivery Center runtime change; no schema / packet / contract change (`envelope.py` untouched); no capability-enum change; no Hot Follow / Digital Anchor change; debt branch untouched. No UI wiring; existing Matrix Script route behavior unchanged.
