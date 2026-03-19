# 1. Frozen Execution Premise

当前执行前提已冻结，不再重开讨论：

- 当前分支已确认是 `VeoSop04`
- 当前阶段不是平台扩张期，而是 `v1.9` 基座收口 + `VeoSop04` 扫雷阶段
- 当前执行顺序固定为：
  1. `TASK-1.3` 收口
  2. `TASK-2.0` 收口
  3. `TASK-2.3` 收口
  4. Verification Baseline Freeze
  5. `TASK-2.2 Skills MVP`
  6. 之后才允许讨论第二条标准产线 / 更大平台能力

本计划只处理以下执行主题：

- `TASK-1.3 Final Closure`
- `TASK-2.0 Runtime Closure`
- `TASK-2.3 Contract Binding`
- `Verification Baseline Freeze`
- `Skills MVP Entry Criteria`

本计划不处理以下主题：

- 第二条标准产线
- OpenClaw / 平台层扩张
- 新 provider 扩张
- 泛泛 review 或方向重排

当前代码事实，作为本计划的前提证据：

- `gateway/app/routers/tasks.py` 与 `gateway/app/routers/hot_follow_api.py` 仍有双向懒加载
- `gateway/app/services/compose_service.py` 已落地，但 `_hf_compose_final_video()` 仍保留 router wrapper 锚点
- `gateway/app/services/ready_gate/engine.py` 与 `gateway/app/services/ready_gate/hot_follow_rules.py` 已落地，但 `compute_hot_follow_state()` 仍直接依赖 `HOT_FOLLOW_GATE_SPEC`
- `LineRegistry.for_kind()` 已实现，但当前 runtime 主链无真实消费点
- `docs/skills/` 当前仅有目录骨架和文档，没有 loader / runtime hook
- 本机 `python3` 实测为 `Python 3.9.6`，依赖 router/config 的 Hot Follow 集成测试仍受 `str | None` 注解阻断


# 2. P0 Closure Tasks

## P0-1 TASK-1.3 Final Closure

目标：

- 完成 Router Split 的最后一公里，彻底解除 `tasks.py` 与 `hot_follow_api.py` 的运行时级耦合

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

当前遗留点：

- `hot_follow_api.py` 仍懒加载：
  - `create_task`
  - `rerun_dub`
  - `run_task_pipeline`
- `tasks.py` 仍懒加载：
  - `_hot_follow_operational_defaults`
  - `_safe_collect_hot_follow_workbench_ui`
  - `_hf_task_status_shape`
  - `_maybe_run_hot_follow_lipsync_stub`
  - `_hf_compose_final_video`
  - `get_hot_follow_workbench_hub`
  - `_hf_subtitle_lane_state`
  - `_hf_dual_channel_state`
  - `_hf_target_lang_gate`

收口要求：

- router 不再知道对方内部 helper
- Hot Follow 专属 orchestration 不再留在总路由
- 通过 service/runtime provider 完成能力装配

依赖关系：

- 无前置依赖，当前必须先开工

是否需要文档先行：

- 是，需要先补一页 runtime 装配说明

## P0-2 TASK-2.0 Runtime Closure

目标：

- 将 compose 从“安全性已收口”推进到“runtime 依赖收口”

涉及目录：

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`

当前遗留点：

- `_hf_compose_final_video()` 仍是 router 兼容锚点
- `tasks.py` 的 compose 路径仍反向依赖 Hot Follow router
- compose 前后状态写入、hub 返回、异常映射仍主要留在 router
- compose 对外仍返回 dict，没有独立 result contract

收口要求：

- `tasks.py` 不再直接接触 Hot Follow compose wrapper
- compose 具备 service contract / result contract / direct test entry
- router 只保留最薄的 HTTP 适配层

依赖关系：

- 强依赖 `TASK-1.3` 解环完成

是否需要文档先行：

- 需要，至少冻结 compose service contract / result contract

## P0-3 TASK-2.3 Contract Binding

目标：

- 将 ready gate 从“局部规则引擎”推进到“line contract 可绑定的运行时能力”

涉及目录：

- `gateway/app/services/ready_gate/`
- `gateway/app/services/status_policy/`
- `gateway/app/lines/`
- `docs/architecture/line_contracts/`

当前遗留点：

- `HOT_FOLLOW_GATE_SPEC` 仍是代码常量
- `compute_hot_follow_state()` 仍直接硬编码规则源
- `status_policy/registry.py` 仍不是 line-aware 装配入口
- line contract 未接管 gate / status policy 绑定

收口要求：

- gate spec 能从 line contract 追溯
- `compute_hot_follow_state()` 不再直接绑定 Hot Follow 常量
- line-aware status policy 最小装配入口建立

依赖关系：

- 强依赖 `TASK-1.3` 与 `TASK-2.0` 基本收口

是否需要文档先行：

- 是，必须先补 line contract 与 gate binding 说明

## P0-4 Verification Baseline Freeze

目标：

- 把运行/测试解释器基线、最小回归集、CI/本地执行前提显式冻结

涉及目录：

- `docs/`
- `gateway/requirements.txt`
- 如存在 CI 配置则一并补齐

当前遗留点：

- 纯 ready-gate 单测可跑
- 依赖 router/config 的集成测试在 Python 3.9.6 下无法收集
- 仓库已使用 Python 3.10+ 语法，但当前验证基线未显式声明

收口要求：

- 明确 Python 最低版本
- 明确 Hot Follow 最小回归命令
- 明确哪些测试仅在更高 Python 版本下可运行

依赖关系：

- 可与 `TASK-1.3` 并行推进，但必须在进入 Skills MVP 前完成

是否需要文档先行：

- 是，本任务本身就是文档先行


# 3. PR Split for TASK-1.3

## PR-1A Runtime Wiring ADR

目标：

- 冻结 router 解环后的运行时装配方式，避免继续通过懒加载补洞

涉及目录：

- `docs/`
- `docs/architecture/`

风险：

- 如果不先冻结，后续编码容易再次做成“函数搬迁但依赖图不闭合”

验收标准：

- 文档明确：
  - `tasks.py` 保留哪些 HTTP/通用入口职责
  - Hot Follow 专属 orchestration 下沉到哪些 service/runtime 模块
  - router 间如何不再互相 import

是否需要文档先行：

- 是

## PR-1B Extract Remaining Router Orchestration

目标：

- 把仍留在 router 的 Hot Follow 专属 orchestration 提取到 services/runtime 层

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

重点处理对象：

- `_hf_task_status_shape`
- `_hot_follow_operational_defaults`
- `_safe_collect_hot_follow_workbench_ui`
- `_hf_subtitle_lane_state`
- `_hf_dual_channel_state`
- `_hf_target_lang_gate`

风险：

- 触及 workbench、task detail、dub 路由
- 若抽取粒度不清，会把更多条件分支重新塞回总路由

验收标准：

- 上述能力进入 service/runtime 模块
- `tasks.py` 不再 import Hot Follow 内部 helper

是否需要文档先行：

- 基于 PR-1A

## PR-1C Remove Cross-Router Lazy Imports

目标：

- 删除 `tasks.py` 与 `hot_follow_api.py` 的剩余双向懒加载

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`

风险：

- 直接影响创建任务、重跑配音、主链执行、compose、workbench

验收标准：

- `rg` 检索不到两文件互相 import
- `tasks.py` 不再调用 `_hf_compose_final_video`、`get_hot_follow_workbench_hub`、`_hf_*`
- `hot_follow_api.py` 不再调用 `create_task`、`rerun_dub`、`run_task_pipeline`

是否需要文档先行：

- 不新增文档，依附 PR-1A


# 4. PR Split for TASK-2.0 and TASK-2.3

## PR-2A Compose Contract Freeze

目标：

- 冻结 compose service 的输入/输出契约，避免继续以 router wrapper 作为事实接口

涉及目录：

- `docs/contracts/`
- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`

风险：

- 若 contract 定义不清，后续 runtime closure 和测试入口都会继续漂移

验收标准：

- 明确 ComposeInput / ComposeResult 或等价 contract
- 明确 router 仅做 HTTP 映射，不承载 compose 领域语义

是否需要文档先行：

- 是

## PR-2B Compose Runtime Closure

目标：

- 去掉 router 级兼容锚点对主链的影响

涉及目录：

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`

重点处理对象：

- `_hf_compose_final_video()`
- `tasks.py` `/api/tasks/{task_id}/compose`
- compose 状态写入与异常映射

风险：

- 影响 compose 状态、hub 返回、异常路径

验收标准：

- `tasks.py` compose 不再反向依赖 Hot Follow router
- `_hf_compose_final_video()` 不再作为外部兼容锚点
- compose service 有直接测试入口

是否需要文档先行：

- 基于 PR-2A

## PR-2C Ready Gate Binding ADR

目标：

- 冻结 line contract 与 gate/status policy 的绑定方式

涉及目录：

- `docs/architecture/line_contracts/`
- `docs/contracts/`
- `gateway/app/lines/`

风险：

- 若直接编码而无绑定说明，极易变成新的局部常量拼装

验收标准：

- 文档明确：
  - gate spec 绑定入口
  - status policy 绑定入口
  - Hot Follow 作为第一条 line 的接法

是否需要文档先行：

- 是

## PR-2D Ready Gate Contract Binding

目标：

- 让 line contract 真正接管 ready gate / status policy 选择

涉及目录：

- `gateway/app/services/ready_gate/`
- `gateway/app/services/status_policy/`
- `gateway/app/lines/`
- `docs/architecture/line_contracts/`

重点处理对象：

- `HOT_FOLLOW_GATE_SPEC`
- `compute_hot_follow_state()`
- `status_policy/registry.py`
- `gateway/app/lines/base.py`
- `gateway/app/lines/hot_follow.py`

风险：

- 若设计过度，会提前滑向平台大重构

验收标准：

- line contract 可追溯到 gate spec
- `compute_hot_follow_state()` 不再硬编码 Hot Follow 规则源
- status policy 建立 line-aware 最小装配入口

是否需要文档先行：

- 基于 PR-2C

## PR-2E Workbench Contract Typing

目标：

- 为 `get_hot_follow_workbench_hub()` 建立显式响应模型，避免 gate 绑定继续依赖隐式大 dict

涉及目录：

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/domain/` 或新建 `gateway/app/contracts/`
- `docs/contracts/`
- `gateway/app/static/js/hot_follow_workbench.js`

风险：

- 前端兼容性
- workbench 字段已被多个层级隐式消费

验收标准：

- `response_model=None` 被替换
- `artifact_facts`、`current_attempt`、`operator_summary`、`ready_gate` 有显式 schema
- 前端字段兼容不回退

是否需要文档先行：

- 是，先冻结 API contract


# 5. Verification Baseline Plan

## 目标

- 冻结 ApolloVeo 当前分支的运行和测试验证基线，使后续 P0 收口任务有可复现验收标准

## 当前事实

- 实测解释器：`Python 3.9.6`
- 可跑测试：
  - `python3 -m pytest gateway/app/services/status_policy/tests/test_ready_gate.py -q`
- 当前受阻测试类型：
  - 依赖 `gateway/app/config.py`
  - 依赖 router 导入
  - 依赖 `get_task_repository` / `deps.py`
- 受阻原因：
  - 仓库已使用 `str | None` 等 Python 3.10+ 语法
  - 当前 `python3` 为 3.9.6，测试在收集阶段失败

## 计划拆分

### VB-1 文档冻结

目标：

- 明确 Python 最低版本和最小回归命令

涉及目录：

- `docs/`

内容要求：

- 声明当前仓库测试解释器最低版本
- 列出 Hot Follow 最小回归命令：
  - 纯 ready-gate 规则测试
  - compose service 直接测试入口
  - workbench / router 集成测试
- 列出当前在 Python 3.9 下不可运行的测试范围

验收标准：

- 新成员按文档可判断哪些测试应在本机跑、哪些必须在更高 Python 版本跑

### VB-2 依赖与执行说明补齐

目标：

- 明确本地和 CI 使用的解释器、依赖安装方式、回归入口

涉及目录：

- `gateway/requirements.txt`
- `docs/`
- 如存在 CI 配置则补齐相应说明

验收标准：

- 文档和依赖说明不再默认“系统 python3 即可”

### VB-3 基线回归集定义

目标：

- 给 P0/P1 任务提供统一的最小验收集

建议最小回归集：

- Ready Gate 纯规则测试
- Hot Follow workbench hub 测试
- Hot Follow current dub state 测试
- Hot Follow phase_a ops 测试
- Compose service direct tests

验收标准：

- 每个 PR 都能声明自己至少跑了哪些基线项

## 文档先行 / 可直接编码

- 文档先行：
  - Python 版本冻结
  - 回归命令集
  - 本地/CI 执行说明
- 可直接编码：
  - 如有 CI 配置，可在文档冻结后补执行器版本声明


# 6. Skills MVP Entry Criteria

## 进入条件

只有以下条件满足后，才允许启动 `TASK-2.2 Skills MVP`：

1. `TASK-1.3` 解环完成
2. `TASK-2.0` compose runtime closure 完成
3. `TASK-2.3` gate contract binding 完成
4. Verification Baseline Freeze 完成

当前不满足上述条件，因此 Skills MVP 现在不能直接进入实现阶段。

## 启动时的最小范围

Skills MVP 只允许做最小 scope：

- bundle loader
- line-aware skills metadata resolve
- 三类 hook：
  - routing
  - compliance
  - media-compose policy

## 必须后置的内容

以下内容必须后置，不得混入 Skills MVP：

- 通用 agent 平台
- 多 line runtime 扩张
- OpenClaw 接入
- 第二条标准产线复制
- 复杂 quality/recovery/autonomous agent 机制

## 文档先行要求

在 Skills MVP 启动前，必须先补：

- Skills MVP scope 文档
- bundle metadata 格式
- hook 输入输出边界
- 与 line contract 的绑定方式

涉及目录：

- `docs/skills/`
- `docs/contracts/`
- `gateway/app/lines/`
- `gateway/app/services/`

## 启动验收标准

- `skills_bundle_ref` 可被解析
- Hot Follow 能挂一个最小 bundle
- 不新增 router 间耦合
- 策略逻辑不回流到 `tasks.py` 或 `hot_follow_api.py`


# 7. Immediate Next 5 Executable Tasks

## 1. 编写 Router 解环运行时装配说明

目标：

- 冻结 `TASK-1.3` 的最终装配边界

涉及目录：

- `docs/`
- `docs/architecture/`

依赖：

- 无

验收标准：

- 明确 `tasks.py`、`hot_follow_api.py`、services/runtime 的职责切分

文档先行 / 可直接编码：

- 文档先行

## 2. 提取剩余 Hot Follow router orchestration 到 services/runtime

目标：

- 把仍留在 router 的 Hot Follow 专属 helper/orchestration 下沉

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

依赖：

- 依赖任务 1

验收标准：

- `tasks.py` 不再 import Hot Follow 内部 helper

文档先行 / 可直接编码：

- 可直接编码，基于任务 1

## 3. 删除两 router 的剩余双向懒加载

目标：

- 完成 `TASK-1.3` 最后一公里

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`

依赖：

- 依赖任务 2

验收标准：

- `rg` 检索不到两文件互相 import

文档先行 / 可直接编码：

- 可直接编码

## 4. 冻结 compose contract 与 gate binding contract

目标：

- 为 `TASK-2.0` 和 `TASK-2.3` 的收口编码建立契约前提

涉及目录：

- `docs/contracts/`
- `docs/architecture/line_contracts/`

依赖：

- 建议在任务 1 完成后开始

验收标准：

- 明确 ComposeResult / gate binding / line-aware status policy 入口

文档先行 / 可直接编码：

- 文档先行

## 5. 编写 Verification Baseline Freeze 文档并定义最小回归集

目标：

- 冻结 Python 版本、测试解释器基线、Hot Follow 最小回归命令

涉及目录：

- `docs/`
- `gateway/requirements.txt`

依赖：

- 无，可与任务 2/3 并行

验收标准：

- 文档明确 Python 最低版本
- 文档列出最小回归命令
- 明确哪些测试需要 Python 3.10+

文档先行 / 可直接编码：

- 文档先行
