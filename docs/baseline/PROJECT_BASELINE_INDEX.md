# Project Baseline Index

## This Layer Is For

本层是当前项目的长期 baseline，不记录逐日进度，不替代短期 execution 文档。

它负责回答：

- 当前项目定位
- 当前工程现实
- 当前已收口与未收口边界
- 下一层应该读什么

## Current

- ApolloVeo 当前不是平台扩张期，而是 post-review、post-VeoSop05 的基座收口期
- Hot Follow 是当前唯一已经完成一轮真实业务验证的主线
- Hot Follow 现在也是当前唯一完成 Skills MVP v0 closure 的业务样本
- `TASK-1.3`、`TASK-2.0`、`TASK-2.3`、verification baseline、PR-5、PR-6 的收口结果已进入当前 baseline
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` 是 `docs/reviews/ALIGNMENT_BASELINE_20260318.md` 的后续代码验证版，作为新产线前置准入文档和后续 PR gate 依据

## Partial

- `tasks.py` 仍有剩余 Hot Follow-specific logic
- compatibility helpers 仍存在
- full line-aware unification 仍未覆盖 publish / workbench / detail 全链
- current gate/profile binding 仍是 Hot Follow-focused 最小实现
- 新产线 onboarding 当前仍被 `2026-03-18-plus_factory_alignment_code_review.md` 判定为 “Only after prerequisites”

## Postponed

- Skills implementation
- second production line
- OpenClaw integration work
- broad platformization

## Historical

- `_drafts/` 是历史 review 与 RFC source material，不是日常 source-of-truth
- superseded v1.9 review baseline 已移到 `docs/archive/`
- 诊断性 review 文档保留在 `docs/reviews/`

## Read Next

1. `PRODUCT_BASELINE.md`
2. `ARCHITECTURE_BASELINE.md`
3. `EXECUTION_BASELINE.md`
4. `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
5. `docs/execution/HOT_FOLLOW_SKILLS_MVP_V0_CLOSURE.md`
6. `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
7. `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
8. `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md`
9. `docs/reviews/appendix_code_inventory.md`
10. `docs/reviews/appendix_router_service_state_dependency_map.md`
11. `docs/reviews/appendix_four_layer_state_map.md`
12. `docs/reviews/appendix_line_contract_skill_readiness.md`

## Gate References

后续涉及以下范围的 PR 必须引用 `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` 或其 appendices：

- 新 production line onboarding
- `tasks.py` / `hot_follow_api.py` / `task_view.py` 结构性改动
- 四层 state model / ready gate / deliverables SSOT 改动
- Skills / Worker Gateway / line contract runtime 扩展
- publish / workbench response contract 改动
