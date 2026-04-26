# W2 Admission · AdapterBase Lifecycle Review v1

- Date: 2026-04-26
- Reviewer role: ApolloVeo L5 Architect (lifecycle / capability boundary authority)
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase C only
- Scope: Governance review of the existing `AdapterBase` surface against the lifecycle requirements W2.1 will impose. **Review only. No code changes proposed in this wave.**
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §3.3, §4 Phase C, §9
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.2
  - `docs/donor/swiftcraft_donor_boundary_v1.md` §5.5 (adapter binding rule)
  - `docs/donor/swiftcraft_capability_mapping_v1.md` §3 (row lifecycle, frozen at this Phase C)
  - `docs/contracts/factory_packet_validator_rules_v1.md` R3 (closed capability kind set, vendor-pin prohibition)
- Code under review (read-only):
  - `gateway/app/services/capability/adapters/base.py`
  - `gateway/app/services/packet/envelope.py` (`CAPABILITY_KINDS`)

> **Scope hard stop.** This document is a *review* artefact. It does not extend `AdapterBase`, does not write code, and does not authorise W2.1 to start. It records what the existing base already covers, what gaps exist for W2.1, and the rule that any gap fix is a separate PR before the first W2 absorption (W1 review §3.1.2).

---

## 1. Why this review exists

The W2 Admission directive §3.3 is explicit:

> Adapter 先评审，后实现。W2 不允许一边吸收 Provider，一边临场发明 Adapter 生命周期。任何 AdapterBase 扩展，必须先在独立 review 中冻结。

W1 review §3.1.2 reinforces:

> If gaps exist, fix the base in a **separate** PR before the first W2 absorption — do not extend the base inline with absorption.

Phase C therefore must produce a *standalone authority doc* — this file — that:

1. enumerates what the base already gives W2.1;
2. enumerates what W2.1 will need that the base does not yet give;
3. fixes the rule that any base extension is a separate PR, not an absorption-bundled change.

---

## 2. Current AdapterBase surface (what exists today)

`gateway/app/services/capability/adapters/base.py` provides:

| Element | Shape | Lifecycle role |
|---|---|---|
| `AdapterCapabilityKind` | type alias for `str`, constrained at runtime to `CAPABILITY_KINDS` from `factory_packet_validator_rules_v1.md` R3 | Pins the closed set; prevents new capability kinds from being invented inside an adapter PR. |
| `AdapterInvocation` | frozen dataclass (`capability_kind`, `inputs`, `outputs`, `mode`, `quality_hint`, `language_hint`, `extras`) | Contract-shaped input envelope. Mirrors a packet `capability_plan` entry. `extras` is forward-compatible but MUST NOT carry vendor / model / engine ids (R3). |
| `AdapterResult` | frozen dataclass (`artefacts`, `advisories`, `rule_versions`) | Contract-shaped return envelope. Adapters return artefact references and advisories; they never return raw vendor responses. |
| `AdapterBase` | abstract base; `__init_subclass__` validates `capability_kind` against `CAPABILITY_KINDS`; `invoke` is `@abstractmethod` and raises `NotImplementedError` | Donor-free skeleton. Subclass instantiation without an `invoke` override is a `TypeError`. |
| Concrete kind subclasses | `UnderstandingAdapter`, `SubtitlesAdapter`, `DubAdapter`, `VideoGenAdapter`, `AvatarAdapter`, `FaceSwapAdapter`, `PostProductionAdapter`, `PackAdapter` | Pin `capability_kind`; do not implement `invoke`. Vendor adapters subclass these. |

### 2.1 What the base already enforces (W2.1-relevant)

- **Closed capability set.** A new kind cannot be introduced by a W2.1 PR — the runtime check in `__init_subclass__` rejects any `capability_kind` outside `CAPABILITY_KINDS`. This eliminates the most common drift vector during provider absorption.
- **No vendor/model/engine ids in invocation.** `AdapterInvocation.extras` is documented as forward-compatible only; vendor-pin prohibition is contract-level (R3) and re-stated at the dataclass docstring.
- **No truth writes.** `AdapterResult` exposes only `artefacts`, `advisories`, `rule_versions` — there is no return path that lets an adapter write to L1/L2/L3/L4 truth. This matches `swiftcraft_donor_boundary_v1.md` §5.4.
- **Donor-free.** The base imports only stdlib + `gateway.app.services.packet.envelope`. No `swiftcraft.*` import path exists or is reachable.
- **Side-effect-free import.** `invoke` raises `NotImplementedError`; no I/O happens at module import.

---

## 3. Gap analysis against W2.1 needs

W2.1 absorbs an Understanding Provider (`A-03 translate_gemini` is the candidate per W1 review §3.3). To support a real provider call behind `UnderstandingAdapter` without re-litigating lifecycle inside the absorption PR, W2.1 will need at least the following capabilities. Each is recorded as a *gap*, with the rule that closing the gap is a **separate, base-only PR** — never bundled with the provider absorption PR.

### 3.1 Auth / credential surface — **GAP (deferred)**

- The base does not declare how a provider adapter receives its credentials. Today a vendor adapter would have to read env vars directly inside `invoke`, which couples credential loading to the request path.
- **W2 admission Phase B** has already landed `ops/env/env_matrix_v1.md` and `ops/env/secret_loading_baseline_v1.md`. Phase C records that the loading shape (where credentials are resolved, by whom, at what lifecycle moment) is a `AdapterBase`-level concern, not a per-provider concern.
- **Resolution rule:** a credential-loading hook on `AdapterBase` (e.g. an injected `secrets: SecretResolver` constructor argument bound at adapter construction, not at `invoke`) MUST be added in a base-only PR before the first W2.1 provider PR. Shape is left to that PR; this review does not pre-design it.
- **Forbidden in W2 admission:** implementing this hook now. Phase C is review-only.

### 3.2 Retry / timeout / cancellation semantics — **GAP (deferred)**

- The base does not declare retry policy, idempotency expectation, or timeout / cancellation surface. A provider adapter today would either swallow these concerns silently or re-implement them per provider.
- W1 review §3.2 R1 calls this out: "Provider clients carry side effects … Test isolation must monkeypatch the network layer."
- **Resolution rule:** retry / timeout policy lives on `AdapterBase` as an explicit, declarable shape (not on the provider client). Closing this gap is a separate base-only PR; the policy must be expressible without reference to any specific provider SDK.
- **Forbidden in W2 admission:** designing the policy. Phase C only freezes that the policy is a base-level concern.

### 3.3 Error envelope — **GAP (deferred)**

- The base returns `AdapterResult` on success but does not pin the error shape on failure. Today a vendor adapter could raise any exception type, leaking provider-specific error classes upward and giving the ready gate no stable surface to consume.
- W1 review §3.2 R2 calls out per-file severance from donor task/queue coupling — analogous discipline is needed for error reporting.
- **Resolution rule:** an `AdapterError` (or equivalent error envelope) MUST be defined on `AdapterBase` before the first W2.1 PR. It MUST be advisory-shaped (not truth-shaped) to preserve the "no truth writes" rule.
- **Forbidden in W2 admission:** implementing the envelope. Phase C only freezes its location.

### 3.4 Advisory-vs-primary-truth contract — **PARTIAL (review-confirmed)**

- The base already separates `artefacts` (contract-shaped) from `advisories` (free-form). That is the correct shape.
- **What is missing** is a typed advisory shape so that a provider absorption cannot accidentally promote an advisory to primary truth (W1 review §3.2 R1, donor boundary §4.4).
- **Status:** this is review-confirmed adequate for W2.1 *if* the absorption PR adds typed advisories at the vendor-adapter layer rather than at the base. The W2 admission Phase A guardrail `tests/guardrails/test_fallback_never_primary_truth.py` already enforces the no-promotion rule from the runtime side.
- **Forbidden in W2 admission:** changing the base today.

### 3.5 Construction-vs-invocation lifecycle — **GAP (deferred)**

- The base today has no `__init__` contract: a vendor adapter could perform I/O at construction time, which would couple module import to network calls and break test isolation.
- **Resolution rule:** `AdapterBase` MUST forbid I/O at construction. The construction hook (when added in §3.1's base-only PR) carries injected dependencies only; first I/O is reachable only via `invoke`.
- **Forbidden in W2 admission:** adding a construction contract today.

### 3.6 Rule-version provenance — **PARTIAL (review-confirmed)**

- `AdapterResult.rule_versions` already exists. It is the right place to record which rule-set / prompt-version the adapter used.
- **Status:** adequate as a *shape*. The W2.1 absorption PR will populate it; no base change is required for that to work.

---

## 4. Frozen rules out of this review

The following rules are **frozen** by this review and govern every W2.x absorption PR:

1. **Base extension is a separate PR.** Any change to `gateway/app/services/capability/adapters/base.py` (or to `AdapterInvocation` / `AdapterResult` / `AdapterBase` / kind subclasses) is its own PR. It MUST NOT be bundled with a provider absorption PR. Bundling is a contract violation regardless of how small the base change is.
2. **Closed capability set is immutable in W2.x.** No new `capability_kind` is added during W2.x. If a W2.x provider needs a kind not in `CAPABILITY_KINDS`, the absorption is blocked; opening the closed set is a Master Plan amendment, not a W2.x decision.
3. **Vendor-pin prohibition holds.** `AdapterInvocation.extras` MUST NOT carry vendor / model / engine identifiers. Provider selection happens *outside* the adapter contract surface (worker / planning layer), not inside it.
4. **No truth writes from adapters.** `AdapterResult` is the only return path. Adapters return artefact references and advisories; Apollo callers write truth. This rule is absolute and is not negotiable per provider.
5. **No I/O at import or construction.** Module import is side-effect-free today. Once a construction hook is added (§3.5), construction must remain side-effect-free; first I/O is `invoke`-only.
6. **Donor-free base.** The base imports nothing donor-derived. No future base PR may introduce a transitive donor import.
7. **Fallback never primary truth.** A provider adapter that returns a fallback path (e.g. a degraded ASR result) MUST mark it as `advisories`, never as `artefacts`. Enforced runtime-side by `tests/guardrails/test_fallback_never_primary_truth.py`.

---

## 5. Minimum AdapterBase contract required before W2.1 starts

Restating the W1 review §3.1.2 gate in this review's language:

W2.1 may NOT open a provider absorption PR until *all* of the following are true:

1. A separate base-only PR has landed that closes the §3.1 (auth/credential) gap.
2. A separate base-only PR has landed that closes the §3.2 (retry/timeout/cancellation) gap.
3. A separate base-only PR has landed that closes the §3.3 (error envelope) gap.
4. A separate base-only PR has landed that closes the §3.5 (construction-vs-invocation lifecycle) gap.

Items §3.4 (advisory shape) and §3.6 (rule-version provenance) do NOT block W2.1; they are review-confirmed adequate as-is.

These four base-only PRs are the *exact* allowed scope for any AdapterBase extension before W2.1. Anything else is out of scope until W2.2 or later.

---

## 6. Out of scope (intentionally not done in this wave)

This Phase C review does NOT:

- propose, draft, or implement any change to `gateway/app/services/capability/adapters/base.py`;
- design the auth, retry, error, or construction hook shapes (those are the four base-only PRs above);
- enumerate W2.2 / W2.3 lifecycle needs (Subtitles/Dub, Avatar/VideoGen/Storage providers carry their own lifecycle reviews when those waves open);
- modify any vendor adapter, provider client, worker adapter, or Hot Follow path;
- touch `tests/guardrails/`, `ops/env/`, or any other Phase A / Phase B artefact;
- evaluate Hot Follow regression baseline freeze (that is Phase D).

---

## 7. Architect signoff

This review is the standalone authority artefact required by `ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §3.3 and §9 item 6.

- **Verdict on AdapterBase as W2.1 admission gate:** existing base is *adequate as a skeleton* and *inadequate as a W2.1 launch contract* — four base-only gap-closing PRs (§5) are required before the first W2.1 absorption PR.
- **Verdict on bundling:** any AdapterBase change bundled inside a W2.x absorption PR is a contract violation and must be rejected at review.
- **Verdict on Phase C closure for this artefact:** the lifecycle review exists, is standalone, and freezes the four §4 rules and the four §5 gates. Phase C closure for the lifecycle item is therefore green.

This review does NOT signoff the rest of Phase C (donor SHA pin, mapping lifecycle freeze, evidence write-back); those are recorded in `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md`.

---

## 8. References

- `gateway/app/services/capability/adapters/base.py`
- `gateway/app/services/packet/envelope.py`
- `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md`
- `docs/donor/swiftcraft_donor_boundary_v1.md`
- `docs/donor/swiftcraft_capability_mapping_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`
- `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md`
