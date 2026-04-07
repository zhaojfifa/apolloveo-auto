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
- `docs/adr/`
  - 架构决策记录（ADR）
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
- `adr/`
  - 固化已经接受的架构决策与拆解原则
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
7. `docs/contracts/hot_follow_line_contract.md`
8. `docs/contracts/status_ownership_matrix.md`
9. `docs/contracts/hot_follow_ready_gate.yaml`
10. `docs/contracts/worker_gateway_contract.md`
11. `docs/contracts/skills_runtime_contract.md`
12. `docs/contracts/worker_gateway_runtime_contract.md`
13. `docs/contracts/script_video_planning_contract.md`
14. `docs/contracts/action_replica_planning_assets_contract.md`
15. `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
16. `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
17. `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
18. `docs/contracts/SKILLS_MVP_ADVISORY_CONTRACT.md`
19. `docs/adr/ADR-task-router-decomposition.md`
20. `docs/adr/ADR-phase2-skills-worker-planning.md`
21. `docs/runbooks/hot_follow_sop.md`
22. `docs/runbooks/phase2_execution_plan.md`
23. `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
24. `docs/runbooks/VERIFICATION_BASELINE.md`
25. `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
26. `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
27. `docs/execution/HOT_FOLLOW_SKILLS_MVP_V0_CLOSURE.md`
28. `docs/execution/SKILLS_MVP_ENTRY_REVIEW.md`
29. `docs/execution/NEXT_HOT_FOLLOW_CLEANUP_SCOPE.md`
30. `docs/execution/logs/VEOSOP05_PROGRESS_LOG.md`
31. `docs/execution/logs/PHASE2_PROGRESS_LOG.md`

## Important Review References

以下文档是重要 review/reference，但不等于日常 baseline authority：

- `docs/reviews/ALIGNMENT_BASELINE_20260318.md`
  - 重要架构对齐文件，保留在 `reviews/`
- `docs/reviews/ALIGNMENT_EXECUTION_REVIEW_20260321.md`
  - 面向执行边界的后续对齐 review
- `docs/reviews/review_jellyfish_importability_for_factory.md`
  - 只作为中间契约/分层吸收参考，不作为 studio product 导入依据
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
- Phase-2 contract freeze 文档进入 source-of-truth 阅读顺序，不等于 Phase-2 runtime 已实现；实现状态仍以对应 PR 和 progress log 为准。
