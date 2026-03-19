# ApolloVeo v1.9 Review Baseline（平台化演进前基线）

> 定位：ApolloVeo 属于 **L4 业务编排层**（AI + Workflow Orchestration），以“**输出结构/交付物**”为导向，而非工具堆叠。  
> 目的：在 v1.9 → 平台化演进前做一次全面诊断，确立六边形架构底座与扩展边界，避免在真实接入阶段越陷越深。

---

## 1. v1.9 当前结论（一句话）

v1.9 已具备 L4 编排层的公共能力雏形：以任务为中心的流程入口、可复用的 steps 管线、以及以交付物为导向的 publish 展示；但“真实接入”尚未开始，且**状态/交付物真相源、写入边界与路由语义仍未稳定**，继续补丁式修复会放大平台期耦合风险。

---

## 2. 已达成（公共能力基座已经成型）

### 2.1 业务流程骨架已跑通：Task → Workbench → Publish
- **Task 创建与列表**：按 `kind`（如 `apollo_avatar`）聚合与展示，UI 入口已独立。
- **Workbench**：可拉取任务数据、展示事件流、触发生成（generate）与查看产物（publish hub 等）。
- **Publish 页/Publish Hub**：以交付物为导向展示 deliverables（至少 publish_hub 渲染链路已打通）。

### 2.2 可复用的公共步骤（Steps Pipeline）具备稳定执行能力
从日志链路可见公共步骤已具备工程可跑性与可观测性：
- `subtitles (whisper + gemini)`
- `dub (edge-tts)`
- `pack`
- `publish_bundle (upload)`
并具备 step timing 记录与事件输出。

### 2.3 场景扩展出现雏形：ApolloAvatar 成为可复用样板
- `apollo_avatar` 场景已经形成“router/service/publish_hub/状态策略”等成组结构雏形，为后续 baseline/hot/broll 的同构扩展提供实践参考。

---

## 3. 未达成（平台化演进前必须补齐的关键）

### 3.1 尚未进入“真实接入”阶段
- **真实业务模型/真实供应商接入（live）**尚未开始：仍处在“工程可跑/能力占位”阶段。
- **真实素材体系（尤其 B-roll）**尚未闭环：缺少素材目录规范、选择策略与 pack 结构一致的可交付方案。

### 3.2 状态与交付物真相源不稳定（结构性风险）
已出现并被验证的问题类型：
- pipeline 明明产出并上传交付物，但 UI/接口可能出现 **ready ↔ failed** 反复或错配。
- 出现 `409 not_ready` / `missing pack_key` 等，与“实际 deliverables 已存在”相冲突。
- 根因倾向：**状态字段（status/pack_status/publish_status/last_step）与 deliverables keys（pack_key/publish_key）之间缺少单一真相源**，并且存在多处 `repo.upsert` 写入点导致回退/覆盖。

### 3.3 API 路由与鉴权语义存在割裂
- 存在 `/api/...` 与 `/v1/...` 两套路径并存，且出现 `/api/... 401` 与 `/v1/... 200` 并行的情况。
- 平台期风险：前端/运营一旦走错路径，就会出现“看起来失败”的假失败与不一致体验。

---

## 4. 本次 Review 的目标（平台化演进前必须定底座）

### 4.1 六边形架构底座（Ports & Adapters）要落地的边界
- **Domain（业务规则）**：以“交付物事实”为核心，状态为派生视图。
- **Application（编排层）**：Steps/Scenes/Task Orchestration 与策略注入。
- **Adapters（基础设施与外部服务）**：存储（R2/S3）、模型（Gemini/Whisper/TTS/Avatar Provider）、下载分发与鉴权。

### 4.2 业务平台基座（L4）要固化的共性模块
- 任务模型（Task）、事件流（Events）、交付物索引（Deliverables Index）
- 工作台（Workbench）与发布中心（Publish Hub）的标准交互协议
- Skills（语言政策等）与 Ops（操作手册）的固化入口与规则化机制

### 4.3 业务场景扩展（Scene）必须同构且可复制
- baseline / hot-follow / avatar / broll 等场景必须按统一模板扩展：
  - Scene 定义（输入、约束、产物）
  - Steps 编排（复用公共步骤 + 场景独有步骤）
  - Publish Hub 渲染（交付物清单 + 下载策略）
  - Status Policy（仅做“防回退/防错写”的策略层，不能成为业务事实）

### 4.4 Tools 集成与 B-roll 素材集成（平台期关键）
- Tools：作为可配置能力嵌入 Workbench/Publish（而非散落 UI 按钮）
- B-roll：定义素材目录规范、索引结构与选择策略，并保证 pack/scene 产物结构一致

---

## 5. Review 后的“真实接入门槛”（必须可验收）

1. **Deliverables 真相源唯一**：`pack_key/publish_key/...` 存在即“可交付事实”，UI 状态必须从事实派生  
2. **repo.upsert 写入边界收敛**：状态/产物索引只能从单入口写入；场景策略不得散落多点写库  
3. **/api 与 /v1 语义与鉴权对齐**：前端只走一条稳定链路（避免假失败）  
4. **Avatar SOP 固化**：作为新增场景模板（baseline/hot/broll 必须能按同一套路扩展）  
5. **Skills/Ops/编排规则进入文档与配置**：语言政策、运营操作手册、流程编排约束形成可版本化资产

---

## 6. 当前阶段建议（执行策略）

- **短期（冻结补丁，进入 review）**：停止在 `steps_v1.py` 等核心文件做“继续加条件”的补丁式修复，避免平台化前把主线变成泥球。
- **中期（完成底座收敛）**：先收敛真相源与写入边界，再推进 UI 优化与真实接入。
- **长期（平台化扩展）**：以 avatar 场景为样板，同构扩展 baseline/hot/broll，并把 tools/broll 作为平台基座能力纳入统一协议。

---

## 7. 附：v1.9 现状补充说明（你可在此补链接/截图）

- 关键页面：
  - `/tasks?kind=apollo_avatar`（任务列表）
  - `/tasks/{task_id}`（workbench）
  - `/tasks/{task_id}/publish`（publish hub）
- 关键接口：
  - `/api/tasks`, `/api/tasks/{id}/events`
  - `/api/apollo/avatar/{id}/generate`
  - `/api/apollo/avatar/{id}/publish_hub`（若存在鉴权差异，需在 review 中统一）
- 关键风险点：
  - 多处 `repo.upsert(...)` 导致状态回退/覆盖
  - `/api` 与 `/v1` 双通道导致鉴权与结果不一致
