# ApolloVeo Docs Index

## Directory Map

- `docs/baseline/`
  - 当前长期 baseline
- `docs/execution/`
  - 当前阶段执行文档与执行日志
- `docs/reviews/`
  - review、诊断、架构对齐与工程分析
- `docs/contracts/`
  - 当前 runtime / service contract
- `docs/architecture/`
  - 架构说明、line contracts、结构化 YAML
- `docs/runbooks/`
  - verification、business regression、operator/developer runbooks
- `docs/skills/`
  - skills 相关规范与目录说明
- `docs/archive/`
  - 历史/legacy 文档

保留目录：

- `docs/scenarios/`
  - 场景/SOP 文档，当前仍有业务语义引用
- `docs/sop/`
  - 历史 SOP 路径，当前 line contract / review 仍直接引用

## Purpose Of Each Bucket

- `baseline/`
  - 说明当前项目到底是什么、当前现实到哪里、哪些仍是 partial
- `execution/`
  - 说明当前阶段在做什么、已经收口什么、下一步只允许做什么
- `reviews/`
  - 保留 review 诊断与架构对齐材料
- `contracts/`
  - 固化当前运行时与服务边界
- `architecture/`
  - 保留结构性设计、line contract 和架构规范
- `runbooks/`
  - 固化验证、回归、运维/开发执行手册
- `skills/`
  - 保留 skills 相关规范；当前不代表 skills runtime 已实现
- `archive/`
  - 放置 superseded / legacy material，不作为当前 source-of-truth

## Current Source-Of-Truth Reading Order

1. `ENGINEERING_RULES.md`
2. `CURRENT_ENGINEERING_FOCUS.md`
3. `docs/baseline/PROJECT_BASELINE_INDEX.md`
4. `docs/baseline/PRODUCT_BASELINE.md`
5. `docs/baseline/ARCHITECTURE_BASELINE.md`
6. `docs/baseline/EXECUTION_BASELINE.md`
7. `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
8. `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
9. `docs/runbooks/VERIFICATION_BASELINE.md`
10. `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
11. `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
12. `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
13. `docs/execution/NEXT_HOT_FOLLOW_CLEANUP_SCOPE.md`
14. `docs/execution/logs/VEOSOP05_PROGRESS_LOG.md`

## Important Review References

以下文档是重要 review/reference，但不等于日常 baseline authority：

- `docs/reviews/ALIGNMENT_BASELINE_20260318.md`
  - 重要架构对齐文件，保留在 `reviews/`
- `docs/reviews/REVIEW_AFTER_VEOSOP04_WITH_DEMINING_PRIORITY.md`
- `docs/reviews/TASK_1_3_PORT_MERGE_PLAN.md`
- `docs/reviews/TASK_2_0_COMPOSE_SURGERY.md`
- `docs/reviews/TASK_2_3_READY_GATE_REPORT.md`

## Historical / Reference-Only Areas

- `_drafts/`
  - 历史 review source material 与 RFC 草案来源
  - 不作为 day-to-day active source-of-truth
- `docs/archive/`
  - 已降级为历史参考的旧 baseline / 旧 contract / legacy docs
- `docs/reviews/v1.9/`
  - v1.9 review package，保留参考价值但不是当前 baseline authority

## Notes

- `_drafts/` 的结论必须被吸收到 `docs/baseline/`、`docs/execution/`、`docs/reviews/`，不能让 `_drafts/` 继续承担活文档职责。
- 本 docs system 反映的是 post-review、post-VeoSop05 reality，而不是未来平台理想态。
