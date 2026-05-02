# Matrix Script Operator-Visible Slice — Merge / Signoff Note v1

- Date: 2026-05-02
- Branch: `claude/cranky-borg-b4f5ac`
- Status: ready for architect / reviewer signoff
- Verdict on review: **CONDITIONAL PASS** — conditional only on the merge text honoring the scope fence below.
- Authority:
  - `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md`
  - `docs/execution/evidence/matrix_script_phase_a_task_entry_v1.md`
  - `docs/execution/evidence/matrix_script_phase_b_workbench_variation_surface_v1.md`
  - `docs/execution/evidence/matrix_script_workbench_panel_integration_v1.md`
  - `docs/contracts/matrix_script/task_entry_contract_v1.md`
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md` (referenced for boundary; **not** part of this merge)

## Purpose

Lock the scope of this merge to the Matrix Script operator-visible slice that has been reviewed and is ready for signoff. Reviewers and merge authors must read this note as the authoritative scope fence; nothing in this branch should be interpreted as implementing Phase C delivery rendering, Phase D publish-feedback write-back, Digital Anchor, Hot Follow, B-roll, or any broader operator-visible closure.

## Scope INCLUDED in this merge

This merge covers exactly the following, and nothing more:

1. **Matrix Script formal create-entry**
   - New Tasks card (`矩阵脚本`) targets `/tasks/matrix-script/new` (formal route).
   - Closed entry field set per `matrix_script_task_entry_contract_v1` (required: `topic`, `source_script_ref`, `source_language`, `target_language`, `target_platform`, `variation_target_count`; optional: `audience_hint`, `tone_hint`, `length_hint`, `product_ref`, `operator_notes`).
   - Operator hints map to `metadata.notes` only; only `source_script_ref` and `language_scope` cross to seed structures.
   - No vendor / model / provider / engine controls; no truth-shape state fields.
   - (Already landed in commit `4896f7c`; documented in `matrix_script_formal_create_entry_alignment_v1.md`.)

2. **Matrix Script workbench panel integration**
   - The Workbench's existing line-specific panel slot consumes the formal Phase B projection helper `gateway.app.services.matrix_script.workbench_variation_surface.project_workbench_variation_surface(packet)`.
   - Renders, when `panel_kind == "matrix_script"`: variation matrix axes, cells × slots (with non-blocking unresolved-slot warning), per-slot collapsible detail (`slot_id`, `binds_cell_id`, `length_hint`, `language_scope.source_language`, `language_scope.target_language`, `body_ref`), attribution refs (`generic_refs`, `line_specific_refs`, `capability_plan` kind/mode/required only, `worker_profile_ref`), and the read-only publish-feedback projection (`feedback_writeback = not_implemented_phase_b`).
   - Read-only; no authoring affordances; `evidence.ready_state` is the only state authority.
   - Generic Workbench skeleton untouched (header, deliverables, scenes, publish hub, steps, debug panel preserved).
   - Implementation surface: `gateway/app/services/operator_visible_surfaces/wiring.py`, `gateway/app/templates/task_workbench.html`, `tests/contracts/operator_visible_surfaces/test_wiring.py`.
   - Documented in `matrix_script_workbench_panel_integration_v1.md`.

3. **State-sync closure**
   - Evidence doc: `docs/execution/evidence/matrix_script_workbench_panel_integration_v1.md`.
   - Progress log entry: top section of `docs/execution/logs/PHASE2_PROGRESS_LOG.md`.
   - Evidence index entries: four rows under the Phase-2 evidence table in `docs/execution/apolloveo_2_0_evidence_index_v1.md`.
   - This merge note: `docs/execution/evidence/matrix_script_operator_visible_slice_merge_note_v1.md`.

## Scope EXPLICITLY DEFERRED — NOT part of this merge

The merge text, PR title, PR body, and reviewer commentary must **not** claim any of the following. These items remain frozen / contract-only / out-of-scope:

- **Phase C — Matrix Script Delivery Binding rendering.** The Phase C contract `delivery_binding_contract_v1` and projection helper `project_delivery_binding` exist, but **no Delivery Center matrix-script-specific rendering is added in this merge**. The Workbench's link to `/tasks/{task_id}/publish` remains a navigational pointer only.
- **Phase D — publish-feedback write-back.** The publish-feedback projection is rendered in the Workbench panel as the fixed read-only placeholder `feedback_writeback = not_implemented_phase_b`. No write-back, no `variation_id` collection, no impressions / CTR / completion metrics, no publish URL or status authoring.
- **Digital Anchor.** No code, template, contract, or surface change.
- **Hot Follow.** Frozen — no change.
- **B-roll / Asset Supply.** Blocked — no change.
- **Board / New Tasks layout redesign.** New Tasks card target was already aligned in commit `4896f7c`; no layout change in this merge.
- **Packet / schema redesign.** No envelope, no `$defs`, no sample mutation.
- **Provider / model / vendor / engine exposure.** Forbidden in all surfaces.
- **State-machine changes.** The Workbench remains a read-only render of `evidence.ready_state` plus the Phase B projection.
- **Re-run / regenerate / comparison view / line switcher / asset-library access.** Design-deferred.
- **Authoring affordances on axes / cells / slots.** Phase B is read-only by contract.
- **`body_ref` content fetch / preview.** Forbidden by Phase B contract.

## Files in the merge

Implementation:

- `gateway/app/services/operator_visible_surfaces/wiring.py`
- `gateway/app/templates/task_workbench.html`
- `tests/contracts/operator_visible_surfaces/test_wiring.py`

Documentation / state-sync:

- `docs/execution/evidence/matrix_script_workbench_panel_integration_v1.md` (new)
- `docs/execution/evidence/matrix_script_operator_visible_slice_merge_note_v1.md` (new — this file)
- `docs/execution/logs/PHASE2_PROGRESS_LOG.md` (appended top section)
- `docs/execution/apolloveo_2_0_evidence_index_v1.md` (appended four rows)

No template, presenter, router, service, schema, or test files outside the two listed under "Implementation" were modified.

## Tests

Command:

```bash
python3 -m pytest tests/contracts/matrix_script/ tests/contracts/operator_visible_surfaces/ -q
```

Result: `79 passed`.

Pre-existing pydantic-v2 collection error in `gateway/app/services/tests/test_task_router_presenters.py` (`gateway/app/config.py:43` — `str | None` + `BaseSettings(env=...)`) is environmental and **unchanged by this merge**. Reviewers seeing that error should treat it as pre-existing, not introduced.

## Suggested PR title

```
Matrix Script operator-visible slice: formal create-entry + workbench panel integration + state-sync (Phase A + Phase B only)
```

## Suggested PR body (paste-ready)

```
Scope (this PR only):
- Matrix Script formal create-entry (Phase A) — already in 4896f7c, indexed here.
- Matrix Script workbench panel integration: line-specific slot now renders the formal Phase B variation surface (axes, cells × slots, slot detail, attribution refs, read-only publish-feedback projection).
- State-sync write-back: evidence doc, progress log entry, evidence index rows, merge note.

Explicitly NOT in this PR:
- Phase C Delivery Center matrix-script delivery-binding rendering.
- Phase D publish-feedback write-back.
- Digital Anchor / Hot Follow / B-roll / Board / New Tasks redesign.
- Packet / schema redesign, provider / model / vendor / engine exposure, state-machine changes.

Tests: tests/contracts/matrix_script/ + tests/contracts/operator_visible_surfaces/ — 79 passed.

Authority docs:
- docs/execution/evidence/matrix_script_operator_visible_slice_merge_note_v1.md
- docs/execution/evidence/matrix_script_workbench_panel_integration_v1.md
- docs/contracts/matrix_script/task_entry_contract_v1.md
- docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md
```

## Reviewer checklist

- [ ] PR title and body match the scope fence above (no Phase C / Phase D claims).
- [ ] No Hot Follow, Digital Anchor, B-roll, Board, or New Tasks layout changes in the diff.
- [ ] No vendor / model / provider / engine fields, controls, or selectors anywhere in the diff.
- [ ] No packet schema, envelope, or sample mutation.
- [ ] Workbench Phase B panel renders only the documented fields, in read-only form.
- [ ] Evidence index has four new rows under Phase-2; progress log has the dated top section; evidence doc and merge note are present.
- [ ] Test suite `tests/contracts/matrix_script/` + `tests/contracts/operator_visible_surfaces/` is green locally.

## Hard scope fence (do not edit at merge time)

This merge is **Matrix Script Phase A entry + Phase B workbench panel integration + state-sync** only. Any item not listed under "Scope INCLUDED" is **not** in this merge. Any reviewer or merge author observing such an item in the diff should treat it as a regression and reject the merge.
