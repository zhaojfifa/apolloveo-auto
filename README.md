# ApolloVeo Auto

ApolloVeo 当前是一个以成片交付为目标的 AI 内容生产工厂代码库。

当前阶段不是平台扩张期，而是 Factory Alignment Review Gate Active：post-review、post-VeoSop05 的基座收口必须遵守 `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`。

## Start Here

1. `ENGINEERING_RULES.md`
2. `CURRENT_ENGINEERING_FOCUS.md`
3. `PROJECT_RULES.md`
4. `docs/baseline/PROJECT_BASELINE_INDEX.md`
5. `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
6. `docs/README.md`
7. `ENGINEERING_STATUS.md`
8. `CHANGELOG_STAGE.md`

## Current Reality

- Hot Follow 是当前主线
- 新产线 onboarding 在 factory alignment gate prerequisites 清除前 blocked
- business validation 是 mandatory merge gate
- `_drafts/` 仅作为历史评审与 RFC source material，不是日常 source-of-truth

## Before Any Codex Task

Use index-first reading. Start with only:

1. `README.md`
2. `ENGINEERING_CONSTRAINTS_INDEX.md`
3. `docs/README.md`
4. `docs/ENGINEERING_INDEX.md`
5. `docs/contracts/engineering_reading_contract_v1.md`

Then classify the task through the indexes and read only the minimum
task-specific authority files selected by that path. Do not begin engineering
work from a long flat list of contracts, baselines, and reviews.

当前 canonical authority set 已补齐，阅读 contract/index 时不应再依赖缺失路径或隐式 fallback。

## Repo Map

- `gateway/` runtime code
- `docs/` current documentation system
- `_drafts/` historical review source material
- `ops/` scripts and checks
- `assets/` reusable assets
