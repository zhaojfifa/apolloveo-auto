# Matrix Script Operator UI Redesign — 2026-05-28 wave snapshots

This directory carries before/after Jinja template snapshots for the
2026-05-28 Matrix Script Operator UI Redesign wave. **Not screenshots in
the visual sense** — the snapshots are the raw template files (and the
matrix_script branches of the shared workbench / publish-hub templates)
so reviewers can diff the source and trace each operator-visible change
back to its template path. A full visual screenshot pass requires
Playwright + a running `uvicorn gateway.app.main:app` server, which is
not available in the current sandbox.

## Snapshot pairs

| Path under `before/` | Path under `after/` | What changed |
|---|---|---|
| `matrix_script_new.html` | `matrix_script_new.html` | Full rewrite: paste / upload / select primary tabs, op-card layout, mission copy "创建后，系统会解析脚本结构、生成变体方案，并进入工作台评审。", opaque `source_script_ref` moved behind `<details class="op-collapse">` |
| `task_workbench_matrix_script_block.html` | `task_workbench_matrix_script_block.html` | Block C 变体策略 → 变体方案; Block D 生成/重新生成 → 生成进度; Block E adds empty-state honesty when no preview/final media is resolved; Block F simplified to mission copy ("当前不能交付：尚未生成成片" / "已具备" / "待补齐"); collapsed fold relabeled to "F · 诊断 · 技术诊断（架构师视图，默认收起）" |
| `task_publish_hub_matrix_script_block.html` | `task_publish_hub_matrix_script_block.html` | **Unchanged** in this wave (PR #164 / OWC-MS-RO PR-4 substrate already shipped op-card six-block delivery center A–F). Included only for diff parity. |
| n/a | `operator_console.css.snapshot` | The shared op-card / op-pill / op-banner / op-collapse system from PR #164. Snapshot taken so the templates can be browsed offline without the live `gateway/app/static/css/operator_console.css`. **Not modified** in this wave; the redesign reuses it verbatim plus a few page-local styles inside `matrix_script_new.html` for tab affordances. |

## How to inspect locally

```bash
# Side-by-side diff of the new task page
diff -u before/matrix_script_new.html after/matrix_script_new.html | less

# Side-by-side diff of the workbench matrix_script block
diff -u before/task_workbench_matrix_script_block.html \
        after/task_workbench_matrix_script_block.html | less
```

To see the page rendered, open `after/matrix_script_new.html` in a
browser (the file references absolute paths like `/static/i18n.css`;
either run the gateway or temporarily inline-substitute the stylesheets).

## Mission deliverable mapping

Mission §6 asked for before/after screenshots covering the seven surfaces
below. Snapshot mapping:

| Mission surface | Snapshot file |
|---|---|
| Matrix Script new task page | `before|after/matrix_script_new.html` (full page) |
| Workbench top summary | `after/task_workbench_matrix_script_block.html` Block A region (search `matrix-script-block-a-goal-summary`) |
| Script structure + variants | `after/task_workbench_matrix_script_block.html` Blocks B + C (`matrix-script-block-b-script-structure`, `matrix-script-block-c-variant-strategy`) |
| Generation progress | `after/task_workbench_matrix_script_block.html` Block D (`matrix-script-block-d-generate-regenerate`) |
| Candidate review when no media exists | `after/task_workbench_matrix_script_block.html` Block E empty-state (`ms-block-e-no-preview-available`) |
| Delivery summary | `after/task_workbench_matrix_script_block.html` Block F (`matrix-script-block-f-delivery-teaser`) |
| Collapsed technical diagnostics | `after/task_workbench_matrix_script_block.html` collapsed `op-console-ms-secondary-fold` |

## Limits

- Real browser screenshots are NOT in this directory. Producing them
  requires running the FastAPI app + Playwright in a follow-up. The
  Jinja snapshots are honest stand-ins so reviewers can confirm the
  HTML the operator will see; visual rendering will match the PR #164
  + redesign styling once the page is served.
- The publish-hub matrix_script block is **unchanged** in this wave —
  PR #164 / OWC-MS-RO PR-4 already shipped the six op-card Delivery
  Center blocks (A 最终成片 / B 必需交付物 / C 场景包 / D 文案包 /
  E 发布反馈 / F 迭代归档). The publish-hub matrix_script block
  appears in this snapshot pair only for diff parity.
- The deliverable verdict after this wave is: **Matrix Script UI is
  operator-verifiable; backend final-video generation remains pending.**
  The redesign does not produce media. It makes honest what's there.
