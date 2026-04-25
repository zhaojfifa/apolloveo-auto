# ApolloVeo 2.0 Overall Master Plan · v1.1（Donor 整合 + 12 问收口）

**角色**：Chief Architect（L5）
**版本**：v1.1（在 v1.0 基础上吸收两份新输入）
**日期**：2026-04-25
**状态**：架构师收口版 —— supersedes Master Plan v1.0 in `~/.claude/plans/`，作为 repo 内权威母计划
**新增输入（本版次吸收）**：
- 《ApolloVeo 2.0 产品与架构对齐稿 v1（评审版）》—— 产品与架构联合对齐稿，固化产品总定位 / 三条线产品定义 / 五面 IA / 三大主 surface / 6 件 generic objects / packet strategy / 状态显示红线
- 《SwiftCraft 纳入 Apollo 2.0 统一规划说明》—— 把 SwiftCraft 正式定位为后台能力供给与实现参考层，明确可吸收 / 不吸收清单与目标目录

**未变更项（从 v1.0 继承，本版不重述）**：
- Hot Follow 冻结基线、四层状态模型、六件 factory-generic contracts 既有内容
- 后台十域命名、UI 五面与 contract 映射既有规则
- P0 Guardrail Test Suite、P3 onboarding 候选优先级（Matrix Script 先 / Digital Anchor 后）

---

## Part I · 架构师对 12 问的收口表态

### A · SwiftCraft 后台能力供给

| # | 议题 | 表态 | 边界 |
|---|---|---|---|
| 1 | 把 SwiftCraft 正式纳入"后台能力供给与实现参考层" | **通过** | 仅作为 capability donor + reference repo；不引入其 `TaskService / TaskStore / TaskRecord / scenario truth / fallback ASR-as-truth` 任一对象。Apollo 仍是宿主。 |
| 2 | 在 2.0 总图中新增 Provider / Worker / Media / Artifact / Env 五类供给层 | **有条件通过（不另起一层）** | 不引入新顶层"五类供给层"概念；将其映射回 v1.0 既有的**后台十域**：Provider→`capability_adapters`；Worker→`worker_execution_envelope`；Media→新增子域 `media_processing`；Artifact/Manifest→`delivery_response_modeling` 下子域 `manifest_shaping`；Env→`ops/env/`（独立运维域，不入十域）。详见 Part IV 的物理映射表。 |
| 3 | 前台五面 IA 与后台供给层保持硬边界 | **通过且加固** | UI 五面只与 contract objects + derived gates 对话，**禁止**任一前台调用直达 SwiftCraft helper / provider adapter；越界视同 v1.0 §2 第 5 条禁止回退项。 |

### B · Contract 与 Packet

| # | 议题 | 表态 | 边界 |
|---|---|---|---|
| 4 | Matrix Script / Digital Anchor 的 packet 是否足以作为 runtime 准入真相接口 | **当前不足，需补强** | 产品对齐稿 §6 已给出 strategy，但**两份 packet schema 仍未交付**（产品 Handoff 目标日 2026-05-01）。准入真相接口须三件套：契约 md + JSON Schema + 至少 1 条样例 instance + onboarding gate validator 通过。任一缺失即不得进 P3 runtime。 |
| 5 | factory-generic objects 是否还需补充或收缩 | **维持 6 件，不收缩；另在 generic 层加 1 件 envelope（不计入 6 件）** | 6 件（input / content_structure / scene_plan / audio_plan / language_plan / delivery）保持冻结；新增 `factory_packet_envelope_contract_v1`（v1.0 已要求，本版重申），它是装订规则、不是第 7 件 generic object。 |
| 6 | generic refs 与 line packet 的 validator 规则是否还需更明确 | **需更明确，增独立规则文档** | P1 必交付 `docs/contracts/factory_packet_validator_rules_v1.md`，规则包含：① `generic_refs[]` 必须指向 `docs/contracts/factory_*_contract_v1.md` 真实存在的文件；② line packet 不得复刻 generic 同形字段（声明 `extends` / `binds_to` 而非重写）；③ `capability_plan[]` 元素必须为 capability kind（`understanding / subtitles / dub / video_gen / avatar / face_swap / post_production / pack / variation / speaker / lip_sync`），禁止出现 `vendor_id / model_id`；④ packet schema 必须可被 JSON Schema Draft-2020-12 校验器加载；⑤ packet 不得新增 `status / ready / done` 任一状态字段。 |

### C · Backend Donor

| # | 议题 | 表态 | 边界 |
|---|---|---|---|
| 7 | SwiftCraft 能力吸收边界是否足够清楚 | **概念清楚，需正式化为契约文件** | swift_craft 文档 §3、§4、§5 已划界；P1 必交付 `docs/donor/swiftcraft_donor_boundary_v1.md`，正式列出**可吸收清单**（ffmpeg_localization / subtitle_builder / media / akool_client / vendor_asset_bridge / action_replica_prompt 等）+ **不吸收清单**（TaskService / TaskStore / TaskRecord / scenario truth / monolithic orchestration 等）+ **每条吸收项的 license 与代码归属备注**。 |
| 8 | repo 中是否先预留 services/media、services/artifacts、workers/adapters、ops/env 等宿主 | **同意预留，但按 Apollo-actual 路径建立，不照搬 SwiftCraft 命名** | Apollo 现有代码根为 `gateway/app/services/`，因此预留路径为：`gateway/app/services/media/`、`gateway/app/services/artifacts/`、`gateway/app/services/manifests/`、`gateway/app/services/workers/adapters/<vendor>/`、`gateway/app/services/providers/`、`ops/env/`。在 P1 Donor Phase 起点统一 `mkdir` + 占位 `__init__.py` + README，**不在 P0 提前建空目录**（避免裸结构污染）。 |
| 9 | 是否先补 donor capability mapping 文档，再开始工程实施 | **通过且必需（前置卡点）** | 任何 SwiftCraft → Apollo 的代码迁移**必须先有** `docs/donor/swiftcraft_capability_mapping_v1.md`，逐条映射：SwiftCraft 模块路径 → Apollo 目标路径 → 对应 Apollo contract / capability kind → license / 改写要点。无映射条目，工程不得动手。 |

### D · 工程实施

| # | 议题 | 表态 | 边界 |
|---|---|---|---|
| 10 | 同意按"产品/设计冻结 → donor 吸收冻结 → runtime 接线"推进 | **通过，已对齐 v1.0 P0~P3 节奏** | 在 v1.0 P1（Factory Generic 收口）与 P2（Line Packet 收口）之间插入 **P1.5 Donor Phase**（详见 Part III），完整顺序：P0 守基线 → P1 generic 基座 → **P1.5 donor 吸收冻结** → P2 line packet 冻结 → P3 首条新线 runtime。 |
| 11 | 同意当前不整体并入 SwiftCraft backend | **通过且不可逾越** | 不允许任一 PR 将 SwiftCraft `backend/` 整体目录拷入 Apollo；只允许按 capability mapping 文档逐模块吸收并 Apollo-native 化（重写、包裹或引用）。违反者视为契约破坏。 |
| 12 | 同意在实现前，先把 donor 只定义为 capability donor，而非系统宿主 | **通过** | Apollo 是唯一系统宿主与真相源；SwiftCraft 永远是捐赠源。任何吸收代码进入 Apollo 后，必须落入 Apollo-native contract / worker profile / skills bundle，**禁止保留 SwiftCraft 自有的 task/state/delivery 语义**。 |

**12 问总裁定**：Q1、Q3、Q9、Q10、Q11、Q12 直接通过；Q2 收紧为"不另起一层、映射回十域"；Q4 标注"当前不足、待 packet 交付"；Q5 维持 6 件 + 加 envelope；Q6、Q7、Q8 通过且需补正式化文档 / 路径预留方案。

---

## Part II · SwiftCraft Donor Integration Strategy

### II.1 定位

SwiftCraft 在 ApolloVeo 2.0 中的**唯一**身份：
- ✅ Capability Donor（能力捐赠源）
- ✅ Implementation Reference（实现参考库）
- ❌ Independent Backend Service（不接入为外部服务）
- ❌ Parallel Task System（不引入并行任务系统）
- ❌ Truth Source（不成为业务真相宿主）

### II.2 三类吸收形态

| 形态 | 含义 | 代码处理 | 使用场景 |
|---|---|---|---|
| **Pattern Reference**（模式参考） | 仅借鉴组织方式 / 边界划分 | 不复制代码，写入 ADR / docs | provider adapter boundary、env 分层、polling/retry pattern |
| **Helper Absorption**（helper 吸收） | 低风险纯能力函数 | 重写或包裹后落入 Apollo 目录 | media helpers、subtitle builder、ffmpeg helpers、vendor_asset_bridge |
| **Adapter Absorption**（adapter 吸收） | provider 适配 | 必须包裹在 Apollo capability adapter 接口下 | Fal / Akool / Azure / faster-whisper / Gemini translation |

### II.3 吸收的不可逾越红线

1. 任何吸收代码必须放进 Apollo `gateway/app/services/...` 或 `ops/env/...`，**禁止**保留 `swiftcraft.*` 命名空间
2. 吸收 provider adapter 时，必须**先**写 Apollo 侧 capability adapter 接口（基于 `gateway/app/services/providers/` 与 `gateway/app/services/workers/adapters/`），再把 SwiftCraft 实现包裹进去
3. 不得搬入 SwiftCraft 的 `TaskService / TaskStore / TaskRecord / run_config_snapshot / scenario truth`
4. 不得将 SwiftCraft 的 fallback ASR/TTS 写法当作真相 —— Apollo 的真相由 artifact facts 派生
5. 吸收 manifest / artifact shaping 时，必须最终投影到 `factory_delivery_contract_v1`，**禁止**形成第二套 delivery 语义

### II.4 三类新线对 Donor 的主消费点

| 新线（Apollo） | Donor 主贡献（SwiftCraft） | Apollo 落位 |
|---|---|---|
| Hot Follow（reference） | ASR / Gemini translation / Azure TTS / ffmpeg render / subtitle helpers | `gateway/app/services/media/`、`gateway/app/services/providers/azure/`、`gateway/app/services/providers/gemini/` |
| Matrix Script | copy generation pattern、variation prompt 组织、publish feedback shaping | `gateway/app/services/planning/`（已存在）、`skills/matrix_script/`（待建） |
| Digital Anchor | Fal / Kling / WAN / OmniHuman adapter 模式、Action Replica prompt、identity anchor / motion preserve / camera preserve 封装 | `gateway/app/services/workers/adapters/<vendor>/`、`skills/digital_anchor/`（待建） |
| Swap 家族（后续线，本版不展开） | Akool adapter / segmentation / quality 思路；保持 swap_face vs swap_scene 分离 | `gateway/app/services/workers/adapters/akool/` |

---

## Part III · 更新后的分阶段路线图（P0 → P3，新增 P1.5）

> **总顺序**：P0 守基线 → P1 generic 基座 → **P1.5 Donor 吸收冻结** → P2 line packet 冻结 → P3 首条新线 runtime onboarding

### P0 · 守基线（0~2 周，2026-04-25 起算）
不变（继承 v1.0）。Guardrail Test Suite v1 + 八条禁止回退项契约测试 + structure guard 进 CI 门禁。

### P1 · Factory Generic 基座（2~6 周）
v1.0 已定义 + 本版增补：
- 增补 ① `factory_packet_envelope_contract_v1.md` + schema + validator
- 增补 ② `factory_packet_validator_rules_v1.md`（Q6 要求的独立规则文档）
- 增补 ③ Onboarding gate（消费 validator 输出 + Hot Follow reference evidence）
- 不变：capability registry / adapter 骨架、asset supply 基础表 + promote flow、UI 五面 IA + 后台十域骨架

### P1.5 · Donor 吸收冻结阶段（5~8 周，与 P1 后段重叠）

**目标**：把 SwiftCraft 从"捐赠候选"变成"已知边界 + 已映射目录 + 已签 license"的可控 donor，工程吸收的预备工作完成、但**尚未开吸收 PR**。

**P1.5 进度（截至 2026-04-25 v1.1 签署日）**：必交付物 1~3、5 已落盘；必交付物 4（Capability Adapter 接口骨架代码）保持 P1.5 卡点要求，待 P1 generic 基座代码骨架阶段实施。

**必交付物（P1.5 卡点）**：
1. ✅ [docs/donor/swiftcraft_donor_boundary_v1.md](docs/donor/swiftcraft_donor_boundary_v1.md)（Q7 要求，已落盘）
   - 可吸收清单（每条附 SwiftCraft 文件路径 + 改写策略）
   - 不吸收清单
   - License / commercial scope / attribution 要求
2. ✅ [docs/donor/swiftcraft_capability_mapping_v1.md](docs/donor/swiftcraft_capability_mapping_v1.md)（Q9 要求，前置卡点，已落盘）
   - 一行一映射：`SwiftCraft 路径 → Apollo 目标路径 → 对应 contract / capability kind → 改写要点`
   - 行号体系：M-01..M-05 / A-01..A-05 / P-01..P-03 / V-01..V-02 / E-01..E-09 / R-01..R-04 / O-01..O-03
3. ✅ Apollo-side 宿主目录预留（Q8 要求，已落盘 + README）
   - [gateway/app/services/media/](gateway/app/services/media/README.md)
   - [gateway/app/services/artifacts/](gateway/app/services/artifacts/README.md)
   - [gateway/app/services/manifests/](gateway/app/services/manifests/README.md)
   - [gateway/app/services/workers/adapters/](gateway/app/services/workers/adapters/README.md)
   - [gateway/app/services/providers/](gateway/app/services/providers/README.md)
   - [gateway/app/services/packet/](gateway/app/services/packet/README.md)
   - [gateway/app/services/capability/](gateway/app/services/capability/README.md)
   - [gateway/app/services/asset/](gateway/app/services/asset/README.md)
   - [skills/digital_anchor/](skills/digital_anchor/README.md)
   - [skills/matrix_script/](skills/matrix_script/README.md)
   - [ops/env/](ops/env/README.md)（独立运维域，不入十域）
   - 每个目录附 `__init__.py`（除 `ops/env/`）+ `README.md`（说明该目录消费哪类 contract、不做什么、absorption 前置条件）
4. ⏳ Capability Adapter 接口骨架（代码层级，P1 内实施；P1.5 卡点要求**先于** SwiftCraft 任一 adapter 吸收完成）
   - 至少：`AdapterBase`、`UnderstandingAdapter`、`SubtitlesAdapter`、`DubAdapter`、`PackAdapter`、`VideoGenAdapter`、`AvatarAdapter` 接口契约
   - 落位：[gateway/app/services/capability/](gateway/app/services/capability/README.md)（host 已预留）
5. ✅ Donor ADR：[docs/adr/ADR-donor-swiftcraft-capability-only.md](docs/adr/ADR-donor-swiftcraft-capability-only.md)（裁定 Q11/Q12 决议，已落盘）

**P1.5 不交付物**：任一 SwiftCraft 代码迁移 PR（吸收动作延后至 P2 起点之后）。

### P2 · Line Packet 冻结（6~10 周）
v1.0 已定义 + 本版增补：
- 增补 ① 三线 packet 必须通过 `factory_packet_validator_rules_v1` 完整校验
- 增补 ② Donor 吸收 PR 在本阶段开始（**前提**：P1.5 卡点全数通过 + capability mapping 文档冻结），按"helper → provider adapter → skills 策略"顺序吸收，每个 PR 单独提交，每个 PR 必须引用 capability mapping 文档对应行
- 不变：Hot Follow packet v1 向上适配、Matrix Script / Digital Anchor 两份 packet 冻结、reference evidence 产出

### P3 · 首条新线 Runtime（10~16 周）
不变（继承 v1.0）。Matrix Script 优先；Digital Anchor 仍为 packet-only。

---

## Part IV · 物理映射（Apollo-actual 路径）

### IV.1 后台供给层 → Apollo-actual 路径

| 评审稿 / Donor 文档命名 | Apollo-actual 路径 | 主消费 contract |
|---|---|---|
| Provider Supply | `gateway/app/services/providers/<vendor>/` | capability_adapters 注册 |
| Worker Adapter Supply | `gateway/app/services/workers/adapters/<vendor>/` | worker_gateway_contract |
| Media Processing Supply | `gateway/app/services/media/`（新增） | factory_audio_plan / factory_scene_plan / factory_delivery |
| Artifact / Manifest Supply | `gateway/app/services/artifacts/` + `gateway/app/services/manifests/`（新增） | factory_delivery_contract（manifest 子集） |
| Skills 策略层 | `skills/<line>/`（已部分存在：`skills/hot_follow/`） | skills_runtime_contract |
| Env / Runtime / Storage Supply | `ops/env/`（新增）+ 已有 `ops/checks/` | 不入十域；运维独立 |
| Capability Registry / Routing | `gateway/app/services/capability/registry.py` + `routing.py`（新增） | capability_routing_policy |
| Asset Supply / Broll Library | `gateway/app/services/asset/`（新增） | asset_supply_contract |
| Packet Envelope / Validator | `gateway/app/services/packet/envelope.py` + `validator.py`（新增） | factory_packet_envelope_contract |
| Onboarding Gate | `gateway/app/services/packet/onboarding_gate.py`（新增） | onboarding_gate_contract |

### IV.2 v1.0 中"`gateway/<domain>/`"占位的更正

v1.0 §3、§6、§7、§8.2 中以 `gateway/<domain>/` 表达的物理落位，**全部更正**为 `gateway/app/services/<domain>/`，与 Apollo 现有代码层级对齐（`gateway/app/services/` 是真实 services 根）。本版起，所有 ADR / 契约 / handoff 文档统一使用更正后路径。

---

## Part V · 本版触发的新增/修订文档清单

P1 / P1.5 必交付文档（在已有 v1.0 清单上**新增**）：

1. ✅ [docs/contracts/factory_packet_envelope_contract_v1.md](docs/contracts/factory_packet_envelope_contract_v1.md)（v1.0 已列，本版重申；含 E1~E5 envelope 结构规则与 capability_plan 收口）
2. ✅ [docs/contracts/factory_packet_validator_rules_v1.md](docs/contracts/factory_packet_validator_rules_v1.md)（**本版新增**，Q6 强制；R1~R5 规则 + PacketValidationReport 输出形态）
3. ✅ [docs/donor/swiftcraft_donor_boundary_v1.md](docs/donor/swiftcraft_donor_boundary_v1.md)（**本版新增**，Q7 强制；§3 可吸收 / §4 不吸收 / §5 attribution header 规范）
4. ✅ [docs/donor/swiftcraft_capability_mapping_v1.md](docs/donor/swiftcraft_capability_mapping_v1.md)（**本版新增**，Q9 强制，工程吸收前置卡点；§0 commit pin 表 + 行 ID 体系 M/A/P/V/E/R/O）
5. ✅ [docs/adr/ADR-donor-swiftcraft-capability-only.md](docs/adr/ADR-donor-swiftcraft-capability-only.md)（**本版新增**，Q11/Q12 决议）
6. ✅ 修订：[docs/handoffs/apolloveo_2_0_product_handoff_v1.md](docs/handoffs/apolloveo_2_0_product_handoff_v1.md)（v1.1 注脚已附：packet schema 须同时满足 R1~R5 与 E1~E5；不影响 5-1 节点）
7. ✅ 修订：[docs/handoffs/apolloveo_2_0_design_handoff_v1.md](docs/handoffs/apolloveo_2_0_design_handoff_v1.md)（v1.1 注脚已附：新增红线 6 = UI 不直连任一 SwiftCraft helper / provider；不影响 5-8 节点）

> **签署日落盘说明（2026-04-25）**：本清单第 1~5 项 5 份新增文档均已物化为 repo 文件；第 6、7 项注脚已就位。Part III P1.5 卡点除"Capability Adapter 接口骨架代码"外全部完成。

> **注**：6、7 两份修订采用"补注脚不重发"模式，避免冲击产品 / 设计已经在执行的 5-1 / 5-8 节点。

---

## Part VI · 状态显示红线（与产品对齐稿 §7 对账）

产品对齐稿 §7 列出的 5 条状态显示红线，与 v1.0 §2 八条禁止回退项**完全相容**，本版作如下对账（无新增、无冲突）：

| 产品对齐稿 §7 红线 | v1.0 §2 对应禁令 |
|---|---|
| 红线 1：UI 不能发明状态真相 | 禁令 1（L4 不得回推 L2）+ 禁令 2（compatibility 字段不得覆盖 artifact facts） |
| 红线 2：工作台不能自创完成度语义 | 禁令 1 子集 |
| 红线 3：交付中心不能发明补齐状态 | 禁令 2 子集 |
| 红线 4：Scene Pack 非阻塞 | v1.0 Part II §5 Delivery Readiness Gate 显式规定 |
| 红线 5：任务区 / 素材区 / 工具后台三者不越界 | 禁令 8（Artifact 不污染 Asset）+ 本版 Q3 加固（前后台硬边界） |

P0 Guardrail Test Suite 已覆盖前 4 条；本版要求 P0 收尾前**追加** 1 条 contract test 覆盖红线 5（前台不调 SwiftCraft helper / provider、任务区不出现 asset 管理 API 调用）。

---

## Part VII · 验收标准更新（衔接 v1.0 §11）

在 v1.0 §11 的阶段 evidence 表上**追加**：

| 阶段 | 本版追加 evidence | 截至 2026-04-25 状态 |
|---|---|---|
| P0 | 红线 5 contract test 全绿（前台不直达 donor / supply 层） | 待办（P0 收尾追加） |
| P1 | `factory_packet_validator_rules_v1` 文档冻结；validator 在至少 1 条样例 packet（Hot Follow packet v1）上跑通校验全部 5 条规则 | 文档冻结 ✅ ；Hot Follow sample validator 跑通待办 |
| P1.5 | donor boundary + capability mapping 两份文档冻结；Apollo-side 宿主目录建立完成；capability adapter 接口骨架合入 main；ADR-donor 进 `docs/adr/` | 文档冻结 ✅ ；宿主目录预留 ✅ ；ADR 进 `docs/adr/` ✅ ；adapter 接口骨架代码待办（P1 阶段） |
| P2 | 每条 SwiftCraft 吸收 PR 引用 capability mapping 行号；任一 PR 不得保留 `swiftcraft.*` 命名空间；任一 PR 不得搬入禁列对象 | 待办（P2 起执行） |
| P3 | 不变（v1.0 既定） | 待办 |

---

## Part VIII · 架构师最终裁定（v1.1）

1. **通过** SwiftCraft 作为 Apollo 2.0 唯一指定的 capability donor；**禁止**整体并入 backend / 引入并行任务系统 / 引入第二套 delivery 语义
2. **通过** 12 问全部裁定（Q2 收紧、Q4 待 packet 交付、Q5/6/7/8/9 各加正式化文档要求）
3. **锁定** 顺序：P0 → P1 → **P1.5（Donor 吸收冻结）** → P2 → P3；任一阶段 evidence 不齐不得跨阶段晋升
4. **锁定** 物理路径：所有 v1.0 中 `gateway/<domain>/` 表达统一更正为 `gateway/app/services/<domain>/`；新增的 5 类供给层映射回**后台十域 + ops/env 独立运维域**，不另起一层
5. **锁定** 产品对齐稿 §7 五条状态红线为 P0 Guardrail Test 必覆盖项
6. **锁定** "donor 永远是捐赠源、Apollo 永远是宿主"为不可逾越红线，违反视同 OpenClaw 写真相 / Skills 越界发明状态同等严重

---

## Part IX · v1.1 签署日 Evidence Index（2026-04-25）

> 本节给出 v1.1 所有规范性引用的具象文件指针；每条目同时是 v1.1 自身的"已落盘"凭证。任一引用变更（重命名 / 删除 / 路径迁移），必须同步更新本节。

### IX.1 契约层（generic + 装订）

- [docs/contracts/factory_packet_envelope_contract_v1.md](docs/contracts/factory_packet_envelope_contract_v1.md) — packet envelope 字段 + E1~E5 结构规则
- [docs/contracts/factory_packet_validator_rules_v1.md](docs/contracts/factory_packet_validator_rules_v1.md) — R1~R5 校验规则 + PacketValidationReport
- 既有 6 件 generic contracts（v1.0 已冻结，本版未触动）：[factory_input](docs/contracts/factory_input_contract_v1.md) · [factory_content_structure](docs/contracts/factory_content_structure_contract_v1.md) · [factory_scene_plan](docs/contracts/factory_scene_plan_contract_v1.md) · [factory_audio_plan](docs/contracts/factory_audio_plan_contract_v1.md) · [factory_language_plan](docs/contracts/factory_language_plan_contract_v1.md) · [factory_delivery](docs/contracts/factory_delivery_contract_v1.md)

### IX.2 Donor 治理层

- [docs/donor/swiftcraft_donor_boundary_v1.md](docs/donor/swiftcraft_donor_boundary_v1.md) — §3 permitted (M/A/P/V/E/R/O) · §4 forbidden · §5 attribution header · §7 前后台隔离
- [docs/donor/swiftcraft_capability_mapping_v1.md](docs/donor/swiftcraft_capability_mapping_v1.md) — §0 commit pin · §2 行 ID 表 · §3 row lifecycle
- [docs/adr/ADR-donor-swiftcraft-capability-only.md](docs/adr/ADR-donor-swiftcraft-capability-only.md) — Q11/Q12 决议 ADR

### IX.3 宿主目录预留（P1.5 Q8）

| Apollo 路径 | 主消费 contract | 主对应 mapping 行 |
|---|---|---|
| [gateway/app/services/media/](gateway/app/services/media/README.md) | factory_audio_plan / factory_scene_plan / factory_delivery | M-01..M-05 |
| [gateway/app/services/artifacts/](gateway/app/services/artifacts/README.md) | factory_delivery（artifact 子集） | V-01..V-02 |
| [gateway/app/services/manifests/](gateway/app/services/manifests/README.md) | factory_delivery（manifest 子集） | manifest_shaping 子域 |
| [gateway/app/services/providers/](gateway/app/services/providers/README.md) | capability_adapters 注册 | P-01..P-03 |
| [gateway/app/services/workers/adapters/](gateway/app/services/workers/adapters/README.md) | worker_gateway_contract | E-01..E-07（vendor 适配段） |
| [gateway/app/services/packet/](gateway/app/services/packet/README.md) | factory_packet_envelope_contract + onboarding_gate | — |
| [gateway/app/services/capability/](gateway/app/services/capability/README.md) | capability_routing_policy | — |
| [gateway/app/services/asset/](gateway/app/services/asset/README.md) | asset_supply_contract | — |
| [skills/digital_anchor/](skills/digital_anchor/README.md) | skills_runtime_contract | E-01, E-02, E-04..E-07 |
| [skills/matrix_script/](skills/matrix_script/README.md) | skills_runtime_contract | （无直接 donor 映射） |
| [ops/env/](ops/env/README.md) | 独立运维域，不入十域 | O-01..O-03 |

### IX.4 Handoffs（v1.1 footnoted）

- [docs/handoffs/apolloveo_2_0_product_handoff_v1.md](docs/handoffs/apolloveo_2_0_product_handoff_v1.md) — v1.1 注脚要求 packet schema 满足 R1~R5 + E1~E5
- [docs/handoffs/apolloveo_2_0_design_handoff_v1.md](docs/handoffs/apolloveo_2_0_design_handoff_v1.md) — v1.1 注脚新增红线 6（UI 不直连 donor / supply 层）

### IX.5 v1.0 母计划历史指针

- [~/.claude/plans/users-tylerzhao-downloads-apolloveo2-0-atomic-goose.md](../../.claude/plans/users-tylerzhao-downloads-apolloveo2-0-atomic-goose.md) — v1.0 历史参考（路径表达 `gateway/<domain>/` 已被 v1.1 Part IV 更正为 `gateway/app/services/<domain>/`）

---

## Verification（v1.1 本身的校验方式）

- **产品侧**：Handoff v1（2026-05-01 节点）不变；交付的 packet schema 须满足 `factory_packet_validator_rules_v1` 全部 5 条规则
- **设计侧**：Handoff v1（2026-05-08 节点）不变；五面 IA 图须明确表达"UI 不直连 donor / supply 层"
- **工程侧**：
  - 2 周内（P0 收尾）追加红线 5 contract test
  - 6 周内完成 P1 + 同步启动 P1.5 文档冻结
  - 8 周内 P1.5 卡点全过；P2 起开始 SwiftCraft 吸收 PR
- **契约侧**：本版列出的 5 份新增文档（Part V 第 1~5 条）必须在 P1.5 结束前全部进 `main`
- **红线侧**：任一 PR 出现 `from swiftcraft.*` import / 任一前台模块 import donor 模块 / 任一 contract 复刻 generic 同形字段 → 立即阻塞合入

---

**签署**：Chief Architect（L5），ApolloVeo 2.0 Overall Master Plan v1.1 —— 2026-04-25
**生效**：本版生效后，v1.0 仅保留为历史参考；后续所有派生计划（产品 / 设计 / 工程）以 v1.1 为唯一上位母契约。
