# Matrix Script Product-Flow Design v1 — 矩阵脚本产线设计（面向结果交付与契约重构）

> **Status (Recovery PR-5, 2026-05-04): line-specific execution authority.**
>
> Per Recovery PR-5 §"Product-Flow Enforcement Order", this document is
> elevated from design notes to **binding line-specific execution
> authority** for the Matrix Script production line. Future Task Area /
> Workbench / Delivery Center implementations on the Matrix Script line
> MUST map to the §5 / §6 / §7 modules below — task-area card fields
> (§5.3), workbench modules A / B / C / D / E (§6.1), delivery-center
> standard deliverables (§7.1) and publish rules (§7.2) — not only to
> the packet / contract / runtime truth. "Operator-ready" cannot be
> claimed for Matrix Script unless those modules are actually present
> on the operator-visible surfaces.
>
> The top-level
> [`apolloveo_2_0_top_level_business_flow_v1.md`](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
> remains the **factory-wide abstract flow** (task → line → workbench
> → delivery → publish → archive). This document is the **line-
> specific concretization** of that flow for Matrix Script. Where the
> two diverge for a Matrix-Script-only concern, this document wins on
> Matrix-Script surfaces.
>
> Authority chain:
> - Decision: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
> - Action: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`
> - Recovery PR-5 gate: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md`
> - Top-level flow: `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
> - Sibling line authority: `docs/product/digital_anchor_product_flow_v1.md`

## 1. 文档目的

本文档用于冻结“矩阵脚本产线”的产品定义、业务流程、任务区与工作台设计、交付逻辑，以及下一阶段契约重构的对象边界。当前阶段目标不是追求最强单模型能力，而是在已具备 Gemini API、Akool、Azure、ffmpeg 等能力基础上，先搭建稳定的整体生产流程，支撑矩阵化短视频内容的批量生产、可复盘和可交付。

---

## 2. 产品定位

矩阵脚本产线是 ApolloVeo 中一条正式结果产线。

它的核心目标不是“生成一个视频”，而是：

- 将一个内容主题转化为多条可发布短视频版本；
- 以统一脚本结构驱动批量生成；
- 形成可复盘的变体与交付包；
- 支撑账号矩阵的测试、分发与迭代。

### 2.1 主结果

- final_video

### 2.2 附属结果

- subtitle
- audio
- copy_bundle
- scene_pack（可选 / 非阻塞）
- metadata
- manifest
- publish_status
- variation_config

---

## 3. 当前阶段约束

### 3.1 当前目标

- 先打通脚本驱动的整体生产流程；
- 先形成任务区、工作台、交付中心统一逻辑；
- 先以契约驱动组织步骤和交付；
- 不把前端做成“选模型页”；
- 不把工具能力散落为大量 if/else。

### 3.2 当前不追求

- 不追求覆盖所有视频生成模型；
- 不追求复杂多 Agent 协作；
- 不追求所有场景一次做全；
- 不把 Scene Pack 作为主链阻塞项；
- 不把视频编辑深度能力前置到一期。

---

## 4. 核心业务逻辑

矩阵脚本产线的核心业务逻辑应为：

**主题/目标 → 脚本结构化 → 变体配置 → 生成任务 → 校对与筛选 → 成片交付 → 发布回填 → 复盘沉淀**

### 4.1 内容结构标准

所有矩阵脚本默认遵循统一结构：

1. Hook（前 3 秒吸引）
2. Body（中间展示结果 / 过程 / 对比）
3. CTA（结尾引导评论 / 私信 / 点击）

### 4.2 变体维度

每个核心脚本可挂多个变体，至少包括：

- Hook 变体
- 背景画面变体
- 配音变体（男 / 女 / 情绪）
- 字幕语言变体
- 视觉风格变体
- 节奏快慢变体

### 4.3 运营目标

这条线不是为“单条精品”服务，而是为：

- 跑量测试
- 内容配方验证
- 账号矩阵分发
- 快速复盘与下轮优化

---

## 5. 任务区设计

任务区是任务管理视角，不是创作细节页。

### 5.1 任务层级

建议采用三层：

1. 脚本任务（母任务）
2. 变体任务（子任务）
3. 发布任务（渠道 / 账号任务）

### 5.2 任务状态

建议任务区重点展示以下业务状态：

- 已创建
- 待配置
- 生成中
- 待校对
- 成片完成
- 可发布
- 已回填
- 已归档

### 5.3 任务卡片核心字段

- 主题 / 目标
- 核心脚本名称
- 当前变体数
- 可发布版本数
- 已发布账号数
- 当前最佳版本
- 最近一次生成时间
- 当前阻塞项

---

## 6. 工作台设计

工作台是创作与校对视角，重点是结构、变体、预览与交付确认。

### 6.1 工作台模块

#### A. 脚本结构区

- 标题
- Hook
- Body points
- CTA
- 关键词 / 禁用词

#### B. 变体配置区

- 开头钩子
- 背景画面
- 配音 preset
- 字幕语言
- 节奏档位
- 特效模板

#### C. 预览对比区

- 版本 A / B / C 并排预览
- 差异项提示
- 推荐版本标识

#### D. 校对区

- 字幕校对
- 配音试听
- 文案 / 标签校对
- CTA 校对

#### E. 质检与诊断区

- 风险提示
- 合规提示
- 时长 / 清晰度 / 字幕可读性
- 产物状态与 ready gate 解释

---

## 7. 交付中心设计

交付中心必须围绕“面向发布的结果交付”设计。

### 7.1 标准交付物

- final.mp4
- subtitles（.srt / .vtt）
- audio（.wav / .mp3）
- copy_bundle（标题 / hashtags / CTA / 评论关键词）
- metadata / manifest
- scene_pack（可选）
- publish_status

### 7.2 发布规则

建议冻结以下规则：

- 成片完成 + 发布必需项就绪 = 可发布
- Scene Pack 可为非阻塞项
- 历史成功产物与当前尝试必须分开解释
- publish 只消费 authoritative projection，不得自行发明 ready 状态

### 7.3 回填对象

- 发布渠道
- 账号 ID
- 发布时间
- 发布链接
- 发布状态
- 指标入口（预留）

---

## 8. 工具嵌入策略（面向供给，不面向前台）

### 8.1 输入理解层

- Gemini API：参考视频理解、内容标签、脚本结构辅助、风险提示

### 8.2 视频生成层

当前阶段不以高成本 Seedance 作为默认主引擎。

建议：

- 先以现有可控工具能力搭建流程骨架；
- 视频生成能力按 Worker / Tool Routing 在后端装配；
- 生成层对前端暴露为“生成模式”，而不是“模型选择”。

### 8.3 特效 / 角色增强层

- Akool API：角色替换、换脸、人物增强场景
- 可挂接特效型场景模板，如参考图驱动、局部替换、角色强化

### 8.4 音频与本地化层

- Azure：TTS / 多语言配音
- 字幕生成 / 翻译 / 辅助翻译能力作为语言计划供给

### 8.5 后处理与交付层

- ffmpeg：关键帧提取、字幕烧录、合成、切分、打包
- CapCut / 外部编辑工具：作为 Pack 的下游精修出口

---

## 9. 契约对象设计（下一阶段重构重点）

### 9.1 Input Contract

定义输入：

- goal
- audience
- topic
- script_text
- target_language
- reference_assets
- forbidden_rules

### 9.2 Outline Contract

定义内容结构：

- hook
- body_points
- cta
- rhythm_profile
- emphasis_terms

### 9.3 Variant Contract

定义变体：

- hook_variant
- background_variant
- voice_variant
- subtitle_variant
- effect_variant
- pacing_variant

### 9.4 Tool Routing Contract

定义工具装配：

- understanding_tool
- video_gen_tool
- enhancement_tool
- audio_tool
- post_tool
- fallback_chain

### 9.5 Deliverable Contract

定义交付：

- primary_result
- secondary_results
- publish_required_items
- optional_items
- manifest_required

### 9.6 Publish Feedback Contract

定义回填：

- channel
- account_id
- publish_url
- publish_status
- metrics_stub
- next_iteration_hint

---

## 10. 一期范围建议

建议一期只做三类标准场景：

### 场景 1：矩阵脚本变体线
- 一个脚本，多版本输出
- 快速测试 Hook / 字幕 / 配音 / 背景差异

### 场景 2：上传素材执行线
- 素材 + 文案 → 多版本成片

### 场景 3：轻特效脚本线
- 参考图 / 参考视频增强
- 简单场景替换 / 角色强化 / 特效模板

---

## 11. 产品判断

矩阵脚本产线应被正式定义为：

**面向矩阵运营与快速试错的脚本驱动成片产线。**

它必须：

- 面向 final video 结果组织；
- 面向标准交付包组织；
- 面向契约对象组织；
- 面向工具适配而不是工具暴露组织；
- 面向后续数据回填与内容配方沉淀组织。

这条线的成功标准，不是“调用了多少模型”，而是：

- 能否稳定生成多版本；
- 能否清晰解释状态；
- 能否形成可发布交付物；
- 能否为下一轮内容优化提供结构化依据。