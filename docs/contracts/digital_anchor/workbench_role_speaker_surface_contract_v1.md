# Digital Anchor Workbench Role / Speaker Surface Contract v1

Date: 2026-04-28
Status: Phase B landing (Digital Anchor Second Production Line Wave — Workbench Role / Speaker Surface)
Authority:
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` Part I Q5 / Part III P2
- `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `schemas/packets/digital_anchor/packet.schema.json`
- `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`

## Purpose

Define the formal Workbench Role / Speaker Surface for Digital Anchor. This surface turns the frozen Digital Anchor packet into a read-only workbench projection for:

1. role pack review;
2. speaker plan review;
3. role ↔ segment binding review;
4. scene binding projection notes at workbench scope;
5. attribution / refs inspection.

This contract does **not** create delivery binding, publish feedback write-back, provider controls, runtime orchestration, packet/schema redesign, or any Matrix Script / Hot Follow / W2.2 / W2.3 scope.

## Phase A seed rule

Phase B consumes the Phase A entry seed; it does not re-author the entry surface. The entry seed remains outside the packet unless Phase B authoring has projected the approved line-truth entries into the packet's line-specific deltas.

The workbench surface may show which packet fields are seeded by Phase A, but it must not expose a second task-entry form and must not promote operator hints into packet truth.

## Projection object

The formal Phase B surface is named `digital_anchor_workbench_role_speaker_surface_v1`.

It is produced by projecting a Digital Anchor packet instance through:

`gateway.app.services.digital_anchor.workbench_role_speaker_surface.project_workbench_role_speaker_surface(packet)`

The projection returns these top-level sections:

| Section | Purpose | Source |
|---|---|---|
| `role_surface` | Formal role pack workbench surface | `line_specific_refs[ref_id=digital_anchor_role_pack].delta` |
| `speaker_surface` | Formal speaker plan workbench surface | `line_specific_refs[ref_id=digital_anchor_speaker_plan].delta` |
| `role_segment_binding_surface` | Role ↔ segment binding projection | `speaker_plan.delta.segments[].binds_role_id` joined to `role_pack.delta.roles[].role_id` |
| `scene_binding_projection` | Workbench-scope scene binding projection notes | `speaker_plan.delta.segments[]` + `g_scene` reference presence |
| `attribution_refs` | Packet/ref/capability provenance | `generic_refs[]`, `line_specific_refs[]`, `binding.capability_plan[]`, `binding.worker_profile_ref` |
| `phase_c_deferred` | Explicit delivery deferral | contract-owned fixed labels only |

## Role surface

`role_surface` is the formal workbench shape for role review:

| Field | Source | Rule |
|---|---|---|
| `framing_kind_set` | `role_pack.delta.framing_kind_set` | Closed set; rendered/selected only; never widened by the surface |
| `appearance_ref_kind_set` | `role_pack.delta.appearance_ref_kind_set` | Closed set; rendered/selected only; never widened by the surface |
| `roles[]` | `role_pack.delta.roles[]` | One row/card per declared role |

Role rows render only:

- `role_id`
- `display_name`
- `framing_kind`
- `language_scope_ref`
- `appearance_ref`
- `notes`

The surface must not embed appearance assets, resolve avatar engines, execute role rendering, or infer delivery readiness.

## Speaker surface

`speaker_surface` is the formal workbench shape for speaker plan review:

| Field | Source | Rule |
|---|---|---|
| `dub_kind_set` | `speaker_plan.delta.dub_kind_set` | Closed set; rendered/selected only; never widened by the surface |
| `lip_sync_kind_set` | `speaker_plan.delta.lip_sync_kind_set` | Closed set; rendered/selected only; never widened by the surface |
| `segments[]` | `speaker_plan.delta.segments[]` | One row per declared segment |

Segment rows render only:

- `segment_id`
- `binds_role_id`
- `script_ref`
- `dub_kind`
- `lip_sync_kind`
- `language_pick`

The surface must not embed script body text, audio waveforms, viseme streams, vendor names, TTS providers, lip-sync engines, or render-provider controls.

## Role ↔ segment binding surface

`role_segment_binding_surface` is the Phase B-owned workbench binding projection. It evaluates the join:

`speaker_plan.delta.segments[].binds_role_id == role_pack.delta.roles[].role_id`

For each segment, the projection returns:

- `segment_id`
- `binds_role_id`
- `role_resolved` (`true` when the role id exists in `roles[]`)
- `role_display_name`
- `role_framing_kind`
- `script_ref`
- `dub_kind`
- `lip_sync_kind`
- `language_pick`

Unresolved role bindings may be shown as inline workbench warnings, but those warnings are not a new state field and must not mutate `evidence.ready_state`.

## Scene binding projection rules

Phase B may show scene-binding projection notes only at workbench scope:

- `scene_contract_ref` is true when packet `generic_refs[]` contains `g_scene`;
- `segments[]` are listed by `segment_id` and `script_ref`;
- `scene_binding_writeback = not_implemented_phase_b`.

Phase B must not create delivery scenes, scene packs, manifests, publishability, or final output readiness. Delivery binding is Phase C.

## Attribution / refs projection rules

`attribution_refs` contains only provenance needed by an operator/reviewer to trace the surface back to packet truth:

- `generic_refs[]`: `ref_id`, `path`, `version`
- `line_specific_refs[]`: `ref_id`, `path`, `version`, `binds_to`
- `capability_plan[]`: `kind`, `mode`, `required`
- `worker_profile_ref`

`deliverable_profile_ref` and `asset_sink_profile_ref` are intentionally not resolved in Phase B. Delivery binding is Phase C.

## Forbidden

The Workbench Role / Speaker Surface must not introduce:

- provider / model / vendor / engine controls;
- avatar-engine / TTS-provider / lip-sync-engine controls;
- Matrix Script fields or contract mutation;
- Hot Follow behavior;
- W2.2 / W2.3 scope;
- packet/schema/sample redesign;
- delivery binding, manifest, metadata resolution, or publish feedback write-back;
- truth-shape state fields such as `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`.

## Acceptance

Phase B is green only when:

1. the projection is derived from the Digital Anchor packet sample without packet mutation;
2. `role_surface` matches the packet's role pack delta;
3. `speaker_surface` matches the packet's speaker plan delta;
4. `role_segment_binding_surface` evaluates the role ↔ segment join without creating state truth;
5. scene binding remains a workbench-scope projection note only;
6. `attribution_refs` contains packet/generic/line-specific provenance only;
7. tests prove no provider controls, Matrix Script mutation, Hot Follow behavior, W2.2 / W2.3 scope, delivery binding, or publish feedback write-back was introduced.

## Remaining blockers before Phase C

Phase C may not start until this Phase B surface is reviewed and accepted. Phase C must define delivery pack projection, result packet binding visualization, metadata, and manifest behavior separately without changing this Phase B workbench projection.
