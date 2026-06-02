# Matrix Script Phase 3 — PR-17R Real Operator Trial (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr17r-matrix-script-real-operator-trial`
Base: `main` @ `0e2868d71772ce5a4975e853f11847231bf81020`
Status: Final slice of the Real Operator Trial Wave. Chains gate → optional Akool one-shot → real final.mp4 → artifact staging → Delivery staged candidate. `official_publish_ready=false`; real generation stays gated (default off).

---

## Reading Declaration

Root + docs indexes + governance read. Task-specific: Phase 3 design plan §2/§5/§10; PR-15R gate (`akool_real_gate`); PR-16R staging (`minimal_result_artifact_staging`); PR-4R loop; PR-5R outline derivation; the closure-router conventions; `config.workspace_root`; `main.py` registration. The existing `artifact_storage` abstraction is consumed only via an injected sink. Sufficient; no contract/schema change. No missing authority.

---

## Governance decision (binding)

The decree §11 listed `generation_provider = akool_one_shot_attempted` for the Delivery candidate, but §1/§5/§8 forbid any Akool/vendor name in the UI, and the four-layer rule bars provider names from the operator surface. Resolved in favour of the no-vendor-in-UI governance: the operator-facing label is the **provider-agnostic** `real_oneshot_attempted` (never `akool`). Live generation remains the Capability Expansion Gate Wave (W2.3) scope; it is reachable only by explicitly enabling `MATRIX_SCRIPT_AKOOL_REAL` with a key + a wired transport (none shipped) — default off.

---

## What was added / changed

| File | Change |
| --- | --- |
| `gateway/app/services/matrix_script/real_trial_orchestrator.py` | **new** — `run_matrix_script_real_trial(task, output_dir, sink, env, resolver, akool_credentials, akool_transport, ...)` + `real_trial_result_to_payload`. |
| `gateway/app/routers/matrix_script_real_trial.py` | **new** — `POST /api/matrix-script/{task_id}/real-trial`; resolves task (404) + matrix_script guard (400); local workspace output dir; default sink wraps `upload_artifact` (existing abstraction); 503 on ffmpeg absence; leak-guarded payload. |
| `gateway/app/services/matrix_script/minimal_result_delivery_view.py` | **+ additive** `generation_provider` param on `staged_record_to_delivery_block` (closed `none` / `real_oneshot_attempted`). |
| `gateway/app/main.py` | **+2 lines** — router import + `include_router`. Registration only. |
| `gateway/app/templates/task_publish_hub.html` | **+1 display block** in the matrix_script gate — staged-candidate read-only block (artifact refs, storage_scope, delivery_candidate, official_publish_ready, generation_provider). No publish button. |
| `gateway/app/services/tests/test_matrix_script_real_trial_orchestrator.py` + `..._route.py` | **new** — 14 tests. |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR17R_REAL_OPERATOR_TRIAL.md` | this note. |

`artifact_storage.py` NOT modified; `tasks.py` NOT touched.

### Flow
`task → gate → (optional one-shot under gate; provider output internal-only, never spliced/surfaced) → derive outline → run_minimal_result_loop (real final.mp4) → stage_minimal_result (artifact_staged refs) → staged delivery block`.

### Gate behavior (criteria 1/2/3/9/10)
- `MATRIX_SCRIPT_AKOOL_REAL` unset/false → no provider attempt; fallback; final.mp4; staged.
- flag true but no key / no transport → operator-readable blocked reason; fallback; final.mp4; staged.
- flag true + key + injected (fake/live) transport → one shot attempted; output accepted only internally; `generation_provider=real_oneshot_attempted`; staged.
- invalid task → `RealTrialError` (400 at route); ffmpeg missing → `FFmpegUnavailableError` (503 at route), never a fake final.mp4.

---

## Validation

Real end-to-end proof (gate off, ffmpeg 8.1.1): `gate_enabled=False`, `real_oneshot_used=False`, `generation_provider=none`, `storage_scope=artifact_staged`, `delivery_candidate=True`, `official_publish_ready=False`, `final_ref=artifact://matrix_script/rt-demo/final/final.mp4`, 9 files staged.

- `pytest test_matrix_script_real_trial_orchestrator.py` + `..._route.py` → **14 passed** (gate off/on-not-wired/on-success, artifact refs, no provider leak, no publish keys, invalid task, ffmpeg-missing → no fake / 503, route safe payload + no repo mutation, Delivery staged-candidate static block).
- Regression: staging + akool gate + operator visibility wave → **47 passed**; publish-hub delivery suites → **105 passed**.
- `py_compile` (orchestrator + route + main.py + delivery_view) OK; `git diff --check` clean; forbidden-path guard → none; `main.py` registration-only; `artifact_storage.py` untouched.

---

## Acceptance mapping (wave criteria 1–8)

1. No-Akool → stable local fallback: ✅ · 2. Akool enabled + key/transport → ≥1 shot via real path (fake transport in CI; live verified manually only): ✅ (`real_oneshot_attempted`) · 3. provider temp URL copied/internal, not in operator payload: ✅ · 4. final.mp4 written to artifact staged area: ✅ (`artifact://` ref via injected sink; real R2 only when env-configured) · 5. Delivery shows staged candidate: ✅ (route payload + publish_hub block) · 6. official_publish_ready=false: ✅ · 7. no provider/vendor/model/credit/provider_url/publish_url leakage: ✅ (guards + tests) · 8. operator-readable blocked reason on failure: ✅.

---

## What was explicitly NOT added (PR-17R forbidden scope)

No `official_publish_ready=true`; no `publish_url` / `publish_status` / `download_url` / `provider_url` / `temporary_url`; no Akool task id / model / credit / raw provider response in UI; no provider URL as `final_video`; no `artifact_storage.py` modification; no schema/packet/contract change; no Hot Follow / Digital Anchor change; no broad UI redesign; no publish button. Live Akool calls require explicit flag + key + wired transport (none shipped); any manual live trial is recorded separately and is not the default test behavior.
