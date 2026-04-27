# W2.1 Base-Only Adapter Preparation — Execution Log

Active execution log for the W2.1 Base-Only Adapter Preparation Wave
(`docs/architecture/ApolloVeo_2.0_W2.1_Base_Only_Adapter_Preparation_Wave_指挥单_v1.md`).

The four base-only PRs (B1–B4) are tracked here. Each entry must record what
was added, what was intentionally not added, and what blockers remain.

---

## B3 — Error Envelope (`AdapterError`)

- Date: 2026-04-27
- Status: implementation green; awaiting architect + reviewer signoff
- Evidence: `docs/execution/evidence/w2_1_b3_adapter_error_envelope_v1.md`
- Code:
  - `gateway/app/services/capability/adapters/base.py` (added
    `AdapterErrorCategory`, `AdapterError`)
  - `gateway/app/services/capability/adapters/__init__.py` (export)
  - `tests/services/capability/adapters/test_adapter_error.py` (13 tests, pass)
- What B3 adds: closed `AdapterErrorCategory` set, advisory-shaped
  `AdapterError` exception with frozen `{category, message, source, retryable,
  details}` shape, immutable `details` view, stable `to_dict()` serialisation.
- What B3 does NOT add: B1 (auth/credential), B2 (retry/timeout/cancellation),
  B4 (construction-vs-invocation), provider code, runtime wiring, Hot Follow
  changes, packet / schema / contracts / workbench changes.
- Validation: `python3 -m pytest tests/services/capability/adapters/test_adapter_error.py -v` → 13 passed.
- Next handoff: architect signoff on B3 boundary; reviewer closes B3 PR; B1 may then start.

---

## B1 — Auth / Credential Surface

- Status: NOT STARTED. Blocked on B3 signoff per recommended order
  (W2.1 directive §4).

## B2 — Retry / Timeout / Cancellation

- Status: NOT STARTED.

## B4 — Construction-vs-Invocation Lifecycle

- Status: NOT STARTED.

---

## W2.1 Provider Absorption gate

W2.1 Provider Absorption remains BLOCKED until B1–B4 are all green and
signed off (W2.1 directive §9). After B3, three of the four base-only PRs
remain outstanding.
