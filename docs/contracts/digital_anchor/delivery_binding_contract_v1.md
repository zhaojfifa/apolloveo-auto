# Digital Anchor Delivery Binding Contract v1

Date: 2026-04-28
Status: Phase C landing (Digital Anchor Second Production Line Wave - Delivery Binding)
Authority:
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Part III P2
- `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `schemas/packets/digital_anchor/packet.schema.json`
- `docs/contracts/factory_delivery_contract_v1.md`

## Purpose

Define the formal Delivery Binding for Digital Anchor. This surface turns the frozen Digital Anchor packet into a read-only delivery-center projection for:

1. visible Digital Anchor deliverables;
2. `result_packet_binding` visualization;
3. delivery manifest / metadata display;
4. Phase D publish feedback deferral.

This contract does **not** implement publish feedback write-back, provider controls, runtime orchestration, packet/schema redesign, or any Matrix Script / Hot Follow / W2.2 / W2.3 scope.

## Phase B boundary rule

Phase C defines delivery binding separately from the Phase B Workbench Role / Speaker Surface.

Phase C may consume the same packet truth that Phase B projects, but it must not mutate `digital_anchor_workbench_role_speaker_surface_v1`, must not make `scene_binding_projection` an owner, and must not turn role / speaker workbench rows into delivery truth.

## Projection object

The formal Phase C surface is named `digital_anchor_delivery_binding_v1`.

It is produced by projecting a Digital Anchor packet instance through:

`gateway.app.services.digital_anchor.delivery_binding.project_delivery_binding(packet)`

The projection returns these top-level sections:

| Section | Purpose | Source |
|---|---|---|
| `delivery_pack` | Delivery-center visible deliverable rows | packet `binding`, `line_specific_refs[]`, and `binding.capability_plan[]` |
| `result_packet_binding` | Packet/ref/role-segment binding visualization | packet `generic_refs[]`, `line_specific_refs[]`, `binding`, role pack delta, and speaker plan delta |
| `manifest` | Read-only delivery manifest display | packet identity, binding profile refs, source refs, metadata, and validator evidence |
| `metadata_projection` | Operator-facing metadata display | packet `metadata` plus line identity |
| `phase_d_deferred` | Explicit publish feedback closure deferral | contract-owned fixed labels only |

## Visible deliverables

Phase C makes these deliverable rows visible in the Digital Anchor delivery center:

| Deliverable id | Kind | Required | Source |
|---|---|---|---|
| `digital_anchor_role_manifest` | `role_manifest` | yes | `line_specific_refs[ref_id=digital_anchor_role_pack]` |
| `digital_anchor_speaker_segment_bundle` | `speaker_segment_bundle` | yes | `line_specific_refs[ref_id=digital_anchor_speaker_plan]` |
| `digital_anchor_subtitle_bundle` | `subtitle_bundle` | follows `capability_plan[kind=subtitles].required` | `binding.capability_plan[kind=subtitles]` + speaker language picks |
| `digital_anchor_audio_bundle` | `audio_bundle` | follows `capability_plan[kind=dub].required` | `binding.capability_plan[kind=dub]` |
| `digital_anchor_lip_sync_bundle` | `lip_sync_bundle` | follows `capability_plan[kind=lip_sync].required` | `binding.capability_plan[kind=lip_sync]` |
| `digital_anchor_scene_pack` | `scene_pack` | follows `capability_plan[kind=pack].required` | `binding.capability_plan[kind=pack]` + `g_scene` reference presence |

Rows are projections only. They do not prove artifact existence, freshness, publishability, final delivery readiness, provider selection, or runtime execution.

## Result packet binding visualization

`result_packet_binding` shows how packet truth is bound for delivery display:

| Projection field | Packet source |
|---|---|
| `generic_refs[]` | `generic_refs[].ref_id` |
| `line_specific_refs[]` | `line_specific_refs[].ref_id` |
| `binding_profile_refs.worker_profile_ref` | `binding.worker_profile_ref` |
| `binding_profile_refs.deliverable_profile_ref` | `binding.deliverable_profile_ref` |
| `binding_profile_refs.asset_sink_profile_ref` | `binding.asset_sink_profile_ref` |
| `capability_plan[]` | `binding.capability_plan[]` as kind/mode/required only |
| `role_segment_bindings[]` | `speaker_plan.delta.segments[].binds_role_id` joined to `role_pack.delta.roles[].role_id` |

`result_packet_binding` is delivery visualization. It must not mutate packet refs, resolve storage providers, call workers, or create runtime task state.

## Manifest / metadata behavior

The Phase C manifest is a read-only derived display:

| Manifest field | Source |
|---|---|
| `manifest_id` | fixed `digital_anchor_delivery_manifest_v1` |
| `line_id` | packet `line_id` |
| `packet_version` | packet `packet_version` |
| `deliverable_profile_ref` | `binding.deliverable_profile_ref` |
| `asset_sink_profile_ref` | `binding.asset_sink_profile_ref` |
| `source_refs.generic` | `generic_refs[].ref_id` |
| `source_refs.line_specific` | `line_specific_refs[].ref_id` |
| `metadata` | packet `metadata` |
| `validator_report_path` | `evidence.validator_report_path` |
| `packet_ready_state` | `evidence.ready_state` |

Manifest fields are delivery display truth only. They are not delivery artifact truth and do not create publish feedback truth.

## Read-only vs mutable

Read-only in Phase C:

- deliverable rows;
- result packet binding visualization;
- manifest;
- metadata projection;
- validator report path and packet ready state display.

Mutable only in Phase D:

- role-level publish feedback;
- segment-level publish feedback;
- publish URL;
- publish status;
- channel metrics;
- operator publish notes;
- feedback closure records.

## Forbidden

The Delivery Binding must not introduce:

- publish feedback write-back;
- provider / model / vendor / engine controls;
- avatar-engine / TTS-provider / lip-sync-engine controls;
- Matrix Script fields or contract mutation;
- Hot Follow behavior;
- W2.2 / W2.3 scope;
- packet/schema/sample redesign;
- runtime/provider orchestration;
- truth-shape state fields such as `delivery_ready`, `final_ready`, `publishable`, `current_attempt`, `status`, `done`.

## Acceptance

Phase C is green only when:

1. the delivery projection is derived from the Digital Anchor packet sample without packet mutation;
2. visible deliverables are explicit and sourced from packet binding / refs / capability plan only;
3. `result_packet_binding` includes binding profile refs and role-to-segment visualization without storage/provider resolution;
4. manifest and metadata are read-only, phase-correct projections;
5. publish feedback write-back is explicitly absent and deferred to Phase D;
6. tests prove no provider controls, Matrix Script mutation, Hot Follow behavior, W2.2 / W2.3 scope, or packet/schema/sample redesign was introduced.

## Remaining blockers before Phase D

Phase D may not start until this Phase C delivery binding is reviewed and accepted. Phase D must define publish feedback closure separately, including role-level and segment-level feedback behavior, without changing the Phase C delivery projection into a mutable feedback owner.
