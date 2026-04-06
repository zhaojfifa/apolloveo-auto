# Hot Follow Gate Binding Contract

## 1. 目的

本文件冻结 `TASK-2.3` / `PR-4` 之后的 gate binding 基线，明确 Hot Follow 的 ready gate spec、line contract、status policy 三者当前如何对齐，以及哪些部分仍未进入更大范围的 runtime 主链。

## 2. 绑定对象

- line contract 文档：`docs/architecture/line_contracts/hot_follow_line.yaml`
- line 注册：`gateway/app/lines/hot_follow.py`
- gate spec 来源：`docs/contracts/hot_follow_ready_gate.yaml`
- runtime loader：`gateway/app/services/ready_gate/hot_follow_rules.py::load_hot_follow_gate_spec`
- gate spec 绑定入口：`gateway/app/services/ready_gate/registry.py`
- gate 解释执行：`gateway/app/services/ready_gate/engine.py::evaluate_ready_gate`
- status 聚合入口：`gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state`
- status 装配入口：`gateway/app/services/status_policy/registry.py::get_status_runtime_binding`

## 3. ready gate spec 的来源

当前来源冻结为：

- Hot Follow 的 ready gate spec 来自 `docs/contracts/hot_follow_ready_gate.yaml`
- `gateway/app/services/ready_gate/hot_follow_rules.py` 负责把 YAML 规则装载成运行时 `HOT_FOLLOW_GATE_SPEC`
- 运行时通过 `ready_gate/registry.py` 把 line contract 上的 `ready_gate_ref` 绑定到该对象

这表示当前状态是：

- gate engine 已落地
- gate spec 已声明式化
- gate spec 已切到 YAML-backed runtime loader
- gate spec 已有最小 line-aware 绑定入口
- 但还不是通用多产线 profile loader

## 4. line contract 如何绑定 gate spec

本阶段冻结的绑定关系是“line contract 明示 + runtime 最小绑定”：

1. `hot_follow_line.yaml` 负责声明这是 `hot_follow_line`
2. `gateway/app/lines/hot_follow.py` 负责把 `task_kind=hot_follow` 注册到 `LineRegistry`
3. `hot_follow_line.yaml` 与 `gateway/app/lines/hot_follow.py` 共同声明 `ready_gate_ref=docs/contracts/hot_follow_ready_gate.yaml`
4. `gateway/app/services/ready_gate/registry.py` 负责把 `LineRegistry.for_kind(task.kind)` 解析到 gate spec 对象
5. `gateway/app/services/status_policy/registry.py::get_status_runtime_binding()` 负责给 status/runtime 提供最小 line-aware 绑定结果
6. `compute_hot_follow_state()` 负责消费 runtime 绑定出来的 gate spec

当前连接链路是：

- `task.kind -> LineRegistry.for_kind() -> hot_follow_line`
- `hot_follow_line.ready_gate_ref -> docs/contracts/hot_follow_ready_gate.yaml`
- `load_hot_follow_gate_spec(...) -> HOT_FOLLOW_GATE_SPEC`
- `get_status_runtime_binding(task) -> ready_gate_spec`
- `compute_hot_follow_state() -> evaluate_ready_gate(ready_gate_spec, ...)`

本阶段不宣称已存在：

- 新的平台配置中心
- 通用多产线 gate/profile 动态装载
- line-aware publish / compose / workbench 全面统一装配

## 5. status policy 的最小 line-aware 接口

当前最小接口冻结如下：

- 运行时已存在：`LineRegistry.for_kind(task_kind)`
- 运行时已存在：`get_status_runtime_binding(task)`
- `get_status_policy(task)` 继续作为兼容包装层
- `get_status_runtime_binding(task)` 当前返回：
  - `line`
  - `policy`
  - `kind`
  - `ready_gate_spec`

因此，本阶段已经满足的最小 line-aware 目标是：

- 能从 `task.kind=hot_follow` 追溯到 `hot_follow_line`
- 能从 `hot_follow_line.ready_gate_ref` 追溯到 YAML-backed `HOT_FOLLOW_GATE_SPEC`
- 能让 `compute_hot_follow_state()` 真实消费这条绑定链

## 6. 当前仍未完成的部分

- `status_policy/registry.py` 里的 policy 选择仍主要按 `kind`，不是完整的 `line_id` 策略表
- workbench / publish / compose 还没有统一走 line-aware gate binding
- `ready_gate/registry.py` 当前只显式挂了 Hot Follow，一个 line 一个绑定
- `status_policy_ref` 目前主要用于可追溯性，还不是通用策略加载器

## 7. 当前做 / 当前不做

### 当前做

- 落地 `hot_follow_line -> ready_gate_ref -> gate spec -> compute_hot_follow_state()` 的最小 runtime 绑定
- 提供 `get_status_runtime_binding(task)` 作为 status policy 最小 line-aware 装配入口
- 保持 router / bridge 职责不扩张

### 当前不做

- 不发明新的多产线平台配置中心
- 不做 Skills runtime
- 不扩第二条产线
- 不宣称 line contract 已全面接管所有 runtime 主链
