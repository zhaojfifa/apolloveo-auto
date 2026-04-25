# skills/matrix_script/

**Status**: P1.5 host reservation (empty until Matrix Script packet is frozen)
**Authority**: Master Plan v1.1 Part II §II.4; Donor Boundary §3.5 (pattern only)

## Purpose

Host directory for Matrix Script line skills: copy generation, variation prompt shaping, publish feedback shaping, and result packet binding.

No SwiftCraft engine prompt fragment maps directly to Matrix Script — the donor is matrix-unaware. Skills here are authored fresh against the Matrix Script line packet, with optional reference to SwiftCraft `localization_engine.py` patterns where relevant.

## Consumes

- Matrix Script line packet (to be authored by product, see `docs/handoffs/apolloveo_2_0_product_handoff_v1.md`)
- `factory_input_contract_v1`, `factory_content_structure_contract_v1`, `factory_delivery_contract_v1`
- `skills_runtime_contract.md`
- Capability kinds: `understanding`, `variation`, `subtitles`, `dub`, `pack`

## Does not

- Hold variation truth (variations are artifacts; their state is derived by ready_gate)
- Pin vendors
- Write publish feedback truth (publish feedback is delivery-contract-shaped artifact)
- Import any `swiftcraft.*` package

## Absorption pre-condition

Matrix Script packet (per `docs/handoffs/apolloveo_2_0_product_handoff_v1.md` deliverable 1) MUST be frozen before any skill module lands here.
