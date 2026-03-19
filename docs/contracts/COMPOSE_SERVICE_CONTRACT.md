# Compose Service Contract

## 1. 目的

本文件冻结 Hot Follow 当前 compose service contract，避免 `TASK-2.0` 后续继续回退成 router orchestration。

## 2. 当前主体

- service 主体：`gateway/app/services/compose_service.py`
- 当前兼容 wrapper：`gateway/app/routers/hot_follow_api.py::_hf_compose_final_video()`
- 当前兼容调用方：`gateway/app/routers/tasks.py` 与 `gateway/app/routers/hot_follow_api.py`

## 3. service 输入 / 输出

### 3.1 输入

当前唯一冻结的 compose service 入口是：

`CompositionService.compose(task_id, task, *, subtitle_resolver, subtitle_only_check)`

输入边界包括：

- `task_id`
- 原始 `task` dict
- `subtitle_resolver`
- `subtitle_only_check`

这些输入反映当前事实：

- compose service 已从 router 中抽离
- 但 subtitle 路由与 subtitle-only 判定仍通过调用方注入
- 本阶段不再发明新的 request model 或 line runtime 注入容器

### 3.2 输出

当前输出冻结为：

- 可直接用于 task 更新的结果 dict

当前不冻结为：

- 独立 `ComposeResult` 类
- 新的 deliverable contract model

说明：

- 基线承认当前仍是 dict contract
- `PR-2 / PR-3` 可以在不改语义的前提下，把 dict contract 收口成更明确的 result contract

## 4. router wrapper 的兼容职责

`_hf_compose_final_video()` 当前只允许承担以下职责：

- 为现有调用方保留旧函数名
- 从 router 环境中取到 repo / settings / storage 等现有依赖
- 调用 `CompositionService`
- 保持现有异常语义和返回结构兼容

`_hf_compose_final_video()` 当前不应继续承担：

- 新的 FFmpeg 逻辑
- 新的 compose 策略分支
- 新的状态真相写入规则
- 面向其他产线的通用抽象

## 5. timeout / retry / logging 边界归属

### 5.1 timeout

归属 `compose_service.py`。

冻结依据：

- `_run_ffmpeg()` 已是统一子进程入口
- `ComposeTimeouts` 已明确 `freeze_tail / compose / probe / clamp` 四类超时

### 5.2 retry

当前冻结为：

- router 负责“是否重试这次动作”的 HTTP 触发语义
- service 负责单次 compose 执行，不在本阶段内建新的 retry orchestration

本阶段不做：

- service 内自动重试
- artifact checkpoint retry-reconcile 机制
- cancel / abort 模型

### 5.3 logging

归属 `compose_service.py` 的执行过程日志。

当前文档认可的边界：

- service 负责 FFmpeg 执行日志与 compose 执行日志
- router 不再新增 compose 细节日志作为主记录面

## 6. direct test entry 目标

当前 direct test entry 目标冻结为：

- 未来优先直接覆盖 `gateway/app/services/compose_service.py`
- 测试 focus 是 service contract，而不是 router wrapper 名称

本 PR 不新增测试，但冻结以下方向：

- compose service 应成为直接测试入口
- router compose wrapper 只保留兼容回归验证

## 7. 当前做 / 当前不做

### 当前做

- 冻结 compose 入口、兼容层职责、timeout/logging 归属
- 承认返回仍为 dict contract
- 为后续从 wrapper 迁出调用方提供边界基线

### 当前不做

- 不移除 `_hf_compose_final_video()`
- 不改 `tasks.py` 当前 compose 反向依赖
- 不引入新的 compose 平台层抽象
- 不在本 PR 中完成 cancel / abort / result model
