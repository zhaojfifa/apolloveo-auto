# Matrix Script Design Authority Index

Date: 2026-06-01
Branch: `cleanup/matrix-script-reset-to-mock-and-result-line-20260601`
Baseline rollback tag: `baseline-ms-before-cleanup-20260601`
Status: **BINDING authority index.**

This file is an authority convergence index only. It does not introduce a new
Matrix Script mock, IA, reset design, contract, schema, runtime, worker, Akool
binding, Hot Follow behavior, Digital Anchor behavior, or `artifact_storage.py`
change.

## Bucket A — Binding Authority

Future Matrix Script UI and result-line work must cite these files first and
must not use execution logs as design authority:

1. `docs/product/matrix_script_product_flow_v2_delta.md`
2. `docs/design/matrix_script_script_to_video_presenter_alignment_v1.md`
3. `docs/design/previews/matrix_script_script_to_video_workbench_v1/index.html`
4. `docs/design/matrix_script_workbench_product_flow_reset_v1.md`
5. `docs/design/matrix_script_phase2c_operator_readability_plan_v1.md`
6. `docs/architecture/matrix_script_script_to_video_contract_alignment_v1.md`
7. `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md`
8. `docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md`
   (P0 closure baseline — #202 artifact-truth + #203 async lifecycle / polling /
   stale guard; records the New Task → Workbench inline-video terminal flow,
   the operator-only primary-UI rule, and the four-layer boundary. Binding for
   the P0 lifecycle baseline; not a new UI/IA design.)

## Binding Reading

- The accepted product surface is the script-to-video Workbench, not a
  generic task/status/result surface.
- The Workbench operator flow is A-J:
  A 主视频结果, B 脚本理解, C 视频生成计划 / 分镜故事板, D 画面与素材,
  E 角色与声音, F 字幕与音乐, G 视频变体, H 校对与微调,
  I 交付入口, J 技术诊断.
- The PR-A real-result chain is retained as a result capability:
  local real assets -> script-driven shot plan -> final.mp4 ->
  artifact_staged -> preview_url -> operator acceptance ->
  official_publish_ready=false.
- PR-A result fields are projected into the A-J flow; they must not create
  standalone temporary result cards or a second parallel flow.
- `docs/execution/MATRIX_SCRIPT_REAL_RESULT_BASELINE_20260601.md` is binding
  only for result acceptance facts. It is not a new UI or IA design.

## Anti-Sprawl Rules

1. Execution logs are evidence only, not authority.
2. No new Matrix Script mock, IA, reset, or next-wave design document may be
   created to supersede Bucket A.
3. Future UI work must cite Bucket A only.
4. New operator value must be merged into an existing A-J section, not added as
   a parallel Workbench flow.
5. Engineering fields, raw artifact references, traces, and raw JSON belong
   only in J 技术诊断, collapsed by default.
6. `official_publish_ready` remains false until an approved delivery contract
   gate says otherwise.

## PR-191 Handling

PR-191 is superseded by the one-step cleanup branch. Its authority
consolidation intent is folded into this index after the baseline tag; the PR
must not be merged separately.

## Planning / Review Inputs (NOT authority)

These are operator-lens planning and review proposals. They are **not Bucket A
binding authority**, do not supersede Bucket A, do not define IA, and authorize no
implementation. Future UI work still cites Bucket A first (Anti-Sprawl rule 3); a
planning input may only be acted on after it is converted into a gate spec under the
standard discipline.

- `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_PLAN_20260607.md` — Guided
  Operator Workflow Planning Review (2026-06-07) over the #211–#215 substrate.
  Operator-mainline procedure, advanced/diagnostics fold, A/B/C/D/E re-order
  proposal, operator-language state vocabulary, per-button expectations,
  diagnosable-but-non-leaking Network/action-log split, and a gate-spec-first 6-PR
  slicing proposal. Proposal only.
