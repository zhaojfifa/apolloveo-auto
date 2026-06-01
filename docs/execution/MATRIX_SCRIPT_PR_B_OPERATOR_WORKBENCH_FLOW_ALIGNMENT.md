# PR-B · Matrix Script Operator Workbench Flow Alignment

Date: 2026-06-01
Branch: `phase3/pr-b-matrix-script-operator-workbench-flow`
Scope: UI / presenter alignment only. No new generation engine, no schema/contract, no Hot Follow / Digital Anchor, no `artifact_storage.py`, no Akool live, no `official_publish_ready=true`, no `provider_url`/`publish_url`/`temporary_url`.

## Goal

Make the Matrix Script Workbench an operator-driven, script→video production surface. The **Main Video Result** is the dominant top surface and is **linked** to the decisions that produced it:

```
主视频结果 ↕ 脚本理解 ↕ 分镜/镜头计划 ↕ 素材与视觉资产 ↕ 角色/配音 ↕ 字幕/音乐 ↕ 视频变体 ↕ 交付
```

The main result is the current projection of those lower decisions — not an isolated card above technical blocks.

## What changed

- **New presenter** `gateway/app/services/matrix_script/operator_workbench_view.py` → `build_matrix_script_operator_workbench_view(task, *, result=None, env=None)` returns one `MatrixScriptOperatorWorkbenchView` dict: `main_result` / `script_understanding` / `storyboard` / `materials` / `voice` / `subtitles_music` / `variants` / `delivery`. Pure projection over the fixed tomato plan + the PR-A staged result (read-only). Self-guards against provider/publish token leakage.
- **Fixture additions** in `tomato_real_result_plan.py`: `TOMATO_SCRIPT_UNDERSTANDING` + `TOMATO_VARIANTS` (V1 generated; V2/V3 planned/pending — same script plan). No contract.
- **Wiring** (`operator_visible_surfaces/wiring.py`, +14 lines): inside the existing `panel_kind == "matrix_script"` branch, attach `bundle["workbench"]["matrix_script_operator_flow"]`. Kind-gated; never enters for Hot Follow / Digital Anchor.
- **Template** (`task_workbench.html`, matrix_script branch only): added the linked A–H operator-flow `<section>` as the dominant top surface; **removed the now-redundant PR-A "运营可用预览" action block** (Section A owns the generate action and updates its own fields live from the route response). Legacy blocks below are untouched (their retirement is the separate Workbench-reset wave).

## Four-layer mapping (UI invents no truth)

- **L1**: generation steps / shot assembly status (storyboard `generation_status`).
- **L2**: artifacts — final.mp4 / subtitles / audio / manifest / preview_url / shot clips (drive `main_result.preview_url`, `subtitles_music`).
- **L3**: operator acceptance — `operator_usable` / `visual_semantic_match` / `shot_match_count` / `real_visual_count` / `delivery_candidate` (drive `main_result` + per-shot `semantic_status`).
- **L4**: the Workbench sections display only these derived facts. Main result derives from L2+L3; storyboard from the fixed shot plan + acceptance; variants carry planned V2/V3 but only V1 may be marked generated.

## Result linkage (tomato case, operator-usable result)

| field | value |
|---|---|
| current variant | V1 清新种草版 |
| status | operator_usable (运营可用) |
| visual_semantic_match | partial_pass |
| shot_match_count | 3 / 5 |
| real_visual_count | 3 |
| delivery_candidate | true |
| official_publish_ready | false |
| preview_url | `/api/matrix-script/{id}/tomato-real-result/preview/final.mp4` |

### Storyboard linkage

| Shot | Script role | Asset | Source | Semantic | In current video |
|---|---|---|---|---|---|
| 01 海边 Hook | Hook | 01_beach_hook.png | local_real_asset | pass | true |
| 02 小番茄产品特写 | Body | 02_tomato_bowl.png | local_real_asset | pass | true |
| 03 拿起小番茄 | Body | 03_pick_tomato.png | local_real_asset | pass | true |
| 04 品尝爆汁 | Body | 03_pick_tomato.png | fallback_semantic_reuse | partial | true |
| 05 递向镜头 CTA | CTA | 02_tomato_bowl.png | fallback_semantic_reuse | partial | true |

Rendered evidence: `docs/execution/screenshots/pr_a_tomato/pr_b_operator_flow.png` (Section A shows 运营可用, not 未生成; B–E linked below).

## Tests

`gateway/app/services/tests/test_matrix_script_operator_workbench_flow_alignment.py` — **15 passed**. Covers: main result uses operator_usable result; not_generated when no result; technical_preview on fallback; rendered Section A has no 未生成/主成片缺失 when usable; storyboard 5 shots with source+semantic; materials→shots mapping; voice azure vs fallback; subtitles state; variants V1 generated / V2/V3 pending; delivery V1 candidate + official_publish_ready false; no provider/publish leakage; staged-candidate-on-config path; module import boundary. Adjacent regression (PR-A tomato + phase2b fidelity + main_video_result_view): **81 passed**.

## Boundary

No schema/contract; no Hot Follow / Digital Anchor; `artifact_storage.py` untouched; no Akool live; no `official_publish_ready=true`; no `provider_url`/`publish_url`/`temporary_url`. Only: new presenter + fixture + 14-line kind-gated wiring + matrix_script template branch + test + screenshot.
