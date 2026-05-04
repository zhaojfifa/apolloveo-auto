# gateway/app/services/asset/

**Status**: Operator Capability Recovery PR-2 — minimum operator capability landed (read-only library + closed-facet filter + opaque-ref handle + promote intent + closure mirror). Full DAM / upload / admin review UI deferred to a later wave.
**Authority**: Master Plan v1.0 §7 Asset Supply / Broll Roadmap; v1.1 Part IV.1; ApolloVeo 2.0 Operator Capability Recovery Decision §4.1 + Global Action §5.

## Purpose

Host directory for the asset supply domain:

- Asset library object (closed metadata schema; PR-2 = seeded read-only)
- List / filter (closed-facet) / opaque-reference operations
- Promote intent submit + append-only closure mirror
- Operator-visible Asset Supply / B-roll page (`/assets`)

## Consumes

- `docs/contracts/asset_library_object_contract_v1.md` (Plan C)
- `docs/contracts/promote_request_contract_v1.md` (Plan C)
- `docs/contracts/promote_feedback_closure_contract_v1.md` (Plan C)
- Artifact handles (read-only via promote intent — never mutated)

## Does not

- Auto-receive Artifact Store outputs (promote is the only crossing)
- Pollute task workspace main flow (asset supply is a separate UI face)
- Hold task / state truth (asset library is long-term resource, not task truth)
- Import any `swiftcraft.*` package

## Front-end isolation

The asset supply UI face (`docs/handoffs/apolloveo_2_0_design_handoff_v1.md` §3.4) consumes contract-shaped views from gateway routers, never this module directly.
