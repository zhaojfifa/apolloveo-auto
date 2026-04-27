# W2.1 First Provider Absorption — Execution Log

Active execution log for the W2.1 First Provider Absorption Wave
(`docs/architecture/ApolloVeo_2.0_W2.1_First_Provider_Absorption_Wave_指挥单_v1.md`).

This wave is gated to **one provider, one adapter, one PR, one
evidence chain** (wave §4 / §11). The base-only B1–B4 surfaces frozen
in `docs/execution/W2_1_BASE_ONLY_ADAPTER_PREPARATION_LOG.md` are the
prerequisite for entries in this log.

---

## P1+P2 — UnderstandingAdapter ← Gemini text translate (donor A-03)

- Date: 2026-04-27
- Status: implementation green; awaiting architect + reviewer signoff
- Donor row: A-03 (`backend/app/utils/translate_gemini.py`); donor pin
  `62b6da0` (inherits W2 admission pin — donor HEAD has not moved
  since W1; pin recorded explicitly in
  `docs/donor/swiftcraft_capability_mapping_v1.md` §0).
- Evidence: `docs/execution/evidence/w2_1_first_provider_absorption_understanding_gemini_v1.md`
- Code:
  - `gateway/app/services/providers/gemini/__init__.py`
  - `gateway/app/services/providers/gemini/translate.py`
  - `gateway/app/services/workers/adapters/gemini/__init__.py`
  - `gateway/app/services/workers/adapters/gemini/understanding.py`
  - `gateway/app/services/workers/secrets/__init__.py`
  - `gateway/app/services/workers/secrets/env_resolver.py`
  - `tests/services/providers/gemini/test_translate.py` (23 tests, pass)
  - `tests/services/workers/adapters/gemini/test_understanding.py` (31 tests, pass)
  - `tests/services/workers/secrets/test_env_resolver.py` (13 tests, pass)
- What this PR adds:
  - Gemini text-translate provider client with I/O-free construction
    and a single `translate_segments(...)` invocation surface; closed
    `GeminiTextTranslateErrorKind` taxonomy raised as
    `GeminiTextTranslateError` (no dependency on `AdapterError`).
  - `GeminiUnderstandingAdapter`, a concrete `UnderstandingAdapter`
    binding that resolves credentials through
    `AdapterCredentials.resolver` at invoke time (B1), honours
    `AdapterExecutionContext.timeout_seconds` / `cancellation` (B2),
    maps every provider failure onto the closed
    `AdapterErrorCategory` set with `source='gemini.understanding'`
    (B3), and is I/O-free at construction (B4).
  - Minimal `EnvSecretResolver` shim (invocation-time resolve only;
    canonical env names only per
    `ops/env/secret_loading_baseline_v1.md` §3.1; no alias chain;
    fail-closed on missing/empty values per §3.5) placed under
    `gateway/app/services/workers/secrets/` so the AdapterBase
    package never grows a dependency on env loaders.
- What this PR does NOT add: no second provider, no fallback
  provider, no `SubtitlesAdapter` / `DubAdapter` / `AvatarAdapter` /
  `VideoGenAdapter` / `FaceSwapAdapter` / `PostProductionAdapter` /
  `PackAdapter` binding, no change to `AdapterBase` / B1–B4 frozen
  shapes, no runtime / router / registry / worker wiring, no packet
  / schema / contract / surface change, no Hot Follow / workbench /
  frontend touch, no donor concise / strong-retry / per-segment
  retry / raw-save cascade, no generic secret-platform expansion.
- Validation:
  `python3 -m pytest tests/services/capability/adapters tests/services/providers tests/services/workers tests/guardrails -q`
  → 159 passed (B1: 21 unchanged, B2: 31 unchanged, B3: 13 unchanged,
  B4: 20 unchanged, donor-leak / fallback-never-primary-truth /
  provider-leak guardrails: 7 unchanged, NEW provider client: 23,
  NEW binding: 31, NEW resolver shim: 13).
- Next handoff: architect signoff on the provider absorption
  boundary; reviewer closes this PR independently; `main` continues
  as the single authority baseline.

---

## W2.1 Provider Absorption gate

After this PR, donor row A-03 is `Absorbed` for the
`UnderstandingAdapter` half (the `SubtitlesAdapter` half is
intentionally deferred to a later wave per W2.1 wave §4.2). No second
provider has been opened. Matrix Script first production line work,
W2.2 (Subtitles / Dub), and W2.3 (Avatar / VideoGen / Storage) remain
**not started** per W2.1 wave §9 and §11 hard-stop. Engineering MUST
NOT start any of those until architect + reviewer signoff is recorded
on this PR and W2.1 closes.
