# ApolloVeo 2.0 · W2.1 Base-Only Adapter Preparation Wave 指挥单 v1

**文档性质**：执行指挥单 / Phase Wave Brief  
**适用阶段**：W2 Admission Preparation 已完成，W2.1 Provider Absorption 尚未解锁  
**用途**：统一 B1–B4 四个 base-only PR 的执行顺序、角色边界、验收口径与回写要求  
**当前结论**：Admission room 已打开，但 Provider room 仍未打开。当前只允许做 B1–B4 四个 AdapterBase base-only PR，不允许吸收任何 Provider client / SDK 代码。

---

## 0. 当前阶段定义

当前阶段不是 Provider Absorption Wave。  
当前阶段正式定义为：

**W2.1 Base-Only Adapter Preparation Wave**

这意味着：

- W2 Admission Preparation Phase A / B / C / D / E 已闭环；
- Phase E admission 已 PASS；
- W2.1 implementation 仍 BLOCKED；
- 当前唯一允许推进的实现工作，是 B1–B4 四个 base-only PR；
- 在 B1–B4 全绿前，任何第一个 W2.1 Provider PR 都不得启动。

---

## 1. 当前判断

### 1.1 已完成的前置事实
当前 `main` 已具备：

- W2 Admission Guardrails
- Env / Secret Matrix
- W2 donor SHA pin
- AdapterBase lifecycle review
- Hot Follow regression baseline freeze
- W2 admission signoff

### 1.2 当前阻塞点
当前阻塞 W2.1 implementation 的，不再是 admission review，而是以下四个独立 base-only gap：

1. B1 — auth / credential surface  
2. B2 — retry / timeout / cancellation  
3. B3 — error envelope (`AdapterError`)  
4. B4 — construction-vs-invocation lifecycle  

### 1.3 当前统一判断
- **允许做**：B1–B4 base-only PR
- **不允许做**：任何 Provider absorption
- **不允许做**：任何 Provider runtime wiring
- **不允许做**：Hot Follow 主链业务修改
- **不允许做**：W2.2 / W2.3 的预实现

---

## 2. 本阶段总目标

以四个相互独立、可单独 review / merge / rollback 的 PR，补齐 AdapterBase 在 W2.1 前的最低实现前置。

完成后，应达到以下状态：

1. AdapterBase 拥有清晰的 auth / credential surface  
2. AdapterBase 拥有统一的 retry / timeout / cancellation 入口  
3. AdapterBase 拥有统一的错误包络类型 `AdapterError`  
4. AdapterBase 明确 construction 与 invocation 的生命周期边界  
5. 后续第一个 W2.1 Provider PR 可在不扩 Base 的前提下启动

---

## 3. 总原则

### 3.1 一次只做一个 B 项
每个 B 项必须单独成 PR，不允许捆绑。

### 3.2 Base-only 与 Provider-only 严格分离
本阶段只允许改 Base，不允许同时引入任何 Provider client / SDK / adapter binding。

### 3.3 不碰业务真相
本阶段不允许修改：
- task truth
- packet/schema/contracts
- Hot Follow 业务逻辑
- workbench / delivery / preview 前台逻辑

### 3.4 可单独 review / merge / rollback
每个 B 项必须满足：
- 单目标
- 单证据
- 单 review
- 单回滚

### 3.5 不重开 admission review
Admission 阶段已闭环。本阶段不得借机重开 Phase A–E 的治理争论。

---

## 4. 推荐执行顺序

推荐顺序：

1. **B3 — error envelope**
2. **B1 — auth / credential surface**
3. **B2 — retry / timeout / cancellation**
4. **B4 — construction-vs-invocation lifecycle**

### 说明
- B3 先行，可为 B1/B2 提供统一错误语义
- B1 冻结凭证表面，便于后续 Provider client 接入
- B2 统一执行控制
- B4 最容易抽象过头，因此后置

> 注：这是推荐顺序，不是唯一合法顺序；若工程负责人有更稳的独立排序，可提请 reviewer 同意后调整。

---

## 5. 角色任务分配

## A. 工程负责人

### 当前使命
以最小实现补齐 B1–B4 四个 base-only gap，不提前进入 Provider 吸收。

### 当前只允许做
- Base-only 代码改动
- 对应最小测试
- evidence / execution write-back
- 与 B1–B4 直接相关的 review 支撑

### 当前禁止做
- Provider SDK / client / adapter 实现
- Hot Follow 主业务修改
- W2.2 / W2.3 相关预实现
- 前端 / workbench 扩 scope
- packet/schema/contracts 改动

---

## B. 架构师

### 当前使命
逐个裁决 B1–B4 的边界是否足够、是否过界。

### 必须确认
1. 每个 B 项是否仍属于 Base-only  
2. 是否引入了不必要的 Provider 语义  
3. 是否污染了业务 truth 或 runtime 责任边界  
4. 是否满足后续 W2.1 的最小可接入条件  

### 输出物
- 每个 B 项的 signoff judgment
- 是否允许进入下一 B 项
- B1–B4 全绿后的 W2.1 start judgment

### 不负责
- 直接写 Provider 代码
- 替工程补实现
- 重开 W2 admission review

---

## C. Reviewer / Merge Owner

### 当前使命
关闭 B1–B4 各自 PR，不扩大范围。

### 必须确认
1. 每个 B 项是否独立成 PR  
2. 是否存在无关改动  
3. 是否包含必要测试与 evidence  
4. 是否触碰禁止区域  
5. 当前 `main` 是否继续保持为唯一 authority baseline  

### 输出物
- 通过 / 退回判断
- remaining blockers
- next owner / next action

### 禁止做
- 提前放行 Provider PR
- 混入 Hot Follow 修改
- 混入 W2.2 / W2.3 代码
- 让多个 B 项混成一个大 PR

---

## 6. B1–B4 单项边界与验收口径

## B1 — Auth / Credential Surface

### 目标
为 AdapterBase 建立统一的认证/凭证表面，供后续 Provider adapter 以一致方式读取和验证 credentials。

### 允许改动
- AdapterBase 相关 base-only 接口/类型
- 凭证表面抽象
- 最小测试
- 对应 evidence / review 文档

### 禁止改动
- 任意 Provider SDK/client
- 实际 secret loading 逻辑扩散到具体 provider
- 业务层直接读 credentials
- Hot Follow 业务逻辑

### 验收口径
- 认证/凭证表面清晰可测
- 不带任何 provider-specific 行为
- 不破坏现有 adapter closed set
- 有最小测试与 evidence

---

## B2 — Retry / Timeout / Cancellation

### 目标
为 AdapterBase 建立统一的执行控制入口。

### 允许改动
- Base-only 调用控制接口
- timeout / retry / cancellation 相关抽象
- 最小测试
- evidence / review 文档

### 禁止改动
- Provider-specific retry policy
- 业务层 fallback 策略
- 直接接 runtime orchestration
- Hot Follow 主链逻辑

### 验收口径
- timeout / retry / cancellation 入口可测
- 不带 provider-specific 语义
- 不发明新的业务状态真相
- 有最小测试与 evidence

---

## B3 — Error Envelope (`AdapterError`)

### 目标
统一 AdapterBase 的错误包络。

### 允许改动
- `AdapterError` 类型
- 统一错误分类/字段
- 最小测试
- evidence / review 文档

### 禁止改动
- Provider-specific error parsing
- 业务层错误处理逻辑
- UI / presenter 错误文案逻辑
- Hot Follow 行为修复

### 验收口径
- `AdapterError` 明确可测
- 错误字段边界稳定
- 后续 Provider adapter 可消费但未预绑定
- 有最小测试与 evidence

---

## B4 — Construction-vs-Invocation Lifecycle

### 目标
冻结“构造期”与“调用期”的生命周期边界。

### 允许改动
- Base-only 生命周期约束
- construction / invocation 边界说明或最小实现
- 最小测试
- evidence / review 文档

### 禁止改动
- provider client 构造代码
- runtime wiring
- worker / line binding
- admission 旧文档回写之外的额外治理扩张

### 验收口径
- construction 与 invocation 的责任边界明确
- 不在 import 时做 I/O
- 不偷渡 provider-specific 初始化逻辑
- 有最小测试与 evidence

---

## 7. 当前禁止事项

当前阶段明确禁止：

- 任何 Provider client / SDK absorption
- 任何 Provider adapter implementation
- 任何 runtime wiring
- 任何 Hot Follow 主链功能修改
- 任何 W2.2 / W2.3 预实现
- 任何前端 / workbench 扩 scope
- 任何 packet/schema/contracts 修改
- 任何第二套 truth / fallback state 语义

---

## 8. 交付与回写要求

每完成一个 B 项，必须同步回写：

- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 active execution log
- 对应 review / evidence 文档

至少写清楚：

1. 做了什么  
2. 明确没做什么  
3. 当前 blocker 还剩什么  
4. 下一棒交给谁  

---

## 9. W2.1 Provider Absorption 解锁条件

只有以下全部满足，才允许进入真正的：

**W2.1 Provider Absorption Wave**

1. B1 全绿  
2. B2 全绿  
3. B3 全绿  
4. B4 全绿  
5. architect signoff ready  
6. reviewer signoff ready  
7. main 继续保持单一 authority baseline  

---

## 10. 后续波次关系

### 当前阶段
- W2.1 Base-Only Adapter Preparation Wave

### 下一阶段
- W2.1 Provider Absorption Wave（仅在 B1–B4 全绿后允许）

### 更后阶段
- W2.2 Subtitles / Dub Provider
- W2.3 Avatar / VideoGen / Storage Provider

当前不对 W2.2 / W2.3 开放实现授权。

---

## 11. 总控口令

当前全体角色统一按这句执行：

> **Current execution focus is W2.1 Base-Only Adapter Preparation.  
> Do not absorb any provider code.  
> Engineering implements B1–B4 one PR at a time.  
> Architect signs each base-only boundary.  
> Reviewer closes each PR independently.  
> Only after B1–B4 are all green do we open the first W2.1 provider PR.**

---

## 12. 一句话总结

**现在不是“开始吸收 Provider”的阶段，而是“先把 AdapterBase 的四块基础能力补齐”的阶段。B1–B4 必须逐项、独立、可回滚地完成；只有它们全绿，才允许进入真正的 W2.1。**
