# Matrix Script Phase 3 — PR-8R Minimal Result Surface View (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr8r-matrix-script-minimal-result-surface`
Base: `main` @ `4b2d7573b596a16a6e974cad61fc884beba5a59e`
Status: Read-only, operator-facing **minimal result surface view** in front of any Workbench / Delivery presenter. Pure conversion, local-workspace scoped, **no template change**. NOT a delivery contract, NOT a publish gate, NOT artifact truth.

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5/§7 (operator surface read-only; result-oriented)
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR7R_RESULT_PROJECTION.md` (operator projection consumed here), `…PR6R…`, `…PR5R…`, `…PR4R…`
- `gateway/app/services/matrix_script/`: `minimal_result_projection.py` (operator projection API), `minimal_result_record.py`, `minimal_result_service.py`, `main_video_result_view.py`, `delivery_binding.py`

### Why sufficient
PR-8R is a pure read-model conversion of the PR-7R operator projection into a narrow read-only surface view. No template/router change, no contract/schema change, no I/O.

### Missing-authority handling
None.

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/minimal_result_surface.py` | `MatrixScriptMinimalResultSurfaceView` + `operator_projection_to_surface_view()` + `minimal_result_record_to_surface_view()` (convenience) + `minimal_result_surface_view_to_dict()` + `assert_no_result_surface_forbidden_tokens()`. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_surface.py` | Pure unit tests (no ffmpeg). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR8R_MINIMAL_RESULT_SURFACE.md` | This note. |

**No template was touched.** No existing file modified. The surface lives entirely at the service layer and consumes the PR-7R operator projection.

### Surface shape (fixed/derived values)
- `line_id = "matrix_script"`, `final_video_label = "本地最小成片"`, `operator_note = "已生成本地最小成片，尚未进入正式交付存储"`, `storage_scope = "local_workspace"`, `official_publish_ready = False` (always).
- `has_result` = operator projection's `has_final_video`; `result_status` = `"generated"`; local `final_video_path` / `manifest_path` preserved.

### Field discipline
- Allowed local paths only (`final_video_path`, `manifest_path`).
- Forbidden (absent + guarded as keys AND values): `provider_url`, `temporary_url`, `download_url`, `akool`, `vendor`, `model_id`, `credit`, `provider_task_id`, `artifact_key`, `final_video_key`, `r2_key`, `publish_url`, `publish_status`.

---

## Validation

- `pytest test_matrix_script_minimal_result_surface.py` → all pass (pure unit, no ffmpeg).
- `pytest test_matrix_script_minimal_result_projection.py` / `…record.py` → pass (regression).
- `py_compile minimal_result_surface.py` → OK; `git diff --check` → clean; forbidden-path guard → none; **no template touched**.

---

## What was explicitly NOT added (PR-8R forbidden scope)

No Akool live API / adapter import; no provider URL / download URL; no `artifact_storage` / R2 write or truth field; no official publish gate / `publish_url` / `publish_status`; no template change; no router change; no Delivery Center runtime change; no schema / packet / contract change (`envelope.py` untouched); no Hot Follow / Digital Anchor change; no broad Workbench/Delivery redesign; debt branch untouched. Real generation + provider integration remain gated behind the Capability Expansion Gate Wave (W2.3).
