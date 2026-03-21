# Skills MVP Advisory Contract

## 1. Scope

本 contract 只定义 Hot Follow 的 Skills MVP v0 advisory-only hook。

它不是：

- Skills runtime framework
- orchestration contract
- multi-line plugin system

## 2. Inputs

该 hook 只能读取当前 Hot Follow workbench hub 已存在的只读事实与聚合结果。

允许输入按组冻结如下：

- `task`
  - 当前 task dict 的只读快照
- line contract metadata
  - `task.kind`
  - line reference / line contract metadata
- four-layer state facts
  - object/source facts
  - attempt facts
  - derived readiness/freshness facts
  - projection/presentation-safe facts
- concrete allowed blocks
  - `ready_gate`
  - `pipeline`
  - `pipeline_legacy`
  - `deliverables`
  - `media`
  - `source_video`
  - `artifact_facts`
  - `current_attempt`
  - `operator_summary`

该 hook 不能成为新的 runtime truth source。

## 3. Outputs

advisory 输出必须是 small, structured, read-only：

- `advisory.id`
- `advisory.kind`
- `advisory.level`
- `advisory.recommended_next_action`
- `advisory.operator_hint`
- `advisory.explanation`
- `advisory.evidence`

输出必须是 non-blocking 的说明性数据。

## 4. Call Site Boundary

Skills MVP v0 的唯一允许调用边界是：

- Hot Follow workbench / operator guidance payload 的 advisory block 生成位置

当前不允许的调用位置：

- compose service
- publish runtime
- ready gate engine
- status policy truth derivation
- compatibility bridge as runtime owner

## 5. Ownership Boundary

该 contract 不拥有：

- repo state write
- deliverable write / artifact mutation
- current-final promotion
- gate / status policy truth
- compose / publish / parse / dub execution
- multi-line runtime ownership

它只能补充 advisory，不得改写既有 truth blocks。

## 6. Failure / Fallback Behavior

若没有 advisory、hook 未接入、或 advisory 计算失败：

- 主 payload 仍按现有 runtime / state / projection 逻辑返回
- 不阻塞 compose / publish / workbench 展示
- 不回退为新的 legacy truth
- advisory block 可为空、缺失或降级为 non-blocking note
