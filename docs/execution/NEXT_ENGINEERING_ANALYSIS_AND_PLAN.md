# 1. Baseline Understanding

## 项目统一定位

ApolloVeo 当前不是“泛化视频平台”，而是 **以成片交付为目标的 AI 内容生产工厂**。工程组织必须以产线为核心，而不是以 provider、工具或 UI 页面为核心。

当前主线不是做 2.0 大平台，而是继续完成 **v1.9 运营稳定化与基座收口**，让 Hot Follow 成为第一条真正可复制的标准产线。

## 当前阶段

当前阶段已经从“链路能否跑通”转向“状态真相、交付物真相、产线合同和运行时边界是否一致”。

从 `docs/reviews/ALIGNMENT_BASELINE_20260318.md`、`_drafts/B.2 .REVIEW_v1.9_BASELINE.md`、`_drafts/C.1`、`_drafts/C.2`、`_drafts/C.3`、`_drafts/C.5`、`_drafts/E.1` 结合代码状态来看，当前阶段判断是：

- Hot Follow 主链已具备试运营条件。
- 产线合同、ready gate、部分服务拆分已经起步。
- 运行时仍未真正进入 line-contract-driven。
- 当前仍处于“基座收口期”，不是“扩第二平台层”的时机。

## 已冻结原则

后续建议必须继续服从以下冻结原则：

- `SSOT / deliverables-first`：交付物事实优先，状态只能派生，不能反向覆盖事实。
- `Unified Gateway`：业务入口要继续收口，不能把 provider 直连和业务判定扩散到更多 router/service。
- `Asset ≠ Artifact`：任务交付物、运行中 artifact、沉淀资产必须分层，不能继续混用名词和职责。
- `Factory-first, not platform-first`：先做标准产线与基座收口，再做平台化抽象。
- `line contract / scenario contract / deliverable contract` 需要显式化，不能继续靠隐式 dict 和页面逻辑维持。
- `registry / catalog / skills / ops` 只能做边界清晰的支撑层，不能替代业务真相源。
- 不能继续制造 God file / God router / God service。
- 不能用 UI 补丁掩盖状态真相问题。

## 当前禁止继续犯的错误

- 继续在 `gateway/app/routers/tasks.py` 和 `gateway/app/routers/hot_follow_api.py` 之间互相懒加载。
- 继续把 Hot Follow 专属逻辑塞回总路由或总步骤函数。
- 继续让 `workbench_hub` 依赖无类型约束的大 dict 作为隐式 API 合同。
- 继续把 line contract 当成“声明存在”，但运行时完全不消费。
- 继续把 asset sink、skills bundle、worker profile 只写在文档/YAML，不进入运行时绑定。
- 继续扩大 `/api` 与 `/v1` 的双语义分裂，让前端或 ops 依赖 fallback 兜底。


# 2. What Has Been Landed

## task1.3 实际落地内容

`task1.3` 已经完成了 **共享 helper 的第一轮下沉**，不是纯文档宣称。

已确认落地：

- 新增了 `gateway/app/services/task_view_helpers.py`
- 新增了 `gateway/app/services/voice_state.py`
- 新增了 `gateway/app/services/compose_helpers.py`
- 新增了 `gateway/app/services/media_helpers.py`
- 新增了 `gateway/app/core/constants.py`
- `gateway/app/routers/hot_follow_api.py` 顶部已改为从这些 services/core 模块导入 helper，而不是直接批量从 `tasks.py` 导入

这说明 task1.3 至少完成了“39 个共享 helper 从 `tasks.py` 拆出”的主体工作。

## task1.3 未完全兑现的部分

`TASK_1_3_PORT_MERGE_PLAN.md` 的目标是“`tasks.py` 与 `hot_follow_api.py` 零互相引用”，这一点 **没有完成**。

当前代码仍存在双向耦合：

- `gateway/app/routers/hot_follow_api.py` 仍懒加载 `create_task`、`rerun_dub`、`run_task_pipeline`
- `gateway/app/routers/tasks.py` 仍懒加载 Hot Follow 专属函数，包括：
  - `_hot_follow_operational_defaults`
  - `_safe_collect_hot_follow_workbench_ui`
  - `_hf_task_status_shape`
  - `_maybe_run_hot_follow_lipsync_stub`
  - `_hf_compose_final_video`
  - `get_hot_follow_workbench_hub`
  - `_hf_subtitle_lane_state`
  - `_hf_dual_channel_state`
  - `_hf_target_lang_gate`

所以 task1.3 的真实状态应判断为：

- 已完成：共享 helper 下沉
- 部分完成：依赖缩减
- 未完成：运行时解环、回调注册、按 line 能力注入替代懒加载

## task2.0 实际落地内容

`task2.0` 基本已经真实落地。

已确认：

- `gateway/app/services/compose_service.py` 已存在，约 856 行，和 review 报告一致
- FFmpeg 调用已收口到 `_run_ffmpeg()`
- `_run_ffmpeg()` 已统一加 `timeout`
- `freeze_tail`、主 compose、probe、duration clamp 都通过统一网关执行
- `gateway/app/routers/hot_follow_api.py` 内已不再保留 600+ 行 compose god function，本体已被 wrapper 化

这说明 task2.0 已经真正解决了 baseline 中最危险的 Hot Follow 合成链路问题之一：**compose subprocess 无 timeout**。

## task2.0 仍然留下的缺口

task2.0 是心脏搭桥，不是整条合成产线完成 DDD 化。

仍然存在的问题：

- `CompositionService` 仍然是 Hot Follow 专属服务，不是 line-aware 的通用 compose runtime
- 路由层仍负责大量 compose 前后状态拼接、plan patch、hub 拼装
- compose 结果仍返回大 dict，而不是显式 deliverable contract
- 临时文件管理和后处理虽然收口，但没有形成 artifact checkpoint / retry-reconcile 模型
- task2.0 没有解决 `tasks.py` 中 `/api/tasks/{task_id}/compose` 仍反向调用 Hot Follow compose wrapper 的问题

## task2.3 实际落地内容

`task2.3` 也已经真实落地，不只是文档层。

已确认：

- 新增 `gateway/app/services/ready_gate/engine.py`
- 新增 `gateway/app/services/ready_gate/hot_follow_rules.py`
- `gateway/app/services/status_policy/hot_follow_state.py` 已改为三段式：
  - `_resolve_artifacts()`
  - `evaluate_ready_gate(...)`
  - `_apply_gate_side_effects()`

因此 task2.3 已把 baseline 中“Hot Follow ready gate 的 120 行硬编码 if/else”抽成了可扩的规则引擎。

## task2.3 的边界与遗留

task2.3 只解决了 **ready gate 规则表达**，没有解决 **状态治理全链统一**。

当前仍未完成：

- ready gate spec 没有挂入 `LineRegistry`
- status policy registry 仍按 `kind` 注册，不按 line contract 注册
- gate 规则仍是 Python 代码，不是受 line contract 引用的正式契约资产
- workbench、publish、compose 等链路没有统一通过 line contract 读取 gate / confirmation / deliverable policy

## 本轮验证结果

本轮按“只验证、不动代码”的方式补做了环境校验与测试尝试，结论如下：

- 结构检查再次确认：`tasks.py` 与 `hot_follow_api.py` 的双向懒加载依然存在，task1.3 的“零互相引用”没有达成。
- 解释器实测为 `Python 3.9.6`。
- 与 Hot Follow 当前主线直接相关的测试在收集阶段失败，不是业务断言失败，而是导入 `gateway/app/config.py` 时被 `str | None` 类型注解拦截。
- 这说明当前仓库的验证基线实际要求 Python 3.10+，但这一前提没有在本轮分析所覆盖的基线文档和工程计划中被明确标注。

因此，关于 task2.0 / task2.3 的“已落地”判断，当前仍成立，但其“可验证性”需要补一个前置条件：**先冻结并声明运行/测试解释器基线**。

## 与基线不一致的已知遗留实现

- `gateway/app/lines/hot_follow.py` 中 `sop_profile_ref="docs/sop/hot_follow_v1.md"`，但仓库里实际存在的是 `docs/sop/hot_follow/hot_follow_v_1_9_operations_manual.md`，合同引用路径已漂移。
- `skills_bundle_ref="docs/skills/"` 只是目录指针，没有 loader、bundle 解析或 line runtime 消费。
- `deliverable_kinds`、`auto_sink_enabled`、`confirmation_before_publish` 仍是“声明字段”，不是运行时约束。
- `LineRegistry.for_kind()` 已实现，但仓库内没有真实运行时消费点。


# 3. Current Gaps

## G1. line contract 仍未进入运行时主链

这是当前最关键缺口。

现状：

- `gateway/app/lines/base.py` 与 `gateway/app/lines/hot_follow.py` 已存在
- `gateway/app/main.py` 启动时会注册 `HOT_FOLLOW_LINE`
- 但仓库里没有任何业务主路径真正使用 `LineRegistry.for_kind()` 来决定路由、服务装配、ready gate、skills、worker、confirmation 或 deliverable policy

影响：

- line contract 仍是 ceremonial declaration
- 无法验证“Factory-first, not platform-first”是否真的进入运行时
- 第二条产线接入时仍会优先复制 router 分支，而不是复制 contract + runtime

## G2. task1.3 的“解环”没有完成，主路由仍互相知道对方

现状：

- `tasks.py` 仍通过懒加载调用 Hot Follow 专属实现
- `hot_follow_api.py` 仍懒加载调用总路由中的动作入口

影响：

- Hot Follow 仍不是独立可装配产线
- 总路由与场景路由之间仍有隐藏耦合
- 下一轮加 Localization / Action Replica 时，极易复用这套互引模式，重新制造 God router

## G3. workbench hub 仍是隐式大 dict 契约

`get_hot_follow_workbench_hub()` 仍然是当前最大 API 契约风险之一。

现状：

- `response_model=None`
- 响应体由大量 helper 在路由内组装
- `artifact_facts`、`current_attempt`、`operator_summary` 已开始成型，但没有显式 schema

影响：

- 前端仍依赖隐式字段约定
- line contract、scenario contract、deliverable contract 无法闭环
- 字段新增/重命名风险继续存在

## G4. 状态真相源比之前清晰，但仍不是“单入口 + 单模型”

虽然 `policy_upsert()` 已经是主 upsert 入口，但当前状态治理仍未完全收口。

现状：

- `policy_upsert()` 已成为统一入口
- ready gate 已声明化
- 但 `status_policy/registry.py` 仍只对 `apollo_avatar` 注册特化策略，Hot Follow 仍主要依赖默认策略 + 运行时聚合
- `task_view_helpers.py`、`hot_follow_api.py`、`hot_follow_state.py`、`steps_v1.py` 仍在不同层读写/推断 deliverables 和状态

影响：

- 交付物事实优先的原则已开始生效，但还没形成真正统一的 deliverable registry / contract
- “状态解释层”和“状态写入层”仍未完全分离

## G5. `/api` 与 `/v1` 的职责分层仍然模糊

现状：

- `main.py` 中 `/api/` 和 `/v1/` 都被视为 API path 并统一鉴权
- 实际业务里 `/api/...` 多用于动作与聚合接口，`\/v1/...` 多用于 deliverable 下载和老 action routes
- 前端和模板里仍大量存在 `/api` 优先、`/v1` fallback 或直接拼 `/v1/tasks/{id}/...` 的混用

影响：

- 统一 Gateway 边界仍未明确冻结
- 新接口继续沿两套语义增长的风险很高
- 运维、前端、API 合同会继续出现“看起来能用，但语义不稳”的状态

## G6. Asset / Artifact / Deliverable 仍未完成分层建模

现状：

- `artifact_storage.py` 是事实上的任务 artifact 存取层
- `deliverable` 在 task 详情、publish hub、state 里被多处使用
- `asset sink` 只存在于 line contract YAML 与 review 文档里，没有运行时
- promote / canonical asset / catalog 也没有真正 runtime

影响：

- `Asset ≠ Artifact` 原则仍未工程化
- 后续做 asset promote、catalog、ops handoff 时会继续把任务级 artifact 当成资产库

## G7. Skills / registry / ops 文档已铺路，但 runtime 边界尚未形成

现状：

- 有 `docs/skills/`、`docs/runbooks/ops/`、`docs/architecture/line_contracts/hot_follow_line.yaml`
- 有 `tools_registry.py`、`workbench_registry.py`
- 但没有 skills bundle loader、没有 line-aware registry wiring、没有 ops handoff 与 line runtime 的绑定

影响：

- 文档与代码方向一致，但还停在“目录和文档就绪”
- 如果现在直接冲平台化，很容易做成新的空心 registry 层

## G8. 非当前主阻塞但需要后置的事项

这些事项重要，但不应抢占当前优先级：

- OpenClaw Gateway 接入
- 通用 Skills Runtime 平台化
- 多产线统一 line job / confirmation 状态机全实现
- 资产库 promote / catalog 平台化
- 第二条以上产线的大规模复制
- 更复杂的 OCR、口型增强、静音内容智能路由等增强能力

这些都应建立在 Hot Follow 基座收口完成之后。

## G9. 工程验证基线未显式冻结

现状：

- 本机可用解释器为 Python 3.9.6
- 仓库当前代码已使用 `str | None` 这类 Python 3.10+ 语法
- 与 Hot Follow 主链直接相关的测试无法在收集阶段通过，失败点位于 `gateway/app/config.py`

影响：

- 当前“环境已准备完毕”的判断对业务代码和对测试运行不是同一件事
- 后续如果不显式冻结 Python 版本与测试入口，工程计划中的“验收标准”会继续失真
- 这类问题不属于业务架构缺陷，但属于交付执行层的真实阻塞


# 4. Engineering Priority Plan

## P0：必须先做，否则继续扩展会继续失控

### 任务包 P0-1：冻结 Hot Follow 运行时合同边界

目标：

- 把 Hot Follow 现有 line contract、API contract、deliverable contract、状态边界统一成一份可执行基线

为什么现在做：

- 当前文档和代码已有多份相近定义，但引用路径、字段范围、运行时消费点不一致
- 不先冻结，后续做 gateway 统一和状态收口时会继续反复返工

涉及目录：

- `docs/architecture/line_contracts/`
- `docs/contracts/`
- `docs/architecture/`
- `docs/runbooks/ops/`
- `gateway/app/lines/`

建议改造方式：

- 补一份 Hot Follow 运行时合同 ADR，明确：
  - line contract
  - workbench/publish API contract
  - deliverable kinds 与命名
  - `/api` 与 `/v1` 职责边界
  - artifact / deliverable / asset 的定义
- 修正 `sop_profile_ref` 和实际文档路径漂移
- 明确 `skills_bundle_ref`、`worker_profile`、`asset_sink` 当前属于“声明存在但未 runtime 化”

完成标志 / 验收标准：

- Hot Follow 合同引用路径不再漂移
- 关键名词和字段责任有单一文档
- 代码中的 line contract 字段与文档定义一致

是否需要先写文档/契约：

- 是，必须先做

### 任务包 P0-2：完成 tasks/hot_follow 运行时解环

目标：

- 彻底消除 `tasks.py` 与 `hot_follow_api.py` 的互相懒加载

为什么现在做：

- 这是当前阻塞 line-contract-driven runtime 的结构债务
- 如果不解环，后续所有 line runtime 注入、gateway 统一、第二条产线复制都会继续耦合在总路由上

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`
- `gateway/app/lines/`

建议改造方式：

- 把剩余 Hot Follow 专属逻辑提到 `services/hot_follow_*` 或 line runtime 模块
- 把总路由中仍依赖 Hot Follow 的 UI/status/compose/dub 特化逻辑抽成可注册能力
- 用 line callback registry 或 line runtime provider 替代懒加载导入

完成标志 / 验收标准：

- `rg` 搜索不到两文件互相 import
- `tasks.py` 不再知道 Hot Follow 内部 helper 名称
- `hot_follow_api.py` 不再回调总路由中的业务函数

是否需要先写文档/契约：

- 需要先补一页运行时装配说明，但可与编码并行

### 任务包 P0-3：定义并收口 Hot Follow Workbench/Publish 显式响应契约

目标：

- 把 `workbench_hub` 从隐式 dict 改成显式 schema

为什么现在做：

- 当前前后端最脆弱的接口就是这里
- 不先把契约显式化，状态收口和 line runtime 绑定都无法稳定推进

涉及目录：

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/domain/` 或新增 `gateway/app/contracts/`
- `docs/contracts/`
- `gateway/app/static/js/hot_follow_workbench.js`

建议改造方式：

- 新增 `WorkbenchHubResponse` 及子模型
- 明确 `artifact_facts`、`current_attempt`、`operator_summary`、`ready_gate`、`deliverables`
- 保持字段兼容，先“显式化不改语义”，再逐步内聚 helper

完成标志 / 验收标准：

- `get_hot_follow_workbench_hub()` 使用显式 response model
- 关键块有可测试 schema
- 前端不再依赖隐式字段漂移

是否需要先写文档/契约：

- 是，先冻结响应 contract

## P1：基座稳定后立刻推进

### 任务包 P1-1：把 Hot Follow ready gate / status policy 挂入 line runtime

目标：

- 让 line contract 真正驱动 ready gate、status policy、confirmation policy

为什么现在做：

- task2.3 已经把规则引擎准备好，但没有 runtime binding
- 这是从“文档对齐”走向“运行时对齐”的第一步

涉及目录：

- `gateway/app/lines/`
- `gateway/app/services/ready_gate/`
- `gateway/app/services/status_policy/`

建议改造方式：

- 在 `ProductionLine` 中补足 `ready_gate_ref` / `status_policy_ref` / `deliverable_profile_ref` 等正式字段
- `compute_hot_follow_state()` 改成通过 line runtime 获取 spec，而不是直接硬编码 `HOT_FOLLOW_GATE_SPEC`
- status policy registry 从按 `kind` 逐步过渡到按 line contract 装配

完成标志 / 验收标准：

- Hot Follow 的 ready gate/spec 来源可从 line contract 追溯
- status policy registry 不再只靠 kind 分派

是否需要先写文档/契约：

- 需要先冻结 line runtime 字段

### 任务包 P1-2：统一 `/api` 与 `/v1` 的语义

目标：

- 形成统一 Gateway 路由约定，避免继续双通道扩散

为什么现在做：

- 当前已有明确分裂历史，如果不现在收口，后续 contract 和前端都会继续依赖 fallback

涉及目录：

- `gateway/app/main.py`
- `gateway/app/routers/`
- `gateway/app/routes/`
- `gateway/app/static/js/`
- `docs/contracts/`

建议改造方式：

- 明确：
  - `/api` 只用于业务动作与聚合查询
  - `/v1` 只用于稳定资源下载/兼容 action routes，或反过来，但必须选一套清晰语义
- 清理前端 fallback 逻辑
- 为旧路径保留兼容层，但不再新增新语义

完成标志 / 验收标准：

- 新文档明确一套路由职责
- Hot Follow/Task 主链不再依赖 `/api` `/v1` 双猜测

是否需要先写文档/契约：

- 是，必须先冻结路由语义

### 任务包 P1-3：建立 Deliverable Contract 与写入边界

目标：

- 把 deliverables 从“多处拼装”收口为正式合同

为什么现在做：

- SSOT 的真正落点不是 ready gate，而是 deliverables 的统一结构和写口

涉及目录：

- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/status_policy/`
- `gateway/app/services/scenes_service.py`
- `gateway/app/services/steps_v1.py`
- `docs/contracts/`

建议改造方式：

- 定义 deliverable schema
- 明确哪些字段是事实写口，哪些只是视图派生
- 把 publish hub / workbench / state 读的 deliverables 结构统一

完成标志 / 验收标准：

- deliverables 结构有统一 schema
- 不同模块不再各自定义 final/pack/scenes/audio 的局部表示

是否需要先写文档/契约：

- 是

### 任务包 P1-4：冻结运行与测试验证基线

目标：

- 明确 ApolloVeo 当前分支的最小运行解释器、测试入口和验证前提

为什么现在做：

- 这次验证已经证明，若不冻结验证基线，任务“已完成/未完成”的判断无法稳定复现

涉及目录：

- `docs/`
- `gateway/requirements.txt`
- 仓库根运行说明文档

建议改造方式：

- 先补文档，不改业务代码
- 明确 Python 最低版本
- 明确推荐测试入口
- 明确哪些测试属于 Hot Follow 基线回归集

完成标志 / 验收标准：

- 新成员或 CI 能按同一解释器前提运行基线测试
- 架构任务包中的“验收标准”不再脱离实际运行环境

是否需要先写文档/契约：

- 是，且应尽快补齐

## P2：平台化前置能力

### 任务包 P2-1：建立 Hot Follow line runtime / gateway 装配层

目标：

- 让 Hot Follow 不再依附于 router 互引，而是通过 line runtime 装配

为什么现在做：

- 只有这一层存在，第二条产线复制才不会回到 God router

涉及目录：

- `gateway/app/lines/`
- `gateway/app/services/`
- `gateway/app/routers/`

建议改造方式：

- 增加 line runtime provider
- 将 compose、dub routing、ready gate、hub assembler 逐步挂到 runtime

完成标志 / 验收标准：

- 新增产线时主要扩展 line/runtime/service，而不是修改总路由

是否需要先写文档/契约：

- 需要

### 任务包 P2-2：厘清 Artifact / Deliverable / Asset Sink 分层

目标：

- 为后续 catalog、promote、ops handoff、资产复用建立清晰边界

为什么现在做：

- 文档已反复强调 `Asset ≠ Artifact`，但代码中还没有承接

涉及目录：

- `gateway/app/services/artifact_storage.py`
- `gateway/app/assets/`
- `docs/architecture/`
- `docs/runbooks/ops/`

建议改造方式：

- 定义任务运行 artifact
- 定义任务交付 deliverable
- 定义 promote 后 canonical asset
- 先出分层文档和 metadata schema，再决定是否编码

完成标志 / 验收标准：

- 三层对象的命名、字段、生命周期清晰
- `asset_sink` 从文档术语变成可实现边界

是否需要先写文档/契约：

- 必须先写

### 任务包 P2-3：最小 Skills Bundle Loader

目标：

- 让 `skills_bundle_ref` 从目录路径变成最小可消费运行时

为什么现在做：

- baseline 明确要求 skills 是行为策略层，但当前完全未 runtime 化

涉及目录：

- `docs/skills/`
- `gateway/app/lines/`
- `gateway/app/services/`

建议改造方式：

- 第一阶段只做最小 loader，不做通用 agent 平台
- 先支持静态配置读取和简单 routing/compliance hooks

完成标志 / 验收标准：

- line contract 可以加载自己的 skills bundle 元数据
- 不再把所有策略硬编码在 router/tasks 大函数中

是否需要先写文档/契约：

- 需要

## P3：可后置项

### 任务包 P3-1：第二条标准产线复制

目标：

- 用 Localization 或 Action Replica 验证 Hot Follow 基座可复制

为什么后置：

- 当前基座还没有真正收口，直接复制只会复制结构债务

涉及目录：

- `gateway/app/lines/`
- `gateway/app/routers/`
- `gateway/app/services/`

建议改造方式：

- 只在 P0/P1/P2 主干完成后启动

完成标志 / 验收标准：

- 第二条产线主要通过 contract/runtime/service 复制完成

是否需要先写文档/契约：

- 需要

### 任务包 P3-2：OpenClaw gateway stub / line job / confirmation 状态机

目标：

- 对接外部执行网格和确认节点

为什么后置：

- 当前业务真相源和 line runtime 还未收口，过早接入会反向塑形

涉及目录：

- `docs/architecture/`
- `_drafts/C.4 RFC-0003_OpenClaw_Control_Mesh_Integration.md`
- 新增 gateway 模块

建议改造方式：

- 先补 line job 状态机和 confirmation contract，再做 stub

完成标志 / 验收标准：

- OpenClaw 只作为控制与执行网关，不成为业务真相源

是否需要先写文档/契约：

- 必须先写


# 5. Recommended Execution Order

1. 先冻结 Hot Follow 运行时合同基线。
   明确 line contract、API contract、deliverable contract、`/api`/`/v1` 语义，以及 artifact/deliverable/asset 的边界。先把“说法统一”解决掉，再推进结构改造。

2. 再完成 `tasks.py` 与 `hot_follow_api.py` 解环。
   这是当前最直接的结构阻塞。不先拆掉互引，line contract 不可能真正装配到运行时。

3. 再把 Workbench/Publish 响应模型显式化。
   先固定 workbench hub 契约，避免后续状态收口和 gateway 收口时把前端一起拖进不稳定区。

4. 再把 ready gate / status policy / confirmation policy 挂入 line runtime。
   让 `LineRegistry` 从“注册表”变成“运行时绑定源”。

5. 再统一 deliverables 写入边界和读取模型。
   这一步要把 SSOT 真正落实到 deliverable contract 上，而不是继续靠散落 helper 和 UI 解释层维持。

6. 再冻结运行与测试验证基线。
   先明确 Python 版本和回归入口，避免后续每个任务包的“验收”都停在口头判断。

7. 再收口 `/api` 与 `/v1` 的 Gateway 语义。
   等 workbench 和 deliverables 契约稳定后，统一入口边界的成本更低，也更不容易回滚。

8. 再做最小 Skills loader、Artifact/Deliverable/Asset 分层。
   这是第二条产线复制前的必要平台前置能力，但不应抢在 P0 前面。

9. 最后再复制第二条标准产线，再考虑 OpenClaw / line job / confirmation 状态机外扩。


# 6. Concrete Next Tasks

1. 编写 `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`。
   冻结 Hot Follow 的 line contract、workbench contract、deliverable contract、`/api` 与 `/v1` 语义，以及 artifact/deliverable/asset 分层定义。

2. 修正 `gateway/app/lines/hot_follow.py` 与 `docs/architecture/line_contracts/hot_follow_line.yaml` 的漂移。
   包括 `sop_profile_ref` 实际路径、deliverable kinds 命名、confirmation/asset sink 字段一致性。

3. 新增 Hot Follow line runtime 装配层。
   先只承接剩余懒加载能力，把 `tasks.py` 和 `hot_follow_api.py` 的互引拆掉。

4. 为 `get_hot_follow_workbench_hub()` 定义显式 response model。
   至少覆盖 `pipeline`、`subtitles`、`audio`、`deliverables`、`ready_gate`、`artifact_facts`、`current_attempt`、`operator_summary`。

5. 设计并落地 `Deliverable Contract v1`。
   统一 final/audio/subtitle/pack/scenes 的事实字段、状态字段、下载字段和 UI 消费字段。

6. 编写运行与测试基线说明。
   明确当前分支需要 Python 3.10+ 才能运行 Hot Follow 相关测试，并列出最小回归命令集。

7. 把 ready gate spec 与 status policy 绑定到 line contract。
   让 Hot Follow 先成为第一个真正由 line contract 驱动的运行时样板。

8. 冻结 `/api` 与 `/v1` 的 Gateway 规则并清理前端 fallback。
   先写契约，再清理 `hot_follow_workbench.js`、模板和相关 router 中的双通道猜测。
