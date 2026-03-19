# Hot Follow Runtime Contract

## 1. 目的

本文件冻结 `hot_follow` 当前 runtime contract，供 `PR-2 / PR-3 / PR-4` 直接引用。

本文件只描述当前代码已经存在的运行时边界，不引入新的平台层或第二条产线抽象。

## 2. 适用范围

- task kind: `hot_follow`
- line id: `hot_follow_line`
- 当前主入口：
  - `gateway/app/routers/tasks.py`
  - `gateway/app/routers/hot_follow_api.py`
- 当前状态聚合：
  - `gateway/app/services/status_policy/hot_follow_state.py`
- 当前 line contract 文档：
  - `docs/architecture/line_contracts/hot_follow_line.yaml`

## 3. 当前运行时边界

### 3.1 `tasks.py`

当前保留职责：

- 通用 `/api/tasks/*` HTTP 入口
- 通用任务列表、任务详情、基础步骤触发
- 对 Hot Follow 兼容入口的转发

当前不应继续扩张的职责：

- 不再新增 Hot Follow 专属 orchestration
- 不再新增对 `hot_follow_api.py` 内部 helper 的直接依赖
- 不把 workbench hub、compose gate、subtitle lane 逻辑继续塞回总路由

### 3.2 `hot_follow_api.py`

当前保留职责：

- Hot Follow 专属 HTTP 入口与 workbench / publish hub 聚合
- 对既有调用方保留兼容 wrapper
- 调用现有 service 层能力而不是重新内联主逻辑

当前已知兼容锚点：

- `_hf_compose_final_video()`
- `get_hot_follow_workbench_hub()`
- `_hot_follow_operational_defaults()`
- `_safe_collect_hot_follow_workbench_ui()`
- `_hf_task_status_shape()`
- `_hf_subtitle_lane_state()`
- `_hf_dual_channel_state()`
- `_hf_target_lang_gate()`

这些函数在本阶段仍可存在，但被视为兼容层，不是新的 runtime contract 扩展点。

### 3.3 service / status policy / ready gate

当前职责：

- `gateway/app/services/compose_service.py`
  - 承接 compose 主体执行
  - 统一 FFmpeg 子进程 timeout
  - 返回 compose 更新结果 dict
- `gateway/app/services/status_policy/hot_follow_state.py`
  - 负责 Hot Follow 状态聚合
  - 通过 `compute_hot_follow_state()` 输出 `ready_gate` 与兼容状态字段
- `gateway/app/services/ready_gate/hot_follow_rules.py`
  - 提供 `HOT_FOLLOW_GATE_SPEC`
- `gateway/app/services/status_policy/registry.py`
  - 当前仍是按 `kind` 的最小 registry，不是 line-aware runtime

### 3.4 line contract

当前职责：

- `docs/architecture/line_contracts/hot_follow_line.yaml`
  - 作为 Hot Follow line contract 文档基线
- `gateway/app/lines/hot_follow.py`
  - 作为当前运行时可见的最小 line 注册

当前限制：

- `LineRegistry.for_kind()` 已存在，但尚未成为主链装配入口
- line contract 当前是声明存在，不是完整 runtime wiring

## 4. 输入 / 输出边界

### 4.1 Router 输入

- HTTP request
- path/query/form/body 参数
- repo 中的 task 记录

### 4.2 Service 输入

- `CompositionService.compose(task_id, task, subtitle_resolver, subtitle_only_check)`
- `compute_hot_follow_state(task, base_state=None)`

service 当前不直接承担：

- HTTP status code 适配层之外的路由拼装
- 前端页面字段命名兼容
- 新的 line runtime 注入框架

### 4.3 Runtime 输出

- compose 路径当前输出：更新 task 所需的 dict
- state 路径当前输出：带 `ready_gate` 的状态 dict
- workbench / publish hub 当前输出：router 聚合后的大 dict

## 5. 当前做 / 当前不做

### 当前做

- 冻结 Hot Follow runtime 角色分工
- 明确 router / service / line contract 的边界
- 明确现有兼容 wrapper 属于过渡层
- 为后续 PR 提供不再回退到 router 互相懒加载的文档基线

### 当前不做

- 不修改 `tasks.py` 与 `hot_follow_api.py` 业务逻辑
- 不把 workbench hub 在本 PR 中重构成显式 schema
- 不在本 PR 中建立新的 provider/runtime 平台抽象
- 不扩第二条产线
- 不启动 skills runtime 实现

## 6. 后续 PR 直接使用方式

- `PR-2` 以本文件作为 router 解环边界
- `PR-3` 以本文件与 compose contract 一起收口 compose 主链
- `PR-4` 以本文件与 gate binding contract 一起建立 line-aware 最小装配入口
