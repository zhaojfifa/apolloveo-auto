# Evidence: New Tasks Line-First Surface Wiring v1

Date: 2026-05-01
Scope: New Tasks surface only (`/tasks/newtasks`)

## What Changed

Retargeted the active `/tasks/newtasks` template from the legacy scene wizard
(`Avatar` / `Hot` / `Baseline`) to the frozen line-first New Tasks surface.

Files changed:

- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`

## Current Route And Template

- Current route target: `gateway/app/routers/tasks.py::tasks_newtasks`
- Current template target: `gateway/app/templates/tasks_newtasks.html`
- `/tasks` primary "new task" link remains `/tasks/newtasks`
- Legacy `/tasks/new` remains as compatibility path only and still renders
  `tasks_new.html`

## Surface Contract

`/tasks/newtasks` now renders the three frozen production line entries:

- `hot_follow`
- `matrix_script`
- `digital_anchor`

The surface is line-first. It presents:

- Step 1: choose production line
- Step 2: line-specific intake fields
- Step 3: read-only envelope completeness counters

No provider/model/vendor controls are present.

## Tests

Command:

```bash
python3.11 -m pytest gateway/app/services/tests/test_new_tasks_surface.py -q
```

Result:

```text
3 passed
```

Coverage:

- `/tasks` template links to `/tasks/newtasks`
- `/tasks/newtasks` route renders the active template with the three frozen
  line ids
- legacy scene-wizard entry semantics are absent from `tasks_newtasks.html`

## Red Lines

- No Board implementation changed.
- No Workbench implementation changed.
- No Delivery implementation changed.
- No Hot Follow panel implementation changed.
- No B-roll implementation changed.
- No packet/schema change.
- No provider/model/vendor controls.
- No Platform Runtime Assembly.
