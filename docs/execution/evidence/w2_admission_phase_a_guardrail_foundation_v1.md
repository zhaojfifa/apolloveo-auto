# W2 Admission Preparation — Phase A: Guardrail Foundation (v1)

- Date: 2026-04-26
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase A only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
  - `docs/donor/swiftcraft_donor_boundary_v1.md`
  - `docs/donor/swiftcraft_capability_mapping_v1.md`
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.4

## 1. Scope

This wave delivers ONLY the guardrail host and the foundation guardrail
tests required by the W2 Admission directive §4 Phase A and W1 review
§3.1.4. No provider absorption, no env matrix, no donor SHA pin, no
adapter lifecycle changes, no Hot Follow regression baseline freeze.

## 2. What was added

### 2.1 Formal guardrail host
- `tests/guardrails/` created on mainline.
- `tests/guardrails/__init__.py`
- `tests/guardrails/README.md` — documents authority, scope, and out-of-
  scope items for this wave.
- `tests/guardrails/_scan.py` — shared AST-based import scanner used by
  the three guardrail tests. AST-only matching (not substring) so
  unrelated docstrings and string literals do not produce false hits.

### 2.2 Foundation guardrail tests

1. `tests/guardrails/test_provider_leak_boundary.py`
   - Forbids provider SDK imports (`openai`, `azure.cognitiveservices*`,
     `fal_client`, `elevenlabs`, `anthropic`, `google.cloud.speech`,
     `google.cloud.texttospeech`, `boto3`) inside frontstage/UI zones
     (`gateway/app/web/`) and domain/truth zones
     (`gateway/app/domain/`, `services/contract_runtime/`,
     `services/ready_gate/`, `services/packet/`).
   - Includes a "zone inventory not empty" sanity assertion so a layout
     change cannot silently make the test vacuous.

2. `tests/guardrails/test_donor_leak_boundary.py`
   - Forbids any `swiftcraft.*` import anywhere in `gateway/` or
     `tests/` (boundary §5.1, §5.3).
   - Forbids re-introduction of donor truth modules
     (`app.models.task`, `app.engines.*`) per boundary §4.1/§4.2.
   - Adds a literal-token belt-and-suspenders scan for the string
     `swiftcraft` in Apollo `.py` source (catches accidental string
     literals the AST scan would not see). Documentation under `docs/`
     is intentionally not scanned — those files MUST reference the
     donor by name.

3. `tests/guardrails/test_fallback_never_primary_truth.py`
   - Forbids truth-authority modules (`services/contract_runtime/`,
     `services/ready_gate/`, `services/packet/`, `gateway/app/domain/`,
     and `services/hot_follow_subtitle_authority.py`) from importing
     projection / presenter / `*_fallback*` / `*_panel_debug` helpers.
   - Backs §3.4 "Hot Follow 主链优先保护" and §7 "no second truth /
     fallback state semantic" by enforcing one-way flow: truth modules
     emit, helpers consume.
   - Includes a truth-zone inventory sanity assertion.

## 3. Tests run

```
python3 -m pytest tests/guardrails/ -q
=> 7 passed in 0.03s
```

Sanity re-run of adjacent suites to confirm no regression introduced:

```
python3 -m pytest tests/services/media/ tests/contracts/ -q
=> 79 passed in 0.17s
```

## 4. What was intentionally NOT done (red lines preserved)

- No provider SDK / client absorption code added or modified.
- No new files inside `gateway/app/services/providers/`, `gateway/adapters/`,
  or `gateway/app/services/capability/adapters/`.
- No changes to Hot Follow main-line business behaviour.
- No `AdapterBase` lifecycle method extensions.
- No env / secret matrix work (Phase B).
- No donor SHA pin update for W2 (Phase C).
- No Hot Follow regression baseline freeze (Phase D).
- No migration of the existing W1 severance / guard-compat tests out of
  `tests/services/media/`. Those tests still pass and remain
  authoritative for W1's M-02 / M-05 absorptions; relocating them now
  would be churn unrelated to the W2 admission gate. The new
  `tests/guardrails/` host provides the W2-scoped boundary regardless.
- No frontend / workbench scope expansion.

## 5. Acceptance vs. directive §10 / §4 Phase A

| Acceptance criterion | Status |
|---|---|
| `tests/guardrails/` exists on mainline worktree | DONE |
| guardrail tests run and pass | DONE (7 passed) |
| explicit provider leak / import-boundary test | DONE (`test_provider_leak_boundary.py`) |
| explicit donor leak boundary test | DONE (`test_donor_leak_boundary.py`) |
| explicit "fallback never primary truth" test | DONE (`test_fallback_never_primary_truth.py`) |
| evidence / write-back updated | DONE (this file + index entry) |
| no provider code touched | DONE |

## 6. What remains before W2.1 unlock

Per W2 Admission Preparation directive §4 (Phases B–E) and W1 review
§3.1 hard prerequisites #1, #2, #3, #5:

- Phase B — O-01..O-03 env / secret matrix (`ops/env/env_matrix_v1.md`,
  storage layout, secret loading baseline).
- Phase C — fresh W2 donor SHA pin in
  `docs/donor/swiftcraft_capability_mapping_v1.md`; mapping row
  lifecycle freeze; AdapterBase lifecycle review (separate PR).
- Phase D — Hot Follow regression baseline freeze with green run
  evidence.
- Phase E — W2.1 admission review and signoff (architect + reviewer).

These are explicitly out of scope for this wave per directive §0 and
§7. The next wave owner picks up at Phase B.

## 7. Hard stop confirmation

This wave stops here. No env matrix, no donor pin, no provider code.
Awaiting review and next instruction.
