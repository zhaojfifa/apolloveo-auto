# Matrix Script First Production Line Wave — Phase B Workbench Variation Surface v1

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 **Matrix Script First Production Line Wave** — Phase B only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §6 Phase B
  - `docs/contracts/matrix_script/task_entry_contract_v1.md`
  - `docs/contracts/matrix_script/packet_v1.md`
  - `schemas/packets/matrix_script/packet.schema.json`
  - `docs/design/panel_matrix_script_variation_lowfi_v1.md`
- Contract: `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`

## Scope

Phase B establishes the formal Workbench Variation Surface for Matrix Script.

In scope:

- formal definition of `variation_plan`;
- formal definition of `copy_bundle` and slot detail;
- attribution / refs projection rules;
- read-only publish feedback projection rules;
- a minimal projection helper consumed by the existing lightweight debug panel;
- focused tests and evidence/index/log write-back.

Out of scope:

- delivery binding;
- publish feedback write-back;
- provider/model/vendor controls;
- packet/schema redesign;
- Digital Anchor;
- Hot Follow business logic;
- W2.2 / W2.3 work.

## Files added / updated

- Added `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- Added `gateway/app/services/matrix_script/workbench_variation_surface.py`
- Added `gateway/app/services/matrix_script/__init__.py`
- Updated `gateway/app/routers/matrix_script_panel_debug.py` to consume the formal projection helper
- Added `tests/contracts/matrix_script/test_workbench_variation_phase_b.py`
- Updated `docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md`
- Updated `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## Projection summary

The formal projection helper:

`gateway.app.services.matrix_script.workbench_variation_surface.project_workbench_variation_surface(packet)`

returns:

- `variation_plan` from `matrix_script_variation_matrix.delta`
- `copy_bundle` from `matrix_script_slot_pack.delta`
- `slot_detail_surface` with the cell-to-slot join rule
- `attribution_refs` from packet refs and capability plan
- `publish_feedback_projection` as read-only evidence projection
- compatibility aliases used by the current lightweight panel

The helper does not mutate the packet, resolve delivery profiles, write feedback, call providers, or create runtime task state.

## Validation

Command:

```bash
python3.11 -m pytest tests/contracts/matrix_script/test_workbench_variation_phase_b.py -q
```

Expected result:

```text
8 passed
```

## Boundary confirmation

No provider code was added. No Digital Anchor files were touched. No Hot Follow code was touched. No delivery binding or publish feedback write-back was implemented. Phase C and Phase D remain not started.

## Remaining blockers before Phase C

1. Phase B must be reviewed and accepted.
2. Phase C must define delivery pack projection / metadata / manifest separately.
3. Phase C must decide how `result_packet_binding` becomes a delivery-center visualization without changing the Phase B workbench projection.
