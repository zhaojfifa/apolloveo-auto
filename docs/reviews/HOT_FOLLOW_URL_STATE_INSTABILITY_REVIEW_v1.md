# Hot Follow URL State Instability Review v1

## 1. 证据摘要

本次 review 只针对 Hot Follow 当前不稳定形态做合同驱动确认，不实施修复，不吸收 donor code，不改 runtime 行为。

主证据任务：`68b60f8ac45e`。

观察到的矛盾是同一任务先后出现两种不兼容形态：

- Shape A：`subtitles.status=failed`、`subtitle_ready=false`、`target_subtitle_current=false`、`target_subtitle_authoritative_source=false`、`audio_ready=false`、`selected_compose_route=no_tts_compose_route`，但 `edited_text` / `srt_text` 已经含有有效越南语目标字幕。
- Shape B：后续收敛为 `subtitles.status=done`、`subtitle_ready=true`、`target_subtitle_current=true`、`target_subtitle_authoritative_source=true`、`audio_ready=true`、`selected_compose_route=tts_replace_route`、`compose.status=done`、`final.exists=true`、`publish_ready=true`，但 `subtitles.error` 仍残留“权威目标字幕缺失...”。

本次结论：Shape A 不是目标字幕文本本身无效，而是目标字幕“文本存在”早于“权威字幕提交完成”。当前实现允许投影/route reducer 在权威字幕提交完成前读取中间状态，并叠加历史 no-dub/no-tts 终态残留，因此会短暂得到错误 route。Shape B 的错误残留是 L4/兼容字段没有在 L2 已恢复为当前权威真相后统一 scrub。

## 2. Authority 路径检查

已按要求先检查 authority 路径。以下指定文件在当前仓库不存在：

- `docs/contracts/hot_follow_state_flow_v1.md`
- `docs/contracts/hot_follow_state_table_v1.md`
- `docs/contracts/hot_follow_forbidden_invariants_v1.md`

未用其他文件替代这三个缺失文件。后续判断只基于当前存在的 authority、合同、ready gate 和限定代码路径。

## 3. 四层 ownership trace

| 层级 | 字段 | truth owner | 写入/投影时机 | truth 类型 | 是否可能早于权威字幕提交 |
| --- | --- | --- | --- | --- | --- |
| L1 | `subtitles.status` | subtitle step / subtitle authority commit path | `steps_v1.run_subtitles_step`、`finalize_hot_follow_subtitles_step`、`hot_follow_subtitle_authority.persist_hot_follow_authoritative_target_subtitle`、router helper failure updates | 持久 truth，投影可按 L2 纠偏为 done/ready | 是。helper failure 可在 authority 可见前写 failed |
| L1 | `dub.status` | dub step | `steps_v1.run_dub_step`、`_skip_empty_dub`、TTS 成功路径 | 持久 truth | 是。若 authority 尚未可见，dub input 为空会写 skipped/no_dub |
| L1 | `compose.status` | compose/update path 与 subtitle/dub 更新路径 | subtitle authority 成功后可置 pending，compose 成功后置 done | 持久 truth | 是。route 可能先按旧 no_dub residue 降级 |
| L2 | `subtitle_ready` | Hot Follow subtitle lane currentness | `_hf_subtitle_lane_state` / projection 计算 | 计算投影 | 是。只看到 `edited_text` 不足以 true |
| L2 | `subtitle_ready_reason` | subtitle currentness evaluator | `compute_hot_follow_target_subtitle_currentness` | 计算投影 | 是 |
| L2 | `target_subtitle_current` | subtitle currentness evaluator，部分路径也持久写入 | authority commit / lane projection | 混合：持久 hint + 计算 truth | 是 |
| L2 | `target_subtitle_authoritative_source` | subtitle currentness evaluator | 根据 artifact existence、source match、source-copy 判定 | 计算投影 | 是。artifact/source 尚未提交时为 false |
| L2 | `audio_ready` | voice/dub currentness 与 deliverable projection | projection/helper 根据 voiceover/audio artifact 判断 | 计算投影 | 是。subtitle 未 ready 时 dub input 被置空 |
| L2 | `dub_current` | voice/dub currentness | projection helper | 计算投影 | 是 |
| L2 | `selected_compose_route` | current attempt / ready gate route reducer | task view helper、status policy、presenter ready gate | 计算投影，部分 payload 写入 | 是。可能先消费 no_dub residue |
| L3 | `current_attempt.selected_compose_route` | `compute_hot_follow_state` / presenter aggregate | `_build_hot_follow_authoritative_state` 在 payload/projection 之后计算 | 计算投影 | 是 |
| L3 | `ready_gate.selected_compose_route` | ready gate/status policy | `compute_hot_follow_state`、ready gate projection | 计算投影 | 是 |
| L3 | `compose_allowed` / `publish_ready` | ready gate/status policy | presenter 组装后输出 | 计算投影 | 是 |
| L3 | advisory recommended action | advisory builder | `maybe_build_hot_follow_advisory` | 计算投影 | 是 |
| L4 | `pipeline.subtitles.error` | workbench projection | `build_hot_follow_workbench_projection` | 展示投影 | 是，但可被 L2 terminal success 清空 |
| L4 | `subtitles.error` | workbench/presenter 兼容 payload | task persisted error 与 projection payload 混合 | 展示/兼容字段，可能带持久 residue | 是，且可能晚于恢复 truth 残留 |
| L4 | `errors.audio` / `errors.pack` / `errors.compose` | projection/presenter | 根据 L1/L2/L3 组装 | 展示投影 | 是 |
| L4 | `operator_summary` | safe presentation aggregate | 从 L2/L3 投影聚合 | 展示投影 | 是 |
| L4 | `presentation` | presenter | hub/publish payload 组装 | 展示投影 | 是 |

关键点：`edited_text` / `srt_text` 是候选文本来源，不等同于 L2 权威目标字幕 truth。L2 必须同时满足语义文本、artifact 存在、expected/actual subtitle source 匹配、非 source-copy、非 translation-incomplete。

## 4. Shape A 根因

Shape A 的直接形成链路如下：

1. `persist_hot_follow_authoritative_target_subtitle` 的写入顺序是：先写 override text，再同步 artifact，再重新评估 persisted authority，最后一次性 `policy_upsert` 更新 `subtitles_status`、`subtitles_error=None`、`compose_status=pending`、`target_subtitle_current=True` 等字段。
2. 在 override text 已经可被读取、artifact/source/currentness 还未完成提交的窗口内，`_hf_subtitle_lane_state` 能读到有效越南语 `edited_text` / `srt_text`，但 `compute_hot_follow_target_subtitle_currentness` 仍会因为 artifact 不存在、source 未匹配或 authority source 不成立而返回 `target_subtitle_current=false`、`target_subtitle_authoritative_source=false`、`subtitle_ready=false`。
3. 当 `subtitle_ready=false` 时，subtitle lane 会把 `dub_input_text` 压为空字符串。dub 路径和 helper 路径此前可能已经因为空输入走过 `_skip_empty_dub`，留下 `pipeline_config.no_dub=true`、`dub_skip_reason=target_subtitle_empty` 或 `dub_input_empty`。
4. `hot_follow_terminal_no_dub_projection` 在 authority 尚未可见时无法用 `subtitle_ready=true` 或 `audio_ready=true` 清除这些历史 terminal no-dub residue，于是 route reducer 可以把当前尝试投影为 `no_tts_compose_route`。
5. 若 source subtitle helper/translation failure 在 authority 可见前落库，`_hf_source_subtitle_translation_failure_updates` 还会写入 `subtitles_status=failed`、`subtitles_error=权威目标字幕缺失...`、`target_subtitle_current=false`。

因此，Shape A 的精确根因是：权威目标字幕提交、route reduction、ready-gate/project 之间缺少一个统一的 state commit 边界。有效目标字幕文本已经存在，但它还不是合同意义上的 authoritative target subtitle。route reduction 在 authority commit 完成前消费了旧 no-dub/no-tts residue，并把中间态投成 `no_tts_compose_route`。

不是根因的项：

- 不是越南语字幕内容无效。
- 不是应该把 `edited_text` / `srt_text` 直接当成权威 truth。
- 不是 projection 应该绕过 artifact/source currentness。

## 5. Shape B stale error 根因

Shape B 表明系统后续已经完成权威字幕、音频、compose 和 publish ready 的收敛。`subtitles.status=done`、`subtitle_ready=true`、`target_subtitle_current=true`、`target_subtitle_authoritative_source=true`、`audio_ready=true` 时，“权威目标字幕缺失...”不再是当前 truth。

该错误能残留的原因是：

1. 该中文错误来自 authority/helper failure 路径的持久错误字段，例如 `subtitles_error` / `subtitles_error_reason`。
2. 后续 projection 能根据 `hf_subtitle_terminal_success(subtitle_lane)` 把 pipeline subtitle state 投成 done/ready，并在部分 pipeline error 字段中隐藏错误。
3. 但 L4 的 `subtitles.error` 兼容字段/展示字段没有一个统一规则保证：当 L2 已满足 `target_subtitle_current=true`、`target_subtitle_authoritative_source=true`、`subtitle_ready=true` 时，所有 subtitle error alias 必须清空。
4. 结果是 L2/L3 已恢复，L4 仍带着旧 L1/helper failure residue。

Shape B 的精确根因是 stale persisted error field 加上 L1/L2/L4 混合 ownership。它不是当前失败 truth，而是恢复后没有被统一 scrub 的展示/兼容残留。

## 6. 当前抽象是否足够

判断：B，当前抽象仍然太低，需要一个更高层的合同驱动 state commit 抽象。

仅在现有分散函数里补一个 if 不足以彻底解决，因为问题跨越了四个边界：

- subtitle authority commit：override text、artifact、source match、content hash、currentness 的提交不是一个对外可见的原子阶段。
- current-attempt route reducer：会在 authority 提交完成前消费 no-dub/no-tts residue。
- ready gate / publish gate：消费的是已经被中间态污染的 projection。
- L4 error/presentation：没有统一以恢复后的 L2/L3 truth scrub stale errors。

最小需要的高层抽象不是大重构，而是一个 Hot Follow current-state commit reducer：

1. authoritative subtitle commit phase：先完成 target override、artifact sync、source/currentness/hash 验证，再发布一个一致的 L1/L2 update bundle。
2. route/current-attempt reducer phase：只消费 commit 后的 L2 truth；若 `subtitle_ready=true` 或 `audio_ready=true`，必须清除旧 `target_subtitle_empty` / `dub_input_empty` no-dub/no-tts residue。
3. recovered-truth error scrub phase：当 L2/L3 已恢复时，统一清空 `subtitles_error`、`subtitles.error`、helper failure alias 和 presentation error residue。
4. ready-gate/project phase：只消费 post-commit state，不再从中间写入窗口推导 route。

## 7. 推荐下一步修复模式

推荐：review complete, higher abstraction doc/spec first。

下一 pass 应先写一个很小的 Hot Follow state commit contract/spec，明确 “authoritative subtitle commit -> route reducer -> recovered error scrub -> projection” 的顺序和字段归属，然后再做窄实现。这样可以避免把修复散落在 router、steps、projection、presenter 多个位置后继续产生新 residue。

## 8. 下一 pass 可能需要触碰的文件

预计下一 pass 的 runtime 触碰范围应限于：

- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/steps_v1.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/task_view_projection.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/status_policy/hot_follow_state.py`

如先补合同/spec，建议新增或更新 Hot Follow state commit 相关 contract 文档，再进入代码修复。

## 9. 本次实际读取文件

Phase 0：

- `README.md`
- `ENGINEERING_CONSTRAINTS_INDEX.md`
- `docs/ENGINEERING_INDEX.md`
- `docs/contracts/engineering_reading_contract_v1.md`

Phase 1：

- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`

Phase 2：

- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/task_view_projection.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/services/task_view_helpers.py`
- `gateway/app/services/steps_v1.py`
- `gateway/app/routers/hot_follow_api.py`

直接委托扩展：

- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/services/hot_follow_subtitle_currentness.py`

