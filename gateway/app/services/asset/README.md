# gateway/app/services/asset/

**Status**: P1 implementation target (asset library + broll views + promote flow)
**Authority**: Master Plan v1.0 §7 Asset Supply / Broll Roadmap; v1.1 Part IV.1

## Purpose

Host directory for the asset supply domain:

- Asset table (`asset` per Master Plan v1.0 §7.1)
- List / filter / upload / fingerprint / index / tag operations
- Promote flow (Artifact Store → Asset Library; explicit-only)
- Broll library view (`asset.type = broll`)

## Consumes

- `asset_supply_contract_v1.md` (to be authored in P1)
- `promote_flow_contract_v1.md` (to be authored in P1)
- Artifact Store outputs (read-only via promote_flow)

## Does not

- Auto-receive Artifact Store outputs (promote is the only crossing)
- Pollute task workspace main flow (asset supply is a separate UI face)
- Hold task / state truth (asset library is long-term resource, not task truth)
- Import any `swiftcraft.*` package

## Front-end isolation

The asset supply UI face (`docs/handoffs/apolloveo_2_0_design_handoff_v1.md` §3.4) consumes contract-shaped views from gateway routers, never this module directly.
