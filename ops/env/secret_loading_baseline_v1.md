# ApolloVeo W2 Admission — Provider Secret Loading Baseline v1

- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase B
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase B
  - `ops/env/env_matrix_v1.md` (canonical key registry)
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.2 R1 (provider clients carry
    side effects), R6 (compliance / cost surface)

## 1. Purpose

Define the single, reviewable pattern that every W2 provider client must
follow when consuming a secret declared in `env_matrix_v1.md`. This file
does NOT introduce code; it constrains how the W2.1+ provider PRs are
allowed to consume env values when they land.

## 2. Scope

Applies to provider clients under `gateway/app/services/providers/**` (W2
target zone) and to any future `gateway/adapters/<provider>_*.py` files that
are absorbed under `AdapterBase`. Does NOT apply to:

- existing W1 helpers (`gateway/app/services/media/`) — closed.
- platform infrastructure (auth, db, storage) — those existing
  `os.getenv` call sites are documented in `env_matrix_v1.md` and frozen
  unless a separate PR proposes change.

## 3. Canonical loading pattern

Every W2 provider secret read MUST satisfy all of the following:

1. **Canonical name only.** Read the canonical key listed in
   `env_matrix_v1.md`. Aliases (e.g. `GOOGLE_API_KEY` for `GEMINI_API_KEY`,
   the `R2_*_ID` family) are read-only and MUST NOT be referenced in new
   provider code. New code reads the canonical name; the alias chain is a
   frozen back-compat surface in the existing platform-layer files only.
2. **No literal default for secrets.** `os.getenv("PROVIDER_KEY")` only.
   `os.getenv("PROVIDER_KEY", "<literal>")` for a secret is forbidden — a
   literal default is either dead code (never used) or worse, an embedded
   token. Use `None` and fail closed at the call site.
3. **Non-secret tuning may have defaults.** Tuning knobs (timeouts, model
   names, base URLs) may use `os.getenv("KEY", "<safe default>")`; the
   matrix marks which keys are non-secret.
4. **Single read per process boundary.** A provider client reads its env
   keys once at module import (or via a cached factory) and surfaces a
   typed config object. Per-call `os.getenv` for the same key is forbidden
   — it makes mocking and cache-invalidation harder.
5. **Fail closed.** If a required secret is absent and no degraded path
   is documented in `env_matrix_v1.md`, the provider MUST raise at call
   time with a structured error envelope, not silently fall back to a
   different provider or to advisory-truth output.
6. **No request-time secret echoing.** Logged messages, error envelopes,
   and observability metadata MUST NOT include the secret value (or any
   prefix longer than 4 characters of it). Names of keys may be logged.
7. **Test isolation.** Provider unit tests MUST monkeypatch the network
   layer (or the provider SDK's transport) — they MUST NOT depend on a
   live provider key being present in the test environment.

## 4. Hardcoded-token / hardcoded-key rule (binding)

Restated from `env_matrix_v1.md` §5 for emphasis; both files are
authoritative:

- No secret value (token, API key, signing secret, credential pair) may be
  committed to the repository in any form: source, fixtures, docs,
  comments, sample env files, render descriptors, or test data.
- `os.getenv("KEY", "<value>")` where `<value>` is a real or
  realistic-looking token is forbidden.
- Detected violations are treated as security incidents — the leaked key
  must be rotated regardless of whether the commit was reverted.

## 5. PR checklist for W2 provider absorption

When a W2.1+ PR opens, the author MUST confirm:

- [ ] Every provider env read is from a key listed in `env_matrix_v1.md`.
- [ ] If a new key is required, this PR also amends `env_matrix_v1.md`.
- [ ] No literal default is supplied for any secret key.
- [ ] No alias key is read from new code.
- [ ] Tests do not require live provider keys.
- [ ] Logs / error envelopes do not include the secret value.
- [ ] The provider fails closed when required secrets are absent.

The reviewer enforces this list before merge. Failures are returned, not
fixed inline.

## 6. Future enforcement (not part of this wave)

A guardrail test that scans `gateway/app/services/providers/**` for
`os.getenv("...", "<non-empty literal>")` patterns on keys in the
secret-marked subset of `env_matrix_v1.md` is planned but not authored
here — Phase B is docs/evidence only. The test will be authored alongside
the first W2.1 provider absorption PR, in `tests/guardrails/`.

## 7. Out of scope for this wave

- No provider client code added or modified.
- No new `tests/guardrails/` tests added.
- No changes to existing platform `os.getenv` call sites listed in
  `env_matrix_v1.md`.
- No deploy-pipeline / `render.yaml` authorship.
