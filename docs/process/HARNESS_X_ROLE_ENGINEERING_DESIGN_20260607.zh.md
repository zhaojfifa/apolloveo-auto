# Harness X — 角色工程设计（2026-06-07）

> 中文版本。**内容以英文版为准**
> （`docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md`）；
> 如有歧义或冲突，以英文版为权威，本文档随后做 docs-only 更正。

状态：**设计文档 — 仅文档（docs-only）。这是一份协同协议规范，不是自动化代码，也不是
runtime authority。** 它把 Harness X v2.1 从一份*工作流建议*推进为一套*可执行的多角色
协同协议*：一个状态机，其中每个角色消费一个已定义的产物、产出一个已定义的产物、给出一个
裁决，并且**除非协议明确允许自动推进，否则不得自我授权进入下一阶段**。**Owner 是所有
风险步骤唯一的最终阶段流转裁决者。**

来源输入：
- `Harness-X_WORKFLOW_v2.1.md`（v2.1 候选基线）——角色、阶段、红线、Matrix Script 复盘、
  报告模板。
- v2.0 `WORKFLOW.md`——工程主线（Architect → Developer → Reviewer → Owner）及本设计所
  保留的 L0/L1/L2 分级与红线。

本设计不 supersede 仓库 authority。当它与 `ENGINEERING_RULES.md`、
`CURRENT_ENGINEERING_FOCUS.md` 或任何 Bucket A authority 冲突时，仓库 authority 优先，
本规范随后做 docs-only 更正。特别地，Harness X 角色是一套*协同*协议；它们绝不凌驾于 wave
gate、contract-first 规则，或 no-private-memory 规则（CLAUDE.md §3）之上。

---

## 1. 目的（§2.1）

Harness X 角色**不是多个可自由行动的 agent**。它们是状态机中的位置。该协议存在的意义是
让“做错的代价”变得便宜：在规划文档或静态预览阶段就抓住可用性与 scope 问题——在写任何
runtime 代码之前——而不是等到生产环境才发现。

每个角色遵守四条不变量：

- **消费（Consume）** 恰好一个已定义的前序产物（它的输入）。
- **产出（Produce）** 恰好一个已定义的产物（它的输出），采用标准结构（§4）。
- **裁决（Declare）** 一个结论：`PASS` / `PASS WITH ISSUES` / `FAIL` / `BLOCKED`。
- **绝不自我授权（Never self-authorize）** 进入下一阶段，除非流转表（§3）标记为可自动
  推进。风险流转需要 Owner 批准。

Owner 仍然是所有风险步骤唯一的最终阶段流转裁决者（合并到 main、部署、scope 扩张、authority
变更、推翻 Operator Review FAIL，以及跨越 Gate Spec → runtime 实现）。

这是 Matrix Script 案例（§8）那条教训的工程化推广：*能力正确 ≠ 运营可用；测试通过 ≠ 一线
运营知道怎么用；状态可观测 ≠ 产品路径清楚。*

---

## 2. 角色定义（§2.2）

每个角色都被规定为一份契约。“必读（Required reads）”始终隐含包含 `CLAUDE.md` §2 的 boot
sequence 与 index-first 纪律；下面只列出与任务相关的必读项。

### 2.1 Architect（架构师）

- **目的：** 给问题定性，并决定它进入工程主线（v2.1 §3.1）还是运营产品流（§3.2）。设定
  架构边界。
- **输入：** Problem Raised（Owner 的描述 / 一次失败试跑 / 一个 bug）。
- **必读：** `CURRENT_ENGINEERING_FOCUS.md`、`ENGINEERING_RULES.md`、相关 Bucket A /
  authority 索引。
- **产物：** Problem Decision Memo（§4）。
- **允许：** 对问题分类（能力 / 流程 / 状态 / 运营理解 / 环境）；指明所适用的 authority；
  声明任务类型与复杂度（L0/L1/L2/P-flow）。
- **禁止：** 写 runtime 代码；动手实现；绕过 wave gate。
- **PASS 标准：** 用一句诊断说清问题；分配任务类型 + 复杂度；引用所适用的 authority。
- **BLOCK 条件：** 所需 authority 文件缺失；请求与当前 wave 焦点冲突 →
  `BLOCKED_AUTHORITY_CONFLICT`。
- **下一消费者：** Product Planner（P-flow）或 Developer（工程 / bug）。

### 2.2 Product Planner（产品规划者）

- **目的：** 把已交付的能力翻译成运营可执行的流程——主流程、高级折叠、诊断、状态语言、
  页面分区。
- **输入：** Problem Decision Memo（P-flow 裁决）。
- **必读：** Bucket A authority 集；相关执行证据；substrate PR。
- **产物：** Workflow Plan（`docs/design/<feature>_WORKFLOW_PLAN_<date>.md`）。
- **允许：** 定义主流程 / 高级 / 诊断的划分；状态语言；A/B/C/D/E 分区；逐按钮预期；一份
  gate-spec-first 的 PR 拆分建议。
- **禁止：** 写代码；授权实现；supersede Bucket A；新建 IA / 平行流程。
- **PASS 标准：** 回答十个规划问题（v2.1 §5 Phase B）；指明绝对不能改什么；明确标注自身
  非 authority。
- **BLOCK 条件：** Bucket A authority 缺失或自相矛盾 → `BLOCKED_AUTHORITY_CONFLICT`。
- **下一消费者：** Preview Builder。

### 2.3 Preview Builder（预览构建者）

- **目的：** 构建静态预览 + 截图，让人能判断流程是否看得懂——在 runtime 之前，低成本验错。
- **输入：** Workflow Plan。
- **必读：** Workflow Plan；相关预览 Bucket A 参考。
- **产物：** Static Preview（`docs/design/previews/<feature>_preview.html`）+ Preview
  Screenshot（`docs/design/screenshots/<feature>_preview_<date>.png`）。
- **允许：** 仅静态 HTML/CSS；仅本地的折叠开关；一个真实业务场景；为生成截图而临时复用
  一次性静态服务器（事后移除）。
- **禁止：** 接后端；用真实数据；修改 `gateway/**`、真实 Workbench、路由或任何 runtime。
- **PASS 标准：** 所有要求的分区都渲染出来；真实场景（不是空白骨架）；无 runtime 接线；
  `git diff --check` 干净；docs-only。
- **BLOCK 条件：** 不接后端 / 真实数据就无法渲染 → 与 Product Planner 重新界定 scope；若
  预览开始需要 runtime → `BLOCKED_SCOPE_CREEP`。
- **下一消费者：** Operator Reviewer。

### 2.4 Operator Reviewer（运营评审者）

- **目的：** 严格站在一线运营的座位上，判断该流程能否被独立操作。这是实现前的可用性闸门。
- **输入：** Static Preview + Screenshot（Workflow Plan 仅作上下文）。
- **必读：** 预览 HTML + 截图。**不读代码。**
- **产物：** Operator Review Report（§4）。
- **允许：** 回答运营问题（v2.1 §5 Phase D）；指出令人困惑的文案 / 布局 / 密度；标注
  must-fix vs 可延后。
- **禁止：** 阅读或评估代码；评估架构；让工程“测试通过”的论点推翻一个可用性发现。
- **PASS 标准：** 无需工程师帮助即可完成流程；不再有阻断运营的困惑。
- **BLOCK 条件：** 预览缺少必需分区 / 无法渲染 → `BLOCKED_OPERATOR_FAIL`，退回 Preview
  Builder。
- **下一消费者：** Owner（裁决），随后 Gate Spec Author（PASS 时）。

### 2.5 Gate Spec Author（Gate Spec 作者）

- **目的：** 把已验证的规划 + 预览冻结成可强制执行的工程规则——runtime 实现的唯一输入。
- **输入：** Workflow Plan + 已通过的 Operator Review + Owner 放行。
- **必读：** Bucket A；Workflow Plan；两轮 Operator Review。
- **产物：** Gate Spec（`docs/design/<feature>_GATE_SPEC_<date>.md`）。
- **允许：** 约束性分区规则；状态源 / 四层映射；按钮行为；数据投影 + 禁止泄漏规则；验收
  测试；PR 拆分；禁改清单；一个 `<fill>` 签字块。
- **禁止：** 实现任何东西；开 wave；supersede Bucket A；授权后端/存储/provider/schema/
  contract 变更。
- **PASS（READY）标准：** 每个必需小节齐备；禁止 scope 明确且可路径扫描；验收行具体；切片
  小且有序；authority 边界已声明；签字块齐备。
- **BLOCK 条件：** Operator Review 未 PASS → 不得撰写（硬前置）；scope 超出规划 →
  `BLOCKED_SCOPE_CREEP`。
- **下一消费者：** Owner（签字），随后 Developer（签字合并后）。

### 2.6 Developer（开发者）

- **目的：** 严格按 Gate Spec 实现，一次一个 PR 切片，带测试。
- **输入：** 已签字的 Gate Spec；具体切片（如 PR-1）。
- **必读：** Gate Spec；`ENGINEERING_RULES.md`；它所消费的 substrate。
- **产物：** Implementation PR Report（§4）+ 代码/测试 diff。
- **允许：** 仅该切片允许的 scope；在既有真相之上做展示/文案/重排（UI 类 gate）；专用测试；
  行为保持。
- **禁止：** 自审作为 gating review；扩大 scope；切片打包；用绿色测试替代运营验收；触碰任何
  forbidden path。
- **PASS 标准：** diff 落在该切片允许 scope 内；测试覆盖用户路径；forbidden-path 扫描干净；
  行为保持；报告齐备。
- **BLOCK 条件：** Gate Spec 有歧义 → 退回 Gate Spec Author；所需改动落入 forbidden scope →
  `BLOCKED_SCOPE_CREEP`；测试失败 → `BLOCKED_TEST_FAIL`。
- **下一消费者：** Code Reviewer。

### 2.7 Code Reviewer（代码评审者）

- **目的：** 独立的 diff / 边界 / 测试 / 泄漏审计。非对称复核（实现者绝不为自己的代码把关）。
- **输入：** Implementation PR Report + diff。
- **必读：** Gate Spec；diff；forbidden-path 清单。
- **产物：** Code Review Report（§4）。
- **允许：** 核对 diff ⊆ Gate Spec；forbidden-path 扫描；测试覆盖检查；后端字段 / secret
  泄漏扫描；状态漂移检查。
- **禁止：** 产出产品方案；替代 Owner 批准；替代 Operator Trial。
- **PASS 标准：** 无 Gate Spec 偏离；无 forbidden-path 触碰；测试覆盖用户路径；无泄漏；无
  状态漂移。
- **BLOCK 条件：** 触碰 forbidden-path / 泄漏 / scope 偏离 → `BLOCKED_SCOPE_CREEP`；测试
  不足 → `BLOCKED_TEST_FAIL`。
- **下一消费者：** Operator Trial Reviewer。

### 2.8 Operator Trial Reviewer（运营试跑评审者）

- **目的：** 对已实现的构建跑真实运营路径（不只是 pytest）。确认上线的流程就是预览所承诺的。
- **输入：** 已合并 / 可上预发的实现（按切片或在集成时）。
- **必读：** Gate Spec 验收行；原始 Operator Review。
- **产物：** Operator Trial Report（§4）。
- **允许：** 跑真实运营路径（新建 → 生成 V1 → 检查 Shot → 上传 → 再生成 V2 → 对比 →
  确认 → 交付）；核对验收行；现场确认无泄漏。
- **禁止：** 批准部署；替代 Owner 批准；改写 Gate Spec。
- **PASS 标准：** 运营路径按规范走通；验收行现场成立；未观察到泄漏。
- **BLOCK 条件：** 运营路径中断 / 验收失败 → `BLOCKED_OPERATOR_FAIL`，退回 Developer（若
  是流程问题，则退回 Product Planner）。
- **下一消费者：** Owner（合并/部署批准）。

### 2.9 Scribe（记录者）

- **目的：** 记录执行、closure 与 lessons；保持痕迹 on-index。不做任何决策。
- **输入：** closeout 时任一阶段的产物。
- **必读：** 被记录的产物；`docs/README.md` 放置规则。
- **产物：** Closure Report（§4）+ Lessons Entry（`tasks/lessons.md`，见 v2.1 §13）。
- **允许：** docs-only 汇总；索引指针；lessons 沉淀。
- **禁止：** 撰写 authority；改动裁决；改变状态。
- **PASS 标准：** closure 记录每个验收行的最终状态；lessons 条目采用标准格式；指针已加。
- **BLOCK 条件：** 一般无；若证据缺失，索取（不臆造）。
- **下一消费者：** Owner / 未来读者。

### 2.10 Owner（所有者）

- **目的：** 所有风险步骤唯一的最终阶段流转裁决者。裁决；不被任何工具自动越权覆盖。
- **输入：** 相关阶段报告。
- **必读：** 各裁决；如有 divergence 报告。
- **产物：** Owner Decision（记为批准 / 指示；风险流转时回应一份 Owner Decision Request）。
- **允许：** 批准流转；退回；叫停某方向；合并；授权部署；授权 scope / authority 变更。
- **禁止：**（设计上不设限）——但在每个风险流转点，Owner 批准是必需的，不是可选的。
- **PASS 标准：** 决策针对具体流转点被记录。
- **下一消费者：** 该决策所解锁的角色。

> v2.1 的辅助角色（用于 L2 历史扫描的 Librarian、用于未来流水线自动化的 Worker）被认可，但
> 不在本协议版本的 scope 内；Worker 在达到 §7 的自动化成熟度之前保持停用。

---

## 3. 状态机（§2.3）

### 3.1 状态

```
S0  Problem Raised               问题提出
S1  Architect Decision Ready     架构裁决就绪
S2  Product Plan Ready           产品规划就绪
S3  Preview Ready                预览就绪
S4  Operator Review Passed       运营评审通过
S5  Gate Spec Ready              Gate Spec 就绪（READY = §10 签字合并 → gate 打开）
S6  Implementation PR Ready      实现 PR 就绪
S7  Code Review Passed           代码评审通过
S8  Operator Trial Passed        运营试跑通过
S9  Merge / Deploy Approved      合并 / 部署批准（切片/特性的终态）
```

Blocked（解决前为终态）状态：

```
BLOCKED_STATE_DIVERGENCE     仓库状态 ≠ 前提（见 §6）
BLOCKED_SCOPE_CREEP          工作超出授权 scope / forbidden path
BLOCKED_OPERATOR_FAIL        运营无法完成流程
BLOCKED_TEST_FAIL            测试失败 / 覆盖不足
BLOCKED_AUTHORITY_CONFLICT   spec/plan 与 Bucket A 或 wave gate 冲突
```

### 3.2 流转表

图例：**AA** = 允许自动推进（角色无需 Owner 即可继续）；
**OA** = 需要 Owner 批准。

| 从 | 到 | 允许角色 | 必需产物 | AA | OA | 回滚 / 重试目标 |
|----|----|----------|----------|----|----|-----------------|
| S0 | S1 | Architect | Problem Decision Memo | 否 | OA（任务类型 + 准入） | 停留 S0；询问 Owner |
| S1 | S2 | Product Planner | Workflow Plan | AA（撰写） | OA 以*合并*规划 | 误分类则退回 S1 |
| S2 | S3 | Preview Builder | Static Preview + Screenshot | AA | OA 以合并预览 | 规划有缺则退回 S2 |
| S3 | S4 | Operator Reviewer | Operator Review Report = PASS | 否 | —（裁决即闸门） | PASS WITH ISSUES → S2/S3；FAIL → S2 |
| S4 | S5 | Gate Spec Author | Gate Spec（已撰写） | AA（撰写） | **OA —— §10 签字打开 gate** | 未 PASS 则退回 S4 |
| S5 | S6 | Developer | Implementation PR Report（切片） | 否 | **OA —— gate 打开 + 切片顺序** | 按 §3.1 BLOCKED_* |
| S6 | S7 | Code Reviewer | Code Review Report = PASS | AA（执行评审） | —（裁决即闸门） | FAIL → S6（Developer） |
| S7 | S8 | Operator Trial Reviewer | Operator Trial Report = PASS | 否 | —（裁决即闸门） | FAIL → S6 或 S2 |
| S8 | S9 | Owner | Owner Decision = 批准 | 否 | **OA —— 合并 / 部署** | 停在 S8 |
| 任一 | BLOCKED_* | 任一角色 | Divergence / Block Report | — | **OA 以解除** | 在指定重试目标恢复 |

表中固化的硬规则：

- **S3 → S4 仅在 Operator Review `PASS` 时发生。** `PASS WITH ISSUES` **不**自动授权下一
  阶段——它退回去修规划/预览，然后复评（Matrix Script 正因如此跑了两轮）。
- **S4 → S5 是硬前置：** Operator Review PASS 之前不得撰写任何 Gate Spec。
- **S5 → S6 需要 Gate Spec 的 §10 签字已合并**（Architect + Reviewer）——撰写 Gate Spec
  *不*打开 gate；Owner 批准的签字才打开，且仅对第一个切片。
- **S7 → S8 与 S8 → S9 相互独立：** Code Review PASS 绝不替代 Operator Trial，Operator
  Trial PASS 绝不替代 Owner 的合并/部署批准。

---

## 4. 产物契约（§2.4）

每个产物共享一个头部：标题、日期、状态行（DESIGN / PLANNING / GATE / REPORT）、来源输入，
以及一行明确的 authority 声明。标准类型：

| 产物 | 路径约定 | 必需小节 | 最小证据 | 签字 | 消费者 |
|------|----------|----------|----------|------|--------|
| **Problem Decision Memo** | `docs/process/decisions/<feature>_<date>.md`（或内联） | 诊断句；任务类型；复杂度；所适用 authority；准入裁决 | 引用的 authority 文件 | Architect | Product Planner / Developer |
| **Workflow Plan** | `docs/design/<feature>_WORKFLOW_PLAN_<date>.md` | 能力；主流程；高级折叠；诊断；A/B/C/D/E；状态语言；按钮预期；PR 拆分；绝对不能改 | substrate PR 列表；authority 引用 | Product Planner | Preview Builder / Gate Spec |
| **Static Preview** | `docs/design/previews/<feature>_preview.html` | 必需分区；一个真实场景 | 独立渲染；无网络 | Preview Builder | Operator Reviewer |
| **Preview Screenshot** | `docs/design/screenshots/<feature>_preview_<date>.png` | 整页截图 | 与 HTML 一致 | Preview Builder | Operator Reviewer / Owner |
| **Operator Review Report** | `docs/reviews/<feature>_operator_review[_rN].md` | 总体；逐步评审；困惑点；建议改动；裁决 | 逐问题作答 | Operator Reviewer | Owner / Gate Spec |
| **Gate Spec** | `docs/design/<feature>_GATE_SPEC_<date>.md` | 分区规则；状态映射；按钮行为；泄漏清单；验收测试；PR 切片；禁改清单；签字块 | 验收行 A-n；forbidden-path 清单 | Architect + Reviewer（§10） | Developer |
| **Implementation PR Report** | PR 正文 + `docs/execution/<feature>_<slice>_*.md` | scope；文件；测试；边界；验证 | 测试数；diff scope；forbidden 扫描 | Developer | Code Reviewer |
| **Code Review Report** | `docs/reviews/<feature>_code_review[_slice].md` | diff vs spec；forbidden-path；测试；泄漏；裁决 | 扫描输出 | Code Reviewer | Operator Trial Reviewer |
| **Operator Trial Report** | `docs/execution/<feature>_operator_trial_<date>.md` | 路径走查；验收行结果；泄漏检查；裁决 | 现场路径证据 | Operator Trial Reviewer | Owner |
| **Closure Report** | `docs/execution/<feature>_closure_<date>.md` | 落地内容；验收最终状态；冻结复审；签字 | 逐行 PASS/FAIL | Scribe + 签字方 | Owner / 未来 |
| **Lessons Entry** | `tasks/lessons.md`（追加） | 做了什么 / 哪里不顺 / 根因 / 下次怎么改 / 是否更新 WORKFLOW | 一条 | Scribe | 未来读者 |

每个产物的 authority 类别（来自 v2.1 §6.1）是固定的：Bucket A = authority；Gate Spec =
authority（仅本 wave）；Workflow Plan / Preview / Operator Review / Execution Report =
**非** authority。

---

## 5. 验收闸门（§2.5）

对每个受控阶段，`PASS` / `PASS WITH ISSUES` / `FAIL` 含义如下：

| 闸门 | PASS | PASS WITH ISSUES | FAIL |
|------|------|------------------|------|
| **Product Planner Review** | 流程解决了运营问题；已声明非 authority | 解决但有缺口、且这些缺口可被预览检验 → 进入预览，带着 issues | 没解决 / 引入新 IA → 重做规划 |
| **Preview Builder** | 所有分区 + 真实场景；docs-only；干净 | 能渲染但某分区偏薄 → 记录，仍可用 | 无法渲染 / 需要 runtime → BLOCKED_SCOPE_CREEP |
| **Operator Review** | 无需工程师即可操作 | 可操作但仍有具体 must-fix → **退回规划/预览，复评**（不自动推进） | 无法操作 → 重做规划 |
| **Gate Spec Review** | READY：可强制执行、scope 清晰、authority 干净 | 不阻塞合并的轻微清晰度缺口 → 先合并 + 后续跟进 | 不可强制执行 / scope 泄漏 → 重写 |
| **Implementation Review** | diff ⊆ spec；测试覆盖用户路径；干净 | 琐碎小问题 → 合并 + nit 跟进 | spec 偏离 / forbidden-path / 泄漏 → BLOCKED |
| **Code Review** | 无偏离 / 泄漏 / 漂移 | 仅外观问题 | 任何边界破坏 → BLOCKED |
| **Operator Trial** | 现场运营路径按规范走通 | 走通但有轻微外观缺口 → 记录，延后 | 路径中断 / 验收失败 → BLOCKED_OPERATOR_FAIL |
| **Closure** | 每个验收行 PASS + 签字 | 各行 PASS 但有记录在案的延后项 | 仍有未决验收行 → 未关闭 |

**约束性闸门规则（不可让步）：**

1. `PASS WITH ISSUES` **不**自动授权实现。
2. Operator Review `FAIL` 退回 Product Planner 或 Preview Builder——绝不向前。
3. Gate Spec `READY`（签字已合并）是 Developer 写 runtime 代码的前提。
4. Implementation PR `PASS` **不**替代 Operator Trial。
5. Code Review `PASS` **不**替代 Owner 批准。

---

## 6. Divergence 协议（§2.6）

角色必须在阶段进入时做一次状态检查。若观察到的仓库/PR 状态与它被交付的前提冲突，它进入
`BLOCKED_STATE_DIVERGENCE` 并停止。

触发示例（均在 Matrix Script 案例中或其附近观察到）：

```
指令说某 PR 是 OPEN 但 git 显示已 MERGED
假设某规划文档在 main 上，但它缺失（PR 仍 open）
handoff 引用了一个不存在的文件
当前 main 已经包含比指令所假设更晚的 PR
所需 authority 文件缺失
```

要求的响应——**停下并报告，绝不打补丁掩盖**：

```
1. 在当前阶段停止。不要推进。
2. 精确报告 divergence：期望 vs 观察，附 git/PR 证据。
3. 不要修补该差异。不要在错误前提上开 PR。
4. 不要在未合并/缺失的产物之上构建，除非 Owner 明确授权（且仅作为清晰标注的基于分支的
   validation，而非 authority）。
5. 向 Owner 索取更正方向；仅从 Owner 指定的重试目标恢复。
```

先例：当 #216 未合并时，预览任务正确地停止，并仅在 Owner 明确授权后才基于 #216 分支
validation——且不将其视作 main authority。这就是规范的 divergence 响应。

---

## 7. 自动化就绪度（§2.7）

**之后可安全自动化**（只读检测 + 模板化；不改状态）：

```
从 git / gh PR 状态做状态检测（某特性处于哪个 S 状态）
必需文件存在性检查（期望产物是否在其路径存在）
forbidden-path 扫描（git diff --name-only 对照禁改清单）
产物完整性检查（报告中必需小节是否齐备）
报告模板生成（预填标准头部/小节）
流转建议（建议下一个允许的流转 + 由谁执行）
```

**没有 Owner 明确动作就绝不可自动化**（每个风险流转）：

```
合并到 main
部署
scope 扩张
变更 authority（什么是 Bucket A / Gate Spec 管辖什么）
推翻 Operator Review FAIL
从 Gate Spec 跨到 runtime 实现（S5 → S6）
```

设计规则：自动化可以*检测、检查、建议*；它绝不可*决定*一个风险流转。Owner 的批准是自动化
等待的必需输入，而不是它默认假定的东西。（这呼应 v2.1 红线“不得把 AI 自我授权”；Worker
角色在这些只读检查被证实之前保持停用。）

---

## 8. Matrix Script 案例映射（§2.8）

Matrix Script Guided Operator Workflow 案例是工作样例。状态映射：

| 产物 / 事件 | Harness X 状态 | 裁决 |
|-------------|----------------|------|
| 运营抱怨：“能力暴露了，但没产品化” | S0 Problem Raised | — |
| （Architect 定性：流程问题，而非能力问题） | S1 Architect Decision Ready | 流程问题 |
| **#216** Guided Operator Workflow Planning | S2 Product Plan Ready | PASS |
| **#217** Static Preview + Screenshot | S3 Preview Ready | 已构建 |
| **Operator Review Round 1** | S3→（闸门） | **PASS WITH ISSUES**（3 个 must-fix） |
| 预览修订（shot 原因 / 上传→再生成 / 去掉 raw 字段） | S3（重新进入） | 已修复 |
| **Operator Review Round 2** | S4 Operator Review Passed | **PASS** |
| **#218** Guided Operator Workflow Gate Spec | S5 Gate Spec Ready（已撰写） | READY TO MERGE |
| Gate Spec §10 签字（待办） | S5 → gate-open 前置 | `<fill>` |
| **未来 PR-1..PR-6** 实现切片 | S6 → S7 → S8（逐切片） | 未开始 |
| Closeout（PR-6）+ Operator Trial | S8 → S9 | 未开始 |

该案例所演示的关键协议事实：

- Round 1 的 `PASS WITH ISSUES` **没有**推进到 Gate Spec——它退回预览，正符合 §5 规则 1/2。
- Gate Spec（#218）**仅在** Operator Review Round 2 PASS **之后**才撰写——即 S4 → S5 硬前置。
- #216/#217 仍是 **Planning / Review Inputs（NOT authority）**；#218 是一个不 supersede
  Bucket A 的、已接受的实现 gate——§4 的 authority 类别全程成立。
- 通往 runtime 的 gate（S5 → S6）仍然**关闭**：#218 的 §10 签字带 `<fill>` 占位符，因此
  尚未授权任何 Developer 工作。

---

## 9. 模板（§2.9）

简洁、可直接复制。（完整的逐阶段报告模板已在 `Harness-X_WORKFLOW_v2.1.md` §14 中；以下五个
填补协议层面的空缺。）

### 9.1 Role Handoff Packet（角色交接包）

```markdown
# Handoff: <from-role> → <to-role> · <feature> · <date>
- from-state → to-state:
- input artifact (path):
- output artifact expected (path):
- verdict carried: PASS / PASS WITH ISSUES (issues listed) / —
- premise the next role must verify: <要核对的 git/PR 事实>
- forbidden scope reminder: <路径/行为>
```

### 9.2 Divergence Report（偏离报告）

```markdown
# Divergence Report · <feature> · <date>
- phase / role:
- expected premise:
- observed state (evidence):  <git log / gh pr view 输出>
- conflict type: STATE_DIVERGENCE / SCOPE_CREEP / OPERATOR_FAIL / TEST_FAIL / AUTHORITY_CONFLICT
- action taken: STOPPED — 未打补丁，未开 PR
- Owner question: <需要什么方向>
- proposed retry target (for Owner to confirm):
```

### 9.3 Owner Decision Request（Owner 决策请求）

```markdown
# Owner Decision Request · <feature> · <date>
- transition requested: S<x> → S<y>
- why this is a risky (Owner-gated) transition:
- evidence the predecessor verdict is satisfied:
- options: [A approve] [B send back to S<z>] [C stop direction]
- recommendation:
```

### 9.4 Transition Report（流转报告）

```markdown
# Transition Report · <feature> · <date>
- from-state → to-state:
- role acted:
- artifact produced (path):
- auto-advance or Owner-approved:
- acceptance rows touched:
- next allowed transition + role:
```

### 9.5 Closure Report（关闭报告）

```markdown
# Closure Report · <feature> · <date>
- slices landed (PRs):
- acceptance rows: <A-1..A-n 各 PASS/FAIL>
- preserved freezes re-audited:
- operator trial result:
- signoffs: Architect / Reviewer / Operator / Owner
- lessons entry appended: yes/no
- verdict: CLOSED / NOT CLOSED
```

---

## 10. 边界与 authority 说明

- **仅文档（docs-only）。** 本设计不新增自动化代码，不改任何 runtime。
- 它不修改 Matrix Script runtime、`gateway/**`、`schemas/**`、`docs/contracts/**`、
  `artifact_storage.py`、Hot Follow、Digital Anchor 或 Akool/provider 逻辑，且不改
  `CURRENT_ENGINEERING_FOCUS.md`。
- Harness X 是一套**协同协议**，不是项目 authority 的来源。它编排“谁在何时行动”；它绝不
  凌驾于 `ENGINEERING_RULES.md`、wave gate、contract-first 纪律，或 no-private-memory
  规则（CLAUDE.md §3）之上。当它与仓库 authority 冲突时，仓库 authority 优先。
- 本文档本身是 Harness X 设计层的一个产物；把它（或一份 `harness-x/WORKFLOW.md`）提升为
  约束性的流程 authority，是 Owner 的决定，而非合并本文档的副作用。

*协议的意义不是更多角色——而是每个角色只在自己擅长的阶段说话，且在“做错代价高”的地方，没有
角色为自己授权下一步。*
