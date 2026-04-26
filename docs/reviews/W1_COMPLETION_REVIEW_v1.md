# P2 W1 Completion Review v1 — Media Helpers Absorption

- Date: 2026-04-26
- Reviewer role: ApolloVeo L5 Chief Architect & Reviewer
- Scope: P2 Wave 1 closure (Media helpers M-01..M-05). **No W2/Provider work in scope.**
- Authority:
  - `docs/donor/swiftcraft_donor_boundary_v1.md`
  - `docs/donor/swiftcraft_capability_mapping_v1.md`
  - `docs/adr/ADR-donor-swiftcraft-capability-only.md`
- Evidence:
  - `docs/execution/evidence/donor_absorption_w1_m04_m05_v1.md`
  - `docs/execution/evidence/donor_absorption_w1_m01_m02_m03_v1.md`
- Commits reviewed: `dcb49ca` (M-04/M-05), `09ec391` (M-01/M-02/M-03)
- Donor commit pin (W1): `62b6da0`

---

## 1. Status reconciliation

Mapping doc `docs/donor/swiftcraft_capability_mapping_v1.md` §2.1 was already
flipped at code-merge time (commit `09ec391`); no further status edit is
required. All five Media-helper rows are confirmed `Absorbed`:

| Row | Apollo target | Status | Verified by |
|---|---|---|---|
| M-01 | `gateway/app/services/media/ffmpeg_localization.py` | Absorbed | code present, attribution header present, tests pass |
| M-02 | `gateway/app/services/media/media_helpers.py` | Absorbed | severance assertion test passes |
| M-03 | `gateway/app/services/media/subtitle_builder.py` | Absorbed | code present, plain-text SRT path preserved |
| M-04 | `gateway/app/services/media/serialize.py` | Absorbed | byte-equivalent, 5 unit tests |
| M-05 | `gateway/app/services/media/zh_normalize.py` | Absorbed | guard-compat test pins CJK detection |

The mapping doc, evidence files, and Evidence Index v1 are now mutually
consistent.

---

## 2. W1 closure assessment

### 2.1 Boundary cleanliness — **PASS**

- Static check on `gateway/app/services/media/*.py` shows **only stdlib imports**
  (`json`, `os`, `re`, `shlex`, `signal`, `subprocess`, `time`, `pathlib`,
  `typing`, `dataclasses`, `shutil`, `uuid`, `unicodedata`). Zero references
  to `app.*`, `swiftcraft.*`, or any donor task / queue / model package.
- The single sensitive cut — donor's `from app.models.task import InputMetadata`
  in M-02 — is severed correctly. Replacement is a local
  `MediaProbeResult` dataclass; behavior preserved; no donor truth model
  enters Apollo. The cut is **legal** under boundary §3.1 + Wave-1 red-line
  (capability code only, no truth model coupling).
- The severance is enforced by an actual test
  (`test_media_helpers_donor.py::test_no_donor_task_model_leak`) that runs
  both a runtime and an AST scan. Regression of the cut would fail CI before
  merge.
- No business-logic pollution observed: no router rewiring, no engine code,
  no provider clients, no auto-promote paths, no truth writes. M-03's
  default ASS title was rebranded to ApolloVeo (cosmetic, not a contract
  invention).

### 2.2 Helper completeness — **PASS**

All 5 Media helpers from boundary §3.1 are landed at their mapped Apollo
targets with attribution headers pointing back to mapping rows + donor SHA.

### 2.3 Test posture — **PASS with one note**

- `tests/services/media/` — 43 cases, all green.
- Full suite (`tests/`) — 79 cases, all green. No regression to packet
  validator contracts.
- **Note (informational, not a blocker):** there is no formal
  `tests/guardrails/` directory yet. The "frontend guardrail" framing in the
  P2 directives currently has no host. The M-05 guard-compat test and the
  M-02 severance assertion are doing the equivalent work under
  `tests/services/media/`. This is acceptable for W1 (matches the
  follow-up note in `donor_absorption_w1_m04_m05_v1.md` §"Open follow-ups"),
  but a `tests/guardrails/` host should be opened **before** W2 lands its
  first provider client, since provider clients are where leak risks are
  much higher than for pure helpers.

### 2.4 Documentation hygiene — **PASS**

- Mapping doc statuses match reality.
- Evidence Index v1 now indexes both W1 evidence files + this review.
- "capability adapter base missing" gap line updated to reflect W1
  closure and W2 prerequisite pointer.

### 2.5 W1 verdict — **CLOSED**

Wave 1 is closed. Donor pin `62b6da0` is the authoritative source for any
later audit of W1 absorptions.

---

## 3. W2 (Provider Clients absorption) — admission conditions

> **Reminder:** The directive forbids starting W2 in this turn. The list
> below is the gate, not a kickoff.

### 3.1 Hard prerequisites (all required before opening any W2 PR)

1. **W2 donor SHA pin recorded.** Mapping doc §0 must add a fresh row for W2
   with the donor SHA at the time W2 begins. If donor HEAD has moved past
   `62b6da0`, a new pin is mandatory; do **not** silently reuse the W1 pin.
2. **`AdapterBase` review pass for provider use-case.** W2 binds to
   `SubtitlesAdapter`, `UnderstandingAdapter`, `DubAdapter`. Confirm the
   existing base (`gateway/app/services/capability/adapters/base.py`) covers
   provider lifecycle (auth, retry semantics, error envelope, advisory vs
   primary truth). If gaps exist, fix the base in a **separate** PR before
   the first W2 absorption — do not extend the base inline with absorption.
3. **Provider env matrix landed.** O-01 (`ops/env/env_matrix_v1.md`) is
   currently `Not started`. Provider clients require env-key naming to be
   pinned first; otherwise key-name normalization will be re-litigated per
   PR. This must land before A-02/A-03/A-05.
4. **`tests/guardrails/` host created.** Before A-01..A-05 land, open
   `tests/guardrails/` with at least:
   - a leak test pattern (no `swiftcraft.*`, no `app.models.*`, no
     `app.engines.*` imports in `gateway/app/services/providers/**`)
   - a "fallback never primary truth" assertion pattern reusable across
     providers.
5. **Hot Follow regression baseline frozen.** A-01 (Whisper worker) and
   A-05 (Azure dub) overlap conceptually with Hot Follow's frozen
   subtitle/dub paths. Capture a green run of the existing Hot Follow
   regression suite **before** the first W2 PR opens, so any drift is
   attributable.
6. **Mapping rows flipped to `In progress` at PR-open, not at PR-merge.**
   Lifecycle is `Not started → In progress → Absorbed`. W1 followed this;
   W2 must as well.

### 3.2 Risk warnings for the commander

- **R1 — Provider clients carry side effects.** Unlike Media helpers,
  provider clients perform network I/O, hold credentials, and emit cost.
  Test isolation must monkeypatch the network layer; no PR may be merged
  whose tests depend on live provider keys.
- **R2 — Donor providers were coupled to SwiftCraft task queue.** Expect
  several severances per file (analogous to M-02 but more aggressive).
  Each severance must have its own assertion test, not a docstring promise.
- **R3 — Duplicate Akool client (P-01 vs P-02).** Mapping doc already
  flags this — `backend/app/providers/akool_client.py` and
  `backend/app/services/akool_client.py` collapse to one Apollo target.
  Decide reconciliation policy in the W2 entry note **before** the first
  Akool PR, not during it.
- **R4 — Engine prompt drift.** Donor prompt fragments (E-01..E-08) live
  in donor engines that providers call. There will be temptation to drag
  prompt-shaping into a provider PR. **Forbidden.** Prompt fragments are
  W5 territory; if a W2 provider needs a prompt, stub it and let W5 fill it.
- **R5 — Hot Follow line is frozen.** A-01/A-05 must not edit any file
  inside Hot Follow's frozen surface. Reference patterns only.
- **R6 — Compliance/cost surface.** Provider absorption widens the
  attack/cost surface. Recommend running `security-review` on the first W2
  PR before merge, not after.

### 3.3 Recommended W2 sequencing

Sequencing is advisory, not a directive — final order is the commander's
call:

1. Open W2 entry note (donor SHA pin, env matrix, guardrails host).
2. A-02 (`fastwhisper`) — narrowest provider, lowest blast radius; good
   shake-down for the provider absorption pattern.
3. A-03 (`translate_gemini`) — pure text I/O, easy to mock.
4. A-01 (`asr_worker`) — depends on A-02 being settled.
5. A-05 (`dubbing_service`) — highest risk (Hot Follow adjacency); land last.
6. A-04 — pattern-only; capture as ADR, do not absorb code.

P-row provider clients (Akool, R2) are a separate sub-wave inside W2; do
not interleave with A-rows.

---

## 4. Recommendation to the commander

**W1 is closed and ready for sign-off.** No code changes are requested.
Sign-off action set:

1. Commit the two new docs (`donor_absorption_w1_m01_m02_m03_v1.md`,
   `W1_COMPLETION_REVIEW_v1.md`) and the Evidence Index v1 edits.
2. Do **not** open W2 PRs until §3.1 prerequisites #1, #3, #4 are landed
   (these are doc/test-host work, not provider code).
3. When ready to start W2, open a W2 entry note that explicitly cites this
   review and pins the W2 donor SHA.
