# TASK-2.0 CompositionService 心脏搭桥手术报告

> 日期: 2026-03-18 | 分支: VeoSop04 | 主刀: Claude Opus 4.6

## 变更清单

| 文件 | 操作 | 行数变化 |
|------|------|----------|
| `gateway/app/services/compose_service.py` | **新建** | +856 行 |
| `gateway/app/routers/hot_follow_api.py` | **编辑** | -575 行（625 行 god function → 46 行 thin wrapper + promoted helpers） |
| `gateway/app/routers/tasks.py` | **不动** | 0 |

## 三大目标达成

### 1. 职责分离

`CompositionService` 拆分为 4 个阶段：

- `_validate_inputs()` — 前置校验
- `_prepare_workspace()` — 下载 & 准备
- `_compose_*()` — 3 个分支方法 + 统一 `_run_ffmpeg()` 网关
- `_validate_and_probe_output()` + `_upload_and_verify()` — 后置处理

### 2. 健壮性注入

8 个 `subprocess.run` 全部收敛至 `_run_ffmpeg()` 网关：

| 调用点 | Timeout | 超时后行为 |
|--------|---------|------------|
| freeze-tail (tpad) | 120s | **降级**：回退到 match_video |
| 主合成 ×4 | 600s | **终止**：compose_fail → 409 compose_timeout |
| compose fallback CRF23 | 600s | **终止**：compose_fail → 409 |
| ffprobe 探测 | 30s | **静默跳过**：使用 assert_local_video_ok 的 duration |
| 时长裁剪 clamp | 120s | **静默跳过**：保留未裁剪版本，添加 warning |

### 3. 回归防御

5 个历史 bug 修复 100% 继承：

| Bug | 原 Commit | 本次处理 | 回归风险 |
|-----|-----------|----------|----------|
| datetime UnboundLocalError | bb73f5d | compose_service.py 使用模块级 `from datetime import datetime, timezone`，绝无局部 import 遮蔽 | 零 |
| Exception handler cascade | 76e15a3 | 调用方 tasks.py:2486-2526 完全不动 | 零 |
| Compose lock outside try | 267744a | 调用方 tasks.py:2446 完全不动 | 零 |
| Empty SRT crash on subtitle-only | 267744a | 逐行移植到 `_prepare_workspace()`，保持 `if subtitle_only_compose: overlay_subtitles = False` 逻辑 | 低 |
| Compose revision stale check | 42677d0 | 调用方 tasks.py:2467-2474 完全不动 | 零 |

## 9 个嵌套函数去向

| 原嵌套函数 | 目标位置 | 理由 |
|---|---|---|
| `_compose_fail` | `compose_service.py` 模块级 `compose_fail()` | 纯函数，无闭包变量 |
| `_normalize_target_lang` | `hot_follow_api.py` 模块级 `_normalize_compose_target_lang()` | 被 `_resolve_target_srt_key` 调用 |
| `_resolve_target_srt_key` | `hot_follow_api.py` 模块级 | 深度依赖 HF 专有函数，通过 callable 注入 |
| `_escape_subtitles_path` | `compose_service.py` 模块级 | 纯字符串变换 |
| `_bgm_filter_expr` | `CompositionService` 私有方法 | 闭包变量 → 显式参数 |
| `_bgm_only_filter_expr` | `CompositionService` 私有方法 | 同上 |
| `_assert_overlay_cmd` | `CompositionService` 静态方法 | 同上 |
| `_source_subtitle_cover_filter` | `compose_service.py` 模块级 | 纯函数 |
| `_compose_subtitle_vf` | `compose_service.py` 模块级 | 纯函数 |

## 依赖拓扑

```
tasks.py (调用方，不动 try/except/finally)
  └── _hf_compose_final_video (thin wrapper)
        └── CompositionService.compose()           [compose_service.py]
              ├── subtitle_resolver(callable)       [hot_follow_api.py: _resolve_target_srt_key]
              │     └── _hf_sync_saved_target_subtitle_artifact
              │     └── _task_key, deliver_key, object_exists
              ├── subtitle_only_check(callable)     [hot_follow_api.py: _hf_allow_subtitle_only_compose]
              ├── storage                           [ports/storage_provider]
              ├── get_settings()                    [config.py]
              ├── collect_voice_execution_state     [voice_state.py]
              ├── assert_artifact_ready / assert_local_*  [media_validation]
              └── sha256_file                       [media_helpers.py]
```

## Scope Fence（不做什么）

- 不改 tasks.py 的 try/except/finally 异常处理结构
- 不改 policy_upsert 写入边界
- 不改 compose_helpers.py 现有函数（lock、atempo、audio-fit）
- 不加新的外部依赖
- 不动 compose_plan 的 JSON schema
- 不动返回值 dict 的 27 个字段签名
- 不做中间检查点持久化（留给 Phase 2.1）
