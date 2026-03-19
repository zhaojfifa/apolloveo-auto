# Project Rules

## Doc Usage Rules

- day-to-day source-of-truth 在 `docs/`
- `_drafts/` 只作为历史 source material
- review 结论必须吸收到 `docs/reviews/`、`docs/baseline/` 或 `docs/execution/`
- every Codex run should read `ENGINEERING_RULES.md` and `CURRENT_ENGINEERING_FOCUS.md` first

## Merge Rules

- no merge without required validation
- Hot Follow follow-up PR 必须重跑 business regression
- 文档边界变化必须同步更新 docs
- 阶段性变更必须追加 execution log
- PR 必须写清 fix / not-fix / follow-up

## Engineering Constraints

- 不把 cleanup 扩成平台化重构
- 不把 future-state 设计描述成已实现
- 不继续制造 God router / God service / hidden contract
- 不允许用 lazy import 掩盖耦合问题
- 不允许让 compatibility helper 持续膨胀

## Required Validation Discipline

- 遵守 `docs/runbooks/VERIFICATION_BASELINE.md`
- 遵守 `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`
- 区分 code regression 与 environment limitation

## Currently Forbidden

- Skills implementation
- second production line
- OpenClaw integration work
- broad platform abstractions
- unrelated runtime rewrites mixed into docs or cleanup PRs
