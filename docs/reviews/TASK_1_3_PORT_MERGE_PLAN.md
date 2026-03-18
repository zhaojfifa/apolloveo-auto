# TASK-1.3 Port Merge — 下沉文件结构规划

> **日期**: 2026-03-18
> **分支**: VeoSop04
> **前置**: Phase 1.2 Router Split 完成
> **目标**: 消除 tasks.py ↔ hot_follow_api.py 的 39+4 循环依赖

## 现状依赖拓扑

```
hot_follow_api.py ───── 39 imports ─────→ tasks.py
tasks.py ───── 4 lazy imports (10 函数) ──→ hot_follow_api.py
```

## 目标依赖拓扑

```
tasks.py ─────────┐
                   ├──→ services/ (新模块)
hot_follow_api.py ─┘

tasks.py ✕ hot_follow_api.py  (零互相引用)
```

## 新建模块规划

### 模块 1: `services/task_view_helpers.py` (~480 行, 15 函数)

| 函数 | tasks.py 行号 | 行数 |
|------|-------------|------|
| `_task_value` | L1616 | ~11 |
| `_task_key` | L1627 | ~5 |
| `_task_endpoint` | L1158 | ~23 |
| `_task_to_detail` | L1874 | ~77 |
| `_scenes_status_from_ssot` | L1632 | ~27 |
| `_deliverable_url` | L1277 | ~41 |
| `_resolve_hub_final_url` | L1466 | ~23 |
| `_publish_hub_payload` | L1533 | ~83 |
| `_compute_composed_state` | L1335 | ~67 |
| `_scene_pack_info` | L1402 | ~39 |
| `_compose_error_parts` | L1318 | ~17 |
| `_backfill_compose_done_if_final_ready` | L1489 | ~44 |
| `_count_srt_cues` | L273 | ~7 |
| `_build_translation_qa_summary` | L280 | ~10 |
| `_build_workbench_debug_payload` | L290 | ~10 |

### 模块 2: `services/voice_state.py` (~222 行, 8 函数)

| 函数 | tasks.py 行号 | 行数 |
|------|-------------|------|
| `_build_hot_follow_voice_options` | L1982 | ~19 |
| `_resolve_hot_follow_requested_voice` | L2001 | ~46 |
| `_hot_follow_expected_provider` | L2047 | ~10 |
| `_voice_state_config` | L2057 | ~11 |
| `_resolve_hot_follow_provider_voice` | L2068 | ~27 |
| `_hf_persisted_audio_state` | L2095 | ~17 |
| `_hf_audio_matches_expected` | L2112 | ~18 |
| `_collect_voice_execution_state` | L2130 | ~74 |

### 模块 3: `services/compose_helpers.py` (~77 行, 5 函数)

| 函数 | tasks.py 行号 | 行数 |
|------|-------------|------|
| `_task_compose_lock` | L196 | ~9 |
| `_compose_in_progress_response` | L205 | ~12 |
| `_build_atempo_chain` | L217 | ~25 |
| `_resolve_audio_fit_max_speed` | L242 | ~16 |
| `_compute_audio_fit_speeds` | L258 | ~15 |

### 模块 4: `services/media_helpers.py` (~133 行, 4 函数)

| 函数 | tasks.py 行号 | 行数 |
|------|-------------|------|
| `_sha256_file` | L1958 | ~10 |
| `_probe_url_metadata` | L2697 | ~50 |
| `_update_pipeline_probe` | L2225 | ~12 |
| `_upload_task_bgm_impl` | L2953 | ~61 |

### 模块 5: `core/constants.py` (~20 行)

| 符号 | 说明 |
|------|------|
| `OP_HEADER_KEY` | `"X-OP-KEY"` |
| `COMPOSE_RETRY_AFTER_MS` | `1500` |
| `api_key_header` | `APIKeyHeader(...)` |
| `DubProviderRequest` | Pydantic model |
| `PublishBackfillRequest` | Pydantic model |

### `_policy_upsert` 处理

删除 wrapper，所有调用点直接使用 `policy_upsert()`。

### 反向懒加载 (4 处)

本次保留，标注 `# TODO(Phase-2): eliminate via line callback registry`。

## 执行影响

| 文件 | 变化 |
|------|------|
| `tasks.py` | 删除 ~930 行函数定义，改写 import |
| `hot_follow_api.py` | 39-import 块 → 4 个 services import |
| 新增 5 个模块 | ~932 行 |
| 测试文件 (6 个) | monkeypatch 路径更新 |

零 URL 变更，零行为变更，纯结构搬迁。
