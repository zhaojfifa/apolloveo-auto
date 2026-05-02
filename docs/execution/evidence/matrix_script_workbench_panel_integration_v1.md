# Matrix Script Workbench Panel Integration — Alignment Wave v1

> **Merge scope fence**: this evidence covers Matrix Script Phase B workbench panel integration only. The merge it accompanies (see `matrix_script_operator_visible_slice_merge_note_v1.md`) does **not** include Phase C Delivery Binding rendering, Phase D publish-feedback write-back, Digital Anchor, Hot Follow, B-roll, or any Board / New Tasks layout redesign.

- Date: 2026-05-02
- Wave: ApolloVeo 2.0 — Matrix Script Workbench Panel-Integration Alignment (UI / Product Alignment)
- Authority:
  - `docs/design/surface_workbench_lowfi_v1.md`
  - `docs/design/panel_matrix_script_variation_lowfi_v1.md`
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md`
  - `docs/execution/evidence/matrix_script_phase_b_workbench_variation_surface_v1.md`
  - `docs/execution/evidence/operator_visible_surfaces_phase_3b_ui_presenter_wiring_v1.md`

## Scope

Narrow UI alignment wave that consumes the already-resolved Matrix Script Phase B variation surface inside the existing Workbench template. Turns the line-specific panel slot from "mounted ref names only" into a real operator-visible variation workspace, without touching create-entry, route taxonomy, packet truth, or any other line.

In scope:

- workbench bundle wiring extension that attaches `matrix_script_workbench_variation_surface_v1` to the Workbench operator-surface bundle when the resolved `panel_kind == "matrix_script"`;
- Workbench template rendering of the variation surface (axes, cells × slots, slot detail, attribution refs, publish feedback projection) inside the existing line-specific panel area;
- focused wiring tests for the new attachment path.

Out of scope (intentionally deferred):

- Hot Follow (frozen — untouched);
- Digital Anchor (not started — untouched);
- B-roll (blocked — untouched);
- Board / New Tasks (untouched);
- Matrix Script create-entry redesign (already aligned in `4896f7c`; no further changes here);
- Delivery binding / Phase C surfaces (no Workbench rendering of delivery added);
- Publish feedback write-back (Phase D — not implemented);
- Packet / schema redesign;
- Capability dispatch / route taxonomy changes;
- Provider / model / vendor / engine controls;
- State-machine changes — Workbench remains a read-only render of `evidence.ready_state` plus the Phase B projection;
- Re-run / regenerate affordances, comparison view, line switcher, asset library access (design-deferred).

## Files added / updated

Implementation (from the integration wave):

- Updated `gateway/app/services/operator_visible_surfaces/wiring.py`
  - `_packet_view` now passes through `binding`, `evidence`, `generic_refs`, `metadata`, `line_id`, `packet_version` from the task or its attached `packet` envelope.
  - `build_operator_surfaces_for_workbench` calls `project_workbench_variation_surface(packet_view)` and attaches the result under `workbench.matrix_script_variation_surface` only when the resolved `panel_kind == "matrix_script"`.
- Updated `gateway/app/templates/task_workbench.html`
  - Renders axes table, cells × slots table (with non-blocking unresolved-slot warning), per-slot collapsible detail (`slot_id`, `binds_cell_id`, `length_hint`, `language_scope.source/target`, `body_ref`), attribution refs (generic / line-specific / capability_plan / worker_profile_ref), and read-only publish feedback projection.
  - Rendering is gated on `ops.workbench.line_specific_panel.panel_kind == "matrix_script"`.
- Updated `tests/contracts/operator_visible_surfaces/test_wiring.py`
  - `test_workbench_bundle_attaches_matrix_script_variation_surface_when_panel_mounts`
  - `test_workbench_bundle_omits_matrix_script_surface_when_panel_kind_differs`

Documentation / state-sync (this follow-up wave):

- Added `docs/execution/evidence/matrix_script_workbench_panel_integration_v1.md`
- Updated `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- Updated `docs/execution/apolloveo_2_0_evidence_index_v1.md`

No template logic was changed in this state-sync follow-up wave; only documentation files.

## What was aligned

- The Matrix Script line-specific Workbench slot now consumes the formal Phase B projection helper `gateway.app.services.matrix_script.workbench_variation_surface.project_workbench_variation_surface(packet)` directly.
- Operator-visible elements rendered when authoritative payload is present:
  - variation matrix `axes[]` (axis_id / kind / values / required) from `variation_matrix.delta.axes[]`;
  - variation `cells[]` (cell_id / axis_selections / script_slot_ref / notes) from `variation_matrix.delta.cells[]`;
  - per-slot detail (`slot_id`, `binds_cell_id`, `length_hint`, `language_scope.source_language`, `language_scope.target_language`, `body_ref`) from `slot_pack.delta.slots[]`;
  - the cell→slot join rule shown verbatim from the contract (`variation_plan.cells[].script_slot_ref == copy_bundle.slots[].slot_id`);
  - `attribution_refs` (`generic_refs`, `line_specific_refs`, `capability_plan` kind/mode/required only, `worker_profile_ref`);
  - `publish_feedback_projection` (`reference_line`, `validator_report_path`, `ready_state`, fixed `feedback_writeback = not_implemented_phase_b`).
- Generic Workbench skeleton (header, deliverables, scenes, publish hub, steps, debug panel) is unchanged.

## What remained deferred

- Authoring affordances on axes / cells / slots (Phase B remains read-only);
- `body_ref` content fetch / preview (explicitly forbidden by the Phase B contract);
- Delivery binding rendering (Phase C);
- Publish feedback write-back / variation-level feedback / channel metrics (Phase D);
- Re-run / regenerate, comparison, line switcher, asset library access (design-deferred);
- Digital Anchor, Hot Follow, B-roll, Board, New Tasks alignment — out of scope of this wave.

## Tests run

Command:

```bash
python3 -m pytest tests/contracts/matrix_script/ tests/contracts/operator_visible_surfaces/ -q
```

Result: `79 passed`.

Pre-existing collection error in `gateway/app/services/tests/test_task_router_presenters.py` (`gateway/app/config.py:43` pydantic-v2 BaseSettings env-keyword) is unrelated to this wave and was not introduced or modified.

## Red lines preserved

- No vendor / model / provider / engine controls introduced.
- No packet truth or packet schema mutated; the projection helper is a pure read.
- No new Workbench state machine; visible state is `evidence.ready_state` plus the Phase B projection.
- No publish feedback write-back, delivery binding rendering, manifest, or metadata authoring.
- No Hot Follow code or template changes.
- No Digital Anchor code, template, or surface changes.
- No B-roll, Board, or New Tasks changes.
- No route taxonomy changes; no presenter or router behavior changes.
- No Matrix Script create-entry changes in this wave.
- Optional capabilities (`pack`, `dub`) remain non-blocking — no gate authority added.

## Boundary confirmation

The integration wave is functionally complete and bounded to the Matrix Script Workbench line-specific panel slot. This follow-up wave only writes back evidence, progress log, and evidence index entries; no code, template, presenter, route, or test changes were made in the state-sync wave.

## Remaining for merge / signoff

1. Architect / reviewer signoff on this wave.
2. Pre-existing `test_task_router_presenters.py` collection error is environmental (pydantic BaseSettings + `str | None`) and out of scope.
3. Phase C Workbench-side rendering (delivery binding) remains intentionally not started.
