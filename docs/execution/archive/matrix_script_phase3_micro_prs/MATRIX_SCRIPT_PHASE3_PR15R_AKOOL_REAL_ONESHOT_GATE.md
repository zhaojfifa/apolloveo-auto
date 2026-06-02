# Matrix Script Phase 3 — PR-15R Akool Real One-Shot Gate (Design + Execution)

Date: 2026-06-01
Branch: `phase3/pr15r-akool-real-one-shot-gate`
Base: `main` @ `5311e0d13af4a8a9f7c21bf331ad83a4570ba6e2`
Status: First slice of the **Matrix Script Real Operator Trial Wave**. Ships the *gate mechanism* for a real Akool one-shot generation, **default OFF**. No live transport is shipped; no persistence (PR-16R); no route (PR-17R).

---

## 0. Governance position (binding)

Real provider generation is the Capability Expansion Gate Wave (**W2.3**) per the Phase 3 design plan §2/§10 (`docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md`). This PR does **not** open live generation by default. It introduces a controlled gate that permits a real call **only** when all hold:

1. the explicit feature flag `MATRIX_SCRIPT_AKOOL_REAL` is truthy (default unset → off), **and**
2. an Akool API key is resolvable, **and**
3. a live transport is explicitly injected (PR-15R ships **none**).

With any condition unmet, the system performs a local fallback and reports an operator-safe reason. Flipping the flag on (with key + a wired transport) is a deliberate operator act under the trial wave, not the default.

---

## 1. Reading Declaration

Root + docs indexes and governance read. Task-specific: Phase 3 design plan §2/§4/§5/§10; PR-1 Akool adapter skeleton (`workers/adapters/akool`, `AKOOL_API_KEY_REF`, `AKOOL_LOGICAL_TO_ENV`, `AkoolVideoGenAdapter`); `workers/secrets/EnvSecretResolver`; capability adapter base (`AdapterError`/`AdapterResult`/`AdapterInvocation`). Sufficient — PR-15R only composes existing pieces behind a flag. No contract/schema change. No missing authority.

---

## 2. What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/akool_real_gate.py` | `evaluate_akool_real_gate(env, resolver) → AkoolRealGateDecision` (default off; closed reason codes) + `guarded_generate_one_shot(gate, invocation, credentials, transport) → GuardedInvocationResult` + dict serializers + leakage guard. |
| `gateway/app/services/tests/test_matrix_script_akool_real_gate.py` | 19 tests. |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR15R_AKOOL_REAL_ONESHOT_GATE.md` | This doc. |

### Gate decision
`AkoolRealGateDecision{enabled, reason_code, operator_reason_zh}` — reason codes `real_disabled_flag_off` / `real_disabled_no_key` / `real_enabled`; operator text is provider-agnostic Chinese (no Akool/vendor/model/credit).

### Guarded invocation
`GuardedInvocationResult{used_real_provider, fallback, status, operator_reason_zh, provider_output_present, requires_staging, blocked_reason_zh}` — statuses `fallback_local` / `real_attempted_ok` / `real_blocked`.
- gate closed → `fallback_local`, **no adapter call**.
- gate open + injected transport success → `real_attempted_ok`, `requires_staging=True` (the real output must be copied into Apollo storage by PR-16R; its URL is **not** carried here).
- gate open + no transport / `AdapterError` (incl. quota) → `real_blocked` fallback with an operator-safe `blocked_reason_zh`; provider category/message/url/credit are never surfaced.

---

## 3. Validation

- `pytest test_matrix_script_akool_real_gate.py` → **19 passed** (default-off; flag+key enable; truthiness; gate-closed → 0 provider calls; success → staging-flagged + no URL leak; no-transport → graceful blocked; quota error → no credit leak; serializer leak-free).
- Regression: PR-1 akool client + adapters + orchestrator → **71 passed**.
- `py_compile` OK; `git diff --check` clean; forbidden-path guard → none.

---

## 4. Acceptance mapping (wave criteria 1, 3, 8 — others land in PR-16R/PR-17R)

1. No-Akool-enabled → local fallback, stable: ✅ (default off → `fallback_local`, no call).
3. Provider temporary URL not in operator payload: ✅ (success result carries `requires_staging` only; URL never surfaced; PR-16R does the copy).
8. Operator-readable blocked reason on failure: ✅ (`blocked_reason_zh`, provider-agnostic).
(2 real one-shot end-to-end, 4 artifact/R2 staging, 5 Delivery staged candidate, 6 official_publish_ready=false, 7 full no-leak page audit — delivered by PR-16R + PR-17R.)

---

## 5. What was explicitly NOT added

No live HTTP transport (no real network call possible by default); no `artifact_storage` / R2 write (PR-16R); no route / action (PR-17R); no provider URL / Akool task id / model / credit in any operator field; no official publish gate / `publish_url` / `publish_status`; no Hot Follow / Digital Anchor change; no schema / packet / contract change; no UI change. Provider temporary URLs are never treated as deliverable.
