\# ApolloVeo Operator-Visible Surfaces 需求与设计 v1

\#\# 1\. 文档目标

本稿用于冻结 ApolloVeo 当前阶段的 operator-visible surfaces 需求与设计范围，作为评审基线。    
当前目标不是扩更多能力，不是做模型控制台，也不是直接进入全面平台化实现，而是先把三条产线在前台/后台的可见面收口为统一、可试用、可反馈的结构。ApolloVeo 2.0 的上位定位已经明确为：按产线组织、以成片交付为统一目标的 AI 内容生产工厂，而不是按工具或模型组织的平台。

\---

\#\# 2\. 设计总原则

\#\#\# 2.1 按工厂职责组织，不按工具组织  
页面体系固定围绕五个面组织：  
\- 任务区  
\- 工作台  
\- 交付中心  
\- 素材供给区  
\- 工具后台

Board、New Tasks 属于任务区；Workbench 与两个 line-specific panels 属于工作台；Delivery / 发布页属于交付中心；B-roll / 素材页属于素材供给区；工具页与后台管理控制页属于工具后台。

\#\#\# 2.2 UI 只消费 truth，不发明 truth  
所有状态显示必须来自：  
\- L2 Artifact Facts  
\- L3 Current Attempt  
\- authoritative projections / derived gates

不得由页面自行推断新的业务真相，不得用 presentation-only 字段覆盖事实层。

\#\#\# 2.3 Asset 与 Artifact 严格分离  
\- Asset Library：长期复用资产  
\- Artifact Store：任务产物与中间结果

任务产物不能自动污染资产库；必须通过 promote 才能晋级为可复用资产。B-roll / 素材页必须服从这条原则。

\#\#\# 2.4 前台不承接 provider 差异  
前台不出现 vendor/model/provider 选择，不做供应商切换页。能力供给通过 capability plan、tool registry、worker profile 在后端装配。

\#\#\# 2.5 接口层物理隔离 Provider 信息  
所有面向 Board、New Tasks、Workbench、Delivery、B-roll / 素材页 的后端返回 payload，默认不得包含以下字段：

\- vendor\_id  
\- model\_id  
\- provider\_id  
\- engine\_id  
\- raw provider route  
\- 任何仅用于后端 tool registry / worker routing 的内部执行标识

前台只允许消费：  
\- contract objects  
\- line packet fields  
\- L2 artifact facts  
\- L3 current attempt  
\- authoritative projections / derived gates

如后端运行时确需保留 provider 信息，也必须：  
\- 仅保留在后台管理控制页或内部 debug/admin payload 中  
\- 不进入 operator-visible payload  
\- 不作为前台状态或行为判断依据

设计含义：  
前台不仅“不展示 provider”，而且后端默认“不给 provider”。通过接口层物理隔离，强制执行“运营只面向业务结果，不面向供应商差异”的原则。

\---

\#\# 3\. 页面体系总览

当前 operator-visible surfaces 收口为以下 8 个对象：

1\. Board 页    
2\. New Tasks 页    
3\. Workbench 页    
4\. Delivery / 发布页    
5\. B-roll / 素材页    
6\. 工具页    
7\. 后台管理控制页    
8\. 两个 line-specific panels    
   \- Matrix Script variation panel    
   \- Digital Anchor role/speaker panel

\---

\#\# 4\. 三条产线的统一承载要求

\#\#\# 4.1 Hot Follow  
Hot Follow 已从救火线回到正式产线治理，当前前台重点不是增加更多按钮，而是正确展示：  
\- 历史成功交付物  
\- 当前 attempt  
\- subtitle authority  
\- helper 后的 materialization  
\- re-dub / re-compose 状态解释

Hot Follow 的前台价值核心是解释 artifact facts、current attempt 与 operator summary 的关系。

\#\#\# 4.2 Matrix Script  
Matrix Script 是面向矩阵运营与快速试错的脚本驱动成片线，重点承载：  
\- 一稿多变体  
\- 结构化预览与筛选  
\- 交付与发布回填  
\- 变体归因与复盘

页面需要支撑脚本结构、变体配置、版本对比、交付与回填。

\#\#\# 4.3 Digital Anchor  
Digital Anchor 是面向个人主播的脚本驱动数字人口播成片线，重点承载：  
\- role 绑定  
\- speaker / language / scene template  
\- delivery pack  
\- 多语言成片与可追溯证据

页面需要支撑 role、speaker、scene、language 等结构化对象。

\---

\#\# 5\. 页面需求与设计

\#\# 5.1 Board 页

\#\#\# 页面定位  
运营总览与任务分流页。

\#\#\# 页面目标  
让运营快速看见：  
\- 当前有哪些任务  
\- 任务属于哪条产线  
\- 哪些任务 blocked / ready / publishable  
\- 哪些任务最近更新  
\- 哪些任务可以进入工作台或交付中心

\#\#\# 核心区块  
\- 任务列表  
\- line 过滤器  
\- 状态总览条  
\- 阻塞项提示  
\- 快捷入口：进入工作台 / 交付中心 / 新建任务

\#\#\# 核心字段  
\- task\_id  
\- line\_id  
\- title / summary  
\- created\_at / updated\_at  
\- current\_state  
\- publishable  
\- current blocker  
\- latest deliverable signal

\#\#\# 设计要求  
\- 按 line 聚合，但不按工具聚合  
\- 状态只做展示，不做推导  
\- 不出现 vendor/model/provider 字段  
\- 不承担素材、工具、后台管理职责

\---

\#\# 5.2 New Tasks 页

\#\#\# 页面定位  
统一任务创建入口，按产线发起任务。

\#\#\# 页面目标  
支持三条线标准化进线：

\#\#\#\# Hot Follow  
\- reference URL / reference video  
\- target language  
\- 字幕/配音策略说明  
\- helper 翻译入口说明

\#\#\#\# Matrix Script  
\- goal  
\- audience  
\- topic  
\- script\_text  
\- target\_language  
\- reference\_assets  
\- forbidden\_rules

\#\#\#\# Digital Anchor  
\- script / copy  
\- role\_profile\_ref  
\- scene\_binding\_hint  
\- speaker / language 初始偏好

\#\#\# 页面结构  
\- 第一步：选择产线  
\- 第二步：显示对应 line 的输入模块  
\- 第三步：校验输入完整性  
\- 第四步：创建任务并进入任务区 / 工作台

\#\#\# 设计要求  
\- line-first，而不是 tool-first  
\- 所有字段尽量映射到 factory input contract 或 line packet  
\- 不暴露高级工具路由与供应商差异

\---

\#\# 5.3 Workbench 页

\#\#\# 页面定位  
创作、校对、状态解释与最小操作中心。

\#\#\# 通用结构  
\- content\_structure 面板  
\- scene\_plan 面板  
\- audio\_plan 面板  
\- language\_plan 面板  
\- line-specific 侧栏 panel

\#\#\# 通用目标  
支持：  
\- 内容结构确认  
\- 语言与音频调整  
\- 预览与校对  
\- 交付前判断  
\- line-specific 信息操作

\#\#\# Hot Follow 工作台

\#\#\#\# 重点区块  
\- subtitle authority 区  
\- current subtitle source  
\- current dub / compose legality  
\- 历史成功成片 vs 当前 attempt  
\- helper 后状态解释  
\- operator summary / advisory

\#\#\#\# 设计要求  
\- 清楚区分“已有交付物”和“当前重试状态”  
\- 不用 L4 文案回推事实层  
\- 当前 attempt 必须可见

\#\#\# Matrix Script 工作台

\#\#\#\# 重点区块  
\- 脚本结构区（Hook / Body / CTA）  
\- 变体配置区  
\- A/B/C 预览对比区  
\- 字幕 / 配音 / CTA 校对区  
\- ready gate / 风险提示 / 质检区

\#\#\#\# 设计要求  
\- 变体操作必须可视化  
\- 多版本差异必须可解释  
\- 不把 Scene Pack 作为主链阻塞项

\#\#\# Digital Anchor 工作台

\#\#\#\# 重点区块  
\- role 绑定区  
\- speaker 配置区  
\- scene template 装配区  
\- language output 区  
\- 试听 / 预览 / 字幕校对区

\#\#\#\# 设计要求  
\- role、speaker、scene、language 是主对象  
\- 不做“角色页 \+ 模型页 \+ 场景页”的拼盘式页面  
\- 前台只做结构化配置，不做工具选择

\#\#\# Workbench 红线  
\- 不发明状态  
\- 不直连供应商  
\- 不承担资产库管理  
\- 不承担工具后台管理

\---

\#\# 5.4 Delivery / 发布页

\#\#\# 页面定位  
围绕交付与发布的结果中心。

\#\#\# 页面目标  
让运营清楚区分：  
\- 主交付物  
\- 发布必需项  
\- 非阻塞项  
\- manifest / metadata  
\- publish feedback / publish status

\#\#\# 通用结构

\#\#\#\# A. Final Video  
\- 主交付物，突出显示

\#\#\#\# B. Required Deliverables  
\- 字幕  
\- 音轨  
\- metadata  
\- 其他阻塞发布的必需项

\#\#\#\# C. Optional / Non-blocking Items  
\- scene\_pack  
\- 辅助包  
\- 额外导出物

\#\#\#\# D. Publish 区  
\- 发布按钮  
\- 启用条件说明  
\- 发布结果回填入口

\#\#\# 设计要求  
\- final\_video 是主交付  
\- required\_deliverables 决定可发布  
\- Scene Pack 必须视觉上明确为非阻塞  
\- manifest 是交付证据的一部分  
\- 发布按钮只能消费 authoritative projection

\#\#\# 三条线差异

\#\#\#\# Hot Follow  
\- final / subtitle / dubbed audio / pack  
\- 当前 attempt 与历史成功成片分开解释

\#\#\#\# Matrix Script  
\- 多变体成片  
\- copy\_bundle  
\- publish feedback  
\- variation attribution

\#\#\#\# Digital Anchor  
\- 多语言版本  
\- role\_usage / scene\_usage / language\_usage  
\- delivery pack 与 manifest

\---

\#\# 5.5 B-roll / 素材页

\#\#\# 页面定位  
素材供给区的正式前台入口，对应 Asset Library，而不是任务区的文件附件页。

\#\#\# 页面目标  
\- 浏览与检索标准素材  
\- 引用素材到任务  
\- 将任务产物 promote 为可复用资产  
\- 展示来源、许可、质量与可复用边界  
\- 形成“资产复用飞轮”，避免一次性消费

\#\#\# 核心对象  
首批支持的 asset 类型：  
\- broll  
\- reference\_video  
\- product\_shot  
\- background  
\- template  
\- role\_ref  
\- scene\_pack\_ref  
\- audio\_ref

\#\#\# 页面结构

\#\#\#\# A. 素材列表区  
\- asset\_id  
\- thumbnail / preview  
\- asset\_type  
\- tags  
\- quality summary  
\- source / license  
\- last used line

\#\#\#\# B. 搜索筛选区  
\- line  
\- topic  
\- style  
\- language  
\- role\_id  
\- scene  
\- variation\_axis  
\- quality threshold

\#\#\#\# C. 素材详情区  
\- provenance  
\- hash / version  
\- quality  
\- tags  
\- 使用限制  
\- 可供哪些 line 使用

\#\#\#\# D. 动作区  
\- 引用到任务  
\- promote\_to\_asset  
\- 标记 reusable / canonical（可占位）  
\- 关联模板 / 角色 / scene usage

\#\#\# 三条线的使用差异

\#\#\#\# Hot Follow  
\- reference\_video  
\- broll  
\- style / language tags

\#\#\#\# Matrix Script  
\- broll  
\- product\_shot  
\- background  
\- template  
\- variation\_axis

\#\#\#\# Digital Anchor  
\- role\_ref  
\- background  
\- template  
\- scene / language tags

\#\#\# 页面红线  
\- 不把 Artifact 直接等同于 Asset  
\- 不承担任务状态展示  
\- 不承担 deliverable truth 写入  
\- 不变成工具页或供应商页  
\- 不暴露 vendor/model/provider

\---

\#\# 5.6 工具页

\#\#\# 页面定位  
供给层说明页，不是主流程入口。

\#\#\# 页面目标  
展示：  
\- capability kind  
\- tool catalog  
\- capability status  
\- 可供哪些 line / scenario 使用

\#\#\# 页面结构  
\- 能力分类导航  
\- capability / tool 列表  
\- 说明与限制  
\- 状态概览

\#\#\# 设计要求  
\- 只做能力说明与状态展示  
\- 不作为任务创建入口  
\- 不出现前台供应商切换逻辑  
\- 不压过任务区 / 工作台 / 交付中心 / 素材页

\---

\#\# 5.7 后台管理控制页

\#\#\# 页面定位  
管理员控制面，不是运营执行页。

\#\#\# 页面目标  
承载：  
\- line 开关 / feature gate  
\- tool registry / capability status  
\- queue / retry / quota  
\- asset promote 审核  
\- 权限 / 合规模板 / 风险规则  
\- 系统运行健康信息

\#\#\# 页面结构  
\- line / feature gates  
\- capability / registry 状态  
\- asset 审核与 promote 管理  
\- 系统与队列状态  
\- 风险与策略配置

\#\#\# 设计要求  
\- 与任务区、素材页、工作台分离  
\- 不直接改写业务真相  
\- 不替代 line contract / status policy / asset sink

\---

\#\# 6\. 两个 line-specific panels

\#\# 6.1 Matrix Script variation panel

\#\#\# 面板定位  
Workbench 的正式侧栏插件。

\#\#\# 必备区块  
\- 变体矩阵  
\- 单变体详情  
\- attribution\_id  
\- variation axes / 差异项  
\- 发布回填区

\#\#\# 设计要求  
\- 显示变体结构而不是散乱版本列表  
\- 支撑变体比较与筛选  
\- 消费 variation\_plan / publish\_feedback / result\_packet\_binding

\---

\#\# 6.2 Digital Anchor role/speaker panel

\#\#\# 面板定位  
Workbench 的正式侧栏插件。

\#\#\# 必备区块  
\- role 选择与预览  
\- scene 绑定  
\- speaker plan 配置  
\- language × subtitles × dub 策略矩阵

\#\#\# 设计要求  
\- role / speaker / scene / language 是主对象  
\- 不是独立“角色库页面”  
\- 消费 role\_profile / speaker\_plan / language\_output / scene\_plan\_binding

\---

\#\# 7\. 状态口径

所有页面必须统一遵守以下四层状态口径：

\#\#\# L1：Pipeline Step Status  
只表达步骤执行状态：  
\- parse  
\- subtitles  
\- dub  
\- compose

\#\#\# L2：Artifact Facts  
只表达交付物事实：  
\- final 是否存在  
\- subtitle 是否存在  
\- audio 是否存在  
\- pack / manifest / scene pack 是否存在

\#\#\# L3：Current Attempt  
只表达当前尝试是否 current / ready / stale：  
\- dub\_current  
\- compose\_status  
\- requires\_redub  
\- requires\_recompose  
\- current\_subtitle\_source

\#\#\# L4：Ready Gate / Operator Summary / Advisory / Presentation  
只从 L2/L3 派生：  
\- compose\_ready  
\- publish\_ready  
\- operator\_summary  
\- advisory  
\- workbench / delivery / board 的展示投影

\#\#\# 硬约束  
\- 任何页面不得用 L4 覆盖 L2/L3  
\- 任何页面不得发明 status 真相  
\- 任何 compatibility fallback 不得压过有效 artifact facts

\---

\#\# 8\. 页面优先级

\#\#\# P0：本轮评审必须冻结  
\- Board  
\- New Tasks  
\- Workbench  
\- Delivery / 发布页  
\- B-roll / 素材页  
\- Matrix Script variation panel  
\- Digital Anchor role/speaker panel

\#\#\# P1：只定义边界  
\- 工具页  
\- 后台管理控制页

\#\#\# P2：后续细化  
\- asset promote 细节  
\- runtime API / callback  
\- durable persistence  
\- 更复杂的审批协作机制

\---

\#\# 9\. 本轮不做清单

本轮明确不做：  
\- provider/model/vendor 选择页  
\- 供应商对比页  
\- 高保真视觉稿  
\- 大规模后台管理实现  
\- 第三条新产线  
\- W2.2 / W2.3 capability expansion  
\- runtime API 正式化  
\- packet/schema redesign  
\- Hot Follow 新功能扩写

\---

\#\# 10\. 评审问题

本稿评审只看以下问题：

1\. 页面体系是否按工厂职责组织，而不是按工具组织    
2\. 三条线是否都能被这套页面体系承接    
3\. B-roll / 素材页是否正确区分 Asset Library 与 Artifact Store    
4\. 两个 panels 是否已成为正式 line-specific surface    
5\. 所有状态显示是否都能追溯到 L2/L3 或 authoritative projection    
6\. 是否存在 UI 第二真相源风险    
7\. 工具页与后台控制页是否与运营执行页分离    
8\. operator-visible payload 是否已从接口层物理剔除 Provider 信息

\---

\#\# 11\. 下一步交付顺序

1\. 冻结本需求梳理 v1    
2\. 基于本稿产出低保真 IA 与页面结构稿    
3\. 为每个页面补 contract mapping table    
4\. 工程做最小可见对接    
5\. 再进入 Platform Runtime Assembly Wave

