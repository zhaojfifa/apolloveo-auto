# ApolloVeo 2.0 · W2 Admission Preparation Wave 指挥单 v1

**文档性质**：执行指挥单 / Phase Wave Brief  
**适用阶段**：W1 已闭环，W2 尚未解锁  
**用途**：在不启动 Provider 吸收代码的前提下，先完成 W2 准入基础设施、治理门禁与风险隔离  
**当前结论**：当前不允许直接进入 W2 Provider Absorption。必须先完成 W2 Admission Preparation，再以单 Provider、单 Adapter、单 PR 的方式进入 W2.1。

---

## 0. 当前阶段定义

当前阶段不是 Provider 吸收实施波次。  
当前阶段定义为：

**W2 Admission Preparation Wave**

其目标不是“先接一个 Provider 跑起来”，而是：

1. 先补齐 W2 的 guardrails、env、baseline、signoff 前置；
2. 先冻结 Adapter 生命周期边界；
3. 先把 Hot Follow 主链从后续 Provider 风险中隔离出来；
4. 先形成可以审计、可以回滚、可以逐波推进的 W2 工程底座。

---

## 1. 当前判断

### 1.1 已完成的前置事实
当前主线已具备以下基础：

- P2 解锁前的 Packet / Surface / Gate / Signoff 基线已基本收口；
- W1 donor absorption（M-01 ~ M-05）已闭环；
- W1 completion review 已形成；
- Matrix Script live preview 已完成结构校验，但这不改变 W2 准入顺序。

### 1.2 当前仍未解锁的原因
W2 仍未解锁，不是因为缺少新的业务代码，而是因为以下准入项尚需正式补齐并冻结：

1. `tests/guardrails/` 正式宿主与规则  
2. O-01 ~ O-03 env matrix  
3. W2 donor SHA pin  
4. Hot Follow regression baseline freeze  
5. Adapter lifecycle review / boundary  
6. donor mapping lifecycle rule 固化  

### 1.3 当前统一判断
- **允许做**：W2 Admission Preparation
- **不允许做**：W2 Provider code absorption
- **不允许做**：Provider runtime wiring
- **不允许做**：Hot Follow 主链业务修改
- **不允许做**：前端/工作台继续扩 scope

---

## 2. 本阶段总目标

在不吸收任何 Provider 实际代码的前提下，完成 W2 的工程准入基础设施建设，确保后续 W2.1 可以按 **单 Provider / 单 Adapter / 单 PR** 的方式安全进入。

完成后，应达到以下状态：

1. W2 具备独立 guardrail 宿主  
2. W2 具备统一 env / secret matrix  
3. W2 具备新的 donor SHA pin  
4. W2 具备 Hot Follow regression baseline  
5. W2 具备 Adapter lifecycle review authority  
6. W2 具备可执行的第一波准入规则（只批准 W2.1）

---

## 3. 总原则

### 3.1 先建隔离室，再搬 Provider
任何 Provider 代码进入前，必须先具备：
- guardrails
- env matrix
- donor pin
- baseline freeze
- lifecycle review

### 3.2 一次只批准一个风险层级
W2 不按“全家桶”推进，而按风险层级推进：

- W2.1：Understanding Provider
- W2.2：Subtitles / Dub Provider
- W2.3：Avatar / VideoGen / Storage Provider

### 3.3 Adapter 先评审，后实现
W2 不允许一边吸收 Provider，一边临场发明 Adapter 生命周期。
任何 AdapterBase 扩展，必须先在独立 review 中冻结。

### 3.4 Hot Follow 主链优先保护
任何会触碰 dub/subtitle path 的 Provider 波次，都必须以前置 baseline freeze 为准，不得把 Hot Follow 主链当成试验场。

### 3.5 每一波必须独立 review / merge / rollback
后续所有 W2 波次都必须满足：
- 单一目标
- 单一 Adapter
- 单一 Provider
- 单独 evidence
- 单独 review
- 可单独回滚

---

## 4. 当前阶段顺序

### Phase A — Guardrail Foundation
- 建 `tests/guardrails/`
- 迁移/新增 donor leak tests
- 增加 Provider leak tests
- 增加 “fallback never primary truth” tests

### Phase B — Env / Secret Matrix
- O-01 ~ O-03 env matrix
- local / render / production 配置维度
- provider secret loading baseline
- 禁止硬编码 token / key

### Phase C — Donor / Lifecycle Freeze
- 钉 W2 donor SHA
- 冻结 mapping row lifecycle
- 完成 Adapter lifecycle review
- 确认 W2.1 允许的最小 Adapter contract

### Phase D — Hot Follow Regression Freeze
- 冻结 Hot Follow regression baseline
- 明确 W2.2 前的不可触碰路径
- 固化 baseline 验证方法

### Phase E — W2.1 Admission Review
只有 A+B+C+D 全绿，才允许进入：
- **W2.1: Understanding Provider Absorption**

---

## 5. 角色任务分配

## A. 工程负责人

### 当前使命
完成 W2 准入基础设施，不写 Provider 代码。

### 必交付物
1. `tests/guardrails/` 宿主
2. W2 相关 leak / fallback 守门测试
3. O-01 ~ O-03 env matrix 对应文档/实现骨架
4. donor pin 回写
5. Hot Follow regression baseline 冻结协作件
6. W2 Admission Preparation execution log / evidence write-back

### 必须遵守
- 不吸收任何 Provider SDK/client
- 不修改 Hot Follow 主业务逻辑
- 不扩 AdapterBase 生命周期实现，除非 review 已先完成
- 不把 env matrix 写成散落 README

### 不负责
- 决定 W2.1 之外的 Provider 范围
- 直接批准 W2.2 / W2.3
- 代替架构师定义生命周期边界

---

## B. 架构师

### 当前使命
冻结 W2 admission gate，不重开大规划。

### 必须确认
1. `tests/guardrails/` 的规则是否足够作为 W2 第一防线
2. O-01 ~ O-03 env matrix 是否足够支撑 Provider 吸收
3. donor SHA pin 与 mapping lifecycle 是否正确
4. Adapter lifecycle review 是否足够支撑 W2.1
5. Hot Follow baseline 是否足够保护后续 Provider 波次

### 输出物
- W2 admission gate judgment
- Adapter lifecycle review
- W2.1 allowed / W2.2 pending / W2.3 pending 裁决
- exact blockers before W2.1 start

### 不负责
- 直接写 Provider 代码
- 替工程补测试
- 代替 reviewer 关闭 merge

---

## C. Reviewer / Merge Owner

### 当前使命
只关闭 W2 Admission Preparation Wave，不放大范围。

### 必须确认
1. `tests/guardrails/` 已建立且可执行
2. env matrix 已落位并可供后续复用
3. donor pin / lifecycle rule 已同步
4. Hot Follow baseline freeze 有明确证据
5. 当前变更不含 Provider 吸收代码
6. main 是否可作为 W2.1 唯一基线

### 输出物
- 每个 review 单元的通过 / 退回判断
- W2.1 start readiness judgment
- next owner / next action

### 禁止做
- 提前放行 W2.2 / W2.3
- 混入 Provider 实现
- 重开 packet/surface 旧议题

---

## 6. 当前最该做的动作

### 第一优先级
建立并冻结：
- `tests/guardrails/`
- provider leak tests
- fallback truth tests

### 第二优先级
完成：
- O-01 ~ O-03 env matrix
- secret loading baseline
- render/local/production 对齐规则

### 第三优先级
完成：
- W2 donor SHA pin
- mapping lifecycle rule
- Adapter lifecycle review

### 第四优先级
完成：
- Hot Follow regression baseline freeze
- baseline evidence
- W2 admission signoff

---

## 7. 当前禁止事项

当前阶段明确禁止：

- 任何 Provider client / SDK 吸收代码
- 任何 Provider runtime wiring
- 任何 Hot Follow 主链功能修改
- 任何“顺手”扩 AdapterBase 的实现性改动
- 任何 W2.2 / W2.3 预实现
- 任何前端 / workbench 扩 scope
- 任何第二套 truth / fallback state 语义

---

## 8. 交付与回写要求

每完成一个动作，必须同步回写：

- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 active execution log
- 对应 review / evidence 文档
- donor mapping doc（若涉及 pin / lifecycle）

至少写清楚：

1. 做了什么  
2. 明确没做什么  
3. 当前 blocker 还剩什么  
4. 下一棒交给谁  

---

## 9. W2.1 解锁条件

只有以下全部满足，才允许启动 **W2.1 Understanding Provider Absorption**：

1. `tests/guardrails/` 建立并通过  
2. Provider leak tests 就位  
3. “fallback never primary truth” tests 就位  
4. O-01 ~ O-03 env matrix 就位  
5. fresh W2 donor SHA pin 已写入 mapping doc  
6. Adapter lifecycle review 已通过  
7. Hot Follow regression baseline freeze 已完成  
8. reviewer signoff ready  
9. architect signoff ready  

---

## 10. W2 后续波次原则（提前冻结）

### W2.1 — Understanding Provider
- 允许：1 个 understanding/text provider
- 绑定：`UnderstandingAdapter`
- 规则：一个 Provider，一个 PR，一套 evidence

### W2.2 — Subtitles / Dub Provider
- 仅在 W2.1 完成后评估
- 需重新检查 Hot Follow baseline

### W2.3 — Avatar / VideoGen / Storage Provider
- 当前只作为规划波次
- 不视为已批准实施
- 需单独风险评审与 duplicate reconciliation

---

## 11. 总控口令

当前全体角色统一按这句执行：

> **Current execution focus is W2 Admission Preparation.  
> Do not absorb any provider code yet.  
> Engineering builds guardrails, env matrix, donor pin, and baseline freeze.  
> Architect freezes adapter lifecycle and W2.1 admission conditions.  
> Reviewer closes the admission wave.  
> Only after that do we start W2.1, with one provider, one adapter, one PR.**

---

## 12. 一句话总结

**现在不是“开始吸收 Provider”的阶段，而是“先把 W2 的准入隔离室建好”的阶段。先做 guardrails、env matrix、donor pin、adapter lifecycle review、Hot Follow baseline freeze；只有这些全绿，才允许启动 W2.1。**
