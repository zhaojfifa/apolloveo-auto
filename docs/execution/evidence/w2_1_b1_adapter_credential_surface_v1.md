# W2.1 Base-Only Adapter Preparation — B1: Auth / Credential Surface (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **W2.1 Base-Only Adapter Preparation** — B1 only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md` §4 (recommended order, B1 second), §6 B1 (boundary + acceptance)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §3.1, §4, §5 (gap definition + frozen rules)
  - `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 (W2.1 BLOCKED on the four base-only PRs, of which B1 is one)
  - `ops/env/env_matrix_v1.md`, `ops/env/secret_loading_baseline_v1.md` (Phase B canonical env / secret authority — frozen, not modified by B1)
- Code under review:
  - `gateway/app/services/capability/adapters/base.py`
  - `gateway/app/services/capability/adapters/__init__.py`
  - `tests/services/capability/adapters/test_adapter_credentials.py`

---

## 1. Scope

This evidence note covers ONLY B1 — the base-only auth / credential surface
on `AdapterBase` (`SecretRef`, `SecretResolver`, `AdapterCredentials`, plus
the construction-time injection point on `AdapterBase`).

In scope:

- adding `SecretRef`, `SecretResolver`, `AdapterCredentials` to the
  existing base-only module `gateway/app/services/capability/adapters/base.py`;
- adding a `__init__(*, credentials=None)` construction surface to
  `AdapterBase` that stores credentials without I/O and exposes them as
  a read-only `credentials` property;
- exporting the three new types from the package `__init__`;
- adding minimum tests under `tests/services/capability/adapters/`;
- evidence + index write-back.

Out of scope (intentionally not done — see §5):

- B2 (retry / timeout / cancellation);
- B4 (construction-vs-invocation lifecycle policy beyond bare storage);
- any concrete `SecretResolver` implementation (env-loader, vault client,
  KMS, file-backed loader);
- any provider SDK / client absorption;
- any provider adapter implementation;
- any runtime wiring;
- any change to `ops/env/env_matrix_v1.md` or
  `ops/env/secret_loading_baseline_v1.md`;
- any Hot Follow / packet / contracts / workbench / frontend change.

---

## 2. What B1 added

### 2.1 `SecretRef`

Frozen dataclass holding a logical, provider-agnostic secret handle:

| Field | Type | Role |
|---|---|---|
| `name` | non-empty `str` | adapter-defined logical key (NOT an env var name, NOT a vendor token id) |
| `purpose` | `Optional[str]` | optional human-readable annotation |

Discipline encoded:

- Validates `name` is a non-empty string at construction.
- Validates `purpose` is a string when set.
- Frozen — no mutation after construction.
- The base does not interpret `name` — mapping logical names to concrete
  sources (env, vault, KMS, file) is the resolver's job, not the base's.

### 2.2 `SecretResolver`

Abstract base class with a single abstract method:

```
resolve(ref: SecretRef) -> Optional[str]
```

Discipline encoded:

- `SecretResolver` is `abc.ABC`; instantiation without an override is a
  `TypeError` (test-enforced).
- The base ships **only the abstract surface** — no concrete subclass of
  `SecretResolver` exists inside `capability/adapters/` (test-enforced).
- Concrete resolvers will live in the runtime / ops layer in a later
  PR; the base never grows a direct dependency on env-loading code.
- Construction is side-effect-free; `resolve` MAY do I/O at invocation time.
- Fail-closed semantics belong to the caller per
  `ops/env/secret_loading_baseline_v1.md` §3.5.

### 2.3 `AdapterCredentials`

Frozen dataclass holding the injected resolver:

| Field | Type | Role |
|---|---|---|
| `resolver` | `SecretResolver` | the only field; an injected resolver instance |

Discipline encoded:

- Field set is exactly `{resolver}` (test-enforced; guards against silent shape drift).
- Validates `resolver` is a `SecretResolver` instance.
- Frozen — no mutation after construction.
- MUST NOT carry vendor / model / engine identifiers.
- MUST NOT carry resolved secret values; the value lives only inside
  `resolver.resolve(...)` calls at invocation time.
- MUST NOT carry env var names — those are resolver-internal.
- MUST NOT encode business / task / packet truth.

### 2.4 `AdapterBase.__init__`

A keyword-only `credentials: Optional[AdapterCredentials] = None`
construction surface, plus a read-only `credentials` property:

- Validates the argument is an `AdapterCredentials` instance when set.
- Performs **no I/O**; never calls `resolver.resolve(...)`.
- Does not mutate global state.
- Subclasses (vendor adapters in a later W2.1 wave) call
  `super().__init__(credentials=...)` to receive credentials in a
  consistent shape.
- Capability-kind subclasses (`UnderstandingAdapter`, `SubtitlesAdapter`,
  …) inherit unchanged — no override added.

### 2.5 Package exports

`SecretRef`, `SecretResolver`, `AdapterCredentials` are re-exported from
`gateway.app.services.capability.adapters` and added to `__all__` so a
future provider adapter (under `workers/adapters/<vendor>/`) can import
them without reaching into the `base` module.

### 2.6 Tests

`tests/services/capability/adapters/test_adapter_credentials.py` covers:

1. `SecretRef` construction (minimum and with purpose);
2. `SecretRef` rejects empty / non-string `name`;
3. `SecretRef` rejects non-string `purpose`;
4. `SecretRef` is frozen;
5. `SecretResolver` cannot be instantiated directly (abstract);
6. `SecretResolver` subclasses must implement `resolve`;
7. `SecretResolver` concrete subclass works as expected;
8. `AdapterCredentials` holds the injected resolver;
9. `AdapterCredentials` rejects non-resolver objects;
10. `AdapterCredentials` is frozen;
11. `AdapterCredentials` field set is stable (`{resolver}` only);
12. `AdapterBase.__init__` accepts `credentials=` kwarg;
13. `AdapterBase.credentials` defaults to `None`;
14. `AdapterBase.__init__` rejects non-`AdapterCredentials` objects;
15. `AdapterBase` construction does NOT call `resolver.resolve(...)`
    (no I/O at construction);
16. `AdapterBase.credentials` property is read-only;
17. **Base module import surface** — no provider / business / vendor /
    `os.getenv` imports introduced;
18. Credential surface carries **no truth / vendor / presenter / env_name /
    api_key / token fields**;
19. `SecretResolver` is shipped only as abstract in base — no concrete
    subclass exists inside `capability/adapters/`;
20. `AdapterCredentials` does not carry a resolved secret value field.

Run:

```
python3 -m pytest tests/services/capability/adapters/test_adapter_credentials.py -v
```

Result: 21 passed (combined with B3 suite: 34 passed).

---

## 3. What B1 explicitly did NOT add

- No concrete `SecretResolver` implementation. The base ships only the
  abstract surface; env / vault / KMS / file loaders belong outside the
  base.
- No retry policy, timeout shape, deadline plumbing, or cancellation
  primitives (deferred to B2).
- No broader construction-vs-invocation lifecycle policy beyond bare
  storage of the injected envelope (deferred to B4 — e.g. a hard
  guardrail forbidding all I/O at construction time).
- No change to `AdapterError` / `AdapterErrorCategory` (frozen by B3).
- No change to `AdapterInvocation` / `AdapterResult` / capability-kind
  subclasses.
- No env var names, no vendor names, no model names, no engine names
  encoded in the base.
- No change to `ops/env/env_matrix_v1.md`,
  `ops/env/secret_loading_baseline_v1.md`, or any Phase B artefact.
- No change to `gateway/app/services/packet/`, `tests/contracts/`,
  `tests/guardrails/`, Hot Follow code, frontend, or workbench.
- No re-opening of W2 admission Phase A–E governance.

---

## 4. Boundary verification

Per W2.1 directive §6 B1 acceptance:

| Check | Result |
|---|---|
| Auth / credential surface exists as base-only authority | Pass — `SecretRef`, `SecretResolver`, `AdapterCredentials` defined in `base.py`; injected via `AdapterBase.__init__` |
| Surface is provider-agnostic | Pass — no vendor / model / engine / env-name fields; resolver is abstract; mapping logical→concrete is resolver-internal |
| Surface is testable | Pass — 21 tests under `tests/services/capability/adapters/test_adapter_credentials.py` |
| No provider-specific dependency | Pass — guarded by `test_b1_does_not_widen_base_module_import_surface` (forbids `swiftcraft`, `jellyfish`, `providers.`, `workers.adapters`, `hot_follow`, `tasks`, `openai`, `gemini`, `anthropic`, `os.getenv`) |
| No business / runtime truth leakage | Pass — guarded by `test_credential_surface_carries_no_truth_or_vendor_fields`; no truth-write path; no state semantics |
| Compatible with frozen env / secret baseline | Pass — `ops/env/env_matrix_v1.md` and `ops/env/secret_loading_baseline_v1.md` unchanged; resolver indirection lets future ops-layer code consume those baselines without coupling the base to env names |
| Existing adapter closed set preserved | Pass — capability-kind subclasses inherit unchanged; `__init_subclass__` `capability_kind` validation untouched |
| No real secret loading implementation | Pass — `SecretResolver` is abstract; no concrete subclass shipped in base (test-enforced) |
| Reviewable as a single isolated PR | Pass — change is local to `base.py` + `__init__.py` + one new test file + this evidence note + index entry + execution log |
| Donor-free | Pass — only stdlib imports added (`typing`, `dataclasses`, `abc`, `enum`, `types` — all already in use) |
| Side-effect-free import | Pass — only class / dataclass definitions; no I/O |

---

## 5. Remaining blockers after B1

W2.1 Provider Absorption Wave remains BLOCKED. Outstanding base-only PRs
(per W2 admission Phase C lifecycle review §5 and W2.1 directive §9):

1. **B2 — retry / timeout / cancellation** (not started)
2. **B4 — construction-vs-invocation lifecycle** (not started)

(B3 — error envelope — is implementation green and awaits architect +
reviewer signoff per `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md`.)

After all four (B1–B4) are green and architect + reviewer signoff is
recorded, the first W2.1 Provider PR may open. None of B2 / B4 may be
bundled with a provider absorption PR (W2 admission Phase C lifecycle
review §4.1).

---

## 6. Next handoff

- **Architect** — judge whether B1's surface (`SecretRef`,
  `SecretResolver`, `AdapterCredentials`, `AdapterBase.__init__`'s
  credentials kwarg) is sufficient and not over-designed; in particular
  confirm that deferring the I/O-at-construction guardrail to B4 is
  acceptable. Signoff before B2 starts.
- **Reviewer** — close B1 as a single PR; verify no scope leak into B2 /
  B4 and no Hot Follow / packet / contracts / frontend touch; verify
  `ops/env/*` artefacts unchanged.
- **Engineering** — do NOT begin B2 / B4 until B1 is signed off; do NOT
  start any W2.1 provider absorption.
