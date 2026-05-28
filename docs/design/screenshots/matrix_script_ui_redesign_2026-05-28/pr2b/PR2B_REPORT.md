# PR-2B · Workbench Observable Production Flow Stepper — Implementation Report

Branch: `redesign/ms-workbench-flow-pr2b-20260528`
Wave: Matrix Script Operator Experience Implementation — **PR-2B of 7**
Date: 2026-05-28
Rollback point: PR-2A commit (`git log --oneline -1 HEAD~1`)

## Reading Declaration

Reads from PR-2A baseline (already in this branch's history): the
approved design plan §6.3 + Mission §B.2 (compact 3-step horizontal
stepper 脚本结构 → 变体选择 → 生成; navigation aid only; ≤120px when
collapsed; operator language only); existing helpers
`derive_matrix_script_script_structure_view` /
`derive_matrix_script_readable_variants` /
`derive_matrix_script_main_video_result` (PR-2A).

## Files changed

| File | Change | Net |
|---|---|---|
| `gateway/app/templates/task_workbench.html` | New compact stepper op-card between the PR-2A main video result block and the existing Block A. Three steps with same-page anchor hrefs (`#matrix-script-main-video-result`, `#matrix-script-block-b-script-structure`, `#matrix-script-block-c-variant-strategy`). Added matching `id=` attributes to the three target blocks so the anchors actually scroll. State per step (`done` / `active` / `todo`) derived inline from already-attached helpers. | +85 |
| `gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py` | NEW · 9 template-source tests covering ordering (between main-video and Block A), three-step canonical order (脚本结构 / 变体选择 / 生成), anchor target IDs, operator-language only (no engineering identifier in stepper card source), redesign-wave attribute. | +106 |
| `docs/design/screenshots/.../pr2b/` | Snapshot + report. | new |

## Scope boundary

**Inside PR-2B**: stepper template block + id attributes on the three anchor target blocks + tests + snapshot/report.

**Outside PR-2B** (sequenced into PR-2C / 2D / 3 / 4):
- Optional variants redesign (PR-2C — Block E rename + 1-main+N-optional).
- Workbench delivery summary + diagnostics quarantine (PR-2D).
- Delivery Center reframing (PR-3).
- Unified visual validation report (PR-4).

**Bytewise unchanged**: no helper created or modified, no wiring change, no contract/packet/closed-enum/schema/POST/endpoint change, no Hot Follow/Digital Anchor/Asset Supply touch, no provider/model/vendor/engine surface.

## Screenshots

Real browser capture via Claude Preview MCP on running gateway (pyenv Python 3.13.5, `AUTH_MODE=off`, viewport 1280×900). Inline image above. HTML snapshot:

| # | Capture | Viewport | URL | HTML | Runtime DOM probe |
|---|---|---|---|---|---|
| 1 | Workbench at task `2be4843363da` with PR-2A main video result + PR-2B stepper visible | 1280×900 | `/tasks/2be4843363da` | [`01_workbench_stepper_1280x900.html`](01_workbench_stepper_1280x900.html) | 3 steps: `[script_structure, done, "✓ 脚本结构 3 段已具备"]`, `[variant_selection, done, "✓ 变体选择 4 个候选已派生"]`, `[generation, todo, "3 生成 未生成"]` ✓ |

Visual confirmation: the stepper renders below the PR-2A main video result block, above Block A. Steps 1 + 2 show ✓ (脚本结构 has 3 sections; 变体选择 has 4 derived candidates); step 3 shows the 未生成 state badge from the helper. All step labels and counts are operator language only. The card sits below the main video block (which is tall due to the empty-state preview hero); the stepper appears just above Block A 任务摘要.

## Tests

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_workbench_production_flow_stepper.py \
                    gateway/app/services/tests/test_matrix_script_workbench_main_video_result_template.py \
                    gateway/app/services/tests/test_matrix_script_main_video_result_view.py
============================== 40 passed in 0.08s ==============================
```

Broader regression: still 1005 pass / 1 fail pre-existing / 17 skipped.

## Explicit no-change statement

This PR does **NOT**: touch any contract, packet, closed enum, schema, or endpoint; create or modify any helper; modify the wiring; touch Hot Follow / Digital Anchor / Asset Supply files; add provider/model/vendor/engine selectors; fake any media output; add any backend generation capability. The stepper is a pure presentation-layer Jinja navigation aid that reads from already-attached helper outputs.

## Remaining backend limitations (unchanged from PR-2A)

- No variant generation backend; the stepper "生成" step displays the honest state derived from `main_video_result.state_label_zh` (today: 未生成).
- No `final_video` worker.
- Closure store still volatile.

## Matrix Script is not production-operable

The stepper is a navigation aid. It does not change what the line actually produces. The wave target remains *"UI visually verifiable; backend final-video generation remains pending."* after PR-1..PR-4.

## Rollback

`git reset --hard <PR-2A-commit>` removes the PR-2B stepper + id attributes + tests + snapshot/report.
