# VeoSop05 Stage Closure

## 1. Stage Scope

`VeoSop05` 当前阶段只覆盖以下收口主题：

- `TASK-1.3` closure
- `TASK-2.0` runtime closure
- `TASK-2.3` minimal line-aware binding
- verification baseline freeze
- `PR-5` parse/subtitle consistency fix
- `PR-6` video-master compose duration fix

本阶段不包含：

- Skills implementation
- second production line
- OpenClaw integration
- platform-level abstractions

## 2. What Is Now Closed

以下事项在当前阶段视为真实收口，不再按“仅文档宣称”处理：

- `tasks.py` 与 `hot_follow_api.py` 的 router direct coupling 已清零
- Hot Follow compose flow 已进入 `CompositionService.run_hot_follow_compose(...)` / `CompositionService.compose(...)` 背后的 service contract 主链
- 最小 line-aware gate binding 已建立：
  - `task.kind -> LineRegistry.for_kind() -> hot_follow_line -> ready_gate_ref -> HOT_FOLLOW_GATE_SPEC`
- verification baseline 已冻结：
  - 系统 `python3` 的限制
  - `./venv/bin/python` 的推荐角色
  - 最小回归命令
- parse 展示已与 raw artifact / fact 对齐，不再被误导性的 legacy state 覆盖
- translated subtitle editing 保持 SRT-first，时间线编辑对象仍是主对象
- final compose duration 已跟随视频时长，不再被短音频或 `-shortest` 截断

## 3. What Is Still Partial

以下内容仍是 partial，不能过度宣称：

- `gateway/app/routers/tasks.py` 仍承载一部分 Hot Follow-specific logic
- compatibility-only helpers 仍存在，尤其是 Hot Follow router 兼容入口与少量 helper 名称
- publish / workbench / detail 的 full line-aware unification 还未完成
- 当前 gate/profile resolution 仍是 Hot Follow-focused 的最小实现，不是 generic multi-line loader
- Skills MVP 尚未开始

## 4. Business Validation Results

近期业务验证结果已冻结为项目事实：

- parse success 现在会正确渲染为成功状态，不再出现 `raw=ready` 但 parse 显示 failed
- translated subtitle editing 仍保持 timeline-based 的 SRT-first 语义
- final composition length 不再塌缩到 dub/audio length
- final output 已可在真实业务流中使用，而不是只在测试里通过

这意味着当前阶段的收口不只是代码层通过，也已经过真实业务使用验证。

## 5. Validation Baseline

本阶段验证基线以 [docs/runbooks/VERIFICATION_BASELINE.md](/Users/tylerzhao/Code/apolloveo-auto/docs/runbooks/VERIFICATION_BASELINE.md) 为准，核心结论如下：

- 系统 `python3` 仍受 Python 3.9.6 限制，不能被误写成主线回归环境
- 推荐解释器是 `./venv/bin/python`，当前为 Python 3.11.15
- 最小回归命令必须按冻结文档执行
- 必须区分：
  - environment limitation
  - real regression

不能把 Python baseline 不匹配误判成业务回归，也不能把真实业务回归误判成环境噪声。

## 6. Next-Step Boundary

下一步必须继续留在 Hot Follow cleanup 范围内：

- 继续削薄 `tasks.py`
- 继续隔离 compatibility-only helpers
- 继续清理 Hot Follow-specific workbench / detail / presentation assembly

下一步明确不做：

- no second production line yet
- no Skills implementation yet
- no OpenClaw work
- no platformization expansion

后续每一个 Hot Follow follow-up change 都必须重新通过 business regression，而不能只靠自动化测试或结构判断合并。
