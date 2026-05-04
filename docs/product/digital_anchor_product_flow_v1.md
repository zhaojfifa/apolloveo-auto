# 数字人口播产线设计（面向结果交付与契约重构）

## 1. 文档目的

本文档用于冻结数字人口播产线在 ApolloVeo 平台中的产品定义、业务流程、任务区与工作台逻辑、交付物设计，以及下一阶段契约重构的对象边界。本文档只讨论产品逻辑与平台归属，不展开工程实现细节。

---

## 2. 产品定位

数字人口播方向当前不应被定义为泛数字人平台，而应定义为 ApolloVeo 中的一条正式结果产线：

**面向个人主播的数字人口播视频生产线。**

这条线的目标不是“生成一个会说话的人”，而是：

- 将脚本 / 文案转化为可执行表达结构；
- 通过角色绑定和场景模板稳定生产成片；
- 支持多语言字幕与配音输出；
- 形成标准化可交付包与可追溯证据。

### 2.1 主结果

- final_video

### 2.2 附属结果

- subtitle
- dubbed_audio
- metadata
- manifest
- pack
- role_usage
- scene_usage
- language_usage

---

## 3. 平台归属

数字人口播产线应被理解为：

### 3.1 一条结果产线

它与 Hot Follow、Localization、Script Video 一样，属于面向 final video 的业务执行单元。

### 3.2 一条依赖公共供给能力的产线

它依赖但不等同于：

- 角色资产
- 声音预设
- 语言能力
- 场景模板
- 执行路由
- 后处理与交付能力

因此，这条线不能做成“角色页 + 模型页 + 场景页”的拼盘，而必须是：

**一条以成片为统一目标的标准视频生产线。**

---

## 4. 核心业务逻辑

这条线的核心逻辑应为：

**输入归一化 → 内容结构生成 → 场景计划 → 角色 / 声音绑定 → 多语言与字幕 → 合成任务 → 质检 → 交付包**

### 4.1 内容先结构化，再渲染

脚本 / 文案不是终态输入，而是生产原料。系统需要先把它转换为：

- 讲解提纲
- 段落逻辑
- 节奏安排
- 强调点
- 语言输出要求

### 4.2 场景模板是核心控制点

对个人主播类视频，真正决定可复用性和规模化的，不只是角色本身，而是：

- scene plan
- scene template
- layout
- background style
- information zone
- reference style policy

### 4.3 数字人是表达载体，不是产品本体

产品本体不是单独的角色资产，而是：

- 内容结构
- 场景模板
- 角色绑定
- 语言输出
- 交付包

这些对象的组合体。

---

## 5. 任务区设计

任务区是产线任务管理视角，不是角色库或素材库。

### 5.1 任务阶段

建议按以下阶段展示：

- 输入已提交
- 内容结构已生成
- 场景计划已生成
- 角色 / 声音已绑定
- 多语言版本生成中
- 合成完成
- 可交付
- 已归档

### 5.2 任务卡片核心字段

- 任务标题
- Role Profile
- Scene Template
- Target Language
- 当前版本状态
- 当前阻塞项
- 交付包状态
- 最近更新

### 5.3 任务区与资产区边界

任务区只展示“当前任务使用了什么角色 / 模板 / 声音”，
不承担长期资产管理职责。

角色库、模板库、声音预设库都应归到供给层或资产层。

---

## 6. 工作台设计

数字人口播工作台应重于矩阵脚本线，因为它需要同时支持：

- 内容结构确认
- 角色与声音绑定
- 场景模板装配
- 语言输出控制
- 预览与校对

### 6.1 工作台模块

#### A. 角色绑定面

- 选择 Role Profile
- 选择形象风格
- 选择声音 preset
- 表达风格 / 情绪控制

#### B. 内容结构面

- Outline
- 段落结构
- 强调点
- 节奏控制

#### C. 场景模板面

- Scene Plan
- 布局模式
- 背景模板
- 信息区 / 标题区 / 辅助区

#### D. 语言输出面

- Target Language
- Subtitle Strategy
- Terminology Rules
- 多版本语言切换

#### E. 预览与校对面

- 试听
- 视频预览
- 字幕校对
- 表达与节奏复核
- 质检与诊断

---

## 7. 交付中心设计

数字人口播的交付中心必须按 Delivery Pack 组织，而不是只按 mp4 文件组织。

### 7.1 标准交付物

- final_video
- subtitle
- dubbed_audio
- metadata
- manifest
- pack
- role_usage
- scene_usage
- language_usage

### 7.2 交付规则

建议冻结以下原则：

- 主交付物是成片
- 附属交付物必须可追溯
- manifest 是交付证据的一部分
- pack 是协作接口，不是可有可无的附件
- 历史成功产物与当前尝试必须分开解释

### 7.3 交付中心职责

- 展示最终可发布结果
- 展示语言版本与音频版本
- 展示交付包与 manifest
- 展示角色 / 场景 / 语言使用记录
- 承担回填与发布结果记录

---

## 8. 工具嵌入策略（后端供给视角）

### 8.1 输入理解层

- Gemini API：脚本理解、参考表达理解、场景标签、风险提示

### 8.2 角色与表达层

当前阶段不把“复杂数字人能力平台化”前置。

建议先以：

- 角色资产 + 声音 preset + 场景模板
- 形成可执行组合

### 8.3 音频与语言层

- Azure：TTS / 多语言配音
- 字幕与翻译链：作为 Language Plan 执行能力

### 8.4 视频与场景生成层

- 视频生成 / 场景增强工具作为 Worker Profile 供给
- 前台不直接暴露“选模型”逻辑
- 场景模板与参考图 / 参考视频能力按 Scene Plan 驱动

### 8.5 后处理与交付层

- ffmpeg：合成、字幕烧录、打包、交付整形
- 外部编辑工具：作为 Pack 下游精修出口

---

## 9. 契约对象设计（下一阶段重构重点）

这条线建议先冻结 6 个平台级对象。

### 9.1 Role Profile Contract

定义角色：

- role_id
- appearance_profile
- expression_profile
- voice_preset_ref
- language_defaults
- brand_constraints

### 9.2 Presentation Outline Contract

定义表达结构：

- title
- opening
- sections
- emphasis
- rhythm_profile
- cta

### 9.3 Scene Plan Contract

定义场景模板：

- scene_template_id
- layout_mode
- visual_slots
- background_policy
- info_zone_policy
- reference_style_policy

### 9.4 Speaker Plan Contract

定义讲解与声音执行：

- voice_provider
- voice_preset
- speech_speed
- emotion_profile
- lipsync_policy
- bgm_policy

### 9.5 Language Plan Contract

定义语言输出：

- target_language
- subtitle_strategy
- terminology_rules
- variant_languages
- helper_translation_policy

### 9.6 Delivery Pack Contract

定义交付：

- primary_result
- secondary_results
- manifest_required
- pack_required
- publishable
- review_required_items

---

## 10. 一期范围建议

数字人口播一期不做“大而全数字人平台”，建议只做：

### 场景 1：个人主播讲解视频
- 固定角色
- 固定场景模板
- 单主题讲解
- 多语言输出

### 场景 2：产品介绍型口播
- 简单信息区
- 统一模板
- 一主角 + 一内容结构

### 场景 3：培训 / 说明型口播
- 段落式讲解
- 字幕与术语一致性要求更高

当前不建议前置：

- 高复杂度企业知识视频
- 多角色互动视频
- 大规模场景自动生成
- 高复杂数字人能力集合平台

---

## 11. 产品判断

数字人口播产线应被正式定义为：

**面向个人主播的脚本驱动数字人口播成片线。**

它必须：

- 以 final video 为统一主结果；
- 以内容结构、场景模板、角色绑定、语言输出、交付包为核心对象；
- 以后端工具供给方式嵌入能力；
- 以前台结构化配置而不是模型选择来组织工作台；
- 以 Delivery Pack 作为协作与交付接口。

这条线的成功标准，不是“数字人看起来多炫”，而是：

- 是否能稳定出成片；
- 是否能跨语言稳定输出；
- 是否能形成标准交付包；
- 是否能为后续更复杂数字人能力留出清晰平台边界。

