# Hot Follow Gate Binding Contract

## 1. 目的

本文件冻结 `TASK-2.3` 之后的 gate binding 基线，明确 Hot Follow 的 ready gate spec、line contract、status policy 三者当前如何对齐，以及哪些部分仍未进入 runtime 主链。

## 2. 绑定对象

- line contract 文档：`docs/architecture/line_contracts/hot_follow_line.yaml`
- line 注册：`gateway/app/lines/hot_follow.py`
- gate spec 来源：`gateway/app/services/ready_gate/hot_follow_rules.py::HOT_FOLLOW_GATE_SPEC`
- gate 解释执行：`gateway/app/services/ready_gate/engine.py::evaluate_ready_gate`
- status 聚合入口：`gateway/app/services/status_policy/hot_follow_state.py::compute_hot_follow_state`
- 当前 registry：`gateway/app/services/status_policy/registry.py`

## 3. ready gate spec 的来源

当前来源冻结为：

- Hot Follow 的 ready gate spec 来自 Python 代码常量 `HOT_FOLLOW_GATE_SPEC`
- 该常量定义在 `gateway/app/services/ready_gate/hot_follow_rules.py`
- `compute_hot_follow_state()` 当前直接 import 并调用它

这表示当前状态是：

- gate engine 已落地
- gate spec 已声明式化
- 但 gate spec 还不是从 line contract 运行时解析出来的

## 4. line contract 如何绑定 gate spec

本阶段冻结的绑定关系是“文档绑定优先，运行时绑定后置”：

1. `hot_follow_line.yaml` 负责声明这是 `hot_follow_line`
2. `gateway/app/lines/hot_follow.py` 负责把 `task_kind=hot_follow` 注册到 `LineRegistry`
3. `compute_hot_follow_state()` 负责消费 Hot Follow 专属 gate spec
4. 本文件负责把 line contract 与 gate spec 的对应关系冻结成显式基线

也就是说，当前绑定方式不是：

- 运行时先 `LineRegistry.for_kind()` 再动态取 gate spec

而是：

- 文档上确认 `hot_follow_line -> HOT_FOLLOW_GATE_SPEC`
- 代码上仍由 `compute_hot_follow_state()` 直接绑定 Hot Follow spec

这正是本阶段要冻结而不是假装已完成的边界。

## 5. status policy 的最小 line-aware 接口

当前最小接口冻结如下：

- 运行时已存在：`LineRegistry.for_kind(task_kind)`
- 运行时已存在：`get_status_policy(task)`
- 运行时未完成：按 `line_id` 或 line contract 做 status policy 装配

因此，`PR-4` 之前允许的最小 line-aware 目标只有：

- 能从 `task.kind=hot_follow` 追溯到 `hot_follow_line`
- 能在 status policy / ready gate 文档中明确这条映射

本阶段不宣称已存在以下能力：

- line-aware `status_policy/registry.py`
- line contract 驱动的 gate spec 动态分发
- 多产线 gate profile 选择器

## 6. 当前仍未完成的部分

- `compute_hot_follow_state()` 仍直接依赖 `HOT_FOLLOW_GATE_SPEC`
- `status_policy/registry.py` 仍按 `kind` 注册，不按 `line_id` 注册
- `LineRegistry.for_kind()` 还没有被 Hot Follow 主链真实消费
- workbench / publish / compose 还没有统一走 line-aware gate binding
- `gateway/app/lines/hot_follow.py` 与 `hot_follow_line.yaml` 的引用路径仍有历史漂移，需后续代码收口时一并对齐

## 7. 当前做 / 当前不做

### 当前做

- 冻结 `hot_follow_line -> HOT_FOLLOW_GATE_SPEC -> compute_hot_follow_state()` 的文档对应关系
- 冻结最小 line-aware 目标，避免后续把 registry 说成已经 runtime 化
- 为 `PR-4` 建立可以直接接手的 gate binding 基线

### 当前不做

- 不改 `status_policy/registry.py`
- 不改 `compute_hot_follow_state()` 的直接 import
- 不在本 PR 中发明新的 gate profile loader
- 不宣称 line contract 已正式接管 runtime
