# skills/digital_anchor/

**Status**: P1.5 host reservation (empty until Digital Anchor packet is frozen and engine prompt fragments are absorbed)
**Authority**: Master Plan v1.1 Part II §II.4; Donor Boundary §3.5; Capability Mapping rows E-01, E-02, E-04..E-07

## Purpose

Host directory for Digital Anchor line skills: prompt shaping, provider route hints, and quality / recovery logic specific to role / scene / speaker / language production.

Planned modules (after Digital Anchor packet is frozen and absorption rows reach `In progress`):

- `action_replica_prompt.py` (E-01)
- `akool_prompt.py` (E-02)
- `fal_kling_prompt.py` (E-04)
- `fal_kling_v2v_prompt.py` (E-05)
- `fal_wan26_flash_prompt.py` (E-06)
- `fal_wan26_r2v_prompt.py` (E-07)

## Consumes

- Digital Anchor line packet (to be authored by product, see `docs/handoffs/apolloveo_2_0_product_handoff_v1.md`)
- `factory_scene_plan_contract_v1`, `factory_audio_plan_contract_v1`, `factory_language_plan_contract_v1`, `factory_delivery_contract_v1`
- `skills_runtime_contract.md`

## Does not

- Carry engine task / orchestration code (only prompt shaping is absorbed)
- Write L1 / L2 / L3 / L4 truth (skills produce candidates / advisories, not truth)
- Pin vendors (capability_plan kinds only; routing decides vendor)
- Import any `swiftcraft.*` package
