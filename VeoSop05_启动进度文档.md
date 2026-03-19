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
