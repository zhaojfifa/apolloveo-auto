# ApolloVeo 2.0 多角色实施指挥单 v1

**文档性质**：执行指挥单  
**适用阶段**：P2 解锁前  
**用途**：统一产品、设计、工程、架构、Reviewer 的协作节奏与边界  
**当前结论**：现在不是“谁先写代码”的阶段，而是“谁先把 P2 的准入真相补齐”的阶段。产品先冻 packet，设计先冻 surface，工程只保 gate，架构做裁决，Reviewer 做闭环；P2 解锁前，不准进入 donor absorption。

---

## 0. 当前阶段定义

当前阶段不是 donor absorption implementation wave。  
当前阶段定义为：

**Packet Gate + Surface Gate + Signoff Closure Wave**

当前 `main` 已是后续工程 planning baseline；`v1.1 master plan` 是唯一母契约，Hot Follow 继续只作为 reference line。P2 仍未解锁，当前 blocker 仍集中在：

1. packet schema + sample + validator evidence  
2. surface contracts  
3. adapter base / donor signoff  
4. reviewer signoff  

---

## 1. 总目标

在不启动 donor absorption 的前提下，完成以下闭环：

1. 两条新线 packet 冻结  
2. 三大主 surface 冻结  
3. Packet Gate 跑实  
4. Hot Follow reference evidence 固化  
5. reviewer / architect signoff 闭环  
6. 为 P2 entry review 做最终准备  

---

## 2. 总原则

### 2.1 产品与前台优先
当前优先级高于 donor absorption engineering 的，是：

- Matrix Script packet
- Digital Anchor packet
- task / workbench / delivery surface
- 顶层业务流程图与 contract mapping

### 2.2 SwiftCraft 只是 capability donor
SwiftCraft 只能作为后台能力 donor 和实现参考层，不能成为新的 task/state truth 宿主。

### 2.3 Hot Follow 只是 reference line
本轮不得顺手改 Hot Follow 业务逻辑；它只作为 packet validator / onboarding gate 的 reference green baseline。

### 2.4 每一步必须相对独立、可单独 review
后续动作必须满足：

- 单步目标清楚
- 边界清楚
- 可单独 review / merge
- 失败不污染整体基线

---

## 3. 当前阶段顺序

### Phase A — Product Packet Freeze
- Matrix Script packet v1
- Digital Anchor packet v1
- sample packet instances
- asset supply matrix

### Phase B — Surface Freeze
- task area
- workbench
- delivery center
- Matrix Script variation panel
- Digital Anchor role/speaker panel
- surface contract mapping

### Phase C — Gate Closure
- packet validator
- onboarding gate
- Hot Follow reference evidence
- gate checklist / evidence index 回写

### Phase D — Signoff Closure
- architect signoff
- reviewer signoff
- donor precondition signoff

### Phase E — P2 Entry Review
只有 A+B+C+D 全绿，才允许进入 P2。

---

## 4. 角色任务分配

## A. 产品经理

### 当前使命
交付两条新线的 **truth interface**，而不是功能描述。

### 必交付物
1. `docs/contracts/matrix_script/packet_v1.md`
2. `schemas/packets/matrix_script/packet.schema.json`
3. `schemas/packets/matrix_script/sample/*.json`

4. `docs/contracts/digital_anchor/packet_v1.md`
5. `schemas/packets/digital_anchor/packet.schema.json`
6. `schemas/packets/digital_anchor/sample/*.json`

7. `docs/product/asset_supply_matrix_v1.md`

### 必须遵守
- 遵循 packet envelope / validator rules
- 引用 generic contracts，不复刻 generic objects
- 不得出现 vendor/model/runtime truth 字段
- sample 必须能被当前 validator + onboarding gate 消费

### 不负责
- runtime 实现
- donor/provider 逻辑
- 新状态真相定义

---

## B. 设计师

### 当前使命
把 packet 与 generic contracts 落成前台三大 surface，而不是做工具页。

### 必交付物
1. task area low-fi
2. workbench low-fi
3. delivery center low-fi
4. Matrix Script variation panel
5. Digital Anchor role/speaker panel
6. 每个 surface 的 contract mapping notes

### 必须遵守
- 只消费 contract objects
- 所有状态必须来自 L2/L3
- 不出现 vendor_id / model 选择
- Scene Pack 必须非阻塞
- 不暴露 donor / supply 概念到前台

### 不负责
- backend/provider 逻辑
- packet schema 真相
- 新的状态定义

---

## C. 工程师

### 当前使命
把 gate 跑实，不要提前吸 donor。

### 当前工程重点
1. packet validator
2. onboarding gate
3. capability adapter base
4. frontend ↛ donor/supply guardrail
5. Hot Follow reference green evidence

### 当前只允许做
- 配合新线 packet 过 gate
- 固化 evidence / execution write-back
- 补最小 gate support
- 收紧 signoff 前置条件

### 禁止做
- donor absorption
- provider implementation
- 新线 runtime 编排
- Hot Follow 业务修改

---

## D. 架构师

### 当前使命
做 gate 裁决，不重开大规划。

### 必须确认
1. onboarding gate 是否足以作为 packet admission layer
2. Hot Follow reference evidence 是否足够成为 green baseline
3. capability adapter base 是否足以作为 donor precondition
4. Matrix Script / Digital Anchor packet 还缺哪些准入条件

### 输出物
- Packet Gate signoff judgment
- donor precondition judgment
- exact remaining blockers before P2 entry review

### 不负责
- 代替产品写字段
- 代替设计画 surface
- 直接做 donor 吸收代码

---

## E. Reviewer / Merge Owner

### 当前使命
关闭 pre-unlock wave，不扩大范围。

### 必须确认
1. onboarding gate skeleton
2. packet entry/scaffolding
3. Hot Follow reference evidence
4. doc/evidence write-back 是否足够协同使用
5. 当前 baseline 是否可作为后续 packet freeze 的统一依据

### 输出物
- 每个 review 单元的通过 / 退回判断
- remaining signoff items
- next owner / next action

### 禁止做
- 提前放行 donor wave 1
- 提前要求 provider implementation
- 重开治理层争论

---

## 5. 当前最该做的动作

### 第一优先级
产品侧立刻完成：

- Matrix Script packet
- Digital Anchor packet
- sample json
- asset supply matrix

### 第二优先级
设计侧立刻完成：

- task / workbench / delivery low-fi
- variation / role-speaker panels
- contract mapping notes

### 第三优先级
工程侧只做最小承接：

- 让新线 packet 能接入 validator / onboarding gate
- 固化 Hot Follow reference evidence 使用路径
- 配合 gate report 输出

### 第四优先级
架构师 / reviewer 完成：

- packet gate signoff
- donor precondition signoff
- P2 entry review 触发条件确认

---

## 6. 当前禁止事项

当前阶段明确禁止：

- donor wave 1 absorption
- provider client implementation
- 新线 runtime implementation
- Hot Follow feature-fix
- frontend 暴露 vendor/model
- donor/supply 直连前台
- 任何第二套 task/state truth

---

## 7. 交付与回写要求

每个角色完成动作后，必须同步更新对应协同文件，保证多人共享同一真相：

- `CLAUDE.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 active execution log
- 对应 review / evidence 文档

至少写清楚：

1. 做了什么  
2. 明确没做什么  
3. 当前 blocker 还剩什么  
4. 下一棒应该交给谁  

---

## 8. P2 解锁条件

只有以下全部满足，才允许进入 P2：

1. Matrix Script packet schema + sample + validator evidence 通过  
2. Digital Anchor packet schema + sample + validator evidence 通过  
3. surface contracts / low-fi contract mapping ready  
4. onboarding gate ready  
5. Hot Follow reference evidence ready  
6. adapter base / donor precondition ready  
7. reviewer signoff ready  
8. architect signoff ready  

---

## 9. 总控口令

当前全体角色统一按这句执行：

> **Current execution focus is Packet Gate + Surface Gate + Signoff Closure.  
> Do not start donor absorption.  
> Product freezes line packets.  
> Design freezes task/workbench/delivery + line-specific panels.  
> Engineering keeps gate/evidence ready.  
> Architect signs gate conditions.  
> Reviewer closes the pre-unlock wave.  
> Only after that do we run P2 entry review.**

---

## 10. 一句话总结

**现在不是“谁先写代码”的阶段，而是“谁先把 P2 的准入真相补齐”的阶段。产品先冻 packet，设计先冻 surface，工程只保 gate，架构做裁决，Reviewer 做闭环；P2 解锁前，不准进入 donor absorption。**
