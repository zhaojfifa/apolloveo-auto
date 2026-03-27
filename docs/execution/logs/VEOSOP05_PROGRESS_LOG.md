# VeoSop05 启动进度文档

## PR-1 Runtime Contract Freeze

日期：2026-03-19

本节点冻结以下文档边界：

- Hot Follow runtime contract
- Compose service contract
- Gate binding contract
- Verification baseline

本次冻结的核心边界：

- `tasks.py` / `hot_follow_api.py` / service / line contract 的职责边界先文档收口，不改业务逻辑
- `CompositionService.compose()` 是当前 compose 主体，`_hf_compose_final_video()` 仍是兼容 wrapper
- `HOT_FOLLOW_GATE_SPEC` 是当前 ready gate spec 来源，但尚未由 line contract 运行时接管
- Python 3.10+ 是后续 Hot Follow 本地/CI 验证的最低基线

本次明确后置的实现：

- router 解环的实际代码收口
- compose 调用方从 router wrapper 迁出
- line-aware status policy / ready gate runtime 装配
- skills runtime
- 第二条产线扩展

本节点输出文档：

- `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- `docs/contracts/COMPOSE_SERVICE_CONTRACT.md`
- `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
- `docs/runbooks/VERIFICATION_BASELINE.md`

## PR-3 Compose Runtime Closure

日期：2026-03-19

本节点完成：

- 将 Hot Follow compose 主链编排收口到 `gateway/app/services/compose_service.py`
- 为 compose 增加明确的 request / response contract
- 让 `tasks.py` 与 `hot_follow_api.py` 的 compose 路由只保留 request parsing / response mapping
- 为 compose service 增加 direct test entry

本次削薄的 wrapper / router：

- `gateway/app/routers/tasks.py::compose_task()`
  - 不再直接编排 compose plan、状态写入、短路返回、异常回写
- `gateway/app/routers/hot_follow_api.py::compose_hot_follow_final_video()`
  - 不再保留重复的 compose orchestration
- `gateway/app/routers/hot_follow_api.py::_hf_compose_final_video()`
  - 保留为兼容 wrapper，不再作为主链入口

本节点后置保留：

- gate binding / line-aware status policy 仍留给 PR-4
- `_hf_allow_subtitle_only_compose` / `_resolve_target_srt_key` 仍是 Hot Follow 兼容 helper，后续可继续从 router 退出

## PR-4 Gate Binding + Verification Baseline

日期：2026-03-19

本节点完成：

- 将 `hot_follow_line -> ready_gate_ref -> HOT_FOLLOW_GATE_SPEC` 的最小 runtime 绑定落到代码
- 为 status policy 增加 `get_status_runtime_binding(task)` 作为最小 line-aware 装配入口
- 让 `compute_hot_follow_state()` 通过 runtime binding 消费 gate spec，而不是继续直接 import 规则源
- 冻结系统 `python3` 与 `./venv/bin/python` 的最小验证职责边界

本次新增或更新的最小绑定点：

- `gateway/app/lines/base.py`
  - 增加 `ready_gate_ref` / `status_policy_ref`
- `gateway/app/lines/hot_follow.py`
  - 明确声明 Hot Follow line 的 `ready_gate_ref` / `status_policy_ref`
- `gateway/app/services/ready_gate/registry.py`
  - 负责 `LineRegistry.for_kind(task.kind) -> ready_gate spec`
- `gateway/app/services/status_policy/registry.py`
  - 提供 `get_status_runtime_binding(task)`
- `gateway/app/services/status_policy/hot_follow_state.py`
  - 改为消费 runtime 绑定出来的 `ready_gate_spec`

本节点验证冻结：

- 系统 `python3` 当前为 `Python 3.9.6`
- `./venv/bin/python` 当前为 `Python 3.11.15`
- 最低纯单测与推荐 3.10+ 回归命令已写入 `docs/runbooks/VERIFICATION_BASELINE.md`

本节点明确不做：

- 不扩大 router / bridge 职责
- 不继续改 compose 主链
- 不启动 Skills MVP
- 不扩第二条产线

## PR-5 Parse Status + Subtitle SRT-First Consistency Fix

日期：2026-03-19

本节点修复：

- parse 实际已成功但 UI 仍显示 failed 的一致性问题
- Hot Follow 工作台中目标语言字幕编辑对象的 SRT-first 语义不够明确的问题

本次收口的边界：

- parse 状态改为优先由 raw artifact / fact 推导
  - `raw_video done`
  - `raw_url`
  - `source_video.url`
  - `raw=ready`
- 目标语言字幕编辑区明确为 `mm.srt` 对应的 SRT 主对象
- 辅助输入 / OCR 候选 / 标准化来源文本明确降级为 helper-only 语义，不再与主 SRT 对象混淆

本节点明确不做：

- 不改 translation generation
- 不改 dubbing logic
- 不改 compose runtime policy
- 不扩大 router 重构范围

## PR-6 Compose Duration Must Be Video-Master

日期：2026-03-19

本节点修复：

- Hot Follow formal compose path 在短音频场景下被 `-shortest` 截断，导致最终时长错误跟随音频的问题
- compose plan 声明为 `match_video` / `freeze_tail` 时，runtime ffmpeg 行为与视频主时长不一致的问题

本次收口的 runtime 边界：

- `gateway/app/services/compose_service.py`
  - formal compose path 不再依赖 `-shortest` 决定输出时长
  - `match_video` 下，短音频通过 `apad + atrim` 补齐到视频时长
  - `match_video` 下，长音频通过 `atrim + afade` 裁到视频时长
  - freeze-tail 成功后，compose 主时长改为冻结后的视频时长，而不是原始视频时长

本节点对 `freeze_tail` 的真实状态说明：

- 当前为部分实现
- 当音频长于视频且所需 hold 时长未超过 cap 时，会先做 `tpad` 冻尾再进入 compose
- 本节点不引入更复杂的高级 policy 框架，只保证 formal path 始终是 video-master

本节点明确后置：

- 不扩 compose policy family
- 不改 router / workbench / parse 逻辑
- 不启动 Skills 或第二条产线

## PR-7 Stage Closure Docs + Business Regression Freeze

日期：2026-03-19

本节点完成：

- 冻结 `docs/execution/VEOSOP05_STAGE_CLOSURE.md`
- 冻结 `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
- 冻结 `docs/execution/NEXT_HOT_FOLLOW_CLEANUP_SCOPE.md`

本次执行对齐结论：

- `VeoSop05` 阶段收口说明已固化
- Hot Follow business validation 已升级为 mandatory merge gate，而不是可选补充验证
- 下一步工作仍严格限制在 Hot Follow cleanup 内

本节点明确不做：

- 不改任何 runtime logic
- 不启动 Skills implementation
- 不扩第二条产线
- 不做平台层扩张

## PR-A1 Thin tasks.py Further Without Behavior Change

日期：2026-03-19

本节点完成：

- 将 `tasks.py` 中的 Hot Follow workbench `task_json` enrich 迁出到窄职责 presenter
- 将 `tasks.py` 中的 task detail stale/status-shape payload 组装迁出到窄职责 presenter

本次收口说明：

- `tasks.py` 继续只保留 request parsing、entry、dispatch 与 response/log mapping
- 迁出的逻辑属于 line-/presentation-specific assembly，不涉及 runtime policy 变更
- 未引入新的 router-to-router coupling，也未让 bridge 文件承担新的状态治理职责

本节点明确不做：

- 不改 compose policy
- 不改 gate binding
- 不改 Skills runtime
- 不扩第二条产线

## PR-A2 Isolate Compatibility-Only Helpers Before Skills Entry

日期：2026-03-19

本节点完成：

- 将 `gateway/app/services/hot_follow_runtime_bridge.py` 明确收口为 compatibility-only bridge
- 为 bridge 导出补充显式 `compat_*` 命名，避免兼容 helper 继续看起来像正式 runtime owner
- 让 `gateway/app/routers/tasks.py` 改为显式消费 compatibility bridge 名称，而不是继续直接依赖模糊命名的 Hot Follow helper

本次收口说明：

- primary runtime / contract path 仍然是 `CompositionService`、status policy、line-aware gate binding 与正式 presenter/service 路径
- bridge 仍保留旧名称 alias，只为行为稳定，不作为新增业务逻辑入口
- `hot_follow_api.py` 中保留的 `_hf_*` / `_safe_*` helper 仍属于过渡残留，但已补充 compatibility 角色说明

本节点明确不做：

- 不实现 Skills MVP
- 不改 compose 主链语义
- 不改 gate binding 结构
- 不扩第二条产线

## Skills MVP Entry Review

日期：2026-03-19

本节点完成：

- 完成 Skills MVP entry review 文档冻结
- 将第一 Skills hook 定义为 Hot Follow workbench / operator guidance layer 中的 read-only advisory hook
- 冻结 advisory hook 的输入、输出、非目标与 merge gate

本次对齐结论：

- 未启动任何 Skills runtime implementation
- 第一 hook 只允许读取现有 `ready_gate`、`artifact_facts`、`current_attempt`、`operator_summary`、deliverable facts 等只读事实
- 第一 hook 只允许输出 non-blocking advisory，不得写状态、改真相、触发 compose / publish
- 后续任何 Skills implementation 仍必须受 business regression、verification baseline 与当前 execution rules 约束

本节点明确不做：

- 不改 runtime logic
- 不改 gate / compose / publish ownership
- 不启动第二条产线或 OpenClaw 相关工作

## PR-S0 Docs Freeze — State Schema + Skills Entry Contract

日期：2026-03-21

本节点完成：

- 将四层 state schema 正式提升为 contract 级输入模板
- 冻结 Skills MVP entry review 的最小边界
- 冻结 Skills MVP v0 advisory contract 的调用边界、输入、输出与失败回退行为

本次冻结结论：

- 四层 schema 的正式位置现在是 `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- Skills MVP v0 第一 hook 仍限制为 Hot Follow workbench / operator guidance layer 的 read-only advisory hook
- 当前仅冻结 schema 与 contract，不代表 Skills runtime implementation 已开始

本节点明确不做：

- 不启动 Skills runtime
- 不改 runtime logic
- 不改 tests
- 不扩第二条产线

## PR-S0 Cleanup — Clean Advisory Entry Surface

日期：2026-03-21

本节点完成：

- 将 Hot Follow workbench/operator-guidance 的 advisory-adjacent 只读聚合从 `hot_follow_api.py` 迁到窄职责 presenter
- 保持 `workbench_hub` 的 payload shape 与现有 truth-source ownership 不变
- 为后续 Skills MVP v0 advisory hook 预留更清晰的只读接入面

本次收口说明：

- router 继续保留 route ownership、request/response façade 与 payload 挂接
- `artifact_facts`、`current_attempt`、`operator_summary` 这组只读 presentation aggregates 不再直接由 router 定义
- 未引入 Skills logic、bundle loader、compose/publish/gate redesign

本节点明确不做：

- 不实现 Skills advisory
- 不改 product behavior
- 不改 compose / publish / ready gate 语义
- 不扩第二条产线或 OpenClaw 范围

## PR-S1 Skills MVP Skeleton

日期：2026-03-21

本节点完成：

- 为 Hot Follow 增加最小 Skills bundle metadata resolution path
- 增加 read-only advisory hook 的最小 skeleton interface
- 将 no-op-safe advisory call path 挂到 Hot Follow workbench / operator guidance surface

本次收口说明：

- 仅支持 Hot Follow advisory skeleton
- bundle resolution 仍为显式映射，不是 generalized plugin platform
- advisory 默认 no-op，不改变当前业务可见行为
- advisory 不拥有 repo write、deliverable write、compose/publish ownership 或 truth-source ownership

本节点明确不做：

- 不实现真实 advisory intelligence
- 不实现第二条产线 skills
- 不改 compose / publish / ready gate / status policy 主链
- 不做 OpenClaw 或平台化扩张

## PR-S2 Hot Follow Advisory Content v0

日期：2026-03-21

本节点完成：

- 为 Hot Follow advisory skeleton 增加最小可用的 advisory content v0
- 仅基于现有只读输入面生成建议，不改 truth-source ownership
- 保持 bundle 缺失、无 advisory 命中、或 advisory 计算失败时的 no-op-safe 行为

本次收口说明：

- advisory 仅覆盖小范围确定性 case：字幕检查、配音刷新、重新合成、成片可 QA、以及主字幕来源对齐提示
- advisory 输出仍为 small, structured, read-only block
- 未引入 generic rule engine、multi-line support 或 direct action execution

本节点明确不做：

- 不改 compose / publish / ready gate / status policy 逻辑
- 不写 repo state 或 deliverables
- 不扩第二条产线
- 不做 UI redesign 或 generalized skills runtime

## PR-S3 Advisory Rendering + Operator UX Integration

日期：2026-03-22

本节点完成：

- 在 Hot Follow workbench 中接入 advisory block 的只读展示
- advisory 仅作为 operator guidance 附加区块显示，不接管现有状态块
- advisory 缺失时页面安全降级，不影响既有工作流与页面结构

本次收口说明：

- 展示位置固定在 workbench 左侧指导区，与任务判断卡相邻，但语义保持次级
- 展示字段仅消费已冻结的 advisory contract：level、recommended_next_action、operator_hint、explanation、evidence
- 未增加新的 advisory 生成逻辑，也未把 advisory 升格为 gate 或 action controller

本节点明确不做：

- 不新增 advisory rules
- 不自动触发按钮或动作
- 不改 compose / publish / ready gate / status policy
- 不扩展到第二条产线或通用 UI framework

## PR-S4 Docs — Hot Follow Skills MVP v0 Closure Freeze

日期：2026-03-22

本节点完成：

- 冻结 `Hot Follow Skills MVP v0 Closure` 阶段文档
- 更新 product / architecture / execution baseline 与 `ENGINEERING_STATUS.md`
- 明确当前阶段已闭合、仍 partial、以及下一步建议

本次收口说明：

- Hot Follow 现为当前唯一完成 Skills MVP v0 closure 的业务样本
- baseline 口径已同步为 Hot Follow first、controlled continuation、no broad expansion
- 下一阶段尚未启动

本节点明确不做：

- 不改 runtime logic
- 不改 tests
- 不启动第二条产线
- 不启动 generalized platform / loader / Skills runtime 扩张

## Tasks Router Thinning — Hot Follow Continuation

日期：2026-03-22

本节点完成：

- 继续将任务列表整形、workbench 页面上下文组装、任务列表 summary 组装移出 `tasks.py`
- 将这些只读呈现职责收口到更明确的 presenter owner
- 追加 Avatar / baseline touchpoints 审计说明

本次收口说明：

- `tasks.py` 保留 router façade、request parsing、route ownership 与必要兼容入口
- Avatar / baseline 触点仅记录，不改变行为
- 未新增 router-to-router coupling，也未扩写成广义平台重构

本节点明确不做：

- 不改 Avatar behavior
- 不改 baseline / legacy flow behavior
- 不改 compose / gate / status 逻辑
- 不开启第二条产线或 OpenClaw 范围

## Tasks Router Thinning — Hot Follow Boundary-Safe Residue Cleanup

日期：2026-03-22

本节点完成：

- 将 `tasks.py` 中剩余的 Hot Follow compose compat wiring 收口到 `hot_follow_runtime_bridge.py`
- 将 dub 入口前的 subtitle-lane / route-state / no-dub 候选整形收口到同一兼容边界
- 为新 compat helper 增加回归测试，验证只是搬运边界而非改变业务判断

本次收口说明：

- `tasks.py` 继续保留 route ownership、request parsing、dispatch 与 response mapping
- Hot Follow compose / dub 的 line-specific compat residue 现在由更窄的 bridge owner 负责
- Avatar 与 baseline / legacy 触点未改行为；只维持既有 router 入口 ownership
- compose ownership、publish ownership、ready gate / status truth、Skills ownership 均未变化

本节点明确不做：

- 不改 Avatar behavior
- 不改 baseline / legacy flow behavior
- 不改 compose service business contract
- 不改 publish / ready gate / status / Skills ownership
- 不扩展到第二条产线、OpenClaw 或平台化抽象

## Hot Follow Cleanup Stage Freeze / Review

日期：2026-03-22

本节点完成：

- 冻结当前 Hot Follow cleanup stage review
- 明确本阶段已完成的 `tasks.py` thinning 与 compat residue narrowing
- 明确 Avatar / baseline 仍是 recorded-not-refactored
- 明确下一步仍需保持 controlled continuation

本次收口说明：

- Hot Follow sample 已明显更干净，但尚未 fully thinned
- `tasks.py` 仍偏大，compatibility residue 仍存在
- 当前建议仍是继续小范围、显式的 Hot Follow cleanup，而不是切换到新阶段扩张

本节点明确不做：

- 不改 runtime logic
- 不改 tests
- 不改 Avatar / baseline behavior
- 不开启第二条产线或 generalized platform work

## Hot Follow Boundary Cleanup 3

日期：2026-03-22

本节点完成：

- 将 Hot Follow workbench page context 的 compat hook 选择从 `tasks.py` 收口到 presenter owner
- 将 task detail/status payload 的 Hot Follow status-shape hook 选择从 `tasks.py` 收口到 presenter owner
- 为 presenter 默认 compat fallback 增加回归测试

本次收口说明：

- `tasks.py` 继续保留 route ownership、request parsing、dispatch 与 response mapping
- Hot Follow 的只读 shaping hook 进一步离开 router，owner 更接近 presenter / compatibility boundary
- Avatar 与 baseline 触点未改行为，只继续保留 audit 结论
- compose ownership、publish ownership、ready gate / status truth ownership、Skills ownership 均未变化

本节点明确不做：

- 不改 Avatar behavior
- 不改 baseline / legacy flow behavior
- 不改 compose / publish / ready gate / status / Skills ownership
- 不开启第二条产线、OpenClaw 或平台化扩张

## New Scenario Readiness Review

日期：2026-03-22

本节点完成：

- 完成 new-scenario discussion 前的 readiness review
- 明确当前 Hot Follow cleanup line 已接近 closure，但未 fully closed
- 明确 Avatar / baseline 不再作为 Hot Follow cleanup judgment 的内含项

本次收口说明：

- 当前判断为 `Conditionally Ready`
- 当前样本已足够作为新 scenario discussion 的参考起点
- 剩余 Hot Follow router-space residue 仍需保持为显式 carry-forward debt
- Avatar / baseline / platform work 需继续分开跟踪，避免混回当前判断

本节点明确不做：

- 不启动 new scenario implementation
- 不改 runtime logic
- 不改 tests
- 不把当前 readiness review 扩写成 broad platform strategy

## Hot Follow Localization Extension: Vietnamese Profile

日期：2026-03-27

本节点完成：

- 在现有 Hot Follow 单线内新增 Vietnamese (`vi`) 目标语言 profile，未创建第二条业务线
- 将 Hot Follow 的目标字幕文件名、目标配音文件名、允许 voice options、默认 voice mapping 收口到单一 profile truth source
- 复用既有 `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION`，未新增 Render secrets
- 维持 Myanmar (`my` / `mm`) 既有 workflow 与 deliverable 语义不变

本次收口说明：

- Hot Follow line 仍然 singular；只是新增第二个 supported target-language instance
- Myanmar 继续使用 `mm.srt` / `audio_mm.mp3`
- Vietnamese 新增 `vi.srt` / `audio_vi.mp3`
- compose / deliverable semantics / workbench ownership / ready gate ownership 均未改边界

本节点明确不做：

- 不新建 Vietnamese-specific line 或 workbench
- 不做 menu-wide i18n 扩张
- 不重构 unrelated scenarios
- 不改 Hot Follow 之外的 ownership truth source
