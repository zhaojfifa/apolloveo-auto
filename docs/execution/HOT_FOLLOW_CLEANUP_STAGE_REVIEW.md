# Hot Follow Cleanup Stage Review

## 1. Review Scope

本次 freeze/review 只覆盖当前 Hot Follow cleanup continuation：

- 继续削薄 `gateway/app/routers/tasks.py`
- 继续缩窄 Hot Follow compatibility residue
- 继续明确 router façade 与 line-specific assembly 的边界
- Avatar / baseline touchpoints 维持 audit-only 处理，不进入本次改造

这不是新的架构阶段启动，也不是第二条产线或平台化工作的入口。

## 2. What Has Been Completed in This Cleanup Stage

本 cleanup stage 内已完成的事项包括：

- 任务列表整形、任务 summary 组装、workbench 页面上下文组装已继续移出 `tasks.py`
- Hot Follow compat bridge wiring 已进一步收口，不再直接散落在 `tasks.py` 的 compose path 中
- dub 入口前的 subtitle-lane / route-state / no-dub 候选整形已收口到更窄的 compat boundary
- advisory entry surface 已提前清理，避免 router 继续吸收 presentation-side shaping
- Hot Follow advisory skeleton、advisory content v0、advisory UI rendering 已经在前序节点落地
- Hot Follow business regression discipline 与 verification baseline 在这一阶段保持为强制 merge gate

## 3. What Still Remains Partial

当前仍然只是 partial，而不是 fully cleaned：

- `gateway/app/routers/tasks.py` 仍然结构偏大
- compatibility residue 仍然存在，尤其是 compat imports 与过渡性 façade 命名
- Avatar 与 baseline 的 route/entry behavior 仍留在 router 空间
- 仍有部分 scenario-aware façade logic 没有完全退出 `tasks.py`
- Hot Follow sample 明显更干净了，但还没有做到 fully thinned

## 4. Why Avatar / Baseline Was Not Refactored Here

Avatar / baseline 在这一阶段被记录但未改动，原因很明确：

- 当前 PR scope 明确停留在 Hot Follow cleanup
- Avatar 与 baseline 入口仍带有兼容路由、入口模板、feature gate 等高风险语义
- 在 Hot Follow-thinning PR 中顺手改这些行为，会扩大风险面并模糊业务线边界
- 这些触点应作为后续 dedicated cleanup candidates 单独评估，而不是在本阶段被连带改写

## 5. Business-Line Validation Summary

近期 cleanup PR 保持了以下业务线约束：

- Hot Follow behavior 作为唯一 active line 被持续验证
- Avatar behavior 没有被顺带修改
- baseline / legacy flow behavior 没有被顺带修改
- 共享区域如果发生机械性触达，也保持为不改变行为的 boundary cleanup

## 6. Boundary Validation Summary

近期 cleanup PR 保持了以下架构边界：

- compose ownership 未变化
- publish ownership 未变化
- ready-gate / status truth ownership 未变化
- Skills ownership 边界未变化
- 没有开启第二条产线扩张
- 没有开启 generalized platform / runtime 扩张

## 7. Recommended Immediate Next Direction

当前更合适的下一步是：

- 继续 controlled Hot Follow cleanup，优先再做一次小范围 entry review 或小范围 router/presentation boundary 收口

不建议立刻转向 Avatar refactor、baseline rewrite、第二产线复制或 broad platform work。

## 8. What Is Still Not Allowed

当前仍明确不允许：

- 在这条 cleanup path 上直接做 Avatar refactor
- 在这条 cleanup path 上直接做 baseline-flow rewrite
- 启动第二条 production line
- 开启平台化 / generalized runtime work
- 把当前 cleanup checkpoint 扩写成 broad architecture program
