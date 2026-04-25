# Digital Anchor Line Packet v1

Date: 2026-04-26
Status: Frozen for P2 entry review (product packet freeze, awaiting validator + onboarding gate evidence)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`

## Purpose

Declare the **truth interface** of the Digital Anchor production line as a packet, so the factory packet validator and onboarding gate can admit it without any runtime, donor, or vendor knowledge.

This packet describes:

- which factory-generic contracts the line consumes
- which line-specific objects the line adds (role pack, speaker plan)
- which capability kinds the line declares (closed kinds only; no vendors)
- which reference evidence backs onboarding readiness (Hot Follow green baseline)

This packet does NOT describe runtime behavior, donor absorption, provider clients, avatar engines, or any second source of task / state truth.

## Ownership

- Packet owner: product (line packet author)
- Runtime consumers: packet validator, onboarding gate, line registration
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Line identity

- `line_id`: `digital_anchor`
- `packet_version`: `v1`
- Reference line for evidence: `hot_follow`

## Generic contract references

The Digital Anchor line consumes the six factory-generic contracts unmodified. Each ref is reachable via the envelope's `generic_refs[]`:

| ref_id     | path                                                        | version |
| ---------- | ----------------------------------------------------------- | ------- |
| `g_input`  | `docs/contracts/factory_input_contract_v1.md`               | v1      |
| `g_struct` | `docs/contracts/factory_content_structure_contract_v1.md`   | v1      |
| `g_scene`  | `docs/contracts/factory_scene_plan_contract_v1.md`          | v1      |
| `g_audio`  | `docs/contracts/factory_audio_plan_contract_v1.md`          | v1      |
| `g_lang`   | `docs/contracts/factory_language_plan_contract_v1.md`       | v1      |
| `g_deliv`  | `docs/contracts/factory_delivery_contract_v1.md`            | v1      |

The Digital Anchor line MUST NOT redeclare any field shape owned by these generic contracts (validator rule R2).

## Line-specific objects

Two line-specific contracts extend the generic refs via `binds_to`. Each declares ONLY delta fields. Neither may carry truth-shape state fields (R5) nor vendor pins (R3).

### LS1 · `digital_anchor_role_pack`

Binds to: `g_input`, `g_struct`

Purpose: declare the on-screen anchor role catalog this packet authorizes — the role identity, framing, and language scope, without naming any avatar engine, model, or vendor.

Delta fields:

- `roles[]` — declared anchor roles; each entry declares:
  - `role_id` — stable id within this packet
  - `display_name` — non-truth label for editorial / UI use
  - `framing_kind` — drawn from `framing_kind_set`
  - `language_scope_ref` — id of a `g_lang` allowed scope this role is permitted to speak in
  - `appearance_ref` — opaque catalog reference (e.g. role-card storage key); the packet does not embed appearance assets
  - `notes` — non-truth descriptive string (optional)
- `framing_kind_set` — closed set: `{head, half_body, full_body}`; additions require packet re-version
- `appearance_ref_kind_set` — closed set: `{role_card, role_pose_set}`; additions require packet re-version

Forbidden in LS1:

- any avatar `engine` / `model` / `provider` field (R3)
- any `status` / `ready` / `is_publishable` field (R5)
- any embed of the full `factory_input` or `factory_content_structure` record shape (R2)
- any donor module path (envelope §Forbidden)

### LS2 · `digital_anchor_speaker_plan`

Binds to: `g_audio`, `g_lang`, `g_scene`

Purpose: declare the per-segment speaker plan that binds a role to a script segment, declares lip-sync expectations, and declares dub kind expectations — all as planning intent, never as runtime state or vendor selection.

Delta fields:

- `segments[]` — ordered list of speaker segments; each entry declares:
  - `segment_id` — stable id within this packet
  - `binds_role_id` — id of the `digital_anchor_role_pack.roles[]` entry that owns this segment
  - `script_ref` — opaque content reference to the script body for this segment
  - `dub_kind` — drawn from `dub_kind_set`
  - `lip_sync_kind` — drawn from `lip_sync_kind_set`
  - `language_pick` — single language token drawn from the role's `language_scope_ref`
- `dub_kind_set` — closed set: `{tts_neutral, tts_role_voice, source_passthrough}`; additions require packet re-version
- `lip_sync_kind_set` — closed set: `{tight, loose, none}`; additions require packet re-version

Forbidden in LS2:

- any vendor / engine / model name (R3)
- any `delivery_ready` / `final_ready` / `done` field (R5)
- any subtitle authority override that contradicts `g_lang`'s single-owner rule
- any donor module path (envelope §Forbidden)

## Capability plan (kinds only)

Capability kinds declared by Digital Anchor, drawn from the closed kind set in validator rule R3. Vendor selection is performed by `capability_routing_policy_v1` at runtime; the packet MUST NOT pin any vendor, model, provider, or engine.

| kind          | required | mode      | notes                                              |
| ------------- | -------- | --------- | -------------------------------------------------- |
| `understanding` | yes    | analyze   | derive structural understanding of source script   |
| `avatar`        | yes    | role_render | render anchor role per `role_pack` entry         |
| `speaker`       | yes    | segment_speak | bind role + script segment per `speaker_plan` |
| `subtitles`     | yes    | author    | authoritative subtitle ownership per `g_lang`      |
| `dub`           | yes    | tts       | voice realization per `dub_kind`                   |
| `lip_sync`      | optional | sync     | required only when `lip_sync_kind ≠ none`          |
| `pack`          | optional | bundle   | optional scene-pack derivative (non-blocking)      |

`mode` values are descriptive hints, not provider selectors.

## Binding profiles

Declared at envelope level in `binding`:

- `worker_profile_ref`: `worker_profile_digital_anchor_v1` (resolved by worker gateway; not embedded here)
- `deliverable_profile_ref`: `deliverable_profile_digital_anchor_v1`
- `asset_sink_profile_ref`: `asset_sink_profile_digital_anchor_v1`

These are referenced by id only. Their declarations live outside this packet (worker gateway / delivery contracts).

## Evidence

Onboarding evidence object declared at envelope level in `evidence`:

- `reference_line`: `hot_follow`
- `reference_evidence_path`: `docs/contracts/hot_follow_line_contract.md`
- `validator_report_path`: `docs/execution/logs/packet_validator_digital_anchor_v1.json` (written by validator on first run; absent before first validation)
- `ready_state`: `draft` (transitions per envelope E4)

`ready_state` is the only readiness field permitted in this packet (envelope E4 / validator R5).

## Forbidden in this packet

Cross-cutting prohibitions inherited from the envelope and validator rules; restated here for product clarity:

- vendor / model / provider / engine / avatar-engine names (R3)
- truth-shape state fields: `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, etc. (R5)
- direct embed of any generic contract's full record shape inside line-specific objects (R2)
- references to donor (SwiftCraft) module paths (envelope §Forbidden)
- any second source of task / state truth

## Lifecycle

Per envelope E4:

```
draft  →  validating  →  ready  →  frozen
                    ↘
                      gated  (validator failures or onboarding gate blocked)
```

The packet author submits `draft`; the validator promotes through `validating`; the onboarding gate emits `passed`/`blocked`/`pending`; only `passed` packets at `ready_state = ready` are eligible for runtime onboarding (P3).

## Schema and samples

- Schema: `schemas/packets/digital_anchor/packet.schema.json` (Draft 2020-12)
- Samples: `schemas/packets/digital_anchor/sample/*.json`
- `$id`: `apolloveo://packets/digital_anchor/v1`

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
