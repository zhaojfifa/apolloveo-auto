# ApolloVeo 2.0 · Matrix Script First Production Line Wave 指挥单 v1

**文档性质**：执行指挥单 / Production Line Brief  
**适用阶段**：W2.1 第一条 Provider 吸收已通过，ApolloVeo 2.0 准备落出第一条正式生产结果  
**用途**：统一 Matrix Script 作为第一条正式生产线的产品、契约、UI、工程、交付与回填路径  
**当前结论**：Matrix Script 是 ApolloVeo 2.0 最适合先落地的第一条正式生产线。它应先证明“脚本/变体/反馈闭环”的生产工厂模式，而不是一开始追求完整视频平台。

---

## 0. 使用声明（重要）

本文件是 Matrix Script 第一条正式生产线的阶段指挥基线。  
它不替代动态 authority、state、evidence 的读取与回写。

后续执行仍必须持续读取并回写：

- `docs/baseline/PRODUCT_BASELINE.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `schemas/packets/matrix_script/sample/*.json`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`
- 当前 active execution log
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 review / evidence / signoff 文档

本文件定义阶段顺序、边界与验收口径，但**不替代**当前真实状态文件。

---

## 1. 当前阶段定义

当前阶段正式定义为：

**Matrix Script First Production Line Wave**

其含义是：

1. Matrix Script 不再只是 packet/schema/demo/panel preview；
2. 它将成为 ApolloVeo 2.0 的第一条正式生产线；
3. 本阶段的重点是让 Matrix Script 形成从 task 到 workbench 到 delivery 再到 publish feedback 的闭环；
4. 当前不追求全视频平台，也不追求重前端系统，更不追求三条产线同时完备。

---

## 2. 为什么先做 Matrix Script

### 2.1 它是当前最轻的正式产线
相比 Digital Anchor，Matrix Script：

- 对重视频生成依赖更轻；
- 对 role/scene/speaker 资产依赖更轻；
- 更适合先证明“工厂式内容生产闭环”。

### 2.2 它已具备较好的 truth interface
当前 Matrix Script 已拥有：

- packet contract
- schema
- sample packet
- variation panel low-fi
- preview / live projection 基础

这意味着它已经可以从“静态定义”进入“正式生产线”。

### 2.3 它最适合作为 2.0 第一条正式生产结果
第一条正式产线的目标不是做得最重，而是做得最稳、最可复用、最能给后续 Digital Anchor 提供模板。

---

## 3. 本阶段总目标

把 Matrix Script 从“可过 gate 的 packet + 可看的 panel”推进到“可生产、可交付、可回填”的正式生产线。

完成后，应达到以下状态：

1. task area 可创建 Matrix Script 任务；
2. workbench 可查看和校对 variation matrix / slot detail / publish feedback；
3. delivery center 可查看 deliverables / metadata / manifest / publish result；
4. packet → workbench → delivery → feedback 的映射清晰可追溯；
5. Matrix Script 成为可复用的第一条正式生产线样板。

---

## 4. 总原则

### 4.1 先做生产闭环，不做全平台
本阶段目标是闭环，不是平台化。

### 4.2 只消费既有 contract truth
所有实现必须从 packet / generic refs / line-specific refs / derived gates 出发。  
不得发明新的业务真相。

### 4.3 先做工作台，不做模型控制台
本阶段 UI 目标是：
- task area
- workbench
- delivery center
- Matrix Script variation panel

不得先做：
- provider/model 选择器
- 复杂 Prompt Studio
- 跨线统一后台

### 4.4 发布反馈是闭环的一部分
`publish_feedback` 不是后话，它是 Matrix Script 成为正式生产线的关键部分。  
如果只做生成不做回填，这条线就还是 demo，不是工厂。

### 4.5 每一步可独立 review / merge / rollback
本阶段推进仍必须波次化。

---

## 5. 角色任务分配

## A. 产品经理

### 当前使命
把 Matrix Script 的 truth interface 从 packet 级定义推进到可生产的闭环定义。

### 必须确认
1. `variation_plan` 的生产含义
2. `copy_bundle` 的交付含义
3. `publish_feedback` 的回填含义
4. `result_packet_binding` 的 deliverable 绑定含义
5. `asset_supply_matrix` 中 Matrix Script 行是否足够支撑生产

### 输出物
- 必要的 packet / contract clarification
- 生产线闭环定义说明
- publish feedback 回填口径

### 不负责
- provider 代码
- UI 实现细节
- runtime 细节

---

## B. 设计师

### 当前使命
把 Matrix Script 从 panel preview 推进为正式 workbench surface。

### 必须确认
1. task area 中的 Matrix Script 任务入口
2. workbench 中 variation matrix / slot detail / feedback 区
3. delivery center 中 Matrix Script 的交付面
4. 每个区块的 contract mapping notes

### 输出物
- Matrix Script 正式 surface low-fi / implementation notes
- task/workbench/delivery 对应 mapping notes

### 不负责
- provider/model 选择
- packet 真相定义
- runtime / backend 行为

---

## C. 工程负责人

### 当前使命
把 Matrix Script 的 contract、surface、delivery 和 feedback 接成第一条正式产线。

### 当前只允许做
- Matrix Script 任务入口的最小承接
- variation panel/workbench 的正式接线
- delivery center 的最小接线
- publish feedback 的最小读写路径
- 与 Matrix Script 直接相关的 evidence / execution write-back

### 当前禁止做
- 扩到 Digital Anchor
- 扩到 W2.2 / W2.3
- 扩到复杂前端平台化
- 改 Hot Follow 主业务
- 在当前阶段重做 packet / gate 基座

---

## D. 架构师

### 当前使命
确认 Matrix Script 是否已真正成为正式产线，而不是仍停留在 demo/preview 层。

### 必须确认
1. packet → workbench → delivery → feedback 是否形成单线闭环
2. 是否仍只消费 contract truth
3. 是否没有引入第二套 truth
4. 是否可作为第二条产线（Digital Anchor）的模板

### 输出物
- Matrix Script production line signoff
- exact remaining blockers before Digital Anchor wave

---

## E. Reviewer / Merge Owner

### 当前使命
关闭 Matrix Script 第一条正式生产线波次，不扩大范围。

### 必须确认
1. 是否仅围绕 Matrix Script
2. 是否没有混入 Hot Follow / Digital Anchor / provider 平台化
3. 是否有完整 evidence chain
4. `main` 是否继续保持单一 authority baseline

### 输出物
- 通过 / 退回判断
- remaining blockers
- next owner / next action

---

## 6. 阶段拆分建议

## Phase A — Task Entry

### 目标
让 task area 能以 contract-driven 方式创建 Matrix Script 任务。

### 最小范围
- topic / product / platform / variation target 等任务入口
- 不引入 provider/model 选择

### 验收
- 可创建任务
- 输入可映射到 packet truth

---

## Phase B — Workbench Variation Surface

### 目标
让 workbench 成为 Matrix Script 的正式操作面。

### 最小范围
- variation matrix
- slot detail
- attribution / refs
- publish feedback projection

### 验收
- 与 packet/sample/design authority 一致
- 不发明新 truth
- debug preview 可升级为正式 panel

---

## Phase C — Delivery Binding

### 目标
让 Matrix Script 的 deliverables、manifest、metadata 进入 delivery center。

### 最小范围
- delivery pack projection
- result_packet_binding 可视化
- metadata / manifest 接线

### 验收
- delivery center 可读
- 与 line packet 可追溯

---

## Phase D — Publish Feedback Closure

### 目标
让 publish feedback 成为正式回填对象。

### 最小范围
- feedback 结构投影
- variation_id 级回填
- 不做复杂营销后台

### 验收
- feedback 可读 / 可回填 / 可追溯
- 闭环成立

---

## 7. 当前禁止事项

当前阶段明确禁止：

- 直接并行推进 Digital Anchor 正式实现
- 复杂 provider/model 控制台
- 多 Provider fallback orchestration
- 重前端平台化（React/Vite 全量重构）
- Hot Follow 功能扩写
- W2.2 / W2.3 代码推进
- 引入新的 packet/state truth

---

## 8. 交付与回写要求

每个阶段完成后，必须同步回写：

- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 active execution log
- Matrix Script 对应 evidence / review 文档
- 必要的 design / product clarification 文档

至少写清楚：

1. 做了什么
2. 明确没做什么
3. 当前 blocker 还剩什么
4. 下一棒交给谁

---

## 9. 下一阶段关系

### 当前阶段
- Matrix Script First Production Line Wave

### 后续阶段
- Digital Anchor Second Production Line Wave
- W2.2 Subtitles / Dub Provider
- W2.3 Avatar / VideoGen / Storage Provider
- Workbench Surface Implementation 收口波次（若仍需要）

本阶段不对这些后续阶段开放实现授权。

---

## 10. 总控口令

当前全体角色统一按这句执行：

> **Current execution focus is Matrix Script First Production Line.  
> Do not expand into Digital Anchor or W2.2/W2.3.  
> Product clarifies packet-to-production truth.  
> Design upgrades variation panel into workbench surface.  
> Engineering wires task, workbench, delivery, and publish feedback into one line closure.  
> Architect signs the line closure.  
> Reviewer closes the wave independently.**

---

## 11. 一句话总结

**Matrix Script 现在应成为 ApolloVeo 2.0 的第一条正式生产线。目标不是做大平台，而是先做出一条“task → workbench → delivery → publish feedback”完整闭环的工厂样板。**
