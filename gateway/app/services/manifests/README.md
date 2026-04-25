# gateway/app/services/manifests/

**Status**: P1.5 host reservation (empty until P2 absorption begins)
**Authority**: Master Plan v1.1 Part IV.1 (Artifact / Manifest Supply); Donor Boundary §3.4

## Purpose

Host directory for manifest shaping and delivery-output formatting. Manifest objects are projections of `factory_delivery_contract_v1` and MUST NOT introduce a second delivery semantic.

## Consumes

- `factory_delivery_contract_v1` — single source of delivery truth; manifests project from it
- Artifact rows produced by `gateway/app/services/artifacts/`

## Does not

- Define delivery semantics independent of `factory_delivery_contract_v1`
- Write publishability or readiness state (those are derived by ready_gate, not shaped here)
- Import any `swiftcraft.*` package

## Absorption pre-condition

Manifest shaping is a derived concern; code lands here as part of broader artifact / delivery refinement, not via a single donor row.
