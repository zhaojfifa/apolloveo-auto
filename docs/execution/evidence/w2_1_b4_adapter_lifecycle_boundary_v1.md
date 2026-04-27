# W2.1 Base-Only Adapter Preparation — B4: Construction-vs-Invocation Lifecycle (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **W2.1 Base-Only Adapter Preparation** — B4 only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md` §4 (recommended order, B4 fourth), §6 B4 (boundary + acceptance)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §3.5, §4, §5 (gap definition + frozen rules — "AdapterBase MUST forbid I/O at construction; first I/O is reachable only via `invoke`")
  - `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 (W2.1 BLOCKED on the four base-only PRs, of which B4 is the last)
  - B1 evidence: `docs/execution/evidence/w2_1_b1_adapter_credential_surface_v1.md` (frozen credential surface)
  - B2 evidence: `docs/execution/evidence/w2_1_b2_adapter_execution_context_v1.md` (frozen execution control surface)
  - B3 evidence: `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md` (frozen error envelope)
- Code under review:
  - `gateway/app/services/capability/adapters/base.py`
  - `tests/services/capability/adapters/test_adapter_lifecycle.py`

---

## 1. Scope

This evidence note covers ONLY B4 — freezing the construction-vs-invocation
lifecycle boundary on `AdapterBase`.

In scope:

- consolidating the construction-vs-invocation lifecycle policy as a
  single, authoritative section in the `AdapterBase` class docstring;
- restating the I/O-free contract on `AdapterBase.__init__` and the
  "invoke is the first I/O surface" contract on `AdapterBase.invoke`,
  removing the "deferred to B4" placeholders left by B1 / B2;
- adding a dedicated test surface
  (`tests/services/capability/adapters/test_adapter_lifecycle.py`, 20
  tests) that enforces the boundary;
- evidence + index + execution-log write-back.

Out of scope (intentionally not done — see §3, §5):

- any new dataclass / abstract class on the base (B1 / B2 / B3 already
  ship the construction-time and invocation-time envelopes);
- any concrete `SecretResolver` or `CancellationToken` implementation;
- any provider SDK / client absorption;
- any provider adapter implementation;
- any runtime wiring;
- any change to `ops/env/*`, `gateway/app/services/packet/`,
  `tests/contracts/`, `tests/guardrails/`, Hot Follow code, frontend,
  or workbench;
- any change to the B1 (credentials), B2 (execution context), or B3
  (error envelope) frozen field shapes.

---

## 2. What B4 added

### 2.1 Frozen lifecycle policy on `AdapterBase`

The class docstring now carries a single, authoritative
"Construction-vs-invocation lifecycle (B4 — frozen)" section that
enumerates:

**Construction time (`__init__`) — allowed:**

- accepting and storing the injected `AdapterCredentials` envelope (B1)
  on a private slot, exposed read-only via `credentials`;
- type validation of injected dependencies (raise `TypeError` /
  `ValueError` on shape violations);
- pure assignment to instance state derived from the constructor
  arguments only.

**Construction time — forbidden:**

- I/O of any kind (network / disk / env / sleep / scheduler / timer /
  database / queue);
- calling `credentials.resolver.resolve(...)` (secret resolution is
  invocation-time only);
- starting timers, spawning background work, polling cancellation;
- provider-specific initialisation (SDK client construction, auth
  handshake, capability probe);
- reading or writing any business / packet truth.

**Invocation time (`invoke`) — allowed:**

- the first reachable I/O point of an adapter;
- calling `self.credentials.resolver.resolve(...)` (B1);
- honouring the injected `AdapterExecutionContext` (B2)
  (`timeout_seconds` / `cancellation` / `retry`);
- raising `AdapterError` (B3) with a closed `AdapterErrorCategory` on
  failure.

**Module / import time:**

- import is side-effect-free; `invoke` is the only path that reaches
  I/O.

The `__init__` and `invoke` docstrings are updated to point at this
single source of truth and to drop the B1 / B2 "deferred to the B4 PR"
placeholders.

### 2.2 No new code surface

B4 introduces no new dataclass, abstract class, public method, or
exported symbol. The construction-time envelope (`AdapterCredentials`,
B1) and invocation-time envelopes (`AdapterInvocation` /
`AdapterExecutionContext`, B0/B2) and error envelope (`AdapterError`,
B3) are sufficient; B4's job is to *freeze* the boundary between
construction and invocation, not to widen the surface.

This is intentional and matches the W2 admission lifecycle review §3.5
resolution ("forbid I/O at construction") and the W2.1 directive §6 B4
acceptance ("不偷渡 provider-specific 初始化逻辑 / 不在 import 时做 I/O").

### 2.3 Tests

`tests/services/capability/adapters/test_adapter_lifecycle.py` adds 20
tests in five groups:

**Construction-time allowed state (5):**

1. construction stores `AdapterCredentials` without calling
   `resolver.resolve(...)`;
2. omitted `credentials` defaults to `None`;
3. `credentials` is keyword-only (positional construction is rejected);
4. construction parameter set is exactly `{self, credentials}` (guards
   against silent surface drift);
5. construction-time instance state on the base is exactly
   `{_credentials}`.

**Construction-time forbidden behaviours (4):**

6. repeated construction never triggers resolver I/O;
7. constructing an adapter (and constructing an
   `AdapterExecutionContext` with a cancellation token) never polls
   the token;
8. construction rejects non-`AdapterCredentials` dependencies;
9. construction does not accept invocation-time arguments
   (`invocation`, `context`).

**Invocation-time boundary (4):**

10. `AdapterBase.__abstractmethods__ == {"invoke"}` — `invoke` is the
    only abstract surface (the only first-I/O entry);
11. `invoke` signature carries `(self, invocation, *, context=None)`
    and `context` is keyword-only with default `None`;
12. invocation does not mutate construction-time `credentials`;
13. invocation may raise `AdapterError` from the closed
    `AdapterErrorCategory` set (B3 is the only error contract).

**Module / import-time boundary (2):**

14. re-importing `base` is side-effect-free; AST check forbids
    top-level imports of I/O-capable modules (`socket`, `ssl`, `http`,
    `urllib`, `urllib3`, `requests`, `httpx`, `aiohttp`, `asyncio`,
    `trio`, `anyio`, `subprocess`, `threading`, `multiprocessing`,
    `sqlite3`, `pathlib`);
15. no module-level I/O calls (`open(...)`, `eval(...)`, `exec(...)`,
    `*.getenv(...)`, `*.system(...)`, `*.sleep(...)`, `*.popen(...)`).

**No provider-specific initialisation (2):**

16. base module source contains no provider / SDK / vendor token
    substrings (`swiftcraft`, `jellyfish`, `providers.`,
    `workers.adapters`, `hot_follow`, `openai`, `gemini`, `anthropic`,
    `google.cloud`, `boto3`, `azure.`, `client(`, `api_key`,
    `access_token`, `bearer `);
17. capability-kind subclasses (`UnderstandingAdapter`,
    `SubtitlesAdapter`, `DubAdapter`, `VideoGenAdapter`,
    `AvatarAdapter`, `FaceSwapAdapter`, `PostProductionAdapter`,
    `PackAdapter`) inherit `AdapterBase.__init__` directly and do not
    override the construction surface.

**Compatibility with B1 / B2 / B3 frozen surfaces (3):**

18. B4 does not widen the B1 surface (`AdapterCredentials.resolver`,
    `SecretRef.{name, purpose}`, `SecretResolver.__abstractmethods__`);
19. B4 does not widen the B2 surface
    (`AdapterExecutionContext.{timeout_seconds, cancellation, retry}`,
    `RetryPolicy.{max_attempts, initial_backoff_seconds,
    max_backoff_seconds, backoff_multiplier}`,
    `CancellationToken.__abstractmethods__`);
20. B4 does not widen the B3 surface (`AdapterError.to_dict()` keys
    `{category, message, source, retryable, details}`; closed
    `AdapterErrorCategory` set unchanged).

Run:

```
python3 -m pytest tests/services/capability/adapters/ tests/guardrails -v
```

Result: 92 passed (B4: 20 new, B2: 31 unchanged, B1: 21 unchanged, B3:
13 unchanged, guardrails: 7 unchanged).

---

## 3. What B4 explicitly did NOT add

- No new dataclass, abstract class, public method, or exported symbol.
- No concrete `SecretResolver` / `CancellationToken` implementation.
- No retry-loop / scheduler / timer plumbing.
- No provider SDK / client absorption.
- No provider adapter implementation.
- No runtime wiring / worker binding / line binding.
- No business-layer fallback / truth-write path.
- No change to B1 (credential surface), B2 (execution context), or
  B3 (error envelope) frozen field shapes.
- No change to `AdapterInvocation` / `AdapterResult` /
  capability-kind subclasses.
- No env var names, vendor names, model names, or engine names encoded
  in the base.
- No change to `ops/env/*`, `gateway/app/services/packet/`,
  `tests/contracts/`, `tests/guardrails/`, Hot Follow code, frontend,
  or workbench.
- No re-opening of W2 admission Phase A–E governance.

---

## 4. Boundary verification

Per W2.1 directive §6 B4 acceptance:

| Check | Result |
|---|---|
| construction-vs-invocation 责任边界明确 | Pass — `AdapterBase` class docstring carries the frozen lifecycle section; `__init__` and `invoke` docstrings reference it as the single source of truth |
| 不在 import 时做 I/O | Pass — guarded by `test_base_module_import_is_side_effect_free` (AST check bans top-level imports of `socket`, `ssl`, `http`, `urllib`, `urllib3`, `requests`, `httpx`, `aiohttp`, `asyncio`, `trio`, `anyio`, `subprocess`, `threading`, `multiprocessing`, `sqlite3`, `pathlib`) and `test_base_module_has_no_module_level_io_calls` (AST check bans top-level `open(...)`, `*.getenv(...)`, `*.system(...)`, `*.sleep(...)`, `*.popen(...)`, `eval(...)`, `exec(...)`) |
| 不偷渡 provider-specific 初始化逻辑 | Pass — guarded by `test_base_module_has_no_provider_specific_initialisation` (substring ban list) and `test_kind_subclasses_do_not_override_construction` (capability-kind subclasses inherit `AdapterBase.__init__` directly) |
| 有最小测试与 evidence | Pass — 20 tests under `tests/services/capability/adapters/test_adapter_lifecycle.py` and this evidence note |
| Reviewable as a single isolated PR | Pass — change is local to `base.py` (docstring-only) + one new test file + this evidence note + index entry + execution log |
| Donor-free | Pass — base module imports nothing donor-derived; verified by AST + substring checks |
| B1 / B2 / B3 surfaces preserved | Pass — guarded by three dedicated compatibility tests |
| Provider-agnostic | Pass — no vendor / model / engine identifier appears in the lifecycle policy or tests |

---

## 5. What B1–B4 now freeze (taken together)

After B4, the `AdapterBase` surface is fully prepared for the first
W2.1 provider absorption PR:

- **B1** — `SecretRef`, `SecretResolver`, `AdapterCredentials`, plus
  `AdapterBase.__init__(*, credentials=None)` construction-time
  injection point. (Frozen.)
- **B2** — `CancellationToken`, `RetryPolicy`,
  `AdapterExecutionContext`, plus
  `AdapterBase.invoke(invocation, *, context=None)` execution control
  entry. (Frozen.)
- **B3** — closed `AdapterErrorCategory` set, advisory-shaped
  `AdapterError` envelope with frozen `{category, message, source,
  retryable, details}` keys and immutable `details`. (Frozen.)
- **B4** — explicit construction-vs-invocation lifecycle boundary:
  construction is I/O-free; invocation is the first I/O surface; module
  import is side-effect-free; no provider-specific initialisation in
  the base. (Frozen.)

The four base-only PRs B1–B4 are implementation-complete. Provider
absorption is still NOT started in this wave.

---

## 6. Remaining blockers after B4

After B4 lands, the remaining gates before the first W2.1 Provider
Absorption PR may open are governance-only (W2.1 directive §9):

1. architect signoff on B4 boundary;
2. reviewer signoff on B4 PR (closed as a single isolated PR);
3. confirmation that `main` continues as the single authority baseline.

No further base-only PR is required before W2.1 Provider Absorption.
The W2.2 (Subtitles / Dub) and W2.3 (Avatar / VideoGen / Storage)
waves remain out of scope.

---

## 7. Next handoff

- **Architect** — judge whether B4's lifecycle policy is sufficient
  and not over-designed; in particular confirm that:
  - consolidating the policy in the `AdapterBase` class docstring
    (rather than introducing a new abstract hook or class attribute)
    is acceptable as the "minimum implementation" the directive asks
    for;
  - test-level enforcement (AST + substring + parameter-set + state
    checks) is the right enforcement layer for "no I/O at construction
    or import" given the base intentionally has no runtime executor;
  - leaving the construction-time / invocation-time policy unenforced
    *inside* vendor adapters (i.e. enforcing it only at the base + at
    PR review) is acceptable.
  Signoff before W2.1 Provider Absorption opens.
- **Reviewer** — close B4 as a single PR; verify no scope leak into
  provider absorption; verify no Hot Follow / packet / contracts /
  frontend touch; verify B1 / B2 / B3 surfaces are unchanged.
- **Engineering** — do NOT start any W2.1 provider absorption until
  architect + reviewer signoff is recorded for the full B1–B4 set.
