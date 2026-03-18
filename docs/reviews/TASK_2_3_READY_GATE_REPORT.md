# TASK-2.3 Declarative Ready Gate Engine 战报

> 日期: 2026-03-18 | 分支: VeoSop04 | 主刀: Claude Opus 4.6

## 变更清单

| 文件 | 操作 | 行数 |
|------|------|------|
| `gateway/app/services/ready_gate/engine.py` | **新建** | 189 行 |
| `gateway/app/services/ready_gate/hot_follow_rules.py` | **新建** | 216 行 |
| `gateway/app/services/ready_gate/__init__.py` | **新建** | 27 行 |
| `gateway/app/services/status_policy/hot_follow_state.py` | **重构** | 272→261 行 |

## 三大目标达成

### 1. 规则剥离

120 行 if/else 完全替换为声明式规则：

| 类型 | 数量 | 映射 |
|------|------|------|
| `Signal` | 8 | 命名布尔信号，带独立 extract 函数 |
| `OverrideRule` | 2 | 产物存在 → 覆盖 no_dub 标记 |
| `GateRule` | 2 | compose_ready = final_exists AND (audio_ready OR no_dub) |
| `BlockingRule` | 7 | 精确映射原有 7 个 if 语句 |

### 2. 数据流设计 (Single Source of Truth)

三段式架构：

```
_resolve_artifacts()  →  evaluate_ready_gate()  →  _apply_gate_side_effects()
     副作用                    纯函数                      副作用
```

- `evaluate_ready_gate()` 是纯函数，4-pass 求值：Signal提取 → Override应用 → Gate求值 → Blocking收集
- 输出 9 字段 `ready_gate` dict，前端 JS 直接消费，无需改动

### 3. 可扩展性

新产线（如 Localization Line）只需声明自己的 `ReadyGateSpec`：

```python
LOCALIZATION_GATE_SPEC = ReadyGateSpec(
    line_id="localization_line",
    signals=(...),
    gates=(...),
    blocking=(...),
)
```

## 信号映射表

| Signal | 提取逻辑 | 原代码行 |
|--------|----------|----------|
| `final_exists` | `_pick_final()` + URL evidence | L95-97 |
| `audio_done` | status in {"done","ready","success","completed"} | L158 |
| `voiceover_exists` | audio/media URL OR mm_audio_key/path | L159-164 |
| `tts_voice_valid` | non-empty, not in {"-","none","null"} | L165-166 |
| `audio_ready` | hint override OR (audio_done AND voiceover_exists AND tts_voice_valid) | L167-171 |
| `subtitle_artifact_exists` | artifact/source/text/srt_text/mm_srt_path | L173-179 |
| `subtitle_ready` | hint override OR subtitle_artifact_exists | L181 |
| `no_dub` | audio.no_dub flag (before override) | L183 |

## 向后兼容性

- `compute_hot_follow_state()` 函数签名完全不变
- `ready_gate` 输出 9 字段格式完全不变
- 前端 JS 零改动
- 调用方零改动

## Scope Fence

- 不改 `compute_composed_state()`（留 Phase 2.4）
- 不改 `collect_voice_execution_state()`（仍独立调用）
- 不改前端 JS（已是 ready_gate 消费者）
- 不改 `policy_upsert` 写入边界
- 不加 YAML/JSON 配置文件（规则是 Python 代码）
