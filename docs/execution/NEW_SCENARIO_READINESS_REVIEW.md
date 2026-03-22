# New Scenario Readiness Review

## 1. Review Scope

本次 readiness review 只覆盖：

- Hot Follow cleanup 之后的当前样本状态
- Skills MVP v0 sample 已落地后的当前工程状态
- 是否已经足够安全地开始“新 scenario 的讨论”

它不是：

- 新 scenario 计划文档
- 新 scenario 实现启动文档
- generalized platform strategy

## 2. What Is Already Strong Enough

当前 Hot Follow sample 中，以下部分已经足够强，可以作为后续参考点：

- line-aware state/sample structure 已形成并经过真实业务验证
- compose 主路径已稳定地位于 service contract 背后
- advisory hook sample 已完成 skeleton、content v0、UI rendering 的闭环
- business regression discipline 已成为强制 merge gate
- verification baseline discipline 已冻结并持续执行
- documentation / governance / progress-log discipline 已建立

这些部分已经足以支撑“讨论下一个 scenario 应该怎么进入”，而不必再等待平台化大实现。

## 3. What Still Remains Open in Hot Follow Cleanup

Hot Follow cleanup 仍未完全关闭，当前仍开放的点包括：

- `gateway/app/routers/tasks.py` 仍然结构偏大
- 仍有剩余 compatibility residue
- 仍有部分 scenario-aware façade residue
- 仍有一些 router ownership risk，主要集中在剩余的 Hot Follow compose/dub transitional glue
- 当前 sample 已明显更干净，但还不能宣称为 fully closed cleanup line

## 4. What Is Clearly Not Part of Hot Follow Cleanup Anymore

以下事项不应继续混在 Hot Follow cleanup line 里：

- Avatar-specific route / entry behavior
- baseline / legacy flow behavior
- future multi-line / platform work

原因是：

- 这些事项已被明确单独记录
- 它们不属于当前 Hot Follow sample 的核心清理闭环
- 它们若继续挂在 Hot Follow cleanup 名下，会让“是否可以开始新 scenario 讨论”被不必要地拖延

因此，这些事项应继续被单独跟踪，而不是作为当前 readiness judgment 的阻塞项。

## 5. Readiness Criteria for New-Scenario Discussion

当前判断基于以下 criteria：

- Hot Follow 不再携带 major hidden structure debt in active runtime ownership：部分满足
- remaining router residue 已被显式识别且范围有界：已满足
- business regression 稳定：已满足
- current line contract / state schema / advisory sample 足以作为 reference：已满足
- 新 scenario 不会立刻继承当前样本的 unresolved chaos：部分满足

总体来看，阻塞已经从“未知结构混乱”下降为“已知且有界的剩余 cleanup debt”。

## 6. Readiness Judgment

当前判断：

- Conditionally Ready

条件是：

- 进入新 scenario discussion 时，必须明确将剩余 Hot Follow router-space residue 作为 carry-forward cleanup debt 记录
- 不应把 Avatar / baseline / platform work 混入该 discussion

## 7. Recommended Immediate Next Step

当前推荐的 immediate next step 是：

- 可以开始 new-scenario discussion，但必须带着显式边界进行；同时保留一条最后的小范围 Hot Follow cleanup pass 作为并行或前置选项

不建议把当前判断解读为 Hot Follow cleanup 已 fully complete。
