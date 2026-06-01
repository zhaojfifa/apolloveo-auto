# Matrix Script Phase 3 — PR-185 Delivery Render Path Fix

Date: 2026-06-01
Branch: `phase3/pr185-delivery-render-path-fix`
Base: `main` @ `3ecff9e0d61ffc677bd22015dc143c2db5c01540`
Status: Makes the Delivery Center server-rendered staged-candidate (and local-result) blocks actually display the staged preview link. No Akool live, no schema/contract, no Hot Follow / Digital Anchor, no artifact_storage.py, no official publish change.

---

## Root Cause

The PR-14R/PR-17R Delivery blocks read `task.config.matrix_script_*`, but the publish handler renders `task_publish_hub.html` with `ctx={"task": detail}` — a projected `detail`, not the raw repo task. So `task.config.matrix_script_minimal_result` / `matrix_script_staged_candidate` never resolved and the `{% if %}` gates were always false (graceful, no 500, but inert).

## Fix

The matrix_script publish render-data function (`derive_matrix_script_publish_hub_render_data(task)`) DOES receive the **raw** task. Surface the candidates there and read them in the template via `ms_pub.*` (which already reaches the template):

- `minimal_result_delivery_view.py` — new `derive_matrix_script_staged_candidate_block(task)` (reads `config.matrix_script_staged_candidate`; pins `official_publish_ready=False`; sanitised; empty on absent/forbidden).
- `publish_hub_render_data.py` — adds `local_result` + `staged_candidate` keys (via guarded `_safe_local_result` / `_safe_staged_candidate`) to the returned `ms_pub` dict.
- `task_publish_hub.html` — `{% set ms_local_result = ms_pub.local_result or {} %}` and `{% set ms_staged = ms_pub.staged_candidate or {} %}` (replacing the inert `task.config.*` reads). Blocks + preview link unchanged.
- `task_workbench.html` — removed the `d.generation_provider` row from the "暂存并预览" action JS (a latent PR-184 issue: the literal `provider` tripped the phase2c operator-readability scan). The preview link + storage_scope/candidate/publish-ready rows remain.

## Validation

- New `test_matrix_script_delivery_render_path.py` (8): render-data surfaces staged + local result from raw config; empty without config; `{}` for non-matrix; staged reader pins `official_publish_ready=False`, empty/leak-safe; template reads `ms_pub.*` and no longer reads `task.config.*`.
- Regression: operator-visibility + delivery-center (prb / pr3) + phase2c readability (now green) + real-trial route + artifact-staging + phase2b fidelity → **185 passing**.
- **Live (deployed-equivalent, local storage):** create matrix_script task → `POST real-trial` (200) → inject the returned staged candidate onto task config (simulating persistence) → `GET /tasks/{id}/publish` → **staged-candidate block renders (count 1)** with `data-role="ms-dc-staged-preview" href="/api/matrix-script/{id}/real-trial/preview/final.mp4"`.

## Boundary Confirmation

- official_publish_ready stays false ✅ · preview is internal staged link ✅
- no Akool live / adapter ✅ · no schema/contract ✅ · no Hot Follow / Digital Anchor ✅ · `artifact_storage.py` untouched ✅ · `main.py` untouched ✅ · no publish_url/publish_status/provider_url/download_url ✅

## Note

This resolves the previously-filed follow-up ("Delivery staged-candidate block not rendering"). Persisting the staged candidate onto `task.config.matrix_script_staged_candidate` (so it appears without manual injection) is a separate concern — the current wave intentionally avoids task mutation; the render path is now correct for whenever that persistence lands, and the Workbench "暂存并预览" action already surfaces the preview link client-side today.
