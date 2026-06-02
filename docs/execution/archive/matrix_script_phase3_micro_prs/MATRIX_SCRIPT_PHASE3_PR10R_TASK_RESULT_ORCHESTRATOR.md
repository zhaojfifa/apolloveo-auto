# Matrix Script Phase 3 — PR-10R Task Result Orchestrator (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr10r-matrix-script-minimal-result-orchestrator`
Base: `main` @ `df3ec12b9beb3d5d5dbbccd1cd8482859bc04d2c`
Status: Service-internal orchestrator chaining the merged minimal-result modules so an existing Matrix Script task becomes a real local result + surface view. **No UI, no route, no button/action wiring.**

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5
- Phase 3 execution notes PR-4R … PR-9R
- `gateway/app/services/matrix_script/`: `minimal_result_service.py` (`derive_outline_from_task`, `run_matrix_script_minimal_result`, request/summary), `minimal_result_record.py`, `minimal_result_projection.py`, `minimal_result_surface.py`

### Why sufficient
PR-10R only wires the already-merged PR-5R…PR-8R modules into one call. No module logic is rewritten; no contract/schema change.

### Missing-authority handling
None.

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/minimal_result_orchestrator.py` | `run_matrix_script_task_minimal_result(task, output_dir, *, aspect_ratio, target_duration_seconds) -> MatrixScriptMinimalResultSurfaceView`. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_orchestrator.py` | Logic tests (always-run) + real-render tests (gated on ffmpeg). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR10R_TASK_RESULT_ORCHESTRATOR.md` | This note. |

No existing file was modified.

### Chain
```
task
  → derive_outline_from_task (PR-5R)
  → run_matrix_script_minimal_result (PR-5R)  → real final.mp4 + summary
  → minimal_result_summary_to_record (PR-6R)
  → minimal_result_record_to_operator_projection (PR-7R)
  → operator_projection_to_surface_view (PR-8R)
  → MatrixScriptMinimalResultSurfaceView
```
The returned surface view (`has_result=True`, `storage_scope="local_workspace"`, `official_publish_ready=False`, operator note) is exactly what the PR-9R Workbench block consumes.

---

## Validation

Environment: ffmpeg 8.1.1 / ffprobe present. Without ffmpeg the real-render tests **skip** with a clear reason — a fake `final.mp4` is never produced.

- `pytest test_matrix_script_minimal_result_orchestrator.py` → all pass (logic + real-render).
- `pytest test_matrix_script_minimal_result_workbench_block.py` / `…minimal_result_service.py` → pass (regression).
- `py_compile minimal_result_orchestrator.py` → OK; `git diff --check` → clean; forbidden-path guard → none.

---

## What was explicitly NOT added (PR-10R forbidden scope)

No UI / template / router change; no button/action wiring; no Delivery Center runtime change; no official publish gate / publish logic; no `artifact_storage` / R2 write (output only to caller temp dir); no Akool live API / adapter usage; no webhook / polling; no schema / packet / contract change (`envelope.py` untouched); no Hot Follow / Digital Anchor change; debt branch untouched. Real generation via Akool + copy-into-Apollo storage remain gated behind the Capability Expansion Gate Wave (W2.3).
