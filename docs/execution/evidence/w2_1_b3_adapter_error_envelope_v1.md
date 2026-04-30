# W2.1 Base-Only Adapter Preparation — B3: Error Envelope (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **W2.1 Base-Only Adapter Preparation** — B3 only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md` §4 (recommended order, B3 first), §6 B3 (boundary + acceptance)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §3.3, §4, §5 (gap definition + frozen rules)
  - `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 (W2.1 BLOCKED on the four base-only PRs, of which B3 is one)
- Code under review:
  - `gateway/app/services/capability/adapters/base.py`
  - `gateway/app/services/capability/adapters/__init__.py`
  - `tests/services/capability/adapters/test_adapter_error.py`

---

## 1. Scope

This evidence note covers ONLY B3 — the base-only error envelope
(`AdapterError` + closed `AdapterErrorCategory`) on `AdapterBase`.

In scope:

- adding `AdapterError` and `AdapterErrorCategory` to the existing
  base-only module `gateway/app/services/capability/adapters/base.py`;
- exporting them from the package `__init__`;
- adding minimum tests under `tests/services/capability/adapters/`;
- evidence + index write-back.

Out of scope (intentionally not done — see §5):

- B1 (auth / credential surface);
- B2 (retry / timeout / cancellation);
- B4 (construction-vs-invocation lifecycle);
- any provider SDK / client absorption;
- any provider adapter implementation;
- any runtime wiring;
- any Hot Follow / packet / contracts / workbench change.

---

## 2. What B3 added

### 2.1 `AdapterErrorCategory`

Closed string-enum of provider-agnostic failure shapes:

```
invalid_invocation
unavailable
timeout
cancelled
auth
rate_limited
upstream
internal
```

Categories describe *shape of failure*, not vendor codes. A future provider
adapter MUST translate native errors into one of these at its own boundary;
free-form provider codes belong only inside `AdapterError.details`.

### 2.2 `AdapterError`

Minimum, base-only exception envelope. Fields:

| Field | Type | Role |
|---|---|---|
| `category` | `AdapterErrorCategory` | mandatory; constrained to closed set |
| `message` | non-empty `str` | developer-facing diagnostic; not UI wording |
| `source` | `Optional[str]` | optional provider/source hint label |
| `retryable` | `Optional[bool]` | advisory hint only — does not authorise retry |
| `details` | read-only `Mapping[str, Any]` | structured payload; immutable view |

Discipline encoded:

- `AdapterError` subclasses `Exception` — raisable / catchable as a normal
  exception, no parallel hierarchy.
- `details` is wrapped in `MappingProxyType` and copied at construction time;
  external mutation cannot leak into the envelope.
- `to_dict()` returns the **frozen serialisation shape** with exactly the keys
  `{category, message, source, retryable, details}`.
- Validation rejects: unknown categories, empty/non-string messages, non-bool
  `retryable`, non-string `source`.

### 2.3 Package export

`AdapterError` and `AdapterErrorCategory` are re-exported from
`gateway.app.services.capability.adapters` and added to `__all__` so future
provider adapters (under `workers/adapters/<vendor>/`) can import them
without reaching into the `base` module.

### 2.4 Tests

`tests/services/capability/adapters/test_adapter_error.py` covers:

1. construction (minimum and full);
2. closed-set acceptance via enum and via raw string;
3. rejection of categories outside the closed set;
4. validation of `message` / `source` / `retryable` types;
5. raisable + catchable behaviour;
6. `details` immutability against external mutation;
7. **stable serialisation shape** (`to_dict()` exact key set + value mapping);
8. **closed category set is frozen** (assertion lists every value);
9. base module carries no provider/business imports
   (`swiftcraft`, `jellyfish`, `providers.`, `workers.adapters`, `hot_follow`,
   `tasks`, `openai`, `gemini`, `anthropic`);
10. `AdapterError` carries no truth/presenter/vendor-pin fields
    (`task_id`, `packet_id`, `line_id`, `state`, `primary_truth`,
    `user_message`, `presenter_text`, `vendor_id`, `model_id`, `engine_id`).

Run:

```
python3 -m pytest tests/services/capability/adapters/test_adapter_error.py -v
```

Result: 13 passed.

---

## 3. What B3 explicitly did NOT add

- No `AdapterCredentials` / `SecretResolver` / construction injection
  (deferred to B1).
- No retry policy, timeout shape, deadline plumbing, or cancellation
  primitives (deferred to B2).
- No `__init__` lifecycle contract on `AdapterBase`, no I/O-at-construction
  ban beyond what already exists (deferred to B4).
- No provider-specific error code translation tables.
- No provider SDK / client / vendor adapter code.
- No mapping of `AdapterError` into `AdapterResult.advisories` at the call
  site — that promotion belongs to the (future) caller / runtime layer, not
  to the base envelope itself.
- No change to `AdapterInvocation` / `AdapterResult` / `AdapterBase` /
  capability-kind subclasses.
- No change to `gateway/app/services/packet/`, `tests/contracts/`,
  `tests/guardrails/`, `ops/env/`, Hot Follow code, frontend, or workbench.
- No re-opening of W2 admission Phase A–E governance.

---

## 4. Boundary verification

Per W2.1 directive §6 B3 acceptance:

| Check | Result |
|---|---|
| `AdapterError` exists as base-only authority | Pass — defined alongside `AdapterBase` in `base.py` |
| Field/shape clearly defined and tested | Pass — frozen `to_dict()` key set + value-shape assertions |
| No provider code introduced | Pass — guarded by `test_base_module_has_no_provider_or_business_imports` |
| No business / runtime truth added | Pass — guarded by `test_adapter_error_carries_no_truth_or_presenter_fields`; no truth-write path; no state semantics |
| `AdapterResult.advisories` route preserved as the truth-safe surface | Pass — `AdapterError` is **advisory-shaped**, never artefact-shaped (W2 admission Phase C lifecycle review §3.3) |
| Reviewable as a single isolated PR | Pass — change is local to `base.py` + `__init__.py` + one new test file + this evidence note + index entry |
| Donor-free | Pass — only stdlib + existing `gateway.app.services.packet.envelope` import |
| Side-effect-free import | Pass — only class/enum definitions; no I/O |

---

## 5. Remaining blockers after B3

W2.1 Provider Absorption Wave remains BLOCKED. Outstanding base-only PRs
(per W2 admission Phase C lifecycle review §5 and W2.1 directive §9):

1. **B1 — auth / credential surface** (not started)
2. **B2 — retry / timeout / cancellation** (not started)
3. **B4 — construction-vs-invocation lifecycle** (not started)

After all four (B1–B4) are green and architect + reviewer signoff is
recorded, the first W2.1 Provider PR may open. None of B1 / B2 / B4 may be
bundled with a provider absorption PR (W2 admission Phase C lifecycle
review §4.1).

---

## 6. Next handoff

- **Architect** — judge whether B3's field set (`category`, `message`,
  `source`, `retryable`, `details`), the closed `AdapterErrorCategory` set,
  and the `to_dict()` shape are sufficient and not over-designed; signoff
  before B1 starts.
- **Reviewer** — close B3 as a single PR; verify no scope leak into B1 /
  B2 / B4 and no Hot Follow / packet / contracts / frontend touch.
- **Engineering** — do NOT begin B1 / B2 / B4 until B3 is signed off.
