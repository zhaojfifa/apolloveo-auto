# 1. Review Basis

本轮 review 直接依据以下材料：

- `docs/execution/NEXT_ENGINEERING_ANALYSIS_AND_PLAN.md`
- `docs/reviews/ALIGNMENT_BASELINE_20260318.md`
  说明：用户给出的路径为 `docs/ALIGNMENT_BASELINE_20260318.md`，仓库中实际存在的是 `docs/reviews/ALIGNMENT_BASELINE_20260318.md`，本轮以实际文件为准
- `_drafts/C.3 RFC-0002_Skills_Runtime_and_Production_Agent_Framework.md`
- `_drafts/C.5 RFC-0001_Production_Line_Contract.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

本轮新增的“扫雷优先”约束，实质上改变的不是方向，而是执行顺序：

- 原先可以并行讨论的 line runtime、第二条产线、OpenClaw、平台层扩张，现在必须后置。
- `TASK-1.3`、`TASK-2.0`、`TASK-2.3` 不再是“建议修补项”，而是明确的前置扫雷包。
- `TASK-2.2 Skills MVP` 不能再被当作“未来平台能力”，而必须作为扫雷后的第一阶段建设项。
- 在 `1.3 / 2.0 / 2.3` 未真正收口前，不应再推进第二条标准产线。

本轮 review 的判断标准因此从“是否方向正确”切换为“是否真正解除结构爆点、是否足以进入 Skills MVP”。


# 2. Reconfirmed Current Stage

当前阶段应重新确认如下：

- 不是 2.0 大平台建设期。
- 不是第二条产线扩张期。
- 不是 OpenClaw 接入期。

当前阶段是：

- `v1.9` 基座收口
- `VeoSop04` Router Split 后续扫雷
- Hot Follow 第一条标准产线候选的运行时收口
- Skills MVP 前置准备阶段

当前最重要的问题仍然是结构性爆点，而不是能力数量：

- `gateway/app/routers/tasks.py` 与 `gateway/app/routers/hot_follow_api.py` 仍未解环
- Compose 主链虽已抽出，但主流程仍未摆脱 router 级 orchestration
- Ready Gate 已有规则引擎，但还没有进入 line contract 驱动主链
- Skills 仍停留在 RFC 和目录骨架，尚未形成最小 runtime

因此，原先任何“先复制第二条标准产线验证架构”的思路，现在都应被推翻。现阶段正确路径是：

1. 扫雷排险
2. 声明式门控收口
3. Skills MVP
4. 才能讨论第二条产线和更大平台层


# 3. TASK-1.3 Status

## Landed

`TASK-1.3 Port Merge` 已完成第一轮 helper 下沉，是真实落地，不是纯文档宣称。

已确认落地文件：

- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/voice_state.py`
- `gateway/app/services/compose_helpers.py`
- `gateway/app/services/media_helpers.py`
- `gateway/app/core/constants.py`

`gateway/app/routers/hot_follow_api.py` 顶部也已改为主要从这些 service/core 模块取共享能力，而不是继续批量直接从 `tasks.py` 导入。

## Partial

`TASK-1.3` 目前只能判定为 **Partial**，不能判定为 Landed。

原因不是 helper 没拆，而是“解环目标”没有完成。

当前仍存在双向 import / 懒加载：

- `gateway/app/routers/hot_follow_api.py`
  - 懒加载 `create_task`
  - 懒加载 `rerun_dub`
  - 懒加载 `run_task_pipeline`
- `gateway/app/routers/tasks.py`
  - 懒加载 `_hot_follow_operational_defaults`
  - 懒加载 `_safe_collect_hot_follow_workbench_ui`
  - 懒加载 `_hf_task_status_shape`
  - 懒加载 `_maybe_run_hot_follow_lipsync_stub`
  - 懒加载 `_hf_compose_final_video`
  - 懒加载 `get_hot_follow_workbench_hub`
  - 懒加载 `_hf_subtitle_lane_state`
  - 懒加载 `_hf_dual_channel_state`
  - 懒加载 `_hf_target_lang_gate`

这说明两个 router 仍然知道彼此内部实现，Port Merge 还停在“函数搬迁”，没有完成“运行时依赖切断”。

## Missing

缺失的核心不是更多 helper 拆分，而是以下运行时能力：

- line callback registry 或 scene/runtime provider
- 可替代懒加载 import 的服务装配层
- 把 `tasks.py` 中 Hot Follow 专属 orchestration 移出总路由
- 把 `hot_follow_api.py` 中仍依赖总路由入口的动作能力移出 router

也就是说，Port Merge 还缺最后一公里：**从文件拆分走到依赖图闭合**。

## Drift

`TASK_1_3_PORT_MERGE_PLAN.md` 的验收标准写的是：

- `hot_follow_api.py` 对 `tasks.py` 的 import 数 ≤ 5
- `tasks.py` 对 `hot_follow_api.py` 的懒加载 import = 0

当前代码与该验收标准明显漂移：

- `tasks.py` 对 `hot_follow_api.py` 的懒加载 import 仍不为 0
- `tasks.py` 中 `/api/tasks/{task_id}/compose` 仍反向调用 Hot Follow 的 compose wrapper 和 hub 组装函数
- `task_workbench_page()` 仍需要知道 Hot Follow 的 UI 聚合实现

结论：

- `TASK-1.3` 状态 = **Partial + Drift**


# 4. TASK-2.0 Status

## Landed

`TASK-2.0 Compose Service` 已真实落地，且解决了最危险的运行时问题。

已确认：

- `gateway/app/services/compose_service.py` 已存在，约 856 行
- `gateway/app/routers/hot_follow_api.py` 中 `_hf_compose_final_video()` 已降为 thin wrapper
- FFmpeg 调用已统一收口到 `CompositionService._run_ffmpeg()`
- `_run_ffmpeg()` 已统一加 `timeout`
- 已有结构化日志点：
  - `COMPOSE_SUBPROCESS_START`
  - `COMPOSE_FFMPEG_CMD`
  - `COMPOSE_DONE`
- probe / clamp / freeze-tail 等调用均已进入统一超时边界

这意味着 baseline 里“629 行 God Function + 无 timeout”的 P0 风险，已经被明显削弱。

## Partial

`TASK-2.0` 仍不能判定为 fully landed，只能判定为 **Partial**。

原因：

- `_hf_compose_final_video()` 仍存在于 `gateway/app/routers/hot_follow_api.py`
  - 虽然已经只是 wrapper，但调用者仍然继续依赖 router 层函数名，而不是直接依赖 compose service
- `gateway/app/routers/tasks.py` 的 `/api/tasks/{task_id}/compose` 仍反向懒加载 `_hf_compose_final_video()`
- compose 前置状态写入、plan patch、hub 返回、异常映射，仍主要在 router 中完成
- 目前没有显式 cancel / abort 边界
- 目前没有独立的 compose contract/result model，返回仍是大 dict

所以 task2.0 完成的是“God Function 拆离 + timeout 注入”，没有完成“Compose 主链服务化闭环”。

## Missing

当前仍缺：

- 面向 line runtime 的 compose service 装配入口
- 独立的 `ComposeResult` / deliverable contract 对外契约
- 从 `tasks.py` 中彻底移除对 Hot Follow compose wrapper 的依赖
- 针对 `compose_service.py` 的直接单测覆盖
- 清晰的 cancel / interruption 设计

换句话说，task2.0 解决了“炸弹会不会立刻爆”，但还没解决“合成链是不是已经从 router 脱身”。

## Drift

`TASK_2_0_COMPOSE_SURGERY.md` 的核心叙事是：

- God Function 已迁出路由
- 路由应该变成 thin wrapper
- tasks.py 调用方不动

实际代码的漂移点在于：

- `hot_follow_api.py` 里的 wrapper 仍承担了兼容锚点，外部继续按旧函数名调用
- `tasks.py` 仍直接知道 Hot Follow compose 的内部接入点
- compose 仍不是一个可按 line contract 注入的 runtime 能力

结论：

- `TASK-2.0` 状态 = **Landed on safety, Partial on architecture, Drift on runtime closure**


# 5. TASK-2.3 Status

## Landed

`TASK-2.3` 的规则引擎本体已经真实落地。

已确认：

- `gateway/app/services/ready_gate/engine.py`
- `gateway/app/services/ready_gate/hot_follow_rules.py`
- `gateway/app/services/status_policy/hot_follow_state.py`

当前 `compute_hot_follow_state()` 已采用三段式：

1. `_resolve_artifacts()`
2. `evaluate_ready_gate(HOT_FOLLOW_GATE_SPEC, task, state)`
3. `_apply_gate_side_effects()`

并且最小纯规则测试可直接通过：

- `python3 -m pytest gateway/app/services/status_policy/tests/test_ready_gate.py -q`

这说明 `TASK-2.3` 的核心引擎不是空文档，而是可运行模块。

## Partial

`TASK-2.3` 只能判定为 **Partial**，因为它解决的是 Hot Follow 内部规则表达，不是整条门控主链正式化。

当前仍然存在：

- `HOT_FOLLOW_GATE_SPEC` 仍是代码常量，不是被 line contract 引用的正式 profile
- `compute_hot_follow_state()` 仍直接 import `HOT_FOLLOW_GATE_SPEC`
- `LineRegistry` 没有接管 ready gate
- `status_policy/registry.py` 仍不是 line-aware 的装配机制
- workbench / publish / compose 的 gate 消费仍主要靠 Hot Follow 局部聚合逻辑

因此，task2.3 完成的是“从 if/else 到规则对象”，不是“从规则对象到 runtime binding”。

## Missing

缺失的关键项：

- line contract 到 ready gate spec 的绑定字段
- line-aware status policy 装配
- publish gate / workbench gate 的统一 contract
- 配置化 profile 入口
- 多产线复用所需的规则选择机制

## Drift

原始任务目标强调的是“声明式门控是后续 line runtime、status policy、ready gate 正式化的前提”。

当前代码的漂移点在于：

- 规则已经声明式，但只在 Hot Follow 内部局部生效
- 没有进入 line runtime 主链
- 没有真正完成“文档中的 line contract 接管门控”

结论：

- `TASK-2.3` 状态 = **Landed on engine, Partial on integration, Drift on contract binding**


# 6. Skills MVP Readiness

当前**还不具备直接推进 `TASK-2.2 Skills MVP` 的完整工程条件**，但已经具备开始做 Skills MVP 设计与最小骨架的前置条件。

## 已具备的条件

- 总基线已明确 Skills 是行为策略层，而不是任务真相源
- `docs/skills/` 目录已存在
- `docs/architecture/line_contracts/hot_follow_line.yaml` 已有 `skills_bundle_ref`
- `_drafts/C.3 RFC-0002_Skills_Runtime_and_Production_Agent_Framework.md` 已给出目录建议和边界约束

## 当前前置缺口

### 缺口 1：`TASK-1.3` 未完成解环

如果 router 仍互相懒加载，Skills hook 没有稳定挂载点。此时引入 Skills，只会把策略逻辑再塞回 `tasks.py` 或 `hot_follow_api.py`。

### 缺口 2：`TASK-2.0` 还未从 runtime 角度闭环

Compose 目前仍通过 router wrapper 暴露。若现在引入 `media-compose` 或 `routing` skills，会继续绑定到兼容 wrapper，而不是绑定到稳定 service/runtime 接口。

### 缺口 3：`TASK-2.3` 还未挂入 line contract

Skills 最终需要与 line contract 协同，但现在 line contract 仍不驱动 ready gate、status policy、worker 选择。此时引入 Skills，只会得到新的“文档有、运行时弱绑定”层。

### 缺口 4：没有 Skills loader / hook runtime

当前仓库里能看到的是：

- `docs/skills/README.md`
- `docs/skills/compliance/.gitkeep`
- `docs/skills/content/.gitkeep`
- `docs/skills/language/.gitkeep`
- 若干 Markdown 文档

没有看到：

- bundle loader
- runtime hook
- profile parser
- line-aware skills registry

## 结论

`TASK-2.2 Skills MVP` 的正确时机是：

- 在 `TASK-1.3` 解环完成后
- 在 `TASK-2.0` 的 router 兼容依赖进一步收口后
- 在 `TASK-2.3` 至少完成 line contract 级绑定后

但这不意味着要等所有平台层都完成。正确做法是：

- 先完成扫雷包
- 然后立刻做最小 Skills MVP
- 不要在 Skills MVP 之前启动第二条标准产线


# 7. Revised Engineering Priority Plan

## P0：扫雷排险

### P0-1 完成 Port Merge 最后一公里

目标：

- 彻底解除 `tasks.py` 与 `hot_follow_api.py` 的双向 import / 懒加载

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

当前原因：

- 这是 Router Split 留下的致命结构债
- 不解环，后续改动会持续在总路由和场景路由之间回流

### P0-2 收口 Compose 主链依赖

目标：

- 让 compose 进入稳定 service 接口，而不是继续经由 router wrapper 和 router 反向调用

涉及目录：

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`

当前原因：

- 虽然超时风险已处理，但 runtime 依赖仍不干净
- 若不收口，后续 Skills 只能继续绑在 router 兼容层上

### P0-3 冻结验证基线

目标：

- 明确 Python 版本、测试入口、Hot Follow 基线回归集

涉及目录：

- `docs/`
- `gateway/requirements.txt`

当前原因：

- 现有纯 ready-gate 测试可跑，但依赖 router/config 的测试被 Python 3.9 阻断
- 如果不冻结验证基线，后续每个任务包都难以可靠验收

## P1：声明式门控收口

### P1-1 让 line contract 接管 ready gate / status policy

目标：

- 从“规则引擎存在”推进到“line contract 驱动规则选择”

涉及目录：

- `gateway/app/lines/`
- `gateway/app/services/ready_gate/`
- `gateway/app/services/status_policy/`
- `docs/architecture/line_contracts/`

### P1-2 显式化 workbench / publish gate contract

目标：

- 避免继续用大 dict 和 UI 逻辑兜底 gate 语义

涉及目录：

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/static/js/hot_follow_workbench.js`
- `docs/contracts/`

## P1/P2：Skills MVP

### P1/P2-1 最小 Skills loader

目标：

- 让 `skills_bundle_ref` 从目录路径变成可解析的最小 bundle

涉及目录：

- `docs/skills/`
- `gateway/app/lines/`
- `gateway/app/services/`

### P1/P2-2 最小 hook 挂点

目标：

- 只支持最必要的三类 hook：
  - routing
  - compliance
  - media-compose policy

涉及目录：

- `gateway/app/services/`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`
- `gateway/app/services/compose_service.py`

### P1/P2-3 不做的事情

此阶段明确不做：

- 通用 agent 平台
- 多 line runtime 扩张
- OpenClaw 深接入
- 第二条产线复制

## P2 之后：第二条产线 / 更大平台层

只有在以下条件满足后，第二条产线才应启动：

- `TASK-1.3` 真正解环
- `TASK-2.0` 从 runtime 角度收口
- `TASK-2.3` 进入 line contract 绑定
- Skills MVP 已可挂载到 Hot Follow

在此之前，任何继续推进 Localization / Action Replica 标准产线的动作，都应视为**抢跑**。


# 8. Immediate PR / Task Proposal

## PR-1：Router De-Coupling Final Pass

目标：

- 移除 `tasks.py` 与 `hot_follow_api.py` 的剩余双向 import / 懒加载

涉及目录：

- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

风险：

- 直接触及主链入口
- 容易把 Hot Follow 专属逻辑重新散回总路由

验收标准：

- `rg` 检索不到两文件互相 import
- `tasks.py` 不再调用 `_hf_compose_final_video`、`get_hot_follow_workbench_hub`、`_hf_*` 路由 helper
- `hot_follow_api.py` 不再懒加载总路由动作函数

是否需要文档先行：

- 需要，先补一页 runtime 装配说明

## PR-2：Compose Runtime Closure

目标：

- 让 compose 主链只通过 service 能力暴露，进一步削薄 router 兼容层

涉及目录：

- `gateway/app/services/compose_service.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/routers/tasks.py`

风险：

- 影响 compose 状态写入、hub 返回、异常映射
- 若和 PR-1 交叉过深，容易产生回归

验收标准：

- router 中 `_hf_compose_final_video()` 不再是外部兼容锚点
- `tasks.py` compose 路径不再反向依赖 Hot Follow router
- compose service 有直接测试入口

是否需要文档先行：

- 不必须单独先写，但应依附于 PR-1 的 runtime 装配说明

## PR-3：Ready Gate Contract Binding

目标：

- 把 `HOT_FOLLOW_GATE_SPEC` 从 Hot Follow 局部规则提升为 line contract 可引用对象

涉及目录：

- `gateway/app/lines/`
- `gateway/app/services/ready_gate/`
- `gateway/app/services/status_policy/`
- `docs/architecture/line_contracts/`

风险：

- 若设计过度，会提前滑向大平台

验收标准：

- line contract 可追溯到 ready gate spec
- `compute_hot_follow_state()` 不再硬编码 Hot Follow 规则源
- status policy 装配具备 line-aware 入口

是否需要文档先行：

- 需要，先补 line contract 与 gate binding 说明

## PR-4：Workbench Contract Typing

目标：

- 为 `get_hot_follow_workbench_hub()` 建立显式响应模型

涉及目录：

- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/domain/` 或新建 `gateway/app/contracts/`
- `docs/contracts/`

风险：

- 前端依赖隐式字段，兼容性要谨慎

验收标准：

- `response_model=None` 被替换
- `artifact_facts`、`current_attempt`、`operator_summary`、`ready_gate` 有显式 schema
- 现有前端字段保持兼容

是否需要文档先行：

- 需要，先冻结 API contract

## PR-5：Skills MVP Skeleton

目标：

- 建最小 skills bundle loader 与三类 hook

涉及目录：

- `docs/skills/`
- `gateway/app/services/`
- `gateway/app/lines/`

风险：

- 如果在解环前启动，会反向把策略塞回 router

验收标准：

- `skills_bundle_ref` 可被解析
- 至少支持 routing / compliance / media-compose 三类最小 hook
- Hot Follow 能挂第一个最小 bundle

是否需要文档先行：

- 需要，必须先冻结 Skills MVP scope

## PR-6：Verification Baseline Doc

目标：

- 明确当前分支的运行与测试解释器基线

涉及目录：

- `docs/`
- `gateway/requirements.txt`

风险：

- 风险低，但容易被忽略，结果是后续所有“验收”继续口头化

验收标准：

- 文档明确 Python 最低版本
- 文档列出 Hot Follow 基线回归命令
- CI 或本地执行前提清晰

是否需要文档先行：

- 本任务本身就是文档先行
