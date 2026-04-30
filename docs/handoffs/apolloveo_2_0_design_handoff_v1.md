# ApolloVeo 2.0 · 设计交付 Handoff v1

**来源**：Chief Architect · ApolloVeo 2.0 Overall Master Plan v1.0（Part III · UI 设计师交付清单）
**日期**：2026-04-24
**状态**：架构师派发稿 —— 供 UI 设计负责人直接执行
**上位参考**：
- 《ApolloVeo2.0_Claude架构对齐评审与整体Plan.md》评审稿 v1.0
- ApolloVeo 2.0 Overall Master Plan v1.0（架构师收口版）
- 六件 factory-generic 契约：`docs/contracts/factory_*_contract_v1.md`

---

## Context

ApolloVeo 2.0 要求 UI 从"按工具组织"转为"按工厂职责组织"，固定为五个面：**任务区 / 工作台 / 交付中心 / 素材供给区 / 工具后台**。设计侧的目标不是输出新的工具页，而是画出这五个面的信息架构与三类主 surface 的低保真结构，确保任一像素都能映射到 contract object，不发明状态真相、不直连供应商。

---

## 交付物 1 · 工厂信息架构图（IA Diagram）

**期望形态**：
- 一张总览图（可放 Figma / Whimsical / draw.io / 手绘扫描），导出 `docs/design/apolloveo_2_0_factory_ia_v1.png` + 源文件
- 附一页 `docs/design/apolloveo_2_0_factory_ia_v1.md` 说明图上每个节点与数据流向

**必须体现**：
- 五面关系：任务区 / 工作台 / 交付中心 / 素材供给区 / 工具后台
- 跨面跳转路径（哪些面之间允许导航、哪些禁止）
- 数据流向：每个面消费 / 产出哪类 contract object
- 明确标注每面**不得**承担的职责（参考 Master Plan §8.1）

**验收标准（DoD）**：
- 图上每一个 UI 实体旁标注其消费的 contract（如"任务列表 ← factory_input + job state"）
- 不出现未映射到 contract 的实体
- 工具后台与工作台之间的分界线被明确画出（防止后续混用）

**期限**：1 周（目标日：2026-05-01）

---

## 交付物 2 · 三类主 Surface 低保真布局

**期望形态**：
- 三张低保真线框图（低保真 = 不做视觉风格，只画区块 + 字段位置）
- 落位 `docs/design/surfaces/task_area_v1.png` / `workbench_v1.png` / `delivery_center_v1.png`（源文件同目录）
- 各自附一页 Markdown 说明区块到 contract object 的映射

### 2.1 任务区（Task Area）
**必备区块**：
- 任务列表（列字段：task_id / line_id / created_at / current_state / publishable）
- 进线选择器（选哪条产线：Hot Follow / Matrix Script / Digital Anchor）
- 状态视觉：`blocked` / `ready` / `publishable` 三态明确区分
- 入口按钮：新建任务、进入工作台、跳交付中心

**映射 contract**：`factory_input_contract_v1` + line packet binding + job state

**禁止**：列中出现"选模型 / 选 vendor"字段；任务区承担 asset 或 tool 管理。

### 2.2 工作台（Workbench）
**必备区块**（四分栏或等价布局）：
- content_structure 面板（消费 `factory_content_structure_contract_v1`）
- scene_plan 面板（消费 `factory_scene_plan_contract_v1`）
- audio_plan 面板（消费 `factory_audio_plan_contract_v1`）
- language_plan 面板（消费 `factory_language_plan_contract_v1`）
- line-specific 侧栏（Matrix Script → variation 面板；Digital Anchor → role/speaker 面板；Hot Follow → subtitle authority 面板）

**映射 contract**：上述四件 factory-generic + line packet 的 `line_specific_refs[]`

**禁止**：工作台内发明状态（不得出现"已完成/待处理"等不由 artifact facts 推出的标签）；不得直连供应商。

### 2.3 交付中心（Delivery Center）
**必备区块**（三段式）：
- `final_video`（主交付，突出显示）
- `required_deliverables`（字幕 / 音轨 / 封面 / metadata，阻塞项）
- `scene_pack`（非阻塞项，视觉上与 required 明显区分）
- 发布按钮的启用条件视觉化："final_video.ready && required_deliverables.ready" 才可发布

**映射 contract**：`factory_delivery_contract_v1` + manifest + publish status

**禁止**：scene_pack 挡住发布；交付中心自建"补齐状态"语义。

**验收标准（DoD，三个 surface 共用）**：
- 每个区块都标注其消费的 contract object（在说明 md 中以表格呈现）
- 不出现未映射到 contract 的字段
- 所有"状态显示"必须注明来源于 L2 artifact facts 或 L3 current attempt，而非独立逻辑

**期限**：1 周（目标日：2026-05-01）

---

## 交付物 3 · 两条新线在工作台的差异化模块草图

**期望形态**：
- 两张低保真模块草图，落位 `docs/design/surfaces/workbench_matrix_script_variation_panel_v1.png` / `workbench_digital_anchor_role_speaker_panel_v1.png`
- 可作为交付物 2 的 workbench surface 侧栏插件形态呈现

### 3.1 Matrix Script · variation 面板
- 变体矩阵视图（variation_axis 作为行/列）
- 单变体详情（文案、分镜、音轨差异）
- 归因标签（每条变体的 attribution_id）
- 发布回填区（显示已发布变体的回流指标）

**映射**：Matrix Script packet 的 `variation_plan` + `publish_feedback`（由产品交付物 1 定义）

### 3.2 Digital Anchor · role/speaker 面板
- 角色选择 + 角色预览
- 场景绑定（引用 scene_plan）
- 声线配置（speaker_plan 字段）
- 多语言策略矩阵（language × subtitles × dub）

**映射**：Digital Anchor packet 的 `role_profile` + `speaker_plan` + `language_output`（由产品交付物 2 定义）

**验收标准（DoD）**：
- 两个面板均消费对应 line packet 字段，不发明新字段
- 产品 packet schema 未冻结时允许使用占位字段，但需在说明中标注"待产品 schema 冻结后对齐"

**期限**：1.5 周（目标日：2026-05-05，晚于交付物 1、2，依赖产品 schema 初稿）

---

## 不需要交付的内容（明确划线）

- ❌ 模型选择页 / 供应商切换页 / 能力对比页
- ❌ 工具后台的视觉化管理页（P1 由工程直出基础形态，不由 UI 主导）
- ❌ 单功能弹窗 / 按钮级别的高保真
- ❌ 任何视觉风格 / 配色方案（本次只做低保真结构）

---

## 设计侧必须消费的既有契约（请先读）

| 契约 | 路径 | 消费目的 |
|---|---|---|
| factory_input_contract_v1 | `docs/contracts/factory_input_contract_v1.md` | 任务区字段源 |
| factory_content_structure_contract_v1 | `docs/contracts/factory_content_structure_contract_v1.md` | 工作台区块 1 |
| factory_scene_plan_contract_v1 | `docs/contracts/factory_scene_plan_contract_v1.md` | 工作台区块 2 + Digital Anchor 引用 |
| factory_audio_plan_contract_v1 | `docs/contracts/factory_audio_plan_contract_v1.md` | 工作台区块 3 |
| factory_language_plan_contract_v1 | `docs/contracts/factory_language_plan_contract_v1.md` | 工作台区块 4 |
| factory_delivery_contract_v1 | `docs/contracts/factory_delivery_contract_v1.md` | 交付中心字段源 |
| hot_follow_projection_rules_v1.md | `docs/contracts/hot_follow_projection_rules_v1.md` | Hot Follow workbench 投影参考 |

---

## 铁律（设计侧红线）

1. **UI 不能发明状态真相** —— 所有状态显示必须指向 L2 artifact facts 或 L3 current attempt
2. **UI 不能直接承接供应商差异** —— 前台永远不出现 vendor_id
3. **UI 只能消费 contract objects 与 derived gates** —— 不得自创 presentation-only 字段
4. **Scene Pack 必须非阻塞** —— 交付中心视觉上必须明确区分阻塞项与非阻塞项
5. **任务区 ≠ 素材库 ≠ 工具后台** —— 三者互不越界

任一红线被触碰 → 设计稿回退修订。

---

## 路由与答疑

- **contract 字段含义问题** → 架构师
- **line-specific 字段问题** → 产品经理（需先有 packet schema）
- **交互可行性问题** → 工程负责人
- **评审节奏**：2026-05-01 初稿 → 2026-05-05 架构师 + 产品 + 工程三方评审 → 2026-05-08 冻结低保真 v1

---

## 里程碑对齐

- 2026-05-01：交付物 1、2 初稿
- 2026-05-05：交付物 3 初稿（依赖产品 schema）
- 2026-05-08：低保真 v1 冻结，进入 P1~P2 工程实现参考基线
- 后续高保真 / 视觉稿不在本次 handoff 范围

---

**签署**：Chief Architect（L5），2026-04-24 派发

---

## 附 · v1.1 补注（2026-04-25，不修订上文、不影响节点）

Master Plan 升级至 v1.1，对本 handoff 三份交付物追加一条**前后台硬边界要求**，不改交付时间、不改区块结构、不改红线条数。

**新红线 6（叠加在原 5 条之上）**：UI 五面与后台供给层之间存在硬边界，前台代码**不得直连**任一捐赠源（SwiftCraft）helper、provider client 或 worker adapter；前台只消费 ApolloVeo gateway 暴露的 contract objects 与 derived gates。

落到设计交付物：

- **交付物 1（IA 图）**：图上必须明确表达"UI 五面 ↔ gateway 契约对象"的单向数据流，不得画出任一前台节点直达 `gateway/app/services/providers/*`、`workers/adapters/*`、`media/*` 的连线
- **交付物 2（三类主 surface 低保真）**：任务区 / 工作台 / 交付中心的任何区块都不得显示 `vendor_id` / `model_id` / `provider_name` / `engine_id` 字段；所有"能力"以 capability kind（understanding / subtitles / dub / video_gen / avatar / face_swap / post_production / pack / variation / speaker / lip_sync）形式出现
- **交付物 3（差异化模块）**：Matrix Script variation 面板 / Digital Anchor role/speaker 面板同样遵循前后台硬边界；不得在前台引入任何 SwiftCraft 命名空间或 donor 模块路径

校验路径：P0 Guardrail Test Suite 将通过静态扫描前端源码强制执行 —— 出现 `swiftcraft` 字符串、`gateway/app/services/providers/*`、`workers/adapters/*` import 的设计实现立即阻塞。设计稿不会被静态扫描，但评审会基于该规则验收。

**v1.1 补注签署**：Chief Architect（L5），2026-04-25
