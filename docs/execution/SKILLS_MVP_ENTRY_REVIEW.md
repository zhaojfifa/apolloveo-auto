# Skills MVP Entry Review

## 1. Current Readiness

项目现在可以进入 Skills MVP entry review，但还不适合直接启动广义 Skills implementation。

当前 readiness 基于以下已完成事实：

- router direct coupling 已清零
- compose 主链已收口到 `CompositionService`
- 最小 line-aware gate binding 已建立
- verification baseline 已冻结
- parse / subtitle / compose duration 的业务一致性问题已在真实业务流中验证修复
- `tasks.py` thinning 与 compatibility helper isolation 已推进

当前仍不适合直接做 broad Skills runtime 的原因：

- `tasks.py` 与 `hot_follow_api.py` 仍有 Hot Follow-specific residue
- compatibility-only helpers 仍存在
- publish / workbench / detail 尚未 fully line-aware unified
- 当前 gate/profile resolution 仍是 Hot Follow-focused 最小实现

因此，本阶段只定义最窄的 Skills MVP entry boundary，不启动执行。

## 2. First Hook Location

第一个 Skills hook 应放在 Hot Follow workbench / operator guidance layer。

当前最安全的具体位置：

- `GET /api/hot_follow/tasks/{task_id}/workbench_hub` 对应的 workbench hub 聚合结果之后
- 以现有 `artifact_facts`、`current_attempt`、`operator_summary`、`ready_gate`、deliverable facts 为只读输入
- 作为额外 advisory block 注入 workbench payload，而不是改写已有状态块

为什么这里最安全：

- 这里已经是 presentation / operator guidance 层，不是 runtime ownership 层
- 现有 payload 已有稳定事实来源，不需要创建新的 truth source
- advisory 输出可以天然是 non-blocking，不会直接触发 compose / publish / repo write
- 该位置最符合当前 business regression discipline，容易人工验证

当前不建议的第一 hook 位置：

- compose service 内
- ready gate engine 内
- status policy truth derivation 内
- publish path 内
- router entry 或 bridge compatibility 层内

## 3. Inputs

Skills MVP v0 第一 hook 允许读取以下输入：

- `task`
  - 仅当前 task dict 的只读快照
- line contract reference
  - `task.kind`
  - `LineRegistry.for_kind(task.kind)` 的结果或等价 line reference
- ready gate facts
  - `ready_gate`
  - gate reason / gate details
- presentation facts
  - `pipeline`
  - `pipeline_legacy`
  - `deliverables`
  - `media`
  - `source_video`
- operator-facing aggregates
  - `artifact_facts`
  - `current_attempt`
  - `operator_summary`
- four-layer state contract 已暴露的只读事实
  - object/source facts
  - attempt facts
  - derived freshness / ready gate facts
  - presentation-safe aggregates
- availability facts
  - subtitle/audio/final existence与url级事实

输入约束：

- hook 只能读取已有 truth-source blocks
- 不允许把 legacy status 当成高于 artifact facts 的新真相
- 不允许额外读取未冻结的 provider 内部状态作为决策主依据

## 4. Outputs

Skills MVP v0 第一 hook 允许输出一个只读 advisory block，建议格式为结构化 dict：

- `advisory.id`
- `advisory.kind`
- `advisory.level`
- `advisory.recommended_next_action`
- `advisory.operator_hint`
- `advisory.explanation`
- `advisory.evidence`

允许的输出语义：

- structured advisory
- recommended next action
- operator hint
- non-blocking explanation text

输出约束：

- advisory 只能补充说明，不能改写现有 `operator_summary`
- advisory 不能覆盖 `ready_gate`、`pipeline`、`deliverables`、`artifact_facts`
- advisory 不是新的 status / compose / publish contract

## 5. Explicit Non-Goals

Skills MVP v0 明确不做：

- 不写 repo state
- 不写 deliverables
- 不 override status truth
- 不触发 compose
- 不触发 publish
- 不 mutate deliverables
- 不替换 gate / status policy
- 不变成 hidden orchestration layer
- 不实现 multi-line Skills runtime
- 不实现 Skills marketplace / provider expansion

## 6. Merge Gate

任何 Skills MVP implementation PR 在合并前必须满足：

- 入口位置仍然保持在 read-only advisory layer
- 不改变 runtime ownership
- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md` 仍是输入模板基线
- contract 文档同步更新：
  - `docs/contracts/SKILLS_MVP_ADVISORY_CONTRACT.md`
  - 相关 execution / runbook 文档
- business regression 必须重跑，至少覆盖：
  - Case A — Parse Status Consistency
  - Case B — Subtitle Editing Semantics
  - Case D — Deliverable Consistency
  - Case F — Workbench Consistency
- verification baseline 必须声明解释器与环境
- progress log 必须追加
- PR 必须明确写出：
  - it fixes / adds
  - it does not do
  - follow-up remains
