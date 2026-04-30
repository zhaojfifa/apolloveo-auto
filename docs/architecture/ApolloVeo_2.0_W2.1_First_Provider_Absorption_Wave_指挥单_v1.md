# ApolloVeo 2.0 · W2.1 First Provider Absorption Wave 指挥单 v1

**文档性质**：执行指挥单 / Phase Wave Brief  
**适用阶段**：W2 Admission Preparation 已完成，W2.1 Provider Absorption 尚未解锁  
**用途**：统一第一条 Provider 吸收波次的范围、角色边界、验收口径与回写要求  
**当前结论**：本阶段允许启动**第一条** W2.1 Provider PR，但必须严格保持“单 Provider / 单 Adapter / 单 PR / 单 evidence”纪律；任何人不得以本文件替代当前阶段 authority、state、evidence 的读取与回写。

---

## 0. 使用声明（重要）

本文件是**阶段指挥基线**，不是永久真相替代物。  
后续任何执行，仍然必须继续读取并回写当前有效的：

- `docs/baseline/PRODUCT_BASELINE.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- 当前 active execution log
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 review / evidence / signoff 文档
- 当前 state / gate / packet / adapter authority 文档

**禁止**把本指挥单当成“以后不用再读状态文件”的借口。  
本文件只负责定义本阶段目标、边界和顺序；不替代动态状态读取。

---

## 1. 当前阶段定义

当前阶段正式定义为：

**W2.1 First Provider Absorption Wave**

其含义是：

1. W2 Admission Preparation 已完成；
2. B1–B4 base-only adapter preparation 已完成并签收；
3. 现在允许开启**第一条** Provider 吸收 PR；
4. 但当前只允许吸收**一个 Provider、一个 Adapter、一个 PR**；
5. 该波次的目标是证明“Provider 可在 ApolloVeo 2.0 工厂约束下被干净吸收”，而不是一次性铺开多 Provider 平台。

---

## 2. 当前判断

### 2.1 已完成的前置事实
当前主线应已具备以下基础（实际执行前仍需重新读取 authority 确认）：

- packet / surface / gate / signoff 的 pre-unlock 基线已闭环；
- W1 donor absorption 已闭环；
- W2 Admission Preparation Phase A–E 已完成；
- B1–B4（AdapterBase base-only）已闭环；
- 第一个 W2.1 Provider PR 已获得“可开启”判断。

### 2.2 当前仍然严格有效的红线
即使 Provider PR 被允许开启，以下红线仍然有效：

- 不得在 Provider PR 中继续修改 AdapterBase shape；
- 不得改 Hot Follow business/runtime；
- 不得碰 W2.2 / W2.3 scope；
- 不得把 fallback output 提升为 primary truth；
- 不得把 vendor/model/provider/engine 真相写入 packet/base surface；
- 不得在 adapter construction 阶段直接读 env；
- 不得在 construction/import 阶段做 I/O；
- Provider error 必须映射到 `AdapterError`；
- credentials 必须经 `AdapterCredentials / SecretResolver`；
- timeout / retry / cancellation 必须经 `AdapterExecutionContext`。

### 2.3 当前统一判断
- **允许做**：第一条 W2.1 Provider 吸收 PR
- **不允许做**：第二个 Provider、多个 Adapter 绑定、W2.2 / W2.3 预实现
- **不允许做**：Hot Follow 修复与业务扩写
- **不允许做**：把 UI、packet、runtime、provider 吸收绑进一个 PR

---

## 3. 本阶段总目标

以一个最小、可审计、可回滚的 Provider 吸收 PR，验证下列路径同时成立：

1. Provider client 可被干净吸收进入 Apollo 代码边界；
2. Provider 只通过既有 AdapterBase/B1–B4 表面接入；
3. 不引入新的业务真相；
4. 不污染 packet / surface / runtime authority；
5. 能形成一条完整 evidence chain；
6. 为后续 Matrix Script 第一条正式生产线提供理解/文本能力接入基础。

---

## 4. 第一波范围冻结

### 4.1 只批准一个 Provider
本阶段只允许一个 understanding/text provider。  
不得并行引入第二个 provider，也不得顺手放入 fallback provider。

### 4.2 只绑定一个 Adapter
本阶段只允许绑定：

- `UnderstandingAdapter`

不得同时触碰：
- `SubtitlesAdapter`
- `DubAdapter`
- `AvatarAdapter`
- `VideoGenAdapter`
- 其他能力 Adapter

### 4.3 只允许一个 PR
必须做到：

- 一个 PR
- 一个 Provider
- 一个 Adapter
- 一套 evidence
- 一轮独立 review / merge / rollback

---

## 5. 推荐实施对象

### 推荐对象
第一条 W2.1 Provider PR 应优先选择：

- **understanding / text provider**

### 选择原则
优先选择满足以下条件者：

1. 能力边界清楚；
2. 凭证和调用方式简单；
3. 不强依赖复杂媒体文件；
4. 不触碰 Hot Follow dub/subtitle 路径；
5. 不引入复杂多阶段异步编排；
6. 不要求额外 storage / avatar / video generation 逻辑。

### 当前不建议的对象
当前不建议第一波就吸收：

- 字幕 / 配音 provider
- 数字人 / 视频 provider
- 存储 / 资产 upload provider
- 需要复杂回调/轮询/任务状态机的 provider

---

## 6. 角色任务分配

## A. 工程负责人

### 当前使命
实现**第一条** Provider 吸收 PR，不越界、不扩 scope、不污染基线。

### 当前只允许做
- Provider client 最小吸收
- `UnderstandingAdapter` 最小绑定
- 必要的最小测试
- 必要的最小 evidence / execution write-back

### 当前禁止做
- 修改 AdapterBase shape
- 引入第二个 Provider
- 加 runtime orchestration
- 修改 Hot Follow
- 修改 packet/schema/contracts
- 修改前台 / workbench / preview
- 处理 W2.2 / W2.3 议题

---

## B. 架构师

### 当前使命
裁决第一条 Provider PR 是否仍然维持 base-only 上层纪律。

### 必须确认
1. 是否只绑定一个 Provider + 一个 Adapter
2. 是否没有越过 B1–B4 既有边界
3. 是否没有把 provider-specific truth 写入 packet/base surface
4. 是否没有 construction/import I/O 违规
5. 是否具备进入后续 line integration 的最小条件

### 输出物
- Provider absorption signoff judgment
- 是否允许进入后续 line integration
- exact remaining blockers

### 不负责
- 直接写 Provider 代码
- 代替工程修实现
- 重开 admission / base-only 旧议题

---

## C. Reviewer / Merge Owner

### 当前使命
关闭第一条 Provider PR，不扩大范围。

### 必须确认
1. 只有一个 Provider
2. 只有一个 Adapter binding
3. 无无关改动
4. 测试和 evidence 齐全
5. `main` 继续保持唯一 authority baseline

### 输出物
- 通过 / 退回判断
- remaining blockers
- next owner / next action

### 禁止做
- 顺手放行第二个 Provider
- 混入 Hot Follow、packet、前端改动
- 把 line integration 混进当前 PR

---

## 7. 工程边界与验收口径

## P1 — Provider Client Absorption

### 目标
将一个 Provider client 以 Apollo 原生边界吸收进 repo。

### 允许改动
- provider client 最小封装
- Apollo target path 落位
- 最小测试
- evidence / review 文档

### 禁止改动
- 直接把 donor 命名空间带进 repo
- 在业务层直接调用 provider SDK
- 多 provider fallback 逻辑
- 新 truth/state 语义

### 验收口径
- donor pin 明确
- severance 清楚
- 不产生 provider leakage
- 可单独 review / merge / rollback

---

## P2 — UnderstandingAdapter Binding

### 目标
让第一个 Provider 能通过 `UnderstandingAdapter` 被 Apollo 消费。

### 允许改动
- provider → `UnderstandingAdapter` 的最小绑定
- 必要的 request/response 适配
- 最小测试
- evidence / review 文档

### 禁止改动
- 修改 `AdapterBase`
- 修改其他 adapter
- 混入 prompt framework 扩写
- 直接把 provider response 当业务 truth

### 验收口径
- 绑定路径清晰
- 错误通过 `AdapterError`
- credentials 通过 `AdapterCredentials / SecretResolver`
- execution control 通过 `AdapterExecutionContext`

---

## P3 — Evidence Chain

### 目标
证明本次吸收是“干净的、可追溯的、可审计的”。

### 必须具备
- donor pin
- changed files
- tests run
- intentionally not done
- remaining blockers
- review / signoff 结论

---

## 8. 当前禁止事项

当前阶段明确禁止：

- 第二个 Provider PR
- 任何 W2.2 / W2.3 代码
- `SubtitlesAdapter` / `DubAdapter` / `AvatarAdapter` / `VideoGenAdapter` 绑定
- Hot Follow 修复
- workbench / panel / preview 扩写
- Matrix Script line integration
- 新的 packet/schema/contracts 设计
- 新的全局状态真相

---

## 9. 下一阶段关系

### 当前阶段
- W2.1 First Provider Absorption Wave

### 下一阶段（仅在本阶段绿后允许）
- Matrix Script First Production Line Wave

### 更后阶段
- W2.2 Subtitles / Dub Provider
- W2.3 Avatar / VideoGen / Storage Provider
- Digital Anchor Second Production Line Wave

---

## 10. 交付与回写要求

本阶段执行后，必须继续回写：

- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- 当前 active execution log
- 本波 Provider evidence 文档
- 对应 review / signoff 文档

至少写清楚：

1. 做了什么
2. 明确没做什么
3. 当前 blocker 还剩什么
4. 下一棒交给谁

---

## 11. 总控口令

当前全体角色统一按这句执行：

> **Current execution focus is W2.1 First Provider Absorption.  
> One provider, one adapter, one PR.  
> Do not change AdapterBase shape.  
> Do not touch Hot Follow.  
> Do not touch W2.2 / W2.3.  
> Engineering absorbs the first provider through UnderstandingAdapter only.  
> Architect signs the provider boundary.  
> Reviewer closes the PR independently.  
> Only after this wave is green do we move into Matrix Script first production line work.**

---

## 12. 一句话总结

**现在终于可以启动第一个 W2.1 Provider PR，但目标不是扩平台，而是证明“一个 Provider 能干净地接进 ApolloVeo 2.0 的工厂底座”。这一波必须单 Provider、单 Adapter、单 PR、单 evidence；过线后，下一棒才轮到 Matrix Script 第一条正式生产线。**
