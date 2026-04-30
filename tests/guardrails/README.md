# `tests/guardrails/` — W2 Admission Guardrail Host

Authority:
- `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
- `docs/donor/swiftcraft_donor_boundary_v1.md` §5.3, §7
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.4

This host is the formal home for cross-cutting boundary/leak/truth-authority
guardrail tests. It exists so that, before any W2 provider absorption PR is
opened, leak tests and truth-authority tests live in a single audited
location rather than scattered across `tests/services/...`.

This wave (W2 Admission Preparation Phase A) only adds the host and the
**foundation** guardrail categories required by the directive:

1. `test_provider_leak_boundary.py` — provider SDKs (e.g. `openai`,
   `azure.cognitiveservices.*`, `fal_client`, `elevenlabs`, `anthropic`)
   must NOT appear inside frontstage/UI zones or domain/truth zones. They
   are only allowed inside the explicit adapter/provider zones listed in
   `swiftcraft_donor_boundary_v1.md` §3.

2. `test_donor_leak_boundary.py` — no `swiftcraft.*` import may appear
   anywhere inside Apollo source under `gateway/` or `tests/`. This is the
   §5.3 import rule, hosted formally for W2.

3. `test_fallback_never_primary_truth.py` — projection / presenter /
   `*_fallback*` / debug helpers are not authoritative truth sources and
   must NOT be imported by truth-authority runtime modules
   (`gateway/app/services/contract_runtime/`, `gateway/app/services/ready_gate/`,
   `gateway/app/services/packet/`, `gateway/app/domain/`,
   `gateway/app/services/hot_follow_subtitle_authority.py`).

## Out of scope for this wave

- env / secret matrix (Phase B)
- donor SHA pin / mapping lifecycle (Phase C)
- Adapter lifecycle review (Phase C)
- Hot Follow regression baseline freeze (Phase D)
- any provider SDK / client absorption code

## How to run

```
pytest tests/guardrails/ -q
```
