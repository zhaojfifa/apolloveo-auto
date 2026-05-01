# Evidence: New Tasks Strict Card Link Correction v1

Date: 2026-05-01
Scope: New Tasks entry surface only

## What Changed

Restored `/tasks/newtasks` to the original card-based visual/layout baseline
and corrected the primary card targets so no New Tasks card points at disabled
legacy scene routes.

Files changed:

- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`

## Current Route And Template

- Current route target: `gateway/app/routers/tasks.py::tasks_newtasks`
- Current template target: `gateway/app/templates/tasks_newtasks.html`
- `/tasks` primary "new task" link remains `/tasks/newtasks`
- Legacy `/tasks/avatar/new` and `/tasks/apollo-avatar/new` are not used by
  primary New Tasks cards.

## Surface Contract

`/tasks/newtasks` is selection-only, keeps the original New Tasks card visual
baseline (`wizard-wrap`, `wizard-card`, `icon-box`, Tailwind grid, original
topbar and bottom guidance rhythm), and renders four card entries:

| Visible label | Internal id | Active target |
| --- | --- | --- |
| 数字人IP | `digital_anchor` | `/tasks/new?line=digital_anchor` |
| 热点跟拍 | `hot_follow` | `/tasks/new?line=hot_follow` |
| 矩阵脚本 | `matrix_script` | `/tasks/new?line=matrix_script` |
| 基础剪辑 | `baseline` | `/tasks/new?line=baseline` |

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

No provider/model/vendor controls are present. No language-plan, subtitle,
dub, helper translation, or skill-driven language logic changed.

## Tests

Command:

```bash
python3.11 -m pytest gateway/app/services/tests/test_new_tasks_surface.py gateway/app/services/tests/test_task_router_presenters.py -q
```

Result:

```text
35 passed
```

Coverage:

- `/tasks` template links to `/tasks/newtasks`
- `/tasks/newtasks` route renders the active card-based template with the four
  line ids
- New Tasks has no workbench-like form, target-language inputs, helper
  textarea, or envelope counters
- every visible card uses `/tasks/new?line=<line_id>` as the active create
  target
- `/tasks/new?line=digital_anchor`, `/tasks/new?line=hot_follow`,
  `/tasks/new?line=matrix_script`, and `/tasks/new?line=baseline` load the
  active create template and do not return `ApolloAvatar is disabled`
- original visual baseline classes remain present and the semi-custom
  `line-card` / `newtasks-header` / `page-shell` variant is absent

## Red Lines

- New Tasks change only.
- No Board redesign.
- No Workbench implementation changed.
- No Delivery implementation changed.
- No Hot Follow panel implementation changed.
- No B-roll implementation changed.
- No packet/schema change.
- No provider/model/vendor controls.
- No Platform Runtime Assembly.
- No language-system redesign and no expansion beyond the existing
  Burmese/Vietnamese target scope.
