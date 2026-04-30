# Digital Anchor · Role Pack Contract v1

Date: 2026-04-26
Status: Frozen for P2 entry review (line-specific delta contract; consumed by packet validator)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`; parent packet `docs/contracts/digital_anchor/packet_v1.md`
Owner: Product
Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Purpose

Declare the **role pack delta** that the Digital Anchor line adds on top of the factory-generic input and content-structure contracts. The role pack holds the line's anchor role declarations — framing, appearance reference, and language scope binding — at the level of *role kinds*, never at the level of avatar engines, voice models, or rendering vendors.

This contract describes:

- the closed framing-kind set the pack may use
- the closed appearance-ref kind set the pack may use
- the shape of `roles[]` declarations
- the prohibitions that keep the role pack free of state truth, vendor pins, and avatar engine identity

This contract does NOT describe avatar runtime, render execution, donor absorption, provider clients, or any second source of task / state truth.

## Identity

- `ref_id`: `digital_anchor_role_pack`
- `binds_to`: `g_input`, `g_struct`
- Parent packet: `docs/contracts/digital_anchor/packet_v1.md`
- Version: `v1`

## Closed sets

- `framing_kind_set`: `{head, half_body, full_body}` — adding a kind requires a packet re-version
- `appearance_ref_kind_set`: `{role_card, role_pose_set}` — adding a kind requires a packet re-version

## Delta fields

### `roles[]`

Ordered list of anchor roles. Each entry declares:

| field                | type            | notes                                                                       |
| -------------------- | --------------- | --------------------------------------------------------------------------- |
| `role_id`            | string (stable) | unique within the packet                                                    |
| `display_name`       | string          | non-truth presentational label                                              |
| `framing_kind`       | enum            | one of `framing_kind_set`                                                   |
| `language_scope_ref` | string          | id of a language-scope declaration drawn from `factory_language_plan_contract_v1` |
| `appearance_ref`     | string (opaque) | catalog reference (e.g. `catalog://role_card/<id>`); MUST identify a kind drawn from `appearance_ref_kind_set` via the catalog scheme |
| `notes`              | string (opt.)   | non-truth descriptive string                                                |

Rules:

- `role_id` MUST be unique within the packet
- `appearance_ref` MUST resolve through the role catalog; the packet does not embed appearance assets and MUST NOT pin a vendor / model / engine
- `language_scope_ref` MUST resolve to a language scope reachable via `g_lang`
- The contract does NOT enumerate catalog entries; entries are line-declared and may evolve outside this packet

## Cross-binding rules

- Roles declared here are consumed by `digital_anchor_speaker_plan.segments[].binds_role_id`; every consumed `role_id` MUST be declared here
- A role MAY be consumed by zero or more segments; unconsumed roles are admissible (e.g. fallback roles), but MUST still satisfy this contract
- The role pack MUST NOT redeclare any field shape owned by `factory_input_contract_v1` or `factory_content_structure_contract_v1` (validator rule R2)

## Forbidden

- any avatar-engine / render-engine / voice-model / TTS-provider name (validator rule R3)
- any `status` / `ready` / `done` / `phase` / `current_attempt` / `delivery_ready` field (validator rule R5)
- any embed of the full `factory_input` or `factory_content_structure` record shape (validator rule R2)
- any embedded appearance asset (image, mesh, motion data) — assets are referenced by `appearance_ref` only
- any donor (SwiftCraft) module path or module-level reference

## Surface implications

For Phase B (Surface Freeze), design MUST:

- render role collection slots only for the framing-kinds declared in the active packet
- expose `appearance_ref` only as a resolved catalog handle, never as a vendor or engine id
- never surface `framing_kind_set` or `appearance_ref_kind_set` membership as user-visible terminology

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
