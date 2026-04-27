# W2.1 Base-Only Adapter Preparation — B2: Retry / Timeout / Cancellation (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **W2.1 Base-Only Adapter Preparation** — B2 only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md` §4 (recommended order, B2 third), §6 B2 (boundary + acceptance)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §3.2, §4, §5 (gap definition + frozen rules)
  - `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 (W2.1 BLOCKED on the four base-only PRs, of which B2 is one)
  - `tests/guardrails/test_fallback_never_primary_truth.py` (W2 admission Phase A — fallback must never become primary truth; B2 inherits this discipline by carrying no fallback strategy)
- Code under review:
  - `gateway/app/services/capability/adapters/base.py`
  - `gateway/app/services/capability/adapters/__init__.py`
  - `tests/services/capability/adapters/test_adapter_execution_context.py`

---

## 1. Scope

This evidence note covers ONLY B2 — the base-only execution control
surface (timeout / retry / cancellation entry) on `AdapterBase`.

In scope:

- adding `CancellationToken`, `RetryPolicy`, and `AdapterExecutionContext`
  to the existing base-only module
  `gateway/app/services/capability/adapters/base.py`;
- extending `AdapterBase.invoke` with a keyword-only
  `context: Optional[AdapterExecutionContext] = None` parameter as the
  unified execution control entry, while keeping `invoke` abstract and
  the base I/O-free;
- exporting the three new types from the package `__init__`;
- adding minimum tests under `tests/services/capability/adapters/`;
- evidence + index write-back.

Out of scope (intentionally not done — see §5):

- B4 (construction-vs-invocation lifecycle policy beyond the bare
  `invoke(context=...)` signature);
- any concrete `CancellationToken` implementation (manual,
  deadline-driven, parent-linked);
- any retry-loop executor (no library binding, no scheduling);
- any provider SDK / client absorption;
- any provider-specific retry policy (e.g. OpenAI / Gemini / Anthropic
  rate-limit tuning);
- any business-layer fallback strategy;
- any runtime wiring;
- any change to `AdapterError` / `AdapterErrorCategory` (frozen by B3),
  `AdapterCredentials` / `SecretRef` / `SecretResolver` (frozen by B1),
  or `AdapterInvocation` / `AdapterResult`;
- any change to `ops/env/*`, `gateway/app/services/packet/`,
  `tests/contracts/`, `tests/guardrails/`, Hot Follow code, frontend,
  or workbench.

---

## 2. What B2 added

### 2.1 `CancellationToken`

Abstract base class with a single abstract property and a small base
convenience:

```
is_cancelled: bool          # abstractproperty
raise_if_cancelled() -> None  # base convenience; raises AdapterError(CANCELLED)
```

Discipline encoded:

- `CancellationToken` is `abc.ABC`; instantiation without an override
  is a `TypeError` (test-enforced).
- The base ships **only the abstract surface** — no concrete subclass
  of `CancellationToken` exists inside `capability/adapters/`
  (test-enforced).
- `raise_if_cancelled()` raises `AdapterError(AdapterErrorCategory.CANCELLED)`
  so callers raise a consistent, provider-agnostic error shape (reusing
  the B3 envelope without widening it).
- Construction is side-effect-free; `is_cancelled` MUST be cheap and
  side-effect-free.
- The base never authors cancellation truth; it only reads the signal a
  caller hands in via `AdapterExecutionContext`.

### 2.2 `RetryPolicy`

Frozen dataclass holding provider-agnostic retry advisory hints:

| Field | Type | Default | Role |
|---|---|---|---|
| `max_attempts` | `int` | `1` | total attempts (initial try + retries); `1` = no retry |
| `initial_backoff_seconds` | `float` | `0.0` | first-retry wait |
| `max_backoff_seconds` | `float` | `0.0` | upper bound on backoff |
| `backoff_multiplier` | `float` | `1.0` | exponential growth factor (≥ 1.0) |

Discipline encoded:

- Frozen — no mutation after construction.
- Validates `max_attempts` is a non-bool `int >= 1`.
- Validates backoff seconds are non-bool numbers `>= 0`.
- Validates `max_backoff_seconds >= initial_backoff_seconds`.
- Validates `backoff_multiplier` is a non-bool number `>= 1.0`.
- Carries hints **only** — does NOT bind to any third-party retry
  library or vendor SDK retry helper, does NOT encode jitter /
  scheduling primitives, and does NOT itself execute the retry.
- Test-enforced: no third-party retry library or async runtime is
  imported by the base module (`tenacity`, `backoff`, `urllib3`,
  `asyncio`, `trio`, `anyio` all banned via AST-level import check).

### 2.3 `AdapterExecutionContext`

Frozen dataclass holding the per-invocation execution control envelope:

| Field | Type | Default | Role |
|---|---|---|---|
| `timeout_seconds` | `Optional[float]` | `None` | overall invocation deadline hint |
| `cancellation` | `Optional[CancellationToken]` | `None` | injected cancellation signal |
| `retry` | `Optional[RetryPolicy]` | `None` | retry advisory shape |

Discipline encoded:

- Frozen — no mutation after construction.
- Validates `timeout_seconds` is a non-bool, positive number when set.
- Validates `cancellation` is a `CancellationToken` instance when set.
- Validates `retry` is a `RetryPolicy` instance when set.
- Field set is exactly `{timeout_seconds, cancellation, retry}`
  (test-enforced; guards against silent shape drift).
- MUST NOT carry vendor / model / engine identifiers.
- MUST NOT carry business / task / packet truth (no `task_id`,
  `packet_id`, `line_id`, `state`, `primary_truth`).
- MUST NOT carry presenter / UI wording.
- MUST NOT carry fallback strategy — fallback is a business-layer
  concern (W2 admission Phase A
  `tests/guardrails/test_fallback_never_primary_truth.py`).
- MUST NOT carry wall-clock truth (`deadline_at`); only relative
  hints. Wall-clock binding belongs to the caller layer.
- The base never starts timers, never schedules retries, and never
  polls cancellation itself — it only carries the shape.

### 2.4 `AdapterBase.invoke`

Extended with a keyword-only `context: Optional[AdapterExecutionContext] = None`
parameter:

```python
@abc.abstractmethod
def invoke(
    self,
    invocation: AdapterInvocation,
    *,
    context: Optional[AdapterExecutionContext] = None,
) -> AdapterResult:
    ...
```

- The signature change is backward-compatible: subclasses that override
  with the older `(self, invocation)` shape still satisfy the abstract
  contract by name.
- The base never inspects `context` itself; honouring it is the
  (future) caller / runtime + vendor adapter responsibility.
- No I/O, no side effects, no timer / retry / cancellation logic in the
  base.

### 2.5 Package exports

`CancellationToken`, `RetryPolicy`, `AdapterExecutionContext` are
re-exported from `gateway.app.services.capability.adapters` and added
to `__all__` so a future provider adapter (under
`workers/adapters/<vendor>/`) can import them without reaching into the
`base` module.

### 2.6 Tests

`tests/services/capability/adapters/test_adapter_execution_context.py`
(31 tests) covers:

`CancellationToken`:

1. `CancellationToken` cannot be instantiated directly (abstract);
2. `CancellationToken` subclasses must implement `is_cancelled`;
3. concrete subclass reports the cancellation signal correctly;
4. `raise_if_cancelled()` is a no-op when not cancelled;
5. `raise_if_cancelled()` raises `AdapterError(CANCELLED)` when cancelled;
6. `CancellationToken` is shipped only as abstract in base — no
   concrete subclass exists inside `capability/adapters/`.

`RetryPolicy`:

7. defaults model "no retry" (`max_attempts=1`, zero backoff,
   multiplier 1.0);
8. accepts valid configurations;
9. rejects `max_attempts < 1`;
10. rejects non-`int` (or `bool`) `max_attempts`;
11. rejects negative backoff seconds;
12. rejects `max_backoff_seconds < initial_backoff_seconds`;
13. rejects `backoff_multiplier < 1.0`;
14. rejects `bool` multiplier;
15. is frozen;
16. field set is stable.

`AdapterExecutionContext`:

17. defaults are all `None`;
18. holds all three fields;
19. rejects non-positive `timeout_seconds`;
20. rejects non-numeric `timeout_seconds` (string, bool);
21. rejects non-`CancellationToken` cancellation;
22. rejects non-`RetryPolicy` retry;
23. is frozen;
24. field set is stable (`{timeout_seconds, cancellation, retry}`).

`AdapterBase.invoke` wiring:

25. `invoke` signature carries keyword-only `context` parameter
    defaulting to `None`;
26. `invoke` accepts and forwards the context; base never inspects it
    itself (cancellation token left untouched);
27. `context` defaults to `None` when omitted.

Boundary discipline:

28. base module import surface — no provider / vendor / business /
    `os.getenv` / `time.sleep` substrings, AND no AST-level import of
    `tenacity` / `backoff` / `urllib3` / `asyncio` / `trio` / `anyio`;
29. neither `RetryPolicy` nor `AdapterExecutionContext` carries
    truth / vendor / presenter / fallback / wall-clock fields;
30. `AdapterExecutionContext` has no fallback-shaped field
    (`fallback`, `primary`, `secondary`, `alternate`);
31. B2 leaves B1 (`AdapterCredentials.resolver`) and B3
    (`AdapterError.to_dict()` key set) shapes intact.

Run:

```
python3 -m pytest tests/services/capability/adapters/ tests/guardrails -v
```

Result: 72 passed (B2: 31 new, B1: 21 unchanged, B3: 13 unchanged,
guardrails: 7 unchanged).

---

## 3. What B2 explicitly did NOT add

- No concrete `CancellationToken` implementation. The base ships only
  the abstract surface; manual / deadline-driven / parent-linked tokens
  belong outside the base.
- No retry-loop executor. `RetryPolicy` is shape-only; no scheduler, no
  jitter, no async wiring.
- No timer / deadline plumbing. `timeout_seconds` is an advisory hint
  only; the base never calls `time.sleep`, `signal.alarm`, or any
  scheduler.
- No third-party retry library binding (`tenacity`, `backoff`,
  `urllib3.util.retry`, vendor SDK retry helpers).
- No async runtime binding (`asyncio`, `trio`, `anyio`).
- No provider-specific retry policy (e.g. OpenAI / Gemini / Anthropic
  rate-limit tuning).
- No business-layer fallback strategy. Fallback is a business concern
  enforced separately (`tests/guardrails/test_fallback_never_primary_truth.py`).
- No broader construction-vs-invocation lifecycle policy beyond the
  signature change to `invoke` (deferred to B4 — e.g. a hard guardrail
  forbidding all I/O at construction time).
- No change to `AdapterError` / `AdapterErrorCategory` (frozen by B3) —
  only re-used (`raise_if_cancelled` raises the existing
  `AdapterErrorCategory.CANCELLED` shape).
- No change to `AdapterCredentials` / `SecretRef` / `SecretResolver`
  (frozen by B1).
- No change to `AdapterInvocation` / `AdapterResult` / capability-kind
  subclasses.
- No env var names, vendor names, model names, or engine names encoded
  in the base.
- No change to `ops/env/*`, `gateway/app/services/packet/`,
  `tests/contracts/`, `tests/guardrails/`, Hot Follow code, frontend,
  or workbench.
- No re-opening of W2 admission Phase A–E governance.

---

## 4. Boundary verification

Per W2.1 directive §6 B2 acceptance:

| Check | Result |
|---|---|
| Timeout / retry / cancellation entry exists as base-only authority | Pass — `AdapterExecutionContext` defined in `base.py`; injected via `AdapterBase.invoke(context=...)` |
| Entry is testable | Pass — 31 tests under `tests/services/capability/adapters/test_adapter_execution_context.py` |
| Surface is provider-agnostic | Pass — no vendor / model / engine fields; no third-party retry library import (AST-checked); no async runtime import (AST-checked); no env-name / wall-clock binding |
| No business / runtime truth leakage | Pass — guarded by `test_execution_context_carries_no_truth_or_vendor_fields`; no truth-write path; no state semantics |
| No fallback strategy leak | Pass — guarded by `test_execution_context_has_no_fallback_field`; fallback remains a business-layer concern (W2 admission Phase A guardrail) |
| Existing adapter closed set preserved | Pass — capability-kind subclasses inherit unchanged; `__init_subclass__` `capability_kind` validation untouched |
| B1 / B3 surfaces preserved | Pass — guarded by `test_b2_does_not_modify_existing_b1_or_b3_field_shapes` |
| Reviewable as a single isolated PR | Pass — change is local to `base.py` + `__init__.py` + one new test file + this evidence note + index entry + execution log |
| Donor-free | Pass — only stdlib (`abc`, `dataclasses`) and the existing in-package `AdapterError` are used |
| Side-effect-free import | Pass — only class / dataclass definitions; no I/O |

---

## 5. Remaining blockers after B2

W2.1 Provider Absorption Wave remains BLOCKED. Outstanding base-only PRs
(per W2 admission Phase C lifecycle review §5 and W2.1 directive §9):

1. **B4 — construction-vs-invocation lifecycle** (not started)

(B1, B2, B3 are implementation green; B1 and B3 are merged on `main`,
B2 awaits architect + reviewer signoff.)

After B4 is green and architect + reviewer signoff is recorded for all
four base-only PRs, the first W2.1 Provider PR may open. B4 may not be
bundled with a provider absorption PR (W2 admission Phase C lifecycle
review §4.1).

---

## 6. Next handoff

- **Architect** — judge whether B2's surface (`CancellationToken`,
  `RetryPolicy`, `AdapterExecutionContext`, the keyword-only `context`
  parameter on `AdapterBase.invoke`) is sufficient and not
  over-designed; in particular confirm that:
  - keeping the base I/O-free (no timer / sleep / scheduler) and
    delegating actual timeout / retry / cancellation execution to a
    future caller layer is acceptable;
  - reusing `AdapterErrorCategory.CANCELLED` (frozen by B3) for
    `raise_if_cancelled()` does not require widening B3;
  - deferring the I/O-at-construction guardrail and any per-attempt
    advisory hooks to B4 is acceptable.
  Signoff before B4 starts.
- **Reviewer** — close B2 as a single PR; verify no scope leak into B4;
  verify no Hot Follow / packet / contracts / frontend touch; verify
  `ops/env/*` and B1 / B3 surfaces are unchanged.
- **Engineering** — do NOT begin B4 until B2 is signed off; do NOT
  start any W2.1 provider absorption.
