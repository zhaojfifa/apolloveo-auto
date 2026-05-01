# Evidence: New Tasks Card-Based Line Entry Rollback v1

Date: 2026-05-01
Scope: Board taxonomy + New Tasks entry surface only

## What Changed

Rolled back `/tasks/newtasks` from the semi-workbench intake form to the
original card-based entry layout, then aligned the active Board taxonomy with
the same line vocabulary.

Files changed:

- `gateway/app/services/task_semantics.py`
- `gateway/app/templates/tasks.html`
- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`

## Current Route And Template

- Current route target: `gateway/app/routers/tasks.py::tasks_newtasks`
- Current template target: `gateway/app/templates/tasks_newtasks.html`
- `/tasks` primary "new task" link remains `/tasks/newtasks`
- Legacy `/tasks/new`, `/tasks/avatar/new`, `/tasks/hot/new`, and
  `/tasks/baseline/new` remain compatibility / next-step paths only; they do
  not define primary operator-visible taxonomy.

## Surface Contract

`/tasks/newtasks` is selection-only and renders four card entries:

| Visible label | Internal id |
| --- | --- |
| 热点跟拍 | `hot_follow` |
| 矩阵脚本 | `matrix_script` |
| 数字人IP | `digital_anchor` |
| 基础剪辑 | `baseline` |

The page preserves:

- page title area
- line cards
- per-card short Chinese description
- per-card "开始创建" action
- bottom guidance section
- top nav: 任务 / 工具 / 返回任务看板

Removed from New Tasks:

- step-based intake form
- inline line-specific field editing
- target-language input
- helper translation textarea
- envelope completeness counters
- `generic_refs` / `line_specific_refs` display
- contract/debug style hints

Board taxonomy now uses the same vocabulary:

| Visible label | Internal id |
| --- | --- |
| 全部场景 | `all` |
| 热点跟拍 | `hot_follow` |
| 矩阵脚本 | `matrix_script` |
| 数字人IP | `digital_anchor` |
| 基础剪辑 | `baseline` |

No provider/model/vendor controls are present. No language-plan, subtitle,
dub, helper translation, or skill-driven language logic changed.

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
- Board tabs and task labels use the unified line taxonomy
- `/tasks/newtasks` route renders the active card-based template with the four
  line ids
- New Tasks has no workbench-like form, target-language inputs, helper
  textarea, or envelope counters

## Red Lines

- Board change limited to active line taxonomy/filter labels.
- No Workbench implementation changed.
- No Delivery implementation changed.
- No Hot Follow panel implementation changed.
- No B-roll implementation changed.
- No packet/schema change.
- No provider/model/vendor controls.
- No Platform Runtime Assembly.
- No language-system redesign and no expansion beyond the existing
  Burmese/Vietnamese target scope.
