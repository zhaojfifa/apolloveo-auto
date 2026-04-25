# gateway/app/services/artifacts/

**Status**: P1.5 host reservation (empty until P2 absorption begins)
**Authority**: Master Plan v1.1 Part IV.1; Donor Boundary §3.4; Capability Mapping rows V-01, V-02

## Purpose

Host directory for artifact shaping and vendor-readable asset bridges. Will receive absorbed code from SwiftCraft `backend/app/services/{vendor_asset_bridge,video_face_extractor}.py`.

## Consumes

- `factory_delivery_contract_v1` — artifact rows must conform to delivery shape

## Does not

- Auto-promote artifacts to Asset Library (Asset Library entries are created only by Apollo's explicit `promote_flow`)
- Write delivery truth — produces shaped rows that callers persist into the Artifact Store
- Import any `swiftcraft.*` package
- Expose helpers directly to the front-end

## Absorption pre-condition

Code lands here only after `swiftcraft_capability_mapping_v1.md` rows V-01..V-02 move to `In progress` via an absorption PR citing the row id.
