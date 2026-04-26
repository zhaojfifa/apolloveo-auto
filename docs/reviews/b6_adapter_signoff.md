# B6 — Capability Adapter Base Signoff

**Wave**: Packet Gate + Surface Gate + Signoff Closure
**Date**: 2026-04-26
**Authority**: `docs/reviews/architect_signoff_packet_gate_v1.md` §3 (B6)
**Donor Absorption**: NOT APPROVED — this signoff covers only the donor-free interface layer.

---

## 1. Artefact under review

- `gateway/app/services/capability/adapters/__init__.py`
- `gateway/app/services/capability/adapters/base.py`

## 2. Boundary verification

| Check | Result |
|---|---|
| No vendor SDK / donor (SwiftCraft, Jellyfish, etc.) imports | Pass — only stdlib + `gateway.app.services.packet.envelope` for the closed `CAPABILITY_KINDS` set |
| No provider client invocation | Pass — `invoke` is abstract, base raises `NotImplementedError` |
| `capability_kind` constrained to R3 closed set | Pass — `AdapterBase.__init_subclass__` enforces membership in `CAPABILITY_KINDS` |
| No `vendor_id` / `model_id` / `engine_id` on invocation surface | Pass — `AdapterInvocation` exposes only contract-shaped fields (`inputs`, `outputs`, `mode`, `quality_hint`, `language_hint`, `extras`) |
| No truth-state writes / no four-layer mutation | Pass — adapters return `AdapterResult`; base layer performs no I/O |
| Interface set matches `services/capability/README.md` catalog | Pass — `Understanding / Subtitles / Dub / VideoGen / Avatar / FaceSwap / PostProduction / Pack` adapters all declared |

## 3. Adapter classes delivered

`AdapterBase`, `UnderstandingAdapter`, `SubtitlesAdapter`, `DubAdapter`,
`VideoGenAdapter`, `AvatarAdapter`, `FaceSwapAdapter`, `PostProductionAdapter`,
`PackAdapter`.

`variation` / `speaker` / `lip_sync` capability kinds remain reserved for line-
specific adapters under `workers/adapters/<vendor>/` and are not pre-bound at
the base layer; the closed-set guard in `__init_subclass__` accepts them when a
vendor adapter declares them.

## 4. Verdict

| Item | Status |
|---|---|
| Donor Precondition (B6) | **Met — Donor gate Partial → Pass eligible** |
| Interface boundary | **Signed off** |
| Donor Absorption | **Still HOLD** — separate signoff required per `architect_signoff_packet_gate_v1.md` §2 |

B6 satisfies the Donor Precondition. Vendor implementations under
`workers/adapters/<vendor>/` and provider clients under `providers/<vendor>/`
remain gated behind a separate Donor Absorption signoff and are NOT released
by this document.
