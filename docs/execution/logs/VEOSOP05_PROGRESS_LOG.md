# VeoSop05 启动进度文档

## PR-Status Truth Binding Audit / Fix

日期：2026-04-17

本节点完成：

- 收紧 Hot Follow ready gate 的 voiceover/audio extraction：raw `mm_audio_key` / `mm_audio_path` 不再能满足 `voiceover_exists` 或 fallback `audio_ready`
- Hot Follow task board / summary status 不再用 `final_video_key`、`publish_key`、`compose_status=done` 直接投影 ready
- 保持真正的 ready 投影来自 computed `ready_gate.compose_ready` / `ready_gate.publish_ready`
- 补充回归，覆盖 legacy audio key 不能让 ready gate 误判 audio ready，以及 board/summary 不再被 final/publish artifact 单独置 ready

本次收口说明：

- 只做 PR-4 status truth binding audit/fix
- 不改 compose input binding、不改 source-audio policy persistence、不改 preview/player binding
- 不做 UI redesign、不做 `mm_*` / `/audio_mm` / `audio_url` 命名清理，不重写 publish ownership

本节点验证：

- Interpreter: `Python 3.11.15` via `python3.11`
- `python3.11 -m py_compile gateway/app/services/ready_gate/hot_follow_rules.py gateway/app/services/task_semantics.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_task_router_presenters.py`
- `python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py gateway/app/services/tests/test_hf_compose_freshness.py -q` -> 63 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 41 passed
- `python3.11 -m pytest gateway/app/services/ready_gate/tests/test_line_binding.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 6 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/tests/test_source_audio_policy_persistence.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_subtitle_template_semantics.py -q` -> 6 passed

剩余风险：

- compatibility naming cleanup 仍后置，尤其是 `mm_audio_key`、`/audio_mm`、`audio_url` 等历史命名
- 真实素材仍需按 Hot Follow business regression 抽样确认 final/source playback 与 operator-facing 状态一致
- `tasks.py`、`compose_service.py` 等结构性 thinning 仍应作为独立工程治理 PR

## PR-Preview Player Binding Audit / Fix

日期：2026-04-17

本节点完成：

- 将 Hot Follow workbench 的 TTS 预览 / voiceover audio / compose gate 统一收敛到 `dub_preview_url` / `tts_voiceover_url`
- 移除播放器侧对 `media.voiceover_url`、`audio.voiceover_url` 兼容别名的 fallback，避免 preserved source audio / BGM 被误当成 dubbing preview
- 补充静态回归，要求 workbench preview player 只使用显式 TTS preview truth
- 保持 source video、final video、compose ownership、status projection 不变

本次收口说明：

- 只做 PR-3 preview/player binding audit/fix
- 不做 PR-4 status truth projection、不改 ready gate、不改 publish/task board status
- 不做 UI redesign、不做 `mm_*` / `/audio_mm` / `audio_url` 命名清理

本节点验证：

- Interpreter: `Python 3.11.15` via `python3.11`
- `node --check gateway/app/static/js/hot_follow_workbench.js`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_subtitle_template_semantics.py -q` -> 3 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q` -> 28 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py -q` -> 59 passed
- `python3.11 -m pytest gateway/app/services/tests/test_source_audio_policy_persistence.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 3 passed

剩余风险：

- PR-4 status truth binding audit/fix 仍需独立确认 task board、workbench、publish hub 不绕过 voice state / ready gate
- compatibility naming cleanup 继续后置；本 PR 不移除兼容 payload 字段或路由
- 真实素材的试听观感仍需按 Hot Follow business regression 抽样确认

## PR-Source Audio Policy Persistence Audit / Fix

日期：2026-04-17

本节点完成：

- 修正 `pipeline_config_to_storage()` 的 allowlist，使 `source_audio_policy`、`bgm_strategy`、`audio_strategy` 不再在落库时丢失
- 将 Hot Follow create path 的 `source_audio_policy` 同步写入 `config.source_audio_policy`，避免只依赖 pipeline config 或 BGM strategy 推断
- 修正 workbench BGM 上传：请求会携带当前 `source_audio_policy` 对应的 `strategy`
- 修正 BGM 上传后端缺省策略：未显式传 `strategy` 时继承任务当前 source-audio policy，而不是默认 `replace`
- 补充策略持久化回归，覆盖 preserve 任务上传 BGM 不被覆盖，以及显式 replace 可切回 mute

本次收口说明：

- 只做 PR-2 source-audio policy persistence audit/fix
- 不做 compose input binding 新改动、不做 preview/player binding、不改 status truth projection
- 不做 UI 语义重排、不清理 `mm_*` / `/audio_mm` / `audio_url` 兼容命名

本节点验证：

- Interpreter: `Python 3.11.15` via `python3.11`
- `python3.11 -m py_compile gateway/app/utils/pipeline_config.py gateway/app/services/source_audio_policy.py gateway/app/services/media_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_source_audio_policy_persistence.py`
- `node --check gateway/app/static/js/hot_follow_workbench.js`
- `python3.11 -m pytest gateway/app/services/tests/test_source_audio_policy_persistence.py -q` -> 2 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_new_page_routes.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py -q` -> 77 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 14 passed

剩余风险：

- PR-3 preview/player binding audit/fix 仍需独立确认所有播放器只按冻结资产语义取源
- PR-4 status truth binding audit/fix 仍需独立确认 task board、workbench、publish hub 不绕过 voice state / ready gate
- compatibility naming cleanup 继续后置，不能与线路修复混在一起

## PR-Compose Input Binding Audit / Source-Audio Preserve Fix

日期：2026-04-17

本节点完成：

- 修正 Hot Follow compose video input selection，使 `preserve original BGM/source audio` 优先使用 `raw_path` 作为 compose carrier
- 保持 `mute original audio` 继续优先使用 `mute_video_key / mute_video_path`
- 当 probe 明确 `has_audio=false` 时，即使策略为 preserve，也关闭 source-audio lane，避免把静音 carrier 当作 source-audio bed
- 补充 compose input binding 回归，覆盖 preserve/raw、mute/mute-video、preserve/no-source-audio 三条路径

本次收口说明：

- 只做 PR-1 compose input binding audit/fix
- 不做 UI 语义调整、不做 preview/player binding、不改状态投影、不做 source-audio policy persistence 审计
- 不做 `mm_*` / `/audio_mm` / `audio_url` 命名清理，不新增外部 API，不重写 compose ownership

本节点验证：

- Interpreter: `Python 3.11.15` via `python3.11`
- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/tests/test_compose_video_master_duration.py`
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py -q` -> 8 passed
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q` -> 67 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 41 passed
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 114 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 1 passed

剩余风险：

- `compose_service.py` 仍超过 service oversized threshold；本 PR 只做 policy-aware input binding，后续仍需要专门 thinning PR
- PR-2 source-audio policy persistence、PR-3 preview/player binding、PR-4 status truth binding 继续独立执行
- 真实素材仍需按 Hot Follow business regression 抽样确认 source-audio preserve 最终混音观感

## PR-Source Audio Semantics Alignment / Operator Flow

日期：2026-04-16

本节点完成：

- 将 Hot Follow audio payload 显式区分 `source_audio_policy`、preserved source audio、current TTS voiceover、dub preview URL
- preserved source audio / BGM 只显示为 source-audio bed，不再作为 TTS preview 或 dubbing completed 语义展示
- 工作台音频诊断与路由诊断增加当前 source-audio policy 与 audio flow 语义
- 标准配音预览与 compose 前端判断改为优先使用 true TTS voiceover / dub preview URL
- 保持 mute path、标准 subtitle -> TTS dub -> compose happy path 与 compose source-audio policy 不变

本次收口说明：

- 只做 Hot Follow source-audio operator-facing semantics、diagnostics 与 preview binding 对齐
- 不改 subtitle truth chain、不重写 compose / publish ownership、不新增 scenario 或 task kind
- 不做 translation bridge、不清理 `mm_*` 兼容命名、不做 UI redesign

本节点验证：

- `python3.11 --version` -> Python 3.11.15
- `python3.11 -m py_compile gateway/app/services/voice_service.py gateway/app/routers/hot_follow_api.py gateway/app/services/task_view.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py`
- `node --check gateway/app/static/js/hot_follow_workbench.js`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q` -> 28 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 13 passed
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py -q` -> 43 passed

剩余风险：

- source-audio preserve 的真实混音观感仍需按 Hot Follow business regression 用真实素材抽样确认
- `compose_service.py`、`hot_follow_api.py`、`tasks.py` 仍超过结构阈值；本 PR 不处理 thinning
- `audio_mm` / `mm_*` 兼容命名仍可能造成表层理解成本，命名清理继续保持独立后续 PR

## PR-Source Audio Policy Binding / Dub Truth Correction

日期：2026-04-16

本节点完成：

- 将 Hot Follow 新建页的 `replace / keep / mute` source-audio 选择写入任务配置
- 将 `keep original` 绑定到 compose audio policy，最终合成可使用原视频音轨作为 source-audio bed
- 保持 `replace / mute` 不携带原视频音轨的既有静音/替换语义
- preserved source audio / uploaded BGM 不再能冒充当前 TTS voiceover，也不会让 `dub_current=true`
- 将 source-audio policy 写入 final freshness snapshot，policy 改变会触发重新 compose

本次收口说明：

- 只修复 Hot Follow source-audio policy binding、compose audio input selection、dub truth-source gating
- 不改 subtitle truth chain、不重写 compose ownership、不改 publish ownership
- 不做 UI redesign、不新增外部 API、不混入 translation bridge / cleanup / `mm_*` 命名清理

本节点验证：

- `python3.11 --version` -> Python 3.11.15
- `python3.11 -m py_compile gateway/app/services/source_audio_policy.py gateway/app/services/compose_service.py gateway/app/services/voice_state.py gateway/app/services/voice_service.py gateway/app/services/media_helpers.py gateway/app/routers/hot_follow_api.py gateway/app/services/task_view_helpers.py gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py`
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py -q` -> 5 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q` -> 25 passed
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q` -> 38 passed
- `python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 40 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_new_page_routes.py gateway/app/services/tests/test_tasks_subtitle_upload_paths.py -q` -> 7 passed
- `python3.11 -m pytest gateway/app/services/tests/test_compose_video_master_duration.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 108 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 1 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q` -> 14 passed

剩余风险：

- `compose_service.py`、`hot_follow_api.py`、`tasks.py` 仍超过结构阈值；本 PR 只做窄 truth-source 修复，后续需要专门 thinning PR
- source-audio preserve 依赖源视频实际存在音轨；若上游 probe 明确 `has_audio=false`，compose 会回落为无 source-audio bed
- 真实素材仍需按 Hot Follow business regression 抽样确认原声 bed 与 TTS 混音观感
- 曾尝试运行 `test_hot_follow_provider_mismatch_gate.py`，失败点是该测试的 AST-only loader 保留了过期 helper 名称，不能代表本 PR 的 runtime regression

## PR-Myanmar Target Subtitle Currentness Alignment

日期：2026-04-16

本节点完成：

- 将 Myanmar Hot Follow target subtitle currentness 对齐到 Vietnamese 已有的严格规则
- Myanmar target subtitle 不再因为 artifact 存在或内容非空就被视为 current
- source-copy 与 translation-incomplete 的 Myanmar target subtitle 会阻断 `subtitle_ready`、`dub_current`、`compose_ready`、`publish_ready`
- 保留 Vietnamese target subtitle currentness 行为，并补充 Myanmar false-ready 回归覆盖

本次收口说明：

- 仅修正 Hot Follow target subtitle truth-source 与直接下游 gating
- 不新增 localization_line，不做 translation bridge/tooling，不重命名 `mm_*` 兼容字段
- 不改 UI 设计、不重写 compose ownership、不扩成宽状态/runtime 重构

本节点验证：

- `python3.11 --version` -> Python 3.11.15
- `python3.11 -m py_compile gateway/app/services/hot_follow_subtitle_currentness.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/task_view.py gateway/app/services/task_semantics.py gateway/app/services/steps_v1.py gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_task_router_presenters.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_currentness.py -q` -> 4 passed
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py -q` -> 4 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q` -> 24 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 13 passed
- `python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py -q` -> 24 passed
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py -q` -> 13 passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/tests/test_hf_compose_freshness.py gateway/app/services/status_policy/tests/test_app_import_smoke.py -q` -> 58 passed
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_currentness.py gateway/app/services/tests/test_steps_v1_subtitles_step.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q` -> 21 passed

剩余风险：

- 本次不清理历史 `mm_*` 命名与兼容字段，后续不得把命名清理混入 currentness 修复
- Direct dub 仍依赖已计算出的 target subtitle currentness fact；缺失 fact 的强制重跑路径保持原有行为以保护 happy path
- 真实素材仍需按 Hot Follow business regression 抽样验证 target subtitle 内容质量

## PR-Subtitle Font Micro-Tuning After Cleanup v1

日期：2026-04-04

本节点完成：

- 将 Hot Follow target subtitle 的最终烧录字号再收一档，降低底部字幕块的视觉重量
- 将字幕在底部 safe-zone 内再下压一小步，并同步收紧两行宽度阈值
- 将 `bottom_mask / safe_band` 的 core band 高度与羽化层一并收紧，使 cleanup 区域更贴近实际字幕块高度

本次收口说明：

- 仅做字幕字体、底边距、两行阈值与 cleanup band 高度的微调
- 不改 cleanup 逻辑家族、不改 compose ownership、不改状态链或发布语义
- 不引入 OCR / CV / vision API，不扩成通用 subtitle removal

本节点验证：

- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 本次是视觉参数微调，不是自动视觉评估；最终观感仍建议结合真实 beauty/tutorial 素材抽样复核
- 当前字体资源仍未扩展，本次只微调已有布局/cleanup 参数

## PR-Render Binding Fix: Cleanup / Layout Snapshot Wiring

日期：2026-04-04

本节点完成：

- 将 Hot Follow `cleanup_mode` 与 subtitle layout render policy 绑定进 compose freshness snapshot
- 当 cleanup/layout render signature 变化时，旧 final 不再被误判为 fresh
- 让 compose plan、最终 render 行为与成片结果重新一致，而不是继续复用旧 final

本次收口说明：

- 这是 render binding 修复，不新增 cleanup feature family，不改 source/target subtitle truth、dub/compose/publish ownership
- 不引入 OCR / CV / vision API
- 不扩成通用 subtitle removal 或广义 video cleanup 平台

本节点验证：

- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/routers/hot_follow_api.py gateway/app/services/tests/test_hf_compose_freshness.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 当前修复保证 render plan 变化会触发新 compose；它不替代真实视频视觉对比工具
- cleanup/layout 仍是 rule-based v1 行为，不应描述成 universal subtitle removal

## PR-3 Hot Follow Original Subtitle Cleanup / Mask Overlay v1

日期：2026-04-04

本节点完成：

- 将 Hot Follow 现有 `bottom_mask / safe_band` 收口为底部字幕带的分层柔化遮罩，而不是单块重黑遮挡
- 保持 target subtitle 继续在底部 safe-zone 烧录，并让 cleanup band 与现有 target subtitle overlay 路径兼容
- 让越南语路径也能复用同一套柔和底部 cleanup，而不是继续完全跳过底部遮罩

本次收口说明：

- 仅改最终合成的视觉 cleanup 路径，不改 source/target subtitle truth、dub/compose/publish ownership 或状态链
- 这是 rule-based/template-style 的 v1 底部字幕带 cleanup，不是通用 AI subtitle removal
- 未引入 OCR / CV / vision API，也未扩成手动清理编辑器

本节点验证：

- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 当前 v1 只针对常见底部 hard-subtitle band；不覆盖任意位置、彩色描边、复杂背景或动态字幕
- 柔化遮罩改善的是常见场景的视觉观感，不应被描述成 universal subtitle removal

## PR-2 Hot Follow Subtitle Layout Safe-Zone Optimization

日期：2026-04-04

本节点完成：

- 将 Hot Follow 最终烧录字幕收口到更稳定的底部 safe-zone 样式，显式固定 `Alignment=2`
- 将常见字幕烧录路径压回两行默认展示，避免长字幕在成片中占据过高垂直空间
- 在 compose 临时工作目录内对烧录用 SRT 做窄范围 layout 重排，改进中英缅越长句断行可读性

本次收口说明：

- 只改最终烧录展示，不改 source/target subtitle truth、dub freshness、compose ownership 或 publish/workbench 状态链
- 不引入新字体依赖或外部 layout 服务
- 不扩成字幕清洗、翻译质量或 bridge 方案改造

本节点验证：

- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 当前仓库只内置 Myanmar 字体资源；本 PR 仅优化 safe-zone / wrap，不额外引入 CJK / Latin 字体资产
- 两行策略是 common-path 优化，不是完整排版引擎；极端超长字幕仍可能需要上游字幕编辑配合

## Hot Follow Local Upload Parse Binding Fix

日期：2026-04-02

本节点完成：

- 修复 Hot Follow local-upload 任务在 `/run` 后仍落入 link-based parse 校验的问题
- local ingest 任务若 `raw.mp4 / raw_path` 已就绪，则后台 pipeline 直接将 parse 视为 source-ready，不再构造 `ParseRequest.link`
- 同步 parse route 对 local ingest 的状态回写与后台 pipeline 保持一致
- 补齐后台 pipeline 中 `Workspace(task_id, target_lang=...)` 的显式绑定，避免 local-upload 继续向下游时踩未定义变量

本次收口说明：

- 仅修 Hot Follow 既有 local-upload entry 到 parse/subtitles 的绑定缺口
- 未新增 scenario / task kind / workbench path
- 未改 translation、subtitle quality、compose 主链策略

本节点明确不做：

- 不改新建页交互
- 不做字幕/翻译功能扩张
- 不做广义 runtime 重构

## Hot Follow Local Video Entry Narrow Enhancement

日期：2026-04-01

本节点完成：

- 在既有 Hot Follow 新建页增加 `link / local video` 两种 source mode
- local video 模式支持上传本地视频并创建正常 Hot Follow 任务，不新增 task kind / scenario / production line
- 上传后任务按既有 Hot Follow truth shape 写入 `raw.mp4` / `raw_path`，继续进入既有 workbench / subtitles / dub / compose 流
- 初版仅显式支持源视频语言 `zh / en` 作为入口提示与 pipeline config hint

本次收口说明：

- 仍保持 Hot Follow 为单线；只是新增 baseline-style local import entry
- link-based create flow 未改行为；仍沿用 probe -> create -> optional BGM -> run
- local-upload path 只做入口归一化，不扩成媒体库、批量上传或新场景

本节点明确不做：

- 不改全局菜单 / 导航
- 不改翻译质量、字幕清洗或 compose 主链策略
- 不新增 image/multi-asset upload

## Vietnamese Hot Follow Runtime Validation: Chain Confirmed Green

日期：2026-03-27

本节点确认：

- Hot Follow 仍为单一产线，当前目标语言实例为 Myanmar / Vietnamese 两条 profile
- Vietnamese 已完成链路验证：
  - 新建任务页可正常选择越南语
  - male / female voice 选项均可用
  - parse 正常进入后续链路
  - 目标语言字幕可生成、可再编辑
  - dub 可继续使用当前越南语目标字幕完成配音
  - compose 可完成最终合成
- 当前状态应视为 Vietnamese Hot Follow runtime chain 已打通，而不是继续处于 closure gap 阶段

本节点验证命令：

- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_new_page_routes.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_steps_v1_subtitles_step.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_dub_voice_and_text_guard.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

本节点边界说明：

- 未新增文件，仅更新现有进度记录
- 未扩展为新 scenario / 新工作台 / 新产线
- 未混入新的越南语功能开发，仅记录已验证通过的运行状态

## PR-Localization Closure Pack v2: Vietnamese Subtitle Currentness + Gate Alignment

日期：2026-03-27

本节点完成：

- 将越南语目标字幕 currentness 明确收口为可验证事实，而不是继续按 artifact existence 近似判定
- 让 `vi.srt` 只有在成为真实当前越南语目标字幕后才被视为 ready / authoritative burn source
- 让配音、合成、board/list/workbench 状态共同服从同一份越南语目标字幕 currentness 事实，避免 false done

本次边界说明：

- Hot Follow 仍保持单一产线
- 未引入新 scenario / 新工作台 / 新 compose path
- 未扩大为平台级 gate/status 重写

## PR-Localization Closure Pack: Vietnamese Profile + Compose Burn Source + Board Status

日期：2026-03-27

本节点完成：

- 将 Hot Follow 越南语 profile 显式收口到现有语言 profile source，补齐正确展示名与 female/male voice 选项
- 修复越南语目标字幕 artifact / compose burn source 对齐，确保 `vi.srt` 为真实目标烧录来源，而不是静默回退到 Myanmar 默认
- 修复 Hot Follow board/list 状态投影，优先由 final / compose / ready_gate 等事实字段推导 completed，而不是在原始状态缺失时落回 `unknown`

本次边界说明：

- Hot Follow 仍保持单一产线
- 未引入新的 scenario / workbench / compose path
- 未扩大为菜单级 i18n 或平台级状态治理改造

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

## Hot Follow Vietnamese Route Narrow Fix Pack

日期：2026-03-27

本节点完成：

- 修正 Hot Follow 新建页声线标签判断，恢复女声 / 男声正确显示
- 收紧 Hot Follow 目标语言 SRT truth chain，目标字幕主编辑区不再回退显示来源中文
- 越南语 workbench 配音前增加目标字幕当前性校验，要求先翻译并保存 `vi.srt`
- 越南语 compose 关闭底部黑色遮罩框，保留目标字幕烧录本身

本次收口说明：

- 仍在既有 Hot Follow 单线内完成
- 未新增新场景、第二条产线或平台级 i18n 抽象
- root fix 落在 subtitle truth / compose filter / page option rendering 三个直接链路

本节点明确不做：

- 不改越南语之外的 provider 配置边界
- 不做 broad compose redesign
- 不重写 workbench 架构

## Hot Follow Subtitle Step Error Classification Fix

日期：2026-03-27

本节点完成：

- 修复 subtitles step 收尾阶段错误引用未定义局部变量，避免解析完成后被误打成 step error
- 接通 `translation_incomplete` 在 pipeline config / workbench / ready 判定中的真实传递
- 调整目标字幕 currentness 诊断优先级：翻译未完成优先于空目标字幕占位
- workbench / pipeline 摘要现在可区分 `no_subtitles`、`translation_incomplete` 与真实异常

本次收口说明：

- 这次修复的是 Hot Follow 既有字幕链路的错误分类与状态回写，不是新功能
- 目标是让“无法解析 / 无字幕 / 翻译未完成”在现有单线里被事实化区分

本节点明确不做：

- 不改 Gemini / Whisper provider 本身
- 不扩成新的字幕架构

## Hot Follow Target Subtitle Upload Path Fix

日期：2026-03-27

本节点完成：

- 修复自动 subtitles job / auto pipeline 在目标字幕落库时遗漏 `target_lang` 的问题
- 修复越南语任务仍按默认 `mm.srt` / `mm.txt` 回写，导致真实 `vi.srt` / `vi.txt` 丢失的问题
- 追加缅甸语 / 越南语两条目标字幕上传路径回归测试

本次收口说明：

- 本次修复聚焦 Hot Follow 现有字幕上传链，不改 dub / compose 已稳定路径
- 根因是目标语言 profile 没有贯穿到旧的字幕收尾上传 helper

本节点明确不做：

- 不重构 tasks router 其他旧 helper
- 不扩到非 Hot Follow 线路

## Hot Follow Standard Dub Freshness Alignment

日期：2026-04-04

本节点完成：

- 将 Hot Follow 标准配音链继续作为默认主路径，未引入新的 provider 或第二条 truth-source
- 成功配音时回写“当前目标字幕快照”，让配音 currentness 与当前 authoritative target subtitle 绑定
- 字幕编辑后若 target subtitle 已变化，旧 dub 不再视为 current，compose readiness 与 workbench audio step 会同步降级
- workbench/operator summary 明确给出“需重新配音”提示，而不是把 stale dub 继续当成可合成状态

本次收口说明：

- 本次只修既有 subtitle/dub/compose currentness 链，不改 compose/publish ownership
- 目标是消除旧 dub freshness drift，而不是扩展翻译桥接或改 UI 架构

本节点明确不做：

- 不新增外部 TTS provider
- 不新建状态层或新 helper 文件
- 不改 Hot Follow 以外的业务线路

验证结果：

- `python3.11 -m py_compile gateway/app/services/voice_state.py gateway/app/routers/tasks.py gateway/app/routers/hot_follow_api.py gateway/app/services/hot_follow_workbench_presenter.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 旧任务在首次重新标准配音前，可能还缺少 `dub_source_*` 快照字段；该类任务会在重新配音一次后进入新的 freshness 基线

## Hot Follow Dub Speed Binding + Freshness Invalidation

日期：2026-04-04

本节点完成：

- 修复 `audio_fit_max_speed` 未被 `pipeline_config` 规范化保留，导致 workbench/hub 一直回退显示默认 `1.25`
- 让 workbench hub / `audio_config` 返回当前 authoritative dub speed，避免 UI slider 与 API 返回值分裂
- 将 dub speed 纳入当前 dub freshness：当前 speed 与 dub 生成时 snapshot 不一致时，旧 dub 不再视为 current
- speed 变更时若旧任务还没有 speed snapshot，会回填当前旧 speed 作为 dub 基线，从而在下一次 speed 改动后立即失效旧 dub
- 成功 re-dub 时持久化 `dub_source_audio_fit_max_speed`，让新 speed 成为 authoritative dub config 的一部分

本次收口说明：

- 本次只修 Hot Follow 既有 dub speed request/persistence/currentness 链
- 不改 compose/publish ownership，不新增 provider，不改翻译桥接

本节点明确不做：

- 不新增外部 TTS provider
- 不重写 workbench UI 架构
- 不扩展到 Hot Follow 以外线路

验证结果：

- `python3.11 -m py_compile gateway/app/services/voice_state.py gateway/app/routers/tasks.py gateway/app/routers/hot_follow_api.py gateway/app/utils/pipeline_config.py gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q gateway/app/services/tests/test_hf_compose_freshness.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- 极早期旧任务若没有 audio speed snapshot，首次 speed 调整会依赖本次补上的旧 speed 回填来进入新的 freshness 基线；再完成一次标准配音后即可稳定落到新模型

## PR-0 Hot Follow Contracts / ADR / SOP Freeze

日期：2026-04-06

本节点完成：

- 冻结 Hot Follow 人类可读 line contract：明确 line id、input/deliverable/SOP/skills/worker/asset sink/status/ready gate 引用
- 冻结 Hot Follow ready gate YAML 草案，明确 compose/publish ready、artifact/step/currentness 条件与 operator confirmation hook
- 冻结 Worker Gateway contract，明确 request/response shape、internal/external/hybrid 模式与禁止直接写 truth 的边界
- 冻结 Status Ownership Matrix，明确谁写 truth、谁算 derived、谁只做 display projection
- 新增 `tasks.py` 拆解 ADR，明确按职责拆，不按文件大小拆
- 新增 Hot Follow SOP runbook，并更新 docs 索引把 Jellyfish importability review 纳入参考阅读链

本次收口说明：

- 本次只做 docs-first / rules-first 冻结，为后续 `tasks.py` P0 拆解和 line-contract-driven runtime 提供边界
- 本次不改业务代码、不改 URL、不改 UI、不扩第二条产线

本节点明确不做：

- 不在本次 PR 建 Skills Runtime
- 不在本次 PR 建 Worker Gateway 实现
- 不在本次 PR 改 compose/publish ownership
- 不在本次 PR 引入新的 business feature

验证结果：

- 新增/更新文档已覆盖：
  - `docs/contracts/hot_follow_line_contract.md`
  - `docs/contracts/hot_follow_ready_gate.yaml`
  - `docs/contracts/worker_gateway_contract.md`
  - `docs/contracts/status_ownership_matrix.md`
  - `docs/adr/ADR-task-router-decomposition.md`
  - `docs/runbooks/hot_follow_sop.md`
  - `docs/README.md`
- 文档内容已与以下现有 runtime/baseline/review 对齐：
  - `docs/architecture/line_contracts/hot_follow_line.yaml`
  - `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`
  - `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
  - `gateway/app/services/ready_gate/hot_follow_rules.py`
  - `docs/reviews/review_jellyfish_importability_for_factory.md`

剩余风险：

- 这些 contracts/ADR 先是 docs-first 冻结，运行时主链仍需后续 PR 把 `tasks.py` / `hot_follow_api.py` / ready gate binding 真正对齐到合同消费
- `status` 与 `ready_gate` 的历史兼容字段仍可能在旧逻辑里并存，代码拆解时必须按本矩阵继续收口

## PR-2 Compose Service Extraction Boundary

日期：2026-04-06

本节点完成：

- 将 Hot Follow compose 的 repo/status 写路径从 `compose_service.py` 中移出，改为由 `tasks.py` / `hot_follow_api.py` 外层 orchestration shell 负责
- 保留 `compose_service.py` 作为执行边界：负责 compose plan 规范化、输入校验、workspace 准备、FFmpeg 调用、输出校验、上传验证与结构化 compose result 返回
- 引入 `ComposePlan` / `ComposeResult`，使 compose execution 输出不再只是匿名 dict
- 保留并强化 FFmpeg timeout 保护：所有 subprocess/ffmpeg 路径继续统一走 `_run_ffmpeg(...)`
- 保持临时目录生命周期在 `TemporaryDirectory()` / finally-managed flow 内，不把 temp/intermediate 文件生命周期泄漏到 router
- 保持 `_hf_compose_final_video()` 仅为向后兼容的薄包装器，不再承载 execution body

本次收口说明：

- 本次只做 compose execution ownership boundary 收口
- 不做 line contract runtime binding
- 不做 declarative ready gate evaluator
- 不改 URL / route shape / UI / compose 输出语义

本节点明确不做：

- 不实现 Worker Gateway
- 不实现 Skills Runtime loader
- 不改 publish ownership
- 不改 ready gate 主判断逻辑

验证结果：

- `python3.11 -m py_compile gateway/app/services/compose_service.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/tests/test_hot_follow_subtitle_binding.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/tests/test_compose_service_contract.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hot_follow_subtitle_binding.py -q`
- `python3.11 -m pytest gateway/app/services/tests/test_hf_compose_freshness.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q gateway/app/services/tests/test_compose_video_master_duration.py -q`

剩余风险：

- `tasks.py` 与 `hot_follow_api.py` 仍各自保留一层 compose orchestration shell；后续若做 PR-3/PR-4，应在不回退 status ownership 的前提下继续收口到更稳定的 controller/runtime boundary
- line contract 与 ready gate 目前仍未成为 compose controller 的 runtime 主输入，这部分留给后续 PR

## PR-3 Hot Follow Contract Binding

日期：2026-04-06

本节点完成：

- 为 `ProductionLine` 补齐 PR-0 冻结的合同字段：input/deliverable/worker/asset sink/confirmation policy
- 新增 `gateway/app/services/line_binding_service.py`，把 `LineRegistry.for_kind(...)` 收口为统一 runtime binding 入口
- 将 Hot Follow publish/workbench hub 和 compose 成功响应接入 line binding 元数据，使 runtime 真实消费 line contract，而不是只保留仪式性声明
- 对齐 runtime-critical SOP 引用：`gateway/app/lines/hot_follow.py` 与 `docs/architecture/line_contracts/hot_follow_line.yaml` 现均指向 `docs/runbooks/hot_follow_sop.md`

本次收口说明：

- 本次只做 line contract metadata binding
- 不做 declarative ready gate evaluator
- 不做 worker gateway 实现
- 不做 skills runtime loader
- 不改变 status truth / deliverable truth 的写入边界

本节点明确不做：

- 不在本次 PR 把 ready gate 变成 YAML evaluator
- 不在本次 PR 让 line metadata 直接驱动 status 写回
- 不在本次 PR 改 URL / route / UI

验证结果：

- `python3.11 -m py_compile gateway/app/lines/base.py gateway/app/lines/hot_follow.py gateway/app/services/line_binding_service.py gateway/app/services/task_view.py gateway/app/services/hot_follow_skills_advisory.py gateway/app/routers/hot_follow_api.py gateway/app/routers/tasks.py gateway/app/services/tests/test_line_binding_service.py gateway/app/services/tests/test_compose_service_contract.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py`
- `python3.11 -m pytest gateway/app/services/tests/test_line_binding_service.py -q gateway/app/services/tests/test_compose_service_contract.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/status_policy/tests/test_line_runtime_binding.py -q gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py -q gateway/app/services/tests/test_hot_follow_skills_advisory.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- line contract 目前已进入 runtime metadata 主链，但 ready gate 仍使用现有 Python 规则镜像，尚未读取 docs YAML
- worker profile / skills bundle / confirmation policy 目前是 live metadata / hook refs，还不是可执行 loader
- `tasks.py` orchestration 仍未完成最终 contract-driven layering，这部分留给 PR-4

## PR-4 Declarative Ready Gate For Hot Follow

日期：2026-04-06

本节点完成：

- 将 Hot Follow ready gate spec 的 runtime source 切到 `docs/contracts/hot_follow_ready_gate.yaml`
- 为 YAML 增加 machine-readable `runtime_rules`，覆盖 signal / override / gate / blocking rule
- 在 `gateway/app/services/ready_gate/hot_follow_rules.py` 中保留 signal/reason extractor 库，但由 YAML 规则动态构建 `HOT_FOLLOW_GATE_SPEC`
- 将 `gateway/app/lines/hot_follow.py` 与 `docs/architecture/line_contracts/hot_follow_line.yaml` 的 `ready_gate_ref` 对齐到 YAML
- 保持 `compute_hot_follow_state()` 只消费 evaluator 结果，不新增任何 truth 写回

本次收口说明：

- 本次只做 declarative ready gate evaluator/source 收口
- 不做 worker gateway
- 不做 skills runtime loader
- 不做 broader status-system rewrite
- workbench/publish 继续经由 `compute_hot_follow_state()` 消费 ready gate 输出

本节点明确不做：

- 不在本次 PR 引入多产线通用 profile 平台
- 不在本次 PR 让 evaluator 直接写 repo/status truth
- 不在本次 PR 改 route / UI / publish write path

验证结果：

- `python3.11 -m py_compile gateway/app/lines/hot_follow.py gateway/app/services/ready_gate/hot_follow_rules.py gateway/app/services/ready_gate/registry.py gateway/app/services/status_policy/hot_follow_state.py gateway/app/services/ready_gate/tests/test_line_binding.py gateway/app/services/status_policy/tests/test_line_runtime_binding.py gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py gateway/app/services/tests/test_line_binding_service.py`
- `python3.11 -m pytest gateway/app/services/ready_gate/tests/test_line_binding.py -q gateway/app/services/status_policy/tests/test_line_runtime_binding.py -q gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py -q`
- `python3.11 -m pytest gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py -q gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py -q gateway/app/services/tests/test_line_binding_service.py -q gateway/app/services/status_policy/tests/test_app_import_smoke.py -q`

剩余风险：

- YAML 目前只驱动 Hot Follow 一条线，signal extractor 库仍是 Python 映射，不是完全通用 DSL
- optional artifact / richer operator confirmation hooks 仍未扩展为通用 evaluator input model
- worker gateway / skills runtime / broader line-driven orchestration 继续留给下一阶段
