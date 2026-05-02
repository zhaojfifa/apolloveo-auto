# Evidence: Surface Connect-First Routing v1

Date: 2026-05-01
Scope: New Tasks routing + temporary connected paths for incomplete lines

Supersession note (2026-05-02): Matrix Script has since been promoted from
temporary connected create entry to formal create entry at
`/tasks/matrix-script/new`. Digital Anchor remains temporary connected. See
`docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md`.

## What Changed

Ran the narrow connect-first wave. Hot Follow now uses its existing formal
create entry, while Matrix Script and Digital Anchor use explicit temporary
connected paths until their formal create-entry routes are commissioned.
Baseline remains on the existing compatibility entry.

Files changed:

- `gateway/app/routers/tasks.py`
- `gateway/app/templates/tasks_connected_placeholder.html`
- `gateway/app/templates/tasks_newtasks.html`
- `gateway/app/services/tests/test_new_tasks_surface.py`

## Current Route And Template

- Current route target: `gateway/app/routers/tasks.py::tasks_newtasks`
- Current template target: `gateway/app/templates/tasks_newtasks.html`
- `/tasks` primary "new task" link remains `/tasks/newtasks`
- Legacy `/tasks/avatar/new` and `/tasks/apollo-avatar/new` are not used by
  primary New Tasks cards.

## New Tasks Card Mapping

`/tasks/newtasks` is selection-only, keeps the original New Tasks card visual
baseline (`wizard-wrap`, `wizard-card`, `icon-box`, Tailwind grid, original
topbar and bottom guidance rhythm), and renders four card entries:

| Visible label | Internal id | Active target |
| --- | --- | --- |
| 数字人IP | `digital_anchor` | `/tasks/connect/digital_anchor/new` |
| 热点跟拍 | `hot_follow` | `/tasks/hot/new` |
| 矩阵脚本 | `matrix_script` | `/tasks/connect/matrix_script/new` |
| 基础剪辑 | `baseline` | `/tasks/baseline/new` |

## Formal vs Temporary Connected

| Line | Status | Create / entry | Workbench | Delivery |
| --- | --- | --- | --- | --- |
| `hot_follow` | Formal | `/tasks/hot/new?ui_locale=zh` | `/tasks/{task_id}` -> `hot_follow_workbench.html` | `/tasks/{task_id}/publish` -> `hot_follow_publish.html` |
| `matrix_script` | Temporary connected | `/tasks/connect/matrix_script/new?ui_locale=zh` | `/tasks/connect/matrix_script/workbench?ui_locale=zh` | `/tasks/connect/matrix_script/publish?ui_locale=zh` |
| `digital_anchor` | Temporary connected | `/tasks/connect/digital_anchor/new?ui_locale=zh` | `/tasks/connect/digital_anchor/workbench?ui_locale=zh` | `/tasks/connect/digital_anchor/publish?ui_locale=zh` |
| `baseline` | Compatibility | `/tasks/baseline/new?ui_locale=zh` | `/tasks/{task_id}` fallback workbench | `/tasks/{task_id}/publish` fallback delivery |

The temporary connected page clearly labels itself as "当前接通版本" and states
that it does not represent final production-line capability or introduce task /
delivery truth.

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
38 passed
```

Coverage:

- `/tasks` template links to `/tasks/newtasks`
- `/tasks/newtasks` route renders the active card-based template with the four
  line ids
- New Tasks has no workbench-like form, target-language inputs, helper
  textarea, or envelope counters
- Hot Follow card targets `/tasks/hot/new`, which renders
  `hot_follow_new.html`
- Hot Follow task workbench and delivery resolve to `hot_follow_workbench.html`
  and `hot_follow_publish.html`
- Matrix Script and Digital Anchor temporary create / workbench / delivery
  paths load and identify the correct line id and page role
- Digital Anchor no longer lands on `/tasks/avatar/new` and does not return
  `ApolloAvatar is disabled`
- original visual baseline classes remain present and the semi-custom
  `line-card` / `newtasks-header` / `page-shell` variant is absent

## Red Lines

- No Board redesign.
- Workbench change limited to temporary connected placeholder routes for
  Matrix Script and Digital Anchor.
- Delivery change limited to temporary connected placeholder routes for
  Matrix Script and Digital Anchor.
- No Hot Follow panel implementation changed.
- No B-roll implementation changed.
- No packet/schema change.
- No provider/model/vendor controls.
- No Platform Runtime Assembly.
- No language-system redesign and no expansion beyond the existing
  Burmese/Vietnamese target scope.
