# ApolloVeo 2.0 — 业务与代码双向对齐评审 (Global Alignment Review)

> **分支**: VeoSop04
> **日期**: 2026-03-18
> **前置**: Phase 1.2 Router Split 完成后的首次全局评审
> **范围**: A 系列产品愿景 × C 系列 RFC 设计 × 当前代码实现 — 三角对齐
> **审查者**: Claude (Architecture Review Session)

---

## 〇、评审摘要 (Executive Summary)

Phase 1.2 Router Split 将 `tasks.py` 从 7196 行拆至 4612 行，新建 `hot_follow_api.py` 2715 行，
完成了**物理分离**。但从 C 系列 RFC 的视角审视，当前代码距离真正的产线合同驱动 (Line-Contract-Driven)
架构仍有**结构性鸿沟**。本报告聚焦三个维度：

| 维度 | 当前状态 | 目标状态 | 差距等级 |
|------|----------|----------|----------|
| 产线合同对齐 (C.5 RFC-0001) | LineRegistry 已注册，但路由层无感知 | 路由/服务按合同装配 | 🔴 大 |
| Skills 行为驱动 (C.3 RFC-0002) | 无 Skills 运行时 | 可组合策略层驱动产线 Agent | 🔴 大 |
| 状态与交付物真相源 (B.2 + E.1) | 四层状态模型已识别，policy_upsert 已收口 | 声明式 Ready Gate + 统一交付物 SSOT | 🟡 中 |

**核心结论**：Router Split 是正确的第一步，但它只解决了"文件太大"的表层问题。
真正的架构演进需要在**合同 → 服务 → 路由**三层建立从 LineRegistry 到端点的完整绑定链。

---

## 一、业务与架构对齐 (A × C × Code)

### 1.1 产品愿景 (A 系列) 与工厂架构 (C.1) 的映射

A 系列定义的核心产品身份：**面向成片交付的 AI 内容生产工厂**。

C.1 将其结构化为三层工厂：

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Result Lines (产线层)                          │
│  Action Replica │ Localization │ Hot Follow │ Script Video│
├─────────────────────────────────────────────────────────┤
│  Layer 2: Supply Support (供给层)                        │
│  Model Supply │ Workflow │ Material │ Remote Exec │ Pack │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Factory Foundation (基座层)                     │
│  Job Registry │ Line Registry │ Worker Gateway │         │
│  Artifact Store │ Asset Sink │ Status Policy │           │
│  Smart Pack │ Publish Hub                                │
└─────────────────────────────────────────────────────────┘
```

**代码对齐评估**：

| C.1 概念 | 代码对应物 | 对齐程度 | 缺口 |
|----------|-----------|----------|------|
| Line Registry | `gateway/app/lines/base.py` — `LineRegistry` 类 | ✅ 已实现 | 仅注册，未被路由/服务消费 |
| Hot Follow Line | `gateway/app/lines/hot_follow.py` — `HOT_FOLLOW_LINE` | ✅ 已注册 | 合同字段仅声明，未约束行为 |
| Status Policy | `services/status_policy/service.py` — `policy_upsert` | ✅ 已收口 | 缺声明式规则引擎 |
| Publish Hub | `_publish_hub_payload()` + `/publish_hub` 端点 | ✅ 已实现 | 与产线合同无关联 |
| Worker Gateway | 无 | ❌ 未实现 | TTS/FFmpeg 调用散落路由层 |
| Asset Sink | 无 | ❌ 未实现 | 产物上传散落各处 |
| Smart Pack | `run_pack_step_v1()` | 🟡 原型 | 无产线感知 |
| Skills Runtime | 无 | ❌ 未实现 | 全部为硬编码策略 |

### 1.2 hot_follow_api.py 对照 RFC-0001 产线合同标准

RFC-0001 (C.5) 定义的产线合同最小字段集：

```yaml
line_id: hot_follow_line
line_name: Hot Follow Line
line_version: 1.9.0
target_result_type: final_video
sop_profile_ref: docs/sop/hot_follow_v1.md
skills_bundle_ref: docs/skills/
deliverable_kinds: [final_video, subtitle, audio, pack]
confirmation_policy:
  before_execute: true
  before_result_accept: true
  before_publish: true
```

**当前 `hot_follow_api.py` 的合同符合度**：

| 合同要求 | 当前实现 | 符合度 |
|----------|---------|--------|
| 独立 line_id | `HOT_FOLLOW_LINE` 已注册 | ✅ |
| 独立 input contract | 无 — `HotFollowComposeRequest` 等是 API schema，不是业务 contract | ❌ |
| 独立 SOP profile | `sop_profile_ref` 指向 `docs/sop/hot_follow_v1.md`（路径存在但未关联） | 🟡 |
| 独立 Skills bundle | `skills_bundle_ref` 指向 `docs/skills/`（目录存在但无 loader） | ❌ |
| 独立 Worker profile | 无 — TTS provider 硬编码在路由层 | ❌ |
| 独立 Deliverable profile | `deliverable_kinds` 已声明但未约束 deliverable 写入 | 🟡 |
| 明确 Asset sink 行为 | `auto_sink_enabled=True` 已声明但无 sink 运行时 | ❌ |
| 明确 Confirmation policy | `confirmation_before_publish=True` 已声明但合成/发布流未读取 | ❌ |

**结论**：`HOT_FOLLOW_LINE` 目前是一个**仪式性声明 (ceremonial declaration)**——
合同已在 `lines/hot_follow.py` 中注册，但整个运行时（路由、服务、状态策略）对这份合同毫无感知。
没有任何代码路径调用 `LineRegistry.for_kind("hot_follow")` 来决定行为。

### 1.3 距离 DDD (领域驱动) 的差距

RFC-0002 (C.3) 定义的 Production Agent 模型：

```
Production Agent = Line Contract + SOP Profile + Skills Bundle + Worker Profile + Deliverable Profile
```

当前实现是**事务脚本 (Transaction Script)** 模式——每个端点函数是一个完整的过程式脚本，
从验证到执行到状态写入全部内联：

```python
# 典型的事务脚本模式 (hot_follow_api.py 中的每个端点)
@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/compose")
def compose_hot_follow_final_video(...):
    task = repo.get(task_id)           # 1. 加载
    if not task: raise 404             # 2. 验证
    lock = _task_compose_lock(...)     # 3. 并发控制
    _policy_upsert(...)               # 4. 状态写入
    result = _hf_compose_final_video() # 5. 执行（629行 God Function）
    _policy_upsert(...)               # 6. 再次状态写入
    return {...}                       # 7. 响应
```

DDD 目标模型应当是：

```python
# 领域驱动模型 (目标)
@hot_follow_api_router.post("/hot_follow/tasks/{task_id}/compose")
def compose_hot_follow_final_video(
    task_id: str,
    request: ComposeRequest,
    line: ProductionLine = Depends(get_line_for_task),  # 合同注入
    composer: CompositionService = Depends(),             # 服务注入
):
    result = composer.compose(task_id, request, line.confirmation_policy)
    return result.to_response()
```

**差距量化**：当前代码需要经过**三次结构性重构**才能抵达 DDD：
1. **Port Merge (Phase 1.3)**：将 39 个从 tasks.py 导入的共享函数下沉到服务层
2. **Service Extraction**：将 `_hf_compose_final_video()` (629行) 和 `get_hot_follow_workbench_hub()` (349行) 提取为独立服务
3. **Contract Binding**：让路由层通过 `LineRegistry.for_kind()` 获取合同，注入到服务

---

## 二、隐患降维打击 — 系统最脆弱链路

### 2.1 四层状态模型：已识别但仍散装

上一轮评审 (review_20260317) 首次提出四层状态模型：

| 层 | 语义 | 来源函数 |
|----|------|---------|
| L1: Pipeline Step Status | `parse=done, subtitles=running` | 各步骤执行函数直接写入 |
| L2: Artifact Existence | `final_exists=true` | `object_exists()` / `object_head()` |
| L3: Currentness | `dub_current=false` | `_hf_audio_matches_expected()` |
| L4: Ready Gate | `compose_ready=false` | `compute_hot_follow_state()` |

**Router Split 后的新隐患**：

四层数据原本散落在一个 7196 行文件中，至少在物理上紧邻。Split 后：
- **L1 写入点**分布在 `tasks.py` (dub/parse/subtitles 步骤) 和 `hot_follow_api.py` (compose/probe 步骤)
- **L2 检查点**在 `hot_follow_api.py` (deliverable helpers)
- **L3 推断**在 `tasks.py` (`_hf_audio_matches_expected`, `_hf_persisted_audio_state`)
- **L4 聚合**在 `hot_follow_state.py` (compute_hot_follow_state)

这意味着**一次状态 bug 的调查需要跨 3 个文件 7000+ 行**。Split 降低了单文件复杂度，
但增加了状态链路的追踪成本。

**脆弱度评估**：🔴 高 — 任何新增步骤或修改门控逻辑都可能在 L1-L4 某一层引入不一致。

### 2.2 Compose 合成链路：629 行 God Function

`_hf_compose_final_video()` 是全系统最高风险单体：

```
_hf_compose_final_video()  [629 行, 9 个内嵌函数]
├── _compose_fail()              # 错误聚合
├── _normalize_target_lang()     # 语言规范化（与 tts_policy 重复）
├── _resolve_target_srt_key()    # SRT 产物定位
├── _escape_subtitles_path()     # FFmpeg 路径转义
├── _bgm_filter_expr()           # BGM 滤镜构建
├── _audio_fit_filter_expr()     # 音频适配滤镜
├── _build_compose_cmd()         # FFmpeg 命令组装
├── _run_compose()               # subprocess 执行
└── _finalize_composite_details()# 结果打包
```

**风险清单**：

| # | 风险 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | **无 subprocess 超时** | 🔴 P0 | 8 个 `subprocess.run()` 调用均无 `timeout` 参数，FFmpeg 卡死将阻塞整个 worker |
| 2 | **无中间产物检查点** | 🟡 P1 | 多步骤 FFmpeg 操作（freeze → overlay → mix → assemble）无中间状态持久化，任一步失败全部重做 |
| 3 | **错误恢复不完整** | 🟡 P1 | `_compose_fail()` 写 `compose_state=failed` 但不清理临时文件，磁盘空间风险 |
| 4 | **内嵌函数不可测** | 🟡 P1 | 9 个内嵌函数无法独立单元测试 |
| 5 | **硬编码音频参数** | 🟢 P2 | `volume=48000` 等参数硬编码，无法通过合同或 Skills 配置 |

### 2.3 tasks.py ↔ hot_follow_api.py 循环依赖

当前双向依赖关系：

```
hot_follow_api.py ──── 39 个 import ────→ tasks.py
                                            │
tasks.py ──── 4 处懒加载 import ────→ hot_follow_api.py
```

这是一个**建筑级结构债务 (structural debt)**：
- 正向依赖 (39 imports) 表明 `hot_follow_api.py` 仍无法独立运行
- 反向懒加载 (4 lazy imports) 是循环引用的临时解法
- 共享函数中 8 个是 `_hf_*` 命名（HF 专属），但因被 tasks.py 的 baseline 路径共用而无法搬迁

**这 39 个 import 按职责分类**：

| 类别 | 数量 | 代表函数 | 应下沉到 |
|------|------|---------|---------|
| 状态写入 | 3 | `_policy_upsert`, `_task_compose_lock`, `_compose_in_progress_response` | `services/compose_policy.py` |
| 任务视图 | 5 | `_task_value`, `_task_key`, `_task_to_detail`, `_task_endpoint`, `_publish_hub_payload` | `services/task_view.py` |
| 语音/TTS | 7 | `_hot_follow_expected_provider`, `_build_hot_follow_voice_options`, `_voice_state_config` 等 | `services/voice_service.py` |
| 合成辅助 | 8 | `_compute_composed_state`, `_compose_error_parts`, `_build_atempo_chain` 等 | `services/compose_service.py` |
| 产物/媒体 | 7 | `_sha256_file`, `_probe_url_metadata`, `_deliverable_url`, `_resolve_hub_final_url` 等 | `services/artifact_service.py` |
| 字幕分析 | 3 | `_count_srt_cues`, `_build_translation_qa_summary`, `_scenes_status_from_ssot` | `services/subtitle_service.py` |
| Pipeline | 4 | `create_task`, `run_task_pipeline`, `rerun_dub`, `DubProviderRequest` | `services/pipeline_service.py` |
| 常量/Auth | 3 | `COMPOSE_RETRY_AFTER_MS`, `api_key_header`, `OP_HEADER_KEY` | `core/constants.py` |

**Phase 1.3 Port Merge 的本质**：将上述 39 个函数从 tasks.py 路由层下沉到 services 层，
消除循环依赖，使两个路由文件都从服务层获取能力而非互相导入。

### 2.4 Workbench Hub 隐式响应契约

`get_hot_follow_workbench_hub()` (349 行) 返回一个**无类型约束的嵌套 dict**，
由 ~20 个 helper 函数拼装。前端 JS (1776 行) 按隐式约定解析这个 dict。

```python
# 当前：隐式契约
return {
    "pipeline_state": {...},    # _hf_pipeline_state() 拼装
    "deliverables": [...],      # _hf_deliverables() 拼装
    "audio_config": {...},      # _hf_audio_config() 拼装
    "compose_plan": {...},      # 从 pipeline_config 提取
    "ready_gate": {...},        # compute_hot_follow_state() 提取
    "voice_options": [...],     # _build_hot_follow_voice_options() 拼装
    "dub_warnings": [...],      # _hf_build_hot_follow_dub_warnings() 拼装
    "translation_qa": {...},    # _build_translation_qa_summary() 拼装
    "operational_defaults": {}, # _hot_follow_operational_defaults() 拼装
    "debug": {...},             # _build_workbench_debug_payload() 拼装
    # ... 更多隐式字段
}
```

**风险**：
- 任何 helper 返回格式变更都可能无声破坏前端
- 无法通过 Pydantic 模型做编译期检查
- 新增字段无规范流程

**建议**：定义 `WorkbenchHubResponse(BaseModel)` 作为显式 API 契约，所有 helper 返回对应子模型。

### 2.5 _run_dub_job() 的 HF 条件分支

`_run_dub_job()` (667 行) 是 tasks.py 中最长的函数，包含大量 HF 专属分支：

- Line 3792-3796: 懒加载 `_hf_subtitle_lane_state`, `_hf_dual_channel_state`, `_hf_target_lang_gate`
- Line 3799-3829: `no_dub_candidate` 早返回（静默内容跳过配音）
- Line 3831-3840: 目标语言门控

这些分支应当由 Skills Runtime 的 **Routing Skills** 驱动（按 RFC-0002 设计），
而非硬编码在路由层。当第二条产线 (Localization) 引入时，
`_run_dub_job()` 将需要更多分支，复杂度将不可控。

---

## 三、工程行动路径 — Top 3 核心任务卡片

### 卡片 1: Port Merge — 消除循环依赖 (Phase 1.3)

```
┌──────────────────────────────────────────────────────────┐
│ TASK-1.3: Port Merge — 共享函数下沉到服务层               │
├──────────────────────────────────────────────────────────┤
│ 优先级: P0 (阻塞所有后续架构演进)                          │
│ 预估影响: tasks.py -800行, hot_follow_api.py 改 import    │
│ 前置条件: Phase 1.2 已完成 ✅                              │
│ 验收标准:                                                 │
│   1. hot_follow_api.py 对 tasks.py 的 import 数 ≤ 5      │
│   2. tasks.py 对 hot_follow_api.py 的懒加载 import = 0   │
│   3. 所有现有测试通过                                      │
│   4. 无 URL 变更                                          │
├──────────────────────────────────────────────────────────┤
│ 执行步骤:                                                 │
│                                                           │
│ Step 1: 新建服务模块                                      │
│   gateway/app/services/                                   │
│   ├── task_view.py          ← _task_value, _task_key,    │
│   │                           _task_to_detail,            │
│   │                           _task_endpoint,             │
│   │                           _publish_hub_payload        │
│   ├── voice_service.py      ← 7 个 voice/tts 函数        │
│   ├── compose_service.py    ← _hf_compose_final_video,   │
│   │                           _compute_composed_state,    │
│   │                           _compose_error_parts,       │
│   │                           _build_atempo_chain,        │
│   │                           _resolve_audio_fit_max_speed│
│   ├── artifact_helpers.py   ← _sha256_file,              │
│   │                           _probe_url_metadata,        │
│   │                           _deliverable_url,           │
│   │                           _resolve_hub_final_url      │
│   └── subtitle_helpers.py   ← _count_srt_cues,           │
│                                _build_translation_qa      │
│                                                           │
│ Step 2: 迁移常量到 core/constants.py                      │
│   COMPOSE_RETRY_AFTER_MS, OP_HEADER_KEY, api_key_header  │
│                                                           │
│ Step 3: 更新 tasks.py 和 hot_follow_api.py 的 import     │
│   两者都从 services/ 导入，不再互相导入                     │
│                                                           │
│ Step 4: 删除所有懒加载 import                              │
│   tasks.py 中 4 处 function-body import 全部消除           │
│                                                           │
│ Step 5: 更新测试文件的 monkeypatch 路径                    │
│   6 个测试文件的 setattr 路径改为新服务模块                  │
│                                                           │
│ 风险控制:                                                  │
│   - 每个 Step 独立 commit，可逐步回滚                      │
│   - Step 1-2 不改变任何行为，纯搬迁                        │
│   - Step 3-4 修改 import 路径，需要 AST 验证               │
└──────────────────────────────────────────────────────────┘
```

### 卡片 2: Compose Service 提取 — 消灭 God Function

```
┌──────────────────────────────────────────────────────────┐
│ TASK-2.0: Compose Service — 合成链路服务化                 │
├──────────────────────────────────────────────────────────┤
│ 优先级: P0 (Hot Follow 运营安全)                           │
│ 预估影响: hot_follow_api.py -700行                        │
│ 前置条件: TASK-1.3 (Port Merge) 完成                      │
│ 验收标准:                                                 │
│   1. _hf_compose_final_video() 不再存在于路由文件中        │
│   2. 所有 subprocess.run() 调用有 timeout 参数             │
│   3. 临时文件在 finally 块中清理                           │
│   4. 9 个内嵌函数可独立单元测试                             │
│   5. 现有合成功能不变                                      │
├──────────────────────────────────────────────────────────┤
│ 执行步骤:                                                 │
│                                                           │
│ Step 1: 新建 services/compose_service.py                  │
│   class CompositionService:                               │
│     def compose(self, task, plan, config) -> ComposeResult│
│     def _freeze_tail(self, ...) -> Path                   │
│     def _overlay_subtitles(self, ...) -> Path             │
│     def _mix_audio(self, ...) -> Path                     │
│     def _assemble_final(self, ...) -> Path                │
│     def _run_ffmpeg(self, cmd, *, timeout=300) -> Result  │
│                                                           │
│ Step 2: 定义 ComposeResult / ComposePlan 数据类            │
│   @dataclass                                              │
│   class ComposePlan:                                      │
│     overlay_subtitles: bool                               │
│     freeze_tail_enabled: bool                             │
│     freeze_tail_cap_sec: int                              │
│     bgm_mix: float                                        │
│     cleanup_mode: str                                     │
│     target_lang: str                                      │
│                                                           │
│ Step 3: 添加 subprocess timeout (300s default)            │
│   所有 subprocess.run() 增加 timeout=timeout_sec          │
│   超时触发 ComposeTimeoutError                             │
│                                                           │
│ Step 4: 添加临时文件清理                                   │
│   使用 tempfile.TemporaryDirectory 上下文管理器             │
│   finally 块确保清理                                       │
│                                                           │
│ Step 5: 路由端点简化为调用服务                              │
│   compose_hot_follow_final_video() 缩减到 ~50 行          │
│                                                           │
│ 安全约束:                                                  │
│   - CompositionService 不直接调用 repo.upsert             │
│   - 状态写入仍由路由端点通过 policy_upsert 执行            │
│   - 服务仅返回 ComposeResult，由调用者决定写入              │
└──────────────────────────────────────────────────────────┘
```

### 卡片 3: 声明式 Ready Gate — 状态模型统一 (Phase 2.3)

```
┌──────────────────────────────────────────────────────────┐
│ TASK-2.3: Declarative Ready Gate — 声明式门控              │
├──────────────────────────────────────────────────────────┤
│ 优先级: P1 (产线扩展前置条件)                               │
│ 预估影响: hot_follow_state.py 重写, 新增 ready_gate.py    │
│ 前置条件: TASK-1.3 完成 (Port Merge)                      │
│ 验收标准:                                                 │
│   1. Ready Gate 规则从 YAML/dict 配置加载，非硬编码         │
│   2. 每条产线可独立声明 Ready Gate 规则                     │
│   3. 四层状态语义有明确的代码边界                            │
│   4. Workbench Hub 使用 Ready Gate 输出，不再自行推断       │
│   5. 现有状态行为不变                                      │
├──────────────────────────────────────────────────────────┤
│ 设计方案:                                                 │
│                                                           │
│ Ready Gate 规则格式 (per-line):                           │
│                                                           │
│   hot_follow_line:                                        │
│     compose_ready:                                        │
│       require_all:                                        │
│         - artifact: raw_path        # L2: 产物存在        │
│         - step: subtitles = done    # L1: 步骤完成        │
│         - condition: |              # L3: 时效性检查       │
│             audio_current OR no_dub                       │
│     publish_ready:                                        │
│       require_all:                                        │
│         - artifact: final_video_key # L2: 成片存在        │
│         - step: compose = done      # L1: 合成完成        │
│                                                           │
│ Step 1: 定义 ReadyGateRule 数据模型                       │
│   @dataclass                                              │
│   class ReadyGateRule:                                    │
│     gate_id: str                                          │
│     require_all: list[GateCondition]                      │
│     require_any: list[GateCondition] = []                 │
│                                                           │
│ Step 2: 将 compute_hot_follow_state() 的规则提取为配置    │
│   保持计算引擎，将硬编码条件替换为规则查询                   │
│                                                           │
│ Step 3: 在 LineRegistry 中增加 ready_gate_ref 字段        │
│   ProductionLine.ready_gate_ref → 指向规则文件             │
│                                                           │
│ Step 4: Workbench Hub 消费 Ready Gate 输出                 │
│   _collect_hot_follow_workbench_ui() 中的门控判断           │
│   改为调用 ReadyGate.evaluate(task)                        │
│                                                           │
│ 长期价值:                                                  │
│   - Localization Line 只需声明自己的 Ready Gate 规则       │
│   - 不需要写新的 compute_localization_state() 函数         │
│   - 规则可版本化、可审计、可测试                             │
└──────────────────────────────────────────────────────────┘
```

---

## 四、补充发现

### 4.1 hot_follow_api.py 代码质量指标

| 指标 | 数值 | 评价 |
|------|------|------|
| 端点数 | 14 (含 1 个 deprecated) | 合理 |
| Helper 函数 | 39 | 偏多，应拆分到服务层 |
| 从 tasks.py 导入 | 39 个符号 | 🔴 过高，应 ≤ 5 |
| policy_upsert 调用 | 16 次 | 散落分布，缺统一策略 |
| subprocess 调用 | 8 次（均无 timeout） | 🔴 运营风险 |
| 100+ 行函数 | 3 个 (629/349/178) | 🟡 需要提取 |
| Pydantic 响应模型 | 0 (全部返回 dict) | 🟡 缺契约约束 |
| 未使用 import | 1 (threading) | 🟢 轻微 |

### 4.2 tasks.py 残留结构债务

| 项目 | 说明 |
|------|------|
| `_run_dub_job()` 667 行 | 全系统第二大函数，HF 分支应由 Skills Routing 驱动 |
| `compose_task()` 168 行 | HF 早返回逻辑应由合同的 confirmation_policy 驱动 |
| `task_workbench_page()` HF 分支 | 页面路由层不应包含业务逻辑 |
| 43 次 policy_upsert 调用 | 分散在所有步骤函数中 |

### 4.3 与 OpenClaw (C.4 RFC-0003) 的接口缝

RFC-0003 定义的控制协议：`create_line_job → confirm_execution → confirm_result → confirm_publish`

当前代码中 **无任何** OpenClaw 相关实现。但这是**预期内的**——RFC-0003 明确将 OpenClaw 定位为
"执行网格"而非核心业务层，且 C.2 评审结论将其列为 P2 优先级。

**建议**：在 TASK-2.3 (Ready Gate) 完成后，作为 Phase 3 的一部分引入 OpenClaw Gateway stub，
读取合同的 `confirmation_policy` 来决定是否需要 OpenClaw 确认。

---

## 五、路线图总览

```
当前位置
    │
    ▼
[Phase 1.2 ✅] Router Split
    │                     tasks.py 7196→4612, hot_follow_api.py 2715
    │
    ▼
[Phase 1.3 🔜] Port Merge ← TASK-1.3 (本报告 卡片1)
    │                     消除循环依赖, 39 imports → ≤5
    │
    ▼
[Phase 2.0 🔜] Compose Service ← TASK-2.0 (本报告 卡片2)
    │                     God Function 629行 → CompositionService
    │
    ▼
[Phase 2.3 🔜] Declarative Ready Gate ← TASK-2.3 (本报告 卡片3)
    │                     硬编码门控 → 声明式规则配置
    │
    ▼
[Phase 2.2] Skills MVP
    │           Routing Skills 驱动 _run_dub_job() 的 HF 分支
    │
    ▼
[Phase 3.1] Localization Line
    │           第二条产线，验证合同/Skills/ReadyGate 的可复用性
    │
    ▼
[Phase 3.2] OpenClaw Gateway Stub
              confirmation_policy 驱动的外部确认网关
```

---

## 六、术语对齐表 (按 C.2 要求)

| 术语 | 定义 | 代码对应 |
|------|------|---------|
| Production Line | 面向单一目标结果的业务执行单元 | `ProductionLine` dataclass |
| Line Contract | 产线的最小声明合同 | `lines/hot_follow.py` |
| Line Registry | 全局产线注册表 | `LineRegistry` class |
| Production Agent | 合同+SOP+Skills+Worker+Deliverable 的运行时组合 | ❌ 未实现 |
| SOP Profile | 产线的标准操作规程 | `docs/sop/` (文件存在，未关联) |
| Skills Bundle | 可组合的行为策略包 | `docs/skills/` (目录存在，无 loader) |
| Worker Profile | 产线的执行者配置（模型/API/本地） | ❌ 未实现 |
| Deliverable Profile | 产线产出物的种类与规则 | `deliverable_kinds` 字段 (仅声明) |
| Asset Sink | 产物自动沉淀到资产库 | `auto_sink_enabled` 字段 (仅声明) |
| Ready Gate | 复合门控判断（是否可进入下一步） | `compute_hot_follow_state()` |
| Status Policy | 状态写入的唯一策略层 | `policy_upsert()` |
| Smart Pack | 智能打包（多交付物组合） | `run_pack_step_v1()` (原型) |
| Publish Hub | 发布中心（交付物聚合+发布操作） | `_publish_hub_payload()` |
| OpenClaw | 工厂控制与执行网格 | ❌ 未实现 (P2) |

---

## 七、本报告生成的可追踪行动项

| ID | 任务 | 优先级 | 阻塞关系 | 状态 |
|----|------|--------|---------|------|
| TASK-1.3 | Port Merge: 39 imports 下沉到 services | P0 | 阻塞 TASK-2.0, TASK-2.3 | 🔜 待开始 |
| TASK-2.0 | Compose Service: 提取 629 行 God Function | P0 | 依赖 TASK-1.3 | 🔜 待开始 |
| TASK-2.3 | Declarative Ready Gate: 声明式门控规则 | P1 | 依赖 TASK-1.3 | 🔜 待开始 |
| TASK-2.2 | Skills MVP: Routing Skills 驱动配音分支 | P1 | 依赖 TASK-2.3 | 📋 规划中 |
| TASK-3.1 | Localization Line: 第二条产线 | P2 | 依赖 TASK-2.2, TASK-2.3 | 📋 规划中 |
| TASK-3.2 | OpenClaw Gateway Stub | P2 | 依赖 TASK-2.3 | 📋 规划中 |

---

> **附录**: 本报告基于以下输入文档生成：
> - `_drafts/A.1`, `_drafts/A.2` — 产品说明书 (docx, 仅元数据可读)
> - `_drafts/B.2` — v1.9 REVIEW BASELINE
> - `_drafts/C.1` — 2.0 工厂式架构定位与产线定义
> - `_drafts/C.2` — 评审结论与 RFC 草案决策
> - `_drafts/C.3` — RFC-0002 Skills Runtime
> - `_drafts/C.4` — RFC-0003 OpenClaw Integration
> - `_drafts/C.5` — RFC-0001 Production Line Contract
> - `_drafts/E.1` — Hot Follow 当前现状与 abs
> - `docs/reviews/review_20260317.md` — 上轮代码评审报告
> - `docs/architecture/v1.9/STATUS_AND_DELIVERABLES_SPEC.md` — 状态与交付物规范
> - `docs/archive/contracts/HOT_FOLLOW_API_CONTRACT_v1.md` — HF API 契约（historical）
> - `gateway/app/lines/base.py` + `hot_follow.py` — LineRegistry 实现
> - `gateway/app/routers/hot_follow_api.py` — 2715 行完整结构分析
> - `gateway/app/routers/tasks.py` — 4612 行完整结构分析
