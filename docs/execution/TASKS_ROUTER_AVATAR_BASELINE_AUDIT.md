# Tasks Router Avatar / Baseline Audit

## Purpose

本审计只记录 `gateway/app/routers/tasks.py` 中仍然存在的 Avatar-related 与 baseline-related touchpoints。

它不是本次 PR 的改造范围说明书，也不是新的 roadmap。

## Avatar Touchpoints Still In `tasks.py`

当前仍可见的 Avatar 相关触点主要包括：

- `tasks_page(...)`
  - 任务列表页仍保留 `apollo_avatar` 的 kind 兼容过滤语义
- `tasks_apollo_avatar_new(...)`
  - Avatar 新建页入口与 feature gate 仍直接挂在 router
- `tasks_avatar_new(...)`
  - `/tasks/avatar/new` 仍是指向 Apollo Avatar 新建页的兼容别名
- `list_tasks(...)`
  - 任务列表 API 仍保留 `apollo_avatar` 的 kind 兼容过滤语义
- task creation / task summary / task status 路径
  - `platform/category_key/kind` 的兼容判断仍会经过 router 入口

## Baseline / Legacy Flow Touchpoints Still In `tasks.py`

当前仍可见的 baseline / legacy task-flow 触点主要包括：

- `tasks_baseline_new(...)`
  - `/tasks/baseline/new` 仍是 `tasks_new(...)` 的兼容入口
- `tasks_newtasks(...)`
  - 任务创建向导仍在 router 层暴露
- `hot_follow_runtime_bridge` 的 compat imports
  - 仍通过 router 触达 Hot Follow 的 compatibility bridge
- 部分 legacy/compat helper 命名
  - router 中仍显式引用 `compat_*` helper 以维持现有调用面

## Why They Were Not Changed In This PR

这些触点本次未改，原因如下：

- 本次主目标是继续削薄 `tasks.py`，而不是开启 Avatar refactor
- Avatar 相关入口仍带有产品开关、模板入口、兼容 URL 语义，改动风险高于本次收益
- baseline / legacy 入口仍带有兼容路由职责，不适合在一次 Hot Follow-thinning PR 中顺手改写
- 当前更安全的做法是先把 clearly non-router 的列表整形与 workbench 页面组装移出，再单独评估这些入口是否值得继续收口

## Future Cleanup Candidates

后续更可能的 cleanup candidate 包括：

- `apollo_avatar` 的 kind/platform/category compatibility 判断
- `tasks_apollo_avatar_new(...)` / `tasks_avatar_new(...)` 的入口组织
- `/tasks/baseline/new` 这类 baseline alias route
- router 中残留的 `compat_*` bridge wiring

## Risks If They Continue To Accumulate

如果这些触点继续在 router 层累积，主要风险是：

- `tasks.py` 继续承载多产线兼容语义，削弱 router façade 边界
- Avatar 与 baseline alias 逻辑继续和主线任务路由混住，增加未来拆分成本
- compatibility residue 越来越像默认入口，而不是明确的过渡层

## Current Recommendation

当前建议仍然是：

- 先继续 Hot Follow sample 的 controlled thinning
- 将 Avatar / baseline touchpoints 保持为后续单独 cleanup 主题
- 不在本次 PR 中改变 Avatar 或 baseline flow behavior
