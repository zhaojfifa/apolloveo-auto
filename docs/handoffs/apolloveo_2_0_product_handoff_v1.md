# ApolloVeo 2.0 · 产品交付 Handoff v1

**来源**：Chief Architect · ApolloVeo 2.0 Overall Master Plan v1.0（Part III · 产品经理交付清单）
**日期**：2026-04-24
**状态**：架构师派发稿 —— 供产品经理直接执行
**上位参考**：
- 《ApolloVeo2.0_Claude架构对齐评审与整体Plan.md》评审稿 v1.0
- ApolloVeo 2.0 Overall Master Plan v1.0（架构师收口版）
- 六件 factory-generic 契约：`docs/contracts/factory_*_contract_v1.md`

---

## Context

P2 阶段要求 Matrix Script / Digital Anchor 两条线冻结为 line packet。packet 不是 wireframe、不是功能规格、不是 PPT；它是**可被 validator 机械校验的 schema 文件**，也是两条新线能否进入 runtime 的唯一真相接口。本次产品交付的目的是让工程侧能在 P1~P2 阶段直接用产品产出的 schema 跑通 packet envelope + onboarding gate。

---

## 交付物 1 · Matrix Script Line Packet Schema 草案

**期望形态**（两件套，必须同时具备）：
1. `docs/contracts/matrix_script/packet_v1.md`（契约叙述 + 字段表）
2. `schemas/packets/matrix_script/packet.schema.json`（JSON Schema）

**必备字段**：
- `script` / `outline`（主题、分镜大纲、核心卖点）
- `variation_plan`（变体数量、变体轴——如文案风格 × 镜头顺序 × 音轨、变体归因维度）
- `copy_bundle`（标题 / 副标题 / 正文 / 话题标签集合，含语言版本）
- `publish_feedback`（发布结果回填字段：曝光 / CTR / 完播 / 归因 variation_id）
- `result_packet_binding`（一次任务产出 N 条变体成片如何绑定）

**必须声明**：
- `generic_refs[]`：引用哪几件 factory-generic 契约（至少命中 `factory_input` / `factory_content_structure` / `factory_delivery`）
- `capability_plan[]`：声明所需能力（understanding / copy_generation / variation / subtitles / dub / pack），**只声明 capability kind，禁止出现 vendor_id**

**验收标准（DoD）**：
- schema 可被 JSON Schema 校验器加载、无语法错误
- 至少 1 条样例 packet instance 通过 schema 校验
- 每个字段附一句"为什么需要"的业务理由（不是操作说明）
- 明确标注 `required` vs `optional`
- 向上 `generic_refs` 指向的每件契约都真实存在于 `docs/contracts/`

**期限**：1 周（目标日：2026-05-01）

**禁止项**：
- 不得出现 vendor / model 名称
- 不得发明状态真相（禁止定义新的 `status` / `ready` 字段）
- 不得复刻 factory-generic 同形对象（需引用而非重写）

---

## 交付物 2 · Digital Anchor Line Packet Schema 草案

**期望形态**（两件套，必须同时具备）：
1. `docs/contracts/digital_anchor/packet_v1.md`
2. `schemas/packets/digital_anchor/packet.schema.json`

**必备字段**：
- `role_profile`（角色外形 / 人设 / 语气 / 风格锚点 / 引用素材集）
- `scene_plan_binding`（**引用** `factory_scene_plan_contract_v1`，只声明 line-specific 增量，如固定机位 / 固定背景 / 固定 role 占位）
- `speaker_plan`（声线 / 语速 / 情绪曲线 / 多语种策略）
- `language_output`（目标语言集合 × 每语言的字幕 / 配音策略）
- `delivery_pack_binding`（**引用** `factory_delivery_contract_v1`，只声明 line-specific 增量，如 role/scene/language 绑定成片命名）

**必须声明**：
- `generic_refs[]`：至少命中 `factory_scene_plan` / `factory_audio_plan` / `factory_language_plan` / `factory_delivery`
- `capability_plan[]`：声明 avatar / speaker / subtitles / dub / lip_sync / pack 等能力（同样只声明 capability kind）

**验收标准（DoD）**：
- 同交付物 1 的 schema 规范
- `scene_plan_binding` / `delivery_pack_binding` 必须证明是**引用**而非**复刻**（向 validator 暴露 `generic_ref` 路径）
- 至少 1 条样例 packet 通过校验

**期限**：1 周（目标日：2026-05-01）

**禁止项**：
- 不得复刻 `factory_scene_plan` / `factory_delivery` 字段
- 不得出现具体数字人供应商名称
- 不得定义 runtime 字段（runtime 是 P3 事，packet 只管声明）

---

## 交付物 3 · Asset Supply 需求矩阵

**期望形态**：
- `docs/product/asset_supply_matrix_v1.md`（单文件、纯 Markdown 表格）

**表结构**：
| 产线 | asset 类型 | 必备标签 | 质量阈值 | 使用场景说明 |
|---|---|---|---|---|
| Hot Follow | broll / reference_video | topic / language / style | 1080p / ≥10s / score ≥0.6 | 参考视频驱动的解析入口 |
| Matrix Script | broll / product_shot / background / template | topic / style / variation_axis | （由产品填） | 变体成片的素材供给 |
| Digital Anchor | role_ref / background / template | role_id / scene / language | （由产品填） | 角色/场景绑定的口播 |

上表为模板，产品需补全 Matrix Script 与 Digital Anchor 行，并可按需细分行。

**验收标准（DoD）**：
- 每条产线至少声明 3 类必需 asset
- 每类 asset 的标签维度与 `asset.tags_json` 字段对齐（参考 Master Plan §7）
- 质量阈值为可量化值（分辨率 / 时长 / fps / 评分），不可用"高质量"等模糊词

**期限**：1 周（目标日：2026-05-01，与交付物 1、2 并行）

---

## 不需要交付的内容（明确划线）

- ❌ 新的"模型选择"页面 / 供应商对比表 / 能力对比矩阵
- ❌ 单功能弹窗 / 按钮级交互规格
- ❌ wireframe 形态的 Packet（Packet 必须是 schema 文件而非界面草图）
- ❌ 任何命名具体 vendor 的需求文档

---

## 产品侧必须消费的既有契约（请先读）

| 契约 | 路径 | 消费目的 |
|---|---|---|
| factory_input_contract_v1 | `docs/contracts/factory_input_contract_v1.md` | 任务入口字段集合 |
| factory_content_structure_contract_v1 | `docs/contracts/factory_content_structure_contract_v1.md` | 内容结构字段集合 |
| factory_scene_plan_contract_v1 | `docs/contracts/factory_scene_plan_contract_v1.md` | 场景计划字段集合（Digital Anchor 必引） |
| factory_audio_plan_contract_v1 | `docs/contracts/factory_audio_plan_contract_v1.md` | 音轨计划字段集合 |
| factory_language_plan_contract_v1 | `docs/contracts/factory_language_plan_contract_v1.md` | 语言输出字段集合 |
| factory_delivery_contract_v1 | `docs/contracts/factory_delivery_contract_v1.md` | 交付字段集合（两条线必引） |
| hot_follow_line_contract.md | `docs/contracts/hot_follow_line_contract.md` | 作为 packet 结构参考样板 |

---

## 路由与答疑

- **契约边界 / 字段归属问题** → 架构师（L5 Chief Architect）
- **runtime 可行性问题** → 工程负责人（P1 阶段负责人）
- **素材供给接入问题** → 架构师 + Asset Supply owner（待 P1 指派）
- **交付物评审门禁**：每份 schema 必须通过 packet envelope validator（P1 产出）方可合入 main

---

## 里程碑对齐

- 2026-05-01：三份交付物初稿到架构师桌上
- 2026-05-08：架构师评审 + 一轮修订
- 2026-05-15：schema 冻结（可被 P1 validator 消费）
- P2 起点依赖本次交付，延期直接阻塞 Matrix Script / Digital Anchor 进线

---

**签署**：Chief Architect（L5），2026-04-24 派发

---

## 附 · v1.1 补注（2026-04-25，不修订上文、不影响节点）

Master Plan 升级至 v1.1，对本 handoff 三份交付物追加两条**校验前置要求**，不改交付时间，不改字段表，不改禁止项。

1. **packet schema 必须满足 `factory_packet_validator_rules_v1.md` 全部 5 条规则**（R1 generic_refs 路径合法 / R2 不复刻 generic 同形 / R3 capability_plan 仅声明 capability kind 不出现 vendor / R4 JSON Schema Draft 2020-12 可加载 / R5 不出现 status/ready/done 等真相字段）。  
   交付物 1 与交付物 2 在评审时直接以该 5 条规则作为过审条件。
2. **packet envelope 结构必须遵循 `factory_packet_envelope_contract_v1.md` 五项 E 规则**（E1 line_id 唯一 / E2 generic_refs 仅指 factory-generic / E3 binds_to 必须解析 / E4 ready_state 是唯一允许的就绪字段 / E5 capability kind 闭集）。

校验路径：架构师评审会以 `gateway/app/services/packet/validator.py` 的输出（P1 交付物）为准；产品交付时不需要自行运行 validator，但 schema 需可被运行，违反任一规则即视为未达 DoD。

**v1.1 补注签署**：Chief Architect（L5），2026-04-25
