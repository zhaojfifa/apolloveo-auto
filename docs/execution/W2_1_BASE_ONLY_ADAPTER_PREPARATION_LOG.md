# W2.1 Base-Only Adapter Preparation — Execution Log

Active execution log for the W2.1 Base-Only Adapter Preparation Wave
(`docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md`).

The four base-only PRs (B1–B4) are tracked here. Each entry must record what
was added, what was intentionally not added, and what blockers remain.

---

## B3 — Error Envelope (`AdapterError`)

- Date: 2026-04-27
- Status: implementation green; awaiting architect + reviewer signoff
- Evidence: `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md`
- Code:
  - `gateway/app/services/capability/adapters/base.py` (added
    `AdapterErrorCategory`, `AdapterError`)
  - `gateway/app/services/capability/adapters/__init__.py` (export)
  - `tests/services/capability/adapters/test_adapter_error.py` (13 tests, pass)
- What B3 adds: closed `AdapterErrorCategory` set, advisory-shaped
  `AdapterError` exception with frozen `{category, message, source, retryable,
  details}` shape, immutable `details` view, stable `to_dict()` serialisation.
- What B3 does NOT add: B1 (auth/credential), B2 (retry/timeout/cancellation),
  B4 (construction-vs-invocation), provider code, runtime wiring, Hot Follow
  changes, packet / schema / contracts / workbench changes.
- Validation: `python3 -m pytest tests/services/capability/adapters/test_adapter_error.py -v` → 13 passed.
- Next handoff: architect signoff on B3 boundary; reviewer closes B3 PR; B1 may then start.

---

## B1 — Auth / Credential Surface

- Date: 2026-04-27
- Status: implementation green; awaiting architect + reviewer signoff
- Evidence: `docs/execution/evidence/w2_1_b1_adapter_credential_surface_v1.md`
- Code:
  - `gateway/app/services/capability/adapters/base.py` (added
    `SecretRef`, `SecretResolver`, `AdapterCredentials`, plus
    `AdapterBase.__init__(*, credentials=None)` and read-only
    `credentials` property)
  - `gateway/app/services/capability/adapters/__init__.py` (exports)
  - `tests/services/capability/adapters/test_adapter_credentials.py`
    (21 tests, pass)
- What B1 adds: provider-agnostic `SecretRef` (logical handle) and
  abstract `SecretResolver` surface; frozen `AdapterCredentials`
  envelope holding a single `resolver` field; construction-time
  injection on `AdapterBase` via `__init__(*, credentials=None)` that
  stores the envelope without any I/O and exposes it as a read-only
  `credentials` property. Compatible with the frozen
  `ops/env/env_matrix_v1.md` / `ops/env/secret_loading_baseline_v1.md`
  authority — neither file is modified.
- What B1 does NOT add: any concrete `SecretResolver` implementation
  (env / vault / KMS / file loaders); B2 (retry / timeout /
  cancellation); broader B4 lifecycle policy beyond bare storage of
  the envelope; provider code; runtime wiring; Hot Follow / packet /
  schema / contracts / workbench / frontend changes.
- Validation: `python3 -m pytest tests/services/capability/adapters/test_adapter_credentials.py tests/services/capability/adapters/test_adapter_error.py -v`
  → 34 passed (B1: 21 new, B3: 13 unchanged).
- Next handoff: architect signoff on B1 boundary; reviewer closes B1 PR;
  B2 may then start.

## B2 — Retry / Timeout / Cancellation

- Date: 2026-04-27
- Status: implementation green; awaiting architect + reviewer signoff
- Evidence: `docs/execution/evidence/w2_1_b2_adapter_execution_context_v1.md`
- Code:
  - `gateway/app/services/capability/adapters/base.py` (added
    `CancellationToken`, `RetryPolicy`, `AdapterExecutionContext`;
    extended `AdapterBase.invoke` with keyword-only
    `context: Optional[AdapterExecutionContext] = None`)
  - `gateway/app/services/capability/adapters/__init__.py` (exports)
  - `tests/services/capability/adapters/test_adapter_execution_context.py`
    (31 tests, pass)
- What B2 adds: provider-agnostic `CancellationToken` (abstract,
  base ships no concrete impl); frozen `RetryPolicy` advisory shape
  with `max_attempts` / `initial_backoff_seconds` /
  `max_backoff_seconds` / `backoff_multiplier`, no library binding;
  frozen `AdapterExecutionContext` envelope holding `timeout_seconds`,
  `cancellation`, `retry`; unified execution control entry on
  `AdapterBase.invoke(*, context=None)`. Reuses the B3
  `AdapterErrorCategory.CANCELLED` shape for
  `CancellationToken.raise_if_cancelled()` without widening B3.
- What B2 does NOT add: no concrete cancellation token; no retry-loop
  executor; no timer / deadline plumbing; no third-party retry
  library binding (`tenacity`, `backoff`, `urllib3`, vendor SDK retry
  helpers — all AST-checked); no async runtime binding (`asyncio`,
  `trio`, `anyio` — all AST-checked); no provider-specific retry
  policy; no business-layer fallback strategy; no broader B4
  lifecycle policy; no change to B1 or B3 surfaces; no provider code;
  no runtime wiring; no Hot Follow / packet / schema / contracts /
  workbench / frontend changes.
- Validation: `python3 -m pytest tests/services/capability/adapters/ tests/guardrails -v`
  → 72 passed (B2: 31 new, B1: 21 unchanged, B3: 13 unchanged,
  guardrails: 7 unchanged).
- Next handoff: architect signoff on B2 boundary; reviewer closes B2 PR;
  B4 may then start.

## B4 — Construction-vs-Invocation Lifecycle

- Status: NOT STARTED.

---

## W2.1 Provider Absorption gate

W2.1 Provider Absorption remains BLOCKED until B1–B4 are all green and
signed off (W2.1 directive §9). After B3, three of the four base-only PRs
remain outstanding.
