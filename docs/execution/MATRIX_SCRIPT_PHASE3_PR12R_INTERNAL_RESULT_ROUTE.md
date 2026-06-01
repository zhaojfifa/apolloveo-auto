# Matrix Script Phase 3 — PR-12R Internal Minimal-Result Route (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr12r-matrix-script-internal-result-route`
Base: `main` @ `31fb8e7ed85bac03c293c08bd75e6ad60fadd1a8`
Status: Controlled internal backend trigger — "service can run" → "system can trigger". NOT a public operator button, NOT official delivery, NOT a publish gate.

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md` (§3 router-owns-HTTP-only, §9 god-file), `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5
- Phase 3 execution notes PR-10R (orchestrator) + PR-11R (command)
- Conventions mirrored from `gateway/app/routers/matrix_script_closure.py` (task resolve, matrix_script guard, JSONResponse, no mutation), `gateway/app/deps.py` (`get_task_repository`), `gateway/app/config.py` (`workspace_root`), `gateway/app/main.py` (router registration)

### Why sufficient
PR-12R adds one narrow router over the already-merged PR-11R command. Router owns only HTTP concerns (parse path param, resolve+guard task, call service, shape response). No new business logic.

### Missing-authority handling
None.

---

## What was added / changed

| File | Change |
| --- | --- |
| `gateway/app/routers/matrix_script_minimal_result.py` | **new** — `POST /api/matrix-script/{task_id}/minimal-result`; resolves the task (404), enforces matrix_script (400), runs the PR-11R command into a local workspace dir, returns the safe surface dict; FFmpeg absent → 503. |
| `gateway/app/main.py` | **+2 lines** — import + `include_router(matrix_script_minimal_result_router.api_router)`. Registration only; no other change. `tasks.py` untouched. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_route.py` | **new** — HTTP-boundary tests (minimal app harness; real-render gated on ffmpeg). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR12R_INTERNAL_RESULT_ROUTE.md` | **new** — this note. |

### Endpoint
`POST /api/matrix-script/{task_id}/minimal-result`
- Matrix-Script only (4xx otherwise); reads the task via `get_task_repository` — **no repository mutation, no publish-state change**.
- Output dir: `resolve_minimal_result_output_dir(task_id)` = `<workspace_root>/artifacts/matrix_script_minimal/{task_id}` (local workspace; tests monkeypatch to a temp dir — never R2 / artifact storage).
- Response = `minimal_result_surface_view_to_dict(view)` (safe surface dict): `has_result` / local `final_video_path` / `storage_scope="local_workspace"` / `official_publish_ready=false` / operator note. Re-guarded with `assert_no_result_surface_forbidden_tokens`.
- FFmpeg absent → HTTP 503 (`minimal_result_generation_unavailable`); a fake `final.mp4` is never produced.

### Auth / safety boundary
Reuses the existing app/router + `get_task_repository` dependency (same posture as the merged Matrix Script closure router). No new public unprotected mechanism is introduced; it is a controlled backend action, not a UI button.

---

## Validation

Environment: ffmpeg 8.1.1 / ffprobe present. Without ffmpeg the real-render route test **skips**; the 503 path is covered unconditionally.

- `pytest test_matrix_script_minimal_result_route.py` → pass (rejection + 404 + 503 always; real 200 path with ffmpeg).
- `pytest test_matrix_script_minimal_result_command.py` / `…orchestrator.py` → pass (regression).
- `py_compile matrix_script_minimal_result.py` (+ `main.py`) → OK; `git diff --check` → clean.
- Forbidden-path guard (templates / hot_follow / digital_anchor / contracts / schemas / packet / envelope.py / artifact_storage.py) → none. `main.py` touched for registration only (2 lines); `tasks.py` untouched.

---

## What was explicitly NOT added (PR-12R forbidden scope)

No UI button / template change; no Delivery Center runtime; no `publish_url` / `publish_status` / official publish gate; no `artifact_storage` / R2 write; no Akool live API / adapter usage; no webhook / polling; no schema / packet / contract change (`envelope.py` untouched); no Hot Follow / Digital Anchor change; no task-repository mutation beyond reading the task; no broad `tasks.py` modification. Real generation via Akool + copy-into-Apollo storage remain gated behind the Capability Expansion Gate Wave (W2.3).
