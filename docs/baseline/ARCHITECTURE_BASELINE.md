# Architecture Baseline

## This Layer Is For

本文件冻结当前工程架构现实，重点是“已实现什么、partial 在哪里、哪些被明确后置”。

## Current Reality

- `LineRegistry`、`hot_follow_line`、ready gate engine、status policy runtime binding 已存在
- Hot Follow compose 主链已收口到 service contract 背后
- router direct coupling 已清零
- deliverables-first / status-derived 的方向已进入实际修复与展示逻辑
- 四层 state schema 已在 Hot Follow 上形成第一条真实 reference implementation，但正式模板仍以 contract 文档为准

## Partial Reality

- line contract 已进入最小 runtime binding，但尚未成为 full runtime backbone
- `tasks.py` 仍保留一部分 Hot Follow-specific orchestration / presentation residue
- compatibility wrappers 仍存在，尤其在 Hot Follow router 边界
- current gate/profile resolution 仍是 single-line focused，而不是 generic multi-line loader

## Postponed

- Skills runtime
- multi-line runtime loading
- broad asset sink / worker profile runtimeization
- OpenClaw control mesh integration

## Historical Superseded Material

- `_drafts/C.3`、`_drafts/C.5` 描述了 future-facing framework direction
- `docs/archive/v1.9/REVIEW_v1.9_BASELINE.md` 是历史评审锚点
- 它们保留参考价值，但当前实现边界以 `docs/contracts/`、`docs/architecture/line_contracts/`、`docs/execution/` 为准

## Read Next

- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
- `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
