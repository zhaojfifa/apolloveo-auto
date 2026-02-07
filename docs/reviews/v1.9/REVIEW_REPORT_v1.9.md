## 0. Executive Summary（一句话结论 + 风险等级）
v1.9 基线仅部分达标，核心风险集中在“deliverables 真相源不唯一 + /api 与 /v1 双通道鉴权语义不一致”，综合风险等级：**High**。

---

## 1. Baseline 对照（逐条引用 REVIEW_v1.9_BASELINE.md 要点）
**1.1 已达成的公共能力雏形**
- **Task/Workbench/Publish 主流程可跑通**：任务路由与 UI 路由存在并被测试覆盖（`tests/test_route_inventory.py` 列出 `/tasks`、`/ui`、`/api/tasks` 与 `/v1/parse` 等；见 `tests/test_route_inventory.py:8-28`）。
- **Steps Pipeline 可执行**：v1 action routes 仍存在（`gateway/routes/v1_actions.py:39-84`），包含 `/v1/parse`、`/v1/subtitles`、`/v1/dub`、`/v1/pack`。
- **Publish Hub 交付物展示链路**：Deliverables 列表通过 `_publish_hub_payload` 生成（`gateway/app/routers/tasks.py:785-847`），说明发布侧交付物展示逻辑仍在。

**1.2 未达成的关键项**
- **“真实接入”仍未进入可审计状态**：Scene Pack/TaskPlan/Asset Library 的 DoD 没有落地痕迹，工程中仅出现目录创建而未见 schema/索引（`gateway/app/main.py:61`），且未检索到 `TaskPlan`、`tool_chain` 等代码踪迹（仓库搜索无匹配）。
- **Deliverables 真相源不唯一（核心结构性风险）**：`pack_key/publish_key` 与 `status/pack_status/publish_status/last_step` 多处写入，且 `/v1/tasks/{id}/pack` 依赖 `pack_key` 触发 409 not_ready（`gateway/app/routers/tasks.py:520-535` + `_not_ready_response` 定义 `gateway/app/routers/tasks.py:885-899`），与“交付物已存在但状态不一致”高度吻合。
- **/api 与 /v1 双通道语义分裂仍在**：双通道路由共存（`gateway/main.py:51-56`、`gateway/app/main.py:88-92`、`gateway/app/routers/tasks.py:200/453`），且鉴权中统一视为 API（`gateway/app/main.py:115-160`），但 `gateway/main.py` 入口无同级鉴权中间件，存在 200/401 语义差异的现实路径。

---

## 2. Non-Interference Contract 检查（逐条对照 v1.9_constraints.md）
**2.1 API Compatibility（Must Not Break）**
- 约束要求的 v1.85 路由仍存在：
  - `/api/tasks/local_upload`：`gateway/app/routers/tasks.py:1721`
  - `/api/tasks/{task_id}/subtitles`：`gateway/app/routers/tasks.py:2625`
  - `/api/tasks/{task_id}/dub`：`gateway/app/routers/tasks.py:2551`
  - `/api/tasks/{task_id}/pack`：`gateway/app/routers/tasks.py:2507`
  - `/api/tasks`：`gateway/app/routers/tasks.py:1856`
- **结论**：未发现路由删除或语义变更证据，保持兼容（当前符合）。

**2.2 State Machine（Must Not Break）**
- `/v1/*` pipeline 行为仍保留：`gateway/routes/v1_actions.py:39-84`
- `AUTO_PIPELINE_STEP/DONE` 仍被记录：`gateway/app/routers/tasks.py:1277-1292`
- **结论**：v1.85 默认推进行为看似保留，但存在多处并行更新（见 Section 4），属于“未破坏但风险上升”。

**2.3 Artifact Contract（Must Not Break）**
- 代码仍使用 `pack_key/pack_path` 体系（`gateway/app/routers/tasks.py:520-535`，`gateway/app/services/steps_v1.py:1402-1425`），未见替换旧 key 命名；无明显破坏证据。

**2.4 Smart Pack v1.0**
- 未见对 v1.85 manifest 语义的强改证据；pack 相关流程仍以旧机制为主。
- **结论**：暂未发现破坏性变更。

---

## 3. 路由与鉴权语义审计（/api vs /v1）
**3.1 路由现状**
- `/api` 与 `/v1` 并行注册：
  - `gateway/main.py:51-56`
  - `gateway/app/main.py:88-92`
  - `/v1/tasks/*` 下载/状态页：`gateway/app/routers/tasks.py:453-685`
  - `/api/tasks/*` 任务操作：`gateway/app/routers/tasks.py:200,1632-2690`
- 预期/测试覆盖的双通道清单存在：`tests/test_route_inventory.py:8-28`

**3.2 鉴权裂缝**
- `gateway/app/main.py` 对 `/api` 与 `/v1` 统一做鉴权（`_is_api_path` 与 `auth_middleware`，见 `gateway/app/main.py:115-160`）
- 但 `gateway/main.py` 入口仅注册路由，未配置同级鉴权中间件（`gateway/main.py:51-56`）
- **风险**：部署入口不同将导致 `/api` 与 `/v1` 返回 401/200 差异，形成“看似失败”的假负载。

**3.3 收敛策略建议**
- **优选方案**：保留 `/api` 为稳定前端主路径，`/v1` 仅作为兼容桥并显式标注 deprecated；在统一鉴权中间件中强制 `/v1` → `/api` 的 302 或内部代理（仅新增可选路由，符合 Non-Interference Contract）。
- **替代方案**：明确保留 `/v1` 为稳定路径，`/api` 仅薄代理；但需要将现有 UI/运营路由统一走同一入口。

---

## 4. Deliverables 真相源审计
### 4.1 Deliverables keys 写/读位置（举证）
- **写入（pack_key/pack_status）**
  - 自动 pipeline pack 成功后写入 `pack_key/pack_status/status`：
    `gateway/app/routers/tasks.py:1277-1292`
  - steps_v1 在 pipeline 中写 `pack_key` 与 `pack_status: done`：
    `gateway/app/services/steps_v1.py:1402-1425`
- **写入（publish_key/publish_status）**
  - 发布服务写 `publish_key/publish_status`：
    `gateway/app/services/publish_service.py:126-148`
  - steps_v1 写 `publish_status`：
    `gateway/app/services/steps_v1.py:1470-1514`
- **读取（交付物展示）**
  - Publish hub 交付物依赖 `_deliverable_url` → `pack_key/pack_path/scenes_key`：
    `gateway/app/routers/tasks.py:785-847`
- **读取（下载）**
  - `/v1/tasks/{task_id}/pack` 依赖 `pack_key`/`pack_path`，缺失直接 `409 not_ready`：
    `gateway/app/routers/tasks.py:520-535`
  - `_not_ready_response` 返回 `missing` 字段及 status 细节：
    `gateway/app/routers/tasks.py:885-899`

### 4.2 status/pack_status/publish_status/last_step 写/读位置
- 自动 pipeline 写 `status/last_step`：`gateway/app/routers/tasks.py:1277-1292`
- steps_v1 post pipeline 逻辑会在 pack_key 存在时设定 `status` 与 `last_step`（`gateway/app/services/steps_v1.py:1550-1585`）
- Apollo Avatar 的状态政策仅在 publish_key 存在时阻止 regression：
  `gateway/app/services/status_policy/apollo_avatar.py:12-58`

### 4.3 “假失败”的结构性根因
- **多入口写入导致字段不一致**：`pack_key` 由至少两条路径写入（tasks router + steps_v1），`publish_key` 由 publish_service/steps_v1 写入；不同路径可能造成 `pack_key` 缺失但 deliverables 实际存在。
- **not_ready 以 key 缺失为判定**：当 `pack_key` 丢失时，即使已有产物，仍返回 `409 not_ready / missing pack_key`（`gateway/app/routers/tasks.py:520-535` + `885-899`）。
- **结论**：当前 deliverables 真相源并非单点，状态与 key 的推导不具备一致性保障。

### 4.4 “单一真相源”方案（最小可行）
- 以 **deliverables keys 为事实源**：`pack_key/publish_key` 为主，状态仅派生，不直接写“ready/failed”；
- `status/pack_status/publish_status/last_step` 统一由派生策略产出，写入在单入口完成；
- 增设 “DeliverablesIndexWriter” 负责写 key，`StatusPolicy` 仅作防回退，不产生事实更新。

---

## 5. repo.upsert 写入边界收敛方案
### 5.1 当前散落写入点（举证）
- `repo.upsert` 统一入口仅在 `policy_upsert` 中被调用：
  `gateway/app/services/status_policy/utils.py:8-28`
- 但调用方散落在 tasks router 与 steps_v1：
  - `gateway/app/routers/tasks.py:1277-1292`（pack pipeline）
  - `gateway/app/services/steps_v1.py:1402-1425`（pack step）
  - `gateway/app/services/steps_v1.py:1470-1514`（publish step）

### 5.2 建议的单入口结构
- **单写入口**：新增 `TaskStateWriter` / `DeliverablesIndexWriter`（命名示例），仅允许 `repo.upsert` 由此发起；
- **任务策略**：`StatusPolicy` 仅对字段变更进行过滤，禁止直接写事实；
- **幂等保证**：以 key/hash 校验重复写入，重复写入仅增日志，不覆盖 key。

### 5.3 观测口径（Must Have）
- 写入统一输出日志字段：`task_id/step/phase/provider/elapsed_ms`（符合 constraints 3.1）
- 任何 key 写入必须记录 `write_source` 与 `before/after` 以便排障。

---

## 6. v1.9 Roadmap DoD 对齐（ScenePack/TaskPlan/AssetLibrary/Pack增强）
- **Scene Pack**：仅见目录创建逻辑（`gateway/app/main.py:61`），未见 manifest/scene pack schema 或任务映射实现 → **未达成**。
- **TaskPlan/Tools Hub**：代码库无 `TaskPlan`/`tool_chain`/`plan_hooks` 相关实现 → **未达成**。
- **Asset Library**：仅有 assets 目录与 pack 内 assets 字段，无可检索/可复用资产索引 → **未达成**。
- **Smart Pack v1.9 增强层**：未发现新增 pack 交接卡等结构；当前以旧 pack 逻辑为主 → **未达成**。

---

## 7. PR 切分与 Gate（至少 PR-1/PR-2/PR-3）
### PR-1（P0）：Deliverables 真相源 + repo.upsert 收敛
- **改动范围**：将 pack_key/publish_key 写入统一入口；状态从事实派生；替换散落 upsert
- **文件清单**：`gateway/app/services/status_policy/utils.py`、`gateway/app/services/steps_v1.py`、`gateway/app/routers/tasks.py`、新增 writer 类
- **回归证据**：至少 1 条任务从 local_upload → pack 完成日志含 `AUTO_PIPELINE_DONE`
- **回滚点**：保持旧字段写入逻辑可通过 feature flag 暂时恢复
- **Gate**：Smart Pack 校验通过 + v1.85 主链路不回退

### PR-2（P1）：/api 与 /v1 通道语义收敛
- **改动范围**：统一鉴权入口；建立 /v1 → /api 兼容桥或明确唯一前端路径
- **文件清单**：`gateway/main.py`、`gateway/app/main.py`、`gateway/app/routers/tasks.py`
- **回归证据**：Route inventory + /api 与 /v1 返回码一致性检查
- **回滚点**：保留原路由注册，新增可选开关

### PR-3（P1）：Scene Pack / TaskPlan / Asset Library 最小落地
- **改动范围**：最小 schema + 任务映射 + 资产索引写入
- **文件清单**：新增 `scene_packs/*` 或 `models/*` + `repositories/*`
- **回归证据**：2 条任务生成 scene pack manifest；TaskPlan 能保存/展示
- **回滚点**：新路由/字段可通过版本前缀或 feature flag 关闭

---

## 8. 附录：证据索引（含 .review_artifacts/v1.9/*.txt）
- 本仓库未发现 `.review_artifacts/v1.9/*.txt` 文件；仅存在 `.review_artifacts/v1.9CODEX_REVIEW_PROMPT.md`（无 v1.9 子目录与 txt 证据）。
- 主要证据参考：
  - `gateway/app/routers/tasks.py:520-535, 785-847, 885-899, 1277-1292`
  - `gateway/app/services/steps_v1.py:1402-1425, 1470-1514, 1550-1585`
  - `gateway/app/services/publish_service.py:126-148`
  - `gateway/app/main.py:115-160`
  - `gateway/main.py:51-56`
  - `gateway/routes/v1_actions.py:39-84`
  - `tests/test_route_inventory.py:8-28`