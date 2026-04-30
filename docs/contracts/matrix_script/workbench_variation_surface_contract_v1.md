# Matrix Script Workbench Variation Surface Contract v1

Date: 2026-04-27
Status: Phase B landing (Matrix Script First Production Line Wave — Workbench Variation Surface)
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §6 Phase B
- `docs/contracts/matrix_script/task_entry_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`

## Purpose

Define the formal Workbench Variation Surface for Matrix Script. This surface turns the frozen Matrix Script packet into a read-only workbench projection for:

1. variation matrix review;
2. slot detail review;
3. attribution / refs inspection;
4. publish feedback projection preview.

This contract does **not** create delivery binding, publish feedback write-back, provider controls, or new packet truth.

## Projection object

The formal Phase B surface is named `matrix_script_workbench_variation_surface_v1`.

It is produced by projecting a Matrix Script packet instance through:

`gateway.app.services.matrix_script.workbench_variation_surface.project_workbench_variation_surface(packet)`

The projection returns these top-level sections:

| Section | Purpose | Source |
|---|---|---|
| `variation_plan` | Formal variation matrix surface | `line_specific_refs[ref_id=matrix_script_variation_matrix].delta` |
| `copy_bundle` | Formal slot collection surface | `line_specific_refs[ref_id=matrix_script_slot_pack].delta` |
| `slot_detail_surface` | Single-slot detail surface and join rule | `copy_bundle.slots[]` joined from `variation_plan.cells[]` |
| `attribution_refs` | Packet/ref/capability provenance | `generic_refs[]`, `line_specific_refs[]`, `binding.capability_plan[]`, `binding.worker_profile_ref` |
| `publish_feedback_projection` | Read-only feedback projection anchor | `evidence.reference_line`, `evidence.validator_report_path`, `evidence.ready_state` |
| `result_packet_binding` | Phase-B-safe preview alias for packet refs | ref ids + capability kinds only; delivery binding explicitly not implemented |

## Variation matrix surface

`variation_plan` is the formal workbench shape for matrix review:

| Field | Source | Rule |
|---|---|---|
| `axis_kind_set` | `variation_matrix.delta.axis_kind_set` | Closed set, rendered only; never widened by the surface |
| `axes[]` | `variation_matrix.delta.axes[]` | One row per declared axis |
| `cells[]` | `variation_matrix.delta.cells[]` | One row per declared cell |

The surface may render inline integrity warnings when `cells[].script_slot_ref` does not resolve to a slot, but that warning is not a new state field and must not mutate `evidence.ready_state`.

## Slot detail surface

`copy_bundle.slots[]` is the formal slot collection. `slot_detail_surface` defines how a selected cell opens its slot:

`variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id`

Slot detail renders only:

- `slot_id`
- `binds_cell_id`
- `language_scope.source_language`
- `language_scope.target_language`
- `body_ref`
- `length_hint`

The surface must not embed body text, resolve storage providers, execute generation, or infer delivery readiness.

## Attribution / refs projection rules

`attribution_refs` contains only provenance needed by an operator/reviewer to trace the surface back to packet truth:

- `generic_refs[]`: `ref_id`, `path`, `version`
- `line_specific_refs[]`: `ref_id`, `path`, `version`, `binds_to`
- `capability_plan[]`: `kind`, `mode`, `required`
- `worker_profile_ref`

`deliverable_profile_ref` and `asset_sink_profile_ref` are intentionally not resolved in Phase B. Delivery binding is Phase C.

## Publish feedback projection rules

`publish_feedback_projection` is a read-only placeholder for the workbench feedback area. It may render:

- `reference_line`
- `validator_report_path`
- `ready_state`
- `feedback_writeback = not_implemented_phase_b`

It must not collect or write:

- `variation_id`
- impressions / CTR / completion metrics
- publish URL / publish status
- operator feedback
- delivery or manifest fields

Those are Phase D concerns. Phase B only reserves the visible projection area and keeps it traceable to packet evidence.

## Forbidden

The Workbench Variation Surface must not introduce:

- provider / model / vendor / engine controls;
- Digital Anchor fields;
- Hot Follow behavior;
- W2.2 / W2.3 scope;
- packet/schema redesign;
- delivery binding, manifest, metadata resolution, or publish feedback write-back;
- truth-shape state fields such as `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`.

## Acceptance

Phase B is green only when:

1. the projection is derived from the Matrix Script packet sample without packet mutation;
2. `variation_plan` matches the packet's variation matrix delta;
3. `copy_bundle` and `slot_detail_surface` match the packet's slot pack delta;
4. `attribution_refs` contains packet/generic/line-specific provenance only;
5. `publish_feedback_projection` is read-only and marked not implemented for write-back;
6. the debug preview consumes this formal projection instead of maintaining separate projection truth;
7. tests prove no provider controls, delivery binding, Digital Anchor, or Hot Follow scope was introduced.

## Remaining blockers before Phase C

Phase C may not start until this Phase B surface is reviewed and accepted. Phase C must define delivery pack projection, result packet binding visualization, metadata, and manifest behavior separately without changing this Phase B contract.
