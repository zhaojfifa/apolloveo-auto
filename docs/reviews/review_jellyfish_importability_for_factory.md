# Jellyfish Importability Review For Factory

## 1. Executive Summary

本次评审结论不是“Jellyfish 做得好不好”，而是“它对 ApolloVeo 2.0 / SwiftCraft line-contract 工厂是否有可吸收价值”。

结论很明确：

- Jellyfish **最值得吸收的不是整套 studio 产品形态**，而是它在 `script -> shot -> candidate -> link -> asset/file usage` 这条 planning 链路上的中间结构。
- 对我们最有价值的部分主要落在 **L2/L3/L4**，而不是 L1。
- 它的强项是把短剧脚本拆成镜头、把镜头中的角色/场景/道具候选显式化、再让人工确认回写，这非常适合服务 `script_video_line`，也可作为 `action_replica_line` 的 planning/workbench 上游。
- 它的弱项是 **Studio Product 取向过强**。项目/章节/镜头 UI、Agent 管理页、视频编辑页、短剧业务字段、任务状态直接回写业务对象，这些都不适合直接进入我们当前工厂主线。

建议总纲：

- P0 吸收 5 项能力：
  1. `ScriptDivisionResult / StudioScriptExtractionDraft` 这类中间契约
  2. Shot candidate + linked asset 确认流
  3. 项目级/镜头级资产关联与 file usage 归属模型
  4. Prompt template library 的 category/default 机制
  5. Provider / Model / Settings / ApiResponse / service layering 基础治理
- P1 吸收 `Actor + Costume + Prop -> Character -> ShotCharacterLink` 的角色组织方式，但必须改造成 Action Replica 的 line contract 资产视图，不能直接沿用 studio 表意。
- P2 仅参考 `ChapterStudio` 这类工作台布局与交互，不建议现在引入 workflow editor、agent product、video editor。

Jellyfish 最值得我们吸收的前 5 项能力：

| Rank | 能力 | 先服务哪里 |
| --- | --- | --- |
| 1 | 脚本到镜头表的中间结构与 schema | `script_video_line` |
| 2 | 镜头候选资产确认流 | `script_video_line`、`action_replica_line` planning |
| 3 | 角色资产组合模型（actor/costume/prop + shot link） | `action_replica_line` planning/workbench |
| 4 | 提示词模板分类与默认模板治理 | 公共底座 |
| 5 | Provider/Model/Settings + ApiResponse + service layering | 公共底座 |

不应进入当前主线的部分：

- AgentManagement 及其 mock/product workflow 思路
- VideoEditor / timeline editor 产品壳
- 以 project/chapter/studio UI 为中心的顶层组织
- 任务执行层直接回写 shot status 的耦合方式
- 与短剧拍摄语义强绑定的字段和页面复杂度

## 2. Jellyfish Repo Inventory

### 2.1 Top-Level Inventory

顶层目录摘要：

- `backend/`: FastAPI 后端，包含 API、schema、service、LangChain/LangGraph agent、ORM、task manager、storage
- `front/`: React studio 前端，包含项目/章节/镜头/资产/提示词/模型/Agent/视频编辑页面
- `deploy/`: Dockerfile 与 compose，提供 MySQL + RustFS + Backend + Front 联调
- `docs/`: 项目说明与静态资源
- `site/`: 独立站点/展示站

### 2.2 Backend / Front / Docs / Deploy Responsibilities

Backend 主要职责：

- `backend/app/api/v1/routes/script_processing.py`: 剧本拆镜、实体合并、变体分析、一致性检查、脚本精简/优化
- `backend/app/api/v1/routes/studio/*.py`: 项目、章节、镜头、资产、提示词、文件、图片任务、时间线等 CRUD 与聚合接口
- `backend/app/services/studio/*.py`: Studio 主业务逻辑，尤其是 shot/assets/prompt/file usage/image task
- `backend/app/services/llm/*.py`: provider/model/settings 管理与解析
- `backend/app/core/task_manager/*`: 异步任务存储、状态、交付模式抽象
- `backend/app/models/*`: project/chapter/shot/asset/prompt/file/task 等数据模型

Front 主要职责：

- `front/src/pages/aiStudio/project/*`: 项目工作台、章节入口、角色页
- `front/src/pages/aiStudio/shots/*`: 章节镜头列表、镜头资产确认页
- `front/src/pages/aiStudio/chapter/ChapterStudio.tsx`: 三栏式章节拍摄工作台
- `front/src/pages/aiStudio/assets/*`: 资产管理与编辑
- `front/src/pages/aiStudio/models/*`: provider/model/settings 管理 UI
- `front/src/pages/aiStudio/prompts/*`: 提示词模板库
- `front/src/pages/aiStudio/agents/*`: Agent 产品页，主要是产品层壳
- `front/src/pages/aiStudio/editor/VideoEditor.tsx`: 后期剪辑产品壳，当前较浅

Docs / Deploy 主要职责：

- `README.md`: 总体产品叙事与开发说明
- `backend/README.md`: 后端分层与响应约定
- `deploy/compose/docker-compose.yml`: 本地 compose 编排

### 2.3 Key Files By Theme

| 主题 | 关键位置 | 判断 |
| --- | --- | --- |
| 剧本处理 | `backend/app/api/v1/routes/script_processing.py`, `backend/app/chains/agents/*script*`, `backend/app/schemas/skills/script_processing.py` | 价值高，偏 L2 契约与编排 |
| 分镜 / shot 建模 | `backend/app/models/studio_shots.py`, `backend/app/schemas/studio/shots.py`, `backend/app/services/studio/shots.py`, `backend/app/services/studio/shot_details.py` | 价值高，尤其 shot/detail 拆表与候选确认流 |
| 项目 / 章节 / 镜头工作台 | `front/src/pages/aiStudio/project/*`, `front/src/pages/aiStudio/shots/*`, `front/src/pages/aiStudio/chapter/ChapterStudio.tsx` | 可参考交互组织，不宜整体移植 |
| 资产库 / 模板库 / 提示词模板 | `backend/app/models/studio_assets.py`, `backend/app/models/studio_prompts_files_timeline.py`, `backend/app/api/v1/routes/studio/prompts.py`, `front/src/pages/aiStudio/assets/*` | 价值高，适合沉底座 |
| Agent / workflow / graph | `backend/app/chains/graphs.py`, `backend/app/chains/agents/*`, `front/src/pages/aiStudio/agents/*` | 后端 agent 可参考，前端 agent product 不建议引入 |
| 模型管理 / provider 管理 | `backend/app/models/llm.py`, `backend/app/services/llm/*`, `backend/app/api/v1/routes/llm.py`, `front/src/pages/aiStudio/models/*` | 高价值底座 |
| 视频生成编排 | `backend/app/services/film/generated_video.py`, `backend/app/core/tasks/video_generation_tasks.py`, `backend/app/api/v1/routes/film/*` | 可参考 L3 worker adapter 层，当前不够 line-contract 化 |
| 后期剪辑 / 导出 | `backend/app/models/studio_prompts_files_timeline.py`, `front/src/pages/aiStudio/editor/VideoEditor.tsx`, `backend/app/api/v1/routes/studio/timeline.py` | 当前偏浅，参考价值有限 |
| API schema / response envelope / service layering | `backend/app/schemas/common.py`, `backend/app/main.py`, `backend/README.md`, `backend/app/services/*` | 高价值底座 |

## 3. Four-Layer Mapping

### 3.1 Layer Reading

- **L1 Scenario / Production Line**：Jellyfish 的顶层是 `project -> chapter -> studio/shots/editor`。这是 studio product 组织，不是 production line 组织。
- **L2 SOP / Skills / Orchestration**：最强。`script_processing`、`StudioScriptExtractionDraft`、prompt categories、shot candidate confirmation 都在这里。
- **L3 Worker / Tool / Model / External Adapter**：中等。provider/model 管理、image/video task、storage adapter、LangChain agent 在这里。
- **L4 Foundation / SSOT / Artifact / Asset / Status / Publish**：有价值但边界不够干净。文件、file usage、prompt template、task tables 可吸收；status 回写方式需要改。

### 3.2 Architecture Mapping Table

| Jellyfish 模块/能力 | 当前仓库位置 | 所属层 | 对应我们的目标对象 | 建议动作 | 优先级 | 原因 |
| --- | --- | --- | --- | --- | --- | --- |
| 脚本拆镜 schema `ScriptDivisionResult` / `ShotDivision` | `backend/app/schemas/skills/script_processing.py` | L2 | `line contract`, `skill`, `smart pack` | adopt | P0 | 已经形成清晰中间契约，最适合做 `script_video_line` 上游 planning output |
| `StudioScriptExtractionDraft` name-based 导入草稿 | `backend/app/schemas/skills/script_processing.py` | L2 | `line contract`, `editor`, `skill` | refactor | P0 | 很适合做“planning draft”，但需要从 studio import 草稿改成 line contract draft |
| 剧本拆镜写库服务 | `backend/app/services/studio/script_division.py` | L2/L4 | `editor`, `foundation` | refactor | P1 | 可借鉴把 contract output 落到工作台，但不能直接写 project/chapter/shots SSOT |
| 镜头候选资产表与确认流 | `backend/app/services/studio/shot_extracted_candidates.py`, `backend/app/api/v1/routes/studio/shots.py` | L2/L4 | `editor`, `asset sink`, `foundation` | adopt | P0 | 明确区分 extracted candidate 与 linked asset，适合 line-contract 下的人审确认环节 |
| 镜头资产总览聚合 | `backend/app/services/studio/shot_assets_overview.py` | L2/L4 | `editor`, `asset sink` | adopt | P0 | 对 planning/workbench 特别有用，能同时展示候选与已绑定真相 |
| 角色组织：Actor + Costume + Prop -> Character | `backend/app/models/studio_assets.py` | L2/L4 | `worker profile`, `asset sink`, `editor` | refactor | P1 | 很适合 action replica 的 planning 资产视图，但需改名义与归属边界 |
| Shot / ShotDetail / ShotDialogLine / ShotFrameImage 拆表 | `backend/app/models/studio_shots.py` | L2/L4 | `deliverable profile`, `editor`, `foundation` | refactor | P1 | 数据组织合理，但字段混入 studio camera UI 语义，需收敛为 line deliverable schema |
| 项目/章节/镜头 scoped asset links | `backend/app/models/studio_projects.py`, `backend/app/utils/project_links.py` | L4 | `asset sink`, `foundation` | adopt | P0 | project/chapter/shot scope link 对我们非常重要，可转成 line/run/step scope |
| File usage 归属回写 | `backend/app/services/studio/file_usages.py`, `backend/app/models/studio_file_usages.py` | L4 | `asset sink`, `foundation`, `publish` | adopt | P0 | 很接近我们需要的资产归属索引，不必依赖 UI 也能成立 |
| Prompt template category/default 体系 | `backend/app/models/studio_prompts_files_timeline.py`, `backend/app/api/v1/routes/studio/prompts.py`, `backend/app/services/studio/image_tasks.py` | L2/L4 | `skills bundle`, `smart pack`, `foundation` | adopt | P0 | category + default + system template 机制可直接服务多线共用模板系统 |
| Provider / Model / Settings | `backend/app/models/llm.py`, `backend/app/services/llm/*`, `backend/app/api/v1/routes/llm.py` | L3/L4 | `model supply`, `foundation` | adopt | P0 | 结构清楚，且与 line 无强耦合 |
| `ApiResponse` / 分页壳 / 错误统一 | `backend/app/schemas/common.py`, `backend/app/main.py` | L4 | `foundation` | adopt | P1 | 适合统一网关响应风格 |
| 异步任务表 + task link | `backend/app/models/task.py`, `backend/app/models/task_links.py`, `backend/app/core/task_manager/*` | L3/L4 | `worker`, `foundation`, `status policy` | refactor | P0 | 基础结构可用，但状态真相回写方式需和 skills runtime 边界重做 |
| Image task -> file -> asset persistence | `backend/app/services/studio/image_task_runner.py` | L3/L4 | `worker gateway`, `asset sink` | refactor | P1 | 适合作为 worker gateway 示例，但不能让任务服务直写业务 status 真相 |
| Script processing agents | `backend/app/chains/agents/*`, `backend/app/api/v1/routes/script_processing.py` | L2/L3 | `skill`, `worker` | refactor | P1 | 能力可用，但要拆成 line skill + worker adapter，而不是 studio API 拼装 |
| LangGraph 示例 | `backend/app/chains/graphs.py` | L2 | `skill` | reference | P2 | 当前只是示例，不构成必须能力 |
| `ChapterShotsPage` 拆镜入口 + 镜头列表 | `front/src/pages/aiStudio/shots/ChapterShotsPage.tsx` | L1/L2 | `editor` | reference | P2 | 适合参考 planning workbench 的入口组织 |
| `ChapterShotEditPage` 候选资产确认页 | `front/src/pages/aiStudio/shots/ChapterShotEditPage.tsx` | L2 | `editor` | refactor | P1 | 很适合 action/script planning workbench，但需改成 line-aware editor |
| `ChapterStudio` 三栏拍摄工作台 | `front/src/pages/aiStudio/chapter/ChapterStudio.tsx` | L1/L2 | `editor` | reference | P2 | 交互复杂度高，当前主线不宜引入 |
| AssetManager | `front/src/pages/aiStudio/assets/*` | L1/L4 | `editor`, `asset sink` | reference | P2 | 可参考 project/global 资产双层管理，但不应先做完整 UI |
| AgentManagement | `front/src/pages/aiStudio/agents/*` | L1/L2 | `editor` | reject | P2 | 明显是 studio product 壳，不服务当前 line-contract 主线 |
| VideoEditor / Timeline | `front/src/pages/aiStudio/editor/VideoEditor.tsx`, `backend/app/api/v1/routes/studio/timeline.py` | L1/L4 | `editor`, `publish` | reject | P2 | 现阶段实现浅，且会把 UI 复杂度带进主线 |

## 4. Script-Driven Opportunities

### 4.1 对 `script_video_line` 最有价值的内容

最有价值的不是“自动拆镜”这个动作本身，而是拆镜后形成的 **可审、可改、可再绑定** 的中间结构。

优先吸收：

- `ShotDivision` / `ScriptDivisionResult`
  - 来源：`backend/app/schemas/skills/script_processing.py`
  - 解决问题：给脚本到镜头表之间一个稳定中间态，保留 `index/start_line/end_line/script_excerpt/shot_name`
  - 对应层：L2
  - 更适合：`script_video_line`
  - 风险：当前仍以章节内镜头为单位，不是 line run / deliverable scope
  - 最小落地：在我们仓内新增 `script_video_line` 的 `planning_draft` contract，先沿用这套字段

- `StudioScriptExtractionDraft`
  - 来源：同上
  - 解决问题：把脚本提取结果组织成 `characters/scenes/props/costumes/shots` 的 name-based 草稿，便于人工确认与后续导入
  - 对应层：L2
  - 更适合：`script_video_line`
  - 风险：当前是 studio import contract，不是 line contract
  - 最小落地：改造为 `script_video_line.plan_bundle_draft`，保留 shot 与 asset draft，不直接绑定 DB 表

- `shot_extracted_candidates` + `assets_overview`
  - 来源：`backend/app/services/studio/shot_extracted_candidates.py`, `backend/app/services/studio/shot_assets_overview.py`
  - 解决问题：把 LLM 抽取结果显式为候选项，再通过人工/规则确认成 linked asset
  - 对应层：L2/L4
  - 更适合：`script_video_line`
  - 风险：当前默认把 candidate 状态与 shot 状态耦合
  - 最小落地：只引入 candidate schema 与 confirmation flow，不引入 Jellyfish 的 shot status 写法

- `ChapterShotsPage` + `ChapterShotEditPage`
  - 来源：`front/src/pages/aiStudio/shots/*`
  - 解决问题：一页负责“拆镜”，一页负责“镜头级候选确认”
  - 对应层：L2 editor
  - 更适合：`script_video_line`
  - 风险：会把 project/chapter UI 组织一起带入
  - 最小落地：只借界面信息架构，不搬 UI 组件树

### 4.2 剧本解析 / 镜头表中间结构判断

Jellyfish 在这一段最可吸收的地方：

- 明确把“剧本拆镜”和“实体合并/变体分析/一致性检查”拆成多个 skill 输出，而不是一次性黑盒生成最终 studio 对象。
- `ScriptDivisionResult -> ShotElementExtractionResult -> EntityMergeResult -> VariantAnalysisResult -> StudioScriptExtractionDraft` 这条链非常适合改造成我们的 `line contract -> skill outputs -> editor draft`。

不建议直接照搬的地方：

- `write_to_db` 这种由 script-processing API 直接写 studio chapter/shots 的方式，会让 L2 输出直接侵入 L4 SSOT。
- `full-process` 风格的 product API 如果直接引入，会削弱我们对 line-contract / smart pack / worker gateway 的边界控制。

## 5. Action-Replica / Digital Human Opportunities

### 5.1 最有价值的内容

对 `action_replica_line`，Jellyfish 最有价值的不是生成引擎，而是 **角色资产组织和镜头绑定方式**。

优先吸收：

- `Actor / Costume / Prop / Character / CharacterPropLink`
  - 来源：`backend/app/models/studio_assets.py`
  - 解决问题：把角色拆成可治理的组成资产，再形成镜头中的角色引用
  - 对应层：L2/L4
  - 更适合：`action_replica_line` planning/workbench
  - 风险：`Actor` 在 Jellyfish 里是“演员形象资产”，不完全等于我们数字人 identity
  - 最小落地：改成 `ReplicaIdentity / Wardrobe / HandProp / RoleBinding` 视图，不照抄命名

- `ShotCharacterLink` 与 project/chapter/shot scoped links
  - 来源：`backend/app/models/studio_shots.py`, `backend/app/models/studio_projects.py`
  - 解决问题：角色与镜头的绑定、角色顺序、镜头作用域引用
  - 对应层：L2/L4
  - 更适合：`action_replica_line`
  - 风险：当前默认 project/chapter/shot 作用域，和 line/run/step scope 不一致
  - 最小落地：映射成 `line_run -> segment -> shot_unit` 的作用域 link 表

- `shot_assets_overview`
  - 来源：`backend/app/services/studio/shot_assets_overview.py`
  - 解决问题：在镜头级同时看到已绑定角色/服装/道具与待确认候选
  - 对应层：L2 editor
  - 更适合：`action_replica_line`
  - 风险：对 scene/prop/costume 分类写死
  - 最小落地：把 overview item 抽象为 `replica planning slot`

### 5.2 哪些适合作为 Action Replica 的 planning/workbench，而不是生成引擎

适合作为 planning/workbench：

- 角色资产分层组织
- 镜头级候选确认
- 角色-镜头绑定
- project-vs-shot 两级资产引用
- prompt template 对角色图、服装图、道具图的分类

不适合作为生成引擎直接吸收：

- `image_task_runner.py` 直接按 provider name 分支并落库
- `ChapterStudio` 中把镜头细节、生成任务、文件采用状态揉在一个页面内的产品逻辑
- 当前 repo 对口型、动作控制、参考控制的抽象仍偏 UI/任务级，没有形成 action replica 的 worker contract

## 6. Tooling / Foundation Opportunities

### 6.1 最有价值的底层支撑逻辑

- Provider / Model / Settings
  - 来源：`backend/app/models/llm.py`, `backend/app/services/llm/manage.py`, `backend/app/services/llm/resolver.py`
  - 判断：可直接进入公共底座
  - 原因：与业务线低耦合，已经有 category/default/provider 三级结构

- `ApiResponse` + error envelope
  - 来源：`backend/app/schemas/common.py`, `backend/app/main.py`
  - 判断：适合借鉴
  - 原因：统一前后端 envelope，减少 UI 适配碎片

- Prompt template library
  - 来源：`backend/app/models/studio_prompts_files_timeline.py`, `backend/app/api/v1/routes/studio/prompts.py`, `backend/app/services/studio/image_tasks.py`
  - 判断：高价值
  - 原因：category/default/system template 机制适合沉到 smart pack / skills bundle

- File usage / asset sink indexing
  - 来源：`backend/app/services/studio/file_usages.py`
  - 判断：高价值
  - 原因：文件与 project/chapter/shot 的使用归属可迁移成 line/run/deliverable 归属

- task + task link
  - 来源：`backend/app/models/task.py`, `backend/app/models/task_links.py`
  - 判断：结构可取，边界需改
  - 原因：任务表独立、业务关联表独立，这和 worker gateway 的方向一致

### 6.2 底层不一致与改造点

- `image_task_runner.py` 会在任务完成后直接更新业务图片表、file usage、shot status。  
  这会让执行层污染状态真相口，不符合我们“Skills Runtime 不得污染 status / deliverable / asset sink 真相口”的要求。

- `provider_key_from_db_name()` 这种根据显示名做 provider 分支的写法过脆。  
  我们需要 provider registry / worker gateway capability registration，而不是 name-based branching。

- `PromptCategory` 当前仍部分带有 studio UI 语义。  
  需要改成 line-neutral 的 `template slot` / `prompt family`。

## 7. What Not To Import

### 7.1 Studio Product 思路，不适合直接带进工厂底座

- `project -> chapter -> chapter studio -> editor` 是 studio 产品导航，不是 production line 导航。
- `ChapterStudio.tsx` 把拍摄、镜头编辑、关键帧生成、文件采用、预览等揉成一个重页面，这不是当前工厂主线应该优先做的结构。
- `AgentManagement.tsx` 和 `AgentEdit.tsx` 是产品化 agent 管理，不是 line-contract 能力编排。

### 7.2 短剧业务强绑定，不适合直接复用到 `hot_follow_line` / `localization_line`

- camera shot / angle / movement / vfx / bgm / scene atmosphere 等字段强烈服务短剧拍摄工作台
- chapter/raw_text/condensed_text/storyboard_count 这些对象设计默认是短剧章节生产
- `VideoEditor.tsx` 默认成片剪辑心智，不适用于 localization / hot follow 主线

### 7.3 如果直接引入，会破坏边界的部分

- `script_processing` 结果直接 `write_to_db`
- 任务完成后直接回写 `Shot.status`
- 业务对象与生成任务的同步更新揉在同一 service
- studio object 被当作 skill output SSOT

这些都会破坏：

- line-contract 边界
- skills runtime 与 status truth 的边界
- asset sink 独立真相口
- foundation SSOT 的清晰层次

### 7.4 可能把 UI editor 复杂度带进主线，不值得现在做

- `ChapterStudio.tsx`
- 完整资产管理页与各类编辑页
- Agent workflow product UI
- 时间线/视频编辑器

## 8. Priority Backlog (P0 / P1 / P2)

### P0

- 引入 `script_video_line` planning contract：
  - 参考 `ScriptDivisionResult`, `StudioScriptExtractionDraft`
- 引入 shot candidate / linked asset 双态模型：
  - 参考 `shot_extracted_candidates.py`, `shot_assets_overview.py`
- 引入 line-scoped asset/file usage 索引：
  - 参考 `project_*_links`, `file_usages.py`
- 引入 prompt template registry：
  - 参考 `PromptTemplate`, prompt categories, default/system rule
- 引入 provider/model/settings/service layering：
  - 参考 `llm.py`, `manage.py`, `resolver.py`, `ApiResponse`

### P1

- 为 `action_replica_line` 设计角色资产组合模型：
  - 基于 `Actor + Costume + Prop + Character + ShotCharacterLink`
- 将 task/task-link 改造成 worker gateway：
  - 保留 task 独立表，移除对业务 status 真相的直接写入
- 设计简化版 planning/workbench：
  - 借鉴 `ChapterShotEditPage` 的镜头候选确认页

### P2

- 参考 `ChapterStudio` 的多栏工作台信息架构
- 参考 AssetManager 的 project/global 双层资产库产品表现
- 参考但不引入 AgentManagement / VideoEditor

## 9. Proposed Integration Path

建议按最小可落地路径推进，不做整仓迁移，不做整套前端替换。

### Phase 1: 先服务 `script_video_line`

1. 在我们仓内新建 `script_video_line` planning draft contract  
   来源参考：`ScriptDivisionResult`, `StudioScriptExtractionDraft`

2. 新建 shot candidate confirmation service  
   来源参考：`shot_extracted_candidates.py`, `shot_assets_overview.py`

3. 把确认后的 asset binding 落到 line-scoped asset sink index  
   来源参考：`project_*_links`, `file_usages.py`

### Phase 2: 再服务 `action_replica_line`

1. 将 `Actor/Costume/Prop/Character` 改造成数字人 planning 资产视图  
2. 建立 `replica planning slot -> shot binding`  
3. 用简化 workbench 提供角色-镜头绑定与候选确认，不引入完整 studio

### Phase 3: 沉公共底座

1. Provider / Model / Settings registry  
2. Prompt template system  
3. ApiResponse / service layering 规范  
4. Task / task-link 结构，但改造成 worker gateway + status policy

## 10. Appendix: Key Files Reviewed

- `/Users/tylerzhao/Code/Jellyfish/README.md`
- `/Users/tylerzhao/Code/Jellyfish/backend/README.md`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/main.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/schemas/common.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/schemas/skills/script_processing.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/__init__.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/script_processing.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/llm.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/studio/__init__.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/studio/projects.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/studio/prompts.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/api/v1/routes/studio/shots.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/llm.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/studio_projects.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/studio_assets.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/studio_shots.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/studio_prompts_files_timeline.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/task.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/models/task_links.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/llm/manage.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/llm/resolver.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/script_division.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/shot_extraction_draft.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/shot_extracted_candidates.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/shot_assets_overview.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/file_usages.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/image_tasks.py`
- `/Users/tylerzhao/Code/Jellyfish/backend/app/services/studio/image_task_runner.py`
- `/Users/tylerzhao/Code/Jellyfish/front/src/App.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/shots/ChapterShotsPage.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/shots/ChapterShotEditPage.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/chapter/ChapterStudio.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/assets/AssetManager.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/models/ModelManagement.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/models/ProvidersTab.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/models/SettingsTab.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/agents/AgentManagement.tsx`
- `/Users/tylerzhao/Code/Jellyfish/front/src/pages/aiStudio/editor/VideoEditor.tsx`
- `/Users/tylerzhao/Code/Jellyfish/deploy/compose/docker-compose.yml`
