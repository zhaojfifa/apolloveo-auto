# Hot Follow Business Regression

## 1. Purpose

本清单是 Hot Follow 后续变更的 mandatory business regression baseline。

用途不是替代自动化测试，而是保证真实业务链路中的状态、字幕、交付物、播放与工作台语义不再出现“代码看起来通过，但业务结果错误”的回归。

## 2. Mandatory Regression Cases

### Case A — Parse Status Consistency

- 当 raw video 可用时，parse 必须显示 success / done
- `pipeline.parse.message = raw=ready` 时，parse 不得显示 failed
- displayed parse status 必须与 raw artifact facts 一致

### Case B — Subtitle Editing Semantics

- translated subtitle editing 必须保持 SRT-first
- 任何 plain-text helper 都必须是 secondary/helper-only
- primary editing source 必须保持 timeline-based

### Case C — Compose Duration Policy

- 当 dub/audio 短于 video 时，final duration 仍必须跟随 video length
- final output 不得再被 shortest-audio behavior 截断
- 若 compose plan 声明 `match_video` / `freeze_tail`，runtime 行为必须与之不冲突

### Case D — Deliverable Consistency

- final video artifact 存在
- subtitle artifact 存在
- audio artifact 存在
- displayed status 必须与 artifact facts 一致

### Case E — Download / Playback Consistency

- final video 可播放
- source video 可播放
- 若页面显示 subtitle/audio/final 下载路径，则对应下载路径必须有效

### Case F — Workbench Consistency

- workbench messaging、ready state、compose status、deliverables 之间不得互相矛盾
- 不允许出现 artifact 已 ready 但页面仍显示明显冲突状态

## 3. Execution Notes

解释器 / 环境：

- 推荐使用 `./venv/bin/python`
- 系统 `python3` 仅用于最低纯单测，不作为 Hot Follow 主线业务回归解释器
- 详细解释器边界以 `docs/runbooks/VERIFICATION_BASELINE.md` 为准

自动化检查：

- 运行当前冻结的最小回归命令
- 对本次修改直接相关的 targeted tests 必须执行

人工检查：

- 打开真实 task/workbench 页面确认 parse / subtitle / compose / deliverable 展示
- 验证 final/source 的播放与下载行为
- 验证工作台中不存在主对象与 helper 文案互相覆盖

失败记录要求：

- task id
- 分支名
- 解释器 / 环境
- 失败 case
- 观察到的事实层证据
- 是否可稳定复现

## 4. Failure Classification

- code regression
  - 代码改动直接导致状态、交付物、页面或行为回退
- environment limitation
  - 由本地依赖、环境变量、资源缺失或执行环境差异导致
- known Python baseline mismatch
  - 由于 Python 3.9 vs 3.10+ 基线不匹配导致的收集或导入问题
- external dependency issue
  - 由对象存储、外部 provider、网络或第三方服务异常导致

## 5. Sign-off Template

```text
task id:
branch:
verifier:
date:
passed cases:
failed cases:
notes:
```
