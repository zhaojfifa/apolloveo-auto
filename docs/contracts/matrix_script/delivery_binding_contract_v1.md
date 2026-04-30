# Matrix Script Delivery Binding Contract v1

Date: 2026-04-28
Status: Phase C landing (Matrix Script First Production Line Wave — Delivery Binding)
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` Phase C
- `docs/contracts/matrix_script/task_entry_contract_v1.md`
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `docs/contracts/factory_delivery_contract_v1.md`

## Purpose

Define the formal Delivery Binding for Matrix Script. This surface turns the frozen Matrix Script packet into a read-only delivery-center projection for:

1. visible Matrix Script deliverables;
2. `result_packet_binding` visualization;
3. delivery manifest / metadata display;
4. Phase D publish feedback deferral.

This contract does **not** implement publish feedback write-back, provider controls, runtime orchestration, packet/schema redesign, or any Digital Anchor / Hot Follow / W2.2 / W2.3 scope.

## Projection object

The formal Phase C surface is named `matrix_script_delivery_binding_v1`.

It is produced by projecting a Matrix Script packet instance through:

`gateway.app.services.matrix_script.delivery_binding.project_delivery_binding(packet)`

The projection returns these top-level sections:

| Section | Purpose | Source |
|---|---|---|
| `delivery_pack` | Delivery-center visible deliverable rows | packet `binding`, `line_specific_refs[]`, and `binding.capability_plan[]` |
| `result_packet_binding` | Packet/ref/cell-slot binding visualization | packet `generic_refs[]`, `line_specific_refs[]`, `binding`, and line deltas |
| `manifest` | Read-only delivery manifest display | packet identity, binding profile refs, source refs, metadata, and validator evidence |
| `metadata_projection` | Operator-facing metadata display | packet `metadata` plus line identity |
| `phase_d_deferred` | Explicit publish feedback closure deferral | contract-owned fixed labels only |

## Visible deliverables

Phase C makes these deliverable rows visible in the Matrix Script delivery center:

| Deliverable id | Kind | Required | Source |
|---|---|---|---|
| `matrix_script_variation_manifest` | `variation_manifest` | yes | `line_specific_refs[ref_id=matrix_script_variation_matrix]` |
| `matrix_script_slot_bundle` | `script_slot_bundle` | yes | `line_specific_refs[ref_id=matrix_script_slot_pack]` |
| `matrix_script_subtitle_bundle` | `subtitle_bundle` | follows `capability_plan[kind=subtitles].required` | `binding.capability_plan[kind=subtitles]` + slot language scopes |
| `matrix_script_audio_preview` | `audio_preview` | follows `capability_plan[kind=dub].required` | `binding.capability_plan[kind=dub]` |
| `matrix_script_scene_pack` | `scene_pack` | follows `capability_plan[kind=pack].required` | `binding.capability_plan[kind=pack]` |

Rows are projections only. They do not prove artifact existence, freshness, publishability, or final delivery readiness.

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
| `cell_slot_bindings[]` | `variation_matrix.delta.cells[].script_slot_ref` joined to `slot_pack.delta.slots[].slot_id` |

`result_packet_binding` is delivery visualization. It must not mutate packet refs, resolve storage providers, call workers, or create runtime task state.

## Manifest / metadata behavior

The Phase C manifest is a read-only derived display:

| Manifest field | Source |
|---|---|
| `manifest_id` | fixed `matrix_script_delivery_manifest_v1` |
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

- `variation_id` feedback;
- publish URL;
- publish status;
- channel metrics;
- operator publish notes;
- feedback closure records.

## Forbidden

The Delivery Binding must not introduce:

- publish feedback write-back;
- provider / model / vendor / engine controls;
- Digital Anchor fields;
- Hot Follow behavior;
- W2.2 / W2.3 scope;
- packet/schema redesign;
- runtime/provider orchestration;
- truth-shape state fields such as `delivery_ready`, `final_ready`, `publishable`, `current_attempt`, `status`, `done`.

## Acceptance

Phase C is green only when:

1. the delivery projection is derived from the Matrix Script packet sample without packet mutation;
2. visible deliverables are explicit and sourced from packet binding / refs / capability plan only;
3. `result_packet_binding` includes binding profile refs and cell-to-slot visualization without storage/provider resolution;
4. manifest and metadata are read-only, phase-correct projections;
5. publish feedback write-back is explicitly absent and deferred to Phase D;
6. tests prove no provider controls, Digital Anchor, Hot Follow behavior, W2.2 / W2.3 scope, or packet/schema redesign was introduced.

## Remaining blockers before Phase D

Phase D may not start until this Phase C delivery binding is reviewed and accepted. Phase D must define publish feedback closure separately, including variation-level feedback and write-back behavior, without changing the Phase C delivery projection into a mutable feedback owner.
