# Next Hot Follow Cleanup Scope

## 1. Immediate Cleanup Targets

下一阶段只聚焦 Hot Follow cleanup：

- 继续削薄 `gateway/app/routers/tasks.py`
- 继续移除或隔离 compatibility-only helpers
- 继续清理剩余的 Hot Follow-specific workbench / detail / presentation assembly

当前目标是减少兼容层残留和场景专属拼装残留，不是开启新的系统能力面。

## 2. Explicit Non-Goals

以下事项明确排除：

- Skills implementation
- second production line
- OpenClaw work
- provider expansion
- broad platformization

## 3. Proposed Next PR Buckets

### PR-A — Thin Remaining Hot Follow Logic in `tasks.py`

purpose:
- 继续减少 `tasks.py` 中仍然存在的 Hot Follow-specific branching / assembly

likely files:
- `gateway/app/routers/tasks.py`
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`

why it matters now:
- `tasks.py` 仍是当前 Hot Follow cleanup 最明显的剩余承载点

business regression cases to rerun:
- Case D — Deliverable Consistency
- Case F — Workbench Consistency

### PR-B — Isolate Compatibility-Only Helpers

purpose:
- 进一步明确哪些 helper 只是 compatibility layer，并把它们从主 runtime contract 隔离出来

likely files:
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/services/`
- `docs/contracts/`

why it matters now:
- 兼容 helper 若持续与主路径混用，会重新模糊 runtime boundary

business regression cases to rerun:
- Case A — Parse Status Consistency
- Case B — Subtitle Editing Semantics
- Case F — Workbench Consistency

### PR-C — Clean Hot Follow Workbench / Detail Presentation Assembly

purpose:
- 清理 Hot Follow-specific workbench/detail/presentation assembly，减少隐式 view-model 拼装漂移

likely files:
- `gateway/app/routers/hot_follow_api.py`
- `gateway/app/templates/`
- `gateway/app/static/js/`
- `gateway/app/services/`

why it matters now:
- PR-5 已证明业务一致性问题会直接出现在 presentation layer

business regression cases to rerun:
- Case A — Parse Status Consistency
- Case B — Subtitle Editing Semantics
- Case D — Deliverable Consistency
- Case E — Download / Playback Consistency
- Case F — Workbench Consistency

## 4. Business Gate Before Merge

后续 Hot Follow PR 必须遵守以下 merge gate：

- no PR merges without business regression
- document validation must be updated when boundary semantics change
- `docs/execution/logs/VEOSOP05_PROGRESS_LOG.md` or successor progress log must be appended
