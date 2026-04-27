# W2.1 Base-Only Adapter Preparation — Guardrail Reconciliation v1

- Date: 2026-04-27
- Scope: minimal reconciliation for `tests/guardrails/test_donor_leak_boundary.py::test_no_swiftcraft_string_in_python_source_outside_donor_docs`
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md`
  - `docs/execution/evidence/w2_1_b4_adapter_lifecycle_boundary_v1.md`

## Root cause

The failing guardrail was a scan-scope drift, not real donor package leakage.

The import-layer donor boundary tests were already AST-based and still enforce that no `swiftcraft.*` import appears in Apollo source. The failing literal-string test was a belt-and-suspenders text scan over all Python files under `gateway/` and `tests/`; it matched required W1 attribution/audit docstrings in absorbed media helpers and boundary-test string constants that intentionally name the forbidden donor token.

Those strings are not runtime donor package usage and do not indicate provider absorption.

## Minimal fix

`tests/guardrails/test_donor_leak_boundary.py` now keeps the import scan unchanged and narrows the literal-string scan to executable gateway string literals only:

- scans `gateway/` Python files;
- parses with `ast`;
- excludes module / class / function docstrings;
- leaves comments and test guardrail fixtures out of the literal scan;
- still catches executable hardcoded `swiftcraft` string literals in gateway source.

## Files changed

- `tests/guardrails/test_donor_leak_boundary.py`
- `docs/execution/evidence/w2_1_guardrail_reconciliation_v1.md`
- `docs/execution/W2_1_BASE_ONLY_ADAPTER_PREPARATION_LOG.md`

## Validation

Command:

```bash
python3.11 -m pytest tests/services/capability/adapters/ tests/guardrails -q
```

Result after reconciliation:

```text
92 passed
```

## Boundary confirmation

No provider code was added. No B1/B2/B3/B4 implementation was redesigned. No Hot Follow code was changed. No W2.2/W2.3 work was started.
