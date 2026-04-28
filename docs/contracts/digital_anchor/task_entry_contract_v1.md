# Digital Anchor Task Entry Contract v1

Date: 2026-04-28
Status: Phase A landing (Digital Anchor Second Production Line Wave — Phase A: Task / Role Entry)
Authority:
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Part III P2
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
- `docs/baseline/PRODUCT_BASELINE.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `schemas/packets/digital_anchor/packet.schema.json`
- `schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md` (digital_anchor row)
- `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`

## Purpose

Declare the **operator-facing task / role entry surface** by which a Digital Anchor task is initiated, and the **mapping rule** by which that entry projects onto the frozen Digital Anchor packet truth (`schemas/packets/digital_anchor/packet.schema.json` + `docs/contracts/digital_anchor/packet_v1.md` + the line-specific `digital_anchor_role_pack` and `digital_anchor_speaker_plan` contracts).

This contract is the Phase A deliverable of the Digital Anchor Second Production Line Wave. It does not author packet truth; it declares which operator inputs are accepted at task creation, and which packet fields each input is allowed to seed.

## Ownership

- Owner: product (entry-surface author) + design (surface mapping)
- Runtime consumers: future task-creation path (Phase B+), packet validator (rejects vendor pins / state fields regardless of entry origin)
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, provider adapters, frontend platform

## Scope discipline (normative)

This contract:
1. defines the **closed set** of fields the Digital Anchor task / role entry MAY accept;
2. classifies each field as **line truth** (projects onto a packet field) or **operator hint** (seeds a packet authoring step but is itself non-truth);
3. classifies each field as **required**, **optional**, or **deferred**;
4. names what entry-time inputs are explicitly **forbidden** (provider/model selection, status-shape fields, donor-side concepts);
5. names what is **deferred** to Phase B (Workbench Role / Speaker Surface), Phase C (Delivery Binding), Phase D (Publish Feedback Closure) — none of those phases are in this wave's Phase A landing.

This contract does NOT:
- define runtime task-creation behavior;
- redeclare packet truth;
- introduce a second source of state or task truth;
- name vendors / models / providers / engines / avatar-engines / TTS-providers / lip-sync-engines (validator rule R3);
- attach truth-shape state fields (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`) to any entry field (validator rule R5);
- re-version the Digital Anchor packet, schema, or sample;
- touch any Matrix Script contract;
- touch Hot Follow;
- touch W2.2 / W2.3.

## Entry field set (closed)

The Digital Anchor task / role entry accepts exactly the fields below. The set is closed at v1; additions require a re-version of this contract.

| entry field                  | discipline | classification     | line truth?      | seeds (packet path)                                                                                                  | authority (generic / line contract)                                                  |
| ---------------------------- | ---------- | ------------------ | ---------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `topic`                      | required   | operator hint      | no               | `metadata.notes` (free-form trail) + downstream Phase B authoring seed                                                | `factory_input_contract_v1` (operator metadata envelope)                             |
| `source_script_ref`          | required   | line truth (asset) | yes (opaque ref) | downstream `digital_anchor_speaker_plan.delta.segments[].script_ref` (Phase B authoring; entry only carries the opaque handle) | `factory_input_contract_v1` (`source_script` per `asset_supply_matrix_v1`)            |
| `language_scope`             | required   | line truth         | yes              | `digital_anchor_role_pack.delta.roles[].language_scope_ref` + `digital_anchor_speaker_plan.delta.segments[].language_pick` (Phase B authoring binds per role/segment) | `factory_language_plan_contract_v1` (`g_lang`)                                       |
| `role_profile_ref`           | required   | line truth (asset) | yes (opaque ref) | downstream `digital_anchor_role_pack.delta.roles[].appearance_ref` (Phase B authoring resolves the catalog handle into a role card / role pose set) | `factory_input_contract_v1` (`role_appearance_ref` per `asset_supply_matrix_v1`)      |
| `role_framing_hint`          | required   | operator hint      | no               | seeds Phase B selection within `digital_anchor_role_pack.delta.framing_kind_set` (operator picks among `head` / `half_body` / `full_body`; the hint never widens the set) | `digital_anchor_role_pack` line-specific contract                                    |
| `output_intent`              | required   | operator hint      | no               | `metadata.notes` (free-form trail); does NOT bind delivery — delivery binding is Phase C                              | `factory_input_contract_v1` (operator metadata envelope)                             |
| `speaker_segment_count_hint` | required   | operator hint      | no               | seeds Phase B authoring of `digital_anchor_speaker_plan.delta.segments[]` cardinality; does NOT itself become a packet field | `digital_anchor_speaker_plan` line-specific contract                                  |
| `dub_kind_hint`              | optional   | operator hint      | no               | seeds Phase B selection within `digital_anchor_speaker_plan.delta.dub_kind_set` (operator picks among `tts_neutral` / `tts_role_voice` / `source_passthrough`; hint never widens the set) | `digital_anchor_speaker_plan` line-specific contract                                  |
| `lip_sync_kind_hint`         | optional   | operator hint      | no               | seeds Phase B selection within `digital_anchor_speaker_plan.delta.lip_sync_kind_set` (operator picks among `tight` / `loose` / `none`; hint never widens the set) | `digital_anchor_speaker_plan` line-specific contract                                  |
| `scene_binding_hint`         | optional   | operator hint      | no               | seeds Phase B authoring of `digital_anchor_speaker_plan` ↔ `g_scene` binding decisions (segment-to-scene placement); does NOT itself become a packet field | `factory_scene_plan_contract_v1` (`g_scene`)                                          |
| `operator_notes`             | optional   | operator hint      | no               | `metadata.notes`                                                                                                       | `factory_input_contract_v1` (operator metadata envelope)                             |

Required vs optional discipline matches the `digital_anchor` column of `docs/product/asset_supply_matrix_v1.md`:

- `source_script` row → `source_script_ref` required at entry;
- `language_scope_decl` row → `language_scope` required at entry;
- `role_appearance_ref` row → `role_profile_ref` required at entry.

Other entry fields are operator hints and are required only as authoring scaffolding for Phase B; they never become packet line truth.

## Line-truth vs operator-hint rule

- **Line truth** entries are the only entries that appear (after Phase B authoring) inside the packet's `line_specific_refs[].delta` blocks or generic-ref shapes. Line-truth content is owned by the packet, never by the entry surface.
- **Operator hint** entries seed Phase B authoring decisions but are themselves stored only as free-form trail in `metadata.notes` (or carried in an out-of-packet authoring scratch — to be defined in Phase B). They MUST NOT mutate any closed kind-set (`framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`).
- An entry surface that promotes an operator hint into a packet truth field without going through Phase B authoring is a **violation** of this contract.

## Required vs optional (entry-time)

- Required: `topic`, `source_script_ref`, `language_scope`, `role_profile_ref`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint`.
  - `source_script_ref`, `language_scope`, and `role_profile_ref` are required by the asset supply matrix for the `digital_anchor` line; absence MUST block task creation.
  - `topic`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint` are required by this entry contract as the minimum operator-hint scaffolding so Phase B authoring has enough seed to construct a non-trivial role pack and speaker plan; absence MUST block task creation at the entry surface, but their absence is NOT a packet-truth gate (the packet validator does not see them).
- Optional: `dub_kind_hint`, `lip_sync_kind_hint`, `scene_binding_hint`, `operator_notes`.

## Deferred to later phases (entry surface MUST NOT collect)

The following are explicitly out of scope for Phase A entry. Any attempt to collect them at task entry is a violation of this contract.

| concern                                                                          | deferred to                                                       |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| explicit `digital_anchor_role_pack.delta.roles[]` enumeration (role_id, framing_kind, language_scope_ref, appearance_ref) | Phase B (Workbench Role / Speaker Surface)                        |
| explicit `digital_anchor_speaker_plan.delta.segments[]` authoring (segment_id, binds_role_id, script_ref, dub_kind, lip_sync_kind, language_pick) | Phase B (Workbench Role / Speaker Surface)                        |
| `binding.capability_plan[]` authoring (kinds, modes, required flags)              | static-by-line per `docs/contracts/digital_anchor/packet_v1.md` §Capability plan; NEVER an entry-surface concern |
| `delivery` binding, manifest, deliverable selection                               | Phase C (Delivery Binding)                                        |
| `result_packet_binding` deliverable wiring                                        | Phase C (Delivery Binding)                                        |
| `publish_feedback` projection / per-segment or per-role feedback                  | Phase D (Publish Feedback Closure)                                |
| provider / model / vendor / engine / avatar-engine / TTS-provider / lip-sync-engine selection | **never** at entry surface (validator R3)                |
| status / ready / done / delivery_ready / final_ready / publishable                | **never** at entry surface (validator R5)                         |
| donor (SwiftCraft) module identity                                                | **never** at entry surface                                        |
| Matrix Script concerns (variation matrix, slot pack, target_platform pick)        | out of this wave entirely                                          |
| Hot Follow concerns                                                               | out of this wave entirely                                          |
| W2.2 / W2.3 concerns                                                              | out of this wave entirely                                          |

## Forbidden at entry surface

- Any field named or shaped as `vendor_id`, `model_id`, `provider_id`, `engine_id`, or any avatar-engine / TTS-provider / lip-sync-engine identifier (validator R3).
- Any field named or shaped as `current_attempt`, `delivery_ready`, `final_ready`, `publishable`, or any other state-shape field (validator R5; restated by packet schema `metadata.not.anyOf`).
- Any donor-side concept: `donor_*`, `swiftcraft_*`, absorption-module names.
- Any second source of task / state truth (envelope §Forbidden).
- Any cross-line concern (Matrix Script, Hot Follow, VideoGen, FaceSwap).
- Any frontend exposure of `vendor_id` / `model_id` / `donor_*` per `docs/product/asset_supply_matrix_v1.md` §Decoupling rules item 7.
- Any embed of role-pack appearance assets, audio waveforms, or script bodies — entries carry opaque references only.
- Any extension of `framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, or `lip_sync_kind_set` from the entry surface — closed kind-sets are owned by line-specific contracts.

## Mapping note (entry → packet)

Notation: `entry.<field>  →  packet.<json-pointer-ish path>`.

```
entry.topic                       →  metadata.notes (appended; non-truth trail)
entry.source_script_ref           →  (Phase B authoring)
                                     line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.segments[*].script_ref
                                     (entry carries opaque handle only; resolution to per-segment script bodies is Phase B)
entry.language_scope              →  (Phase B authoring)
                                     line_specific_refs[ref_id="digital_anchor_role_pack"].delta.roles[*].language_scope_ref
                                     + line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.segments[*].language_pick
                                     bound by g_lang allowed values
entry.role_profile_ref            →  (Phase B authoring)
                                     line_specific_refs[ref_id="digital_anchor_role_pack"].delta.roles[*].appearance_ref
                                     (entry carries opaque catalog handle; appearance kind constrained by role_pack.delta.appearance_ref_kind_set)
entry.role_framing_hint           →  (Phase B authoring scaffold) selection within
                                     line_specific_refs[ref_id="digital_anchor_role_pack"].delta.framing_kind_set
                                     (hint never widens the closed set)
entry.output_intent               →  metadata.notes (appended; non-truth trail)
                                     (delivery target binding is Phase C)
entry.speaker_segment_count_hint  →  (Phase B authoring scaffold) drives count of
                                     line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.segments[]
                                     (does NOT appear as a packet field)
entry.dub_kind_hint               →  (Phase B authoring scaffold) selection within
                                     line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.dub_kind_set
entry.lip_sync_kind_hint          →  (Phase B authoring scaffold) selection within
                                     line_specific_refs[ref_id="digital_anchor_speaker_plan"].delta.lip_sync_kind_set
entry.scene_binding_hint          →  (Phase B authoring scaffold) per-segment binding into g_scene
                                     (does NOT appear as a packet field)
entry.operator_notes              →  metadata.notes (appended; non-truth trail)
```

Mapping discipline:

- Only `entry.source_script_ref`, `entry.language_scope`, and `entry.role_profile_ref` cross from entry surface to packet **truth** (line-specific delta). All other entries cross only to `metadata.notes` (non-truth trail) or to Phase B authoring scaffolding (out of packet entirely).
- Closed kind-sets (`framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`) are NOT widened by any entry field. Hints select among existing values; they never add values.
- `binding.capability_plan[]`, `binding.worker_profile_ref`, `binding.deliverable_profile_ref`, `binding.asset_sink_profile_ref` are **NOT** populated from the entry surface. They are static for the Digital Anchor line per `docs/contracts/digital_anchor/packet_v1.md` §Capability plan and §Binding profiles.
- `evidence.ready_state` is **NOT** writable from the entry surface. `ready_state` is one-way projection from validator output (`docs/design/surface_task_area_lowfi_v1.md` §Gate Truth Rule).
- The cross-binding rule "every `segments[].binds_role_id` resolves to a `roles[].role_id`" (per `digital_anchor_speaker_plan` §Cross-binding rules) is enforced at Phase B authoring time, not at entry time. The entry surface MUST NOT collect any `binds_role_id` value.

## Acceptance (Phase A)

Phase A is green only when:

1. The entry field set above is the exact closed set used by any Digital Anchor task-creation surface.
2. Every required entry field is collected; absence blocks task creation at entry.
3. No forbidden field is collected, displayed, or stored at entry.
4. Every line-truth entry maps onto a packet path that is reachable from the existing Digital Anchor schema/contracts; no new packet field is invented.
5. Every operator-hint entry maps either to `metadata.notes` or to Phase B authoring scaffolding; none is promoted to packet truth at entry time.
6. Implementation, if any, is Digital-Anchor-only; no code path under `matrix_script`, no provider/adapter touch, no Hot Follow business-logic change, no W2.2 / W2.3 movement.

## What Phase A intentionally does NOT add

- No workbench role / speaker authoring surface (Phase B).
- No delivery center binding (Phase C).
- No publish feedback projection (Phase D).
- No provider / model / vendor / avatar-engine / TTS-provider / lip-sync-engine selection control (forbidden at all phases).
- No new packet schema / sample / contract version.
- No mutation of Matrix Script contracts to fit Digital Anchor.
- No Hot Follow change.
- No W2.2 / W2.3 advancement.
- No frontend platform rebuild.
- No runtime task-creation implementation in this Phase A landing — this contract is the surface-first definition; engineering implementation is sequenced separately and bounded by this contract.

## Remaining blockers before Phase B

1. Phase B requires this Phase A entry contract to be reviewed and accepted as the authority for the operator-supplied seed feeding workbench role / speaker authoring.
2. Phase B requires the workbench authoring surface to consume the `entry.*` seed without re-authoring it — i.e. the workbench MUST start from this entry's projection into `metadata.notes` and Phase B authoring scaffolding, not from a freshly invented form.
3. Phase B requires `framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, and `lip_sync_kind_set` to remain frozen as declared in `docs/contracts/digital_anchor/role_pack_contract_v1.md` and `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`; this Phase A contract relies on that freeze to keep `role_framing_hint` / `dub_kind_hint` / `lip_sync_kind_hint` mapping stable.
4. Phase B requires the role↔segment cross-binding rule (every `segments[].binds_role_id` resolves to a `roles[].role_id`) to be authored at workbench time, not at entry time.

## References

- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
- `docs/baseline/PRODUCT_BASELINE.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `schemas/packets/digital_anchor/packet.schema.json`
- `schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`
