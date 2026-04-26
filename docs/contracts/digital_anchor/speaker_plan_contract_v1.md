# Digital Anchor · Speaker Plan Contract v1

Date: 2026-04-26
Status: Frozen for P2 entry review (line-specific delta contract; consumed by packet validator)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`; parent packet `docs/contracts/digital_anchor/packet_v1.md`
Owner: Product
Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Purpose

Declare the **speaker plan delta** that the Digital Anchor line adds on top of the factory-generic audio, language, and scene-plan contracts. The speaker plan declares per-segment dub kind, lip-sync kind, language pick, and the binding to the role that owns the segment — at the level of *kinds*, never at the level of TTS vendors, lip-sync engines, or render providers.

This contract describes:

- the closed dub-kind set the plan may use
- the closed lip-sync-kind set the plan may use
- the shape of `segments[]` declarations
- the prohibitions that keep the speaker plan free of state truth, vendor pins, and embedded audio

This contract does NOT describe TTS runtime, lip-sync runtime, donor absorption, provider clients, or any second source of task / state truth.

## Identity

- `ref_id`: `digital_anchor_speaker_plan`
- `binds_to`: `g_audio`, `g_lang`, `g_scene`
- Parent packet: `docs/contracts/digital_anchor/packet_v1.md`
- Version: `v1`

## Closed sets

- `dub_kind_set`: `{tts_neutral, tts_role_voice, source_passthrough}` — adding a kind requires a packet re-version
- `lip_sync_kind_set`: `{tight, loose, none}` — adding a kind requires a packet re-version

## Delta fields

### `segments[]`

Ordered list of speaker segments. Each entry declares:

| field            | type            | notes                                                                          |
| ---------------- | --------------- | ------------------------------------------------------------------------------ |
| `segment_id`     | string (stable) | unique within the packet                                                       |
| `binds_role_id`  | string          | id of a `digital_anchor_role_pack.roles[]` entry that owns this segment        |
| `script_ref`     | string (opaque) | content reference (e.g. content storage key); script text MUST NOT be embedded |
| `dub_kind`       | enum            | one of `dub_kind_set`                                                          |
| `lip_sync_kind`  | enum            | one of `lip_sync_kind_set`                                                     |
| `language_pick`  | string          | language token drawn from the role's `language_scope_ref` allowed values       |

Rules:

- `segment_id` MUST be unique within the packet
- `binds_role_id` MUST resolve to a role declared in the sibling `digital_anchor_role_pack`
- `language_pick` MUST be a member of the language-scope referenced by the bound role
- `dub_kind = source_passthrough` requires a corresponding source audio reference reachable via `g_audio`; the packet itself MUST NOT embed audio
- `lip_sync_kind = none` is admissible (e.g. for off-camera narration); the packet MUST NOT mark this as a degraded state
- `script_ref` MUST be opaque and dereferenceable by content storage — the plan does not embed script text

## Cross-binding rules

- Every consumed `binds_role_id` MUST resolve to a role declared in `digital_anchor_role_pack`
- A role MAY be consumed by zero or more segments
- The plan MUST NOT redeclare any field shape owned by `factory_audio_plan_contract_v1`, `factory_language_plan_contract_v1`, or `factory_scene_plan_contract_v1` (validator rule R2)
- Subtitle authority follows `g_lang`'s single-owner rule; the plan MUST NOT override it

## Forbidden

- any TTS-provider / voice-model / lip-sync-engine / render-engine name (validator rule R3)
- any `status` / `ready` / `done` / `phase` / `current_attempt` / `delivery_ready` field (validator rule R5)
- any embed of the full `factory_audio_plan`, `factory_language_plan`, or `factory_scene_plan` record shape (validator rule R2)
- any embedded audio waveform, viseme stream, or lip-sync timing payload — these are runtime artifacts
- any donor (SwiftCraft) module path or module-level reference

## Surface implications

For Phase B (Surface Freeze), design MUST:

- render dub-kind and lip-sync-kind selectors only for the kinds declared in the active packet
- never expose TTS-provider, voice-model, or lip-sync-engine choice to the operator
- never surface `dub_kind_set` or `lip_sync_kind_set` membership as user-visible terminology

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
