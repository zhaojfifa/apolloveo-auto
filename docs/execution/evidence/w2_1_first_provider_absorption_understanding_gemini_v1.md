# W2.1 First Provider Absorption — UnderstandingAdapter ← Gemini text translate (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **W2.1 First Provider Absorption** — first (and only) provider PR
- Donor row: A-03 (`backend/app/utils/translate_gemini.py` → `gateway/app/services/providers/gemini/translate.py`) per `docs/donor/swiftcraft_capability_mapping_v1.md` §2.2
- Donor commit pin: inherits W2 admission pin `62b6da0` (no donor drift since W1; recorded explicitly in mapping §0)
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_First_Provider_Absorption_Wave_指挥单_v1.md` §2.2 (red lines), §4 (scope freeze: one provider, one adapter, one PR), §5 (recommend understanding/text), §7.P1/P2 (acceptance), §8 (forbidden surface), §11 (总控口令)
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md` §6 B1–B4 (frozen base-only surfaces)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §3.5, §5 (lifecycle freeze)
  - `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 (W2.1 unblock criteria)
  - B1 evidence: `docs/execution/evidence/w2_1_b1_adapter_credential_surface_v1.md`
  - B2 evidence: `docs/execution/evidence/w2_1_b2_adapter_execution_context_v1.md`
  - B3 evidence: `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md`
  - B4 evidence: `docs/execution/evidence/w2_1_b4_adapter_lifecycle_boundary_v1.md`
  - `ops/env/env_matrix_v1.md` §2.4 (canonical Gemini env names)
  - `ops/env/secret_loading_baseline_v1.md` §3.1 (no alias chain), §3.5 (fail-closed)
- Code under review:
  - `gateway/app/services/providers/gemini/__init__.py`
  - `gateway/app/services/providers/gemini/translate.py`
  - `gateway/app/services/workers/adapters/gemini/__init__.py`
  - `gateway/app/services/workers/adapters/gemini/understanding.py`
  - `gateway/app/services/workers/secrets/__init__.py`
  - `gateway/app/services/workers/secrets/env_resolver.py`
  - `tests/services/providers/gemini/test_translate.py`
  - `tests/services/workers/adapters/gemini/test_understanding.py`
  - `tests/services/workers/secrets/test_env_resolver.py`

---

## 1. Scope

This evidence note covers the **first** W2.1 provider absorption PR.
Single Gemini text-translation provider client, bound through
`UnderstandingAdapter` only, behind the frozen B1–B4 AdapterBase
surfaces.

In scope:

- absorbing the donor `backend/app/utils/translate_gemini.py` capability
  as a side-effect-free provider client at
  `gateway/app/services/providers/gemini/translate.py` (donor row A-03);
- binding that client through `UnderstandingAdapter` at
  `gateway/app/services/workers/adapters/gemini/understanding.py`,
  mapping every provider-typed failure into the closed
  `AdapterErrorCategory` set;
- a minimal `EnvSecretResolver` shim at
  `gateway/app/services/workers/secrets/env_resolver.py` so the binding
  has a B1-compliant invocation-time secret resolver to consume; the
  shim is **not** a generic secret platform — its only job is to map
  the adapter's logical refs to canonical env names per
  `ops/env/secret_loading_baseline_v1.md` §3.1;
- focused tests for all three surfaces (67 new), plus combined
  regression with B1–B4 (92) and the W2 admission guardrails;
- evidence + index + execution-log + donor-mapping write-back.

Out of scope (intentionally not done — see §3, §6):

- a second provider, even as fallback (W2.1 wave §4.1 / §8);
- any other capability adapter binding — `SubtitlesAdapter`,
  `DubAdapter`, `AvatarAdapter`, `VideoGenAdapter`, `FaceSwapAdapter`,
  `PostProductionAdapter`, `PackAdapter` are all untouched;
- any change to `AdapterBase` shape (B1–B4 surfaces are unchanged);
- any runtime / router / registry / worker dispatch wiring — the
  binding is reachable only via direct construction;
- any packet / schema / contract / Hot Follow / workbench / frontend
  change;
- the donor's multi-stage retry / concise / strong-retry / per-segment
  retry / raw-save fallback cascade — that is business-layer policy
  and is explicitly NOT absorbed in this PR;
- any generic secret-platform expansion (vault / KMS / file / alias
  chain).

---

## 2. What this PR adds

### 2.1 Gemini text-translate provider client (donor A-03)

`gateway/app/services/providers/gemini/translate.py` exposes a single
class `GeminiTextTranslateClient` plus a frozen
`GeminiTextTranslateConfig`, request/segment/result dataclasses, and
the closed `GeminiTextTranslateErrorKind` set. The client:

- has **I/O-free construction** — `__init__` only stores the resolved
  `GeminiTextTranslateConfig` and builds an `httpx.Timeout`; no env
  reads, no socket, no logger binding;
- exposes a single `translate_segments(request, *, cancel_check=None,
  http_client_factory=None)` invocation surface — the only path that
  touches the network;
- maps every failure onto a small, provider-internal taxonomy
  (`INVALID_REQUEST` / `AUTH` / `RATE_LIMITED` / `TIMEOUT` / `CANCELLED`
  / `UPSTREAM` / `PROTOCOL`) raised as `GeminiTextTranslateError`;
- does **not** depend on `AdapterError` or any
  `gateway.app.services.capability.adapters.*` symbol — mapping into
  the provider-agnostic envelope is the binding's job;
- does **not** read `os.environ` / `os.getenv` anywhere — credentials
  arrive through the `GeminiTextTranslateConfig` value object;
- does **not** import `swiftcraft.*` or the donor module path —
  guarded by AST scan in `tests/services/providers/gemini/test_translate.py`;
- intentionally does **not** absorb the donor's concise / strong /
  per-segment retry cascade — that is business-layer fallback policy
  and would otherwise risk surfacing fallback as primary truth.

### 2.2 `UnderstandingAdapter` ← Gemini binding

`gateway/app/services/workers/adapters/gemini/understanding.py`
defines `GeminiUnderstandingAdapter`, a concrete `UnderstandingAdapter`
subclass. The binding:

- **B4 lifecycle**: construction stores only the injected
  `AdapterCredentials` and validates dependency shape — no
  `resolver.resolve(...)` call, no provider client construction, no
  env read, no I/O. `invoke` is the first reachable I/O surface;
- **B1 credential surface**: secrets flow exclusively through
  `self.credentials.resolver.resolve(SecretRef(...))` at invoke time,
  using the three logical refs `gemini.translate.{api_key, base_url,
  model}` (exported as `GEMINI_API_KEY_REF` / `GEMINI_BASE_URL_REF` /
  `GEMINI_MODEL_REF`). The recommended logical→env mapping is exposed
  as `GEMINI_LOGICAL_TO_ENV` and points to the canonical env names
  from `ops/env/env_matrix_v1.md` §2.4 only (no `GOOGLE_API_KEY`
  alias);
- **B2 execution context**: `AdapterExecutionContext.timeout_seconds`
  flows into `GeminiTextTranslateConfig.timeout_seconds`;
  `cancellation` is checked once before the network call and
  propagated as `cancel_check` into the provider client;
  `RetryPolicy` is **not** executed by the adapter (retry-loop
  ownership stays at the runtime / caller layer per B2 §3);
- **B3 error envelope**: `_map_provider_error` translates every
  `GeminiTextTranslateError` onto the closed
  `AdapterErrorCategory` set:

  | provider kind        | adapter category        | retryable |
  |----------------------|-------------------------|-----------|
  | `INVALID_REQUEST`    | `INVALID_INVOCATION`    | False     |
  | `AUTH`               | `AUTH`                  | False     |
  | `RATE_LIMITED`       | `RATE_LIMITED`          | True      |
  | `TIMEOUT`            | `TIMEOUT`               | True      |
  | `CANCELLED`          | `CANCELLED`             | False     |
  | `UPSTREAM`           | `UPSTREAM`              | True      |
  | `PROTOCOL`           | `UPSTREAM`              | False     |

  All raised `AdapterError`s carry `source='gemini.understanding'`
  and stash `provider_kind` (and HTTP `status` when present) inside
  the immutable `details` view only — no first-class vendor field;
- emits a result of provider-agnostic shape: `artefacts`
  carries `translated_segments` (in input index order) and
  `missing_indexes`; `advisories` carries a single
  `{"kind": "json_repair_used", "source": "gemini.understanding"}`
  entry only when the provider repair path was taken — never as
  primary truth (cf. W2 admission Phase A
  `test_fallback_never_primary_truth`).

### 2.3 `EnvSecretResolver` shim

`gateway/app/services/workers/secrets/env_resolver.py` is the
**minimal** invocation-time resolver the binding consumes. It:

- subclasses `SecretResolver` from the AdapterBase package;
- accepts only a frozen `Mapping[str, str]` of logical→env names at
  construction; construction does **not** read env;
- on `resolve(...)` reads `os.environ`, strips, and returns `None` for
  missing/empty values — fail-closed semantics belong to the caller
  per `secret_loading_baseline_v1.md` §3.5;
- carries no logger, no cache, no platform expansion, no alias chain
  (the test `test_resolver_does_not_alias_logical_keys` enforces this
  with a `GOOGLE_API_KEY` decoy).

The shim is intentionally placed under
`gateway/app/services/workers/secrets/`, **outside**
`gateway/app/services/capability/adapters/`, so the AdapterBase
package never grows a dependency on env loaders (B1 boundary).

### 2.4 Tests (67 new)

Three focused test files, all hermetic (no real network, no real
filesystem outside `tmpdir`, no real env beyond `monkeypatch`):

- `tests/services/providers/gemini/test_translate.py` — 23 tests:
  config validation, I/O-free construction, AST import-time
  side-effect scan, happy path with stubbed `httpx.Client`,
  cooperative cancellation, fenced-JSON repair flag, missing-index
  reporting, status-code → kind mapping (7 cases),
  timeout/transport error mapping, protocol failures, no-`AdapterError`
  / no-donor-import boundary;
- `tests/services/workers/adapters/gemini/test_understanding.py` —
  31 tests: subclass shape, invoke signature matches base, B4
  construction-vs-invocation lifecycle, B1 credential resolution at
  invoke time only, missing-key auth failure, default base/model,
  B2 timeout propagation, cancellation pre-check + in-flight cancel,
  retry-policy NOT executed by adapter, B3 mapping for all 7
  provider kinds, invocation validation (capability_kind /
  segments / target_lang / segment shape), absorption boundary
  (no packet / runtime / Hot Follow leak, no env read, no second
  adapter binding via AST class-def scan);
- `tests/services/workers/secrets/test_env_resolver.py` — 13 tests:
  abc subclass check, no env read at construction, mapping
  validation, read-only mapping view, invoke-time resolution,
  missing/empty/whitespace values fail closed, value strip,
  `SecretRef` type check, no alias chain, no provider/packet
  imports.

Run:

```
python3 -m pytest \
  tests/services/capability/adapters \
  tests/services/providers \
  tests/services/workers \
  tests/guardrails -q
```

Result: **159 passed** (B1: 21, B2: 31, B3: 13, B4: 20, provider:
23, binding: 31, resolver: 13, guardrails: 7 — see §5 for the
breakdown).

---

## 3. What this PR explicitly did NOT add

- No second provider, no fallback provider, no provider registry.
- No other capability adapter binding (`SubtitlesAdapter`,
  `DubAdapter`, `AvatarAdapter`, `VideoGenAdapter`,
  `FaceSwapAdapter`, `PostProductionAdapter`, `PackAdapter`
  untouched).
- No change to `AdapterBase` / `AdapterError` /
  `AdapterErrorCategory` / `AdapterCredentials` / `SecretRef` /
  `SecretResolver` / `AdapterExecutionContext` / `RetryPolicy` /
  `CancellationToken` / `AdapterInvocation` / `AdapterResult`
  shapes (B1–B4 frozen).
- No runtime wiring: no router entry, no worker dispatch, no
  registry registration, no scheduled task, no env-driven autoload.
  The binding is reachable only via direct construction by a future
  caller.
- No provider-pin field on packet / schema / contract / surface;
  no `vendor_id` / `model_id` / `engine_id` written into the
  packet; capability-kind set in `gateway/app/services/packet/envelope.py`
  is unchanged.
- No Hot Follow code touched. No `gateway/app/services/runtime/`
  edits. No `gateway/app/services/packet/` edits. No
  `tests/contracts/` or `tests/guardrails/` edits.
- No frontend / workbench / preview / panel edit.
- No env var read inside `capability/adapters/`. No env var read
  inside `providers/gemini/`. Env reads are confined to
  `EnvSecretResolver.resolve` at invoke time.
- No alias chain (`GOOGLE_API_KEY` etc.) — the resolver reads only
  the canonical env names from `ops/env/env_matrix_v1.md` §2.4.
- No donor concise / strong-retry / per-segment retry / raw-save
  cascade. No business-layer truth promotion of fallback output.
- No re-pinning of donor commit. The W2.1 wave inherits the W2
  admission pin `62b6da0` (donor mapping §0 row 3 "inherits W2
  admission pin unless re-pinned" — donor HEAD has not moved).

---

## 4. Boundary verification (per W2.1 directive §7.P1 / §7.P2 / §11)

| Check | Result |
|---|---|
| Single provider absorbed | Pass — only `gateway/app/services/providers/gemini/translate.py` (donor A-03). |
| Single adapter binding | Pass — only `GeminiUnderstandingAdapter`; AST class-def scan in `test_binding_only_targets_understanding_capability`. |
| AdapterBase shape unchanged | Pass — `gateway/app/services/capability/adapters/base.py` and `__init__.py` are unchanged in this PR; B1–B4 evidence files are not modified. |
| Provider error → `AdapterError` mapping | Pass — `_map_provider_error` covers all 7 provider kinds; verified by parametrised test (`test_provider_errors_map_to_closed_adapter_categories`). |
| Credentials via `AdapterCredentials` / `SecretResolver` | Pass — `_resolve_config` is the only credential consumer; verified by `test_invoke_resolves_credentials_at_invocation_time`. |
| Timeout / cancellation via `AdapterExecutionContext` | Pass — `test_timeout_seconds_flows_into_provider_config`, `test_cancellation_before_invoke_raises_cancelled`, `test_cancel_check_propagates_into_provider_call`. |
| Construction is I/O-free | Pass — `test_construction_is_io_free_and_does_not_resolve_secrets` (binding) + module-import AST scan (provider client) + `test_construction_does_not_read_env` (resolver). |
| Invoke is the first I/O surface | Pass — secret resolution and provider-client construction only happen inside `invoke`. |
| No fallback provider, no business fallback cascade | Pass — single `translate_segments` call per invoke; `RetryPolicy` not executed (`test_retry_policy_is_not_executed_by_adapter`). |
| Fallback never primary truth | Pass — `json_repair_used` advisory is emitted only via `AdapterResult.advisories`, not via `artefacts`. |
| No vendor pin in packet / surface / base | Pass — base / packet envelope / contracts unchanged in this PR. |
| Donor leak boundary intact | Pass — `swiftcraft` not imported anywhere in absorbed source; donor module path only mentioned in docstrings (excluded by `tests/guardrails/test_donor_leak_boundary.py::test_no_swiftcraft_string_in_python_source_outside_donor_docs` AST filter). |
| Hot Follow untouched | Pass — no edit under `gateway/app/services/hot_follow/` or related code paths. |
| Independent review / merge / rollback | Pass — change set is contained to `gateway/app/services/providers/gemini/`, `gateway/app/services/workers/adapters/gemini/`, `gateway/app/services/workers/secrets/`, three test files, this evidence note, the index entry, the execution log entry, and the donor mapping row update. |

---

## 5. Validation

Combined run:

```
python3 -m pytest \
  tests/services/capability/adapters \
  tests/services/providers \
  tests/services/workers \
  tests/guardrails -q
```

Result: **159 passed** (no skips, no warnings).

Breakdown:

- B1 credentials: 21 unchanged
- B2 execution context: 31 unchanged
- B3 error envelope: 13 unchanged
- B4 lifecycle: 20 unchanged
- W2 admission donor-leak guardrails: 3 unchanged
- W2 admission fallback-never-primary-truth guardrails: 2 unchanged
- W2 admission provider-leak guardrails: 2 unchanged
- **NEW** Gemini provider client: 23 passed
- **NEW** Gemini ↔ UnderstandingAdapter binding: 31 passed
- **NEW** EnvSecretResolver shim: 13 passed

No B1–B4 drift, no guardrail drift.

---

## 6. Remaining blockers after this PR

After this PR lands, the W2.1 wave's directive §11 sequencing is:

1. Architect signoff on the provider-absorption boundary
   (single provider, single adapter, single PR; B1–B4 surfaces
   unchanged; no fallback / packet / runtime / Hot Follow leak).
2. Reviewer signoff on the PR independently (merge gate; verifies
   no scope leak into Matrix Script line integration or W2.2 / W2.3
   territory).
3. Confirmation that `main` continues as the single authority
   baseline.

**Hard stop after this PR**: Engineering MUST NOT begin Matrix
Script first production line work, MUST NOT open W2.2 (Subtitles /
Dub) or W2.3 (Avatar / VideoGen / Storage), and MUST NOT add a
second provider, until architect + reviewer signoff is recorded
for this PR and W2.1 is closed.

---

## 7. Next handoff

- **Architect** — judge whether the absorption boundary is
  acceptable as the "first provider" baseline; in particular
  confirm:
  - the binding's `_map_provider_error` table is the right closure
    of provider failure shapes onto the B3 closed set (especially
    `PROTOCOL → UPSTREAM` with `retryable=False`);
  - placing `EnvSecretResolver` under
    `gateway/app/services/workers/secrets/` (outside
    `capability/adapters/`) is the right home for B1-compliant
    invocation-time secret resolvers;
  - leaving `RetryPolicy` execution to the (future) caller / runtime
    layer is acceptable for the first provider PR (consistent with
    B2 §3 boundary).
  Signoff before Matrix Script first production line work opens.
- **Reviewer** — close this PR as a single isolated PR; verify no
  scope leak into a second provider / packet / runtime / Hot Follow
  / frontend / workbench; verify B1–B4 surfaces are unchanged; verify
  donor mapping row A-03 has moved from `Not started` to `Absorbed`
  (with the binding scoped to `UnderstandingAdapter` only — the
  `+ SubtitlesAdapter` half of A-03's binding column is intentionally
  deferred).
- **Engineering** — do NOT start Matrix Script production-line work,
  W2.2, or W2.3, until architect + reviewer signoff is recorded
  here.
