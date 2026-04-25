# ApolloVeo 2.0 P2 Readiness Unified Review

Date: 2026-04-25
Status: P2 pre-readiness review; docs/planning only

## 1. Executive Summary

本次评审结论：当前仓库已经具备 P2 前置规划的主要材料，但还不能直接进入 P2 实施。

已经足够的部分：

- Hot Follow 已经可以作为 ApolloVeo 2.0 的 reference line，而不是继续作为本轮修复目标。
- v1.1 规划基线已把 factory contract objects、runtime boundary、workbench mapping、line template 提升到 Hot Follow 之上。
- v1.1 remote merge 已补齐 factory packet envelope 与 validator rules：P2 前必须把 input、content structure、scene plan、audio plan、language plan、delivery 六类合同对象通过 envelope 装订，并由 validator rules 校验。
- donor/SwiftCraft 已正式定位为 capability donor；donor boundary、capability mapping、ADR、host directory reservation 已落盘。
- donor/Jellyfish 的吸收边界已经清楚：只吸收 planning/intermediate structure，不吸收 studio product shell、Agent 管理、VideoEditor、直接业务 truth 写法。

部分足够的部分：

- authority layer 有索引优先纪律、v1.1 master plan、packet/donor/handoff 文件和当前 source-of-truth 顺序；本次 review 将其收口成 P2 专用 minimum authority set。
- gate layer 的 packet、surface、donor、execution-base 四类 gate 已有规则来源；本次补齐 P2 前可逐项签收的 gate checklist。
- role layer 已有 product/design handoff；本次补齐产品、架构、设计、后端、实现、review/merge owner 的同一张责任矩阵。

缺失的部分：

- 缺少一个顶层、product-facing、role-readable 的 ApolloVeo 2.0 business flow diagram。
- 缺少一个 P2 pre-execution base，明确 P2 之前只能做什么、不能做什么、哪些 gate 失败时必须继续 blocked。本次已补齐。
- 缺少 evidence index，把当前判断依赖的 authority、handoff、donor、Hot Follow reference-line 证据聚合到一个入口。本次已补齐。
- factory-wide surface response contracts 仍未冻结；当前仅有 Hot Follow workbench response authority 与 product/design handoff 的 surface 要求。

Codex judgment:

- Repo is not ready for P2 implementation now.
- Exact blockers are:
  1. Product handoff 要求的 Matrix Script / Digital Anchor packet schema、sample instance 尚未交付。
  2. Packet validator rules 已冻结为文档，但 validator runtime、contract tests、Hot Follow sample validator run 尚未完成。
  3. P1.5 donor gate 除 capability adapter 接口骨架外已落盘；adapter base 仍是卡点，且不得吸收 donor code。
  4. Factory-wide versioned intake/planning/delivery surface response contracts 尚未冻结。
  5. Reviewer / Merge Owner 尚未对 P2 implementation entry gate 做最终 signoff。

## 2. Current Authority Map

### 2.1 当前权威入口

P2 前的 authority 必须从这些入口开始：

| 层级 | 当前文件 | 评审判断 |
| --- | --- | --- |
| root stage / scope | `README.md` | 明确当前是 Factory Alignment Review Gate Active，不是平台扩张期。 |
| root engineering constraints | `ENGINEERING_CONSTRAINTS_INDEX.md` | 明确 router/service ownership、single-writer、validation、PR slicing。 |
| current focus | `CURRENT_ENGINEERING_FOCUS.md` | 明确 forbidden work 包括 second/new production line onboarding、OpenClaw 扩张、runtime rewrite。 |
| current status | `ENGINEERING_STATUS.md` | 明确 Hot Follow 是 business-validated line，但不是完全标准化 reusable engineering line。 |
| docs structure | `docs/README.md` | 明确 docs bucket 责任和 historical/reference-only 区域。 |
| engineering index | `docs/ENGINEERING_INDEX.md` | 明确 document priority、task-oriented reading map、new-line gate。 |
| reading contract | `docs/contracts/engineering_reading_contract_v1.md` | 冻结 index-first reading 和 Reading Declaration。 |
| project baseline | `docs/baseline/PROJECT_BASELINE_INDEX.md` | 明确 current/partial/postponed 和 factory alignment code review gate。 |

### 2.2 P2 前 minimum authority set

P2 前只允许以以下 minimum set 作为统一执行 base 的上层 authority：

1. `README.md`
2. `ENGINEERING_CONSTRAINTS_INDEX.md`
3. `CURRENT_ENGINEERING_FOCUS.md`
4. `ENGINEERING_STATUS.md`
5. `docs/README.md`
6. `docs/ENGINEERING_INDEX.md`
7. `docs/contracts/engineering_reading_contract_v1.md`
8. `docs/baseline/PROJECT_BASELINE_INDEX.md`
9. `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
10. `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md`
11. `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
12. `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
13. `docs/architecture/factory_line_template_design_v1.md`
14. `docs/architecture/factory_runtime_boundary_design_v1.md`
15. `docs/architecture/factory_workbench_mapping_v1.md`
16. `docs/contracts/production_line_runtime_assembly_rules_v1.md`
17. `docs/contracts/factory_input_contract_v1.md`
18. `docs/contracts/factory_content_structure_contract_v1.md`
19. `docs/contracts/factory_scene_plan_contract_v1.md`
20. `docs/contracts/factory_audio_plan_contract_v1.md`
21. `docs/contracts/factory_language_plan_contract_v1.md`
22. `docs/contracts/factory_delivery_contract_v1.md`
23. `docs/reviews/review_jellyfish_importability_for_factory.md`
24. `docs/architecture/hot_follow_business_flow_v1.md`
25. `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
26. `docs/contracts/factory_packet_envelope_contract_v1.md`
27. `docs/contracts/factory_packet_validator_rules_v1.md`
28. `docs/donor/swiftcraft_donor_boundary_v1.md`
29. `docs/donor/swiftcraft_capability_mapping_v1.md`
30. `docs/adr/ADR-donor-swiftcraft-capability-only.md`
31. `docs/handoffs/apolloveo_2_0_product_handoff_v1.md`
32. `docs/handoffs/apolloveo_2_0_design_handoff_v1.md`

### 2.3 Historical-only / reference-only

这些材料可解释历史，但不能覆盖当前 authority：

| 文件/区域 | 当前定位 |
| --- | --- |
| `_drafts/` | 历史 review source material，不是 day-to-day source-of-truth。 |
| `docs/archive/` | superseded / legacy material，仅历史参考。 |
| `docs/reviews/v1.9/` | v1.9 review package，保留参考价值，不是当前 baseline authority。 |
| `docs/archive/contracts/HOT_FOLLOW_API_CONTRACT_v1.md` | 旧 Hot Follow API contract，不覆盖当前 workbench/ready-gate 合同。 |
| `docs/reviews/ALIGNMENT_BASELINE_20260318.md` | 重要前序 review，但当前 active gate 是 2026-03-18+ code review。 |

### 2.4 Authority 问题

当前 `docs/ENGINEERING_INDEX.md` 仍列出若干未在当前仓库中发现的未来文件名，例如 `docs/contracts/line_contract.schema.json`、`docs/contracts/veobase01_glossary.md`、`docs/contracts/new_line_onboarding_template.md`、`docs/contracts/skills_bundle_boundary.md`。这些不能作为 P2 签收证据，除非后续补齐或在索引中明确替换。

## 3. P2 Precondition Gates Review

| Gate | 当前状态 | 已有证据 | 缺口 |
| --- | --- | --- | --- |
| Packet gate | Partially defined | factory six contract objects、factory line template、`factory_packet_envelope_contract_v1.md`、`factory_packet_validator_rules_v1.md` | envelope / rules 已冻结；缺少 line packet schema、sample instance、validator runtime、validator report。 |
| Surface gate | Partially defined | `workbench_hub_response.contract.md`、`factory_workbench_mapping_v1.md`、Hot Follow freeze | 缺少 P2 级 intake/planning/delivery center versioned response contracts。 |
| Donor gate | Partially passed | `swiftcraft_donor_boundary_v1.md`、`swiftcraft_capability_mapping_v1.md`、donor ADR、host directories | 文档与目录已落盘；capability adapter base 未实现；donor code absorption 仍 blocked。 |
| Execution-base gate | Pass after this pass | root/docs indexes、engineering reading contract、Factory Alignment gate、P2 execution base、role matrix、gate checklist、evidence index | 仍需 Reviewer / Merge Owner signoff。 |

Gate 判断：

- packet gate 不能视为 implementation-ready；envelope 与 validator rules 已存在，但 line packet schema、sample、validator runtime/report 尚未完成。
- surface gate 不能视为通过；Hot Follow surface discipline 已足够作为 reference，但 ApolloVeo 2.0 P2 的通用 surface response 仍未冻结。
- donor gate 文档层已基本通过，但不能作为吸收授权；P2 前只能做 mapping、adapter interface、contract refactoring plan。
- execution-base gate 本次已补齐；进入 implementation 仍需要 review/merge owner 明确冻结。

## 4. Multi-Role Execution Readiness Review

当前 repo 支持分层责任，但角色协作基线不够显式。

| Role | 当前已有支撑 | 缺口 | P2 前判断 |
| --- | --- | --- | --- |
| Product | factory contract objects、Hot Follow business flow、product handoff、v1.1 packet requirements | Matrix Script / Digital Anchor packet schema 与 sample 尚未交付 | Partially ready |
| Architect | v1.1 master plan、factory four-layer baseline、runtime boundary、line template、runtime assembly rules、packet/donor docs | 需要对本次 P2 execution base 与 checklist 做签收 | Mostly ready |
| Designer | factory workbench mapping、design handoff、Hot Follow business flow | 低保真 IA/surface artifact 尚未交付；surface response contracts 尚未冻结 | Partially ready |
| Backend/Platform | runtime boundary、worker/skills contracts、status ownership、packet validator rules、host directories | validator runtime、adapter base、surface response versioning、line conformance gate 未实现 | Partially ready |
| Implementer | reading contract、engineering constraints、execution logs | P2 implementation must remain blocked until gates pass | Not ready for implementation |
| Reviewer / Merge Owner | active review gate、baseline index、validation rules、P2 gate checklist、evidence index | 需要签收 implementation entry gate | Partially ready |

P2 前必须冻结的 role-facing 结果：

- `docs/execution/apolloveo_2_0_role_matrix_v1.md`
- `docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`

## 5. Top-Level Business Flow Review

已有的 `docs/architecture/hot_follow_business_flow_v1.md` 是 Hot Follow line 的业务流，质量足够作为 reference line。

但它不满足 P2 所需的顶层 ApolloVeo 2.0 flow，因为：

- 它是 Hot Follow-specific，不是 factory-level。
- 它没有同时表达 product production logic、workbench flow、delivery logic。
- 它没有把 six factory contract objects 映射到每个 stage。
- 它没有给 Product、Architect、Designer、Backend/Platform、Implementer、Reviewer 同一张 role-readable handoff 图。

因此，本次评审要求新增 `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` 作为 P2 前 required baseline artifact。

## 6. Concrete Recommendations

### Must do before P2

1. 冻结 P2 execution base，声明 P2 前只允许 docs/planning/gate work，不允许 runtime behavior change。
2. 冻结 P2 gate checklist，并把 packet、surface、donor、execution-base gate 分成 pass/partial/missing/blocking。
3. 冻结 role matrix，明确每个角色的 owner/non-owner 和 handoff evidence。
4. 冻结 top-level business flow diagram，作为所有角色共同阅读的 product/business reference。
5. 交付 Matrix Script / Digital Anchor line packet schema、sample instance，并通过 envelope + validator rules 的文档级检查。
6. 明确 capability adapter base 的接口骨架交付范围；它是 donor absorption 前置卡点，不是 donor code absorption。

### Should do before P2

1. 将 intake、planning/workbench、delivery center 的 versioned response contract 补齐到 docs/contracts。
2. 把 SwiftCraft donor boundary / capability mapping 的 row-id 机制纳入 P2 donor acceptance checklist。
3. 为 future line packet 增加 line conformance test plan，但不要写 runtime tests 或实现。
4. 增加 P2 review owner signoff 规则：没有 gate checklist signoff，不进入 implementation PR。

### Can defer to P2/P3

1. packet validator service 的 runtime implementation，直到 P1/P2 implementation gate 开启。
2. capability registry / adapter governance 的代码实现。
3. new line runtime onboarding。
4. OpenClaw gateway stub。
5. UI/workbench implementation 或 donor UI pattern absorption。

## 7. Blocking Items Before P2

进入 P2 implementation 前必须继续 blocked 的事项：

- new production line route stack
- donor code absorption
- Jellyfish studio shell import
- UI implementation
- router/service refactor
- packet validator runtime code
- surface response runtime rewiring
- Hot Follow feature fixes
- OpenClaw integration

必须先完成的 blockers：

1. P2 execution base review/merge owner signoff。
2. gate checklist 全部 Must gate 至少达到 `ready_for_p2_planning`，且 implementation gates 明确 blocked。
3. top-level business flow 被 Product、Architect、Designer、Backend/Platform、Reviewer 共同引用。
4. factory packet envelope 和 validator spec 已冻结；下一步必须产出 packet schema、sample、validator report 或明确 blocked reason。

## 8. Suggested Execution Order

1. 合并本次 review/planning artifacts。
2. Review/merge owner 对 P2 execution base 和 gate checklist 做一次 docs-only signoff。
3. Product + Architect 共同补齐 Matrix Script / Digital Anchor packet schema 与 sample instance。
4. Designer + Backend/Platform 共同补齐 surface response contract draft，并对齐 design handoff 的五面 IA。
5. Reviewer 建立 P2 implementation entry gate：没有 packet/surface/donor/execution-base evidence，不允许开 runtime PR。
6. 只有 gate pass 后，再拆 P2 implementation PR；每个 PR 仍必须遵守 index-first reading、single purpose、behavior declaration、validation rules。

## 9. Evidence Links

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`
- `docs/README.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`
- `docs/baseline/PROJECT_BASELINE_INDEX.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- `docs/reviews/2026-03-18-plus_factory_alignment_code_review_summary.md`
- `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
- `docs/architecture/factory_four_layer_architecture_baseline_v1.md`
- `docs/architecture/factory_line_template_design_v1.md`
- `docs/architecture/factory_runtime_boundary_design_v1.md`
- `docs/architecture/factory_workbench_mapping_v1.md`
- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/donor/swiftcraft_donor_boundary_v1.md`
- `docs/donor/swiftcraft_capability_mapping_v1.md`
- `docs/adr/ADR-donor-swiftcraft-capability-only.md`
- `docs/handoffs/apolloveo_2_0_product_handoff_v1.md`
- `docs/handoffs/apolloveo_2_0_design_handoff_v1.md`
- `docs/contracts/production_line_runtime_assembly_rules_v1.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/reviews/review_jellyfish_importability_for_factory.md`
- `docs/execution/VEOBASE01_EXECUTION_LOG.md`
