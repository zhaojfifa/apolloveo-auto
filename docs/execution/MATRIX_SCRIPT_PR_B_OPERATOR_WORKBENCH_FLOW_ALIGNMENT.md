# PR-B · Matrix Script Operator Workbench Flow Alignment (revised → overlay)

Date: 2026-06-01
Branch: `phase3/pr-b-matrix-script-operator-workbench-flow`
Scope: UI / presenter overlay only. No new generation engine, no schema/contract, no Hot Follow / Digital Anchor, no `artifact_storage.py`, no Akool live, no `official_publish_ready=true`, no `provider_url`/`publish_url`/`temporary_url`.

## Revision context

The first PR-B revision added a **parallel** `matrix-script-operator-flow` (`ms-flow-*`) section. The mock-alignment review (`docs/reviews/MATRIX_SCRIPT_PR_B_MOCK_ALIGNMENT_REVIEW.md`) classified that **FAIL** — the binding Workbench mock is already implemented on `main` (presenter-bound ① / ② / script-understanding / variants / ⑤), so a second flow created duplicate + contradictory sections.

**This revision is the corrected, narrow overlay.** It removes the parallel flow and overlays only the useful PR-A acceptance values into the EXISTING sections.

## What was removed

- The entire `matrix-script-operator-flow` parallel `<section>` (all `ms-flow-*` primary sections).
- `TOMATO_SCRIPT_UNDERSTANDING` and `TOMATO_VARIANTS` fixtures (deleted from `tomato_real_result_plan.py`) — no longer rendered as task truth.
- The duplicate parallel delivery block.
- The redundant standalone PR-A "运营可用预览" action card (folded into ① below).

## What was overlaid into the existing mock

- **① `matrix-script-main-video-result`** — acceptance overlay (`ms-main-video-result-acceptance`): 运营状态 (operator_usable→可交付 / technical_preview→待审核 / none→未生成), 画面语义匹配, 匹配镜头数 (shot_match_count/shot_count), 真实视觉镜头数, 交付候选, 正式交付就绪=false, 阻塞原因, a 生成运营可用预览 action, and a 打开视频 link. When the PR-A result is operator-usable, the legacy empty-state (`ms-main-video-result-preview-empty`) and blocker banner are **suppressed** (server-side `{% elif ms_overlay_mr.operator_usable %}` + `{% if not ms_overlay_mr.operator_usable %}`; JS hides them after a live generate) so ① never shows 未生成 / 主成片缺失 in that state.
- **② `matrix-script-section-generation-plan`** — per-shot acceptance overlay (`ms-section-generation-plan-shot-acceptance-overlay`, loop over `ms_overlay.shots`): each shot's 素材来源 / 语义匹配 / 是否进入当前主视频. No second storyboard.
- **⑤ `matrix-script-section-delivery-entry`** — delivery overlay (`ms-section-delivery-entry-acceptance`): 交付候选 / 正式交付就绪=false / 打开视频（暂存预览）. CTA stays `/tasks/{task_id}/publish`.

The existing **脚本理解** (`ms_script_structure`) and **变体** (`ms_readable_variants`) sections are untouched and remain presenter-bound per task.

## Helper

`gateway/app/services/matrix_script/operator_workbench_view.py::build_matrix_script_operator_workbench_view(task, *, result=None, env=None)` now returns an **overlay-only** payload: `{is_matrix_script, has_pr_a_result, main_result, shots, delivery, generate_endpoint}`. Result source: the staged PR-A candidate on `task.config` (read-only) or an explicit `result`. Wired into the existing matrix_script branch of `operator_visible_surfaces/wiring.py` as `matrix_script_operator_flow` (kind-gated). Self-guards against provider/publish token leakage.

## Four-layer mapping

L1 generation/shot status · L2 artifacts (final.mp4/subtitles/audio/manifest/preview_url) · L3 acceptance (operator_usable / visual_semantic_match / shot_match_count / real_visual_count / delivery_candidate) → overlaid into ①/②/⑤ · L4 displays derived facts only. No invented truth; fixtures no longer rendered as task content.

## Single-flow proof

| Section | anchors |
|---|---|
| main result | exactly 1 (`matrix-script-main-video-result`); `ms-flow-main-result` = 0 |
| script understanding | exactly 1 (`matrix-script-section-script-understanding`); `ms-flow-*` = 0 |
| generation-plan / storyboard | exactly 1 (`matrix-script-section-generation-plan`) |
| variants | existing `matrix-script-section-optional-variants` retained; `ms-flow-variants` = 0 |
| delivery entry | exactly 1 (`matrix-script-section-delivery-entry`), CTA `/tasks/{task_id}/publish` |

## Tests

`gateway/app/services/tests/test_matrix_script_operator_workbench_flow_alignment.py` — **15 passed**. Proves: exactly one of each section; overlay feeds PR-A acceptance (operator_usable / partial_pass / 3 of 5 / real 3 / preview_url / official_publish_ready=false); ① suppresses empty-state/blocker when operator_usable (source-structure + block-render); ② carries the per-shot acceptance overlay; script-understanding + variants stay presenter-bound and the tomato fixtures are gone (`not hasattr` checks); delivery keeps `/tasks/{task_id}/publish`; no provider/publish leakage. Adjacent regression (PR-A tomato + phase2b fidelity + main_video_result_view): **81 passed**.

Rendered evidence: `docs/execution/screenshots/pr_a_tomato/pr_b_overlay_main_result.png` — existing ① block with PR-A acceptance overlaid (可交付 / 主视频已生成·运营可用 / partial_pass), no 未生成.

## Boundary

No schema/contract; no Hot Follow / Digital Anchor; `artifact_storage.py` untouched; no Akool live; no `official_publish_ready=true`; no `provider_url`/`publish_url`/`temporary_url`. Files: `operator_workbench_view.py` (overlay-only), `tomato_real_result_plan.py` (fixtures removed), kind-gated `wiring.py`, matrix_script branch of `task_workbench.html` (parallel flow removed; overlays added to ①/②/⑤), test, docs, screenshot.
