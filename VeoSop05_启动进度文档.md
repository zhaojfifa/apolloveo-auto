# VeoSop05 启动进度文档

## PR-1 Runtime Contract Freeze

日期：2026-03-19

本节点冻结以下文档边界：

- Hot Follow runtime contract
- Compose service contract
- Gate binding contract
- Verification baseline

本次冻结的核心边界：

- `tasks.py` / `hot_follow_api.py` / service / line contract 的职责边界先文档收口，不改业务逻辑
- `CompositionService.compose()` 是当前 compose 主体，`_hf_compose_final_video()` 仍是兼容 wrapper
- `HOT_FOLLOW_GATE_SPEC` 是当前 ready gate spec 来源，但尚未由 line contract 运行时接管
- Python 3.10+ 是后续 Hot Follow 本地/CI 验证的最低基线

本次明确后置的实现：

- router 解环的实际代码收口
- compose 调用方从 router wrapper 迁出
- line-aware status policy / ready gate runtime 装配
- skills runtime
- 第二条产线扩展

本节点输出文档：

- `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
- `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
- `docs/runbooks/VERIFICATION_BASELINE.md`

## PR-3 Compose Runtime Closure

日期：2026-03-19

本节点完成：

- 将 Hot Follow compose 主链编排收口到 `gateway/app/services/compose_service.py`
- 为 compose 增加明确的 request / response contract
- 让 `tasks.py` 与 `hot_follow_api.py` 的 compose 路由只保留 request parsing / response mapping
- 为 compose service 增加 direct test entry

本次削薄的 wrapper / router：

- `gateway/app/routers/tasks.py::compose_task()`
  - 不再直接编排 compose plan、状态写入、短路返回、异常回写
- `gateway/app/routers/hot_follow_api.py::compose_hot_follow_final_video()`
  - 不再保留重复的 compose orchestration
- `gateway/app/routers/hot_follow_api.py::_hf_compose_final_video()`
  - 保留为兼容 wrapper，不再作为主链入口

本节点后置保留：

- gate binding / line-aware status policy 仍留给 PR-4
- `_hf_allow_subtitle_only_compose` / `_resolve_target_srt_key` 仍是 Hot Follow 兼容 helper，后续可继续从 router 退出

## PR-4 Gate Binding + Verification Baseline

日期：2026-03-19

本节点完成：

- 将 `hot_follow_line -> ready_gate_ref -> HOT_FOLLOW_GATE_SPEC` 的最小 runtime 绑定落到代码
- 为 status policy 增加 `get_status_runtime_binding(task)` 作为最小 line-aware 装配入口
- 让 `compute_hot_follow_state()` 通过 runtime binding 消费 gate spec，而不是继续直接 import 规则源
- 冻结系统 `python3` 与 `./venv/bin/python` 的最小验证职责边界

本次新增或更新的最小绑定点：

- `gateway/app/lines/base.py`
  - 增加 `ready_gate_ref` / `status_policy_ref`
- `gateway/app/lines/hot_follow.py`
  - 明确声明 Hot Follow line 的 `ready_gate_ref` / `status_policy_ref`
- `gateway/app/services/ready_gate/registry.py`
  - 负责 `LineRegistry.for_kind(task.kind) -> ready_gate spec`
- `gateway/app/services/status_policy/registry.py`
  - 提供 `get_status_runtime_binding(task)`
- `gateway/app/services/status_policy/hot_follow_state.py`
  - 改为消费 runtime 绑定出来的 `ready_gate_spec`

本节点验证冻结：

- 系统 `python3` 当前为 `Python 3.9.6`
- `./venv/bin/python` 当前为 `Python 3.11.15`
- 最低纯单测与推荐 3.10+ 回归命令已写入 `docs/runbooks/VERIFICATION_BASELINE.md`

本节点明确不做：

- 不扩大 router / bridge 职责
- 不继续改 compose 主链
- 不启动 Skills MVP
- 不扩第二条产线

## PR-5 Parse Status + Subtitle SRT-First Consistency Fix

日期：2026-03-19

本节点修复：

- parse 实际已成功但 UI 仍显示 failed 的一致性问题
- Hot Follow 工作台中目标语言字幕编辑对象的 SRT-first 语义不够明确的问题

本次收口的边界：

- parse 状态改为优先由 raw artifact / fact 推导
  - `raw_video done`
  - `raw_url`
  - `source_video.url`
  - `raw=ready`
- 目标语言字幕编辑区明确为 `mm.srt` 对应的 SRT 主对象
- 辅助输入 / OCR 候选 / 标准化来源文本明确降级为 helper-only 语义，不再与主 SRT 对象混淆

本节点明确不做：

- 不改 translation generation
- 不改 dubbing logic
- 不改 compose runtime policy
- 不扩大 router 重构范围
