# ApolloVeo 2.0 — Surface Freeze Index (Low-fi v1)

**Wave**: Packet Gate + Surface Gate + Signoff Closure
**Owner**: Designer
**Status**: Low-fi frozen, awaiting Reviewer signoff
**Date**: 2026-04-26

## Discipline (red lines)

- UI consumes **contract objects only**. No new state invented at the surface layer.
- Every visible status string is a projection of `evidence.ready_state` ∈ {`draft`, `validating`, `ready`, `gated`, `frozen`} or a derived L2/L3 contract field. No surface-local status machine.
- **No vendor / model / provider / engine** selectors anywhere. `capability_plan[].kind` + `mode` are the only capability-shaped affordances.
- **No donor / supply concept** is exposed. Internal capability sourcing stays invisible to the operator.
- **Scene Pack is non-blocking**. Its absence must never gate the operator from advancing other capabilities.
- No backend / provider logic, no packet schema authority, no new status definitions.

## Deliverables

| # | Doc | Scope |
|---|---|---|
| 1 | [surface_task_area_lowfi_v1.md](surface_task_area_lowfi_v1.md) | Task Area surface (entry / packet intake / line selection) |
| 2 | [surface_workbench_lowfi_v1.md](surface_workbench_lowfi_v1.md) | Workbench surface (capability_plan execution shell) |
| 3 | [surface_delivery_center_lowfi_v1.md](surface_delivery_center_lowfi_v1.md) | Delivery Center surface (deliverable + asset_sink projection) |
| 4 | [panel_matrix_script_variation_lowfi_v1.md](panel_matrix_script_variation_lowfi_v1.md) | Matrix Script line-specific panel (variation_matrix + slot_pack) |
| 5 | [panel_digital_anchor_role_speaker_lowfi_v1.md](panel_digital_anchor_role_speaker_lowfi_v1.md) | Digital Anchor line-specific panel (role_pack + speaker_plan) |

## Contract source of truth

- Packet envelope: `schemas/packets/matrix_script/packet.schema.json`, `schemas/packets/digital_anchor/packet.schema.json`
- Generic refs (L2): `factory_input`, `factory_content_structure`, `factory_scene_plan`, `factory_audio_plan`, `factory_language_plan`, `factory_delivery`
- Line-specific refs (L3): `matrix_script_variation_matrix`, `matrix_script_slot_pack`, `digital_anchor_role_pack`, `digital_anchor_speaker_plan`
- Reference baseline (always green): `hot_follow` via `evidence.reference_line`
