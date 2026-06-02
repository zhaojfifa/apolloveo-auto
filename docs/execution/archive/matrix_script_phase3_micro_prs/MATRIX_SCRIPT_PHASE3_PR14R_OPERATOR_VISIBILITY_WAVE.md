# Matrix Script Phase 3 — PR-14R Operator Visibility Wave (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr14r-matrix-script-operator-visibility-wave`
Base: `main` @ `f0a9c410d8a5abbed6ff8ab4db706804b58ea6c1`
Status: Two operator-visible capabilities in one wave — (A) Delivery local read-only result view, (B) execution_trace process observability. NOT Akool, NOT official delivery, NOT publish.

---

## Reading Declaration

Root + docs indexes and root governance read (`CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md` §8/§13, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`, `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`). Task-specific: PR-0 design §6/§7, PR-9R/PR-12R/PR-13R notes, `task_publish_hub.html` matrix_script gate (`ms_pub`), `task_workbench.html` matrix_script branch, the minimal-result module chain. Sufficient — both surfaces are read-only projections over the already-merged surface model; no contract/schema change. No missing authority.

---

## What was added / changed

| File | Change |
| --- | --- |
| `gateway/app/services/matrix_script/minimal_result_trace.py` | **new** — closed 6-step `TRACE_STEPS` + `build_minimal_result_trace(surface)` (all `done` when a local result exists, else `pending`) + label helper + guard. |
| `gateway/app/services/matrix_script/minimal_result_delivery_view.py` | **new** — `derive_matrix_script_minimal_result_delivery_block(task)` (+ surface-view variant); local read-only Delivery block with `DELIVERY_NOTE`; `official_publish_ready` hard-pinned `False`; token/key guard. |
| `gateway/app/templates/task_publish_hub.html` | **+1 block** inside the matrix_script gate (after Section 1): `data-role="matrix-script-dc-local-result"`, gated by `task.config.matrix_script_minimal_result.has_result`; shows label/status/local path/duration/shots/storage_scope/official_publish_ready + the delivery note. |
| `gateway/app/templates/task_workbench.html` | **trace** added to the PR-13R action block: a `data-role="ms-minimal-result-trace"` container + JS `renderTrace()` over a closed 6-step `TRACE_STEPS` list (mirrors the module); rendered client-side after a successful generate. |
| `gateway/app/services/tests/test_matrix_script_operator_visibility_wave.py` | **new** — module + static-template tests (15). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR14R_OPERATOR_VISIBILITY_WAVE.md` | **new** — this note. |

`wiring.py`, `publish_hub_render_data.py`, `tasks.py`, the route, and the orchestrator were **not** touched — both surfaces read the existing surface dict (`task.config.matrix_script_minimal_result` for Delivery; the PR-13R POST response for the Workbench trace).

### A. Delivery local read-only result
`本地最小成片` · `result_status` · `final_video_path` (local) · `duration_seconds` · `shot_count` · `storage_scope=local_workspace` · `official_publish_ready=false` · note `该结果尚未进入正式交付存储，不能作为正式发布文件。`

### B. execution_trace (process observable)
Closed 6 steps, all `done` on success: `生成镜头计划` (shot_plan) · `生成场景片段` (scene_clips) · `生成音频` (audio) · `生成字幕` (subtitles) · `合成成片` (assembly) · `生成结果视图` (surface). Synchronous v1 (no async progress). Rendered in the Workbench action block after a successful generate.

---

## Validation

- `pytest test_matrix_script_operator_visibility_wave.py` → **15 passed**.
- Decreed regressions: `test_matrix_script_minimal_result_workbench_action.py` + `test_matrix_script_minimal_result_route.py` + `test_matrix_script_workbench_phase2b_product_fidelity.py` → pass.
- Touched-surface (publish_hub) regressions: `test_matrix_script_delivery_center_product_flow_reset_prb.py` + `test_matrix_script_delivery_center_pr3_reframing.py` + `test_matrix_script_workbench_phase2c_operator_readability.py` → pass.
- Aggregate run of the above: **177 passed**. `git diff --check` clean. Forbidden-path guard → none.
- Note: the assembly trace label is `合成成片` (not `合成 final.mp4`) so no literal `.mp4` appears in primary-scanned template text (keeps the no-fake-media fidelity invariants green).

---

## What was explicitly NOT added (PR-14R forbidden scope)

No Akool live API / adapter usage; no provider URL; no `artifact_storage` / R2 write; no official publish gate / `publish_url` / `publish_status` / `download_url` / `artifact_key` / `r2_key`; no schema / packet / contract change (`envelope.py` untouched); no Hot Follow / Digital Anchor change (both surfaces gated to matrix_script); no Delivery Center publish runtime; no big UI refactor (one Delivery card + a trace block in the existing Workbench action). Real generation via Akool + official delivery remain gated behind the Capability Expansion Gate Wave (W2.3).
