# Matrix Script Formal Create-Entry Alignment v1

- Date: 2026-05-02
- Line: Matrix Script only
- Status: implementation green; awaiting review/signoff
- Authority:
  - `docs/contracts/matrix_script/task_entry_contract_v1.md`
  - `docs/design/surface_task_area_lowfi_v1.md`
  - `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
  - `docs/contracts/matrix_script/delivery_binding_contract_v1.md`

## Scope

This wave replaces the Matrix Script temporary connected create page as the
primary operator entry with a formal line-specific create-entry page:

- New Tasks Matrix Script card now targets `/tasks/matrix-script/new`.
- `/tasks/matrix-script/new` renders the Matrix Script create-entry page.
- POST `/tasks/matrix-script/new` validates the Matrix Script closed entry
  field set and creates a `kind=matrix_script` task.
- Task creation redirects to the existing task workbench route
  `/tasks/{task_id}`.
- Delivery remains the existing task delivery route
  `/tasks/{task_id}/publish`.

## Low-Fi Alignment

Aligned low-fi elements:

- New Tasks remains card-based line selection only.
- Matrix Script create-entry collects only required and optional creation
  inputs from the Matrix Script task-entry contract.
- Workbench-level variation cells, slot authoring, feedback rows, and delivery
  details are not collected on the create page.
- No debug-panel route is used as operator entry.
- No provider, model, vendor, or engine controls are exposed.
- Target-language options remain limited to the current UI scope: `mm`, `vi`.

## Backend / Frontend Mapping

Backend:

- `gateway/app/services/matrix_script/create_entry.py`
  - validates Matrix Script create-entry input;
  - builds the repository task payload;
  - seeds `line_specific_refs[]` for Matrix Script workbench panel mounting;
  - stores entry hints under task `config.entry` and packet `metadata.notes`
    without creating packet truth.
- `gateway/app/routers/tasks.py`
  - adds GET/POST `/tasks/matrix-script/new`;
  - removes `matrix_script` from `_TEMP_CONNECTED_LINES` so
    `/tasks/connect/matrix_script/new` is no longer the primary path.

Frontend:

- `gateway/app/templates/tasks_newtasks.html`
  - Matrix Script card now links to `/tasks/matrix-script/new`.
- `gateway/app/templates/matrix_script_new.html`
  - formal Matrix Script create-entry form.

## Final Route Mapping

| Surface | Route |
| --- | --- |
| New Tasks Matrix Script card | `/tasks/matrix-script/new` |
| Matrix Script create-entry GET | `/tasks/matrix-script/new` |
| Matrix Script create-entry POST | `/tasks/matrix-script/new` |
| Matrix Script workbench after create | `/tasks/{task_id}` |
| Matrix Script delivery after task exists | `/tasks/{task_id}/publish` |
| Removed temporary primary create path | `/tasks/connect/matrix_script/new` |

## Tests

- `gateway/app/services/tests/test_new_tasks_surface.py`

## Red Lines Preserved

- Hot Follow route/template/flow untouched.
- Digital Anchor remains on its temporary connected path; not started.
- No Board redesign.
- No Delivery redesign.
- No B-roll.
- No packet/schema redesign.
- No provider/model/vendor/engine controls.
- No `/debug/panels/...` operator entry.
- No language logic change or target-language expansion.
