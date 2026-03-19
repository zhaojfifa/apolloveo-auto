# ApolloVeo Docs

## Layout

- `docs/baseline/`
  - 长期基线文档与基线历史
- `docs/reviews/`
  - review、诊断、扫雷报告、阶段分析输出
- `docs/execution/`
  - 当前阶段执行计划、阶段收口文档、下一步 cleanup 包
- `docs/contracts/`
  - runtime / service / API contract 文档
- `docs/architecture/`
  - 架构说明、line contract、YAML contract、结构性规范
- `docs/runbooks/`
  - verification、business regression、operator/developer runbook
- `docs/skills/`
  - skills 相关文档与技能目录
- `docs/archive/`
  - legacy / 历史保留文档，不作为当前阶段 source-of-truth

现阶段仍保留但未并入上述主桶的目录：

- `docs/scenarios/`
  - 场景/SOP 文档，当前仍有业务语义引用
- `docs/sop/`
  - 现存 SOP 历史路径，当前 line contract / review 仍引用

## Current Source Of Truth

当前阶段优先以以下文档作为 source-of-truth：

1. `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
2. `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
3. `docs/runbooks/VERIFICATION_BASELINE.md`
4. `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
5. `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
6. `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
7. `docs/execution/NEXT_HOT_FOLLOW_CLEANUP_SCOPE.md`

## Recommended Reading Order

如果要理解当前阶段执行边界，推荐顺序如下：

1. `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
2. `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
3. `docs/runbooks/VERIFICATION_BASELINE.md`
4. `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
5. `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
6. `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
7. `docs/execution/NEXT_HOT_FOLLOW_CLEANUP_SCOPE.md`
8. `docs/execution/FROZEN_EXECUTION_PLAN_AFTER_VEOSOP04.md`
9. `docs/reviews/REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md`
10. `docs/reviews/ALIGNMENT_BASELINE_20260318.md`

## Notes

- `docs/reviews/` 里的文档用于诊断与审计，不默认等于当前执行 source-of-truth。
- `docs/archive/` 里的文档保留 traceability，但不作为当前阶段执行入口。
- 本次整理仅调整 docs 信息架构，不涉及 runtime logic、tests 或 feature work。
